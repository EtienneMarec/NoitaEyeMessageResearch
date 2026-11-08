"""Search for spaces through the block-cycle score (space model, β and σ known) (§37).

Columns = classes of positions carrying the same plaintext letter (block alignments). For two cards
c1, c2 both read in two columns k1, k2 (occurrences o1, o2 in k1; o3, o4 in k2), the equations
x(c2) = M(o1→o2) x(c1) and x(c1) = M(o4→o3) x(c2), with M(o→o') = F_{o'}⁻¹ F_o, impose
x(c1) ∈ Fix(P), P = M(o4→o3)·M(o1→o2). A card read twice in the same column gives a short cycle.
With the right decisions, all cycles of c1 share the fixed point x(c1).
Score(decisions) = Σ_c max_y #{cycles of c having y as a fixed point} (+ a prior on spaces).
Decisions tied per column (same plaintext letter ⇒ same decision). Annealing: flip one free decision.
Validation: testbed with spaces, true blocks (the 8 longest, the order of magnitude of the eyes)."""
import sys
import math
import numpy as np
from numba import njit
from keyed_deck_attack import tables, flatten, N
from testkey import true_blocks
import testbed_spaces as tbs
from explore import xgak_encrypt


def build_columns(starts, blocks, trim=2):
    par = {}

    def f(x):
        while par.setdefault(x, x) != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, i, b, j, L in blocks:
        for k in range(trim, L - trim):
            par[f(int(starts[a] + i + k))] = f(int(starts[b] + j + k))
    cols = {}
    for g in list(par):
        cols.setdefault(f(g), []).append(g)
    return [sorted(v) for v in cols.values() if len(v) >= 2]


def build_cycles(C, cols):
    """list of cycles (o1, o2, o3, o4): c1 read at o1 (col k1) and o3 (col k2), c2 at o2 (k1) and o4 (k2);
    plus short cycles (o1, o2, -1, -1): same card read at o1 and o2 of one column."""
    where = {}
    for ki, col in enumerate(cols):
        for o in col:
            where.setdefault(int(C[o]), []).append((ki, o))
    cyc = []
    for ki, col in enumerate(cols):
        for a in range(len(col)):
            for b in range(len(col)):
                if a == b:
                    continue
                o1, o2 = col[a], col[b]
                c1, c2 = int(C[o1]), int(C[o2])
                if c1 == c2:
                    if a < b:
                        cyc.append((c1, o1, o2, -1, -1))
                    continue
                for kj, o3 in where[c1]:
                    if kj == ki:
                        continue
                    for kk, o4 in where[c2]:
                        if kk == kj:
                            cyc.append((c1, o1, o2, o3, o4))
    return np.array(cyc, np.int64)


@njit(cache=True)
def all_F(L, starts, lens, sp, binv, sinv):
    F = np.empty((L, N), np.int64)
    cur = np.empty(N, np.int64)
    for m in range(starts.shape[0]):
        for y in range(N):
            cur[y] = y
        for t in range(starts[m], starts[m] + lens[m]):
            F[t] = cur
            S = sinv if sp[t] else binv
            for y in range(N):
                cur[y] = S[cur[y]]
    return F


@njit(cache=True)
def score(F, cyc):
    acc = np.zeros((N, N), np.int64)       # acc[c, y] = number of cycles of c having y as a fixed point
    inv2 = np.empty(N, np.int64); inv4 = np.empty(N, np.int64)
    for i in range(cyc.shape[0]):
        c1, o1, o2, o3, o4 = cyc[i, 0], cyc[i, 1], cyc[i, 2], cyc[i, 3], cyc[i, 4]
        for y in range(N):
            inv2[F[o2, y]] = y
        if o3 < 0:
            for y in range(N):
                if inv2[F[o1, y]] == y:
                    acc[c1, y] += 1
        else:
            for y in range(N):
                inv4[F[o3, y]] = y        # M(o4→o3) = F_o3⁻¹ F_o4
            for y in range(N):
                z = inv2[F[o1, y]]       # x(c2) = F_o2⁻¹ F_o1 y
                w = inv4[F[o4, z]]       # x(c1) = F_o3⁻¹ F_o4 z
                if w == y:
                    acc[c1, y] += 1
    s = 0
    for c in range(N):
        best = 0
        for y in range(N):
            if acc[c, y] > best:
                best = acc[c, y]
        s += best
    return s


def anneal(C, starts, lens, cols, cyc, binv, sinv, sp0, free, groups, iters, rng, t0=3.0, t1=0.1, truth=None):
    sp = sp0.copy()
    F = all_F(len(C), starts, lens, sp, binv, sinv)
    cur = score(F, cyc)
    best = cur; bsp = sp.copy()
    for it in range(iters):
        temp = t0 * (t1 / t0) ** (it / iters)
        gi = groups[rng.integers(len(groups))]
        sp[gi] = ~sp[gi]
        F = all_F(len(C), starts, lens, sp, binv, sinv)
        new = score(F, cyc)
        if new >= cur or rng.random() < math.exp((new - cur) / temp):
            cur = new
            if cur > best:
                best = cur; bsp = sp.copy()
        else:
            sp[gi] = ~sp[gi]
        if truth is not None and (it + 1) % (iters // 10) == 0:
            print(f"   it {it + 1}: score {cur} (best {best}), correct decisions {int((sp == truth).sum())}/{len(sp)}", flush=True)
    return bsp, best


def decision_groups(L, cols):
    """groups of linked positions (same column); each position outside a column forms its own group"""
    g = {}
    for col in cols:
        for o in col:
            g[o] = col
    out = []
    seen = set()
    for t in range(L):
        if t in seen:
            continue
        grp = g.get(t, [t])
        seen.update(grp)
        out.append(np.array(grp, np.int64))
    return out


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    names, BS, inv = tables()
    rng = np.random.default_rng(5)
    pl = tbs.build_plaintexts()
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    blocks = sorted(true_blocks(pl), key=lambda b: -b[4])[:8]
    cols = build_columns(starts, blocks)
    cyc = build_cycles(C, cols)
    groups = decision_groups(len(C), cols)
    Ft = all_F(len(C), starts, lens, sp_true, inv[bname], inv[sname])
    sr = score(all_F(len(C), starts, lens, rng.random(len(C)) < 0.18, inv[bname], inv[sname]), cyc)
    print(f"{len(cols)} columns, {len(cyc)} cycles; true score {score(Ft, cyc)}, random decisions {sr}")
    sp0 = np.zeros(len(C), bool)
    for gi in groups:
        if rng.random() < 0.18:
            sp0[gi] = True
    bsp, best = anneal(C, starts, lens, cols, cyc, inv[bname], inv[sname], sp0, None, groups, iters, rng, truth=sp_true)
    print(f"best score {best}; correct decisions {int((bsp == sp_true).sum())}/{len(sp_true)}")
