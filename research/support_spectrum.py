"""Spectrum of supports (lead 1 of the status notes): a model-free measure, valid for any XGAK.

After the last plaintext difference, two messages are linked by c' = π(c) with a fixed π.
A position is identical exactly when the card read is a fixed point of π. In a window
with no text difference, we therefore observe:
  - identical cards: fixed points of π;
  - different pairs (c, π(c)): c and π(c) are in the support of π.
We estimate |supp π| = 83 - |Fix π| by likelihood, assuming the card read is drawn
uniformly (the flat gap profile roughly justifies it), with a 90% interval.
Windows are taken between two proven differences (XGAK conflicts, intervals [i, j]).

0-indexed positions, in the first message of each pair; the second is shifted by `off`.
"""
import sys
from math import comb
import numpy as np
from stats import load_eyes

names, M = load_eyes()
N = dict(zip(names, M))
Q = 83


def aligned(a, b, off):
    A, B = N[a], N[b]
    L = min(len(A), len(B) - off)
    return [A[i] for i in range(max(0, -off), L)], [B[i + off] for i in range(max(0, -off), L)], max(0, -off)


def conflicts(A, B, lo, hi):
    """minimal intervals [i, j] (XGAK) proving a difference, within the window [lo, hi]"""
    iv = [(i, j) for i in range(lo, hi + 1) for j in range(i + 1, hi + 1)
          if (A[i] == A[j]) != (B[i] == B[j])]
    keep = []
    for x, y in sorted(iv, key=lambda t: (t[1] - t[0], t[0])):
        if not any(c >= x and d <= y for c, d in keep):
            keep.append((x, y))
    return sorted(keep)


def line(A, B, s0):
    out = []
    for k in range(len(A)):
        out.append("=" if A[k] == B[k] else ".")
    return "".join(out)


def window(A, B, lo, hi):
    """statistics of a window assumed to have no text difference (positions lo..hi of the aligned lists)"""
    eq = [A[k] == B[k] for k in range(lo, hi + 1)]
    n, k = len(eq), sum(eq)
    fixed = {A[i] for i in range(lo, hi + 1) if A[i] == B[i]}
    moved = {A[i] for i in range(lo, hi + 1) if A[i] != B[i]} | {B[i] for i in range(lo, hi + 1) if A[i] != B[i]}
    # binomial likelihood of F = |Fix| under the constraints F >= |fixed|, 83 - F >= |moved|
    Fs = np.arange(len(fixed), Q - len(moved) + 1)
    ll = np.array([k * np.log(max(F, 1e-9) / Q) + (n - k) * np.log(max(Q - F, 1e-9) / Q) for F in Fs])
    p = np.exp(ll - ll.max()); p /= p.sum()
    cdf = np.cumsum(p)
    lo90, hi90 = Fs[np.searchsorted(cdf, 0.05)], Fs[np.searchsorted(cdf, 0.95)]
    Fhat = Fs[np.argmax(p)]
    return n, k, len(fixed), len(moved), Q - Fhat, Q - hi90, Q - lo90


# (message 1, message 2, shift of 2 relative to 1, windows [lo, hi] in positions of 1, label)
CASES = [
    ("E1", "W1", 0, [(34, 49, "obstacle: after the 2nd difference (proven in [28,33])"),
                    (26, 49, "obstacle: after the 1st difference, ignoring the 2nd"),
                    (60, 77, "A2 after the divergence around 50 (shift E1→W1 = +2)")]),
    ("E4", "E5", 0, [(21, 46, "stutter 21..46 (at least 2 or 3 differences inside)"),
                    (29, 37, "C1: shared block inside the stutter")]),
]

if __name__ == "__main__":
    for a, b, off, wins in CASES:
        A, B, s0 = aligned(a, b, off)
        print(f"### {a}/{b} shift {off}")
        L = line(A, B, s0)
        for s in range(0, len(L), 60):
            print(f"  {s:3d} {L[s:s + 60]}")
        print("  proven differences (XGAK):", conflicts(A, B, 1, len(A) - 1)[:30])
        for lo, hi, lab in wins:
            n, k, nf, nm, s, slo, shi = window(A, B, lo, hi)
            print(f"  [{lo},{hi}] {lab}\n      {k}/{n} identical, {nf} fixed cards seen, {nm} moved cards seen"
                  f"; estimated |supp π| {s} (90%: {slo}..{shi})")
            print("      internal conflicts:", conflicts(A, B, lo, hi))
