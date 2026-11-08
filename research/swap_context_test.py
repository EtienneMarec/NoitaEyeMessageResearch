"""Lymm's model (small swaps + base shuffle β) with homophones chosen from the previous letter.

Motivation (§23): the E1/W1 obstacle read as Lymm does (4 different, 4 identical, 4 different, 13 identical:
two 4-letter words swapped) requires the permutations of two different words to be very close
(small Hamming distance). Swaps give that, but fail on flatness (§7.4, §14).
Question: do deterministic homophones (hence perfect isomorphs) flatten the profile of the swaps?

Key: for each slot s (homophone), read at q_s, τ_s = swap (q_s, m_s) + (k-1) random swaps,
then β. First trigram outside the deck.
Criteria: isomorphs (6 occurrences of phrase P), flat profile, 0 doubles, E4/E5 stutter (letters
substituted at random), fixed points <= 1%, "word swap" obstacle (window d0+4..d0+24: >= 80%
identical and run >= 13), and for reference the "two substitutions" obstacle (§19)."""
import sys
from collections import Counter
from itertools import combinations
import numpy as np
from family_zoo import beta_arr
from testbed import build_plaintexts, english_letters, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, d0
from fair_joint_test import edited
from context_homophone_test import encode, enc_all
from architecture import iso_ok
from stats import load_eyes

N = 83
FREQ = Counter(english_letters()[:200000])


def _letter_perm(kswaps, q, beta, rng, top):
    """τ = swap (q, m) + (k-1) random swaps, then β (row S of a slot)"""
    idx = np.arange(N)
    m = 0 if top else int(rng.integers(0, N))
    while m == q:
        m = int(rng.integers(0, N))
    idx[[q, m]] = idx[[m, q]]
    for _ in range(kswaps - 1):
        a, b = rng.choice(N, 2, replace=False)
        idx[[a, b]] = idx[[b, a]]
    return idx[beta]


def make_key(kswaps, bkind, nslots, rng, top=False, nodouble=False):
    """nodouble: design rule (Lymm, "No Doubles"): the card read never lands on a
    read position, which forbids doubles by construction (τ is redrawn until the rule holds).
    xgak_encrypt convention: D'[x] = D[S[x]], so the card read (position q) arrives at x such that S[x] = q."""
    beta = beta_arr(bkind, rng)
    w = np.array([FREQ.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (nslots - len(ALPHA))
    counts = [1 + int(x) for x in w]
    while sum(counts) < nslots:
        counts[int(np.argmax(w - np.array(counts) + 1))] += 1
    slots, k = {}, 0
    for ch, c in zip(ALPHA, counts):
        slots[ch] = list(range(k, k + c)); k += c
    q = rng.choice(np.arange(1, N), k, replace=False)
    Q = set(q.tolist())
    S = np.empty((k, N), np.int64)
    for s in range(k):
        for _try in range(10000):
            S[s] = _letter_perm(kswaps, int(q[s]), beta, rng, top)
            if not nodouble or int(np.where(S[s] == q[s])[0][0]) not in Q:
                break
    return slots, q.astype(np.int64), S


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    P = "AINYOUAMINUTEBUT"
    occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
    rng = np.random.default_rng(77)
    print("swaps     β          slots  iso   flat  0dbl  texture  fixpts    obst(words) obst(subst)  ALL(words)  ALL(subst)", flush=True)
    for kswaps, top in ((1, False), (1, True), (2, False), (4, False)):
        for bkind in ("aleatoire", "riffle"):
            for nslots in (len(ALPHA), 60, 82):
                c = np.zeros(9)
                for _ in range(R):
                    pl, pv = edited(base, rng)
                    for attempt in range(25):
                        slots, reads, S = make_key(kswaps, bkind, nslots, rng, top)
                        C = enc_all(pl, slots, reads, S)
                        if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                            break
                    segs = [C[k][i + 1:i + len(P)] for k, i in occ]
                    iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                    a = chi2(C) <= EYES_CHI
                    b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    fr, run = window_stats(C, 0, 1, d0 + 4, d0 + 24); om = fr >= 0.8 and run >= 13
                    fr, run = window_stats(enc_all(pv, slots, reads, S), 0, 1, d0 + 4, d0 + 24); os_ = fr >= 0.8 and run >= 13
                    core = iso and a and b and t and x
                    c += [iso, a, b, t, x, om, os_, core and om, core and os_]
                lab = f"{kswaps}{'(top)   ' if top else '        '}"
                print(f"{lab:9s} {bkind:9s}  {nslots:3d}   " + "  ".join(f"{v / R:.2f}" for v in c), flush=True)
