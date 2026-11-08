"""Homophones chosen from the PREVIOUS LETTER (deterministic): a repeated phrase keeps the same homophones
(except at most its first symbol), so it stays isomorphic, while flattening the use of read positions.
Mechanism: gesture τ (reinsertion / segment reversal, reach K) + base shuffle β.
Criteria: isomorphs (6 occurrences of phrase P, first symbol excluded), flat profile, 0 doubles, stutter, fixed
points <= 1%, obstacle; substituted letters drawn at random (fair_joint_test).
Tokens: "retournement" = segment reversal, "aleatoire" = random base shuffle."""
import sys
from collections import Counter
from itertools import combinations
import numpy as np
from explore import xgak_encrypt
from family_zoo import tau_arr, beta_arr
from testbed import build_plaintexts, english_letters, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, d0
from fair_joint_test import edited
from architecture import iso_ok
from stats import load_eyes

N = 83
FREQ = Counter(english_letters()[:200000])


def make_key(tkind, bkind, K, nslots, rng):
    beta = beta_arr(bkind, rng)
    w = np.array([FREQ.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (nslots - len(ALPHA))
    counts = [1 + int(x) for x in w]
    while sum(counts) < nslots:
        counts[int(np.argmax(w - np.array(counts) + 1))] += 1
    slots, k = {}, 0
    for ch, c in zip(ALPHA, counts):
        slots[ch] = list(range(k, k + c)); k += c
    q = rng.choice(np.arange(1, N), k, replace=False)
    S = np.empty((k, N), np.int64)
    for s in range(k):
        while True:
            d = int(rng.integers(-K, K + 1)); m = int(q[s]) + d
            if d != 0 and 0 <= m < N:
                break
        S[s] = tau_arr(tkind, int(q[s]), m)[beta]
    return slots, q.astype(np.int64), S


def encode(msg, slots):
    out, prev = [], " "
    for ch in msg:
        sl = slots[ch]
        out.append(sl[(ord(prev) * 7 + 3) % len(sl)])
        prev = ch
    return np.array(out, np.int64)


def enc_all(plains, slots, reads, S):
    return [[0] + xgak_encrypt(encode(m[1:], slots), reads, S).tolist() for m in plains]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    P = "AINYOUAMINUTEBUT"
    occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
    rng = np.random.default_rng(55)
    print("τ             β          K   slots  iso   flat  0dbl  texture  fixpts    obstacle  ALL", flush=True)
    for tkind in ("reinsertion", "retournement"):
        for bkind in ("aleatoire", "riffle"):
            for K in (5, 20, 82):
                for nslots in (41, 60):
                    c = np.zeros(7)
                    for _ in range(R):
                        pl, pv = edited(base, rng)
                        for attempt in range(25):
                            slots, reads, S = make_key(tkind, bkind, K, nslots, rng)
                            C = enc_all(pl, slots, reads, S)
                            if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                                break
                        segs = [C[k][i + 1:i + len(P)] for k, i in occ]
                        iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                        a = chi2(C) <= EYES_CHI
                        b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                        f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                        tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                        fr, run = window_stats(enc_all(pv, slots, reads, S), 0, 1, d0 + 4, d0 + 24); o = fr >= 0.8 and run >= 13
                        c += [iso, a, b, t, x, o, iso and a and b and t and x and o]
                    print(f"{tkind:12s}  {bkind:9s}  {K:2d}  {nslots:3d}    " + "  ".join(f"{v / R:.2f}" for v in c), flush=True)
