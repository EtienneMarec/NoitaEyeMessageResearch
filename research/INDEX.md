# Script index

One script per analysis. Generated from the module docstrings; §N refers to the sections of [`REPORT.md`](../REPORT.md).

| Script | Purpose |
|---|---|
| `abc_posterior.py` | ABC rejection inference (§40): posterior probabilities of the hypotheses, from abc_sims.tsv. |
| `abc_simulate.py` | Simulations for ABC inference (§40). |
| `abc_small_k.py` | Is the "space almost equal to β" regime (k ≤ 2 swaps) compatible with the eyes? (§41) |
| `abc_stats.py` | Summary statistics shared by the eyes and the simulations (ABC inference, §40). |
| `alignment_map.py` | Shifted alignments of shared plaintext between two messages (GAK model). |
| `architecture.py` | Plaintext architecture deduced from alignment_map.py and plaintext_diff_map.py (GAK model). |
| `avoid_homophone_test.py` | Homophones chosen by an EQUALITY rule with the last outputs (§28). |
| `basin_keyed_deck.py` | Basin of attraction of the keyed-starting-deck attack (space decisions recomputed) (§36). |
| `basin_test.py` | Basin of attraction: starting from the true table with a fraction of the destinations (of the read positions) replaced at random, does annealing recover the true table? |
| `beam_blocks.py` | Lead 2: "parallel" beam (the 9 messages advance together) over the reinsertion table, with two constraints on top of the "Chinese restaurant" likelihood: * BLOCKS:… |
| `beam_reinsert.py` | Beam search over the reinsertion table (mechanism of §8, sorted deck, first symbol outside the deck, no base shuffle). Step-by-step decryption, message after message;… |
| `block_propagation.py` | Propagation of shared-block equations (space model, β and σ known) (§36). |
| `burst_sweep.py` | Bursts of differences: base shuffle = rotation (cut c cards) and grouped read positions (§25). |
| `cauldron_key_test.py` | User's hypothesis: the deck key might come from another Noita secret, here the 64-byte cauldron block (512 bits, 365 of which for the calendar; an arbitrary… |
| `chaocipher_test.py` | Adapted Chaocipher (cipher alphabet of 83 cards, plain alphabet of 83 slots of which 35 are symbols): does a repeated phrase give perfect isomorphs, as in the eyes?… |
| `check_keyword_battery.py` | Control: does the keyword_decks battery detect a keyword deck on test messages? |
| `class_model.py` | Letter-class model (§43): a generalisation of the space model. |
| `closed_cycles_test.py` | Short closed cycles in the correspondences after an insertion: a discriminator between base shuffles. Eyes (cycle_structure.py): 0 closed cycles in 10 blocks (~210… |
| `coincidence_distance_test.py` | Where do coincidences fall after a divergence? Near (+1..+9) versus far (+10..+20) (§32). |
| `coincidence_pvalues.py` | P-values of the eyes' coincidences after a divergence, on the window CHOSEN IN ADVANCE (+1..+20) (§32). |
| `commutativity_test.py` | Commutativity conflicts in the main isomorph family (§25). |
| `context_homophone_test.py` | Homophones chosen from the PREVIOUS LETTER (deterministic): a repeated phrase keeps the same homophones (except at most its first symbol), so it stays isomorphic,… |
| `context_read_test.py` | Read position depends on context, shuffle depends on the letter (§25). |
| `convention_abc_filter.py` | ABC filter of the (read convention, β, σ) combinations surviving §42 (§45). |
| `convention_abc_summary.py` | Summary of the ABC filter of conventions (§45): convention_abc_out_*.tsv against the space-model baseline (random q). |
| `convention_top_detail.py` | Per-statistic detail of the best (convention, β, σ) combinations of the ABC filter (§45). |
| `cpsat_reinsert.py` | EXACT constraint-programming attack (OR-Tools CP-SAT) on the reinsertion table. |
| `cpsat_space_attack.py` | Exact constraint-programming attack (OR-Tools CP-SAT) on the space model (§42). |
| `crib_candidates.py` | Generation of probable texts taken from the game data (§38). |
| `crib_candidates_texts.py` | Probable texts taken from the alchemical texts and the Kalevala (sources/texts) (§38). |
| `crib_length_known_q.py` | Length of probable text needed under the "known positions" convention + letter frequencies (§44). |
| `crib_length_test.py` | How many space positions must be known to recover the starting deck? (§33) |
| `crib_scan.py` | Parallel scan of probable texts × natural shuffle pairs (space model) (§38). |
| `crib_test.py` | Test of a probable text (crib) in the space model, for a given (β, σ) shuffle pair (§38). |
| `cycle_score_sa.py` | Search for spaces through the block-cycle score (space model, β and σ known) (§37). |
| `cycle_structure.py` | Cycle structure of the correspondence between two shifted occurrences of the same text. |
| `deckcipher.py` | Position-read "deck of cards" ciphers (XGAK family), with numba. |
| `diag_lazy.py` | Compares, event by event, the cost of the true table (exact replay) with the beam's best cost. |
| `divergence_models.py` | Coincidences right after a divergence: eyes versus models (§26). |
| `download_gutenberg.py` | Download of a public-domain English corpus (Project Gutenberg) for a stronger language model (§49). |
| `eq_graph_info.py` | How many INFORMATIVE cycles does the system of block equations of the eyes contain? (§36) |
| `explore.py` | Exploration of more structured "deck of cards" mechanism families (XGAK). |
| `explore2.py` | Variant: the first trigram does NOT go through the deck (all messages start from the same state after it). Absence of doubles is guaranteed: the card read, after τ… |
| `extract.py` | Extracts the 9 eye messages from the PDF and converts them into trigrams 0-82. |
| `eyes_near_beta_scan.py` | Attack on the eyes in the "space ≈ β" regime (k ≤ 2 swaps), the only regime where the attack works on the testbed (§41). |
| `fair_joint_test.py` | A "fair" joint test: the substituted letters in the testbed (Stutter E4/E5 at 21 and 26, obstacle E1/W1 at d0 and d0+8) are drawn at random from English frequencies… |
| `family_zoo.py` | Zoo of structured XGAK families, judged on ALL the criteria from the eyes (testbed, no homophones). |
| `fingerprint_models.py` | Statistical fingerprint (stats.fingerprint, from position 50): eyes versus models (§26). |
| `first_letter_test.py` | Test "only the first letter differs" in a deck-of-cards model (GAK, fixed-read XGAK). |
| `first_trigram_checksum.py` | Is the first trigram a checksum / an index computable from the rest of the message? We test a battery of simple functions f(message without its first trigram, length,… |
| `first_trigram_window_scan.py` | Test "consecutive message numbers" on generated starting decks (§46). |
| `fixed_points_test.py` | Fixed points in the shifted blocks after a letter insertion: eyes vs models. Eyes (cycle_structure.py): 0 fixed points over ~210 pairs (10 blocks). For each model, we… |
| `flat_joint_test.py` | Joint battery of Lymm's model with a flattened plaintext (§31). |
| `flat_plaintext_test.py` | Hypothesis "plaintext with flat frequencies": full battery of Lymm's model (§31). |
| `flatten_gamma_test.py` | Flatness versus coincidences: is there a flattening of the plaintext that satisfies both? (§31) |
| `formulaic_test.py` | FORMULAIC texts: can the space model reproduce the stutter and the coincidences? (§30) |
| `gap_profile.py` | Profile of repeats at distance d (c[i] == c[i+d] within one message), deduplicated. |
| `gap_profile_collapsed.py` | Profile of repeats at distance d, counting ONCE each repeat produced by the same repeated phrase (isomorphs from Toboter's list,… |
| `gap_profile_order.py` | Gap profile (repeats at distance d): eyes versus Lymm's model with β of order 4 or 8 (§27). |
| `groupA_attack.py` | Attack on group A (E1, W1, E2) through block consistency, space model, given natural (β, σ) (§37). |
| `homophone_test.py` | Variant: β + ONE swap per letter, but with a flattened homophonic alphabet. Each letter gets a number of read positions proportional to its frequency (82 positions),… |
| `insertion_maps.py` | Insertion correspondences and cycles of the natural shuffles (§35, step 1). |
| `isomorphs.py` | Detection of maximal isomorphs between all pairs of positions. |
| `joint_test.py` | Joint test of the structured XGAK families on the testbed (first trigram outside the deck, no homophones, 40 keys per family). Criteria from the eyes: (1) flat gap… |
| `keyed_deck_attack.py` | Attack "keyed starting deck, natural shuffles" on the space model (§33). |
| `keyed_deck_attack2.py` | Attack "keyed starting deck, natural shuffles", time-progressive version (§33). |
| `keyed_deck_robust.py` | Attack "keyed starting deck" with ROBUST space decisions (§36). |
| `keyed_deck_sa.py` | Simulated annealing on the keyed starting deck (known natural β, σ) (§33). |
| `keyword_decks.py` | Decks ordered by keywords taken from the game texts and the wiki (user's hypothesis: the deck key might come from a detail of the game, even a minor one). |
| `known_positions_attack.py` | Attack on the starting deck when the read positions follow a known convention (§39). |
| `known_positions_greedy.py` | Space decisions through greedy passes over time, known read positions (§39). |
| `known_positions_sa.py` | Annealing over the space decisions when the read positions are known (§39). |
| `known_positions_sa_x.py` | Annealing over the starting deck, time-progressive, "known positions" convention + frequencies (§44). |
| `known_positions_unigram.py` | Convention "known read positions" + letter frequencies (§44). |
| `known_q_local_filter.py` | Local filter of the natural pairs (β, σ) under the "known read positions" convention (§42). |
| `lazy_beam.py` | LAZY search for the reinsertion table (model of §8/§10: sorted deck, no base shuffle, first symbol outside the deck, one read position per letter). |
| `lazy_exact.py` | EXACT lazy search for the reinsertion table (one held card at a time). |
| `lineage_coincidence.py` | Coincidences after a divergence, counted by LINEAGES (§26). |
| `lm_beam.py` | Beam over the PLAINTEXT with a language model, known read positions (space model) (§39). |
| `lm_beam2.py` | Beam over the plaintext, messages decoded IN PARALLEL (time step by time step) (§39). |
| `mixed_context_test.py` | Combination of the two best leads (§20, §21): letter-dependent reach (Ks) AND homophones chosen from the previous letter. Same criteria as context_homophone_test… |
| `moderate_space_attack.py` | Attack on the space model with a MODERATE space shuffle (§41): σ = τ_k ∘ β, τ_k = k random swaps. |
| `moderate_space_curriculum.py` | Time-progressive attack on the space model with a moderate shuffle (§41). |
| `natural_pair_filter.py` | Filter of the NATURAL pairs (β, σ) of the space model by the statistics of the eyes (§36). |
| `near_space_test.py` | Hybrid model "letters = exactly β, space = β + small swaps" (§32). |
| `nodouble_profile.py` | Why does the no-doubles rule degrade the flatness of the "β of order 8" model? (§29) |
| `obstacle_bounds.py` | Figures of §24.2: model-free bound for the obstacle, and clustering of the differences. |
| `obstacle_exact_rate.py` | Precise probability of the exact obstacle pattern (4/4/4/13) in Lymm's model (§31). |
| `obstacle_pattern_test.py` | Probability of the EXACT PATTERN of the E1/W1 obstacle under several readings of the plaintext (§24). |
| `obstacle_readings_rate.py` | Exact obstacle pattern depending on the text reading, in Lymm's 1-swap model (§32). |
| `obstacle_test.py` | Is the E1/W1 "obstacle" (Lymm: two 4-letter words swapped) compatible with the surviving families (reinsertion / segment reversal + base shuffle β)? Eyes: E1/W1,… |
| `offset_scan.py` | For a set of occurrences of the same phrase, looks for the effective offsets e_k (mod 83) making the "single wheel" model consistent: pos(y)-pos(x) = e_l - e_k (mod… |
| `opening_blind_calib.py` | Calibration of the BLIND brute force on the openings (§47): share of "whole-word" testbeds decrypted with no guessed symbol, with the true pair and a dictionary taken… |
| `opening_crib_solver.py` | Guessed-openings solver under the known read positions convention (§44). |
| `opening_pipeline.py` | Full chain "guessed partial openings → brute force → verification" (§47). |
| `opening_search.py` | Dictionary-guided brute force on the message OPENINGS (§47). |
| `opening_search2.py` | Beam over the openings with a "word bigram conditioning the prefix" language model (§49). |
| `opening_truth_rank.py` | Final rank of the true solution in the blind beam (§47, diagnosis of the verification). |
| `order_deficit_test.py` | Signature of a β of order L with doubles forbidden by construction: dip at d ≡ 1 (mod L) (§29). |
| `plaintext_diff_map.py` | Map of plaintext differences between aligned messages (allomorph method). |
| `plaintext_flatness_test.py` | Does the flatness of the gap profile depend on the plaintext? (§28) |
| `post_divergence_test.py` | Coincidences at the same position right after a text divergence (§26). |
| `probe1.py` |  |
| `progressive_cores.py` | Pure progressive alphabet (c_t = W[x(p_t) + s·t]) on the isomorph cores, repeated columns only (§23). |
| `progressive_redundancy.py` | Rate of satisfaction of the redundant constraints under the "progressive alphabet" hypothesis (§23). |
| `progressive_test.py` | Test of the "progressive alphabet" model (disc advancing s steps per letter). In this model c_i = C[P[p_i] + s*i]. Two occurrences of the same phrase at positions i… |
| `qscan.py` | Scan of natural "deck of cards" mechanisms: for each, the sequence of read positions q is computed from the ciphertext (initial deck assumed known) and its IoC is… |
| `quarter_turn_analysis.py` | Why are the 241 favourite combinations of §45 mostly cuts of about a quarter of the deck? (§48) |
| `reinsert_scan.py` | Scan of the "reinsertion" family: output = D[q]; the card read is removed then reinserted at position f(q); then base shuffle β. If f is a fixed function of q… |
| `rng_decks.py` | Decks shuffled by NOITA'S PSEUDO-RANDOM GENERATOR (hypothesis: the deck key is a numeric seed passed through the game's generator). |
| `run_crib_queue.py` | Autonomous queue of the probable-text scans (§38). |
| `run_overnight_fi.py` | Night queue of 17/10/2026 (§50): "Finnish plaintext" hypothesis with a strong language model. |
| `run_overnight_gut.py` | Night queue of 15/10/2026 (§49, continued): chained computations, each step in 1 or 2 processes. |
| `run_overnight_openings.py` | Night queue (§47, continued): long computations chained, one at a time (limited memory). |
| `run_rng_scan.py` | Scan of the eyes: direct seeds 0..S (M1/M2 × 3 shuffles) + SetRandomSeed(x, y) for special world seeds, x, y in [-100, 100] (3 shuffles). Then re-check of the best on… |
| `sa_progressive.py` | PROGRESSIVE annealing on the reinsertion table: only the first L symbols of each message are used, L increasing (5, 10, 15, ...), restarting from the best previous… |
| `sa_reinsert.py` | Simulated annealing on the reinsertion table f (mechanism of §8: read at q, reinsertion at f(q), sorted initial deck, no base shuffle, first symbol outside the deck). |
| `sa_robust.py` | Simulated annealing on the starting deck, with robust space decisions (one beam per message) (§36). |
| `sa_space_model.py` | Simulated annealing on the space model (β for letters, σ for the space), sorted starting deck (§30). |
| `same_delta_models.py` | The "same shift" test (same_delta_test.py) applied to the models, on the testbed (§25). |
| `same_delta_space_k.py` | The "same shift" test (§23) applied to the space model with a moderate shuffle σ = τ_k ∘ β (§41). |
| `same_delta_test.py` | Same shift, different message pairs (§23). |
| `scan_space_natural.py` | Scan of the space model with NATURAL shuffles (§26). |
| `segment_length_test.py` | All criteria at once, including the E1/W1 "obstacle", for "reinsertion / segment reversal + base shuffle β" families whose segment length is controlled: destination… |
| `segment_mix_test.py` | Follow-up to segment_length_test: (1) letter-dependent reach (each letter draws its reach K from a set, e.g. {2, 41}); (2) base shuffle "cut one card" with a short… |
| `sigma_power_test.py` | Test of the positional model c_i = sigma^i(u_i) (Pyry/dextercd: "P^pos[S[char]]"). |
| `single_wheel_all.py` | Single wheel for ALL shifted blocks (§23). |
| `single_wheel_cores.py` | Single wheel (cyclic abelian GAK) on the isomorph cores, columns with a repeated symbol only (§23). |
| `small_order_test.py` | Lymm's model with a base shuffle β of SMALL ORDER (β^8 = id) (§27). |
| `space_beam.py` | Beam search with the SPACES as unknowns (space model, β and σ known, keyed starting deck) (§34). |
| `space_joint_test.py` | Joint battery of the space model, on equal assumptions with Lymm's model (§32). |
| `space_k_sweep.py` | Trade-off between flatness and far coincidences as a function of the strength of the space shuffle (§32). |
| `space_model_test.py` | Model "the space shuffles differently" on the testbed with spaces (§26). |
| `special_letters_test.py` | Model "shared shuffle + special letters" (§26). |
| `stats.py` | Statistical fingerprint of a corpus of encrypted messages (lists of integers). |
| `stutter_budget_test.py` | How many differing letters are needed in the E4/E5 stutter for Lymm's model to pass? (§24) |
| `stutter_test.py` | Quantitative test of the "Stutter Section": between two messages with almost identical text (point edits), share of identical positions and number of =/. alternations… |
| `support_spectrum.py` | Spectrum of supports (lead 1 of the status notes): a model-free measure, valid for any XGAK. |
| `swap_context_test.py` | Lymm's model (small swaps + base shuffle β) with homophones chosen from the previous letter. |
| `swap_model_test.py` | Is Lymm's hypothesis (σ_p = β ∘ τ_p, τ_p = k letter-specific swaps) compatible with the FLAT gap profile of the eyes? |
| `testbed.py` | Test corpus with the architecture of the eyes, encrypted by a known mechanism (ground truth). |
| `testbed_spaces.py` | Testbed WITH spaces (symbol "_"), same architecture as testbed.build_plaintexts (§26). |
| `testkey.py` | Test key "reinsertion" (corrected model of §8: NO homophones, compatible with perfect isomorphs): one read position per symbol, arbitrary destinations outside the… |
| `uniform_plaintext_test.py` | Full battery of Lymm's model (β of order 8 or random, k = 1) with a plaintext of FLAT frequencies (§28). |
| `validate_beam.py` |  |
| `validate_blocks.py` |  |
| `validate_cpsat.py` | Validation of the CP-SAT attack on the test key (reinsertion with no shuffle, no homophones). |
| `validate_cpsat_blocks.py` | CP-SAT + block constraints (true shared blocks of the testbed) on the 9 messages, prefix L. |
| `validate_lazy.py` |  |
| `validate_lazy_exact.py` |  |
| `validate_reinsert.py` | Validation of the "reinsertion" sweep on test messages encrypted by reinsertion at destination f(q) = q+17, flattened homophones, 1st symbol outside the deck. |
| `validate_rng.py` | Validation: (1) the generator reproduces pick_world_seed/Next as in misc.cpp on a few values; (2) a deck shuffled by the generator (known seed) is recovered by the sweep. |
| `validate_sa.py` | Validation of simulated annealing on test messages: ARBITRARY reinsertion table (reads on 41 positions, destinations on the others), flattened homophones, sorted… |
| `validate_sa2.py` |  |
| `validate_testbed.py` | Validation on test messages (known truth): 1. does the statistical fingerprint look like that of the eyes? 2. does the mapping (alignment_map) recover the real shared… |
| `verify_from_game.py` | Independent check: rebuilds the digits of the eyes from the 64-bit numbers hard-coded in noita.exe (function decompiled by Ninji,… |
| `wheel_solver.py` | Is there ONE wheel (mixed alphabet of 83 notches) and offsets e_k such that each occurrence k of a phrase is the same phrase encrypted with the wheel rotated by e_k?… |
