# Sim lane findings C2: equation tests for the ALG rows with no test (2026-10-13)

Writer: sim-lane test writer C2. Built tree: `origin/main` at the worktree base, `make` clean. Run line:
`~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/csim/test_alg_*.py -q` gives 61 passed, 9 failed.
No csrc change, no existing test touched, no threshold widened. A red test is a finding and stays red.

Tolerances the writer chose (numeric, not game values; Westley may overrule): `1e-6` to `1e-12` on double comparisons; ALG-56
allows half a tick because the C result is a whole tick count; ALG-47 allows `0.05` on a measured share over 800 seeds
(observed 0.370 against 0.356 expected; the rival readings sit at 0.286 and 0.58, so the test discriminates).

## Coverage

| ALG | Test file | Result | Note |
|---|---|---|---|
| ALG-46 rotation decision | `tests/csim/test_alg_46_rotation_decision.py` | 8 green, 1 red | Red: `test_ALG_46_the_delta_the_rule_names_reaches_the_live_selector` (SL-C2-01). |
| ALG-47 commander pools | `tests/csim/test_alg_47_commander_pools.py` | green (7) | Pool roll, score formula, unrelated pool, nemesis uniform draw, search order, weighted previous draw. See SL-C2-12 (observation). |
| ALG-48 lineage generation | `tests/csim/test_alg_48_lineage_generation.py` | 5 green, 2 red | Red: exact-integer count (SL-C2-02), single-member parent draw (SL-C2-03). |
| ALG-49 lifespan and succession | `tests/csim/test_alg_49_lifespan_and_succession.py` | 8 green, 2 red | Red: successor region (SL-C2-04), name pool exclusion (SL-C2-05). Q-060-01 conflict is SL-C2-06 (green test pins the rule text). |
| ALG-51 clustering | `tests/csim/test_alg_51_clustering.py` | 6 green, 1 red | Red: primary region (SL-C2-07). Step 1 band to category mapping is covered by `test_E09_B5_consequence_entry.py` (does not name ALG-51); live clustering gaps are SL-C2-08 and SL-C2-09 (code read). |
| ALG-52 selection | `tests/csim/test_alg_52_selection.py` | green (5) | Reference implementation compared entry by entry. The minimum-refill sentence is dead text (see note below the table). |
| ALG-53 assembly | `tests/csim/test_alg_53_assembly.py` | 6 green, 1 red | Red: slot echo seam (SL-C2-10). Live echo path is correct. |
| ALG-54 candidate pool | `tests/csim/test_alg_54_candidate_pool.py` | 4 green, 2 red | Red: unowned neighbor (SL-C2-11), empty tier (SL-C2-13). |
| ALG-56 time limit | `tests/csim/test_alg_56_time_limit.py` | green (3) | All 10 archetypes by 61 urgencies. |
| ALG-57 force parity | `tests/csim/test_alg_57_force_parity.py` | green (6) | Enemy power, base parity, difficulty parity and floor, fill, shortfall. Tie order is SL-C2-14 (observation, no red test). |
| ALG-61 area damage | `tests/csim/test_alg_61_area_damage.py` | green (3) | Direct Bombard path `om_unit_fire_aoe_attack`; Barrage ability path not exercised. |

No row was skipped: every function the tests need is in `signatures.toml` and bound by `conftest.py`.

Note on ALG-52: the sentence "if fewer than 5, add skipped clusters while a category has fewer than 2" can never add anything, because a cluster is only skipped when its category already has 2. The C sim has no refill pass and the green test asserts the same outcome as the reference that does implement it. A bible cleanup (delete the sentence, R-065-06 already says the cap wins), not a code change.

## Findings

Classes: C = C differs from the bible; B = bible is ambiguous or contradicts itself (a proposed `Q-` row follows).

### SL-C2-01 (C, high) ALG-46: the rotation chance ignores how much the home region changed

