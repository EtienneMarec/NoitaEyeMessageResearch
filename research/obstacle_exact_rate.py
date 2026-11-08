"""Precise probability of the exact obstacle pattern (4/4/4/13) in Lymm's model (§31).

Model: flat_plaintext_test.make_key (1 swap per letter, random β, no doubles), first symbol outside the
deck. W1 = E1 with the two 4-letter words swapped around a 4-letter segment (Lymm's reading).
Texts: real English and flattened plaintext (γ = 0.25). We also draw 20 different realisations of the words
("build" with different seeds) so as not to depend on a single draw. R keys in total."""
import sys
import random
from collections import Counter
import numpy as np
from testbed import english_letters
from flat_plaintext_test import build, make_key, enc

LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    T0 = english_letters()[:400000]
    fr = Counter(T0); p = np.array([fr[c] for c in LET], float); p /= p.sum()
    rnd = random.Random(34); rng = np.random.default_rng(34)
    for g in ("real", 0.25):
        if g == "real":
            T = T0
        else:
            w = p ** g; w /= w.sum(); T = "".join(rnd.choices(LET, weights=w, k=len(T0)))
        bases = [build(T, LET, seed=s)[0] for s in range(20)]
        hits = 0; inner = 0
        for r in range(R):
            E1, W1 = bases[r % 20][0], bases[r % 20][1]
            d0 = next(i for i in range(1, len(E1)) if E1[i] != W1[i])
            q, S = make_key(26, rng)
            A, B = enc([E1, W1], LET, q, S)
            m1 = all(A[i] != B[i] for i in range(d0, d0 + 4))
            m2 = all(A[i] == B[i] for i in range(d0 + 4, d0 + 8))
            m3 = all(A[i] != B[i] for i in range(d0 + 8, d0 + 12))
            m4 = all(A[i] == B[i] for i in range(d0 + 12, d0 + 25))
            hits += m1 and m2 and m3 and m4
            inner += m1 and m2
        print(f"{('real English' if g == 'real' else 'γ = 0.25'):12s}: exact pattern {hits}/{R} = {hits / R:.4f}; "
              f"first part (4 different then 4 identical) {inner / R:.3f}", flush=True)
