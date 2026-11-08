"""Why are the 241 favourite combinations of §45 mostly cuts of about a quarter of the deck? (§48)

Hypothesis: with β = rotation by k cards and consecutive read positions (convention), a card read at t is
re-read at t + d (no space between) iff the letters' ranks differ by ±(d·k mod 83). A quarter cut
(4k ≡ ±small mod 83) makes repeats at d = 4 frequent (letters of neighbouring ranks) and those at d = 2 rare
(2k ≈ 41: no pair of ranks that far apart in a 36-symbol alphabet). For the β that are rotations, we compare the
distribution of r4 = min(4k mod 83, 83 - 4k mod 83) and r2 = min(2k mod 83, ...) among the 241 favourites, among
all the survivors of §42, and among the 38,808 starting combinations."""
import csv
import glob
from collections import Counter

N = 83


def r(k, d):
    v = (d * k) % N
    return min(v, N - v)


def rows_top():
    out = []
    for f in glob.glob("convention_top_out_*.tsv"):
        for l in open(f, encoding="utf-8"):
            a, o, b, s, acc, *_ = l.rstrip("\n").split("\t")
            if float(acc) >= 0.3:
                out.append(b)
    return out


if __name__ == "__main__":
    allrows = list(csv.DictReader(open("known_q_local_filter_out.tsv", encoding="utf-8"), delimiter="\t"))
    surv = [x["beta"] for x in allrows if min(float(x["P1"]), float(x["P2"]), float(x["P3"])) >= 0.05]
    groups = {"241 favourites (§45)": rows_top(), "3,814 survivors (§42)": surv,
              "38,808 starting": [x["beta"] for x in allrows]}
    for lab, betas in groups.items():
        rot = [int(b[3:]) for b in betas if b.startswith("rot")]
        r4 = Counter(min(r(k, 4), 20) for k in rot); r2 = Counter(min(r(k, 2), 20) for k in rot)
        share_rot = len(rot) / len(betas)
        small4 = sum(1 for k in rot if r(k, 4) <= 13) / max(len(rot), 1)
        small2 = sum(1 for k in rot if r(k, 2) <= 13) / max(len(rot), 1)
        print(f"{lab}: {len(betas)} combinations, share of β rotations {share_rot:.2f}; among the rotations, "
              f"|4k mod 83| ≤ 13: {small4:.2f}; |2k mod 83| ≤ 13: {small2:.2f}")
    print("reference: rotations k = 1..82 uniform: |4k| ≤ 13:", f"{sum(1 for k in range(1, 83) if r(k, 4) <= 13) / 82:.2f}",
          "; |2k| ≤ 13:", f"{sum(1 for k in range(1, 83) if r(k, 2) <= 13) / 82:.2f}")
    top = Counter(int(b[3:]) for b in rows_top() if b.startswith("rot"))
    print("most frequent rotations among the favourites (k: count, 4k mod 83 folded):",
          ", ".join(f"{k}:{n} ({r(k, 4)})" for k, n in top.most_common(12)))
