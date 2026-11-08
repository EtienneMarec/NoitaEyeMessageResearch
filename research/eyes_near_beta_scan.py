"""Attack on the eyes in the "space ≈ β" regime (k ≤ 2 swaps), the only regime where the attack works on the testbed (§41).

Approximation σ := β: each symbol applies β, output c_t = D0[β^t(q_x)] (keyed starting deck D0).
With D0 free, two conjugate β give the same cipher: only the CYCLE TYPE of β matters. We sweep the
cycle types of the 115 natural shuffles (excluding the identity) with the keyed-deck EM (keyed_deck_attack.attack,
σ = β) and record the entropy H of the read positions (truth ≈ 4.1 bits; failure ≈ 5.5–6.2).
  1. Calibration on the testbed: β = deal3fwd, k = 0, 1, 2 (real σ = τ_k ∘ β, attack with σ := β).
  2. Control: testbed encrypted with the space model at k = 16 and random β (no natural type is right).
  3. Eyes (first trigram inside the deck).
Usage: python eyes_near_beta_scan.py [R]"""
import sys
from collections import Counter
import numpy as np
from keyed_deck_attack import tables, flatten, decode, attack, N
from moderate_space_attack import make_case, inv
from moderate_space_curriculum import letter_acc
from stats import load_eyes
import testbed_spaces as tbs
import space_model_test as sm
from explore import xgak_encrypt


def cycle_type(p):
    seen = np.zeros(N, bool); out = []
    for i in range(N):
        if not seen[i]:
            j, L = i, 0
            while not seen[j]:
                seen[j] = True; j = p[j]; L += 1
            out.append(L)
    return tuple(sorted(out, reverse=True))


def short(ct):
    c = Counter(ct)
    return " ".join(f"{L}^{m}" if m > 1 else f"{L}" for L, m in sorted(c.items(), reverse=True))


def scan(msgs, reps, INV, rng, R):
    C, st, ln = flatten(msgs)
    res = []
    for name in reps:
        h, x, qs = attack(C, st, ln, INV[name], INV[name], True, rng, restarts=R)
        res.append((h, name))
    return sorted(res)


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rng = np.random.default_rng(41)
    names, BS, INV = tables()
    types = {}
    for nm in names:
        if nm == "id":
            continue
        types.setdefault(cycle_type(BS[nm]), nm)
    reps = list(types.values())
    print(f"{len(reps)} distinct cycle types among 115 natural shuffles", flush=True)
    pl = tbs.build_plaintexts(); plain = "".join(pl)
    print("1. calibration (testbed, β = deal3fwd, attack with σ := β):", flush=True)
    for k in (0, 1, 2):
        msgs, sS, x_true, qs = make_case(pl, BS["deal3fwd"], k, rng)
        C, st, ln = flatten(msgs)
        h, x, q = attack(C, st, ln, INV["deal3fwd"], INV["deal3fwd"], True, rng, restarts=R)
        r, _ = decode(C, st, ln, x, INV["deal3fwd"], INV["deal3fwd"], -1, True)
        print(f"   k={k}: H = {h:.2f}, letter accuracy {letter_acc(r, plain):.2f}", flush=True)
    print("2. control (testbed, space model k = 16, random β): 5 best types", flush=True)
    for s in range(2):
        q, S = sm.make_key("_", "16", True, np.random.default_rng(100 + s))
        msgs = [xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
        res = scan(msgs, reps, INV, rng, R)
        print(f"   control {s}: " + "; ".join(f"{n} {h:.2f}" for h, n in res[:5]), flush=True)
    print("3. eyes: all types", flush=True)
    _, M = load_eyes()
    res = scan(M, reps, INV, rng, R)
    for h, n in res:
        print(f"   {n:14s} H = {h:.2f}   type {short(cycle_type(BS[n]))}", flush=True)
