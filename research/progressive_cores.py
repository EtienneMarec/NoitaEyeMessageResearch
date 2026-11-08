"""Pure progressive alphabet (c_t = W[x(p_t) + s·t]) on the isomorph cores, repeated columns only (§23).

In this model, two occurrences of the same plaintext at positions i and j satisfy step(c') = step(c) + s·(j - i).
Since 83 is prime, s = 1 without loss of generality: NO free parameter (unlike the wheel
with free offsets). §2 refuted it on all columns except 2 and 15; here we keep only the
columns whose symbol repeats within the core.

Output: verdict for the eyes (with and without W1@59~E3@90), number of linked cards, and controls
(testbed encrypted by reinsertion + β, segment reversal + riffle, and by a progressive alphabet)."""
import sys
import numpy as np
from progressive_test import UF, P
from single_wheel_cores import cores
from stats import load_eyes


def progressive_ok(bl):
    uf = UF()
    for (a, i, b, j, L), prs in bl:
        for x, y in prs:
            if not uf.union(x, y, (j - i) % P):
                return False, uf
    return uf.collisions() == 0, uf


def ncards(uf):
    from collections import Counter
    roots = Counter(uf.find(x)[0] for x in list(uf.par))
    return len(uf.par), sorted(roots.values(), reverse=True)[:5]


if __name__ == "__main__":
    names, M = load_eyes()
    for rc in (True, False):
        bl = cores(M, names, repeat_cols=rc)
        for drop in (False, True):
            b = [x for x in bl if not (drop and x[0][2] == "E3")]
            ok, uf = progressive_ok(b)
            n, comps = ncards(uf)
            print(f"eyes, columns {'repeated' if rc else 'all     '}{', without E3' if drop else '            '}: "
                  f"{'consistent' if ok else 'IMPOSSIBLE'} ({len(b)} cores, {sum(len(p) for _, p in b)} pairs, {n} cards, components {comps})")
    from testbed import build_plaintexts, ALPHA
    from explore import xgak_encrypt
    from family_zoo import make_key
    plains = build_plaintexts()
    seqs = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in plains]
    rng = np.random.default_rng(12)
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    for kind in ("reinsertion+aleatoire", "retournement+riffle", "echange+aleatoire", "progressif"):
        res = []
        for _ in range(R):
            if kind == "progressif":
                W = rng.permutation(P); x = rng.choice(P, len(ALPHA), replace=False)
                C = [[0] + [int(W[(x[c] + t + 1) % P]) for t, c in enumerate(s)] for s in seqs]
            else:
                t, bk = kind.split("+")
                reads, S = make_key(t, bk, 0, rng, len(ALPHA))
                C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs]
            bl = cores(C, [f"m{t}" for t in range(9)])
            if bl:
                res.append(progressive_ok(bl)[0])
        print(f"control {kind:22s}: progressive consistent for {sum(res)}/{len(res)} keys")
