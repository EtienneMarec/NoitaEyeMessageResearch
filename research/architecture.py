"""Plaintext architecture deduced from alignment_map.py and plaintext_diff_map.py (GAK model).

Each block = one presumed plaintext present in several messages (0-indexed, inclusive position ranges).
The bounds are those of the conflict-free windows; the true limits of the shared text may be slightly
narrower. The script checks (1) that the shifts between messages are transitively consistent and
(2) that no block contains an isomorphism conflict between its occurrences.
"""
import html
from itertools import combinations
from stats import load_eyes

names, M = load_eyes()
N = dict(zip(names, M))

# (name, strength, {message: (start, end)}); strength = "strong" (>= 3 shared repeats or identical symbols)
BLOCKS = [
    ("A0 opening", "strong", {"E1": (1, 21), "W1": (1, 21), "E2": (1, 21)}),
    ("A1 phrase 1", "strong", {"E1": (29, 49), "W1": (29, 49), "E2": (34, 54)}),
    ("A2 phrase 1 (again)", "strong", {"E1": (60, 77), "W1": (62, 79), "E2": (72, 89)}),
    ("C0 opening", "strong", {"E4": (1, 20), "W4": (1, 20), "E5": (1, 20)}),
    ("C1 (E4/E5)", "strong", {"E4": (29, 37), "E5": (29, 37)}),
    ("C2", "strong", {"E4": (47, 64), "W4": (49, 66), "E5": (48, 65)}),
    ("C3a", "strong", {"E4": (68, 89), "W4": (71, 92), "E5": (69, 90)}),
    ("C3b", "strong", {"E4": (90, 97), "W4": (93, 100), "E5": (91, 98)}),
    ("X (E3 = end of C3)", "strong", {"E3": (63, 90), "E4": (72, 99), "W4": (75, 102), "E5": (73, 100)}),
    ("B0 opening", "strong", {"W2": (1, 5), "E3": (1, 5), "W3": (1, 5)}),
    ("B1", "weak", {"W2": (12, 34), "E3": (18, 40), "W3": (17, 39)}),
]


def iso_ok(a, b):
    f, g = {}, {}
    for x, y in zip(a, b):
        if f.get(x, y) != y or g.get(y, x) != x:
            return False
        f[x], g[y] = y, x
    return True


def check():
    ok = True
    for name, _, occ in BLOCKS:
        lens = {e - s for s, e in occ.values()}
        if len(lens) != 1:
            print(f"[!] {name}: different lengths {occ}"); ok = False
        for (m1, (s1, e1)), (m2, (s2, e2)) in combinations(occ.items(), 2):
            if not iso_ok(N[m1][s1:e1 + 1], N[m2][s2:e2 + 1]):
                print(f"[!] {name}: {m1}@{s1} and {m2}@{s2} are not isomorphic"); ok = False
    print("block consistency:", "OK" if ok else "PROBLEMS")


def ascii_map(scale=2):
    lab = {}
    for k, (name, force, occ) in enumerate(BLOCKS):
        ch = name.split()[0]
        for m, (s, e) in occ.items():
            for p in range(s, e + 1):
                lab.setdefault((m, p), ch)
    out = []
    for m in names:
        row = []
        for p in range(0, len(N[m]), scale):
            c = lab.get((m, p))
            row.append((c[0] if c[0] != "X" else "x") if c else ".")
        out.append(f"{m} {''.join(row)}")
    return "\n".join(out)


COLORS = {"A": "#3b82f6", "C": "#10b981", "B": "#f59e0b", "X": "#ef4444"}


def svg_html(path="architecture.html"):
    W, rowh, x0 = 7, 34, 60
    L = max(len(m) for m in M)
    h = rowh * len(names) + 60
    parts = [f'<svg viewBox="0 0 {x0 + W * L + 20} {h}" width="100%" role="img" '
             'aria-label="Plaintext architecture of the 9 messages">']
    for t in range(0, L + 1, 10):
        parts.append(f'<text x="{x0 + W * t}" y="14" class="tick">{t}</text>'
                     f'<line x1="{x0 + W * t}" y1="18" x2="{x0 + W * t}" y2="{h - 30}" class="grid"/>')
    for r, m in enumerate(names):
        y = 26 + r * rowh
        parts.append(f'<text x="8" y="{y + 16}" class="lbl">{m}</text>')
        parts.append(f'<rect x="{x0}" y="{y + 4}" width="{W * len(N[m])}" height="16" class="bar"/>')
    for name, force, occ in BLOCKS:
        col = COLORS[name[0]]
        for m, (s, e) in occ.items():
            r = names.index(m)
            y = 26 + r * rowh
            dash = ' stroke-dasharray="3 2"' if force == "weak" else ""
            op = 0.9 if name[0] != "X" else 0.55
            parts.append(f'<rect x="{x0 + W * s}" y="{y + (4 if name[0] != "X" else 21)}" '
                         f'width="{W * (e - s + 1)}" height="{16 if name[0] != "X" else 6}" fill="{col}" '
                         f'fill-opacity="{op}" stroke="{col}"{dash}><title>{html.escape(name)}: {m} {s}..{e}</title></rect>')
            if name[0] != "X":
                parts.append(f'<text x="{x0 + W * s + 3}" y="{y + 16}" class="blk">{html.escape(name.split()[0])}</text>')
    parts.append("</svg>")
    legend = "".join(f'<span><i style="background:{c}"></i>{t}</span>' for t, c in
                     [("group E1/W1/E2", COLORS["A"]), ("group E4/W4/E5", COLORS["C"]),
                      ("group W2/E3/W3 (B1 = weak evidence)", COLORS["B"]),
                      ("E3 text found again in E4/W4/E5", COLORS["X"])])
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Plaintext architecture</title>
<style>
:root{{--bg:#fff;--fg:#1f2328;--muted:#6b7280;--bar:#e5e7eb;--grid:#f0f1f3}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181d;--fg:#e6e6e6;--muted:#9aa0a6;--bar:#2b2f36;--grid:#23262c}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:1100px}}
h1{{font-size:20px;margin:0 0 4px}} p{{color:var(--muted);margin:4px 0 12px}}
.tick{{font-size:9px;fill:var(--muted)}} .grid{{stroke:var(--grid)}} .lbl{{font:600 13px system-ui;fill:var(--fg)}}
.bar{{fill:var(--bar)}} .blk{{font:600 10px system-ui;fill:#fff}}
.leg span{{margin-right:16px;font-size:13px;white-space:nowrap}} .leg i{{display:inline-block;width:12px;height:12px;margin-right:5px;vertical-align:-1px;border-radius:2px}}
</style></head><body>
<h1>Plaintext architecture of the Noita eye messages</h1>
<p>Blocks of presumed shared plaintext, deduced from conflict-free shifted alignments (GAK model). Positions in trigrams, from 0. Hover a block for its positions.</p>
<div class="leg">{legend}</div>
{''.join(parts)}
</body></html>"""
    open(path, "w", encoding="utf-8").write(doc)


if __name__ == "__main__":
    check()
    print(ascii_map())
    svg_html()
