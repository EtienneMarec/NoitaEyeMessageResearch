"""Lead 2: "parallel" beam (the 9 messages advance together) over the reinsertion table, with two constraints
on top of the "Chinese restaurant" likelihood:
  * BLOCKS: two occurrences of the same plaintext must read the same positions q
    (pairs (msg a, pos i) ~ (msg b, pos j) supplied by the alignment map);
  * DESTINATIONS: a position declared as a destination is never read (no-doubles model).
Model: sorted deck, no base shuffle, first symbol outside the deck, no homophones.
"""
import sys
import time
import numpy as np
from numba import njit

N = 83
BIG = 50.0


@njit(cache=True)
def crp(cnt, n, q, alpha):
    if cnt[q] > 0:
        return -np.log(cnt[q] / (n + alpha))
    return -np.log(alpha / (n + alpha) / N)


@njit(cache=True)
def move(D, P, q, t):
    c = D[q]
    if t > q:
        for k in range(q, t):
            D[k] = D[k + 1]; P[D[k]] = k
    elif t < q:
        for k in range(q, t, -1):
            D[k] = D[k - 1]; P[D[k]] = k
    D[t] = c; P[c] = t


@njit(cache=True)
def look(F, isdest, D, P, cnt, n, row, i, L, K, alpha):
    D2 = D.copy(); P2 = P.copy(); c2 = cnt.copy(); n2 = n; s = 0.0
    for j in range(i, min(i + K, L)):
        q = P2[row[j]]
        s += crp(c2, n2, q, alpha)
        if isdest[q]:
            s += BIG
        c2[q] += 1; n2 += 1
        if F[q] < 0:
            break
        move(D2, P2, q, F[q])
    return s


@njit(cache=True)
def search(Cm, lens, ev_m, ev_t, chk_start, chk_a, chk_i, chk_b, chk_j, B, K, alpha, lam):
    M, Lmax = Cm.shape
    F = -np.ones((B, N), np.int64); isd = np.zeros((B, N), np.bool_)
    D = np.zeros((B, M, N), np.int64); P = np.zeros((B, M, N), np.int64)
    for m in range(M):
        for k in range(N):
            D[0, m, k] = k; P[0, m, k] = k
    cnt = np.zeros((B, N)); n = np.zeros(B); sc = np.zeros(B)
    Q = -np.ones((B, M, Lmax), np.int64)
    nb = 1
    maxc = B * N
    cb = np.empty(maxc, np.int64); ct = np.empty(maxc, np.int64); cs = np.empty(maxc)
    for e in range(ev_m.shape[0]):
        m = ev_m[e]; i = ev_t[e]; c = Cm[m, i]
        nc = 0
        for b in range(nb):
            q = P[b, m, c]
            sc[b] += crp(cnt[b], n[b], q, alpha)
            if isd[b, q]:
                sc[b] += BIG
            cnt[b, q] += 1; n[b] += 1; Q[b, m, i] = q
            # block constraints that become complete at this event
            for h in range(chk_start[e], chk_start[e + 1]):
                if Q[b, chk_a[h], chk_i[h]] != Q[b, chk_b[h], chk_j[h]]:
                    sc[b] += lam
            if F[b, q] >= 0:
                move(D[b, m], P[b, m], q, F[b, q])
                cb[nc] = b; ct[nc] = -1; cs[nc] = sc[b]; nc += 1
            else:
                for t in range(N):
                    if t == q or cnt[b, t] > 0:      # a destination is never a read position
                        continue
                    F2 = F[b].copy(); F2[q] = t
                    i2 = isd[b].copy(); i2[t] = True
                    D2 = D[b, m].copy(); P2 = P[b, m].copy()
                    move(D2, P2, q, t)
                    la = look(F2, i2, D2, P2, cnt[b], n[b], Cm[m], i + 1, lens[m], K, alpha)
                    cb[nc] = b; ct[nc] = t; cs[nc] = sc[b] + la; nc += 1
        allk = True
        for r in range(nc):
            if ct[r] >= 0:
                allk = False; break
        if allk:
            continue
        order = np.argsort(cs[:nc])[:B]
        k2 = order.shape[0]
        F_ = np.empty((k2, N), np.int64); I_ = np.empty((k2, N), np.bool_)
        D_ = np.empty((k2, M, N), np.int64); P_ = np.empty((k2, M, N), np.int64)
        C_ = np.empty((k2, N)); n_ = np.empty(k2); s_ = np.empty(k2); Q_ = np.empty((k2, M, Lmax), np.int64)
        for r in range(k2):
            b = cb[order[r]]; t = ct[order[r]]
            F_[r] = F[b]; I_[r] = isd[b]; D_[r] = D[b]; P_[r] = P[b]
            C_[r] = cnt[b]; n_[r] = n[b]; s_[r] = sc[b]; Q_[r] = Q[b]
            if t >= 0:
                q = P[b, m, c]
                F_[r, q] = t; I_[r, t] = True
                move(D_[r, m], P_[r, m], q, t)
        nb = k2
        F[:nb] = F_; isd[:nb] = I_; D[:nb] = D_; P[:nb] = P_; cnt[:nb] = C_; n[:nb] = n_; sc[:nb] = s_; Q[:nb] = Q_
    best = np.argmin(sc[:nb])
    return F[best].copy(), sc[best]


def prepare(msgs, pairs):
    """pairs: list of ((a, i), (b, j)) positions that must read the same position q (positions >= 1)."""
    M, Lmax = len(msgs), max(len(m) for m in msgs)
    Cm = np.zeros((M, Lmax), np.int64)
    for m, s in enumerate(msgs):
        Cm[m, :len(s)] = s
    lens = np.array([len(s) for s in msgs], np.int64)
    ev = [(t, m) for t in range(1, Lmax) for m in range(M) if t < lens[m]]
    idx = {(m, t): e for e, (t, m) in enumerate(ev)}
    buckets = [[] for _ in ev]
    for (a, i), (b, j) in pairs:
        if (a, i) in idx and (b, j) in idx:
            buckets[max(idx[(a, i)], idx[(b, j)])].append((a, i, b, j))
    chk_start = np.cumsum([0] + [len(x) for x in buckets]).astype(np.int64)
    flatc = [x for bk in buckets for x in bk] or [(0, 0, 0, 0)]
    arr = np.array(flatc, np.int64)
    return (Cm, lens, np.array([m for t, m in ev], np.int64), np.array([t for t, m in ev], np.int64),
            chk_start, arr[:, 0].copy(), arr[:, 1].copy(), arr[:, 2].copy(), arr[:, 3].copy())


def run(msgs, pairs, B=500, K=10, alpha=2.0, lam=15.0):
    args = prepare(msgs, pairs)
    t = time.time()
    F, s = search(*args, B, K, alpha, lam)
    print(f"  parallel beam B={B} K={K} λ={lam}: score {s:.1f} ({time.time()-t:.0f} s)", flush=True)
    return F, s
