# Spec audit (Sonnet 5.5, fresh, read-only), 2026-10-13

Refutation of `docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md` at 12943829 against the bible and the code (CLAUDE.md "Workflow specs", Audit). Verbatim.

CONTRADICTIONS: Line numbers are spec lines. Evidence is from origin/main.
- Line 31, `OM_TP_FIRING_ARC_DEG` and `OM_TP_ATTACK_MOVE_RESUME` "appended before `OM_TP__COUNT`", with E0 listing only the header, signatures.toml, pp_contract.md and architecture.md (line 47).
  - The settings table `OM_PP_ROWS[OM_TP__COUNT]` is positional (`csrc/tactical_move.c:367-402`). Without two new rows in that table the new params default to 0, so arc 0 and resume 0.
  - E0 does not own `tactical_move.c`, and E3 and E1 touch it.
  - `tests/csim/conftest.py` also needs the `OMTacParam` mirror and the ABI pin (`pp_contract.md:46`). E0 omits it.
- Line 31 says "ABI bump" and line 47 says the pipe is not touched. These are wrong in four ways.
  - `docs/architecture.md:217` documents the `abi` value in the hello frame, so it must change.
  - `om_pipe.c:1927` sends the ABI version.
  - Header ABI is now 7 (`ouroboros_sim.h:29`, signatures.toml `abi_version = 7`). The queued row `VG-CONTRACT-E7` already claims "ABI 7 to 8".
  - The spec never states the new number.
- Lines 31, 47 and 91 treat the params as plain settings, but `tactical_move.c:3425` hashes them into the net section hash and `:3528` and `:3665` write and read them in the save slot (`save.c:161`). The comment at `:3112` says "not saved, not hashed" and is false.
  - Two more params change the save-slot size and the multiplayer desync hash. That makes this a save-format contract change, which the spec never mentions.
  - The queued `VG-W2` is already a save-format 10 to 11 contract piece.
- Line 82, "`python3 -m scripts.skilllab controls` reproduces the golden hashes". Line 49 asks for the same, "arc 360 byte-identical on the three lab controls".
  - `tests/skilllab/golden_hashes.json` is a SHA of the CSV rows (`integration/test_cross_machine.py:3-9, 44-55`).
  - Line 38 changes the CSV columns and line 36 removes `held`, `decided` and `stalemate`.
  - Lines 52 and 36 make fights elimination-only, which changes the fights themselves.
  - The hashes cannot survive L1/L2, so the parity proof is unsatisfiable as written.
  - The golden file also refuses overwrite except with `SKILLAB_WRITE_GOLDEN=force`, and "a mismatch is never patched" (`test_cross_machine.py:5-9`). The spec gives no re-baseline procedure.
  - The engine-only parity needs the old lab run on the new engine, which is not stated.
- Line 49 (E2), "arc gate on acquisition and fire; flanked unit turns at the R-100-02 rate".
  - Facing and turning live in `tactical_move.c`: `:2213` and `:2342` turn only toward a target already held or toward a destination or movement, at `om_move_turn_rate_by_category`.
  - If the arc blocks acquisition (`unit.c` `om_tac_in_reach` around `:2104`), an idle flanked unit never gets a target and never turns. It is permanently blind.
  - The rule that makes a flanked unit turn is missing, and it needs an edit in `tactical_move.c`, which E2 does not own.
  - Q-100-01 leaves the flanked behaviour to Westley (register line 517). Draft (a) is not implementable as worded.
- Line 32, `om_unit_transition_progress(...)` "int". The header (`ouroboros_sim.h:1989`) and signatures.toml (`:6507`) say it returns `double`.
- Line 41 and line 12 of the pieces table say sub-rows `LAB-REV2-E0` to `-E4`. The piece table has only E0 to E3, and the `pieces.toml` LAB-REV2 `size_estimate` says E0..E3.
- Line 20, ruling 7 (radius guard).
  - Both E-13 R-096-08 and register Q-096-01 say the step-and-return engine piece "is pending; the built guard holds and never steps".
  - No piece in the spec builds it. L2 plays and the bible text disagree about what guard does.
  - Register Q-096-01 option (b) is "no new order: defenders placed idle", yet the resolution recorded under "B" is a radius guard. R-096-08 repeats "option (b)". The letters contradict the content.
