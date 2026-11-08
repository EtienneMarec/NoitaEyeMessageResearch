"""Hybrid model "letters = exactly β, space = β + small swaps" (§32).

Letters do not change the deck (exact obstacle); the space changes it a little (k swaps), so two
diverging texts keep close decks for a long time (far coincidences, as in the eyes).
Models (space_model_test.make_key, no doubles): σ_space = β∘(k swaps), k = 1, 4, 8; random σ
(space model of §26); Lymm k = 1 for all letters (formulaic_test.lymm_key).
Texts: English with spaces; flattened i.i.d. plaintext (space 18%, letters ∝ p^0.25).
Criteria (200 keys): iso, flat, 0 doubles, texture (12 letters substituted in 21..41, spaces unchanged),
fixed points, exact pattern, ALL; coincidences +1..+9 and +10..+20 (divergence_models testbed, 10 corpora, 50 keys).
Eyes (between groups): 0.020 and 0.050; (without E1/W1 and E4/E5): 0.048 and 0.036."""
import sys
import random
from collections import Counter
from itertools import combinations
import numpy as np
import testbed_spaces as tbs
import space_model_test as sm
from explore import xgak_encrypt
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from divergence_models import corpus
from formulaic_test import lymm_key
from coincidence_distance_test import split_count
from architecture import iso_ok
from stats import load_eyes

LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def enc(msgs, q, S):
    return [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in msgs]


def flat_text(n, rnd):
    T = tbs.english_with_spaces()[:300000]
    fr = Counter(c for c in T if c != "_")
    p = np.array([fr[c] for c in LET], float); p /= p.sum(); w = p ** 0.25; w /= w.sum()
    out = []
    for _ in range(n):
        out.append("_" if rnd.random() < 0.18 else rnd.choices(LET, weights=w)[0])
    s = "".join(out)
    while "__" in s:
        s = s.replace("__", "_E_")
    return s


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    names, M = load_eyes(); E = chi2(M); f0, r0 = texture(M[6], M[8])
    rnd = random.Random(38); rng = np.random.default_rng(38)
    texts = {"anglais": tbs.english_with_spaces(), "aplati": flat_text(400000, rnd)}
    print("text     model         iso   flat  0dbl  texture  fixpts  motif  ALL   | coinc. +1..9  +10..20")
    for tname, T in texts.items():
        orig = tbs.english_with_spaces
        tbs.english_with_spaces = lambda T=T: T
        base = tbs.build_plaintexts()
        tbs.english_with_spaces = orig
        d0 = tbs.obstacle_window(base)
        P = base[0][d0 + 14:d0 + 14 + 18]
        occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
        dcs = [corpus(T, s) for s in range(10)]
        for lab, kind in (("space rnd σ", "aleatoire"), ("space k=1", "1"), ("space k=4", "4"), ("space k=8", "8"), ("Lymm k=1", None)):
            c = np.zeros(7); acc = {(1, 9): [0, 0], (10, 20): [0, 0]}
            for it in range(R):
                for attempt in range(25):
                    q, S = sm.make_key("_", kind, True, rng) if kind else lymm_key(rng)
                    pl = list(base); e5 = list(pl[8])
                    idx = [k for k in range(21, 42) if e5[k] != "_"]
                    for k in rnd.sample(idx, min(12, len(idx))):
                        e5[k] = rnd.choice([x for x in LET if x != e5[k]])
                    pl[8] = "".join(e5)
                    C = enc(pl, q, S)
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
                if it < 50:
                    o = split_count(enc(dcs[it % 10], q, S), names, "toutes")
                    for kk in acc:
                        acc[kk][0] += o[kk][0]; acc[kk][1] += o[kk][1]
            print(f"{tname:8s} {lab:13s} " + "  ".join(f"{v / R:.2f}" for v in c)
                  + f"  |  {acc[(1, 9)][0] / acc[(1, 9)][1]:.3f}        {acc[(10, 20)][0] / acc[(10, 20)][1]:.3f}", flush=True)
