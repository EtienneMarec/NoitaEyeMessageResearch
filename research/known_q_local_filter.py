"""Local filter of the natural pairs (β, σ) under the "known read positions" convention (§42).

In the space model (D' = D∘S_x after reading symbol x at position q_x), the card read at t+d equals
the one read at t iff S_{x_t} S_{x_t+1} … S_{x_t+d-1} [q_{x_t+d}] = q_{x_t} (composition of arrays). The
condition depends only on the (d+1)-gram of plaintext: the expected number of repeats at distance d is
therefore λ_d = Σ_{(d+1)-grams} n(gram) · [condition], with no simulation and no key.
Eyes (without symbol 0): doubles d = 1, repeats d = 2, 3. Frequencies: English text of the testbed (with
spaces), scaled to the eyes' number of (d+1)-grams. The filter of §37.4 drew q at random; here q follows a
convention (symbol of rank k read at position k, or 82 - k), alphabets "A-Z 1-9 _", "_ A-Z 1-9" and the
runic order "BDMAGICK…". Output: P(Poisson ≤ eyes' count) per (convention, β, σ); list of survivors.
Usage: python known_q_local_filter.py   (control: python -c "import known_q_local_filter as k; k.validate()")"""
from collections import Counter
import math
import numpy as np
import testbed_spaces as tbs
from deckcipher import base_shuffles
from stats import load_eyes

N = 83
DIG = "123456789"
ALPHAS = {"AZ19_": "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + DIG + "_",
          "_AZ19": "_ABCDEFGHIJKLMNOPQRSTUVWXYZ" + DIG,
          "MAGICK19_": "BDMAGICKEFHJLNOPQRSTUVWXYZ" + DIG + "_"}


def eyes_counts(M, dmax=3):
    out = []
    for d in range(1, dmax + 1):
        rep = sum(m[t] == m[t + d] for m in M for t in range(1, len(m) - d))
        tot = sum(max(0, len(m) - 1 - d) for m in M)
        out.append((rep, tot))
    return out


def gram_counts(T, d):
    return Counter(T[i:i + d + 1] for i in range(len(T) - d))


def pois_le(k, lam):
    return sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))


def lam(grams, total, scale, q, Sb, Ss, sp):
    """λ = scale · Σ n(g)·[repeat] for (d+1)-grams g = x0 x1 … xd (arrays: g (G, d+1), n (G,))."""
    g, n = grams
    p = q[g[:, -1]]
    for j in range(g.shape[1] - 2, -1, -1):
        p = np.where(g[:, j] == sp, Ss[p], Sb[p])
    return scale * float(n[p == q[g[:, 0]]].sum()) / total


if __name__ == "__main__":
    names, M = load_eyes()
    E = eyes_counts(M)
    print("eyes (without symbol 0): " + ", ".join(f"d={d + 1}: {r}/{t}" for d, (r, t) in enumerate(E)))
    T = tbs.english_with_spaces()[:2_000_000]
    BS = base_shuffles(); keys = [k for k in BS if k != "id"]
    rows = []
    for an, alpha in ALPHAS.items():
        Tm = "".join(ch for ch in T if ch in alpha)
        G = []
        for d in (1, 2, 3):
            g = gram_counts(Tm, d)
            ks = list(g)
            G.append(((np.array([[alpha.index(c) for c in k] for k in ks]), np.array([g[k] for k in ks], float)),
                      sum(g.values())))
        sp = alpha.index("_")
        for orient in ("k", "82-k"):
            q = np.arange(len(alpha)) if orient == "k" else N - 1 - np.arange(len(alpha))
            for b in keys:
                for s in keys:
                    if s == b or (b.startswith("rot") and s.startswith("rot")):
                        continue
                    ps, lams = [], []
                    for d in range(3):
                        l = lam(G[d][0], G[d][1], E[d][1], q, BS[b], BS[s], sp)
                        lams.append(l); ps.append(pois_le(E[d][0], l))
                    rows.append((an, orient, b, s, lams, ps))
        print(f"{an} done", flush=True)
    with open("known_q_local_filter_out.tsv", "w", encoding="utf-8") as f:
        f.write("alphabet\torient\tbeta\tsigma\tlam1\tlam2\tlam3\tP1\tP2\tP3\n")
        for r in rows:
            f.write("\t".join([r[0], r[1], r[2], r[3]] + [f"{v:.3g}" for v in r[4]] + [f"{v:.3g}" for v in r[5]]) + "\n")
    print(f"{len(rows)} combinations (convention × pair)")
    for thr in (0.05, 0.01):
        ok = [r for r in rows if min(r[5]) >= thr]
        print(f"survivors (P ≥ {thr} for d = 1, 2, 3): {len(ok)}; per convention: "
              + ", ".join(f"{a}/{o} {sum(1 for r in ok if r[0] == a and r[1] == o)}" for a in ALPHAS for o in ("k", "82-k")))
    ok1 = [r for r in rows if r[5][0] >= 0.05]
    print(f"survivors of the doubles test alone (P ≥ 0.05): {len(ok1)}")


def validate(npairs=5, seed=3):
    """Control: analytic λ against simulated counts on the testbed (same convention, random pairs)."""
    import random
    from explore import xgak_encrypt
    rnd = random.Random(seed)
    alpha = tbs.ALPHA_S; sp = alpha.index("_")
    q = np.arange(len(alpha))
    T = tbs.english_with_spaces()[:2_000_000]
    G = []
    for d in (1, 2, 3):
        g = gram_counts(T, d); ks = list(g)
        G.append(((np.array([[alpha.index(c) for c in k] for k in ks]), np.array([g[k] for k in ks], float)),
                  sum(g.values())))
    BS = base_shuffles(); keys = [k for k in BS if k != "id" and not k.startswith("rot")]
    for _ in range(npairs):
        b, s = rnd.sample(keys, 2)
        S = np.array([BS[s] if ch == "_" else BS[b] for ch in alpha], np.int64)
        sim = np.zeros(3); tot = np.zeros(3)
        for seed2 in range(10):
            pl = tbs.build_plaintexts(seed=seed2, word_start=True)
            C = [xgak_encrypt(np.array([alpha.index(ch) for ch in m], np.int64), q, S).tolist() for m in pl]
            for d in range(3):
                sim[d] += sum(m[t] == m[t + d + 1] for m in C for t in range(1, len(m) - d - 1))
                tot[d] += sum(max(0, len(m) - 2 - d) for m in C)
        an = [lam(G[d][0], G[d][1], tot[d], q, BS[b], BS[s], sp) for d in range(3)]
        print(f"  β={b:14s} σ={s:14s} simulated {sim.astype(int).tolist()}  analytic {[round(v, 1) for v in an]}", flush=True)
