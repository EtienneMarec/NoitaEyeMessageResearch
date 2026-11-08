"""Lymm's model with a base shuffle β of SMALL ORDER (β^8 = id) (§27).

Argument: σ_p = β∘τ_p, τ_p = small swap. The product of a text is β^n · ∏ (conjugates of τ by powers
of β depending on the position mod order(β)). If β^8 = id, two 4-letter words separated by 4 letters
(positions i and i+8) are conjugated by the same power of β; disjoint swaps commute, so swapping
the two words exactly cancels the deck difference: EXACT resynchronisation of the obstacle (4/4/4/13).

β tested: order 2 (random involution with 1 fixed point), order 4, order 8 (cycles of lengths 8/4/2/1,
as few fixed points as possible: 83 is odd, so at least one), mirror ("miroir", order 2), and random β (control).
τ_p: swap (q_p, m_p); k = 1. No homophones (they would break the exact obstacle), first trigram outside the deck.
Criteria: flat profile, 0 doubles, stutter (n = 5 substitutions), fixed points <= 1%, exact pattern of the
obstacle (testbed's "swap" reading: words at d0..d0+3 and d0+8..d0+11), coincidences after a divergence
(divergence_models), "same Δ" agreement."""
import sys
import numpy as np
from testbed import build_plaintexts, english_letters, ALPHA
from explore import xgak_encrypt
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_pattern_test import variants, pattern
from stutter_budget_test import stutter_edit
from same_delta_models import agreement
from testkey import true_blocks
from lineage_coincidence import count
from divergence_models import corpus
from stats import load_eyes

N = 83


def beta_order(order, rng):
    """random permutation whose cycles have lengths dividing `order` (largest possible), 1 fixed point"""
    perm = list(rng.permutation(N))
    b = np.arange(N)
    i = 0
    lens = []
    rest = N
    while rest > 0:
        L = order if rest - order >= 1 or rest == order else (rest if rest in (1, 2, 4, 8) and order % rest == 0 else 1)
        if rest - L < 0:
            L = 1
        lens.append(L); rest -= L
    for L in lens:
        cyc = perm[i:i + L]; i += L
        for a, c in zip(cyc, cyc[1:] + cyc[:1]):
            b[a] = c
    return b


def make_key(bkind, k, rng, nodouble=False):
    """nodouble: design rule — the card read (sent to m then moved by β) never lands
    on a read position: it arrives at β⁻¹(m), which is forced outside Q (convention D'[x] = D[S[x]])."""
    if bkind == "aleatoire":
        beta = rng.permutation(N)
    elif bkind == "miroir":
        beta = np.arange(N)[::-1].copy()
    else:
        beta = beta_order(int(bkind), rng)
    q = rng.choice(np.arange(N), len(ALPHA), replace=False)
    Q = set(q.tolist())
    binv = np.empty(N, np.int64); binv[beta] = np.arange(N)
    S = np.empty((len(ALPHA), N), np.int64)
    for s in range(len(ALPHA)):
        idx = np.arange(N)
        m = int(rng.integers(N))
        while m == q[s] or (nodouble and int(binv[m]) in Q):
            m = int(rng.integers(N))
        idx[[q[s], m]] = idx[[m, q[s]]]
        for _ in range(k - 1):
            a, b = rng.choice(N, 2, replace=False); idx[[a, b]] = idx[[b, a]]
        S[s] = idx[beta]
    return q.astype(np.int64), S


def enc(plains, q, S):
    return [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in plains]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    tb = [b for b in true_blocks(base) if b[4] >= 12]
    div_pl = corpus(english_letters(), 0)
    rng = np.random.default_rng(27)
    print("β          k   flat  0dbl  texture  fixpts  motif(swap)     motif(words) ALL   | coinc. after div.  same-Δ agreement")
    for bkind in ("2", "4", "8", "miroir", "aleatoire"):
        for k in (1, 2):
            c = np.zeros(7); co_s = co_t = 0; agr = []
            for _ in range(R):
                for attempt in range(25):
                    q, S = make_key(bkind, k, rng)
                    pl = stutter_edit(list(base), 5, rng)
                    C = enc(pl, q, S)
                    if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                        break
                a = chi2(C) <= EYES_CHI
                b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                v = variants(base, rng)
                A0 = enc([base[0]], q, S)[0]
                pe = pattern(A0, enc([v["echange"]], q, S)[0]); pm = pattern(A0, enc([v["mots"]], q, S)[0])
                c += [a, b, t, x, pe, pm, a and b and t and x and pe]
                tr, su = count(enc(div_pl, q, S), names, "toutes"); co_s += su["proche"]; co_t += tr["proche"]
                n, ag = agreement(enc(base, q, S), tb); agr.append(ag / max(n, 1))
            print(f"{bkind:9s}  {k}   " + "  ".join(f"{v / R:.2f}" for v in c) + f"  |  {co_s / co_t:.3f}             {np.median(agr):.3f}", flush=True)