- Line 22, ruling 10 and `E-01:239`. S-164 still reads "Space eras only, for now" on origin/main, though README line 96 says it was withdrawn. L7 (line 57) lists no epic edit, so the stale-doc tripwire is unmet.
- Line 48 (E1 default 1). `tests/csim/test_PP_unit_attack_move_group.py:132` (`test_R_096_02_group_ends_when_every_member_has_engaged`) and its control at `:149` encode the superseded group-end ruling. The parity and baseline files `tests/csim/parity/*` run group attack-moves, and neither is listed as superseded.
- Line 22 and line 73, arc sweep "360, 180, 120, 90, 60". 60/360 is 0.167x, outside the ruled 0.25x to 4x band (ruling 11, line 21). So ruling 11 and the batch plan contradict each other.
  - The emitting start pair 2.0 and 3.0 is also not "the bible's value". The engine default is 1.0 (`pp_contract.md:115`).
- Line 17, ruling 3: "for a layer play the naive defender runs twice". This is not in README line 88 or the register. It appears only as a proposal draft ("can stay drafts"), yet the spec presents it as a binding ruling.
- Line 53 and line 58, "same type mix both sides". `s1_outrange` "as Bastions" and `s5_vulnerable_away` as "Raiders behind Vanguards" do not say what the other side fields.
  - A Bastion has range 800 and sensor 300 (`om_constants.h:482-483`), so it cannot see what it outranges without a spotter.
- Line 18, ruling 6 pre-flight "unroutable". No public engine path-exists query exists (`ouroboros_sim.h` has only map/route-grid helpers). The spec does not say how the lab decides routability.

UNVERIFIED:
- Line 51, L1 bindings: `get_param` and `unit_facing` already exist (`engine.py:275-285`). Only `transition_progress` and `can_engage` are new.
- Line 50, E3 "the uses at the listed lines": no lines are listed.
  - `tactical_move.c` reads the compile-time macro at about 20 sites, including `#define`s that size the grid (`:95-96`, `:110-111`), and the param table at `:373` is the only reader of `OM_TP_UNIT_COLLISION_RADIUS`. Making it a runtime value is a structural change (the grid cell and margin macros), not a read swap.
  - `unit.c:2557` and `mission.c` spawn spacing keep the macro (`pp_contract.md:78`).
  - The test "radius 10 against 30 changes how many pass a 2-body gap" needs gap geometry the spec does not give.
- Line 58 and line 60, "red reason: today's fight polls hp per tick".
  - The per-tick polling is a performance cost, not a red assertion.
  - `throughput_2026-10-06.md` measures 32 v 32 at 0.37 s and 55 fights/s at 12 workers. The 1.5 s and 90 s marks (246 fights at 3 replicates, about 5 s) would be green today.
  - `test_speed.py` currently only asserts 260 fights under 30 s at one worker.
  - The doc also says no batched-hp public symbol exists (only `om_unit_get_hp`, `ouroboros_sim.h:2119`). Line 60's "existing public symbol" route is therefore empty.
- Line 82 and line 51, `--full-scan`, bisection default, smoke-run command and first-batch command.
  - `__main__.py` has only `controls`, `reach`, `batch` and flags `--out/--factor/--workers/--layouts`.
  - No bisection exists (throughput doc: B10 deferred).
  - No shard owns `__main__.py`.
- Line 58, "extended" `test_cross_machine.py`: it has no 1-versus-12-workers comparison. Both test files need new content, not just thresholds.
- Line 54 vs the file list: `sweep.py` is new, but `scan.py`, `depth.py`, `breakeven.py` and `pool.py` already exist.
- Line 5 and line 9, approval "plan file `lovely-purring-wozniak.md`" is not in the repo.
  - README line 98 says the type-weight target definition is a "draft to be approved by Westley before plan mode".
- Line 52, pre-flight `prefight` values and `ok` rules: no code checks "types cannot fire at the holder's offset" except `profile_reach`, and nothing is specified beyond the name.

