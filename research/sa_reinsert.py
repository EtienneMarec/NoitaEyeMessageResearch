"""Simulated annealing on the reinsertion table f (mechanism of §8: read at q, reinsertion at f(q),
sorted initial deck, no base shuffle, first symbol outside the deck).

Score to minimise: entropy (bits) of the sequence of read positions q, over all messages.
Good table: only ~41 read positions -> low entropy. Bad one: ~83 positions.
Only the entries of f for positions actually read matter.
"""
import sys
import time
import numpy as np
from numba import njit

N = 83


@njit(cache=True)
def replay(flat, starts, F, qout):
    """Replays all messages (concatenated in flat, starts in starts); fills qout."""
    D = np.empty(N, np.int64)
    P = np.empty(N, np.int64)
    nm = starts.shape[0] - 1
    for m in range(nm):
        for k in range(N):
            D[k] = k; P[k] = k
        a, b = starts[m], starts[m + 1]
        qout[a] = -1                              # first symbol outside the deck
        for i in range(a + 1, b):
            q = P[flat[i]]
            qout[i] = q
            c = D[q]
            t = F[q]
            if t > q:
                for k in range(q, t):
                    D[k] = D[k + 1]; P[D[k]] = k
            elif t < q:
                for k in range(q, t, -1):
                    D[k] = D[k - 1]; P[D[k]] = k
            D[t] = c; P[c] = t


@njit(cache=True)
def entropy(qout):
    cnt = np.zeros(N, np.float64)
    tot = 0.0
    for v in qout:
        if v >= 0:
            cnt[v] += 1; tot += 1
    h = 0.0
    for k in range(N):
        if cnt[k] > 0:
            p = cnt[k] / tot
            h -= p * np.log2(p)
    return h


@njit(cache=True)
def anneal(flat, starts, F0, iters, T0, T1, seed):
    np.random.seed(seed)
    F = F0.copy()
    q = np.empty(flat.shape[0], np.int64)
    replay(flat, starts, F, q)
    cur = entropy(q)
    best = cur
    bestF = F.copy()
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        # preferably choose a position actually read
        j = q[np.random.randint(0, q.shape[0])]
        if j < 0:
            continue
        old = F[j]
        F[j] = np.random.randint(0, N)
        replay(flat, starts, F, q)
        new = entropy(q)
        if new <= cur or np.random.random() < np.exp((cur - new) / T):
            cur = new
            if cur < best:
                best = cur; bestF[:] = F
        else:
            F[j] = old
            replay(flat, starts, F, q)
    return bestF, best


def pack(msgs):
    flat = np.array([v for m in msgs for v in m], np.int64)
    starts = np.cumsum([0] + [len(m) for m in msgs]).astype(np.int64)
    return flat, starts


def run(msgs, iters=200000, restarts=4, T0=0.05, T1=0.0005, seed=0):
    flat, starts = pack(msgs)
    best = (1e9, None)
    for r in range(restarts):
        F0 = np.random.default_rng(seed + r).integers(0, N, N).astype(np.int64)
        t = time.time()
        F, h = anneal(flat, starts, F0, iters, T0, T1, seed + r)
        print(f"  trial {r}: entropy {h:.3f} bits ({time.time()-t:.0f} s)", flush=True)
        if h < best[0]:
            best = (h, F)
    return best


if __name__ == "__main__":
    from stats import load_eyes
    names, M = load_eyes()
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    h, F = run(M, iters)
    q = np.empty(sum(len(m) for m in M), np.int64)
    flat, starts = pack(M); replay(flat, starts, F, q)
    print(f"eyes: best entropy {h:.3f} bits; distinct read positions {len(set(q[q>=0].tolist()))}")
