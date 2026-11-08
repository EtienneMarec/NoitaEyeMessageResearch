"""Statistical fingerprint of a corpus of encrypted messages (lists of integers)."""
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def load_eyes():
    d = json.loads((HERE / "messages.json").read_text())
    return list(d.keys()), list(d.values())


def gap_counts(msgs, maxd=30):
    """Number of pairs c[i]==c[i+d] within one message, per distance d."""
    out = [0] * (maxd + 1)
    for m in msgs:
        for d in range(1, maxd + 1):
            out[d] += sum(1 for i in range(len(m) - d) if m[i] == m[i + d])
    return out


def gap_tests(msgs, maxd=30):
    out = [0] * (maxd + 1)
    for m in msgs:
        for d in range(1, maxd + 1):
            out[d] += max(0, len(m) - d)
    return out


def shared_mask(msgs):
    """Marks the positions whose symbol is identical to the same position in another message
    (shared segments), so they can be excluded from the repeat statistics."""
    mask = [[False] * len(m) for m in msgs]
    for a in range(len(msgs)):
        for b in range(len(msgs)):
            if a == b:
                continue
            for i in range(min(len(msgs[a]), len(msgs[b]))):
                if msgs[a][i] == msgs[b][i]:
                    mask[a][i] = True
    return mask


def ngram_repeats(msgs, n, skip_same_pos=True):
    """Number of repeated n-grams (occurrences beyond the first), ignoring
    repeats falling at the same position in different messages."""
    occ = defaultdict(list)
    for mi, m in enumerate(msgs):
        for i in range(len(m) - n + 1):
            occ[tuple(m[i:i + n])].append((mi, i))
    rep = 0
    for g, lst in occ.items():
        if len(lst) < 2:
            continue
        if skip_same_pos:
            pos = {i for _, i in lst}
            if len(pos) < 2:
                continue
            rep += len(pos) - 1
        else:
            rep += len(lst) - 1
    return rep


def ioc(msgs, alpha=83):
    c = Counter(v for m in msgs for v in m)
    n = sum(c.values())
    return alpha * sum(x * (x - 1) for x in c.values()) / (n * (n - 1))


def canon(w):
    seen = {}
    return tuple(seen.setdefault(x, len(seen)) for x in w)


def isomorphs(msgs, L=10, min_rep=3):
    """Pairs of windows of length L with the same repeat pattern (>= min_rep repeated
    letters), which are not identical ciphertext. Returns the list of pairs."""
    buckets = defaultdict(list)
    for mi, m in enumerate(msgs):
        for i in range(len(m) - L + 1):
            w = m[i:i + L]
            p = canon(w)
            nrep = L - len(set(w))
            if nrep >= min_rep:
                buckets[p].append((mi, i, tuple(w)))
    pairs = []
    for p, lst in buckets.items():
        for x in range(len(lst)):
            for y in range(x + 1, len(lst)):
                a, b = lst[x], lst[y]
                if a[2] == b[2]:
                    continue
                if a[0] == b[0] and abs(a[1] - b[1]) < L:
                    continue
                pairs.append((a[0], a[1], b[0], b[1]))
    return pairs


def fingerprint(msgs, tail=0):
    """tail>0: only uses m[tail:] (the part after the shared segments)."""
    ms = [m[tail:] for m in msgs]
    gc, gt = gap_counts(ms), gap_tests(ms)
    return {
        "n": sum(len(m) for m in ms),
        "ioc": round(ioc(ms), 3),
        "gap_rate_x1000": [round(1000 * gc[d] / gt[d], 1) if gt[d] else 0 for d in range(1, 13)],
        "gap_counts": gc[1:13],
        "digraph_rep": ngram_repeats(ms, 2),
        "trigraph_rep": ngram_repeats(ms, 3),
        "isomorphs_L10": len(isomorphs(ms, 10, 3)),
    }


if __name__ == "__main__":
    names, msgs = load_eyes()
    for t in (0, 50):
        print(f"== eyes, from position {t} ==")
        for k, v in fingerprint(msgs, t).items():
            print(f"  {k}: {v}")
    print("\nIsomorphs L=10 (>=3 repeats):")
    for a, i, b, j in isomorphs(msgs, 10, 3):
        print(f"  {names[a]}@{i}  ~  {names[b]}@{j}   {msgs[a][i:i+10]}  {msgs[b][j:j+10]}")
