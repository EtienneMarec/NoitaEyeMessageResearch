"""Attack "keyed starting deck, natural shuffles", time-progressive version (§33).

Same model as keyed_deck_attack.py. Observed problem: with space decisions deduced from a wrong
deck, the alternating algorithm does not converge (0/40), whereas it converges with the true decisions (oracle).
Here: curriculum on the prefix length T (only the first T symbols of each message are decrypted and
scored), T increasing; at each stage, EM iterations (decisions recomputed, q_space = most frequent read
position, Hungarian assignment of start positions). Several random starts."""
import sys
import numpy as np
from numba import njit
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, entropy, N

SCHED = (4, 6, 8, 10, 13, 16, 20, 25, 30, 40, 55, 75, 100, 140)


@njit(cache=True)
def decodeT(C, starts, lens, x, binv, sinv, qs, first_in, T):
    r = np.full(C.shape[0], -1, np.int64); sp = np.zeros(C.shape[0], np.bool_)
    pos = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
    for m in range(starts.shape[0]):
        pos[:] = x
        a = starts[m] + (0 if first_in else 1)
        for t in range(a, starts[m] + min(lens[m], T)):
            rt = pos[C[t]]; r[t] = rt
            S = sinv if rt == qs else binv
            sp[t] = rt == qs
            for y in range(N):
                tmp[y] = S[pos[y]]
            pos[:] = tmp
    return r, sp


@njit(cache=True)
def scoresT(C, starts, lens, sp, binv, sinv, logphi, first_in, T):
    sc = np.zeros((N, N))
    F = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
    for m in range(starts.shape[0]):
        for y in range(N):
            F[y] = y
        a = starts[m] + (0 if first_in else 1)
        for t in range(a, starts[m] + min(lens[m], T)):
            c = C[t]
            for y in range(N):
                sc[c, y] += logphi[F[y]]
            S = sinv if sp[t] else binv
            for y in range(N):
                tmp[y] = S[F[y]]
            F[:] = tmp
    return sc


def em_step(C, starts, lens, x, binv, sinv, first_in, T, iters=15):
    qs = -1
    for it in range(iters):
        r, sp = decodeT(C, starts, lens, x, binv, sinv, qs, first_in, T)
        cnt = np.bincount(r[r >= 0], minlength=N).astype(float)
        qs = int(np.argmax(cnt))
        r, sp = decodeT(C, starts, lens, x, binv, sinv, qs, first_in, T)
        cnt = np.bincount(r[r >= 0], minlength=N).astype(float)
        logphi = np.log((cnt + 0.5) / (cnt.sum() + 0.5 * N))
        sc = scoresT(C, starts, lens, sp, binv, sinv, logphi, first_in, T)
        rows, cols = linear_sum_assignment(-sc)
        xn = np.empty(N, np.int64); xn[rows] = cols
        if (xn == x).all():
            break
        x = xn
    return x, qs


def attack2(C, starts, lens, binv, sinv, first_in, rng, restarts=10):
    best = (99.0, None, None)
    for _ in range(restarts):
        x = rng.permutation(N).astype(np.int64)
        for T in SCHED:
            x, qs = em_step(C, starts, lens, x, binv, sinv, first_in, T)
        r, sp = decodeT(C, starts, lens, x, binv, sinv, qs, first_in, 10 ** 6)
        h = entropy(r)
        if h < best[0]:
            best = (h, x.copy(), qs)
    return best


if __name__ == "__main__":
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    names, BS, inv = tables()
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    rng = np.random.default_rng(seed)
    pl = tbs.build_plaintexts()
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk"), ("deal2fwd", "rot5")):
        D0 = rng.permutation(N)
        q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        h, x, qs = attack2(C, starts, lens, inv[bname], inv[sname], True, rng)
        print(f"β={bname:10s} σ={sname:9s}: entropy {h:.2f} (truth ≈ 4.1), correct positions {int((x == x_true).sum())}/83", flush=True)
        h2, _, _ = attack2(C, starts, lens, inv["rot2"], inv["deal3rev"], True, rng, restarts=3)
        print(f"   control (wrong β, σ): entropy {h2:.2f}", flush=True)
