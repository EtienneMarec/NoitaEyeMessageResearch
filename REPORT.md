# Noita eye glyphs: research notes (session of 2026-09-30 onwards)

All scripts are in this folder (`research/`) and can be re-run with `python <script>.py`.

*Translated from the original French working notes. Section numbers are kept because the scripts cite them (§N); the sections are in the order they were written, not in numerical order at the start. Positions are 0-indexed unless stated otherwise. Some data labels stay in French: see the glossary in the top-level `README.md`. `sources/` and `corpus/` are referred to throughout but are not included in this repository (see `SOURCES.md`).*

## ⚠ Update after reading the sources (`sources/`)

**Lymm's wiki** (`sources/github/Lymm37_eye-messages.wiki`), with its proofs formalised in Lean, is the state of the art. Here is what it already establishes.

- **Cipher hierarchy.** CTAK ⊂ GCTAK ⊂ GAK = "fixed-read XGAK" ⊂ XGAK = "consistently perfectly isomorphic" ciphers. The progressive cipher is a case of XGAK.
- **Possible groups for 83 symbols.** There are only 6: C83 and D166 are excluded, AGL(1,83) and C83:C41 are very unlikely because of the message openings, and what remains is **A83/S83**, i.e. a "deck of 83 cards" where each letter applies a shuffle and the top card is read.
- **Already reproduced with this model:** the message openings, the shared sections, the E1/W1 "obstacle" and the E4/E5 "Stutter Section", which corresponds to my "locality of differences" in section 3. This requires the permutations of the different letters to be **close to a base permutation**: about 4 swaps at most per letter.
- **Chaining conflicts.** In a non-commutative group they are *normal*: they are not errors. Fixed points in the mappings between isomorphs are normal too.
- **What is missing, according to Lymm themself:** an attack against GAK ("we need a GAK attack").

What my results add, once put in this context:

| My result | Status |
|---|---|
| Progressive alphabet refuted | already known (codewarrior0, Toboter); I confirm it with an exact test |
| Positional model σ^i(S(p)) refuted | **new**: it was marked "Maybe?" in Progress, and I find no refutation of it in the wiki |
| Fixed point 17 → 17 (W1@59 ~ E3@90) | consistent with S83 and incompatible with a cyclic wheel; supports Lymm's conclusion |
| E4/E5 locality | already known ("Stutter Section") |
| Columns 2 and 15 break single-wheel chaining | an interesting nuance, but CTAK remains excluded by other conflicts (group 789, E1@62) |
| Positions ≡ 4 (mod 5) | new, but weak (1 chance in 125) |

The "Hidden Secret" episode (2023) contains many hints but no proof: gonzo, one of its proponents, concludes it is a probable hoax. Its hints ("3D planes", "Avarice diamond") also contradict the 0-82 trigram reading, which is almost certain (see "Why 83").

The **useful research lead** is therefore to build an attack against a deck of cards whose letter shuffles are a base permutation B followed by a few letter-specific swaps.

## 5. New results (2026-09-30, after reading the sources)

### 5.1 The "excess at distance 4" is mostly a counting artefact (`gap_profile.py`, `gap_profile_collapsed.py`)

Progress, the Overview and Dykoine present the excess of repeats at distance 4 as a property of the cipher. An "offset-4 autokey" lead was even drawn from it. But a phrase repeated N times reproduces its internal repeats N times. Here is what the different ways of counting give:

