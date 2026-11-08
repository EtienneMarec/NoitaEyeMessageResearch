import sys
import numpy as np
from testkey import make, true_blocks, N
from lazy_beam import search, prepare, replay
plains, C, F_true, reads = make(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
blocks = true_blocks(plains)
pairs = [((a, i + k), (b, j + k)) for a, i, b, j, L in blocks for k in range(L)]
flat, starts, nev, cs, ca, cb = prepare(C, pairs)
cum = np.full(nev, np.inf)
r, s = replay(flat, starts, F_true, 2.0, 15.0, cs, ca, cb, cum)
print(f"true table: cost {cum[r-1]:.1f} over {r}/{nev} events")
B = int(sys.argv[1]) if len(sys.argv) > 1 else 100
F, cost = search(C, pairs, B=B, F_true=F_true, reads=reads)
print(f"B={B} : cost {cost:.1f} ; correct destinations {np.sum(F[reads]==F_true[reads])}/{len(reads)} "
      f"(of which {np.sum(F[reads]>=0)} fixed)")
