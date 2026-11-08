"""EXACT lazy search for the reinsertion table (one held card at a time).

Model: sorted deck at the start of each message, first symbol outside the deck, no base shuffle;
letter = read position q; the card read is removed then reinserted at rank F[q].

State of a hypothesis:
  K = order of the "known" cards; at most ONE held card d, whose destination m (rank at the
  moment of its reinsertion) is unknown but bounded: m ∈ [mlo, mhi]. Its number of known cards
  in front of it is k = m + Δ (Δ exact in each branch).
Event (card c read):
  * c known at index j of K: real rank q = j + [d in front of c]; if d's interval overlaps j,
    TWO branches (d in front: q = j+1; d behind: q = j), which cut the interval of m;
  * reinsertion of c at rank t = F[q]: if d overlaps t, two branches;
  * c is d (re-read): m is decided over its interval (rank read = m + Δ);
  * new letter (F[q] unknown) or second card for d's slot: m is decided first.
All hypotheses advance together, event by event: compared on equal terms.
Cost: "Chinese restaurant" likelihood + BIG if a destination is read (or if a read position
becomes a destination) + λ per violated block equality.
"""
import time
import numpy as np
from numba import njit

N = 83
BIG = 50.0


A_LET = 30.0
BETA = 0.5


@njit(cache=True)
def crp(cnt, n, q, alpha):
    """Dirichlet-multinomial over an alphabet of A_LET letters (alpha ignored, kept for the signature)."""
    k = 0
    for x in range(N):
        if cnt[x] > 0:
            k += 1
    if cnt[q] > 0:
        return -np.log((cnt[q] + BETA) / (n + A_LET * BETA))
    free = max(A_LET - k, 0.3)
    return -np.log(free * BETA / (n + A_LET * BETA) / (N - k))


@njit(cache=True)
def blockpen(Q, g, q, chk_start, chk_a, chk_b, e, lam):
    s = 0.0
    for h in range(chk_start[e], chk_start[e + 1]):
        a, b = chk_a[h], chk_b[h]
        qa = q if a == g else Q[a]
        qb = q if b == g else Q[b]
        if qa != qb:
            s += lam
    return s


# ---- operations on a state (1D arrays of a hypothesis) -------------------------------
@njit(cache=True)
def k_remove(K, Kp, L, j):
    for x in range(j, L - 1):
        K[x] = K[x + 1]; Kp[K[x]] = x
    return L - 1


@njit(cache=True)
def k_insert(K, Kp, L, ti, c):
    if ti > L:
        ti = L
    for x in range(L, ti, -1):
        K[x] = K[x - 1]; Kp[K[x]] = x
    K[ti] = c; Kp[c] = ti
    return L + 1


# Branch descriptor: (parent, resolved m or -1, rel_read (-1 none, 1 in front, 0 behind),
#                               rel_insertion (-1, 1, 0), q)
@njit(cache=True)
def enumerate_children(b, c, g, e, F, K, Kp, L, dact, dcard, dslot, mlo, mhi, dl, cnt, n, isd, Q,
                       chk_start, chk_a, chk_b, alpha, lam, out, cost0, nout):
    """Writes the branches of state b to out (rows [parent, m, relR, relI, q]) and their costs."""
    if dact[b] and dcard[b] == c:
        for m in range(mlo[b], mhi[b] + 1):
            if m == dslot[b]:
                continue
            q = m + dl[b]
            if q < 0 or q >= N:
                continue
            cc = crp(cnt[b], n[b], q, alpha) + (BIG if isd[b, q] else 0.0) + (BIG if cnt[b, m] > 0 else 0.0)
            cc += blockpen(Q[b], g, q, chk_start, chk_a, chk_b, e, lam)
            out[nout, 0] = b; out[nout, 1] = m; out[nout, 2] = -1; out[nout, 3] = -1; out[nout, 4] = q
            cost0[nout] = cc; nout += 1
        return nout
    j = Kp[b, c]
    if not dact[b]:
        q = j
        cc = crp(cnt[b], n[b], q, alpha) + (BIG if isd[b, q] else 0.0)
        cc += blockpen(Q[b], g, q, chk_start, chk_a, chk_b, e, lam)
        out[nout, 0] = b; out[nout, 1] = -1; out[nout, 2] = -1; out[nout, 3] = -1; out[nout, 4] = q
        cost0[nout] = cc; nout += 1
        return nout
    # one held card: read relation
    for rel in (1, 0):
        if rel == 1:
            lo, hi, q, d2 = mlo[b], min(mhi[b], j - dl[b]), j + 1, dl[b]
        else:
            lo, hi, q, d2 = max(mlo[b], j + 1 - dl[b]), mhi[b], j, dl[b] - 1
        if lo > hi or q >= N:
            continue
        base = crp(cnt[b], n[b], q, alpha) + (BIG if isd[b, q] else 0.0)
        base += blockpen(Q[b], g, q, chk_start, chk_a, chk_b, e, lam)
        t = F[b, q]
        if q == dslot[b] or t < 0:
            # m must be decided over [lo, hi]
            for m in range(lo, hi + 1):
                if m == dslot[b]:
                    continue
                cc = base + (BIG if cnt[b, m] > 0 or m == q else 0.0)
                out[nout, 0] = b; out[nout, 1] = m; out[nout, 2] = rel; out[nout, 3] = -1; out[nout, 4] = q
                cost0[nout] = cc; nout += 1
        else:
            # reinsertion at rank t: d in front (k <= t-1) or behind (k >= t)
            for reli in (1, 0):
                if reli == 1:
                    lo2, hi2 = lo, min(hi, t - 1 - d2)
                else:
                    lo2, hi2 = max(lo, t - d2), hi
                if lo2 > hi2:
                    continue
                out[nout, 0] = b; out[nout, 1] = -2 - (lo2 * 100 + hi2); out[nout, 2] = rel; out[nout, 3] = reli
                out[nout, 4] = q
                cost0[nout] = base; nout += 1
    return nout


