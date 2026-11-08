"""Night queue of 17/10/2026 (§50): "Finnish plaintext" hypothesis with a strong language model.

0. wait for the end of the current run (lex=gut tous01);
1. download up to 400 Finnish books from Project Gutenberg (sources/texts/gutenberg_fi/);
2. eyes, Finnish v2 model (lex=gutfi), 241 favourite combinations (2 processes);
3. eyes, Finnish v2 model, the other 3,573 survivors (2 processes; will probably be interrupted).
Relaunched on 18/10/2026: the first download had failed (network outage, 14 books); the outputs
made with that weak model are renamed opening_blind_out_gutfi14_*.
Log: run_overnight_fi_log.txt ("QUEUE FINISHED" at the end)."""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "run_overnight_fi_log.txt"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
STEPS = [
    [(["download_gutenberg.py", "400", "fi"], "download_gutenberg_fi.log")],
    [(["download_gutenberg.py", "400", "fi"], "download_gutenberg_fi_2.log")],   # 2nd pass: catches up on network failures
    [(["opening_pipeline.py", "yeux", "lex=gutfi", "300000", "30", "241", "0", "2"], "ogfi_top_0.log"),
     (["opening_pipeline.py", "yeux", "lex=gutfi", "300000", "30", "241", "1", "2"], "ogfi_top_1.log")],
    [(["opening_pipeline.py", "yeux", "lex=gutfi", "tous", "300000", "30", "1000000", "0", "2"], "ogfi_tous_0.log"),
     (["opening_pipeline.py", "yeux", "lex=gutfi", "tous", "300000", "30", "1000000", "1", "2"], "ogfi_tous_1.log")],
]


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')} {msg}\n")


def tous01_running():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' } | "
                          "ForEach-Object { $_.CommandLine }"],
                         capture_output=True, text=True, errors="ignore").stdout
    return "tous01" in out


if __name__ == "__main__":
    log("waiting for the end of the tous01 run")
    while tous01_running():
        time.sleep(120)
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
