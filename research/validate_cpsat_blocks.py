"""CP-SAT + block constraints (true shared blocks of the testbed) on the 9 messages, prefix L."""
import sys
import numpy as np
from testkey import make, true_blocks
from cpsat_reinsert import solve
from sa_reinsert import pack, replay

plains, C, F_true, reads = make()
L = int(sys.argv[1]); secs = int(sys.argv[2])
pairs = [((a, i + k), (b, j + k)) for a, i, b, j, n in true_blocks(plains) for k in range(n) if i + k < L and j + k < L]
flat, starts = pack(C); q = np.empty(flat.shape[0], np.int64); replay(flat, starts, F_true, q)
truth_q = [q[starts[m] + t] for m in range(9) for t in range(1, min(L, len(C[m])))]
used = sorted(set(truth_q))
print(f"L={L}, 9 messages, {len(pairs)} block equalities; the true table reads {len(used)} positions", flush=True)
res = solve(C, L, seconds=secs, dest_not_read=True, pairs=pairs)
print(res["status"], f"{res['time']:.0f} s", "objective", res.get("obj"), "bound", res.get("bound"), flush=True)
if "F" in res:
    qs = [v for _, _, v in res["q"]]
    print(f"read positions identical to the truth: {sum(a == b for a, b in zip(qs, truth_q))}/{len(qs)} ; "
          f"exact destinations: {sum(res['F'][p] == F_true[p] for p in used)}/{len(used)}", flush=True)
