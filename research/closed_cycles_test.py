"""Short closed cycles in the correspondences after an insertion: a discriminator between base shuffles.
Eyes (cycle_structure.py): 0 closed cycles in 10 blocks (~210 pairs); chains of length <= 7.
For each surviving family of the zoo, we measure on the testbed (2 blocks after a known insertion):
P(no closed cycle of length <= 4) and the length of the longest chain.
Family tokens: "retournement" = segment reversal, "aleatoire" = random, "tas3" = deal into 3 piles,
"coupe1" = cut 1 card, "miroir" = mirror, "cycle83" = one 83-cycle; "ordre" = order."""
import numpy as np
from family_zoo import make_key, encipher
from testbed import build_plaintexts, ALPHA

plains = build_plaintexts()
BLK = ((6, 50, 8, 51, 45), (6, 70, 7, 72, 25))


def short_cycles(C):
    n = 0; longest = 0
    for a, i, b, j, L in BLK:
        pairs = dict(zip(C[a][i:i + L], C[b][j:j + L]))
        for x in pairs:
            cur, k = x, 0
            while cur in pairs and k < 5:
                cur = pairs[cur]; k += 1
                if cur == x:
                    if k <= 4 and k >= 1 and not (k == 1):
                        n += 1
                    break
        # longest chain
        inv = {y: x for x, y in pairs.items()}
        for x in pairs:
            if x in inv:
                continue
            cur, k = x, 1
            while cur in pairs and pairs[cur] != x and k < 90:
                cur = pairs[cur]; k += 1
            longest = max(longest, k)
    return n, longest


rng = np.random.default_rng(5)
FAM = [("reinsertion", "aleatoire", 0), ("reinsertion", "riffle", 1), ("reinsertion", "tas3", 0),
       ("reinsertion", "cycle83", 1), ("retournement", "aleatoire", 0), ("retournement", "tas3", 1),
       ("retournement", "coupe1", 0), ("retournement", "riffle", 1), ("retournement", "miroir", 0)]
print("family                               P(no closed cycle 2..4)     longest chain (median)")
for t, b, o in FAM:
    ok, lg = 0, []
    for _ in range(40):
        reads, S = make_key(t, b, o, rng, len(ALPHA))
        C = encipher(plains, reads, S, False)
        n, l = short_cycles(C)
        ok += n == 0; lg.append(l)
    print(f"{t:13s} {b:10s} order {o}          {ok/40:.2f}                         {np.median(lg):.0f}")
print("eyes: no closed cycle, longest chain 7")
