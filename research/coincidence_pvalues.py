"""P-values of the eyes' coincidences after a divergence, on the window CHOSEN IN ADVANCE (+1..+20) (§32).

Eyes: 7/169 (between groups), 12/301 (without E1/W1 and E4/E5). Rates of the space model (random σ) on
+1..+20: 0.017 (space_joint_test, first symbol inside), 0.019 (outside), up to 0.026–0.030 depending on the text.
P = binomial probability of at least as many coincidences."""
from math import comb


def ge(k, n, p):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


if __name__ == "__main__":
    for r in (0.017, 0.019, 0.026, 0.030):
        print(f"rate {r}: P(>=7 | 169) = {ge(7, 169, r):.3f}; P(>=12 | 301) = {ge(12, 301, r):.4f}")
