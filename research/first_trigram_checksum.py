"""Is the first trigram a checksum / an index computable from the rest of the message?
We test a battery of simple functions f(message without its first trigram, length, rank) and look for
a constant k (mod 83 or mod 125) such that first = f + k (or k - f, or k·f) for the 9 messages.
An exact relation over 9 messages would have probability ~ 83^-8 per function tested (k free).
Positions are 0-indexed; rank = internal order E1, W1, E2, W2, E3, W3, E4, W4, E5 (0..8)."""
import numpy as np
from stats import load_eyes
names, M = load_eyes()
first = [m[0] for m in M]
rest = [m[1:] for m in M]
feats = {
    "sum": [sum(r) for r in rest],
    "weighted_sum_i": [sum((i + 1) * v for i, v in enumerate(r)) for r in rest],
    "alternating_sum": [sum(v if i % 2 == 0 else -v for i, v in enumerate(r)) for r in rest],
    "xor": [int(np.bitwise_xor.reduce(np.array(r))) for r in rest],
    "last": [r[-1] for r in rest],
    "second_to_last": [r[-2] for r in rest],
    "length": [len(m) for m in M],
    "remaining_length": [len(r) for r in rest],
    "rank": list(range(9)),
    "rank_per_world": [0, 0, 1, 1, 2, 2, 3, 3, 4],
    "sum_of_eyes": [sum(int(d) for v in r for d in np.base_repr(v, 5)) for r in rest],
    "product_mod83": [int(np.prod([v % 83 or 1 for v in r], dtype=object) % 83) for r in rest],
    "n_distinct": [len(set(r)) for r in rest],
    "sum_of_differences": [sum((b - a) % 83 for a, b in zip(r, r[1:])) for r in rest],
}
hits = []
for name, f in feats.items():
    for mod in (83, 125):
        for op in ("f+k", "k-f", "k*f"):
            for k in range(mod):
                if op == "f+k":
                    pred = [(x + k) % mod for x in f]
                elif op == "k-f":
                    pred = [(k - x) % mod for x in f]
                else:
                    pred = [(k * x) % mod for x in f]
                ok = sum(p == t for p, t in zip(pred, first))
                if ok >= 4:
                    hits.append((ok, name, mod, op, k))
hits.sort(reverse=True)
print("first trigrams:", first)
print("best relations (number of messages explained out of 9):")
for h in hits[:10]:
    print("  ", h)
n_tests = len(feats) * 2 * 3 * 100
print(f"~{n_tests} relations tested; by chance, explaining 3 messages out of 9 is common, 5 or more would be notable.")