- **Raw count** (as in the documents): 26 repeats at d=4.
- **Without the duplicates from shared sections**: 22 repeats for 11.0 expected (z = 3.3).
- **Counting only once each repeat internal to an isomorph family** (Toboter's list): 17 repeats. The expectation is 12.3 (z = 1.35), or about 9.7 when normalised by the global deficit due to deduplication (z ≈ 2.3).

To put this z ≈ 2.3 in context: over 40 tested distances, about 2 values with |z| ≥ 2 are expected by chance. The excess at d=4 therefore becomes **marginal**, and the deficit at d=2 (3 observed against about 10 expected, z ≈ −2.2) is just as marginal. Neither should serve as a strong constraint. I found this challenge nowhere in the sources.

### 5.2 The "Stutter Section" requires a real plaintext difference (`first_letter_test.py`)

> **Correction (same day).**
> - This test is Lymm's **allomorph** method, applied from position 0.
> - Its conclusion holds only for **GAK** (deck read at the top card after the shuffle, Lymm's favourite model, which includes CTAK). In that model, a differing letter at position i is absorbed into π, so a conflict (i, j) proves a difference in [i+1, j].
> - In a general XGAK, where the letter chooses the card read, a conflict only proves a difference in [i, j]. For E4/E5 (conflict between 0 and 21), the first letter is then enough.
> - The text below must therefore be read "under GAK".

**Principle.** Take any XGAK cipher: deck of cards, GAK, CTAK, progressive cipher, whatever the initial state and convention. If two messages differ only in their first letter (a ≠ a'), then their states satisfy D'_i = π·D_i, with π fixed. Hence **c'_i = π(c_i) at all positions**, including position 0, and π leaves fixed the symbols at identical positions.

**Application to E4, W4 and E5.** Positions 1 to 20 are identical, so π fixes these 18 symbols, and π(27) = 33 (first letters of E4 and E5). At position 21, E4 has 77 and E5 has 33, which would require π(77) = 33: this is **impossible**. Same conclusion for E4/W4 (W4 has 60 at position 21, but 60 has been fixed since position 7) and for W4/E5.

**Conclusion.** In any XGAK cipher, the plaintexts of E4, W4 and E5 differ **at position 21 at the latest** (in addition to the first letter). If the first letter is not encrypted by the deck, an identical initial state gives the same conclusion. The desynchronisation opening the Stutter Section is therefore a real change of text, not merely the hidden effect of the first letter. Lymm's wiki suggests the opposite ("can be caused naturally from identical plaintext"). The resynchronisations that follow (25-27, 29-31…) remain explicable by a deck whose shuffles are close to each other.

### 5.3 A curiosity, probably accidental

At the divergence point, E1@25 = 80 (first letter of W1), E2@26 = 76 (first letter of W2) and E4@21 = 77 (first letter of W4). Each time these are the twin messages from the parallel world. Nothing equivalent on the W side, and no known mechanism explains it. p ≈ 0.003 before correction, about 5% once the fact that I noticed it after the fact is taken into account. **Not to be used as a hint.**

## 0. Data

- `extract.py` reads `Noita Eye Glyph Messages.pdf`, applies the triangle reading and then base 5, and writes `messages.json` and `messages.txt`.
- Checks passed:
  - 9 messages, 1036 trigrams;
  - lengths 99/103/118/102/137/124/119/120/114;
  - first symbols 50/80/36/76/63/34/27/77/33;
  - values 0-82, all present.
- `stats.py` computes the statistical fingerprint. It reproduces the published figures:
  - gaps d = 1..8: 0, 5, 9, 26, 11, 12, 12, 11;
  - 55 repeated digraphs, 0 repeated trigrams;
  - IoC 1.066.

## 1. Isomorphs: systematic search (`isomorphs.py`)

- 14 maximal isomorphs are found, of length ≥ 8 and with at least 3 repeated letters.
- On random data of the same size, about 0.1 per draw are found (20 draws). So almost all are real.
- The main family (pattern `x_____ayb_cb_ac_yx`, 18 letters) has 4 occurrences whose extent is confirmed by repeats at both ends: **W1@34, W1@64, E2@39, E2@74**. To these must be added **E1@62**, which is shorter.
- **W1@59 ~ E3@90** (Δ = 31): this isomorph contains a **fixed point** (17 maps to 17, twice, at relative positions 13 and 16). This is the messages 1/4 alignment that codewarrior had noticed.

## 2. Model test results

| Model | Test | Result |
|---|---|---|
| Additive, multiplicative or affine relation mod 83 in numerical order | the 6 pairs of the main family | **refuted** (no solution) |
| **Progressive alphabet** (wheel advancing one notch per letter, any mixed alphabet): the offsets equal the position differences | `progressive_test.py`, `wheel_solver.py` | **refuted**, even after removing the doubtful columns 2 and 15 |
| **Positional σ^i** ("P^pos[S[char]]", Pyry/dextercd, marked "Maybe?" in Progress): any σ, constraints taken modulo the length of each cycle | `sigma_power_test.py` | **refuted**. Even on the 4 safe occurrences alone, without E1@62 and without columns 2 and 15, a component of 16 symbols admits no cycle length (the symbols overlap for every l ≤ 83). |
| Single wheel with free offsets (classic chaining: CTAK, Alberti, clock…) | `wheel_solver.py` on W1@34, W1@64, E2@39, E2@74 | **consistent**, provided 2 columns without repeats (2 and 15) are excluded. These two columns alone are enough to make chaining impossible, which probably explains some of the "contradictions" reported by the community. Hypothesis: the plaintext differs by one letter at these places. |
| Single wheel with free offsets, isomorph W1@59 ~ E3@90 | fixed point 17 → 17 | incompatible with any rotation of a single wheel, **if** this isomorph is causal. It is less certain than the main family (probability that it is due to chance: about 2 to 10%). |

Adding the 5th occurrence **E1@62**:

- on the 16 columns (without columns 2 and 15), there is **no single-wheel solution**;
- on the 9-letter core (columns 6 to 14), chaining remains **consistent**.

The conflict therefore comes from the columns outside the core. Hypothesis: in E1, the plaintext of this occurrence differs from that of the other occurrences outside the common core (E1@62 is indeed shorter).

Note: the 4 safe occurrences start at positions 34, 64, 39 and 74, **all ≡ 4 (mod 5)**. Their mutual gaps are 30, 5, 40, 25, 35 and 10. The occurrence E1@62 (≡ 2 mod 5) is the one that chains badly. This regularity remains to be confirmed, as it could be just a coincidence (about 1/125).

## 3. Locality of differences (strong constraint, little exploited so far)

Map of equal (=) and differing (x) positions between pairs of messages, for positions 0 to 43:

```
E1/W1 : x========================xxxx====xxxx=============xxxxx…
E4/E5 : x====================xxxx===x===xxx=xx===x=xxxxxxx…
```

Between E4 and E5, **only one** position differs (28: 04 against 59), then the ciphertext becomes identical again from position 29 (34 60 63). The same phenomenon recurs at positions 41→42, 32-34→35 and 36-37→38.

Consequences:

- **"Latin square" CTAK** (c_i = f(c_{i-1}, p_i), with f injective in each argument, which covers all mixed-alphabet CTAKs): each resynchronisation requires the plaintexts to differ *also* at the next position, and that this difference produces the same ciphertext by chance (probability 1/83). 5 resynchronisations are observed, i.e. a probability of about 83⁻⁵: **excluded**.
- **Group Autokey S83 with independent generators**: a single differing letter shifts the whole state, and the ciphertext would not resynchronise: **excluded**.
- What remains compatible:
  - (a) an essentially **positional** dependency;
  - (b) a "deck of cards" state where the permutations of the different letters differ on only **a few positions**. The state difference then keeps a small support, and is conjugated at each step.
- But a "pure" positional cipher with natural-language plaintext would give about 66 coincidences per 1000 at the same positions. 14.9 per 1000 are measured from position 50, for about 12 expected by chance. It would therefore require homophones flattening the distribution, chosen by a message-dependent rule.

## 4. Where to look next (proposal)

The profile that fits everything:

- state = a wheel or deck of 83 symbols;
- at each letter, the output is read at a notch depending on the letter;
- then the state undergoes a **fixed transformation** (for example a shift of one notch) **followed by a small letter-dependent modification** (a swap, for example).

This profile gives:

- isomorphs, since it is a group structure;
- possible fixed points (S83);
- local differences and resynchronisations;
- no doubles, if the notch read is never the one just read;
- gaps close to random, thanks to the fixed rotation.

This is the "Chaocipher / dynamic permutation wheel" family. The next step would be to simulate several variants of this family on English and Finnish text (the corpora are already in `corpus/`), then compare their fingerprint (`stats.fingerprint`) and resynchronisation behaviour with the eyes.

## 6. Mapping the plaintext differences (2026-09-30)

Scripts:
- `plaintext_diff_map.py`: proven differences between aligned messages;
- `alignment_map.py`: shifted alignments, with a random baseline;
- `architecture.py`: blocks, with an automatic consistency check;
- `architecture.html`: the SVG map.

Model: GAK. Positions 0-indexed.

**Principle.**
- An isomorphism conflict between two positions proves a plaintext difference between them.
- A conflict-free window containing common repeats or identical symbols indicates shared text.
- Random baseline: about 1.8 false windows per corpus, with only 2 common repeats. Windows with 3 or more repeats are reliable.
- All the offsets found are consistent by transitivity. For example, E1→W1 = +2 and W1→E2 = +10 indeed give E1→E2 = +12.

```
(1 character = 2 positions ; A, B, C = shared text blocks of the group ; x = text of E3 found again in E4/W4/E5)
E1 .AAAAAAAAAA....AAAAAAAAAA.....AAAAAAAAA...........
W1 .AAAAAAAAAA....AAAAAAAAAA......AAAAAAAAA............
E2 .AAAAAAAAAA......AAAAAAAAAAA........AAAAAAAAA..............
W2 .BB...BBBBBBBBBBBB.................................
E3 .BB......BBBBBBBBBBBB...........xxxxxxxxxxxxxx.......................
W3 .BB......BBBBBBBBBBB..........................................
E4 .CCCCCCCCCC....CCCC.....CCCCCCCCC.CCCCCCCCCCCCCCCx..........
W4 .CCCCCCCCCC..............CCCCCCCCC..CCCCCCCCCCCCCCCx........
E5 .CCCCCCCCCC....CCCC.....CCCCCCCCC..CCCCCCCCCCCCCCCx......
```

**Group E1 / W1 / E2**
- **Opening**: positions 1-21, identical text in all three messages. Only position 0 differs.
- **E1/W1 "obstacle"**: at least **2** text differences, one in [22, 25], the other in [28, 33]. This is compatible with Lymm's hypothesis (two words of about 4 letters swapped).
- **E2**: inserts 5 more letters around positions 25-33.
- **Phrase A1**: E1 29-49 = W1 29-49 = E2 34-54.
- **Divergence** around 50 (difference forced in [42, 50] for E1/W1). The variable part has a length of 10, 12 and 17 letters depending on the message.
- **Phrase A2**: E1 60-77 = W1 62-79 = E2 72-89.
- **Refrain**: the 6 occurrences (A1 and A2 in each message) are consistent with each other on an 18-letter core. **Each message therefore repeats the same phrase twice.**

**Group E4 / W4 / E5**
- **Opening**: positions 1-20, shared by all three messages.
- **W4** changes text at position 21, then has 1 more letter than the others.
- **E4 and E5** stay aligned until about 47. 2 text differences are enough (around 21, then in [24, 28]) plus a third in [38, 48]. The other desynchronisations of the Stutter Section are explained by the hidden state of the deck.
- **Nearly shared ending**, with one-letter insertions:
  - C2: E4 47-64 = E5 48-65 = W4 49-66;
  - C3a: E4 68-89 = E5 69-90 = W4 71-92;
  - C3b: E4 90-97 = E5 91-98 = W4 93-100;
  - relative to E4, E5 is shifted by +1, and W4 by +2 then +3.
- **These three messages are almost three versions of the same text**, with a few words changed.

**Group W2 / E3 / W3 and links between groups**
- **Positions 1-5**: shared by the 6 messages W2 to E5. E3 even shares positions 1-9 with E4, W4 and E5.
- **Block B1**, weak evidence (2 repeats per pair), but with offsets consistent by transitivity: W2 12-34 = E3 18-40 = W3 17-39.
- **Link between groups**: **E3 63-90 = E4 72-99 = W4 75-102 = E5 73-100.** The text of E3 reappears in the shared ending of E4, W4 and E5.
- Outside these blocks, W2, E3 and W3 mostly have their own texts.

**What this brings to an attack.**
- About 12 blocks of identical text are now known, with their exact positions in each message. Each block gives a permutation π between its occurrences: these are the starting constraints of a GAK attack.
- The **one-letter insertions** (group E4/W4/E5) are valuable. Just after an insertion, two identical texts are shifted by one letter. The state difference between them is then the shuffle of a single letter, conjugated by the current state.
- **Limits.** The block boundaries are those of the conflict-free windows: the truly shared text may be a little shorter. And a block with no internal repeat (for example in the openings) is supported mainly by identical symbols.

## 7. Attack on test messages, then on the eyes (2026-09-30)

Scripts:
- `deckcipher.py`: position-read "deck of cards" ciphers, compiled with numba;
- `testbed.py`: test corpus with the architecture of the eyes, encrypted with a known key;
- `validate_testbed.py`: validation of the tools on this corpus;
- `qscan.py`: mechanism sweep;
- `swap_model_test.py` and `homophone_test.py`: tests of Lymm's hypothesis.

**7.1 Testbed.** 9 messages of 104 to 130 letters drawn from *Pride and Prejudice*:
- 3 groups, first letter = digit from 1 to 9;
- a shared opening of 21 letters for E1, W1 and E2, and 5 letters shared by the 6 messages W2 to E5;
- in group E1/W1/E2: swapped words, and a phrase repeated twice in each message;
- in group E4/W4/E5: three versions of one text, with one-letter insertions;
- a passage of E3 copied into E4, W4 and E5.

**7.2 Tool validation.**
- **Mapping** (`alignment_map`): 24 to 25 real shared blocks (of at least 12 letters) found out of 31, depending on the mechanism.
  - But **the false-window rate depends on the cipher**: from 18 out of 66 to 75 out of 117 in these very structured mechanisms, against about 1.8 per corpus on random data.
  - The blocks of section 6 are thus reliable only if the ciphertext of the eyes behaves like random, which its flat gap profile suggests.
  - Blocks with 3 or more common repeats, consistent by transitivity, remain the safest.
- **Mechanism sweep** (`qscan`): if the base shuffle is among the candidates, the right mechanism stands out very clearly (IoC of 5.5, 25 values of q, z = 11 to 41). If β is random, the sweep cannot find anything.

**7.3 The eyes through the sweep.** 3,712 mechanisms tested:
- 8 rules;
- 116 base shuffles (identity, reversal, 82 rotations, riffles, deals into k piles, milk, Monge, and their inverses);
- 2 orders;
- 2 initial decks (sorted and reversed).

Result: **no signal**. The best mechanism gives an IoC of 1.15 with 82 values of q, against 5.5 and about 35 values for a real mechanism. Max z = 4.3, as expected over 3,712 trials.
⇒ None of these natural mechanisms encrypted the eyes, **unless** the alphabet is flattened homophonic or the initial deck is shuffled by a key.

**7.4 The "base shuffle + small swaps" hypothesis (Lymm) put to the test.** GAK model σ_p = β∘τ_p, where τ_p contains the swap (0, a_p) and k−1 random swaps. Two constraints of the eyes are measured:
- **synchronisation**: identical ciphertext for 20 to 24 positions after a differing first letter;
- **flatness** of the gap profile: chi² over d = 2..40, measured the same way on the eyes and on the simulation; it is 63.2 for the eyes.

| k swaps/letter | 1 | 2 | 4 | 8 | 16 | 41 |
|---|---|---|---|---|---|---|
| P(sync ≥ 15 in both groups) | 0.23 | 0.03 | 0 | 0 | 0 | 0 |
| P(chi² ≤ eyes) | 0 | 0 | 0 | 0 | 0.10 | 0.33 |
| P(both) | 0 | 0 | 0 | 0 | 0 | 0 |

(40 draws per value of k.)
- **Why.** With few swaps, the card output follows the cycle of β and returns at fixed intervals. The gap profile then reproduces the frequency of the read positions, arranged along this cycle, hence the spikes.
- **With a flattened homophonic alphabet** (k = 1, homophones used in turn): median chi² of 94, P(chi² ≤ eyes) = 0.07. But the median synchronisation falls to 4, and P(both) = 0 over 40 draws.
- ⇒ **The simple forms of Lymm's hypothesis do not reproduce the eyes.** If the cipher is a deck of cards, its shuffles must be more structured: the letter-specific part must move the card just output, without touching the rest of the deck.

**Proposed next step.** Use the two constraints (synchronisation and flat profile), plus the absence of doubles, as an **evaluation function** to explore the mechanism space, before any attack. A mechanism satisfying all three would be a serious candidate, to which the mapping and the sweep would then be applied.

## 8. Exploring more structured mechanisms (2026-09-30)

Scripts: `explore.py`, `explore2.py`, `stutter_test.py`, `reinsert_scan.py`, `validate_reinsert.py`.

**Framework.** XGAK mechanisms:
1. read at a symbol-specific position q;
2. modification τ, which decides where the card read goes;
3. base shuffle β.

Each family is judged over 40 draws, with the test corpus with the architecture of the eyes, and measured on:
- synchronisation after a differing first letter;
- flatness of the gap profile (chi² ≤ 63.2);
- absence of doubles;
- the **texture of the Stutter Section**: between E4 and E5, positions 21..46, 42% identical positions and 11 =/. alternations.

**8.1 First trigram INSIDE the deck (`explore.py`).** No family passes.
- Without a base shuffle, "swap" synchronises perfectly, but degenerates into a periodic homophonic cipher.
- With a base shuffle, the profile is flat, but the first-letter difference is quickly re-read: median synchronisation of 3 to 5, against 20 to 24 for the eyes.
- "Reinsertion" desynchronises immediately (0).

**8.2 First trigram OUTSIDE the deck**: all messages restart from the same state after it. Lymm raises this possibility in the form of a number or checksum.

| τ (card read) | β | homophones | P(texture) | P(flat profile) | P(all, 0 doubles) |
|---|---|---|---|---|---|
| reinsertion | none | yes | 0.60 | 0.78 | **0.45** |
| reinsertion | cut 1 | yes | 0.55 | 0.70 | **0.42** |
| reinsertion | cycle 83 | no | 0.42 | 0.60 | 0.23 |
| swap | all | — | 0.00 | ≤ 0.15 | 0.00 |
| top | all | — | — | 0 (doubles) | 0.00 |

> **Correction (§10): homophones used in turn BREAK the isomorphs.** A same repeated phrase is isomorphic in only 3 draws out of 20, against 20 out of 20 without homophones. Yet the eyes have perfect isomorphs: **the "homophones yes" rows are therefore excluded**. What remains compatible: reinsertion without homophones (P(all) from 0.12 to 0.23 depending on β).

⇒ **First simple mechanism compatible with all the constraints tested:** the card is read at a symbol-specific position, removed, then reinserted at another symbol-specific position. A base shuffle is optional. Homophones help, and the first trigram stays outside the chaining.

- This is a very natural card operation, of the "move the card to position m" kind.
- It modifies a whole segment of the deck, not a few cards: this is consistent with the refutation of the "few swaps" model (§7.4).
- "Swap" fails because it resynchronises too cleanly after an edit.

**8.3 Attacking the eyes in this family (`reinsert_scan.py`).**
- **Principle.** If the destination is a fixed function f(q), the sequence of q values can be computed from the ciphertext. For the right mechanism, it uses only the read positions (about 41), and never the destinations.
- **Validation** on test messages (f(q) = q+17, homophones): the right mechanism stands out at z = −16, with 31 values against about 80.
- **Eyes**: 6,696 mechanisms tested (82 shifts q+k, mirror, top, bottom, multiplications, 34 base shuffles, sorted or reversed deck, first trigram outside or inside the deck). **No signal**: always 82 to 83 values, and a max z of about −4, as expected given the number of trials.
- ⇒ If it is a reinsertion, the destination table and/or the starting deck are **arbitrary (set by a key)**, not "natural".

**Limits.**
- A single source text (English).
- The edits of the test corpus were placed according to the mapping of the eyes. The texture test therefore checks the consistency of the cipher's response to these edits, not their location.
- 40 draws per family.
- Unverified assumptions: homophones used in turn, first trigram outside the chaining.

**Possible next step.** Attack an arbitrary destination table. Start from a sorted deck and an unknown table f, then simulated annealing on f seeks to minimise the number of distinct positions in the sequence of q values. It would first have to be validated on test messages.

## 9. Attack by searching for the reinsertion table (2026-09-30): failure, well documented

Scripts:
- `sa_reinsert.py`: simple annealing, score = entropy;
- `sa_progressive.py`: progressive annealing, score = "Chinese restaurant" likelihood;
- `beam_reinsert.py`: beam search with lookahead;
- `validate_sa.py`, `validate_sa2.py`, `validate_beam.py`, `basin_test.py`: validations.

**Test setting.** Mechanism of §8:
- sorted deck, no base shuffle, first symbol outside the deck;
- **arbitrary** destination table: 41 read positions, destinations taken among the other 42;
- flattened homophones;
- test corpus with the architecture of the eyes.

| Method | Score reached | True table | Exact destinations |
|---|---|---|---|
| simple annealing (entropy) | 6.07 bits | 4.70 bits | 2% |
| progressive annealing (L = 5, 10, …) | entropy 6.01 | 4.70 | 0% |
| beam B = 100 / 1000, lookahead 12 steps | nll 4,893 / 4,857 | 3,570 | 0% / 5% |

**Diagnosis.** The score is not at fault: it separates the right table very well.
- At L = 20: 630 against 773 ± 16 for a random table; a single error costs +27.
- Over the whole corpus: a single error costs +800.

The problem comes from the **search landscape**. Its basin of attraction can be measured by starting from the true table partially corrupted:

| Corrupted destinations | 5% | 10% | 25% | 50% |
|---|---|---|---|---|
| Annealing recovers the table | 2/4 | 1/4 | 0/4 | 0/4 |

A wrong destination only shifts a segment of cards by one notch. It betrays itself only much later, when letters repeat. The minimum is therefore a needle: **90 to 95% of the table would have to be known** for annealing to find the rest.

**Consequence.** I did not run these attacks on the eyes. A method that fails on test messages whose key is known cannot prove anything about the eyes, whether by success or failure.

**What could unblock the situation (leads):**
1. **Inject knowledge of the language.** The sequence of q values is a homophonic substitution of English or Finnish. The table and the plaintext would be sought jointly, with an n-gram score on a partial decryption, instead of the concentration of q alone.
2. **Exploit the shared text blocks (§6).** Between two occurrences of the same text, the q sequences must be identical. This is a strong constraint for pruning the search.
3. **Look for hints about the table in the game.** A "natural" mechanism would have been found by `reinsert_scan`; if the table comes from a keyword or game object, that is the way to go.

## 10. Lead 2: using the shared text blocks (2026-09-30)

Scripts: `testkey.py` (test key without homophones and true shared blocks), `beam_blocks.py`, `validate_blocks.py`.

**Prior correction.** Homophones used in turn break perfect isomorphs (see the note in §8). The model retained becomes: reinsertion **without** homophones, with one read position per letter (about 26 positions read).

**Method.**
- The 9 messages advance together, position by position, in a beam.
- The score combines three terms:
  - the "Chinese restaurant" likelihood (few read positions, often reused);
  - a penalty if two occurrences of the same text read different positions (blocks);
  - a penalty if a position declared as a destination is read, which never happens in a model without doubles.
- Validation on test messages, with the **true** shared blocks: 34 blocks, i.e. 876 imposed equalities.

**Results.**

| | nll | destination reads | violated blocks |
|---|---|---|---|
| true table | 3,143 | 0 | 0 |
| true table with 1 wrong destination | 4,136 | 83 | 387 |
| random table | 4,854 | 354 | 708 |

- The score is **extremely discriminating**: a single error violates 387 constraints.
- But the beam (B = 300 to 2,000, with or without blocks) recovers only **0 to 6%** of the destinations. Progressive annealing and the simple beam, re-run without homophones, fail too (0 to 3%).

**Diagnosis.**
- At the start of each group, some twenty letters appear for the first time, and their destinations have to be fixed (83 choices each).
- As long as a moved card has not been re-read, these choices have no observable effect. They are therefore tied, and the beam settles them arbitrarily.
- The hints (repeats, blocks, destination reads) only arrive afterwards, when the right hypothesis has already been eliminated.

**What would be needed: a "lazy" search.**
- Do not choose the destination of a card when it is reinserted.
- Keep it "pending", and only settle it when a later read depends on it (which card is at position q?).
- The number of hypotheses then grows only with the information actually available. This is a constraint search, no longer a sampling one: a real algorithmic undertaking.

**Not run on the eyes**, for the same reason as in §9.

## 11. Exact lazy search (2026-09-30, in progress)

Scripts: `lazy_beam.py` (heuristic version), `lazy_exact.py` (one pending card at a time, exact intervals), `diag_lazy.py`, `validate_lazy*.py`.

**Heuristic version** (`lazy_beam.py`, pending cards removed, rank guessed greedily): **failure**, for a fundamental reason. Hypotheses leaving many cards pending receive an optimistic and free score: the true table scores 118.8 at event 24, against 84.8 for the beam.

**Exact version** (`lazy_exact.py`).
- **Principle**: the destination of a pending card is an interval [mlo, mhi]. Each read cuts it into two branches (the pending card is in front of or behind the card read), and the score separates these branches immediately.
- **Score correction**: the "Chinese restaurant" likelihood was replaced by a Dirichlet-multinomial on a finite alphabet (30 letters, β = 0.5). With this score, the true table is only slightly worse at the start (92.1 against 88.7 at event 20). It becomes **better than the whole beam from event 40** (159 against 170), then overwhelming (3,125 against 24,000 at the end).
- **But the true branch leaves the beam from event 3**, at rank 75,362 out of 157,145 candidates, with B = 2,000 (same with B = 5,000).
- **Cause**: the limit of a single pending card. At the start of a text, a new letter arrives almost at every step, which forces settling the previous card over its whole interval (83 values), with no hint.
- **Next step**: handle **several pending cards simultaneously** (intervals and relative order between pending cards). This is the complete version of the lazy search.

## 12. Hypothesis "key drawn from another game secret": the cauldron (2026-09-30)

Script: `cauldron_key_test.py`.

**Idea** (proposed by the repository owner): if the eyes are a keyed deck of cards (§8: no "natural" table works), the key might come from another Noita secret.
- The cauldron calendar is a block of **64 bytes (512 bits)** in the executable, of which only 365 bits are used for the daily calendar (reading shifted by 156 days, cf. `sources/github/ToboterXP_EyeGlyphs/cauldron data/`).
- A permutation of 83 cards needs about 414 bits: the 64 bytes would be enough to encode one.
- Toboter had already tried AES decryption of this block with phrases from the game, and a base-7 conversion: without success.

**Test.**
- 20 permutations derived from the block: Lehmer code (big-endian or little-endian integer, bits in both orders), sorting of 6-bit blocks, byte-by-byte or bit-by-bit Fisher-Yates, and their inverses.
- Each is tried as a starting deck (8 rules × 6 shuffles × 2 orders), as a base shuffle (sorted or reversed deck) and as a reinsertion table (sorted deck or = permutation, first trigram outside or inside the deck).
- Baseline: the same tests with 200 random permutations.

**Result: no signal.** Best cauldron IoC 1.126, against 1.113 ± 0.013 for random permutations (15% of them do better). All 83 positions are always read. A real mechanism would give an IoC of about 5.5 with 25 to 31 positions.

**Limits.** This test covers only these derivations and roles. Other encodings of the block, the 365 calendar bits alone, or other secrets (game keywords used to order the deck, tablet texts, "lumikki", orb positions) remain to be tested. **Keyword-ordered decks** (like classic keyword alphabets) are the most natural and least costly next lead.

### 12.2 Keyword-ordered decks drawn from the game and the wiki (`keyword_decks.py`, 2026-09-30)

**Sources** (downloaded to `sources/gamedata/`):
- all game texts: `translations/common.csv`, English column and internal identifiers;
- the credits, `magic_numbers.xml`, `debug_keys.txt`;
- **148 pages of the official wiki** (Secrets category, items, lore, glitches, flags…);
- the tablet texts;
- community words (lumikki, Kolmisilmä, AS ABOVE SO BELOW…).

This gives **24,533 keywords**: each word of at least 3 letters and each phrase of at least 8 letters.

**Constructions.** Letters (A=0) in order of appearance, or ASCII+32 values of the raw text, or ASCII+32 in upper case; then the remaining cards; plus the inverse of each. That makes **122,954 distinct decks**.

**Test battery** for each deck:
- as a starting deck (8 rules × no shuffle or cutting one card × 2 orders);
- as a base shuffle (8 rules × 2 orders);
- as a reinsertion table (sorted deck or = keyword deck, first trigram outside or inside the deck).

**Positive control** (`check_keyword_battery.py`): test messages encrypted with a "LUMIKKI" deck are detected unambiguously. As a starting deck, IoC of 5.53; as a reinsertion table, 25 positions read against 83 for a control.

**Result on the eyes: no signal.**
- Best IoC: 1.180 ("statusdesc brain damage", ASCII inverse). The record of 2,000 random permutations is 1.174; for 123,000 trials, a maximum around 1.18 is expected.
- The displayed "z" values (up to 6) come from the non-Gaussian tail of the maximum: **this is not a detection**. A real mechanism would give an IoC of 3 to 5.5.
- In reinsertion, always 82 to 83 positions read, against about 25 to 31 expected for a real mechanism.

⇒ No deck ordered by a word or phrase from the game or wiki, according to these constructions, is the key of these mechanism families.

**Not covered:**
- numeric keys (seeds, dates, 1602761874…) passed through **Noita's pseudo-random generator**, which would be a very natural way for a developer to shuffle a deck;
- other constructions (keyword then remainder in reverse order, keyword columns);
- mechanisms outside these families.

### 12.3 Decks shuffled by Noita's pseudo-random generator (`rng_decks.py`, `run_rng_scan.py`, 2026-09-30 – 2026-10-01)

**Generator.** This is Noita's generator as reconstructed by the seed-searching community (`sources/github/pudy248_NoitaSeedSearcherCUDA/src/misc.cpp`, agreeing with `TwoAbove_noita-tools`):
- **Next**: Park-Miller, 16807 and 2³¹−1, in signed 32-bit integers with C overflow;
- **Random(a, b)**: a + (int)((b−a+1) × Seed × 4.656612875e-10);
- **SetRandomSeed(x, y)**: hash of the world seed and the coordinates (CPU version in misc.cpp).

Check: the sequence 16807, 282475249, 1622650073 is reproduced identically.

**Shuffles**: descending Fisher-Yates (j = Random(0, i)); ascending Fisher-Yates (j = Random(i, 82)); sort by random keys.

**Seeds**:
- **direct from 0 to 5,000,000**, taken as is or after one Next(), with the 3 shuffles, i.e. 6 decks per seed;
- **SetRandomSeed(x, y)** for x and y from −100 to 100, with 30 "special" world seeds: 0 to 3, 9, 11, 12, 26, 27, 33, 34, 42, 83, 125, 666, 777, 1036, 1337, the sums 4040, 4545 and 5656, 12345, the dates 20201015 and 15102020, the release date 1602761874, the constant 0x93262e6f, the "lumikki" block words 0xacf68674 and 0x5634505c, 123456789 and 2³¹−1. With the 3 shuffles.

**Battery and control.**
- Each deck is tested as a starting deck (8 rules), as a base shuffle (8 rules) and as a reinsertion table (first trigram outside or inside the deck).
- Sorting is done on 3 messages from different groups (E1, W2, E4), for speed; the best candidates are then re-checked on the 9 messages.
- Positive control: on test messages shuffled by seed 123456, the sweep recovers this seed with an IoC of 5.37.

**Result: no signal.**
- The blocks of 250,000 seeds from 0 to 2,250,000 were swept before an interruption. Their best scores (1.32 to 1.375) were noted, but the candidates were not kept for re-checking.
- Over the 3,962,030 seeds swept afterwards, the maximal IoC per seed has a median of 1.127, a 99.99th percentile of 1.281 and a record of 1.400, on 3 messages.
- Re-checked on the 9 messages, the best 12 fall back between 1.09 and 1.17, within the noise of random permutations (record 1.17), with always 83 positions read.
- A real mechanism would give an IoC of 3 to 5.5.

⇒ None of these seeds, with these shuffles, produces the key of a deck in these mechanism families.

**Not covered:**
- seeds beyond 5 million;
- SetRandomSeed with other coordinates or other world seeds;
- other generators (MSVC rand(), C++ or Python Mersenne Twister, Lua math.random);
- other ways of consuming the generator;
- mechanisms outside these families.

## 13. Fixed-point test after insertion: reinsertion ALONE is refuted (2026-10-01)

Scripts: `cycle_structure.py`, `fixed_points_test.py`, `joint_test.py`.

**Principle.** In any XGAK cipher, if two messages have the same text from a given point, their ciphertexts are linked by a fixed bijection π (c' = π(c)). Suppose one of the two texts contains **an inserted letter** x, and that the decks are identical just before. Then π = D·σ_x·D⁻¹ is a conjugate of the shuffle of letter x, and it therefore has the **same cycle type** as σ_x.
- For **reinsertion alone** (remove at q, reinsert at m), σ_x is a cycle on the segment [q, m]: all cards outside the segment are **fixed points** (c' = c).
- For a **swap**, σ_x is a transposition: almost everything is fixed.

**Eyes.** 10 shifted blocks (E4/E5 +1, W4/E5 −1 and +2, E4/W4 +2 and +3, E1/W1 +2, E1/E2 and W1/E2 +5, W1/E2 +10), i.e. about **210 symbol pairs: 0 fixed points**. No chain closes into a short cycle; the longest chain has 7 cards (E4@68 → W4@71).

**Models** (testbed, blocks following the known insertions, 40 keys):

| Model | Share of fixed points (median) | P(≤ 1%) |
|---|---|---|
| reinsertion without base shuffle, mixed table | 0.23 | 0.00 |
| reinsertion without shuffle, reads at the top / destinations at the bottom | 0.17 | 0.00 |
| random permutations S83 | 0.02 | 0.47 |

⇒ **Each letter of the eyes seems to move (almost) all the cards.** Reinsertion without a base shuffle (§8) is **refuted**, as are swap and card-put-back-on-top without a shuffle.

**Joint test** (`joint_test.py`, first trigram outside the deck, no homophones, 40 keys): flat profile, 0 doubles, Stutter Section texture, fixed points ≤ 1%.

| τ (card read) | β | P(flat) | P(texture) | P(fix. points ≤ 1%) | P(ALL) |
|---|---|---|---|---|---|
| reinsertion | none | 0.33 | 0.45 | 0.00 | 0.00 |
| reinsertion | cut 1 | 0.23 | 0.47 | 0.12 | 0.00 |
| reinsertion | random 83-cycle | 0.42 | 0.47 | 0.35 | **0.03** |
| reinsertion | random permutation | 0.45 | 0.30 | 0.47 | **0.10** |
| swap / top | all | ≤ 0.03 | 0.00 | — | 0.00 |

⇒ **Only reinsertion followed by a "rich" base shuffle β survives** (random, hence set by a key). The attack would then have to recover a reinsertion table **and** a permutation β of 83 cards, i.e. about 414 more bits.

**To go further**: systematic exploration of about 220 families (`family_zoo.py`, 8 ways of moving the card read × 7 base shuffles × 2 orders × first trigram inside or outside the deck).

## 14. Zoo of structured families (`family_zoo.py`, 2026-10-01)

208 XGAK families = 8 gestures on the card read × 7 base shuffles × 2 orders × first trigram inside or outside the deck.
- **Gestures**: reinsertion at m_p, on top, at the bottom, swap with m_p, swap with the top, reversal of the segment q_p..m_p, cut at q_p, nothing.
- **Base shuffles**: none, cut 1, out-riffle, 3 piles, 83-cycle, random permutation, mirror.
- **Protocol**: testbed without homophones, 30 keys per family. For each key, up to 25 draws to find one with no doubles.
- **Criteria**: flat profile, 0 doubles, Stutter Section texture, fixed points ≤ 1% after insertion, and synchronisation ≥ 15 if the first trigram is inside the deck.

**Results.**
- **First trigram INSIDE the deck: no family passes** (104 families, P(ALL) = 0 everywhere). Those that synchronise (swaps: P(sync) up to 0.33) fail on the flat profile and the texture; the others do not synchronise.
  ⇒ In these families, the first trigram is not encrypted like the rest. This matches a hypothesis that Lymm left open.
- **First trigram OUTSIDE the deck**: only **reinsertion** and **segment reversal** pass, always with a base shuffle.

| Family | P(ALL) |
|---|---|
| reinsertion + random permutation (order 0) | 0.17 |
| reversal + random permutation (order 0 / 1) | 0.17 / 0.13 |
| reinsertion + out-riffle (order 1 / 0) | 0.10 / 0.07 |
| reinsertion + random permutation (order 1) | 0.10 |
| reversal + 3 piles (order 1) | 0.10 |
| reinsertion + 3 piles, + 83-cycle; reversal + cut 1, + riffle, + mirror, + 83-cycle | 0.03 to 0.07 |
| top or bottom + 3 piles | 0.03 (marginal) |
| swap, swap with top, cut, nothing | 0 |

- **Short closed cycles** in the mappings (`closed_cycles_test.py`): 62 to 93% of keys have none, like the eyes. This test therefore does not separate the survivors.
- **Consequence for the attack.** With a "natural" base shuffle (riffle, 3 piles, cut 1, mirror), the key reduces to the letters' table (q_p, m_p), and β is one of a handful of candidates.

## 15. The first trigram is not a simple checksum (`first_trigram_checksum.py`, 2026-10-01)

- **Functions tested** on the rest of the message: sum, position-weighted sum, alternating sum, XOR, last and second-to-last trigram, length, message rank, rank per world, sum of eyes, product mod 83, number of distinct symbols, sum of differences.
- **Form tested**: first = f + k, k − f or k·f (mod 83 or mod 125), i.e. about 8,400 relations.
- **Result**: none explains 4 messages out of 9.
- First trigrams: 50, 80, 36, 76, 63, 34, 27, 77, 33.

**Robustness of §13.** Keeping only the 4 safest blocks (at least 5 common repeats) and trimming 3 positions at each end: 0 fixed points over 85 pairs. With reinsertion alone (share of fixed points from 0.17 to 0.23), the probability of observing none would be about 1e-7.

## 16. Exact attack by constraint programming (OR-Tools CP-SAT): does not scale (2026-10-01)

Scripts: `cpsat_reinsert.py`, `validate_cpsat.py`, `validate_cpsat_blocks.py`.

**Model.**
- Unknowns: the table F (83 integers).
- The positions of the 83 cards at each step are derived by exact reinsertion constraints (with a possible known base shuffle β).
- Each position read must belong to R; objective: minimise |R|.
- Options: a destination is never read; equalities imposed by the shared text blocks.

**Validation** (test key, reinsertion without shuffle):

| Prefix | Messages | Extra constraints | Result (16 cores) | True table |
|---|---|---|---|---|
| L = 12 | 3 | — | OPTIMAL in 74 s: 11 positions, 1/15 destination correct | 15 positions |
| L = 20 | 3 | destinations never read | 16 positions in 20 min (bound 14), 0/19 correct | 19 positions |
| L = 30 | 3 | destinations never read | 29 positions in 20 min (bound 12), 1/20 correct | 20 positions |
| L = 20 | 9 | + 115 block equalities | 33 positions in 15 min (bound 10), 1/20 correct | 20 positions |

**Reading.**
- On short prefixes, there are wrong tables **better than the true one** for this criterion: the problem is not identifiable.
- As soon as the prefix is long enough to become so, the model (positions of the 83 cards at each step) is too big, and the solver no longer converges.
- A more compact formulation (following only the cards that will be read) remains to be tried.

## 17. Chaocipher adapted to 83 symbols: excluded (`chaocipher_test.py`, 2026-10-01)

- **Setup**: cipher alphabet of 83 cards, plain alphabet of 83 slots (35 symbols), nadir at 41, Byrne's permutations.
- **Result**: in the testbed, the 6 occurrences of the repeated phrase are mutually isomorphic in **0 keys out of 40**, against 40 out of 40 for any XGAK.
- **Reason**: the position read depends on the state of the plain alphabet, which prevents the perfect isomorphs shown by the eyes.

## 18. Remark on the scope of the key sweeps (§12)

The "key drawn from the game" sweeps (cauldron, keywords, Noita generator) mostly tested mechanisms that the zoo (§14) now excludes statistically: card put back on top, bottom, swap, and reinsertion without a base shuffle. They therefore bring almost nothing on the surviving family (reinsertion or reversal **+ base shuffle β**), whose key comprises both the letters' table and β. A new sweep would have to generate these two elements, which supposes guessing the designer's conventions.

## 19. The E1/W1 "obstacle" strongly constrains the surviving families (`obstacle_test.py`, 2026-10-01)

**Eyes.** E1/W1, positions 29..49: 17 identical positions out of 21 (81%), of which 37..49 in a row (13). Text differences are proven in [22, 25] and [28, 33] (§6).

**Mechanism.** In the model "letter-specific gesture τ_p, then common shuffle β":
- a one-letter **substitution** leaves a deck difference conjugate to τ_b·τ_a⁻¹, where **β cancels out**: its support is small, hence the resynchronisations;
- an **insertion** leaves a difference conjugate to τ_x·β, which moves all the cards: no fixed points (§13);
- **several differing letters in a row** interleave βs that no longer cancel: the difference becomes large and resynchronisation rare.

**Testbed** (window +4..+24 after the first difference, 40 keys):

| Family | Swap of two 4-letter words: identical share / longest run | Two one-letter substitutions: share / run (P(≥ 80% and run ≥ 13)) |
|---|---|---|
| reinsertion + random | 0.02 / 0 | 0.29 / 2 (0.05) |
| reinsertion + riffle | 0.00 / 0 | 0.29 / 2 (0.00) |
| reinsertion + 3 piles | 0.00 / 0 | 0.38 / 3 (0.00) |
| reversal + random | 0.00 / 0 | 0.24 / 2 (0.00) |
| reversal + 3 piles | 0.00 / 0 | 0.19 / 2 (0.00) |
| reinsertion without β (excluded in §13) | 0.43 / 4 | 0.29 / 2 (0.00) |

⇒ **Under these models, the obstacle cannot be a word swap** (contrary to Lymm's hypothesis). Even with isolated substitutions, the resynchronisation of the eyes (81%, run of 13) is rare (P ≤ 0.05).

The eyes demand both a "dirty" desynchronisation (the E4/E5 stutter: 42% identical) and a "clean" resynchronisation (the E1/W1 obstacle: 81%). **Hypothesis to test**: the reach of the gesture varies with the letter (`segment_length_test.py`).

## 20. Reach of the gestures: a trade-off the eyes stretch to the limit (`segment_length_test.py`, `segment_mix_test.py`, 2026-10-01)

**Protocol.** Reinsertion or reversal, followed by a base shuffle β (random, riffle, 3 piles, cut 1). The destination is m_p = q_p + δ, with |δ| ≤ K (the reach). First trigram outside the deck, no homophones, 100 keys per family.

**Criteria (all at once)**: flat profile, 0 doubles, E4/E5 stutter, fixed points ≤ 1%, and **E1/W1 obstacle** (W1 = E1 with two one-letter substitutions; ≥ 80% identical and run ≥ 13 in the window +4..+24).

**Uniform reach K** (`segment_length_test.py`, 36 families):
- **Small K (2 to 5)**: the obstacle passes (0.10 to 0.44), but the flat profile (≤ 0.12) and the stutter (≤ 0.01) fail;
- **Large K (≥ 20)**: flat profile (0.28 to 0.57) and stutter (0.23 to 0.59) pass, but the obstacle fails (0.00 to 0.02);
- **P(ALL) = 0 in all 36 families.**

**Letter-dependent reach, and β "cut 1"** (`segment_mix_test.py`):

| Family | P(ALL) |
|---|---|
| reinsertion + riffle, reaches {2, 41} | 0.01 |
| reversal + random, reaches {3, 82} | 0.01 |
| reversal + riffle, reaches {2, 41} | 0.01 |
| other combinations of variable reaches | 0.00 |
| β = cut 1 (reaches 2, 5, 10, 41 or {2, 41}) | 0.00: fails on the fixed points (≤ 0.31) and the stutter |

**Reading.**
- The eyes combine a **long memory** (no fixed points after insertion), a **clean resynchronisation** (the obstacle) and a **dirty desynchronisation** (the stutter).
- In all the "letter gesture + base shuffle" families tested, this combination happens at best in **about 1% of keys**. The model is not refuted, but it is under strain.
- Caveat: the testbed fixes one realisation of the texts (substituted letters Q/Z, precise positions). Another realisation of the text differences might be more favourable.

**Open leads.**
- Mechanisms with a "resynchronising" state (generalised CTAK, state = last outputs). They must however remain perfectly isomorphic (Lymm: only GAK and XGAK are) and non-commutative.
- Or a base shuffle that partly commutes with the letters' gestures.

## 21. Checks of the tension (`fair_joint_test.py`, `context_homophone_test.py`, 2026-10-01)

**Substituted letters drawn at random** according to English frequencies, instead of the rare letters Q/X/Z (60 keys per family, 28 families: swap, swap with top, reinsertion, reversal × 4 base shuffles × reach 82 or 5):
- P(ALL) = 0 everywhere;
- swaps always fail on the flat profile (≤ 0.03) and the stutter (0.00);
- long-reach reinsertion and reversal fail on the obstacle (0.00); at short reach, on the flat profile and the stutter.

⇒ The letter bias of the testbed did not explain the tension.

**Homophones chosen from the previous letter** (deterministic, hence compatible with perfect isomorphs up to one symbol; 41 or 60 slots):
- isomorphs preserved in 100% of keys;
- flat profile improved for short gestures (K = 5: 0.23 to 0.62, against ≤ 0.15 without homophones);
- but P(ALL) = 0 in the 24 variants (60 keys each). The best compromise (K = 5, 60 slots) obtains flat 0.53, stutter 0.30, obstacle 0.08.

**Overnight summary (§13 to §21).** The eyes simultaneously demand:
1. **no fixed points** after an insertion: each letter moves all the cards;
2. a **clean resynchronisation** after the substitutions of the obstacle: two letters differ by few cards;
3. a **"dirty" stutter** (42% identical) after the substitutions of E4/E5;
4. a **flat gap profile**;
5. no doubles, and perfect isomorphs.

No deck family tested (about 330 configurations) combines them in more than about 1% of keys. This is not a refutation: each criterion compares with a single observation of the eyes, with a tolerance. But it is a **strong tension** for the whole class "letter-specific gesture + common base shuffle".

## 22. Variable reach + homophones from the previous letter (`mixed_context_test.py`, 2026-10-01)

**Theoretical reminder (holds for any XGAK).** Once two texts are identical again, c' = π(c) with π fixed. A position is identical exactly when the card read is a fixed point of π: there is no "spontaneous" resynchronisation. The observations therefore translate as follows:
- the E1/W1 obstacle means that π has **small support**;
- the E4/E5 stutter means that π has **medium support**;
- an insertion gives a π **with no fixed points**.

In the model "gesture τ_p + shuffle β", the support of π after a substitution is that of τ_b·τ_a⁻¹: it depends on the reach of the letters involved.

**Test**: reaches drawn per letter in (2, 41), (3, 82), (2, 5, 41) or (5, 20), with homophones chosen from the previous letter (41 or 60 slots), reinsertion or reversal, β random or riffle, 100 keys per family. Criteria: isomorphs, flat profile, 0 doubles, stutter, fixed points, obstacle (letters substituted at random).
- Isomorphs: 1.00 everywhere.
- Flat profile: 0.37 to 0.68; stutter: 0.25 to 0.60; fixed points: 0.42 to 0.70; obstacle: 0.01 to 0.11.
- **P(ALL) ≤ 0.02** (at best 2%: reinsertion + random, reaches (3, 82), 41 slots; reversal + random, reaches (2, 41), 41 slots).

**Reading.** The obstacle requires the 4 letters of the two substitutions of E1/W1 all to have a short gesture. With a reach drawn between "short" and "long", this happens with a probability of about (1/2)⁴ ≈ 6%, which the measurements confirm. It is therefore not an impossibility but a **constraint on the key and on the text**: the letters swapped in the obstacle would be short-gesture letters. The "gesture + shuffle" class stays alive, with a joint probability of about 1 to 2%.

## 23. Model-free measures, swaps + homophones, and commutative models (2026-10-01, after compaction)

**23.1 Spectrum of supports (`support_spectrum.py`).** In any XGAK, after the last text difference, c' = π(c) with π fixed, and a position is identical exactly when the card read is a fixed point of π. Assuming a roughly uniform reading of the cards (flat profile), the size of the support of π is estimated:

| Window (0-indexed positions) | Identical | Estimated |supp π| (90%) |
|---|---|---|
| E1/W1 34..49 (after the 2nd difference of the obstacle) | 13/16 | 16 (8..33) |
| E1/W1 26..49 (ignoring the 2nd difference) | 17/24 | 24 (15..38) |
| E4/E5 21..46 (stutter, ≥ 2 differences inside) | 11/26 | 48 (35..60) |
| E4/E5 29..37 (block C1) | 4/9 | 46 (25..65) |

Reminder: an insertion gives a π with no fixed points (support 83, §13). Lymm describes the obstacle as 4 different, 4 identical, 4 different, 13 identical (wiki, *The Funny-looking Obstacle*), i.e. two words of about 4 letters swapped. Read this way, the residual support after replacing a 4-letter word must be tiny (17 reads without touching it).

**23.2 Lymm's swaps + homophones from the previous letter (`swap_context_test.py`, 100 keys per configuration, 24 configurations).** τ = swap (q, m) + k−1 random swaps (k = 1, 2, 4), or swap with the top; β random or riffle; 35, 60 or 82 homophone slots.
- **New: deterministic homophones make the profile flat** for swaps (P(flat) from 0.50 to 0.67 with 60 or 82 slots, against ≤ 0.03 without homophones). Flatness alone is therefore no longer an argument against Lymm's model (§7.4, §14).
- But **the obstacle read as a word swap** is reproduced in only 0 to 4% of keys, in all configurations. Read as two one-letter substitutions, it passes in 20 to 51% of keys for k = 1.
- The stutter fails for k ≤ 2 (≤ 0.14). It passes for k = 4 (0.43 to 0.70), but then the obstacle fails.
- P(ALL) = 0 everywhere, with either reading of the obstacle.

⇒ Lymm's reading of the obstacle (word swap) is reproduced by **none** of the families tested, including theirs. Lymm writes that they reproduced it with deck ciphers: their parameters would be needed.

**23.3 Commutative models: single wheel, progressive alphabet, possibly homophonic.** A commutative GAK would resynchronise exactly after a swap of words of the same weight. It would leave no fixed points after an insertion. And with several wheels, a substitution would desynchronise only part of the deck. Lymm excludes them through commutativity conflicts; we checked with three tests.
- `single_wheel_all.py`, `single_wheel_cores.py`: a single wheel with a free offset per pair of blocks is **impossible** on the full cores. On the repeated-symbol columns alone, it is **compatible** without the isomorph W1@59~E3@90 (fixed point 17→17). But this test has almost no power: more than 200 solutions, components of 2 to 8 cards, and non-commutative ciphers pass in 2/12 to 7/19 control keys.
- `progressive_cores.py`: the pure progressive alphabet (δ = Δpos) is **impossible** on all columns (this confirms §2). It is compatible on the repeated columns without E3, but the test is weak here too: non-progressive controls pass in 2 to 3 keys out of 24.
- `progressive_redundancy.py`: the rate of redundant constraints satisfied does not discriminate (eyes 19%, control GAK 14 to 19%, progressive with homophones in turn 25%, pure progressive 98%). Block compositions are satisfied by any GAK.
- **`same_delta_test.py` (decisive)**: with a progressive alphabet, two *different* message pairs at the same gap Δ must have the same mapping (rotation by Δ notches). This is the case for E4→E5 and E5→W4 (Δ = 1), and for E5→W4, E4→W4 and E1→W1 (Δ = 2). Result: **2 agreements over 36 shared cards**, for about 0.4 expected in a GAK and about 36 with a progressive. The homophones would have to differ in more than 90% of the columns.

⇒ **Refuted**: progressive alphabet, even homophonic (codewarrior0's hypothesis). This confirms, by a test independent of the doubtful columns, Lymm's exclusion of commutative GAKs.

**Summary of §23.** The eyes demand that the permutations of two letters (or two words) be very close: obstacle, shared openings if the first trigram is inside the deck. They also demand that each letter be far from the identity (no fixed points after an insertion), and that the trajectory of the cards depend enough on the text to flatten the profile (with deterministic homophones, this is possible). No family tested reproduces the obstacle under its "word swap" reading.

## 24. The stutter, the no-doubles rule and the exact pattern of the obstacle (2026-10-01)

**24.1 How many differing letters in the stutter? (`stutter_budget_test.py`, 100 keys).** My testbed only put 2 substitutions in the E4/E5 stutter (21..46), whereas the eyes require at least 3 (§6) and perhaps more. Model: 1 or 2 swaps per slot, random β, homophones from the previous letter (60 slots), and Lymm's **no-doubles rule**: the card read never lands on a read position (`swap_context_test.make_key(nodouble=True)`).

| k | n differing letters | texture | P(ALL), loose obstacle (§19) |
|---|---|---|---|
| 1 | 2 / 4 / 6 / 8 / 10 | 0.40 / 0.83 / 0.84 / 0.69 / 0.33 | 0.02 / 0.05 / **0.07** / 0.06 / 0.02 |
| 2 | 2 / 4 / 6 / 8 / 10 | 0.78 / 0.80 / 0.44 / 0.21 / 0.10 | 0.01 / 0.01 / 0.02 / 0.00 / 0.00 |

- The no-doubles rule takes "0 doubles" from 0.2–0.3 to 1.00.
- This is the best joint score obtained so far (0.07), with the obstacle counted **loosely**: window d0+4..d0+24, ≥ 80% identical, run ≥ 13.
- Prediction of this model: E4 and E5 differ by about 4 to 8 letters between 21 and 46.

**24.2 The EXACT pattern of the obstacle (`obstacle_pattern_test.py`, 1,000 keys × 5 models × 3 readings).** The loose criterion ignores the first burst. The eyes show exactly 25-28 different, 29-32 identical, 33-36 different, 37-49 identical. Readings tested: two one-letter substitutions, two different 4-letter words, or two swapped words (Lymm). Models: swaps k = 1 + homophones + no-doubles; reinsertion or reversal + random β, with or without homophones.
- **1 success out of 15,000 trials** (swaps, "words" reading).

**Model-free argument (XGAK, roughly uniform reads; figures from `obstacle_bounds.py`).** After the last text difference, a position is identical if and only if the card read is a fixed point of π.
- If the second segment (33-36) is **not** a text difference, 4 reads of the support are needed between 4 and 13 clean reads: P ≤ max_s (1−s/83)^17 (s/83)^4 = 3.6·10⁻⁵ (reached for s = 16).
- If it is a text difference (two words), the support of π after 8 differing letters must be ≤ ~13 cards to have 17 clean reads with a reasonable probability. Since each differing letter adds at least 2 cards, a **cancellation** is needed: the second word must undo the first (word swap AND commuting permutations). Without cancellation, with h support cards added per differing letter, P(4 then 13 clean reads) is 0.041 for h = 2, 0.006 for h = 3 and 0.0008 for h = 4.
- The differences of the eyes are also very **clustered**. If the only text difference is at 25, there are 4 runs for 24 positions of which 7 differ, against 10.9 on average for randomly permuted positions (P(≤ 4) = 0.0008).

**24.3 Context-dependent read (`context_read_test.py`).** Read position chosen by the letter and the w−1 previous ones, shuffle chosen by the letter alone. A substitution would then give a burst of w differing outputs.
- The exact pattern never appears (0/100 for w = 1, 2 and 4), because letters with 1 or 2 slots often give the same read.
- Doubles explode (P(0 doubles) = 0.00 for w = 4).
- **Inconclusive / unfavourable.**

## 25. Commutativity: what the eyes really say (2026-10-01)

**25.1 Commutativity conflicts in the main family (`commutativity_test.py`).** For three occurrences X, Y, Z, we test π_XY∘π_XZ = π_XZ∘π_XY wherever it is defined.
- 4 safe occurrences: 2 possible tests, 2 failures, and they involve columns 2 and 15.
- With E1@62: 9 tests, 9 failures. Without columns 2 and 15, 2 tests remain (2 failures), going through columns 3, 4 and 12 of E1@62. This occurrence is the shortest and chains badly outside the core (§2).
- **No test is possible on the repeated-symbol columns.**
- Controls: abelian GAK with 2 wheels, 0 failures over 43 tests per key; reinsertion + β, 98% failures.

⇒ In the main family, the proof of non-commutativity relies on fragile columns. Lymm may have other examples elsewhere: **to be asked of them**.

**25.2 The trilemma of commutative models (reasoning, figures from §13 and §23).** In an abelian GAK (one or several wheels, each letter p turning wheel i by k_{p,i}), conjugation is trivial. After an insertion of x, π = σ_x; after a substitution of a by b, π = σ_b σ_a⁻¹; a word swap cancels exactly.
- **Dense moves** (k_{p,i} ≠ 0 almost everywhere): a substitution shifts all the wheels, so no clean read in 29-32 (obstacle) ✗.
- **Sparse moves** (each letter touches few wheels): an insertion leaves almost all cards fixed, against 0 fixed points over 210 pairs (§13) ✗.
- **Global step β + sparse moves**: after insertions x and y, π = βρ_x and βρ_y agree on all untouched wheels. But the "same shift" test gives 0 agreements over 11 cards (E4→E5 against E5→W4) ✗.

⇒ **Refuted** without resorting to commutativity conflicts: a commutative GAK cannot combine the fixed points, the "same shift" test and the partial resynchronisation of the obstacle.

**25.3 "Same shift" test on the models (`same_delta_models.py`, 30 keys, testbed).** Agreement rate between different message pairs at the same Δ:

| Model | Agreement rate | P(≤ eyes) |
|---|---|---|
| progressive | 1.00 | 0.00 |
| swaps k = 1 (with or without homophones) | 0.09 to 0.10 | 0.07 to 0.20 |
| swaps k = 4, reinsertion, reversal, random S83 | 0.01 to 0.02 | ≥ 0.97 |

The eyes give 2/36 = 0.056: compatible with all non-commutative models. This test therefore only separates the progressive and commutative models.

**25.4 Bursts by rotation (`burst_sweep.py`, 300 keys per configuration, 45 configurations).** Clustered read in a zone of Z cards (35, 50, 83). Card read reinserted at random, deep or at the bottom, then rotation by c cards (c = 1, 2, 3, 5, 8, 13).
- Exact 4/4/4/13 pattern: **0** everywhere, except "bottom + cut 2, Z = 35" (1% in the "word swap" reading, 0.3% in the "words" reading). But this configuration has a gap profile that is never flat (P(flat) = 0.00) and a stutter at 0.03.
- More generally, rotations never give a flat profile with a deep or bottom destination (P(flat) ≤ 0.02). With a free destination, P(flat) ≤ 0.40, but then there are doubles (P(0 doubles) ≤ 0.12).

**Summary of §23 to §25.**
1. **Refuted**: progressive alphabet, even homophonic ("same shift" test); any commutative GAK (trilemma of §25.2).
2. **Best model to date**: Lymm's (1 swap per slot + random β), with homophones chosen from the previous letter and the no-doubles rule. P(ALL) ≈ 0.07 if the stutter contains 4 to 8 differing letters, but only with the loose obstacle criterion.
3. **Main anomaly: the exact pattern of the obstacle.** It appears once in 15,000 trials in the "gesture + β" models, and about 1% at best in a rotation configuration excluded on other grounds. Without a model, it requires either a cancellation (swapped words whose permutations commute), or very clustered reads of the perturbed cards. In any non-commutative XGAK, cancellation is rare.
4. **To ask Lymm**: the parameters with which the obstacle was "reproduced with deck ciphers", and the commutativity conflicts observed outside the fragile columns of the main family.

*English summary updated on 2026-10-01 (rev 27): Results 9 (commutative models, Lymm's model with homophones) and 10 (exact pattern of the obstacle), plus two questions for Lymm.*

## 26. Do the letters modify the deck? "Space" model and coincidences after divergence (2026-10-01)

Context: Lymm is no longer active. I was left free to explore algorithms other than the deck of cards.

**26.1 Model "common shuffle + special symbols" (`special_letters_test.py`, `testbed_spaces.py`, `space_model_test.py`).** The letter only chooses the card read; the deck undergoes the same shuffle β for all letters, except one or a few "special" symbols (the space, for example) that apply σ.
- A substitution between ordinary letters does not change the deck: the exact pattern of the obstacle (4/4/4/13) comes out **deterministically**, if the swapped words have the same length and no special letter.
- An insertion gives π conjugate to β, hence 0 fixed points if β is a derangement.
- If the first symbol is ordinary, it does not touch the deck: the first trigram can be **inside** the cipher, and the openings stay identical.
- Testbed with spaces (18% spaces; obstacle "JANE_TO_ONLY" / "ONLY_TO_JANE"), space = random permutation, 100 keys: isomorphs 1.00, exact pattern **1.00**, flat 0.27–0.46 (median chi² 66–72, eyes 63), fixed points ≈ 0.5, "same Δ" agreement 0.009 (compatible).
- Failure: the texture of the stutter (0.12–0.17). In this model, differing letters do not desynchronise the deck. The stutter would then mean that E4 and E5 have, in 21..41, words of the same lengths with about half of the letters in common at the same place.
- Special letters among A-Z (`special_letters_test.py`): rare ones (JQXZ), pattern 0.96–1.00 but a profile never flat; frequent ones (E, ET, ETAO…), flat profile up to 0.58 but pattern 0 (the testbed's obstacle words contain these letters).
- **Natural sweep (`scan_space_natural.py`)**: deterministic decryption if (β, σ, D0, q_space) are known. We sweep 116 × 115 pairs of natural shuffles × 2 starting decks × 83 space positions × first symbol inside or outside. Validation: the true combination comes out with 35 positions, the next at 82. **Eyes: no signal** (at best 82 positions). If this model is the right one, β and σ are keyed.
- Novelty: this model does not appear in the sources.

**26.2 Coincidences at the same position just after a divergence (`post_divergence_test.py`, `lineage_coincidence.py`).** Examples:
- position 20: symbol 47 in W2, E3, E4, W4 and E5, whereas W2 diverges from the E4 group from 6 and E3 from 10;
- position 22: symbol 21 in W2, W4 and E5;
- position 10: symbol 42 in E1, W1, E2 and W2.

Lymm had noticed these alignments in *Eye Message Alignments* ("individual letters shared more randomly"). They first read them as identical plaintext letters, then abandoned the idea. Count by **lineages** (messages with identical history merged):

| Pairs counted | Window div+1..div+20 | Far zone (> div+30) | Chance (2,000 corpora) |
|---|---|---|---|
| all | 35/341 (0.103) | 34/2495 (0.014) | 4.2 on average, P(≥ 35) < 0.0005 |
| without E1/W1 and E4/E5 | 12/301 (0.040) | 32/2390 (0.013) | 3.7, P(≥ 12) = 0.002 |
| different groups only (A, B, C) | **7/169 (0.041)** | 22/1954 (0.011) | 2.2, **P(≥ 7) = 0.008** |

⇒ For about 20 positions after a text divergence, and even between different groups, the decks stay close enough for a letter shared at the same place to often give the same symbol. Further on, it returns to chance.

**26.3 This rate according to the models (`divergence_models.py`).** Dedicated testbed: shared prefixes as in the eyes, then unrelated English texts; about 14,300 trials per model.

| Model | Near-coincidence rate |
|---|---|
| reinsertion + random β | 0.014 |
| reversal + random β | 0.014 |
| space (special symbol) | 0.017 |
| Lymm, 1 swap + homophones from the previous letter | 0.022 |
| Lymm, 4 swaps | 0.027 |
| Lymm, 1 swap without homophones (`small_order_test.py`, random β) | 0.044 |
| **eyes** | **0.040–0.041** |

- **Disfavoured**: reinsertion and reversal, the survivors of the zoo (§14). With 301 trials: expected 4.2, observed 12, P ≈ 0.001. The space model is too (P ≈ 0.007).
- **Favoured**: Lymm's small swaps **without homophones**. Letters modify the deck very little there.

## 27. Exact cancellation of the obstacle: β of order dividing 8 (`small_order_test.py`, `gap_profile_order.py`, 2026-10-01)

**Argument.** In the model σ_p = β∘τ_p (τ_p a small swap), the product of a text is β^n multiplied by conjugates of the τ by powers of β, which depend on the position modulo the order of β.
- If β⁸ = id, two 4-letter words separated by 4 letters (positions i and i+8, as in the 4/4/4 obstacle) are conjugated by the same powers.
- Swaps with disjoint supports commute: swapping the words then exactly cancels the deck difference.

**Test** (100 keys, testbed without homophones, k = 1 or 2 swaps per letter):

| β | k | flat | texture | fix. points | exact pattern (swap) | coinc. after div. | same-Δ agreement |
|---|---|---|---|---|---|---|---|
| order 4 | 1 | 0.05 | 0.43 | 0.40 | **0.24** | 0.041 | 0.20 |
| order 8 | 1 | 0.03 | 0.35 | 0.41 | **0.23** | 0.045 | 0.17 |
| order 8 | 2 | 0.14 | 0.81 | 0.49 | 0.01 | 0.032 | 0.06 |
| order 2 / mirror | 1–2 | ≤ 0.04 | 0.39–0.79 | ≤ 0.02 | 0.00 | 0.025–0.032 | 0.14–0.30 |
| random | 1 | 0.01 | 0.20 | 0.54 | 0.00 | 0.044 | 0.10 |

- **The cancellation works**: the exact pattern goes from 0 to 23–24% of keys. The failures come from non-disjoint swaps, and from the 4 clean reads needed between the words (about 0.4).
- Order 2: the perturbed cards return too quickly to the read positions.
- Among the 34 non-rotational natural shuffles, only reversal (order 2) has an order dividing 8. A β of order 8 would therefore be a keyed choice.
- Gap profile (`gap_profile_order.py`, 60 keys): the profiles depend mostly on the key. No link with the excess of the eyes at d = 4 (correlation of mean profiles ≈ 0). P(chi² ≤ eyes) is 0.13 for order 8 and 0.02 for a random β.
- **Joint estimate** (order 8, k = 1, no-doubles rule): about 0.1 × 0.35 × 0.41 × 0.23 ≈ 0.3%. Flatness remains the bottleneck.

**Summary of §26 and §27: the tension comes down to this.**
- **Flatness**: the trajectory of a card must depend on the text, so the letters must modify the deck a lot (or homophones are needed).
- **Exact obstacle and coincidences after divergence**: the letters must modify the deck very little. Context-based homophones reduce the coincidences (0.022) and break the obstacle.

A homophone rule depending neither on the differing text nor on the position would be the only one to reconcile the two. For example, a rule based on equalities with the last outputs: it is invariant under card relabelling, hence compatible with perfect isomorphs. This is the next lead.

## 28. Flatness and plaintext; equality-rule homophones (2026-10-01, work paused)

**28.1 Homophones chosen by equality with the last outputs (`avoid_homophone_test.py`, 100 keys).** The first slot whose card is not among the K last outputs is taken. The rule is invariant under relabelling, so isomorphs remain perfect (1.00).
- Problem: the first slot is almost always chosen, so nothing is flattened (flat from 0.00 to 0.07).
- The exact pattern of the obstacle (0.15–0.29 with β of order 8) and the coincidences after divergence (0.042–0.043) are preserved.
- **Inconclusive.**

**28.2 Flatness depends on the plaintext (`plaintext_flatness_test.py`, 100 keys).** P(chi² ≤ eyes):

| Plaintext | Lymm, random β | Lymm, β order 8 | reinsertion + β |
|---|---|---|---|
| English (testbed) | 0.03 | 0.08 | 0.56 |
| English redrawn | 0.15 | 0.24 | 0.94 |
| Finnish | 0.05 | 0.13 | 0.90 |
| uniform letters | **0.89** | **0.86** | 0.98 |

Redrawing slightly alters the structure of the repeats: the "redrawn", Finnish and uniform rows must be compared with each other. In the "small changes" models, the gap spikes come from pairs of frequent letters. **With a plaintext of flat frequencies, flatness is no longer a bottleneck.**

**28.3 Full battery with a uniform plaintext (`uniform_plaintext_test.py`, testbed with the architecture of the eyes, 100 keys, k = 1).**

| Text | β | No-doubles | flat | 0 doubles | texture | fix. points | exact pattern | div. coinc. | same Δ |
|---|---|---|---|---|---|---|---|---|---|
| English | order 8 | no | 0.07 | 0.70 | 0.43 | 0.49 | 0.29 | 0.044 | 0.18 |
| uniform | random | no | 0.33 | 0.13 | 0.20 | 0.67 | 0.01 | 0.035 | 0.09 |
| uniform | order 8 | no | 0.34 | 0.13 | 0.35 | 0.52 | 0.23 | 0.036 | 0.11 |
| English | order 8 | yes | 0.02 | 1.00 | 0.31 | 0.61 | 0.25 | 0.044 | 0.17 |
| uniform | random | yes | 0.24 | 1.00 | 0.25 | 0.65 | 0.01 | 0.034 | 0.10 |
| uniform | order 8 | yes | 0.04 | 1.00 | 0.31 | 0.42 | 0.30 | 0.037 | 0.12 |

- P(ALL) = 0 in the four cases over 100 keys.
- With β of order 8 and a uniform text, flatness falls back to 0.04 when the no-doubles rule is imposed, against 0.34 without it. This rule constrains m and seems to recreate regularities. **To be understood when resuming.**

**Where I stand (for resuming).** Best current candidate: Lymm, 1 swap per letter, keyed β of order dividing 8, without homophones.
- It explains the exact obstacle (about 25%), the coincidences after divergence (0.044 against 0.040 for the eyes), the "same Δ" test and the absence of fixed points (about 0.5).
- It stumbles on flatness with an English text (≤ 0.08). A plaintext with flat frequencies flattens it (0.34), but the no-doubles rule undoes this (0.04).

Next steps considered:
1. understand the effect of the no-doubles rule on flatness;
2. look for plausible "flat" plaintexts (numbers, large alphabet, pre-encoding);
3. compute the joint score over 1,000 keys;
4. if a model reaches a few percent, design an attack specific to the "β of order 8 + one swap per letter" model.

## 29. Resuming: the "β of order dividing 8" explanation is refuted (`nodouble_profile.py`, `order_deficit_test.py`, 2026-10-01)

**Diagnosis of §28.3.** With β of order 8 and doubles forbidden by construction, the gap profile has a dip at d = 9 and d = 17 (3 and 5 repeats on average, against about 11 elsewhere; 60 keys, uniform text). Without the rule, or with a random β, the profile is flat. Explanation: the card read returns to the same position every L steps; forbidding its re-read at the next step also forbids it at steps 1 + L, 1 + 2L, etc.

**Test on the eyes** (raw repeats, same architecture for the model; 100 keys, Lymm k = 1, no-doubles):

| L | Distances 1+L, 1+2L, 1+3L | Eyes | β of order L (mean, P(≥ eyes)) | Random β (mean, P(≥ eyes)) |
|---|---|---|---|---|
| 2 | 3, 5, 7 | 32 | 4.9–7.2, **0.00** | 34.5–37.9, 0.57–0.64 |
| 4 | 5, 9, 13 | 48 | 7.9–11.0, **0.00** | 33.3–33.9, 0.10–0.18 |
| 8 | 9, 17, 25 | 45 | 12.2–14.4, **0.00** | 30.6–33.2, 0.08–0.18 |

(The ranges cover the two plaintexts tested, uniform and English.)

⇒ **Refuted**: a β of order 2, 4 or 8 with doubles avoided by construction. The cancellation of the obstacle (§27) therefore cannot come from there.
- Caveat: if doubles were avoided otherwise (homophones changed on the fly, for example), the dip would disappear. But those homophones do not flatten the profile (§28.1).

**Back to the space model (§26).** Its two weak points came from the **testbed**, not necessarily from the model.
- Coincidences after divergence too rare (0.017): the testbed assumes unrelated texts after the divergence, hence spaces misaligned after a few words.
- Stutter: the testbed assumes random substitutions.

Yet the eyes seem **formulaic**: shared openings, repeated phrase, E4/W4/E5 near-copies. With texts of the same word structure ("THE NORTH EYE" / "THE SOUTH EYE"), the space model naturally gives the coincidences after divergence and the stutter. This is a hypothesis about the plaintext, not a result.

## 30. Attack on the "space" model and formulaic texts (`sa_space_model.py`, `formulaic_test.py`, 2026-10-01)

**30.1 Simulated annealing on (β, σ, q_space).** The starting deck is sorted without loss of generality: in "card" coordinates, D0 is absorbed into β and σ. Testbed with spaces, random β and σ, 300,000 iterations per stage. The score (Dirichlet likelihood of the read positions) only covers the first T symbols of each message.
- On short prefixes (T = 6, 10, 15), wrong keys beat the true one: -127 against -179 for T = 6.
- Over the full length, annealing plateaus at -4,529 against -3,184 for the true key, with at best 4 correct entries out of 83 (1 out of 83 at the last stage).
- ⇒ **Failure**, same diagnosis as in §9 to §16: unidentifiable on prefixes, a needle over the full length.

**30.2 Formulaic texts (feasibility, hypothesis on the plaintext).**
- **Stutter**: E5 = E4 with n words of 21..41 replaced by words of the same length. P(texture) is, for n = 1 to 4: space 0.00 / 0.00 / 0.00 / 0.61; Lymm k = 1: 0.00 / 0.16 / 0.63 / 0.72. The space model requires almost all the words of the passage to change while keeping their lengths.
- **Coincidences after divergence**, if all the messages follow the same template of which a share f of the words is replaced (aligned spaces). For f = 0.3 / 0.6 / 1.0: space 0.565 / 0.350 / 0.274; Lymm 0.571 / 0.422 / 0.301. This is far more than in the eyes (0.040).
- ⇒ In the eyes, after a divergence, the word structure does **not** stay aligned for long. The observed coincidences (0.040) lie between "unrelated texts" (0.014–0.044 depending on the model) and "aligned template" (≥ 0.27).

**Provisional summary (§26 to §30).**
- **The most consistent on the tests with no text assumption**: Lymm, 1 swap per letter, random β, without homophones. It reproduces the coincidences after divergence (0.044), the "same Δ" test, the absence of fixed points (about 0.5) and the stutter if 3 or 4 words change. It fails on flatness with an English plaintext (≤ 0.15, but 0.89 with a flat-frequency plaintext) and on the exact obstacle (0 out of 1,000).
- **The space model** reproduces the exact obstacle, but requires words of the same length in the stutter, and gives too few coincidences on unrelated texts.
- **Refuted**: β of order dividing 8 with doubles forbidden by construction (§29).
- **No attack is practicable as it stands**: annealing, beam, CP-SAT and lazy search all failed on the testbed.

## 31. "Flat-frequency plaintext" hypothesis (`flat_plaintext_test.py`, `flatten_gamma_test.py`, `flat_joint_test.py`, `obstacle_exact_rate.py`, 2026-10-01)

Model tested throughout: Lymm, 1 swap (q_p, m_p) per symbol, random β, no-doubles rule, without homophones, first symbol outside the deck. Testbed with the architecture of the eyes built on the pre-encoded stream.

**31.1 Small-alphabet pre-encodings: excluded** (100 keys).

| Pre-encoding | Alphabet | Median chi² (eyes 63) | P(flat) | Coinc. after divergence (eyes 0.040) |
|---|---|---|---|---|
| English | 26 | 97 | 0.02 | 0.054 |
| A1Z26 (A = 01…) | 10 | 499 | 0.00 | 0.136 |
| Polybius 5×5 | 5 | 726 | 0.00 | 0.167 |
| ternary (3 digits per letter) | 3 | 1,742 | 0.00 | 0.278 |
| uniform letters | 26 | 75 | 0.27 | 0.021 |

With few symbols, few positions are read: a very spiky profile and far too many coincidences. In this model, the plaintext therefore has a **large alphabet** (of the order of 20 symbols or more).

**31.2 Progressive flattening** (i.i.d. letters of frequencies ∝ p_english^γ; coincidences estimated over 10 different divergence texts).

| Text | Σp² | P(flat) | Median chi² | Coinc. (per text) | P(eyes 12/301) |
|---|---|---|---|---|---|
| real English | 0.065 | 0.04 | 103 | 0.047 (0.034–0.061) | 0.68 |
| γ = 1 | 0.065 | 0.02 | 113 | 0.043 (0.031–0.060) | 1.00 |
| γ = 0.75 | 0.056 | 0.05 | 100 | 0.036 (0.027–0.053) | 0.76 |
| γ = 0.5 | 0.048 | 0.13 | 77 | 0.030 (0.022–0.042) | 0.31 |
| γ = 0.25 | 0.042 | 0.27 | 76 | 0.031 (0.020–0.045) | 0.40 |
| γ = 0 (uniform) | 0.038 | 0.27 | 74 | 0.033 (0.021–0.045) | 0.42 |

- The coincidence rate depends mainly on the text drawn: with a single text, the estimate was misleading.
- It remains compatible with the eyes for any γ.
- Flatness goes from 0.02–0.04 to 0.27 as soon as the frequencies are clearly flatter than English (Σp² ≤ 0.048).

**31.3 Joint battery** (200 keys; stutter = n substitutions in 21..46).

| Text | n | flat | texture | fix. points | loose obstacle | exact obstacle | ALL (loose) | ALL (exact) |
|---|---|---|---|---|---|---|---|---|
| real English | 8 | 0.03 | 0.39 | 0.54 | 0.38 | 0.01 | 0.00 | 0.00 |
| real English | 12 | 0.03 | 0.98 | 0.56 | 0.35 | 0.01 | 0.00 | 0.00 |
| γ = 0.25 | 8 | 0.16 | 0.40 | 0.63 | 0.30 | 0.00 | 0.00 | 0.00 |
| γ = 0.25 | 12 | 0.17 | 0.92 | 0.58 | 0.33 | 0.01 | **0.05** | 0.01 |

Isomorphs 1.00 and no doubles everywhere.
- The stutter of the eyes corresponds, in this model, to about **12 differing letters over 26 positions**: half of the passage rewritten, which is consistent with at least 3 proven differences (§6).
- **Best joint score obtained to date: 5%** (loose obstacle).

**31.4 The exact pattern of the obstacle, measured precisely** (5,000 keys, 20 draws of the words): **0.44%** (22 out of 5,000) in English, **0.12%** (6 out of 5,000) in flattened plaintext. The 2 out of 200 of §31.3 were a stroke of luck. With the exact obstacle, the joint probability falls to about 10⁻⁴.

**Summary of §31.**
- Flatness is no longer an argument against Lymm's model, if the plaintext is clearly flatter than English while keeping a large alphabet. Plausible leads: a pre-encryption (for example polyalphabetic) or homophones. These are unverified hypotheses.
- Only one strong anomaly remains: the exact shape of the obstacle, an event of about 1 in 250 to 1 in 800 in this model. For a single trait among a dozen examined (and noticed precisely because it is striking), this is surprising, but not a refutation.

**31.5 How could the plaintext be flat? (reasoning)** A flattening must preserve perfect isomorphs and the 4/4/4 shape of the obstacle.
- Prior monoalphabetic substitution: does not change Σp², so does not flatten.
- Homophones drawn at random or used in turn: break isomorphs (§8).
- Position-dependent pre-encryption (Vigenère, etc.): breaks isomorphs at offsets that are not multiples of the period (group C has offsets of 1, 2 and 3).
- Context-dependent pre-encoding (homophones from the previous letter, autokey on the plaintext): preserves isomorphs, but a differing letter also changes the next symbol. Bursts become 5/3/5/12 instead of 4/4/4/13, and the exact pattern is observed 0 times (§24.2, models with homophones).
- ⇒ The only compatible possibility is an **intrinsically flat** plaintext: non-linguistic data, or a text already encrypted by a process with neither context nor position (hard to imagine). This is a strong hypothesis, to be kept open, no more.

## 32. Lead 2: a mechanism for the exact obstacle. The "space" model comes back on top (2026-10-01)

**32.1 Which reading of the obstacle, in Lymm's model? (`obstacle_readings_rate.py`, 5,000 keys).**

| Reading | Exact pattern | 4≠ then 4= | 13 identical, given the start |
|---|---|---|---|
| word swap | 0.24% | 0.35 | 0.007 |
| two different words | 0.14% | 0.45 | 0.003 |
| a single word (33-36 = hidden state) | 0 | 0.45 | 0 |

The bottleneck is the end of the pattern: 13 clean reads after 8 differing letters.
- With h support cards added per differing letter: P ≈ (1 − 8h/83)^13. Two letters cannot all differ by a single transposition (the product of two distinct transpositions is not one), so h ≥ 3 on average and P ≤ 0.012.
- No exact cancellation is possible without a β of small order (refuted, §29), nor without commutativity (refuted, §25).
- ⇒ The exact obstacle requires the **substituted letters to leave no deck difference**.

**32.2 "Space" model on equal assumptions (`space_joint_test.py`, 200 keys).** Stutter: 12 substituted letters in 21..41, spaces unchanged. This is the same assumption as for Lymm's model (§31.3).

| Model | 1st symbol | iso | flat | 0 doubles | texture | fix. points | exact pattern | **ALL** |
|---|---|---|---|---|---|---|---|---|
| space (random σ) | **inside** | 1.00 | 0.36 | 1.00 | 0.96 | 0.81 | 1.00 | **0.29** |
| space (random σ) | outside | 1.00 | 0.35 | 1.00 | 0.97 | 0.79 | 1.00 | 0.26 |
| Lymm k = 1 | outside | 1.00 | 0.01 | 0.85 | 0.81 | 0.56 | 0.00 | 0.00 |

**Best joint score obtained: 29%**, with the first trigram INSIDE the cipher (the openings stay identical, because an ordinary first symbol does not touch the deck). With 8 substituted letters, the texture fails (0.00): the stutter then corresponds to about 12 letters changed out of 21, spaces aligned.

**32.3 The weak point: coincidences after divergence.**
- Window +1..+20 (`space_joint_test.py`): 0.017 to 0.019 on average (0.008 to 0.030 depending on the text), against 0.040 for the eyes.
- Depending on the text, between groups P(≥ 7/169) ranges from 0.026 to 0.25, and without E1/W1 and E4/E5, P(≥ 12/301) from 0.006 to 0.20 (`coincidence_pvalues.py`). The model is moderately disfavoured, not refuted.
- Split +1..+9 / +10..+20 (`coincidence_distance_test.py`, **chosen after seeing the data**, hence only indicative):

| | +1..+9 | +10..+20 |
|---|---|---|
| Eyes, between groups | 1/50 (0.020) | 6/119 (0.050) |
| Eyes, without E1/W1 and E4/E5 | 5/105 (0.048) | 7/196 (0.036) |
| Space model | 0.026 | 0.013 |
| Lymm's model | 0.065 | 0.047 |
| Reinsertion + β | 0.018 | 0.014 |

The decks of the eyes seem to stay close for a **long time** after a divergence, which the space model does not do (a shifted space separates the decks all at once).

**32.4 Hybrid "letters = exactly β, space = β + k swaps" (`near_space_test.py`, `space_k_sweep.py`).** The exact obstacle is 1.00 in all cases; texture 0.95–0.98; fixed points 0.58–0.78.

| σ_space | P(flat), English | coinc. +10..+20 | P(eyes 6/119) | product |
|---|---|---|---|---|
| k = 8 | 0.01 | 0.047 | 0.83 | 0.008 |
| k = 16 | 0.06 | 0.030 | 0.18 | 0.011 |
| k = 24 | 0.20 | 0.018 | 0.023 | 0.005 |
| k = 40 | 0.28 | 0.015 | 0.011 | 0.003 |
| random | 0.40 | 0.013 | 0.005 | 0.002 |

There is a **real trade-off**: a strongly shuffling space flattens the profile but separates the decks quickly. The product does not exceed about 1%. With a flattened plaintext (letters ∝ p^0.25), k = 8 gives flat 0.06, coincidences 0.054 / 0.029 and ALL 0.04.

**Summary of §32 (provisional ranking, all criteria).**
1. **"Space" model** (letters = β, space = strong shuffle; first trigram inside the deck): 29% on all criteria except the coincidences, which give P ≈ 0.01–0.2 depending on the text (window chosen in advance). Overall score of the order of 0.3 to 5%.
2. **Hybrid** (space = β + 16 swaps): about 0.5%.
3. **Lymm**, 1 swap per letter: about 10⁻⁴ (exact obstacle).

⇒ Working hypothesis: **the letters do not modify the deck; only a separator symbol (the space) does.** The first trigram is then an ordinary symbol, inside the cipher. If this is right, the deck depends only on the **word lengths**. This is a possible foothold for an attack, for example through probable words, to be studied.

## 33. Designing a probable-word attack in the "space" model: first attempts (2026-10-01)

**Answer to the repository owner's question (added value or mere replication of Lymm).**
- **Taken from the community**: the GAK/XGAK framework, allomorphs, the reading of the obstacle and the stutter, the "base + a few swaps" model, the aligned symbols.
- **New, to my knowledge**, and quantified against random baselines:
  - the fixed-point test (§13);
  - the zoo of families (§14);
  - the exact probability of the obstacle (§24);
  - the "same Δ" test (§23);
  - the commutative trilemma (§25);
  - the coincidences after divergence (§26);
  - the "space" model (§26, §32);
  - the signature of small-order βs (§29);
  - the role of the plaintext in flatness (§31).
- **Limit**: no decryption.

**33.1 First step: attack with no probable word, "keyed starting deck + natural shuffles".** Assumption: the designer uses physical shuffles (β for each letter, σ for the space, taken from the 116 natural shuffles) and a starting deck D0 shuffled by a key. The sweep of §26 assumed D0 sorted or reversed; it therefore did not cover this case.
- If β and σ are known, each card follows a trajectory determined by its starting position x_c.
- Alternating algorithm (`keyed_deck_attack.py`): read-position frequencies, then Hungarian assignment of the starting positions, and so on.
- Testbed (β = rot1, σ = deal3fwd, random D0), recomputing the "space" decisions from the current deck: 0 successes over 40 starts; the version progressive in time (`keyed_deck_attack2.py`) also fails (≤ 1/83); simulated annealing on D0 (`keyed_deck_sa.py`): score 2,150 against 3,383 for the truth, at most 2/83.
- **With the true positions of the spaces (oracle)**, the algorithm converges: 83/83 in 1 random start out of 3.
- ⇒ The bottleneck is the cascade of "space" decisions: a single wrong decision derails the rest of the message.

**33.2 What a probable word would bring (`crib_length_test.py`).** A probable word mostly brings the positions of the spaces. The true decisions are given on the first T symbols of each message (6 starts per case):

| β, σ | T = 15 | 20 | 30 | 45 | 70 | 140 (all) |
|---|---|---|---|---|---|---|
| rot1, deal3fwd | 1 | 2 | 4 | 3 | 9 | **83 (2/6)** |
| outshuffle, milk | 7 | 3 | 5 | 23 | 4 | **83 (1/6)** |
| deal2fwd, rot5 | 4 | 5 | 2 | 7 | 79 | **83 (3/6)** |

(best recovery, in correct starting positions out of 83)

⇒ The word structure of **almost the whole corpus** must be known to recover the key, even with β and σ known. A short probable word (around ten letters) is not enough.

**What this implies for what follows.**
1. **Ciphertext only**: an algorithm treating the "space" decisions as hidden variables would be needed, with a beam of decision paths per message, instead of deducing them from a wrong deck. It is heavier, but it is the natural path. Otherwise, propagate from the start, where the messages share their prefixes.
2. **Probable words**: they should bear on the **structure** (word lengths) of long passages, for example an entire phrase assumed to be repeated. The phrase repeated six times in group A lends itself to this, if its word lengths can be guessed.
3. All this only covers natural β and σ. With keyed β and σ, the problem is much harder (§30).

## 34. Spaces as unknowns: beam search (`space_beam.py`, 2026-10-02)

**Method.** Space model, β and σ known (natural), unknown keyed starting deck, q_space given (validation). The assignment is lazy.
- A card already placed has a forced read and decision.
- A new card gives a two-way branch ("space", it is placed at q_space; "letter", it goes on hold).
- A held card reappearing: its read position is chosen among the positions whose start is free. Time is rewound (a single position tracked) to find its start and first read, which must differ from q_space.
- Score: sequential Dirichlet likelihood (α = 0.05).

**Validation** (testbed with spaces, β = rot1, σ = deal3fwd):

| Beam | True branch lost at step | Rank of the true branch just before | Best final hypothesis |
|---|---|---|---|
| 300 | 17 (message 0) | 77, 35 | 0/83 correct starts, 840/1063 decisions |
| 3,000 | 19 (message 0) | 745, 475 | 1/83, 839/1063 |

⇒ **Failure by combinatorial explosion.** At the start, never-read positions are all equivalent for the likelihood, and the true branch drowns among tied hypotheses: multiplying the beam by 10 only gains 2 steps. The constraints only bite once the alphabet of read positions has formed, much further on. It is the same bottleneck as in §11 (reinsertion).

**Remaining lead, specific to the eyes (untested).** In the space model, a mapping after a letter insertion is π = D0·(W β W⁻¹)·D0⁻¹, where W depends only on the word lengths before the insertion. The mappings E4→E5 and E5→W4 are observed (40 to 70 card pairs each). Both constrain the same starting deck D0, provided the word structure of the prefixes is guessed. An algebraic attack combining these mappings and word-length hypotheses would be the logical next step. It remains costly and speculative (natural β and σ assumed).

## 35. Attack through the insertion mappings: too little data (`insertion_maps.py`, 2026-10-02)

**Principle.** In the space model, if Y = X with one inserted letter, the mapping between their shifted shared blocks is π = D_i β D_i⁻¹, with D_i the deck of X at the moment of insertion.
- It depends only on the spaces located **before the word** of the insertion, since β commutes with itself.
- In deck D_i, the card π(c) is at position β(position of c). If β is a rotation ("cut one card"), the chains of π directly give fragments of the **deck order** at that moment.
- Two mappings (E4→E5 and E5→W4) give two snapshots of the same deck. They are linked by the known shuffles and the interleaved spaces.

**Step 1, key-independent test.** π is a conjugate of β, so its chains must fit in the cycles of β.
- **Eyes data** (edges trimmed by 2):
  - π1 = E4→E5 (C2, C3a, C3b, X): 34 pairs, one inconsistency, 20 chains of 2 to 6 cards, no closed cycle;
  - π2 = E5→W4 (C2): 11 pairs, 9 chains of 2 or 3 cards.
- **Result**: 114 natural shuffles out of 116 are compatible (only identity and reversal are excluded). Such short chains do not discriminate.

**Step 2, joining the two snapshots.**
- π1 covers 53 cards, π2 covers 20, and 15 are shared.
- Only 6 edges of π2 have both their cards in π1, and their positions in π1 are known only up to a chain shift.
- The hypotheses to separate (σ among 116, spaces between the two insertions, about 10⁴ patterns) represent about 20 bits. Six partial joins bring a few.
- ⇒ **Unidentifiable: abandoned.**

**Summary of the attacks on the space model (§30 and §33 to §35).**
- The model is the most consistent with the traits of the eyes (§32).
- No attack tested succeeds without knowing the word structure over almost the whole corpus:
  - annealing on keyed β and σ;
  - keyed deck with natural shuffles: alternating algorithm, progressive version, annealing, beam;
  - insertion mappings.
- What would unblock it: a **long** probable word bearing on the word structure, for example the phrase repeated six times in group A, or the openings. Or external information (a game hint) on the deck or the shuffles.

## 36. Probable-text attack: preparation, basin of attraction, natural-pair filter (2026-10-02)

**Probable text on the repeated phrase: framing.**
- In the space model, the 6 copies of the phrase are linked by already observed mappings, and bring nothing more on the shuffles. What would break the cipher is a passage whose **letters and spaces** are known: known decisions, repeated letters at the same read position, re-read cards giving equations.
- The sources propose no probable text (search for "crib", "known plaintext", "probable word").
- Guessing 50 characters blindly is hopeless. The mechanism space must be reduced first.

**36.1 Basin of attraction of the "keyed starting deck, known natural shuffles" attack.**
- Space decisions deduced mechanically from the current deck (`basin_keyed_deck.py`): even starting from an 85% correct deck, the algorithm collapses (1 to 4 correct cards at the end). A single misplaced space card derails the end of the message.
- **Robust** decisions (`keyed_deck_robust.py`), chosen per message by a beam that penalises without derailing:

| Start correct at | rot1 / deal3fwd | outshuffle / milk |
|---|---|---|
| 100% and 95% | 4/4 converge (83/83, decisions 1,063/1,063) | 4/4 |
| 85% | 4/4 | 3/4 |
| 70% | 1/4 | 1/4 |
| 50% | 0/4 | 0/4 |

⇒ With β and σ known, the complete key is recovered from a deck that is about **three quarters** correct.

**36.2 Annealing with robust decisions from a random deck (`sa_robust.py`, 100,000 iterations).** The score progresses (-4,782 → -4,472) towards a false optimum: 0/83 correct. The global coupling comes from the law of read positions (which positions serve as letters, and at what frequency). If it were known, each card would place itself independently. It is unknown at the start.

**36.3 Natural-pair filter (`natural_pair_filter.py`, in progress).** The keyed starting deck is only a relabelling of the cards and changes no statistic of the eyes. The natural pairs (β, σ) are therefore ranked by P(flat), P(fixed points) and P(0 doubles), without knowing the key. Pairs of two rotations are excluded (commutative, refuted in §25), as well as β = identity.

## 37. Block equations: a perfect but degenerate test (`block_propagation.py`, `eq_graph_info.py`, `cycle_score_sa.py`, `groupA_attack.py`, 2026-10-02)

**37.1 The consistency test (testbed, space model, β and σ known).** Two aligned positions of a shared block read the same deck position. With the space decisions of the prefixes, each aligned pair gives an exact equation x(c_Y) = F_Y⁻¹ F_X x(c_X).
- True decisions, 34 blocks: 81 cards in one component, **a single solution**: the starting deck is fixed.
- With the 12 longest blocks: 80 cards, a single solution; with the 8 longest: 78 cards, a single solution.
- One space moved per message, or random decisions: **no solution** (contradiction).

**37.2 The eyes have enough equations (`eq_graph_info.py`).** Bipartite cards–columns graph, where the columns are the positions bearing the same letter according to the alignments:
- eyes: 111 columns, 80 cards, **114 independent informative cycles** (84 without the weak block B1);
- testbed with 8 blocks: 110 cycles, a configuration where the deck was determined.

**37.3 But the search for the decisions is degenerate.**
- Score by short cycles (`cycle_score_sa.py`): annealing reaches the score of the truth (339/339) with only 622/1,063 correct decisions. The complete system then has **no** solution: short cycles do not detect the error.
- Theory: for a cycle linking X and Y, the condition depends only on the decisions located between the columns where the texts **differ**. Decisions in shared-text zones cancel out; they are fixed only by the concentration of the read positions.
- "Satisfied equations" score on group A of the testbed (`groupA_attack.py`, 312 equations, 101 groups of free decisions): the true pair (rot1, deal3fwd) reaches the maximum (297) one time in 4 (otherwise 186–190). **A wrong pair (outshuffle, milk) reaches it 3 times out of 3.** Other wrong pairs: 168–230.
- The letter partition rebuilt from a partial solution is poor: 166 of the 919 same-letter pairs recovered, 107 false equalities.

⇒ On group A alone, consistency does not separate the pairs (β, σ): too few truly informative cycles, too much freedom on the spaces.

**37.4 Natural-pair filter (`natural_pair_filter.py`, 10 draws per pair).** 5,631 pairs out of 6,583 (excluding pairs of rotations and β = identity) have P(flat) ≥ 0.2 and P(fixed points) ≥ 0.2. The statistics therefore do not reduce the list of natural shuffles.

**State of the attack on the space model.**
- There is an exact test (block equations), and the eyes have enough cycles.
- But the joint search (pair (β, σ) among about 6,500, spaces of all prefixes) has no exploitable landscape: all local methods (annealing, beam, alternating) fail or degenerate, even on the testbed with the true pair.

## 38. Probable-text attack (space model, natural shuffle pairs) (`crib_test.py`, `crib_scan.py`, 2026-10-02)

**Testing a probable text** (`crib_test.py`). A candidate text for the start of a message fixes the space/letter decisions (hence F_t for a pair (β, σ)) and the letter pattern. Two positions with the same letter read the same deck position: x(c_t2) = F_t2⁻¹ F_t1 x(c_t1). A re-read card closes cycles; the text and the pair are consistent if each component admits a seed satisfying its equations (x injective, distinct letters read at distinct positions).

Validation (testbed with spaces, natural pairs drawn at random; wrong texts = random English windows):

| Length | True text and true pair | Wrong texts consistent | Wrong pairs consistent (true text) |
|---|---|---|---|
| 25 | 2/2 | 298/400 (75%) | 196/400 (49%) |
| 50 | 6/6 | 110/1,200 (9%) | 46/1,200 (4%) |
| 75 | 6/6 | **0/1,200** | 5/1,200 (0.4%) |
| 100 | 6/6 | 0/1,200 | 5/1,200 |

**Parallel sweep** (`crib_scan.py`, numba). 660 pairs (cuts of ±1 to ±5 cards for the letters with each of the 33 non-rotational natural shuffles for the space, and the reverse).
- Validation: true text hidden among 5,000 decoys, in 16 s. The true text is found (with several neighbouring pairs: the exact pair remains ambiguous, the text does not). **No alert on the decoys.**
- Three placement modes: "chiffre" (number then text), "hors" (symbol 0 outside the cipher), "lettre" (text from symbol 0).

**Candidates.**
- Game texts (`crib_candidates.py`): common.csv (English) and wiki pages, i.e. 96,088 windows of 75 characters starting at a word start.
- The repository owner's alchemical lead (recipe, repeated lines, rubedo). The game links the Magnum Opus, the Philosopher's Stone and the **Sampo** of the Kalevala, whose style is made of **parallelisms** (lines repeated with variations), like the eyes. Public domain texts downloaded to `sources/texts` (see `SOURCES.md`):
  - Finnish Kalevala, 68,090 windows (Ä, Ö, Å kept);
  - English Kalevala (Crawford), 142,579;
  - Turba Philosophorum, 40,792;
  - Hermetic Museum vol. I (including the Golden Tract), 120,885;
  - Newton's Emerald Tablet, 1,780.
- Hint noted: the trailer's altar gives a keyword runic alphabet "BDMAGICKEFHJLNOPQRSTUVWXYZ" (Mysteries and Oddities page). A possible lead for a deck order, not exploited.

**Results** (as they came in):
- game texts, E1, "chiffre" mode: **0 alerts** over 660 × 96,088 tests.

## 39. "Known read positions" convention and beam over the plaintext (`known_positions_attack.py`, `known_positions_sa.py`, `known_positions_greedy.py`, `lm_beam.py`, `lm_beam2.py`, 2026-10-02)

**Design assumption.** The letter of rank k is read at deck position k (alphabet A-Z, digits, space; or the runic "MAGICK" order). The shuffles are natural and the starting deck is keyed. Since the read positions are known, the law that coupled everything (§36) disappears.

- **Control**: true space decisions and known positions: **a single Hungarian assignment recovers the entire deck (83/83)**. The whole problem reduces to the spaces.
- Robust decisions from a random deck (`known_positions_attack.py`): 1 to 4/83. Progressive version in time: 0 and 6/83.
- Annealing on the decisions, score = value of the optimal assignment (`known_positions_sa.py`, 20,000 iterations): best -5,962 against -3,810 for the truth (all "letter": -6,542); 1/83.
- Greedy passes in time with lookahead (`known_positions_greedy.py`): local optimum (-5,964 and -5,841), 774/1,063 correct decisions, 1 and 2/83.

**Beam over the plaintext** (`lm_beam.py`, `lm_beam2.py`). With known positions, the read position gives the **letter**. The plaintext is therefore sought letter by letter, guided by a language model (character trigrams):
- card already placed: the letter is imposed; it must belong to the alphabet and is scored by the language model;
- new card: the 36 letters are tried.

Testbed with spaces, pieces starting at a word start, β = rot1, σ = deal3fwd:

| Variant | Beam | True branch lost at step (rank) | End |
|---|---|---|---|
| messages one by one | 2,000 / 20,000 | — | everything dies around the 45th–60th symbol |
| messages in parallel (step = time × message) | 20,000 | 28 (rank 25,160) | everything dies at step 123 |
| same | 100,000 | 31 (rank 116,322) | everything dies at step 123 |

- Defect fixed: at symbol 0 (number), the 9! equivalent digit permutations flooded the beam; the card is no longer placed at this step.
- **Finding**: multiplying the beam by 5 only gains 3 steps. The constraints (re-read cards) only bite around step 120 (about 13 symbols per message), and the true branch drowns before that among plausible English texts. **Failure by exponential growth**, even under this favourable convention.
- **Final summary of the sweeps (2026-10-02, overnight, `crib_queue_log.txt`): 0 alerts everywhere.** 660 natural pairs; targets E1, W2 and E4; modes "chiffre" and "hors" (and "lettre" for the game texts).

| Source | Windows | Target × mode combinations | Alerts |
|---|---|---|---|
| game texts | 96,088 | 9 | 0 |
| Finnish Kalevala | 68,090 | 6 | 0 |
| English Kalevala (Crawford) | 142,579 | 6 | 0 |
| Hermetic Museum (Golden Tract included) | 120,885 | 6 | 0 |
| Turba Philosophorum | 40,792 | 6 | 0 |
| Emerald Tablet (Newton) | 1,780 | 6 | 0 |

⇒ None of these texts opens E1, W2 or E4 word for word under the space model with a natural pair from the list.
- **Not excluded**: a paraphrased text or one starting elsewhere than at a word start; a pair outside the list (keyed shuffles, or untested natural pairs); another cipher model.
- **Extension to the 9 messages (night of 2026-10-02, `crib_queue_log.txt`): 74 sweeps, 0 alerts.** Game texts, Finnish Kalevala, English Kalevala and Hermetic Museum, on E1, W1, E2, W2, E3, W3, E4, W4 and E5, modes "chiffre" and "hors" (plus "lettre" on W2 and E4 for game texts). Turba and Newton: E1, W2 and E4 only.

## 40. Simulation-based inference (ABC): which model, which text? (`abc_stats.py`, `abc_simulate.py`, `abc_posterior.py`, 2026-10-02)

**Method** (requested by the repository owner: probabilistic tests rather than random words).
- 15,901 simulations on the testbed with spaces. Each draws uniformly a family (Lymm 1, 2 or 4 swaps; space random σ, β+16 or β+40 swaps; reinsertion + β), a plaintext (English, or flattened p^0.25 with 18% spaces), n ∈ {6, 9, 12, 15} letters changed in the stutter (positions 21..46, spaces kept), a testbed text and a key.
- 11 summary statistics: gap chi², doubles, repeats at d = 2 and 4, IoC, stutter (identical share, runs), fixed points after insertion, obstacle (identical share, exact pattern), coincidences after divergence.
- ABC rejection: Euclidean distance of standardised statistics (interquartile range), keeping the ε closest to the eyes.
- A first pass (`abc_sims_v1.tsv`) had two defects, fixed: rounding of the stored statistics, and too narrow a stutter window (21..41, n ≤ 12).

**Posterior probabilities** (uniform prior: 0.14 per family):

| Hypothesis | ε = 0.02 (318 retained) | ε = 0.005 (79 retained) |
|---|---|---|
| space, σ = β + 16 swaps | 0.36 | 0.32 |
| space, σ = β + 40 swaps | 0.32 | 0.38 |
| space, random σ | 0.27 | 0.27 |
| **total space model** | **0.95** | **0.97** |
| Lymm 1 / 2 / 4 swaps | 0.03 / 0.03 / 0.00 | 0.01 / 0.03 / 0.00 |
| reinsertion + β | 0.00 | 0.00 |
| English / flattened text | 0.53 / 0.47 | 0.54 / 0.46 |
| n = 6 / 9 / 12 / 15 | 0.21 / 0.23 / 0.26 / 0.30 | 0.18 / 0.23 / 0.29 / 0.30 |

**Predictive check**: share of a family's simulations at least as extreme as the eyes, two-sided.
- The **space models reproduce all the statistics**; the weakest are rep_d2 (0.12 to 0.17), the IoC (0.05 for random σ) and the coincidences after divergence (0.16 for random σ, 0.35 for β+40, 0.77 for β+16).
- Lymm fails on the obstacle (pattern 0.00 to 0.01) and the doubles (0.08 to 0.10; no no-doubles rule here).
- Reinsertion fails on the obstacle, the coincidences (0.01) and the stutter.

**Reading.**
- With all the statistics at once, the model "the letters do not change the deck, only the space does" is very clearly preferred (factor of about 20 against Lymm in this model space). The coincidences favour a **moderate** space shuffle (β + 16 swaps).
- The plaintext (English or flattened) is **not separated** by these statistics.
- The stutter slightly favours many changed letters (about 15 out of 26).

**Caveats.**
- The result holds only for the simulated families, and relies largely on the obstacle (the exact pattern is deterministic in the space model).
- The space models have the no-doubles rule, Lymm's does not.
- The testbed fixes the architecture: positions of the blocks and edits.

## 41. Attack on the space model with a moderate space shuffle σ = τ_k ∘ β (`moderate_space_attack.py`, `moderate_space_curriculum.py`, `abc_small_k.py`, `eyes_near_beta_scan.py`, `same_delta_space_k.py`, 2026-10-02)

Request of the repository owner: attack the space model with a moderate space shuffle (§40 favours σ = β + 16 swaps). Idea: if σ is close to β, a wrong "space" decision moves only 2k positions. The cascade of decisions, the bottleneck of §33, might then weaken.

**41.1 Testbed, known natural β, keyed D0, random starts.** Letter accuracy is measured, invariant under relabelling (each read position receives its majority symbol; truth 1.00). This measure replaces "correct starting positions", which underestimates success at k = 0: with σ = β, any D0 conjugated by an element commuting with β is equivalent.

| β | k | baseline (random deck) | Direct EM (σ known) | progressive in time (3 starts) |
|---|---|---|---|---|
| outshuffle | 0 | 0.35 | **1.00** | 1.00 / 1.00 / 1.00 |
| outshuffle | 1 | 0.33 | **0.87** | 0.84 / 0.86 / 0.89 |
| outshuffle | 2 | 0.32 | 0.62 | 0.44 / 0.40 / 0.45 |
| outshuffle | 4 | 0.29 | 0.28 | 0.29 / 0.27 / 0.28 |
| outshuffle | 8 | 0.29 | 0.24 | ≤ 0.25 |
| outshuffle | 16 | 0.28 | 0.26 | ≤ 0.27 |
| deal3fwd | 0 | 0.35 | **1.00** | 1.00 / 1.00 / 1.00 |
| deal3fwd | 1 | 0.36 | **0.90** | 0.88–0.89 |
| deal3fwd | 2 | 0.30 | 0.56 | 0.57–0.63 |
| deal3fwd | 4 | 0.30 | 0.33 | 0.28–0.46 |
| deal3fwd | 8 | 0.28 | 0.33 | 0.32–0.37 |
| deal3fwd | 16 | 0.29 | 0.27 | 0.25–0.27 |

Robust decisions (`keyed_deck_robust.robust_em`) from a random start also fail for k ≥ 2 (≤ 6/83 correct positions, `moderate_space_attack.py`). ⇒ **The attack only works for k ≤ 1 (partially k = 2)**, even with β and σ known. From k = 4, the failure of §33 returns.

**41.2 Do the eyes admit k ≤ 2? ABC (`abc_simulate.py` extended to the space_1, 2, 4, 8 families; `abc_small_k.py`).** 19,900 simulations, of which 10,809 of the space model. Posterior with equal prior between the k values:

| ε | all texts | English | flattened |
|---|---|---|---|
| 0.02 | k=1 0.05; k=2 0.05; k=4 0.13; k=8 0.20; **k=16 0.23**; k=40 0.21; random 0.14 | P(k ≤ 2) = 0.06 | P(k ≤ 2) = 0.13 |
| 0.005 | P(k ≤ 2) = 0.16; k=16 0.26 | 0.09 | 0.20 |

- Predictive check: for k = 1 and 2, the gap chi² is not reproduced (0.00–0.02), because the profile is not flat enough. All other statistics pass.
- All families combined (ε = 0.02): space_16 0.29, space_40 0.25, random 0.24, space_8 0.11, space_4 0.05, space_1 0.03, space_2 0.02, Lymm 1 0.02, Lymm 2 0.01.
- ⇒ k ≤ 2 is disfavoured, but not excluded by the ABC.

**41.3 The attack on the eyes in this regime (`eyes_near_beta_scan.py`).** Approximation σ := β, with keyed D0. Only the **cycle type** of β then matters (two conjugate βs are equivalent). The 115 natural shuffles give 11 types. Measure: entropy H of the read positions (bits).
- Calibration (testbed, β = deal3fwd, attack with σ := β):
  - k = 0: H = 4.10, letters 1.00;
  - k = 1: H = 4.32, letters 0.94;
  - k = 2: H = 5.17, letters 0.76.
- Controls (space model k = 16, random β): best type between 5.71 and 5.84.
- **Eyes**: best type rot1 (83-cycle), H = **5.79**; all types between 5.79 and 5.88 (reverse 6.19). This is the level of the control.
- ⇒ No natural-type β with k ≤ 2. This does not cover a keyed β of arbitrary type, hence 41.4.

**41.4 "Same Δ" test (`same_delta_space_k.py`, 30 keys, real blocks of the testbed with spaces).** This test does not depend on β. Eyes: 2 agreements out of 36 (§23).

| k | mean agreement rate (min) | P(≤ 2/36) | keys with rate ≤ 0.10 |
|---|---|---|---|
| 0 | 1.000 (1.000) | 0.000 | 0.00 |
| 1 | 0.768 (0.545) | 0.000 | 0.00 |
| 2 | 0.541 (0.323) | 0.000 | 0.00 |
| 4 | 0.343 (0.156) | 0.005 | 0.00 |
| 8 | 0.238 (0.086) | 0.089 | 0.10 |
| 16 | 0.049 (0.000) | 0.717 | 0.90 |
| random | 0.014 (0.000) | 0.975 | 1.00 |

⇒ **Refuted, whatever β: a space that differs from β by only k ≤ 4 swaps** (P ≤ 0.005; test predefined in §23, no a posteriori choice). k = 8 is borderline (0.09); k ≥ 16 is compatible.

**Summary of §41.**
- The only regime where the "keyed deck" attack works without a probable word (k ≤ 2) is **refuted** by the "same Δ" test.
- In the compatible regime (k ≥ 8, favourite k ≈ 16), the attack fails even with β and σ known.
- A moderate space shuffle therefore opens no breach: the bottleneck remains the discovery of the spaces (§33, §34, §37).
- With k ≈ 16, σ is moreover unknown even if β is natural (16 swaps to find), which makes the attack harder than with the natural pairs of §38.
- Remaining routes:
  - long probable text;
  - an algorithm treating the spaces as hidden variables without exploding (§34);
  - external information (positions of the spaces).

## 42. Exact solver on the space model, and local filter of the read conventions (`cpsat_space_attack.py`, `known_q_local_filter.py`, 2026-10-02)

Request of the repository owner: "continue with what seems most promising". Under the "known read positions" convention (§39), with known natural (β, σ), the only unknowns are the starting deck (a permutation) and one space/letter decision per symbol. This problem is handed to an exact solver, since all local searches have failed.

**42.1 CP-SAT (`cpsat_space_attack.py`, testbed with spaces, β = rot1, σ = deal3fwd, 16 cores).**
- Compact formulation:
  - messages merged into a prefix tree;
  - one position variable per (node, card re-read further on), linked by a table of 166 tuples according to the decision;
  - read: space ⇔ position = q_space, otherwise position ∈ Q;
  - options: equalities of the shared text blocks (read position and decision equal at aligned positions), words of at most 14 letters, "decide the spaces first" strategy.

| L (symbols per message) | Constraints | Result | Accuracy |
|---|---|---|---|
| 15 | — | solution in 20 s | **wrong**: 1/48 starts, 102/135 decisions |
| 25 | — | solution in 37 s | wrong: 2/66, 174/225 |
| 25 | + 140 block equalities | solution in 49 s | wrong: 1/66, 150/225 |
| 45 | — | no solution in 1,261 s | — |
| 45 | + 261 block equalities | none in 345 s | — |
| 45 | + blocks, words ≤ 14, strategy | none in 614 s | — |

⇒ **Same dead end as in §16.** At short prefixes, the problem is not identifiable (wrong solutions exist, even with the blocks). As soon as it could become so, the solver no longer finds anything.

Rough information budget:
- each letter read brings about log2(83/36) ≈ 1.2 bits;
- each unknown decision costs about 0.7;
- the deck costs 414 bits;
- identifiability therefore demands almost the whole corpus, around 100 symbols per message.

For the beam over the plaintext (§39), the estimate is the same: before re-reads constrain more than the language model, about 2^26 (word model) to 2^50 (trigrams) hypotheses would have to be kept. The beam is therefore not a realistic route either.

**42.2 Local filter of the conventions (`known_q_local_filter.py`).** New, to my knowledge.
- **Principle.**
  - In the space model, the card read at t+d equals the one read at t iff S_{x_t}…S_{x_{t+d-1}}[q_{x_{t+d}}] = q_{x_t}.
  - This depends only on the (d+1)-gram of the plaintext: the expected number of repeats at distance d is computed exactly from n-gram frequencies, with no key or simulation.
  - The filter of §37.4 drew q at random; here q follows a convention.
- **Control**: the analytic λ follows the counts simulated on the testbed to within about 20%, the gap coming from the texts (5 pairs, `validate()`).
- **Eyes, without symbol 0**: 0 doubles out of 1,018, 5 repeats at d = 2 out of 1,009, 9 at d = 3 out of 1,000.
- **Combinations tested**: 3 alphabets (A-Z 1-9 _, _ A-Z 1-9, runic order BDMAGICK… 1-9 _) × 2 orientations (k, 82 − k) × 6,468 pairs, i.e. 38,808. English testbed text.
- **Results**:
  - expected doubles: median 6.8;
  - survivors with P(Poisson ≤ eyes) ≥ 0.05 for d = 1, 2 and 3: **3,814 out of 38,808 (10%)**;
  - survivors at P ≥ 0.01: 7,320;
  - survivors of the doubles test alone: 11,803.
  - Complete list: `known_q_local_filter_out.tsv`.
- **Reading**: the "known positions" convention with natural shuffles is not excluded wholesale, but 90% of the combinations are, essentially through the absence of doubles. The test only holds for an English plaintext.

**Summary of §42.** The two exact (CP-SAT) or exhaustive (beam over the plaintext) attacks hit the same wall: the constraints only become strong with almost the whole corpus, and the search space explodes before that. The local filter brings a cheap tool for pruning families of conventions, without breaking the cipher.

## 43. Letter-class model: generalising the space model (`class_model.py`, `abc_simulate.py`, `abc_posterior.py`, 2026-10-02)

Request of the repository owner: widen the model. The space model is the case "one letter class + the space". It is generalised: the symbols are divided into classes, each class applies its own shuffle, and the first symbol is inside the deck.
- Shuffles: β for the largest letter class; β + m swaps (or a random shuffle) for the other classes; β + 16 for the space.
- Partitions:
  - **vc**: vowels AEIOUY / consonants and digits;
  - **r2, r3, r4**: 2, 3 or 4 random classes;
  - **chaque** ("each"): one class per symbol, i.e. Lymm's model, but with no-doubles and first symbol inside the deck;
  - **un** ("one"): a single letter class, a control equal to the space model β + 16.
- The no-doubles rule is generalised to all classes: no bigram (x, y) satisfies S_class(x)[q_y] = q_x. It succeeds for 20 keys out of 20 in each partition.

**Simulations.** Same ABC method as in §40, same testbed, same 11 statistics. About 21,600 simulations are added (1,270 to 2,060 per family), i.e. 41,900 in total with the families of §40–41. The r3-random family has only 2 simulations (trial); it is ignored. As the batches do not all have the same families, the posterior probabilities are given **with an equal prior between families**.

| Family | ε = 0.02 | ε = 0.005 | exact obstacle (predictive check) | other failures |
|---|---|---|---|---|
| classes "un" (= space β+16, control) | 0.153 | 0.169 | 1.00 | — |
| space β+16 / β+40 / random / β+8 | 0.14 / 0.14 / 0.13 / 0.12 | 0.12 / 0.18 / 0.14 / 0.15 | 1.00 | — |
| **vc, vowels = β + 4** | **0.070** | **0.074** | 0.23 | — |
| r2, β + 4 | 0.032 | 0.020 | 0.10 | — |
| vc, β + 16 | 0.026 | 0.024 | 0.19 | coincidences 0.11 |
| chaque, 1 swap (Lymm + no-doubles) | 0.013 | 0.004 | **0.01** | — |
| Lymm 1 / 2 (§40) | 0.012 / 0.009 | 0.010 / 0.007 | 0.00–0.01 | doubles |
| r4, β + 4 | 0.009 | 0.000 | 0.00 | — |
| chaque, 2 swaps | 0.008 | 0.000 | 0.00 | coincidences 0.06 |
| r2, β + 16 | 0.006 | 0.000 | 0.06 | IoC 0.06 |
| r3, β + 16 | 0.002 | 0.000 | 0.02 | IoC 0.03 |
| r4 β+16, r2/r4/vc random, chaque 4 swaps | 0.000 | 0.000 | 0.00–0.23 | stutter, coincidences, IoC |

**Reading.**
- The "un" control recovers the space model (0.15–0.17 against 0.12–0.18): the implementation is consistent.
- **Strongly differing letter classes are excluded**, whatever the partition. They break the exact obstacle, which requires the two swapped words to have the same class sequence, as well as the stutter and the coincidences.
- **Nearly identical classes** (β + 4 swaps) remain possible but 2 to 4 times less probable than the space model. Especially the vowels/consonants partition (0.07), which amounts almost to the space model.
- **Caveat of §40 lifted**: Lymm's model equipped with no-doubles and first symbol inside the deck ("chaque, 1 swap") still fails on the exact obstacle (0.01). Its lag did not come from the absence of a no-doubles rule.
- ⇒ The working hypothesis comes out strengthened: **"the letters do not (or barely) modify the deck; only the space does"**. The compatible variants all reduce to the space model, up to a few swaps.

**Caveats.**
- The testbed's obstacle is a swap of two English 4-letter words taken at random. If the eyes swap words chosen on purpose (same vowel/consonant scheme, for example), the class models would be less penalised.
- Only a few partitions were tested; those of the form "classes by frequency" or "by position in the word" were not simulated.

## 44. "Known positions" convention + letter frequencies: a short probable text would suffice (`known_positions_unigram.py`, `known_positions_sa_x.py`, `crib_length_known_q.py`, `opening_crib_solver.py`, 2026-10-02)

Request of the repository owner: "continue with what seems most promising". Under the convention of §39 (the letter of rank k is read at position k), the read position **is** the letter. Yet the attack of §39 scored the reads uniformly over the 36 positions: it ignored the language. According to the information budget of §42, letter frequencies bring about 1 bit per symbol.

**44.1 EM with English frequencies, random starts (`known_positions_unigram.py`, testbed, 10 starts).**

| β, σ | Score of the truth | Best score found | Correct positions |
|---|---|---|---|
| rot1, deal3fwd | −3,102 | −6,656 | 0–4/83 |
| outshuffle, milk | −3,102 | −6,974 | 1–5/83 |
| deal2fwd, rot5 | −3,102 | −6,512 | 0–2/83 |

⇒ The truth is a **very sharp** optimum: the problem is identifiable, and the bottleneck is the **search**. Annealing on the starting deck, progressive in time (`known_positions_sa_x.py`, 3,000 iterations per stage), fails too (0–3/83). On short openings, any deck explains the data, and the search freezes there.

**44.2 Length of probable text needed (`crib_length_known_q.py`).** The true plaintext (letters and spaces) of the first T symbols is given. The cards read in this passage then have a known start; EM on the rest (best of 3 starts).

| Probable text | T = 10 | 15 | 20 | 30 | 45 |
|---|---|---|---|---|---|
| E1 alone (outshuffle/milk) | 13/83 | 17 | 20 | 33 | **83/83, letters 1.00** |
| E1 alone (rot1/deal3fwd) | 13 | 15 | 18 | 27 | **83/83** |
| E1 + W2 + E4 (outshuffle/milk) | 27 | **83/83** | 83 | 83 | 83 |
| E1 + W2 + E4 (rot1/deal3fwd) | 25 | **83/83** | 83 | 83 | 83 |

⇒ Under this convention, **15 symbols at the start of each of the three groups** (45 characters in all), or 45 symbols at the start of a single message, are enough to decrypt **everything**. Without a convention, almost the whole corpus was needed (§33.2).

**44.3 The `opening_crib_solver.py` tool.**
- **Input**: guessed openings, for example `E1=… W2=… E4=…`.
- **For each combination** (convention, β, σ) surviving §42:
  - fixes the cards read in these openings;
  - immediately rejects inconsistent combinations (same card with two starts, or the reverse);
  - runs EM on the rest and ranks the combinations by score per symbol.
- **Control on the testbed**: the true combination gives −2.92 per symbol and the entire text. The 30 wrong combinations drawn at random are **all inconsistent at once**.
- **Eyes, dummy guess** ("1THE_", 40 combinations): 25 are consistent (too short to filter), and all have a failure score (≈ −6). The mechanics are validated.
- Structure of the openings of the eyes (alignments of §6):
  - E1/W1/E2 share 21 symbols after the first trigram;
  - E4/W4/E5 share 20;
  - W2/E3/W3 share 5;
  - E3 and E4 share 9 symbols.

**What this means.**
- **Chain of hypotheses**:
  - space model;
  - natural shuffles from the list;
  - "letter of rank k at position k" convention (3 alphabets × 2 directions);
  - English plaintext.
- **Consequence if it is right**: guessing about fifteen characters at the start of each group breaks the cipher, and the tool checks a guess in a few seconds per combination.
- **Limit**: guessing these openings blindly remains out of reach (§39, §42). It is a job for human guesses (community readings, game texts, opening formulas).
- **Nothing is decrypted.**

## 45. Which read conventions fit the eyes? ABC filter of the combinations (`convention_abc_filter.py`, `convention_abc_summary.py`, `convention_top_detail.py`, 2026-10-02)

Request of the repository owner: "continue with what seems most promising". Before searching for guessed openings (§44), the hypotheses are reduced. Among the 3,814 combinations (read convention, β, σ) surviving the local filter of §42, which ones reproduce **all** the statistics of the eyes?

**Facts from the data, useful for probable texts.**
- The first 9 trigrams are all distinct (50, 80, 36, 76, 63, 34, 27, 77, 33): this is compatible with a message number read in the deck.
- The 9 messages then share positions 1–2 (66, 5).
- W2, E3, W3, E4, W4 and E5 share positions 1–5 (66 5 49 75 54).
- E3, E4, W4 and E5 share positions 1–9.
- E1, W1 and E2 share positions 1–21 approximately.

**Method.**
- For each combination, corpora are simulated: testbed with spaces, English text, stutter with 6–15 letters as in §40, read positions fixed by the convention.
- The 11 statistics and the standardised distance to the eyes are computed (scale of §40).
- Acceptance rate: share of simulations at distance ≤ 1.73, the threshold ε = 0.02 of §40.
- Baseline: generic space model (random q, English), with rates of 0.051 (β + 16), 0.046 (β + 40 and random σ) and 0.026 (β + 8).

**Results.**
- **Pass 1** (R = 10, 3,814 combinations): mean rate 0.090, median 0; 60% of the combinations at 0; 514 at ≥ 0.3.
- **Pass 2** (R = 60, the best 514): mean rate 0.29; **241 combinations ≥ 0.3**, 110 ≥ 0.4, the best at 0.6–0.7. Best:
  - MAGICK/82−k, β = rot24, σ = deal3fwd_inv;
  - _AZ19/k, rot24 / deal5fwd_inv;
  - _AZ19/k, rot23 / inshuffle_inv;
  - _AZ19/82−k, deal5rev_inv / reverse.
- The βs are mostly rotations (rot20–rot29, rot5x–rot6x) and "deals". All 6 conventions are represented (30 to 49 each).
- **What makes the difference** (`convention_top_detail.py`, best 4 combinations × 100 simulations, against generic space_16):

| Statistic | Eyes | Generic: median (contribution to distance²) | Best combinations: median (contribution) |
|---|---|---|---|
| gap-spike chi² | 63.2 | 100 (3.14) | **69 (0.24)** |
| repeats at d = 2 | 5 | 17 (2.36) | **5.5 (0.11)** |
| repeats at d = 4 | 26 | 13 (2.84) | **21 (0.79)** |
| IoC | 1.072 | 1.046 (6.77) | 1.045 (1.25) |
| coincidences after divergence | 0.040 | 0.038 (0.14) | 0.027 (0.17) |
| acceptance | | 0.051 | **0.58** |

**Reading.**
- Some "convention + natural shuffles" combinations jointly reproduce three traits of the eyes that the generic model reproduces poorly:
  - a not very spiky gap profile;
  - **few** repeats at d = 2;
  - **many** at d = 4, the excess of §5.
- Distance 4 **was not used by the local filter** (d = 1, 2 and 3), and these combinations still partly reproduce this excess. This is a hint, not a proof.
- **But selection and multiple testing**: 38,808 variants were examined. At the scale of the entire "convention" family, the mean rate is about 0.090 × 3,814 / 38,808 ≈ 0.009, plus what the combinations discarded in §42, not simulated, would give. This is about 5 times **less** than the generic model. The family is therefore not favoured as a whole.
- **If** the convention is right, the right combination is very probably among the 241. Within these two families alone, the posterior share of these 241 combinations is of the order of 5%.
- The chi² and distance 2 partly overlap with the local filter (d = 2, 3); only distance 4 is truly independent.

**Tool.** `opening_crib_solver.py` now tests these 241 combinations by default, best first (option "tous": the 3,814).

## 46. The message numbers in the starting deck: a test independent of the shuffles (`first_trigram_window_scan.py`, 2026-10-02)

Request of the repository owner: "continue with what seems most promising".

**Idea.** Under a "letter of rank k at position k" convention (§39), the first symbol of each message (its number) is read **directly** in the starting deck D0, at the position of its digit. The digits are consecutive in every alphabet of the convention. The first 9 trigrams of the eyes, all distinct (50, 80, 36, 76, 63, 34, 27, 77, 33), must therefore occupy **9 consecutive positions** of D0, in any order.
- This test depends **neither on β, nor σ, nor the text**. It holds for any deck cipher whose first symbol is inside the deck.
- For a random deck: P = 83 / C(83, 9) ≈ 2.5·10⁻¹⁰ (circular arc of 9 positions).
- Variant: the first read happens after a natural shuffle S (D0∘S). Identity, reversal and rotations send an arc to an arc, which leaves 33 independent variants.
- Each deck is taken as D0 = P (position → card) or as its inverse.
- Controls: a deck built to pass is detected; 2,000 random decks × 234 variants give no false alert.

**Decks tested (those of §12, never tested under this model).**

| Source | Decks | Alerts | Expected by chance |
|---|---|---|---|
| Keyword decks (game, wiki, community, §12.2) | 145,382 | **0** | 0.002 |
| Noita generator, seeds 0 to 5,000,000, direct or after one Next(), 3 shuffles (§12.3) | 30,000,000 | **0** | 0.5 |
| SetRandomSeed(x, y), x, y ∈ [−100, 100], 30 special world seeds, 3 shuffles | 3,636,090 | **0** | 0.06 |

**Reading.**
- If the first trigram is a number read directly at consecutive positions, none of these generated decks is the starting deck, with or without a natural shuffle before the first read.
- This excludes the scenario "the developer shuffled the deck with the game's generator and a simple seed", or "ordered it by a game keyword", **under this convention**.
- Not excluded:
  - non-consecutive numbers or numbers read after other operations;
  - a first symbol that is not a number;
  - other generators or seeds.
- Gain for a future attack: under the convention, 9 cards of D0 are known up to order in a window of 9 positions. `opening_crib_solver.py` already fixes them if the guessed text starts with the digit.

## 47. "Intelligent" brute force on the message openings (`opening_search.py`, `opening_pipeline.py`, `opening_blind_calib.py`, 2026-10-11)

Request of the repository owner: "start implementing intelligent brute force if feasible". Setting: the chain of hypotheses of §44 (space model, natural pair, read convention, English text). It is added that the first symbol is the message number, read in the digit zone (§46).

**Method (`opening_search.py`).**
- **Beam over the plaintext of the openings**, node by node of the tree of ciphertext prefixes. The same ciphertext prefix implies the same plaintext. In the eyes:
  - the 9 messages share positions 1–2;
  - E1/W1/E2 share 1–24;
  - W2/E3/W3/E4/W4/E5 share 1–5;
  - E3 and E4/W4/E5 share 1–9;
  - E4/W4/E5 share 1–20.
- **Language model**: word dictionary (the space is allowed only at word end), word unigrams corrected by bigrams. Out-of-dictionary words are allowed, with a penalty (p = 0.03) and a character bigram model.
- **Exact constraints**:
  - each card read receives a start y = G_t⁻¹(q_symbol);
  - a card already placed imposes its symbol;
  - two cards cannot have the same start;
  - the cards of the numbers have their start in the digit zone, the others outside this zone.
- **Verification (`opening_pipeline.py`)**: the best 30 hypotheses each give 15 symbols of E1, W2 and E4. The EM of §44 completes them over the whole corpus, then a free EM refines from the deck found. A success gives a score of about −2.9 per symbol, a failure about −6.
- **"Whole words" testbed** (`wordy_plaintexts`): the pieces of the ordinary testbed are glued together in the middle of words, which no dictionary accepts. This testbed has the opening structure of the eyes, with whole words.

**Measurements.**
- **Free reads** (`prefix_tree`, depth-first order): on the eyes, the first 24 nodes re-read only 3 cards already seen. Afterwards, about one read in two is imposed. A greedy order favouring re-reads changes almost nothing (4 re-reads over the first 24).
- **Reading**: about 20 to 25 "free" symbols precede any constraint. With about 2 bits per character, that is of the order of 2⁴⁰ to 2⁵⁰ hypotheses per combination.
- **Beam alone, dictionary drawn from the same book as the testbed, no out-of-dictionary words**: true branch lost at steps 13–24 (beam 20,000 or 200,000). Word bigrams do not help. Restricting the search to E1/W2/E4 does worse (fewer constraints).
- **Guessed nodes** (true text imposed on the first KF nodes):
  - with KF = 20, the beam keeps the truth until the end;
  - on the eyes, these 20 nodes are positions 1 to 8 of the openings of E1, W2, W3 and E3/E4.

**Calibration**, with a dictionary drawn from OTHER texts (English Kalevala, Hermetic Museum, Turba), out-of-dictionary words allowed, natural pairs and texts drawn at random:

| Beam | Guessed symbols | Texts fully decrypted |
|---|---|---|
| 150,000 | 0 | 0 / 6 |
| 300,000 | 0 | **1 / 12** |
| 300,000 | 20 nodes | **8 / 12** |
| 500,000 | 20 / 15 / 10 / 0 nodes (2 cases) | 2/2, 1/2, 1/2, 1/2 |

A wrong shuffle pair makes the beam die in less than a second as soon as symbols are guessed: the elimination test is very sharp. The remaining weak point is out-of-dictionary words (proper nouns) in the free zone.

**Eyes, blind brute force.**
- Parameters: 241 combinations of §45, beam 300,000, English dictionary (Pride and Prejudice, English Kalevala, Hermetic Museum, Turba) with out-of-dictionary words allowed.
- Result: **the 241 beams die** (median 38 s per combination, 67 s at most). No compatible message opening was found.
- **This is not a refutation.** On the testbed, blind brute force only succeeds in about 1 case out of 12, even when all the hypotheses are true. This negative result therefore barely shifts the probability of the chain of hypotheses.

**Complexity (for the repository owner).**
- Pure brute force: 83! ≈ 10¹²⁴ starting decks, or 27⁴⁵ ≈ 10⁶⁴ text openings. Out of reach of any machine.
- "Intelligent" brute force, under the chain of hypotheses:
  - 241 combinations;
  - 20 to 25 free symbols, i.e. 2⁴⁰ to 2⁵⁰ hypotheses (full exploration impossible);
  - a beam of about 1 minute per combination, but missing the truth about 9 times out of 10 when blind;
  - with about 20 guessed symbols: success about 2 times out of 3 on the testbed.

**Usage.** A human guess, even partial, is tested like this:
`python opening_pipeline.py yeux E1=… W2=… W3=… E4=…`
The texts start at position 1, with "_" for the space. All combinations are tested and the best is indicated.

**47 bis. Results of the night of 2026-10-12 (`run_overnight_openings.py`, log `run_overnight_openings_log.txt`).**
- **Calibration with a beam of 600,000** (8 test texts, dictionary from other texts): **0 / 8** decrypted. The true branch is lost at steps 9 to 25.
  - Blind summary across all widths: 1 success out of 26 cases (0/6 at 150,000, 1/12 at 300,000, 0/8 at 600,000).
  - **Doubling the beam is useless**: the truth leaves the ranking long before the width matters.
- **Eyes, best 241 combinations, beam 600,000** (02:41 → 05:28): **all die**. The beam dies between steps 24 and 44 (median 34), i.e. just when re-reads begin to constrain (around the 24th node).
- **Eyes, other survivors of §42, beam 300,000** (launched at 05:28, **still running** at the time of the reading): 989 combinations out of 3,573 processed.
  - 988 die (steps 10 to 44, median 34).
  - Only 1 finishes: AZ19_/k, β = rot20, σ = deal6fwd_inv, score **−6.11**. This is the level of a failure; the text makes no sense ("BE_A_FOR_A_HXMA…").
- **Reading**:
  - no alert;
  - the step of death does not distinguish any combination;
  - blind brute force has only about a 4% chance of finding the truth even if all the hypotheses are right, so this silence refutes nothing;
  - the only effective route remains a human guess of about 20 symbols (8 successes out of 12).
- **Update of 2026-10-13**: after resuming and pausing again, step 3 covers **3,331 combinations out of 3,573**, still **with no alert**.
  - Only two beams go to the end, both at a failure score: AZ19_/k rot20/deal6fwd_inv −6.11; _AZ19/k deal3rev_inv/rot39 −6.14 ("REPEATED_ITLQZE…", meaningless).
  - 242 combinations remain. To resume: `python -u opening_pipeline.py yeux tous 300000 30 1000000 0 1`.
- **End of step 3 (2026-10-14)**: the **3,573** other survivors of §42 are processed (beam 300,000), **with no alert**.
  - 3,571 beams die, between steps 10 and 44 (median 34).
  - The only two that finish stay at a failure score (−6.11 and −6.14).
- **Summary of the blind brute force on the eyes**: the 3,814 "convention × natural pair" combinations surviving §42 have all been swept (241 at 600,000, 3,573 at 300,000), with no result.
- Given the measured sensitivity (about 1 success in 26 when blind on the testbed), this does not exclude these hypotheses. The remaining route is a human guess on the openings (positions 1–8 of E1, W2, W3, E4).

## 48. What limits blind brute force, plaintext language, and quarter-deck cuts (`opening_blind_calib.py`, `opening_truth_rank.py`, `quarter_turn_analysis.py`, `opening_pipeline.py lex=…`, 2026-10-14)

I was left 6 hours of autonomy by the repository owner: "continue on whatever you want".

**48.1 Vocabulary is not the limiting factor.** Blind calibration (beam 300,000, 12 test texts) with a dictionary drawn from the **very book** of the test texts, hence an ideal vocabulary: **1 / 12** decrypted. This is as much as with a dictionary drawn from other books (1 / 12, §47).

**48.2 The truth never reaches the end of the beam** (`opening_truth_rank.py`, 10 test texts, beam 300,000, blind): it is lost in **10 cases out of 10**, at steps 9 to 20. Checking more hypotheses at the end (K > 30) would be of no use. The bottleneck is the free zone of the first 20 to 25 symbols, where only the language model ranks the hypotheses.
- Order of magnitude: our model (≈ 2.5 MB of text) gives about 2.2 bits per character. A model trained on hundreds of MB would go down to about 1.3 bits, i.e. a factor of about 2^20 over the ~22 free symbols.
- This would be the only serious algorithmic lever. It requires downloading a large English corpus: to be asked of the repository owner.

**48.3 The favourites of §45 are cuts of about a quarter of the deck** (`quarter_turn_analysis.py`).
- **Mechanism**: with β = "cut k cards" and letters read at consecutive positions, a card read at t is re-read at t + d (with no space in between) when the ranks of the two letters differ by ±(d·k mod 83).

| Set | Share of β "cut k" | among them, \|4k mod 83\| ≤ 13 | \|2k mod 83\| ≤ 13 |
|---|---|---|---|
| 241 favourites (§45) | 0.73 | **0.74** | **0.02** |
| 3,814 survivors (§42) | 0.38 | 0.44 | 0.09 |
| 38,808 initial | 0.42 | 0.32 | 0.32 |
| uniform k from 1 to 82 | — | 0.32 | 0.32 |

- Most frequent cuts: k = 63, 24, 59, 20, 60, 25, 23, 58, 21. For these, 4k ≡ ±1 to ±17 (mod 83), i.e. about a quarter of the deck.
- With such a cut, two letters of neighbouring ranks separated by 4 symbols give the same card, hence the excess at d = 4. Two letters 2 symbols apart would have to differ by about 41 ranks, which is impossible in a 36-symbol alphabet, hence the deficit at d = 2.
- **Caution**: the deficit at d = 2 was used by the filter of §42; only the excess at d = 4 is independent, and it is itself weak (z ≈ 2 once repeated phrases are counted only once, §5).
- This is a **precise physical hypothesis**: "at each letter, cut the deck by about a quarter; at each space, perform another natural shuffle". It is not confirmed.

**48.4 Other languages or vocabularies on the eyes** (`opening_pipeline.py yeux lex=fi|jeu`, 241 favourite combinations, beam 300,000, blind).
- **Finnish**: Finnish corpus and Kalevala, Ä/Å → A, Ö → O. **The 241 beams die** (steps 23 to 41, median 30).
- **Game texts**: English translations, wiki, tablets. **The 241 beams die** (steps 23 to 41, median 34).
- No alert. Same reading as in §47: blind search only succeeds about 1 time in 12 to 26 on the testbed, so this is not a refutation.

**Summary of §48.** Blind brute force on the openings is exhausted under these hypotheses: 3,814 combinations in English, plus the 241 favourites in Finnish and with the game texts. It is limited by the language model, neither by the vocabulary nor by the beam width. Two levers remain:
- a much stronger language model, which requires downloading a large corpus;
- a human guess of about twenty symbols.

## 49. A stronger language model (Gutenberg corpus) (`download_gutenberg.py`, `opening_search2.py`, 2026-10-14)

The repository owner authorised the download of a large corpus ("download whatever you want").

**Corpus.** 400 English books from the "top 1000" ranking of gutenberg.org, without *Pride and Prejudice* (testbed text), i.e. 268 MB and 46.3 million words (`sources/texts/gutenberg/`, see `SOURCES.md`).

**Model v2** (`opening_search2.py`): word bigrams that **condition each letter**, not only word ends.
- P(prefix | previous word) is interpolated according to Witten-Bell.
- The dictionary words are numbered in lexicographic order: the words starting with a prefix form an interval, which reduces the computation to a binary search in the sorted successors of the previous word.
- Size: 140,793 words (seen at least 2 times) and 6.25 million bigrams, built in 32 s.

**Model strength** (`bits_per_char`, over 60,000 characters of *Pride and Prejudice*, out-of-dictionary words ignored, hence optimistic values, useful for comparison):
- **1.38 bits per character** with the Gutenberg corpus;
- 1.84 with the 3 books of §47.

**Blind calibration** (beam 300,000, 12 test texts): **1 / 12**, as before. The true branch is lost at steps 5 to 27.

**Diagnosis** (rank of the truth at the moment of loss). The truth is not wrongly eliminated: it slides down the ranking, from rank ~10–500 to rank ~5·10⁵ in 3 or 4 steps. This always happens **where several messages diverge at the same time**, each starting a new word. Example: "OF_" shared, then "EMPHATIC…", "CLEVER…", "I…".
- The uncertainty on the first letters of 3 or 4 simultaneous words multiplies (about 4 bits each). A better model does not compensate for this explosion.
- The eyes have exactly this structure: W2, W3 and E3/E4 diverge together at position 6.

**Reading.**
- The language model was not the only bottleneck. The bottleneck is structural: the joint search over several openings diverging together.
- A search separated per message would not work either: it would lose the constraints between messages, and about fifteen characters of a single message have too much entropy (about 2²⁰ to 2³⁰).
- **Eyes with model v2**: 241 combinations, beam 300,000, launched on 10/14; result in the next paragraph.
- **Eyes with model v2** (state on 2026-10-14, paused at the repository owner's request): **235 combinations out of 241** processed, all **dead**, with no alert.
  - 6 remain. To resume: `python -u opening_pipeline.py yeux lex=gut 300000 30 241 P 2`, with P = 0 and 1 (combinations already done are skipped).
- **Night of 2026-10-15** (`run_overnight_gut.py`):
  - **Eyes, model v2**: the 241 favourites and the 3,573 other survivors of §42 are all swept, **with no alert**. Two beams go to the end, at a failure score (−6.06 and −6.16).
  - **Calibration with model v2 and guessed symbols** (12 test texts each): **6 / 12 decrypted with 10 guessed nodes, 3 / 12 with 5**. With the small model of §47, about 20 nodes were needed for 8 / 12.
  - ⇒ The strong model does not unblock the blind search, but it **reduces the human guess needed**: about ten symbols at the start of the messages.
- **Nights of 2026-10-16 to 10-18**:
  - **`tous01` pass** (English model v2; combinations of the local filter at P ≥ 0.01 excluding those at 0.05): **3,507 combinations, with no alert**. Three beams go to the end, at a failure score (−6.04; −6.20; −6.23; meaningless texts).
  - In total, **7,321 "convention × natural pair" combinations** have been swept blindly with the strong English model, with no result.
  - **Aborted Finnish attempt**: the Finnish Gutenberg download failed (network outage, 14 books out of 400). The passes done with this weak model (241 favourites, all dead; 276 others) are kept under `opening_blind_out_gutfi14_*` and do not count.
  - Relaunched on 10/18 at 22:10 (`run_overnight_fi.py`).

## 50. "Finnish plaintext" hypothesis with a strong language model (`download_gutenberg.py 400 fi`, `opening_pipeline.py lex=gutfi`, 2026-10-18 to 10-19)

Noita is a Finnish game, and the Finnish attempt of §48 only had a small corpus (Finnish corpus and Kalevala).
- **Corpus**: 400 Finnish books from Project Gutenberg (100 MB, `sources/texts/gutenberg_fi/`), plus the Finnish corpus and the Kalevala. Ä/Å → A and Ö → O, for lack of room in the convention's alphabet.
- **Model**: the model v2 of §49 (word bigrams conditioning each letter), in Finnish.
- **Eyes, 241 favourites** (beam 300,000, blind, 10/18 22:29 → 10/19 03:25): **the 241 beams die** (steps 23 to 44, median 34), with no alert.
- **Eyes, other survivors of §42**: **402 out of 3,573** processed at the reading of 10/19 at 11:38, all dead; the pass is still running.
- **Reading**:
  - no alert;
  - no Finnish calibration on the testbed, but the structural limit of §49 (several openings diverging together) holds in Finnish too;
  - this negative result therefore does not exclude a Finnish plaintext.
- **End of the Finnish pass (2026-10-21)**: the **3,573** other survivors of §42 are processed, **with no alert**.
  - Only one beam goes to the end, at a failure score: AZ19_/k, deal5fwd_inv/rot49, −6.34, meaningless pseudo-Finnish ("EIPA_NIIN_IK_IL…").
  - The 3,814 combinations of §42 are therefore swept in Finnish as in English, with no result.
