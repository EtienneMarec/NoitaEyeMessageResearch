"""Filter of the NATURAL pairs (β, σ) of the space model by the statistics of the eyes (§36).

The keyed starting deck is only a relabelling of the cards: it changes no statistic (gaps,
coincidences, fixed points, isomorphs). So each pair (β, σ) among the 116 natural shuffles can be judged
without knowing the key. For each pair: R draws of the read positions (no-doubles rule not
imposed; doubles are measured), testbed with spaces (stutter: 12 substituted letters, spaces
kept), first symbol inside the deck. Measures: P(flat), P(fixed points <= 1%), P(0 doubles).
Output: pairs ranked by P(flat) × P(fixed points) × P(0 doubles), in natural_pair_filter_out.tsv."""
import sys
import random
import numpy as np
from numba import njit
import testbed_spaces as tbs
from deckcipher import base_shuffles
from explore import xgak_encrypt
from swap_model_test import chi2
from fixed_points_test import blocks_fixed
from stats import load_eyes

N = 83
LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    names, M = load_eyes(); E = chi2(M)
    BS = base_shuffles(); keys = list(BS)
    rnd = random.Random(40); rng = np.random.default_rng(40)
    base = tbs.build_plaintexts()
    pl = list(base); e5 = list(pl[8])
    idx = [k for k in range(21, 42) if e5[k] != "_"]
    for k in rnd.sample(idx, min(12, len(idx))):
        e5[k] = rnd.choice([x for x in LET if x != e5[k]])
    pl[8] = "".join(e5)
    seqs = [np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64) for m in pl]
    sp_idx = tbs.ALPHA_S.index("_")
    rows = []
    for bi, b in enumerate(keys):
        if b == 'id':
            continue
        for s in keys:
            if s == b or (b.startswith('rot') and s.startswith('rot')):
                continue  # rotations with each other: commutative model, refuted (§25)
            fl = fx = db = 0
            for _ in range(R):
                q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
                S = np.array([BS[s] if k == sp_idx else BS[b] for k in range(len(tbs.ALPHA_S))], np.int64)
                C = [xgak_encrypt(x, q, S).tolist() for x in seqs]
                fl += chi2(C) <= E
                tt, f = blocks_fixed(C); fx += f / tt <= 0.01
                db += sum(a == c for m in C for a, c in zip(m[1:], m[2:])) == 0
            rows.append((b, s, fl / R, fx / R, db / R))
        if bi % 10 == 9:
            print(f"{bi + 1}/{len(keys)} β done", flush=True)
    rows.sort(key=lambda r: -(r[2] * r[3] * max(r[4], 0.05)))
    with open("natural_pair_filter_out.tsv", "w", encoding="utf-8") as f:
        f.write("beta\tsigma\tP_plat\tP_ptsfix\tP_0dbl\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]:.2f}\t{r[3]:.2f}\t{r[4]:.2f}\n")
    good = [r for r in rows if r[2] >= 0.2 and r[3] >= 0.2]
    print(f"pairs with P(flat) >= 0.2 and P(fixed points) >= 0.2: {len(good)} / {len(rows)}")
    for r in rows[:25]:
        print(f"  β={r[0]:14s} σ={r[1]:14s} flat {r[2]:.2f}  fixpts {r[3]:.2f}  0dbl {r[4]:.2f}")
