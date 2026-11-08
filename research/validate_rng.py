"""Validation: (1) the generator reproduces pick_world_seed/Next as in misc.cpp on a few values;
(2) a deck shuffled by the generator (known seed) is recovered by the sweep."""
import time
import numpy as np
import rng_decks as R
from testbed import build_plaintexts, make_key, encrypt_all
from deckcipher import N
# (1) generator properties: Park-Miller -> period; Next(1) = 16807; Next(16807) = 282475249
s = 1
seq = []
for _ in range(3):
    s = R.nnext(s); seq.append(s)
print("Next from 1:", seq, "(Park-Miller expected: 16807, 282475249, 1622650073)")
# (2) test encryption with a starting deck shuffled by seed 123456 (M2, sh1), "dessus" (top) rule
seed = R.nnext(123456)
P = R.shuffle(seed, 0)
plains = build_plaintexts()
C = encrypt_all(plains, make_key(2), np.arange(N), 1, 0, D0=P)
flat, starts = R.pack([C[0], C[3], C[6]])
t = time.time()
out = R.scan_direct(123000, 124000, flat, starts)
print(f"sweep of 1000 seeds in {time.time()-t:.1f} s (compilation included)")
best = np.unravel_index(np.argmax(out), out.shape)
print("best seed:", 123000 + best[0], "variant", best[1], "IoC", out[best], "; median", np.median(out))
t = time.time(); R.scan_direct(200000, 210000, flat, starts); print(f"10,000 seeds: {time.time()-t:.1f} s")
