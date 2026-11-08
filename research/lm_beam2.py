"""Beam over the plaintext, messages decoded IN PARALLEL (time step by time step) (§39).

Same model as lm_beam.py (known read positions, natural shuffles given, keyed starting deck),
but the processing order is (t, message): at time t, symbol t of each message is decoded. Cards
thus reappear from one message to another from the first positions on, which constrains the beam early.
Each hypothesis keeps a deck state (F, F⁻¹) and a language-model context PER message (int8)."""
import sys
import time
import numpy as np
from numba import njit
from lm_beam import train_trigram

N = 83


@njit(cache=True)
def beam_decode2(C, starts, lens, binv, sinv, lm, A, space, ndig, B, TR):
    M = starts.shape[0]
    L = C.shape[0]
    X = np.full((B, N), -1, np.int8); XI = np.full((B, N), -1, np.int8)
    F = np.zeros((B, M, N), np.int8); FI = np.zeros((B, M, N), np.int8)
    P2 = np.full((B, M), A, np.int8); P1 = np.full((B, M), A, np.int8)
    SC = np.zeros(B)
    TXT = np.full((B, L), -1, np.int8)
    ISTRUE = np.zeros(B, np.bool_); ISTRUE[0] = True; nIST = np.zeros(B, np.bool_)
    lost_step = -1; lost_rank = -1
    for m in range(M):
        for y in range(N):
            F[0, m, y] = y; FI[0, m, y] = y
    nb = 1
    MAXC = B * A
    cpar = np.empty(MAXC, np.int64); clet = np.empty(MAXC, np.int64); csc = np.empty(MAXC); cx = np.empty(MAXC, np.int64)
    nX = np.empty_like(X); nXI = np.empty_like(XI); nF = np.empty_like(F); nFI = np.empty_like(FI)
    nP2 = np.empty_like(P2); nP1 = np.empty_like(P1); nSC = np.empty_like(SC); nTXT = np.empty_like(TXT)
    tmax = 0
    for m in range(M):
        if lens[m] > tmax:
            tmax = lens[m]
    alive_steps = 0
    for t in range(tmax):
        for m in range(M):
            if t >= lens[m]:
                continue
            g = starts[m] + t
            c = C[g]
            nc = 0
            for b in range(nb):
                if t == 0:
                    # symbol 0 (number): no assignment (avoids the 9! equivalent digit permutations);
                    # the deck advances by one "letter" step; the card will be placed at its next appearance
                    cpar[nc] = b; clet[nc] = 26; cx[nc] = -1; csc[nc] = SC[b]; nc += 1
                    continue
                xc = X[b, c]
                if xc >= 0:
                    r = F[b, m, xc]
                    if r >= A:
                        continue
                    if t == 0 and not (26 <= r < 26 + ndig):
                        continue
                    if t > 0 and 26 <= r < 26 + ndig:
                        continue
                    cpar[nc] = b; clet[nc] = r; cx[nc] = -1
                    csc[nc] = SC[b] + lm[P2[b, m], P1[b, m], r]; nc += 1
                else:
                    lo = 26 if t == 0 else 0
                    hi = 26 + ndig if t == 0 else A
                    for l in range(lo, hi):
                        if t > 0 and 26 <= l < 26 + ndig:
                            continue
                        x0 = FI[b, m, l]
                        if XI[b, x0] >= 0:
                            continue
                        cpar[nc] = b; clet[nc] = l; cx[nc] = x0
                        csc[nc] = SC[b] + lm[P2[b, m], P1[b, m], l]; nc += 1
            if nc == 0:
                return SC[:1], TXT[:1], X[:1], 0, alive_steps, lost_step, lost_rank
            alive_steps += 1
            k = min(B, nc)
            fullorder = np.argsort(-csc[:nc])
            order = fullorder[:k]
            if lost_step < 0:
                rk = -1
                for ii in range(nc):
                    jj = fullorder[ii]
                    if ISTRUE[cpar[jj]] and (t == 0 or clet[jj] == TR[g]):
                        rk = ii
                        break
                if rk < 0 or rk >= k:
                    lost_step = alive_steps; lost_rank = rk
            for i in range(k):
                j = order[i]; b = cpar[j]; l = clet[j]
                nX[i] = X[b]; nXI[i] = XI[b]; nTXT[i] = TXT[b]; nF[i] = F[b]; nFI[i] = FI[b]
                nP2[i] = P2[b]; nP1[i] = P1[b]
                nIST[i] = ISTRUE[b] and (t == 0 or l == TR[g])
                if cx[j] >= 0:
                    nX[i, c] = cx[j]; nXI[i, cx[j]] = c
                nTXT[i, g] = l
                nP2[i, m] = P1[b, m] if t > 0 else A; nP1[i, m] = l if t > 0 else A; nSC[i] = csc[j]
                S = sinv if l == space else binv
                for y in range(N):
                    nF[i, m, y] = S[F[b, m, y]]
                for y in range(N):
                    nFI[i, m, nF[i, m, y]] = y
            nb = k
            X[:nb] = nX[:nb]; XI[:nb] = nXI[:nb]; F[:nb] = nF[:nb]; FI[:nb] = nFI[:nb]
            P2[:nb] = nP2[:nb]; P1[:nb] = nP1[:nb]; SC[:nb] = nSC[:nb]; TXT[:nb] = nTXT[:nb]; ISTRUE[:nb] = nIST[:nb]
    return SC[:nb], TXT[:nb], X[:nb], nb, alive_steps, lost_step, lost_rank


if __name__ == "__main__":
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    from keyed_deck_attack import tables, flatten
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    names, BS, inv = tables()
    rng = np.random.default_rng(14)
    alpha = tbs.ALPHA_S
    A = len(alpha); space = alpha.index("_")
    T = tbs.english_with_spaces()
    lm = train_trigram(T[:600000], alpha)
    pl = tbs.build_plaintexts(word_start=True)
    q = np.arange(A, dtype=np.int64)
    for bname, sname in (("rot1", "deal3fwd"),):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in alpha], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        C, starts, lens = flatten(msgs)
        t0 = time.time()
        TR = np.array([alpha.index(ch) for m in pl for ch in m], np.int8)
        SC, TXT, X, nb, steps, lost, lrank = beam_decode2(C, starts, lens, inv[bname].astype(np.int8), inv[sname].astype(np.int8), lm, A, space, 9, B, TR)
        print(f'   true branch lost at step {lost} (rank {lrank}, beam {B})')
        best = int(np.argmax(SC))
        dec = ["".join(alpha[v] if v >= 0 else "?" for v in TXT[best][starts[m]:starts[m] + lens[m]]) for m in range(len(pl))]
        ok = sum(a == b for d, p in zip(dec, pl) for a, b in zip(d, p))
        print(f"β={bname} σ={sname}, beam {B} ({time.time() - t0:.0f} s): {steps} live steps out of {len(C)}; {ok}/{len(C)} correct characters")
        for m in (0, 3, 6):
            print(f"   {m} decoded: {dec[m][:70]}")
            print(f"   {m} true   : {pl[m][:70]}", flush=True)
