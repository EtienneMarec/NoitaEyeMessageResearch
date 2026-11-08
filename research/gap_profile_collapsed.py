"""Profile of repeats at distance d, counting ONCE each repeat produced by the same repeated phrase
(isomorphs from Toboter's list, sources/github/ToboterXP_EyeGlyphs/isomorphs.txt, 0-indexed positions).

Under a GAK/deck-of-cards model, a repeated phrase reproduces its internal repeats at each
occurrence: counting them N times artificially inflates some distances.
"""
import ast
import random
from pathlib import Path
from stats import load_eyes
from gap_profile import random_msgs

HERE = Path(__file__).parent
names, M = load_eyes()
ISO = ast.literal_eval((HERE / "sources/github/ToboterXP_EyeGlyphs/isomorphs.txt").read_text())
MAXD = 40


def event_key(mi, i, d):
    """Key of a repeat (message mi, positions i and i+d). If it is internal to an occurrence
    of an isomorph (repeated letters of the pattern), it is attached to the pattern."""
    best = None
    for pat, occ in ISO.items():
        for m, p in occ:
            if m == mi and p <= i and i + d < p + len(pat):
                r = i - p
                if pat[r] != "." and pat[r] == pat[r + d]:
                    if best is None or len(pat) > len(best[0]):
                        best = (pat, r)
    if best:
        return ("iso", best[0], best[1], d)
    return ("pos", i, d, M[mi][i])  # also deduplicates shared sections (same position, same value)


def collapsed_profile(msgs, use_iso=True):
    keys = set()
    tests = [0] * (MAXD + 1)
    cnt = [0] * (MAXD + 1)
    for mi, m in enumerate(msgs):
        for d in range(1, MAXD + 1):
            for i in range(len(m) - d):
                tests[d] += 1
                if m[i] == m[i + d]:
                    k = event_key(mi, i, d) if use_iso else ("pos", i, d, m[i])
                    if k not in keys:
                        keys.add(k)
                        cnt[d] += 1
    return cnt, tests


if __name__ == "__main__":
    random.seed(2)
    raw, _ = collapsed_profile(M, use_iso=False)
    col, tests = collapsed_profile(M, use_iso=True)
    R = 300
    sims = [collapsed_profile(random_msgs(), use_iso=False)[0] for _ in range(R)]
    print(" d  raw   grouped   expected  z(grouped)")
    for d in range(1, 16):
        exp = sum(s[d] for s in sims) / R
        z = (col[d] - exp) / exp ** 0.5 if exp else 0
        print(f"{d:2d} {raw[d]:5d} {col[d]:8d} {exp:9.1f} {z:8.2f}")
