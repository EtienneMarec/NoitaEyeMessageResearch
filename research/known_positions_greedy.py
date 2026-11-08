"""Space decisions through greedy passes over time, known read positions (§39).

Pass: for t = 0, 1, 2, … and each message active at t, compare "letter" and "space" at t, the other
decisions being fixed. Score = value of the optimal Hungarian assignment over the prefixes [0, t + K] of all
messages (K = lookahead), with space consistency (read at q_space ⇔ space decision).
Passes are repeated (over the whole text) until stable. Validation on the testbed, (β, σ) known."""
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, N
from keyed_deck_attack2 import scoresT
from keyed_deck_robust import reads
from known_positions_attack import logphi_known
import testbed_spaces as tbs
from explore import xgak_encrypt


def eval_T(C, starts, lens, sp, binv, sinv, lp, qs, T):
    sc = scoresT(C, starts, lens, sp, binv, sinv, lp, True, T)
    rows, cols = linear_sum_assignment(-sc)
    x = np.empty(N, np.int64); x[rows] = cols
    r = reads(C, starts, lens, x, binv, sinv, sp)
    mask = np.zeros(len(C), bool)
    for m, a in enumerate(starts):
        mask[a:a + min(lens[m], T)] = True
    mism = int((((r == qs) != sp) & mask).sum())
    return float(sc[rows, cols].sum()) - 5.0 * mism, x


def greedy(C, starts, lens, binv, sinv, Q, qs, K=6, passes=4, sp=None, truth=None, log=True):
    lp = logphi_known(Q)
    L = len(C)
    sp = np.zeros(L, bool) if sp is None else sp.copy()
    tmax = int(lens.max())
    for p in range(passes):
        changes = 0
        for t in range(tmax):
            T = t + 1 + K if p == 0 else 10 ** 6
            for m, a in enumerate(starts):
                if t >= lens[m]:
                    continue
                g = a + t
                s0, _ = eval_T(C, starts, lens, sp, binv, sinv, lp, qs, T)
                sp[g] = ~sp[g]
                s1, _ = eval_T(C, starts, lens, sp, binv, sinv, lp, qs, T)
                if s1 > s0:
                    changes += 1
                else:
                    sp[g] = ~sp[g]
        s, x = eval_T(C, starts, lens, sp, binv, sinv, lp, qs, 10 ** 6)
        if log:
            msg = f"   pass {p}: {changes} changes, score {s:.0f}"
            if truth is not None:
                msg += f", correct decisions {int((sp == truth).sum())}/{L}"
            print(msg, flush=True)
        if changes == 0 and p > 0:
            break
    return sp, x, s


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(13)
    pl = tbs.build_plaintexts()
    alpha = tbs.ALPHA_S; q = np.arange(len(alpha), dtype=np.int64); Q = set(q.tolist()); qs = int(q[alpha.index("_")])
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk")):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        print(f"β={bname} σ={sname}")
        sp, x, s = greedy(C, starts, lens, inv[bname], inv[sname], Q, qs, truth=sp_true)
        print(f"   => correct deck {int((x == x_true).sum())}/83", flush=True)
