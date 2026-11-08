"""Probability of the EXACT PATTERN of the E1/W1 obstacle under several readings of the plaintext (§24).

Eyes (0-indexed): positions 25-28 different, 29-32 identical, 33-36 different, 37-49 identical
(4/4/4/13 pattern described by Lymm). Testbed: d0 = first E1/W1 difference; we require
  d0..d0+3 all different, d0+4..d0+7 all identical, d0+8..d0+11 all different, d0+12..d0+24 all identical.
Readings of W1 (relative to E1) (tokens):
  subst   : two one-letter substitutions, at d0 and d0+8 (the rest of the bursts comes from the hidden state);
  mots    : two DIFFERENT 4-letter words (letters drawn at random) at d0..d0+3 and d0+8..d0+11;
  echange : the two 4-letter words swapped (Lymm's reading; this is the base testbed).
Models: small swaps + homophones from the previous letter + no-doubles rule (k = 1; 60 slots),
reinsertion / segment reversal + random β (free reach), with or without these homophones."""
import sys
import numpy as np
from testbed import build_plaintexts, ALPHA
from obstacle_test import d0
from fair_joint_test import rand_letter
from context_homophone_test import enc_all, make_key as ctx_key
from swap_context_test import make_key as swap_key
from family_zoo import make_key as zoo_key, encipher


def variants(base, rng):
    E1 = base[0]
    out = {}
    w = list(E1)
    for k in (d0, d0 + 8):
        w[k] = rand_letter(rng, w[k])
    out["subst"] = "".join(w)
    w = list(E1)
    for k in list(range(d0, d0 + 4)) + list(range(d0 + 8, d0 + 12)):
        w[k] = rand_letter(rng, w[k])
    out["mots"] = "".join(w)
    out["echange"] = base[1]
    return out


def pattern(A, B):
    d = [A[i] != B[i] for i in range(d0, d0 + 25)]
    return all(d[0:4]) and not any(d[4:8]) and all(d[8:12]) and not any(d[12:25])


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    base = build_plaintexts()
    # check that the testbed's "echange" (swap) reading has the form word / 4 letters / word
    rng = np.random.default_rng(4)
    MODELS = [("swaps k=1 + homoph. 60 + no doubles", "swap"),
              ("reinsertion + random β, homoph. 60", "ctx_re"),
              ("segment reversal + random β, homoph. 60", "ctx_ret"),
              ("reinsertion + random β, no homoph.", "zoo_re"),
              ("segment reversal + random β, no homoph.", "zoo_ret")]
    print(f"{R} keys per model; exact 4/4/4/13 pattern; frequency (and number of successes)")
    print("model                                          subst          mots           echange")
    for lab, kind in MODELS:
        hits = {"subst": 0, "mots": 0, "echange": 0}
        for _ in range(R):
            v = variants(base, rng)
            if kind == "swap":
                slots, reads, S = swap_key(1, "aleatoire", 60, rng, nodouble=True)
                enc = lambda m: enc_all([base[0], m], slots, reads, S)
            elif kind.startswith("ctx"):
                slots, reads, S = ctx_key("reinsertion" if kind == "ctx_re" else "retournement", "aleatoire", 82, 60, rng)
                enc = lambda m: enc_all([base[0], m], slots, reads, S)
            else:
                reads, S = zoo_key("reinsertion" if kind == "zoo_re" else "retournement", "aleatoire", 0, rng, len(ALPHA))
                enc = lambda m: encipher([base[0], m], reads, S, False)
            for name, w1 in v.items():
                A, B = enc(w1)
                hits[name] += pattern(A, B)
        print(f"{lab:45s}  " + "  ".join(f"{hits[k] / R:.4f} ({hits[k]:3d})" for k in ("subst", "mots", "echange")), flush=True)
