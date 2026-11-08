"""Position-read "deck of cards" ciphers (XGAK family), with numba.

Mechanism (one step, letter at position q = POS[letter]):
  order 0: output = D[q]; then rule(q); then base shuffle β
  order 1: base shuffle β; output = D[q]; then rule(q)
D is the deck (position -> card). Shuffle β: D_new[x] = D_old[β[x]].
Rules (applied at position q):
  0 swap the top card and q             1 card q put back on top (shifts 0..q-1)
  2 card q moved to the bottom           3 swap q and the bottom card
  4 cut: q moves to the top (rotation)  5 cut: q+1 moves to the top
  6 reversal of cards 0..q              7 no change
Since the rule depends only on q, knowing β and the initial deck is enough to compute the
sequence of q from the ciphertext: the plaintext is then a substitution of the q.
"""
import numpy as np
from numba import njit

N = 83
RULES = ["swap0", "totop", "tobottom", "swaplast", "cut_q", "cut_q1", "flip", "none"]


@njit(cache=True)
def _apply_rule(D, P, q, rule, n):
    if rule == 0:
        a, b = D[0], D[q]
        D[0], D[q] = b, a
    elif rule == 1:
        c = D[q]
        for k in range(q, 0, -1):
            D[k] = D[k - 1]
        D[0] = c
    elif rule == 2:
        c = D[q]
        for k in range(q, n - 1):
            D[k] = D[k + 1]
        D[n - 1] = c
    elif rule == 3:
        a, b = D[n - 1], D[q]
        D[n - 1], D[q] = b, a
    elif rule == 4 or rule == 5:
        s = q if rule == 4 else (q + 1) % n
        tmp = D.copy()
        for k in range(n):
            D[k] = tmp[(k + s) % n]
    elif rule == 6:
        i, j = 0, q
        while i < j:
            a = D[i]; D[i] = D[j]; D[j] = a
            i += 1; j -= 1
    for k in range(n):
        P[D[k]] = k


@njit(cache=True)
def _apply_base(D, P, beta, n):
    tmp = D.copy()
    for k in range(n):
        D[k] = tmp[beta[k]]
    for k in range(n):
        P[D[k]] = k


@njit(cache=True)
def encrypt(qs, D0, beta, rule, order):
    """qs: read positions (one per letter). Returns the output cards."""
    n = D0.shape[0]
    D = D0.copy()
    P = np.empty(n, np.int64)
    for k in range(n):
        P[D[k]] = k
    out = np.empty(qs.shape[0], np.int64)
    for i in range(qs.shape[0]):
        q = qs[i]
        if order == 1:
            _apply_base(D, P, beta, n)
        out[i] = D[q]
        _apply_rule(D, P, q, rule, n)
        if order == 0:
            _apply_base(D, P, beta, n)
    return out


@njit(cache=True)
def recover_q(cs, D0, beta, rule, order):
    """Inverse: from the output cards, recovers the read positions."""
    n = D0.shape[0]
    D = D0.copy()
    P = np.empty(n, np.int64)
    for k in range(n):
        P[D[k]] = k
    out = np.empty(cs.shape[0], np.int64)
    for i in range(cs.shape[0]):
        if order == 1:
            _apply_base(D, P, beta, n)
        q = P[cs[i]]
        out[i] = q
        _apply_rule(D, P, q, rule, n)
        if order == 0:
            _apply_base(D, P, beta, n)
    return out


def ioc83(streams):
    """Normalised IoC (×83) of the concatenated q sequences (1.0 = uniform random)."""
    cnt = np.zeros(N, np.int64)
    tot = 0
    for s in streams:
        for v in s:
            cnt[v] += 1
            tot += 1
    return N * float((cnt * (cnt - 1)).sum()) / (tot * (tot - 1)), int((cnt > 0).sum())


# ---- "natural" base shuffles -------------------------------------------------------
def base_shuffles(n=N):
    idx = np.arange(n)
    out = {"id": idx.copy(), "reverse": idx[::-1].copy()}
    for r in range(1, n):
        out[f"rot{r}"] = (idx + r) % n
    # perfect riffles: out-shuffle / in-shuffle (and their inverses)
    h = (n + 1) // 2
    outs = np.empty(n, np.int64); ins = np.empty(n, np.int64)
    top, bot = list(range(h)), list(range(h, n))
    seq = [];
    for a, b in zip(top, bot + [None]):
        seq.append(a)
        if b is not None: seq.append(b)
    outs[:] = seq
    seq = []
    top2, bot2 = list(range(n // 2)), list(range(n // 2, n))
    for a, b in zip(bot2, top2 + [None]):
        seq.append(a)
        if b is not None: seq.append(b)
    ins[:] = seq
    for name, p in [("outshuffle", outs), ("inshuffle", ins)]:
        out[name] = p
        inv = np.empty(n, np.int64); inv[p] = idx
        out[name + "_inv"] = inv
    # deal into k piles then gather
    for k in range(2, 8):
        piles = [list(range(j, n, k)) for j in range(k)]
        for order in ("fwd", "rev"):
            seq = []
            for pl in (piles if order == "fwd" else piles[::-1]):
                seq += pl[::-1]
            out[f"deal{k}{order}"] = np.array(seq)
            inv = np.empty(n, np.int64); inv[np.array(seq)] = idx
            out[f"deal{k}{order}_inv"] = inv
    # "milk" shuffle (alternating top/bottom) and Mongean shuffle
    milk = []
    i, j = 0, n - 1
    while i <= j:
        milk.append(i); i += 1
        if i <= j: milk.append(j); j -= 1
    out["milk"] = np.array(milk)
    inv = np.empty(n, np.int64); inv[np.array(milk)] = idx; out["milk_inv"] = inv
    mong = []
    for c in range(n):
        if c % 2 == 0: mong.insert(0, c)
        else: mong.append(c)
    out["mongean"] = np.array(mong)
    inv = np.empty(n, np.int64); inv[np.array(mong)] = idx; out["mongean_inv"] = inv
    for k, v in out.items():
        assert sorted(v.tolist()) == list(range(n)), k
    return {k: np.asarray(v, np.int64) for k, v in out.items()}
