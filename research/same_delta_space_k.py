"""The "same shift" test (§23) applied to the space model with a moderate shuffle σ = τ_k ∘ β (§41).

The regime k ≤ 2 is the only one where the keyed-deck attack works (moderate_space_curriculum.py). In this regime,
the cipher is almost progressive: two DIFFERENT message pairs at the same Δ should partly
agree, whatever β (the test does not depend on the cycle type). Eyes: 2 agreements over 36 shared cards.
Testbed with spaces (testbed_spaces, same texts as the ABC), true blocks of length ≥ 12, edges trimmed by 2,
same comparison rule as same_delta_models.agreement. We report the mean agreement rate and
P(X ≤ 2 | 36 cards, model rate), averaged over the keys.
Usage: python same_delta_space_k.py [R]"""
import sys
from math import comb
import numpy as np
import testbed_spaces as tbs
import space_model_test as sm
from testkey import true_blocks
from same_delta_models import agreement
from explore import xgak_encrypt


def p_le(x, n, p):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    rng = np.random.default_rng(7)
    corp = [tbs.build_plaintexts(seed=s, word_start=True) for s in range(5)]
    blocks = [[b for b in true_blocks(pl) if b[4] >= 12] for pl in corp]
    print("true blocks per corpus: " + ", ".join(str(len(b)) for b in blocks) + "; eyes 2/36 = 0.056")
    for k in ("0", "1", "2", "4", "8", "16", "aleatoire"):
        rates, ps = [], []
        for r in range(R):
            c = r % len(corp)
            q, S = sm.make_key("_", k, True, rng)
            C = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in corp[c]]
            n, a = agreement(C, blocks[c])
            if n:
                rates.append(a / n); ps.append(p_le(2, 36, a / n))
        print(f"k={k:9s} mean agreement rate {np.mean(rates):.3f} (min {np.min(rates):.3f}); "
              f"mean P(≤ 2/36) {np.mean(ps):.3f}; keys with rate ≤ 0.10: {np.mean(np.array(rates) <= 0.10):.2f}",
              flush=True)
