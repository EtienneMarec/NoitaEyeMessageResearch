"""Test of a probable text (crib) in the space model, for a given (β, σ) shuffle pair (§38).

A candidate text for the first L symbols of a message (position 0 = number, ordinary symbol) fixes:
  - the space/letter decisions, hence F_t (start position -> current position) for t < L;
  - the letter pattern: two positions with the same letter read the same deck position:
    x(c_t2) = F_t2⁻¹ F_t1 x(c_t1) (successive occurrences of each letter are linked).
A card read at two positions (any letters) closes cycles: the text and the pair are only
consistent if each component admits a seed (83 values) satisfying all its equations, with
x injective and distinct letters read at distinct positions.
Validation on the testbed with spaces: true text / true pair, wrong texts, wrong pairs."""
import sys
import numpy as np
from numba import njit

N = 83


@njit(cache=True)
def consistent(cs, lt, binv, sinv, space_code):
    """cs: cards (L), lt: letter codes (L); returns (number of components without solution, number of components)."""
    L = cs.shape[0]
    F = np.empty((L, N), np.int64); Fi = np.empty((L, N), np.int64)
    cur = np.arange(N)
    for t in range(L):
        F[t] = cur
        for y in range(N):
            Fi[t, cur[y]] = y
        S = sinv if lt[t] == space_code else binv
        nxt = np.empty(N, np.int64)
        for y in range(N):
            nxt[y] = S[cur[y]]
        cur = nxt
    # edges: successive occurrences of the same letter
    ea = np.empty(L, np.int64); eb = np.empty(L, np.int64); ne = 0
    last = np.full(64, -1, np.int64)
    for t in range(L):
        a = lt[t]
        if last[a] >= 0:
            ea[ne] = last[a]; eb[ne] = t; ne += 1
        last[a] = t
    # components over the cards (letter edges + card identity)
    comp = np.full(N, -1, np.int64)
    ncomp = 0
    for t in range(L):
        c = cs[t]
        if comp[c] < 0:
            # BFS
            stack = np.empty(N, np.int64); sp = 0
            stack[sp] = c; sp += 1; comp[c] = ncomp
            while sp > 0:
                sp -= 1; u = stack[sp]
                for e in range(ne):
                    v = -1
                    if cs[ea[e]] == u:
                        v = cs[eb[e]]
                    elif cs[eb[e]] == u:
                        v = cs[ea[e]]
                    if v >= 0 and comp[v] < 0:
                        comp[v] = ncomp; stack[sp] = v; sp += 1
            ncomp += 1
    dead = 0
    val = np.full(N, -1, np.int64)
    for k in range(ncomp):
        root = -1
        for c in range(N):
            if comp[c] == k:
                root = c; break
        found = False
        for x0 in range(N):
            for c in range(N):
                val[c] = -1
            val[root] = x0
            ok = True
            changed = True
            while changed and ok:
                changed = False
                for e in range(ne):
                    u = cs[ea[e]]; v = cs[eb[e]]
                    if comp[u] != k:
                        continue
                    if val[u] >= 0:
                        w = Fi[eb[e], F[ea[e], val[u]]]
                        if val[v] < 0:
                            val[v] = w; changed = True
                        elif val[v] != w:
                            ok = False; break
                    elif val[v] >= 0:
                        w = Fi[ea[e], F[eb[e], val[v]]]
                        val[u] = w; changed = True
            if not ok:
                continue
            # injectivity of x within the component
            used = np.zeros(N, np.bool_)
            for c in range(N):
                if comp[c] == k and val[c] >= 0:
                    if used[val[c]]:
                        ok = False; break
                    used[val[c]] = True
            if not ok:
                continue
            # distinct letters -> distinct read positions (within the component)
            rd = np.full(64, -1, np.int64)
            seenpos = np.full(N, -1, np.int64)
            for t in range(L):
                c = cs[t]
                if comp[c] != k:
                    continue
                r = F[t, val[c]]
                a = lt[t]
                if rd[a] < 0:
                    if seenpos[r] >= 0 and seenpos[r] != a:
                        ok = False; break
                    rd[a] = r; seenpos[r] = a
                elif rd[a] != r:
                    ok = False; break
            if ok:
                found = True; break
        if not found:
            dead += 1
    return dead, ncomp


CODES = {ch: i for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789ÄÖÅ")}  # ÄÖÅ for Finnish
SPACE = CODES["_"]


def encode_text(s):
    return np.array([CODES[ch] for ch in s], np.int64)


if __name__ == "__main__":
    import random
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    from keyed_deck_attack import tables
    names, BS, inv = tables()
    rng = np.random.default_rng(7); rnd = random.Random(7)
    pl = tbs.build_plaintexts()
    T = tbs.english_with_spaces()
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    pairs = [k for k in BS]
    res = {"true": 0, "wrong text": [0, 0], "wrong pair": [0, 0]}
    trial = 0
    while trial < 6:
        bname, sname = rnd.choice(pairs), rnd.choice(pairs)
        if bname == sname or bname.startswith("rot") and sname.startswith("rot") or bname == "id":
            continue
        trial += 1
        D0 = rng.permutation(N); q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
        m = pl[0]
        cs = D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))][:L]
        crib = "1" + m[1:L]
        d, nc = consistent(cs, encode_text(crib), inv[bname], inv[sname], SPACE)
        res["true"] += d == 0
        for _ in range(200):
            i = rnd.randrange(1000, len(T) - 100)
            fake = "1" + T[i:i + L - 1]
            d2, _ = consistent(cs, encode_text(fake), inv[bname], inv[sname], SPACE)
            res["wrong text"][0] += d2 == 0; res["wrong text"][1] += 1
        for _ in range(200):
            b2, s2 = rnd.choice(pairs), rnd.choice(pairs)
            d3, _ = consistent(cs, encode_text(crib), inv[b2], inv[s2], SPACE)
            res["wrong pair"][0] += d3 == 0; res["wrong pair"][1] += 1
        print(f"trial {trial} (β={bname}, σ={sname}): true text consistent: {d == 0} ({nc} components, repeated cards "
              f"{L - len(set(cs.tolist()))})", flush=True)
    print(f"L = {L}: true consistent {res['true']}; wrong texts consistent {res['wrong text'][0]}/{res['wrong text'][1]}; "
          f"wrong pairs consistent {res['wrong pair'][0]}/{res['wrong pair'][1]}")
