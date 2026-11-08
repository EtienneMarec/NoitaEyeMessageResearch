"""Full chain "guessed partial openings → brute force → verification" (§47).

1. opening_search.run: beam constrained by the dictionary, with the guessed symbols imposed;
2. the K best opening hypotheses (15 symbols of E1, W2, E4) go through EM on the whole corpus
   (opening_crib_solver.solve); success gives a score of about -2.9 per symbol (failure ≈ -6).
On the eyes, under the convention, the first 20 nodes of the prefix tree are positions 1 to 8 of the
openings of E1 (= W1, E2), W2, W3 and E3/E4 (0-indexed positions, the number is position 0).
Usage:
  python opening_pipeline.py banc [K] [meme|autre] [beam] [guessed nodes]   (dictionary from the testbed's book, or from other texts)
  python opening_pipeline.py yeux [E1=TEXT W2=TEXT W3=TEXT E4=TEXT] [beam] [K] [max_combos] [part] [nparts]
     option lex=en|jeu|fi|gut|gutfi (dictionary; jeu = game texts; gut = v2 model on the Gutenberg corpus, §49); (without text: blind brute force; results in opening_blind_out_{beam}_{top|tous}_{part}.tsv;
      "tous": the survivors of §42 outside the 241 best; column 6 = step where the beam dies; "mort" = beam died)
     (TEXT = plaintext from position 1, A-Z and "_" for the space)"""
import sys
import time
import re
from collections import Counter
from pathlib import Path
import numpy as np
from keyed_deck_attack import tables, flatten
from known_q_local_filter import ALPHAS
from known_positions_unigram import logphi_unigram
from opening_search import run, build_lexicon, build_bigrams, texts_of, wordy_plaintexts, char_model
from opening_crib_solver import solve, convention, top_combos, decode_text
import testbed_spaces as tbs
from explore import xgak_encrypt

NAMES = ["E1", "W1", "E2", "W2", "E3", "W3", "E4", "W4", "E5"]


def other_books():
    return " ".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in
                    ("sources/texts/kalevala_en_crawford.txt", "sources/texts/hermetic_museum_vol1_waite1893.txt",
                     "sources/texts/turba_philosophorum_waite1896.txt"))


def lexicon_text(kind):
    """Source text of the dictionary: en (4 English books), jeu (Noita's texts: translations, wiki, tablets),
    fi (Finnish: corpus + Kalevala, Ä/Å → A, Ö → O, no room for them in the convention's alphabet)."""
    if kind == "jeu":
        import keyword_decks as kd
        return " ".join(kd.texts())
    if kind == "fi":
        t = " ".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in
                     ("corpus/fi.txt", "sources/texts/kalevala_fi.txt")).upper()
        return t.replace("Ä", "A").replace("Å", "A").replace("Ö", "O")
    return " ".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in
                    ("corpus/en.txt", "sources/texts/kalevala_en_crawford.txt",
                     "sources/texts/hermetic_museum_vol1_waite1893.txt", "sources/texts/turba_philosophorum_waite1896.txt"))


def lexicon(text):
    tokens = re.findall(r"[A-Z]+", text.upper())
    child, lpc, lpe, wid = build_lexicon(Counter(tokens))
    bkeys, bvals, bdef, V = build_bigrams(tokens, child, wid)
    return (child, lpc, lpe, wid, bkeys, bvals, bdef, V) + char_model(tokens)


def em_refine(msgs, x, alpha, q, binv, sinv, lp_alpha, iters=30):
    from scipy.optimize import linear_sum_assignment
    from keyed_deck_attack import scores
    from keyed_deck_robust import decide, reads
    qs = int(q[alpha.index("_")])
    lp = np.full(83, np.log(1e-4 / 83)); lp[q] = lp_alpha
    lpl = lp.copy(); lpl[qs] = np.log(1e-6)
    let = [int(v) for v in q if v != qs]; lpl[let] -= np.log(np.exp(lp[let]).sum())
    C, st, ln = flatten(msgs)
    for _ in range(iters):
        sp = decide(C, st, ln, x, binv, sinv, qs, lpl, 16)
        sc = scores(C, st, ln, sp, binv, sinv, lp, True)
        rows, cols = linear_sum_assignment(-sc)
        xn = np.empty(83, np.int64); xn[rows] = cols
        if (xn == x).all():
            break
        x = xn
    sp = decide(C, st, ln, x, binv, sinv, qs, lpl, 16)
    r = reads(C, st, ln, x, binv, sinv, sp)
    return float(lp[r].sum()) / len(r), x, r


