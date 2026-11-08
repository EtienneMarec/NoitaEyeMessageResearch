"""Model "shared shuffle + special letters" (§26).

Idea: the letter only chooses the card read (position q_p); the deck then undergoes the SAME shuffle β for
almost all letters. Only a few "special" letters (e.g. the space, or a frequent letter)
apply a different shuffle σ_s. Consequences in an XGAK:
  - substitution between ordinary letters: σ_b σ_a⁻¹ = id, so no deck difference, exact and immediate
    resynchronisation (the obstacle's 4/4/4/13 pattern comes out deterministically);
  - insertion: π = conjugate of σ_x, with no fixed point if β has none (§13);
  - difference involving a special letter: real deck difference (stutter).
With no special letter, this is the progressive alphabet (refuted, §23): control.

Criteria: flat profile, 0 doubles, stutter (E5 = E4 with n = 5 random substitutions in 21..46),
fixed points <= 1%, exact obstacle pattern (readings subst / mots (words) / echange (swap)), and agreement rate of the
"same shift" test (eyes: 2/36 = 0.056). First trigram outside the deck, no homophones, R keys."""
import sys
from collections import Counter
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
from stats import load_eyes

N = 83


def derangement(rng):
    while True:
        b = rng.permutation(N)
        if not (b == np.arange(N)).any():
            return b


def make_key(special, skind, rng):
    beta = derangement(rng)
    q = rng.choice(np.arange(N), len(ALPHA), replace=False)
    S = np.empty((len(ALPHA), N), np.int64)
    for i, ch in enumerate(ALPHA):
        if ch in special:
            if skind == "aleatoire":
                S[i] = rng.permutation(N)
            else:  # β then k random swaps (small difference)
                idx = np.arange(N)
                for _ in range(int(skind)):
                    a, b = rng.choice(N, 2, replace=False)
                    idx[[a, b]] = idx[[b, a]]
                S[i] = idx[beta]
        else:
            S[i] = beta
    return q.astype(np.int64), S


def enc(plains, q, S):
    return [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in plains]


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    tb = [b for b in true_blocks(base) if b[4] >= 12]
    freq = Counter(english_letters()[:200000])
    rng = np.random.default_rng(26)
    CASES = [("", "aleatoire"), ("E", "aleatoire"), ("ET", "aleatoire"), ("ETAO", "aleatoire"),
             ("ETAOINS", "aleatoire"), ("E", "8"), ("ETAO", "8"), ("ETAO", "20"), ("JQXZ", "aleatoire")]
    print("special    σ_s        share  flat  0dbl  texture  fixpts  subst  words swap     | ALL(motif words)  same-Δ agreement (med.)")
    for special, skind in CASES:
        share = sum(freq[c] for c in special) / sum(freq.values())
        c = np.zeros(8); agr = []
        for _ in range(R):
            for attempt in range(25):
                q, S = make_key(special, skind, rng)
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
            pm = [pattern(A0, enc([v[k]], q, S)[0]) for k in ("subst", "mots", "echange")]
            n, ag = agreement(enc(base, q, S), tb)
            agr.append(ag / max(n, 1))
            c += [a, b, t, x] + pm + [a and b and t and x and pm[1]]
        print(f"{special or '-':8s}  {skind:9s}  {share:.2f}   " + "  ".join(f"{v / R:.2f}" for v in c[:7])
              + f"  |  {c[7] / R:.2f}              {np.median(agr):.3f}", flush=True)
