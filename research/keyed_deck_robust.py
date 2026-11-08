"""Attack "keyed starting deck" with ROBUST space decisions (§36).

Instead of imposing "space iff the card read is at q_space" (a single misplaced card derails the whole
message), we choose, for each message, the sequence of space/letter decisions that maximises the likelihood
of the reads, with a small beam:
  letter: log(1 - p_sp) + log φ_letters(r) + (log ε if r = q_space)
  space : log p_sp + (0 if r = q_space else log ε)
then the deck x is updated by Hungarian assignment (keyed_deck_attack.scores), and we repeat.
Test: basin of attraction (start with a fraction f of correct positions)."""
import sys
import math
import numpy as np
from numba import njit
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, scores, decode, N
import testbed_spaces as tbs
from explore import xgak_encrypt

PESP = 0.18
EPS = 1e-4


@njit(cache=True)
def decide(C, starts, lens, x, binv, sinv, qs, logphi, Bw):
    L = C.shape[0]
    out = np.zeros(L, np.bool_)
    lpe = math.log(PESP); lpl = math.log(1 - PESP); leps = math.log(EPS)
    for m in range(starts.shape[0]):
        a, e = starts[m], starts[m] + lens[m]
        n = e - a
        F = np.zeros((Bw, N), np.int64); SC = np.zeros(Bw); D = np.zeros((Bw, n), np.bool_)
        for y in range(N):
            F[0, y] = y
        nb = 1
        cF = np.zeros((2 * Bw, N), np.int64); cS = np.zeros(2 * Bw); cD = np.zeros((2 * Bw, n), np.bool_)
        for t in range(a, e):
            k = 0
            for b in range(nb):
                r = F[b, x[C[t]]]
                # letter
                s = SC[b] + lpl + logphi[r] + (leps if r == qs else 0.0)
                cS[k] = s; cD[k] = D[b]; cD[k, t - a] = False
                for y in range(N):
                    cF[k, y] = binv[F[b, y]]
                k += 1
                # space
                s = SC[b] + lpe + (0.0 if r == qs else leps)
                cS[k] = s; cD[k] = D[b]; cD[k, t - a] = True
                for y in range(N):
                    cF[k, y] = sinv[F[b, y]]
                k += 1
            order = np.argsort(-cS[:k])
            nb = min(Bw, k)
            for i in range(nb):
                j = order[i]
                F[i] = cF[j]; SC[i] = cS[j]; D[i] = cD[j]
        for u in range(n):
            out[a + u] = D[0, u]
    return out


@njit(cache=True)
def reads(C, starts, lens, x, binv, sinv, sp):
    r = np.empty(C.shape[0], np.int64)
    pos = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
    for m in range(starts.shape[0]):
        pos[:] = x
        for t in range(starts[m], starts[m] + lens[m]):
            r[t] = pos[C[t]]
            S = sinv if sp[t] else binv
            for y in range(N):
                tmp[y] = S[pos[y]]
            pos[:] = tmp
    return r


def robust_em(C, starts, lens, x, qs, binv, sinv, iters=30, Bw=16, sp=None):
    for it in range(iters):
        if sp is None:
            _, sp = decode(C, starts, lens, x, binv, sinv, qs, True)
        r = reads(C, starts, lens, x, binv, sinv, sp)
        cnt = np.bincount(r[~sp], minlength=N).astype(float)
        cnt[qs] = 0.0
        logphi = np.log((cnt + 0.5) / (cnt.sum() + 0.5 * N))
        sp = decide(C, starts, lens, x, binv, sinv, qs, logphi, Bw)
        r = reads(C, starts, lens, x, binv, sinv, sp)
        cnt = np.bincount(r, minlength=N).astype(float)
        logphi2 = np.log((cnt + 0.5) / (cnt.sum() + 0.5 * N))
        sc = scores(C, starts, lens, sp, binv, sinv, logphi2, True)
        rows, cols = linear_sum_assignment(-sc)
        xn = np.empty(N, np.int64); xn[rows] = cols
        if (xn == x).all():
            break
        x = xn
    return x, sp


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(2)
    pl = tbs.build_plaintexts()
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk")):
        D0 = rng.permutation(N)
        q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        qs = int(q[tbs.ALPHA_S.index("_")])
        for f in (1.0, 0.95, 0.85, 0.7, 0.5):
            res = []
            for _ in range(4):
                x = x_true.copy()
                k = int(round((1 - f) * N))
                idx = rng.choice(N, k, replace=False)
                x[idx] = x[idx][rng.permutation(k)]
                xf, sp = robust_em(C, starts, lens, x, qs, inv[bname], inv[sname])
                res.append((int((xf == x_true).sum()), int((sp == sp_true).sum())))
            print(f"β={bname:10s} σ={sname:9s} start {int(f * 100):2d}% -> (correct positions, correct decisions/{len(sp_true)}): {res}", flush=True)
