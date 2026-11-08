"""Insertion correspondences and cycles of the natural shuffles (§35, step 1).

Space model: if Y = X with one inserted LETTER (same space structure afterwards), the correspondence between
shifted shared blocks is π = D_i β D_i⁻¹ (D_i = deck of X at the moment of the insertion), whatever
follows (as long as only letters differ). π is thus a conjugate of β: its chains (sequences c → π(c) → …)
must fit into the cycles of β, without overlap. This test depends neither on the starting deck nor on the spaces.
(If the inserted symbol is a space, replace β by σ.)

Data (0-indexed positions, blocks of §6 and cycle_structure, edges trimmed by 2):
  π1 = E4 → E5 (shift +1) on C2, C3a, C3b, X;
  π2 = E5 → W4 (shift +1) on C2.
For each natural shuffle (116), we test whether the chains of π1 (and π2) fit into its cycles."""
import numpy as np
from stats import load_eyes
from deckcipher import base_shuffles

N = 83
TRIM = 2
BL1 = [("E4", 47, "E5", 48, 18), ("E4", 68, "E5", 69, 22), ("E4", 90, "E5", 91, 8), ("E4", 72, "E5", 73, 28)]
BL2 = [("E5", 48, "W4", 49, 18)]


def pairs(N_, blocks):
    m = {}
    bad = 0
    for a, i, b, j, L in blocks:
        for k in range(TRIM, L - TRIM):
            x, y = N_[a][i + k], N_[b][j + k]
            if x in m and m[x] != y:
                bad += 1
            m[x] = y
    return m, bad


def chains(m):
    inv = {v: k for k, v in m.items()}
    out = []
    seen = set()
    for s in m:
        if s in inv:      # not the start of a chain
            continue
        ch = [s]
        while ch[-1] in m:
            ch.append(m[ch[-1]])
            if ch[-1] == s:
                break
        out.append(ch); seen.update(ch)
    cyc = []
    for s in m:            # closed cycles
        if s not in seen:
            c = [s]
            while m[c[-1]] != s:
                c.append(m[c[-1]])
            seen.update(c); cyc.append(c)
    return out, cyc


def cycle_lengths(p):
    seen = np.zeros(N, bool); L = []
    for i in range(N):
        if not seen[i]:
            l = 0; j = i
            while not seen[j]:
                seen[j] = True; j = p[j]; l += 1
            L.append(l)
    return sorted(L, reverse=True)


def fits(paths, closed, cyc):
    """the observed closed cycles must equal a cycle of β; the paths (number of cards) fit into the
    remaining cycles (sum per cycle <= length; a path as long as a cycle is allowed)."""
    cyc = list(cyc)
    for c in closed:
        if len(c) in cyc:
            cyc.remove(len(c))
        else:
            return False
    rest = sorted((len(p) for p in paths), reverse=True)
    caps = sorted(cyc, reverse=True)

    def place(i, caps):
        if i == len(rest):
            return True
        tried = set()
        for k, cap in enumerate(caps):
            if cap >= rest[i] and cap not in tried:
                tried.add(cap)
                nc = list(caps); nc[k] -= rest[i]
                if place(i + 1, nc):
                    return True
        return False
    return place(0, caps)


if __name__ == "__main__":
    names, M = load_eyes(); Nd = dict(zip(names, M))
    BS = base_shuffles()
    for lab, bl in (("π1 = E4→E5", BL1), ("π2 = E5→W4", BL2)):
        m, bad = pairs(Nd, bl)
        p, c = chains(m)
        print(f"{lab}: {len(m)} pairs, {bad} inconsistencies, {len(p)} chains (lengths {sorted((len(x) for x in p), reverse=True)}), "
              f"{len(c)} closed cycles {[len(x) for x in c]}")
    m1, _ = pairs(Nd, BL1); p1, c1 = chains(m1)
    m2, _ = pairs(Nd, BL2); p2, c2 = chains(m2)
    ok = []
    for k, perm in BS.items():
        cl = cycle_lengths(perm)
        f1 = fits(p1, c1, cl); f2 = fits(p2, c2, cl)
        if f1 and f2:
            ok.append(k)
    print(f"natural shuffles compatible with π1 and π2: {len(ok)}/{len(BS)}")
    nonrot = [k for k in ok if not k.startswith("rot")]
    print("   excluding rotations:", nonrot)
    print("   compatible rotations:", sum(1 for k in ok if k.startswith("rot")), "/ 82")
