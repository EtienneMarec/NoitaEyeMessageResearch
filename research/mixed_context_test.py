"""Combination of the two best leads (§20, §21): letter-dependent reach (Ks) AND homophones
chosen from the previous letter. Same criteria as context_homophone_test (isomorphs, flat, 0 doubles,
stutter, fixed points, obstacle; substituted letters drawn at random). 100 keys per family."""
import sys
from itertools import combinations
import numpy as np
import context_homophone_test as CH
from family_zoo import tau_arr, beta_arr
from testbed import build_plaintexts, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, d0
from fair_joint_test import edited
from architecture import iso_ok
from stats import load_eyes

N = 83


def make_key(tkind, bkind, Ks, nslots, rng):
    beta = beta_arr(bkind, rng)
    w = np.array([CH.FREQ.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (nslots - len(ALPHA))
    counts = [1 + int(x) for x in w]
    while sum(counts) < nslots:
        counts[int(np.argmax(w - np.array(counts) + 1))] += 1
    slots, k = {}, 0
    for ch, c in zip(ALPHA, counts):
        slots[ch] = list(range(k, k + c)); k += c
    q = rng.choice(np.arange(1, N), k, replace=False)
    S = np.empty((k, N), np.int64)
    for s in range(k):
        K = int(rng.choice(Ks))
        while True:
            d = int(rng.integers(-K, K + 1)); m = int(q[s]) + d
            if d != 0 and 0 <= m < N:
                break
        S[s] = tau_arr(tkind, int(q[s]), m)[beta]
    return slots, q.astype(np.int64), S


R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
names, M = load_eyes()
EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
base = build_plaintexts()
P = "AINYOUAMINUTEBUT"
occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
rng = np.random.default_rng(77)
print("τ             β          reaches    slots  iso   flat  0dbl  texture  fixpts    obstacle  ALL", flush=True)
for tkind in ("reinsertion", "retournement"):
    for bkind in ("aleatoire", "riffle"):
        for Ks in ((2, 41), (3, 82), (2, 5, 41), (5, 20)):
            for nslots in (41, 60):
                c = np.zeros(7)
                for _ in range(R):
                    pl, pv = edited(base, rng)
                    for attempt in range(25):
                        slots, reads, S = make_key(tkind, bkind, Ks, nslots, rng)
                        C = CH.enc_all(pl, slots, reads, S)
                        if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                            break
                    segs = [C[k][i + 1:i + len(P)] for k, i in occ]
                    iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                    a = chi2(C) <= EYES_CHI
                    b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    fr, run = window_stats(CH.enc_all(pv, slots, reads, S), 0, 1, d0 + 4, d0 + 24); o = fr >= 0.8 and run >= 13
                    c += [iso, a, b, t, x, o, iso and a and b and t and x and o]
                print(f"{tkind:12s}  {bkind:9s}  {str(Ks):10s}  {nslots:3d}    " + "  ".join(f"{v / R:.2f}" for v in c), flush=True)
