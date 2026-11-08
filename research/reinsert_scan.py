"""Scan of the "reinsertion" family: output = D[q]; the card read is removed then reinserted at
position f(q); then base shuffle β. If f is a fixed function of q (homophones
included: each read position has its destination), the sequence of q can be computed
from the ciphertext. For the right mechanism, it uses only the read positions
(~41 values at most), and NEVER the destinations. For a wrong one, ~83 values.
Statistic: number of distinct values of q, and share of the q falling in the 20 least used
values (close to 0 for the right mechanism).
Option: first symbol outside the deck (all messages start from the initial deck after it).
"""
import sys
import numpy as np
from numba import njit
from deckcipher import base_shuffles, N


@njit(cache=True)
def recover_q_reinsert(cs, D0, F, beta, start):
    n = D0.shape[0]
    D = D0.copy()
    P = np.empty(n, np.int64)
    for k in range(n):
        P[D[k]] = k
    out = np.full(cs.shape[0], -1, np.int64)
    for i in range(start, cs.shape[0]):
        q = P[cs[i]]
        out[i] = q
        c = D[q]
        m = F[q]
        if m > q:
            for k in range(q, m):
                D[k] = D[k + 1]
        else:
            for k in range(q, m, -1):
                D[k] = D[k - 1]
        D[m] = c
        tmp = D.copy()
        for k in range(n):
            D[k] = tmp[beta[k]]
        for k in range(n):
            P[D[k]] = k
    return out


def dest_maps(n=N):
    q = np.arange(n)
    maps = {"dessus": np.zeros(n, np.int64), "dessous": np.full(n, n - 1, np.int64),
            "miroir": (n - 1 - q) % n}
    for k in range(1, n):
        maps[f"q+{k}"] = (q + k) % n
    for a in (2, 3, 4, 5, 41, 42):
        maps[f"{a}q"] = (a * q) % n
    maps["q/2"] = q // 2
    maps["(q+n)/2"] = (q + n) // 2
    return maps


def score(streams):
    v = np.concatenate([s[s >= 0] for s in streams])
    cnt = np.bincount(v, minlength=N)
    low = np.sort(cnt)[:20].sum() / cnt.sum()
    return int((cnt > 0).sum()), float(low)


def scan(cipher_msgs, first_outside=True, bases=None):
    bases = bases or {k: v for k, v in base_shuffles().items() if not k.startswith("rot") or k in ("rot1", "rot82")}
    arrs = [np.array(m, np.int64) for m in cipher_msgs]
    res = []
    for d0n, D0 in (("sorted", np.arange(N)), ("reversed", np.arange(N)[::-1].copy())):
        for fn, F in dest_maps().items():
            for bn, beta in bases.items():
                qs = [recover_q_reinsert(a, D0, F, beta, 1 if first_outside else 0) for a in arrs]
                d, low = score(qs)
                res.append((low, d, d0n, fn, bn))
    res.sort()
    return res


def report(res, top=8):
    lows = np.array([r[0] for r in res])
    print(f"{len(res)} mechanisms; share of the 20 rarest values: median {np.median(lows):.3f} (std {lows.std():.3f})")
    for low, d, d0, fn, bn in res[:top]:
        print(f"  {low:.3f}  {d:3d} values   deck {d0:8s}  destination {fn:8s}  base {bn}   (z={(low-np.median(lows))/lows.std():.1f})")


if __name__ == "__main__":
    from stats import load_eyes
    names, M = load_eyes()
    for fo in (True, False):
        print(f"\n=== eyes, first trigram {'outside' if fo else 'inside'} the deck ===")
        report(scan(M, fo))
