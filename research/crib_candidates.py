"""Generation of probable texts taken from the game data (§38).

Sources: common.csv (English column: all the game texts) and the wiki pages (sources/gamedata/wiki).
Normalisation: upper case, any run of characters outside A-Z replaced by "_" (space).
Candidates: windows of L characters starting at each word start (after a space or at the start of a text),
deduplicated. Writes crib_candidates_L{L}.txt (one window per line)."""
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent


def norm(s):
    s = s.upper().replace("\\N", " ")
    s = re.sub(r"[^A-Z]+", "_", s)
    return s.strip("_")


def texts():
    out = []
    with open(HERE / "sources/gamedata/common.csv", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        header = next(r)
        en = header.index("en")
        for row in r:
            if len(row) > en and row[en].strip():
                out.append(norm(row[en]))
    for p in (HERE / "sources/gamedata/wiki").glob("*.txt"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        for para in re.split(r"\n\s*\n", t):
            n = norm(para)
            if n:
                out.append(n)
    return out


if __name__ == "__main__":
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 75
    T = texts()
    cands = set()
    for s in T:
        s = s + "_"
        starts = [0] + [i + 1 for i, ch in enumerate(s) if ch == "_"]
        for i in starts:
            w = s[i:i + L]
            if len(w) == L:
                cands.add(w)
    cands = sorted(cands)
    (HERE / f"crib_candidates_L{L}.txt").write_text("\n".join(cands), encoding="utf-8")
    print(f"{len(T)} texts, {len(cands)} candidate windows of {L} characters")
    print("examples:", cands[:3])
