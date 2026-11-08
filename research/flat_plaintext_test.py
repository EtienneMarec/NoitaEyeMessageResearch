"""Hypothesis "plaintext with flat frequencies": full battery of Lymm's model (§31).

The English text is first PRE-ENCODED, then encrypted with Lymm's model: 1 swap (q_p, m_p) per symbol
then random β, no-doubles rule (the card read never lands on a read position), no
homophones, first symbol outside the deck. Pre-encodings:
  anglais  : letters A-Z (reference);
  A1Z26    : A = 01 … Z = 26 (alphabet 0-9);
  polybe   : 5×5 Polybius square (I = J), letter -> row, column (alphabet 1-5);
  ternaire : rank 0..25 written in base 3 on 3 digits (alphabet 0-2);
  uniforme : letters A-Z drawn at random (bound).
Testbed: same architecture as testbed.build_plaintexts (shared openings, swapped words of 4 SYMBOLS,
repeated phrase, one-symbol insertions, copied block), built here on the pre-encoded stream.
Criteria: isomorphs (occurrences of the phrase), flat (chi² <= eyes), 0 doubles, stutter (5 substitutions
in 21..46), fixed points <= 1%, exact obstacle pattern ("swap" reading), coincidences after a
divergence (eyes 0.040), "same Δ" agreement (eyes 0.056). R keys per pre-encoding."""
import sys
import random
from itertools import combinations
import numpy as np
from testbed import english_letters
from explore import xgak_encrypt
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from same_delta_models import agreement
from testkey import true_blocks
from lineage_coincidence import count
from divergence_models import PREF, LENS
from architecture import iso_ok
from stats import load_eyes

N = 83
POLY = "ABCDEFGHIKLMNOPQRSTUVWXYZ"


def encode(T, kind, rnd):
    if kind == "anglais":
        return T, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if kind == "uniforme":
        return "".join(rnd.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(len(T))), "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if kind == "A1Z26":
        return "".join(f"{ord(c) - 64:02d}" for c in T), "0123456789"
    if kind == "polybe":
        out = []
        for c in T:
            i = POLY.index("I" if c == "J" else c)
            out.append(f"{i // 5 + 1}{i % 5 + 1}")
        return "".join(out), "12345"
    if kind == "ternaire":
        out = []
        for c in T:
            v = ord(c) - 65
            out.append(f"{v // 9}{(v // 3) % 3}{v % 3}")
        return "".join(out), "012"
    raise ValueError(kind)


def build(T, alpha, seed=0):
    rng = random.Random(seed)
    pos = [rng.randrange(1000, len(T) - 5000)]

    def take(n):
        s = T[pos[0]:pos[0] + n]
        pos[0] += n + rng.randrange(50, 400)
        return s

    OA, P = take(21), take(22)
    w = [take(4) for _ in range(3)]
    INTO = take(4)
    A = ["#" + OA + w[0] + INTO + w[1] + P + take(10) + P + take(24),
         "#" + OA + w[1] + INTO + w[0] + P + take(12) + P + take(26),
         "#" + OA + take(9) + INTO + take(4) + P + take(17) + P + take(30)]
    OBC, OC, TC = take(5), take(15), take(95)
    X = take(28)
    TC = TC[:45] + X + TC[45 + 28:]
    c1 = "#" + OBC + OC + TC
    c2 = list("#" + OBC + OC + TC); c2[21:25] = list(take(5)); c2.insert(66, rng.choice(alpha))
    c3 = list("#" + OBC + OC + TC); c3.insert(47, rng.choice(alpha))
    C = [c1, "".join(c2), "".join(c3)]
    PB = take(20)
    B = ["#" + OBC + take(8) + PB + take(70), "#" + OBC + take(14) + PB + take(80),
         "#" + OBC + take(13) + PB + take(30) + X + take(30)]
    return [A[0], A[1], A[2], B[0], B[2], B[1], C[0], C[1], C[2]], P


def div_corpus(T, seed):
    rng = random.Random(seed)
    def take(n):
        i = rng.randrange(1000, len(T) - 2000); return T[i:i + n]
    pA, pBC, pE3C, pC, p12 = take(24), take(5), take(9), take(20), take(2)
    pBC = p12 + pBC[2:]; pA = p12 + pA[2:]; pE3C = pBC + pE3C[5:]; pC = pE3C + pC[9:]
    pre = [pA, pA, pA, pBC, pE3C, pBC, pC, pC, pC]
    return ["#" + pre[k] + take(LENS[k] - 1 - len(pre[k])) for k in range(9)]


def make_key(nsym, rng):
    beta = rng.permutation(N)
    binv = np.empty(N, np.int64); binv[beta] = np.arange(N)
    q = rng.choice(N, nsym, replace=False)
    Q = set(q.tolist())
    S = np.empty((nsym, N), np.int64)
    for s in range(nsym):
        idx = np.arange(N)
        m = int(rng.integers(N))
        while m == q[s] or int(binv[m]) in Q:
            m = int(rng.integers(N))
        idx[[q[s], m]] = idx[[m, q[s]]]
        S[s] = idx[beta]
    return q.astype(np.int64), S


def enc(msgs, alpha, q, S):
    return [[0] + xgak_encrypt(np.array([alpha.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in msgs]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    T0 = english_letters()[:400000]
    rnd = random.Random(31); rng = np.random.default_rng(31)
    print("pre-coding  iso   flat  0dbl  texture  fixpts  motif  ALL   | div. coinc.  same-Δ  med. chi²")
    for kind in ("anglais", "A1Z26", "polybe", "ternaire", "uniforme"):
        T, alpha = encode(T0, kind, rnd)
        base, P = build(T, alpha)
        E1, W1 = base[0], base[1]
        d0 = next(i for i in range(1, len(E1)) if E1[i] != W1[i])
        occ = [(k, i) for k in range(3) for i in range(1, len(base[k])) if base[k].startswith(P, i)]
        tb = [b for b in true_blocks(base) if b[4] >= 12]
        dc = div_corpus(T, 0)
        c = np.zeros(7); cs = ct = 0; agr = []; chis = []
        for _ in range(R):
            q, S = make_key(len(alpha), rng)
            pl = list(base); e5 = list(pl[8])
            for k in rnd.sample(range(21, 47), 5):
                e5[k] = rnd.choice([x for x in alpha if x != e5[k]])
            pl[8] = "".join(e5)
            C = enc(pl, alpha, q, S)
            segs = [C[k][i + 1:i + len(P)] for k, i in occ]
            iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
            chis.append(chi2(C)); a = chis[-1] <= EYES_CHI
            b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
            f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
            tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
            A0, B0 = enc([E1, W1], alpha, q, S)
            pe = all(A0[i] != B0[i] for i in range(d0, d0 + 4)) and all(A0[i] == B0[i] for i in range(d0 + 4, d0 + 8)) \
                and all(A0[i] != B0[i] for i in range(d0 + 8, d0 + 12)) and all(A0[i] == B0[i] for i in range(d0 + 12, d0 + 25))
            c += [iso, a, b, t, x, pe, iso and a and b and t and x and pe]
            tr, su = count(enc(dc, alpha, q, S), names, "toutes"); cs += su["proche"]; ct += tr["proche"]
            n, ag = agreement(enc(base, alpha, q, S), tb); agr.append(ag / max(n, 1))
        print(f"{kind:10s}  " + "  ".join(f"{v / R:.2f}" for v in c) + f"  |  {cs / ct:.3f}        {np.median(agr):.3f}   {np.median(chis):.0f}", flush=True)
