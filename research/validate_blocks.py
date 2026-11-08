import sys
import numpy as np
from testkey import make, true_blocks, N
from beam_blocks import run
plains, C, F_true, reads = make()
blocks = true_blocks(plains)
pairs = [((a, i + k), (b, j + k)) for a, i, b, j, L in blocks for k in range(L)]
print(f"{len(blocks)} real blocks -> {len(pairs)} q equality constraints")
for B in [int(x) for x in sys.argv[1:]] or [500]:
    for use in (False, True):
        F, s = run(C, pairs if use else [], B=B)
        Fx = np.where(F < 0, np.arange(N), F)
        print(f"   B={B} blocks={'yes' if use else 'no'} : exact destinations {np.mean(Fx[reads]==F_true[reads]):.0%}")
