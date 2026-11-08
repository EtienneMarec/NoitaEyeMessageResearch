"""Cycle structure of the correspondence between two shifted occurrences of the same text.

In an XGAK cipher, if two messages have the same plaintext from some point on, their decks are linked by a
fixed bijection π (cards -> cards): c' = π(c) over the whole aligned block.
After the insertion of ONE letter x in one of the messages (identical decks before), π = D μ_x D^-1:
a conjugate of the shuffle of letter x. Its cycle shape is therefore that of μ_x:
  reinsertion (remove at q, reinsert at m) -> ONE cycle of length |q-m|+1, the rest fixed;
  swap of two positions -> a transposition (almost all the ciphertext identical).
For each shifted block of the map, we extract the chains and cycles of the observed partial bijection
c -> c'. Positions are 0-indexed.
"""
from stats import load_eyes
from architecture import iso_ok
names, M = load_eyes(); N = dict(zip(names, M))

# (message A, start A, message B, start B, length): shifted blocks from alignment_map / architecture
BLOCKS = [
    ("E4", 47, "E5", 48, 18), ("E4", 68, "E5", 69, 30),
    ("W4", 34, "E5", 33, 33), ("E5", 66, "W4", 68, 33),
    ("E4", 46, "W4", 48, 19), ("E4", 68, "W4", 71, 30),
    ("E1", 58, "W1", 60, 20), ("E1", 29, "E2", 34, 21), ("W1", 29, "E2", 34, 28), ("W1", 60, "E2", 70, 27),
]


def analyse(a, i, b, j, L):
    A, B = N[a][i:i + L], N[b][j:j + L]
    pairs = {}
    ok = iso_ok(A, B)
    for x, y in zip(A, B):
        pairs[x] = y
    fixed = sorted(x for x, y in pairs.items() if x == y)
    inv = {y: x for x, y in pairs.items()}
    # maximal chains and closed cycles
    seen, chains, cycles = set(), [], []
    for x in pairs:
        if x in seen or x == pairs[x]:
            continue
        # go back to the start of the chain
        s = x
        while s in inv and inv[s] != s and inv[s] not in (x,) and s not in seen:
            s = inv[s]
            if s == x:
                break
        cur, ch = s, [s]
        seen.add(s)
        closed = False
        while cur in pairs and pairs[cur] != cur:
            nxt = pairs[cur]
            if nxt == ch[0]:
                closed = True
                break
            if nxt in seen:
                break
            ch.append(nxt); seen.add(nxt); cur = nxt
        (cycles if closed else chains).append(ch)
    return ok, len(pairs), fixed, chains, cycles


if __name__ == "__main__":
    for a, i, b, j, L in BLOCKS:
        ok, n, fixed, chains, cycles = analyse(a, i, b, j, L)
        chains.sort(key=len, reverse=True)
        print(f"{a}@{i} -> {b}@{j} (L={L}, shift {j-i:+d}): isomorphic={ok}, {n} pairs, "
              f"{len(fixed)} fixed points, {len(cycles)} closed cycles {[len(c) for c in cycles]}, "
              f"open chains {[len(c) for c in chains]}")
        for c in cycles:
            print("     cycle:", " -> ".join(map(str, c)))
        if chains:
            print("     longest chain:", " -> ".join(map(str, chains[0])))
