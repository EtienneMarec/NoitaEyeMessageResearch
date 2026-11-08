"""Time-progressive attack on the space model with a moderate shuffle (§41).

Idea: at the start of the messages, few spaces have occurred; if σ = τ_k ∘ β with small k, the deck stays
close to the "all β" (progressive) cipher, which EM solves from a random start. So we learn the
starting deck on the first T symbols of each message, then lengthen T starting from the previous
solution (robust decisions, keyed_deck_robust.robust_em; q_space = most frequent read).
Success measure invariant under relabelling of the read positions: letter accuracy, each read position
being associated with its majority symbol (the truth gives 1.00; a random deck gives the baseline).
Usage: python moderate_space_curriculum.py [seed] [R]"""
import sys
from collections import Counter, defaultdict
import numpy as np
from keyed_deck_attack import tables, flatten, decode, attack, N
from keyed_deck_robust import robust_em, reads
from moderate_space_attack import make_case, inv
import testbed_spaces as tbs

STEPS = (12, 20, 30, 45, 70, 100, 140, 10 ** 6)


def letter_acc(r, plain):
    by = defaultdict(Counter)
    for a, ch in zip(r.tolist(), plain):
        by[a][ch] += 1
    return sum(c.most_common(1)[0][1] for c in by.values()) / len(plain)


def truncate(msgs, T):
    return flatten([m[:T] for m in msgs])


def curriculum(msgs, binv, sinv, rng):
    x = rng.permutation(N).astype(np.int64)
    for T in STEPS:
        C, st, ln = truncate(msgs, T)
        r, _ = decode(C, st, ln, x, binv, sinv, -1, True)
        qs = int(np.argmax(np.bincount(r, minlength=N)))
        x, sp = robust_em(C, st, ln, x, qs, binv, sinv, iters=20, Bw=8)
    C, st, ln = flatten(msgs)
    return x, reads(C, st, ln, x, binv, sinv, sp)


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    rng = np.random.default_rng(seed)
    names, BS, INV = tables()
    pl = tbs.build_plaintexts()
    plain = "".join(pl)
    for bname in ("outshuffle", "deal3fwd"):
        for k in (0, 1, 2, 4, 8, 16):
            msgs, sS, x_true, qs = make_case(pl, BS[bname], k, rng)
            C, st, ln = flatten(msgs)
            binv, sinv = INV[bname], inv(sS)
            sp_true = np.array([ch == "_" for ch in plain])
            base = letter_acc(reads(C, st, ln, rng.permutation(N).astype(np.int64), binv, sinv, sp_true), plain)
            hA, xA, qA = attack(C, st, ln, binv, sinv, True, rng, restarts=R)
            rA, _ = decode(C, st, ln, xA, binv, sinv, qA, True)
            accC = []
            for _ in range(R):
                xc, rc = curriculum(msgs, binv, sinv, rng)
                accC.append(round(letter_acc(rc, plain), 2))
            print(f"β={bname:10s} k={k:2d} | base {base:.2f} | direct EM {letter_acc(rA, plain):.2f} | "
                  f"progressive {accC}", flush=True)
