"""Propagation of shared-block equations (space model, β and σ known) (§36).

Two aligned positions of a shared text block (message X at time t, message Y at time t') read the same deck
position: F_X,t(x(c_X)) = F_Y,t'(x(c_Y)), where F = composition of shuffles given the space decisions of the
prefix. If the decisions are known, each pair gives x(c_Y) = F_Y,t'⁻¹ F_X,t (x(c_X)).
We propagate these equations (connected components; one seed with 83 values per component) and measure:
  - the number of linked cards and of components;
  - the number of consistent seed values (injectivity, no contradiction) per component;
  - with WRONG decisions (some spaces moved), how often contradictions appear.
Testbed with spaces, true blocks (testkey.true_blocks), known key."""
import numpy as np
from keyed_deck_attack import tables, flatten, N
from testkey import true_blocks
import testbed_spaces as tbs
from explore import xgak_encrypt


def prefix_maps(msgs_len, sp, binv, sinv, starts):
    """F[g] = composition at global time g (start position -> current position), per message"""
    F = {}
    for m, a in enumerate(starts):
        cur = np.arange(N)
        for t in range(msgs_len[m]):
            F[a + t] = cur.copy()
            cur = (sinv if sp[a + t] else binv)[cur]
    return F


def edges(C, starts, lens, blocks, F):
    E = []
    for a, i, b, j, L in blocks:
        for k in range(L):
            ga, gb = starts[a] + i + k, starts[b] + j + k
            Fa, Fb = F[ga], F[gb]
            Fbinv = np.empty(N, np.int64); Fbinv[Fb] = np.arange(N)
            M = Fbinv[Fa]                       # x(c_Y) = M[x(c_X)]
            E.append((C[ga], C[gb], M))
    return E


def solve(E):
    adj = {}
    for u, v, M in E:
        Minv = np.empty(N, np.int64); Minv[M] = np.arange(N)
        adj.setdefault(u, []).append((v, M)); adj.setdefault(v, []).append((u, Minv))
    seen = set(); comps = []
    for s in adj:
        if s in seen:
            continue
        comp = [s]; seen.add(s); k = 0
        while k < len(comp):
            for v, _ in adj[comp[k]]:
                if v not in seen:
                    seen.add(v); comp.append(v)
            k += 1
        good = []
        for x0 in range(N):
            val = {s: x0}; ok = True; stack = [s]
            while stack and ok:
                u = stack.pop()
                for v, M in adj[u]:
                    w = int(M[val[u]])
                    if v in val:
                        if val[v] != w:
                            ok = False; break
                    else:
                        val[v] = w; stack.append(v)
            if ok and len(set(val.values())) == len(val):
                good.append(x0)
        comps.append((len(comp), len(good)))
    return comps


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(4)
    pl = tbs.build_plaintexts()
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    blocks = [b for b in true_blocks(pl) if b[4] >= 8]
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    for label, sp in (("correct decisions", sp_true),
                      ("1 space moved per message", None), ("random decisions (18%)", "rand")):
        if sp is None:
            sp = sp_true.copy()
            for m in range(len(starts)):
                idx = [g for g in range(starts[m] + 1, starts[m] + lens[m] - 1) if sp[g]]
                g = idx[len(idx) // 3]
                sp[g] = False; sp[g + 1] = True
        elif isinstance(sp, str):
            sp = rng.random(len(C)) < 0.18
        F = prefix_maps(lens, sp, inv[bname], inv[sname], starts)
        comps = solve(edges(C, starts, lens, blocks, F))
        cards = sum(c for c, g in comps)
        dead = sum(1 for c, g in comps if g == 0)
        print(f"{label:30s}: {len(blocks)} blocks, {cards} cards linked in {len(comps)} components; "
              f"components with no solution {dead}; consistent seeds (median) {np.median([g for c, g in comps]):.0f}", flush=True)
