"""Annealing over the space decisions when the read positions are known (§39).

With known positions (convention "the letter of rank k is read at position k") and correct decisions, a single
Hungarian assignment recovers the starting deck (83/83). So we search the decisions: score(decisions) =
value of the optimal assignment Σ_c log φ(F_t(x_c)) (φ uniform over the known positions, ε elsewhere),
and the read at q_space must exactly match the space decisions (penalty otherwise).
Moves: flip a decision, or shift a space by one position.
Validation on the testbed with spaces, (β, σ) known."""
import sys
import math
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, scores, N
from keyed_deck_robust import reads
from known_positions_attack import logphi_known
import testbed_spaces as tbs
from explore import xgak_encrypt


def evaluate(C, starts, lens, sp, binv, sinv, lp, qs):
    sc = scores(C, starts, lens, sp, binv, sinv, lp, True)
    rows, cols = linear_sum_assignment(-sc)
    x = np.empty(N, np.int64); x[rows] = cols
    r = reads(C, starts, lens, x, binv, sinv, sp)
    # space consistency: read at qs <=> space decision
    mism = int(((r == qs) != sp).sum())
    return float(sc[rows, cols].sum()) - 5.0 * mism, x


def anneal(C, starts, lens, binv, sinv, Q, qs, iters, rng, sp=None, t0=20.0, t1=0.5, truth=None):
    lp = logphi_known(Q)
    L = len(C)
    if sp is None:
        sp = np.zeros(L, bool)
    cur, x = evaluate(C, starts, lens, sp, binv, sinv, lp, qs)
    best, bsp, bx = cur, sp.copy(), x
    for it in range(iters):
        temp = t0 * (t1 / t0) ** (it / iters)
        g = int(rng.integers(L))
        if rng.random() < 0.5 or not sp[g]:
            moves = [g]
        else:
            h = g + (1 if rng.random() < 0.5 else -1)
            moves = [g, h] if 0 <= h < L else [g]
        for k in moves:
            sp[k] = ~sp[k]
        new, x = evaluate(C, starts, lens, sp, binv, sinv, lp, qs)
        if new >= cur or rng.random() < math.exp((new - cur) / temp):
            cur = new
            if cur > best:
                best, bsp, bx = cur, sp.copy(), x
        else:
            for k in moves:
                sp[k] = ~sp[k]
        if truth is not None and (it + 1) % (iters // 10) == 0:
            print(f"   it {it + 1}: score {cur:.0f} (best {best:.0f}), correct decisions {int((sp == truth).sum())}/{L}", flush=True)
    return bsp, bx, best


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    names, BS, inv = tables()
    rng = np.random.default_rng(12)
    pl = tbs.build_plaintexts()
    alpha = tbs.ALPHA_S; q = np.arange(len(alpha), dtype=np.int64); Q = set(q.tolist()); qs = int(q[alpha.index("_")])
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
    lp = logphi_known(Q)
    st, _ = evaluate(C, starts, lens, sp_true, inv[bname], inv[sname], lp, qs)
    s0, _ = evaluate(C, starts, lens, np.zeros(len(C), bool), inv[bname], inv[sname], lp, qs)
    print(f"true score {st:.0f}; all letters {s0:.0f}")
    bsp, bx, best = anneal(C, starts, lens, inv[bname], inv[sname], Q, qs, iters, rng, truth=sp_true)
    print(f"best {best:.0f}; correct decisions {int((bsp == sp_true).sum())}/{len(C)}; correct deck {int((bx == x_true).sum())}/83")
