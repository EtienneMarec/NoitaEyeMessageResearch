"""Decks shuffled by NOITA'S PSEUDO-RANDOM GENERATOR (hypothesis: the deck key is a numeric
seed passed through the game's generator).

Generator (community reconstruction, sources/github/pudy248_NoitaSeedSearcherCUDA/src/misc.cpp and
TwoAbove_noita-tools/.../noita_random.cpp): "Noita-style" Park-Miller with signed 32-bit integers
  Next: v = Seed*16807 + (Seed/127773)*(-2147483647)  (int32 overflows), if v < 0: v += 2^31-1
  Random(a, b) = a + (int)((b - a + 1) * Seed * 4.656612875e-10)   (after Next)
  SetRandomSeed(x, y): hash of (world seed, x, y), CPU version of misc.cpp.
Initialisations:
  M1: Seed = s          M2: Seed = s then one Next()          M3: SetRandomSeed(x, y), world seed ws
Shuffles of 0..82:
  sh1: descending Fisher-Yates, j = Random(0, i)      sh2: ascending, j = Random(i, 82)
  sh3: sort by random Next() keys
Battery (3 messages from different groups, for speed): starting deck = P (8 rules),
base shuffle = P (8 rules), reinsertion table = P (first trigram outside / inside the deck).
Score of a seed = maximum IoC of the sequence of read positions (true mechanism ≈ 3 to 5.5; chance ≈ 1.1).
"""
import sys
import time
import numpy as np
from numba import njit, prange
from deckcipher import recover_q, N
from reinsert_scan import recover_q_reinsert


@njit(cache=True, inline="always")
def w32(x):
    return ((x + 2147483648) % 4294967296) - 2147483648


