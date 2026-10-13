# Mission choice against E-10 S-072 to S-074 (sim lane scout A)

Read on `origin/main` b64ff6d2, worktree `push/simlane-a`. Findings only: nothing under `csrc/`, `tests/`, `docs/bible/` or the ambiguity register was changed. Thresholds are Westley's.

## How it was run

- Command: `~/Projects/ouroboros-manifold/.venv/bin/python scripts/simlane/mission_choice.py --seeds 1-10 --missions 6 --n-regions 80`, then `scripts/simlane/mission_choice_report.py <raw json> <this file> <sha>`. Raw rows (every candidate list and input) are in `mission_choice_raw.json` beside this file.
- **n_regions is 80, not the briefed 60.** A pinned count of 60 fails `set_seed` (`generation failed`) for all ten seeds; counts up to 65 failed for every seed tried (seeds 1 to 3) and 66 to 72 failed for some (the feasible minimum, Q-021-07, depends on the rolled templates). 80 is the client's `DEFAULT_N_REGIONS` (`autoload/c_bridge.gd:23`). Features are `[0..7]`, faction 0, `era_kind` 0.
- Per campaign: `set_seed`, then six times: `mission_start`, `snapshot`, `objective_complete` on every objective at 1.0, `mission_end`, `jump 50`. The pipe is the debug pipe (`pipe/ouroboros_pipe_dbg`) through `scripts/simviewer/pipe_session.py`; its `mission` frame and `snapshot` frames are the ground truth.
- The pipe shows no candidate pool, no previous owners, no lineage rows. `tests/csim/conftest.py` binds the C API that does (`om_mission_candidates`, `om_mission_compute_urgency/relevance`, `om_region_previous_owner`, `om_lineage_*`), so a ctypes replica of the pipe handlers (`handle_set_seed`, `handle_mission_start`, `handle_objective_complete`, `handle_mission_end`, `handle_jump`) runs the same campaign on `libouroboros_dbg.so` and is cross-checked per mission against the pipe: **60 of 60 missions identical in tick, world checksum, region, archetype and `quiet_world`**, so the replica's pool reads are the pool the pipe drew from. (The replica binds the same symbols directly, not through `conftest.py`, because importing `conftest.py` runs `make` and unlinks the libraries on a failed build.)
- Independent recomputation is Python from the pipe snapshot (fields, composites, edges, stance, telegraphs). Two models: **V_C** takes the C pool's membership and recomputes urgency, relevance, preference, score and the top 5 per ALG-55 (arithmetic check). **V_R** rebuilds the pool from the R-073-01 trigger table as written, with the inputs the world can supply, and the relevance with the lineage run-count as R-072-03 words it (rule check). Containment and Counterinsurgency cannot be built in V_R (the world keeps no colonization or revolt log), shown as `?`.
- The genuine pick is the generator's draw (`om_mission_generator_run` at the end of the previous jump). The table shows both the drawn pair and the pair the pipe finally showed (they differ when the pipe's zero-force scan overrides, SL-A-01).

## Result

| Check | Result |
|---|---|
| Missions checked | 60 (10 seeds x 6) |
| Replica == pipe (tick, checksum, region, archetype, quiet_world) | 60 / 60 |
| `quiet_world = true` (simulation-health warning, architecture.md) | **0 / 60** |
| Pool candidates checked, urgency recomputed from the snapshot equals the C value | 797 / 797 (max abs diff 0.0) |
| Drawn pair inside the top 5 by the C's stored scores (R-072-05) | 60 / 60 |
| Drawn rank among top 5 (1 to 5) | 1:13, 2:17, 3:15, 4:7, 5:8; expected rank-1 count under the weighted draw 15.1, observed 13 |
| Relevance recomputed equals the C value | 48 / 60 missions; the 12 that differ are the stale-lineage cases, SL-A-08 |
| Shown mission equals the generator's draw | 48 / 60; 12 overridden by the pipe's zero-force scan, SL-A-01 |
| Drawn pair inside the rule-literal (V_R) top 5 | 36 y, 18 n, 6 unevaluable (Containment) |
| Missions with no deviation at all (shown == drawn, in C top 5, fresh relevance, in V_R top 5 or unevaluable and not otherwise flagged) | 31 / 60 |

Chosen archetype counts (shown): Defensive Stand 12, Siege Breaking 19, Assault 12, Multi-Front Defense 6, Evacuation 5, Containment 6.
Never chosen in 60 missions: Reconquest, Suppression, Interception, Counterinsurgency. Pool entries over the 60 states by archetype (C): DS 173, SB 129, RC 0, AS 134, SU 1, MF 66, IN 0, EV 112, CT 182, CI 0.

## Every mission

Archetype codes: DS Defensive Stand, SB Siege Breaking, RC Reconquest, AS Assault, SU Suppression, MF Multi-Front Defense, IN Interception, EV Evacuation, CT Containment, CI Counterinsurgency. `u`, `rel`, `score` are the C's stored values for the drawn pair; `u_R`, `rel_R` the rule-literal figures (lineage run-count included). Rule-expected is V_R's top 5, `region/archetype`. `match`: y = shown equals draw, draw in the C top 5 and in the V_R top 5, relevance fresh; otherwise the reasons.

