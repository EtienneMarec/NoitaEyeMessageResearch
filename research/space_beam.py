"""Beam search with the SPACES as unknowns (space model, β and σ known, keyed starting deck) (§34).

State of a hypothesis: start position x_c of the cards already "placed" (otherwise -1), "held" cards
(seen once, position unknown; the time t1 of their first read is kept), space/letter decisions
of each step, counts of read positions. For the current message, F (start → current position) and Finv.
At each symbol c_t:
  - placed card: forced read position r = F[x_c]; forced decision (space iff r = q_space);
  - new card: two-way branch. "Space": it is at q_space (if that start is free), it is
    placed at once. "Letter": it is put on hold;
  - held card reappearing: its read position r is chosen among the positions whose start is free.
    We go back in time (a single position tracked) to the start x, then forward to t1 to find
    its first read r1, which must be ≠ q_space (it had been decided "letter").
Score: sequential Dirichlet log-likelihood of the read positions (small α: few positions).
q_space is given (validation) or scanned. Convention: D'[x] = D[S[x]], position y → Sinv[y]."""
import sys
import math
import numpy as np
from numba import njit

N = 83
ALPHA = 0.05


@njit(cache=True)
def lp(cnt, n, r):
    return math.log((cnt[r] + ALPHA) / (n + N * ALPHA))


@njit(cache=True)
def run_beam(C, msg_of, starts, binv, sinv, bfw, sfw, qs, B, xt, dt):
    L = C.shape[0]
    M = starts.shape[0]
    # beam states
    X = np.full((B, N), -1, np.int64); XI = np.full((B, N), -1, np.int64)   # card -> start, start -> card
    T1 = np.full((B, N), -1, np.int64)                                       # held card: time t1
    CNT = np.zeros((B, N), np.int64); NN = np.zeros(B, np.int64)
    DEC = np.zeros((B, L), np.int8)
    F = np.zeros((B, N), np.int64); FI = np.zeros((B, N), np.int64)
    SC = np.zeros(B)
    nb = 1
    alive = np.zeros(L, np.int64)
    for y in range(N):
        F[0, y] = y; FI[0, y] = y
    # candidate buffers
    MAXC = B * 90
    cpar = np.empty(MAXC, np.int64); ctyp = np.empty(MAXC, np.int64); cr = np.empty(MAXC, np.int64); csc = np.empty(MAXC)
    cx = np.empty(MAXC, np.int64); cr1 = np.empty(MAXC, np.int64)
    nX = np.empty_like(X); nXI = np.empty_like(XI); nT1 = np.empty_like(T1); nCNT = np.empty_like(CNT); nNN = np.empty_like(NN)
    nDEC = np.empty_like(DEC); nF = np.empty_like(F); nFI = np.empty_like(FI); nSC = np.empty_like(SC)
    for g in range(L):
        m = msg_of[g]
        if g == starts[m]:
            for b in range(nb):
                for y in range(N):
                    F[b, y] = y; FI[b, y] = y
        c = C[g]
        nc = 0
        for b in range(nb):
            if X[b, c] >= 0:                      # placed card: forced read
                r = F[b, X[b, c]]
                cpar[nc] = b; ctyp[nc] = 0; cr[nc] = r; csc[nc] = SC[b] + lp(CNT[b], NN[b], r); nc += 1
            elif T1[b, c] < 0:                    # new card
                # "space": it is at qs; its start FI[qs] must be free
                x0 = FI[b, qs]
                if XI[b, x0] < 0:
                    cpar[nc] = b; ctyp[nc] = 1; cr[nc] = qs; cx[nc] = x0; csc[nc] = SC[b] + lp(CNT[b], NN[b], qs); nc += 1
                # "letter": on hold (neutral score, adjusted at resolution)
                cpar[nc] = b; ctyp[nc] = 2; cr[nc] = -1; csc[nc] = SC[b]; nc += 1
            else:                                 # held card reappearing
                t1 = T1[b, c]
                for r in range(N):
                    x0 = FI[b, r]
                    if XI[b, x0] >= 0:
                        continue
                    # first read: go down from start x0 to t1 in the message of t1
                    m1 = msg_of[t1]
                    p = x0
                    for u in range(starts[m1], t1):
                        p = sinv[p] if DEC[b, u] == 1 else binv[p]
                    if p == qs:
                        continue
                    s = SC[b] + lp(CNT[b], NN[b], p)
                    # (approximate counts: p then r are added)
                    s += math.log((CNT[b, r] + (1 if r == p else 0) + ALPHA) / (NN[b] + 1 + N * ALPHA))
                    if r == qs:
                        pass
                    cpar[nc] = b; ctyp[nc] = 3; cr[nc] = r; cx[nc] = x0; cr1[nc] = p; csc[nc] = s; nc += 1
                    if nc >= MAXC - 2:
                        break
        if nc == 0:
            return SC[:1], X[:1], DEC[:1], 0, alive
        k = min(B, nc)
        order = np.argsort(-csc[:nc])[:k]
        for i in range(k):
            j = order[i]; b = cpar[j]
            nX[i] = X[b]; nXI[i] = XI[b]; nT1[i] = T1[b]; nCNT[i] = CNT[b]; nNN[i] = NN[b]
            nDEC[i] = DEC[b]; nF[i] = F[b]; nFI[i] = FI[b]; nSC[i] = csc[j]
            t = ctyp[j]
            if t == 0:
                r = cr[j]; nCNT[i, r] += 1; nNN[i] += 1
                dec = 1 if r == qs else 0
            elif t == 1:
                r = qs; x0 = cx[j]
                nX[i, c] = x0; nXI[i, x0] = c; nCNT[i, r] += 1; nNN[i] += 1; dec = 1
            elif t == 2:
                nT1[i, c] = g; dec = 0
            else:
                r = cr[j]; x0 = cx[j]; p = cr1[j]
                nX[i, c] = x0; nXI[i, x0] = c; nT1[i, c] = -1
                nCNT[i, p] += 1; nCNT[i, r] += 1; nNN[i] += 2
                dec = 1 if r == qs else 0
            nDEC[i, g] = dec
            S = sinv if dec == 1 else binv
            for y in range(N):
                nF[i, y] = S[nF[i, y]]
            for y in range(N):
                nFI[i, nF[i, y]] = y
        nb = k
        X[:nb] = nX[:nb]; XI[:nb] = nXI[:nb]; T1[:nb] = nT1[:nb]; CNT[:nb] = nCNT[:nb]; NN[:nb] = nNN[:nb]
        DEC[:nb] = nDEC[:nb]; F[:nb] = nF[:nb]; FI[:nb] = nFI[:nb]; SC[:nb] = nSC[:nb]
        alive[g] = -1
        for b in range(nb):
            okb = True
            for u in range(g + 1):
                if DEC[b, u] != dt[u]:
                    okb = False; break
            if okb:
                for cc in range(N):
                    if X[b, cc] >= 0 and X[b, cc] != xt[cc]:
                        okb = False; break
            if okb:
                alive[g] = b; break
    return SC[:nb], X[:nb], DEC[:nb], nb, alive


