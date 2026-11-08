"""Why does the no-doubles rule degrade the flatness of the "β of order 8" model? (§29)

Uniform plaintext (architecture of the eyes), Lymm k = 1, β of order 8 or random, with or without the
no-doubles rule (small_order_test.make_key(nodouble=...)). We print the mean repeat profile at d = 1..24,
the median chi² and P(chi² <= eyes), over R keys."""
import sys
import random
import numpy as np
import testbed
from small_order_test import make_key, enc
from swap_model_test import chi2
from gap_profile_order import gaps
from uniform_plaintext_test import source
from stats import load_eyes

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    names, M = load_eyes(); E = chi2(M)
    T = source("uniforme")
    orig = testbed.english_letters
    testbed.english_letters = lambda: T
    base = testbed.build_plaintexts()
    testbed.english_letters = orig
    rng = np.random.default_rng(30)
    for bkind in ("8", "aleatoire"):
        for nd in (False, True):
            G, X = [], []
            for _ in range(R):
                q, S = make_key(bkind, 1, rng, nodouble=nd)
                C = enc(base, q, S)
                G.append(gaps(C)); X.append(chi2(C))
            m = np.mean(G, 0)
            print(f"β {bkind:9s} no-doubles {str(nd):5s}: med. chi² {np.median(X):5.0f}  P(<= eyes) {np.mean(np.array(X) <= E):.2f}  "
                  f"profile d=1..24: " + " ".join(f"{x:.0f}" for x in m), flush=True)
