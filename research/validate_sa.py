"""Validation of simulated annealing on test messages: ARBITRARY reinsertion table (reads on 41
positions, destinations on the others), flattened homophones, sorted deck, 1st symbol outside the deck.
The entropy found is compared with that of the true table, along with the share of destinations recovered."""
import sys
import numpy as np
from collections import Counter
from testbed import build_plaintexts, english_letters, ALPHA
from explore import xgak_encrypt, encode
from sa_reinsert import run, replay, entropy, pack, N

rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
freq = Counter(english_letters()[:200000])
w = np.array([freq.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (41 - len(ALPHA))
counts = [1 + int(x) for x in w]
while sum(counts) < 41: counts[int(np.argmax(w - np.array(counts) + 1))] += 1
perm = rng.permutation(N)
reads, dest_pool = perm[:41], perm[41:]
F_true = np.arange(N)
F_true[reads] = rng.choice(dest_pool, 41, replace=True)
slots, k = {}, 0
for ch, c in zip(ALPHA, counts): slots[ch] = list(range(k, k + c)); k += c
S = np.empty((41, N), np.int64)
for s, q in enumerate(reads):
    idx = list(range(N)); card = idx.pop(int(q)); idx.insert(int(F_true[q]), card); S[s] = idx
plains = build_plaintexts()
C = [[99] + xgak_encrypt(encode(m[1:], slots), reads, S).tolist() for m in plains]

flat, starts = pack(C)
q = np.empty(flat.shape[0], np.int64)
replay(flat, starts, F_true, q)
print(f"true table: entropy {entropy(q):.3f} bits, {len(set(q[q>=0].tolist()))} read positions")
F_rand = rng.integers(0, N, N)
replay(flat, starts, F_rand, q)
print(f"random table: entropy {entropy(q):.3f} bits")
iters = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
h, F = run(C, iters)
ok = np.mean(F[reads] == F_true[reads])
replay(flat, starts, F, q)
print(f"annealing: entropy {h:.3f} ; exact destinations on read positions: {ok:.0%} ; "
      f"distinct read positions {len(set(q[q>=0].tolist()))}")
