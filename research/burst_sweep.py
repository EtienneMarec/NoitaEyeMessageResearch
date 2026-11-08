"""Bursts of differences: base shuffle = rotation (cut c cards) and grouped read positions (§25).

Hypothesis: if β is a rotation (the deck stays "contiguous") and the read positions are grouped within a zone
of Z cards, the deck difference left by a substitution (a shifted contiguous segment, for reinsertion) crosses
the read zone as a block: we get BURSTS of differences separated by clean windows, like the obstacle
(4/4/4/13) and the stutter.

Family: read at q_p ∈ [0, Z), reinsertion of the read card at m_p (dest "dessous" = bottom, "profond" = deep,
"libre" = anywhere), then rotation by c.
Measures (300 keys per configuration, first trigram outside the deck, no homophones):
  exact 4/4/4/13 pattern under the "subst", "mots" (words) and "echange" (swap) readings
  (obstacle_pattern_test.pattern); fixed points <= 1% after an insertion, flat profile, 0 doubles, stutter
  texture (testbed base)."""
import sys
import numpy as np
from testbed import build_plaintexts, ALPHA
from explore import xgak_encrypt
from obstacle_pattern_test import variants, pattern
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from stats import load_eyes

N = 83


def make_key(c, Z, dest, rng):
    q = rng.choice(np.arange(0, Z), len(ALPHA), replace=False) if Z >= len(ALPHA) else None
    S = np.empty((len(ALPHA), N), np.int64)
    for s in range(len(ALPHA)):
        idx = list(range(N))
        card = idx.pop(int(q[s]))
        if dest == "dessous":
            m = N - 1
        elif dest == "profond":
            m = int(rng.integers(Z, N))
        else:
            m = int(rng.integers(0, N))
        idx.insert(m, card)
        idx = np.array(idx, np.int64)
        S[s] = np.roll(idx, -c)          # then rotation by c cards (D'[x] = D[S[x]])
    return q.astype(np.int64), S


def enc(plains, q, S):
    return [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in plains]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    rng = np.random.default_rng(17)
    print("c   Z   dest      motif: subst   words  swap    | fixpts  flat  0dbl  texture")
    best = []
    for c in (1, 2, 3, 5, 8, 13):
        for Z in (35, 50, 83):
            for dest in ("libre", "profond", "dessous"):
                if dest == "profond" and Z == 83:
                    continue
                h = np.zeros(3); o = np.zeros(4)
                for _ in range(R):
                    q, S = make_key(c, Z, dest, rng)
                    v = variants(base, rng)
                    A = enc([base[0]], q, S)[0]
                    for k, name in enumerate(("subst", "mots", "echange")):
                        B = enc([v[name]], q, S)[0]
                        h[k] += pattern(A, B)
                    if _ < 60:   # general criteria on 60 keys only (slower)
                        C = enc(base, q, S)
                        tt, fx = blocks_fixed(C)
                        f, r = texture(C[6], C[8])
                        o += [fx / tt <= 0.01, chi2(C) <= EYES_CHI,
                              sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0,
                              abs(f - f0) <= 0.15 and r >= r0 - 4]
                line = f"{c:2d}  {Z:2d}  {dest:8s}  {h[0] / R:.4f} {h[1] / R:.4f} {h[2] / R:.4f} | " + "  ".join(f"{x / 60:.2f}" for x in o)
                print(line, flush=True)
