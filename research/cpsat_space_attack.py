"""Exact constraint-programming attack (OR-Tools CP-SAT) on the space model (§42).

Space model, known natural shuffles (β, σ), unknown keyed starting deck. The only unknowns are the
start position x_c of each card (a permutation) and one space/letter decision per symbol. Local
searches fail (§33–§39); the whole problem is handed to an exact solver.

Compact formulation:
  - messages are merged into a tree of cipher prefixes (identical cipher prefix ⇒ identical plaintext);
  - for each node and each card re-read later in the subtree, a "position" variable;
    child position = Sinv_β[position] or Sinv_σ[position] depending on the node's decision (166-tuple table);
  - read at the node: space decision ⇔ read position = q_space; otherwise read position ∈ Q_letters;
  - Q known (convention "letter of rank k read at position k", §39) or unknown (booleans inQ, |Q| = 36,
    q_space variable);
  - options: no two consecutive spaces; no space at the first symbol;
  - shared text blocks (a, i, b, j, L): aligned positions ⇒ same letter ⇒ same read position and same
    decision (block equations of §37, exact here inside the solver).
"banc" (testbed) mode: known truth, we measure time and accuracy (start positions, decisions).
Usage: python cpsat_space_attack.py banc L [Qconnu|Qinconnu] [time_s] [seed] [blocs] [strategie]"""
import sys
import time
import numpy as np
from ortools.sat.python import cp_model
from keyed_deck_attack import tables, N
import testbed_spaces as tbs
from explore import xgak_encrypt


def build_trie(msgs):
    """Nodes: (parent, card read); returns the list of nodes, children, and for each message its node sequence."""
    nodes, children, index, paths = [], [], {}, []
    for m in msgs:
        par, path = -1, []
        for c in m:
            key = (par, c)
            if key not in index:
                index[key] = len(nodes); nodes.append(key); children.append([])
                if par >= 0:
                    children[par].append(index[key])
            par = index[key]; path.append(par)
        paths.append(path)
    return nodes, children, paths


