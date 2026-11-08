"""Full battery of Lymm's model (β of order 8 or random, k = 1) with a plaintext of FLAT
frequencies (§28).

Testbed: same architecture as testbed.build_plaintexts, but the source text is replaced by a sequence of
letters drawn uniformly among 26 (or among the 26 letters with the English law, for comparison).
Criteria: flat, 0 doubles (no-doubles rule not imposed), stutter (n = 5 uniform substitutions),
fixed points, exact obstacle pattern ("swap" reading), coincidences after a divergence
(divergence_models testbed with the same source text), "same Δ" agreement. 100 keys."""
import sys
import random
import numpy as np
import testbed
from small_order_test import make_key, enc
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_pattern_test import pattern
from obstacle_test import d0 as _d0_unused
from same_delta_models import agreement
from testkey import true_blocks
from lineage_coincidence import count
from divergence_models import corpus
from stats import load_eyes

LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def source(kind, n=400000, seed=0):
    rnd = random.Random(seed)
    if kind == "uniforme":
        return "".join(rnd.choice(LET) for _ in range(n))
    return testbed.english_letters()


def edit_stutter(pl, n, rnd):
    out = list(pl); e5 = list(out[8])
    for k in rnd.sample(range(21, 47), n):
        e5[k] = rnd.choice([c for c in LET if c != e5[k]])
    out[8] = "".join(e5); return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    NODBL = '--nodouble' in sys.argv
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    rng = np.random.default_rng(29); rnd = random.Random(29)
    orig = testbed.english_letters
    print("text       β          flat  0dbl  texture  fixpts  motif  ALL   | div. coinc.  same-Δ")
    for kind in ("anglais", "uniforme"):
        T = source(kind)
        testbed.english_letters = lambda T=T: T
        base = testbed.build_plaintexts()
        testbed.english_letters = orig
        E1, W1 = base[0], base[1]
        d0 = next(i for i in range(1, len(E1)) if E1[i] != W1[i])
        tb = [b for b in true_blocks(base) if b[4] >= 12]
        div_pl = corpus(T, 0)
        for bkind in ("aleatoire", "8"):
            c = np.zeros(6); cs = ct = 0; agr = []
            for _ in range(R):
                for attempt in range(25):
                    q, S = make_key(bkind, 1, rng, nodouble=NODBL)
                    pl = edit_stutter(base, 5, rnd)
                    C = enc(pl, q, S)
                    if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                        break
                a = chi2(C) <= EYES_CHI
                b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                A0, B0 = enc([E1, W1], q, S)
                pe = all(A0[i] != B0[i] for i in range(d0, d0 + 4)) and all(A0[i] == B0[i] for i in range(d0 + 4, d0 + 8)) \
                    and all(A0[i] != B0[i] for i in range(d0 + 8, d0 + 12)) and all(A0[i] == B0[i] for i in range(d0 + 12, d0 + 25))
                c += [a, b, t, x, pe, a and b and t and x and pe]
                tr, su = count(enc(div_pl, q, S), names, "toutes"); cs += su["proche"]; ct += tr["proche"]
                n, ag = agreement(enc(base, q, S), tb); agr.append(ag / max(n, 1))
            print(f"{kind:9s}  {bkind:9s}  " + "  ".join(f"{v / R:.2f}" for v in c) + f"  |  {cs / ct:.3f}        {np.median(agr):.3f}", flush=True)
