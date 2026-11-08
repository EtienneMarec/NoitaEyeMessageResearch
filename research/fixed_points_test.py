"""Fixed points in the shifted blocks after a letter insertion: eyes vs models.
Eyes (cycle_structure.py): 0 fixed points over ~210 pairs (10 blocks). For each model, we encrypt the testbed
and count the fixed points in the blocks E4(i)/E5(i+1) and E4(i)/W4(i+2) that follow the
insertions (known truth). Models: reinsertion with an arbitrary table (reads and destinations mixed),
reinsertion "reads at the top, destinations at the bottom", GAK with random permutations (S83)."""
import numpy as np
from testkey import make
from testbed import build_plaintexts, ALPHA
from explore import xgak_encrypt
from swap_model_test import gak_encrypt

N = 83
plains = build_plaintexts()


def blocks_fixed(C):
    """counts (pairs, fixed points) in the blocks after an insertion: E5 insertion at 47 (δ=+1 after 48),
    W4 insertion at 66 (δ=+1 more); we take E4 50..95 vs E5 51..96 and E4 70..95 vs W4 72..97."""
    tot = fx = 0
    for (a, i, b, j, L) in ((6, 50, 8, 51, 45), (6, 70, 7, 72, 25)):
        A, B = C[a][i:i + L], C[b][j:j + L]
        pairs = dict(zip(A, B))
        tot += len(pairs); fx += sum(1 for x, y in pairs.items() if x == y)
    return tot, fx


def reinsertion(rng, mode):
    perm = rng.permutation(np.arange(1, N))
    if mode == "mixed":
        reads, pool = perm[:len(ALPHA)], perm[len(ALPHA):]
    else:  # reads at the top of the deck, destinations at the bottom
        reads = rng.choice(np.arange(1, 42), len(ALPHA), replace=False); pool = np.arange(42, N)
    F = {int(q): int(rng.choice(pool)) for q in reads}
    S = np.empty((len(ALPHA), N), np.int64)
    for s, q in enumerate(reads):
        idx = list(range(N)); c = idx.pop(int(q)); idx.insert(F[int(q)], c); S[s] = idx
    return [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]]), reads.astype(np.int64), S).tolist()
            for m in plains]


def gak_random(rng):
    sig = np.array([rng.permutation(N) for _ in ALPHA])
    return [gak_encrypt(np.array([ALPHA.index(ch) for ch in m]), sig).tolist() for m in plains]


rng = np.random.default_rng(12)
for label, fn in (("reinsertion, mixed table", lambda: reinsertion(rng, "mixed")),
                  ("reinsertion, reads at top / destinations at bottom", lambda: reinsertion(rng, "haut_bas")),
                  ("GAK random permutations (S83)", lambda: gak_random(rng))):
    fr = []
    for _ in range(40):
        t, f = blocks_fixed(fn())
        fr.append(f / t)
    fr = np.array(fr)
    print(f"{label:52s} share of fixed points: median {np.median(fr):.2f}, P(share <= 0.01) = {np.mean(fr <= 0.01):.2f}")
print("eyes: 0 fixed points over ~210 pairs (share 0.00)")