MISSING INTERFACES (with the fix the spec should state):
- `om_combat_can_engage` (line 32): state the `module` field (signatures.toml has one per symbol; sibling `om_combat_can_shoot` is in `tactical_move.c`) and the order of checks when several fail (listed 1..5?). Say what it returns for dead, same-faction, stealth or noncombat units. Use `const om_world*` and `uint32_t` as written, and give `symbol_count` in signatures.toml.
- `om_roster_set_cone` (line 32): `type_id uint32_t`, but siblings take `int unit_type`. State the bounds the setter refuses (range hi, half-angle lo/hi, share lo/hi), the module, and where the cone lives.
  - Reach lives in move state, which is saved and hashed. A per-type cone must say whether it is saved and hashed.
- Cone semantics (line 49): the primary target takes full damage, but is it forced to lie inside the wedge? What about the Bombard disc's friendly fire, the offset damage family, and the cone orientation (facing vs target bearing)? Say how a cone combined with a Bombard disc resolves.
- `FightResult` (line 36): the types and units of `firing_window` and `weighted_window`.
  - Per-side float unit-seconds, or per-sample lists? `states` currently is `[(tick, unit, state)]`; say what the reason code type is.
- `agreement` (line 36): what value a `tie` prediction gets, and what a `draw` or `cap` outcome gets.
- Which fields survive in `FightResult` and `Setup`:
  - `winner`, `margin`, `strength_left`, `won` (cell win rule: today needs margin > 0.05 and no stalemate/cap, `skilllab-harness-spec.md` clauses 13 and 15), `WIN_MARGIN`, `DRAW_BAND`, `objective`, `start_distance`, `quiet_from_first_damage`, `approach`, `mopup_interval_ticks`, `defender_side`.
  - `Setup.arc_deg` collides with `Group.params["arc_deg"]` (formation arc).
  - `Setup.point` duplicates `Setup.objective`. Which survives?
  - `cone per type` has no type, and `orders_per_unit` flips default "until the parity test passes" (which test?).
- The L1/L2 seam: L1 owns `firing.py`, L2 owns `fight.py`/`contract.py`/`rows.py`. The calls between them (names, args, return shape of the count, the predictions and the reason codes) are not fixed, so two builders could build different shapes.
- The roster mix for each play at 8..48 (counts per type, per side). The spec only says "identical". The sweep point lists for range-up, damage-up and vision per offset; the arc and cone grids at line 73 are the only explicit lists.
- Knob names in CSV: `knob`, `knob_value` string/float types, `ceiling_hit` bool format, how `baseline` is emitted for plays that have a single baseline.
- Smoke run: "3 layouts, 1 vision point, the controls" has no named layouts, vision value, replicate count, or command.
- The shared point/centroid rule (L2): "centre of mass" of whom, at which tick, on which layer.

NUMBERS NOBODY GAVE:
- `OM_TP_FIRING_ARC_DEG` bounds lo 10, hi 360 (line 31); cone bounds none.
- 3 replicates for the scan (line 25). Controls use 10 (`__main__.py`, harness clause 20).
- "refinement halves, at most two rounds" (line 54).
- Test geometry numbers: 8 Vanguards plus 8 Raiders per side, 600 wu apart (line 48). Collision radius 10, 30 and "2-body gap" (line 50). Damage-up 0.5 and vision 0.5 test values (lines 51, 54).
- "Within the cohort lag" tolerance (line 51).
- Named step factors for the sweeps (ruling 11 requires them named; L4 names none).
- Sweep point lists for range-up, damage-up, vision, emitting joint points (0.125 to 0.25 are given only as a range), and the number of fights in the 4 h batch. At 55 fights/s that bounds about 790k fights, but the batch size is not stated.
- Elimination fight cap (`max_ticks` 12000 default kept?).
- The smoke run size.

