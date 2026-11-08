"""Summary of the ABC filter of conventions (§45): convention_abc_out_*.tsv against the space-model baseline (random q).

Baseline: acceptance rate (distance ≤ 1.73) of the espace_16 / espace_40 / espace_aleatoire /
espace_8 simulations of abc_sims.tsv, English only. A combination is "compatible" if its rate (R = 10 draws)
is not significantly below the baseline (one-sided binomial, P ≥ 0.05)."""
import glob
from math import comb
import numpy as np
from abc_stats import NAMES_STATS
from convention_abc_filter import scale_and_eyes, THR


def binom_le(k, n, p):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


if __name__ == "__main__":
    scale, e = scale_and_eyes()
    ref = {}
    for line in open("abc_sims.tsv", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) != 4 + len(NAMES_STATS) or p[0] != "espace" or p[2] != "anglais" or p[1] not in ("8", "16", "40", "aleatoire"):
            continue
        s = np.array([float(v) for v in p[4:]])
        ref.setdefault(p[1], []).append(float(np.sqrt((((s - e) / scale) ** 2).sum())) <= THR)
    for k, v in ref.items():
        print(f"baseline espace_{k} (random q, English): acceptance rate {np.mean(v):.3f} over {len(v)}")
    p_ref = float(np.mean([x for v in ref.values() for x in v]))
    rows = []
    for f in sorted(glob.glob("convention_abc_out_*.tsv")):
        for line in open(f, encoding="utf-8"):
            a, o, b, s, acc, med, mn = line.rstrip("\n").split("\t")
            rows.append((a, o, b, s, float(acc), float(med), float(mn)))
    R = 10
    print(f"{len(rows)} combinations; pooled baseline {p_ref:.3f}")
    acc = np.array([r[4] for r in rows])
    print(f"acceptance rate of the combinations: mean {acc.mean():.3f}, median {np.median(acc):.3f}, "
          f"share at 0: {np.mean(acc == 0):.2f}")
    ok = [r for r in rows if binom_le(int(round(r[4] * R)), R, p_ref) >= 0.05]
    print(f"compatible (P ≥ 0.05 against the baseline): {len(ok)}; with at least 3/10 accepted: "
          f"{sum(r[4] >= 0.3 for r in rows)}")
    rows.sort(key=lambda r: (-r[4], r[5]))
    for r in rows[:15]:
        print(f"  {r[0]}/{r[1]:5s} β={r[2]:14s} σ={r[3]:14s} accepted {r[4]:.1f}  median distance {r[5]:.2f}")
