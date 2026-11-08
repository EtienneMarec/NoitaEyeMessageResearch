"""Joint test of the structured XGAK families on the testbed (first trigram outside the deck, no
homophones, 40 keys per family). Criteria from the eyes:
  (1) flat gap profile: chi² <= 63.2          (2) no doubles
  (3) texture of the Stutter Section E4/E5 21..46: identical share 0.42 ± 0.15, >= 7 runs
  (4) fixed points after an insertion <= 1% (eyes: 0 over ~210 pairs)
Families: τ (the card read is reinserted / swapped / put on top) × β (none, cut 1, 83-cycle, random),
with explore2's "no doubles" construction (destinations never re-read).
"""
import sys
import numpy as np
from explore import xgak_encrypt, tau_for, make_beta
from explore2 import make_key_nodbl
from testbed import build_plaintexts, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from stats import load_eyes

names, M = load_eyes()
EYES_CHI = chi2(M)
f0, r0 = texture(M[6], M[8])
plains = build_plaintexts()
seqs = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in plains]
R = int(sys.argv[1]) if len(sys.argv) > 1 else 40
rng = np.random.default_rng(77)
print(f"eyes: chi² {EYES_CHI:.1f}, texture {f0:.2f}/{r0}, fixed points 0/210; {R} keys per family")
print("τ            β           P(flat) P(0 doubles) P(texture) P(fixpts<=1%)     med. fixpts     P(ALL)")
for tkind in ("reinsertion", "echange", "dessus"):
    for bkind in ("aucun", "coupe1", "cycle83", "aleatoire"):
        c1 = c2 = c3 = c4 = call = 0; fxs = []
        for _ in range(R):
            slots, reads, S = make_key_nodbl(tkind, bkind, False, rng)
            C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs]
            a = chi2(C) <= EYES_CHI
            b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
            f, r = texture(C[6], C[8]); c = abs(f - f0) <= 0.15 and r >= r0 - 4
            t, fx = blocks_fixed(C); fr = fx / t; d = fr <= 0.01
            fxs.append(fr)
            c1 += a; c2 += b; c3 += c; c4 += d; call += a and b and c and d
        print(f"{tkind:11s}  {bkind:9s}  {c1/R:5.2f}   {c2/R:5.2f}       {c3/R:5.2f}      {c4/R:5.2f}           "
              f"{np.median(fxs):5.2f}          {call/R:5.2f}", flush=True)
