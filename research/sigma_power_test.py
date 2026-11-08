"""Test of the positional model c_i = sigma^i(u_i)  (Pyry/dextercd: "P^pos[S[char]]").

u_i = plaintext symbol (possibly homophonic), sigma = unknown permutation of the 83 symbols.
Two occurrences of the same phrase at positions i and j give sigma^(j-i)(x) = y for each
aligned pair (x, y). If x and y are in a cycle of sigma of length l, this reads
pos(y) - pos(x) = j - i  (mod l); x and y must be in the same cycle.

For each connected component of the constraint graph we compute, over the integers, the GCD G
of the cycle gaps: the length l of the cycle of sigma containing the component must divide G.
If G = 1, no permutation sigma works: the model is refuted by this component.
"""
import sys
from math import gcd
from collections import defaultdict, Counter, deque
from stats import load_eyes
from isomorphs import find_isomorphs

names, M = load_eyes()


def core(sa):
    c = Counter(sa)
    idx = [k for k, v in enumerate(sa) if c[v] > 1]
    return idx[0], idx[-1] + 1


def constraints(min_rep, use_core=True):
    out = []
    for (a, i, b, j, L), (sa, sb) in find_isomorphs(M):
        s, e = core(sa) if use_core else (0, L)
        seg = sa[s:e]
        if len(seg) - len(set(seg)) < min_rep:
            continue
        d = j - i
        for x, y in zip(sa[s:e], sb[s:e]):
            out.append((x, y, d, f"{names[a]}@{i+s}~{names[b]}@{j+s}"))
    return out


def analyse(cons):
    adj = defaultdict(list)
    for x, y, d, tag in cons:
        adj[x].append((y, d, tag))
        adj[y].append((x, -d, tag))
    pot, comp = {}, {}
    comps = []
    for start in adj:
        if start in pot:
            continue
        cid = len(comps)
        pot[start] = 0
        comp[start] = cid
        q = deque([start])
        members, g = [start], 0
        while q:
            x = q.popleft()
            for y, d, _ in adj[x]:
                if y not in pot:
                    pot[y] = pot[x] + d
                    comp[y] = cid
                    members.append(y)
                    q.append(y)
                else:
                    g = gcd(g, abs(pot[x] + d - pot[y]))
        comps.append((members, g, {m: pot[m] for m in members}))
    return comps


if __name__ == "__main__":
    min_rep = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    cons = constraints(min_rep)
    comps = analyse(cons)
    print(f"min_rep={min_rep}: {len(cons)} constraints, {len(comps)} components")
    for members, g, pot in sorted(comps, key=lambda c: -len(c[0])):
        # l must divide g, and the members must occupy distinct positions mod l
        ok = [l for l in range(1, 84) if (g == 0 or g % l == 0)
              and len({pot[m] % l for m in members}) == len(members)]
        print(f"  size={len(members):2d}  GCD of gaps={g:4d}  possible cycle lengths={ok if g else '>= size (free)'}")
