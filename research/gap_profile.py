"""Profile of repeats at distance d (c[i] == c[i+d] within one message), deduplicated.

In a "deck of cards" cipher (GAK over S83), a repeat at distance d means that the top card came back
to the top after d shuffles: the profile is therefore a fingerprint of the structure of the
permutations.

Deduplication: a pair (i, i+d) is ignored if the same pair of symbols at the same positions
already exists in an earlier message (shared sections).
Baseline: random sequences without doubles, same lengths.
"""
import random
import sys
from stats import load_eyes

names, M = load_eyes()
MAXD = int(sys.argv[1]) if __name__ == "__main__" and len(sys.argv) > 1 else 40


def profile(msgs, dedup=True):
    cnt = [0] * (MAXD + 1)
    tests = [0] * (MAXD + 1)
    seen = set()
    for m in msgs:
        for d in range(1, MAXD + 1):
            for i in range(len(m) - d):
                key = (i, d, m[i], m[i + d])
                if dedup and key in seen:
                    continue
                seen.add(key)
                tests[d] += 1
                cnt[d] += m[i] == m[i + d]
    return cnt, tests


def random_msgs():
    out = []
    for m in M:
        s = [random.randrange(83)]
        while len(s) < len(m):
            v = random.randrange(83)
            if v != s[-1]:
                s.append(v)
        out.append(s)
    return out


if __name__ == "__main__":
    random.seed(1)
    obs, tests = profile(M)
    R = 400
    sims = [profile(random_msgs(), dedup=False)[0] for _ in range(R)]
    print(" d  obs   expected  z     rate/1000")
    for d in range(1, MAXD + 1):
        # expected: same number of tests as observed
        mean = sum(s[d] for s in sims) / R
        tr = sum(len(m) - d for m in M if len(m) > d)
        exp = mean * tests[d] / tr if tr else 0
        var = exp  # ~Poisson
        z = (obs[d] - exp) / var ** 0.5 if var > 0 else 0
        flag = " <==" if abs(z) >= 3 else (" <-" if abs(z) >= 2 else "")
        print(f"{d:2d} {obs[d]:4d} {exp:8.1f} {z:6.2f} {1000*obs[d]/tests[d]:8.1f}{flag}")
    tot = sum(obs[2:])
    print("total d=2..", MAXD, ":", tot, " expected", round(sum(sum(s[2:]) for s in sims) / R * sum(tests[2:]) / sum(sum(len(m) - d for m in M if len(m) > d) for d in range(2, MAXD + 1)), 1))