| seed | m | tick | shown | drawn | u | rel | score | rank | pool | u_R | rel_R | rule-expected top 5 (V_R) | match |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 20 | 76/AS | 76/AS | 0.694 | 0.00 | 0.447 | 1 | 7 | 0.694 | 0.70 | 76/AS 57/SB 66/EV 74/EV 8/AS | n: stale-relevance |
| 1 | 2 | 70 | 66/DS | 76/DS | 0.771 | 0.70 | 0.696 | 1 | 13 | 0.771 | 0.70 | 76/SB 76/EV 71/AS 57/SB 57/EV | n: scan-override, not-in-rule-pool |
| 1 | 3 | 120 | 76/MF | 76/MF | 0.775 | 0.70 | 0.697 | 3 | 13 | 0.775 | 0.70 | 76/DS 76/SB 76/MF 76/IN 76/EV | y |
| 1 | 4 | 170 | 74/DS | 74/DS | 0.529 | 0.12 | 0.401 | 3 | 3 | 0.529 | 0.70 | 74/DS 74/IN 74/EV 66/AS | n: stale-relevance |
| 1 | 5 | 220 | 71/DS | 57/DS | 0.777 | 0.18 | 0.543 | 1 | 14 | 0.777 | 0.28 | 57/SB 57/EV 71/DS 74/EV 71/SB | n: scan-override, not-in-rule-pool |
| 1 | 6 | 270 | 57/CT | 57/CT | 0.776 | 0.18 | 0.542 | 5 | 6 | 0.776 | 0.18 | 66/SB 66/EV 57/AS 5/AS | ? (archetype not evaluable by V_R; C checks y) |
| 2 | 1 | 50 | 77/AS | 77/AS | 0.769 | 0.00 | 0.484 | 5 | 11 | 0.769 | 0.70 | 77/AS 75/DS 75/SB 75/MF 75/IN | n: stale-relevance |
| 2 | 2 | 100 | 67/SB | 67/SB | 0.763 | 0.24 | 0.554 | 2 | 11 | 0.763 | 0.24 | 67/DS 67/SB 67/IN 67/EV 75/AS | y |
| 2 | 3 | 150 | 67/AS | 67/AS | 0.409 | 0.24 | 0.377 | 2 | 3 | 0.409 | 0.34 | 77/DS 77/IN 77/EV 67/AS | y |
| 2 | 4 | 200 | 67/DS | 67/DS | 0.771 | 0.24 | 0.557 | 3 | 20 | 0.771 | 0.24 | 77/AS 71/AS 67/SB 67/DS 67/IN | y |
| 2 | 5 | 250 | 77/AS | 77/AS | 0.779 | 0.70 | 0.700 | 1 | 3 | 0.779 | 0.90 | 77/AS | y |
| 2 | 6 | 300 | 0/SB | 3/DS | 0.080 | 0.64 | 0.332 | 3 | 3 | 0.080 | 0.74 | 77/AS | n: scan-override, not-in-rule-pool |
| 3 | 1 | 44 | 62/EV | 62/EV | 0.775 | 0.00 | 0.488 | 4 | 23 | 0.775 | 0.70 | 62/DS 62/SB 62/IN 62/EV 68/SB | n: stale-relevance |
| 3 | 2 | 94 | 62/SB | 62/SB | 0.769 | 0.70 | 0.695 | 2 | 31 | 0.769 | 0.70 | 62/EV 62/SB 74/EV 68/EV 76/EV | y |
| 3 | 3 | 144 | 62/SB | 62/SB | 0.769 | 0.70 | 0.695 | 2 | 27 | 0.769 | 0.80 | 62/SB 62/EV 74/SB 74/EV 76/SB | y |
| 3 | 4 | 194 | 67/DS | 62/DS | 0.770 | 0.70 | 0.695 | 1 | 30 | 0.770 | 0.70 | 62/SB 62/EV 68/SB 75/SB 68/EV | n: scan-override, not-in-rule-pool |
| 3 | 5 | 244 | 71/DS | 62/DS | 0.760 | 0.70 | 0.690 | 1 | 25 | 0.760 | 0.80 | 62/SB 68/SB 75/SB 71/SB 68/EV | n: scan-override, not-in-rule-pool |
| 3 | 6 | 294 | 62/SB | 62/SB | 0.676 | 0.70 | 0.648 | 2 | 27 | 0.676 | 0.90 | 62/SB 62/EV 68/SB 74/DS 74/SB | y |
| 4 | 1 | 45 | 73/SB | 73/SB | 0.768 | 0.00 | 0.484 | 2 | 15 | 0.768 | 0.70 | 73/DS 73/SB 73/IN 73/EV 70/SB | n: stale-relevance |
| 4 | 2 | 95 | 73/AS | 73/AS | 0.779 | 0.70 | 0.700 | 1 | 7 | 0.779 | 0.70 | 73/AS 74/SB 70/AS 74/EV 29/AS | y |
| 4 | 3 | 145 | 0/SB | 3/DS | 0.133 | 0.18 | 0.221 | 3 | 3 | 0.133 | 0.18 | 74/AS | n: scan-override, not-in-rule-pool |
| 4 | 4 | 195 | 74/CT | 74/CT | 0.777 | 0.24 | 0.561 | 2 | 3 | 0.777 | 0.24 | 74/AS | ? (archetype not evaluable by V_R; C checks y) |
| 4 | 5 | 245 | 0/SB | 74/DS | 0.768 | 0.24 | 0.556 | 2 | 5 | 0.768 | 0.24 | 73/AS 74/SB 74/EV 29/AS | n: scan-override, not-in-rule-pool |
| 4 | 6 | 295 | 74/CT | 74/CT | 0.775 | 0.24 | 0.559 | 2 | 3 | 0.775 | 0.34 | 74/AS | ? (archetype not evaluable by V_R; C checks y) |
| 5 | 1 | 31 | 77/DS | 77/DS | 0.757 | 0.00 | 0.478 | 5 | 22 | 0.757 | 0.70 | 77/DS 77/SB 77/IN 77/EV 79/DS | n: stale-relevance |
| 5 | 2 | 81 | 68/DS | 77/DS | 0.780 | 0.70 | 0.700 | 1 | 17 | 0.780 | 0.80 | 77/SB 77/EV 79/DS 68/DS 79/SB | n: scan-override, not-in-rule-pool |
| 5 | 3 | 131 | 79/AS | 79/AS | 0.779 | 0.24 | 0.561 | 3 | 11 | 0.779 | 0.24 | 77/AS 79/AS 68/SB 68/EV 69/AS | y |
| 5 | 4 | 181 | 77/EV | 77/EV | 0.769 | 0.70 | 0.695 | 4 | 16 | 0.769 | 0.70 | 77/DS 77/SB 77/IN 77/EV 68/DS | y |
| 5 | 5 | 231 | 77/SB | 77/SB | 0.765 | 0.70 | 0.692 | 2 | 21 | 0.765 | 0.70 | 77/EV 77/SB 68/DS 78/AS 79/AS | y |
| 5 | 6 | 281 | 79/AS | 79/AS | 0.771 | 0.24 | 0.557 | 5 | 15 | 0.771 | 0.34 | 77/DS 77/SB 77/EV 77/IN 68/DS | n: rule-rank>5 |
| 6 | 1 | 22 | 75/MF | 75/MF | 0.752 | 0.00 | 0.476 | 3 | 8 | 0.752 | 0.70 | 75/DS 75/SB 75/IN 75/EV 68/AS | n: stale-relevance, not-in-rule-pool |
| 6 | 2 | 72 | 68/AS | 68/AS | 0.782 | 0.18 | 0.545 | 5 | 14 | 0.782 | 0.18 | 75/AS 62/SB 62/EV 68/AS 67/SB | y |
| 6 | 3 | 122 | 75/EV | 75/EV | 0.767 | 0.70 | 0.694 | 3 | 10 | 0.767 | 0.70 | 75/SB 75/EV 62/DS 62/SB 62/IN | y |
| 6 | 4 | 172 | 75/EV | 75/EV | 0.766 | 0.70 | 0.693 | 3 | 9 | 0.766 | 0.80 | 75/EV 75/SB 62/EV 68/AS 62/SB | y |
| 6 | 5 | 222 | 68/AS | 68/AS | 0.775 | 0.18 | 0.542 | 2 | 12 | 0.775 | 0.28 | 75/AS 66/EV 68/AS 66/MF 67/AS | y |
| 6 | 6 | 272 | 74/DS | 74/DS | 0.767 | 0.00 | 0.484 | 4 | 13 | 0.767 | 0.70 | 74/DS 74/SB 74/IN 74/EV 65/AS | n: stale-relevance |
| 7 | 1 | 24 | 74/CT | 74/CT | 0.480 | 0.00 | 0.340 | 3 | 3 | 0.480 | 0.70 | 74/AS 69/DS 69/IN 69/EV | n: stale-relevance |
| 7 | 2 | 74 | 0/SB | 62/DS | 0.778 | 0.24 | 0.561 | 1 | 9 | 0.778 | 0.24 | 62/SB 62/EV 69/AS 79/AS 74/AS | n: scan-override, not-in-rule-pool |
| 7 | 3 | 124 | 73/CT | 73/CT | 0.780 | 0.24 | 0.562 | 5 | 7 | 0.780 | 0.34 | 74/SB 74/EV 73/AS 62/AS 69/EV | ? (archetype not evaluable by V_R; C checks y) |
| 7 | 4 | 174 | 74/SB | 74/SB | 0.765 | 0.70 | 0.693 | 2 | 8 | 0.765 | 0.80 | 74/SB 74/DS 74/IN 74/EV 73/AS | y |
| 7 | 5 | 224 | 0/SB | 2/DS | 0.081 | 0.18 | 0.194 | 3 | 3 | 0.081 | 0.18 | 69/AS | n: scan-override, not-in-rule-pool |
| 7 | 6 | 274 | 74/AS | 74/AS | 0.778 | 0.70 | 0.699 | 1 | 2 | 0.778 | 0.70 | 74/AS 69/DS 69/IN | y |
| 8 | 1 | 43 | 77/AS | 77/AS | 0.776 | 0.00 | 0.488 | 1 | 13 | 0.776 | 0.70 | 77/AS 63/SB 63/EV 74/SB 74/EV | n: stale-relevance |
| 8 | 2 | 93 | 63/SB | 63/SB | 0.766 | 0.24 | 0.555 | 4 | 14 | 0.766 | 0.24 | 77/AS 63/DS 63/SB 63/MF 63/IN | y |
| 8 | 3 | 143 | 77/SB | 77/SB | 0.774 | 0.70 | 0.697 | 2 | 30 | 0.774 | 0.80 | 77/SB 77/EV 64/SB 63/SB 69/SB | y |
| 8 | 4 | 193 | 77/MF | 77/MF | 0.767 | 0.70 | 0.694 | 3 | 17 | 0.767 | 0.70 | 77/SB 77/DS 77/IN 77/EV 63/SB | n: not-in-rule-pool |
| 8 | 5 | 243 | 63/DS | 63/DS | 0.774 | 0.24 | 0.559 | 4 | 21 | 0.774 | 0.24 | 77/SB 77/EV 63/SB 69/SB 63/DS | y |
| 8 | 6 | 293 | 77/SB | 77/SB | 0.771 | 0.70 | 0.696 | 2 | 22 | 0.771 | 0.90 | 77/SB 77/EV 69/SB 74/SB 69/DS | y |
| 9 | 1 | 26 | 62/AS | 62/AS | 0.747 | 0.00 | 0.474 | 4 | 13 | 0.747 | 0.70 | 62/AS 59/SB 59/EV 75/SB 75/EV | n: stale-relevance |
| 9 | 2 | 76 | 62/MF | 62/MF | 0.776 | 0.70 | 0.698 | 3 | 31 | 0.776 | 0.70 | 62/DS 62/SB 62/IN 62/EV 75/AS | n: not-in-rule-pool |
| 9 | 3 | 126 | 75/CT | 75/CT | 0.774 | 0.24 | 0.559 | 5 | 11 | 0.774 | 0.24 | 62/SB 62/EV 75/AS 77/AS 59/SB | ? (archetype not evaluable by V_R; C checks y) |
| 9 | 4 | 176 | 62/SB | 62/SB | 0.776 | 0.70 | 0.698 | 2 | 19 | 0.776 | 0.70 | 62/SB 62/EV 75/MF 70/AS 59/AS | y |
| 9 | 5 | 226 | 59/DS | 62/DS | 0.769 | 0.70 | 0.695 | 1 | 19 | 0.769 | 0.70 | 62/SB 62/EV 75/SB 75/MF 77/SB | n: scan-override, not-in-rule-pool |
| 9 | 6 | 276 | 77/SB | 77/SB | 0.777 | 0.24 | 0.560 | 5 | 20 | 0.777 | 0.34 | 62/SB 62/EV 77/SB 75/DS 75/SB | y |
| 10 | 1 | 47 | 77/EV | 77/EV | 0.773 | 0.00 | 0.487 | 4 | 9 | 0.773 | 0.70 | 77/DS 77/SB 77/IN 77/EV 66/DS | n: stale-relevance |
| 10 | 2 | 97 | 77/MF | 77/MF | 0.774 | 0.70 | 0.697 | 3 | 10 | 0.774 | 0.70 | 77/EV 77/DS 77/SB 77/IN 66/DS | n: not-in-rule-pool |
| 10 | 3 | 147 | 77/MF | 77/MF | 0.757 | 0.70 | 0.689 | 3 | 10 | 0.757 | 0.80 | 77/DS 77/SB 77/IN 66/EV 66/DS | n: not-in-rule-pool |
| 10 | 4 | 197 | 66/DS | 77/DS | 0.750 | 0.70 | 0.685 | 1 | 7 | 0.750 | 0.70 | 77/SB 66/DS 66/SB 66/IN 56/AS | n: scan-override, not-in-rule-pool |
| 10 | 5 | 247 | 77/SB | 77/SB | 0.757 | 0.70 | 0.689 | 2 | 13 | 0.757 | 0.70 | 77/SB 66/SB 64/SB 76/DS 76/IN | y |
| 10 | 6 | 297 | 77/SB | 77/SB | 0.757 | 0.70 | 0.688 | 2 | 12 | 0.757 | 0.80 | 77/SB 66/SB 64/MF 64/DS 64/SB | y |