def flatten(msgs):
    starts = np.cumsum([0] + [len(m) for m in msgs[:-1]]).astype(np.int64)
    C = np.concatenate([np.array(m, np.int64) for m in msgs])
    msg_of = np.concatenate([np.full(len(m), k, np.int64) for k, m in enumerate(msgs)])
    return C, msg_of, starts


if __name__ == "__main__":
    import time
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    from keyed_deck_attack import tables
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    names, BS, inv = tables()
    rng = np.random.default_rng(0)
    pl = tbs.build_plaintexts()
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, msg_of, starts = flatten(msgs)
    x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    qs = int(q[tbs.ALPHA_S.index("_")])
    t0 = time.time()
    SC, X, DEC, nb, alive = run_beam(C, msg_of, starts, inv[bname], inv[sname], BS[bname], BS[sname], qs, B, x_true, sp_true.astype(np.int8))
    lost = int(np.argmax(alive < 0)) if (alive < 0).any() else -1
    print(f'true branch lost at step {lost} (message {msg_of[lost] if lost >= 0 else -1}, position {lost - starts[msg_of[lost]] if lost >= 0 else -1}); ranks before: {alive[max(0, lost - 8):lost].tolist()}')
    best = int(np.argmax(SC))
    placed = X[best] >= 0
    print(f"beam B={B} ({time.time() - t0:.0f} s): {nb} hypotheses; best: correct starts "
          f"{int(((X[best] == x_true) & placed).sum())}/{int(placed.sum())} placed, correct decisions {int((DEC[best].astype(bool) == sp_true).sum())}/{len(sp_true)}")
    # did the true branch survive? (approx: a hypothesis with all decisions correct)
    ok = [(DEC[b].astype(bool) == sp_true).all() for b in range(nb)]
    print("true branch present at the end:", any(ok))