def solve(msgs, binv, sinv, Q=None, qs_known=None, tlimit=600, workers=16, no_double_space=True, hint=None,
          log=False, blocks=(), maxword=0, strategy=False):
    nodes, children, paths = build_trie(msgs)
    nN = len(nodes)
    roots = [i for i, (p, c) in enumerate(nodes) if p == -1]
    # cards needed at each node: read at this node or in the subtree (later)
    need = [set() for _ in range(nN)]
    for i in reversed(range(nN)):
        for ch in children[i]:
            need[i] |= need[ch]
        need[i].add(nodes[i][1])
    md = cp_model.CpModel()
    x = [md.NewIntVar(0, N - 1, f"x{c}") for c in range(N)]
    md.AddAllDifferent(x)
    s = [md.NewBoolVar(f"s{i}") for i in range(nN)]
    pos = [dict() for _ in range(nN)]
    tup = [(0, y, int(binv[y])) for y in range(N)] + [(1, y, int(sinv[y])) for y in range(N)]
    for r in roots:
        for c in need[r]:
            pos[r][c] = x[c]
    for i in range(nN):
        for ch in children[i]:
            for c in need[ch]:
                v = md.NewIntVar(0, N - 1, f"p{ch}_{c}")
                md.AddAllowedAssignments([s[i], pos[i][c], v], tup)
                pos[ch][c] = v
    if Q is not None:
        qs = qs_known
        allowed = [(1, qs)] + [(0, q) for q in Q if q != qs]
        for i in range(nN):
            md.AddAllowedAssignments([s[i], pos[i][nodes[i][1]]], allowed)
        inQ = None
    else:
        inQ = [md.NewBoolVar(f"q{y}") for y in range(N)]
        md.Add(sum(inQ) == 36)
        qsv = md.NewIntVar(0, N - 1, "qs")
        md.AddElement(qsv, inQ, 1)
        one = md.NewConstant(1)
        for i in range(nN):
            p = pos[i][nodes[i][1]]
            md.AddElement(p, inQ, one)
            md.Add(p == qsv).OnlyEnforceIf(s[i]); md.Add(p != qsv).OnlyEnforceIf(s[i].Not())
    for r in roots:
        md.Add(s[r] == 0)
    if no_double_space:
        for i in range(nN):
            for ch in children[i]:
                md.AddBoolOr([s[i].Not(), s[ch].Not()])
    if maxword:
        # at most maxword letters in a row: every window of maxword+1 symbols contains a space
        for path in paths:
            for k in range(len(path) - maxword):
                md.AddBoolOr([s[path[k + u]] for u in range(maxword + 1)])
    if strategy:
        md.AddDecisionStrategy(s, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)
        sv_fixed = True
    nb = 0
    for a, i0, b, j0, Lb in blocks:
        for k in range(Lb):
            if i0 + k < len(paths[a]) and j0 + k < len(paths[b]):
                na, nb_ = paths[a][i0 + k], paths[b][j0 + k]
                if na == nb_:
                    continue
                md.Add(pos[na][nodes[na][1]] == pos[nb_][nodes[nb_][1]])
                md.Add(s[na] == s[nb_]); nb += 1
    if hint is not None:
        for c in range(N):
            md.AddHint(x[c], int(hint[c]))
    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = tlimit
    sv.parameters.num_workers = workers
    sv.parameters.log_search_progress = log
    if strategy:
        sv.parameters.search_branching = cp_model.FIXED_SEARCH if workers == 1 else cp_model.AUTOMATIC_SEARCH
    t0 = time.time()
    st = sv.Solve(md)
    info = {"status": sv.StatusName(st), "time": time.time() - t0, "nodes": nN, "eq": nb,
            "vars": sum(len(p) for p in pos)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        info["x"] = np.array([sv.Value(v) for v in x])
        info["s"] = [[bool(sv.Value(s[i])) for i in path] for path in paths]
    return info


def testbed_case(rng, bname="rot1", sname="deal3fwd"):
    names, BS, INV = tables()
    pl = tbs.build_plaintexts()
    D0 = rng.permutation(N)
    q = np.arange(len(tbs.ALPHA_S), dtype=np.int64)  # convention: symbol of rank k read at position k
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist()
            for m in pl]
    x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
    return pl, msgs, INV[bname], INV[sname], q, x_true


if __name__ == "__main__":
    L = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    mode = sys.argv[3] if len(sys.argv) > 3 else "Qconnu"
    use_blocks = "blocs" in sys.argv
    strat = "strategie" in sys.argv
    tl = float(sys.argv[4]) if len(sys.argv) > 4 else 300
    rng = np.random.default_rng(int(sys.argv[5]) if len(sys.argv) > 5 else 0)
    pl, msgs, binv, sinv, q, x_true = testbed_case(rng)
    msgsL = [m[:L] for m in msgs]
    plL = [p[:L] for p in pl]
    from testkey import true_blocks
    blocks = [b for b in true_blocks(pl) if b[4] >= 8] if use_blocks else []
    if mode == "Qconnu":
        info = solve(msgsL, binv, sinv, Q=list(range(36)), qs_known=35, tlimit=tl, blocks=blocks,
                     maxword=14 if strat else 0, strategy=strat)
    else:
        info = solve(msgsL, binv, sinv, tlimit=tl, blocks=blocks)
    print(f"L={L} {mode} blocks={use_blocks}: {info['status']} in {info['time']:.0f} s; {info['nodes']} nodes, "
          f"{info['vars']} position variables, {info['eq']} block equalities")
    if "x" in info:
        # cards actually read in the prefixes
        seen = sorted(set(c for m in msgsL for c in m))
        ok = sum(int(info["x"][c] == x_true[c]) for c in seen)
        dec = sum(a == (ch == "_") for sp, p in zip(info["s"], plL) for a, ch in zip(sp, p))
        tot = sum(len(p) for p in plL)
        print(f"   correct starts {ok}/{len(seen)} cards read; correct decisions {dec}/{tot}")
