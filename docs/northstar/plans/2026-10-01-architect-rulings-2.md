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
