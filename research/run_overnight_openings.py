"""Night queue (§47, continued): long computations chained, one at a time (limited memory).

1. calibration of the blind brute force with a beam of 600,000 (8 test texts);
2. eyes, blind brute force, 241 best combinations, beam 600,000;
3. eyes, blind brute force, the other survivors of §42 (≈ 3,573), beam 300,000.
Log: run_overnight_openings_log.txt (start and end of each step)."""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "run_overnight_openings_log.txt"
STEPS = [
    (["opening_blind_calib.py", "8", "600000", "4"], "opening_blind_calib_600k.txt"),
    (["opening_pipeline.py", "yeux", "600000", "30", "241", "0", "1"], "opening_blind_600k_top.log"),
    (["opening_pipeline.py", "yeux", "tous", "300000", "30", "1000000", "0", "1"], "opening_blind_300k_tous.log"),
]

if __name__ == "__main__":
    for args, out in STEPS:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M')} start: {' '.join(args)}\n")
        with open(HERE / out, "w", encoding="utf-8") as fo:
            r = subprocess.run([sys.executable, "-u"] + args, cwd=HERE, stdout=fo, stderr=subprocess.STDOUT,
                               env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M')} end (code {r.returncode}): {' '.join(args)}\n")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("QUEUE FINISHED\n")
