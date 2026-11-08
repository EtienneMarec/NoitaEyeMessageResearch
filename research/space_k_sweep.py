"""Trade-off between flatness and far coincidences as a function of the strength of the space shuffle (§32).

Model: letters = exactly β, space = β∘(k random swaps), no doubles, first symbol inside the
deck; k = 8, 16, 24, 40, 83 and random σ. Text: English with spaces.
Measures: P(flat) (200 keys, testbed_spaces), rate of coincidences +10..+20 after a divergence (50 keys,
10 corpora), and two-sided binomial likelihood of the eyes under this rate: between groups 6/119, without E1/W1
and E4/E5 7/196. Product P(flat) × P(group coinc.) as a rough compatibility indicator."""
import sys
import numpy as np
import testbed_spaces as tbs
import space_model_test as sm
from explore import xgak_encrypt
from swap_model_test import chi2
from divergence_models import corpus
from coincidence_distance_test import split_count
from flatten_gamma_test import binom_two_sided
from stats import load_eyes


def enc(msgs, q, S):
    return [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in msgs]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    names, M = load_eyes(); E = chi2(M)
    base = tbs.build_plaintexts()
    dcs = [corpus(tbs.english_with_spaces(), s) for s in range(10)]
    rng = np.random.default_rng(39)
    print("σ_space       P(flat)  coinc. +10..20  P(eyes 6/119)  P(eyes 7/196)  product")
    for kind in ("8", "16", "24", "40", "83", "aleatoire"):
        X = []; s = t = 0
        for it in range(R):
            q, S = sm.make_key("_", kind, True, rng)
            X.append(chi2(enc(base, q, S)))
            if it < 50:
                o = split_count(enc(dcs[it % 10], q, S), names, "toutes")
                s += o[(10, 20)][0]; t += o[(10, 20)][1]
        pf = float(np.mean(np.array(X) <= E)); r = s / t
        pa, pb = binom_two_sided(6, 119, r), binom_two_sided(7, 196, r)
        print(f"{('k = ' + kind) if kind != 'aleatoire' else 'random':12s}  {pf:.2f}     {r:.3f}           {pa:.3f}          {pb:.3f}        {pf * pa:.3f}", flush=True)
