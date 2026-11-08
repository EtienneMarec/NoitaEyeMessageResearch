"""Compares, event by event, the cost of the true table (exact replay) with the beam's best cost."""
import sys
import numpy as np
from numba import njit
from testkey import make, true_blocks, N
from lazy_beam import prepare
import lazy_exact as LX

@njit(cache=True)
def true_cum(flat, starts, F, lam, cs, ca, cb):
    G = flat.shape[0]; cnt = np.zeros(N); n = 0.0; isd = np.zeros(N, np.bool_)
    for k in range(N):
        if F[k] >= 0: isd[F[k]] = True
    Q = -np.ones(G, np.int64); cum = np.zeros(G); cost = 0.0; e = 0
    D = np.empty(N, np.int64); P = np.empty(N, np.int64)
    for m in range(starts.shape[0] - 1):
        for k in range(N): D[k] = k; P[k] = k
        for g in range(starts[m] + 1, starts[m + 1]):
            q = P[flat[g]]
            cost += LX.crp(cnt, n, q, 2.0) + (LX.BIG if isd[q] else 0.0) + LX.blockpen(Q, g, q, cs, ca, cb, e, lam)
            cnt[q] += 1; n += 1; Q[g] = q
            c = D[q]; t = F[q]
            if t > q:
                for k in range(q, t): D[k] = D[k + 1]; P[D[k]] = k
            elif t < q:
                for k in range(q, t, -1): D[k] = D[k - 1]; P[D[k]] = k
            D[t] = c; P[c] = t
            cum[e] = cost; e += 1
    return cum[:e], Q

plains, C, F_true, reads = make()
pairs = [((a, i + k), (b, j + k)) for a, i, b, j, L in true_blocks(plains) for k in range(L)]
flat, starts, nev, cs, ca, cb = prepare(C, pairs)
tc, Qt = true_cum(flat, starts, F_true, 15.0, cs, ca, cb)
B = int(sys.argv[1]) if len(sys.argv) > 1 else 500
F, cost, Q, dt, bestc, trank, tcand = LX.search(C, pairs, B=B, Qt=Qt, Ft=F_true)
print(f"B={B}: correct {np.sum(F[reads]==F_true[reads])}/{len(reads)}; final beam cost {cost:.1f}, true table {tc[-1]:.1f} ({dt:.0f} s)")
first = next((e for e in range(len(tc)) if bestc[e] < tc[e] - 1e-6), None)
print("first event where the beam does BETTER than the truth (so where it may have been eliminated):", first)
for e in (5, 10, 20, 40, 80, 150, 300, 600, len(tc) - 1):
    print(f"  event {e:4d}: truth {tc[e]:8.1f}   best of beam {bestc[e]:8.1f}")

lost = next((e for e in range(len(trank)) if trank[e] < 0 or trank[e] >= B), None)
print("the true branch leaves the beam at event", lost)
if lost is not None:
    for e in range(max(0, lost - 8), min(len(trank), lost + 1)):
        print(f"  event {e:3d}: rank of the truth {trank[e]:6d} out of {tcand[e]:7d} candidates")
