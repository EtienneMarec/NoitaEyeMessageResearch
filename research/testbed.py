"""Test corpus with the architecture of the eyes, encrypted by a known mechanism (ground truth).

Architecture (see REPORT section 6):
  group A: digit + shared opening (21) + swapped/inserted words + phrase P + variable part + P + end
  group B/C: first 5 letters shared by the 6 messages;
  group C: three almost identical versions of one text (substitutions, 1-letter insertions);
  group B: own texts + a short shared phrase, shifted; a passage of B3 copied into C.
"""
import re
import random
import numpy as np
from pathlib import Path
from deckcipher import encrypt, N

HERE = Path(__file__).parent
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"


def english_letters():
    t = (HERE / "corpus/en.txt").read_text(encoding="utf-8", errors="ignore")
    i = t.find("CHAPTER I.")
    t = t[i if i >= 0 else 0:]
    return re.sub(r"[^A-Z]", "", t.upper())


def build_plaintexts(seed=0):
    rng = random.Random(seed)
    T = english_letters()
    pos = [rng.randrange(1000, len(T) - 5000)]

    def take(n):
        s = T[pos[0]:pos[0] + n]
        pos[0] += n + rng.randrange(50, 400)
        return s

    OA, P = take(21), take(22)
    w = [take(4) for _ in range(3)]
    A = [
        "1" + OA + w[0] + "INTO" + w[1] + P + take(10) + P + take(24),
        "2" + OA + w[1] + "INTO" + w[0] + P + take(12) + P + take(26),
        "3" + OA + take(9) + "INTO" + take(4) + P + take(17) + P + take(30),
    ]
    OBC, OC, TC = take(5), take(15), take(95)
    X = take(28)  # passage shared by B3 -> C
    TC = TC[:45] + X + TC[45 + 28:]
    c1 = "7" + OBC + OC + TC
    c2 = list("8" + OBC + OC + TC)
    c2[21:25] = list(take(5))                 # substitution + 1 more letter
    c2.insert(66, "E")                         # insertion of a letter
    c3 = list("9" + OBC + OC + TC)
    c3[21] = "Q" if c3[21] != "Q" else "Z"     # two small edits ("stutter")
    c3[26] = "X" if c3[26] != "X" else "Z"
    c3.insert(47, "S")                         # insertion of a letter
    C = [c1, "".join(c2), "".join(c3)]
    PB = take(20)
    B = [
        "4" + OBC + take(8) + PB + take(70),
        "5" + OBC + take(14) + PB + take(80),
        "6" + OBC + take(13) + PB + take(30) + X + take(30),
    ]
    # order of the eyes: E1 W1 E2 W2 E3 W3 E4 W4 E5
    msgs = [A[0], A[1], A[2], B[0], B[2], B[1], C[0], C[1], C[2]]
    return msgs


def make_key(seed=0, n_letters=len(ALPHA)):
    rng = np.random.default_rng(seed)
    pos = rng.choice(np.arange(1, N), size=n_letters, replace=False)
    return {ch: int(p) for ch, p in zip(ALPHA, pos)}


def encrypt_all(msgs, key, beta, rule, order, D0=None):
    D0 = np.arange(N) if D0 is None else D0
    return [encrypt(np.array([key[ch] for ch in m], np.int64), D0, beta, rule, order).tolist() for m in msgs]


if __name__ == "__main__":
    for m in build_plaintexts():
        print(len(m), m[:60])
