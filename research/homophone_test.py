"""Variant: β + ONE swap per letter, but with a flattened homophonic alphabet.
Each letter gets a number of read positions proportional to its frequency (82 positions),
and a letter's homophones are used in turn within each message (Zodiac style).
We measure the flatness of the gap profile and the synchronisation after the first letter.
"""
import sys
from collections import Counter
import numpy as np
from testbed import build_plaintexts, english_letters, ALPHA
from swap_model_test import gak_encrypt, chi2, prefix_sync, N
from stats import load_eyes


def homophone_key(beta, rng, homophones=True):
    freq = Counter(english_letters()[:200000])
    letters = ALPHA
    avail = [a for a in range(1, N) if beta[a] != 0]          # β(a) != 0: no doubles
    rng.shuffle(avail)
    if not homophones:
        return {ch: [avail[i]] for i, ch in enumerate(letters)}
    w = np.array([freq.get(ch, 0) for ch in letters], float)
    w = w / w.sum() * (len(avail) - len(letters)) if w.sum() else w
    counts = [1 + int(x) for x in w]
    while sum(counts) < len(avail):
        counts[int(np.argmax(w - np.array(counts)))] += 1
    key, k = {}, 0
    for ch, c in zip(letters, counts):
        key[ch] = avail[k:k + c]; k += c
    return key


def sigmas_for(beta, key):
    slots = [(ch, a) for ch in ALPHA for a in key[ch]]
    sig = np.empty((len(slots), N), np.int64)
    for s, (ch, a) in enumerate(slots):
        tau = np.arange(N); tau[0], tau[a] = a, 0
        sig[s] = beta[tau]
    return slots, sig


def encode(msg, key, slots):
    idx = {sl: i for i, sl in enumerate(slots)}
    cnt = Counter(); out = []
    for ch in msg:
        a = key[ch][cnt[ch] % len(key[ch])]; cnt[ch] += 1
        out.append(idx[(ch, a)])
    return np.array(out, np.int64)


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    names, M = load_eyes()
    eyes = chi2(M)
    print(f"eyes: chi² {eyes:.1f}, sync {prefix_sync(M)}")
    plains = build_plaintexts()
    rng = np.random.default_rng(5)
    for homo in (False, True):
        chis, syns, dbl, both = [], [], [], 0
        for r in range(R):
            beta = rng.permutation(N)
            key = homophone_key(beta, rng, homo)
            slots, sig = sigmas_for(beta, key)
            C = [gak_encrypt(encode(m, key, slots), sig).tolist() for m in plains]
            c, s = chi2(C), prefix_sync(C)
            chis.append(c); syns.append(min(s)); dbl.append(sum(a == b for m in C for a, b in zip(m, m[1:])))
            both += (c <= eyes) and min(s) >= 15
        print(f"{'flattened homophones' if homo else 'no homophones       '}: median chi² {np.median(chis):7.1f} "
              f"P(chi²<=eyes) {np.mean(np.array(chis) <= eyes):.2f}; median sync {np.median(syns):.0f}; "
              f"median doubles {np.median(dbl):.0f}; P(both) {both/R:.2f}")