## Findings ledger

Confidence is about the facts shown, not about what Westley rules. Every fix is a piece to be built only after he reads the row. `repro` is `~/Projects/ouroboros-manifold/.venv/bin/python scripts/simlane/mission_choice.py --seeds S --missions K --out DIR` (about 9 seconds for all ten seeds) and the row `seed S, m K` of `mission_choice_raw.json`.

**SL-A-01. The pipe replaces a drawn mission that fields no enemy, silently (high).**
- Rule: R-072-05 "one weighted draw proportional to score picks the mission"; R-072-07/08 name one fallback only, the quiet-world Defensive Stand, flagged `quiet_world`; R-074-01 "given an archetype driven by an attack, enemy power is the attacker's committed budget x 300".
- Sim: 12 of 60 shown missions (20%) are not the generator's draw (seed/mission 1/2, 1/5, 2/6, 3/4, 3/5, 4/3, 4/5, 5/2, 7/2, 7/5, 9/5, 10/4). All 12 draws were Defensive Stand with zero committed attack budget, so enemy power was 0 (`drawn_enemy_power` 0.0 in the raw rows); `handle_mission_start` (`csrc/pipe/om_pipe.c:1314-1347`, comment "Never compose a zero-unit mission silently") then scans archetype 0 to 9 against the player's regions in index order and shows the first that fields both sides. 5 of the 12 shown missions are in no pool at all (2/6, 4/3, 4/5, 7/2, 7/5), e.g. a Siege Breaking on region 0; `quiet_world` stays false. 12 of the 17 Defensive Stand draws (71%) were overridden.
- Seed and tick: first seen seed 1 m2 (tick 70, drawn 76/DS, shown 66/DS); a pool-less one seed 4 m3 (tick 145, drawn 3/DS, shown 0/SB).
- Repro: `--seeds 4 --missions 3`, row seed 4 m3 (`scan_used` true).
- Proposed fix: piece SIM-A-MC1, owner rows `csrc/mission.c` (SL-A-02 trigger fix removes the cause), `csrc/pipe/om_pipe.c` (drop or surface the scan), `docs/architecture.md`, test files for S-072/S-073 (test writer first). Surfacing it in the `mission` frame is a contract change and its own piece (`docs/architecture.md` frame, `autoload/c_bridge.gd`). Needs Westley's ruling first (Q-A2 below).
- Confidence: high on the facts, medium on the right remedy.

