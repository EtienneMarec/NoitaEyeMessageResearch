"""Per-statistic detail of the best (convention, β, σ) combinations of the ABC filter (§45).

For the K best combinations of convention_top_out_*.tsv: 100 simulated corpora, median of each statistic
and mean contribution (squared standardised deviation) to the ABC distance, compared with the generic space model
(espace_16, random q, English, abc_sims.tsv). Shows what makes these combinations closer to the eyes.
Usage: python convention_top_detail.py [K] [R]"""
import sys
import glob
import random
import numpy as np
import testbed_spaces as tbs
from explore import xgak_encrypt
from deckcipher import base_shuffles
from abc_stats import summary, NAMES_STATS
from known_q_local_filter import ALPHAS
from convention_abc_filter import scale_and_eyes, corpus, N

if __name__ == "__main__":
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    scale, e = scale_and_eyes()
    BS = base_shuffles(); rnd = random.Random(5)
    bases = [tbs.build_plaintexts(seed=s, word_start=True) for s in range(10)]
    G = []
    for line in open("abc_sims.tsv", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 4 + len(NAMES_STATS) and p[0] == "espace" and p[1] == "16" and p[2] == "anglais":
            G.append([float(v) for v in p[4:]])
    G = np.array(G)
    print("statistic        eyes    | generic: median, contrib.     | combinations: median, contrib.")
    rows = []
    for f in glob.glob("convention_top_out_*.tsv"):
        rows += [l.rstrip("\n").split("\t") for l in open(f, encoding="utf-8")]
    rows.sort(key=lambda r: -float(r[4]))
    sims = []
    for a, o, b, s, *_ in rows[:K]:
        alpha = ALPHAS[a]
        rank = np.array([alpha.index(ch) for ch in tbs.ALPHA_S])
        q = (rank if o == "k" else N - 1 - rank).astype(np.int64)
        S = np.array([BS[s] if ch == "_" else BS[b] for ch in tbs.ALPHA_S], np.int64)
        for _ in range(R):
            pl = corpus(bases, rnd)
            C = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
            sims.append(summary(C, tbs.obstacle_window(pl)))
    T = np.array(sims)
    for j, n in enumerate(NAMES_STATS):
        cg = np.mean(((G[:, j] - e[j]) / scale[j]) ** 2); ct = np.mean(((T[:, j] - e[j]) / scale[j]) ** 2)
        print(f"{n:12s} {e[j]:9.4g} | {np.median(G[:, j]):9.4g}  {cg:6.2f} | {np.median(T[:, j]):9.4g}  {ct:6.2f}")
    dg = np.sqrt((((G - e) / scale) ** 2).sum(axis=1)); dt = np.sqrt((((T - e) / scale) ** 2).sum(axis=1))
    print(f"acceptance (≤ 1.73): generic {np.mean(dg <= 1.73):.3f}; {K} best combinations {np.mean(dt <= 1.73):.3f}")
