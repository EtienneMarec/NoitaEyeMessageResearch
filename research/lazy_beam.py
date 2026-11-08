"""LAZY search for the reinsertion table (model of §8/§10: sorted deck, no base shuffle, first symbol
outside the deck, one read position per letter).

Principle: when a card is read at a position q whose destination F[q] is unknown, we do NOT
choose F[q]: the card is put on hold (removed from the simulated deck). We only decide
when the ciphertext READS THIS CARD AGAIN: at that moment, the 83 values of F[q] are evaluated by an
exact replay from the start, and so are separated by what is observed.
While cards are on hold, the real rank of a card read is unknown up to δ
(δ = number of held cards placed before it): δ is chosen greedily by
preferring a position already read (heuristic; corrected by the exact replay after each decision).
Hypotheses are compared at the same point of the decryption (cumulative cost).
Cost: "Chinese restaurant" likelihood + penalty if a destination is read + penalty per
violated block equality (pairs of positions that must read the same position).
"""
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
def replay(flat, starts, F, alpha, lam, chk_start, chk_a, chk_b, cum):
    """Replays the events (messages in sequence, first symbol of each message skipped).
    Fills cum[e] = cumulative cost after event e. Returns (event reached, slot to
    decide or -1). Stops right BEFORE the event that re-reads a held card."""
    cnt = np.zeros(N); n = 0.0; isdest = np.zeros(N, np.bool_)
    for k in range(N):
        if F[k] >= 0:
            isdest[F[k]] = True
    Qev = -np.ones(flat.shape[0], np.int64)       # q read at each global position
    cost = 0.0
    order = np.empty(N, np.int64); pos = np.empty(N, np.int64); defslot = np.empty(N, np.int64)
    e = 0
    for m in range(starts.shape[0] - 1):
        for k in range(N):
            order[k] = k; pos[k] = k; defslot[k] = -1
        L = N; D = 0
        for g in range(starts[m] + 1, starts[m + 1]):
            c = flat[g]
            if defslot[c] >= 0:
                return e, defslot[c]
            j = pos[c]
            q = j
            for d in range(D + 1):
                if j + d < N and cnt[j + d] > 0 and not isdest[j + d]:
                    q = j + d
                    break
            cost += crp(cnt, n, q, alpha)
            if isdest[q]:
                cost += BIG
            cnt[q] += 1; n += 1
            Qev[g] = q
            for h in range(chk_start[e], chk_start[e + 1]):
                if Qev[chk_a[h]] != Qev[chk_b[h]]:
                    cost += lam
            # remove c from the known order
            for k in range(j, L - 1):
                order[k] = order[k + 1]; pos[order[k]] = k
            L -= 1
            t = F[q]
            if t >= 0:
                ti = min(t, L)
                for k in range(L, ti, -1):
                    order[k] = order[k - 1]; pos[order[k]] = k
                order[ti] = c; pos[c] = ti; L += 1
            else:
                defslot[c] = q; pos[c] = -1; D += 1
            cum[e] = cost
            e += 1
    return e, -1


def prepare(msgs, pairs):
    flat = np.array([v for m in msgs for v in m], np.int64)
    starts = np.cumsum([0] + [len(m) for m in msgs]).astype(np.int64)
    gidx = {}
    ev = 0
    ev_of = {}
    for m in range(len(msgs)):
        for i in range(1, len(msgs[m])):
            ev_of[(m, i)] = ev
            gidx[(m, i)] = int(starts[m]) + i
            ev += 1
    buckets = [[] for _ in range(ev)]
    for (a, i), (b, j) in pairs:
        if (a, i) in ev_of and (b, j) in ev_of:
            buckets[max(ev_of[(a, i)], ev_of[(b, j)])].append((gidx[(a, i)], gidx[(b, j)]))
    chk_start = np.cumsum([0] + [len(x) for x in buckets]).astype(np.int64)
    fl = [x for bk in buckets for x in bk] or [(0, 0)]
    arr = np.array(fl, np.int64)
    return flat, starts, ev, chk_start, arr[:, 0].copy(), arr[:, 1].copy()


@njit(cache=True)
def expand(flat, starts, parents, slots, alpha, lam, chk_start, chk_a, chk_b, nev):
    """For each parent, tries the 83 destinations of the slot to decide."""
    P = parents.shape[0]
    kids = np.empty((P * N, N), np.int64)
    reach = np.empty(P * N, np.int64); nxt = np.empty(P * N, np.int64)
    cums = np.empty((P * N, nev))
    k = 0
    for p in range(P):
        s = slots[p]
        for t in range(N):
            if t == s:
                continue
            F = parents[p].copy(); F[s] = t
            cum = np.full(nev, np.inf)
            r, ns = replay(flat, starts, F, alpha, lam, chk_start, chk_a, chk_b, cum)
            kids[k] = F; reach[k] = r; nxt[k] = ns; cums[k] = cum
            k += 1
    return kids[:k], reach[:k], nxt[:k], cums[:k]


def search(msgs, pairs, B=200, alpha=2.0, lam=15.0, verbose=True, F_true=None, reads=None):
    flat, starts, nev, cs, ca, cb = prepare(msgs, pairs)
    F0 = -np.ones(N, np.int64)
    cum = np.full(nev, np.inf)
    r, s = replay(flat, starts, F0, alpha, lam, cs, ca, cb, cum)
    beam = [(F0, r, s, cum)]
    rounds = 0
    t0 = time.time()
    while any(b[2] >= 0 for b in beam):
        rounds += 1
        done = [b for b in beam if b[2] < 0]
        todo = [b for b in beam if b[2] >= 0]
        parents = np.array([b[0] for b in todo]); slots = np.array([b[2] for b in todo], np.int64)
        kids, reach, nxt, cums = expand(flat, starts, parents, slots, alpha, lam, cs, ca, cb, nev)
        cand = [(kids[i], int(reach[i]), int(nxt[i]), cums[i]) for i in range(len(kids))] + done
        emin = min(c[1] for c in cand)
        if emin == 0:
            key = lambda c: 0.0
        else:
            key = lambda c: c[3][emin - 1]
        cand.sort(key=key)
        beam = cand[:B]
        if verbose and (rounds % 5 == 0 or not any(b[2] >= 0 for b in beam)):
            best = beam[0]
            msg = f"  round {rounds:3d}: common event {emin}/{nev}, cost {key(best):.1f}"
            if F_true is not None:
                Fb = best[0]
                known = reads[Fb[reads] >= 0]
                msg += (f", fixed destinations {len(known)}/{len(reads)}, "
                        f"correct {np.sum(Fb[reads] == F_true[reads])}")
            print(msg + f"  ({time.time()-t0:.0f} s)", flush=True)
    best = min(beam, key=lambda c: c[3][c[1] - 1] if c[1] > 0 else 0)
    return best[0], best[3][best[1] - 1]
