"""Calibration of the BLIND brute force on the openings (§47): share of "whole-word" testbeds decrypted with
no guessed symbol, with the true pair and a dictionary taken from OTHER texts (English Kalevala, Hermetic
Museum, Turba), out-of-dictionary words allowed. Several texts (seeds) and natural pairs drawn at random.
Option: KF = number of guessed nodes (truth imposed on the first KF nodes), 0 by default (blind).
Option: dictionary "autre" (other, default) or "meme" (same: taken from the very book of the test texts: ideal vocabulary).
Usage: python opening_blind_calib.py NB_CASES [beam] [seed] [KF] [autre|meme|gut]"""
import sys
import time
from pathlib import Path
import numpy as np
from keyed_deck_attack import tables, flatten
from known_q_local_filter import ALPHAS
from opening_search import wordy_plaintexts
from opening_pipeline import lexicon, pipeline
from opening_crib_solver import convention, decode_text
import testbed_spaces as tbs
from explore import xgak_encrypt

if __name__ == "__main__":
    R = int(sys.argv[1]); B = int(sys.argv[2]) if len(sys.argv) > 2 else 300000
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    KF = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    lexsrc = sys.argv[5] if len(sys.argv) > 5 else "autre"
    names, BS, INV = tables(); rng = np.random.default_rng(seed)
    T_en = tbs.english_with_spaces()
    if lexsrc == "gut":   # v2 model (§49): Gutenberg without Pride and Prejudice + 3 other books
        from opening_search2 import build_lm, gutenberg_books
        from opening_pipeline import other_books
        lex = build_lm(list(gutenberg_books()) + [other_books()])
        print(f"v2 model: {lex['V']} words, {lex['ntok']} occurrences", flush=True)
    elif lexsrc == "meme":
        lex = lexicon(T_en.replace("_", " "))
    else:
        lex = lexicon(" ".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in
                               ("sources/texts/kalevala_en_crawford.txt", "sources/texts/hermetic_museum_vol1_waite1893.txt",
                                "sources/texts/turba_philosophorum_waite1896.txt")))
    keys = [k for k in BS if k not in ("id",)]
    alpha = ALPHAS["AZ19_"]; q = np.array([alpha.index(ch) for ch in tbs.ALPHA_S], np.int64)
    ok = 0
    for r in range(R):
        pl = wordy_plaintexts(T_en, 100 + seed * 1000 + r)
        b, s = rng.choice(keys, 2, replace=False)
        D0 = rng.permutation(83)
        S = np.array([BS[s] if ch == "_" else BS[b] for ch in tbs.ALPHA_S], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        t0 = time.time()
        best, lost = pipeline(msgs, "AZ19_", "k", INV[b], INV[s], lex, B, 30, KF=KF, truth=pl, rng=rng, en_text=T_en)
        acc = 0.0
        if best is not None:
            C, st, ln = flatten(msgs); a_, q_ = convention("AZ19_", "k")
            acc = float(np.mean([x == y for x, y in zip("".join(decode_text(best[2][2], q_, a_, st, ln)), "".join(pl))]))
        ok += acc > 0.99
        print(f"case {r} β={b} σ={s}: {'score %.2f' % best[0] if best else 'beam died'}, text correct at {acc:.2f}, "
              f"true branch lost at step {lost} ({time.time() - t0:.0f} s)", flush=True)
    print(f"100% decrypted: {ok}/{R}")
