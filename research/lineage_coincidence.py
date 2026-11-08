"""Coincidences after a divergence, counted by LINEAGES (§26).

At each position i, a lineage = group of messages whose ciphertexts are identical over 1..i-1.
A "trial" = a pair of distinct lineages whose divergence d (first position where they differ)
satisfies 1 <= i-d <= W ("proche", near) or i-d > W2 ("lointain", far). Success if a symbol at i is shared by both.
Chance: about 1/83 per trial. We distinguish (mode tokens):
  - "toutes": all lineages;
  - "sans E1/W1 et E4/E5": without the pairs E1/W1 and E4/E5 (obstacle and stutter, already known resynchronisations);
  - "groupes": only pairs from different GROUPS (A = E1/W1/E2, B = W2/E3/W3, C = E4/W4/E5), whose texts
    a priori have nothing in common after the divergence.
Random baseline: same computations over 2,000 corpora of the same lengths, shared openings copied,
the rest drawn at random without doubles."""
import numpy as np
from stats import load_eyes

W, W2 = 20, 30
names, M = load_eyes()
GROUP = {"E1": "A", "W1": "A", "E2": "A", "W2": "B", "E3": "B", "W3": "B", "E4": "C", "W4": "C", "E5": "C"}


def count(M, names, mode):
    tr = {"proche": 0, "lointain": 0}; su = {"proche": 0, "lointain": 0}
    L = max(len(m) for m in M)
    for i in range(1, L):
        idx = [k for k in range(len(M)) if len(M[k]) > i]
        lin = {}
        for k in idx:
            lin.setdefault(tuple(M[k][1:i]), []).append(k)
        groups = list(lin.values())
        for x in range(len(groups)):
            for y in range(x + 1, len(groups)):
                A, B = groups[x], groups[y]
                a, b = M[A[0]], M[B[0]]
                d = next(j for j in range(1, i) if a[j] != b[j])
                na = {names[k] for k in A}; nb = {names[k] for k in B}
                if mode != "toutes" and ({"E1", "W1"} <= na | nb and (na == {"E1"} or nb == {"E1"} or na == {"W1"} or nb == {"W1"})
                                         and ({"E1", "W1"} & na and {"E1", "W1"} & nb)):
                    continue
                if mode != "toutes" and ({"E4", "E5"} & na and {"E4", "E5"} & nb and not ({"W4"} & (na | nb))):
                    continue
                if mode == "groupes" and {GROUP[n] for n in na} == {GROUP[n] for n in nb}:
                    continue
                zone = "proche" if 1 <= i - d <= W else ("lointain" if i - d > W2 else None)
                if zone is None:
                    continue
                tr[zone] += 1
                su[zone] += bool({M[k][i] for k in A} & {M[k][i] for k in B})
    return tr, su


def random_corpus(rng):
    out = []
    for m in M:
        out.append(list(m))
    # copy the shared openings, draw the rest at random without doubles
    for k, m in enumerate(M):
        r = list(m[:1])
        for i in range(1, len(m)):
            same = [j for j in range(k) if len(M[j]) > i and M[j][1:i + 1] == m[1:i + 1]]
            if same:
                r.append(out[same[0]][i])
            else:
                while True:
                    v = int(rng.integers(83))
                    if v != r[-1]:
                        break
                r.append(v)
        out[k] = r
    return out


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    for mode in ("toutes", "sans E1/W1 et E4/E5", "groupes"):
        tr, su = count(M, names, mode)
        sims = [count(random_corpus(rng), names, mode)[1]["proche"] for _ in range(2000)]
        sims = np.array(sims)
        print(f"{mode:22s}: near {su['proche']}/{tr['proche']} ({su['proche'] / max(tr['proche'], 1):.3f}), "
              f"far {su['lointain']}/{tr['lointain']} ({su['lointain'] / max(tr['lointain'], 1):.3f}); "
              f"random near: mean {sims.mean():.1f}, P(>= {su['proche']}) = {(sims >= su['proche']).mean():.4f}", flush=True)
