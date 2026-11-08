"""Exact obstacle pattern depending on the text reading, in Lymm's 1-swap model (§32).

Readings of W1 relative to E1 (the testbed places a first word at d0..d0+3, a shared segment at d0+4..d0+7,
a second word at d0+8..d0+11) (tokens):
  echange : the two words swapped (Lymm's reading);
  mots    : two different 4-letter words (drawn at random) at the same places;
  unique  : only the first word differs; 33-36 (d0+8..d0+11) would then be due to the disturbed cards;
  unique1 : one single different letter at d0 (the rest of the bursts comes from the hidden state).
Model: flat_plaintext_test.make_key (1 swap, random β, no doubles). Real English, 20 draws of the
words, R keys. We also report the share of keys where only the first half (4 different then 4 identical)
holds, and the share where the end (13 identical) holds given the rest."""
import sys
import random
import numpy as np
from testbed import english_letters
from flat_plaintext_test import build, make_key, enc

LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def variant(E1, W1, d0, kind, rnd):
    if kind == "echange":
        return W1
    w = list(E1)
    if kind == "mots":
        idx = list(range(d0, d0 + 4)) + list(range(d0 + 8, d0 + 12))
    elif kind == "unique":
        idx = list(range(d0, d0 + 4))
    else:
        idx = [d0]
    for k in idx:
        w[k] = rnd.choice([c for c in LET if c != w[k]])
    return "".join(w)


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    T = english_letters()[:400000]
    rnd = random.Random(35); rng = np.random.default_rng(35)
    bases = [build(T, LET, seed=s)[0] for s in range(20)]
    res = {k: [0, 0, 0] for k in ("echange", "mots", "unique", "unique1")}
    for r in range(R):
        E1, W1 = bases[r % 20][0], bases[r % 20][1]
        d0 = next(i for i in range(1, len(E1)) if E1[i] != W1[i])
        q, S = make_key(26, rng)
        A = enc([E1], LET, q, S)[0]
        for kind in res:
            B = enc([variant(E1, W1, d0, kind, rnd)], LET, q, S)[0]
            m1 = all(A[i] != B[i] for i in range(d0, d0 + 4))
            m2 = all(A[i] == B[i] for i in range(d0 + 4, d0 + 8))
            m3 = all(A[i] != B[i] for i in range(d0 + 8, d0 + 12))
            m4 = all(A[i] == B[i] for i in range(d0 + 12, d0 + 25))
            res[kind][0] += m1 and m2 and m3 and m4
            res[kind][1] += m1 and m2
            res[kind][2] += m1 and m2 and m3
    for kind, (h, a, b) in res.items():
        print(f"{kind:8s}: exact pattern {h}/{R} = {h / R:.4f}; 4≠ then 4=: {a / R:.3f}; then 4≠: {b / R:.3f}; "
              f"P(13 identical | start) = {h / max(b, 1):.3f}", flush=True)
