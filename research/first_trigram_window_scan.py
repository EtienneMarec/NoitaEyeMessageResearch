"""Test "consecutive message numbers" on generated starting decks (§46).

Hypothesis: the first symbol of each message is its number, read DIRECTLY from the starting deck D0 at
the digit's position; the digits occupy consecutive positions (convention of §39, whatever the
alphabet). Then the 9 first trigrams {50, 80, 36, 76, 63, 34, 27, 77, 33} occupy 9 CONSECUTIVE
positions of D0 (in any order), independently of β and σ. Variant: the first read happens
after a natural shuffle S (D0∘S). For a random deck: P ≈ 75 / C(83, 9) ≈ 2.3e-10 (linear window),
83 / C(83, 9) as a circular arc (C(83, 9) = 3.29e11).
Decks: Noita's generator (rng_decks.py; direct seeds and after one Next(), 3 shuffles), keyword
decks of §12.2 (keyword_decks.py), each taken as D0 = P (position → card) or P⁻¹, with or without S.
Usage: python first_trigram_window_scan.py rng MAX_SEED | xy [R] | mots"""
import sys
import numpy as np
from numba import njit, prange
from rng_decks import shuffle, nnext, set_random_seed, SPECIAL_WS
from deckcipher import base_shuffles

N = 83
FIRST = np.array([50, 80, 36, 76, 63, 34, 27, 77, 33], np.int64)


@njit(cache=True)
def window_hit(pos):
    """1 if the 9 positions are consecutive (linear window), 2 if only as a circular arc, 0 otherwise."""
    mn = 1000; mx = -1
    occ = np.zeros(N, np.bool_)
    for i in range(pos.shape[0]):
        p = pos[i]; occ[p] = True
        mn = min(mn, p); mx = max(mx, p)
    if mx - mn == pos.shape[0] - 1:
        return 1
    # circular arc: there is a start a such that a..a+8 (mod 83) is occupied
    for a in range(N):
        ok = True
        for k in range(pos.shape[0]):
            if not occ[(a + k) % N]:
                ok = False; break
        if ok:
            return 2
    return 0


@njit(cache=True)
def check_deck(P, SINV, out_codes):
    """P: position -> card. Tests D0 = P and D0 = P^-1, each without a shuffle then with each S (D0∘S)."""
    n = 0
    Pinv = np.empty(N, np.int64)
    for i in range(N):
        Pinv[P[i]] = i
    pos = np.empty(FIRST.shape[0], np.int64)
    for orient in range(2):
        for v in range(SINV.shape[0] + 1):
            for i in range(FIRST.shape[0]):
                c = FIRST[i]
                p = Pinv[c] if orient == 0 else P[c]   # position of card c in D0
                if v > 0:
                    p = SINV[v - 1, p]                 # D0∘S: the card at p moves to Sinv[p]
                pos[i] = p
            h = window_hit(pos)
            if h > 0:
                out_codes[n] = orient * 1000 + v * 2 + (h - 1); n += 1
    return n


@njit(parallel=True, cache=True)
def scan_rng(smax, SINV):
    hits = np.zeros((smax, 6), np.int64) - 1
    for s in prange(smax):
        codes = np.empty(2 * (SINV.shape[0] + 1) * 2, np.int64)
        k = 0
        for mode in range(2):
            seed = s if mode == 0 else nnext(s)
            for kind in range(3):
                P = shuffle(seed, kind)
                n = check_deck(P, SINV, codes)
                if n > 0:
                    hits[s, k] = mode * 1000000 + kind * 100000 + codes[0]; k = min(k + 1, 5)
    return hits


@njit(parallel=True, cache=True)
def scan_xy(wss, R, SINV):
    """SetRandomSeed(x, y) for x, y in [-R, R] and each world seed; 3 shuffles."""
    W = 2 * R + 1
    hits = np.zeros((wss.shape[0] * W * W, 3), np.int64) - 1
    for idx in prange(wss.shape[0] * W * W):
        wi = idx // (W * W); x = (idx // W) % W - R; y = idx % W - R
        seed = set_random_seed(float(x), float(y), wss[wi])
        codes = np.empty(2 * (SINV.shape[0] + 1) * 2, np.int64)
        for kind in range(3):
            P = shuffle(seed, kind)
            if check_deck(P, SINV, codes) > 0:
                hits[idx, kind] = codes[0]
    return hits


def n_indep(names):
    """Independent variants: identity, reversal and rotations map an arc onto an arc."""
    return 1 + sum(1 for k in names if k not in ("id", "reverse") and not k.startswith("rot"))


if __name__ == "__main__":
    BS = base_shuffles()
    names = list(BS)
    SINV = np.array([np.argsort(BS[k]) for k in names], np.int64)
    if sys.argv[1] == "rng":
        smax = int(sys.argv[2])
        H = scan_rng(smax, SINV)
        found = [(s, h) for s in range(smax) for h in H[s] if h >= 0]
        print(f"seeds 0..{smax - 1} × (direct, after Next) × 3 shuffles × (P, P⁻¹) × (no shuffle + {len(names)} S): "
              f"{len(found)} decks with a consecutive window; expected by chance ≈ "
              f"{smax * 6 * 2 * n_indep(names) * 83 / 3.29e11:.2f}", flush=True)
        for s, h in found[:50]:
            mode, rest = divmod(h, 1000000); kind, code = divmod(rest, 100000)
            orient, r2 = divmod(code, 1000); v, arc = divmod(r2, 2)
            print(f"  seed {s} mode {mode} shuffle {kind} orient {orient} S={'none' if v == 0 else names[v - 1]} "
                  f"{'arc' if arc else 'window'}")
    elif sys.argv[1] == "xy":
        R = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        wss = np.array(SPECIAL_WS, np.int64)
        H = scan_xy(wss, R, SINV)
        found = np.argwhere(H >= 0)
        n = H.shape[0] * 3
        print(f"SetRandomSeed(x, y), x, y ∈ [-{R}, {R}], {len(wss)} world seeds, 3 shuffles ({n} decks) × (P, P⁻¹) × "
              f"(no shuffle + {len(names)} S): {len(found)} with a consecutive window; expected by chance ≈ "
              f"{n * 2 * n_indep(names) * 83 / 3.29e11:.3f}", flush=True)
        for i, k in found[:50]:
            W = 2 * R + 1
            print(f"  ws={wss[i // (W * W)]} x={(i // W) % W - R} y={i % W - R} shuffle {k} code {H[i, k]}")
    else:
        import keyword_decks as kd
        ts = kd.texts(); kws = kd.keywords(ts)
        decks = []
        for w in kws:
            decks += [np.array(p, np.int64) for _, p in kd.perms_for(w)]
        codes = np.empty(2 * (len(names) + 1) * 2, np.int64)
        found = []
        for i, P in enumerate(decks):
            n = check_deck(P, SINV, codes)
            if n:
                found.append((i, codes[:n].tolist()))
        print(f"{len(decks)} keyword decks: {len(found)} with a consecutive window; expected by chance ≈ "
              f"{len(decks) * 2 * n_indep(names) * 83 / 3.29e11:.4f}", flush=True)
        for i, c in found[:50]:
            print("  ", i, c)
