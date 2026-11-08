"""Figures of §24.2: model-free bound for the obstacle, and clustering of the differences.

1. If 33-36 are NOT text differences, we need, with a fixed π of support s and uniform reads,
   17 clean reads (29-32, 37-49) and 4 reads of the support (33-36): P(s) = (1-s/83)^17 (s/83)^4.
2. After 8 differing letters (two words), probability of 4 then 13 clean reads if the support of π
   is s1 after the first word and s2 after the second: (1-s1/83)^4 (1-s2/83)^13, for s1 = 4h, s2 = 8h
   (h = mean support added per differing letter, without cancellation).
3. Clustering: window 26..49 of E1/W1 (after the difference proven in [22,25]); number of =/≠ runs
   compared with random permutations of the same positions (runs test, 100,000 draws)."""
import numpy as np
from stats import load_eyes

Q = 83
s = np.arange(1, Q)
p1 = (1 - s / Q) ** 17 * (s / Q) ** 4
print(f"1. max_s P(s) = {p1.max():.2e} (reached for s = {s[p1.argmax()]})")
for h in (2, 3, 4):
    print(f"2. h = {h}: P = {(1 - 4 * h / Q) ** 4 * (1 - 8 * h / Q) ** 13:.4f}")
names, M = load_eyes()
N = dict(zip(names, M))
E1, W1 = N["E1"], N["W1"]
d = np.array([E1[i] != W1[i] for i in range(26, 50)])
runs = 1 + int((d[1:] != d[:-1]).sum())
rng = np.random.default_rng(0)
sim = np.array([1 + int((x[1:] != x[:-1]).sum()) for x in (rng.permutation(d) for _ in range(100000))])
print(f"3. E1/W1 26..49: {d.sum()} different out of {len(d)}, {runs} runs; "
      f"permutations: mean {sim.mean():.1f}, P(runs <= {runs}) = {(sim <= runs).mean():.4f}")
