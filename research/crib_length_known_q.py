"""Length of probable text needed under the "known positions" convention + letter frequencies (§44).

Like crib_length_test.py (§33.2), but under the convention of §39: the letter of rank k is read at position k.
We give the true plaintext (letters AND spaces) of the first T symbols of groups of messages; each card read
in that passage then has a known start position (x_c = F_t⁻¹(position of the letter)). The other
cards start at random, then EM with robust decisions and frequencies (known_positions_unigram). Measures:
correct start positions (best of R starts) and letter accuracy over the whole corpus.
Cases: probable text on ONE message of each group (E1, W2, E4), or on a single message (E1).
Usage: python crib_length_known_q.py [seed] [R]"""
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, scores, N
from keyed_deck_robust import decide, reads
from known_positions_unigram import logphi_unigram
import testbed_spaces as tbs
from explore import xgak_encrypt


def pinned(msg, plain, binv, sinv, alpha, T):
    """Start positions of the cards read in the first T symbols of a message whose plaintext is known."""
    F = np.arange(N)  # F[y] = current position of the card that started at y; we track the inverse
    G = np.arange(N)  # G[p] = start position of the card currently at p
    out = {}
    for t in range(min(T, len(msg))):
        p = alpha.index(plain[t])
        out[msg[t]] = int(G[p])
        S = sinv if plain[t] == "_" else binv
        Gn = np.empty(N, np.int64); Gn[S] = G  # the card at p moves to S[p]
        G = Gn
    return out


def em(C, st, ln, x, fixed, binv, sinv, qs, lp, lpl, iters=40):
    for _ in range(iters):
        sp = decide(C, st, ln, x, binv, sinv, qs, lpl, 16)
        sc = scores(C, st, ln, sp, binv, sinv, lp, True)
        for c, y in fixed.items():
            sc[c, :] = -1e9; sc[c, y] = 1e9
        rows, cols = linear_sum_assignment(-sc)
        xn = np.empty(N, np.int64); xn[rows] = cols
        if (xn == x).all():
            break
        x = xn
    return x


if __name__ == "__main__":
    names, BS, inv = tables()
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    pl = tbs.build_plaintexts()
    alpha = tbs.ALPHA_S
    q = np.arange(len(alpha), dtype=np.int64); qs = alpha.index("_")
    lp = logphi_unigram(alpha, tbs.english_with_spaces()[:1_000_000])
    lpl = lp.copy(); lpl[qs] = np.log(1e-6); lpl[:qs] -= np.log(np.exp(lp[:qs]).sum())
    plain = "".join(pl)
    for bname, sname in (("outshuffle", "milk"), ("rot1", "deal3fwd")):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, st, ln = flatten(msgs)
        x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
        binv, sinv = inv[bname], inv[sname]
        for lab, ids in (("E1 only", (0,)), ("E1+W2+E4", (0, 3, 6))):
            row = []
            for T in (10, 15, 20, 30, 45):
                fixed = {}
                for i in ids:
                    fixed.update(pinned(msgs[i], pl[i], binv, sinv, alpha, T))
                assert all(x_true[c] == y for c, y in fixed.items())
                best = (0, 0.0)
                for _ in range(R):
                    x = rng.permutation(N).astype(np.int64)
                    xf = em(C, st, ln, x, fixed, binv, sinv, qs, lp, lpl)
                    sp = decide(C, st, ln, xf, binv, sinv, qs, lpl, 16)
                    r = reads(C, st, ln, xf, binv, sinv, sp)
                    acc = float(np.mean([alpha[v] == ch if v < len(alpha) else False for v, ch in zip(r, plain)]))
                    best = max(best, (int((xf == x_true).sum()), acc))
                row.append(f"T={T}: {len(fixed)} cards given → {best[0]}/83, letters {best[1]:.2f}")
            print(f"β={bname} σ={sname} {lab}: " + " | ".join(row), flush=True)