**SL-A-02. The Defensive Stand trigger fires on any hostile neighbour, without an attack (high).**
- Rule: R-073-01 "player region targeted by an enemy attack this window"; `simulation/mission_generator.py:80-95` (the equations source) returns false without an attack in the action log.
- Sim: `om_mission_trigger_fires` case `OM_MISSION_ARCH_DEFENSIVE_STAND` (`csrc/mission.c:558-561`) is `has_hostile_neighbor(w, r, 0.0) || attacks > 0`. Of 173 Defensive Stand pool entries over the 60 states, 110 (64%) have no pending attack against the region; Defensive Stand is the most common pool archetype (173 of 797 entries, 21.7%). With no attack the committed budget is 0, enemy power is 0 and SL-A-01 follows.
- Seed and tick: every mission; first: seed 1 m1 (tick 20), 2 of its 2 Defensive Stand entries have no attack.
- Repro: as SL-A-01, field `analysis.ds_pool_no_attack`.
- Proposed fix: piece SIM-A-MC2, `csrc/mission.c` (the one `case`), `tests/csim/test_E10_S073_*` (positive control: a quiet border region produces no Defensive Stand; an attacked one does).
- Confidence: high that the code departs from the rule text; the remedy follows the rule.

**SL-A-03. Interception can never enter the pool (high).**
- Rule: R-073-01 "enemy attack declared against a player region, force in transit"; legacy `trigger_interception` (`mission_generator.py:203-225`): an attack whose attacker owns no region adjacent to the target.
- Sim: the C case adds `!om_mission_has_hostile_neighbor(w, r, 0.0)` (`csrc/mission.c:604-607`): it fires only for a region with no hostile neighbour at all, which an attacked border region seldom is. Interception pool entries over the 60 states: **0**. Player regions with a pending attack in those states: 63; of them 10 have an attacker owning no adjacent region (the legacy meaning), where the pool should hold an Interception.
- Seed and tick: first: seed 2 m1 (tick 50), regions [75] attacked from a non-adjacent attacker, no Interception in a pool of 11.
- Repro: field `analysis.legacy_interception_regions`.
- Proposed fix: piece SIM-A-MC3, `csrc/mission.c` (the one `case`) and `tests/csim/` (positive control: a telegraphed attack from a non-adjacent faction yields Interception).
- Confidence: high that it never fires; medium on the exact intended condition (the rule table gives "force in transit" only).

