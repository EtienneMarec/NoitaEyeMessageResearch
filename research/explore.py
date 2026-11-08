"""Exploration of more structured "deck of cards" mechanism families (XGAK).

Step for a plaintext symbol s (letter or homophone):
    output = D[q_s]                 (read at a position specific to the symbol)
    D = D[τ_s]                      (symbol-specific change: what becomes of the card read?)
    D = D[β]                        (base shuffle shared by all letters)
Families for τ_s (tokens):
  "dessus"      : the card read goes on top (swap 0 <-> q_s)                  [control, see §7.4]
  "echange"     : the card read is swapped with a symbol-specific position m_s
  "reinsertion" : the card read is removed then reinserted at position m_s (shifting the cards between)
  "aucune"      : nothing (all letters have the same permutation -> progressive cipher)
No doubles guaranteed by choosing read positions disjoint from the destinations.
Criteria from the eyes: synchronisation after a differing first letter (A: 24, C: 20),
chi² of the gap profile (eyes: 63.2 over d = 2..40), no doubles.
"""
import sys
from collections import Counter
import numpy as np
from numba import njit
from testbed import build_plaintexts, english_letters, ALPHA
from swap_model_test import chi2, prefix_sync
from stats import load_eyes

N = 83


@njit(cache=True)
def xgak_encrypt(seq, reads, S):
    D = np.arange(N)
    out = np.empty(seq.shape[0], np.int64)
    for i in range(seq.shape[0]):
        s = seq[i]
        out[i] = D[reads[s]]
        tmp = D.copy()
        row = S[s]
        for x in range(N):
            D[x] = tmp[row[x]]
    return out


def tau_for(kind, q, m):
    idx = list(range(N))
    if kind == "dessus":
        idx[0], idx[q] = idx[q], idx[0]
    elif kind == "echange":
        idx[q], idx[m] = idx[m], idx[q]
    elif kind == "reinsertion":
        c = idx.pop(q); idx.insert(m, c)
    return np.array(idx, np.int64)


def make_beta(kind, rng):
    if kind == "aucun":
        return np.arange(N)
    if kind == "coupe1":
        return (np.arange(N) + 1) % N
    if kind == "cycle83":
        o = rng.permutation(N); b = np.empty(N, np.int64); b[o] = np.roll(o, 1); return b
    return rng.permutation(N)


def make_key(tkind, bkind, homophones, rng):
    freq = Counter(english_letters()[:200000])
    beta = make_beta(bkind, rng)
    counts = [1] * len(ALPHA)
    if homophones:
        w = np.array([freq.get(ch, 0) for ch in ALPHA], float)
        extra = 41 - len(ALPHA)                       # at most 41 reads + 41 destinations
        w = w / w.sum() * extra
        counts = [1 + int(x) for x in w]
        while sum(counts) < 41:
            counts[int(np.argmax(w - np.array(counts) + 1))] += 1
    nslots = sum(counts)
    pos = rng.permutation(np.arange(1, N))
    reads, dests = pos[:nslots], pos[nslots:2 * nslots] if 2 * nslots <= N - 1 else pos[nslots:]
    slots, k = {}, 0
    for ch, c in zip(ALPHA, counts):
        slots[ch] = list(range(k, k + c)); k += c
    R = np.array(reads, np.int64)
    S = np.empty((nslots, N), np.int64)
    for s in range(nslots):
        t = tau_for(tkind, int(reads[s]), int(dests[s % len(dests)]))
        S[s] = t[beta]
    return slots, R, S


def encode(msg, slots):
    cnt = Counter(); out = []
    for ch in msg:
        sl = slots[ch]; out.append(sl[cnt[ch] % len(sl)]); cnt[ch] += 1
    return np.array(out, np.int64)


def evaluate(tkind, bkind, homo, R, rng, plains, eyes_chi):
    chis, syncs, dbls, ok = [], [], [], 0
    for _ in range(R):
        slots, reads, S = make_key(tkind, bkind, homo, rng)
        C = [xgak_encrypt(encode(m, slots), reads, S).tolist() for m in plains]
        c, s = chi2(C), prefix_sync(C)
        d = sum(a == b for m in C for a, b in zip(m, m[1:]))
        chis.append(c); syncs.append(min(s)); dbls.append(d)
        ok += (c <= eyes_chi * 1.0) and min(s) >= 15 and d == 0
    return np.median(chis), np.mean(np.array(chis) <= eyes_chi), np.median(syncs), np.mean(np.array(syncs) >= 15), max(dbls), ok / R


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    names, M = load_eyes()
    eyes_chi = chi2(M)
    plains = build_plaintexts()
    rng = np.random.default_rng(11)
    print(f"eyes: chi² {eyes_chi:.1f}, sync {prefix_sync(M)}, doubles 0     ({R} draws per family)")
    print("τ (card read)   β          homoph.  med. chi²  P(chi²<=eyes)  med. sync     P(sync>=15)     max doubles   P(all)")
    for tkind in ("dessus", "echange", "reinsertion", "aucune"):
        for bkind in ("aucun", "coupe1", "cycle83", "aleatoire"):
            for homo in (False, True):
                r = evaluate(tkind, bkind, homo, R, rng, plains, eyes_chi)
                print(f"{tkind:14s}  {bkind:9s}  {'yes' if homo else 'no':6s}  {r[0]:8.1f}   {r[1]:6.2f}         "
                      f"{r[2]:5.0f}         {r[3]:5.2f}           {r[4]:4d}        {r[5]:.2f}", flush=True)
