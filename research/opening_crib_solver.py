"""Guessed-openings solver under the known read positions convention (§44).

On the testbed, guessing the first 15 symbols (letters and spaces) of E1, W2 and E4, or 45 symbols of a single
message, is enough to decrypt everything (crib_length_known_q.py). This tool takes guessed openings and, for each
(convention, β, σ) combination that survived the local filter (known_q_local_filter_out.tsv), fixes the cards
read in the openings, runs EM with robust decisions + English frequencies, and ranks the combinations by
score per symbol (testbed truth ≈ -2.9; failure ≈ -6). The first symbol of each message is treated as
an ordinary symbol (digit) if it appears in the guessed text, otherwise as an unknown letter.
Usage:
  python opening_crib_solver.py banc                       (control on the testbed, true combination + 30 wrong ones)
  python opening_crib_solver.py yeux E1=TEXT W2=TEXT ... [tous] [max_combos]   (text in A-Z 1-9 and "_" for the space)
  Default: the 241 combinations best fitting the eyes (§45); "tous" (all): the 3,814 survivors of §42."""
import sys
import csv
import numpy as np
from scipy.optimize import linear_sum_assignment
from keyed_deck_attack import tables, flatten, scores, N
from keyed_deck_robust import decide, reads
from known_positions_unigram import logphi_unigram
from known_q_local_filter import ALPHAS
import testbed_spaces as tbs
from explore import xgak_encrypt

NAMES = ["E1", "W1", "E2", "W2", "E3", "W3", "E4", "W4", "E5"]


def convention(alpha_name, orient):
    alpha = ALPHAS[alpha_name]
    q = np.arange(len(alpha)) if orient == "k" else N - 1 - np.arange(len(alpha))
    return alpha, q.astype(np.int64)


def pin(msg, guess, q, alpha, binv, sinv, skip_first):
    G = np.arange(N); out = {}
    for t in range(min(len(guess), len(msg))):
        ch = guess[t]
        if not (t == 0 and skip_first):
            y = int(G[q[alpha.index(ch)]])
            if out.get(msg[t], y) != y or (y in out.values() and out.get(msg[t]) != y):
                return None  # inconsistency: same card, two starts, or two cards, same start
            out[msg[t]] = y
        S = sinv if ch == "_" else binv
        Gn = np.empty(N, np.int64); Gn[S] = G; G = Gn
    return out


def solve(msgs, guesses, alpha, q, binv, sinv, lp_alpha, rng, R=2, iters=40, skip_first=False):
    """Returns (score per symbol, x, reads) or None if the guessed openings are inconsistent."""
    qs = int(q[alpha.index("_")])
    lp = np.full(N, np.log(1e-4 / N)); lp[q] = lp_alpha
    lpl = lp.copy(); lpl[qs] = np.log(1e-6)
    let = [int(v) for v in q if v != qs]; lpl[let] -= np.log(np.exp(lp[let]).sum())
    fixed = {}
    for i, g in guesses.items():
        f = pin(msgs[i], g, q, alpha, binv, sinv, skip_first)
        if f is None:
            return None
        for c, y in f.items():
            if fixed.get(c, y) != y:
                return None
            fixed[c] = y
    if len(set(fixed.values())) < len(fixed):
        return None
    C, st, ln = flatten(msgs)
    best = None
    for _ in range(R):
        x = rng.permutation(N).astype(np.int64)
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
        sp = decide(C, st, ln, x, binv, sinv, qs, lpl, 16)
        r = reads(C, st, ln, x, binv, sinv, sp)
        s = float(lp[r].sum()) / len(r)
        if best is None or s > best[0]:
            best = (s, x, r)
    return best


def decode_text(r, q, alpha, st, ln):
    inv = {int(v): ch for v, ch in zip(q, alpha)}
    return ["".join(inv.get(int(v), "?") for v in r[a:a + l]) for a, l in zip(st, ln)]


def top_combos(min_rate=0.3):
    """Combinations best fitting the statistics of the eyes (§45, convention_top_out_*.tsv), best first."""
    import glob
    rows = []
    for f in glob.glob("convention_top_out_*.tsv"):
        for l in open(f, encoding="utf-8"):
            a, o, b, s, acc, *_ = l.rstrip("\n").split("\t")
            if float(acc) >= min_rate:
                rows.append({"alphabet": a, "orient": o, "beta": b, "sigma": s, "rate": float(acc)})
    rows.sort(key=lambda r: -r["rate"])
    return rows


def survivors(thr=0.05):
    rows = list(csv.DictReader(open("known_q_local_filter_out.tsv", encoding="utf-8"), delimiter="\t"))
    ok = [r for r in rows if min(float(r["P1"]), float(r["P2"]), float(r["P3"])) >= thr]
    ok.sort(key=lambda r: -min(float(r["P1"]), float(r["P2"]), float(r["P3"])))
    return ok


if __name__ == "__main__":
    names, BS, INV = tables()
    rng = np.random.default_rng(1)
    T = tbs.english_with_spaces()[:1_000_000]
    if sys.argv[1] == "banc":
        alpha, q = convention("AZ19_", "k")
        lpa = logphi_unigram(alpha, T)[:len(alpha)]
        pl = tbs.build_plaintexts()
        b, s = "outshuffle", "milk"
        D0 = rng.permutation(N)
        S = np.array([BS[s] if ch == "_" else BS[b] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        guesses = {0: pl[0][:15], 3: pl[3][:15], 6: pl[6][:15]}
        res = solve(msgs, guesses, alpha, q, INV[b], INV[s], lpa, rng)
        C, st, ln = flatten(msgs)
        print(f"true combination: score {res[0]:.2f} per symbol; {decode_text(res[2], q, alpha, st, ln)[0][:60]}")
        keys = [k for k in BS if k != "id"]
        sc = []
        for _ in range(30):
            b2, s2 = rng.choice(keys, 2, replace=False)
            r2 = solve(msgs, guesses, alpha, q, INV[b2], INV[s2], lpa, rng, R=1)
            sc.append(None if r2 is None else round(r2[0], 2))
        print(f"30 wrong combinations: {sum(v is None for v in sc)} inconsistent at once; scores of the others: "
              f"{sorted(v for v in sc if v is not None)[-5:]} (best)")
    else:
        from stats import load_eyes
        _, M = load_eyes()
        guesses = {}
        for a in sys.argv[2:]:
            if "=" in a:
                k, v = a.split("=", 1); guesses[NAMES.index(k)] = v.upper()
        maxc = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 10 ** 6
        out = []
        combos = survivors() if "tous" in sys.argv else top_combos()
        for i, row in enumerate(combos[:maxc]):
            alpha, q = convention(row["alphabet"], row["orient"])
            if any(ch not in alpha for g in guesses.values() for ch in g):
                continue
            lpa = logphi_unigram(alpha, T)[:len(alpha)]
            res = solve(M, guesses, alpha, q, INV[row["beta"]], INV[row["sigma"]], lpa, rng, R=1)
            if res is not None:
                out.append((res[0], row, res))
        out.sort(key=lambda z: -z[0])
        C, st, ln = flatten(M)
        print(f"{len(out)} combinations consistent with the guessed openings; success threshold on the testbed ≈ -3.2")
        for s, row, res in out[:5]:
            alpha, q = convention(row["alphabet"], row["orient"])
            print(f"  {s:.2f} {row['alphabet']}/{row['orient']} β={row['beta']} σ={row['sigma']} : "
                  f"{decode_text(res[2], q, alpha, st, ln)[0][:70]}")
