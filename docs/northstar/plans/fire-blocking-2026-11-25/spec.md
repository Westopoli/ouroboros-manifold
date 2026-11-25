# Fire blocking: units never block fire, enforced in the lab checker and the Godot project (2026-11-25)

Decision: `DEC-units-never-block-fire-2026-11-25` in `docs/northstar/story_reviews/westley/decisions.md`. A cascade of checks, not an engine change: the engine (`csrc/tactical_move.c` `om_combat_can_shoot_from`, ~2959) already never consults a unit, and the docs are being aligned to it by another agent (worktree `sidestep-docs2`). This spec makes the lab checker and the Godot project hold the same rule, and makes the docs unable to drift again. Method and Constraints are those of `docs/northstar/plans/engine-rules-2026-11-08/spec.md` and `docs/northstar/plans/movement-sidestep-2026-11-24/spec.md`; their Constraints and Test architecture bind (stated again below where they matter). Draft only: nothing here is built.

## What "the beta" means here (Westley, 2026-11-25)

"The Godot project is the main program containing the beta code and is the canonical main version of the game." So two things are held to the rule: (1) the lab checker (`scripts/skilllab/`), and (2) the Godot project at the repository root (`project.godot`, `autoload/`, `scenes/`, `scripts/`, with the C engine `csrc/` behind the pipe). The beta staircase file `docs/northstar/story_reviews/westley/beta-staircase.md` is the plan, not code.

## 1. The rule, and what it is not

