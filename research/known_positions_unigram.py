"""Convention "known read positions" + letter frequencies (§44).

Under the convention of §39, the position read IS the letter. The attack of §39 (known_positions_attack.py) scored
reads with a uniform law over the 36 known positions, and so did not use the language. Here, φ(y) =
frequency of letter y in English (space included), both in the robust decisions and in the
Hungarian assignment. Information budget (§42): about +1 bit per symbol, which should make the
problem clearly identifiable. Testbed with spaces, random starts.
Usage: python known_positions_unigram.py [seed] [starts]"""
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, scores, N
from keyed_deck_robust import decide, reads
import testbed_spaces as tbs
from explore import xgak_encrypt
from moderate_space_curriculum import letter_acc


def logphi_unigram(alpha, T, eps=1e-4):
    cnt = np.array([T.count(ch) for ch in alpha], float) + 1.0
    p = cnt / cnt.sum()
    lp = np.full(N, np.log(eps / N))
    lp[:len(alpha)] = np.log((1 - eps) * p)
    return lp


def attack_unigram(C, starts, lens, binv, sinv, lp, qs, rng, iters=40, Bw=16, restarts=10, x_true=None):
    lpl = lp.copy(); lpl[qs] = np.log(1e-6)
    lpl[:qs] -= np.log(np.exp(lp[:qs]).sum())  # law of the letters given "letter"
    out = []
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
        out.append((float(lp[r].sum()), int((x == x_true).sum()) if x_true is not None else -1, r))
    return out


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 9)
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    pl = tbs.build_plaintexts()
    alpha = tbs.ALPHA_S
    q = np.arange(len(alpha), dtype=np.int64); qs = alpha.index("_")
    lp = logphi_unigram(alpha, tbs.english_with_spaces()[:1_000_000])
    plain = "".join(pl)
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk"), ("deal2fwd", "rot5")):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        sp_true = np.array([ch == "_" for ch in plain])
        r_true = reads(C, starts, lens, x_true, inv[bname], inv[sname], sp_true)
        res = attack_unigram(C, starts, lens, inv[bname], inv[sname], lp, qs, rng, restarts=R, x_true=x_true)
        res.sort(key=lambda z: -z[0])
        print(f"β={bname:10s} σ={sname:9s}: true score {lp[r_true].sum():.0f}; starts (score, correct positions) "
              f"{[(round(s), k) for s, k, _ in res]}; letters of the best {letter_acc(res[0][2], plain):.2f}", flush=True)
