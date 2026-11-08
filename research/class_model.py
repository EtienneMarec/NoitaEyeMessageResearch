"""Letter-class model (§43): a generalisation of the space model.

The 36 symbols (A-Z, 1-9, space) are split into classes; each class applies its own shuffle after the read
(D' = D∘S_class), and the first symbol is inside the deck. The space model (§32) is the case "one letter class +
the space". Shuffles: β (random derangement) for the largest letter class; τ_m∘β (m random swaps) for the other
letter classes; τ_16∘β for the space (favourite value of §40).
Partitions (tokens):
  vc     : vowels AEIOUY / consonants + digits / space;
  r2, r3, r4 : letters and digits split at random into 2, 3 or 4 classes / space;
  un     : a single letter class (= space model β + 16, as a control);
  chaque : one class per symbol (≈ Lymm's model, but with the no-doubles rule and the first symbol inside).
No-doubles rule: read positions chosen (with retries) so that no bigram (x, y) satisfies S_class(x)[q_y] = q_x;
if that is impossible after 200 attempts, the last draw is kept (flagged). m = "aleatoire" means random shuffles."""
import numpy as np
import testbed_spaces as tbs
from explore import xgak_encrypt

N = 83
A = tbs.ALPHA_S
SP = A.index("_")


def derangement(rng):
    while True:
        p = rng.permutation(N)
        if (p != np.arange(N)).all():
            return p


def swaps(beta, m, rng):
    idx = np.arange(N)
    for _ in range(m):
        a, b = rng.choice(N, 2, replace=False)
        idx[[a, b]] = idx[[b, a]]
    return idx[beta]


def partition(kind, rng):
    cl = np.zeros(len(A), np.int64)
    if kind == "vc":
        for i, ch in enumerate(A):
            cl[i] = 0 if ch in "AEIOUY" else 1
    elif kind == "chaque":
        cl[:] = np.arange(len(A))
    elif kind.startswith("r"):
        k = int(kind[1:])
        while True:
            cl[:] = rng.integers(0, k, len(A))
            if len(set(cl[:SP].tolist() + cl[SP + 1:].tolist())) == k:
                break
    cl[SP] = cl.max() + 1
    return cl


def make_key(kind, m, rng, nodouble=True):
    cl = partition(kind, rng)
    ncl = cl.max() + 1
    beta = derangement(rng)
    sizes = np.bincount(cl[np.arange(len(A)) != SP], minlength=ncl)
    big = int(np.argmax(sizes))
    P = np.empty((ncl, N), np.int64)
    for c in range(ncl):
        if c == cl[SP]:
            P[c] = swaps(beta, 16, rng)
        elif c == big:
            P[c] = beta
        else:
            P[c] = rng.permutation(N) if m == "aleatoire" else swaps(beta, int(m), rng)
    S = P[cl]
    q = rng.choice(N, len(A), replace=False).astype(np.int64)
    ok = not nodouble
    for _ in range(200 if nodouble else 0):
        q = np.full(len(A), -1, np.int64)
        free = set(range(N)); fail = False
        for x in rng.permutation(len(A)):
            bad = set()
            for y in range(len(A)):
                if q[y] >= 0:
                    bad.add(int(S[x][q[y]]))                      # x then y
                    bad.update(np.where(S[y] == q[y])[0].tolist())  # y then x: S_y[q_x] = q_y
            cand = [p for p in free - bad if S[x][p] != p]          # x then x
            if not cand:
                fail = True; break
            q[x] = int(rng.choice(cand)); free.discard(int(q[x]))
        if not fail:
            ok = True; break
    if not ok:
        q = rng.choice(N, len(A), replace=False).astype(np.int64)
    return q, S, ok


def encrypt(pl, kind, m, rng):
    q, S, ok = make_key(kind, m, rng)
    return [xgak_encrypt(np.array([A.index(ch) for ch in msg], np.int64), q, S).tolist() for msg in pl], ok


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    for kind, m in (("un", "16"), ("vc", "16"), ("r2", "16"), ("r3", "16"), ("r4", "16"), ("chaque", "1"), ("chaque", "4")):
        oks = [make_key(kind, m, rng)[2] for _ in range(20)]
        print(f"{kind}-{m}: no-doubles rule satisfied {sum(oks)}/20")
