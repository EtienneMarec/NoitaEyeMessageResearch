"""Quantitative test of the "Stutter Section": between two messages with almost identical text
(point edits), share of identical positions and number of =/. alternations in the
zone following the first edit, before the insertion. Eyes: E4/E5, positions 21..46.
Test corpus: synthetic E4/E5, edits at 21 and 26, insertion at 47 (window 21..46),
first symbol outside the deck. Joint criteria: flat profile, 0 doubles, stutter texture.
"""
import sys
import numpy as np
from explore import xgak_encrypt, encode
from explore2 import make_key_nodbl
from testbed import build_plaintexts
from swap_model_test import chi2
from stats import load_eyes


def texture(a, b, s=21, e=46):
    eq = [a[i] == b[i] for i in range(s, e + 1)]
    runs = 1 + sum(eq[i] != eq[i - 1] for i in range(1, len(eq)))
    return sum(eq) / len(eq), runs


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    names, M = load_eyes()
    eyes_chi = chi2(M)
    f0, r0 = texture(M[6], M[8])
    print(f"eyes E4/E5 21..46: {f0:.2f} of identical positions, {r0} = / . runs; chi² {eyes_chi:.1f}")
    ok_tex = lambda f, r: abs(f - f0) <= 0.15 and r >= r0 - 4
    plains = [m[1:] for m in build_plaintexts()]
    rng = np.random.default_rng(31)
    print("τ             β          homoph.  med. frac.=  med. runs       P(texture)  P(chi²<=eyes)  P(all, 0 doubles)")
    for tkind in ("reinsertion", "echange"):
        for bkind in ("aucun", "coupe1", "cycle83", "aleatoire"):
            for homo in (False, True):
                F, Rn, tex, flat, allok = [], [], 0, 0, 0
                for _ in range(R):
                    slots, reads, S = make_key_nodbl(tkind, bkind, homo, rng)
                    C = [[1000 + j] + xgak_encrypt(encode(m, slots), reads, S).tolist() for j, m in enumerate(plains)]
                    f, r = texture(C[6], C[8]); F.append(f); Rn.append(r)
                    c = chi2(C); d = sum(x == y for m in C for x, y in zip(m, m[1:]))
                    t = ok_tex(f, r); tex += t; flat += c <= eyes_chi; allok += t and c <= eyes_chi and d == 0
                print(f"{tkind:12s}  {bkind:9s}  {'yes' if homo else 'no':6s}  {np.median(F):8.2f}     {np.median(Rn):8.0f}"
                      f"        {tex/R:5.2f}       {flat/R:5.2f}          {allok/R:5.2f}", flush=True)
