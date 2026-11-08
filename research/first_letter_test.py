"""Test "only the first letter differs" in a deck-of-cards model (GAK, fixed-read XGAK).

Convention (that of Lymm's wiki, fixed-read XGAK): D_i = D_{i-1} ∘ σ(p_i), c_i = D_i(0).
If two messages have first letters a ≠ a' and then the SAME plaintext, then
    D_i = σ_a W_i  and  D'_i = σ_a' W_i   (W_i = product of letters 1..i)
so c'_i = π(c_i) for the FIXED permutation π = σ_a' σ_a^{-1}, at all positions i ≥ 0
(position 0 included). At positions where c'_i = c_i, π fixes c_i.

We walk through the positions and build π. The first position where π stops being a consistent
partial bijection bounds the place where the plaintext must have diverged
(under the fixed-read GAK/XGAK assumption).
"""
from itertools import combinations
from stats import load_eyes

names, M = load_eyes()


def first_conflict(a, b):
    f, g = {}, {}
    for i in range(min(len(a), len(b))):
        x, y = a[i], b[i]
        if f.get(x, y) != y or g.get(y, x) != x:
            return i, (x, y, f.get(x), g.get(y))
        f[x], g[y] = y, x
    return None, None


def last_shared(a, b):
    """last position where the two ciphertexts are still identical (excluding position 0)"""
    last = 0
    for i in range(1, min(len(a), len(b))):
        if a[i] == b[i]:
            last = i
    return last


if __name__ == "__main__":
    print("pair      1st inconsistency of π  last identical position       detail")
    for i, j in combinations(range(9), 2):
        a, b = M[i], M[j]
        pos, det = first_conflict(a, b)
        ls = last_shared(a, b)
        d = ""
        if det:
            x, y, fx, gy = det
            d = f"c={x}->c'={y}, but π({x})={fx}" if fx is not None and fx != y else f"c={x}->c'={y}, but π^-1({y})={gy}"
        print(f"{names[i]}/{names[j]}   {pos!s:>5}                 {ls:>5}                  {d}")
