"""Validation of the CP-SAT attack on the test key (reinsertion with no shuffle, no homophones)."""
import sys
import numpy as np
from testkey import make
from cpsat_reinsert import solve
from sa_reinsert import pack, replay

plains, C, F_true, reads = make()
L = int(sys.argv[1]) if len(sys.argv) > 1 else 20
sub = [C[0], C[3], C[6]] if "--3" in sys.argv else C
# truth: positions read in the prefix, distinct count
flat, starts = pack(sub); q = np.empty(flat.shape[0], np.int64); replay(flat, starts, F_true, q)
truth_q = [q[starts[m] + t] for m in range(len(sub)) for t in range(1, min(L, len(sub[m])))]
used = sorted(set(truth_q))
print(f"L={L}, {len(sub)} messages: the true table reads {len(used)} distinct positions in this prefix")
res = solve(sub, L, seconds=int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 300, dest_not_read="--dnr" in sys.argv)
print(res["status"], f"{res['time']:.0f} s", "objective", res.get("obj"), "bound", res.get("bound"))
if "F" in res:
    rel = [p for p in used]
    # destinations that matter: those of positions read BEFORE the last read (otherwise no effect)
    ok = sum(res["F"][p] == F_true[p] for p in rel)
    qs = [v for _, _, v in res["q"]]
    print(f"read positions identical to the truth: {sum(a == b for a, b in zip(qs, truth_q))}/{len(qs)} ; "
          f"exact destinations on read positions: {ok}/{len(rel)}")
