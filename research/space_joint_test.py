"""Joint battery of the space model, on equal assumptions with Lymm's model (§32).

Model (space_model_test.make_key): letters → β (random derangement), space → random σ, no-doubles
rule; FIRST SYMBOL INSIDE the deck (ordinary digit) or outside the deck.
Testbed with spaces (testbed_spaces). Stutter: E5 = E4 with n LETTERS substituted in 21..41, spaces
unchanged (same assumption as Lymm's model, §31.3, which requires about 12 letters).
Criteria: isomorphs, flat, 0 doubles, texture, fixed points, exact obstacle pattern, ALL.
Coincidences after a divergence: divergence_models testbed with spaced text, 10 corpora.
Lymm (1 swap, space = ordinary letter) on the same testbed for comparison."""
import sys
import random
from itertools import combinations
import numpy as np
import testbed_spaces as tbs
import space_model_test as sm
from explore import xgak_encrypt
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from lineage_coincidence import count
from divergence_models import corpus
from formulaic_test import lymm_key
from architecture import iso_ok
from stats import load_eyes

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def enc(msgs, q, S, first_in):
    a = 0 if first_in else 1
    return [([] if first_in else [0]) + xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m[a:]], np.int64), q, S).tolist()
            for m in msgs]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    names, M = load_eyes(); E = chi2(M); f0, r0 = texture(M[6], M[8])
    base = tbs.build_plaintexts()
    d0 = tbs.obstacle_window(base)
    P = base[0][d0 + 14:d0 + 14 + 18]
    occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
    T = tbs.english_with_spaces()
    dcs = [corpus(T, s) for s in range(10)]
    rnd = random.Random(36); rng = np.random.default_rng(36)
    print("model           1st    n   iso   flat  0dbl  texture  fixpts  motif  ALL   | div. coinc. (per corpus)")
    for model in ("espace", "Lymm k=1"):
        for first_in in ((True, False) if model == "espace" else (False,)):
            for n in (8, 12):
                c = np.zeros(7); cs = ct = 0; per = []
                for it in range(R):
                    for attempt in range(25):
                        q, S = sm.make_key("_", "aleatoire", True, rng) if model == "espace" else lymm_key(rng)
                        pl = list(base); e5 = list(pl[8])
                        idx = [k for k in range(21, 42) if e5[k] != "_"]
                        for k in rnd.sample(idx, min(n, len(idx))):
                            e5[k] = rnd.choice([x for x in LETTERS if x != e5[k]])
                        pl[8] = "".join(e5)
                        C = enc(pl, q, S, first_in)
                        if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                            break
                    segs = [C[k][i + 1:i + len(P)] for k, i in occ]
                    iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                    a = chi2(C) <= E
                    b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    pm = sm.pattern(C[0], C[1], d0)
                    c += [iso, a, b, t, x, pm, iso and a and b and t and x and pm]
                    if it < 50 and n == 8:
                        k = it % 10
                        tr, su = count(enc(dcs[k], q, S, first_in), names, "toutes"); cs += su["proche"]; ct += tr["proche"]
                        per.append((k, su["proche"], tr["proche"]))
                cz = ""
                if per:
                    byc = [sum(a for k2, a, b in per if k2 == k) / max(1, sum(b for k2, a, b in per if k2 == k)) for k in range(10)]
                    cz = f"{cs / ct:.3f} ({min(byc):.3f}–{max(byc):.3f})"
                print(f"{model:14s}  {'in ' if first_in else 'out'}  {n:2d}   " + "  ".join(f"{v / R:.2f}" for v in c) + f"  |  {cz}", flush=True)