**SL-A-04. Multi-Front Defense counts hostile neighbour regions, not distinct attacking factions (medium).**
- Rule: R-073-01 "player region attacked by two or more factions this window"; legacy `trigger_multi_front_defense` (`mission_generator.py:184-200`): the union of attacker faction ids and owners of hostile neighbours above military 50, at least 2 distinct.
- Sim: `csrc/mission.c:588-603` counts neighbouring regions (two regions of one faction count twice) and adds 1 for any attack. Of 66 Multi-Front pool entries, 17 (26%) have fewer than 2 distinct threat factions (legacy reading), and 52 (79%) have fewer than 2 distinct attacking factions among pending attacks (the rule read literally; the world keeps no attack log, SL-A-11).
- Seed and tick: 6 shown Multi-Front missions, e.g. seed 6 m1 (tick 22, 75/MF, not in the rule-literal pool).
- Repro: field `analysis.mf_lt2_distinct_sources`.
- Proposed fix: piece SIM-A-MC4, `csrc/mission.c` (the one `case`), `tests/csim/` (two regions of one faction: no Multi-Front; two factions: yes).
- Confidence: medium (the rule text and the legacy differ on whether neighbours count).

**SL-A-05. Siege Breaking ignores "held long enough" (medium).**
- Rule: R-073-01 "player region with a hostile neighbor above military 50, held long enough, own military <= 40 or economy <= 40"; legacy `trigger_siege_breaking` requires `current_tick - held_since >= config.SIEGE_BREAKING_MIN_TICKS` (200, `simulation/config.py:670`).
- Sim: `OM_MISSION_SIEGE_MIN_HELD_TICKS 200` is defined (`csrc/mission.c:146`) and never read; the trigger has no held-time test. Of 129 Siege pool entries, 126 are in regions held for fewer than 200 ticks (confounded: these campaigns end at tick <= 300, so most regions are young). Siege Breaking is the most chosen archetype, 19 of 60 (32%).
- Seed and tick: every Siege mission; seed 3 m2 and m3 (ticks 94, 144) pick the same region twice.
- Repro: field `analysis.siege_held_lt_200`.
- Proposed fix: piece SIM-A-MC5, `csrc/mission.c` (the `case`, using `om_region_held_since`), `tests/csim/`. "Long enough" has no number in the bible, see Q-A3.
- Confidence: medium.

