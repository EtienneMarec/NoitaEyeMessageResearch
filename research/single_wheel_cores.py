"""Single wheel (cyclic abelian GAK) on the isomorph cores, columns with a repeated symbol only (§23).

Same procedure on the eyes and on the testbed (controls):
  1. isomorphs (find_isomorphs), core = from the first to the last repeat, >= 3 repeats;
  2. only columns whose symbol repeats within the core are kept (the safest);
  3. search for an injective wheel and one shift δ per pair of cores.
Output: consistent or not, the δ found, and their ratio to the position gaps (progressive alphabet: δ = s·Δ).
Controls: testbed encrypted by reinsertion + random β (non-abelian) and by an abelian GAK."""
import sys
from collections import Counter
import numpy as np
from single_wheel_all import search, order
from progressive_test import core, P
from isomorphs import find_isomorphs
from stats import load_eyes


def cores(M, names, min_rep=3, repeat_cols=True):
    out = []
    for (a, i, b, j, L), (sa, sb) in find_isomorphs(M):
        s, e = core(sa)
        c = Counter(sa[s:e])
        if len(sa[s:e]) - len(c) >= min_rep:
            prs = [(x, y) for x, y in zip(sa[s:e], sb[s:e]) if c[x] > 1 or not repeat_cols]
            out.append(((names[a], i + s, names[b], j + s, e - s), prs))
    return out


def verdict(bl):
    if not bl:
        return None, []
    s, n = search(order(bl), 1)
    return bool(s), (s[0] if s else [])


if __name__ == "__main__":
    names, M = load_eyes()
    bl = cores(M, names)
    ok, d = verdict(bl)
    print(f"eyes, {len(bl)} cores: {'consistent' if ok else 'IMPOSSIBLE'}")
    bl2 = [b for b in bl if b[0][2] != "E3"]
    ok, d = verdict(bl2)
    print(f"eyes without W1@59~E3@90, {len(bl2)} cores: {'consistent' if ok else 'IMPOSSIBLE'}")
    if ok:
        o = order(bl2)
        for (nm, prs), dd in zip(o, d):
            a, i, b, j, L = nm
            Dpos = j - i
            print(f"   {a}@{i} ~ {b}@{j}  Δpos = {Dpos:3d}  δ = {dd:2d}  δ/Δpos mod 83 = {dd * pow(Dpos % P, -1, P) % P if Dpos % P else '-'}")
    # controls
    from testbed import build_plaintexts, ALPHA
    from explore import xgak_encrypt
    from family_zoo import make_key
    plains = build_plaintexts()
    seqs = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in plains]
    rng = np.random.default_rng(11)
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    for kind in ("reinsertion+aleatoire", "retournement+riffle", "abelian"):
        res, nb = [], []
        for _ in range(R):
            if kind == "abelian":
                rho = rng.permutation(P); cyc = np.empty(P, np.int64); cyc[rho] = np.roll(rho, 1)
                pw = [np.arange(P)]
                for _ in range(P):
                    pw.append(cyc[pw[-1]])
                k = rng.integers(1, P, len(ALPHA)); reads = rng.choice(P, len(ALPHA), replace=False)
                S = np.array([pw[kk] for kk in k], np.int64)
            elif kind == "reinsertion+aleatoire":
                reads, S = make_key("reinsertion", "aleatoire", 0, rng, len(ALPHA))
            else:
                reads, S = make_key("retournement", "riffle", 0, rng, len(ALPHA))
            C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs]
            b = cores(C, [f"m{t}" for t in range(9)])
            v, _ = verdict(b)
            if v is not None:
                res.append(v); nb.append(len(b))
        print(f"control {kind:22s}: consistent wheel for {sum(res)}/{len(res)} keys (cores per key: median {np.median(nb) if nb else 0:.0f})")
