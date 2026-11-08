"""Commutativity conflicts in the main isomorph family (§25).

For three occurrences X, Y, Z of the same plaintext, π_XY maps c_X(k) to c_Y(k), and π_XZ maps c_X(k) to c_Z(k).
In an abelian GAK (one or several wheels), π_XY and π_XZ commute: π_XY(π_XZ(c)) = π_XZ(π_XY(c)), wherever both
compositions are defined. In a non-commutative GAK this is false in general (Lymm: "commutativity conflict").
We count the tests and the failures:
  - on all columns of the shared core;
  - on the columns whose symbol repeats within the core only (the safest).
Occurrences (0-indexed): the main family W1@34, W1@64, E2@39, E2@74 (+ E1@62, shorter), length 18; we restrict
to the core 0..17 and optionally exclude columns 2 and 15 (§2).
Controls: same computation on the testbed (6 occurrences of phrase P), abelian GAK versus reinsertion + β."""
import sys
from collections import Counter
from itertools import permutations
import numpy as np
from stats import load_eyes

OCC = [("W1", 34), ("W1", 64), ("E2", 39), ("E2", 74), ("E1", 62)]
L = 18


def comm_counts(seqs, cols):
    """seqs: list of aligned sequences (one per occurrence); returns (tests, failures)"""
    tests = fails = 0
    for X, Y, Z in permutations(range(len(seqs)), 3):
        if Y > Z:
            continue
        pXY = {seqs[X][k]: seqs[Y][k] for k in cols}
        pXZ = {seqs[X][k]: seqs[Z][k] for k in cols}
        for c in pXY:
            a = pXY.get(pXZ.get(c))
            b = pXZ.get(pXY.get(c))
            if a is not None and b is not None:
                tests += 1; fails += a != b
    return tests, fails


def run(seqs, label):
    allc = list(range(len(seqs[0])))
    cnt = Counter(x for s in seqs[:1] for x in s)
    rep = [k for k in allc if cnt[seqs[0][k]] > 1]
    for name, cols in (("all columns", allc), ("repeated columns", rep)):
        t, f = comm_counts(seqs, cols)
        print(f"  {label:38s} {name:18s}: {t:3d} tests, {f:3d} failures")


if __name__ == "__main__":
    names, M = load_eyes()
    N = dict(zip(names, M))
    for occ, lab in ((OCC[:4], "eyes, 4 safe occurrences"), (OCC, "eyes, + E1@62")):
        seqs = [N[n][i:i + L] for n, i in occ]
        run(seqs, lab)
        seqs2 = [[s[k] for k in range(L) if k not in (2, 15)] for s in seqs]
        run(seqs2, lab + ", without cols 2 and 15")
    # controls
    from testbed import build_plaintexts, ALPHA
    from explore import xgak_encrypt
    from family_zoo import make_key
    plains = build_plaintexts()
    PH = "AINYOUAMINUTEBUT"
    occ = [(k, i) for k in range(3) for i in range(len(plains[k])) if plains[k].startswith(PH, i)]
    seqs_p = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in plains]
    rng = np.random.default_rng(8)
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    for kind in ("abelian 2 wheels", "reinsertion + aleatoire", "echange + aleatoire"):
        tt = ff = 0; fr = []
        for _ in range(R):
            if kind.startswith("abelian"):
                # two wheels of 41 and 42 cards; each letter turns each wheel by its own step
                perm = rng.permutation(83); w1, w2 = perm[:41], perm[41:]
                S = []
                for _ in ALPHA:
                    a, b = rng.integers(1, 41), rng.integers(1, 42)
                    idx = np.arange(83)
                    idx[w1] = np.roll(w1, a); idx[w2] = np.roll(w2, b)
                    S.append(idx)
                S = np.array(S, np.int64); reads = rng.choice(83, len(ALPHA), replace=False)
            else:
                t, b = kind.split(" + ")          # family-zoo tokens: gesture + base shuffle ("aleatoire" = random)
                reads, S = make_key(t, b, 0, rng, len(ALPHA))
            C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs_p]
            seqs = [C[k][i + 1:i + len(PH)] for k, i in occ]
            t, f = comm_counts(seqs, list(range(len(seqs[0]))))
            tt += t; ff += f; fr.append(f / max(t, 1))
        print(f"  control {kind:30s} all columns: {tt / R:.0f} tests, {ff / R:.1f} failures per key (median share {np.median(fr):.2f})")
