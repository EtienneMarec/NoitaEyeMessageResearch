"""ABC rejection inference (§40): posterior probabilities of the hypotheses, from abc_sims.tsv.

Uniform prior over (family, text, n) (uniform draws in abc_simulate.py). Distance = Euclidean norm of the
standardised statistics (interquartile range of the simulations); we keep the fraction ε of simulations
closest to the eyes, and each hypothesis's share among them estimates its posterior probability.
Predictive check: for each family and each statistic, share of simulations at least as extreme as the eyes
(two-sided), to spot the statistics a family cannot reproduce."""
import sys
from collections import Counter
import numpy as np
from abc_stats import summary, NAMES_STATS
from stats import load_eyes

if __name__ == "__main__":
    eps = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
    names, M = load_eyes()
    e = np.array([float(f"{v:.5g}") for v in summary(M, 25)])  # same rounding as abc_sims.tsv
    rows = []
    for line in open("abc_sims.tsv", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) != 4 + len(NAMES_STATS):
            continue
        try:
            rows.append((p[0] + ("" if p[0] == "reinsertion" else "_" + p[1]), p[2], int(p[3]), np.array([float(v) for v in p[4:]])))
        except ValueError:
            continue
    S = np.array([r[3] for r in rows])
    q75, q25 = np.percentile(S, 75, axis=0), np.percentile(S, 25, axis=0)
    scale = np.where(q75 - q25 > 0, q75 - q25, S.std(axis=0) + 1e-9)
    d = np.sqrt((((S - e) / scale) ** 2).sum(axis=1))
    k = max(10, int(eps * len(rows)))
    keep = np.argsort(d)[:k]
    print(f"{len(rows)} simulations; eyes: " + ", ".join(f"{n}={v:.3g}" for n, v in zip(NAMES_STATS, e)))
    print(f"ε = {eps}: {k} simulations kept (max distance {d[keep[-1]]:.2f}, overall median {np.median(d):.2f})")
    for lab, idx in (("family", 0), ("text", 1), ("n (stutter)", 2)):
        prior = Counter(r[idx] for r in rows)
        post = Counter(rows[i][idx] for i in keep)
        print(f"  {lab}: " + "; ".join(f"{h} {post[h] / k:.2f} (prior {prior[h] / len(rows):.2f})"
                                      for h in sorted(prior, key=lambda h: -post[h])))
    prior = Counter(r[0] for r in rows); post = Counter(rows[i][0] for i in keep)
    w = {h: (post[h] / k) / (prior[h] / len(rows)) for h in prior}; z = sum(w.values())
    print("  family, with equal priors across families (simulation batches do not all contain the same families):")
    print("    " + "; ".join(f"{h} {w[h] / z:.3f}" for h in sorted(w, key=lambda h: -w[h])))
    print("predictive check (share of the family's simulations at least as extreme as the eyes):")
    fams = sorted(set(r[0] for r in rows))
    print("  " + " " * 14 + "  ".join(f"{n[:9]:>9s}" for n in NAMES_STATS))
    for f in fams:
        Sf = np.array([r[3] for r in rows if r[0] == f])
        pv = []
        for j in range(len(NAMES_STATS)):
            lo = np.mean(Sf[:, j] <= e[j]); hi = np.mean(Sf[:, j] >= e[j])
            pv.append(min(1.0, 2 * min(lo, hi)))
        print(f"  {f:14s}" + "  ".join(f"{v:9.2f}" for v in pv))
