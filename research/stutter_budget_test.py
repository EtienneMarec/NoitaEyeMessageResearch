"""How many differing letters are needed in the E4/E5 stutter for Lymm's model to pass? (§24)

Model: small swaps (k = 1 or 2 per slot) + random base shuffle β, homophones chosen from the
previous letter (60 or 82 slots), first trigram outside the deck (swap_context_test.make_key).
Testbed variant: E5 = E4 with n one-letter substitutions drawn at random in 21..46
(n = 2, 4, 6, 8, 10), letters drawn from English frequencies. The rest as in fair_joint_test.
Criteria: isomorphs, flat profile, 0 doubles, stutter texture, fixed points <= 1%,
obstacle read as two substitutions (§19; its "word swap" reading always fails, §23.2)."""
import sys
from itertools import combinations
import numpy as np
from testbed import build_plaintexts
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, d0
from fair_joint_test import edited, rand_letter
from context_homophone_test import enc_all
from swap_context_test import make_key
from architecture import iso_ok
from stats import load_eyes


def stutter_edit(pl, n, rng):
    """E5 (index 8): n substitutions at distinct positions of 21..46 (instead of 21 and 26)"""
    out = list(pl)
    e5 = list(out[8])
    for k in rng.choice(np.arange(21, 47), n, replace=False):
        e5[k] = rand_letter(rng, e5[k])
    out[8] = "".join(e5)
    return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    NODBL = '--nodouble' in sys.argv
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    P = "AINYOUAMINUTEBUT"
    occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
    rng = np.random.default_rng(99)
    print(f"eyes: texture {f0:.2f} identical, {r0} runs")
    print("k  β          slots  n    iso   flat  0dbl  texture  fixpts    obst(subst)  ALL    median texture (share, runs)", flush=True)
    for kswaps in (1, 2):
        for bkind in ("aleatoire",):
            for nslots in ((60,) if NODBL else (60, 82)):
                for n in (2, 4, 6, 8, 10):
                    c = np.zeros(7); tex = []
                    for _ in range(R):
                        pl0, pv0 = edited(base, rng)
                        # start again from the base text for E5, then n substitutions in 21..46
                        pl = stutter_edit(list(base), n, rng); pl[1] = pl0[1]
                        pv = list(pl); pv[1] = pv0[1]
                        for attempt in range(25):
                            slots, reads, S = make_key(kswaps, bkind, nslots, rng, nodouble=NODBL)
                            C = enc_all(pl, slots, reads, S)
                            if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                                break
                        segs = [C[k][i + 1:i + len(P)] for k, i in occ]
                        iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                        a = chi2(C) <= EYES_CHI
                        b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                        f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                        tex.append((f, r))
                        tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                        fr, run = window_stats(enc_all(pv, slots, reads, S), 0, 1, d0 + 4, d0 + 24); o = fr >= 0.8 and run >= 13
                        c += [iso, a, b, t, x, o, iso and a and b and t and x and o]
                    tex = np.array(tex)
                    print(f"{kswaps}  {bkind:9s}  {nslots:3d}  {n:2d}   " + "  ".join(f"{v / R:.2f}" for v in c)
                          + f"   ({np.median(tex[:, 0]):.2f}, {np.median(tex[:, 1]):.0f})", flush=True)
