"""Coincidences at the same position right after a text divergence (§26).

For each pair of messages at shift 0, divergence = first position > 0 where the ciphertexts differ
after the shared opening. We count the identical positions in the window [div+1, div+W] and, as a
baseline, beyond div+W+10 (decks assumed well separated). Chance: 1/83 per position.
Messages still sharing their text (same group, before their own divergence) are treated by pair,
so a coincidence common to a group counts several times: we also give the count per distinct position
and per "independent groups" (E1/W1/E2; W2; E3; W3; E4/W4/E5 after merging their openings).

Interpretation: if letters do not (or hardly) change the deck, two messages stay in the same
state after a divergence as long as their structure (spaces) stays aligned, and a shared letter at the same
place gives the same symbol."""
from itertools import combinations
from math import comb
import numpy as np
from stats import load_eyes

W = 20
names, M = load_eyes()
N = dict(zip(names, M))


def divergence(A, B):
    i = 1
    while i < min(len(A), len(B)) and A[i] == B[i]:
        i += 1
    return i


near = far = nn = nf = 0
hits = []
for a, b in combinations(names, 2):
    A, B = N[a], N[b]
    L = min(len(A), len(B))
    d = divergence(A, B)
    for i in range(d + 1, min(d + 1 + W, L)):
        nn += 1
        if A[i] == B[i]:
            near += 1; hits.append((a, b, d, i, A[i]))
    for i in range(d + W + 10, L):
        nf += 1; far += A[i] == B[i]
print(f"near window (div+1..div+{W}): {near} identical out of {nn} ({1000 * near / nn:.1f} ‰; chance {1000 / 83:.1f} ‰)")
print(f"far zone (> div+{W + 10})   : {far} identical out of {nf} ({1000 * far / nf:.1f} ‰)")
# binomial probability of >= near under p = 1/83
p = 1 / 83
pv = sum(comb(nn, k) * p ** k * (1 - p) ** (nn - k) for k in range(near, nn + 1))
print(f"P(>= {near} | binomial {nn}, 1/83) = {pv:.2e}  (pairs not independent: see the count per position below)")
pos = {}
for a, b, d, i, v in hits:
    pos.setdefault((i, v), set()).update([a, b])
for (i, v), s in sorted(pos.items()):
    print(f"   position {i:2d}, symbol {v:2d}: {' '.join(sorted(s, key=names.index))}")
