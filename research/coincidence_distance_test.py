"""Where do coincidences fall after a divergence? Near (+1..+9) versus far (+10..+20) (§32).

In the space model, two diverging texts keep the same deck only until the first shifted space (a few letters):
coincidences should concentrate right after the divergence. In Lymm's model, the deck difference grows slowly:
coincidences remain possible 10 to 20 steps further.
Counting by lineages (lineage_coincidence), separating the windows +1..+9 and +10..+20.
Eyes: modes "sans E1/W1 et E4/E5" (without E1/W1 and E4/E5) and "groupes" (between groups). Models: the
divergence_models testbed (unrelated texts, 10 corpora), 50 keys each."""
import numpy as np
from stats import load_eyes
import lineage_coincidence as lc
from divergence_models import corpus
import testbed_spaces as tbs
import space_model_test as sm
from formulaic_test import lymm_key
from family_zoo import make_key as zoo_key
from testbed import english_letters, ALPHA
from explore import xgak_encrypt


def split_count(M, names, mode):
    out = {}
    for lo, hi in ((1, 9), (10, 20)):
        lc.W = hi
        tr_hi, su_hi = lc.count(M, names, mode)
        lc.W = lo - 1
        if lo > 1:
            tr_lo, su_lo = lc.count(M, names, mode)
            out[(lo, hi)] = (su_hi["proche"] - su_lo["proche"], tr_hi["proche"] - tr_lo["proche"])
        else:
            out[(lo, hi)] = (su_hi["proche"], tr_hi["proche"])
    lc.W = 20
    return out


if __name__ == "__main__":
    names, M = load_eyes()
    for mode in ("sans E1/W1 et E4/E5", "groupes"):
        o = split_count(M, names, mode)
        print(f"eyes ({mode:20s}): +1..+9 {o[(1, 9)][0]}/{o[(1, 9)][1]} ({o[(1, 9)][0] / o[(1, 9)][1]:.3f}); "
              f"+10..+20 {o[(10, 20)][0]}/{o[(10, 20)][1]} ({o[(10, 20)][0] / o[(10, 20)][1]:.3f})", flush=True)
    rng = np.random.default_rng(37)
    TS, TL = tbs.english_with_spaces(), english_letters()
    for lab in ("space model", "Lymm k=1", "reinsertion"):
        acc = {(1, 9): [0, 0], (10, 20): [0, 0]}
        for it in range(50):
            if lab == "space model":
                pl = corpus(TS, it % 10); q, S = sm.make_key("_", "aleatoire", True, rng)
                C = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
            elif lab == "Lymm k=1":
                pl = corpus(TS, it % 10); q, S = lymm_key(rng)
                C = [[0] + xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in pl]
            else:
                pl = corpus(TL, it % 10); r, S = zoo_key("reinsertion", "aleatoire", 0, rng, len(ALPHA))
                C = [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]], np.int64), r, S).tolist() for m in pl]
            o = split_count(C, names, "toutes")
            for k in acc:
                acc[k][0] += o[k][0]; acc[k][1] += o[k][1]
        print(f"{lab:12s}: +1..+9 {acc[(1, 9)][0] / acc[(1, 9)][1]:.3f}; +10..+20 {acc[(10, 20)][0] / acc[(10, 20)][1]:.3f}", flush=True)
