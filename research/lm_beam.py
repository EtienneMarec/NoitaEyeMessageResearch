"""Beam over the PLAINTEXT with a language model, known read positions (space model) (§39).

Assumed convention: the letter of rank k of the alphabet ALPHA is read at deck position k. Natural
shuffles given (β for letters and digits, σ for the space); keyed (unknown) starting deck.
Messages are decoded one after the other (the starting deck is shared). For each symbol:
  - card already placed: the read position r is forced; if r is not a rank of the alphabet, the hypothesis dies;
    otherwise the letter is ALPHA[r] (forced) and the language model scores it;
  - new card: each allowed letter ℓ is tried; it fixes the card's start (F_t⁻¹(ℓ)),
    which must be free; the language model scores ℓ.
Space decision ⇔ letter = "_". Language model: character trigrams (English with spaces).
Validation on the testbed with spaces."""
import sys
import math
import time
import numpy as np
from numba import njit

N = 83


def train_trigram(text, alpha, k=0.1):
    A = len(alpha)
    idx = {c: i for i, c in enumerate(alpha)}
    cnt = np.full((A + 1, A + 1, A), k)
    prev2, prev1 = A, A                          # A = start
    for ch in text:
        if ch not in idx:
            continue
        c = idx[ch]
        cnt[prev2, prev1, c] += 1
        prev2, prev1 = prev1, c
    return np.log(cnt / cnt.sum(axis=2, keepdims=True))


@njit(cache=True)
def beam_decode(C, starts, lens, binv, sinv, lm, A, space, ndig, B):
    """A = alphabet size (letters + digits + space); ranks: 0..25 letters, 26..26+ndig-1 digits, space."""
    M = starts.shape[0]
    X = np.full((B, N), -1, np.int64); XI = np.full((B, N), -1, np.int64)
    F = np.zeros((B, N), np.int64); FI = np.zeros((B, N), np.int64)
    P2 = np.full(B, A, np.int64); P1 = np.full(B, A, np.int64)
    SC = np.zeros(B)
    L = C.shape[0]
    TXT = np.full((B, L), -1, np.int8)
    nb = 1
    MAXC = B * A
    cpar = np.empty(MAXC, np.int64); clet = np.empty(MAXC, np.int64); csc = np.empty(MAXC); cx = np.empty(MAXC, np.int64)
    nX = np.empty_like(X); nXI = np.empty_like(XI); nF = np.empty_like(F); nFI = np.empty_like(FI)
    nP2 = np.empty_like(P2); nP1 = np.empty_like(P1); nSC = np.empty_like(SC); nTXT = np.empty_like(TXT)
    for m in range(M):
        for b in range(nb):
            for y in range(N):
                F[b, y] = y; FI[b, y] = y
            P2[b] = A; P1[b] = A
        for t in range(lens[m]):
            g = starts[m] + t
            c = C[g]
            nc = 0
            for b in range(nb):
                if X[b, c] >= 0:
                    r = F[b, X[b, c]]
                    if r >= A:
                        continue
                    if t == 0 and not (26 <= r < 26 + ndig):
                        continue
                    if t > 0 and 26 <= r < 26 + ndig:
                        continue
                    cpar[nc] = b; clet[nc] = r; cx[nc] = -1
                    csc[nc] = SC[b] + lm[P2[b], P1[b], r]; nc += 1
                else:
                    lo, hi = (26, 26 + ndig) if t == 0 else (0, A)
                    for l in range(lo, hi):
                        if t > 0 and 26 <= l < 26 + ndig:
                            continue
                        x0 = FI[b, l]
                        if XI[b, x0] >= 0:
                            continue
                        cpar[nc] = b; clet[nc] = l; cx[nc] = x0
                        csc[nc] = SC[b] + lm[P2[b], P1[b], l]; nc += 1
            if nc == 0:
                return SC[:1], TXT[:1], X[:1], 0
            k = min(B, nc)
            order = np.argsort(-csc[:nc])[:k]
            for i in range(k):
                j = order[i]; b = cpar[j]; l = clet[j]
                nX[i] = X[b]; nXI[i] = XI[b]; nTXT[i] = TXT[b]
                if cx[j] >= 0:
                    nX[i, c] = cx[j]; nXI[i, cx[j]] = c
                nTXT[i, g] = l
                nP2[i] = P1[b]; nP1[i] = l; nSC[i] = csc[j]
                S = sinv if l == space else binv
                for y in range(N):
                    nF[i, y] = S[F[b, y]]
                for y in range(N):
                    nFI[i, nF[i, y]] = y
            nb = k
            X[:nb] = nX[:nb]; XI[:nb] = nXI[:nb]; F[:nb] = nF[:nb]; FI[:nb] = nFI[:nb]
            P2[:nb] = nP2[:nb]; P1[:nb] = nP1[:nb]; SC[:nb] = nSC[:nb]; TXT[:nb] = nTXT[:nb]
    return SC[:nb], TXT[:nb], X[:nb], nb


if __name__ == "__main__":
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    from keyed_deck_attack import tables, flatten
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    names, BS, inv = tables()
    rng = np.random.default_rng(14)
    alpha = tbs.ALPHA_S                                 # A-Z, 1-9, _ (rank 35)
    A = len(alpha); space = alpha.index("_")
    T = tbs.english_with_spaces()
    lm = train_trigram(T[:600000], alpha)
    pl = tbs.build_plaintexts()
    q = np.arange(A, dtype=np.int64)
    for bname, sname in (("rot1", "deal3fwd"), ("outshuffle", "milk")):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        t0 = time.time()
        SC, TXT, X, nb = beam_decode(C, starts, lens, inv[bname], inv[sname], lm, A, space, 9, B)
        best = int(np.argmax(SC))
        dec = "".join(alpha[v] if v >= 0 else "?" for v in TXT[best])
        truth = "".join(pl)
        ok = sum(a == b for a, b in zip(dec, truth))
        print(f"β={bname} σ={sname}, beam {B} ({time.time() - t0:.0f} s): {ok}/{len(truth)} correct characters")
        print("   decoded:", dec[:110])
        print("   true   :", truth[:110], flush=True)
