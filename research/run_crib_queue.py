"""Autonomous queue of the probable-text scans (§38).

Runs crib_scan.py for each (candidates file, target, mode) not yet finished, one after the other.
"Finished" = a line "… file=…: N alerts …" present in crib_queue_log.txt (or in the older
logs crib_scan_texts_log.txt / crib_scan_game_log.txt). Meant to run as a detached process."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "crib_queue_log.txt"
JOBS = []
for src in ("crib_candidates_L75.txt", "crib_cand_kalevala_fi_L75.txt", "crib_cand_kalevala_en_L75.txt",
            "crib_cand_hermetic_museum_L75.txt"):
    for tg in ("E1", "W2", "E4", "W1", "E2", "E3", "W3", "W4", "E5"):
        for md in ("chiffre", "hors"):
            JOBS.append((src, tg, md))
for tg in ("W2", "E4"):
    JOBS.append(("crib_candidates_L75.txt", tg, "lettre"))


def done_lines():
    out = []
    for f in (LOG, HERE / "crib_scan_texts_log.txt", HERE / "crib_scan_game_log.txt"):
        if f.exists():
            out += f.read_text(encoding="utf-8", errors="ignore").splitlines()
    return out


if __name__ == "__main__":
    for src, tg, md in JOBS:
        key = f"{tg} mode={md} file={src}:"
        if any(key in l for l in done_lines()):
            continue
        r = subprocess.run([sys.executable, "-u", "crib_scan.py", tg, src, md], cwd=HERE,
                           capture_output=True, text=True, encoding="utf-8", errors="ignore")
        last = [l for l in r.stdout.splitlines() if "alerts" in l]
        with open(LOG, "a", encoding="utf-8") as f:
            f.write((last[-1] if last else f"{key} FAILURE: {r.stderr[-300:]}") + "\n")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("QUEUE FINISHED\n")
