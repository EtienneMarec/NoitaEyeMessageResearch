"""Attack on the starting deck when the read positions follow a known convention (§39).

Design hypothesis: the letter of rank k (in a given alphabet: A-Z then space, or the runic alphabet
"BDMAGICKEFHJLNOPQRSTUVWXYZ") is read at deck position k (or 82 - k). The read positions are then
KNOWN, and so is the law φ (which coupled everything, §36): each card is placed independently of the others.
Algorithm: robust decisions (keyed_deck_robust.decide, φ = uniform over the known positions), then
Hungarian assignment of the start positions, in a loop, from a random deck.
Validation on the testbed with spaces, known natural shuffles (β, σ)."""
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, scores, N
from keyed_deck_robust import decide, reads
import testbed_spaces as tbs
from explore import xgak_encrypt


def logphi_known(Q, eps=1e-3):
    lp = np.full(N, np.log(eps / N))
    lp[list(Q)] = np.log((1 - eps) / len(Q))
    return lp


def attack_known(C, starts, lens, binv, sinv, Q, qs, rng, iters=30, Bw=16, restarts=3):
    lp = logphi_known(Q)
    lpl = lp.copy(); lpl[qs] = np.log(1e-6)
    best = (-1e18, None, None)
    for _ in range(restarts):
        x = rng.permutation(N).astype(np.int64)
        for it in range(iters):
            sp = decide(C, starts, lens, x, binv, sinv, qs, lpl, Bw)
            sc = scores(C, starts, lens, sp, binv, sinv, lp, True)
            rows, cols = linear_sum_assignment(-sc)
            xn = np.empty(N, np.int64); xn[rows] = cols
            if (xn == x).all():
                break
            x = xn
        sp = decide(C, starts, lens, x, binv, sinv, qs, lpl, Bw)
        r = reads(C, starts, lens, x, binv, sinv, sp)
        s = float(lp[r].sum())
        if s > best[0]:
            best = (s, x.copy(), sp)
    return best


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 9)
    pl = tbs.build_plaintexts()
    alpha = tbs.ALPHA_S                     # A-Z, 1-9, _: position = rank in this alphabet
    q = np.arange(len(alpha), dtype=np.int64)
    Q = set(q.tolist()); qs = int(q[alpha.index("_")])
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk"), ("deal2fwd", "rot5")):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        s, x, sp = attack_known(C, starts, lens, inv[bname], inv[sname], Q, qs, rng)
        print(f"β={bname:10s} σ={sname:9s}: correct start positions {int((x == x_true).sum())}/83, "
              f"correct decisions {int((sp == sp_true).sum())}/{len(sp_true)}", flush=True)
        s2, x2, _ = attack_known(C, starts, lens, inv["rot2"], inv["deal3rev"], Q, qs, rng)
        print(f"   control (wrong pair): score {s2:.0f} versus {s:.0f}", flush=True)
