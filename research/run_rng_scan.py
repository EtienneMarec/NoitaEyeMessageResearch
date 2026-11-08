"""Scan of the eyes: direct seeds 0..S (M1/M2 × 3 shuffles) + SetRandomSeed(x, y) for special world
seeds, x, y in [-100, 100] (3 shuffles). Then re-check of the best on the 9 messages."""
import sys
import time
import numpy as np
import rng_decks as R
import keyword_decks as K
from stats import load_eyes

names, M = load_eyes()
flat, starts = R.pack([M[0], M[3], M[6]])
# Resume: python run_rng_scan.py <S> <starting seed>. Each finished block is saved to
# rng_scan_tops.tsv (5 best candidates) and rng_scan_progress.tsv (block max): it can be stopped and resumed.
S = int(sys.argv[1]) if len(sys.argv) > 1 else 5_000_000
START = int(sys.argv[2]) if len(sys.argv) > 2 else 0
CH = 250_000
tops = []
allmax = []
t0 = time.time()
for s0 in range(START, S, CH):
    out = R.scan_direct(s0, min(S, s0 + CH), flat, starts)
    mx = out.max(axis=1); allmax.append(mx)
    with open("rng_scan_tops.tsv", "a", encoding="utf-8") as f:
        for idx in np.argsort(-mx)[:5]:
            v = int(np.argmax(out[idx]))
            f.write(f"{out[idx, v]:.4f}\tdirect\t{s0 + int(idx)}\t{v}\n")
    with open("rng_scan_progress.tsv", "a", encoding="utf-8") as f:
        f.write(f"{s0}\t{min(S, s0 + CH)}\t{mx.max():.4f}\t{np.median(mx):.4f}\n")
    print(f"direct seeds {min(S, s0+CH):>9,} / {S:,}  ({time.time()-t0:.0f} s), block max {mx.max():.3f}", flush=True)
with open("rng_scan_tops.tsv", encoding="utf-8") as f:
    for line in f:
        ic, kind, sd, v = line.rstrip("\n").split("\t")
        tops.append((float(ic), kind, int(sd), int(v)))
g = np.arange(-100, 101)
xs, ys = [a.ravel().astype(np.int64) for a in np.meshgrid(g, g)]
for ws in R.SPECIAL_WS:
    out = R.scan_setseed(ws, xs, ys, flat, starts)
    mx = out.max(axis=1); allmax.append(mx)
    for idx in np.argsort(-mx)[:5]:
        tops.append((float(mx[idx]), f"SetRandomSeed ws={ws}", (int(xs[idx]), int(ys[idx])), int(np.argmax(out[idx]))))
    print(f"world seed {ws}: max {mx.max():.3f} ({time.time()-t0:.0f} s)", flush=True)
allmax = np.concatenate(allmax)
print(f"\n{allmax.size:,} seeds tested; max IoC per seed: median {np.median(allmax):.3f}, "
      f"99.99th percentile {np.quantile(allmax, 0.9999):.3f}, record {allmax.max():.3f}")
tops.sort(key=lambda t: -t[0])
print("Best candidates, re-checked on the 9 messages (full keyword_decks battery):")
arrs = [np.array(m, np.int64) for m in M]
for ic, kind, s, v in tops[:12]:
    if kind == "direct":
        seed = s if v < 3 else R.nnext(s)
    else:
        ws = int(kind.split("=")[1]); seed = R.set_random_seed(float(s[0]), float(s[1]), ws)
    P = R.shuffle(seed, v % 3)
    full = K.battery(P, arrs)
    print(f"  {ic:.3f} (3 messages)  -> 9 messages: IoC {full[0]:.3f}, {full[1]} positions   [{kind} {s}, variant {v}]")
print("For reference: true mechanism ≈ IoC 3 to 5.5; the full battery on random permutations ≈ 1.10 (record 1.17 over 2000).")
