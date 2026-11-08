# Sources (not included in this repository)

Some scripts read material from `research/sources/` and `research/corpus/`. That material is **not published here**: it is third-party work (community documents, game data, other people's repositories, books) and weighs about 800 MB. This file says what it was and where it came from, so the folders can be rebuilt. Scripts that need a missing file fail with a file-not-found error; everything that works from `messages.json` alone runs as is.

Downloaded third-party code was only read, never executed.

## `sources/docs/` and `sources/sheets/`: community documents

Linked from the community's *Noita Eye Glyph Messages* documents. Google Docs were exported to `.docx` and `.txt`, Google Sheets to `.xlsx` and one CSV per tab.

- Analytical Overview, Progress, Messages, Isomorphism, Alignments and Gap Patterns (Lymm), Why 83, Cipher model (Dykoine), Vigenere theory, Capybar.
- Progressive-Alphabet Cipher Hypothesis (codewarrior0), Noita - Hidden Secret, A note from gonzo, Clues and interpretations (HS), HS QnA session, Eye Message Music (Fryke), Noita Decompilation Guide.
- Sheets: **Noita Eye Data** (its `Trigrams Base 10` tab is identical to `research/messages.json`, checked), Repetition Distances, Nemare experimenter, Nemare desert diamond, Emerald Tablet (index), WarFairy conversion sets.

## `sources/github/`: community repositories (shallow clones)

- `codewarrior0/noita-eye-glyph-analyses`
- `Lymm37/eye-messages` and its wiki, the state of the art on GAK ciphers
- `turing-system/Noita-Silma-Huone` (Dykoine)
- `Doctor-Ned/NoitaEyeGlyphResearch` (Capybar)
- `ToboterXP/EyeGlyphs` (isomorph list, cauldron data, `Englishv4.txt`)
- `pudy248/NoitaSeedSearcherCUDA` and `TwoAbove/noita-tools` (reconstruction of Noita's random generator)

## `sources/misc/`

- `ninji_decompiled_function.c`: the game's `select_weird_eyes` function, decompiled by Ninji. The messages are stored as 64-bit numbers read in base 7. `research/verify_from_game.py` rebuilds E1 from it; the rest cannot be checked from this file because the decompilation is incomplete.
- `colab_codewarrior.ipynb`, `repeats_decr_out.html`: companions of the Analytical Overview.

## `sources/gamedata/`

Game texts (`translations/common.csv`), credits, `magic_numbers.xml`, `debug_keys.txt`, tablet texts and 148 pages of the official wiki. Used for keyword decks (§12.2) and probable texts (§38).

## `sources/texts/`: public-domain books

- Kalevala, Finnish (Project Gutenberg #7000) and English translation by J. M. Crawford (#5186).
- *The Turba Philosophorum* (A. E. Waite, 1896) and *The Hermetic Museum*, vol. I (Waite, 1893), OCR text from archive.org (`alchemyturbaphil00waitrich`, `b24927363_0001`).
- Emerald Tablet, Newton's translation (Indiana University, Newton Project, ALCH00017).
- `gutenberg/`: about 400 English books, in the order of gutenberg.org's "top 1000", filtered with the official catalogue. *Pride and Prejudice* (#1342) is excluded because it is the testbed text.
- `gutenberg_fi/`: 400 Finnish books.

Both Gutenberg folders are rebuilt by `research/download_gutenberg.py` (`python download_gutenberg.py 400` and `python download_gutenberg.py 400 fi`), which makes one request every 1.5 s.

## `corpus/`

`en.txt` (*Pride and Prejudice*, the testbed text, Project Gutenberg #1342) and `fi.txt` (Kalevala, Project Gutenberg #7000).

## Also not included

The 10 community PDFs the work started from, including `Noita Eye Glyph Messages.pdf` (read by `extract.py`, whose output `messages.json` is included), the raw run logs, and the 75-character windows cut from the texts above.
