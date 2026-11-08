"""How many space positions must be known to recover the starting deck? (§33)

Space model, known natural shuffles (β, σ), keyed starting deck D0. The alternating algorithm
(EM + Hungarian assignment) is given the TRUE space decisions on the first T symbols of each message
(what a probable word would provide: the word structure), and only those prefixes are decrypted.
Measure: number of start positions recovered (out of 83) and success rate over several starts,
for T = 15, 20, 30, 45, 70, 100 and several (β, σ) pairs."""
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, N
from keyed_deck_attack2 import scoresT
import testbed_spaces as tbs
from explore import xgak_encrypt


def em_oracle(C, starts, lens, sp, binv, sinv, T, x, iters=40):
    for it in range(iters):
        r = np.full(len(C), -1, np.int64)
        for m in range(len(starts)):
            pos = x.copy()
            for t in range(starts[m], starts[m] + min(lens[m], T)):
                r[t] = pos[C[t]]
                pos = (sinv if sp[t] else binv)[pos]
        cnt = np.bincount(r[r >= 0], minlength=N).astype(float)
        logphi = np.log((cnt + 0.5) / (cnt.sum() + 0.5 * N))
        sc = scoresT(C, starts, lens, sp, binv, sinv, logphi, True, T)
        rows, cols = linear_sum_assignment(-sc)
        xn = np.empty(N, np.int64); xn[rows] = cols
        if (xn == x).all():
            break
        x = xn
    return x


if __name__ == "__main__":
    restarts = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    names, BS, inv = tables()
    rng = np.random.default_rng(1)
    pl = tbs.build_plaintexts()
    sp = np.array([ch == "_" for m in pl for ch in m])
    print("β           σ          T    best (correct positions/83)      full successes / starts")
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk"), ("deal2fwd", "rot5")):
        D0 = rng.permutation(N)
        q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        for T in (15, 20, 30, 45, 70, 140):
            best = 0; full = 0
            for k in range(restarts):
                x = em_oracle(C, starts, lens, sp, inv[bname], inv[sname], T, rng.permutation(N).astype(np.int64))
                ok = int((x == x_true).sum()); best = max(best, ok); full += ok == 83
            print(f"{bname:10s}  {sname:9s} {T:3d}   {best:3d}                              {full}/{restarts}", flush=True)