OWNERSHIP:
- Queued or pending rows on main already own files E0, E1, E2, E3 need. `owner_lint.is_in_flight` counts any state not attached or done.
  - `csrc/ouroboros_sim.h`, `signatures.toml`, `tests/csim/conftest.py`, `docs/architecture.md` -> `VG-CONTRACT-E7` (queued); also `signatures.toml` -> `VG-W2`, `VG-E-prodslot`.
  - `csrc/tactical_move.c` -> `VG-W2` (queued).
  - `csrc/unit.c` -> `B10b` (pending, never built).
  - The new rows must declare `depends_on` them (or the lint fails), and the spec must say E0 lands after E7 and W2 (ABI and save-format numbers).
- E0's file list omits `tactical_move.c` (param table), `tests/csim/conftest.py`, `docs/architecture.md:217`, and the pinned ABI tests (`test_E02_S020_abi.py:22`, `test_VG_E_contract.py:73`, `test_VG_E_ke5.py:637`).
- E0 also omits `tests/csim/test_PP_settings.py:72`, which asserts `COUNT == 66` and goes red with two new rows.
- E1 vs E2 both edit `unit.c`: they must be sequential rows with `depends_on`. E2 needs `tactical_move.c` for turning, which it does not own.
- E3, E1 and E0 all touch `tactical_move.c`. Only E3 plus "E1 only if" is listed.
- Shard overlaps: `skilllab-harness-spec.md` is edited by both L1 (clause 10, 24) and L7 ("harness spec"). It is currently owned by no row.
- Unowned files that reference removed fields:
  - `plays.py` (mopup, approach), `asym.py`, `positions.py`, `__main__.py`, `ground/highground.py` (stalemate, mopup).
  - About 45 test files reference retired fields (`stalemate`, `mopup`, `approach`, `decided`, `held`; for example `test_fight.py`, `test_scan.py`, `test_rows.py`, `test_trace.py`, `test_states.py`, `test_timeline*.py`, `test_asym.py`, `test_guard_order.py`). Only a few are listed as retired or rewritten (lines 52 to 55).
  - The CLAUDE.md rule "existing tests encoding a superseded ruling listed with the ruling retiring them" is unmet.
- The spec's umbrella row claims files from attached rows, but attached rows do not conflict (`owner_lint.py:46-47`). The real issue is the queued rows above.
- L7 touches `docs/northstar/plans/push/pieces.toml` (owned by attached `PP-ledger`) and register rows (attached owners). Fine for the lint, but the pieces.toml edit by a shard that also needs the records clerk's rows needs ordering.

TEST DESIGN:
- E0 test (line 47) "ABI bump": there is no way to be red for a stated reason without the new number. The existing pins above encode ABI 7.
- E1 negative control (line 48): with `ATTACK_MOVE_RESUME=0` the existing group-end test passes. The scene "reproduces the stall (303 to 336 wu)" is a number from the register, not an assertion.
  - The existing test `test_R_096_02_group_ends...` is red on the built tree after E1, and a ruler/test-defect ledger row is needed.
- E2 arc test: "arc 90 with the enemy behind reads no shot until the unit has turned; the turn takes the R-100-02 time". With the acquisition gate the unit never turns, so this assertion would fail for the wrong reason. The behaviour is under-specified, so the test cannot be written to a rule.
- E2 cone test: file name `test_E11_S085_cone.py` is mis-numbered. S-085 is "Long enough to think" (time to kill, `E-11:102`), and the cone's rule row is R-082-05 (rewrite pending). The arc has no `R-` id at all (Q-100-01 is open), so the "names the S/R it proves" rule has nothing to name.
- Scale S (line 58) is not red on the built tree (see UNVERIFIED). The 90 s mark at 12 workers can be carried by `test_speed.py` only after a worker-capable scan exists. 1-versus-12-worker hash equality needs a new test.
  - `test_cross_machine.py` hashes control rows at one worker only.
  - The golden hash must be re-recorded after L1/L2 (see CONTRADICTIONS).
- L2: `integration/test_contact_real.py` "a holder on guard with the attacker aimed at its centroid eliminates" depends on the built guard that holds, which never steps (R-096-08). Fine on the built order, but ruling 7 describes behaviour that is not built.
- No positive control is named for: the type-weight prediction (agreement table), the cone scenes of L4, the ceiling-hit logic, and the S3 "blind stall" cell. Only L4 vision-0 and damage-up are named.
- "Tests first by a different agent" is scheduled only for E1, E2, E3, L1, L2, S (line 68). E0, L3, L4, L5, L6 and L7 have no test-writer slot in any wave.

