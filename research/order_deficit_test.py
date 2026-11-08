"""Signature of a β of order L with doubles forbidden by construction: dip at d ≡ 1 (mod L) (§29).

If β^L = id and the card read is never re-read at the next step, it is not re-read either (barring
disturbance by the swaps) L, 2L… steps later: dips at distances d = 1 + L, 1 + 2L, 1 + 3L.
We compare the sum of repeats at distances {1+L, 1+2L, 1+3L} between the eyes and the model
(Lymm k = 1, no-doubles rule, uniform or English plaintext), and a random β (same rule).
P = share of keys whose sum is >= that of the eyes."""
import sys
import numpy as np
import testbed
from small_order_test import make_key, enc
from gap_profile_order import gaps
from uniform_plaintext_test import source
from stats import load_eyes

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    ge = gaps(M, 40)
    rng = np.random.default_rng(31)
    orig = testbed.english_letters
    for kind in ("uniforme", "anglais"):
        T = source(kind)
        testbed.english_letters = lambda T=T: T
        base = testbed.build_plaintexts()
        testbed.english_letters = orig
        for L in (2, 4, 8):
            ds = [1 + L, 1 + 2 * L, 1 + 3 * L]
            eyes = sum(ge[d - 1] for d in ds)
            for bkind in (str(L), "aleatoire"):
                v = []
                for _ in range(R):
                    q, S = make_key(bkind, 1, rng, nodouble=True)
                    g = gaps(enc(base, q, S), 40)
                    v.append(sum(g[d - 1] for d in ds))
                v = np.array(v)
                print(f"{kind:8s} d = {ds}  eyes {eyes:3.0f} | β {bkind:9s}: mean {v.mean():5.1f}, P(>= eyes) {np.mean(v >= eyes):.2f}", flush=True)
