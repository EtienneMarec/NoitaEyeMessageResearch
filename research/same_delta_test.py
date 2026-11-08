"""Same shift, different message pairs (§23).

Progressive alphabet: the correspondence between two occurrences of the same plaintext depends only on the
position gap Δ (rotation by Δ steps), whatever the messages. In a GAK, it depends on the deck states:
two different message pairs at the same Δ give unrelated correspondences.

For each pair of blocks (X, Y) on DIFFERENT message pairs, we compare the shared source
cards: agreement if X and Y send the card to the same image after reduction to the same Δ
(via powers: π_X^{ΔY} and π_Y^{ΔX} are compared when computable through chains, otherwise only equal Δ).
Simple version here: only pairs of blocks with the same Δ (mod 83), up to sign (π_{-Δ} = π_Δ^{-1}).
Positions are 0-indexed; block edges trimmed by TRIM."""
from collections import defaultdict
from itertools import combinations
from stats import load_eyes

TRIM = 2
# shifted blocks (msg a, pos i, msg b, pos j, length): cycle_structure + isomorph blocks of group A
from cycle_structure import BLOCKS as B0
EXTRA = [("W1", 34, "W1", 64, 18), ("E2", 39, "E2", 74, 18), ("W1", 34, "E2", 39, 18), ("W1", 64, "E2", 74, 18),
         ("E1", 60, "W1", 62, 18), ("E3", 63, "E4", 72, 28), ("E3", 63, "E5", 73, 28), ("E3", 63, "W4", 75, 28)]


def maps(N, blocks):
    out = []
    for a, i, b, j, L in blocks:
        m = {}
        for k in range(TRIM, L - TRIM):
            m[N[a][i + k]] = N[b][j + k]
        d = j - i
        if d < 0:  # orient for Δ > 0
            m = {v: k for k, v in m.items()}; d = -d; a, b = b, a
        out.append(((a, b), d, m))
    return out


def compare(N, blocks):
    ms = maps(N, blocks)
    rows = []
    for (p1, d1, m1), (p2, d2, m2) in combinations(ms, 2):
        if d1 != d2 or set(p1) == set(p2):
            continue
        common = set(m1) & set(m2)
        agree = sum(m1[c] == m2[c] for c in common)
        rows.append((p1, p2, d1, len(common), agree))
    return rows


if __name__ == "__main__":
    names, M = load_eyes()
    N = dict(zip(names, M))
    rows = compare(N, list(B0) + EXTRA)
    tot_c = tot_a = 0
    for p1, p2, d, n, a in rows:
        print(f"  {p1[0]}→{p1[1]} and {p2[0]}→{p2[1]}  Δ={d:2d}: {n:2d} shared cards, {a} agreements")
        tot_c += n; tot_a += a
    print(f"total: {tot_a} agreements over {tot_c} shared cards (progressive: almost all; GAK: ~1/83 each, expected {tot_c / 83:.1f})")
    # independent comparisons: those with the same arrival message are set aside (E1→E2 and W1→E2:
    # E1 and W1 have the same ciphertext in this zone, agreement is automatic there)
    ind = [r for r in rows if r[0][1] != r[1][1]]
    c, a = sum(r[3] for r in ind), sum(r[4] for r in ind)
    print(f"independent comparisons: {a} agreements over {c} shared cards (GAK: expected {c / 83:.1f})")
