"""Night queue of 15/10/2026 (§49, continued): chained computations, each step in 1 or 2 processes.

1. eyes, v2 model (lex=gut), end of the 241 favourite combinations (automatic resume);
2. calibration with the v2 model and KF = 10, then KF = 5 guessed nodes (12 test texts each): how many
   symbols must a human guess provide?
3. eyes, v2 model, the other 3,573 survivors of §42 (2 processes).
Log: run_overnight_gut_log.txt ("QUEUE FINISHED" at the end)."""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "run_overnight_gut_log.txt"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
STEPS = [
    [(["opening_pipeline.py", "yeux", "lex=gut", "300000", "30", "241", "0", "2"], "og_top_0.log"),
     (["opening_pipeline.py", "yeux", "lex=gut", "300000", "30", "241", "1", "2"], "og_top_1.log")],
    [(["opening_blind_calib.py", "6", "300000", "1", "10", "gut"], "opening_guess10_gut_1.txt"),
     (["opening_blind_calib.py", "6", "300000", "2", "10", "gut"], "opening_guess10_gut_2.txt")],
    [(["opening_blind_calib.py", "6", "300000", "1", "5", "gut"], "opening_guess5_gut_1.txt"),
     (["opening_blind_calib.py", "6", "300000", "2", "5", "gut"], "opening_guess5_gut_2.txt")],
    [(["opening_pipeline.py", "yeux", "lex=gut", "tous", "300000", "30", "1000000", "0", "2"], "og_tous_0.log"),
     (["opening_pipeline.py", "yeux", "lex=gut", "tous", "300000", "30", "1000000", "1", "2"], "og_tous_1.log")],
]


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')} {msg}\n")


if __name__ == "__main__":
    for step in STEPS:
        procs = []
        for args, out in step:
            log("start: " + " ".join(args))
            fo = open(HERE / out, "w", encoding="utf-8")
            procs.append((subprocess.Popen([sys.executable, "-u"] + args, cwd=HERE, stdout=fo, stderr=subprocess.STDOUT,
                                           env=ENV), fo, args))
        for p, fo, args in procs:
            p.wait(); fo.close()
            log(f"end (code {p.returncode}): " + " ".join(args))
    log("QUEUE FINISHED")
