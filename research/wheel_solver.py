"""Is there ONE wheel (mixed alphabet of 83 notches) and offsets e_k such that each
occurrence k of a phrase is the same phrase encrypted with the wheel rotated by e_k?
(= classic alphabet chaining, with an injectivity check). Search with pruning."""
from itertools import combinations
from stats import load_eyes
from progressive_test import UF, P
names, M = load_eyes(); N = dict(zip(names, M))

def ok(occ, cols, eff):
    uf = UF(); k = len(eff)
    for (a, (n1, i)), (b, (n2, j)) in combinations(enumerate(occ[:k]), 2):
        for c in cols:
            if not uf.union(N[n1][i + c], N[n2][j + c], (eff[b] - eff[a]) % P):
                return False
    return uf.collisions() == 0

def solutions(occ, cols, limit=5):
    sols = []
    def rec(eff):
        if len(sols) >= limit: return
        if not ok(occ, cols, eff): return
        if len(eff) == len(occ): sols.append(tuple(eff)); return
        for e in range(P): rec(eff + [e])
    rec([0])
    return sols

if __name__ == "__main__":
    occ = [("W1", 34), ("W1", 64), ("E2", 39), ("E2", 74)]
    base = list(range(6, 15))
    for extra in [None, 0, 1, 2, 3, 4, 5, 15, 16, 17]:
        cols = base + ([extra] if extra is not None else [])
        s = solutions(occ, cols, 3)
        print(f"columns 6..14 + {extra}: {'consistent ' + str(s) if s else 'IMPOSSIBLE'}", flush=True)
    for c in range(18): print(c, [N[n][i + c] for n, i in occ])
