"""Simulated annealing on the keyed starting deck (known natural β, σ) (§33).

State: x (start position of each card), q_space. Score: Dirichlet log-likelihood (α = 0.5) of the
read positions, full decryption (deterministic space decisions). Moves: swap of two
entries of x (95%), new q_space (5%). Validation on the testbed with spaces."""
import sys
import math
import numpy as np
from numba import njit
from keyed_deck_attack import tables, flatten, entropy, decode, N


@njit(cache=True)
def score(C, starts, lens, x, binv, sinv, qs):
    cnt = np.zeros(N, np.int64)
    pos = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
    tot = 0
    for m in range(starts.shape[0]):
        pos[:] = x
        for t in range(starts[m], starts[m] + lens[m]):
            rt = pos[C[t]]
            cnt[rt] += 1; tot += 1
            S = sinv if rt == qs else binv
            for y in range(N):
                tmp[y] = S[pos[y]]
            pos[:] = tmp
    s = 0.0
    for r in range(N):
        s += math.lgamma(cnt[r] + 0.5)
    return s


@njit(cache=True)
def anneal(C, starts, lens, x, qs, binv, sinv, iters, t0, t1, seed):
    np.random.seed(seed)
    cur = score(C, starts, lens, x, binv, sinv, qs)
    best = cur; bx = x.copy(); bq = qs
    for it in range(iters):
        temp = t0 * (t1 / t0) ** (it / iters)
        if np.random.random() < 0.95:
            i = np.random.randint(N); j = np.random.randint(N)
            x[i], x[j] = x[j], x[i]
            new = score(C, starts, lens, x, binv, sinv, qs)
            if new >= cur or np.random.random() < math.exp((new - cur) / temp):
                cur = new
            else:
                x[i], x[j] = x[j], x[i]
        else:
            old = qs; qs = np.random.randint(N)
            new = score(C, starts, lens, x, binv, sinv, qs)
            if new >= cur or np.random.random() < math.exp((new - cur) / temp):
                cur = new
            else:
                qs = old
        if cur > best:
            best = cur; bx[:] = x; bq = qs
    return best, bx, bq


if __name__ == "__main__":
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 300000
    names, BS, inv = tables()
    rng = np.random.default_rng(0)
    pl = tbs.build_plaintexts()
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
    qs_true = int(q[tbs.ALPHA_S.index("_")])
    print(f"true score {score(C, starts, lens, x_true, inv[bname], inv[sname], qs_true):.1f}")
    for run in range(3):
        x = rng.permutation(N).astype(np.int64)
        b, bx, bq = anneal(C, starts, lens, x, 0, inv[bname], inv[sname], iters, 5.0, 0.05, run)
        print(f"trial {run}: score {b:.1f}, correct positions {int((bx == x_true).sum())}/83, q_space {'correct' if bq == qs_true else 'wrong'}", flush=True)
