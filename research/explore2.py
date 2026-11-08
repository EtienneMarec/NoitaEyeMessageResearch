"""Variant: the first trigram does NOT go through the deck (all messages start from the same state after it).
Absence of doubles is guaranteed: the card read, after τ then β, never lands on
a read position. Criteria: flat profile (chi²), no doubles, and "stutter": after a
one-letter substitution in an identical text, does the ciphertext resynchronise?
"""
import sys
import numpy as np
from explore import xgak_encrypt, tau_for, make_beta, encode, N, ALPHA
from testbed import build_plaintexts, english_letters
from swap_model_test import chi2
from stats import load_eyes
from collections import Counter


def make_key_nodbl(tkind, bkind, homo, rng):
    beta = make_beta(bkind, rng)
    binv = np.argsort(beta)
    freq = Counter(english_letters()[:200000])
    counts = [1] * len(ALPHA)
    if homo:
        w = np.array([freq.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (41 - len(ALPHA))
        counts = [1 + int(x) for x in w]
        while sum(counts) < 41: counts[int(np.argmax(w - np.array(counts) + 1))] += 1
    ns = sum(counts)
    reads = rng.choice(np.arange(1, N), ns, replace=False)
    rs = set(reads.tolist())
    # destinations m: the card read ends at β^{-1}(m) (swap) -> must not be a read position
    cand = [m for m in range(N) if m not in rs and int(binv[m]) not in rs]
    dests = rng.choice(cand, ns, replace=len(cand) < ns)
    slots, k = {}, 0
    for ch, c in zip(ALPHA, counts): slots[ch] = list(range(k, k + c)); k += c
    S = np.empty((ns, N), np.int64)
    for s in range(ns):
        S[s] = tau_for(tkind, int(reads[s]), int(dests[s]))[beta]
    return slots, np.array(reads, np.int64), S


def resync_profile(C, pairs=((6, 8),)):
    """For synthetic E4/E5 (small edits at positions 21, 26 and an insertion at 47):
    string of identical (=) / different (.) positions between 18 and 46."""
    return ["".join("=" if C[a][i] == C[b][i] else "." for i in range(18, 47)) for a, b in pairs]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    names, M = load_eyes()
    eyes_chi = chi2(M)
    print(f"eyes: chi² {eyes_chi:.1f}; E4/E5 positions 18..46: "
          + "".join("=" if M[6][i] == M[8][i] else "." for i in range(18, 47)))
    plains = [m[1:] for m in build_plaintexts()]          # first symbol outside the deck
    rng = np.random.default_rng(21)
    print("τ              β          homoph.  med. chi²  P(chi²<=eyes)  max doubles    example E4/E5 (18..46)")
    for tkind in ("echange", "reinsertion", "dessus"):
        for bkind in ("coupe1", "cycle83", "aleatoire"):
            for homo in (False, True):
                chis, dmax, ex = [], 0, None
                for r in range(R):
                    slots, reads, S = make_key_nodbl(tkind, bkind, homo, rng)
                    C = [[1000 + j] + xgak_encrypt(encode(m, slots), reads, S).tolist() for j, m in enumerate(plains)]
                    chis.append(chi2(C))
                    dmax = max(dmax, sum(a == b for m in C for a, b in zip(m, m[1:])))
                    if r == 0: ex = resync_profile(C)[0]
                print(f"{tkind:13s}  {bkind:9s}  {'yes' if homo else 'no':6s}  {np.median(chis):8.1f}   "
                      f"{np.mean(np.array(chis) <= eyes_chi):5.2f}          {dmax:3d}          {ex}", flush=True)
