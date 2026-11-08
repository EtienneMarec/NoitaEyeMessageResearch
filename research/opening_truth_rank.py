"""Final rank of the true solution in the blind beam (§47, diagnosis of the verification).

On the same testbeds as opening_blind_calib.py (dictionary from other texts, beam B, no guessed
symbol): if the true branch survives to the last node, we give its rank among the final hypotheses
(ranked by score), comparing the first 15 symbols of each opening. If it often survives with a
rank > 30, checking more hypotheses (K) would raise the success rate.
Usage: python opening_truth_rank.py NB_CASES [beam] [seed]"""
import sys
from pathlib import Path
import numpy as np
from keyed_deck_attack import tables
from known_q_local_filter import ALPHAS
from opening_search import run, wordy_plaintexts, texts_of
from opening_pipeline import lexicon
import testbed_spaces as tbs
from explore import xgak_encrypt

if __name__ == "__main__":
    R = int(sys.argv[1]); B = int(sys.argv[2]) if len(sys.argv) > 2 else 300000
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    names, BS, INV = tables(); rng = np.random.default_rng(seed)
    T_en = tbs.english_with_spaces()
    lex = lexicon(" ".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in
                           ("sources/texts/kalevala_en_crawford.txt", "sources/texts/hermetic_museum_vol1_waite1893.txt",
                            "sources/texts/turba_philosophorum_waite1896.txt")))
    keys = [k for k in BS if k != "id"]
    alpha = ALPHAS["AZ19_"]; q = np.array([alpha.index(ch) for ch in tbs.ALPHA_S], np.int64)
    ranks = []
    for r in range(R):
        pl = wordy_plaintexts(T_en, 100 + seed * 1000 + r)
        b, s = rng.choice(keys, 2, replace=False)
        D0 = rng.permutation(83)
        S = np.array([BS[s] if ch == "_" else BS[b] for ch in tbs.ALPHA_S], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        (SC, TXT, alive, trank, lost), (card, order, paths, syms) = run(msgs, 16, alpha, "k", INV[b], INV[s], lex, B,
                                                                       truth=pl)
        rank = None
        if len(SC) and lost < 0:
            order_h = np.argsort(-SC)
            for k, h in enumerate(order_h):
                dec = texts_of(TXT[h], paths, syms, msgs)
                if all(dec[i] == pl[i][1:16] for i in range(len(pl))):
                    rank = k; break
        ranks.append(rank)
        print(f"case {r} β={b} σ={s}: {'beam died' if len(SC) == 0 else f'{len(SC)} final hypotheses'}; "
              f"true branch {'lost at step %d' % lost if lost >= 0 else 'kept, final rank %s' % rank}", flush=True)
    kept = [x for x in ranks if x is not None]
    print(f"truth kept to the end: {len(kept)}/{R}; ranks: {sorted(kept)}")
