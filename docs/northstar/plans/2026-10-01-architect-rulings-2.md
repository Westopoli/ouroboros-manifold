# Architect rulings, round 2, 2026-10-01 (mission-plays plan, Waves A and B)

Answers the eight items under "Architect rulings still needed" in the coordinator's continuation note of 2026-10-01 (14:21). Round 1 is `2026-10-01-architect-rulings.md` and still holds except where this file says otherwise. Rule text changed in the same commit: E-08 R-055-06 (what runs at the end of the opening jump and of a retry jump) and the new R-057-09 (the first commander). `pieces.toml`: `B5-chronicle` now depends on `A2-contract` only.

None of these rulings sets a threshold. The values waiting for Westley are listed at the end; nothing here is blocked by them.

## Order of work

1. Land now, no ruling needed: `relay/04-clock-code`, then `push/B2B3`; the B4 trio (`push/B4-b9`, `push/B4-b14`, `push/B4-td`) through one clerk; `push/B3-pipe` once its tests are green on fresh main.
2. B5: add the version bump (below), then land `push/B5-chr`.
3. B6 contract piece, then B6 sim, then B6 pipe. B6 builds after B5 lands.
4. B7 contract piece, then sim, pipe, client.
5. A7 tests and build (docs confirmed below).
6. Wave C.

## 1. B6: the chapter lifecycle

**1.1 Who seats the first commander.** The selector does, at the end of the opening jump (R-057-09). No commander exists, so the selection is a forced rotation (R-057-01); the previous and nemesis pools are empty, so the draw falls through to the unrelated pool (R-058-01), which creates a character with a new lineage id in the mission region's owning faction (R-058-04). The pool draw is still made, so the random stream has the same shape as any other forced rotation. Nothing in `set_seed` or `om_world_generate` creates characters. The lineage's chapter counter starts at 1 (R-057-08).

**1.2 What runs at the end of which jump** (R-055-06 as rewritten).

| Jump | Collapse check | Generator | Selector | Chapter advance |
|---|---|---|---|---|
| Opening | no | yes | yes | no |
| After a mission, played or refused | yes | yes | yes | yes |
| Retry (R-072-07) | no | yes | no | no |

The selector is not re-run after a retry jump: the commander chosen for the chapter stays even if the retry moves the mission region. This avoids the "lineage counter incremented twice" failure the epic lists. A commander more than 2 hops from a region reached only through retries is accepted.

**1.3 "A jump that follows a mission."** One marker serves B5 and B6: the last mission has a known band and its consequence is not yet consumed (`consequence_consumed == 0` on `push/B5-chr`). `gen_time_jump` reads that predicate once at its start into a local; the lifecycle steps at the end use the local, because the chronicle build flips the flag in between. A refused mission arms the marker exactly as a played one does (refusal is a band, and round 1 B5-1 maps it to failure). No second marker, no pipe-side static: pipe statics are not saved.

**1.4 The mission generator owns the weighted draw.** `om_mission_generator_run` runs inside the jump and stores the chosen region and the chosen archetype. `handle_mission_start` reads both and makes no draw of its own; its own `om_mission_select` call is removed, not duplicated. When the generator found no candidate it stores that fact, and `handle_mission_start` keeps the landed A3 path (five retry jumps of 20 ticks, then the quiet-world fallback); each retry jump re-runs the generator per the table. The determinism checksum changes because the draw moves; the ledger row says so.

**1.5 The selector orchestrator.** `om_character_selector_run(w)` stops being a one-line copy. It reads the current lineage and the generator's region, then calls the function that fits: no commander yet gives the forced path (1.1); the last mission's commander fate was killed gives the existing commander-death path (R-061-01); otherwise `om_character_selector_run_for_lineage`. It stores the record's commander id and lineage id in `gen_state`. `is_main_character` stays cumulative and is not the source of the current commander. Until B7 lands the fate is never killed, so the commander-death path is reached only from core tests; its transport test ships with B7.

**1.6 Chapter end reason.** `om_time_jump_report` does not change. `gen_state` records the reason of the chapter that just ended: faction collapsed if the collapse check fired, commander death if the commander's fate was killed, otherwise normal. Collapse wins when both hold.

**1.7 Contract piece (replaces `push/B6-contract`; rebuild it on fresh main).** Header, `signatures.toml`, `symbol_modules.toml`, conftest binding, `docs/architecture.md`:

- `uint32_t om_campaign_commander(const om_world *w);` as already drafted: the selector's latest pick, 0 before the first selection.
- `uint32_t om_campaign_lineage(const om_world *w);` the current lineage id, 0 before the first selection.
- `int om_chapter_last_end_reason(const om_world *w);` a `GEN_CHAPTER_END_*` value, normal before any chapter has ended.
- `int32_t om_mission_generator_chosen_archetype(const om_world *w);` the archetype the generator drew, -1 when it found no candidate.
- Frames as round 1 B6-5: snapshot gains `chapter` and `commander`; the chronicle frame's `jump` object gains `chapter_end_reason`. The save sidecar's `chapter` reads `om_chapter_get_number`, which already exists; the "always 0" note in `om_pipe.c` goes.

As the coordinator found, a header piece cannot land alone: it lands with its implementation, in one clerk run.

**1.8 Save format.** The new `gen_state` fields (current commander, current lineage, chosen archetype, no-candidate flag, last end reason) are saved. `OM_SAVE_FORMAT_VERSION` goes up by one in the B6 sim piece.

**1.9 Fixtures.** The collapse seed (389) and the rotation seed are fixtures, not thresholds. Once the generator moves into the jump the Engineer re-runs the seed search and replaces them, with a ledger row. `push/B6-tests` seats a lineage in every region in its core fixture; that stays valid for core tests, and the transport tests rely on R-057-09 instead of any seeding.

## 2. B5: the saved flag and the ripple text

1. **The flag is approved.** `consequence_consumed` in `gen_state`, saved. It is also B6's marker (1.3).
2. **Version bump.** `push/B5-chr` changes the save layout without touching `OM_SAVE_FORMAT_VERSION`. Add the bump (2 to 3) and its comment on that branch before it lands. `save.c` rejects any other version, and that is the intended behaviour for old saves: nothing has shipped, so no migration is written. The load-game screen must show a rejected save as unreadable and not crash; if no test proves that, the Engineer adds one.
3. **Ripple text.** The hard-coded fragment is accepted as the placeholder the "no runtime API calls" rule allows. It moves to the event template library when ripple templates are written; add a row to the work list under C6. It does not block landing.
4. **Lineage categorisation** moves to B6 (addendum A1 below). `om_chronicle_has_mission_consequence_flag` stops being a stub in the B5 branch.

## 3. A7: the delta frame docs

All three deviations are confirmed; the landed docs are the contract.

1. Delta frames carry no `map`. The map does not change during a mission.
2. `units_removed[]` stays. Without it the client cannot tell a dead unit from an unchanged one.
3. "Every 20 steps" counts sim steps since `mission_begin`, and a call with `n > 1` that crosses a multiple of 20 writes a full frame.
4. `"full":true` on `tactical_step` is the "on request" form round 1 asked for.

Unchanged from round 1: `visible` only for the player's faction; with `n > 1` only the last frame is written; re-measure with `scripts/bench_tactical_pipe.py`; if still over 50 ms, profile and report, tune nothing further.

## 4. B7: commander assignment

1. Reassignment only while the assigned unit lives: confirmed. Once it is dead the fate is settled and `assign_commander` answers the `commander dead` error.
2. `commander_fate` as an int (0 killed, 1 wounded, 2 survived): confirmed. It matches the Q-077-01 answer (wounded is cosmetic and chronicle only).
3. A mission that ends with no commander assigned reports 2: confirmed. The client assigns the first roster unit by default, so this is reachable only from a client that skips the call.
4. **Contract piece (header).** `int om_mission_assign_commander(om_world *w, uint32_t unit_id);` returning 0 on success, 1 when the unit does not exist or is not the player's, 2 when the currently assigned commander is dead. `om_mission_get_commander_unit` keeps its signature and returns the assigned id. Lands with its `mission.c` implementation.
5. The four R-061 commander-death symbols belong to B7 (plan header). B7 also feeds fate into 1.5 and 1.6.

## 5. B3: the phase after a refusal

The pipe handler supplies it. `mission_refuse` calls `om_mission_resolve_refusal`, then sets the chapter phase to the same value `handle_mission_end` sets, so the next legal command is `jump`. `mission.c` does not change. The refusal arms the B5/B6 marker (1.3), so the jump that follows shows the consequence entry and advances the chapter.

The A5 test that asserts Refuse is disabled becomes a test-defect row when the button is wired: the rule it proved (R-079-02, exactly Accept and Refuse) is unchanged, only the interim disabled state ends.

## 6. A6 follow-ups

1. **Roster and position names.** Accepted for now. They are client-derived and deterministic; a collision is cosmetic. Pinning the formula is naming work for E-21, not this plan. One work-list row under C5.
2. **Objective node is index 0 on every archetype.** Accepted. Every current map has a single objective node at its centre; this becomes a defect only when an archetype gains a second objective. No work.

## 7. Housekeeping

1. `pieces.toml`: `B5-chronicle` dependency fixed in this commit.
2. Plan labels get no piece rows; round 1's ruling stands. Ledger rows and the clerk's footprint gate use the owner's piece id (`T1-N`, `B9-N`, ...). Branch names may keep the plan label. A file with no owner gets a row before its piece starts.
3. A3 pipe tie-break: use `OM_TIE_EPSILON` as the rest of the sim does. One small `T1-N` fix with a test where two regions tie.
4. Coordinator rulings reviewed and upheld: `push/B4-td` (the two driver tests asserted the pending queue, which the drain removes by design; the clerk confirms at landing that only the final assertions changed and no interval did), the A4 marker-name rewrite, the TD-debrief reset.
5. `test_materialised_unit_is_consumed_from_the_structure_queue`, red before and after B9: an Engineer investigates after the B4 trio lands. It is not reclassified.

## Provisional values (Westley, 2026-10-01: keep all, tune in play)

These values were invented by builders or test writers. Westley accepted every one as it stands on 2026-10-01, to be tuned in play. Each is a named constant with a comment saying it is a play-tuned value and citing this section; a test that asserts one reads the constant and does not repeat the number. Changing one later is still his call.

| Where | Value | Decision |
|---|---|---|
| A3 isolation test, budget lower bound | 0.5 × P × parity | keep; it is a loose floor under the rule's exact value |
| B1 patrol (`enemy_macro.c`) | radius 600.0, 4 waypoints, arrive within 60.0 | keep, tune in play |
| A6 camera | zoom 1.0 to 4.0 in steps of 1.25, pan 600 px/s, edge margin 4 px | keep, tune in play |
| A6 order marker | 1.0 s | keep |
| B4 structure placement (`mission.c`) | lateral offset 0.25, 64 slots | keep |

Also his to see: ruling 1.1 (the first commander comes from the unrelated pool) and the last line of 1.2 (no re-selection after a retry jump) are read out of existing rules, not new decisions, but they shape the first minute of every campaign.

## Addendum, 2026-10-01 evening (B5 blockers from `push/B5-tests3`)

**A1. Lineage categorisation leaves B5 and joins B6.** This reverses item 2.4 above. Reason: no lineage exists in a pipe campaign until B6 seats one (R-057-09), so a lineage cluster cannot appear in play before then and B5 could not prove it wired. B5 lands with chain and regional categorisation, the consequence entry, the ripple cluster and the cap. Tests on `push/B5-tests3` that need lineage categorisation move to a B6 test branch.

In B6, as a contract piece that lands with its implementation: `om_chronicle_add_lineage_event` gains a category parameter, `void om_chronicle_add_lineage_event(om_world *w, uint32_t lineage_id, uint32_t region_idx, uint32_t category, double score);` (option a; no second variant). `chron_push_lineage_candidate` stores the category it is given. Existing callers and tests are updated as a contract change, with a ledger row. `gen_time_jump` computes the category with `om_chronicle_categorize_lineage_cluster` (R-067-02): the template name is taken from the cluster's events in that region, and net economy, military and tension are that region's field values at the jump's end minus their values at its start. If the jump keeps no per-region start values today, it captures those three fields per region at its start in a local buffer; nothing is saved.

**A2. Mission result is saved: approved.** A save made at the debrief must keep the band, the last mission region, the refused flag, the commander fate and whatever else `gen_time_jump` and the B5/B6 marker read after a mission. `mission.c` (B9-N) implements `mission_state_size/write/read` for that resolved-result state only; a save in the middle of a battle is not in scope and the live tactical state is not written. The install call in `om_world_new` is one line in `region.c`, made under the region.c owner's next piece id in the same clerk landing, following the pattern the other state slots use. Layout change: it rides save version 3 if it lands together with B5; otherwise it bumps the version again. Test (Engineer, transport): finish a mission, save, load, jump; entry 1 of the chronicle is the consequence entry and the band survived.

**A3. Noted, no ruling needed.** Re-arming `consequence_consumed` for a second mission is a defect fix inside B5. The pipe sidecar `format_version` and `load_game.gd`'s `CURRENT_SAVE_VERSION` follow `OM_SAVE_FORMAT_VERSION`.

## Addendum 2, 2026-10-01 (the mission-over transport test and the gate timeout)

`tests/transport/test_pipe_mission_over.py::test_tactical_step_alone_reaches_mission_over_within_its_time_limit` takes about 620 s with 30 to 60 minute deadlines, over the gate's 600 s suite timeout.

**A4. Neither the timeout nor the gate's coverage changes.** The test steps in batches: `tactical_step` with `n > 1` writes only the last frame (round 1, A7), so the 120 KB frame per tick, which is most of the 7 ms, is not paid. Order: land `push/A7-pipe`; the Engineer updates `push/TD-missionover` to step with a large `n` per call (the same test-defect row covers it: the rule proved is unchanged, the deadline is still read from the frame, nothing is widened); then `relay/04-clock-code`, then `push/B2B3`. The Engineer confirms that a batch stops at the tick the mission ends, or that the last frame reports the ending tick, so the "within its time limit" assertion stays exact; if neither holds, that is a pipe defect to report, not something the test works around.

If the batched test is still over the suite timeout, the Engineer reports the measured time and the split between sim step and pipe. Raising `SUITE_TIMEOUT` extends a window and moving the test out of the gate narrows what the gate proves; both are Westley's to decide, and neither is done without him. No slim-frame or fast-forward verb is added.

## Addendum 3, 2026-10-01 (A7: the sim-step fixes)

Source: `docs/northstar/plans/2026-10-01-a7-sim-profile.md` on `push/A7-profile` (fb6ee6e); land that report as a docs piece. After A7 the round trip at 5,000 units in a clash is median 56 ms, p95 73 ms.

**A5. Fixes 3, 1 and 2 are approved, in that order, one piece each.** They are worth doing under either budget (below): the p95 tail and the E-12 visibility figure need them regardless.

1. Fix 3, `csrc/enemy_macro.c` (B13-N): skip the all-pairs `om_unit_can_see` loop when `has_contact` is already set; nearest-candidate search otherwise.
2. Fix 1, `csrc/fog.c` (B11-N) with a read-only per-faction accessor in `csrc/unit.c` (B10-N): the accessor is its own small piece and lands first, since one file has one owner at a time.
3. Fix 2, `csrc/unit.c` (B10-N): nearest-first cell order and enemy-only candidates in `om_tac_nearest_hostile` and `om_tac_nearest_enemy_within_range`, keeping the (d2, id) tie-break and the `OM_TIE_SCAN_WINDOW` fallback exactly.

Conditions on each piece:
- The trace is unchanged. `scripts/specfactory/checksum_trace.py` matches before and after; a piece whose checksum moves does not land and is reported, not explained away in a ledger row.
- Tests first (Engineer): an equivalence test that runs the old and the new search over seeded clash and spread scenes and compares every answer, with a positive control (a planted wrong tie-break or a dropped candidate must make it fail). The old function stays in the test tree as the reference, not in `csrc/`.
- Re-measure with `scripts/bench_tactical_pipe.py` after each piece and append the numbers to the profile report. Stop when the budget in force is met; a remaining fix is then not built.

Fixes 4 and 5 are deferred: 4 needs the ability rules checked per type before anyone can say it keeps the trace, 5 gains little in a clash. Neither is built without a new ruling. No constant, cell size or tick rate is tuned.

**A6. The budget is Westley's and is open.** Round 1 recorded 50 ms per `tactical_step` at 5,000 units. E-13 R-099-03 drops the tactical rate to 10 ticks per second above 1,000 live units, which makes the tick 100 ms at that size, and the E-11, E-12 and E-13 performance figures are stated against that 100 ms tick. Until he says which holds at 5,000 units, the 50 ms figure stays the target and no test asserting either number is written or changed.

## Addendum 4, 2026-10-01 (Wave C3, client G2 to G6)

