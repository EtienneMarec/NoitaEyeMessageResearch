"""Test of the "progressive alphabet" model (disc advancing s steps per letter).
In this model c_i = C[P[p_i] + s*i]. Two occurrences of the same phrase at positions
i and j give pos_C(y) - pos_C(x) = s*(j-i) for each aligned pair (x, y).
Up to decimating C, we can take s = 1 (83 is prime): the constraints are therefore
entirely known. Their consistency is checked with a union-find with potentials mod 83."""
import sys
from stats import load_eyes
from isomorphs import find_isomorphs
from collections import Counter
P = 83
names, M = load_eyes()

class UF:
    def __init__(s): s.par, s.off = {}, {}
    def find(s, x):
        if x not in s.par: s.par[x], s.off[x] = x, 0
        if s.par[x] == x: return x, 0
        r, o = s.find(s.par[x]); s.par[x] = r; s.off[x] = (s.off[x] + o) % P
        return r, s.off[x]
    def union(s, x, y, d):  # pos(y) - pos(x) = d
        rx, ox = s.find(x); ry, oy = s.find(y)
        if rx == ry: return (oy - ox - d) % P == 0
        s.par[ry] = rx; s.off[ry] = (ox + d - oy) % P
        return True
    def collisions(s):
        """Distinct letters placed at the same step of one component (forbidden)."""
        seen = {}; bad = 0
        for x in list(s.par):
            r, o = s.find(x)
            if (r, o) in seen: bad += 1
            seen[(r, o)] = x
        return bad

def core(sa):
    c = Counter(sa); idx = [k for k, v in enumerate(sa) if c[v] > 1]
    return idx[0], idx[-1] + 1

def main():
  iso = find_isomorphs(M)
  min_rep = int(sys.argv[1]) if len(sys.argv) > 1 else 3
  for s_step in [1]:
      uf = UF(); bad = 0; tot = 0
      for (a, i, b, j, L), (sa, sb) in iso:
          s, e = core(sa)
          if len(sa[s:e]) - len(set(sa[s:e])) < min_rep: continue
          d = ((j + s) - (i + s)) * s_step
          for x, y in zip(sa[s:e], sb[s:e]):
              tot += 1
              if not uf.union(x, y, d % P):
                  bad += 1
      print(f"constraints={tot} contradictions={bad} collisions={uf.collisions()}")

if __name__ == '__main__':
    main()
