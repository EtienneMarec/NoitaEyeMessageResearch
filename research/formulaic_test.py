"""FORMULAIC texts: can the space model reproduce the stutter and the coincidences? (§30)

Hypothesis on the plaintext (unproven): the messages are variants of one template, where words are
replaced by other words of the same length (space structure preserved).
  - Stutter: E5 = E4 where n words (n = 1..4) starting in 21..41 are replaced by words of the same
    length drawn from the corpus. Texture criterion as elsewhere (42% ± 15, >= 7 runs).
  - Coincidences after a divergence: divergence_models testbed, but each message after its prefix is the
    same "template" text with a fraction f of its words replaced (f = 0.3 / 0.6 / 1.0; 1.0 = unrelated,
    with identical space structure).
Models: "espace" (space model, random σ, no doubles); Lymm k = 1 (random β) on the same text with spaces treated
as an ordinary letter."""
import sys
import random
import numpy as np
import testbed_spaces as tbs
import space_model_test as sm
from explore import xgak_encrypt
from stutter_test import texture
from lineage_coincidence import count
from divergence_models import PREF, LENS
from stats import load_eyes

N = 83
T = tbs.english_with_spaces()
WORDS = {}
for w in T[:400000].split("_"):
    if w:
        WORDS.setdefault(len(w), []).append(w)


def replace_words(text, lo, hi, n, rnd):
    """replaces n words starting in [lo, hi] by words of the same length"""
    starts = [i for i in range(max(1, lo), min(hi, len(text) - 1) + 1) if text[i] != "_" and text[i - 1] == "_"]
    s = list(text)
    for i in rnd.sample(starts, min(n, len(starts))):
        j = i
        while j < len(s) and s[j] != "_":
            j += 1
        L = j - i
        if L in WORDS:
            s[i:j] = list(rnd.choice(WORDS[L]))
    return "".join(s)


def lymm_key(rng):
    beta = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.empty((len(tbs.ALPHA_S), N), np.int64)
    for s in range(len(tbs.ALPHA_S)):
        idx = np.arange(N); m = int(rng.integers(N))
        while m == q[s]:
            m = int(rng.integers(N))
        idx[[q[s], m]] = idx[[m, q[s]]]
        S[s] = idx[beta]
    return q, S


def enc(msgs, q, S):
    return [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in msgs]


def formulaic_corpus(f, rnd):
    i = rnd.randrange(1000, len(T) - 3000)
    tmpl = T[i:i + 200]
    pre = {}
    p12 = tmpl[:2]
    msgs = []
    for k in range(9):
        body = replace_words(tmpl, PREF[k] + 1, 199, int(f * tmpl.count("_")), rnd)
        msgs.append(str(k + 1) + tmpl[:PREF[k]] + body[PREF[k]:LENS[k] - 1])
    return msgs


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes(); f0, r0 = texture(M[6], M[8])
    rnd = random.Random(30); rng = np.random.default_rng(30)
    base = tbs.build_plaintexts()
    print("stutter (E5 = E4 with n words replaced, lengths preserved): P(texture)")
    for model in ("espace", "Lymm k=1"):
        row = []
        for n in (1, 2, 3, 4):
            ok = 0
            for _ in range(R):
                q, S = sm.make_key("_", "aleatoire", True, rng) if model == "espace" else lymm_key(rng)
                pl = list(base)
                pl[8] = replace_words(pl[6].replace("7", "9", 1), 21, 41, n, rnd)
                C = enc(pl, q, S)
                f, r = texture(C[6], C[8]); ok += abs(f - f0) <= 0.15 and r >= r0 - 4
            row.append(ok / R)
        print(f"  {model:9s} n = 1..4 : " + "  ".join(f"{x:.2f}" for x in row), flush=True)
    print("coincidences after a divergence (eyes 0.040) by share f of replaced words")
    for model in ("espace", "Lymm k=1"):
        row = []
        for f in (0.3, 0.6, 1.0):
            s = t = 0
            for _ in range(R // 4):
                pl = formulaic_corpus(f, rnd)
                q, S = sm.make_key("_", "aleatoire", True, rng) if model == "espace" else lymm_key(rng)
                tr, su = count(enc(pl, q, S), names, "toutes"); s += su["proche"]; t += tr["proche"]
            row.append(s / max(t, 1))
        print(f"  {model:9s} f = 0.3 / 0.6 / 1.0: " + "  ".join(f"{x:.3f}" for x in row), flush=True)
