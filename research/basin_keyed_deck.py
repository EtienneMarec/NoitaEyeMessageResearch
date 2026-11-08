"""Basin of attraction of the keyed-starting-deck attack (space decisions recomputed) (§36).

Start: deck x with a fraction f of correct start positions (the others shuffled at random), correct
q_space. We iterate keyed_deck_attack (decoding → q_space → frequencies → Hungarian assignment), and measure
the number of correct positions at the end. 5 trials per fraction, two (β, σ) pairs."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, decode, scores, N
import testbed_spaces as tbs
from explore import xgak_encrypt


def em_from(C, starts, lens, x, qs, binv, sinv, iters=40):
    for it in range(iters):
        r, sp = decode(C, starts, lens, x, binv, sinv, qs, True)
        cnt = np.bincount(r[r >= 0], minlength=N).astype(float)
        qs = int(np.argmax(cnt))
        r, sp = decode(C, starts, lens, x, binv, sinv, qs, True)
        cnt = np.bincount(r[r >= 0], minlength=N).astype(float)
        logphi = np.log((cnt + 0.5) / (cnt.sum() + 0.5 * N))
        sc = scores(C, starts, lens, sp, binv, sinv, logphi, True)
        rows, cols = linear_sum_assignment(-sc)
        xn = np.empty(N, np.int64); xn[rows] = cols
        if (xn == x).all():
            break
        x = xn
    return x


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(2)
    pl = tbs.build_plaintexts()
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk")):
        D0 = rng.permutation(N)
        q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        qs = int(q[tbs.ALPHA_S.index("_")])
        for f in (0.3, 0.5, 0.7, 0.85):
            res = []
            for _ in range(5):
                x = x_true.copy()
                k = int(round((1 - f) * N))
                idx = rng.choice(N, k, replace=False)
                x[idx] = x[idx][rng.permutation(k)]
                xf = em_from(C, starts, lens, x, qs, inv[bname], inv[sname])
                res.append(int((xf == x_true).sum()))
            print(f"β={bname:10s} σ={sname:9s} start {int(f * 100)}% correct -> correct positions at the end: {res}", flush=True)
