"""Download of a public-domain English corpus (Project Gutenberg) for a stronger language model (§49).

Selection: books of gutenberg.org's "top 1000" ranking (in ranking order), of type Text and in English
according to the official catalogue (pg_catalog.csv), except Pride and Prejudice (no. 1342), which is the
testbed's text (honest calibration). One file pg{n}.txt per book in sources/texts/gutenberg/, one request
every 1.5 s (moderate use of the site). Resumable (files already present are skipped).
Option: language (en by default; fi = Finnish books of the catalogue, lowest numbers first, in
sources/texts/gutenberg_fi/).
Usage: python download_gutenberg.py [number of books] [language]"""
import csv
import gzip
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "sources/texts/gutenberg"
EXCLUDE = {1342}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script; low rate)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


if __name__ == "__main__":
    nmax = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    OUT.mkdir(parents=True, exist_ok=True)
    cat = OUT / "pg_catalog.csv.gz"
    if lang != "en":
        OUT2 = HERE / f"sources/texts/gutenberg_{lang}"; OUT2.mkdir(parents=True, exist_ok=True)
        ids = []
        with gzip.open(cat, "rt", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("Type") == "Text" and row.get("Language", "").strip() == lang:
                    ids.append(int(row["Text#"]))
        ids.sort(); ok = 0
        print(f"{len(ids)} books in {lang}; taking {min(nmax, len(ids))}", flush=True)
        for n in ids[:nmax]:
            dest = OUT2 / f"pg{n}.txt"
            if dest.exists() and dest.stat().st_size > 1000:
                ok += 1; continue
            try:
                dest.write_bytes(get(f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt")); ok += 1
            except Exception as e:
                print(f"  failure {n}: {e}", flush=True)
            time.sleep(1.5)
        print(f"{ok} books present in {OUT2}", flush=True)
        sys.exit(0)
    if not cat.exists():
        cat.write_bytes(get("https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz"))
    english = set()
    with gzip.open(cat, "rt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Type") == "Text" and row.get("Language", "").strip() == "en":
                english.add(int(row["Text#"]))
    top = OUT / "top1000.html"
    if not top.exists():
        top.write_bytes(get("https://www.gutenberg.org/browse/scores/top1000.php"))
    ids = []
    for m in re.finditer(r'href="/ebooks/(\d+)"', top.read_text(encoding="utf-8", errors="ignore")):
        n = int(m.group(1))
        if n in english and n not in EXCLUDE and n not in ids:
            ids.append(n)
    print(f"{len(ids)} English books in the ranking; taking {min(nmax, len(ids))}", flush=True)
    ok = 0
    for n in ids[:nmax]:
        dest = OUT / f"pg{n}.txt"
        if dest.exists() and dest.stat().st_size > 1000:
            ok += 1
            continue
        try:
            dest.write_bytes(get(f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt"))
            ok += 1
        except Exception as e:
            print(f"  failure {n}: {e}", flush=True)
        time.sleep(1.5)
    print(f"{ok} books present in {OUT}", flush=True)
