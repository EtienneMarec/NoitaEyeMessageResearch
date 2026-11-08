"""ABC filter of the (read convention, β, σ) combinations surviving §42 (§45).

For each combination surviving the local filter (known_q_local_filter_out.tsv, P ≥ 0.05 for d = 1, 2, 3):
R simulated corpora (testbed with spaces, English text, E5 stutter with n ∈ {6, 9, 12, 15} changed letters as
in abc_simulate.py), space model with read positions FIXED by the convention and natural (β, σ); the 11
statistics of abc_stats; standardised distance to the eyes (same IQR scale as abc_posterior.py, computed on
abc_sims.tsv). Acceptance rate = share of simulations at distance ≤ threshold (threshold = acceptance distance at
ε = 0.02 of abc_posterior, 1.73). Comparison: rate of the space-model ("espace") simulations of abc_sims.tsv (random q).
Output: convention_abc_out_{part}.tsv (or {prefix}_{part}.tsv).
Usage: python convention_abc_filter.py R part nparts [combinations file] [output prefix]"""
import sys
import random
import numpy as np
import testbed_spaces as tbs
from explore import xgak_encrypt
from deckcipher import base_shuffles
from abc_stats import summary, NAMES_STATS
from stats import load_eyes
from known_q_local_filter import ALPHAS
from opening_crib_solver import survivors

N = 83
LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
THR = 1.73


def scale_and_eyes():
    S = []
    for line in open("abc_sims.tsv", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 4 + len(NAMES_STATS):
            try:
                S.append([float(v) for v in p[4:]])
            except ValueError:
                pass
    S = np.array(S)
    q75, q25 = np.percentile(S, 75, axis=0), np.percentile(S, 25, axis=0)
    scale = np.where(q75 - q25 > 0, q75 - q25, S.std(axis=0) + 1e-9)
    _, M = load_eyes()
    e = np.array([float(f"{v:.5g}") for v in summary(M, 25)])
    return scale, e


def corpus(bases, rnd):
    pl = list(bases[rnd.randrange(len(bases))])
    pl[8] = "9" + pl[6][1:47] + "S" + pl[6][47:]
    e5 = list(pl[8]); idx = [i for i in range(21, 47) if e5[i] != "_"]
    for i in rnd.sample(idx, min(rnd.choice((6, 9, 12, 15)), len(idx))):
        e5[i] = rnd.choice([c for c in LET if c != e5[i]])
    pl[8] = "".join(e5)
    return pl


if __name__ == "__main__":
    R = int(sys.argv[1]); part = int(sys.argv[2]); nparts = int(sys.argv[3])
    rnd = random.Random(1000 + part)
    BS = base_shuffles()
    scale, e = scale_and_eyes()
    bases = [tbs.build_plaintexts(seed=s, word_start=True) for s in range(10)]
    if len(sys.argv) > 4:
        import csv
        rows = list(csv.DictReader(open(sys.argv[4], encoding="utf-8"), delimiter="	"))[part::nparts]
    else:
        rows = survivors()[part::nparts]
    prefix = sys.argv[5] if len(sys.argv) > 5 else "convention_abc_out"
    with open(f"{prefix}_{part}.tsv", "w", encoding="utf-8") as f:
        for row in rows:
            alpha = ALPHAS[row["alphabet"]]
            rank = np.array([alpha.index(ch) for ch in tbs.ALPHA_S])
            q = (rank if row["orient"] == "k" else N - 1 - rank).astype(np.int64)
            S = np.array([BS[row["sigma"]] if ch == "_" else BS[row["beta"]] for ch in tbs.ALPHA_S], np.int64)
            ds = []
            for _ in range(R):
                pl = corpus(bases, rnd)
                d0 = tbs.obstacle_window(pl)
                C = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
                s = np.array([float(f"{v:.5g}") for v in summary(C, d0)])
                ds.append(float(np.sqrt((((s - e) / scale) ** 2).sum())))
            f.write("\t".join([row["alphabet"], row["orient"], row["beta"], row["sigma"],
                               f"{np.mean(np.array(ds) <= THR):.3f}", f"{np.median(ds):.2f}", f"{min(ds):.2f}"]) + "\n")
            f.flush()
