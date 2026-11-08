"""Testbed WITH spaces (symbol "_"), same architecture as testbed.build_plaintexts (§26).

The English text keeps its word separators (any run of non-letters becomes "_"). The obstacle is
built as in Lymm's reading "EAST TO WEST / WEST TO EAST": two 4-letter words with no shared letter
at the same place, separated by "_TO_", swapped between E1 and W1. The edits of group C are
substitutions and insertions of LETTERS; the stutter may also move a space (option)."""
import re
import random
from pathlib import Path

HERE = Path(__file__).parent
ALPHA_S = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789_"


def english_with_spaces():
    t = (HERE / "corpus/en.txt").read_text(encoding="utf-8", errors="ignore")
    i = t.find("CHAPTER I.")
    t = t[i if i >= 0 else 0:].upper()
    return re.sub(r"[^A-Z]+", "_", t)


def four_letter_words(T):
    ws = [w for w in T.split("_") if len(w) == 4]
    return ws


def build_plaintexts(seed=0, word_start=False):
    rng = random.Random(seed)
    T = english_with_spaces()
    pos = [rng.randrange(1000, len(T) - 5000)]

    def take(n):
        if word_start:  # start each piece at a word start (realistic variant, §39)
            pos[0] = T.find("_", pos[0]) + 1
        s = T[pos[0]:pos[0] + n]
        pos[0] += n + rng.randrange(50, 400)
        return s

    W4 = four_letter_words(T)
    while True:
        a, b = rng.choice(W4), rng.choice(W4)
        if all(x != y for x, y in zip(a, b)):
            break
    OA, P = take(20) + "_", take(22)
    A = [
        "1" + OA + a + "_TO_" + b + "_" + P + take(10) + P + take(24),
        "2" + OA + b + "_TO_" + a + "_" + P + take(12) + P + take(26),
        "3" + OA + take(9) + "_TO_" + take(4) + "_" + P + take(17) + P + take(30),
    ]
    OBC, OC, TC = take(5), take(15), take(95)
    X = take(28)
    TC = TC[:45] + X + TC[45 + 28:]
    c1 = "7" + OBC + OC + TC
    c2 = list("8" + OBC + OC + TC)
    c2[21:25] = list(take(5))
    c2.insert(66, "E")
    c3 = list("9" + OBC + OC + TC)
    c3[21] = "Q" if c3[21] != "Q" else "Z"
    c3[26] = "X" if c3[26] != "X" else "Z"
    c3.insert(47, "S")
    C = [c1, "".join(c2), "".join(c3)]
    PB = take(20)
    B = [
        "4" + OBC + take(8) + PB + take(70),
        "5" + OBC + take(14) + PB + take(80),
        "6" + OBC + take(13) + PB + take(30) + X + take(30),
    ]
    return [A[0], A[1], A[2], B[0], B[2], B[1], C[0], C[1], C[2]]


def obstacle_window(plains):
    """d0 = first E1/W1 difference"""
    E1, W1 = plains[0], plains[1]
    return next(i for i in range(1, len(E1)) if E1[i] != W1[i])


if __name__ == "__main__":
    pl = build_plaintexts()
    for m in pl:
        print(len(m), m[:70])
    print("d0 =", obstacle_window(pl), "share of spaces:", round(sum(m.count("_") for m in pl) / sum(map(len, pl)), 3))
