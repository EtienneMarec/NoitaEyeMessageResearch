"""Statistical fingerprint (stats.fingerprint, from position 50): eyes versus models (§26).

Models, each on its own testbed and R keys:
  - "espace" (space model): letters = shared shuffle β, space = its own permutation (testbed with spaces), FIRST SYMBOL
    INSIDE the deck, no-doubles rule;
  - "Lymm": 1 swap per slot + β, homophones from the previous letter (60), no doubles;
  - "reinsertion + random β" (testbed without spaces).
We report the median and the 10–90% interval of: IoC, repeat rate at d = 1..6 (per 1000 tests),
repeated digraphs and trigraphs."""
import sys
import numpy as np
from stats import load_eyes, fingerprint
from explore import xgak_encrypt
import space_model_test as sm
import testbed_spaces as tbs
from testbed import build_plaintexts, ALPHA
from swap_context_test import make_key as swap_key
from context_homophone_test import enc_all
from family_zoo import make_key as zoo_key


def summarize(fps):
    keys = ("ioc", "digraph_rep", "trigraph_rep")
    out = {k: np.percentile([f[k] for f in fps], [10, 50, 90]) for k in keys}
    g = np.array([f["gap_rate_x1000"][:6] for f in fps])
    out["gap"] = np.median(g, axis=0)
    return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    names, M = load_eyes()
    e = fingerprint(M, 50)
    print(f"eyes: ioc {e['ioc']}, repeats d=1..6 ‰ {e['gap_rate_x1000'][:6]}, digraphs {e['digraph_rep']}, trigraphs {e['trigraph_rep']}")
    rng = np.random.default_rng(5)
    base_s = tbs.build_plaintexts()
    base = build_plaintexts()
    seqs = [np.array([ALPHA.index(ch) for ch in m[1:]], np.int64) for m in base]
    for lab in ("espace", "Lymm", "reinsertion"):
        fps = []
        for _ in range(R):
            if lab == "espace":
                q, S = sm.make_key("_", "aleatoire", True, rng)
                C = [xgak_encrypt(np.array([sm.ALPHA_S.index(ch) for ch in m], np.int64), q, S).tolist() for m in base_s]
            elif lab == "Lymm":
                slots, reads, S = swap_key(1, "aleatoire", 60, rng, nodouble=True)
                C = enc_all(base, slots, reads, S)
            else:
                reads, S = zoo_key("reinsertion", "aleatoire", 0, rng, len(ALPHA))
                C = [[0] + xgak_encrypt(s, reads, S).tolist() for s in seqs]
            fps.append(fingerprint(C, 50))
        s = summarize(fps)
        print(f"{lab:12s}: ioc {s['ioc'][1]:.3f} [{s['ioc'][0]:.3f}–{s['ioc'][2]:.3f}], d=1..6 ‰ {np.round(s['gap'], 1).tolist()}, "
              f"digraphs {s['digraph_rep'][1]:.0f} [{s['digraph_rep'][0]:.0f}–{s['digraph_rep'][2]:.0f}], "
              f"trigraphs {s['trigraph_rep'][1]:.0f} [{s['trigraph_rep'][0]:.0f}–{s['trigraph_rep'][2]:.0f}]", flush=True)
