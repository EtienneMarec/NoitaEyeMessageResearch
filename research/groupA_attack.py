"""Attack on group A (E1, W1, E2) through block consistency, space model, given natural (β, σ) (§37).

Unknowns: space/letter decisions of the positions that affect consistency. Positions aligned in the
blocks carry the same letter: their decisions are tied. The prefix shared by the three messages does not change
consistency (common conjugation): it is fixed to "letter".
Score: number of satisfied block equations, x(c_Y) = F_Y⁻¹ F_X x(c_X), with an assignment x obtained by
propagation from the most connected card (83 seeds), followed by majority-vote passes (a local error
stays local). Annealing over the free decisions. Then, if all equations are satisfied,
x (the starting deck) is recovered and checked.
Validation: group A of the testbed with spaces (true blocks, messages 0..2), β, σ and q_space known."""
import sys
import math
import numpy as np
from numba import njit
from keyed_deck_attack import tables, flatten, N
from testkey import true_blocks
from cycle_score_sa import build_columns, decision_groups, all_F
import testbed_spaces as tbs
from explore import xgak_encrypt


def edge_arrays(C, starts, blocks, trim=0):
    ea, eb = [], []
    for a, i, b, j, L in blocks:
        for k in range(trim, L - trim):
            ea.append(starts[a] + i + k); eb.append(starts[b] + j + k)
    return np.array(ea, np.int64), np.array(eb, np.int64)


@njit(cache=True)
def satisfied(C, F, ea, eb, passes):
    """best number of satisfied equations (seeds × votes)"""
    E = ea.shape[0]
    # maps: x(c_b) = Finv_b[F_a[x(c_a)]]
    deg = np.zeros(N, np.int64)
    for e in range(E):
        deg[C[ea[e]]] += 1; deg[C[eb[e]]] += 1
    root = np.argmax(deg)
    Finv = np.empty((F.shape[0], N), np.int64)
    best = -1
    val = np.full(N, -1, np.int64)
    votes = np.zeros((N, N), np.int64)
    for g in range(F.shape[0]):
        for y in range(N):
            Finv[g, F[g, y]] = y
    for x0 in range(N):
        val[:] = -1
        val[root] = x0
        # simple propagation until stable
        changed = True
        while changed:
            changed = False
            for e in range(E):
                u = C[ea[e]]; v = C[eb[e]]
                if val[u] >= 0 and val[v] < 0:
                    val[v] = Finv[eb[e], F[ea[e], val[u]]]; changed = True
                elif val[v] >= 0 and val[u] < 0:
                    val[u] = Finv[ea[e], F[eb[e], val[v]]]; changed = True
        # majority votes
        for p in range(passes):
            votes[:, :] = 0
            for e in range(E):
                u = C[ea[e]]; v = C[eb[e]]
                if val[u] >= 0:
                    votes[v, Finv[eb[e], F[ea[e], val[u]]]] += 1
                if val[v] >= 0:
                    votes[u, Finv[ea[e], F[eb[e], val[v]]]] += 1
            for c in range(N):
                if c == root:
                    continue
                m = 0; arg = -1
                for y in range(N):
                    if votes[c, y] > m:
                        m = votes[c, y]; arg = y
                if arg >= 0:
                    val[c] = arg
        s = 0
        for e in range(E):
            u = C[ea[e]]; v = C[eb[e]]
            if val[u] >= 0 and val[v] >= 0 and Finv[eb[e], F[ea[e], val[u]]] == val[v]:
                s += 1
        if s > best:
            best = s
    return best


def anneal(C, starts, lens, ea, eb, groups, sp, binv, sinv, iters, rng, t0=4.0, t1=0.1, passes=2, truth=None, log=10):
    F = all_F(len(C), starts, lens, sp, binv, sinv)
    cur = satisfied(C, F, ea, eb, passes)
    best, bsp = cur, sp.copy()
    for it in range(iters):
        temp = t0 * (t1 / t0) ** (it / iters)
        gi = groups[rng.integers(len(groups))]
        sp[gi] = ~sp[gi]
        F = all_F(len(C), starts, lens, sp, binv, sinv)
        new = satisfied(C, F, ea, eb, passes)
        if new >= cur or rng.random() < math.exp((new - cur) / temp):
            cur = new
            if cur > best:
                best, bsp = cur, sp.copy()
        else:
            sp[gi] = ~sp[gi]
        if truth is not None and log and (it + 1) % (iters // log) == 0:
            print(f"   it {it + 1}: score {cur}/{len(ea)} (best {best}), correct free decisions "
                  f"{sum(int(sp[g[0]] == truth[g[0]]) for g in groups)}/{len(groups)}", flush=True)
        if best == len(ea):
            break
    return bsp, best


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    names, BS, inv = tables()
    rng = np.random.default_rng(6)
    pl = tbs.build_plaintexts()[:3]
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    # non-trivial blocks of group A (shifted or within a message), length >= 8
    blocks = [b for b in true_blocks(pl) if b[4] >= 8 and not (b[1] == b[3] and b[0] != b[2])]
    ea, eb = edge_arrays(C, starts, blocks)
    cols = build_columns(starts, blocks, trim=0)
    groups = decision_groups(len(C), cols)
    # shared prefix (1..21 + digit): fixed to "letter", not searched
    pref = 22
    groups = [g for g in groups if not all((t - starts[np.searchsorted(starts, t, 'right') - 1]) < pref for t in g)]
    # positions beyond the last block of each message: no effect, removed
    last = {}
    for a, i, b, j, L in blocks:
        last[a] = max(last.get(a, 0), i + L); last[b] = max(last.get(b, 0), j + L)
    groups = [g for g in groups if any((t - starts[m]) < last.get(m, 0) for t in g for m in [np.searchsorted(starts, t, 'right') - 1])]
    Ft = all_F(len(C), starts, lens, sp_true, inv[bname], inv[sname])
    print(f"{len(blocks)} blocks, {len(ea)} equations, {len(groups)} free decision groups; "
          f"true score {satisfied(C, Ft, ea, eb, 2)}/{len(ea)}")
    sp0 = sp_true.copy()
    for g in groups:
        sp0[g] = rng.random() < 0.18
    bsp, best = anneal(C, starts, lens, ea, eb, groups, sp0, inv[bname], inv[sname], iters, rng, truth=sp_true)
    print(f"best score {best}/{len(ea)}; correct free decisions {sum(int(bsp[g[0]] == sp_true[g[0]]) for g in groups)}/{len(groups)}")