**SL-A-06. Containment fires on the faction's archetype alone (medium).**
- Rule: R-073-01 "hostile faction expanding along the player's border, two or more colonizations"; legacy `trigger_containment` (`mission_generator.py:251-270`): at least `CONTAINMENT_EXPANSION_THRESHOLD` conquests by that faction in the window.
- Sim: `csrc/mission.c:615-623` fires for any region of a Conqueror, Warlord or Opportunist faction adjacent to the player unless `recent_revolt_events >= 2` supplies it (never set, SL-A-07). 182 of 797 pool entries (22.8%) are Containment; 6 were shown. No colonization count is reachable to check the rule: `om_time_jump_report.n_colonizations` is never filled (SL-A-12).
- Seed and tick: seed 1 m6 (tick 270, 57/CT), seed 4 m4 and m6.
- Repro: field `analysis.contain_c_pool`.
- Proposed fix: piece SIM-A-MC6 after Q-A1 is ruled (needs an event/colonization record the world does not keep): `csrc/mission.c`, `csrc/faction.c` or `csrc/events.c` for the record (their owners to be named in `pieces.toml`), `tests/csim/`.
- Confidence: medium (unverifiable without the log; arithmetic of the firing condition is certain).

**SL-A-07. Counterinsurgency is structurally unreachable and the urgency chain term is always 0 (high).**
- Rule: R-073-01 "player region with an active revolt chain"; R-072-02 `chain = min(1, 0.3 x recent revolt events in the region)`, weight 0.2 in urgency.
- Sim: both read `region_ctx.recent_revolt_events`, written only by `om_mission_set_revolt_events`, which has no caller outside `csrc/mission.c` (`om_mission_refresh_context` says "Revolt events ... have no persistent source, so they stay unset", `csrc/mission.c:2197-2200`). Counterinsurgency pool entries over 60 states: 0. The chain term was 0 for every one of the 797 pool candidates. Reconquest, Suppression, Counterinsurgency and Interception were never chosen (Reconquest 0 and Suppression 1 pool entries in total: no player region lost in these campaigns, so those two are unverified, not defective).
- Seed and tick: all.
- Repro: field `analysis.c_pool_by_arch`.
- Proposed fix: piece SIM-A-MC7, owner rows `csrc/events.c` (record of revolt chains by region and tick) and `csrc/generational.c` (feed `om_mission_set_revolt_events` in the generator run), `tests/csim/`; depends on Q-A1.
- Confidence: high.

