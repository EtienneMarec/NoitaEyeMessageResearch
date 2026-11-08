"""Basin of attraction: starting from the true table with a fraction of the destinations (of the read
positions) replaced at random, does annealing recover the true table?"""
import numpy as np
exec(open("validate_sa.py", encoding="utf-8").read().split("iters = int")[0])
from sa_progressive import anneal_lim, replay_lim, crp_nll
flat, starts = pack(C); q = np.empty(flat.shape[0], np.int64)
replay_lim(flat, starts, F_true, q, 10**6); true_nll = crp_nll(q, 2.0)
print(f"nll of the true table {true_nll:.1f}")
rng = np.random.default_rng(9)
for frac in (0.05, 0.1, 0.25, 0.5):
    res = []
    for t in range(4):
        F = F_true.copy()
        bad = rng.choice(reads, max(1, int(frac * len(reads))), replace=False)
        F[bad] = rng.integers(0, N, len(bad))
        F2, s = anneal_lim(flat, starts, F, 10**6, 100000, 3.0, 0.05, 2.0, t)
        res.append((np.mean(F2[reads] == F_true[reads]), s))
    print(f"{frac:4.0%} corrupted: exact after annealing {[f'{a:.0%}' for a,_ in res]}; nll {[round(s) for _,s in res]}")
