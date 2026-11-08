"""User's hypothesis: the deck key might come from another Noita secret, here the 64-byte cauldron block
(512 bits, 365 of which for the calendar; an arbitrary permutation of 83 cards needs ~414 bits).

We derive permutations of 83 elements from these bytes in several natural ways, then try them (and their
inverses) as:
  * starting deck D0, with the 8 rules × a few base shuffles (qscan family);
  * base shuffle β, sorted or reversed deck;
  * reinsertion table F (the card read at q is reinserted at F[q]), sorted deck or deck = permutation.
Measures: IoC of the sequence of read positions (qscan families) and number of distinct read positions
(reinsertion). Baseline: the same tests with 200 random permutations (same number of trials).
"""
import math
import numpy as np
from stats import load_eyes
from deckcipher import recover_q, ioc83, base_shuffles, RULES, N
from reinsert_scan import recover_q_reinsert

DATA = bytes([0x12, 0x3b, 0x92, 0xe2, 0x41, 0xf0, 0xe2, 0x1f, 0xef, 0xf1, 0x03, 0x3e, 0x16, 0xa6, 0x46, 0x3b,
              0xdc, 0x00, 0xdd, 0xce, 0xd0, 0xb0, 0x56, 0x1e, 0x98, 0x29, 0xfa, 0x95, 0x13, 0x55, 0x25, 0x9c,
              0x45, 0x2e, 0x47, 0xbd, 0x8f, 0x22, 0x98, 0xfc, 0x41, 0x74, 0x68, 0xfc, 0x65, 0x32, 0x36, 0x7b,
              0xaf, 0xbc, 0xc7, 0xec, 0x60, 0x14, 0x63, 0xd3, 0xda, 0x20, 0xe3, 0xbf, 0xc4, 0x98, 0xf5, 0x32])


def factoradic(x, n=N):
    """Permutation of rank x (Lehmer code), x reduced modulo n!."""
    x %= math.factorial(n)
    items, out = list(range(n)), []
    for i in range(n, 0, -1):
        f = math.factorial(i - 1)
        k, x = divmod(x, f)
        out.append(items.pop(k))
    return out


def fisher_yates(stream, n=N):
    p = list(range(n))
    it = iter(stream)
    for i in range(n - 1, 0, -1):
        j = next(it) % (i + 1)
        p[i], p[j] = p[j], p[i]
    return p


def bits(data, lsb_first):
    out = []
    for b in data:
        for k in range(8):
            out.append((b >> k) & 1 if lsb_first else (b >> (7 - k)) & 1)
    return out


def chunks(bitlist, w):
    return [int("".join(map(str, bitlist[i:i + w])), 2) for i in range(0, len(bitlist) - w + 1, w)]


def cauldron_perms():
    P = {}
    for endian in ("big", "little"):
        P[f"lehmer_{endian}"] = factoradic(int.from_bytes(DATA, endian))
    for lsb in (False, True):
        b = bits(DATA, lsb)
        P[f"lehmer_bits_{'lsb' if lsb else 'msb'}"] = factoradic(int("".join(map(str, b)), 2))
        six = chunks(b, 6)[:N]
        P[f"argsort6_{'lsb' if lsb else 'msb'}"] = list(np.argsort(np.array(six), kind="stable"))
        P[f"fisher_yates_bits8_{'lsb' if lsb else 'msb'}"] = fisher_yates(chunks(b, 8) * 3)
    P["fisher_yates_bytes"] = fisher_yates(list(DATA) * 3)
    P["fisher_yates_bytes_rev"] = fisher_yates(list(DATA[::-1]) * 3)
    out = {}
    for k, v in P.items():
        v = np.array(v, np.int64)
        assert sorted(v.tolist()) == list(range(N)), k
        out[k] = v
        inv = np.empty(N, np.int64); inv[v] = np.arange(N); out[k + "_inv"] = inv
    return out


def tests(perm, arrs, bases):
    """Returns (best IoC over the qscan families, minimum number of distinct positions for reinsertion)."""
    best_ioc = 0.0
    ident = np.arange(N)
    for bname, beta in bases.items():
        for rule in range(len(RULES)):
            for order in (0, 1):
                for D0, bb in ((perm, beta), (ident, perm), (ident[::-1].copy(), perm)):
                    qs = [recover_q(a, D0, bb, rule, order)[1:] for a in arrs]
                    ic, _ = ioc83(qs)
                    best_ioc = max(best_ioc, ic)
    min_distinct = 99
    for D0 in (ident, perm):
        for F in (perm, np.argsort(perm)):
            for start in (0, 1):
                qs = [recover_q_reinsert(a, D0, F, ident, start) for a in arrs]
                v = np.concatenate([q[q >= 0] for q in qs])
                min_distinct = min(min_distinct, len(set(v.tolist())))
    return best_ioc, min_distinct


if __name__ == "__main__":
    names, M = load_eyes()
    arrs = [np.array(m, np.int64) for m in M]
    bases = {k: v for k, v in base_shuffles().items() if k in ("id", "reverse", "rot1", "rot82", "outshuffle", "inshuffle")}
    print("permutation derived from the cauldron   best IoC   distinct positions (reinsertion)")
    res = {}
    for name, p in cauldron_perms().items():
        res[name] = tests(p, arrs, bases)
        print(f"  {name:32s}  {res[name][0]:6.3f}        {res[name][1]}", flush=True)
    rng = np.random.default_rng(0)
    null = [tests(rng.permutation(N), arrs, bases) for _ in range(200)]
    ni = np.array([x[0] for x in null]); nd = np.array([x[1] for x in null])
    print(f"\nbaseline (200 random permutations): max IoC {ni.mean():.3f} ± {ni.std():.3f} (max {ni.max():.3f}); "
          f"min distinct positions {nd.min()}, median {np.median(nd):.0f}")
    best = max(res.values(), key=lambda x: x[0])[0]
    print(f"best cauldron IoC {best:.3f} -> share of random permutations above it: {np.mean(ni >= best):.2f}")
    print("for reference, a true mechanism on the testbed: IoC ≈ 5.5 and ~25 to 31 positions")
