import sys
import numpy as np
exec(open("validate_sa.py", encoding="utf-8").read().split("iters = int")[0])
from beam_reinsert import run
from sa_progressive import replay_lim, crp_nll
flat, starts = pack(C); q = np.empty(flat.shape[0], np.int64)
replay_lim(flat, starts, F_true, q, 10**6); print(f"nll of the true table: {crp_nll(q, 2.0):.1f}")
for B in [int(x) for x in sys.argv[1:]] or [300]:
    F, L = run(C, B)
    Fx = np.where(F < 0, np.arange(N), F)
    print(f"  B={B}: exact destinations on read positions {np.mean(Fx[reads]==F_true[reads]):.0%}")
