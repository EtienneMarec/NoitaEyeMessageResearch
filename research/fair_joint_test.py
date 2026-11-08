"""A "fair" joint test: the substituted letters in the testbed (Stutter E4/E5 at 21 and 26,
obstacle E1/W1 at d0 and d0+8) are drawn at random from English frequencies for each key, instead
of always being rare (Q/X/Z). Criteria: flat profile, 0 doubles, stutter texture, fixed points
after an insertion <= 1%, obstacle (>= 80% identical, run >= 13). First trigram outside the deck,
no homophones. Families: gesture × β × reach K (reach 82 = free destination)."""
import sys
from collections import Counter
import numpy as np
from family_zoo import tau_arr, beta_arr, encipher, doubles
from testbed import build_plaintexts, english_letters, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, d0
from stats import load_eyes

N = 83
FREQ = Counter(english_letters()[:200000])
LET = [ch for ch in ALPHA if ch.isalpha()]
W = np.array([FREQ[ch] for ch in LET], float); W /= W.sum()


def rand_letter(rng, avoid):
    while True:
        ch = LET[rng.choice(len(LET), p=W)]
        if ch != avoid:
            return ch


def edited(base, rng):
    """copy of the testbed with random edits: E5 (index 8) at 21 and 26; also returns the
    obstacle variant (W1 = E1 with two substitutions at d0 and d0+8)."""
    pl = list(base)
    e5 = list(pl[8])
    for k in (21, 26):
        e5[k] = rand_letter(rng, e5[k])
    pl[8] = "".join(e5)
    w = list(pl[0])
    for k in (d0, d0 + 8):
        w[k] = rand_letter(rng, w[k])
    pv = list(pl); pv[1] = "".join(w)
    return pl, pv


def make_key(tkind, bkind, K, rng):
    beta = beta_arr(bkind, rng)
    ns = len(ALPHA)
    q = rng.choice(np.arange(1, N), ns, replace=False)
    S = np.empty((ns, N), np.int64)
    for s in range(ns):
        while True:
            d = int(rng.integers(-K, K + 1)); m = int(q[s]) + d
            if d != 0 and 0 <= m < N:
                break
        S[s] = tau_arr(tkind, int(q[s]), m)[beta]
    return q.astype(np.int64), S


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    rng = np.random.default_rng(321)
    print("τ               β          K    flat  0dbl  texture  fixpts    obstacle  ALL", flush=True)
    for tkind in ("echange", "echange_dessus", "reinsertion", "retournement"):
        for bkind in ("aleatoire", "riffle", "tas3", "coupe1"):
            for K in ((82, 5) if tkind != "echange_dessus" else (82,)):
                c = np.zeros(6)
                for _ in range(R):
                    pl, pv = edited(base, rng)
                    for attempt in range(25):
                        reads, S = make_key(tkind, bkind, K, rng)
                        C = encipher(pl, reads, S, False)
                        if doubles(C, False) == 0:
                            break
                    a = chi2(C) <= EYES_CHI; b = doubles(C, False) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    fr, run = window_stats(encipher(pv, reads, S, False), 0, 1, d0 + 4, d0 + 24); o = fr >= 0.8 and run >= 13
                    c += [a, b, t, x, o, a and b and t and x and o]
                print(f"{tkind:14s}  {bkind:9s}  {K:2d}   " + "  ".join(f"{v / R:.2f}" for v in c), flush=True)
