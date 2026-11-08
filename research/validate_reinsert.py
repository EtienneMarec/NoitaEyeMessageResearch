"""Validation of the "reinsertion" sweep on test messages encrypted by
reinsertion at destination f(q) = q+17, flattened homophones, 1st symbol outside the deck."""
import numpy as np
from collections import Counter
from testbed import build_plaintexts, english_letters, ALPHA
from reinsert_scan import scan, report, N
from explore import xgak_encrypt, encode

rng = np.random.default_rng(3)
F = (np.arange(N) + 17) % N
freq = Counter(english_letters()[:200000])
w = np.array([freq.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (41 - len(ALPHA))
counts = [1 + int(x) for x in w]
while sum(counts) < 41: counts[int(np.argmax(w - np.array(counts) + 1))] += 1
reads = rng.choice(np.arange(N), sum(counts), replace=False)
slots, k = {}, 0
for ch, c in zip(ALPHA, counts): slots[ch] = list(range(k, k + c)); k += c
S = np.empty((len(reads), N), np.int64)
for s, q in enumerate(reads):
    idx = list(range(N)); card = idx.pop(int(q)); idx.insert(int(F[q]), card); S[s] = idx
plains = build_plaintexts()
C = [[int(reads[slots[m[0]][0]])] + xgak_encrypt(encode(m[1:], slots), reads, S).tolist() for m in plains]
print("doubles:", sum(a == b for m in C for a, b in zip(m, m[1:])))
report(scan(C, True), top=5)
