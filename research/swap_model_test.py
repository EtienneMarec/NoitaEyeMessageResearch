"""Is Lymm's hypothesis (σ_p = β ∘ τ_p, τ_p = k letter-specific swaps) compatible
with the FLAT gap profile of the eyes?

GAK model: D_new[x] = D_old[σ_p[x]], output = D_new[0]. τ_p contains the swap (0 a_p) (a read
distinct per letter, a_p chosen to avoid doubles) plus k-1 random swaps.
"Spikes" statistic: chi² of repeats at distance d = 2..40 (deduplicated) against a
flat profile, compared with the value of the eyes. Text: test corpus with the eyes' architecture.
"""
import sys
import numpy as np
from numba import njit
from testbed import build_plaintexts, ALPHA
from gap_profile import profile
from stats import load_eyes

N = 83


@njit(cache=True)
def gak_encrypt(seq, sig):
    D = np.arange(N)
    out = np.empty(seq.shape[0], np.int64)
    for i in range(seq.shape[0]):
        s = sig[seq[i]]
        tmp = D.copy()
        for x in range(N):
            D[x] = tmp[s[x]]
        out[i] = D[0]
    return out


def make_sigmas(beta, k, rng, n_letters=len(ALPHA)):
    sig = np.empty((n_letters, N), np.int64)
    binv = np.argsort(beta)
    used = set()
    for p in range(n_letters):
        while True:
            tau = np.arange(N)
            a = int(rng.integers(1, N))
            tau[0], tau[a] = tau[a], tau[0]
            for _ in range(k - 1):
                u, v = rng.integers(1, N, size=2)
                tau[u], tau[v] = tau[v], tau[u]
            s = beta[tau]                  # σ = β∘τ: σ[x] = β[τ[x]]
            if s[0] != 0 and s[0] not in used:
                used.add(int(s[0])); sig[p] = s; break
    return sig


def spikiness(msgs, dmax=40):
    cnt, tests = profile(msgs)
    cnt, tests = np.array(cnt[2:dmax + 1], float), np.array(tests[2:dmax + 1], float)
    exp = tests * cnt.sum() / tests.sum()
    return float(((cnt - exp) ** 2 / exp).sum()), int(cnt[0]) if False else None


def chi2(msgs):
    return spikiness(msgs)[0]


if __name__ == "__main__" and "--joint" not in sys.argv:
    names, M = load_eyes()
    eyes = chi2(M)
    print(f"eyes: spike chi² = {eyes:.1f}   (38 degrees of freedom: ~38 for a flat profile)")
    plains = build_plaintexts()
    seqs = [np.array([ALPHA.index(ch) for ch in m], np.int64) for m in plains]
    rng = np.random.default_rng(0)
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(" k   β            median chi²  [min – max]   P(chi² <= eyes)   doubles (median)")
    for beta_kind in ("random", "cycle-83"):
        for k in (1, 2, 4, 8, 16, 41):
            vals, dbl = [], []
            for r in range(R):
                if beta_kind == "random":
                    beta = rng.permutation(N)
                else:
                    order = rng.permutation(N); beta = np.empty(N, np.int64)
                    beta[order] = np.roll(order, 1)
                sig = make_sigmas(beta, k, rng)
                C = [gak_encrypt(s, sig).tolist() for s in seqs]
                vals.append(chi2(C))
                dbl.append(sum(a == b for m in C for a, b in zip(m, m[1:])))
            vals = np.array(vals)
            print(f"{k:2d}   {beta_kind:10s}   {np.median(vals):8.1f}   [{vals.min():6.1f} – {vals.max():7.1f}]   "
                  f"{(vals <= eyes).mean():5.2f}             {int(np.median(dbl))}")


def prefix_sync(C, groups=((0, 1, 2), (6, 7, 8))):
    """Mean length of identical ciphertext from position 1 in each group
    (identical texts after a differing first letter). Eyes: 24 (group A), 20 (group C)."""
    out = []
    for g in groups:
        L = 0
        while all(len(C[m]) > L + 1 for m in g) and len({C[m][L + 1] for m in g}) == 1:
            L += 1
        out.append(L)
    return out


def joint(R=20):
    names, M = load_eyes()
    eyes = chi2(M)
    print(f"\neyes: chi² {eyes:.1f}; identical ciphertext after the 1st letter: {prefix_sync(M)} (max possible here: 21 and 20)")
    plains = build_plaintexts()
    seqs = [np.array([ALPHA.index(ch) for ch in m], np.int64) for m in plains]
    rng = np.random.default_rng(1)
    print(" k    median chi²   P(chi²<=eyes)   median sync A/C       P(sync >= 15 in A and C)       P(both)")
    for k in (1, 2, 3, 4, 6, 8, 12, 16, 24, 41):
        ok_c = ok_s = ok_both = 0; chis = []; syn = []
        for r in range(R):
            sig = make_sigmas(rng.permutation(N), k, rng)
            C = [gak_encrypt(s, sig).tolist() for s in seqs]
            c = chi2(C); s = prefix_sync(C)
            chis.append(c); syn.append(s)
            a, b = c <= eyes, min(s) >= 15
            ok_c += a; ok_s += b; ok_both += a and b
        syn = np.array(syn)
        print(f"{k:2d}   {np.median(chis):9.1f}     {ok_c/R:5.2f}          {int(np.median(syn[:,0]))}/{int(np.median(syn[:,1]))}"
              f"                   {ok_s/R:5.2f}                        {ok_both/R:5.2f}")


if __name__ == "__main__" and "--joint" in sys.argv:
    joint(int(sys.argv[sys.argv.index("--joint") + 1]))
