"""Follow-up to segment_length_test: (1) letter-dependent reach (each letter draws its reach K
from a set, e.g. {2, 41}); (2) base shuffle "cut one card" with a short reach.
Same criteria (including the E1/W1 obstacle), 100 keys per family."""
import sys
import numpy as np
from family_zoo import tau_arr, beta_arr, encipher, doubles
from testbed import build_plaintexts, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, variant_single, d0
from stats import load_eyes

N = 83


def make_key_mix(tkind, bkind, Ks, rng):
    beta = beta_arr(bkind, rng)
    ns = len(ALPHA)
    q = rng.choice(np.arange(1, N), ns, replace=False)
    S = np.empty((ns, N), np.int64)
    for s in range(ns):
        K = int(rng.choice(Ks))
        while True:
            d = int(rng.integers(-K, K + 1)); m = int(q[s]) + d
            if d != 0 and 0 <= m < N:
                break
        S[s] = tau_arr(tkind, int(q[s]), m)[beta]
    return q.astype(np.int64), S


R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
names, M = load_eyes()
EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
plains = build_plaintexts(); pv = variant_single(plains)
rng = np.random.default_rng(123)
print("τ             β          reaches        flat  0dbl  texture  fixpts    obstacle  ALL")
for tkind in ("reinsertion", "retournement"):
    for bkind, Ks in (("aleatoire", (2, 41)), ("aleatoire", (3, 82)), ("riffle", (2, 41)), ("tas3", (2, 41)),
                      ("coupe1", (2,)), ("coupe1", (5,)), ("coupe1", (10,)), ("coupe1", (2, 41)), ("coupe1", (41,))):
        c = np.zeros(6)
        for _ in range(R):
            for attempt in range(25):
                reads, S = make_key_mix(tkind, bkind, Ks, rng)
                C = encipher(plains, reads, S, False)
                if doubles(C, False) == 0:
                    break
            a = chi2(C) <= EYES_CHI; b = doubles(C, False) == 0
            f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
            tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
            fr, run = window_stats(encipher(pv, reads, S, False), 0, 1, d0 + 4, d0 + 24); o = fr >= 0.8 and run >= 13
            c += [a, b, t, x, o, a and b and t and x and o]
        print(f"{tkind:12s}  {bkind:9s}  {str(Ks):12s}   " + "  ".join(f"{v / R:.2f}" for v in c), flush=True)
