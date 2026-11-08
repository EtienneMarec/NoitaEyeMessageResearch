"""Does the flatness of the gap profile depend on the plaintext? (§28)

Same architecture (testkey/true_blocks not needed here): the LETTERS of the testbed are replaced by a
substitution into another "language", keeping the structure (same identical positions between messages):
  - English (original testbed);
  - Finnish (corpus/fi.txt, letters A-Z + ÅÄÖ mapped to 29 symbols): Finnish texts are drawn instead;
  - uniform random letters (26 equiprobable symbols);
  - "English with spaces" (testbed_spaces, space = ordinary symbol).
Models: Lymm k = 1 (random β, β of order 8), no homophones; reinsertion + random β for reference.
Measure: P(chi² <= eyes = 63.2) and median chi², 100 keys."""
import re
import random
import sys
from pathlib import Path
import numpy as np
from testbed import build_plaintexts, ALPHA
from swap_model_test import chi2
from small_order_test import make_key as lymm_key
from family_zoo import make_key as zoo_key
from explore import xgak_encrypt
import testbed_spaces as tbs
from stats import load_eyes

HERE = Path(__file__).parent


def remap(plains, gen):
    """replaces each letter by a stream of another language, keeping the equalities between messages:
    messages are rebuilt by replacing characters position by position via a random table
    applied to the base text, then the clean parts are redrawn. Simple version: monoalphabetic substitution
    on the letters (preserves the structure) — does NOT change the entropy; hence a second version (fresh)."""
    return plains


def fresh(base, source, rng):
    """keeps the structure of the testbed's shared parts, but replaces ALL the text by `source`:
    each position (message, i) gets the character source[off + h], where h = identifier of the equality
    class (same text => same identifier), which preserves the shared blocks."""
    cls = {}
    out = []
    off = rng.randrange(0, len(source) - 20000)
    for m in base:
        s = [m[0]]
        for i, ch in enumerate(m[1:], start=1):
            key = (ch, i, m[max(1, i - 6):i])  # local context: same text => same key
            if key not in cls:
                cls[key] = source[off + len(cls)]
            s.append(cls[key])
        out.append("".join(s))
    return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    names, M = load_eyes(); E = chi2(M)
    base = build_plaintexts()
    t_en = re.sub(r"[^A-Z]", "", (HERE / "corpus/en.txt").read_text(encoding="utf-8", errors="ignore").upper())
    t_fi = re.sub(r"[^A-ZÅÄÖ]", "", (HERE / "corpus/fi.txt").read_text(encoding="utf-8", errors="ignore").upper())
    t_fi = t_fi.replace("Å", "X").replace("Ä", "Q").replace("Ö", "Z")  # mapped to A-Z (X, Q, Z are rare in Finnish)
    rnd = random.Random(1)
    t_un = "".join(rnd.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(200000))
    rng = np.random.default_rng(7)
    print(f"eyes: chi² {E:.1f}")
    for lang, src in (("English (testbed)", None), ("English redrawn", t_en), ("Finnish", t_fi), ("uniform 26", t_un)):
        for model in ("Lymm random β", "Lymm β order 8", "reinsertion + β"):
            X = []
            for r in range(R):
                pl = base if src is None else fresh(base, src, rnd)
                if model.startswith("Lymm"):
                    q, S = lymm_key("aleatoire" if "random" in model else "8", 1, rng)
                else:
                    q, S = zoo_key("reinsertion", "aleatoire", 0, rng, len(ALPHA))
                C = [[0] + xgak_encrypt(np.array([ALPHA.index(ch) for ch in m[1:]], np.int64), q, S).tolist() for m in pl]
                X.append(chi2(C))
            X = np.array(X)
            print(f"{lang:16s} {model:18s}: median chi² {np.median(X):6.1f}, P(chi² <= eyes) {np.mean(X <= E):.2f}", flush=True)
