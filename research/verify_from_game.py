"""Independent check: rebuilds the digits of the eyes from the 64-bit numbers
hard-coded in noita.exe (function decompiled by Ninji, sources/misc/ninji_decompiled_function.c).
Each number is written in base 7; the last digit is removed (never read: the game divides by 7 before starting) and 1 is subtracted
from each digit (values 0-4 = eye directions, 5 = end of line)."""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "sources/misc/ninji_decompiled_function.c").read_text(encoding="utf-8")
lo = re.findall(r'local_50\._0_4_ = (0x[0-9a-f]+);', src)
hi = re.findall(r'local_50\._4_4_ = (0x[0-9a-f]+);', src)
nums = [(int(h, 16) << 32) | int(l, 16) for l, h in zip(lo, hi)]


def chunk(n):
    s = ""
    while n > 0:
        s = str(n % 7) + s
        n //= 7

    return "".join(str(int(c) - 1) for c in s[:-1])


game = "".join(chunk(n) for n in nums)

txt = subprocess.run(["pdftotext", "-layout", str(HERE.parent / "Noita Eye Glyph Messages.pdf"), "-"],
                     capture_output=True, text=True, encoding="latin-1").stdout
ref, cur = [], None
for line in txt.splitlines():
    t = line.strip()
    if re.match(r"^Message \d \(", t):
        cur = []
        ref.append(cur)
    elif cur is not None and re.fullmatch(r"[0-4]+5", t):
        cur.append(t)
    elif t.startswith("Message 8 is the only"):
        cur = None
ref = ["".join(r) for r in ref]

print(f"{len(nums)} numbers, {len(game)} digits extracted from the game")
print("concatenation of the 9 PDF messages == game data:", "".join(ref) == game)
