"""Coincidences right after a divergence: eyes versus models (§26).

Dedicated testbed: 9 messages = shared prefix (structure of the eyes: 1-2 shared by all, 1-5 by six messages, 1-9 by
four, 1-20 by three, 1-24 by three others) then UNRELATED English texts (random positions).
Statistic: lineage_coincidence.count, mode "toutes" (all: no known pair to exclude here),
near window 1..20 after the divergence. Eyes (mode "groupes"): 7/169 = 0.041; without E1/W1 and E4/E5: 0.040.
Models: "espace" (space model, text with spaces), Lymm (1 swap + homophones from the previous letter, no doubles),
Lymm k = 4 without homophones, reinsertion + random β, segment reversal ("retournement") + random β. 40 keys, 3 testbeds."""
import random
import numpy as np
from lineage_coincidence import count
from testbed import english_letters, ALPHA
from testbed_spaces import english_with_spaces, ALPHA_S
from explore import xgak_encrypt
import space_model_test as sm
from swap_context_test import make_key as swap_key
from context_homophone_test import enc_all
from family_zoo import make_key as zoo_key

PREF = [24, 24, 24, 5, 9, 5, 20, 20, 20]  # length of the shared prefix (positions 1..k), groups as in the eyes
LENS = [99, 103, 118, 102, 137, 124, 119, 120, 114]


def corpus(T, seed, digits="123456789"):
    rng = random.Random(seed)
    def take(n):
        i = rng.randrange(1000, len(T) - 2000); return T[i:i + n]
    pA, pBC, pE3C, pC, p12 = take(24), take(5), take(9), take(20), take(2)
    pBC = p12 + pBC[2:]; pA = p12 + pA[2:]; pE3C = pBC + pE3C[5:]; pC = pE3C + pC[9:]
    pre = [pA, pA, pA, pBC, pE3C, pBC, pC, pC, pC]
    return [digits[k] + pre[k] + take(LENS[k] - 1 - len(pre[k])) for k in range(9)]


if __name__ == "__main__":
    names = ["E1", "W1", "E2", "W2", "E3", "W3", "E4", "W4", "E5"]
    TL, TS = english_letters(), english_with_spaces()
    rng = np.random.default_rng(4)
    print("model                        near (successes/trials)  rate   | eyes 0.040–0.041")
    for lab in ("espace", "Lymm k=1 + homoph.", "Lymm k=4", "reinsertion + aleatoire", "retournement + aleatoire"):
        s = t = 0
        for seed in range(3):
            pl = corpus(TS if lab == "espace" else TL, seed)
            for _ in range(40 // 3 + 1):
                if lab == "espace":
                    q, S = sm.make_key("_", "aleatoire", True, rng)
                    C = [xgak_encrypt(np.array([ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
                elif lab.startswith("Lymm k=1"):
                    sl, r, S = swap_key(1, "aleatoire", 60, rng, nodouble=True); C = enc_all(pl, sl, r, S)
                elif lab == "Lymm k=4":
                    sl, r, S = swap_key(4, "aleatoire", len(ALPHA), rng); C = enc_all(pl, sl, r, S)
                else:
                    tk, bk = lab.split(" + ")
                    r, S = zoo_key(tk, bk, 0, rng, len(ALPHA))
                    C = [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]], np.int64), r, S).tolist() for m in pl]
                tr, su = count(C, names, "toutes")
                s += su["proche"]; t += tr["proche"]
        print(f"{lab:28s} {s:5d}/{t:5d}               {s / t:.3f}", flush=True)