- Rule: ALG-46 step 4 / R-057-03: `p = 0.8 + min(1, D/200) * (0.1 - 0.8)`, D the home region's total field delta over the jump.
- Sim: `om_character_selector_run_for_lineage` (`csrc/generational.c`, around line 1343) fixes `double delta = 0.0` ("not wired to this call site"), so p is always 0.8 before the decay, however busy the jump was.
- Repro: `test_ALG_46_the_delta_the_rule_names_reaches_the_live_selector`. Home region (95, 15, 5, 95), 50-tick `om_time_jump_run`, D = 96.9, expected p = 0.461; a draw of 0.630 must stay, the sim rotates. Assertion line: `assert rec.rotated == 0` ... `D=96.9 -> p_rotate=0.461; draw 0.630 must stay but the selector used p=0.8 and rotated`.
- Note: the legacy `simulation/character_selector.py` also defaults `region_field_delta=0.0`; its checkpoint test computes D from before/after snapshots over the lineage's home region (sum of absolute change of the four fields).
- Proposed piece (files `csrc/generational.c` only, plus the gen_state save hooks if D is kept across a save): `SL-ALG46-delta`: in `gen_time_jump` take the four-field absolute change of each lineage's home region between the start snapshot it already holds (`start_eco`, `start_mil`, `start_ten`, add population) and the end; store per lineage; read it in `om_character_selector_run_for_lineage`. Storing it changes the save format, so the save part is a contract piece first. Tests: the red test above plus a golden refresh.
- Confidence: high that the delta is not wired; medium on the exact D definition (four raw fields, home region = first history region).

### SL-C2-02 (B, high) ALG-48: `floor(living * 0.03 * T)` is one short at exact products

- Rule: `n = max(1, floor(living * 0.03 * jump_ticks))`.
- Sim: `(double)n_living * 0.03 * (double)jump_ticks` in IEEE doubles; for 22 living and the live jump length 50 the product is 32.99999999999999, floor 32, rule 33.
- Repro: `test_ALG_48_count_at_exact_integer_products_the_live_jump_length`: `(living, C count, rule count): [(22, 32, 33), (30, 44, 45), (38, 56, 57), (44, 65, 66)]`. Also 60, 74, 76 living at 50; many pairs at 100 ticks (11 living gives 32 not 33).
- The Python reference does the same float arithmetic, so "verbatim" and "as written" disagree.
- Proposed Q row: Q-NEW-ALG48-floor. Candidates: (a) exact arithmetic, `(living * 3 * T) / 100` in integers (matches the rule as written, one more descendant on 7 of the first 79 lineage sizes at T = 50); (b) keep the IEEE product and add a note to ALG-48 that exact boundaries round down; (c) add a half-ulp guard `floor(x + 1e-9)`.
- Proposed piece if (a) or (c): `csrc/generational.c` one line in `om_lineage_generate_descendants`; moves every golden checksum that has a lineage of those sizes.
- Confidence: high on behaviour; ruling needed.

### SL-C2-03 (C, high) ALG-48: the parent draw is skipped when one member lives

- Rule: "Draw order per descendant: parent, spread roll, (neighbor draw), name, lifespan."
- Sim: `om_lineage_generate_descendants` draws the parent only `if n_living > 1`; with one living member the spread roll becomes the first draw and every later draw shifts one place. The Python `rng.choice(living_members)` consumes a draw for a list of one.
- Repro: `test_ALG_48_parent_draw_is_taken_even_for_a_single_living_member`: forced draws `[0.99, 0.05, 0.6, 0.0, 0.5]`, one living member, two inhabited neighbors: expected region 2 and lifespan 250; the sim gives `(0, 270)`. Control: with two living members the same sequence gives the rule's result (`test_ALG_48_draw_order_parent_spread_neighbor_name_lifespan` green).
- Proposed piece (`csrc/generational.c`): always draw the parent (`pidx = floor(d * n_living)`), keep `om_lineage_spawn_single_descendant` as the documented test seam. Changes the random stream of every one-member lineage (the common case early in a campaign): goldens refresh.
- Confidence: high.

### SL-C2-04 (B, medium) ALG-49 versus R-060-03: where a supreme commander's successor stands

- ALG-49: "a supreme commander is succeeded in the faction's first region". R-060-03: "in the same faction and region". Python: `faction_regions[0]`. The sim uses the dead commander's own region (`om_process_natural_deaths`, `csrc/generational.c`), also when the faction no longer owns it.
- Repro: `test_ALG_49_supreme_successor_is_placed_in_the_factions_first_region`: faction 2 owns regions 1 and 3, supreme stands in 3 and dies: successor in region 3, ALG-49 says 1. Assertion: `successor in region 3, the faction's first region is 1`.
- Proposed Q row: Q-NEW-ALG49-successor-region. Candidates: (a) the dead commander's region (edit ALG-49, test goes green after the test is reclassed `test-defect`); (b) the faction's first owned region by index; (c) the dead commander's region while the faction owns it, else the first owned region.
- Confidence: medium; the two bible lines disagree only when a supreme is not in the faction's first region, which happens after the faction loses its first region.

