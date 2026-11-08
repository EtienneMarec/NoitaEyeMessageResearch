"""Read position depends on context, shuffle depends on the letter (§25).

Idea: if the READ POSITION depends on the letter and the w-1 previous letters (homophone chosen by context),
but the deck SHUFFLE depends only on the letter, then a single substituted letter gives a burst of w
different outputs, after which the deck difference stays small (one single different shuffle):
clean resynchronisation. With w = 4, two substitutions would give exactly the obstacle's 4/4/4/13 pattern.
A repeated phrase stays isomorphic, except on its first w-1 columns (different context).

Model: deck of 83 cards. At each letter p, context ctx = (p_{t-w+1} .. p_t):
  output = D[q], q = slots[p][h(ctx) mod n_p] (n_p read slots per letter, ∝ frequency, 60 in total);
  then D ← D[S_p] with S_p = the letter's shuffle:
    'echange' (swap): swap (a_p, b_p) then β;  'reinsertion': card at a_p reinserted at b_p, then β.
First trigram outside the deck. Doubles avoided by redrawing (25 attempts).
Criteria: isomorphs (6 occurrences of P, without the first w-1 columns), flat profile, 0 doubles,
stutter (E5 = E4 with n substitutions in 21..46), fixed points <= 1%, EXACT 4/4/4/13 obstacle pattern
(two substitutions at d0 and d0+8) and, for reference, the loose criterion of §19."""
import sys
from collections import Counter
from itertools import combinations
import numpy as np
from testbed import build_plaintexts, english_letters, ALPHA
from family_zoo import beta_arr
from swap_model_test import chi2
from stutter_test import texture
from fixed_points_test import blocks_fixed
from obstacle_test import window_stats, d0
from fair_joint_test import rand_letter
from stutter_budget_test import stutter_edit
from obstacle_pattern_test import pattern
from architecture import iso_ok
from stats import load_eyes

N = 83
FREQ = Counter(english_letters()[:200000])
PR = (1, 31, 131, 1031, 7919)


def make_key(kind, nslots, rng):
    beta = beta_arr("aleatoire", rng)
    w = np.array([FREQ.get(ch, 0) for ch in ALPHA], float); w = w / w.sum() * (nslots - len(ALPHA))
    counts = [1 + int(x) for x in w]
    while sum(counts) < nslots:
        counts[int(np.argmax(w - np.array(counts) + 1))] += 1
    pos = rng.choice(np.arange(1, N), nslots, replace=False)
    slots, k = {}, 0
    for ch, c in zip(ALPHA, counts):
        slots[ch] = pos[k:k + c].tolist(); k += c
    S = {}
    for ch in ALPHA:
        a, b = rng.choice(N, 2, replace=False)
        idx = list(range(N))
        if kind == "echange":
            idx[a], idx[b] = idx[b], idx[a]
        else:
            c = idx.pop(a); idx.insert(b, c)
        S[ch] = np.array(idx, np.int64)[beta]
    return slots, S


def encrypt(msg, slots, S, w):
    D = np.arange(N)
    out = [0]
    for t in range(1, len(msg)):
        ch = msg[t]
        h = sum(PR[j] * ord(msg[t - j]) for j in range(1, w) if t - j >= 1)
        sl = slots[ch]
        out.append(int(D[sl[h % len(sl)]]))
        D = D[S[ch]]
    return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes()
    EYES_CHI = chi2(M); f0, r0 = texture(M[6], M[8])
    base = build_plaintexts()
    P = "AINYOUAMINUTEBUT"
    occ = [(k, i) for k in range(3) for i in range(len(base[k])) if base[k].startswith(P, i)]
    rng = np.random.default_rng(2025)
    print("shuffle       w  slots  iso   flat  0dbl  texture  fixpts    motif4/4/4/13  obst(loose)  ALL(motif)  ALL(loose)", flush=True)
    for kind in ("echange", "reinsertion"):
        for w in (1, 2, 4):
            for nslots in (60,):
                c = np.zeros(9)
                for _ in range(R):
                    pl = stutter_edit(list(base), 5, rng)
                    e1 = list(pl[0])
                    for k in (d0, d0 + 8):
                        e1[k] = rand_letter(rng, e1[k])
                    w1 = "".join(e1)
                    for attempt in range(25):
                        slots, S = make_key(kind, nslots, rng)
                        C = [encrypt(m, slots, S, w) for m in pl]
                        if sum(a == b for m in C for a, b in zip(m[1:], m[2:])) == 0:
                            break
                    segs = [C[k][i + w:i + len(P)] for k, i in occ]
                    iso = all(iso_ok(a, b) for a, b in combinations(segs, 2))
                    a = chi2(C) <= EYES_CHI
                    b = sum(x == y for m in C for x, y in zip(m[1:], m[2:])) == 0
                    f, r = texture(C[6], C[8]); t = abs(f - f0) <= 0.15 and r >= r0 - 4
                    tt, fx = blocks_fixed(C); x = fx / tt <= 0.01
                    W1 = encrypt(w1, slots, S, w)
                    pm = pattern(C[0], W1)
                    fr, run = window_stats([C[0], W1], 0, 1, d0 + 4, d0 + 24); ol = fr >= 0.8 and run >= 13
                    core = iso and a and b and t and x
                    c += [iso, a, b, t, x, pm, ol, core and pm, core and ol]
                print(f"{kind:12s} {w}  {nslots:3d}    " + "  ".join(f"{v / R:.2f}" for v in c), flush=True)
