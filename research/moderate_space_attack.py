"""Attack on the space model with a MODERATE space shuffle (§41): σ = τ_k ∘ β, τ_k = k random swaps.

Question: when σ is close to β, a wrong space decision moves only ≤ 2k cards instead of
the whole deck. Does the cascade of decisions (the lock of §33) disappear? We reuse the keyed
starting deck attack (keyed_deck_attack.attack, random starts) on the testbed with spaces, known natural β:
  A: σ known (oracle on τ);
  B: σ assumed equal to β (spaces ignored: no decisions);
  C: robust decisions (keyed_deck_robust.robust_em) from a random start, σ known.
Measure: correct start positions out of 83 (best of R starts) and entropy of the read positions.
Usage: python moderate_space_attack.py [seed] [R]"""
import sys
import numpy as np
from keyed_deck_attack import tables, flatten, decode, attack, entropy, N
from keyed_deck_robust import robust_em
import testbed_spaces as tbs
from explore import xgak_encrypt


def sigma_from(beta_S, k, rng):
    idx = np.arange(N)
    for _ in range(k):
        a, b = rng.choice(N, 2, replace=False)
        idx[[a, b]] = idx[[b, a]]
    return idx[beta_S]


def inv(p):
    q = np.empty(N, np.int64); q[p] = np.arange(N); return q


def make_case(pl, bS, k, rng):
    sS = sigma_from(bS, k, rng)
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([sS if ch == "_" else bS for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist()
            for m in pl]
    x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
    return msgs, sS, x_true, int(q[tbs.ALPHA_S.index("_")])


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    rng = np.random.default_rng(seed)
    names, BS, INV = tables()
    pl = tbs.build_plaintexts()
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    for bname in ("rot1", "outshuffle", "deal3fwd"):
        for k in (0, 2, 4, 8, 16, 40):
            msgs, sS, x_true, qs = make_case(pl, BS[bname], k, rng)
            C, starts, lens = flatten(msgs)
            binv, sinv = INV[bname], inv(sS)
            r, _ = decode(C, starts, lens, x_true, binv, sinv, qs, True)
            hA, xA, _ = attack(C, starts, lens, binv, sinv, True, rng, restarts=R)
            hB, xB, _ = attack(C, starts, lens, binv, binv, True, rng, restarts=R)
            bestC = 0; decC = 0
            for _ in range(R):
                xC, spC = robust_em(C, starts, lens, rng.permutation(N).astype(np.int64), qs, binv, sinv)
                if (xC == x_true).sum() >= bestC:
                    bestC = int((xC == x_true).sum()); decC = int((spC == sp_true).sum())
            print(f"β={bname:10s} k={k:2d} | truth H={entropy(r):.2f} | A σ known: {int((xA == x_true).sum()):2d}/83 "
                  f"H={hA:.2f} | B σ:=β: {int((xB == x_true).sum()):2d}/83 H={hB:.2f} | "
                  f"C robust: {bestC:2d}/83 (decisions {decC}/{len(sp_true)})", flush=True)
