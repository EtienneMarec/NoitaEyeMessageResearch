"""Annealing over the starting deck, time-progressive, "known positions" convention + frequencies (§44).

known_positions_unigram.py shows that the truth is a very sharp optimum (score -3,102 versus -6,500 at best for
EM), so the lock is the search. Here: simulated annealing over x (start positions of the cards), move
= swap the starts of two cards; score = Σ log φ(reads) with robust decisions (small beam);
only the first T symbols of each message count, T increasing (at the start, few spaces: the reads
depend almost only on x). EM polishing (Hungarian) at each stage.
Usage: python known_positions_sa_x.py [seed] [iterations per stage]"""
import sys
import math
import numpy as np
from numba import njit
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, scores, N
from keyed_deck_robust import decide, reads
from known_positions_unigram import logphi_unigram
import testbed_spaces as tbs
from explore import xgak_encrypt
from moderate_space_curriculum import letter_acc

STEPS = (8, 12, 16, 20, 25, 30, 40, 50, 70, 100, 10 ** 6)


def score(C, st, ln, x, binv, sinv, qs, lp, lpl, Bw):
    sp = decide(C, st, ln, x, binv, sinv, qs, lpl, Bw)
    r = reads(C, st, ln, x, binv, sinv, sp)
    return float(lp[r].sum()), sp


def polish(C, st, ln, x, binv, sinv, qs, lp, lpl, iters=10):
    for _ in range(iters):
        sp = decide(C, st, ln, x, binv, sinv, qs, lpl, 16)
        sc = scores(C, st, ln, sp, binv, sinv, lp, True)
        rows, cols = linear_sum_assignment(-sc)
        xn = np.empty(N, np.int64); xn[rows] = cols
        if (xn == x).all():
            break
        x = xn
    return x


def anneal(msgs, binv, sinv, qs, lp, rng, iters, x_true=None, log=print):
    lpl = lp.copy(); lpl[qs] = np.log(1e-6); lpl[:qs] -= np.log(np.exp(lp[:qs]).sum())
    x = rng.permutation(N).astype(np.int64)
    for T in STEPS:
        C, st, ln = flatten([m[:T] for m in msgs])
        cur, _ = score(C, st, ln, x, binv, sinv, qs, lp, lpl, 4)
        best, bx = cur, x.copy()
        t0, t1 = 3.0, 0.05
        for k in range(iters):
            temp = t0 * (t1 / t0) ** (k / iters)
            a, b = rng.choice(N, 2, replace=False)
            x[a], x[b] = x[b], x[a]
            new, _ = score(C, st, ln, x, binv, sinv, qs, lp, lpl, 4)
            if new >= cur or rng.random() < math.exp((new - cur) / temp):
                cur = new
                if cur > best:
                    best, bx = cur, x.copy()
            else:
                x[a], x[b] = x[b], x[a]
        x = polish(C, st, ln, bx.copy(), binv, sinv, qs, lp, lpl)
        s, _ = score(C, st, ln, x, binv, sinv, qs, lp, lpl, 16)
        if s < best:
            x = bx
        ok = int((x == x_true).sum()) if x_true is not None else -1
        seen = len(set(c for m in msgs for c in m[:T]))
        log(f"   T={min(T, max(map(len, msgs))):4d}: score {max(s, best):.0f}, correct starts {ok}/83 ({seen} cards seen)")
    return x


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    pl = tbs.build_plaintexts()
    alpha = tbs.ALPHA_S
    q = np.arange(len(alpha), dtype=np.int64); qs = alpha.index("_")
    lp = logphi_unigram(alpha, tbs.english_with_spaces()[:1_000_000])
    plain = "".join(pl)
    for bname, sname in (("outshuffle", "milk"), ("rot1", "deal3fwd")):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        print(f"β={bname} σ={sname}", flush=True)
        x = anneal(msgs, inv[bname], inv[sname], qs, lp, rng, iters, x_true, log=lambda s: print(s, flush=True))
        C, st, ln = flatten(msgs)
        lpl = lp.copy(); lpl[qs] = np.log(1e-6); lpl[:qs] -= np.log(np.exp(lp[:qs]).sum())
        sp = decide(C, st, ln, x, inv[bname], inv[sname], qs, lpl, 16)
        print(f"   correct letters {letter_acc(reads(C, st, ln, x, inv[bname], inv[sname], sp), plain):.2f}", flush=True)