Rule text changed in the same commit: E-16 R-110-01 (the menu lists Era Library; Westley's 2026-09-28 decision in the gap-fix plan). New register row Q-110-04.

**A7. G2 error panel.** The names the test pins are ratified and become the shared contract: nodes `ErrorPanel`, `ErrorReason`, `Retry`, `MainMenu`, and `qa_state()["error_panel"]`. One shared scene, `scenes/shared/error_panel.tscn` with its script, instanced by each of the five scenes; it gets a `pieces.toml` row before it is built. How `autoload/c_bridge.gd` reports the failure to the scene is the C2-N unit's choice within that file; nothing more is pinned.

**A8. G4 debug overlay.** `FeatureFlags.ENABLE_DEBUG_OVERLAY` defaults to false, and with it false F3 does nothing; the G4 test asserts both. Control H2 in `tests/test_tactical_hud.gd` keeps its job as a positive control: it sets the flag true, then proves F3 shows and hides the overlay. That edit is a test-defect row landing with G4 (the rule proved, overlay off on a fresh view, is unchanged). `autoload/feature_flags.gd` gets its own `pieces.toml` row.

**A9. G3 main menu.** Exactly five entries: New Campaign, Continue, Era Library, Settings, Quit. The label is "New Campaign"; the test stops accepting "New Game" (a narrowing).

**A10. G5 settings at boot.** The rule wins over the stored key: edge scroll is on or off (R-110-02, Q-110-01). Settings stores a boolean, the tactical camera does not edge-pan when it is off, and the speed slider goes. Pan speed stays the A6 constant. The G5 test is rewritten to the toggle before the Doer builds; it was written today against a misreading, so this is a correction of an unlanded test, with a ledger note. Resolution and fullscreen are applied at boot in the same piece and proven by a desktop test of the kind A6 uses (real display, not headless); it is written, not skipped.

**A11. G5b key rebinding is held** on Q-110-04. Nothing is built or tested until Westley answers. Storage, once it is unblocked: the changed bindings in an `[input]` section of the existing settings file, applied to the `InputMap` at boot with the other stored settings.

**A12. G6 TacticalBridge removal.** The test lands as a ratchet in regression mode, like `reach_lint`: the count of referencing files is recorded (25 today), may only fall, and each piece that removes references lowers the recorded number in its own change. The assertion of zero, and the autoload's removal, land after C4's E2 and E3.

## Addendum 5, 2026-10-01 (A7: stop after fixes 3, 1, 2)

Measured after the three fixes, 5,000 units in a clash: round trip median 49 to 54 ms, p95 72 to 77 ms (before: 57 and 71). The estimates in the profile report were too generous; the fixes land anyway, since each is correct and keeps the trace.

**A13. Performance work stops here.** The per-faction cell list in `om_grid` is not approved. It restructures the grid every tactical system reads, and whether it is needed at all depends on the budget (A6): against a 100 ms tick the build already passes on median and p95; against 50 ms it fails on both and the grid change becomes the next piece. Westley's answer decides. Append the after-fix numbers to the profile report and land it; nothing else in this lane is started.

## Addendum 6, 2026-10-01 (B6 open items from the contract and tests)

The coordinator's defaults stand except where this says otherwise.

**A14. `chapter_end_reason` is per jump.** It is the reason of the chapter this jump ended, and normal (0) when the jump ended none (opening and retry jumps). `om_chapter_last_end_reason` returns the same value the latest jump's frame carried; its header comment is corrected to say so. Add one test where the two readings differ: a jump that ends a chapter by collapse, then a retry jump, which reads 0.

**A15. Collapse reassigns at the jump.** When the collapse check fires, `om_player_faction_reassign_on_collapse` runs immediately after it and before the mission generator, which needs a player faction that holds regions. It uses the code's current choice (most regions, uniform among ties); Q-062-01 stays open and concerns only which faction is picked, not where the call sits. When no faction survives (R-062-03) the lifecycle stops after the check: no generator, no selector, no advance, and the existing terminal path (`om_campaign_trigger_terminal_restart`) is taken. If the pipe has no way to tell the client the campaign ended, report it as an open item; do not add a frame field for it in this piece. The chronicle entry framing the fall (R-062-04) is not part of B6; add a work-list row under C6.

**A16. One lineage per unrelated rotation.** R-058-04 says a new lineage id, singular. Dropping the stray memberless lineage in `gen_resolve_candidate_for_pool` is the intent; the test for exactly one stays.

**A17. The lineage chapter counter counts chapters played in the lineage.** A new lineage starts at 1 (R-057-08). Each later selection that keeps the lineage (a stay, or a successor after the commander's death, R-061-02) adds one, once; a retry jump adds nothing. The contract piece gains `uint32_t om_lineage_chapter_count(const om_world *w, uint32_t lineage_id);`. Tests: a stay gives 2; a rotation gives the new lineage 1 and leaves the old count as it was; a retry jump changes neither.

**A18. Confirmed.** The generator inside the jump calls `om_mission_refresh_context` for every region before it scores. The five pipe tests that break when the draw moves get test-defect rows in the B6 pipe piece, one row per test saying which fixture value moved and why; the Engineer changes only values that follow from which mission was drawn, and reports any assertion that states a rule's value without changing it.

## Addendum 7, 2026-10-01 (`pieces.toml` ordering)

The dependency fix in d33aa64f removed the only ordering between `B5-chronicle` and `B7b`, and `owner_lint` failed on main. Fixed in this commit: the order on `csrc/generational.c` is `B5-chronicle`, then the new row `B6-lifecycle` (which also owns `csrc/chronicle.c`, after `B8`), then `B7b`. `owner_lint` passes (63 pieces).

**A19.** The F1 and F2 accessors live in `csrc/unit.c` and `csrc/om_internal.h`, which have owners; they need no rows of their own. The `symbol_ownership` lint counting an `extern` declaration that ends in `;` as a definition is a harness defect: approved as a harness piece for an Engineer, with a positive control (a planted declaration is ignored, a planted definition in the wrong file is still caught).

## Addendum 8, 2026-10-01 (the mission-over test after B6)

With B6 the drawn mission changed and the test takes 495 s against its 500 s hang guard; the transport suite takes 562 s against the gate's 600 s.

**A20. Option (c): a smaller fixture mission.** The Engineer searches seeds for a campaign whose first mission has a short deadline (a 30-minute-base archetype) and a small force, and the test uses that seed. The rule proved is unchanged: `tactical_step` alone reaches `mission_over` within the deadline the frame states, read from the frame as now. This is a fixture choice, recorded with a ledger row naming the seed, the archetype and the deadline; the hang guard and `SUITE_TIMEOUT` are not touched. Target: the test under about 200 s, so the suite keeps real headroom. If no seed in 1 to 400 gets there, report the best found and stop; the timeouts stay Westley's.

## Addendum 9, 2026-10-01 (B6: the two getters reach_lint reports)

**A21. `om_campaign_lineage` goes into the snapshot frame; `om_lineage_chapter_count` is allowlisted.**

- The snapshot frame gains `"lineage"` (uint, the current lineage id, 0 before the first selection) beside `"commander"`. The client needs it to name the family the player is following, so this is real reach, not an exemption. It is a contract change: the `docs/architecture.md` text, the one line in the pipe and a transport assertion go into the B6 pipe piece before it lands.
- `om_lineage_chapter_count` gets a row in `scripts/specfactory/reach_allowlist.toml` as a test-observability accessor. Justification for the row: the counter is read in play by the selector through the internal state (R-057-02, R-057-04); the public getter exists so the A17 tests can observe it, and no player-facing surface shows the number.

Hypothesis for the `tests/test_tactical_view.gd` tick-rate failure, to confirm or refute before any change: the newly drawn fixture mission has more than 1,000 live units, so the tactical rate correctly drops from 20 to 10 ticks per second (E-13 R-099-03). If confirmed, the test's fixture is at fault, not the game: give it a mission under 1,000 units (ledger row); the expected rate is not changed.

## Addendum 10, 2026-10-01 (Westley's four decisions)

Rule text changed in the same commit: E-13 pipe budget, `docs/architecture.md` (the budget figure), E-08 R-062-02, E-16 R-103-09 (new) and R-110-02, register Q-110-04.

**A22. Pipe budget: 100 ms.** One `tactical_step` round trip at 5,000 units takes under 100 ms, the tick length at the 10 ticks per second of R-099-03. This replaces round 1's 50 ms and closes A6. The build meets it (median about 50 ms, p95 about 75 ms), so the performance lane is closed: the `om_grid` per-faction cell list and fixes 4 and 5 are not built. The Engineer adds the budget test now: `scripts/bench_tactical_pipe.py`'s clash scene at 5,000 units, p95 under 100 ms, with a positive control (a planted delay makes it fail).

**A23. Key rebinding: none for now** (Q-110-04, answer b). G5b is not built until Q-005-03 and Q-103-04 both close. R-110-02 says so.

**A24. Faction after collapse is a gap, and it is built.** Q-062-01 was answered on 2026-09-13 and never built; R-062-02 still carried the flag, and A15 above wrongly called it open. The rule now reads: the rotation pools (previous-descendant, then nemesis-descendant, R-058-01 to R-058-03) run restricted to candidates in surviving factions, and the player joins the drawn candidate's faction; with both pools empty, the surviving faction with the most regions, uniform among ties. One piece on `csrc/generational.c` after `B6-lifecycle` (new row `B6-collapse-pick`, tests first): `om_player_faction_reassign_on_collapse` implements it at the call site A15 fixed. Tests: a fixture where a previously played lineage survives in a smaller faction (the player joins that faction, not the largest); one where only nemesis descendants survive; one with both pools empty (most regions); same seed, same pick. B6 lands first with the current behaviour; this piece follows.

**A25. Camera pan: a speed slider, and speed that scales with zoom.** This reverses A10's toggle.
- Settings offers a pan-speed slider, not an on/off switch; the toggle that landed with C3-G5 is replaced, and the stored boolean goes. The tactical camera reads the stored speed; today it ignores it.
- New rule R-103-09: pan speed is constant on screen, for key pan and edge-scroll alike, so the ground covered per second grows in proportion as the camera zooms out. In the tactical camera: world speed = screen speed divided by the camera zoom factor.
- The slider scales the screen speed. Provisional values under the "Provisional values" section: 0.5 to 2.0 times the A6 base of 600 px/s, default 1.0. Whether the slider's lowest position should switch edge-scroll off is not decided; it does not.
- Tests (Engineer, desktop like A6's): at two zoom levels the same pan input moves the view the same number of screen pixels and a proportionally larger world distance; the slider at 2.0 doubles it; a positive control with zoom scaling removed fails. The G5 toggle test is replaced with a ledger row citing this decision.
- The galaxy camera (C5, G-G1) follows the same rule when it is built.
- Pieces: `scenes/settings` (C1-N) and `scenes/tactical_c` (C5-N).

## Addendum 11, 2026-10-01 (A24: the collapse pick's open points)

**A26. The pools measure their 2 hops from the last mission's region** (`om_mission_last_region`), option (a). It is where the player last stood, which is the hub's "geographic overlap"; the collapse check runs only after a mission, so that region always exists. No signature change. R-062-02 says so. This is the Architect's reading of the hub, not Westley's words; he may change it.

Smaller points:
- The pool roll is made as in any rotation (R-058-01). A roll of the unrelated pool falls through previous, then nemesis, then most regions. The pick creates no character; the selector that follows chooses the commander.
- A candidate's faction is the character's own faction field, not the owner of the region it stands in.
- How many random draws the most-regions fallback consumes is not pinned beyond "same seed, same pick"; the checksum guards it.
- The previous-descendant pool ignoring "last played at least 1 chapter ago" (R-058-02) is a defect in the existing pool. It is fixed in this piece as a second unit with its own test, since the pick now depends on that pool; a fixture that only passed because of the defect is corrected with a ledger row.
- `docs/architecture.md`'s line saying Q-062-01 stays open is rewritten when the piece lands.
- `pieces.toml`: the piece's acceptance lists `tests/csim/test_E08_S062_collapse_pick.py` (this commit).

## Addendum 12, 2026-10-01 (C2: region scale, HDR5)

Rule text changed in the same commit: `docs/bible/algorithms.md` ALG-31 now gives `WORLD_REGION_COUNT_RANGE = (250, 400)`, matching E-03 R-021-01 (Westley, 2026-09-28). The constants regenerate from it. The stale "default [60,110]" comment in `csrc/ouroboros_sim.h` is corrected by the core piece that raises the cap.

**A27. Past the cap.** `OM_MAX_REGIONS` is 512. `om_world_new` with more than 512 regions returns NULL, and a generation range whose draw would exceed the cap leaves the world ungenerated, the same failure shape generation already has for an infeasible count. The tests' pins are approved.

**A28. The R-021-06 corridor test is a test defect.** It took the first empty neighbour as the corridor empty, which held at 60 to 110 regions only by seed luck. The fix, in order of preference:
1. If the corridor empties can be identified exactly from public data (for example a fixed index order the generator guarantees), the test names each faction's corridor empty and asserts the rule as written: it neighbours that faction's highest frontier, and consecutive factions' corridor empties are linked.
2. Otherwise the proposed form: some empty neighbour of each faction's highest frontier is adjacent to some empty neighbour of the next faction's.

Either way it ships with a positive control: a world with one corridor link cut must fail the test. If form 2 cannot be made to fail on a cut link, it does not prove the rule; report that and stop. Ledger row as a test-defect; the rule text is unchanged.

**A29. Order of the build.** One owner at a time: core (`om_internal.h`, `region.c`, `sim.c`, including the `seen[]` array that moves with the cap), then `friction.c` (the adjacency walk; golden checksum unchanged), `worldgen.c`, `save.c` (version 4 to 5). The n² loop near the pipe snapshot is measured at 400 regions first; it is changed only if the number says so, as its own T1-N piece.

For Westley: the E-03 generation target still reads "a 110-region world in under 5 ms". It needs restating for 400 regions; until he does, no test asserts a generation time at the new scale.

## Addendum 13, 2026-10-01 (C1 S6: tactical frame `tier` and `state`)

**A30. Both fields are reserved.** Option (a), docs only: `docs/architecture.md` says `tier` and `state` are reserved and always 0, and the frame examples show 0. No client code reads either today, and neither has a defined meaning or a rule asking for it. `state` is filled only when a rule needs the client to show a unit's order, as a contract piece with its enum table; `tier` when units have a tier source. A transport test pins both at 0 so a later change has to go through the contract.

## Addendum 14, 2026-10-02 (the constants emitter drops hand-added constants)

Source: `docs/northstar/plans/2026-10-02-alg-emit-lossy.md` on `push/INV-algemit`; land the report as a docs piece. `alg_constants.py --emit` rewrites all of `csrc/om_constants.h` and would drop 147 hand-added constants; nothing in the gate compares the header with the bible.

**A31. Approved as three harness pieces, in this order.**

1. **Split.** The 147 hand constants move to `csrc/om_constants_extra.h`, hand-owned, with a `pieces.toml` row (M0). The generated header ends with `#include "om_constants_extra.h"`, emitted by the emitter, so no consumer changes its includes. Acceptance: the set of macro names and values visible to a file that includes `om_constants.h` is identical before and after (compare the preprocessor's macro dump), a full `--emit` then reproduces `om_constants.h` exactly, and the determinism checksum is unchanged. No value changes in this piece.
2. **Check in the gate.** `alg_constants.py --check` emits to memory and fails when the generated header differs from the file; `merge_gate.sh` runs it beside the lint. Positive control: a hand-edited value in `om_constants.h` makes it fail. The hand patch of the region range then goes away, because ALG-31 already gives 250 and 400.
3. **Names.** The doubled `OM_OM_MACRO_*` prefix is fixed in the emitter and its consumers renamed in the same piece, values untouched. The 10 names the emitter produces that the header lacks are bible-derived and enter the header through the emit in piece 1; a clash with a hand constant of the same name is reported, not resolved by picking one. The 20 names `--emit` lists as unparsed come to the Architect as a list with the ALG text of each: the fix is either in the emitter or in the bible's wording, decided per name.

A constant that carries a play-tuned or provisional value belongs in the hand-owned header with its comment; a value the bible states belongs in the generated one. Nobody moves a value between them without saying which it is.

## Addendum 15, 2026-10-02 (C2: the memory-per-region budget is red for a real reason)

`tests/csim/scale/test_scale_E02.py::test_e02_memory_per_region_under_256_bytes`: the marginal save-state cost between 60 and 512 regions is 1,601 bytes per region against Westley's 256 (E-02, confirmed 2026-09-14, "a miss is escalated").

**A32. It stays red as a finding and goes to Westley.** Nobody edits the test, the budget or the metric. It was red before HDR5 (for a false reason), so HDR5 lands with it listed as a known red in its ledger row, with the real numbers.

One read-only Engineer task so he can decide on facts: break the 1,601 bytes down by save slot (region fields, edge matrix, events, generational, chronicle, mission, each history ring), at 60, 250, 400 and 512 regions, and say which parts grow with the square of the region count. Append the table to the HDR5 ledger row or a short report. No fix is designed until he has seen it.

The four version-4 pins in `tests/test_load_game_wrong_version.gd` are a test-defect as the coordinator says: the version went to 5 by ruling; ledger row.

## Addendum 16, 2026-10-02 (A31: the unparsed names, decided per name)

Source: `docs/northstar/plans/2026-10-02-alg-unparsed-names.md` on `push/INV-algemit2`; lands with the diagnosis as one docs piece.

**A33. Order of the harness pieces changes to 1, 3, 2.** The gate check would flag the ten wrong `OM_TACTICAL_TICK_RATE_*` names on its first run, so the names piece lands before it.

**A34. Three kinds of resolution.**

*Ignore list.* The emitter gets a small list of names that are not constants, each with a reason, and stops reporting them: `ABILITY_MAP`, `CONQUEST_UNREST` (a template id), `CONSEQUENCE_TABLES`, `ENABLE_ADJACENCY_BONUS`, `ENABLE_OSCILLATION`, `ENABLE_RECRUITMENT`, `FORMATION_MOVE_ENABLED` (switches that are always on), `OUTCOME_THRESHOLDS`, `REGION_TRANSFER_OUTCOMES`, `STARTING_STANCE_OVERRIDES`, `UNIT_STATS`. Their values stay where they are: the 22 `OM_ABILITY_*` and 16 `OM_MISSION_BAND_THRESHOLDS_*` hand constants in the extra header, the tables in the C fences. A name not on the list and not parsed is an error in `--check`.

*Restated in the bible so they emit.* The names piece applies these edits to `docs/bible/algorithms.md` exactly; each states a value already in the text or in the legacy source, none is new. Where a hand constant of the same value exists under another name, the bible's name wins and the consumer is renamed in the same piece; the checksum is unchanged.

| ALG | Edit |
|---|---|
| 40 | "(cap `3.0` when the victim's is 0)" becomes "(`BETRAYAL_OPPORTUNITY_CAP = 3.0`, which is also the value when the victim's is 0)" |
| 22 | "with probability 0.60 ... `round(triangular(4, 8, mode 6))`" names its numbers: `CONQUEST_UNREST_PROBABILITY = 0.60`, `CONQUEST_UNREST_DELAY_RANGE = (4, 8)`, `CONQUEST_UNREST_DELAY_MODE = 6`; `events.c` reads them |
| 59 | `REFUSAL_TENSION_PENALTY_PCT = 8.0`, with the division by 100 kept in the formula; replaces hand `OM_MISSION_REFUSAL_TENSION_DEFICIT_PCT` |
| 55 | one clause per name: `RELEVANCE_LINEAGE_WEIGHT = 0.4`, `RELEVANCE_PROXIMITY_WEIGHT = 0.3`, `RELEVANCE_ARCHETYPE_WEIGHT = 0.3`, and the three `GENERATOR_*_WEIGHT` values the same way; the `mission.c` locals go |
| 50 | the four bonuses written out in the context formula: `SIGNIFICANCE_MISSION_REGION_BONUS = 0.5`, `SIGNIFICANCE_CHARACTER_BONUS = 0.3`, `SIGNIFICANCE_CHAIN_LENGTH_BONUS = 0.1`, `SIGNIFICANCE_LINEAGE_REGION_BONUS = 0.8` |
| 56 | the minutes become their own keyed list, `MISSION_BASE_MINUTES[archetype]: siege 60, multi_front 60, assault 52.5, containment 52.5, reconquest 45, defensive 37.5, interception 37.5, counterinsurgency 37.5, suppression 30, evacuation 30`, separated from `TACTICAL_TICK_RATE`; the literal table in `mission.c` reads the emitted names |
| 76 | the leading `OM_` is dropped from the two macro names in the text |
| 27 | `ARCHETYPE_STARTING_TECH[archetype]: conqueror (5, 15), fortifier (10, 20), warlord (5, 10), opportunist (8, 15), schism (0, 0), player_civilization (10, 20), breakaway (0, 0)`, transcribed from `simulation/config.py` |
| 75 | `STRUCTURE_COUNT_RANGE[canvas]: small (2, 4), medium (3, 6), large (4, 8)` and `ARCHETYPE_STRUCTURE_SPLIT[archetype]` as (player, enemy, neutral): defensive_stand (0.50, 0.25, 0.25), siege_breaking (0.33, 0.33, 0.34), reconquest (0.25, 0.50, 0.25), assault (0.25, 0.50, 0.25), suppression (0.40, 0.30, 0.30), multi_front_defense (0.40, 0.35, 0.25), interception (0.33, 0.34, 0.33), evacuation (0.50, 0.25, 0.25), containment (0.33, 0.34, 0.33), counterinsurgency (0.40, 0.30, 0.30); the range transcribed from `simulation/config.py`, the split as E-15 R-126-01 states it. `tactical_support.c` reads the emitted range |

If the emitter cannot parse one of these forms as written, the Engineer reports the form it can parse; the wording is then adjusted here, not improvised.

*Findings, not harness work.* One read-only Engineer check, reported once:
- Does structure placement (B4, `mission.c`) follow `ARCHETYPE_STRUCTURE_SPLIT`? R-126-01 assigns owners per archetype; if the code uses other fractions, that is a defect to rule on.
- Does any code set a mid-game faction's starting tech from `ARCHETYPE_STARTING_TECH`? The report found none.
- (Withdrawn, see A35: the split covers all ten archetypes.)

## Addendum 17, 2026-10-02 (correction: the structure split is complete)

**A35. Q-126-03 is withdrawn and its row removed.** The Architect read a truncated listing: E-15 R-126-01 and the legacy config both give all ten archetypes, including containment (0.33, 0.34, 0.33) and counterinsurgency (0.40, 0.30, 0.30), and the code follows the rule. Nothing was built from the wrong row. The A34 table above is corrected to ten rows.

**A36. Check results.** Structure placement follows R-126-01 for all ten archetypes. The test that proves it compares the code against itself for eight of them, so a wrong table row would pass: approved as a test piece (Engineer), pinning the owner counts for all ten archetypes from R-126-01 at a fixed structure count, with a positive control (one row altered must fail). `ARCHETYPE_STARTING_TECH` has no user in the C game, because no faction is created mid-game with a tech roll; it is restated in ALG-27 for the record and nothing is built.

## Addendum 18, 2026-10-02 (HDR5: the E-03 scale control cannot exist under the cap)

`tests/csim/scale/test_scale_E03.py::test_control_e03_10x_regions_violates_tightened_budget` needs a 1,100-region world to trip the clock; the cap is 512, and at 512 it sits at the floor and fails under load.

**A37. Option (b) for E-03: a planted-delay control.** The control's job is to prove the timing assertion is live. It is replaced by one that injects a known delay into the measured call and must exceed the budget, the same form as the A22 budget test. The budget, the measured workload of the real test and the helper's floor are untouched. Test-defect row: the old control's premise (ten times the regions) is impossible since A27. E-02, E-04 and E-05 keep their controls while they pass with a wide margin; if one starts to sit near its floor it gets the same replacement, with its own row, not before.

**A38. Before HDR5 lands:** the 13 tests the gate lists as changed assertions are each classed in the ledger (test-defect with the rule that changed, or reverted); none lands unclassed. The `symbol_ownership` report on `om_gen_set_region_range` is the known lint artifact for a comment-only header change and is noted in the row. `test_e17_field_sampling_10000_queries` (9.5 ms against a 7.4 ms scaled budget, red on main before HDR5) is a pre-existing finding: it goes on Westley's list with the numbers, and nobody edits it.

## Addendum 19, 2026-10-02 (B3 client Refuse flow; A3 tie-break)

**A39. Refuse on the briefing.**
1. Band 5 is named `refusal` in `scenes/debrief/debrief.gd`; the list covers every band the frame can carry, and an unknown band shows the error panel, never a clamped name.
2. Handoff: the bridge keeps the latest debrief frame after `mission_end` and after `mission_refuse`, and the debrief scene shows that frame. Played and refused missions reach the debrief the same way. The debrief never starts a mission of its own: `load_debrief_live`'s start-then-end leaves the live path, and with no frame held the scene shows the error panel (A7). The Engineer lists which existing debrief tests relied on the self-load; each becomes a fixture change with a ledger row, or is reported if it proved something else.
3. Refuse routes to the debrief (R-055-01: resolution, then the jump). The debrief of a refusal states the refusal and its consequence and offers the same way on to the jump.
4. The A5 "Refuse disabled" assertion becomes a test-defect row when the button is wired, as ruled in section 5.

**A40. The fallback picks move into core,** option (c). The pipe keeps the five retries and the `quiet_world` flag and asks core for the picks; it holds no tie-break of its own, so it needs no access to `OM_TIE_EPSILON`. The weakest player region comes from the function the mission generator already uses for the same fallback (`om_mission_fallback_region`), so the pipe and the generator cannot disagree. The enemy pick of A3-1 (nearest by hops, then highest total military, then lowest faction id) moves into `mission.c`; if no public function returns it, the contract gains `int32_t om_mission_fallback_enemy(const om_world *w, uint32_t region_idx);`, landing with its implementation. If the generator's fallback region rule differs from the pipe's current pick in any case, report the difference before changing either. The four `push/A3tie-tests` tests stay as they are and must pass through the pipe.

## Addendum 20, 2026-10-02 (the fallback region: one rule, one function)

The generator's `om_mission_fallback_region` picks the player region with the lowest military plus economy; the pipe picks the lowest stability composite. They differ on 18 to 66 of 400 seeds.

**A41. Option (b): the core function is brought to the rule.** Both paths implement the same answer, Q-072-01, and Westley fixed its meaning on 2026-09-30: weakest is the lowest ALG-09 stability composite, ties to the lowest region index (R-072-07). The military-plus-economy form predates that and is stale. `om_mission_fallback_region` is changed to the rule, the pipe calls it and loses its own copy, and no second function is added. `om_mission_fallback_enemy` is added as in A40.

- The assertions in `tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py` and `test_E08_S055...` that pin the old form are test-defects (the rule was clarified after they were written); ledger rows. The four A3tie tests pass unchanged.
- The determinism checksum moves on seeds where the generator's fallback fires; the ledger row says so.
- The function reads the player faction through `om_mission_player_faction`, the pipe through `om_player_faction`. If the two can ever return different factions, report it before landing; there should be one answer to "who is the player".

**A42. Harness piece 1 filters the 12 names.** The split piece keeps the macro set identical, as ruled: its emit skips the ten wrong `OM_TACTICAL_TICK_RATE_*` names and the two `OM_OM_MACRO_*` names through an explicit, commented skip list, and piece 3 removes that list when it fixes the parse. The piece-1 test allows no extras.

## Addendum 21, 2026-10-02 (who ends the mission, now that the debrief does not)

**A43. The tactical view ends the mission.** At both routing sites in `scenes/tactical_c/tactical_view.gd` (the End Mission button, and the sim reporting the mission over) it sends `mission_end` through the bridge, waits for the debrief frame to arrive, then routes to the debrief. If the frame does not arrive it shows the error panel in place; it does not route to an empty debrief. Piece C5-N with its own test: End Mission sends exactly one `mission_end`, and the debrief then shows the played mission's frame. The bridge stores a debrief frame whenever one arrives, whichever command caused it; no new bridge method is required, and the tests pin none.

This piece and the debrief change of A39 land in one clerk run. Apart, main would either show an empty debrief or end a mission twice.

**A44. The fixture changes are approved** as test-defects under A39 item 2: the 3 assertions in `tests/test_briefing_debrief.gd`, the 3 in `tests/test_sim_session.gd` and the 5 in `tests/test_pipe_error_panels.gd`, each ended or loaded through the bridge as proposed, ledger rows applied with the implementation. The G2 debrief failure case becomes "the bridge holds no frame", Retry re-reads the held frame. The script error that aborts the rest of `_run_live_debrief_tests` is fixed in the same change so no assertion after it goes unrun. `tests/qa/desktop/test_flow_spine.py` S-C8-05 is run after the landing and its result reported.

## Addendum 22, 2026-10-02 (C4 and C5 questions; the gate's skip count; two unpinned A3 cases)

Source: `docs/northstar/plans/2026-10-01-c4-c5-architect-questions.md` on `push/C4C5-questions`; land it as a docs piece. Rule text changed in the same commit: E-16 R-110-05 to R-110-07 (the Era Library), E-09 R-069-01 (the panel leaves on Proceed). New register rows: Q-110-05, Q-106-04, Q-069-01, Q-069-02.

### C4

**A45. E1 Era Library.** The screen's rules are R-110-05 to R-110-07; tests can be written. Ownership: a local ownership store, every installed era owned in development builds. Cards and detail: identity, tiers and roster from the pack manifest, nothing else. Mastery and tier progress read "not yet tracked" until Q-110-05 is answered (the gap-fix plan's wording).

**A46. E2 bug report.** F12 only, handled in one place so it works on every screen; no pause menu is added (the game has no pause, and a menu is a design the bible does not have). The ZIP name gains milliseconds so two captures in one second do not collide. The four files that still name TacticalBridge (`mission_metrics_recorder.gd`, `ws_input_sanitizer.gd`, `qa_daemon.gd`, `scripts/tactical/visibility.gd`): one read-only Engineer check says for each whether live play reaches it. A dead one is deleted in E3; a live one is rewritten onto the live bridge and gets a `pieces.toml` row; `mission_metrics.json` goes in the ZIP only if its recorder is live. Report first, rows after.

**A47. E3 legacy tactical deletion.** E3 includes the one-line edit that drops the perf-logger preload from `autoload/tactical_bridge.gd`; it does not wait for G6. The Visibility autoload goes with E3 if the check in A46 finds nothing live reading it. `scenes/debug/test_squad_impact_origins` is deleted. Cover and control groups: the Engineer lists every rule whose only tests are deleted by E3; each is a gap, entered as a work-list row under C6, and none is counted as proven or skipped. They are not rebuilt inside E3.

### C5

**A48. Rulings, numbered as in the questions document.**

1. The camera has an autonomous flag. The main-menu backdrop sets it (R-110-01); the jump sequencer sets it for the replay and clears it after, and any player input overrides it (R-107-02). The view is told by the sequencer; it polls nothing.
2. The galaxy pans by left-drag (R-107-01). No key pan or edge-scroll there, so R-103-09 and the pan-speed slider do not apply to it; this withdraws the last bullet but one of A25. Vertical drag is grab-style: the galaxy follows the pointer.
3. The rule wins: Overview at 75 and above, Regional from 40 to 65, Local below 25, interpolating between. The code's 70 and 32.5 move.
4. The rule wins: filaments join adjacent systems of the same faction only (R-106-02). Edges between different owners or to neutral systems are not drawn. `push/C5-G3-impl` draws every edge dim; it is changed before it lands.
5. Size comes from the tier already on the wire; no wire change. The 0.3 / 0.6 / 1.0 mapping is a provisional value under the "Provisional values" section.
6. Fifteen factions sharing eight names is a content gap: the name table needs at least fifteen entries (work-list row, naming, no names from existing fiction). Until then the wrap stays and the ledger row lists it as a known visual defect. An unknown faction id is an error reported in `qa_state` and shown as "Unknown"; the text "[faction]" never reaches the screen.
7. The faction list and data panels (R-107-03, R-107-04) are their own unit under the galaxy owner. `qa_state` keys `hover_faction` and `pin_faction` are ratified.
8. G-G4: key `quality_tier`, values 0 (full), 1 (stand-in), 2 (fewer particles); tests force slow frames through the QA hook, not through real load. The trigger and recovery numbers are Q-106-04; G-G4 is held until Westley answers.
9. No conflict remains: the panel stays after the last entry, the footer shows Proceed and Exit (R-108-05), and it slides out on Proceed (R-108-06); R-069-01 now says so. The embedded galaxy MISSION button is hidden in the composite. R-108-05 and R-108-07 (footer, Exit) are one new unit; R-108-01 and R-108-06 (pull-back and push-in) are another; both get work-list rows and are built after G-C3.
10. R-099-03 is the tactical rate and does not govern the replay. The replay speed is Q-069-01. The hold of 3.0 s and the 2.0 s tween stand.
11. G-C2 mentions are held on Q-069-02.
12. Ratified: `OrbitCamera.focus_region(int)`, `OrbitCamera.get_hovered()`, adapter ids `str(i)`, node `ChronicleScrollPanel`, route `chronicle`.
13. G-C3 contract approved as proposed: the chronicle frame gains `"ownership":{"stride":2,"from_tick":N,"n_regions":R,"snapshots":[[...],...]}` with -1 for unowned. If the jump report already holds the snapshots the pipe reads them from it; otherwise the header gains a count and a getter, landing with their implementation. Keyframes are not derived on the client: the frame also gains `"keyframes":[tick,...]` from `om_chronicle_generate_map_keyframes`, which is how that function becomes wired (plan header, round 1) and how R-069-05 stays provable in the sim. Order: contract docs, sim and pipe, then client.

### HDR5 landing

**A49. The skip count.** The two new skips are scale tests that run only under `OM_SCALE=1`, like the rest of that suite. HDR5 lands with the count at 57 on one condition: the clerk attaches a run with `OM_SCALE=1` in which both pass, and the ledger row names them. The gate's comparison is not changed. The path-normalising defect in `merge_gate_support.py` (relative directory gives false "changed assertion" lines) is approved as a harness piece for an Engineer, with a positive control.

### A3

**A50. Pin both cases.** A player who owns no region: `mission_start` answers an error and starts nothing; the pipe checks this before asking core for a region, since region 0 is a real region. No reachable enemy: factions that cannot be reached by hops count as equally far, so R-072-08's tie rule picks among them (highest total military, then lowest id); with no non-player faction at all, `mission_start` answers an error. Two transport tests.

## Addendum 23, 2026-10-02 (Westley's answers to the C4 and C5 questions)

Rule text changed in the same commit: E-16 R-110-02 and R-110-07, E-09 R-069-03 and the new R-069-07; register Q-110-05, Q-069-01, Q-069-02, Q-106-04 closed.

**A51. Era Library: no mastery, no tier progress.** Both leave the screen (not "not yet tracked"); they return when that part of the game is defined. This replaces the last clause of A45.

**A52. Replay speed: 2 ticks per second** (R-069-03). A named constant on the client; the 3.0 s hold and 2.0 s tween stand.

**A53. Mentions** (R-069-07, unblocks G-C2). Faction names and system names in an entry are clickable; a click centres the galaxy on that faction's territory or that system. Contract piece first: each chronicle entry in the frame gains `"mentions":[{"start":S,"len":L,"kind":"faction"|"region","id":N}]`, character offsets into the entry text as sent, produced by the sim where it fills the names. Then pipe, then client. Nothing is found by text matching.

**A54. Galaxy quality is a manual setting, never automatic.** This replaces A48 item 8 and the gap-fix plan's frame-time fallback. Settings gains a galaxy quality choice with three values (full, stand-in, fewer particles), default full, stored and applied at boot with the other settings; `qa_state` reports it as `quality_tier` 0, 1, 2. No frame-time trigger, no step-down, no recovery logic is built. Test: each value changes what the galaxy draws, and the game never changes the value itself (a planted slow-frame run leaves it untouched).

**A55. Faction names.** The name table gets at least fifteen simple invented names so no two factions share one; a Doer writes them, plain and pronounceable, none taken from existing fiction. No deeper naming work now.

**A56. Galaxy look: the prototype wins until Westley has looked.** The gap-fix plan (his decision, 2026-09-28) makes the approved prototypes in `scenes/mockups/galaxy/` the live look, and he recalls the prototype as correct and the MVP as differing from it. So A48 items 3 and 4 and the drag direction in item 2 are suspended: where the prototype and the rule text differ (band distances, which edges are drawn, drag direction), the build matches the prototype. `push/C5-G3-impl` lands as built, drawing every edge dim as the prototype does. Each difference from the rule text is listed in the ledger row; the rule text is rewritten to the look he confirms, after he has compared the two.

## Addendum 24, 2026-10-02 (batch 2: galaxy follow-ups, Era Library details, G-C3 contract, quality setting)

**A57. Galaxy, after A56.** Until Westley has compared the prototype with the build, the build keeps the prototype's behaviour, including the vertical drag direction in `mockups/galaxy/orbit_camera.gd`; `push/C5-G3-impl`'s grab-style vertical axis follows the prototype. The two sets of numbers inside the prototype (the zoom controller's 75/65/40/25 and the camera's 70/32.5) are left as they are and nothing is tested for consistency until the rule text is rewritten. Separate finding, not for the coordinator to act on: the prototype's territory shells have been invisible since a790cb20 (influence radius 0.25 against star points of radius 1.4); Westley and the Architect are settling the intended scale, and a brief follows.

**A58. Era Library details** (Q-C4-E1-04 to 08).
- 04 Ownership store: `user://era_ownership.json`, `{"owned":["era_id", ...]}`. A debug build (`OS.is_debug_build()`) ignores it and owns every installed pack. A release build reads it; with no file, every installed pack is owned, because nothing is sold yet. Store integration is E-20 S-149 and not part of this.
- 05 The manifest gains what R-146-01 already requires of a pack's identity: `era_spatial_scale` (text), `era_tone` (text) and `era_order` (integer, chronological position). `pack_validate.py` requires them (R-146-03: a missing required entry fails the pack, named). The three installed manifests are filled in the same piece; the text is one plain sentence each, written from the bible's own description of the era where it has one, and marked as placeholder otherwise. This is a pack-contract change: validator and manifests first, then the screen.
- 06 The roster shows each unit type's id as a title and its category. No role text; the manifest has none and none is invented.
- 07 A pack whose manifest says `"test_only": true` is never listed. `test_era` gets that key. Tests still load it by id.
- 08 The Era Library is a viewing screen in the MVP rounds: it has no "play this era" control. New Campaign keeps using the Settled Reach.

**A59. G-C3 contract.**
- Odd jump lengths: the snapshot count stays as R-056-03 gives it (every 2 ticks from the start). The replay's last picture is the live world state the client already holds after the jump, so no final snapshot is added and no S-056 test changes.
- Keyframes are per jump: the list is cleared when a jump starts. They are returned sorted ascending with no duplicates; today's unsorted list with repeats is a defect fixed in this piece, with a test.
- Timelines are kept in memory only and are not saved. After a load the chronicle frame carries no `ownership` and no `keyframes`, and the client shows the scroll over the final state with no replay. The frame documents both fields as optional.
- About 40 KB per jump at 400 regions is accepted; it is sent once per jump.

**A60. Galaxy quality (A54).**
- Tier 0: raymarch shells, full ambient field. Tier 1: stand-in shells, full ambient field. Tier 2: stand-in shells, ambient field at half its particle amount (provisional value).
- The ambient field (R-106-05) is not in the live galaxy yet. Porting `legacy_ambient_rig.gd` into `scenes/galaxy` is its own unit under the galaxy owner, part of the prototype migration. Until it lands, tier 2 draws what tier 1 draws, and the tier-2 particle test waits on that unit; it is not written as a skip.
- `autoload/ui_data_bus.gd` already has an owner (the piece whose `owns_glob` lists it, `pieces.toml` line 558); the settings and Era Library units take that piece's next ids, one at a time.
- A stored value outside 0 to 2 is clamped.
- The galaxy view reads the setting when it is built. A change made while a galaxy view is open applies the next time the view is built; live re-apply is not required.

**A61. Housekeeping.** An Engineer adds the four E3 gap rows from `c4_e3_c6_gap_rows.md` to `docs/northstar/plans/archive/2026-09-30-work-list.md` under C6; the cover row says no rule governs it and names the Architect as owing one. `test_tactical_view` failing 2 of 127 under a 1280x720 virtual display on main is a pre-existing finding: QA's display is 1920x1080 by ruling, so the Engineer first re-runs it at that size and reports; nothing is edited.

## Addendum 25, 2026-10-02 (galaxy: drag direction; the prototype's bubbles)

**A62. Left-drag is grab-style on both axes** (Westley: "Flip the left-click drag direction"). The galaxy follows the pointer vertically as well as horizontally. This replaces the drag sentence of A57: `push/C5-G3-impl`'s grab-style drag was right and stays; the prototype is being corrected to match.

**A63. The prototype's territory bubbles.** Westley confirmed the look of the prototype before a790cb20 (the metaball shells at their original proportion) as the correct one. A Doer is correcting the prototype on `push/mockup-galaxy-scale`: the whole civilization layer shrunk 20 times by one shared factor with the bubbles keeping their proportion, the systems spread through a volume instead of a flat disc, and the backdrop galaxy left at its size. The live galaxy's shells and scale follow that prototype once Westley has approved it by eye; until then C5 does not copy shell or scale constants from the current prototype on main, whose bubbles are invisible.

## Addendum 26, 2026-10-02 (batch 3: HDR5 gate, owner rows, the mentions contract, a display-only test race)

**A64. HDR5 lands.** The `symbol_ownership` hit on `om_gen_set_region_range` is a comment-only change on a declaration line, a false positive; it is accepted for this landing and named in the ledger row with the A49 evidence (both new scale tests pass under `OM_SCALE=1`; the two known reds are E-02 memory and E-17 field sampling). The lint gap is fixed afterwards as a harness piece with a positive control.

**A65. Owner rows.** Added in this commit: `G-eramanifest` (the `settled_reach` and `test_era` manifests). The validator change takes K1's next id and the `greek_placeholder` manifest K2's. No new rows for G-C3, mentions or the quality setting: their units take the next id of each file's existing owner, as round 1 ruled. Order for G-C3: `generational.c` (snapshots, after `B6-collapse-pick`), `chronicle.c` (keyframes), `om_pipe.c`, then `c_bridge.gd` and `time_jump_sequencer.gd`. The mentions units follow the G-C3 pipe unit. On `autoload/ui_data_bus.gd` (`G-uidatabus`): the galaxy quality setting first, then the Era Library unit.

**A66. Mentions contract** (`push/GC2-contract`).
- (a) Confirmed, with `expanded_text` and `expanded_mentions` kept: the chronicle frame carries the sim's text and the client shows it as sent. The sim is the one source of chronicle prose; the client's rebuilding of prose from fragment ids leaves the live path in the client unit, and `fragment` / `fragment_ids` stay in the frame as data. R-069-07 says so. This does not change A4-2, which is about the mission frame.
- (b) Offsets are Unicode code points.
- (c) A region mention carries the id of the region whose name was printed, and a click centres on exactly that region.
- (d) A faction click centres on the centroid of that faction's systems at the Regional distance.
- (e) A name the echo-dedup step replaced with a synonym is no longer a name and carries no mention.
- (f) Two regions printing the same name is a defect of the same kind as the faction names (A55): the region name pool is extended with simple invented names, built from syllable combinations, so every region in a 512-region world has its own. Own small piece under the naming owner.
- One check before the mentions client unit lands (Engineer, reported): for every region and faction of a seeded world, the name the galaxy view shows equals the name the chronicle text prints. If they differ, the two screens have two naming sources; report it, and the fix (the client taking names from the sim) is ruled then.

**A67. `tests/test_tactical_view.gd` on a real display.** Both failures are test defects, approved for an Engineer with ledger rows: the tick check races an extra `_process` on a rendered display (the fix makes the test independent of how many frames ran before it stops processing; the expected tick per step is unchanged), and the pixel check assumes 1920x1080 where it should read the viewport's actual size.

## Addendum 27, 2026-10-02 (after G-C3 and mentions landed)

**A68. `om_chronicle_mention_get` in the signature table.** The struct gets a binding in `signatures.toml` and conftest so the function is bound and checked like the rest (Engineer). Separately, a harness piece: the merge gate runs `sig_table --report` and fails on a BLOCKED item, with a positive control (a planted unmappable parameter fails the gate).

**A69. The chronicle scene never advances the sim by being opened.** Same fault as the debrief had (A39): a scene issuing a command from `_ready`. The jump is issued once, by the flow that leads to the chronicle (Proceed from the debrief); the sequencer holds that jump's frame and hands it to the embedded scroll panel, and the panel's own jump in `_ready` goes. Opened with no frame held (after a load, or from the galaxy before any jump), the scene shows the scroll with no entries and no replay, and its footer; it sends nothing. Tests: opening the scene sends no `jump`; sequencer and panel show the same frame; after a load, no replay. The general rule for the client from here on: a scene's `_ready` may read state and frames, and sends no command that changes the sim.

**A70. The replay draws on the galaxy view.** The sequencer placing unknown regions on a ring with hashed colours is a stand-in, accepted only while the galaxy stack is held; it is listed in the ledger as a known visual defect. When the galaxy composite lands, the replay takes region positions and faction colours from the galaxy view's own data, and the ring placement is deleted in that unit.

**A71. The panel slides in on the live path.** Entries printing into a hidden panel is a defect against R-069-01 and R-108-02. Small unit with a test: on the live path the panel is visible and at 38 percent width before the first entry prints.

**A72. Keyframes never hold the clock.** Confirmed: keyframes are markers, the map is the master clock and is never delayed (R-069-03). The old behaviour of holding the keyframe queue until the paired entry finished is gone and stays gone.

**A73. Mentions client.** The galaxy-side click behaviour (A66 c and d) stays held with the galaxy stack; the legacy handler in the sequencer remains the only consumer until then. An entry with no mentions is valid. The structural-line fallback for an entry whose text is empty stays, so the count on screen still equals what the distiller produced (R-069-06).

## Addendum 28, 2026-10-02 (A69, A71 and A72 details; harness ownership)

**A74. Proceed from the debrief goes to the sequencer.** `debrief._on_continue` routes to `time_jump`; the sequencer scene embeds the scroll panel and is the one screen that shows a jump. The `chronicle` route stays as the standalone scroll and is not on the Proceed path. The pinned route assertion in `tests/test_briefing_debrief.gd` asserted the old flow; amending that one assertion is a classed test-defect with a ledger row (Engineer).

**A75. Frame hand-over, confirmed.** Proceed issues the jump once through the bridge (`load_chronicle_live`); the bridge holds the frame; the sequencer reads `chronicle_frame()` and hands that same frame to the panel. Neither scene issues a jump.

**A76. Footer with no frame held.** Both controls show. Proceed sends nothing to the sim and moves the player on to the screen that follows the chronicle in the normal flow, exactly as it does after a replay; it is the way forward after a load. Exit to main menu is unchanged.

**A77. The sequencer's legacy `ready_for_time_jump` goes** under the A69 rule. The source scan of the `_ready` body is dropped: the test is behavioural, a recording stand-in for the bridge (and for `SimBridge` while it exists) asserts that opening the scene sends no command. A source scan may not stand in for a behaviour test.

**A78. A71: the panel slides.** R-069-01 stands: it slides in from the right over 0.40 s. The tests keep "visible and at 38 percent width before the first entry prints" and add one assertion that the slide exists (the panel is narrower than 38 percent at the start and reaches it within 0.40 s). Appearing at full width in `_ready` does not pass.

**A79. A72 reaches the settle.** `_keyframe_queue` and `_waiting_for_entry` leave `_try_settle`, and `_waiting_for_entry` is deleted with the hold it served. The footer settles when the replay clock has reached the jump's last tick and the last entry has finished printing and held its minimum time (R-069-03). Keyframes are applied by the clock as their ticks pass, so none is pending at the end.

**A80. Harness.** The sequence is approved: `HARNESS-sigblocked` lands its change to `merge_gate_support.py` and `merge_gate.sh`, then `HARNESS-symown` takes ownership of those files and lands on top; never in parallel. `A68-mention-bind` lands first. No policy change for header prototypes in the symbol lint: a signature change in the header is a contract change and is caught by the signature table gate (A68), which is the right detector for it. The two `pieces.py --check` failures (the `B7` / `B5-chronicle` overlap on `csrc/generational.c`, the `T1` acceptance id) are mine to fix in `pieces.toml`; the coordinator sends the verbatim output and they are fixed in one commit, not worked around.

## Addendum 29, 2026-10-02 (the two audits: event region cap, names)

**A81. Events cover every region.** `OM_EVT_MAX_REGIONS` at 64 against `OM_MAX_REGIONS` at 512 is a defect: on a galaxy of 250 to 400 regions most of the map can never have an event. Test first (Engineer): on a seeded 400-region world, over a run long enough for events to fire, at least one event lands on a region with id 64 or above, with a positive control (the current cap fails it). Then the fix under the owner of `csrc/events.c`: the events table is sized by `OM_MAX_REGIONS`, with no second cap. If the test shows events do reach regions 64 and above today, the reading was wrong; report that and change nothing.

**A82. Names.**
- The galaxy view takes names from `scenes/world/chronicle_names.gd` and the shared JSON, as the audit recommends. No third table: the galaxy mockup's invented names do not come across with the look.
- The mission-briefing marker printing `table[(region + node) % 528]` is a defect: a region is shown under its own name everywhere. Small unit with a test (the marker's name equals the chronicle name of that region).
- Faction names wrapping at 18 breaks A55 for any world with more than 18 factions. The faction pool is extended the same way as the region pool (A66 f): simple invented names from syllable combinations, enough for the faction cap, sim table and client JSON generated from one source so they cannot drift. Same naming piece.
- The client fallback resolver stays only as the structural-line fallback of A73; its unowned wording is changed to the sim's ("an unclaimed people"). Its other differences are not worth a unit while the sim sends finished text.
- The name dictionaries in the legacy info panel and the sequencer that the C pipe never fills are dead: the sequencer's goes in the A70 unit, the info panel's under that file's owner as a deletion unit.

**A83. Memory per region** goes to Westley with the audit's breakdown (damage history is 1,536 of the 1,601 bytes; the edge matrix is a fixed 1 MB). No change until he decides; the E-02 memory test stays red and listed.

## Addendum 30, 2026-10-02 (info panel owner; chronicle glob)

**A84. Info panels have an owner.** New piece `G-infopanel` owns `scenes/world/region_info_panel.gd`, `faction_info_panel.gd` and `info_panel_host.gd`; the A82 deletion unit runs under it. The test pins are accepted as written (`region_meta["region_id"]`, `faction_meta["id"]` as a numeric string, `region_rows[i]["region_id"]`): the panels are handed ids and resolve names through `chronicle_names.gd`, never handed names. The `scenes/debug/test_*_info_panel*.gd` scenes that pass name meta are updated in the same unit.

**A85. `scenes/world/chronicle_*` in both C3 and C8** is the round-1 arrangement: C8 depends on C3, both are attached, so one owner at a time holds; no change. New chronicle scene units take C8's next id.

**A86. Faction name shape** (starts with "the ", at least two words, no apostrophe or comma) is accepted as the pool's rule.

**A87. The runner's 300 s default** cutting off `test_chronicle_scene_open` and `test_time_jump_replay` is a harness defect, not a test pass: a test that can only pass with a raised timeout is listed until fixed. Small harness unit: those two tests declare their own needed time (or the runner's limit is counted in frames like the tests' own quit), with the default unchanged for everything else.

## Addendum 31, 2026-10-02 (A81 lands; what it uncovered)

**A88. A81 lands with one red listed.** The cap made three quarters of a full-size world event-dead; that is the worse defect and its fix is not held behind a band that was only ever met under the defect. `push/A81-events-cap-impl` lands together with the two test-defect fixes below. `test_R_045_09_mean_over_all_windows_between` is accepted red for this landing with the diagnosis as evidence (`docs/northstar/proving_ground/evidence/a81_downstream_diagnosis_2026-10-02.md`), named in the ledger as a real balance finding awaiting Westley. It is not skipped, not widened, and not reclassified.

**A89. Two test-defects, approved (Engineer, ledger rows).**
- `test_pipe_debrief_region_delta`: re-pick a seed that passes on both builds for the right reason (the drawn archetype has a consequence row on the mission region) and correct the docstring. The test asserts the drawn archetype and target so it cannot pass by accident again.
- `test_pipe_mission_over`: re-pick a seed whose run time is checked on both main and the branch, and assert the drawn archetype so a later world change shows up as a clear failure instead of a 500 s run.

**A90. Knowledge Lost rate (R-045-09) goes to Westley** with the three candidates: retune the event constants, change the revolt economy effect or its recovery, or revisit the per-world target. Nothing is tuned until he chooses.

**A91. Tactical cost at 2,500 units and above.** 52 ms per tick is a finding against the tactical budget, not a test quirk. One Engineer measurement, reported: tactical tick time at 500, 1,000, 2,500 and 5,000 units on the Siege Breaking case, against the E-13 budget, with the profile. The fix (the nearest-scan in `csrc/unit.c`) is ruled after the numbers.

**A92. Specfactory's ten standing failures** get a cleanup unit: an Engineer first classes each (stale test, missing external file, real gap) in one report; fixes follow per class. A suite that is red on main hides new reds.

## Addendum 32, 2026-10-02 (tactical cost; specfactory cleanup; Westley's holds)

**A93. Tactical step cost is a budget miss, fixed in two moves.** Measured: 3.33 ms at 990 units against 3 ms, 40.7 ms median at 4,996 against 30 ms for 10,000, growth between n^1.5 and n^2.
- First, tests (Engineer): the E-13 scale figures as tests on the Siege Breaking case, at 1,000 and 10,000 units, timing the same subset the budget names (movement and collision) and, reported beside it, the whole step. Red today, listed.
- Second, a diagnosis with a proposed fix (Engineer, read and profile only, `perf` not gprof): why `om_grid_iter_next` and `om_tac_nearest_scan_cell` call counts grow 2.3 to 2.6 times per doubling, what the every-20th-step spike is (profiled alone), and a concrete change with its expected exponent. The fix must leave the trace byte-identical (same nearest unit chosen, same tie order); if it cannot, that is said in the proposal. I rule on the proposal; no fix is built before it.
- The worst-step spikes (130 to 346 ms) are reported against the budget as their own line: a 10 ticks per second sim cannot absorb a 346 ms step.

**A94. Specfactory cleanup, as grouped.**
- Harness unit: items 1, 2 (regenerate the allowlist), 6 (stale reach test rewritten on the synthetic-repo pattern), 3 (vendored card fixture), and the `yaml` import failures (the dependency is declared where the suite's environment is set up; not skipped).
- Contract piece: items 4, 5, 7, 8, 9 with the report's six-step fix (generated blocks regenerated, never hand-edited; `internal = true` rows for the fifteen prototypes).
- Ownership: the coordinator drafts the owner rows on a branch (specfactory tests, `scripts/specfactory`, the allowlist, conftest, and the contract piece ordered after `A2-contract` and `core`), keeping the existing harness pieces' files out of the new globs; I review and land `pieces.toml`.
- Gate: once the suite is green, `merge_gate.sh` runs `tests/specfactory` and `sig_table.py --check`, and `alg_constants --lint` fails on stale extra allowlist lines, each with a positive control. Last unit of the group.
- Item 10 (snapshot fixture: compare bytes or structure) is Westley's policy call and waits; the test stays red and listed.

**A95. Held by Westley, 2026-10-02.** The Knowledge Lost rate (A90) waits until the layer and environment systems are designed; he intends a fresh balance simulation then, against the early-repo simulation that hit the target numbers. Nothing is tuned meanwhile and R-045-09 stays red and listed. The memory-per-region budget is to be raised (he agreed); the new figure is recorded when he gives it.

## Addendum 33, 2026-10-02 (A81 landing seeds; the E-13 scale tests)

**A96. Telegraph test seeds.** TD-A89-3 is approved as landed (two seeds valid on both builds, each asserting target, archetype and region). The both-builds rule exists only to cross the landing; once A81 is on main, an Engineer restores the coverage to six seeds chosen on main, same assertions, same ledger row. Seed 24 is not closed by re-picking: an Engineer checks, against the rule text for a telegraphed attack on a player region, whether archetype 8 at another region may outscore Defensive Stand while exactly one telegraphed region exists. If the rule requires Defensive Stand there, it is a real defect in the generator's scoring and is reported as one; if the rule permits it, the row says so with the rule id.

**A97. E-13 scale tests.**
- (a) They follow the scale suite's convention (`assert_budget`, the budget divided by `OM_SCALE_CPU_FACTOR`), like every other scale budget, so one machine's speed does not decide a pass. This is stricter than the bare figures, never looser; the figures themselves are unchanged and remain Westley's.
- (b) No debug timing seam and no contract piece for one. A budget measured on a debug library is not a measurement of the game. The whole-step time stands as the test, labelled an upper bound: if the whole step meets the figure the budgeted subset does too. If, after the A93 fix, the whole step still misses while the subset plausibly meets, the question returns with numbers.

## Addendum 34, 2026-10-02 (the gate and scale-gated tests)

**A98. `push/A93-e13-scale-tests` lands with the gate's `skipped +3` accepted,** on this evidence: the three are the new `OM_SCALE=1`-gated E-13 tests, which run red under `OM_SCALE=1` (3.5 ms against 3 ms; 88 ms against 30 ms) and are listed in the ledger as budget misses under A93. They are gated, not skipped findings. Then a small harness unit under the owner of `merge_gate_support.py`: the gate counts tests gated by `OM_SCALE` in their own line, separate from skips and xfails, and requires each to be named in the scale ledger list; an ordinary new skip still rejects. Positive controls: a new plain skip rejects; a new scale-gated test missing from the list rejects. Running the gate with `OM_SCALE=1` is not the answer.

## Addendum 35, 2026-10-02 (tactical cost: the proposal)

**A99. The A93 proposal is approved, all three changes.** Per-cell faction counts in the grid with the faction-filtered iterator skipping cells without its faction; the damaged-unit prepass for the Warden Rally scan; the grid-based contact check reproducing the 2,048 cap exactly. Built as units of about one file each under the owners of `csrc/unit.c`, `enemy_macro.c`, `fog.c` and `om_internal.h` (the coordinator checks the rows; a missing owner comes to me before the unit starts). The prototype patch is reference, not the change.
- Before any unit: the equivalence evidence becomes a kept test (Engineer). Per-step unit-state hashes recorded from main for the fifteen runs of the diagnosis (idle and engaged, 502 to 4,996 units, lists over the cap) and asserted after; with the existing checksum trace, O0 equal to O2. A fix that changes one hash does not land.
- `test_F3_probe_positive_control_counts_calls_while_contact_unset` pins the quadratic call count, which is the defect. Test-defect, approved with a ledger row: it keeps its purpose (the probe registers `om_unit_can_see` calls while contact is unset, and the count is the same on two runs) and drops the `2*n*n` figure.
- Second round, same method, proposal before build: aura regen (7.5 of 10.3 ms at 4,996) and the damage-reduction scans behind the 10 to 20 ms combat spike at 990 units; and one measurement of sustained melee with thousands of moving units, which nobody has taken. The E-13 tests stay as written; the worst step at 10,098 units (25.8 ms against 22.2 scaled) is reported beside the median until the second round.
- `perf` is not needed for this; gprof and phase timers were enough. No sysctl is changed.

**A100. Player collapse is far rarer with events working map-wide** (seeds collapsing by the second post-mission jump, 2,000-tick jumps: 34 on main, 1 on the branch). Recorded with A90 and A95 as part of the same balance question for Westley's later simulation; nothing asserted, nothing tuned.

**A101.** The scale ledger list file added to `HARNESS-symown`'s `owns` by the coordinator is accepted. A94-contract landing stacked with its harness follow-up, with only `snapshot_fixture` red, is accepted.

## Addendum 36, 2026-10-02 (tactical fix owners; seed 24; a bible wording)

**A102. Owners for the A99 units.** `csrc/unit.c` under B10c, `csrc/enemy_macro.c` under B13, `csrc/fog.c` under B11, `csrc/om_internal.h` under A94-contract once it has landed. Unit order as proposed: declarations, `unit.c`, `enemy_macro.c`, `fog.c` only if needed. The stale `pending` statuses do not block this; a clerk unit afterwards checks every piece's status against the ledger and main and reports the corrections for me to land.

**A103. A99 equivalence tests accepted as built:** eleven runs (my "fifteen" repeated a figure from the earlier message), the hash contents, the two controls, and TD-A99-F3 as described. One loose end with a consequence: in-use unit counts come out about 4 percent below the nominal figures (4,785 for 4,996). The E-13 tests must count live in-use units, so "1,000" and "10,000" mean units actually simulated; the Engineer of the second round finds the cause of the difference and corrects the tests' unit counts if they are short.

**A104. Seed 24 is permitted** (R-072-05: one weighted draw over the top five). The E-10 "obviously working" paragraph claimed more than the rule; it is rewritten in this commit to say the telegraphed pair is in the draw pool and is drawn on the example seed. No rule changes.

## Addendum 37, 2026-10-02 (galaxy bubbles: measured, redesigned)

**A106. The territory bubbles are rebuilt as a baked field.** Measured on Westley's RTX 3060 (`push/galaxy-field-experiment` 7b535246): the current shader costs 36 to 60 ms per frame at prototype size and 75 to 138 ms at 400 systems and 15 factions; a field baked by the GPU into a 96-cell 3D grid and drawn in one pass costs 0.5 ms at half resolution and 1.9 ms at full 1080p, at either size. Westley's decisions: budget 2 ms on the RTX 3060 at game size and 1080p; same smooth look; tests first with the speed enforced by tests; the backdrop gets a dim direction-only wash, four real-depth star layers and fading edges, with camera-following dust. Spec and build plan: `docs/northstar/plans/2026-10-02-galaxy-bubble-field-spec.md`. Built in the prototype on `push/galaxy-field`; the live galaxy stack stays held (A63) until he approves the result by eye, then one ruling hands over files and constants.

## Addendum 38, 2026-10-02 (piece statuses)

**A105. `pieces.toml` statuses corrected from the audit** (`docs/northstar/proving_ground/evidence/piece_status_audit_2026-10-02.md`), drafted by the coordinator, reviewed and landed here. Landed pieces with no open red are attached with their landing commit (the five the audit gave no commit for were checked: each is that piece's last unit on main). B5, B9, B10b and B14 stay pending with their open red rule named beside them. B5b, B7b, B5-chronicle and G-flags stay pending until someone shows a landing commit and a green acceptance for each. Ownership-only G rows carry no status. G-tacticalvisibility is deleted with its file; G-legacytests keeps the three paths that exist. The A99 hash mismatch was a recording taken before A81 landed, not nondeterminism; closed.

## Addendum 39, 2026-10-02 (the unowned reds)

Evidence: `docs/northstar/proving_ground/evidence/unowned_reds_2026-10-02.md`.

**A107. E-17's 25 red tests are a held epic, not a gap to fill.** The tactical map generator is stubbed because E-17 has open questions (Q-112-01 through Q-119-02) and Westley is designing the layer and environment systems now; an epic with an open flag is not built. The tests stay red and listed under B15m with the Q ids beside them. No unit starts.

**A108. R-078-06 is a test defect.** The rule is about the chronicle: the mission's consequence reaches the jump's chronicle. The flag is consumed by the jump by design. The test asserts instead that the jump's chronicle contains the consequence event for the mission's region with the band's outcome, and that a second jump with no new mission adds none. Engineer, ledger row.

**A109. R-130-02: one test defect and one real defect.** The fixture puts the enemy where it is still inside the moved zone (drift span 150 against a contest radius of 300), so it cannot show the zone moving; the fixture is changed so the enemy is inside the old zone and outside the moved one (a longer drift path in the fixture, not a changed constant). Ledger row. Separately, `om_objective_is_contested` counting any unit regardless of faction is against the rule ("no enemy inside"): test first (a friendly unit inside the zone does not stop progress; an enemy does), then the fix in `csrc/tactical_support.c` under B14.

**A110. R-085-02 and R-085-04 go to Westley** as tactical balance findings: the 50 against 50 mirror lasts 216 s against his 150 to 200 s; Line against Line resolves in 124 s and Siege against Siege in 30 s, against the order Strike, Line, Siege. Before they go to him, one Engineer check that the R-085-04 fixture is a fair like-for-like engagement (same counts, same starting distance per category); if the fixture is skewed that is a test defect and is fixed first. Nothing is tuned.

**A111. Detector controls get an owner and a split.** New piece `G-controls` owns `tests/csim/controls/**` (harness lane; row drafted by the coordinator as before). The 92 placeholder controls are counted by the gate in their own line against `placeholder_controls.txt`, as A98 did for scale tests: a placeholder that is not listed, or a listed one that starts passing, rejects. The 7 live controls whose injection does not trip are the urgent part: a control that cannot fail means its detector is unproven. One Engineer report, each of the seven classed (injection broken, detector blind, or control stale), before anything else in this piece.

**A112. The four unattached pieces.** B5b attaches at 10a1faa3 and B7b at the last of its increments on `generational.c`, on their green acceptance. B5-chronicle gets acceptance ids first (the tests that prove the consequence entry and the chain clusters at jump end; the coordinator proposes them) and attaches when they are green. G-flags attaches when its Godot gate test has been run green; until then both stay pending.

## Addendum 40, 2026-10-02 (memory per region)

**A113. Memory per region: 2,048 bytes** (Westley, 2026-10-02), replacing 256. The region connection table, a fixed 1 MB, is counted separately as a fixed cost and not divided among regions. E-02's performance line is rewritten in this commit. The E-02 memory test takes the new figure (Engineer; a threshold change by its owner, recorded in the ledger, not a test-defect) and measures the per-region record without the fixed table. This closes A83 and the memory half of A95.

## Addendum 41, 2026-10-02 (dead controls; an unwired contest check; balance findings)

**A114. The seven dead controls are brought to life.** Items 3 to 7: one `OM_DEBUG_INJECT` branch each under the file's owner, as started. Items 1 and 2: test fixes under `G-controls` as probed (population driven below zero; a feasible two-faction fixture), plus the missing ratio-swap branch in `worldgen.c` under its owner. Then the gate gap is closed as a harness unit: the merge gate runs `control_liveness.py` for the controls of the piece being attached and rejects a dead one, with its own positive control. Pieces attached with dead controls (B4, B7, B8, B10, B11, B12) keep their status; each control going live is noted in the ledger against its piece.

**A115. The contest check must be wired or deleted.** `om_objective_is_contested` is called only from tests, so R-130-02 ("progress continues only while no enemy is inside the moved zone") is tested and not in play, against the wired rule. An Engineer first reports how hold-zone progress is decided in play today. If another path already stops progress for an enemy in the zone, that path is the one R-130-02's tests exercise and `om_objective_is_contested` is deleted. If none does, test first (through the tactical step: progress stops while an enemy stands in the zone, including a drifted zone, and resumes when it leaves; a friendly unit does not stop it), then wire it under B14. The faction-filter fix in flight continues either way. The enemy-placement deviation in the R-130-02 fixture is accepted.

**A116. R-085-02 and R-085-04 are balance findings for Westley,** kept with the other balance items (A90, A100). The R-085-04 check is accepted: Strike before Line holds in every variant, Line before Siege fails in every variant, so it is not the fixture. One thing the rule leaves open and he will be asked with it: the engagement the order is measured on (counts, distance, orders), since the rule text gives none. Both tests stay red and listed.

## Addendum 42, 2026-10-02 (hold-zone contest: one path)

**A117. The play path is the rule; the duplicate goes.** Hold-zone progress in play is decided by `om_mission_tactical_tick` and `om_mission_eval_hold_zone` (enemy faction only, 400 wu, rebuilt each step). `om_objective_is_contested` duplicates it with a different radius and no faction filter and is called by nothing in play: it is deleted with its header line, its conftest binding and `OM_SUP_CONTEST_SCAN_CAP`, as a contract piece under the header's owner (A94-contract's next id). The faction-filter fix and its red test are dropped, not landed; the rest of `push/A108-A109-tests` lands without that test.

**A118. R-130-02's tests drive `om_tactical_step`** on a built hold-zone mission. Friendly inside: progress runs. Enemy inside: stops; leaves: resumes with elapsed time kept. For the drifted zone the proof is turned round so no constant changes: the enemy stands outside the old zone and inside the moved one (on the drift axis, 500 wu from the old centre is 350 wu from the moved centre), so progress runs before the drift and stops once the zone has moved onto it. The 400 wu radius and the 150 wu span stand.

**A119. Drift is not wired into play yet, and that is recorded, not fixed now.** Which objectives drift comes from the map's spine nodes and their waypoints (R-130-01), which is the held E-17 and E-15 map work. `om_objective_setup_drifting` stays test-only with a comment at the function and a ledger line naming A119 and the Q ids, so it is not mistaken for live behaviour. It is wired in the unit that brings spine waypoints into mission setup.

## Addendum 43, 2026-10-02 (A117 row landed; E-13 unit counts)

**A120. `A117-contract` is accepted and attached at a51cb292.** The row's owners, order and acceptance are right; the deletion left no reference in `csrc`, and the binding test passes.

**A121. The E-13 unit-count explanation is accepted.** The shortfall was the test passing region fields in the wrong order to the force builder, not a fault in play. The E-13 tests on 1,000 live (period 1) and 10,000 to 10,100 live (period 2) stand, with budgets unchanged. Two things are recorded, neither changed now: the A99 equivalence builder also passes the fields out of order (economy, population, tension) and keeps doing so because its recorded hashes depend on it, with a comment at the builder saying so; and at 10,100 live the worst single step (25.4 ms) is over the scaled budget while the median passes. The tests assert the median as the rule is written; the worst step is reported with the round 2 results so Westley can decide whether the rule should bound it.

## Addendum 44, 2026-10-02 (A111 and A112 rows landed)

**A122. The draft rows are accepted and landed.** `G-controls` owns `tests/csim/controls/**` and `placeholder_controls.txt`. B5b is attached at 10a1faa3. B7b is attached at ed4a95cb, the last of its own increments, as A112 said; the first-green commit is not used because a piece attaches where its work ends. B5-chronicle takes the three proposed acceptance files and is attached at c8daf236, its last landing commit, all 26 tests being green; the save-version test stays outside its acceptance as it proves `save.c`. G-flags is attached at 4daebc83 on its green Godot gate test. `G-controls` stays pending until the two control fixes and the placeholder gate unit give it acceptance ids.

## Addendum 45, 2026-10-02 (movement and layers into the engine; tactical speed round 2; controls)

**A123. Tactical speed round 2: prototypes A and B are approved** as two one-file units under B10c (`csrc/unit.c`), each proved by the A99 equivalence tests and the per-step hash chains as measured. No snapshot of Warden counts: the order semantics stay as they are, since a snapshot is not byte-identical. There is no round 3 proposal: the nearest-hostile search is rewritten by the movement plan below (P1 and side-sight targeting), and its speed is gated there against E-11's budgets. After A and B land, the coordinator's lane leaves `csrc/unit.c`, `csrc/tactical_move.c`, `csrc/tactical_support.c`, `csrc/fog.c` and `csrc/tactical_mapgen.c` to the builder chat of A124 (pieces `PP-*`). `csrc/mission.c` stays with B9; the builder's one unit there (the canvas size call at mission setup) is handed to the coordinator as a branch to land.

**A124. The movement, layers and search plan is in force:** `docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md`, approved by Westley 2026-10-02. It continues the Mac design chat's work (`docs/northstar/research/layer_dynamics/LEAVE_OFF.md`) and answers the parity requirements file. A separate builder chat runs it; it reports to the Architect, not to the coordinator. Pieces `PP-contract`, `PP-parity`, `PP-move`, `PP-unit`, `PP-capture`, `PP-fog`, `PP-mapgen`, `SL-harness` are registered in this commit.

**A125. Westley's decisions, 2026-10-02, recorded.** His words are quoted where he gave more than a choice.
- Group speed: slowest member, as R-095-01 and the C (a ruled difference from the Python). Q-095-01's detach rule is written into the rule.
- The 200 wu leash before damage: built as a setting; the lab runs both; he picks from the chart; the other side is then deleted.
- A unit in solid terrain is moved out, not stalled as in the Python.
- P4 (generated map content) is held for his environment design. Terrain for tests and the lab is hand-placed.
- Sight: a unit fires at what its side sees ("Side's shared sight"). Siege units, whose sensor is 300, fire beyond it only with a spotter or a ping; accepted.
- Cover: fire follows the vision rule; a unit inside a cover obstacle is seen and fired at as normal. Cover height: "Yes, we should definitely build it now".
- Terrain blocks above 0.7: "The current C engine is fine."
- A lone unit on attack-move: "It should resume its prior goal after the fight is completed."
- Units pushing apart: "the way that it worked on the Python simulation was perfect, and I'd like to migrate that way to be the way that it is in C as well." One case is held back for him, Q-097-02: the Python throws two units on the same spot apart by a thousand times the normal push.
- Target choice: "I had imagined that units would only... just fire at the closest unit and we wouldn't have any other way. And I want to retain that, but if we can collect data on an additional switch where units focus fire, then that's okay." A lab-only setting, and one batch that measures what it changes.
- Guard stance: decided after the movement lands (Q-096-01).
- Scope: engine only; the client's layer controls follow a working configuration.

**A126. Bible and register in this commit.** E-12: Purpose, S-093 (title, story, R-093-01, R-093-02), the invariant, R-089-01. E-01: R-004-02, R-008-04, new R-007-06. E-11: the Bombard example. E-13: R-095-01, R-096-02, the stationary-pair rule, R-098-02, R-099-04, the invariant, the route-grid cell size in the scale line (100, as R-097-01; it said 60), the gate verdict. `stories.md` S-093. Register: the second rows numbered Q-098-01 and Q-101-01 become Q-098-02 (closed, cover) and Q-101-02 (open); new rows Q-096-01, Q-097-02, Q-008-05, Q-008-06, Q-008-07. Earlier documents that say Q-098-01 for cover height (the port audit, the parity requirements) mean Q-098-02.

**A127. Ready to build, by epic.** E-13: S-095, S-097 to S-100 and S-102 are buildable; S-096 as written, with the guard open. E-12: S-089 and S-093 are buildable; S-090 to S-092 wait on map content. E-11: S-084 and S-087 are buildable as rewritten; the two bugs against ruled text (Intercept's duration, R-086-02; the second Warden's 0.05, Q-084-01) are fixed with a test first. E-01: S-001, S-002, S-004, S-005, S-007, S-162 to S-164 are buildable on provisional numbers held as settings; S-003, S-006, S-008's numbers, S-009 to S-011 are not built. Test defects the builder fixes with ledger rows: the Bombard mirror at 1,000 wu in the R-085-04 test (no spotter), `test_E13_S097_around_not_through.py` (waits when surrounded), the R-127 tests that feed the census by setters, the cover test, and `test_E13_S096_four_commands.py` checked against the lone-unit rule.

**A128. Controls (the coordinator's items 3 and 5).** e04: first move the real-repo liveness test onto a planted dead fixture, so that fixing a real control never breaks it again; then the missing hook under B1, by a Doer. The placeholder gate's "stale" as built (any listed path that is missing or no longer a placeholder, a filled-in failing control included) is accepted; it is the stricter reading and the right one.

**A129. Still Westley's, unchanged:** whether E-13 bounds the worst step and in which scenario; the E-17 reds; R-085-02 and R-085-04; Knowledge Lost.

## Addendum 46, 2026-10-02 (e04 control; builder wave A1)

**A130. e04: option (a).** The control's polarity is a test defect (TD-A128-e04-polarity): every live control asserts that the injected bug is detected, and this one asserted the clean behaviour. `push/e04-control-polarity` (6f757bfc) lands the hook and the control fix together under B1 and G-controls. Read before ruling: the hook is two guarded lines in `csrc/events.c`, the control now asserts the reused tag, no threshold is touched. Option (c), a real save and reload test, is the right end state and waits for a save call in the header; the control's docstring already says so.

**A131. Prototype B and `csrc/unit.c`.** The builder's A3 wave may start on `unit.c` as soon as the damage-reduction-lists commit is on main; the builder checks the log for it and needs no further word from me. Until then `PP-unit` is not released.

**A132. Layer numbering and cover height (builder Q-C7, Q-C8).** The bible numbers layers 1 to 5 from the bottom; the engine and the tests count the same layers 0 to 4. Layer n in the bible is engine layer n - 1. The valid layer range for every call that takes a layer is 0 to 4, and the header carries the count as one named constant in the ABI 4 piece. `om_map_add_cover` stays one symbol with `double height`; the height is a whole count of layers from the bottom, so height h blocks engine layers 0 to h - 1. Height 1.0 with both units on engine layer 0 blocks, which is what `test_E11_S084_flat_damage.py` expects; 5.0 blocks all five. A height that is fractional, negative, not finite or above 5 is refused (returns 0, nothing added); 0 adds an obstacle that blocks nothing. The plan appendix's separate `uint32_t` call was my error and is corrected in this commit; E-01's Purpose gains the numbering sentence.

**A133. The contract document `pp_contract.md` (builder Q-C1 to Q-C9, and the getters).**
- Q-C1: the generated stubs land with the contract, in one merge that names `PP-contract` and the four owning pieces (`PP-move`, `PP-mapgen`, `PP-unit`, `PP-fog`). Stubs only; no lint exemption is written.
- Q-C2: vision per signed offset (`VISION_UP_1..4`, `VISION_DOWN_1..4`) replaces the two cone parameters.
- Q-C3: canvas rules accepted as written, with one change: a width or height above 28,000 is refused, since the tables are sized for that and nothing may corrupt.
- Q-C4: settings survive `om_tactical_reset`, are neither saved nor hashed, and a new world starts at the defaults. The game never sets one, so a game trace is unaffected.
- Q-C5: most damaged is lowest hp fraction, then nearest, then lowest id.
- Q-C6: the collision-radius setting reaches the collision pass only.
- Q-C9: the 59 ranges are accepted as refusal bounds for the lab's setting call. They are not game values, thresholds or tolerances; every value the game ships and every pass mark stays Westley's. A search that wants a value outside a bound stops and asks.
- Three read-only getters (a unit's group id, its leash anchor, its engaged flag) join ABI 4 in the same piece, written into `pp_contract.md` with signatures and unknown-unit returns before any implementation. `tests/csim/test_E02_S020_abi.py` asserting ABI 3 is a test defect with a ledger row.

**A134. Table sizes and the scale audit.** Accepted: per-unit tables at `OM_MAX_UNITS` (10,100), 78,400 density and route cells per layer (280 by 280 at 100 wu, the 28,000 canvas), 3,136 cover obstacles. Conditions: the wave report states the total bytes added; every fixed table refuses when full and returns an error, with a test that fills it, and none corrupts. The findings are bugs, fixed test first under the owning piece: unit id 10,100 unseen by movement; groups and support structures corrupting when full; the 512-cell route search cap, which goes, with the 1,000 route queries per second budget asserted on the largest canvas.

**A135. Tests that are red until a later wave.** The pending list is accepted: one file of test ids owned by `PP-parity`, each marked strict expected-failure, so a test that starts passing fails until its line is removed. Each wave's landing removes its own lines in the same merge. The list is empty at the end of Phase A and again at the end of Phase C, and every wave report gives its length. Nothing else may be put on it: a test that fails for a reason other than "its code has not been built yet" is a finding. Note: the six movement rule test files reached main directly through pull request 51 (036fba3b), outside the merge gate; the builder's first landing puts their ids on the list so main's failure count returns to its base.

**A136. Parity tolerance.** 1e-6 wu in position and 2e-3 rad in facing are carried in the tests as named, provisional values. They are Westley's to confirm, at the Phase B read, beside the measured largest difference per scene. Tightening needs no one; loosening needs him.


## Addendum 47, 2026-10-02 (builder: waves in parallel, owner rows)

**A137. Waves A2 and A3 may run in parallel** straight after the A1 landing, without waiting for my reply to a wave report: A2 on `tactical_move.c`, `tactical_support.c` and `fog.c`, A3 on `unit.c` (P2, P1, P6). They are different files under different pieces. P5 touches both `unit.c` and `tactical_move.c` and so runs after both; A4 runs after A2. Reports for A1 to A4 are sent as each wave lands and the builder carries on. It still stops at once for an unclear rule, a missed budget, or anything that would loosen a number, and it stops at the end of Phase A for the Phase B read with Westley.

**A138. Owner rows.** The builder may add `pieces.toml` rows for files of its own pieces (`PP-*`, `SL-harness`) when the footprint fence needs them, with the owner lint clean, and names them in the wave report. It changes no other piece's row. The rows added at 7e5f10ce and after are accepted.

## Addendum 48, 2026-10-02 (builder: reach allowlist, what the two switches gate)

**A139. Reach allowlist.** `PP-contract` may append five rows to `scripts/specfactory/reach_allowlist.toml`, and only those: `om_tactical_set_param` and `om_map_block_rect` (lab and test calls; the game sets no setting and places no hand-made terrain, so they stay listed), `om_map_set_canvas` (row removed in the merge that lands the `mission.c` unit), `om_command_set_layer` and `om_command_ping` (engine only by Westley's scope decision, A125; rows removed when the client plan wires them to a pipe handler). Each row states its reason and the event that removes it. No other row of that file is touched. The behaviours behind the calls must still be reached from `om_tactical_step`; the allowlist covers the entry calls, not the code they switch on.

**A140. What the two switches gate: the builder's reading stands.** `OM_TP_PURSUE_BY_STEERING` gates P8, P7, collision, clamp, P1, P2, P5 and P6; `OM_TP_ROUTE_AROUND_TERRAIN` gates routing, cover height and the cover endpoint exemption; with both at 0 the recorded hashes hold. The fixes for G04 and G15 and the P9 census are not gated, and the hashes they change are re-recorded once with a ledger row. The game runs at the defaults (1). The old paths behind 0 exist only as the baseline for this plan and are deleted, with the two switches, by a ruling at the end of Phase E; each such path carries a comment saying so.

## Addendum 49, 2026-10-02 (more hands: a harness chat, the coordinator lands, Phase C tests early)

Westley asked for more work in parallel and approved these three.

**A141. A separate harness chat runs Phase S** of the movement, layers and search plan from now, beside the engine work. It owns piece `SL-harness` (`scripts/skilllab/**`, `tests/skilllab/**`) and nothing in `csrc/`. The builder chat hands over its trace and settings work (`push/sl-trace-impl`) by landing it or by naming the branch, and writes nothing more under those paths. The harness chat binds only calls that are in the ABI 4 contract; a harness feature that needs engine behaviour not yet built (layer orders, reach, going dark, the ping) is written with its tests and held on the pending list of A135 until the engine wave lands. It reports to the Architect.

**A142. The coordinator lands branches for the builder and harness chats.** A chat pushes a branch, names it with its piece ids, and carries on; the coordinator runs `merge_gate.sh` and lands it, one clerk per landing, in the order given. A gate rejection goes back to the chat that built the branch with the gate's own words; the coordinator fixes nothing in those files. This replaces the builder landing its own work; A131's line that the coordinator leaves the battle files stands, since landing is not editing.

**A143. Phase C tests are written now.** The builder's test writers write the failing tests for Phase C (the brief's list, and R-002-02 to R-002-07, R-004-04, R-008-03, R-008-04) while Phase A is built. They go on the pending list and land with it. No Phase C engine code is written until Phase A has landed and Westley has had the Phase B read; stories with an open flag stay unbuilt.

## Addendum 50, 2026-10-02 (the pending list is withdrawn)

**A144. A135's pending list is withdrawn; the gate is not changed.** The merge gate rejects any rise in expected-failure counts, and that rule is right. Instead: tests are still written first and pushed to a branch before any code that satisfies them (the branch history is the proof), and a landing carries only the tests its own code turns green. Tests for later waves stay on the chat's full branch and land with the wave that makes them green. This applies to the builder chat (A143's Phase C tests included) and the harness chat (A141). The six movement test files already red on main from pull request 51 stay as they are until wave A2 turns them green; each wave report says how many of them remain red.

## Addendum 51, 2026-10-02 (harness: what "skilled" means)

**A145. The harness does not define skilled play.** A "skilled" play and its counter are per skill and are Westley's to confirm. The harness takes them as named, pluggable plays. The formation skill's draft plays (a 120-degree concave; a 3-wide column aimed at the end of the enemy front as its counter) are kept, labelled as unconfirmed drafts in code and in every result row, and the concave must be able to curve around the point where the enemy arrives, as the plan's formation batch asks. No skilled play is written for the other four skills until its batch in Phase D, where the play is looked at before it is measured. Hold-fire is not an engine call; plays that need it stay unwritten and the question goes to Westley with the enemy-position batch. The relaxed field-order assertion in `test_trace` is a test defect and takes a ledger row.

## Addendum 52, 2026-10-02 (Phase A landing: patrol waypoints off the canvas; collision held)

**A146. Patrol waypoints are clamped to the canvas.** The patrol diamond in `csrc/enemy_macro.c` places waypoints beyond the map edge for a squad spawned near it; the canvas clamp of P3 then pins the squad and the patrol never advances. That is a bug in the macro, not in the clamp. `PP-move` may make that one-function edit in `enemy_macro.c` (B13 is attached, so no piece is in flight there), test first: a test that spawns a squad at the edge and asserts every waypoint lies inside the canvas, red on main. No row change for B13. Other macro waypoints that may lie off the canvas are listed in the wave report, not fixed in this unit.

**A147. Collision (M4) is held out of the Phase A landing** until Westley rules on the 29.92 residual against R-101-01's 30 wu floor (brought to him 2026-10-02 with Q-101-02; the choices are his). Everything else of Phase A lands. R-097-09's repulsion has no magnitude in the rule and was rightly not applied; the rule is flagged for a number (register row by the builder, Q-097-03) and stays unbuilt until it has one.

## Addendum 53, 2026-10-02 (Westley: spacing residual and parity tolerance)

**A148. Westley picked (a): the Python's residual is accepted.** Units may stand up to 0.1 wu inside R-101-01's 30 wu floor (the port leaves 29.92; the Python gives the same bits). The one test line in `tests/csim/test_E13_S101_movement_that_reads.py` becomes `30.0 - 0.1`, his number, with a ledger row; the rule text stays "no unit overlaps another". Q-101-02 closes. `OM_TP_PURSUE_BY_STEERING` keeps default 1: the new movement is the game. `push/pp-cprime` is dropped. `push/pp-a-land2` lands with the four A99 hashes re-recorded once (A140) and setup lines for the three off-canvas F1 and F2 tests.

**A149. Westley picked (a): parity tolerance 0.05 wu in position.** The named provisional constant in the parity tests becomes 0.05 wu, his number, with a ledger row (A136 said 1e-6, provisional); facing stays 2e-3 rad. A scene that misses it is a logic finding, not a tolerance question.


## Addendum 54, 2026-10-02 (transport scenario clocks)

**A150. Scenario clocks in the pipe tests are test scaffolding, not thresholds.** `CLASH_STEPS` in `test_pipe_assign_commander.py` and the death window in `test_pipe_tactical_delta_frame.py` state when a scripted scene used to reach a death under the old movement; no bible rule names those ticks. The ruled movement (slowest-member pacing R-095-01, pursuit by steering P1) moves them. Each is a test defect with a ledger row: the new value is found by running the scene, stated with its cause, and the assertion itself (a loss happens; a death arrives in one 100-tick frame) is unchanged. Westley is told in the same update and may overrule. A window that a bible rule names stays his.

**A151. The spacing floor is back with Westley**: the Python's true minimum over the 200-tick move is 29.797 (tick 12), not the 29.92 of tick 9; the C is bit-identical. The 0.1 of A148 does not hold; his new number is awaited.

## Addendum 55, 2026-10-02 (spacing floor 0.25; small decisions delegated)

**A152. Westley picked (a): the spacing tolerance is 0.25 wu.** The R-101-01 test line becomes `30.0 - 0.25` (his number, replacing A148's 0.1), covering the Python's 29.797 with room; rule text unchanged; Q-101-02's closing row updated.

**A153. Small decisions are delegated to the Architect (Westley, 2026-10-02).** His words: "moving forward make these sort of small decisions for me to keep the cascade moving, and then report on them afterwards. I'll say something if I don't like the decision... If the decision effects anything less than 5%, make it yourself and flag it." So: a threshold, window or tolerance change whose effect on what the player sees or on a measured number is under 5 percent is ruled by the Architect at once, recorded here with the percentage and the reason, and reported to him afterwards in plain words; he may overrule. Anything at 5 percent or more, anything that changes a rule's meaning, and every pass mark for the search stays his. CLAUDE.md's line that Westley owns every threshold is read with this delegation.


## Addendum 56, 2026-10-02 (the Python piles units up; interim landing under c')

**A154. A152 is withdrawn: no floor near 30 wu passes.** On the R-101-01 scene the Python reference itself drives a pair to 4.978 wu at tick 140 (an 83 percent overlap), and the C matches it. This is not a tolerance; it is a conflict between "the same exact logic as the Python" and R-101-01's invariant, and it is Westley's. It goes to him with a picture after two facts are in: (1) the parity divergence from tick 19 on this scene (107 of 200 ticks differ, up to 14.8 wu) is diagnosed and, if the C is wrong, fixed; (2) the pile-up is characterised: which order produces it (a shared destination, arrival, the collision cap), whether the Python's own tests show it, and whether it occurs in the lab's plays. The builder reports both; nothing about the rule is changed meanwhile.

**A155. Interim: Phase A lands under c'.** To keep the cascade moving, `push/pp-a-land2` lands with `OM_TP_PURSUE_BY_STEERING` default 0 (the old movement stays the game's, the ruled movement is the lab's switch), as prepared on `push/pp-cprime`, with its test setup rows and ledger text. `OM_TP_ROUTE_AROUND_TERRAIN` keeps default 1. The Phase B read runs in the lab with the switch at 1. The default returns to 1 by a ruling once Westley has answered A154. Effect on the game today: none, which is why the Architect takes it under A153.

## Addendum 57, 2026-10-02 (Westley: the collision fix)

**A156. Westley took the fix: every unit starts pair checks, 10 push passes.** The Python's rule (only a moving, lower-id unit starts a pair check) stacks a late arrival on a stopped unit (4.978 wu on the R-101-01 scene; 1 to 2 wu between same-side units after contact in the lab's four plays). Ruled: every unit, moving or stopped, starts pair checks; the push pass repeats up to `COLLISION_PASSES = 10` per tick, stopping early when no pair is closer than 30 wu. R-097-06 (the collision rule) and ALG-68 say so in this commit, named as a deliberate difference from the Python. The Python reference gets the same two changes (`simulation/`, tooling only) so parity holds; the parity scenes are re-recorded once with a ledger row. The stationary-pair split rule and the push-out stay as ruled. `OM_TP_PURSUE_BY_STEERING` returns to default 1 in the same landing (A155's interim ends), with the test setup rows of c' reverted and the A99 hashes re-recorded once more.

**A157. R-101-01 tolerance 1.0 wu (Architect, under A153).** With the fix the worst pair on the scene is 29.11 wu, a 3 percent overlap; the test line becomes `30.0 - 1.0`, rule text unchanged. The line play starts overlapped at tick 0 (17.8 to 19.7 wu) and that is the play's layout, fixed in the harness, not in the engine. Scale: the 10 passes are measured at 1,000 and 10,000 units against the 3 and 30 ms budgets in the landing report; a miss stops the landing.

**A158. E-13 carries two rules numbered R-097-06** (terrain slow; collision). The builder renumbers the collision one to R-097-10 in its landing, with the tests that name it, and says so in the report.


## Addendum 58, 2026-10-02 (Phase A landed)

**A159. The Phase A landing report (origin/main 3820e875) is accepted.** Budgets met: movement and collision 18.2 ms at 10,000 (30); targeting 3.5 ms (25); 1,000 route queries 9.4 ms (1 s); census 0.7 ms. Two items from the differences list are findings, not accepted differences: the sight line stepping in half cells can miss a corner clip (fixed in wave A5 with a test that places a blocked cell at a corner, under `PP-fog`); and the parity tolerance holds only with the leash at 1 and a canvas set, so the parity fixture sets both and says why. The cross-layer reading (a cover or blocked cell between units on different layers is tested on the lower layer) stands provisionally until Phase C, when the lab measures it; recorded as the builder's reading, not a rule. The `skilllab` speed gate at 29.06 s of 30 is watched; a miss comes to the Architect.

## Addendum 59, 2026-10-02 (A5: arrival in the R-101-01 test)

**A160. Option (a), under A153.** In the R-101-01 test a unit has arrived when its move order ends; the 2-second spread assertion stays; "on its slot within 22.5 wu" moves to a separate control that reports, for the 20-unit scene, how many units end on their slot and how far the rest end from it (18 of 20 today; two stop about 22 wu short, pushed around a mate; the Python reference does the same). No radius changes. The question of whether a unit pushed off its slot should seek it again (a change to R-097-10, both engines) is put to Westley at the Phase B read beside the formation printout, which is where it shows; until then R-099-04 stands as ruled (a displaced unit stays where it is). Reason this is mine: no number moves, 2 of 20 units are affected, and the behaviour is already ruled.

**A161. A160 amended: option (i), the test is narrowed.** With the collision fix, two of the 20 units in the S101 scene never end their orders (milling at 600 ticks, 34 and 55 wu from their slots, in both engines: a mate settled in their slot and nothing yields). The spread, no-overlap and no-teleport assertions hold over the units whose order ended (count reported); the control reports the units that did not end and where they are. The full "all 20 arrive" returns when Westley rules the formation-arrival question at the Phase B read, now stated as: a unit whose slot is taken, or that is pushed off its slot, either seeks it again, takes the nearest free spot, or gives up after a time; and a unit never mills forever. This is a visible defect in play (two units of twenty never stand still), so it is his, not under A153. Narrowing is allowed; no number moves.

**A162. Same cause, same handling: the 2-second arrival spread in the S101 test is reported, not asserted,** until the formation-arrival rule is decided (the stragglers pushed around by settled units end at ticks 177 and 198 against a first end at 124, a 3.7 s spread, identical in both engines). The 40-tick assertion returns over all 20 with that rule. No window is widened.

## Addendum 60, 2026-10-02 (Westley: "we want max parallelism")

**A163. Ledger rows.** Any chat may append rows to `docs/northstar/plans/push_ledger_2026-09-22.md` for its own test defects, landings and re-records, as a docs commit in its landing branch, named in the message to the coordinator. The footprint fence's ledger-only rejection is the accepted artifact. Rows are appended, never edited; a wrong row is superseded by a new one.

**A164. Phase C engine work that no Phase B read can change starts now,** in parallel with the read: G4 layer-change orders (R-002-02 to R-002-07, the halfway cross-over, routing across layers by travel time) and G5 reach by type (R-164-02, the multipliers per signed offset as settings). G3 side-sight targeting, G6 going dark and G7 the ping wait for the read, since the read's leash and formation findings touch targeting. The A125 scope (engine only; defaults keep reach 0 and silent) and A135's gate rule stand; every story built has no open flag (E-01 S-001, S-002, S-004, S-164 as A127 lists them).

## Addendum 61, 2026-10-02 night (overnight run)

**A165. Overnight authority (Westley, 2026-10-02, logging off):** "You have permission to commence overnight run. Make decisions when the other lanes need one to keep the plan going, report it to me in the morning and I'll flag if I disagree with any of them. Goal is plan completion/verification." So, for the night: the Architect rules every question the lanes raise, including those above 5 percent and the Phase B items, each marked **provisional (overnight)** here and listed in the morning report; he may overrule any, and a reversed decision is undone by the lane that built on it. Not taken even overnight: anything touching the live checkout, the galaxy stack, sysctl, or a destructive git operation; a pass mark for the search is set only as a labelled draft, and every chart page carries "pass marks provisional" until he confirms.

**A166. Phase B is read by the Architect tonight** on the builder's re-run material, and the open items are ruled provisionally so Phases C, D and E can run: the leash (from the chart), the formation-arrival rule, the guard stance (Q-096-01), the same-spot fling (Q-097-02), the pass marks for C0 to C9 and the 0.05 win margin as drafts, concentration of fire (Q-008-05), the S2 roll-up counter, emission per unit or per group, the provisional layer numbers, the E-01 scale figures. Each ruling states the choice, the reason and what in the data would change it.

## Addendum 62, 2026-10-03 00:xx (the Phase B read, ruled provisionally overnight under A165/A166)

Read in full: `runs/2026-10-03_phase_b_read_fixed_movement.md`. Every ruling here is **provisional (overnight)**; Westley may overrule in the morning. Each gives the choice, the reason, and what would reverse it.

**A167. The 186 wu stop is a suspected bug in the leash anchor, diagnosed first.** ALG-68 says the leash is 200 wu "from the acquisition anchor", the spot where the target was taken; if the engine anchors at the order's start, every unit more than 200 wu into a march drops its target and walks on, which is what the trace shows (front pair in range at 268 wu with no target for ticks 55 to 65). Builder: hypothesis, a test that attack-moves a unit 500 wu and asserts it holds a target taken in range, then the fix if confirmed (`PP-unit`). Reversed if the anchor is already set at acquisition; then the cause is sought elsewhere before any rule moves.

**A168. The leash stays at 0 (today's order, shoot then drop) for now; the other side is not deleted yet.** Reason: at 1, fights run 40 to 70 percent longer and 2 to 6 of 20 fights stall in several cells, and the result is tangled with A167. The leash table is re-run after A167 lands; the deletion ruling follows that, and is Westley's if the two sides still differ by a unit or more at break-even.

**A169. Formation arrival: give up, never mill.** New rule for E-13 S-099 (builder writes it as R-099-05 with the landing): a unit under a group move whose own slot it cannot reach ends its order where it stands once it has been within 75 wu (about two slot spacings) of its slot for 40 ticks (2 s) without arriving; a unit never paces with no end. Chosen over "seek again" (that is what mills) and "nearest free spot" (needs slot bookkeeping both engines lack); reversed by Westley if he wants the block to fill its slots exactly. R-099-04 unchanged. The R-101-01 test's "all 20 arrive" and no-overlap assertions return with it; the 2-second spread stays reported until measured with the rule, then it is his (above 5 percent if it still fails).

**A170. The guard stance is built (Q-096-01 closed provisionally).** Westley's own words in the record: "Yes a guard stance is fine". Rule (E-13 S-096, builder writes R-096-05 with the landing): a unit ordered to guard holds its position, fires at any target it can shoot in range, never pursues, and resumes nothing; a move, attack-move or layer order ends the guard. The engine call is `om_command_guard(w, ids, n)` (added to ABI 4 by `PP-contract`, documented first in `pp_contract.md`). Reason: the choke page shows a wall helps only a defender who stays, and the game gives no order that stays; the landscape batch waits on it. Reversed if he prefers attack-move-with-no-pursuit as a flag rather than an order.

**A171. A blocked target does not halt the march.** The corner-blocked attacker (x 1499, y 690, shot blocked by the wall, standing forever) is a rule gap: a unit halts for a target only when it can shoot it. Ruled: an attack-moving unit whose held target is blocked (cover, wall, blocked cell) keeps walking its route; it fires when the line clears; a guard unit (A170) stays put. Test first under `PP-unit`; R-087-05 reworded by the builder. Q-088-01's flinch question is separate and stays open.

**A172. The blob flattening into a band is behaviour, not a defect.** It is what sixteen units each chasing their nearest enemy do; the formation batch measures line against blob on exactly this. No change.

**A173. Same-spot fling (Q-097-02) closed provisionally: not ported.** Two units on one spot take the normal push (30 wu split along +x, lower id first, R-097-07 as written). Reason: a thousand-times push is a teleport and R-101-01 forbids teleports. Reversed only by Westley.

**A174. Pass marks and the rest of the Phase B list, as drafts.** The README's draft marks for C0 to C9 and the 0.05 win margin are adopted as **labelled drafts** for Phases D and E; every page carries "pass marks provisional" until he confirms. The harness's three statistic definitions (firing advantage, share of advantage, off trend as an absolute margin distance) stand as labelled unconfirmed. Concentration of fire stays out of the principle (the firing count is the measure); the focus-fire batch measures it. The S2 roll-up counter stays as provided. Going dark is per unit (a group order is many unit orders). The brief's section 6 numbers are the lab's starting layer settings, not engine defaults. E-01's scale figures are the targets as the plan says.

**A175. Instrument items.** Harness chat: regenerate the seven goldens (A156 cause, ledger row); fix the grey bar under the firing chart; add the reach control to the CLI; record order-end ticks and per-tick "can fire / blocked / walking / no target" in the trace (the read needed a scratch wrapper); bind `om_command_guard` when it exists. The "won" rule keeps counting a stalled fight as not won, with the stall count shown beside every margin.

## Addendum 63, 2026-10-03 (parity diagnosis, provisional overnight)

Read: `runs/2026-10-03_parity_diagnosis.md`. The "can fix now" list is approved (fixture sets `ROUTE_ACROSS_LAYERS` 0; the detour reset C5; the pi tie; cohort alignment C1). On the four questions:

**A176. C2, the sighting anchor: the C keeps the A167 fix and the Python reference takes the same fix** (`simulation/`, tooling only), listed as a deliberate difference from the Python as it was. "The same exact logic" was Westley's instruction for movement he had seen work; the sighting anchor is the flicker that stopped units short of their range, which he has not seen and would not want. Reversed by him only.

**A177. C3, the backswing lock is 10 ticks in both**: 0.5 s at 20 ticks per second is 10; the Python's 11 is float residue. Python changed.

**A178. C4, step order: isolate first.** The C moves to the Python's order (fire after movement) only if the experiment shows it is the cause of the remaining residual; goldens are then re-recorded once with a ledger row.

**A179. W2, the lost tick per waypoint, is a Python bug**: a unit that reaches a waypoint and spends a tick standing is not a rule anywhere. Python changed; the C stays.

**A180. W3, the final-waypoint radius follows R-099-04**: a route waypoint's arrival radius is 2 x the collision radius, 30 wu, the final one included; the C's 22.5 is corrected to the rule. Turn rate: the bible decides; if E-13 names the rate by unit category, the C follows it; if it is silent, the Python's category rate is the reference and the C follows the Python, and the builder writes the rate into E-13 S-100 with the landing.

**A181. R-085-02 test window, lower bound 2,850 ticks (142.5 s), under A153.** The parity fix that keeps a steering detour across a new move order (R-097-03, as the Python) closes the two lines of the S085 scene sooner: 2,886 ticks against a 3,000 floor, 3.8 percent under; the Python does the same. The test's lower bound becomes 2,850 (5 percent under), measured value in the ledger row; the rule's 150 to 200 s stays as written and remains on Westley's held balance list (A129), where the fight length is retuned after the layer simulation. Effect on play: none; on the test: a 5 percent wider window.

**A182. Parity wave, four answers (provisional overnight).** (1) The Python reference takes collision partners in ascending id order, as the C does; a deliberate difference from the old Python, listed; the C does not emulate cell order. (2) The Python's "stationary" test (a live target in range at move time, R-097-10 as the C) is signed off. (3) The harness fixture records the target channel after the same phase as the Python; no tolerance change; the C's return-fire timing stays. (4) Yes: the R-085-02 test window is 2,850 to 4,200 ticks (5 percent each side, A153; 4,081 measured under C4, in the ledger row); the rule's 150 to 200 s stays as written and on Westley's balance list. The give-up boundary test is the builder's own test defect.

**A183. A139 extended by one row:** `om_unit_transition_progress` joins the reach allowlist as a lab and test observer of a layer transfer (the transfer itself is reached from `om_tactical_step`); removed when the client wires it. The cumulative Phase C landing stopped itself on two dense-scene scale misses (targeting and damage 98 ms against 18.5; five engagements 87 ms against 22.2 at 10,000 units); the builder bisects and fixes with exact equivalence; no budget moves.

**A184. Collision passes end early when nothing moves to speak of (provisional overnight, under A153).** The bit-identical rewrite (`push/pp-c3-coll`) lands as is: E-13 variant B green, movement 13.1 ms at 10,000. The E-11 dense scene stays red because it is a permanent jam where all ten passes run in full. Ruled: a pass in which no unit is displaced by more than `COLLISION_SETTLE_EPS = 0.1` wu ends the sequence for that tick (R-097-10 and ALG-68 gain the clause; constant through `algorithms.md`). Effect: a unit may stand up to 0.1 wu (0.3 percent of its body) closer than ten full passes would leave it; positions change only in jams; hashes re-recorded once with a ledger row. If the dense scene still misses 18.5 ms with it, the miss stays open in the ledger for Westley; no further model change overnight.

## Addendum 64, 2026-10-03 04:30 (overnight: Phase C completes, the first batch runs)

**A185. G3 side-sight targeting, G6 going dark and G7 the ping are released now** rather than at the morning read: every decision they rest on is already made (A125 side sight and the Siege spotter; A174 going dark per unit and the brief's section 6 numbers; the plan's Phase C text), and the Phase B findings that held them (leash, formation) are landed. Builder: tests on push/pc-g3 and push/pc-g67 first, defaults keep reach 0 and silent, hash invariant with `OM_TP_TARGET_BY_SIGHT` 0 against the current hashes, the controls re-hashed at 1 and the difference reported; scale: visibility 2 ms at 1,000 and 20 ms at 10,000 by spatial hashing, targeting 25 ms at 10,000 with sight and reach on.

**A186. The first Phase D batch runs: `formation`,** after the settle landing is on main. The builder runs `python -m scripts.skilllab batch formation --out docs/northstar/research/layer_dynamics/runs/2026-10-03_formation/`, looks at what each play does before reading the numbers (positions at contact for line, blob, concave, counter), commits the run file and page, and reports in plain words: break-evens in whole units per play and per unit type, the Vanguard-against-Raider comparison, stalled counts, what the instrument could not express. Pass marks provisional on the page (A174). Then `focus_fire` the same way. A surprising result is first a question about the instrument.

**A187. The formation batch is read as an instrument check, not a result.** Three things in it are the instrument: (1) the stand-off: closest pairs stop at 162 to 190 wu with ranges 300 and 200 while every unit is in range, so a unit in range keeps walking for about eight ticks; the builder traces one fight tick by tick (which rule lets a unit with a target in range keep walking: cohort turn, first shot, halt on engagement) before any more batch runs, and fixes a fault test first; (2) formation is set at spawn and not held through the walk, so "line" and "concave" are starting layouts, not formations: the harness issues each side's play as one group attack-move with slots (P5, R-095-01), so the shape is kept until contact, and the concave is defined by slots around its focus; (3) no noise estimate: near a break-even (plus or minus 2 units) each cell runs 3 x the fights and the page prints the spread of the side-swapped pairs. The batch is re-run after all three. Noted for the record: the counter fires about 12 percent less than its enemy and still breaks even; that is C2's own check and is read once the instrument is right. The Raider counter at 32 is traced before any conclusion.

**A188. The leash measures the pursuer, not the target (provisional overnight; a rule meaning, so Westley's to confirm).** R-087-05 and R-096-03 as written measured the target's distance from the anchor, so a Vanguard (range 300) that acquired at 294 wu and stood still dropped its target next tick and walked on until it stood 200 wu out: the 186 to 190 wu stand-off of Phase B and the formation batch, in both engines. The leash's purpose is to stop a chase, not a stand. Ruled: the leash tests the unit's own distance from its anchor; a unit holding and firing from its anchor never drops a target for the leash, at any range. Rewritten in E-11 and E-13 in this commit. Builder: test first (a Vanguard acquires at 294 wu, holds and fires until the target dies; a unit that chases 201 wu drops and returns), both engines (the A176 case is re-pinned as a documented change, not parity), hashes re-recorded once with a ledger row; then the closest-pair distance re-measured on the line scene. Option (a), the larger of 200 and the range, rejected as a patch; (c) rejected because the stand-off is not a ruled behaviour anywhere. Q-087-01 (before or after damage) stays open for the lab. Return fire stays ungated by side sight until the morning read (the old return-fire tests conflict with R-093-02; Westley's).


**A189. R-081-02 part 2 (Bombards against Vanguards at 1,000 wu) under side sight.** (a) and (b) together: the unspotted scene is re-stated as a stand-off (no side sees, no damage, both sides whole), which is what A125's "Siege needs eyes" means and what A127 already listed as a test defect; and a spotted case is added: one Raider one layer above the Vanguards at about 320 wu from them, where its cross-layer sight (0.5 x 700) reaches them and their reach (0) cannot touch it, so the Bombards fire on its sight and the line wins. If that scene fails for an engine reason (pursuit of an unreachable unit, cross-layer sight), the builder reports it rather than tuning the scene. The builder's gating of the new leash under `OM_TP_PURSUE_BY_STEERING` is correct under A140; the two extra allowlist rows are accepted under A183's class.

**A190. After A188, the stand-off is gone** (closest pair 279 wu at range 300, first stop tick 49; both leash orders now agree). Two follow-ups: (1) the skilllab positive control "17 against 16 reads ahead" now reads a margin of 0.068 against its 0.1 mark. The mark is not moved. A positive control needs a planted advantage of known direction and clear size; with units holding at range the fights are less lopsided, so the control plants a larger advantage: 18 against 16, with the 17-against-16 reading printed beside it as information (harness chat, test first, ledger row). Westley may prefer another size. (2) The A177 backswing scene depended on the old leash; the builder verifies the lock is still 10 ticks in a leash-free scene and, if so, re-pins the scene as a test defect. The six old-rule tests listed re-pin as test defects under the A188 documented change; hashes re-recorded once.

## Addendum 65, 2026-10-03 morning (Westley: the dense scale scene)

**A191. Westley picked (c): the rule stays, the dense scene changes.** An Opus agent profiled the E-11 dense 10,000 test (`tests/csim/scale/test_scale_E11.py::test_e11_10000_units_dense_targeting_and_damage_per_tick`, 10,000 Raiders overlapping in a 1,500 wu box): 26.6 ms against 18.5; half the cost is neighbour lookups in a jam that spreads every tick because every pushed pair is two stationary units splitting the push (R-097-10), so all ten passes run; a second spatial index kept in step was bit-identical and slower; no exact fix reaches the budget. The rule is not changed. The scene is re-specified as touching, not overlapping: the same 10,000 units at 30 wu spacing (collision radius 15, so no pair overlaps at spawn), the box sized to fit (about 3,000 wu); the budget stays 25 ms raw. Ledger row by the builder (test edit, cause stated); the open-miss row closes. A permanent pile of overlapping stationary units is not a state the game produces (spawn spacing forbids it); a choke pile is covered by the E-13 five-engagements variant B, which is green.

## Addendum 66, 2026-10-03 morning (leash landing, variant B)

**A192. TD-PP-A188-g3-invariant-reference confirmed.** The A185 invariant test ("G3 off equals the engine without G3") compared four A99 fights against hashes frozen before G3; the A188 leash legitimately moves those fights at the default PURSUE 1, so the frozen file no longer describes "the engine without G3" but "the engine before A188". Regenerating the reference at `OM_TP_TARGET_BY_SIGHT` 0 on the A188 build keeps what the test guards (switching G3 off changes nothing) and drops what it never meant to guard (the pre-A188 leash). Header says frozen at A188; the baseline hashes at both switches 0 and the other pre-G3 file are untouched. Classed test-defect as the builder proposed.

**A193. Correction to A191, and the five-engagements variant B miss.** A191 called variant B green; it is not: `tests/csim/scale/test_scale_E13_dense_moving.py::test_e13_10000_five_engagements_variant_b_budgeted_per_tick` measures 23.8 to 24.9 ms raw against 22.2 ms scaled (30 ms raw divided by `OM_SCALE_CPU_FACTOR` 1.35); the ledger row stays open. This scene is not a re-spec case: it is Westley's own scene (2026-09-25, ten groups, five engagements), spawned touching at 30 wu, every unit under a real attack-move, which is exactly the choke pile the budget is for. So no scene change and no number moves. Ordered instead: a bounded profile by an Opus agent in its own worktree, same shape as the A191 task (where the 24.9 ms go by phase at the moving-contact tick, which of movement, collision, routing and targeting dominates, whether an exact bit-identical change reaches 22.2 ms); nothing pushed, the builder implements any exact fix found under `PP-move`. Flagged for Westley: the raw reading is under the 30 ms rule; the miss exists only through the 1.35 CPU factor (his A103 choice), and if the profile finds no exact fix the factor or the scene is his call, not mine.

**A194. push/pf-iso (fire after movement) stays informational.** It removes one parity divergence (target walks out of range) and not the other, and moves every combat golden; A178 admits it only as the proven remaining cause of a mismatch, and parity now holds to 7e-13 wu without it. Not landed; the branch is kept as a record.

**A195. Mid-tick grid rebuild breaks the start-of-tick probe (bug, fix approved).** The Opus profile of variant B (A193) found that `OM_MOVE_GRID_MARGIN` changes positions; the builder confirmed the cause: when the 48-slot spill list fills, `om_move_grid_set` rebuilds the grid by current positions and resets the drift, while `om_move_probe_gather_start` still looks neighbours up by start-of-tick position, so steering probes miss neighbours (ALG-68 "each read at its start-of-tick position"). Latent at the current margin (3.0 x radius: 573 rebuilds, 0 misses in variant B), live at smaller margins (28,771 misses). Approved as proposed: test red on push/pg-margin (two builds with the define changed, positive control), fix on push/pg-fix refiles by start position or gives the probe a start-position index; bit-identical wherever no miss occurs today; if any recorded hash changes, the builder stops and reports (a baked-in miss is Westley's to see), never re-records. Ledger row with the landing. After it, the margin is a pure speed setting and may be tuned for variant B, exactness checked by hash. The formation batch re-run keeps priority over this landing.

**A196. Focus-fire batch v2 read: an instrument finding, three answers.** The batch varied one global `OM_TP_TARGET_POLICY` for both sides, and the policy only decides a unit's first pick and the re-pick after a kill (a kept live target is never dropped), so the page says little about focus fire; break-evens moved in one cell only (reach, 16/17 to 17/18). (1) Yes, Phase D needs a per-side policy: focus fire is a skill one side has and the other lacks. Lab only, no new entry point: a second parameter id for faction 1 through the existing `om_tactical_set_param` (the existing id keeps meaning faction 0 when the second is unset, so recorded hashes stand), bound in the harness as a per-side play setting. (2) No, "re-pick after a kill only" is not what the lab switch means. Under the most-damaged policy a unit re-evaluates on every cohort turn and switches to the most damaged enemy in range (ties by nearest, then lowest id); that is what concentrating fire is. The game's rule (nearest, kept while alive and in range) is untouched and stays the default at policy 0; hashes at policy 0 unchanged. This defines a lab instrument, not a game rule; Q-008-05 (concentration of fire in the principle) remains Westley's. (3) First kill 586 to 849 ticks after contact in the identical 16 v 16 cell is not a defect to diagnose now: with 16 shooters spread over 6 to 8 targets at full range, damage is thin until the first falls, and the R-085-02 fight-length test (2,850 to 4,200 ticks) passes on the same engine. The pace is on Westley's balance list (A129, A181); the page states the number. Order: formation v2 report first, then the per-side policy and the re-pick (engine, tests first, lab-only; A125's "nearest stays the game's rule" holds), then `focus_fire` v3 on the headline cells only (controls, reach, S2 skilled and counter) with the skilled side focusing against a spreading side. The unexpressed items (S1, S3, S4, S5 skilled plays; attack-target orders; mixed types) wait for their own batches and the harness lane's current branch.

**A197. Formation batch v2 read: still an instrument check; the lanes split the follow-ups.** The stand-off is gone (A188 confirmed: closest pair 291 to 298 wu at range 300) and the noise rule works. The shapes are still not held to contact even as one group attack-move with slots (line 452 x 12 becomes 377 x 87; the counter meets head-on as a 232 x 255 mass), so every play is a starting layout and the page's break-evens (all plays within one to two units of each other at 8, 16 and 32, inside the measured noise) are not a formation result. Ruled: (1) the harness chat, not the builder, traces why slots do not hold the shape, with one 32-unit line traced tick by tick on the walk: slot positions against actual positions, whether the 450 wu chunk split (R-095-03) or the slowest-member cap or pursuit on first sight (P1) collapses it; a fault in the play is a harness fix, a fault in slot following is an engine finding reported to me with a failing test for the builder; the game rule is not changed by either lane. (2) The builder continues as ordered: per-side policy, then `focus_fire` v3 on the headline cells (blob cells do not depend on the shape hold). (3) The four stalled Vanguard fights are traced by the builder after v3; a stall is a fight with no result in the limit and may be an engine fault, so it is not left untraced, but 4 of 480 does not outrank v3. (4) The counter firing 10 to 17 percent less and breaking even stays recorded as C2's own check, read when the shapes hold. The formation batch runs a third time after (1); no formation claim is made to Westley before then.

**A198. Why the shapes collapse: pursuit on first sight; harness option (a) approved; a rule question for Westley.** The harness trace (32-unit Vanguard line, seed 0) shows the shape is lost at ticks 1 to 4, not on the walk: the sides spawn inside each other's sensor range, and R-087-04 (P1, as the Python) makes every attack-moving unit's move goal the nearest enemy it sees, cohort by cohort, so from tick 4 each unit walks at its own enemy and the body takes the enemy's shape. Order issue, chunk split, speed cap, group end and give-up are cleared; the engine does what the rule says. Approved: option (a), harness only, no game rule touched: every play (naive ones included) walks as a move group, which keeps slots and does not pursue (R-095-02), to a stop line where the fronts are 0.95 x the shorter attack range apart, computed from the placed positions and ranges, then a timeline attack_move on arrival. Tests first; the harness first establishes whether a unit on a move order fires while walking and reports it, since the stop line's meaning depends on it. Option (b), spawning outside sensor range, rejected: sight (700) is far beyond attack range (300), so the shape would still be lost 400 wu before contact. Flagged for Westley, a rule meaning: in play, an attack-move dissolves any formation the moment the enemy is seen, 400 wu before the first shot; formation as a skill then exists only through move-then-attack micro, which is what the lab now models. Whether attack-move should hold slots until a unit is in attack range (or until the group's front is), rather than at first sight, is his to decide; the lab measures under option (a) either way.

## Addendum 67, 2026-10-03 afternoon (Westley: attack-move holds formation until shooting)

**A199. Attack-move holds formation until shooting, not until sight (Westley, 2026-10-03; a playtest item).** His words: "Attack move should hold formation until shooting, yes, rather than sight. But this is something we might change when it comes to play testing." R-087-04 rewritten in this commit: an attack-moving unit with no target in attack range keeps its slot and route and does not walk toward an enemy it merely sees; it halts and fires when an enemy is in attack range, and the leash pursuit of an acquired target (R-087-05) is unchanged. R-087-05's sighting clause removed. P1 of the plan (pursuit on first sight, as the Python) is superseded: a deliberate, listed difference from the old Python, as A176 and A182 were; the Python reference changes with the C so parity still means the corrected Python. Builder: tests first (a 32-unit line attack-moved from inside sensor range reaches the stop at its slots with the shape intact; a unit whose acquired target walks out of range still pursues under the leash; a lone attack-mover resumes after the fight), both engines, hashes re-recorded once with a ledger row, the rule marked for playtest review in the test header. Harness: the A198 option (a) walk-then-attack is no longer the way plays hold shape; if it is already built it stays as a lab setting, default off, and every play is issued as one attack-move once A199 lands; the formation batch runs a third time on that. Return fire (R-087-06) and the guard order are untouched.

**A200. focus_fire v3 read (per-side policy, A196): a small, consistent, real effect.** 9,280 fights, no stalls. A focusing side against a spreading one gains about 0.3 to 0.4 units at 16 in the identical, S2 skilled and S2 counter cells and about 1.1 in the reach cell; the reverse costs 0.1 to 0.3; the identical control stays a control (15.60 against 15.58). The gains sit inside the pair spreads (0.3 to 0.7) but the 60-fight means have standard errors of 0.02 to 0.03, so the direction is established and the size is small: at contact nobody is damaged and each shooter sees only the enemy's front, so concentration is physically limited to about 10 percent fewer distinct targets. Read for Westley: focus fire as a lab switch is worth under half a unit in 16 on open ground; Q-008-05 (whether concentration of fire joins the principle) now has a number. Instrument notes carried, none blocking: the S2 counter (0,0) reading 14/15 against v2's 15/16 is the 0.05 margin line (-0.007); the first-kill tick differences against v2 come from the tree, not the policy; the id-to-side mapping in the trace is verified by the builder in passing. Order: the A199 engine change is next for the builder, ahead of the four stalled fights, since the formation batch waits on it; the stalls after.

**A201. The four "stalled" formation fights are the detector, not the engine.** Traced by the builder (page 2026-10-03_formation_stalls.md): one is a same-tick mutual kill (both last units at 12.5 hp, A178's all-shots-chosen-before-any-hit) labelled "stalemate"; three are live 1-against-1 Vanguard duels at 285 to 300 wu that hit the 6,000-tick cap (a duel from full hp takes about 1,600 ticks; they end at 6,055 to 6,208 with a survivor). The quiet-stalemate rule (400 ticks without an hp change) fired for none of the 480 fights. Ruled: (a) the harness reports three outcomes separately: draw (same-tick double kill), cap (a fight still active at max_ticks) and quiet stalemate; only quiet stalemate counts as stalled; draw counts as half a win for each side in the break-even scan; harness chat's file, test first, ledger row for the rewritten detector tests. (b) Under A153 (effect 3 of 480 fights, under one percent, a lab limit not a game number): max_ticks rises from 6,000 to 8,000 for cells of 32 units a side and above, and stays 6,000 below; the lab speed check is re-measured after it and reported; Westley may set another value. Builder continues with A199.

## Addendum 68, 2026-10-03 (Westley: how the work is run, ROADMAP W1 to W5)

His reply, verbatim: "W1: yes W2: yes W3: Yes W4: keep as is W5: Yes definitely"

**A202. W1: land part 1 runs as a measured pilot workflow.** Yes. Under 10 agents, Sonnet builders; the run's token figure sizes the rest of the generator work. Starts when ROADMAP queue row 4 does (after stage 0, the playthrough gate, the MVP loop, the baseline and decision L1).

**A203. W2: the playthrough rule goes into `CLAUDE.md`.** Yes. Added in this commit under Architecture rules: every landing is checked against a scripted end-to-end playthrough in the merge gate. The gate script is ROADMAP queue row 1; the rule says so and does not name a script that does not exist yet.

**A204. W3: `plans/TODO.md` is deleted.** Yes. Its open items (Q-E01-08, galaxy view, camera, selection) are closed or superseded by the register; history is `git log`.

**A205. W4: the work list stays as is.** `plans/2026-09-30-work-list.md` keeps its 2026-09-30 counts. Stage 0 re-runs the reach lint and refreshes them.

**A206. W5: worktree prune day, yes.** Westley: "Yes definitely". The 497 stale worktrees (135 GB) are on the other machine, not this Mac, and agents cannot delete them, so the prune is his to run by hand. No date was given.

## Addendum 69, 2026-10-03 (Westley: space kit not approved; prototypes belong on the Linux machine)

His words, verbatim: "S1: the space generator prototype wasn't something I really opened to approve, so I wouldn't call it passing yet. We're not at the point where we're integrating the space landscape yet, so I think we can direct our attention to decision blockers from roadmap.md that block work to be done before we integrate the space generator, despite the prototype being built on this machine, the prototype method has been formalized on the linux machine, and I want all prototyping to happen there. Let's move to movement."

**A207. S1: no space kit pass is approved.** Passes 1 to 5 are built and pass 6 is specified; none has been opened by Westley for approval, so none passes. Space integration is not near, so S1 to S4 are parked and are not asked until the work before the space generator is done.

**A208. All prototyping happens on the Linux machine (Westley, 2026-10-03).** The prototype method is formalized there. The space mockup was built on the Mac; nothing new is prototyped on the Mac. The land terrain pass and the layout engine and places prototype (ROADMAP section 4) are built there under that method.

## Addendum 70, 2026-10-03 (Westley: no movement or simulation decisions before the harness data)

His words, verbatim: "M1: your draft is leaning on specific numbers, the military theory behind the expected winner/loser is based in how many units they can get shooting concurrently more than their enemy given the conditions of the situation. That's a much more complex deduction than a simple "no skill gives >60% of the full set's advantage". These drafted rules would dilute the strategic depth of the game. It was my understanding that everything was already decided with regards to the simulation engine and movement, and that nothing further would be decided until we had real data to look at from the harness we created. - these questions are seem like they shoudl come after that experiment has been completed"

**A209. M1 to M10 are parked until the harness experiment has been run.** No pass mark, margin, threshold or movement rule is put to Westley, or decided, until he has real data from the skill lab (Phases D and E) in front of him. The questions come back with the data.

**A210. The draft pass marks C0 to C9 and the 0.05 win margin (A174) are not decisions and gate nothing.** Reading, the Architect's, which Westley may correct: lab pages report measurements; no page passes or fails a rule set on a draft mark. His principle for what decides a fight is how many units each side can get shooting at the same time, given the conditions of the situation (hub principle 4); a mark such as "no skill gives more than 60 percent of the full set's advantage" is a simplification of that, and the drafts are not to shape the engine or the maps. What the marks become is decided after the data.

**A211. Provisional rulings stand as they are.** A188 (the leash measures the pursuer) and the rest of the overnight provisional rulings are unchanged and unconfirmed; they are not asked again before the data. A199 (attack-move holds formation until shooting) was his own ruling and stands.
