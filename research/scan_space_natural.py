"""Scan of the space model with NATURAL shuffles (§26).

Model: letters → shuffle β, space → shuffle σ, read at q_p (D'[x] = D[S[x]], output D[q_p]).
If (β, σ, starting deck D0, q_space) are known, the read position r_t = D_t⁻¹(c_t) is computed
deterministically: it is a space if r_t = q_space (σ is applied), otherwise a letter (β is applied).
Good mechanism: the sequence of r_t uses about as many positions as plaintext symbols (≈ 30–40),
versus ≈ 83 at random. Score = number of distinct positions; early stop if > SEUIL_D after SEUIL_T symbols.

Grid: 116 base shuffles (deckcipher.base_shuffles) for β and for σ (σ ≠ β), D0 sorted or reversed,
q_space ∈ 0..82, first symbol inside or outside the deck. Validation on the testbed with spaces (--valider)."""
import sys
import time
import numpy as np
from numba import njit, prange
from deckcipher import base_shuffles
from stats import load_eyes

N = 83
SEUIL_T, SEUIL_D = 150, 55


@njit(parallel=True, cache=True)
def scan(C, starts, lens, SHinv, pairs, Dinv0, first_in):
    P = pairs.shape[0]
    best = np.full((P, Dinv0.shape[0], N), 999, np.int64)
    nsp = np.zeros((P, Dinv0.shape[0], N), np.int64)
    for pi in prange(P):
        b = pairs[pi, 0]; s = pairs[pi, 1]
        pos = np.empty(N, np.int64); tmp = np.empty(N, np.int64)
        seen = np.zeros(N, np.bool_)
        for di in range(Dinv0.shape[0]):
            for qs in range(N):
                seen[:] = False
                nd = 0; tot = 0; sp = 0; ok = True
                for m in range(starts.shape[0]):
                    pos[:] = Dinv0[di]
                    a = starts[m] + (0 if first_in else 1)
                    for t in range(a, starts[m] + lens[m]):
                        r = pos[C[t]]
                        if not seen[r]:
                            seen[r] = True; nd += 1
                        tot += 1
                        k = b
                        if r == qs:
                            k = s; sp += 1
                        for x in range(N):
                            tmp[x] = SHinv[k, pos[x]]
                        pos[:] = tmp
                        if tot == SEUIL_T and nd > SEUIL_D:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    best[pi, di, qs] = nd; nsp[pi, di, qs] = sp
    return best, nsp


def tables():
    BS = base_shuffles()
    names = list(BS)
    SH = np.array([BS[k] for k in names], np.int64)
    SHinv = np.empty_like(SH)
    for i in range(len(names)):
        SHinv[i][SH[i]] = np.arange(N)
    pairs = np.array([(b, s) for b in range(len(names)) for s in range(len(names)) if b != s], np.int64)
    return names, SH, SHinv, pairs


def flatten(msgs):
    starts = np.cumsum([0] + [len(m) for m in msgs[:-1]]).astype(np.int64)
    return np.concatenate([np.array(m, np.int64) for m in msgs]), starts, np.array([len(m) for m in msgs], np.int64)


def report(names, pairs, best, nsp, total, label, top=12):
    flat = [(int(best[p, d, q]), p, d, q) for p in range(len(pairs)) for d in range(best.shape[1]) for q in range(N)
            if best[p, d, q] < 999]
    flat.sort()
    print(f"[{label}] {len(flat)} combinations not abandoned out of {best.size}")
    for nd, p, d, q in flat[:top]:
        b, s = pairs[p]
        print(f"   {nd:3d} positions  β={names[b]:14s} σ={names[s]:14s} D0={'sorted' if d == 0 else 'reversed'}  "
              f"q_space={q:2d}  spaces={nsp[p, d, q] / total:.2f}")
    return flat


if __name__ == "__main__":
    names, SH, SHinv, pairs = tables()
    Dinv0 = np.array([np.arange(N), np.arange(N)[::-1]], np.int64)
    if "--valider" in sys.argv:
        import testbed_spaces as tbs
        from explore import xgak_encrypt
        pl = tbs.build_plaintexts()
        rng = np.random.default_rng(1)
        bi, si = names.index("outshuffle"), names.index("deal3fwd")
        q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
        S = np.array([SH[si] if ch == "_" else SH[bi] for ch in tbs.ALPHA_S], np.int64)
        msgs = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
        print(f"truth: β=outshuffle σ=deal3fwd D0=sorted q_space={q[tbs.ALPHA_S.index('_')]}, first symbol inside")
    else:
        _, msgs = load_eyes()
    C, starts, lens = flatten(msgs)
    total = int(lens.sum())
    for first_in in (True, False):
        t0 = time.time()
        best, nsp = scan(C, starts, lens, SHinv, pairs, Dinv0, first_in)
        report(names, pairs, best, nsp, total, f"first symbol {'inside' if first_in else 'outside'}, {time.time() - t0:.0f} s")