ORDER AND LIMITS:
- Wave 1 (line 68) puts E0 as a "contract piece lands first", but "Landing: one clerk" is step 72, after Wave 4. E2 "after E0 lands" (line 70) cannot hold if E0 only lands at the end. Say E0 lands as its own piece before wave 2/3 (CLAUDE.md "contract first").
- Wave 2 has four builds (E1, E3, L1, L2) while the limit is "two build workflows". Say whether that is two workflows of two lanes.
- Wave 3 has L4 "after L1 to L3" and L3 in the same wave: serial inside a wave.
- L4 (wave 3) vs L2 default `orders_per_unit`: flips after E1 lands, which changes golden rows again. Order not stated.
- E2 builds after E1 on the same file (unit.c) and after E0, but no depends_on is stated.
- Open question 2 of the proposals synthesis ("cross-layer cell whose sight is below weapon range stalls") is not settled in the spec. The vision family (line 73, 0.125 to 0.25) will hit exactly that case. Under ruling 1 a capped fight is a lab defect, and STOP rule line 76 says stop "when a fight caps under the pre-flight checks". The overseer would stop on the first vision point.
- Step 73 first batch: "night slot", but no scheduler, owner or ready check is stated. The 4 h mark is a draft with no batch size.

BLOCKERS FOR THE OVERSEER:
- No queued-row `depends_on` and no ABI number: the records step cannot add rows that pass `owner_lint`.
- Save-format and net-hash effect of two new params not addressed (contract piece needs the second Fable audit; CLAUDE.md). The pending audit (lines 93-95) is the place for this.
- Flanked-unit turning is undefined, so E2 cannot be built or tested.
- Blind-stall policy undefined (see ORDER); the first vision-family point will cap.
- The golden hashes and "controls reproduces" check (line 82) cannot pass after L1/L2, and the re-baseline procedure is missing.
- No CLI, command names or owner for `--full-scan`, bisection, smoke run, batch run (`__main__.py` unowned).
- The scale tests are green or ungreen for reasons unrelated to the stated red reason. A builder following "STOP when a mark cannot be met without a new symbol" hits the no-symbol fact in the throughput doc.
- Pre-flight "unroutable" and "no_fit" have no engine query. The builder must invent a routing check.
- The mix per play is unspecified, so L3 builders will invent it, and L3's own test ("identical mix") cannot be written.
- `test-defect` handling for ~45 test files is not scheduled.

VERDICT: not ready. The contract piece E0 collides with queued contract pieces (`VG-CONTRACT-E7`, `VG-W2`), changes the save and net-hash formats without saying so, and omits files it must edit, and the arc and the golden-hash parity checks cannot work as written.

ALREADY KNOWN: Of my findings, the proposals folder (`synthesis.md`, `agent_*.md`) records only these.
- The flanked-unit question (open under Q-100-01, also in `agent_three.md:139`) and the `om_combat_can_engage` contract plus ABI bump (`agent_one.md:55`).
- The R-096-02 group stall and the low-vision stall (synthesis "Contact is not guaranteed"). The synthesis lists the low-vision stall as open question 2, which the spec leaves unresolved.
- The ground-fire / `E-01` S-164 conflict (synthesis "Ground fire across bands").
- The `plays_space.py` asymmetric vision setting, and the emitting pair being inert at base 0.5.
- `arc 360 reproduces today's hashes` (`agent_three.md:93`), though not that the golden-hash file itself cannot survive the CSV change.

The proposals do not mention any of these:
- Queued-row ownership collisions.
- The param table and save/hash effects.
- Hello-frame and pinned-test effects of the ABI bump.
- Missing `tactical_move.c` ownership for E2.
- The wrong return type for `om_unit_transition_progress`.
- The scale marks not being red.
- The unowned `__main__.py`, `plays.py`, `asym.py`, `positions.py` and `highground.py`, plus the roughly 45 test files that reference retired fields.
- The Q-096-01 option-letter mismatch.
