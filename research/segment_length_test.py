"""All criteria at once, including the E1/W1 "obstacle", for "reinsertion / segment reversal
+ base shuffle β" families whose segment length is controlled: destination m_p = q_p + δ, δ drawn
uniformly in [-K, K] (K = reach), δ != 0. First trigram outside the deck, no homophones.
Criteria: flat profile (chi² <= 63.2), 0 doubles, Stutter E4/E5 texture (0.42 ± 0.15, >= 7 runs),
fixed points after an insertion <= 1%, OBSTACLE: on the testbed where W1 = E1 with two one-letter
substitutions (as in the eyes: differences around 25 and 33), window +4..+24: >= 80% identical and an
identical run >= 13."""
import sys
import numpy as np
from explore import xgak_encrypt
from family_zoo import tau_arr, beta_arr, encipher, doubles
from testbed import build_plaintexts, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, variant_single, d0
from stats import load_eyes

N = 83


def make_key_K(tkind, bkind, order, K, rng):
    beta = beta_arr(bkind, rng)
    ns = len(ALPHA)
    q = rng.choice(np.arange(1, N), ns, replace=False)
    S = np.empty((ns, N), np.int64); reads = np.empty(ns, np.int64)
    for s in range(ns):
        while True:
            d = int(rng.integers(-K, K + 1))
            m = int(q[s]) + d
            if d != 0 and 0 <= m < N:
                break
        t = tau_arr(tkind, int(q[s]), m)
        if order == 0:
            S[s] = t[beta]; reads[s] = q[s]
        else:
            S[s] = beta[t]; reads[s] = beta[q[s]]
    return reads, S


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    plains = build_plaintexts(); pv = variant_single(plains)
    rng = np.random.default_rng(99)
    print("τ             β          K    flat  0dbl  texture  fixpts    obstacle  ALL    (without obstacle)")
    for tkind in ("reinsertion", "retournement"):
        for bkind in ("aleatoire", "riffle", "tas3"):
            for K in (2, 5, 10, 20, 41, 82):
                c = np.zeros(6)
                for _ in range(R):
                    for attempt in range(25):
                        reads, S = make_key_K(tkind, bkind, 0, K, rng)
                        C = encipher(plains, reads, S, False)
                        if doubles(C, False) == 0:
                            break
                    a = chi2(C) <= EYES_CHI
                    b = doubles(C, False) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    C2 = encipher(pv, reads, S, False)
                    fr, run = window_stats(C2, 0, 1, d0 + 4, d0 + 24); o = fr >= 0.8 and run >= 13
                    c += [a, b, t, x, o, a and b and t and x and o]
                    c[5] += 0
                base = None
                print(f"{tkind:12s}  {bkind:9s}  {K:2d}   " + "  ".join(f"{v / R:.2f}" for v in c[:5]) + f"     {c[5] / R:.2f}", flush=True)