Westley, 2026-11-25: "The rule is units never block fire; only cover, walls and ground do." R-098-01 (E-13), extended to friendly and enemy, alive or dead. A shot is blocked by exactly three things, R-098-02: a cover disc (up to its height), a blocked wall or box cell, ground (the era's terrain sight test).

Not this rule:
- R-087-09's firing-spot walk stays as is: a unit whose line is blocked by cover, a wall or ground steers to a clear spot, and gives the target up after 1 s. It never treats a unit as the blocker.
- Open Q-087-10 (attack-movers release and walk their goal instead of the spot walk, `csrc/unit.c` ~2656) is not decided or touched here.
- Sight (who is seen) and acquisition are not changed.
- The engine, `csrc/ouroboros_sim.h`, `signatures.toml` and the pipe frames are not touched. A piece that finds it must change one stops and reports; the chat opens a contract story.

## 2. What "enforce" means at each layer

### (a) Engine: pinned, not built here
The csim test `tests/csim/test_E13_R098_01_units_never_block_fire.py` is being written in worktree `/home/westopoli/Projects/om-wt/fire-tests` (branch `s/fire-blocking-tests`). This spec references it and does not duplicate it. Its landing is a gate for the regression piece (FB8). Note the stale skeleton `tests/csim/test_E13_S098_firing_through_friends.py` (generated stub, one assertion, no whole-run, no enemy or dead unit); FB6 lists it for the chat to retire or fold into the new file.

### (b) Lab checker: a new whole-run predicate `R-098-01`
New module `scripts/skilllab/invariants_r098.py` (a new file, like `invariants_r5.py` and `invariants_r6.py`). It is not registered in `invariants.py`'s `RULES` until the wiring commit (the last commit of FB3). Entry shape as the other modules (read `invariants_r6.py` first). It is independent of the engine's `can_shoot`: it computes from the fight file's positions.

For every unit-tick in a whole fight it asks: was the unit ready, did it hold a living target in range and in sight, with no cover disc, wall rectangle or ground on the segment, and was any other unit within `DRAFT-unit-on-line-radius` (15 wu) of the segment (any side, alive or dead, endpoints excluded)? If yes, it must fire on that tick or the next (`DRAFT-fire-grace-ticks` 1). A violation `{rule: "R-098-01", tick, unit, detail}` means a unit on the line suppressed a shot.
- Ready: not moving under its own power that tick (R-087-04, reuse the existing predicate's test), not inside the 0.5 s pause after its own shot (R-084-04), reloaded by its own fire history in the file (the gap since its last `fired` tick is at least the smallest gap between two consecutive shots of the same unit type seen in the file, so the checker learns no number from the engine; a unit with no earlier shot is ready), facing inside its arc where the file carries facing.
- Target in range and in sight: range and sight by the same codes `scripts/skilllab/firing.py` computes for codes 1 to 4 (range, sight, arc); the sight rule is the fight's own (`sights` header; sight off means every living enemy is seen).
- No blocker: cover discs, wall, box and ridge rectangles re-derived from the fight's `built_features` and the layout's cover (as `scripts/skilllab/arena/snap.py` writes them), segment tests in Python. Ground: when the fight's era has terrain and the pair's segment crosses ground the checker cannot re-derive from the file, that pair is skipped and counted in a `suspended: ground` tally printed with the result. Never a silent pass, never a guess.
- Diagnostic, not a violation: the same count of ready, eligible, in-sight, unblocked unit-ticks with NO unit on the line that did not fire within the grace. It proves the eligibility test is tight: if this off-line count is not near zero on a standing fight, the writer reports which idle reason the predicate misses (cohort turn, target just taken, backswing) and adds it to "ready" before the on-line count is believed. On-line violations are counted only against a tight baseline.

Second guard, in the same module: `scripts/skilllab/firing.py` code 5 ("line blocked", lines 87 and 148, via the engine's `can_shoot`) must never be raised for a pair whose only obstruction is units. For each pair the lab labels code 5, the checker derives the obstruction independently (cover, wall, ridge; ground counted as an obstruction it cannot rule out) and flags `R-098-01 code5-by-units` when none exists and a unit is within the radius. So the lab's "line blocked" statistic can never silently start counting units. `scripts/skilllab/engine.py:396` (`can_engage`, stub -1 before E0) is read only: no change, noted for the report.

The R-087-09 predicate (`invariants.py` ~430 to 457, and the `shootable` row at ~606, which reads the engine `can_shoot`) stays as it is. It is the other half: the engine says a target is not shootable only for cover, wall or ground, and the new predicate is what stops the engine's answer being trusted blind.

### (c) Lab rows: `shots_through_units`
The isolation arms' measures (`scripts/skilllab/arena/isolation_measures.py`, read-only in `/home/westopoli/Projects/om-wt/iso-int` on branch `s/lab-isolation-int`; the piece waits for that branch to land on main) gain `shots_through_units`: the count of shots in the fight (a row with `fired`, target alive) whose segment has any unit within the radius, using the same geometry helpers as (b), imported, not copied. A page shows the number beside the other measures. The expectation is large and informational: the findings in `/home/westopoli/Projects/om-wt/engine-rules-baseline/fire-through/` put 140 to 309 shots per fight with a unit within 15 wu of the line, so the measure is a count of how often the rule matters, never a pass or fail. It does not change any arm's ranking or any winner.

### (d) The Godot project: the client never decides
The rule for the client: the client NEVER decides whether a shot is blocked; the engine does, over the pipe. Three parts.
1. Inventory (FB1): a read-only grep of the whole project for client-side shot, line-of-fire, sight, targeting or "blocked" logic that could disagree with the engine, each hit listed file:line with whether it consults units. Scope: `autoload/` (the pipe client `c_bridge.gd` and its neighbours), `scenes/` (every `.gd` and every `.tscn` with an embedded script), `scripts/` GDScript, `scripts/qa/rts_detectors.py`, `tests/qa/desktop/` plays and helpers, `scenes/proto/fight_replay/` (the target line drawn from the `fired` row, `fight_replay.gd` ~228, 409, 421; the `BLOCKED_RING_WU` ring, ~29, which marks ground-blocked units from the file's code, not by geometry). The lead's pre-scan (2026-11-25, to be confirmed and completed by FB1): no hit in `autoload/` or the live scenes that computes a line between units; `scenes/proto/fight_replay/` draws what the file says; `scenes/mockups/` blocked-cell code (`toy_sim.gd`, landscape passes) is walk-cost and cell masks, not shots; `scripts/qa/rts_detectors.py` has rubberband, stuck, backwards and dropped-order detectors and none about fire; `tests/qa/desktop/plays/A/test_S_007_cover_and_obstacles.py` is a cover drawing test. FB1 may find more, and reports each.
2. Transport test (real pipe, no Godot): in `tests/transport/` (as `test_pipe_tactical_delta_frame.py` runs `pipe/ouroboros_pipe`). A shooter, a unit and a target on one line; the target's hp falls with a friendly between, with an enemy between, with a dead unit between; and with a cover disc or wall between, the shot is blocked and the hp does not fall. Needs a way to put units and cover at chosen positions through existing verbs. If no pipe verb does it, the writer stops that test and reports (a contract story would be needed); it does not add a verb. The writer dumps the verbs and keys it relies on (test_writer card).
3. Desktop QA play (`tests/qa/desktop/`, the real game through `GodotGame` and `DaemonClient` in `daemon_client.py`): the same scene played through the daemon (`state` for hp, `input` for orders, as `test_tactical_play.py` does): ally between, enemy between, hp of the target read from `state` falls; the cover or wall variant holds hp. Uses the pipe build the way `scripts/play.sh` launches it.
4. Client lint (a test, no engine): under `tests/method/`, a scan of the project's GDScript source (and `.tscn` embedded scripts) that fails if a client script computes unit-on-line blocking: a segment or ray test between two units' positions combined with a loop over other units, `intersect_ray` or `distance_to_segment` or `get_closest_point` used with unit positions in a combat or fire context, or a name matching `blocks_fire`, `friendly_block`, `unit_blocks` and the like (the writer fixes the pattern list from FB1's findings and writes it in the test header; a hit needs a literal `# lint: not fire` marker with the reason). Positive control: a planted GDScript file in the test's tmp dir that does it, which the lint must flag; and the scan runs over today's tree and passes.

### (e) Docs lint
`tests/method/test_docs_units_never_block_fire.py`: scans `docs/bible/`, `docs/northstar/plans/`, `docs/stories/`, `docs/method/`, the epics and `docs/architecture.md` and fails on text saying units block a line of fire: the phrase list the docs agent used (the lines it removed or rewrote, `git diff` of branch of `sidestep-docs2`; the writer takes them from there and lists them in the test header, and adds the obvious variants: "friendly units block", "ally in the way blocks", "line of fire is blocked by units", "units in the line of fire block"). Exempt: `docs/bible_history/`, `docs/reports/`, `docs/legacy/`, and decision rows quoting the old text (`decisions.md`), `docs/northstar/research/`. A hit is allowed only on a line that also says "never" or "not" within the same sentence (so "units never block fire" passes). Positive control: a planted file with "friendly units block fire" in a tmp tree flags. The test reads the tree it is run in.

### (f) Stale comments and the Proof line
- `csrc/tactical_move.c` and `csrc/unit.c` comments that suggest a unit between blocks a shot (FB1 lists, FB6 rewrites only comments, no code; a comment edit in a C file is in its own commit and the movement hash and every golden must stay identical).
- Proof line for R-098-01 in `docs/bible/epics/E-13-movement-and-command.md`, in the format of `docs/method/requirements.md` Proof: `Proof: tests/csim/test_E13_R098_01_units_never_block_fire.py::<name> | whole-run | verified <sha> <date>`, with the second test (qualification 7, reaches the behaviour the way play does) named as the second pointer: the transport test. Written by the chat after landing; agents list it, they do not edit the bible.

## 3. What each test asserts, per tick

Every per-tick assertion stays per-tick (never replaced by a final-state one; a `Test-defect:` commit may not weaken it). Each names `R-098-01` and quotes its text: "Given a ranged unit with a unit between it and its target, friendly or enemy, alive or dead, When it fires, Then the shot lands; no unit ever blocks fire, only cover, a wall or ground does (R-098-02)."

| Test | Asserts | Positive control (green today) | Mutation that turns it red |
|---|---|---|---|
| csim (fire-tests, referenced) | `om_combat_can_shoot` is 1 and damage lands with an ally, an enemy, a dead unit on the segment | the same geometry with a cover disc between returns 0 | `om_combat_can_shoot_from` returns 0 when any unit lies within 15 wu of the segment |
| lab predicate | on every tick of every standing fight, zero `R-098-01` violations; off-line baseline reported | a planted om-fight-2 file: ready shooter, target in range and sight, an ally 5 wu off the segment, no shot for 6 ticks: exactly one violation, on the first tick past the grace; the same file with the ally moved 30 wu away: none; with a cover disc on the segment and the ally removed: none (cover blocks, predicate silent) | a scratch engine build carrying the mutation, one standing fight (L-0054) recorded under it: the predicate goes red; the same run under main stays green |
| code 5 guard | on a pair blocked by a cover disc, code 5 stands and no flag; a pair with only an ally on the line raised as 5 is flagged `code5-by-units` | the cover pair | the mutated build, same fight: flag raised |
| lab rows | `shots_through_units` equals an independent count over a small hand-built fight file (three units, known answer) | the hand file | counting a shot only when the line is clear gives 0 |
| transport | target hp falls tick by tick (read from the delta frames) with ally, enemy, dead unit between; hp unchanged with cover or a wall between | the cover variant | the mutated pipe build: the ally variant holds hp |
| desktop QA play | same, read through `state` while the game runs | the cover variant | the mutated pipe build under the real game |
| docs lint, client lint | as in (d) and (e) | planted files flag | plant a "units block fire" sentence or a unit-on-line ray in a scratch copy |

Each writer reports the mutation it ran and the red line (test_writer card, Proof qualification 5), recorded in the report. The mutation is always on a scratch copy, never on the branch.

## 4. Pieces

Each is one Sonnet agent. A test writer and an implementer are never the same agent; no agent spawns another. Every job (pytest, a fight run, a sweep, a build) runs under `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 -- nice -n 10`, with `pytest -n 2`, in chunks (one test directory or one layout batch per call), never the whole suite at once. Each in a worktree under `/home/westopoli/Projects/om-wt/`, never the repository checkout; commit by path; no push or merge; trailers `Story: fire-blocking`, `Tests:` where a test is added, `Decision: DEC-units-never-block-fire-2026-11-25`. Tests are named with `DRAFT-` constants and `R-098-01`. No agent edits `docs/bible/`; each lists the bible text it finds stale and the chat does it.

| Piece | Who | What | After | Parallel with |
|---|---|---|---|---|
| FB1 | inventory agent | Read-only: the project-wide grep of (d)1, plus the lab consumers of `can_shoot` and of code 5, plus stale C comments (f). Output `docs/reports/2026-11-25-fire-blocking-inventory.md`, a table of file:line, what it does, consults units yes or no, action. No code. | nothing | FB2, FB4 |
| FB2 | test writer A | Lab tests: the predicate, the planted fight files, the code 5 guard, the standing-fight sweep test (chunked), the mutation run. Red because the module is missing. | nothing | FB1, FB4 |
| FB3 | implementer B | `scripts/skilllab/invariants_r098.py`; the wiring commit (register in `RULES`, `run.py` marks a fight `invalid` for it as for the other rules, `SNAPSHOT.md` line) last. Report with the on-line and off-line counts over every standing fight. | FB2 | FB5, FB6 |
| FB4 | test writer C | Transport test and desktop QA play of (d)2 and (d)3, red-or-green honestly: both are expected GREEN on the unmodified engine (the engine already obeys the rule), so the proof is the mutation run, not a red start; the writer states this in the report and ships the mutation recipe. | nothing | FB1, FB2 |
| FB5 | implementer D | Only if FB4's tests expose a real divergence in the client path (a hp that does not fall through an ally in the real game). Otherwise a one-line "nothing to fix" report. A fix is a Godot-side change only, in its own files, with the client rule above. | FB4 | FB3, FB6 |
| FB6 | test writer E, then implementer F | E writes the docs lint and the client lint (e), (d)4, from FB1's report and the docs agent's phrase list. F fixes non-bible hits (plans, specs, stories, stale C comments in their own commit, the stale csim skeleton listed not edited) and lists bible hits for the chat. | FB1, and the docs agent landed | FB3, FB5 |
| FB7 | test writer G, then implementer H | `shots_through_units` in the isolation measures and the page. | `s/lab-isolation-int` on main, and FB3 (shared geometry helpers) | FB5, FB6 |
| FB8 | regression agent (third, read-only on source) | Before and after tables (below), the planted-fight check, the mutation check run by hand on a scratch build, the beta chunk. Report to `docs/reports/2026-11-25-fire-blocking-landing.md`. Also confirms the csim file from `fire-tests` is on main. | FB3, FB5, FB6, FB7, and the csim file landed | none |

Sequence: FB1 | FB2 | FB4 run together; FB3 | FB5 | FB6 together after their writers; FB7 after FB3 and the isolation branch; FB8 last. Each piece's report is one message, once.

## 5. Acceptance

1. Nothing changes in behaviour: fights byte-identical before and after on all 16 standing rows (`docs/northstar/research/layer_dynamics/arena/approved.toml`), recorded with the lab engine, seed 1, the layouts' own orders; compare the frames and ignore the `layout_path` line. The engine is untouched, so any difference stops the landing.
2. The new predicate is green (zero `R-098-01` violations) on every standing fight, with the on-line and off-line counts and the `suspended: ground` tally printed in the report; it is red on the planted fight where a unit on the line suppresses a shot, and red on the standing fight recorded under the scratch mutated engine.
3. The code 5 guard raises nothing on today's fights.
4. The beta: the new transport test and the new desktop play green on the pipe build (`scripts/play.sh --check` first); the Godot project's `tests/qa/desktop` chunk and `tests/transport` chunk still green as before (known reds stay the same list, none added); the client lint and the docs lint green on the tree, red on their planted files; the csim file from `fire-tests` green.
5. Determinism: two runs, identical bytes. `tests/skilllab`, `tests/method` chunks green. Any change to an existing test is in a `Test-defect:` commit naming this decision.
6. The mutation of §3 turns the csim test, the lab predicate, the transport test and the play red on a scratch copy, each recorded with its red line.
7. Played, not just green: the merged build is opened and the ally-between scene is played in the game before the push (CLAUDE.md).

## Docs the change makes wrong, or adds (the chat writes them; agents list)

- `docs/bible/epics/E-13-movement-and-command.md` R-098-01: the Proof line (§2(f)); the docs agent already rewrites the rule text.
- `docs/northstar/story_reviews/westley/beta-staircase.md`, B5 and B8 rows: one sentence each, e.g. B8 "fights in the beta follow R-098-01 (units never block fire; only cover, walls and ground do), decided by the engine over the pipe, never by the client". Not edited by this spec's agents.
- `scripts/skilllab/arena/SNAPSHOT.md` (the new rule in the violations list), `docs/method/requirements.md` only if the Proof format changes (it does not).
- `docs/northstar/story_reviews/westley/decisions.md`: a row for the grace and radius constants once Westley rules them.

## Open for Westley (only the un-ruled)

1. `DRAFT-unit-on-line-radius`: 15 wu, the distance from the line within which a unit counts as "on" it (from the history findings: the old code's body test; it is the predicate's net, it changes no behaviour).
2. Whether an `R-098-01` violation blocks a landing. Default: yes, as the movement-stopping check does, with other flags (`suspended: ground`, the off-line diagnostic) reported and not blocking.
3. Q-087-10: attack-movers walk their goal and release a blocked target instead of walking to a firing spot; the spec does not touch it.
