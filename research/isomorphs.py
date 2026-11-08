"""Detection of maximal isomorphs between all pairs of positions.

An isomorph = two segments (message a, pos i) and (message b, pos j) of the same length
such that the letter-to-letter correspondence x -> y is a partial bijection, with at least
`min_rep` repeated letters inside the segment (otherwise any pair of segments
without repeats would be "isomorphic"). Segments of identical ciphertext at the same place
(shared text) are excluded.
"""
from stats import load_eyes


def consistent(pairs):
    f, g = {}, {}
    for x, y in pairs:
        if f.get(x, y) != y or g.get(y, x) != x:
            return False
        f[x], g[y] = y, x
    return True


def extend(A, B, i, j):
    """Largest interval [s, e) around (i, j) where the correspondence stays bijective."""
    s = 0
    e = 1
    # grow to the right then to the left, greedily
    while i + e < len(A) and j + e < len(B) and consistent(zip(A[i + s:i + e + 1], B[j + s:j + e + 1])):
        e += 1
    while i + s - 1 >= 0 and j + s - 1 >= 0 and consistent(zip(A[i + s - 1:i + e], B[j + s - 1:j + e])):
        s -= 1
    return i + s, j + s, e - s


def n_repeats(seg):
    return len(seg) - len(set(seg))


def find_isomorphs(msgs, min_len=8, min_rep=3, seed=8):
    from collections import defaultdict
    from stats import canon
    buckets = defaultdict(list)
    for a, m in enumerate(msgs):
        for i in range(len(m) - seed + 1):
            w = m[i:i + seed]
            if n_repeats(w) >= 2:
                buckets[canon(w)].append((a, i))
    found = {}
    for lst in buckets.values():
        for x in range(len(lst)):
            for y in range(x + 1, len(lst)):
                (a, i), (b, j) = lst[x], lst[y]
                A, B = msgs[a], msgs[b]
                if A[i:i + seed] == B[j:j + seed]:
                    continue
                s_i, s_j, L = extend(A, B, i, j)
                if L < min_len:
                    continue
                segA, segB = A[s_i:s_i + L], B[s_j:s_j + L]
                if n_repeats(segA) < min_rep:
                    continue
                if a == b and abs(s_i - s_j) < L:
                    continue
                found[(a, s_i, b, s_j, L)] = (segA, segB)
    # remove the isomorphs contained in a larger one with the same shift
    keys = sorted(found, key=lambda k: -k[4])
    kept = []
    for k in keys:
        a, i, b, j, L = k
        if any(a == a2 and b == b2 and (j - i) == (j2 - i2) and i2 <= i and i + L <= i2 + L2
               for a2, i2, b2, j2, L2 in kept):
            continue
        kept.append(k)
    return [(k, found[k]) for k in kept]


if __name__ == "__main__":
    names, msgs = load_eyes()
    res = find_isomorphs(msgs)
    print(len(res), "maximal isomorphs (L>=8, >=3 repeats)")
    for (a, i, b, j, L), (sa, sb) in sorted(res, key=lambda r: (-r[0][4])):
        same = sum(x == y for x, y in zip(sa, sb))
        print(f"{names[a]}@{i:3d} ~ {names[b]}@{j:3d}  L={L:2d} rep={n_repeats(sa)} "
              f"identical={same}")
