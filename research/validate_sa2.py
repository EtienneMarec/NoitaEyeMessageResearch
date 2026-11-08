import sys
import numpy as np
exec(open("validate_sa.py", encoding="utf-8").read().split("iters = int")[0])   # same test key
from sa_progressive import progressive
it = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
F, h = progressive(C, iters=it, F_true=F_true, reads=reads)
print(f"progressive annealing: entropy {h:.3f} (true {entropy(q) if False else 4.698}) ; exact destinations {np.mean(F[reads]==F_true[reads]):.0%}")
