"""For a set of occurrences of the same phrase, looks for the effective offsets e_k
(mod 83) making the "single wheel" model consistent: pos(y)-pos(x) = e_l - e_k (mod 83).
Compares the offsets found with the true positions in the messages."""
from itertools import combinations, product
from stats import load_eyes
from progressive_test import UF, P
names, M = load_eyes(); N = dict(zip(names, M))

def contradictions(occ, eff, L):
    uf = UF(); bad = 0; edges = 0; verts = set()
    for (k1, (n1, i)), (k2, (n2, j)) in combinations(enumerate(occ), 2):
        for x, y in zip(N[n1][i:i+L], N[n2][j:j+L]):
            edges += 1; verts |= {x, y}
            if not uf.union(x, y, (eff[k2] - eff[k1]) % P): bad += 1
    return bad + uf.collisions(), edges, len(verts)

def cyclomatic(occ, L):
    # number of independent cycles of the graph (distinct edges)
    E = set(); V = set()
    for (n1, i), (n2, j) in combinations(occ, 2):
        for x, y in zip(N[n1][i:i+L], N[n2][j:j+L]):
            E.add((min(x, y), max(x, y), )); V |= {x, y}
    uf = UF(); comps = 0
    for x in V: uf.find(x)
    roots = set()
    for a, b in E: uf.union(a, b, 0)
    roots = {uf.find(v)[0] for v in V}
    return len(E) - len(V) + len(roots)

if __name__ == "__main__":
    occ = [("W1", 34), ("W1", 64), ("E2", 39), ("E2", 74)]
    L = 18
    print("independent cycles (not counting columns):", cyclomatic(occ, L))
    real = [i for _, i in occ]
    print("true offsets:", real, "->", contradictions(occ, real, L))
    # how many random offset assignments would also be consistent?
    ok = 0; tot = 0
    for e2, e3, e4 in product(range(P), repeat=3):
        tot += 1
        if contradictions(occ, [0, e2, e3, e4], L)[0] == 0:
            ok += 1
            print("  consistent solution (relative to W1@34):", (e2, e3, e4), " true:", (30, 5, 40))
    print(f"{ok} consistent assignments out of {tot}")
