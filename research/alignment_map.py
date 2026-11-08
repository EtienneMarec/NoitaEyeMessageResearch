"""Shifted alignments of shared plaintext between two messages (GAK model).

For a shift δ (position j = i + δ in the second message), we look for maximal windows with no isomorphism
conflict. Each window is bounded by conflicts, which prove a plaintext difference (see plaintext_diff_map.py).
A window is kept as likely shared text if it contains enough positive evidence:
  * shared repeats: A[i]=A[i'] and B[i+δ]=B[i'+δ];
  * identical symbols (A[i]=B[i+δ]), which only really count at δ=0.
The false-positive rate is estimated by running exactly the same search on random data.

Positions are 0-indexed.
"""
import random
import sys
from itertools import combinations
from stats import load_eyes
from gap_profile import random_msgs

names, M = load_eyes()
DMAX = 20


def windows(A, B, d):
    """Maximal conflict-free windows along the diagonal δ = d."""
    idx = [i for i in range(len(A)) if 0 <= i + d < len(B)]
    if not idx:
        return []
    out = []
    start = idx[0]
    fA, fB = {}, {}
    k = 0
    i = start
    # greedy sweep: extend while the correspondence stays a partial bijection
    while i <= idx[-1]:
        x, y = A[i], B[i + d]
        if fA.get(x, y) != y or fB.get(y, x) != x:
            out.append((start, i - 1))
            # restart right after the last conflicting occurrence
            j = i - 1
            fA, fB = {x: y}, {y: x}
            while j >= start and fA.get(A[j], B[j + d]) == B[j + d] and fB.get(B[j + d], A[j]) == A[j]:
                fA[A[j]] = B[j + d]; fB[B[j + d]] = A[j]; j -= 1
            start = j + 1
        else:
            fA[x], fB[y] = y, x
        i += 1
    out.append((start, idx[-1]))
    return out


def evidence(A, B, d, s, e):
    rep = 0
    for i in range(s, e + 1):
        for j in range(i + 1, e + 1):
            if A[i] == A[j] and B[i + d] == B[j + d]:
                rep += 1
    same = sum(A[i] == B[i + d] for i in range(s, e + 1))
    return rep, same


def scan(msgs, pairs, min_rep=2, min_len=8):
    found = []
    for a, b in pairs:
        A, B = msgs[a], msgs[b]
        for d in range(-DMAX, DMAX + 1):
            for s, e in windows(A, B, d):
                if e - s + 1 < min_len:
                    continue
                rep, same = evidence(A, B, d, s, e)
                score_ok = rep >= min_rep or (d == 0 and same >= 3)
                if score_ok:
                    found.append((a, b, d, s, e, rep, same))
    return found


if __name__ == "__main__":
    pairs = list(combinations(range(9), 2))
    res = scan(M, pairs)
    random.seed(3)
    R = 30
    fp = [len([r for r in scan(random_msgs(), pairs) if r[2] != 0 or r[6] < 3]) for _ in range(R)]
    print(f"Random baseline: {sum(fp)/R:.1f} windows kept per corpus on average "
          f"(min {min(fp)}, max {max(fp)}), with >= 2 shared repeats\n")
    print("pair       δ   window (msg1)    window (msg2)    L  shared rep.   identical")
    for a, b, d, s, e, rep, same in sorted(res, key=lambda r: (r[0], r[1], r[3])):
        print(f"{names[a]}/{names[b]}  {d:+3d}   {s:3d}..{e:<3d}         {s+d:3d}..{e+d:<3d}       {e-s+1:3d}  {rep:5d}        {same:4d}")
