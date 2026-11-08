"""Probable texts taken from the alchemical texts and the Kalevala (sources/texts) (§38).

Normalisation: upper case; English: any run outside A-Z becomes "_"; Finnish: Ä, Ö, Å are kept too.
Project Gutenberg headers and footers are removed. For the Kalevala, each verse is one line:
verses are joined by a space (the text flows from verse to verse).
Candidates: windows of L characters starting at each word start, deduplicated.
Writes crib_cand_{name}_L{L}.txt for each source."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "sources/texts"


def strip_gutenberg(t):
    a = t.find("*** START OF"); b = t.find("*** END OF")
    if a >= 0:
        t = t[t.find("\n", a) + 1:]
    if b >= 0:
        t = t[:b]
    return t


def norm(t, finnish=False):
    t = t.upper()
    if finnish:
        t = re.sub(r"[^A-ZÄÖÅ]+", "_", t)
    else:
        t = re.sub(r"[^A-Z]+", "_", t)
    return t.strip("_")


def windows(s, L):
    s = s + "_"
    out = set()
    for i in [0] + [k + 1 for k, ch in enumerate(s) if ch == "_"]:
        w = s[i:i + L]
        if len(w) == L:
            out.add(w)
    return out


if __name__ == "__main__":
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 75
    sources = {
        "kalevala_fi": (strip_gutenberg((SRC / "kalevala_fi.txt").read_text(encoding="utf-8", errors="ignore")), True),
        "kalevala_en": (strip_gutenberg((SRC / "kalevala_en_crawford.txt").read_text(encoding="utf-8", errors="ignore")), False),
        "turba": ((SRC / "turba_philosophorum_waite1896.txt").read_text(encoding="utf-8", errors="ignore"), False),
        "hermetic_museum": ((SRC / "hermetic_museum_vol1_waite1893.txt").read_text(encoding="utf-8", errors="ignore"), False),
        "newton": (re.sub(r"<[^>]*>", " ", (SRC / "emerald_tablet_newton.htm").read_text(encoding="utf-8", errors="ignore"))
                   .replace("&amp;", " and "), False),
    }
    for name, (txt, fi) in sources.items():
        w = sorted(windows(norm(txt, fi), L))
        (HERE / f"crib_cand_{name}_L{L}.txt").write_text("\n".join(w), encoding="utf-8")
        print(f"{name:16s}: {len(w)} windows; example: {w[len(w) // 2][:60]}")
