"""Map of plaintext differences between aligned messages (allomorph method).

Conflict between two positions i < j: (A[i] == A[j]) != (B[i] == B[j]).
Two cases depending on the model:
  * GAK / deck of cards (fixed read AFTER the shuffle, Lymm's favourite model; includes CTAK):
      D'_i = π D_i as soon as letters i+1..j are identical, whatever letter i is
      => a conflict (i, j) proves a plaintext difference within [i+1, j].
  * general XGAK (the letter chooses the read position): difference proven within [i, j].
A conflict-free segment is only *compatible* with a shared text. The POSITIVE evidence
of shared text is identical symbols (=, 1/83 by chance) and shared repeats
(A[i]=A[j] and B[i]=B[j], rare by chance).

Positions are 0-indexed.
"""
import sys
from itertools import combinations
from stats import load_eyes

names, M = load_eyes()
N = dict(zip(names, M))


def conflicts(A, B, gak=True):
    L = min(len(A), len(B))
    s = 1 if gak else 0
    return [(i + s, j) for i in range(L) for j in range(i + 1, L)
            if (A[i] == A[j]) != (B[i] == B[j])]


def minimal_intervals(iv):
    keep = []
    for a, b in sorted(set(iv), key=lambda x: (x[1] - x[0], x[0])):
        if not any(c >= a and d <= b for c, d in keep):
            keep.append((a, b))
    return sorted(keep)


def stab(iv):
    """Minimum number of divergence points hitting all intervals (optimal greedy)."""
    pts = []
    for a, b in sorted(iv, key=lambda x: x[1]):
        if not pts or pts[-1] < a:
            pts.append(b)
    return pts


def common_repeats(A, B):
    L = min(len(A), len(B))
    return [(i, j) for i in range(L) for j in range(i + 1, L) if A[i] == A[j] and B[i] == B[j] and A[i] != B[i]]


def pair_map(A, B, gak=True):
    L = min(len(A), len(B))
    mins = minimal_intervals(conflicts(A, B, gak))
    forced = [0] * L  # number of minimal intervals covering the position
    for a, b in mins:
        for k in range(a, b + 1):
            forced[k] += 1
    rep = common_repeats(A, B)
    rep_pos = set(k for i, j in rep for k in (i, j))
    line = []
    for k in range(L):
        if A[k] == B[k]:
            line.append("=")
        elif k in rep_pos:
            line.append("r")  # shared repeat: positive evidence of shared text
        else:
            line.append(".")
    return "".join(line), mins, stab(mins), rep


def render(n1, n2, gak=True, width=70):
    A, B = N[n1], N[n2]
    line, mins, pts, rep = pair_map(A, B, gak)
    L = len(line)
    out = [f"### {n1} / {n2}  ({'GAK' if gak else 'XGAK'})  shared length {L}"]
    for s in range(0, L, width):
        e = min(L, s + width)
        out.append("      " + "".join(f"{(i // 10) % 10}" if i % 10 == 0 else " " for i in range(s, e)))
        out.append("  cip " + line[s:e])
        # minimal intervals in this slice, stacked
        rows = []
        for a, b in mins:
            if b < s or a >= e:
                continue
            for r in rows:
                if all(b < c or a > d for c, d in r):
                    r.append((a, b)); break
            else:
                rows.append([(a, b)])
        for r in rows:
            buf = [" "] * (e - s)
            for a, b in r:
                for k in range(max(a, s), min(b, e - 1) + 1):
                    buf[k - s] = "-"
                if s <= a < e: buf[a - s] = "["
                if s <= b < e: buf[b - s] = "]"
                if a == b and s <= a < e: buf[a - s] = "|"
            out.append("      " + "".join(buf))
    out.append(f"  => {len(mins)} minimal intervals, at least {len(pts)} divergence points; "
               f"{line.count('=')} identical symbols, {len(rep)} shared repeats")
    return "\n".join(out), mins, pts


if __name__ == "__main__":
    gak = "--xgak" not in sys.argv
    pairs = [("E1", "W1"), ("E1", "E2"), ("W1", "E2"), ("W2", "E3"), ("W2", "W3"), ("E3", "W3"),
             ("E4", "W4"), ("E4", "E5"), ("W4", "E5")]
    for a, b in pairs:
        txt, _, _ = render(a, b, gak)
        print(txt + "\n")