### SL-C2-05 (C, medium-high) ALG-49: a name in use is never taken out of the pool

- Rule: a dead character's name "returns to the pool after 500 ticks (4500 for a main character)", so a living character's name is out of the pool. Python `NamingSystem` keeps `_in_use` and `_cooldowns` per name.
- Sim: `gen_roll_name` is a uniform pick from a 16-name list; `om_character_name_reuse_cooldown` is a lookup nothing consumes. Twelve characters in one faction carry only 10 distinct names.
- Repro: `test_ALG_49_a_name_in_use_is_out_of_the_pool`: `duplicate names among 12 living characters: [..., 'Odalys', 'Odalys', ..., 'Vashtir', 'Vashtir', ...]`.
- Proposed piece: `csrc/generational.c` tracks name in-use and release tick per name (new world state: hashed in `checksum_full` and saved, so a contract/save piece first), a larger authored name pool, and a rule for exhaustion (Python returns no character; needs a ruling). Test stays red until built.
- Confidence: medium-high on the difference; the bible does not say what happens when the pool is empty.

### SL-C2-06 (B, high) Q-060-01: the register says per tick, the rule text and the sim say end of jump

- `docs/northstar/ambiguity_register.md` Q-060-01 closed "(b) per tick, build it that way in C" (2026-09-13). E-08 line 106 says "Flag closed, rule text pending"; R-060-04, ALG-45 and ALG-49 still say once at the end of each jump. The sim follows the rule text.
- Repro (scratch run, not a test, since the green `test_ALG_49_deaths_are_processed_once_at_the_end_of_the_jump` pins the rule text): character born 0, lifespan 30, `om_time_jump_run(w, 50)`: status historical, `death_tick = 50` (per tick it would be 30).
- Proposed Q row: Q-060-01b. Candidates: (a) end of jump, as built (rewrite the register answer's rule text to say so, name cooldown counts from the end tick); (b) per tick as Westley answered: `om_world_step` runs the death pass each tick, successors appear mid-jump, 4096-character scan every tick (cost); (c) per tick only for commanders (successors matter at once), end of jump for the rest.
- Confidence: high that the two documents disagree; the choice is Westley's.

### SL-C2-07 (C, high) ALG-51: a chain cluster's primary region is the first region seen, not the most common

- Rule: "Primary region = most common region in the cluster."
- Sim: `chron_build_chain_clusters` (`csrc/chronicle.c`) takes the region of the first event of each tag.
- Repro: `test_ALG_51_primary_region_is_the_most_common_region_in_the_cluster`: events of tag 7 in regions 1, 2, 2, 2: cluster region 1, rule 2. Assertion: `primary region 1; regions seen [1, 2, 2, 2]`.
- Proposed piece (`csrc/chronicle.c`, tag groups count regions and take the maximum, ties to the first seen): small. The merge by (primary region, category) then follows the new primary.
- Confidence: high.

### SL-C2-08 (C, high, code read) ALG-51/52: chain clusters carry no score, so they always rank last

- Rule: "Peak score = max event score"; ALG-52 ranks the rest by peak score. `om_chronicle_add_chain_event(w, chain_tag, region_idx, category)` has no score parameter, and `chron_build_chain_clusters` pushes every chain cluster with `0.0`; the time jump (`gen_time_jump`, `csrc/generational.c`) calls it the same way. Every chain cluster therefore sorts after every scored regional cluster and, when the category cap bites, is the one dropped.
- No red test: the contract cannot express the score. Contract gap, so a contract piece first: add `double score` to `om_chronicle_add_chain_event` (`csrc/ouroboros_sim.h`, `signatures.toml`), then `csrc/chronicle.c` keeps the maximum per merged cluster and `gen_time_jump` passes `om_chronicle_score_event` of each chain event.
- Confidence: high on the code; the visible effect (chains missing from scrolls) wants one seeded run to confirm.

### SL-C2-09 (C, medium, code read) ALG-51 steps 2 and 3: the live clustering is not the rule's

- `gen_time_jump` makes one lineage cluster per lineage at that lineage's last history region whatever happened there, and never classifies an event as a lineage event by member location, attached character or mission region (R-067-01); it passes one template name (the first chain event at that region) to the lineage categorizer and `chains[g].template_id` (the first event of the chain) to the chain categorizer, so "any template with ..." (R-067-02, R-067-04) is "the first template with ...". An event in the mission region becomes a regional cluster. Q-070-01 (lineage clusters capped at 2) is closed with rule text pending.
- Not reproduced by a test: forcing fired events into a jump log is not reachable from the ctypes surface. Belongs to the lane's chronicle-source programme (context file task 2): one seeded campaign, compare the delta stream to the scroll.
- Confidence: medium.

### SL-C2-10 (C, low) ALG-53: the slot-echo seam ignores whether the two values are the same

- `om_chronicle_apply_slot_echo_anaphora(w, frag1, frag2)` returns "what followed" whenever `frag1` has 6 or more words, even when `frag2` differs. The live path (`chron_apply_echo_between`) fires on the same slot key in both templates, so the values are equal by construction and the assembled text is right.
- Repro: `test_ALG_53_slot_echo_needs_the_same_value_of_six_or_more_words`: `two different values of 6+ words are not a slot echo` (`'what followed' == 'a quiet winter in the northern hills'`).
- Proposed piece: `csrc/chronicle.c` seam compares the two strings. Only the test seam is wrong.

### SL-C2-11 (C, medium) ALG-54: unowned neighbors never enter the pool

- Rule: regions are the player's regions plus every neighbor, "excluding empty tier". Sim: `om_mission_build_candidate_pool` skips `owner < 0`. A non-empty unowned neighbor the player once held can never fire Reconquest.
- Repro: `test_ALG_54_an_unowned_neighbor_with_population_is_not_empty_tier`: `unowned frontier neighbor with previous owner = player missing from the pool` (pool is empty).
- Proposed piece (`csrc/mission.c`): drop the `owner < 0` skip, rely on each trigger's own owner guard (most already test `owner < 0`). Confidence: medium (the skip may have been chosen on purpose; Python includes these regions).

### SL-C2-12 (B, low) ALG-47: "chapters_ago" is the lineage's chapter counter

- The previous pool scores `min(chapters_ago, 4)/4`, Python computes `current_chapter - last chapter played`. The sim passes `l->chapter_count` (ruling A26, `test_E08_S058_previous_pool_chapter_ago.py`), so a lineage played in each of the last four chapters scores the full gap bonus and the one just left is as attractive as the longest absent one. Measured: lineage with counter 4 and 2 members against counter 1 and 5 members is drawn at 0.37, matching counter-as-gap (green test).
- Observation only, no red test. Proposed Q row: Q-NEW-ALG47-gap. Candidates: (a) keep the counter and rewrite ALG-47 ("chapters played"); (b) store the last chapter each lineage was played (new state, save format) and score the gap since.

### SL-C2-13 (C, medium) ALG-54: empty-tier regions are not excluded

- Same function never reads the tier. An enemy-owned region of empty tier next to the player enters the pool (Reconquest, Assault and Containment all fire).
- Repro: `test_ALG_54_empty_tier_regions_are_excluded`: `assert (1, 2) not in {(1, 2), (1, 3), (1, 8)}`.
- Proposed piece (`csrc/mission.c`, same piece as SL-C2-11): skip `om_region_tier(w, idx) == OM_TIER_EMPTY`. Confidence: medium (an owned region of empty tier may not occur in play; check with a seeded run).

### SL-C2-14 (B, low) ALG-57: ties in the round-robin order and in the fill order

- `om_mission_apply_capacity_shortfall` and `om_mission_fill_counts` order types with an unstable selection sort. Equal counts come out in reverse index order: counts (2,2,6,0,0,0) at capacity 0.1 give (2,1,5,0,0,0), a stable index order gives (1,2,5,0,0,0); Python orders by first appearance in its unit list. Equal profile ratios have the same issue in the fill.
- Observation only (the tests use distinct counts and ratios). Proposed Q row: Q-NEW-ALG57-ties. Candidates: (a) lowest type index first; (b) fill order as Python; (c) leave and document.

## Not found wrong (checked, green)

ALG-56 (all ten base times and the limit equation), ALG-57 (enemy power by archetype class with the 25..70 population interpolation, base parity breakpoints, easy/hard/medium and the 0.75 floor, fill with the 1.15 rule, 20 percent shortfall), ALG-61 (id order, cap 4x base truncating the last hit, radius, friendly and other-layer exclusion), ALG-46 steps 1 to 4 apart from the delta, ALG-47 probabilities, score, unrelated and nemesis pools and search order, ALG-48 count away from integer boundaries and the 0.1 spread rule, ALG-49 lifespan range, the age test, regional succession and event attachment, ALG-51 categories (3528 chain cases, all lineage and regional cases), ALG-52 selection (five scenarios against a literal reference), ALG-53 dedup, word echo, first mention, seed determinism, no digits and word limits.
