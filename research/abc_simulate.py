"""Simulations for ABC inference (§40).

Each simulation draws: a cipher family (with its parameter), a plaintext (English with spaces, or letters
flattened to p^0.25 with 18% spaces), a number n of letters substituted in the E5 stutter (spaces kept), a
testbed text (seed) and a key; it then computes the summary statistics (abc_stats.summary) and appends them to
abc_sims.tsv (one line per simulation).
Families (data tokens kept as written to abc_sims.tsv):
  lymm{k}      : k swaps per symbol then a random β, first symbol outside the deck, space = ordinary letter;
  espace_{s}   : "space model": letters = β (derangement), space = σ (random, or β + s swaps), no-doubles rule,
                 first symbol inside the deck;
  reinsertion  : reinsertion + random β, first symbol outside the deck;
  classes_{p}-{m} (§43): letter-class model (class_model.py), partition p (un, vc, r2, r3, r4),
                 secondary letter classes = β + m swaps (or random), space = β + 16.
Text tokens: "anglais" = English, "aplati" = flattened letters.
Usage: python abc_simulate.py COUNT [seed] [families, e.g. espace:1,espace:2 (§41)]"""
import sys
import random
import numpy as np
import testbed_spaces as tbs
import space_model_test as sm
from explore import xgak_encrypt
from family_zoo import make_key as zoo_key
from near_space_test import flat_text
from abc_stats import summary, NAMES_STATS

N = 83
LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
FAMILIES = [("lymm", 1), ("lymm", 2), ("lymm", 4), ("espace", "aleatoire"), ("espace", "16"), ("espace", "40"),
            ("reinsertion", 0)]


def lymm_key(k, rng):
    beta = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.empty((len(tbs.ALPHA_S), N), np.int64)
    for s in range(len(tbs.ALPHA_S)):
        idx = np.arange(N); m = int(rng.integers(N))
        while m == q[s]:
            m = int(rng.integers(N))
        idx[[q[s], m]] = idx[[m, q[s]]]
        for _ in range(k - 1):
            a, b = rng.choice(N, 2, replace=False); idx[[a, b]] = idx[[b, a]]
        S[s] = idx[beta]
    return q, S


def encrypt(fam, par, pl, rng):
    if fam == "classes":
        import class_model
        kind, m = par.split("-")
        return class_model.encrypt(pl, kind, m, rng)[0]
    if fam == "espace":
        q, S = sm.make_key("_", par, True, rng)
        return [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
    if fam == "lymm":
        q, S = lymm_key(par, rng)
    else:
        q, S = zoo_key("reinsertion", "aleatoire", 0, rng, len(tbs.ALPHA_S))
    return [[0] + xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in pl]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    rng = np.random.default_rng(seed); rnd = random.Random(seed)
    if len(sys.argv) > 3:
        FAMILIES = [(f.split(":")[0], f.split(":")[1] if f.startswith(("espace", "classes")) else int(f.split(":")[1]))
                    for f in sys.argv[3].split(",")]
    texts = {"anglais": tbs.english_with_spaces(), "aplati": flat_text(400000, random.Random(1))}
    orig = tbs.english_with_spaces
    bases = {}
    for tname, T in texts.items():
        tbs.english_with_spaces = lambda T=T: T
        bases[tname] = [tbs.build_plaintexts(seed=s, word_start=True) for s in range(10)]
        tbs.english_with_spaces = orig
    out = open("abc_sims.tsv", "a", encoding="utf-8")
    for r in range(R):
        fam, par = FAMILIES[rnd.randrange(len(FAMILIES))]
        tname = rnd.choice(list(texts))
        n = rnd.choice((6, 9, 12, 15))
        k = rnd.randrange(10)
        pl = list(bases[tname][k])
        # E5 = E4 (number 9) with the letter inserted at 47, without the testbed's fixed Q/X edits
        pl[8] = "9" + pl[6][1:47] + "S" + pl[6][47:]
        e5 = list(pl[8]); idx = [i for i in range(21, 47) if e5[i] != "_"]
        for i in rnd.sample(idx, min(n, len(idx))):
            e5[i] = rnd.choice([c for c in LET if c != e5[i]])
        pl[8] = "".join(e5)
        d0 = tbs.obstacle_window(pl)
        C = encrypt(fam, par, pl, rng)
        s = summary(C, d0)
        out.write("\t".join([fam, str(par), tname, str(n)] + [f"{v:.5g}" for v in s]) + "\n"); out.flush()
    out.close()