@njit(cache=True)
def nnext(s):
    v = w32(w32(s * 16807) + w32((s // 127773) * -2147483647)) if s >= 0 else \
        w32(w32(s * 16807) + w32(-((-s) // 127773) * -2147483647))
    if v < 0:
        v += 2147483647
    return v


@njit(cache=True)
def nrandom(s, a, b):
    s = nnext(s)
    return s, a + int((b - a + 1) * s * 4.656612875e-10)


@njit(cache=True)
def helper_bits(r):
    arr = np.empty(1, np.float64); arr[0] = r
    e = arr.view(np.uint64)[0] & np.uint64(0x7fffffffffffffff)
    c = -1 if r < 0 else 1
    f = (e & np.uint64(0xfffffffffffff)) | np.uint64(0x0010000000000000)
    g = np.int64(0x433) - np.int64(e >> np.uint64(0x34))
    h = f >> np.uint64(g & 63)
    cond = np.uint64(0x433) < ((e >> np.uint64(0x20)) & np.uint64(0xffffffff)) >> np.uint64(0x14)
    j = np.uint64(0xffffffff) if cond else np.uint64(0)
    a = (j << np.uint64(0x20)) | j
    b = np.int64((~a & h) | ((f << np.uint64(0xd)) & a)) * c
    return np.uint64(b) & np.uint64(0xffffffff)


@njit(cache=True)
def helper2(a, b, ws):
    M = np.uint64(0xffffffff)
    a = np.uint64(a) & M; b = np.uint64(b) & M; ws = np.uint64(ws) & M
    u2 = (((a - b) & M) - ws & M) ^ (ws >> np.uint64(13))
    u1 = (((b - u2) & M) - ws & M) ^ ((u2 << np.uint64(8)) & M)
    u3 = (((ws - u2) & M) - u1 & M) ^ (u1 >> np.uint64(13))
    u2 = (((u2 - u1) & M) - u3 & M) ^ (u3 >> np.uint64(12))
    u1 = (((u1 - u2) & M) - u3 & M) ^ ((u2 << np.uint64(16)) & M)
    u3 = (((u3 - u2) & M) - u1 & M) ^ (u1 >> np.uint64(5))
    u2 = (((u2 - u1) & M) - u3 & M) ^ (u3 >> np.uint64(3))
    u1 = (((u1 - u2) & M) - u3 & M) ^ ((u2 << np.uint64(10)) & M)
    return (((u3 - u2) & M) - u1 & M) ^ (u1 >> np.uint64(15))


@njit(cache=True)
def set_random_seed(x, y, ws):
    a = (np.uint64(ws) ^ np.uint64(0x93262e6f)) & np.uint64(0xffffffff)
    x = x + float(a & np.uint64(0xfff))
    y = y + float((a >> np.uint64(12)) & np.uint64(0xfff))
    r = x * 134217727.0
    e = helper_bits(r) if r != 0 else np.uint64(2)
    if 102400.0 <= abs(y) or abs(x) <= 1.0:
        r = y * 134217727.0
    else:
        r = y * (y * 3483.328 + float(e))
    e2 = helper_bits(r) if r != 0 else np.uint64(2)
    g = helper2(e, e2, ws)
    s = float(g) / 4294967295.0 * 2147483639.0 + 1.0
    seed = int(s)
    seed = nnext(seed)
    for _ in range(int(np.uint64(ws) & np.uint64(3))):
        seed = nnext(seed)
    return seed


@njit(cache=True)
def shuffle(seed, kind):
    p = np.arange(N)
    if kind == 0:
        for i in range(N - 1, 0, -1):
            seed, j = nrandom(seed, 0, i)
            t = p[i]; p[i] = p[j]; p[j] = t
    elif kind == 1:
        for i in range(0, N - 1):
            seed, j = nrandom(seed, i, N - 1)
            t = p[i]; p[i] = p[j]; p[j] = t
    else:
        keys = np.empty(N)
        for i in range(N):
            seed = nnext(seed); keys[i] = seed
        p = np.argsort(keys)
    return p


@njit(cache=True)
def ioc_streams(qs_flat):
    cnt = np.zeros(N); tot = 0.0
    for v in qs_flat:
        if v >= 0:
            cnt[v] += 1; tot += 1
    return N * (cnt * (cnt - 1)).sum() / (tot * (tot - 1))


@njit(cache=True)
def battery(P, flat, starts):
    ident = np.arange(N)
    best = 0.0
    nm = starts.shape[0] - 1
    for role in range(2):
        for rule in range(8):
            buf = np.empty(flat.shape[0], np.int64); k = 0
            for m in range(nm):
                cs = flat[starts[m]:starts[m + 1]]
                q = recover_q(cs, P, ident, rule, 0) if role == 0 else recover_q(cs, ident, P, rule, 0)
                for i in range(1, q.shape[0]):
                    buf[k] = q[i]; k += 1
            ic = ioc_streams(buf[:k])
            if ic > best:
                best = ic
    for st in range(2):
        buf = np.empty(flat.shape[0], np.int64); k = 0
        for m in range(nm):
            q = recover_q_reinsert(flat[starts[m]:starts[m + 1]], ident, P, ident, st)
            for i in range(q.shape[0]):
                buf[k] = q[i]; k += 1
        ic = ioc_streams(buf[:k])
        if ic > best:
            best = ic
    return best


@njit(parallel=True, cache=True)
def scan_direct(s0, s1, flat, starts):
    out = np.zeros((s1 - s0, 6), np.float32)
    for idx in prange(s1 - s0):
        s = s0 + idx
        for mode in range(2):
            seed = s if mode == 0 else nnext(s)
            for kind in range(3):
                out[idx, mode * 3 + kind] = battery(shuffle(seed, kind), flat, starts)
    return out


@njit(parallel=True, cache=True)
def scan_setseed(ws, xs, ys, flat, starts):
    out = np.zeros((xs.shape[0], 3), np.float32)
    for idx in prange(xs.shape[0]):
        seed = set_random_seed(float(xs[idx]), float(ys[idx]), ws)
        for kind in range(3):
            out[idx, kind] = battery(shuffle(seed, kind), flat, starts)
    return out


def pack(msgs):
    flat = np.array([v for m in msgs for v in m], np.int64)
    starts = np.cumsum([0] + [len(m) for m in msgs]).astype(np.int64)
    return flat, starts


SPECIAL_WS = [0, 1, 2, 3, 9, 11, 12, 26, 27, 33, 34, 42, 83, 125, 666, 777, 1036, 1337, 4040, 4545, 5656,
              12345, 20201015, 15102020, 1602761874, 0x93262e6f, 0xacf68674, 0x5634505c, 123456789, 2147483647]