@njit(cache=True)
def apply_child(desc, c, g, F, K, Kp, L, dact, dcard, dslot, mlo, mhi, dl, cnt, n, isd, Q, r):
    """Applies branch desc to state r (already copied from the parent)."""
    mval, rel, reli, q = desc[1], desc[2], desc[3], desc[4]
    if dact[r] and dcard[r] == c and rel == -1 and mval >= 0 and Kp[r, c] < 0:
        # re-read of d: m decided
        F[r, dslot[r]] = mval; isd[r, mval] = True; dact[r] = False
        cnt[r, q] += 1; n[r] += 1; Q[r, g] = q
        t = F[r, q]
        if t >= 0:
            L[r] = k_insert(K[r], Kp[r], L[r], t, c)
        else:
            dact[r] = True; dcard[r] = c; dslot[r] = q; mlo[r] = 0; mhi[r] = N - 1; dl[r] = 0
        return
    j = Kp[r, c]
    cnt[r, q] += 1; n[r] += 1; Q[r, g] = q
    L[r] = k_remove(K[r], Kp[r], L[r], j)
    Kp[r, c] = -1
    if not dact[r]:
        t = F[r, q]
        if t >= 0:
            L[r] = k_insert(K[r], Kp[r], L[r], t, c)
        else:
            dact[r] = True; dcard[r] = c; dslot[r] = q; mlo[r] = 0; mhi[r] = N - 1; dl[r] = 0
        return
    # one held card: restrict according to the read relation
    if rel == 1:
        mhi[r] = min(mhi[r], j - dl[r])
    else:
        mlo[r] = max(mlo[r], j + 1 - dl[r]); dl[r] -= 1
    if mval >= 0:
        # decide d: m = mval, d placed at index k = m + Δ
        F[r, dslot[r]] = mval; isd[r, mval] = True
        L[r] = k_insert(K[r], Kp[r], L[r], mval + dl[r], dcard[r])
        dact[r] = False
        t = F[r, q]
        if t >= 0:
            L[r] = k_insert(K[r], Kp[r], L[r], t, c)
        else:
            dact[r] = True; dcard[r] = c; dslot[r] = q; mlo[r] = 0; mhi[r] = N - 1; dl[r] = 0
        return
    # reinsertion at known rank t, relation d/c decided (reli), interval encoded in mval
    code = -2 - mval
    mlo[r] = code // 100; mhi[r] = code % 100
    t = F[r, q]
    if reli == 1:
        L[r] = k_insert(K[r], Kp[r], L[r], t - 1, c)
    else:
        L[r] = k_insert(K[r], Kp[r], L[r], t, c); dl[r] += 1


