"""Attack "keyed starting deck, natural shuffles" on the space model (§33).

Model: KEYED (unknown) starting deck D0; letter → read at q_p then natural shuffle β; space →
read at q_space then natural shuffle σ (β, σ known if guessed from the list of 116 shuffles).
Convention: D'[x] = D[S[x]]; the card at position y moves to position Sinv[y].

If β, σ are known, the trajectory of each card depends only on its start position x_c = D0⁻¹(c)
(and on the space decisions, which depend on the reads). Alternating algorithm (EM type):
  1. with the current x: decrypt → read positions r_t (space if r_t = q_space);
     q_space = most frequent read position; φ = smoothed frequencies of the r_t;
  2. with the decisions fixed, F_t (composition of the Sinv) is known: score(c, y) = Σ_{t : c_t = c} log φ(F_t(y));
  3. optimal assignment cards → start positions (Hungarian algorithm); repeat.
Final score: entropy of the read positions (bits), to compare with log2(83) = 6.37 at random.
Validation on the testbed with spaces (random D0, β = rot1, σ = deal3fwd), then controls (wrong β, σ)."""
import sys
import numpy as np
from numba import njit
from scipy.optimize import linear_sum_assignment
from deckcipher import base_shuffles

N = 83


@njit(cache=True)
def decode(C, starts, lens, x, binv, sinv, qs, first_in):
    r = np.empty(C.shape[0], np.int64); sp = np.zeros(C.shape[0], np.bool_)
    pos = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
    for m in range(starts.shape[0]):
        pos[:] = x
        a = starts[m] + (0 if first_in else 1)
        for t in range(starts[m], a):
            r[t] = -1
        for t in range(a, starts[m] + lens[m]):
            rt = pos[C[t]]; r[t] = rt
            S = sinv if rt == qs else binv
            sp[t] = rt == qs
            for y in range(N):
                tmp[y] = S[pos[y]]
            pos[:] = tmp
    return r, sp


@njit(cache=True)
def scores(C, starts, lens, sp, binv, sinv, logphi, first_in):
    sc = np.zeros((N, N))
    F = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
    for m in range(starts.shape[0]):
        for y in range(N):
            F[y] = y
        a = starts[m] + (0 if first_in else 1)
        for t in range(a, starts[m] + lens[m]):
            c = C[t]
            for y in range(N):
                sc[c, y] += logphi[F[y]]
            S = sinv if sp[t] else binv
            for y in range(N):
                tmp[y] = S[F[y]]
            F[:] = tmp
    return sc


def entropy(r):
    r = r[r >= 0]
    p = np.bincount(r, minlength=N) / len(r)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def attack(C, starts, lens, binv, sinv, first_in, rng, iters=30, restarts=4):
    best = (99.0, None, None)
    for _ in range(restarts):
        x = rng.permutation(N).astype(np.int64)
        qs = -1
        for it in range(iters):
            r, sp = decode(C, starts, lens, x, binv, sinv, qs, first_in)
            rr = r[r >= 0]
            cnt = np.bincount(rr, minlength=N).astype(float)
            qs = int(np.argmax(cnt))
            r, sp = decode(C, starts, lens, x, binv, sinv, qs, first_in)
            cnt = np.bincount(r[r >= 0], minlength=N).astype(float)
            logphi = np.log((cnt + 0.5) / (cnt.sum() + 0.5 * N))
            sc = scores(C, starts, lens, sp, binv, sinv, logphi, first_in)
            rows, cols = linear_sum_assignment(-sc)
            xn = np.empty(N, np.int64); xn[rows] = cols
            if (xn == x).all():
                break
            x = xn
        r, sp = decode(C, starts, lens, x, binv, sinv, qs, first_in)
        h = entropy(r)
        if h < best[0]:
            best = (h, x.copy(), qs)
    return best


def tables():
    BS = base_shuffles()
    names = list(BS)
    inv = {}
    for k, p in BS.items():
        q = np.empty(N, np.int64); q[p] = np.arange(N); inv[k] = q
    return names, BS, inv


def flatten(msgs):
    starts = np.cumsum([0] + [len(m) for m in msgs[:-1]]).astype(np.int64)
    return np.concatenate([np.array(m, np.int64) for m in msgs]), starts, np.array([len(m) for m in msgs], np.int64)


if __name__ == "__main__":
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    names, BS, inv = tables()
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    pl = tbs.build_plaintexts()
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
    r, sp = decode(C, starts, lens, x_true, inv[bname], inv[sname], int(q[tbs.ALPHA_S.index("_")]), True)
    print(f"truth: entropy of read positions {entropy(r):.2f} bits ({len(set(r.tolist()))} positions); random ≈ 6.3")
    h, x, qs = attack(C, starts, lens, inv[bname], inv[sname], True, rng)
    print(f"attack with correct (β, σ): entropy {h:.2f}, correct start positions {int((x == x_true).sum())}/83, "
          f"q_space {'correct' if qs == q[tbs.ALPHA_S.index('_')] else 'wrong'}", flush=True)
    for bn, sn in (("rot1", "deal3rev"), ("rot2", "deal3fwd"), ("outshuffle", "deal3fwd"), ("rot1", "milk")):
        h2, _, _ = attack(C, starts, lens, inv[bn], inv[sn], True, rng)
        print(f"control β={bn:10s} σ={sn:10s}: entropy {h2:.2f}", flush=True)