def pipeline(msgs, alpha_name, orient, binv, sinv, lex, B, K, T=16, KF=0, guesses=None, truth=None, rng=None,
             verify_ids=(0, 3, 6), en_text=None):
    alpha, q = convention(alpha_name, orient)
    if isinstance(lex, dict):   # v2 model (opening_search2): bigrams conditioning the prefix
        from opening_search2 import run2
        (SC, TXT, alive, trank, lost), (card, order, paths, syms) = run2(msgs, T, alpha, orient, binv, sinv, lex, B,
                                                                        truth=truth, KF=KF, guesses=guesses)
    else:
        (SC, TXT, alive, trank, lost), (card, order, paths, syms) = run(msgs, T, alpha, orient, binv, sinv, lex, B,
                                                                       truth=truth, KF=KF, guesses=guesses)
    if len(SC) == 0:
        return None, (lost if truth is not None else int(np.argmax(alive == 0)))
    lpa = logphi_unigram(alpha, en_text)[:len(alpha)]
    C, st, ln = flatten(msgs)
    best = None
    for h in np.argsort(-SC)[:K]:
        dec = texts_of(TXT[h], paths, syms, msgs)
        g = {i: "1" + dec[i] for i in verify_ids}
        if any("?" in v for v in g.values()):
            continue
        res = solve(msgs, g, alpha, q, binv, sinv, lpa, rng, R=1, skip_first=True)
        if res is not None and (best is None or res[0] > best[0]):
            best = (res[0], dec, res)
    # refinement: free EM (no imposed cards) from the deck found; basin ≈ 75% (§36)
    if best is not None:
        r = em_refine(msgs, best[2][1].copy(), alpha, q, binv, sinv, lpa)
        if r[0] > best[0]:
            best = (r[0], best[1], r)
    return best, lost