@njit(cache=True)
def run(flat, starts, B, alpha, lam, chk_start, chk_a, chk_b, maxc, Qt, Ft):
    G = flat.shape[0]
    F = -np.ones((B, N), np.int64); K = np.zeros((B, N), np.int64); Kp = np.zeros((B, N), np.int64)
    L = np.zeros(B, np.int64); dact = np.zeros(B, np.bool_); dcard = np.zeros(B, np.int64)
    dslot = np.zeros(B, np.int64); mlo = np.zeros(B, np.int64); mhi = np.zeros(B, np.int64)
    dl = np.zeros(B, np.int64); cnt = np.zeros((B, N)); n = np.zeros(B); isd = np.zeros((B, N), np.bool_)
    Q = -np.ones((B, G), np.int64); cost = np.zeros(B)
    out = np.zeros((maxc, 5), np.int64); c0 = np.zeros(maxc)
    nb = 1
    e = 0
    bestc = np.zeros(G)
    ok = np.zeros(B, np.bool_); ok[0] = Qt[0] != -9
    trank = -np.ones(G, np.int64); tcand = -np.ones(G, np.int64)
    for m in range(starts.shape[0] - 1):
        for b in range(nb):
            for x in range(N):
                K[b, x] = x; Kp[b, x] = x
            L[b] = N; dact[b] = False
        for g in range(starts[m] + 1, starts[m + 1]):
            c = flat[g]
            nout = 0
            for b in range(nb):
                nout = enumerate_children(b, c, g, e, F, K, Kp, L[b], dact, dcard, dslot, mlo, mhi, dl, cnt, n,
                                          isd, Q, chk_start, chk_a, chk_b, alpha, lam, out, c0, nout)
                if nout > maxc - 2 * N - 10:
                    break
            tot = np.empty(nout)
            for i in range(nout):
                tot[i] = cost[out[i, 0]] + c0[i]
            # true branch among the candidates?
            okc = np.zeros(nout, np.bool_)
            for i in range(nout):
                pb = out[i, 0]
                if not ok[pb] or out[i, 4] != Qt[g]:
                    continue
                mv = out[i, 1]
                if mv >= 0:
                    if mv != Ft[dslot[pb]]:
                        continue
                elif mv <= -2:
                    code = -2 - mv
                    tv = Ft[dslot[pb]]
                    if tv < code // 100 or tv > code % 100:
                        continue
                if dact[pb] and mv < 0 and out[i, 2] >= 0:
                    tv = Ft[dslot[pb]]
                    j = Kp[pb, c]
                    if out[i, 2] == 1 and tv > j - dl[pb]:
                        continue
                    if out[i, 2] == 0 and tv < j + 1 - dl[pb]:
                        continue
                okc[i] = True
            order_all = np.argsort(tot)
            for i in range(nout):
                if okc[order_all[i]]:
                    trank[e] = i
                    break
            tcand[e] = nout
            order = order_all[:B]
            k2 = order.shape[0]
            F2 = F[out[order, 0]].copy(); K2 = K[out[order, 0]].copy(); Kp2 = Kp[out[order, 0]].copy()
            L2 = L[out[order, 0]].copy(); da2 = dact[out[order, 0]].copy(); dc2 = dcard[out[order, 0]].copy()
            ds2 = dslot[out[order, 0]].copy(); lo2 = mlo[out[order, 0]].copy(); hi2 = mhi[out[order, 0]].copy()
            dl2 = dl[out[order, 0]].copy(); cn2 = cnt[out[order, 0]].copy(); n2 = n[out[order, 0]].copy()
            is2 = isd[out[order, 0]].copy(); Q2 = Q[out[order, 0]].copy(); co2 = tot[order].copy()
            ok2 = okc[order].copy()
            for r in range(k2):
                apply_child(out[order[r]], c, g, F2, K2, Kp2, L2, da2, dc2, ds2, lo2, hi2, dl2, cn2, n2, is2, Q2, r)
            nb = k2
            F[:nb] = F2; K[:nb] = K2; Kp[:nb] = Kp2; L[:nb] = L2; dact[:nb] = da2; dcard[:nb] = dc2
            dslot[:nb] = ds2; mlo[:nb] = lo2; mhi[:nb] = hi2; dl[:nb] = dl2; cnt[:nb] = cn2; n[:nb] = n2
            isd[:nb] = is2; Q[:nb] = Q2; cost[:nb] = co2; ok[:nb] = ok2
            bestc[e] = co2[0]
            e += 1
    best = np.argmin(cost[:nb])
    return F[best].copy(), cost[best], Q[best].copy(), bestc[:e], trank[:e], tcand[:e]


def search(msgs, pairs, B=500, alpha=2.0, lam=15.0, Qt=None, Ft=None):
    from lazy_beam import prepare
    flat, starts, nev, cs, ca, cb = prepare(msgs, pairs)
    if Qt is None:
        Qt = np.full(flat.shape[0], -9, np.int64); Ft = np.zeros(N, np.int64)
    t = time.time()
    F, cost, Q, bestc, trank, tcand = run(flat, starts, B, alpha, lam, cs, ca, cb, B * 2 * N + 4 * N + 10, Qt, Ft)
    return F, cost, Q, time.time() - t, bestc, trank, tcand
