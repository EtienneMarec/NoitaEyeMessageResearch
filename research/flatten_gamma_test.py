"""Flatness versus coincidences: is there a flattening of the plaintext that satisfies both? (§31)

i.i.d. plaintext over 26 letters, with frequencies ∝ p_english^γ (γ = 1: English, γ = 0: uniform), plus
real English for reference. Lymm's model (flat_plaintext_test.make_key: 1 swap, random β,
no doubles). For each γ: Σp², P(chi² <= eyes) on the testbed with the eyes' architecture, rate of
coincidences after a divergence, and binomial likelihood of the eyes (12 of 301, mode "sans E1/W1 et E4/E5")
under that rate (two-sided P)."""
import sys
import random
from math import comb
from collections import Counter
import numpy as np
from testbed import english_letters
from flat_plaintext_test import build, div_corpus, make_key, enc
from swap_model_test import chi2
from lineage_coincidence import count
from stats import load_eyes

LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def binom_two_sided(k, n, p):
    pk = [comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    return sum(x for x in pk if x <= pk[k] * (1 + 1e-9))


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes(); E = chi2(M)
    T0 = english_letters()[:400000]
    fr = Counter(T0); p = np.array([fr[c] for c in LET], float); p /= p.sum()
    rnd = random.Random(32); rng = np.random.default_rng(32)
    print("text           Σp²    P(flat)  med. chi²  div. coinc.  P(eyes 12/301)")
    for g in ("real", 1.0, 0.75, 0.5, 0.25, 0.0):
        if g == "real":
            T = T0; s2 = float((p ** 2).sum())
        else:
            w = p ** g; w /= w.sum(); s2 = float((w ** 2).sum())
            T = "".join(rnd.choices(LET, weights=w, k=len(T0)))
        base, P = build(T, LET)
        dcs = [div_corpus(T, sd) for sd in range(10)]; per = []
        X = []; cs = ct = 0
        for _ in range(R):
            q, S = make_key(26, rng)
            X.append(chi2(enc(base, LET, q, S)))
            if _ < 50:
                k = _ % 10; tr, su = count(enc(dcs[k], LET, q, S), names, "toutes"); cs += su["proche"]; ct += tr["proche"]; per.append((k, su["proche"], tr["proche"]))
        r = cs / ct
        byc = [sum(a for k2, a, b in per if k2 == k) / max(1, sum(b for k2, a, b in per if k2 == k)) for k in range(10)]
        print(f"{('real English' if g == 'real' else f'γ = {g}'):13s}  {s2:.3f}   {np.mean(np.array(X) <= E):.2f}     {np.median(X):5.0f}      {r:.3f}        {binom_two_sided(12, 301, r):.3f}   per corpus {min(byc):.3f}–{max(byc):.3f}", flush=True)
