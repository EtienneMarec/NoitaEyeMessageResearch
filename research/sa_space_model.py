"""Simulated annealing on the space model (β for letters, σ for the space), sorted starting deck (§30).

Without loss of generality, D0 = identity (in card coordinates, D0 is absorbed into β and σ).
Key: β, σ (permutations of 83 positions), q_space. Deterministic decryption: r_t = D_t⁻¹(c_t); space if
r_t = q_space (σ is applied), otherwise letter (β). Score = Dirichlet-multinomial log-likelihood (α = 0.5)
of the sequence of r_t (high if few positions are read), weighted towards the start of the messages (where an
error in β has less effect): only the first T symbols of each message are scored (T grows in stages).
Moves: swap of two entries of β or σ, or a new q_space.
Validation on the testbed with spaces (known key, random β and σ): share of entries of β and σ recovered."""
import sys
import math
import numpy as np
from numba import njit
from explore import xgak_encrypt
import testbed_spaces as tbs
import space_model_test as sm

N = 83


@njit(cache=True)
def decrypt_score(C, starts, lens, binv, sinv, qs, T, alpha):
    cnt = np.zeros(N, np.int64)
    pos = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
    tot = 0
    for m in range(starts.shape[0]):
        for x in range(N):
            pos[x] = x
        for t in range(starts[m], starts[m] + min(lens[m], T)):
            r = pos[C[t]]
            cnt[r] += 1; tot += 1
            if r == qs:
                for x in range(N):
                    tmp[x] = sinv[pos[x]]
            else:
                for x in range(N):
                    tmp[x] = binv[pos[x]]
            for x in range(N):
                pos[x] = tmp[x]
    s = 0.0
    for r in range(N):
        s += math.lgamma(cnt[r] + alpha) - math.lgamma(alpha)
    s -= math.lgamma(tot + N * alpha) - math.lgamma(N * alpha)
    return s


@njit(cache=True)
def anneal(C, starts, lens, binv, sinv, qs, T, iters, t0, t1, seed):
    np.random.seed(seed)
    cur = decrypt_score(C, starts, lens, binv, sinv, qs, T, 0.5)
    best = cur
    bb, bs, bq = binv.copy(), sinv.copy(), qs
    for it in range(iters):
        temp = t0 * (t1 / t0) ** (it / iters)
        u = np.random.random()
        if u < 0.45:
            i = np.random.randint(N); j = np.random.randint(N)
            binv[i], binv[j] = binv[j], binv[i]
            new = decrypt_score(C, starts, lens, binv, sinv, qs, T, 0.5)
            if new >= cur or np.random.random() < math.exp((new - cur) / temp):
                cur = new
            else:
                binv[i], binv[j] = binv[j], binv[i]
        elif u < 0.9:
            i = np.random.randint(N); j = np.random.randint(N)
            sinv[i], sinv[j] = sinv[j], sinv[i]
            new = decrypt_score(C, starts, lens, binv, sinv, qs, T, 0.5)
            if new >= cur or np.random.random() < math.exp((new - cur) / temp):
                cur = new
            else:
                sinv[i], sinv[j] = sinv[j], sinv[i]
        else:
            old = qs; qs = np.random.randint(N)
            new = decrypt_score(C, starts, lens, binv, sinv, qs, T, 0.5)
            if new >= cur or np.random.random() < math.exp((new - cur) / temp):
                cur = new
            else:
                qs = old
        if cur > best:
            best = cur; bb[:] = binv; bs[:] = sinv; bq = qs
    return best, bb, bs, bq


def flatten(msgs):
    starts = np.cumsum([0] + [len(m) for m in msgs[:-1]]).astype(np.int64)
    return np.concatenate([np.array(m, np.int64) for m in msgs]), starts, np.array([len(m) for m in msgs], np.int64)


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    rng = np.random.default_rng(1)
    pl = tbs.build_plaintexts()
    beta = rng.permutation(N); sigma = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([sigma if ch == "_" else beta for ch in tbs.ALPHA_S], np.int64)
    msgs = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    binv_true = np.empty(N, np.int64); binv_true[beta] = np.arange(N)
    sinv_true = np.empty(N, np.int64); sinv_true[sigma] = np.arange(N)
    qs_true = int(q[tbs.ALPHA_S.index("_")])
    for T in (8, 15, 30, 200):
        print(f"T = {T:3d}: score of the true key {decrypt_score(C, starts, lens, binv_true, sinv_true, qs_true, T, 0.5):9.1f}, "
              f"random key {decrypt_score(C, starts, lens, rng.permutation(N), rng.permutation(N), 0, T, 0.5):9.1f}", flush=True)
    # annealing in stages of T, random start
    binv = rng.permutation(N).astype(np.int64); sinv = rng.permutation(N).astype(np.int64); qs = 0
    for T in (6, 10, 15, 25, 40, 200):
        best, binv, sinv, qs = anneal(C, starts, lens, binv, sinv, qs, T, iters, 3.0, 0.05, T)
        ok_b = int((binv == binv_true).sum()); ok_s = int((sinv == sinv_true).sum())
        print(f"stage T = {T:3d}: score {best:9.1f} (true key {decrypt_score(C, starts, lens, binv_true, sinv_true, qs_true, T, 0.5):9.1f}); "
              f"correct entries β {ok_b}/83, σ {ok_s}/83, q_space {'correct' if qs == qs_true else 'wrong'}", flush=True)
