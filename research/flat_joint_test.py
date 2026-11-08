"""Joint battery of Lymm's model with a flattened plaintext (§31).

i.i.d. plaintext with frequencies ∝ p_english^γ (γ = 1: English frequencies; γ = 0.25: flattened), plus real English.
Model: flat_plaintext_test.make_key (1 swap, random β, no doubles), first symbol outside the deck.
Stutter: E5 = E4 with n substitutions in 21..46 (n = 8 or 12; number unknown in the eyes).
Obstacle: loose (W1 = E1 with two substitutions at d0 and d0+8; window d0+4..d0+24: >= 80% and run
>= 13, as in §19) and exact (4/4/4/13 pattern, testbed's "swap" reading). 200 keys."""
import sys
import random
from itertools import combinations
from collections import Counter
import numpy as np
from testbed import english_letters
from flat_plaintext_test import build, make_key, enc
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from architecture import iso_ok
from stats import load_eyes

LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    names, M = load_eyes(); E = chi2(M); f0, r0 = texture(M[6], M[8])
    T0 = english_letters()[:400000]
    fr = Counter(T0); p = np.array([fr[c] for c in LET], float); p /= p.sum()
    rnd = random.Random(33); rng = np.random.default_rng(33)
    print("text           n   iso   flat  0dbl  texture  fixpts  obst.loose   obst.exact  ALL(loose)    ALL(exact)")
    for g in ("real", 1.0, 0.25):
        if g == "real":
            T = T0
        else:
            w = p ** g; w /= w.sum(); T = "".join(rnd.choices(LET, weights=w, k=len(T0)))
        base, P = build(T, LET)
        E1, W1 = base[0], base[1]
        d0 = next(i for i in range(1, len(E1)) if E1[i] != W1[i])
        occ = [(k, i) for k in range(3) for i in range(1, len(base[k])) if base[k].startswith(P, i)]
        for n in (8, 12):
            c = np.zeros(9)
            for _ in range(R):
                q, S = make_key(26, rng)
                pl = list(base); e5 = list(pl[8])
                for k in rnd.sample(range(21, 47), n):
                    e5[k] = rnd.choice([x for x in LET if x != e5[k]])
                pl[8] = "".join(e5)
                C = enc(pl, LET, q, S)
                segs = [C[k][i + 1:i + len(P)] for k, i in occ]
                iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                a = chi2(C) <= E
                b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                w1 = list(E1)
                for k in (d0, d0 + 8):
                    w1[k] = rnd.choice([y for y in LET if y != w1[k]])
                A0, B0 = enc([E1, "".join(w1)], LET, q, S)
                eq = [A0[i] == B0[i] for i in range(d0 + 4, d0 + 25)]
                run = best = 0
                for e in eq:
                    run = run + 1 if e else 0; best = max(best, run)
                os_ = sum(eq) / len(eq) >= 0.8 and best >= 13
                A1, B1 = enc([E1, W1], LET, q, S)
                oe = all(A1[i] != B1[i] for i in range(d0, d0 + 4)) and all(A1[i] == B1[i] for i in range(d0 + 4, d0 + 8)) \
                    and all(A1[i] != B1[i] for i in range(d0 + 8, d0 + 12)) and all(A1[i] == B1[i] for i in range(d0 + 12, d0 + 25))
                core = iso and a and b and t and x
                c += [iso, a, b, t, x, os_, oe, core and os_, core and oe]
            lab = "real English" if g == "real" else f"γ = {g}"
            print(f"{lab:13s} {n:2d}   " + "  ".join(f"{v / R:.2f}" for v in c), flush=True)
