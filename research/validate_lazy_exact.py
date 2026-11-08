import sys
import numpy as np
from testkey import make, true_blocks, N
from lazy_exact import search
plains, C, F_true, reads = make(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
blocks = true_blocks(plains)
pairs = [((a, i + k), (b, j + k)) for a, i, b, j, L in blocks for k in range(L)]
for B in [int(x) for x in sys.argv[1].split(",")]:
    for use in (True, False):
        F, cost, Q, dt = search(C, pairs if use else [], B=B)
        ok = np.sum(F[reads] == F_true[reads])
        print(f"B={B:5d} blocks={'yes' if use else 'no '} : cost {cost:8.1f} ; correct destinations {ok}/{len(reads)} "
              f"(fixed {np.sum(F[reads]>=0)}) ; {dt:.0f} s", flush=True)
