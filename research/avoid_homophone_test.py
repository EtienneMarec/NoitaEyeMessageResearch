"""Homophones chosen by an EQUALITY rule with the last outputs (§28).

Rule: letter p has n_p slots (read positions q_{p,1..n}) in a fixed order; we take the first slot whose card is
not among the last K outputs (if all are, the first one). The choice depends only on equalities between cards:
it is invariant under relabelling, so a repeated phrase stays isomorphic once its first K symbols are past. It
depends neither on the position nor on the differing text.
Update: swap (q_slot, m_slot) then β (Lymm's model, k = 1, per slot).
K = 1 forbids doubles; K = 2..4 also avoids short repeats.

Criteria (testbed without spaces, 100 keys): isomorphs (occurrences of P, without the first K columns), flat,
0 doubles, stutter (n = 5), fixed points, exact obstacle pattern ("swap" reading), coincidences after a
divergence (eyes 0.040), "same Δ" agreement (eyes 0.056). Token "aleatoire" = random β."""
import sys
from collections import Counter
from itertools import combinations
import numpy as np
from testbed import build_plaintexts, english_letters, ALPHA
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_pattern_test import variants, pattern
from stutter_budget_test import stutter_edit
from same_delta_models import agreement
from testkey import true_blocks
from lineage_coincidence import count
from divergence_models import corpus
from small_order_test import beta_order
from architecture import iso_ok
from stats import load_eyes

N = 83
FREQ = Counter(english_letters()[:200000])


def make_key(nslots, bkind, rng):
    beta = rng.permutation(N) if bkind == "aleatoire" else beta_order(int(bkind), rng)
    w = np.array([FREQ.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (nslots - len(ALPHA))
    counts = [1 + int(x) for x in w]
    while sum(counts) < nslots:
        counts[int(np.argmax(w - np.array(counts) + 1))] += 1
    pos = rng.choice(N, nslots, replace=False)
    slots, k = {}, 0
    for ch, c in zip(ALPHA, counts):
        slots[ch] = [int(x) for x in pos[k:k + c]]; k += c
    S = {}
    for ch in ALPHA:
        for qq in slots[ch]:
            idx = np.arange(N)
            m = int(rng.integers(N))
            while m == qq:
                m = int(rng.integers(N))
            idx[[qq, m]] = idx[[m, qq]]
            S[qq] = idx[beta]
    return slots, S


def encrypt(msg, slots, S, K):
    D = np.arange(N)
    out = [0]
    for ch in msg[1:]:
        recent = out[-K:] if K > 0 else []
        qs = slots[ch]
        q = next((x for x in qs if D[x] not in recent), qs[0])
        out.append(int(D[q]))
        D = D[S[q]]
    return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    tb = [b for b in true_blocks(base) if b[4] >= 12]
    div_pl = corpus(english_letters(), 0)
    P = "AINYOUAMINUTEBUT"
    occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
    rng = np.random.default_rng(28)
    print("β          slots  K   iso   flat  0dbl  texture  fixpts  motif  ALL   | div. coinc.  same-Δ  med. chi²")
    for bkind in ("aleatoire", "8"):
        for nslots in (35, 60):
            for K in ((1,) if nslots == 35 else (1, 2, 4)):
                c = np.zeros(7); cs = ct = 0; agr = []; chis = []
                for _ in range(R):
                    slots, S = make_key(nslots, bkind, rng)
                    pl = stutter_edit(list(base), 5, rng)
                    C = [encrypt(m, slots, S, K) for m in pl]
                    segs = [C[k][i + 1 + K:i + len(P)] for k, i in occ]
                    iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                    chis.append(chi2(C)); a = chis[-1] <= EYES_CHI
                    b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    v = variants(base, rng)
                    pe = pattern(encrypt(base[0], slots, S, K), encrypt(v["echange"], slots, S, K))
                    c += [iso, a, b, t, x, pe, iso and a and b and t and x and pe]
                    tr, su = count([encrypt(m, slots, S, K) for m in div_pl], names, "toutes"); cs += su["proche"]; ct += tr["proche"]
                    n, ag = agreement([encrypt(m, slots, S, K) for m in base], tb); agr.append(ag / max(n, 1))
                print(f"{bkind:9s}  {nslots:3d}   {K}  " + "  ".join(f"{v / R:.2f}" for v in c)
                      + f"  |  {cs / ct:.3f}        {np.median(agr):.3f}   {np.median(chis):.0f}", flush=True)
