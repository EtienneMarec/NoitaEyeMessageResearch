"""PROGRESSIVE annealing on the reinsertion table: only the first L symbols of each message are used,
L increasing (5, 10, 15, ...), restarting from the best previous table.
Score: -log likelihood of a "Chinese restaurant" process (a position already read is
reused in proportion to its number of reads; a new position is expensive),
which rewards a q sequence concentrated on few positions.
"""
import sys
import time
import numpy as np
from numba import njit
from sa_reinsert import pack, replay, entropy, N


@njit(cache=True)
def replay_lim(flat, starts, F, qout, L):
    D = np.empty(N, np.int64); P = np.empty(N, np.int64)
    for m in range(starts.shape[0] - 1):
        for k in range(N):
            D[k] = k; P[k] = k
        a, b = starts[m], starts[m + 1]
        for i in range(a, b):
            qout[i] = -1
        for i in range(a + 1, min(b, a + L)):
            q = P[flat[i]]
            qout[i] = q
            c = D[q]; t = F[q]
            if t > q:
                for k in range(q, t):
                    D[k] = D[k + 1]; P[D[k]] = k
            elif t < q:
                for k in range(q, t, -1):
                    D[k] = D[k - 1]; P[D[k]] = k
            D[t] = c; P[c] = t


@njit(cache=True)
def crp_nll(qout, alpha):
    cnt = np.zeros(N, np.float64)
    n = 0.0; nll = 0.0
    for v in qout:
        if v < 0:
            continue
        if cnt[v] > 0:
            nll -= np.log(cnt[v] / (n + alpha))
        else:
            nll -= np.log(alpha / (n + alpha) / N)
        cnt[v] += 1; n += 1
    return nll


@njit(cache=True)
def anneal_lim(flat, starts, F, L, iters, T0, T1, alpha, seed):
    np.random.seed(seed)
    q = np.empty(flat.shape[0], np.int64)
    replay_lim(flat, starts, F, q, L)
    cur = crp_nll(q, alpha); best = cur; bestF = F.copy()
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        j = q[np.random.randint(0, q.shape[0])]
        if j < 0:
            continue
        old = F[j]
        F[j] = np.random.randint(0, N)
        replay_lim(flat, starts, F, q, L)
        new = crp_nll(q, alpha)
        if new <= cur or np.random.random() < np.exp((cur - new) / T):
            cur = new
            if cur < best:
                best = cur; bestF[:] = F
        else:
            F[j] = old
    replay_lim(flat, starts, bestF, q, L)
    return bestF, best


def progressive(msgs, step=5, iters=20000, T0=3.0, T1=0.05, alpha=2.0, seed=0, verbose=True, F_true=None, reads=None):
    flat, starts = pack(msgs)
    Lmax = max(len(m) for m in msgs)
    F = np.random.default_rng(seed).integers(0, N, N).astype(np.int64)
    q = np.empty(flat.shape[0], np.int64)
    for L in range(step, Lmax + step, step):
        F, s = anneal_lim(flat, starts, F, L, iters, T0, T1, alpha, seed + L)
        if verbose and (L % 20 == 0 or L >= Lmax):
            replay(flat, starts, F, q)
            msg = f"  L={L:3d}  nll={s:8.1f}  total entropy {entropy(q):.3f}"
            if F_true is not None:
                msg += f"  exact destinations {np.mean(F[reads] == F_true[reads]):.0%}"
            print(msg, flush=True)
    replay(flat, starts, F, q)
    return F, entropy(q)
