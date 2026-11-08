"""The "same shift" test (same_delta_test.py) applied to the models, on the testbed (§25).

Idea: in a GAK dominated by a base shuffle β (σ_p = β∘τ_p with small τ_p, Lymm's model), the deck at
time t is roughly D0∘β^t, disturbed. The correspondence between two occurrences of the same plaintext shifted
by Δ is then roughly D0 β^Δ D0^-1 on the little-disturbed cards: two DIFFERENT message pairs at the
same Δ should therefore partly agree. Eyes: 2 agreements over 36 shared cards (same_delta_test.py).

Testbed: true blocks (testkey.true_blocks, length >= 12, edges trimmed by 2), comparisons between different
message pairs of the same Δ, with no common arrival message. We report the mean agreement rate
and the probability of a rate <= that of the eyes (2/36). Model tokens: "progressif" = progressive, "echange" = swap."""
import sys
from collections import Counter
from itertools import combinations
import numpy as np
from testbed import build_plaintexts, ALPHA
from testkey import true_blocks
from explore import xgak_encrypt
from family_zoo import make_key as zoo_key
from context_homophone_test import enc_all
from swap_context_test import make_key as swap_key

P = 83
TRIM = 2
EYES = 2 / 36


def agreement(C, blocks):
    maps = []
    for a, i, b, j, L in blocks:
        if i == j and a != b:
            continue
        m = {C[a][i + k]: C[b][j + k] for k in range(TRIM, L - TRIM)}
        d = j - i
        if d < 0:
            m = {v: k for k, v in m.items()}; d = -d; a, b = b, a
        maps.append(((a, b), d, m))
    n = agree = 0
    for (p1, d1, m1), (p2, d2, m2) in combinations(maps, 2):
        if d1 != d2 or set(p1) == set(p2) or p1[1] == p2[1]:
            continue
        com = set(m1) & set(m2)
        n += len(com); agree += sum(m1[c] == m2[c] for c in com)
    return n, agree


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    plains = build_plaintexts()
    seqs = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in plains]
    tb = [b for b in true_blocks(plains) if b[4] >= 12]
    rng = np.random.default_rng(31)
    print(f"{len(tb)} true blocks; eyes: agreement rate {EYES:.3f}")
    MODELS = ["progressif", "swap k=1 + homoph. 60", "swap k=1 no homoph.", "swap k=4 no homoph.",
              "reinsertion + aleatoire", "retournement + aleatoire", "reinsertion + riffle", "GAK random (S83)"]
    for lab in MODELS:
        rates, ns = [], []
        for _ in range(R):
            if lab == "progressif":
                W = rng.permutation(P); x = rng.choice(P, len(ALPHA), replace=False)
                C = [[0] + [int(W[(x[c] + t + 1) % P]) for t, c in enumerate(s)] for s in seqs]
            elif lab.startswith("swap") and "homoph" in lab and "no homoph" not in lab:
                slots, reads, S = swap_key(1, "aleatoire", 60, rng, nodouble=True)
                C = enc_all(plains, slots, reads, S)
            elif lab.startswith("swap"):
                k = int(lab.split("k=")[1].split()[0])
                slots, reads, S = swap_key(k, "aleatoire", len(ALPHA), rng)
                C = enc_all(plains, slots, reads, S)
            elif lab.startswith("GAK"):
                reads = rng.choice(P, len(ALPHA), replace=False)
                S = np.array([rng.permutation(P) for _ in ALPHA], np.int64)
                C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs]
            else:
                t, b = lab.split(" + ")
                reads, S = zoo_key(t, b, 0, rng, len(ALPHA))
                C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs]
            n, a = agreement(C, tb)
            if n:
                rates.append(a / n); ns.append(n)
        rates = np.array(rates)
        print(f"{lab:28s}: mean agreement rate {rates.mean():.3f} (median {np.median(rates):.3f}), "
              f"P(rate <= eyes) = {(rates <= EYES).mean():.2f}, cards compared (median) {np.median(ns):.0f}", flush=True)
