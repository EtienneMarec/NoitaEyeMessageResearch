"""Control: does the keyword_decks battery detect a keyword deck on test messages?"""
import numpy as np
import keyword_decks as K
from testbed import build_plaintexts, make_key, encrypt_all, ALPHA
from explore import xgak_encrypt
from deckcipher import N
plains = build_plaintexts()
P = dict(K.perms_for("LUMIKKI"))["ascii"]
key = make_key(3)
ident = np.arange(N)
C1 = encrypt_all(plains, key, ident, 1, 0, D0=P)
print("starting deck LUMIKKI:", K.battery(P, [np.array(m) for m in C1]))
reads = np.array([key[ch] for ch in ALPHA]); S = np.empty((len(ALPHA), N), np.int64)
for s, q in enumerate(reads):
    idx = list(range(N)); c = idx.pop(int(q)); idx.insert(int(P[q]), c); S[s] = idx
C2 = [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]]), reads, S).tolist() for m in plains]
print("reinsertion table LUMIKKI:", K.battery(P, [np.array(m) for m in C2]))
print("control (random permutation):", K.battery(np.random.default_rng(0).permutation(N), [np.array(m) for m in C2]))
