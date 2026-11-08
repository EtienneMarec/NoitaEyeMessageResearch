"""Gap profile (repeats at distance d): eyes versus Lymm's model with β of order 4 or 8 (§27).

For each model (k = 1 swap, no homophones, testbed), we compute the number of repeats at
distance d = 1..24 (same message), averaged over R keys, and the correlation of this mean profile with the eyes'.
We also report the median spike chi² (swap_model_test.chi2, d = 2..40), and the share of keys <= eyes.
The eyes count raw repeats (shared sections included), like the testbed."""
import sys
import numpy as np
from stats import load_eyes
from swap_model_test import chi2
from testbed import build_plaintexts
from small_order_test import make_key, enc


def gaps(C, dmax=24):
    g = np.zeros(dmax + 1)
    for m in C:
        for d in range(1, dmax + 1):
            g[d] += sum(1 for i in range(1, len(m) - d) if m[i] == m[i + d])
    return g[1:]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    names, M = load_eyes()
    ge = gaps(M)
    print("eyes     d=1..24:", " ".join(f"{int(x):2d}" for x in ge), f" chi² {chi2(M):.0f}")
    base = build_plaintexts()
    rng = np.random.default_rng(3)
    for bkind in ("4", "8", "aleatoire"):
        G = []; X = []
        for _ in range(R):
            q, S = make_key(bkind, 1, rng)
            C = enc(base, q, S)
            G.append(gaps(C)); X.append(chi2(C))
        G = np.array(G); m = G.mean(0)
        r = np.corrcoef(m, ge)[0, 1]
        print(f"β {bkind:9s} d=1..24:", " ".join(f"{x:2.0f}" for x in m), f" med. chi² {np.median(X):.0f}, "
              f"P(chi² <= eyes) {np.mean(np.array(X) <= chi2(M)):.2f}, corr. mean profile/eyes {r:.2f}", flush=True)
