"""Is the "space almost equal to β" regime (k ≤ 2 swaps) compatible with the eyes? (§41)

On the testbed, the keyed-deck attack only succeeds for k ≤ 2 (moderate_space_curriculum.py). From
abc_sims.tsv (families espace_k) we read: the posterior probability of each k with equal priors across k
(ratio posterior share / prior share, rejection ABC as in abc_posterior.py but restricted to the "espace"
(space model) families), per text type, and the predictive check per statistic and per text.
Usage: python abc_small_k.py [eps]"""
import sys
from collections import Counter
import numpy as np
from abc_stats import summary, NAMES_STATS
from stats import load_eyes

if __name__ == "__main__":
    eps = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
    names, M = load_eyes()
    e = np.array([float(f"{v:.5g}") for v in summary(M, 25)])
    rows = []
    for line in open("abc_sims.tsv", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) != 4 + len(NAMES_STATS) or p[0] != "espace":
            continue
        try:
            rows.append((p[1], p[2], np.array([float(v) for v in p[4:]])))
        except ValueError:
            continue
    S = np.array([r[2] for r in rows])
    q75, q25 = np.percentile(S, 75, axis=0), np.percentile(S, 25, axis=0)
    scale = np.where(q75 - q25 > 0, q75 - q25, S.std(axis=0) + 1e-9)
    d = np.sqrt((((S - e) / scale) ** 2).sum(axis=1))
    keep = np.argsort(d)[:max(10, int(eps * len(rows)))]
    ks = sorted(set(r[0] for r in rows), key=lambda s: (s == "aleatoire", int(s) if s.isdigit() else 0))
    print(f"{len(rows)} space-model simulations; ε = {eps}: {len(keep)} kept")
    for txt in (None, "anglais", "aplati"):
        sel = [i for i in range(len(rows)) if txt is None or rows[i][1] == txt]
        kp = [i for i in keep if txt is None or rows[i][1] == txt]
        pri = Counter(rows[i][0] for i in sel); post = Counter(rows[i][0] for i in kp)
        w = {k: (post[k] / max(len(kp), 1)) / (pri[k] / len(sel)) for k in ks}
        z = sum(w.values())
        print(f"  text {txt or 'all'} ({len(kp)} kept): posterior with equal priors: "
              + "; ".join(f"k={k} {w[k] / z:.2f}" for k in ks)
              + f"; P(k ≤ 2) = {sum(w[k] for k in ('1', '2') if k in w) / z:.2f}")
    print("predictive check (two-sided) per k and per text:")
    print("  " + " " * 18 + "  ".join(f"{n[:9]:>9s}" for n in NAMES_STATS))
    for k in ks:
        for txt in ("anglais", "aplati"):
            Sf = np.array([r[2] for r in rows if r[0] == k and r[1] == txt])
            pv = [min(1.0, 2 * min(np.mean(Sf[:, j] <= e[j]), np.mean(Sf[:, j] >= e[j]))) for j in range(len(NAMES_STATS))]
            print(f"  k={k:9s} {txt:7s}" + "  ".join(f"{v:9.2f}" for v in pv) + f"   (n={len(Sf)})")
