"""Single wheel for ALL shifted blocks (§23).

Model tested: cyclic abelian GAK (σ_p = ρ^{k_p}, with ρ a fixed 83-cycle). Any pair of shared text
blocks is then linked by a rotation of the same wheel: c' = ρ^δ(c), with an unknown δ specific to the pair.
This is the only type of GAK where a swap of words of equal "weight" resynchronises exactly (obstacle 4/4/4/13).
We look for a wheel (step of each card, injective) and δ consistent across all blocks at once.
Since 83 is prime, we fix δ = 1 for the first block (multiplying the steps).

Controls: same search on the testbed encrypted (a) by an abelian GAK (must be consistent),
(b) by reinsertion + base shuffle (must be inconsistent). Edges trimmed by TRIM positions."""
import sys
import copy
import numpy as np
from progressive_test import UF, P
from cycle_structure import BLOCKS
from stats import load_eyes

TRIM = int(sys.argv[1]) if len(sys.argv) > 1 else 2


def pairs_of(N, blocks):
    out = []
    for a, i, b, j, L in blocks:
        prs = [(N[a][i + k], N[b][j + k]) for k in range(TRIM, L - TRIM)]
        out.append(((a, i, b, j, L), prs))
    return out


def search(blocks, limit=3):
    sols, nodes = [], [0]

    def rec(k, uf, deltas):
        nodes[0] += 1
        if len(sols) >= limit or nodes[0] > 200000:
            return
        if k == len(blocks):
            sols.append(list(deltas)); return
        name, prs = blocks[k]
        forced = None
        for x, y in prs:
            rx, ox = uf.find(x); ry, oy = uf.find(y)
            if rx == ry:
                forced = (oy - ox) % P; break
        cands = [1] if k == 0 else ([forced] if forced is not None else range(1, P))
        for d in cands:
            if d == 0:
                continue
            u = copy.deepcopy(uf)
            if all(u.union(x, y, d) for x, y in prs) and u.collisions() == 0:
                rec(k + 1, u, deltas + [d])

    rec(0, UF(), [])
    return sols, nodes[0]


def order(blocks):
    """greedy order: each next block shares the most cards with those already taken"""
    rest, out, seen = list(blocks), [], set()
    while rest:
        best = max(rest, key=lambda b: len(seen & {c for pr in b[1] for c in pr}))
        rest.remove(best); out.append(best); seen |= {c for pr in best[1] for c in pr}
    return out


def first_failure(blocks):
    """longest prefix (in greedy order) admitting a wheel"""
    for n in range(1, len(blocks) + 1):
        s, nodes = search(blocks[:n], 1)
        if not s:
            return n - 1, blocks[n - 1][0]
    return len(blocks), None


if __name__ == "__main__":
    names, M = load_eyes()
    N = dict(zip(names, M))
    blocks = order(pairs_of(N, BLOCKS))
    print(f"eyes, edges trimmed by {TRIM}: {len(blocks)} blocks, {sum(len(p) for _, p in blocks)} pairs")
    ok, bad = first_failure(blocks)
    print(f"  longest consistent prefix: {ok}/{len(blocks)} blocks; first failing block: {bad}")
    # controls on the testbed: the eyes' block positions make no sense there;
    # true blocks of the testbed (known shared text) are taken via testkey.true_blocks
    from testkey import true_blocks
    from testbed import build_plaintexts, ALPHA
    from explore import xgak_encrypt
    from family_zoo import make_key
    plains = build_plaintexts()
    rng = np.random.default_rng(5)
    seqs = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in plains]
    tb = true_blocks(plains)
    for kind in ("abelian", "reinsertion+aleatoire"):
        res = []
        for _ in range(10):
            if kind == "abelian":
                rho = rng.permutation(P); cyc = np.empty(P, np.int64); cyc[rho] = np.roll(rho, 1)
                pw = [np.arange(P)]
                for _ in range(P):
                    pw.append(cyc[pw[-1]])
                k = rng.integers(1, P, len(ALPHA)); reads = rng.choice(P, len(ALPHA), replace=False)
                S = np.array([pw[kk] for kk in k], np.int64)
            else:
                reads, S = make_key("reinsertion", "aleatoire", 0, rng, len(ALPHA))
            C = {f"m{t}": [0] + xgak_encrypt(s, reads, S).tolist() for t, s in enumerate(seqs)}
            bl = [(f"m{a}", i, f"m{b}", j, L) for a, i, b, j, L in tb if L >= 12 and i != j][:10]
            o = order(pairs_of(C, bl))
            res.append(first_failure(o)[0] == len(o))
        print(f"  control {kind:22s}: consistent wheel for {sum(res)}/10 keys")
