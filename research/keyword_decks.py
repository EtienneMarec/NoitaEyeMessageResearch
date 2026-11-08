"""Decks ordered by keywords taken from the game texts and the wiki (user's hypothesis:
the deck key might come from a detail of the game, even a minor one).

Sources (research/sources): game texts (gamedata/common.csv, English column + identifiers),
credits, magic_numbers.xml, debug_keys.txt, 148 wiki pages (gamedata/wiki), tablet texts
(Toboter Englishv4.txt), plus a few community words (lumikki, kolmisilmä...).
Keywords: each word (>= 3 letters) and each phrase (>= 8 letters).
Constructions (permutations of 83): letters A=0 in order of appearance then the rest;
ASCII+32 of the raw text then the rest; ASCII+32 in upper case; + the inverse of each.
Battery per permutation P:
  * starting deck = P, 8 rules, base shuffle identity or "cut one card", 2 orders;
  * base shuffle = P, sorted deck, 8 rules, 2 orders;
  * reinsertion with table F = P, sorted deck or = P, first trigram outside/inside the deck.
Score = max IoC of the read positions sequence (rule families) and min number of
distinct positions (reinsertion). Baseline: same tests on random permutations.
"""
import csv
import re
import sys
import time
import unicodedata
from pathlib import Path
import numpy as np
from stats import load_eyes
from deckcipher import recover_q, ioc83, N
from reinsert_scan import recover_q_reinsert

HERE = Path(__file__).parent
SRC = HERE / "sources"


def clean(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def texts():
    out = []
    with open(SRC / "gamedata/common.csv", encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if len(row) > 1:
                out.append(row[0].replace("_", " "))
                out.append(row[1].replace("\\n", " "))
    for fn in ("credits.txt", "debug_keys.txt", "magic_numbers.xml", "common_dev.csv"):
        out += (SRC / "gamedata" / fn).read_text(encoding="utf-8", errors="ignore").splitlines()
    for p in (SRC / "gamedata/wiki").glob("*.txt"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
        t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
        t = re.sub(r"<[^>]+>|'''?|==+|\[https?://\S+ ([^\]]*)\]", r" \1 ", t)
        out += t.splitlines()
    out += (SRC / "github/ToboterXP_EyeGlyphs/Englishv4.txt").read_text(encoding="utf-8", errors="ignore").splitlines()
    out += ["lumikki", "Lumikki", "LUMIKKI", "Kolmisilmä", "Kolmisilma", "AS ABOVE SO BELOW", "As above, so below",
            "Noita", "NOITA", "Nolla Games", "Petri Purho", "Arvi Teikari", "Olli Harjola", "silmä", "silmä-huone",
            "Hämis", "Sampo", "Minä", "Kantele", "Emerald Tablet", "The Work", "Seeker", "eyes", "EYES"]
    return [clean(t) for t in out if t and t.strip()]


def keywords(ts):
    kw = set()
    for t in ts:
        for w in re.findall(r"[A-Za-z]{3,}", t):
            kw.add(w)
        for ph in re.split(r"[.!?;:\n]", t):
            ph = ph.strip()
            if len(re.findall(r"[A-Za-z]", ph)) >= 8:
                kw.add(ph[:200])
    return sorted(kw)


def perm_letters(s):
    seq = []
    for ch in s.upper():
        if "A" <= ch <= "Z":
            v = ord(ch) - 65
            if v not in seq:
                seq.append(v)
    return seq


def perm_ascii(s):
    seq = []
    for ch in s:
        v = ord(ch) - 32
        if 0 <= v < N and v not in seq:
            seq.append(v)
    return seq


def complete(seq):
    rest = [x for x in range(N) if x not in set(seq)]
    return np.array(seq + rest, np.int64)


def perms_for(s):
    for name, seq in (("letters", perm_letters(s)), ("ascii", perm_ascii(s)), ("ascii_upper", perm_ascii(s.upper()))):
        if len(seq) >= 3:
            p = complete(seq)
            yield name, p
            inv = np.empty(N, np.int64); inv[p] = np.arange(N)
            yield name + "_inv", inv


def battery(P, arrs):
    ident = np.arange(N)
    rot1 = (ident + 1) % N
    best = 0.0
    for rule in range(8):
        for beta in (ident, rot1):
            for order in (0, 1):
                ic, _ = ioc83([recover_q(a, P, beta, rule, order)[1:] for a in arrs])
                best = max(best, ic)
        for order in (0, 1):
            ic, _ = ioc83([recover_q(a, ident, P, rule, order)[1:] for a in arrs])
            best = max(best, ic)
    mind = N
    for D0, start in ((ident, 1), (ident, 0), (P, 1), (P, 0)):
        v = np.concatenate([q[q >= 0] for q in (recover_q_reinsert(a, D0, P, ident, start) for a in arrs)])
        mind = min(mind, len(np.unique(v)))
    return best, mind


if __name__ == "__main__":
    names, M = load_eyes()
    arrs = [np.array(m, np.int64) for m in M]
    kws = keywords(texts())
    print(f"{len(kws)} distinct keywords", flush=True)
    seen, results = set(), []
    t0 = time.time()
    for i, k in enumerate(kws):
        for cname, P in perms_for(k):
            key = P.tobytes()
            if key in seen:
                continue
            seen.add(key)
            ic, d = battery(P, arrs)
            results.append((ic, d, cname, k))
        if i % 5000 == 0:
            print(f"  {i}/{len(kws)} keywords, {len(seen)} decks, {time.time()-t0:.0f} s", flush=True)
    rng = np.random.default_rng(0)
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    null = np.array([battery(rng.permutation(N), arrs) for _ in range(R)])
    mu, sd = null[:, 0].mean(), null[:, 0].std()
    print(f"\n{len(results)} decks tested. Baseline ({R} random): max IoC {mu:.3f} ± {sd:.3f}, "
          f"record {null[:,0].max():.3f}; min distinct positions {int(null[:,1].min())}")
    results.sort(key=lambda r: -r[0])
    print("Best IoC:")
    for ic, d, c, k in results[:15]:
        print(f"  {ic:.3f} (z={(ic-mu)/sd:+.1f})  {d:2d} pos.  [{c}]  {k[:70]!r}")
    results.sort(key=lambda r: r[1])
    print("Fewest distinct positions (reinsertion):")
    for ic, d, c, k in results[:8]:
        print(f"  {d:2d} pos.  IoC {ic:.3f}  [{c}]  {k[:70]!r}")
    # expected z for the max of n normal draws ~ sqrt(2 ln n)
    print(f"expected z for the best of {len(results)} trials by chance: ≈ {np.sqrt(2*np.log(len(results))):.1f}")
    print("For reference, a true mechanism on the testbed: IoC ≈ 5.5 and ~25 to 31 positions.")
