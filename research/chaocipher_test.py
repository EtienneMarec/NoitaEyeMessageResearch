"""Adapted Chaocipher (cipher alphabet of 83 cards, plain alphabet of 83 slots of which 35 are symbols): does a
repeated phrase give perfect isomorphs, as in the eyes?
Chaocipher (Byrne): look up the plain letter in the plain alphabet (right), output the card at the same position
in the cipher alphabet (left). Then: the left alphabet is rotated to bring the output card to the zenith, the card
at zenith+1 is removed and reinserted at the nadir; the right alphabet is rotated to bring the plain letter to the
zenith, then one step further, the card at zenith+2 removed and reinserted at the nadir. Here nadir = 41.
Test: in the testbed, phrase P appears 6 times (2 per message of group A): P(6 mutually isomorphic
occurrences). Reference: the XGAK models give 100%."""
from itertools import combinations
import numpy as np
from testbed import build_plaintexts, ALPHA
from architecture import iso_ok

N, NADIR = 83, 41


def chao(msg, left, right):
    L, R = list(left), list(right)
    out = []
    for ch in msg:
        p = R.index(ch)
        c = L[p]; out.append(c)
        # left
        L = L[p:] + L[:p]
        x = L.pop(1); L.insert(NADIR, x)
        # right
        R = R[p:] + R[:p]
        R = R[1:] + R[:1]
        x = R.pop(2); R.insert(NADIR, x)
    return out


plains = build_plaintexts()
P = "AINYOUAMINUTEBUT"
occ = [(k, i) for k in range(3) for i in range(len(plains[k])) if plains[k].startswith(P, i)]
rng = np.random.default_rng(3)
ok = 0; T = 40
for _ in range(T):
    left = list(rng.permutation(N))
    slots = list(ALPHA) + [None] * (N - len(ALPHA))
    right = [slots[i] for i in rng.permutation(N)]
    C = [chao(m, left, right) for m in plains[:3]]
    segs = [C[k][i:i + len(P)] for k, i in occ]
    ok += all(iso_ok(a, b) for a, b in combinations(segs, 2))
print(f"Chaocipher-83: the 6 occurrences of the phrase are isomorphic for {ok}/{T} keys (XGAK: {T}/{T})")
