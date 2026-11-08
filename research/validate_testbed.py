"""Validation on test messages (known truth):
  1. does the statistical fingerprint look like that of the eyes?
  2. does the mapping (alignment_map) recover the real shared blocks?
  3. does the mechanism sweep (qscan) recover the right mechanism?
"""
import sys
from itertools import combinations
import numpy as np
from testbed import build_plaintexts, make_key, encrypt_all
from deckcipher import base_shuffles, RULES
from stats import fingerprint
import alignment_map as am
import qscan

bases = base_shuffles()
CASES = [
    ("natural: top swap then deal into 3 piles", bases["deal3fwd"], 0, 0),
    ("natural: card put back on top then riffle", bases["outshuffle"], 1, 1),
    ("RANDOM β (unknown) + top swap [Lymm's model]", np.random.default_rng(7).permutation(83), 0, 0),
]


def true_blocks(P1, P2, minlen=8):
    """Plaintext segments actually shared (maximal common substrings), with shift."""
    out = []
    for i in range(len(P1)):
        for j in range(len(P2)):
            if (i == 0 or j == 0 or P1[i - 1] != P2[j - 1]):
                k = 0
                while i + k < len(P1) and j + k < len(P2) and P1[i + k] == P2[j + k]:
                    k += 1
                if k >= minlen:
                    out.append((i, j, k))
    return out


if __name__ == "__main__":
    plains = build_plaintexts()
    key = make_key()
    for label, beta, rule, order in CASES:
        C = encrypt_all(plains, key, beta, rule, order)
        doubles = sum(1 for m in C for a, b in zip(m, m[1:]) if a == b)
        fp = fingerprint(C)
        print(f"\n=== {label} ===")
        print(f"doubles: {doubles} ; IoC {fp['ioc']} ; gaps d=1..8 {fp['gap_counts'][:8]} ; "
              f"repeated digraphs {fp['digraph_rep']} ; trigraphs {fp['trigraph_rep']} ; isomorphs L10 {fp['isomorphs_L10']}")
        # 2. mapping: blocks found vs true shared (shifted) blocks
        found = am.scan(C, list(combinations(range(9), 2)))
        hit = miss = 0
        for a, b in combinations(range(9), 2):
            for i, j, k in true_blocks(plains[a], plains[b]):
                if k < 12:
                    continue
                d = j - i
                ok = any(fa == a and fb == b and fd == d and fs <= i + k // 2 <= fe for fa, fb, fd, fs, fe, *_ in found)
                hit += ok; miss += not ok
        fp_windows = 0
        for fa, fb, fd, fs, fe, rep, same in found:
            real = any(j - i == fd and i <= fe and i + k >= fs for i, j, k in true_blocks(plains[fa], plains[fb], 6))
            fp_windows += not real
        print(f"mapping: {hit} true blocks (>=12 letters) found, {miss} missed; {fp_windows} false windows out of {len(found)}")
        # 3. sweep
        res = qscan.scan(C)
        qscan.report(res, top=3)
