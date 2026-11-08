"""Summary statistics shared by the eyes and the simulations (ABC inference, §40).

summary(C, d0) for 9 messages (lists of trigrams, symbol 0 included), d0 = start of the E1/W1 obstacle
(eyes: 25). Window positions follow the eyes' architecture (the testbed reproduces it).
Statistics (names kept as stored in abc_sims.tsv): gap-spike chi² (d = 2..40) "khi2", number of doubles
"doublons", repeats at d = 2 and d = 4, IoC, identical share and number of runs in the stutter (E4/E5, 21..46)
"beg_part"/"beg_series", share of fixed points after an insertion "ptsfix", identical share in the obstacle
window d0+4..d0+24 "obst_part", exact 4/4/4/13 pattern (0/1) "obst_motif", rate of coincidences after a
divergence (lineages, without E1/W1 and E4/E5, window +1..+20) "coinc_div"."""
import numpy as np
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from lineage_coincidence import count
from gap_profile_order import gaps
from stats import ioc

NAMES = ["E1", "W1", "E2", "W2", "E3", "W3", "E4", "W4", "E5"]
NAMES_STATS = ["khi2", "doublons", "rep_d2", "rep_d4", "ioc", "beg_part", "beg_series", "ptsfix", "obst_part",
               "obst_motif", "coinc_div"]


def obstacle(A, B, d0):
    eq = [A[i] == B[i] for i in range(d0 + 4, d0 + 25)]
    d = [A[i] != B[i] for i in range(d0, d0 + 25)]
    motif = all(d[0:4]) and not any(d[4:8]) and all(d[8:12]) and not any(d[12:25])
    return sum(eq) / len(eq), float(motif)


def summary(C, d0):
    g = gaps(C, 4)
    f, r = texture(C[6], C[8])
    tt, fx = blocks_fixed(C) if all(len(m) > 97 for m in C[6:9]) else (1, 0)
    op, om = obstacle(C[0], C[1], d0)
    tr, su = count(C, NAMES, "sans E1/W1 et E4/E5")   # mode key of lineage_coincidence.count
    co = su["proche"] / max(tr["proche"], 1)
    dbl = sum(a == b for m in C for a, b in zip(m[1:], m[2:]))
    return [chi2(C), dbl, g[1], g[3], ioc([m[1:] for m in C]), f, r, fx / tt, op, om, co]


if __name__ == "__main__":
    from stats import load_eyes
    names, M = load_eyes()
    s = summary(M, 25)
    for k, v in zip(NAMES_STATS, s):
        print(f"{k:12s} {v:.4g}")
