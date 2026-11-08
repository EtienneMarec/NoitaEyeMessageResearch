"""Parallel scan of probable texts × natural shuffle pairs (space model) (§38).

For each (β, σ) pair of the list and each candidate text (number + L-1 characters), consistency test
crib_test.consistent on the start of a message (E1 by default). Parallelised over the candidates (numba prange).
Pairs: cuts of ±1 to ±5 cards (rot1..rot5, rot78..rot82) for the letters with each of the non-rotation natural
shuffles for the space, and the reverse.
  --valider: testbed with spaces, true text hidden among decoys, pair drawn from the list.
  otherwise: eyes. Usage: python crib_scan.py TARGET CANDIDATES_FILE MODE, with MODE = chiffre (number then text),
              lettre (text from symbol 0) or hors (symbol 0 outside the cipher, text from symbol 1).
              Results: crib_scan_hits_{TARGET}_{MODE}_{file}.tsv (one line per consistent pair × candidate)."""
import sys
import time
import random
import numpy as np
from numba import njit, prange
from crib_test import consistent, CODES, SPACE
from keyed_deck_attack import tables

N = 83


@njit(parallel=True, cache=True)
def batch(cs, LT, binv, sinv, space_code):
    n = LT.shape[0]
    out = np.zeros(n, np.int64)
    for i in prange(n):
        d, nc = consistent(cs, LT[i], binv, sinv, space_code)
        out[i] = d
    return out


def pair_list(names):
    rots = [f"rot{k}" for k in (1, 2, 3, 4, 5, 78, 79, 80, 81, 82)]
    nat = [k for k in names if not k.startswith("rot") and k != "id"]
    return [(r, s) for r in rots for s in nat] + [(s, r) for s in nat for r in rots]


def encode_all(cands, L):
    LT = np.empty((len(cands), L), np.int64)
    for i, s in enumerate(cands):
        t = "1" + s[:L - 1]
        LT[i] = [CODES[ch] for ch in t]
    return LT


if __name__ == "__main__":
    L = 75
    names, BS, inv = tables()
    pairs = pair_list(names)
    if "--valider" in sys.argv:
        import testbed_spaces as tbs
        from explore import xgak_encrypt
        rnd = random.Random(8); rng = np.random.default_rng(8)
        T = tbs.english_with_spaces()
        pl = tbs.build_plaintexts()
        bname, sname = pairs[rnd.randrange(len(pairs))]
        D0 = rng.permutation(N); q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
        cs = D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in pl[0]], np.int64), q, S))][:L].astype(np.int64)
        decoys = []
        while len(decoys) < 5000:
            i = rnd.randrange(1000, len(T) - 200)
            j = T.find("_", i) + 1
            decoys.append(T[j:j + L])
        true = pl[0][1:L]
        cands = decoys[:2500] + [true] + decoys[2500:]
        LT = encode_all(cands, L)
        t0 = time.time()
        hits = []
        for b, s in pairs:
            d = batch(cs, LT, inv[b], inv[s], SPACE)
            for i in np.where(d == 0)[0]:
                hits.append((b, s, int(i)))
        print(f"true pair β={bname}, σ={sname}; {len(pairs)} pairs × {len(cands)} candidates in {time.time() - t0:.0f} s")
        print(f"hits: {len(hits)}; of which the true text: {[h for h in hits if h[2] == 2500][:5]}")
        print("other hits (first 10):", [h for h in hits if h[2] != 2500][:10])
    else:
        # usage: python crib_scan.py TARGET CANDIDATES_FILE MODE   (MODE: chiffre | lettre | hors)
        from stats import load_eyes
        names_e, M = load_eyes()
        target = sys.argv[1] if len(sys.argv) > 1 else "E1"
        cfile = sys.argv[2] if len(sys.argv) > 2 else f"crib_candidates_L{L}.txt"
        mode = sys.argv[3] if len(sys.argv) > 3 else "chiffre"
        seq = M[names_e.index(target)]
        cs = np.array((seq[1:] if mode == "hors" else seq)[:L], np.int64)
        cands = [c for c in open(cfile, encoding="utf-8").read().split("\n") if len(c) >= L]
        LT = np.empty((len(cands), L), np.int64)
        for i, s in enumerate(cands):
            t = ("1" + s[:L - 1]) if mode == "chiffre" else s[:L]
            LT[i] = [CODES[ch] for ch in t]
        t0 = time.time()
        out = f"crib_scan_hits_{target}_{mode}_{cfile.split('.')[0]}.tsv"
        with open(out, "w", encoding="utf-8") as f:
            f.write("beta\tsigma\tcandidat\n")
            nh = 0
            for k, (b, s) in enumerate(pairs):
                d = batch(cs, LT, inv[b], inv[s], SPACE)
                for i in np.where(d == 0)[0]:
                    f.write(f"{b}\t{s}\t{cands[i]}\n"); nh += 1
                f.flush()
        print(f"{target} mode={mode} file={cfile}: {nh} alerts over {len(pairs)} pairs × {len(cands)} candidates ({time.time() - t0:.0f} s)")