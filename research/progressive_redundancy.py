"""Rate of satisfaction of the redundant constraints under the "progressive alphabet" hypothesis (§23).

Hypothesis (codewarrior0, abandoned): c_t = W[x(h_t) + t], h_t = homophone of letter p_t.
Two occurrences of the same plaintext (same homophones) at positions i and j: step(c') = step(c) + (j - i).
A column where the homophone differs breaks the relation, without necessarily breaking the isomorphism.

Test: the pairs (c, c', Δ) of all blocks are added one by one to a union-find with potentials mod 83.
A pair is "redundant" if c and c' are already in the same component. It is then satisfied or not.
  - progressive (with or without homophones): most redundant pairs are satisfied;
  - GAK / deck: a redundant pair is satisfied by chance (about 1/83).
Unsatisfied pairs are rejected (not merged). We also report the collisions (injectivity).

Blocks: isomorph cores (all columns) + shifted blocks of cycle_structure (edges trimmed by 2).
Controls on the testbed: reinsertion + β, and progressive with homophones used in turn."""
import sys
from collections import Counter
import numpy as np
from progressive_test import UF, P
from single_wheel_cores import cores
from cycle_structure import BLOCKS
from stats import load_eyes

TRIM = 2


def all_pairs(C, names, blocks=None):
    """list of (c, c', Δ); blocks = explicit blocks (a, i, b, j, L) by name, otherwise cores only"""
    N = dict(zip(names, C))
    out = []
    for (a, i, b, j, L), prs in cores(C, names, repeat_cols=False):
        out += [(x, y, (j - i) % P) for x, y in prs]
    for a, i, b, j, L in (blocks or []):
        out += [(N[a][i + k], N[b][j + k], (j - i) % P) for k in range(TRIM, L - TRIM)]
    return out


def redundancy(pairs, rng=None):
    if rng is not None:
        pairs = [pairs[k] for k in rng.permutation(len(pairs))]
    uf = UF(); red = sat = 0
    seen = set()
    for x, y, d in pairs:
        if (x, y, d) in seen:
            continue
        seen.add((x, y, d))
        rx, ox = uf.find(x); ry, oy = uf.find(y)
        if rx == ry:
            red += 1; sat += (oy - ox - d) % P == 0
        else:
            uf.union(x, y, d)
    return red, sat, uf.collisions()


def summary(pairs, rng, reps=20):
    r = [redundancy(pairs, rng) for _ in range(reps)]
    red = np.mean([a for a, b, c in r]); sat = np.mean([b for a, b, c in r]); col = np.mean([c for a, b, c in r])
    return red, sat, col


if __name__ == "__main__":
    rng = np.random.default_rng(3)
    names, M = load_eyes()
    pe = all_pairs(M, names, BLOCKS)
    red, sat, col = summary(pe, rng)
    print(f"eyes: {len(set(pe))} distinct pairs; redundant {red:.1f}, satisfied {sat:.1f} ({sat / max(red, 1):.0%}), collisions {col:.1f}")
    pe2 = [p for p in pe]
    # without the pairs of block E3 (fixed point 17 -> 17)
    from testbed import build_plaintexts, ALPHA
    from testkey import true_blocks
    from explore import xgak_encrypt
    from family_zoo import make_key
    plains = build_plaintexts()
    seqs = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in plains]
    tb = [(f"m{a}", i, f"m{b}", j, L) for a, i, b, j, L in true_blocks(plains) if L >= 12]
    tnames = [f"m{t}" for t in range(9)]
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    FREQ = Counter("".join(plains))
    for kind in ("reinsertion+aleatoire", "echange+aleatoire", "progressif", "progressif+homophones"):
        rows = []
        for _ in range(R):
            if kind.startswith("progressif"):
                W = rng.permutation(P)
                if kind == "progressif":
                    slots = {ch: [s] for ch, s in zip(ALPHA, rng.choice(P, len(ALPHA), replace=False))}
                else:  # homophones used in turn, number proportional to frequency (83 slots)
                    cnt = {ch: 1 for ch in ALPHA}
                    tot = sum(FREQ.values())
                    for ch in ALPHA:
                        cnt[ch] += int(FREQ.get(ch, 0) / tot * (P - len(ALPHA)))
                    perm = list(rng.permutation(P)); slots = {}
                    for ch in ALPHA:
                        slots[ch] = [perm.pop() for _ in range(cnt[ch])]
                C = []
                for m in plains:
                    use = Counter(); out = [0]
                    for t, ch in enumerate(m[1:], start=1):
                        h = slots[ch][use[ch] % len(slots[ch])]; use[ch] += 1
                        out.append(int(W[(h + t) % P]))
                    C.append(out)
            else:
                tk, bk = kind.split("+")
                reads, S = make_key(tk, bk, 0, rng, len(ALPHA))
                C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs]
            p = all_pairs(C, tnames, tb)
            rows.append(summary(p, rng, 5))
        rows = np.array(rows)
        print(f"control {kind:22s}: redundant {rows[:, 0].mean():.1f}, satisfied {rows[:, 1].mean():.1f} "
              f"({rows[:, 1].sum() / max(rows[:, 0].sum(), 1):.0%}), collisions {rows[:, 2].mean():.1f}")
