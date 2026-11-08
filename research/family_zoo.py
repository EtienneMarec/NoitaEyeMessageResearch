"""Zoo of structured XGAK families, judged on ALL the criteria from the eyes (testbed, no homophones).

Step for letter p: output = D[q_p] (order "τ then β") or output = (D[β])[q_p] (order "β then τ"),
then the card read undergoes τ_p, and the whole deck undergoes β.
τ_p (what becomes of the card read, read position q_p, letter-specific parameter m_p) (tokens):
  reinsertion (removed then reinserted at m_p) · dessus (reinserted at 0, top) · dessous (at 82, bottom)
  echange (swap with position m_p) · echange_dessus (swap with position 0) · retournement (segment q_p..m_p reversed)
  coupe (cut so that q_p comes on top) · aucune (none)
β: aucun (none) · coupe1 (cut 1) · riffle (out-shuffle) · tas3 (deal into 3 piles) · cycle83 (random 83-cycle) · aleatoire (random permutation) · miroir (mirror)
First trigram: outside the deck (all messages start from the same state) or inside (digit 1..9).
Criteria:
  flat: chi² of the gap profile <= 63.2 · doubles: 0 (up to 25 keys are tried to find one without
  doubles) · texture: E4/E5 21..46 identical share 0.42 ± 0.15 and >= 7 runs · fixed points after an insertion
  <= 1% · sync (first trigram inside only): >= 15 identical positions in both groups.
"""
import sys
import time
import numpy as np
from explore import xgak_encrypt
from testbed import build_plaintexts, ALPHA
from swap_model_test import chi2, prefix_sync
from stutter_test import texture
from fixed_points_test import blocks_fixed
from deckcipher import base_shuffles
from stats import load_eyes

N = 83
TAUS = ["reinsertion", "dessus", "dessous", "echange", "echange_dessus", "retournement", "coupe", "aucune"]
BETAS = ["aucun", "coupe1", "riffle", "tas3", "cycle83", "aleatoire", "miroir"]
BS = base_shuffles()


def tau_arr(kind, q, m):
    idx = list(range(N))
    if kind == "reinsertion":
        c = idx.pop(q); idx.insert(m, c)
    elif kind == "dessus":
        c = idx.pop(q); idx.insert(0, c)
    elif kind == "dessous":
        c = idx.pop(q); idx.append(c)
    elif kind == "echange":
        idx[q], idx[m] = idx[m], idx[q]
    elif kind == "echange_dessus":
        idx[q], idx[0] = idx[0], idx[q]
    elif kind == "retournement":
        a, b = min(q, m), max(q, m)
        idx[a:b + 1] = idx[a:b + 1][::-1]
    elif kind == "coupe":
        idx = idx[q:] + idx[:q]
    return np.array(idx, np.int64)


def beta_arr(kind, rng):
    if kind == "aucun":
        return np.arange(N)
    if kind == "coupe1":
        return (np.arange(N) + 1) % N
    if kind == "riffle":
        return BS["outshuffle"]
    if kind == "tas3":
        return BS["deal3fwd"]
    if kind == "miroir":
        return np.arange(N)[::-1].copy()
    if kind == "cycle83":
        o = rng.permutation(N); b = np.empty(N, np.int64); b[o] = np.roll(o, 1); return b
    return rng.permutation(N)


def make_key(tkind, bkind, order, rng, nsym):
    beta = beta_arr(bkind, rng)
    q = rng.choice(np.arange(1, N), nsym, replace=False)
    m = rng.integers(0, N, nsym)
    S = np.empty((nsym, N), np.int64)
    reads = np.empty(nsym, np.int64)
    for s in range(nsym):
        t = tau_arr(tkind, int(q[s]), int(m[s]))
        if order == 0:           # read at q, then τ, then β
            S[s] = t[beta]; reads[s] = q[s]
        else:                    # β, read at q, then τ  <=>  read at β[q], S = β∘τ
            S[s] = beta[t]; reads[s] = beta[q[s]]
    return reads, S


def encipher(plains, reads, S, first_inside):
    out = []
    for j, m in enumerate(plains):
        if first_inside:
            seq = np.array([ALPHA.index(ch) for ch in m], np.int64)
            out.append(xgak_encrypt(seq, reads, S).tolist())
        else:
            seq = np.array([ALPHA.index(ch) for ch in m[1:]], np.int64)
            out.append([0] + xgak_encrypt(seq, reads, S).tolist())
    return out


def doubles(C, first_inside):
    return sum(a == b for m in C for a, b in zip(m[(0 if first_inside else 1):], m[(1 if first_inside else 2):]))


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    names, M = load_eyes()
    EYES_CHI = chi2(M)
    f0, r0 = texture(M[6], M[8])
    plains = build_plaintexts()
    rng = np.random.default_rng(2026)
    t0 = time.time()
    print(f"eyes: chi² {EYES_CHI:.1f}, texture {f0:.2f}/{r0}, 0 fixed points/210, sync [24, 20]; {R} keys per family", flush=True)
    print("first    τ               β          order  flat  0dbl  texture  fixpts    sync     ALL", flush=True)
    rows = []
    for first_inside in (False, True):
        for tkind in TAUS:
            for bkind in BETAS:
                for order in (0, 1):
                    if bkind == "aucun" and order == 1:
                        continue
                    c = dict(flat=0, dbl=0, tex=0, fx=0, sync=0, all=0)
                    for _ in range(R):
                        C = None
                        for attempt in range(25):
                            reads, S = make_key(tkind, bkind, order, rng, len(ALPHA))
                            C = encipher(plains, reads, S, first_inside)
                            if doubles(C, first_inside) == 0:
                                break
                        ok_d = doubles(C, first_inside) == 0
                        ok_p = chi2(C) <= EYES_CHI
                        f, r = texture(C[6], C[8]); ok_t = abs(f - f0) <= 0.15 and r >= r0 - 4
                        tt, fx = blocks_fixed(C); ok_f = fx / tt <= 0.01
                        ok_s = (min(prefix_sync(C)) >= 15) if first_inside else True
                        c["flat"] += ok_p; c["dbl"] += ok_d; c["tex"] += ok_t; c["fx"] += ok_f; c["sync"] += ok_s
                        c["all"] += ok_p and ok_d and ok_t and ok_f and ok_s
                    row = (("inside" if first_inside else "outside"), tkind, bkind, order, *(c[k] / R for k in ("flat", "dbl", "tex", "fx", "sync", "all")))
                    rows.append(row)
                    print(f"{row[0]:7s}  {tkind:14s}  {bkind:9s}  {order}      {row[4]:.2f}  {row[5]:.2f}  {row[6]:.2f}     "
                          f"{row[7]:.2f}      {row[8]:.2f}     {row[9]:.2f}   ({time.time()-t0:.0f} s)", flush=True)
    rows.sort(key=lambda r: -r[-1])
    print("\nFamilies passing ALL criteria (P(ALL) > 0):")
    for r in rows:
        if r[-1] > 0:
            print("  ", r)
