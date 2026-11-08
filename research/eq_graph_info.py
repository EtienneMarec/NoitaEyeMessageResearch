"""How many INFORMATIVE cycles does the system of block equations of the eyes contain? (§36)

Columns: classes of (message, position) carrying the same plaintext letter, from the block alignments
(union of all aligned pairs). Equations between occurrences of one column compose
automatically (cycles always consistent). Information comes from the cycles of the BIPARTITE card–column graph
(edge card c — column k if c is read in an occurrence of k): these cycles link a card read at two
distinct places of the shared text. Number of independent cycles = E - V + C. Comparison with the
testbed, where this system fixes the starting deck (block_propagation.py)."""
from stats import load_eyes
from testkey import true_blocks

EYES_BLOCKS = [("E1", 29, "E2", 34, 21), ("W1", 29, "E2", 34, 21), ("E1", 60, "W1", 62, 18), ("E1", 60, "E2", 72, 18),
               ("E1", 29, "E1", 60, 18), ("E4", 47, "E5", 48, 18), ("E4", 47, "W4", 49, 18),
               ("E4", 68, "E5", 69, 22), ("E4", 68, "W4", 71, 22), ("E4", 90, "E5", 91, 8), ("E4", 90, "W4", 93, 8),
               ("E3", 63, "E4", 72, 28), ("W2", 12, "E3", 18, 23), ("W2", 12, "W3", 17, 23),
               ("E1", 1, "W1", 1, 21), ("E1", 1, "E2", 1, 21), ("E4", 1, "W4", 1, 20), ("E4", 1, "E5", 1, 20),
               ("W2", 1, "E3", 1, 5), ("W2", 1, "W3", 1, 5), ("E3", 1, "E4", 1, 9)]


def info(seqs, blocks, trim=2):
    par = {}

    def f(x):
        while par.setdefault(x, x) != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, i, b, j, L in blocks:
        for k in range(trim, L - trim):
            par[f((a, i + k))] = f((b, j + k))
    occ = list(par)
    cols = {}
    for o in occ:
        cols.setdefault(f(o), []).append(o)
    E = set()
    for k, os_ in cols.items():
        for (m, p) in os_:
            E.add((seqs[m][p], k))
    cards = {c for c, k in E}
    V = len(cards) + len(cols)
    par2 = {}

    def g(x):
        while par2.setdefault(x, x) != x:
            par2[x] = par2[par2[x]]; x = par2[x]
        return x
    for c, k in E:
        par2[g(("c", c))] = g(("k", k))
    C = len({g(("c", c)) for c in cards} | {g(("k", k)) for k in cols})
    return len(E), len(cards), len(cols), len(E) - V + C


if __name__ == "__main__":
    names, M = load_eyes()
    seqs = dict(zip(names, M))
    E, nc, nk, cyc = info(seqs, EYES_BLOCKS)
    print(f"eyes: {nk} columns, {nc} cards, {E} card–column edges, independent informative cycles = {cyc}")
    E, nc, nk, cyc = info(seqs, [b for b in EYES_BLOCKS if not b[0].startswith("W2")])
    print(f"eyes without the weak block B1: {nk} columns, {nc} cards, informative cycles = {cyc}")
    # testbed (any ciphertext: only the structure matters, but the cards depend on the cipher)
    import numpy as np
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    from keyed_deck_attack import tables
    names_, BS, inv = tables()
    rng = np.random.default_rng(4)
    pl = tbs.build_plaintexts()
    q = rng.choice(83, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS["deal3fwd"] if ch == "_" else BS["rot1"] for ch in tbs.ALPHA_S], np.int64)
    C = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
    tseqs = {k: C[k] for k in range(9)}
    for lab, bl in (("all true blocks", true_blocks(pl)), ("8 longest", sorted(true_blocks(pl), key=lambda b: -b[4])[:8])):
        E, nc, nk, cyc = info(tseqs, bl)
        print(f"testbed ({lab}): {nk} columns, {nc} cards, informative cycles = {cyc}")