**SL-A-08. Relevance is computed from a stale or missing lineage (high).**
- Rule: R-072-03 lineage 1.0 if a lineage member lives in the region, proximity from the lineage home; the mission offered must be weighted toward "where I belong" (S-072).
- Sim: `om_mission_generator_run(w)` runs before `om_character_selector_run(w)` in the same jump (`csrc/generational.c:2141-2142`). On the opening jump no lineage exists when the pool is scored, so **mission 1 of all 10 campaigns has relevance 0.0 for every candidate** (rule value 0.7 for the commander's home region); after a commander rotation the pool carries the previous lineage's relevance (seed 1 m4, seed 6 m6). 12 of 60 missions affected (1/1, 1/4, 2/1, 3/1, 4/1, 5/1, 6/1, 6/6, 7/1, 8/1, 9/1, 10/1); the top-5 set itself changes in 4 (1/1, 2/1, 5/1, 6/6). `mission_start` refreshes the context afterwards but does not rescore the pool.
- Seed and tick: seed 1 m1 tick 20 (all relevance 0.0, region 76 is the commander's home).
- Repro: field `analysis.stale_relevance_regions`.
- Proposed fix: piece SIM-A-MC8, `csrc/generational.c` (swap the two calls, or rebuild the pool once the selector has run). Either changes the random stream after each jump, so the determinism goldens (`tests/long/`) and any trace fixture are regenerated in the same piece, and Westley sees the new traces first.
- Confidence: high.

**SL-A-09. The archetype-fit term of relevance is never fed (medium).**
- Rule: R-072-03 `fit = min(1, times the lineage has run this archetype / 3)`, weight 0.3.
- Sim: `om_mission_refresh_context` passes `times_run = 0` ("Lineage archetype history is not exposed", `csrc/mission.c:2197-2200`, `csrc/mission.c:2261`). In 19 missions (excluding the stale ones) the drawn pair's relevance is lower than the rule gives by 0.1 to 0.2 because the lineage had already run that archetype one to three times; the term never raises a repeated archetype's score. (Repeats are common: Siege Breaking was drawn in consecutive missions in several campaigns.)
- Seed and tick: e.g. seed 2 m5 (tick 250, 77/AS: rule relevance 0.9, C 0.7).
- Repro: raw rows `analysis.chosen_R` against `analysis.chosen_C`.
- Proposed fix: piece SIM-A-MC9, a per-lineage archetype run count in `gen_state` (`csrc/generational.c`, save format version bump, a contract piece first: `csrc/ouroboros_sim.h`/`signatures.toml` if an accessor is public), `csrc/mission.c` reads it.
- Confidence: medium (where the count lives is a design call, Q-A4).

**SL-A-10. Archetype preference is constant 0.5 (medium).**
- Rule: R-072-04 "0.1 for an archetype the player marked rare, else the player's weight, default 0.5".
- Sim: `om_mission_set_preference` has no caller outside `csrc/mission.c`; the onboarding `rare_marks` are saved and validated (`csrc/generational.c:392,528,1628`) but never read into the generator. Preference was 0.5 for all 797 pool candidates; a rare mark cannot change a mission offer in play.
- Seed and tick: all.
- Repro: field `c_pool` preference in the replica (`Sim.pool()` fifth column), or any row `analysis.vc.max_ds` against the 0.5 constant.
- Proposed fix: piece SIM-A-MC10, `csrc/generational.c` (apply `rare_marks` of the active onboarding slot to `om_mission_set_preference` at campaign start and on slot update), `tests/csim/` (positive control: marking Siege rare lowers its score by 0.08).
- Confidence: medium (the onboarding screen's production path is in another epic; check that nothing outside the C writes it).

**SL-A-11. "Recent" and "this window" are, in the sim, only the pending telegraphs and an unwindowed loss count (medium).**
- Rule: R-072-02 "recent attacks", "adjacent regions lost"; R-073-01 "this window" (attack, conquest, breakaway, colonization).
- Sim: attacks are `om_pending_telegraphs` (an attack stays pending 3 ticks, `declared_tick + 3`); at the moment of choice the oldest pending telegraph is 2 ticks old in 58 of 60 states, so a 50-tick jump's earlier attacks are invisible. "Adjacent regions lost" counts any neighbour whose previous owner was the player, however long ago (`csrc/mission.c:2222`). The world keeps no attack, conquest, revolt or colonization log (`csrc/mission.c:545-547` says so).
- Seed and tick: all.
- Repro: field `analysis.telegraph_age_max`.
- Proposed fix: none until Q-A1 is ruled; then `csrc/events.c` or a new `csrc/world_log.c` (new file) for the record, `csrc/mission.c` reads it.
- Confidence: medium.

**SL-A-12. `om_time_jump_report` event counters are never filled (low, relevant to lane step 2).**
- Rule: the header documents `n_conquests`, `n_colonizations`, `n_revolts`, `n_faction_births`, `n_faction_deaths` (`csrc/ouroboros_sim.h` `om_time_jump_report`).
- Sim: `gen_time_jump` sets `start_tick`, `end_tick`, `jump_ticks`, `n_territory_changes`, `n_chronicle_entries`, `n_snapshots` only (`csrc/generational.c`, end of the function). Over the 50 replica jumps the five counters were 0 every time while `n_territory_changes` was 8 to 12.
- Seed and tick: every jump.
- Repro: raw rows `prev_jump`.
- Proposed fix: piece SIM-A-MC11, `csrc/generational.c` (fill from the tick events it already walks), `tests/csim/`.
- Confidence: high on the fact; whether anything reads them is for the chronicle scout.

**SL-A-13. Snapshot `stance` rows omit the faction itself (low, doc).**
- Rule: `docs/architecture.md` snapshot example shows `"id":0 ... "stance":[3,1,2]` for three factions (n entries per row).
- Sim: `write_snapshot` skips `k == f` (`csrc/pipe/om_pipe.c:439`), so a row has n-1 entries and index b maps to `b if b < a else b - 1`. A consumer indexing by faction id reads the wrong faction (and the row for the last faction is one entry too short for an index by faction id).
- Seed and tick: every snapshot.
- Repro: `snapshot` after `set_seed`, `len(factions[i].stance)`.
- Proposed fix: piece SIM-A-MC12, `docs/architecture.md` only (describe the n-1 layout), unless the client reads it as n (then `autoload/c_bridge.gd` first look).
- Confidence: high.

## Proposed Q- rows (not added to the register)

| id | story | question | candidates |
|---|---|---|---|
| Q-A1 | E-10 / S-072, S-073 | What is "recent" / "this window" for the R-072-02 inputs and the R-073-01 triggers (attack, conquest, breakaway, colonization, revolt), and where is that record kept? Today the world keeps only 3-tick pending telegraphs and the loss count has no window. | (a) the last jump (50 ticks): the sim keeps an event record per jump (attacks, conquests, revolts, colonizations, births) the generator reads; (b) the time since the previous mission, same record; (c) keep today's pending telegraphs and ever-lost count and rewrite the rule text to say so |
| Q-A2 | E-10 / S-072, S-074 | A drawn candidate whose enemy has no power (a Defensive Stand with no attacker) cannot field a mission. The pipe now picks another by scanning. What should happen? | (a) it cannot occur once Defensive Stand needs an attack (SL-A-02) and the scan is removed; (b) redraw from the rest of the top 5; (c) treat as the quiet-world fallback with the `quiet_world` warning |
| Q-A3 | E-10 / S-073 | "Held long enough" for Siege Breaking has no number in the bible. | (a) 200 ticks as in the legacy config (`SIEGE_BREAKING_MIN_TICKS`); (b) a named draft value for Westley; (c) drop the clause |
| Q-A4 | E-10 / S-072 | Where does "times the lineage has run this archetype" live (R-072-03 fit)? | (a) a per-lineage counter in the generational state, saved; (b) derived from the ledger/chronicle record; (c) drop the fit term |

Already open and met here: Q-072-02 (R-072-06 cannot reach urgency 0.8 under R-072-02's weights). The R-072-06 control cannot be shown in play; not re-tested.

## What passed

- The replica of the pipe handlers reproduces the pipe exactly in 60 of 60 missions (checksum, tick, region, archetype, quiet_world).
- ALG-55 urgency: 797 of 797 pool candidates equal the independent Python value (deficit from the snapshot composites, border threat from stance and edges, attack pressure from telegraphs, loss count, chain 0), maximum difference 0.0.
- ALG-55 relevance matches in 48 of 60 missions; score = 0.5u + 0.3rel + 0.2pref matches wherever relevance matches; the weights and the 5-hop breadth-first proximity reproduce.
- R-072-05: the drawn pair is in the top 5 by stored score in 60 of 60 missions; the draw is spread over ranks as a weighted draw should (rank-1 expected 15.1, observed 13).
- R-072-01 candidate regions: 0 of 797 C pool entries lie outside "the player's regions and every region adjacent to them".
- `quiet_world`: 0 of 60. The R-072-07 retry and fallback path was not exercised, so the R-072-07/08 region and enemy re-derivation (`fallback_check` in the script) is untested by data.
- The commander lineage used by the C (`om_lineage_id_at(nl-1)`) equalled `om_campaign_lineage` and the snapshot's `lineage` in every state (yes).

## Unverified

- R-072-07/08 quiet-world fallback (never reached), R-072-06 (known open, Q-072-02).
- Reconquest, Suppression (almost no pool entries: the scripted player does not lose regions in 300 ticks) and Assault "scored as an attack target" (the C uses stance, adjacency and a weakness gate, not the player's attack scoring; the V_R model uses `om_faction_candidates` attack rows, so its Assault count is a weak reference).
- Containment and Counterinsurgency against the rule (no colonization or revolt record).
- Evacuation: the C also requires a hostile neighbour above military 50 (same as legacy, not in the rule table's words); 25 V_R-only Evacuation entries come from that. Left as a question for Westley, not counted as a defect.
- Whether the weighted draw uses `om_rng_draw` uniformly (not testable from outside; only the distribution above).
- Campaigns are six missions to tick 300 with an inactive player and `retention` untouched; longer campaigns, rotating lineages and lost regions are not covered.

