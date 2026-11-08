"""Model "the space shuffles differently" on the testbed with spaces (§26).

Letters and digits: read at q_p, then shared shuffle β (random derangement).
Space "_": read at q_, then its own shuffle σ_ (random permutation, or β + k swaps).
Variant "+vowels": AEIOU are special too (each with its own shuffle).
No-doubles rule (option): read positions Q such that β(Q) ∩ Q = ∅ (letter → letter with no doubles).

Criteria: isomorphs (occurrences of P), flat profile, 0 doubles, stutter (E5 = E4 with n substitutions
in 21..46, characters drawn from the text's frequencies, space included), fixed points <= 1%, exact pattern
of the obstacle (E1/W1 of the testbed: 4-letter words swapped around "_TO_"), "same Δ" agreement (eyes 0.056)."""
import sys
from collections import Counter
from itertools import combinations
import numpy as np
from testbed_spaces import build_plaintexts, english_with_spaces, ALPHA_S, obstacle_window
from explore import xgak_encrypt
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from same_delta_models import agreement
from testkey import true_blocks
from architecture import iso_ok
from stats import load_eyes

N = 83
T = english_with_spaces()[:300000]
FR = Counter(T)
CH = [c for c in FR]
W = np.array([FR[c] for c in CH], float); W /= W.sum()


def derangement(rng):
    while True:
        b = rng.permutation(N)
        if not (b == np.arange(N)).any():
            return b


def make_key(special, skind, nodouble, rng):
    beta = derangement(rng)
    if nodouble:
        order = rng.permutation(N); Q = []
        bad = set()
        for x in order:
            if len(Q) == len(ALPHA_S):
                break
            # D'[x] = D[β[x]]: the card read at q arrives at x such that β[x] = q; a double if that x is read
            if x in bad:
                continue
            Q.append(int(x))
            bad |= {int(np.where(beta == x)[0][0]), int(beta[x])}
        q = np.array(Q, np.int64)
        if len(q) < len(ALPHA_S):
            return make_key(special, skind, nodouble, rng)
    else:
        q = rng.choice(N, len(ALPHA_S), replace=False).astype(np.int64)
    S = np.empty((len(ALPHA_S), N), np.int64)
    for i, ch in enumerate(ALPHA_S):
        if ch in special:
            if skind == "aleatoire":
                S[i] = rng.permutation(N)
            else:
                idx = np.arange(N)
                for _ in range(int(skind)):
                    a, b = rng.choice(N, 2, replace=False)
                    idx[[a, b]] = idx[[b, a]]
                S[i] = idx[beta]
        else:
            S[i] = beta
    return q, S


def enc(plains, q, S):
    return [[0] + xgak_encrypt(np.array([ALPHA_S.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in plains]


def stutter_edit(pl, n, rng):
    out = list(pl); e5 = list(out[8])
    for k in rng.choice(np.arange(21, 47), n, replace=False):
        while True:
            c = CH[rng.choice(len(CH), p=W)]
            if c != e5[k]:
                break
        e5[k] = c
    out[8] = "".join(e5)
    return out


def pattern(A, B, d0):
    d = [A[i] != B[i] for i in range(d0, d0 + 25)]
    return all(d[0:4]) and not any(d[4:8]) and all(d[8:12]) and not any(d[12:25])


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    d0 = obstacle_window(base)
    tb = [b for b in true_blocks(base) if b[4] >= 12]
    P = base[0][d0 + 14:d0 + 14 + 18]
    occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
    rng = np.random.default_rng(260)
    print(f"phrase P = {P!r}, {len(occ)} occurrences; d0 = {d0}")
    print("special       σ_spec     no-dbl   n  iso   flat  0dbl  texture  fixpts  motif  ALL    | same-Δ agreement (med.)  med. chi²")
    for special, skind in (("_", "aleatoire"), ("_", "8"), ("_", "20"), ("_AEIOU", "aleatoire"), ("", "aleatoire")):
        for nodbl in (False, True):
            for n in (3, 6):
                c = np.zeros(7); agr = []; chis = []
                for _ in range(R):
                    for attempt in range(25):
                        q, S = make_key(special, skind, nodbl, rng)
                        pl = stutter_edit(base, n, rng)
                        C = enc(pl, q, S)
                        if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                            break
                    segs = [C[k][i + 1:i + len(P)] for k, i in occ]
                    iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                    chis.append(chi2(C))
                    a = chis[-1] <= EYES_CHI
                    b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    pm = pattern(C[0], C[1], d0)
                    nn, ag = agreement(enc(base, q, S), tb); agr.append(ag / max(nn, 1))
                    c += [iso, a, b, t, x, pm, iso and a and b and t and x and pm]
                print(f"{special or '-':12s}  {skind:9s}  {str(nodbl):5s}   {n}  " + "  ".join(f"{v / R:.2f}" for v in c)
                      + f"  |  {np.median(agr):.3f}              {np.median(chis):.0f}", flush=True)
