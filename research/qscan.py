"""Scan of natural "deck of cards" mechanisms: for each, the sequence of read positions q is computed
from the ciphertext (initial deck assumed known) and its IoC is measured.
True mechanism: only ~35 values of q, language-like IoC (≈ 3 to 5 in ×83 units).
Wrong mechanism: q ~ uniform, IoC ≈ 1.

Initial decks tried: sorted (0..82) and reversed.
"""
import sys
import numpy as np
from deckcipher import recover_q, ioc83, base_shuffles, RULES, N


def scan(cipher_msgs, bases=None, rules=range(len(RULES)), orders=(0, 1), skip_first=True):
    bases = bases or base_shuffles()
    D0s = {"sorted": np.arange(N), "reversed": np.arange(N)[::-1].copy()}
    arrs = [np.array(m, np.int64) for m in cipher_msgs]
    res = []
    for d0name, D0 in D0s.items():
        for bname, beta in bases.items():
            for rule in rules:
                for order in orders:
                    qs = [recover_q(a, D0, beta, rule, order) for a in arrs]
                    if skip_first:
                        qs = [q[1:] for q in qs]
                    ic, distinct = ioc83(qs)
                    res.append((ic, distinct, d0name, bname, RULES[rule], order))
    res.sort(reverse=True)
    return res


def report(res, top=10):
    ics = np.array([r[0] for r in res])
    print(f"{len(res)} mechanisms tested; median IoC {np.median(ics):.3f}, std {ics.std():.3f}")
    print("   IoC  q-values      deck      base shuffle      rule       order")
    for ic, d, d0, b, r, o in res[:top]:
        z = (ic - np.median(ics)) / ics.std()
        print(f"{ic:6.3f}  {d:4d}          {d0:8s}  {b:16s}  {r:9s}  {o}    (z={z:.1f})")


if __name__ == "__main__":
    from stats import load_eyes
    names, M = load_eyes()
    report(scan(M), top=int(sys.argv[1]) if len(sys.argv) > 1 else 15)
