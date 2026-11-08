"""Test key "reinsertion" (corrected model of §8: NO homophones, compatible with perfect
isomorphs): one read position per symbol, arbitrary destinations outside the reads,
sorted deck, no base shuffle, first symbol outside the deck. Also returns the true shared
text blocks (ground truth) for lead 2."""
import numpy as np
from itertools import combinations
from testbed import build_plaintexts, ALPHA
from explore import xgak_encrypt

N = 83


def make(seed=5):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(N)
    reads, pool = perm[:len(ALPHA)], perm[len(ALPHA):]
    F_true = np.arange(N)
    F_true[reads] = rng.choice(pool, len(ALPHA), replace=True)
    S = np.empty((len(ALPHA), N), np.int64)
    for s, q in enumerate(reads):
        idx = list(range(N)); card = idx.pop(int(q)); idx.insert(int(F_true[q]), card); S[s] = idx
    plains = build_plaintexts()
    C = [[999] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]], np.int64), reads, S).tolist()
         for m in plains]
    return plains, C, F_true, np.array(reads)


def true_blocks(plains, minlen=10):
    """True shared text blocks: (msg a, pos i, msg b, pos j, length), positions >= 1."""
    out = []
    for a, b in combinations(range(len(plains)), 2):
        A, B = plains[a], plains[b]
        for i in range(1, len(A)):
            for j in range(1, len(B)):
                if A[i - 1] == B[j - 1] and i > 1 and j > 1:
                    continue
                k = 0
                while i + k < len(A) and j + k < len(B) and A[i + k] == B[j + k]:
                    k += 1
                if k >= minlen:
                    out.append((a, i, b, j, k))
    # repeated occurrences within one message
    for a, A in enumerate(plains):
        for i in range(1, len(A)):
            for j in range(i + minlen, len(A)):
                if A[i - 1] == A[j - 1] and i > 1:
                    continue
                k = 0
                while j + k < len(A) and A[i + k] == A[j + k] and i + k < j:
                    k += 1
                if k >= minlen:
                    out.append((a, i, a, j, k))
    return out
