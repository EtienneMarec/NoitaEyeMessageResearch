"""Beam search over the reinsertion table (mechanism of §8, sorted deck, first symbol outside the deck,
no base shuffle). Step-by-step decryption, message after message; when a position q is read for the first
time, its 83 destinations are tried, each judged by a K-step lookahead (up to the next unknown position).
Score: -log likelihood of a "Chinese restaurant" process (see sa_progressive.py).
"""
import sys
import time
import numpy as np
from numba import njit

N = 83


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
def lookahead(F, D, P, cnt, n, msg, i, K, alpha):
    D2 = D.copy(); P2 = P.copy(); c2 = cnt.copy(); n2 = n
    s = 0.0
    for j in range(i, min(i + K, msg.shape[0])):
        q = P2[msg[j]]
        s += crp(c2, n2, q, alpha)
        c2[q] += 1; n2 += 1
        if F[q] < 0:
            break
        move(D2, P2, q, F[q])
    return s


@njit(cache=True)
def beam_search(msgs_flat, starts, B, K, alpha):
    Fb = -np.ones((B, N), np.int64)
    Db = np.zeros((B, N), np.int64); Pb = np.zeros((B, N), np.int64)
    Cb = np.zeros((B, N), np.float64); nb = np.zeros(B); Lb = np.zeros(B)
    nbeam = 1
    cand_b = np.empty(B * N, np.int64); cand_m = np.empty(B * N, np.int64); cand_s = np.empty(B * N)
    for m in range(starts.shape[0] - 1):
        a, e = starts[m] + 1, starts[m + 1]           # first symbol outside the deck
        msg = msgs_flat[a:e]
        for b in range(nbeam):
            for k in range(N):
                Db[b, k] = k; Pb[b, k] = k
        for i in range(msg.shape[0]):
            # read
            nc = 0
            for b in range(nbeam):
                q = Pb[b, msg[i]]
                Lb[b] += crp(Cb[b], nb[b], q, alpha)
                Cb[b, q] += 1; nb[b] += 1
                if Fb[b, q] >= 0:
                    move(Db[b], Pb[b], q, Fb[b, q])
                    cand_b[nc] = b; cand_m[nc] = -1; cand_s[nc] = Lb[b]; nc += 1
                else:
                    for t in range(N):
                        F2 = Fb[b].copy(); F2[q] = t
                        D2 = Db[b].copy(); P2 = Pb[b].copy()
                        move(D2, P2, q, t)
                        la = lookahead(F2, D2, P2, Cb[b], nb[b], msg, i + 1, K, alpha)
                        cand_b[nc] = b; cand_m[nc] = t; cand_s[nc] = Lb[b] + la; nc += 1
            if nc == nbeam and np.all(cand_m[:nc] < 0):
                continue
            order = np.argsort(cand_s[:nc])[:B]
            F_new = np.empty((order.shape[0], N), np.int64); D_new = np.empty_like(F_new); P_new = np.empty_like(F_new)
            C_new = np.empty((order.shape[0], N)); n_new = np.empty(order.shape[0]); L_new = np.empty(order.shape[0])
            for r in range(order.shape[0]):
                b = cand_b[order[r]]; t = cand_m[order[r]]
                F_new[r] = Fb[b]; D_new[r] = Db[b]; P_new[r] = Pb[b]
                C_new[r] = Cb[b]; n_new[r] = nb[b]; L_new[r] = Lb[b]
                if t >= 0:
                    q = Pb[b, msg[i]]
                    F_new[r, q] = t
                    move(D_new[r], P_new[r], q, t)
            nbeam = order.shape[0]
            Fb[:nbeam] = F_new; Db[:nbeam] = D_new; Pb[:nbeam] = P_new
            Cb[:nbeam] = C_new; nb[:nbeam] = n_new; Lb[:nbeam] = L_new
    best = np.argmin(Lb[:nbeam])
    return Fb[best].copy(), Lb[best]


def run(msgs, B=300, K=12, alpha=2.0):
    flat = np.array([v for m in msgs for v in m], np.int64)
    starts = np.cumsum([0] + [len(m) for m in msgs]).astype(np.int64)
    t = time.time()
    F, L = beam_search(flat, starts, B, K, alpha)
    print(f"  beam B={B}, K={K}: nll {L:.1f} ({time.time()-t:.0f} s)", flush=True)
    return F, L


if __name__ == "__main__":
    from stats import load_eyes
    from sa_reinsert import pack, replay, entropy
    names, M = load_eyes()
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    F, L = run(M, B)
    flat, starts = pack(M); q = np.empty(flat.shape[0], np.int64); replay(flat, starts, np.where(F < 0, np.arange(N), F), q)
    print(f"eyes: entropy {entropy(q):.3f}, read positions {len(set(q[q>=0].tolist()))}")
