"""Extracts the 9 eye messages from the PDF and converts them into trigrams 0-82.

Reading scheme (Noita Eye Glyph Messages / Analytical Overview):
lines go in pairs (top T, bottom B); for each block of 3 columns j:
  triangle pointing up  : T[3j],   T[3j+1], B[3j]      (base-5 digits, most significant first)
  triangle pointing down: B[3j+2], B[3j+1], T[3j+2]
The final digit '5' of each line is only an end-of-line marker.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
PDF = HERE.parent / "Noita Eye Glyph Messages.pdf"
NAMES = ["E1", "W1", "E2", "W2", "E3", "W3", "E4", "W4", "E5"]


def raw_rows():
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                          capture_output=True, text=True, encoding="latin-1").stdout
    messages, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^Message \d \((East|West) \d\)$", s):
            cur = []
            messages.append(cur)
        elif cur is not None and re.fullmatch(r"[0-4]+5", s):
            cur.append(s[:-1])
        elif cur is not None and s.startswith("Message 8 is the only"):
            cur = None
    assert len(messages) == 9, len(messages)
    return messages


def trigrams(rows):
    out = []
    for top, bot in zip(rows[0::2], rows[1::2]):
        T = [int(c) for c in top]
        B = [int(c) for c in bot]
        n = max(len(T), len(B))
        for j in range(0, n, 3):
            if j + 1 < len(T) and j < len(B):
                out.append(T[j] * 25 + T[j + 1] * 5 + B[j])
            if j + 2 < len(B) and j + 2 < len(T):
                out.append(B[j + 2] * 25 + B[j + 1] * 5 + T[j + 2])
        used = (len(T) + len(B))
        assert used % 3 == 0, (len(T), len(B))
    return out


def main():
    msgs = [trigrams(r) for r in raw_rows()]
    lens = [len(m) for m in msgs]
    firsts = [m[0] for m in msgs]
    allv = [v for m in msgs for v in m]
    print("lengths:", lens, "total", sum(lens))
    print("first  :", firsts)
    print("min/max:", min(allv), max(allv), "distinct", len(set(allv)))
    assert lens == [99, 103, 118, 102, 137, 124, 119, 120, 114]
    assert firsts == [50, 80, 36, 76, 63, 34, 27, 77, 33]
    assert set(allv) == set(range(83))
    (HERE / "messages.json").write_text(json.dumps(dict(zip(NAMES, msgs))))
    with open(HERE / "messages.txt", "w") as f:
        for n, m in zip(NAMES, msgs):
            f.write(n + ": " + " ".join(f"{v:02d}" for v in m) + "\n")
    print("OK -> messages.json / messages.txt")


if __name__ == "__main__":
    main()