if __name__ == "__main__":
    names, BS, INV = tables()
    rng = np.random.default_rng(11)
    T_en = tbs.english_with_spaces()
    if sys.argv[1] == "banc":
        K = int(sys.argv[2]) if len(sys.argv) > 2 else 40
        BB = int(sys.argv[4]) if len(sys.argv) > 4 else 200000
        KF0 = int(sys.argv[5]) if len(sys.argv) > 5 else 20
        if len(sys.argv) > 3 and sys.argv[3] == "autre":   # dictionary taken from OTHER texts than the testbed's
            lex = lexicon(" ".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in
                                   ("sources/texts/kalevala_en_crawford.txt", "sources/texts/hermetic_museum_vol1_waite1893.txt",
                                    "sources/texts/turba_philosophorum_waite1896.txt")))
        else:
            lex = lexicon(T_en.replace("_", " "))
        pl = wordy_plaintexts(T_en, 5)
        alpha = ALPHAS["AZ19_"]
        q = np.array([alpha.index(ch) for ch in tbs.ALPHA_S], np.int64)
        print(f"testbed: beam {BB}, {KF0} guessed nodes, dictionary {sys.argv[3] if len(sys.argv) > 3 else 'meme'}", flush=True)
        for bname, sname in (("outshuffle", "milk"), ("deal3fwd", "rot24")):
            D0 = rng.permutation(83)
            S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
            msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist()
                    for m in pl]
            for lab, (b2, s2) in (("true pair", (bname, sname)), ("wrong pair", ("inshuffle", "deal5rev"))):
                t0 = time.time()
                best, lost = pipeline(msgs, "AZ19_", "k", INV[b2], INV[s2], lex, BB, K, KF=KF0, truth=pl, rng=rng,
                                      en_text=T_en)
                if best is None:
                    print(f"β={bname} σ={sname}, {lab}: beam died, true branch lost at step {lost} "
                          f"({time.time() - t0:.0f} s)", flush=True)
                    continue
                C, st, ln = flatten(msgs)
                alpha_, q_ = convention("AZ19_", "k")
                full = decode_text(best[2][2], q_, alpha_, st, ln)
                ok = np.mean([a == b for a, b in zip("".join(full), "".join(pl))])
                print(f"β={bname} σ={sname}, {lab}: best score {best[0]:.2f} per symbol; "
                      f"whole text correct at {ok:.2f} ({time.time() - t0:.0f} s)\n   {full[0][:70]}", flush=True)
    else:
        from stats import load_eyes
        _, M = load_eyes()
        args = [a for a in sys.argv[2:] if "=" in a]; nums = [int(a) for a in sys.argv[2:] if a.isdigit()]
        B = nums[0] if len(nums) > 0 else 200000
        K = nums[1] if len(nums) > 1 else 30
        maxc = nums[2] if len(nums) > 2 else 10 ** 6
        part = nums[3] if len(nums) > 3 else 0
        nparts = nums[4] if len(nums) > 4 else 1
        tous = "tous" in sys.argv or "tous01" in sys.argv
        lexarg = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("lex=")), "en")
        tag = f"{B}_{'tous01' if 'tous01' in sys.argv else ('tous' if tous else 'top')}_{part}"
        if lexarg in ("gut", "gutfi"):
            from opening_search2 import build_lm, gutenberg_text
        outname = f"opening_blind_out_{tag}.tsv" if lexarg == "en" else f"opening_blind_out_{lexarg}_{tag}.tsv"
        outf = open(outname, "a", encoding="utf-8")
        guesses = {NAMES.index(a.split("=")[0]): a.split("=", 1)[1].upper() for a in args if not a.startswith("lex=")}
        if lexarg == "gutfi":   # Finnish v2 model: Finnish Gutenberg + Kalevala + corpus, Ä/Å → A, Ö → O
            from opening_search2 import gutenberg_books
            books = [b.upper().replace("Ä", "A").replace("Å", "A").replace("Ö", "O")
                     for b in list(gutenberg_books(folder="gutenberg_fi")) + [lexicon_text("fi")]]
            lex = build_lm(books)
            texts = books[-1]
        elif lexarg == "gut":   # v2 model on the large corpus (Gutenberg, without Pride and Prejudice) + 3 books
            from opening_search2 import gutenberg_books
            books = list(gutenberg_books()) + [other_books()]
            lex = build_lm(books)
            texts = other_books()
        else:
            texts = lexicon_text(lexarg)
            lex = lexicon(texts)
        T_en = re.sub(r"[^A-Z]+", "_", texts.upper())   # letter frequencies for the verification
        out = []
        if tous:   # the survivors of §42 not already in the 241 best
            from opening_crib_solver import survivors
            top = {(r["alphabet"], r["orient"], r["beta"], r["sigma"]) for r in top_combos()}
            combos = [r for r in survivors() if (r["alphabet"], r["orient"], r["beta"], r["sigma"]) not in top]
            if "tous01" in sys.argv:   # threshold 0.01 of the local filter, excluding the survivors at 0.05 already scanned
                done05 = {(r["alphabet"], r["orient"], r["beta"], r["sigma"]) for r in survivors()}
                combos = [r for r in survivors(0.01) if (r["alphabet"], r["orient"], r["beta"], r["sigma"]) not in done05]
        else:
            combos = top_combos()
        done = set()
        if Path(outname).exists():   # resume: combinations already done are skipped
            done = {tuple(l.split("\t")[:4]) for l in open(outname, encoding="utf-8")}
        for row in combos[:maxc][part::nparts]:
            if (row["alphabet"], row["orient"], row["beta"], row["sigma"]) in done:
                continue
            t0 = time.time()
            try:
                best, lost = pipeline(M, row["alphabet"], row["orient"], INV[row["beta"]], INV[row["sigma"]], lex, B, K,
                                      guesses=guesses, rng=rng, verify_ids=(0, 3, 6), en_text=T_en)
            except ValueError as e:
                print("incompatible guesses:", e); break
            outf.write("\t".join([row["alphabet"], row["orient"], row["beta"], row["sigma"],
                                   f"{best[0]:.3f}" if best is not None else "mort", str(lost),
                                   "|".join(best[1][i][:15] for i in (0, 3, 6)) if best is not None else "",
                                   f"{time.time() - t0:.0f}"]) + "\n")
            outf.flush()
            if best is not None:
                out.append((best[0], row, best[1]))
                print(f"{row['alphabet']}/{row['orient']} β={row['beta']} σ={row['sigma']} : {best[0]:.2f}  "
                      f"{best[1][0][:15]} | {best[1][3][:15]} | {best[1][6][:15]}", flush=True)
        out.sort(key=lambda z: -z[0])
        print(f"best: {out[0][0]:.2f} per symbol (success ≈ -2.9, failure ≈ -6)" if out else "no candidate")
