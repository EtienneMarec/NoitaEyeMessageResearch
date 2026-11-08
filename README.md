# Noita eye messages: a statistical and cryptanalytic study

**Nothing has been decrypted.** This repository documents an attempt to narrow down what kind of cipher hides the eye-glyph messages of the game [Noita](https://noitagame.com/): which models the data rules out, which ones survive, how far the attacks got, and exactly where they stop.

The community did the groundwork, and much of this builds on it (see [Credits](#credits)). Every figure below comes from a script in [`research/`](research/) that can be re-run.

## The puzzle

Noita contains 9 messages written in eye glyphs: 5 in the "East" world (E1 to E5) and 4 in the "West" world (W1 to W4). Each triangle of three eyes reads as a base-5 number, giving **1,036 symbols with values from 0 to 82**. The data is in [`research/messages.json`](research/messages.json), in the order E1, W1, E2, W2, E3, W3, E4, W4, E5. Positions are 0-indexed throughout.

What makes the messages tractable, and strange:

- they share long sections, so the same plaintext appears several times under different cipher states;
- they contain perfect **isomorphs**: the same repeat pattern at different places, with different symbols;
- no symbol is ever immediately doubled, and the gap profile between repeats is almost flat.

These properties point to a state-based cipher in which each letter transforms something like an 83-card deck (GAK/XGAK, in the terms of [Lymm's wiki](https://github.com/Lymm37/eye-messages/wiki)).

## The short version

The most consistent model found: **ordinary letters all apply the same shuffle to the deck, and only a separator symbol (the space) applies a different one.** The letter only chooses which card is read. If this is right, the deck's state depends only on the *word lengths* of the text.

This "space model" reproduces the odd E1/W1 "obstacle" (4 different, 4 identical, 4 different, 13 identical symbols) deterministically. In simulation-based inference over all statistics at once, it takes a posterior of 0.95 to 0.97 against the alternatives tested. It is still a hypothesis: **a model can only be confirmed by producing readable plaintext, and this one has not.**

## Results

Section numbers (§) refer to [`REPORT.md`](REPORT.md), which holds the full method, controls and caveats for each result.

### Refuted

| Model | Evidence | § |
|---|---|---|
| Progressive alphabet, even with homophones | "Same shift" test: 2 agreements over 36 shared cards, where about 36 are expected | 23 |
| Any commutative GAK (one or several wheels) | Trilemma: cannot combine no fixed points, the same-shift test and the partial resynchronisation of the obstacle | 25 |
| Positional model σ^i(S(p)) | No admissible cycle length, even on the safest occurrences | 2 |
| Reinsertion, swap or put-on-top *without* a base shuffle | 0 fixed points over about 210 symbol pairs after insertions | 13 |
| Base shuffle of order 2, 4 or 8 with doubles avoided by construction | Would leave a dip in the gap profile at d ≡ 1 mod L; the eyes have none | 29 |
| Chaocipher adapted to 83 symbols | Isomorphs in 0 keys out of 40 | 17 |
| Space shuffle within k ≤ 4 swaps of the letter shuffle, for any shuffle | Same-shift test, P ≤ 0.005 | 41 |
| Strongly differing letter classes | Break the exact obstacle, the stutter and the coincidences | 43 |

### Compatible, but unconfirmed

| Model | Status | § |
|---|---|---|
| **Space model** (letters = β, space = strong shuffle, first symbol inside the deck) | 29% of keys pass every criterion except coincidences after divergence (P ≈ 0.01 to 0.2 depending on the text). ABC posterior 0.95 to 0.97 | 32, 40 |
| Letter classes that are nearly identical (β + 4 swaps), e.g. vowels/consonants | Possible, 2 to 4 times less probable than the space model | 43 |
| Lymm's model (base shuffle + 1 swap per letter) | Exact obstacle in 0.12 to 0.44% of keys; ABC posterior about 0.04 to 0.06 | 31, 40 |

### Hypotheses

- The message's first symbol is a number read inside the deck (§46).
- The letter of rank k is read at deck position k, with natural shuffles and a keyed starting deck (§39, §44). 241 such combinations fit the statistics far better than the generic model, but the family as a whole is not favoured once multiple testing is counted (§45).
- Each letter cuts the deck by about a quarter, each space performs another natural shuffle (§48.3).
- The plaintext is not English or Finnish but intrinsically flat, non-linguistic data (§31).

### Measurements that hold without a cipher model

- The famous "excess at distance 4" is mostly a counting artefact of repeated phrases: z ≈ 2.3 once corrected (§5.1).
- Identified shared-text blocks with their exact offsets, consistent by transitivity (§6, [`research/architecture.html`](research/architecture.html)).
- Symbols coincide at the same position just after a text divergence: 7 of 169 between different groups, P = 0.008 (§26).
- The exact obstacle shape, and the bounds it puts on any XGAK (§24).

## Attacks and where they stop

Attacks were first tried on a testbed with the architecture of the eyes and a known key. Failures there are reported as failures, and a negative result on the eyes is only read as far as the testbed sensitivity allows.

| Approach | Outcome | § |
|---|---|---|
| Simulated annealing, beam search and lazy search on reinsertion tables | The true table is a needle: 90 to 95% must already be known | 9 to 11 |
| Exact constraint programming (CP-SAT) | False solutions at short prefixes; no solution once identifiable | 16, 42 |
| Keyed deck with natural shuffles, ciphertext only | Fails on the cascade of space decisions, even with both shuffles known | 33 to 37 |
| Moderate space shuffle | Only works for k ≤ 2, the regime refuted by §41.4 | 41 |
| Keys from the game (cauldron data, 123,000 keyword decks, Noita's RNG with 5 million seeds) | No signal | 12, 46 |
| Probable texts (game texts, Kalevala, alchemical works), 660 natural shuffle pairs | 74 sweeps, 0 alerts | 38, 39 |
| Dictionary-guided brute force on the openings, 7,321 combinations, English; 3,814 in Finnish | No alert. Blind sensitivity is only about 1 in 12 on the testbed, so this refutes nothing | 47 to 50 |

**The wall.** Under the most favourable assumptions, about 15 guessed symbols at the start of each of three groups would decrypt everything on the testbed (§44). With the strongest language model, about 10 guessed nodes succeed in 6 of 12 test texts (§49). But the first 20 to 25 symbols are unconstrained, and several openings diverge at once, so blind search loses the truth there. What remains is a **human guess at the openings** or external information about the deck.

## Testing a guess

Under the hypotheses above, a guessed opening can be checked in seconds per combination. Texts start at position 1 and use `_` for the space:

```bash
cd research
python opening_crib_solver.py yeux E1=YOUR_GUESS W2=YOUR_GUESS E4=YOUR_GUESS
```

A real hit scores about −3 per symbol; a failure about −6. This tool needs `research/corpus/en.txt`: see [Running the code](#running-the-code).

## Repository layout

| Path | Contents |
|---|---|
| [`REPORT.md`](REPORT.md) | Full research notes, §0 to §50, in the order they were written |
| [`SOURCES.md`](SOURCES.md) | The third-party material used, and where to get it |
| [`research/INDEX.md`](research/INDEX.md) | One line for each of the 157 scripts |
| `research/*.py` | One script per analysis |
| `research/messages.json` | The data, checked against the community's reference spreadsheet |
| `research/*.tsv` | Inputs and results: `abc_sims.tsv` (41,900 simulations), the filter of §42, the conventions of §45, the sweeps of §47 to §50 |

## Running the code

Python 3.11, with:

```bash
pip install -r requirements.txt
```

Scripts must be run from inside `research/`. Those working from `messages.json` alone run directly. The testbed and language models also need the texts in `research/corpus/`, which are not included:

```bash
mkdir -p research/corpus
```

```bash
curl -o research/corpus/en.txt https://www.gutenberg.org/cache/epub/1342/pg1342.txt
```

```bash
curl -o research/corpus/fi.txt https://www.gutenberg.org/cache/epub/7000/pg7000.txt
```

Other scripts need files from `research/sources/`; see [`SOURCES.md`](SOURCES.md). Several analyses take hours; the sweeps of §47 to §50 took whole nights.

## Method

The work followed a few rules:

- Every number comes from a script, not from looking at the data.
- Every "anomaly" is compared with a random baseline of the same size, with a probability or z-score and allowance for multiple testing.
- Sections shared between messages inflate counts, so statistics are given with and without them.
- Results are labelled **refuted**, **compatible** or **hypothesis**. A model is never "confirmed" until it produces readable plaintext.
- Attacks are validated on data with a known key before being used on the eyes.
- A result is only called new after checking the community's documents.

`REPORT.md` is a translation of working notes kept as the research went along, so earlier sections are sometimes corrected by later ones, and those corrections are marked. In it, "I" is the note-taker and "the repository owner" is the person directing the work.

## Glossary of French labels

The original notes were in French. The comments, documentation and printed messages have been translated, but some labels are still French because they are data values in the `.tsv` files or command-line keywords that the scripts parse.

| Label | Meaning |
|---|---|
| `yeux`, `banc` | the eyes (real data), the testbed |
| `espace`, `lettre`, `chiffre`, `hors` | space, letter, digit, outside (the cipher) |
| `mort` | the beam died |
| `aleatoire`, `anglais`, `aplati`, `uniforme` | random, English, flattened, uniform |
| `reinsertion`, `retournement`, `echange`, `echange_dessus` | reinsertion, reversal, swap, swap with the top |
| `dessus`, `dessous`, `profond`, `libre` | top, bottom, deep, free |
| `coupe`, `coupe1`, `tas3`, `miroir`, `cycle83` | cut, cut 1, 3 piles, mirror, 83-cycle |
| `mots`, `subst`, `progressif`, `aucun`/`aucune` | words, substitution, progressive, none |
| `proche`, `lointain`, `toutes`, `groupes`, `sans E1/W1 et E4/E5` | near, far, all, between groups, without E1/W1 and E4/E5 |
| `khi2`, `doublons`, `ptsfix`, `P_plat`, `P_ptsfix` | chi², doubles, fixed points, P(flat), P(fixed points) |
| `beg_part`, `beg_series`, `obst_part`, `obst_motif`, `coinc_div` | stutter share and runs, obstacle share and pattern, coincidences after divergence |
| `tous`, `tous01`, `meme`, `autre`, `jeu`, `blocs`, `strategie` | all, all at P ≥ 0.01, same, other, game, blocks, strategy |
| `Qconnu`, `Qinconnu`, `--valider`, `SEUIL_D` | known Q, unknown Q, validate, threshold D |
| `polybe`, `ternaire` | Polybius, ternary |
| `un`, `vc`, `r2` to `r4`, `chaque` | one class, vowels/consonants, 2 to 4 random classes, one class per symbol |
| `lex=en\|jeu\|fi\|gut\|gutfi` | language model: English, game texts, Finnish, Gutenberg English, Gutenberg Finnish |

## Credits

This work stands on the community's research on the eye messages, in particular:

- **Lymm**, whose wiki and Lean proofs on GAK ciphers are the state of the art;
- **Toboter** (isomorph lists, cauldron data), **codewarrior0** (Analytical Overview, progressive-alphabet hypothesis), **Dykoine**, **Capybar**, **Ninji** (decompilation), **Pyry**, **dextercd**, **gonzo**, **Fryke**, **WarFairy** and **Nemare**;
- **pudy248** and **TwoAbove**, for reconstructing Noita's random generator;
- Nolla Games, for making the game.

Corrections, counter-examples and guesses at the openings are welcome.
