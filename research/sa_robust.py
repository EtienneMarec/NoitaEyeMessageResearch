"""Simulated annealing on the starting deck, with robust space decisions (one beam per message) (§36).

Score of a deck x: sum, over the messages, of the best decision path (keyed_deck_robust.decide:
letter → log φ(r), space → r = q_space else penalty), with φ the frequencies of the "letter" reads
of the best current state (recomputed periodically). Move: swap of the start positions of two
cards. A misplaced card only costs a local penalty: the landscape should be smoother.
Then, if annealing reaches the basin (≥ 75–85% correct), keyed_deck_robust.robust_em finishes.
Validation on the testbed with spaces, q_space given."""
import sys
import math
import numpy as np
from numba import njit
from keyed_deck_attack import tables, flatten, N
from keyed_deck_robust import decide, reads, robust_em, PESP, EPS
import testbed_spaces as tbs
from explore import xgak_encrypt


@njit(cache=True)
def path_score(C, starts, lens, x, binv, sinv, qs, logphi, Bw):
    sp = decide(C, starts, lens, x, binv, sinv, qs, logphi, Bw)
    r = reads(C, starts, lens, x, binv, sinv, sp)
    s = 0.0
    lpe = math.log(PESP); lpl = math.log(1 - PESP); leps = math.log(EPS)
    for t in range(C.shape[0]):
        if sp[t]:
            s += lpe + (0.0 if r[t] == qs else leps)
        else:
            s += lpl + logphi[r[t]] + (leps if r[t] == qs else 0.0)
    return s, sp, r


def phi_from(r, sp, qs):
    cnt = np.bincount(r[~sp], minlength=N).astype(float); cnt[qs] = 0
    return np.log((cnt + 0.5) / (cnt.sum() + 0.5 * N))


def anneal(C, starts, lens, x, binv, sinv, qs, iters, rng, Bw=8, t0=8.0, t1=0.3, refresh=1000, x_true=None):
    logphi = np.zeros(N) - math.log(N)
    cur, sp, r = path_score(C, starts, lens, x, binv, sinv, qs, logphi, Bw)
    logphi = phi_from(r, sp, qs)
    cur, sp, r = path_score(C, starts, lens, x, binv, sinv, qs, logphi, Bw)
    for it in range(iters):
        temp = t0 * (t1 / t0) ** (it / iters)
        i, j = rng.integers(N), rng.integers(N)
        x[i], x[j] = x[j], x[i]
        new, sp2, r2 = path_score(C, starts, lens, x, binv, sinv, qs, logphi, Bw)
        if new >= cur or rng.random() < math.exp((new - cur) / temp):
            cur, sp, r = new, sp2, r2
        else:
            x[i], x[j] = x[j], x[i]
        if (it + 1) % refresh == 0:
            logphi = phi_from(r, sp, qs)
            cur, sp, r = path_score(C, starts, lens, x, binv, sinv, qs, logphi, Bw)
            if x_true is not None and (it + 1) % (refresh * 10) == 0:
                print(f"   it {it + 1}: score {cur:.0f}, correct positions {int((x == x_true).sum())}/83, "
                      f"distinct read positions {len(set(r.tolist()))}", flush=True)
    return x


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    names, BS, inv = tables()
    rng = np.random.default_rng(3)
    pl = tbs.build_plaintexts()
    sp_true = np.array([ch == "_" for m in pl for ch in m])
    bname, sname = "rot1", "deal3fwd"
    D0 = rng.permutation(N)
    q = rng.choice(N, len(tbs.ALPHA_S), replace=False).astype(np.int64)
    S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
    msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
    C, starts, lens = flatten(msgs)
    x_true = np.empty(N, np.int64); x_true[D0] = np.arange(N)
    qs = int(q[tbs.ALPHA_S.index("_")])
    x = rng.permutation(N).astype(np.int64)
    x = anneal(C, starts, lens, x, inv[bname], inv[sname], qs, iters, rng, x_true=x_true)
    print(f"after annealing: correct positions {int((x == x_true).sum())}/83")
    xf, sp = robust_em(C, starts, lens, x.copy(), qs, inv[bname], inv[sname])
    print(f"after robust EM: correct positions {int((xf == x_true).sum())}/83, correct decisions {int((sp == sp_true).sum())}/{len(sp_true)}")
