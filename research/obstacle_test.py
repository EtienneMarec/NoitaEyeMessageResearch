"""Is the E1/W1 "obstacle" (Lymm: two 4-letter words swapped) compatible with the surviving families
(reinsertion / segment reversal + base shuffle β)?
Eyes: E1/W1, positions 29..49: 17 identical positions out of 21 (81%), of which 37..49 in a row (13).
Testbed: E1/W1 = "… w0 INTO w1 P …" versus "… w1 INTO w0 P …" (two 4-letter words swapped),
first symbol outside the deck. We measure the share of identical positions over the same relative window
(the 21 positions following the first swapped word + 4) and the longest identical run.
Variant: two SUBSTITUTIONS of a single letter (positions 25 and 33) instead of the word swap."""
import numpy as np
from family_zoo import make_key, encipher
from testbed import build_plaintexts, ALPHA

plains = build_plaintexts()
E1, W1 = plains[0], plains[1]
# first position where E1 and W1 differ (start of the swapped word)
d0 = next(i for i in range(1, len(E1)) if E1[i] != W1[i])


def window_stats(C, a, b, s, e):
    eq = [C[a][i] == C[b][i] for i in range(s, e + 1)]
    run = best = 0
    for x in eq:
        run = run + 1 if x else 0; best = max(best, run)
    return sum(eq) / len(eq), best


def variant_single(pl):
    """same text as E1 for W1, except two letters substituted at d0 and d0+8"""
    w = list(pl[0])
    for k in (d0, d0 + 8):
        w[k] = "Q" if w[k] != "Q" else "Z"
    out = list(pl); out[1] = "".join(w)
    # remove the other differences: W1 = E1 with two substitutions, over the whole length of E1
    return out


rng = np.random.default_rng(8)
FAM = [("reinsertion", "aleatoire", 0), ("reinsertion", "riffle", 1), ("reinsertion", "tas3", 0),
       ("retournement", "aleatoire", 0), ("retournement", "tas3", 1), ("reinsertion", "aucun", 0)]
print(f"window: positions {d0+4}..{d0+24} (eyes: 29..49, 81% identical, max run 13)")
print("family                          word swap: identical share / max run            two substitutions: share / run")
for t, b, o in FAM:
    sw, ss = [], []
    for _ in range(40):
        reads, S = make_key(t, b, o, rng, len(ALPHA))
        C = encipher(plains, reads, S, False)
        sw.append(window_stats(C, 0, 1, d0 + 4, d0 + 24))
        C2 = encipher(variant_single(plains), reads, S, False)
        ss.append(window_stats(C2, 0, 1, d0 + 4, d0 + 24))
    sw, ss = np.array(sw), np.array(ss)
    print(f"{t:12s} {b:9s} order {o}      {np.median(sw[:,0]):.2f} / {np.median(sw[:,1]):.0f}  "
          f"(P(>=0.8 and run>=13) = {np.mean((sw[:,0]>=0.8)&(sw[:,1]>=13)):.2f})        "
          f"{np.median(ss[:,0]):.2f} / {np.median(ss[:,1]):.0f}  (P = {np.mean((ss[:,0]>=0.8)&(ss[:,1]>=13)):.2f})")
