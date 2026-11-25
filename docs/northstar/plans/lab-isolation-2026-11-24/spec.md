# Lab isolation: stage 3 re-judged part by part under changed movement (2026-11-24)

Docs only. Not a story and not a bug fix: a measurement plan (Westley 2026-11-24). Method: for each piece, one test-writer agent writes the failing tests, then one different implementer agent builds against them; the chat drives both. No code or test is written by this document.

## 1. Goal, and the rulings it carries

Westley, 2026-11-24: "I'd like to go back to stage 3 and do some movement/vision only isolation testing to verify all my rulings on specific layouts still stand given we're changing the movement physics. Adding pieces like roles AND specific layouts requires looking at the scoring system."

The measure is the lab's own ("where the lines cross", `docs/northstar/research/layer_dynamics/README.md` sections 1 to 5, conditions C0 to C9). The plan is `docs/northstar/research/layer_dynamics/decomposition.md` (arms R, F, P, W; DECIDED 2026-11-02, never built, held until the lab finished). His request lifts that hold for stage 3 only. Goal: for each of the four stage 3 layouts, find which part (movement, vision, a role pair, one ground feature) first changes between the engine he approved and the engine now, so a changed picture has a named cause.

Preconditions, binding on every piece (sources in brackets):
1. Depth is not one number. "it depends on the number of units that can get shots, not a basic ratio ... That will indicate the quality of the choke, not just that they should do *1.3x* better" (README 2). On the weak edge of the triangle: "it does not have a headcount ... Strategic depth can't be diluted to a specific number as simple as that" (2026-11-02, decomposition 2.3).
2. The lines cross in several places. "The *lines* can cross in multiple locations" (2026-10-01); "find *multiple* points where the *lines cross*, not just one configuration" (2026-10-15). A part reports a curve or map of where it crosses, possibly several regions, possibly none in range. A report naming one number per part is incomplete.
3. No single headcount, ratio or pass mark. Flags are signals, never verdicts: "only a signal, not a conclusion" (L-0104). A configuration is invalid only by a rule he states; today only L-0102: "siege is designed to beat line, even double the force of line shouldn't beat siege" (2026-11-02).
4. Thresholds are Westley's. Every number this spec needs is named `DRAFT-...` and listed in section 8; none is invented here.
5. Same units, same values on both sides ("Each 'era' will have both sides fighting the same units, same values", 2026-10-13). An arm changes one thing and rescales nothing in its favour.
6. Every arm keeps its mirror control (C0: the larger force wins; a control, not a scenario).
7. One attack-move click per side at tick 0, never another: not from the runner, a layout or a test (`DEC-one-click-2026-11-18`). A fight that stalls under it is a finding about the units, not a reason to add an order. A trap's holding groups get theirs when the trap springs.
8. Findings are never smoothed over: a part that fails where the whole crosses is a finding with its picture (decomposition 2.7). Draws are lab bugs: both sides alive at the end means trace the bug, not accept it (memory, 2026-11-18). Units stuck behind the firing line are expected (2026-11-19); counted, not flagged.

His stage 3 rulings, the rows this plan re-judges (`DEC-stage3-layouts-2026-11-05`, rows in `arena/approved.toml`, ledger rows in `approved_scenes.toml` on branch `s/look-judge-rig`, worktree `/home/westopoli/Projects/om-wt/look-judge-rig`, path `docs/northstar/story_reviews/westley/approved_scenes.toml`):

| Layout | Kind | His words (verbatim, `heuristics.md` and `catalogue/verdicts.md`, 2026-11-01) | predict_rate (side A) |
|---|---|---|---|
| L-0055 | chokepoint | "Blue is expected to win 98% of the time." | 0.98 |
| L-0073 | city | "blue expected to win 75% of the time" | 0.75 |
| L-0084 | slope (redrawn from SIT-0109, 40 v 56, hold:A) | "spread out blue in an arc, blue expected to win 60% of the time" | 0.60 |
| L-0039 | cover | "cover: rejected, ... red is expected to win 75% of the time" (cover is worse off) | 0.25 |

Stage-level approval, 2026-11-05: "I rule approval on stage 3, we are go to move to stage 4" (`ruled.md`, `DEC-stage3-seen-2026-11-05`); there was no per-fight verdict. The four fights are approved as fights, each beside its control twin, 20 seeds each. `crossings.md` holds no stage 3 per-fight row (his per-picture reasoning for L-0055 to L-0083 is owed, `DEC-stage3-layouts-2026-11-05` says so); the plan quotes only what exists and prints "no per-picture verdict" where it does not. `predict_rate` is his target, shown beside the measured rate and never scored (`heuristics.md`). The only numeric rule he has stated for roles is L-0102 (16 Bastion v 32 Vanguard, denied as a roster finding, `crossings.md` line 18).

## 2. Versions compared

All runs deterministic, same seeds (20 per fight as approved, seed 10 for the clips), same layout files.
- V-then: the engine at `4fa618ce78349fcc077ce552753131e737ae2cea` (stage 3 approval, 2026-11-05) with its own lab. Run from a `git archive` of that commit in a scratch directory, exactly as the `reopen_command` field in `approved_scenes.toml` does. Never checked out in the repository.
- V-now: main at the time of the run (the SHA is printed on the page).
- V-fix: the movement fix when built, a later column. Not run until it lands (section 7).
The question per cell: does his ruling still hold, and if it changed, which arm differs first. The lab at V-then and at V-now differ in more than the engine (rule checker, one-click rule, regression harness); the runner uses each version's own lab for its own column and records which lab SHA ran, so a changed number is never blamed on the engine alone. Where a V-then measure does not exist in its lab, the cell says "not measured at V-then", never a blank or a zero.

## 3. Arms for stage 3, in order

Reuse, do not rebuild: `scripts/skilllab/arena/run.py` (`fight`, one layout, one seed), `regression.py` (the approved set, with control twin), `rate.py` (first shot, rate against `predict_rate`), `closeup.py` and the streaming recorder (clips), `scripts/skilllab/breakeven.py` (`find_break_even`: scan with refinement near every flip and the side-swap control) over `scan.py` (cells, jobs), `firing.py` (`count_able`, `count_weighted`, `parity`), `rows.py` (`fight_row`, `write_rows`), `evidence.py` (agreement words, `Thresholds` with no defaults), `report.py` and `arena/page.py` (page). The break-even scan "rstar" named in notes is `breakeven.py` today: bisection by default, every headcount with `--full-scan`, 8 to 48 against 16 (README 4). Roles: `scripts/skilllab/engine.py` `_BUILTIN` and `coverage.py` `CATEGORY`: Vanguard and Warden are Line, Raider and Interceptor are Strike, Bombard and Bastion are Siege. Triangle multipliers (`csrc/om_constants.h:518-526`): Line to Line 1.0, Line to Siege 0.75, Line to Strike 1.5, Siege to Line 1.5, Siege to Siege 1.0, Siege to Strike 0.20, Strike to Line 0.75, Strike to Siege 1.5, Strike to Strike 1.0; `firing.py` `count_weighted` uses them as the type-weighted prediction.

Every arm: mirror control first; sight off unless stated; one click per side; both sides the same units; deterministic seeds; reports curves and regions, never one pass mark.

**M (movement only).** On: one role (Vanguard) both sides, attack-move at tick 0 to the layout's shared point, flat featureless ground (the control twin of each stage 3 layout with its features emptied, `run.control_twin`, plus one plain flat field), mirrored placement. Off: sight, features, roles other than Vanguard, abilities. Reports:
- Arrival and finishing, per unit: the stopping check. Of alive units at the end of the fight or at the tick cap, count those with an active order and no progress; orders ended short must be 0. Any unit counted is listed by id with its tick and place, a finding, not a pass or fail.
- Spread over time (distance from the side's centre of mass, every K ticks), idle counts split behind the firing line and in front of it. Behind is expected and counted separately; in front is the one to look at.
- Time to contact (first tick with a shot), overlap pairs (two living units closer than the engine's body distance, per tick, max and total; same measure as the L-0080 overlap files).
- Headcount scan: 8 to 48 against 16, and 16 against 16 mirror (C0: the larger force wins, break-even near equal). Reported as the cell map with the flips marked, not as a verdict on where equal sits.

**V (vision only).** At stage 3 sight is off, so V is the sight, notice and leash behaviours isolated on flat ground, with one holder (guard stance, one order at tick 0 as its layout names) and one attack-mover, Vanguard both sides, mirrored, no features. Sight on is the stage 4 rule set; V uses only the rules the stage 4 rows already approved and adds none. Reports: first tick each side sees the other; sensor distance against notice distance per side (both numbers read from the engine, printed); whether the holder steps, fires, returns (leash, R-096-03 and its stage 4 rewrite); stand-off count (units arrived beyond each other's notice distance, `DEC-standoff-fix-open-2026-11-18`: found, never fixed here); time to first shot. Compared with M on the same ground, so a difference is vision's.

**R (roles).** On: flat featureless ground, two roles, mirrored positions, one orders rule. For every ordered pair of the six roster types (Vanguard, Warden, Raider, Interceptor, Bombard, Bastion; one pair per cell, 36 ordered pairs, 15 distinct up to side swap), scan break-even and firing-count curves as headcount varies (scan style is open, section 8). Reports: curve or map, flips, every crossing region, units firing over time; the count-only and type-weighted prediction beside the result; the direction the triangle points beside the direction the fight went. A pair whose result points against the triangle is shown, not flagged. The only flag is a contradiction of the L-0102 sentence: Bastion (Siege) against Vanguard (Line) where the Siege side loses at twice the Line headcount. L-0102 is the one reproduction (it was at V-then "B wins, 7 left, tick 6080").

**F (one factor).** Roles neutral (Vanguard both sides), one ground feature alone, as the stage 3 layouts draw it: chokepoint (L-0055), city (L-0073), slope (L-0084), cover (L-0039). Each fight runs beside its feature-free control twin (same positions, features emptied, `control = "ground"`). Reports per feature: what it does to units firing over time and to the crossing compared with its twin, `predict_rate` shown not scored. The factor list is provisional and expected to grow (decomposition 3 and 4); these four are the stage 3 list.

**P (pairs).** Role x feature for each of the four layouts, only where the triangle and the layout predict an interaction (a role the feature helps or hurts: Siege inside the city, Strike over cover, Siege or Strike at a chokepoint mouth, any role on the slope's upper band). The list of pairs is written by the chat from the F results and shown to Westley before running (a case where "whether two factors that fail alone cross together", decomposition 3). No pair is run on a guess.

**W (whole).** The four stage 3 layouts as authored and approved, 20 seeds each, sight off, with the control twin. The result the lab reports today.

Readings per configuration (written without a threshold): all pass; parts pass and whole fails; a part fails and the whole crosses; all fail. A part "passes" when its measured crossing region contains, or lies on the side of, his stated direction (a side wins that he said wins); "fails" when it lies on the other side; no part is read where he stated no direction (marked "no stated direction"). The reading is a label on the row, not a gate.

## 4. Measures per run

Reused as they are (cite the file): result (`side0`, `side1`, `draw`, `cap`), survivors, margin, ticks (`run.py` document); units firing over time with the opening window (40 ticks, DRAFT-opening-window-40, Westley's) and the whole fight (`firing.py`); count-only and type-weighted predictions and `agreement` word (`evidence.py` `row_agreement`); break-even headcount, flips, `multi_flip`, `ceiling_hit` (`breakeven.py`); `predict_rate` and the measured gap `band_gap`, shown not scored (`rate.py`); the F0 rule-checker result (`scripts/skilllab/invariants.py`, listed `violations`, `invalid`) where the version has it.
New (small additions, a new file `scripts/skilllab/arena/isolation_measures.py`, no change to the frozen engine or its contracts): per unit arrival and orders-ended-short count, spread over time, idle split behind and front, time to contact, overlap pairs, sensor against notice distance, first-seen tick, the V-then/V-now/V-fix row key. All derived from the fight document and the engine's own queries, in the lab, Python only. If the V-then lab lacks a field the runner does not synthesise it.

A `draw` or `cap` in any cell marks the cell `defect`, never a result (Q-LAB-03); a fight the rule checker marks `invalid` is listed with its rule and not ranked.

## 5. Comparison output

Per stage 3 layout, one row (the table the page leads with):

| layout | his ruling (verbatim, date) | V-then result | V-now result | same or changed | first differing arm |
|---|---|---|---|---|---|

"Result" is the winner at seed 10 plus the winner counts over the 20 seeds, survivors and ticks; `predict_rate` and the measured rate beside the ruling, shown, not scored. "Same or changed" is `same` when the winner count over the seeds is identical at both versions and `changed` otherwise, plus the number of seeds that flipped; it is never "regressed" or "improved". "First differing arm" is the first arm in the order M, V, R, F, P, W whose reading differs between versions, or "none, the whole differs only at W". Every `changed` row carries its control twin row and its decisive clip. Open with the sentence for each layout in soldiers, not ratios (README 5: "beats 17, loses to 18").

## 6. Delivery

One artifact page (claude.ai artifact, his channel, memory `feedback-artifacts-for-viewing`, 2026-11-24), a standing page kept current: updated after each arm lands and each time a movement change merges, always showing the most recent stage (his 2026-11-24 request). Contents: the comparison table; per-arm tables and curves (break-even maps with flips, units-firing lines labelled, never one number); the DRAFT list; the lab SHAs; then MP4 clips of the decisive runs: those the comparison marks `changed`, one `same` per layout as a reference, one L-0102 reproduction, one M stopping-check offender if any.
Clips are rendered by the real Godot fight replay with the r6 recipe in `/home/westopoli/Projects/om-wt/engine-rules-baseline/r6-clips/` (`tmp/rec.py` streaming twin of `closeup.py`, `tmp/render.sh` xvfb render of `scenes/proto/fight_replay/fight_replay.tscn` under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, `tmp/enc.py` and `tmp/poster.sh` ffmpeg H.264 at 20 fps, tick counter on screen; see its `out/L-0054-stage1.mp4` for the form). The recipe lives in a worktree that may be removed: piece LI5 copies the three scripts it needs into `scripts/skilllab/arena/` (clips) as new files, citing the source. Each clip is captioned with layout, seed, version, tick range and its row on the table. Clip sizes follow the recipe (CRF to keep a page loadable); fight files are scratch, not committed.

## 7. Pieces

Each piece is one Sonnet's work. Test-writer and implementer are different agents; the test-writer writes failing tests first, each naming what it proves (an arm, a measure, a precondition from section 1). Tests are whole-run on real lab fights, not unit scenarios. Constraints (CLAUDE.md, binding, as in `plans/engine-rules-2026-11-08/spec.md`): contracts frozen (no change to `csrc/ouroboros_sim.h`, `signatures.toml` or the pipe frames); new code in new files, wiring its own commit, last; determinism (same seed, byte-identical fight document; no wall clock or hash-order input); builders never edit tests except in a `Test-defect:` commit; thresholds are Westley's, each a named constant with a `DRAFT-` comment; stale-doc tripwire; one worktree under `~/Projects/om-wt/`, no push, no merge by agents; never the repository checkout.
Memory rule for every run: `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, `-n 2` at most, scans in chunks per layout and per arm, results written to disk per chunk so a kill loses one chunk.

| Id | Piece | Role | Held until |
|---|---|---|---|
| LI1 | Version runner: build V-then from `git archive 4fa618ce7` into a scratch dir, run any layout and seed on either version with that version's lab, write one rows file keyed by (version, lab SHA, arm, layout, seed). `scripts/skilllab/arena/isolation_runner.py` | test-writer, then implementer | free |
| LI2 | Measures: the new movement and vision measures of section 4 in `isolation_measures.py`, plus reading labels (the four readings) | test-writer, then implementer | after LI1 |
| LI3 | Arms M and V (flat ground, one role, scan 8 to 48 v 16 and 16 v 16 mirror; vision isolated) | test-writer, then implementer | after LI2 |
| LI4 | Arms R, F, W, then P (R uses `breakeven.py` over the six roles; F and W use the `approved.toml` stage 3 rows and control twins; P only after Westley sees the pair list) | test-writer, then implementer; R, F, W can be split into three | R after LI3; F, W after LI2; P after he approves the list |
| LI5 | Comparison table (section 5) and the artifact page generator, then clips (r6 recipe copied in, xvfb render, ffmpeg) | test-writer, then implementer; two agents: table and page, then clips | after the arms it shows |
| LI6 | V-fix column: re-run every arm on the movement fix and add the column; page updated | implementer only (no new tests; LI1 to LI5's tests bind) | held until the movement fix lands on main; not started before |

Order: LI1, LI2, LI3 and the F and W part of LI4 (parallel after LI2), R, LI5 page and clips, P (after his list), LI6. V-then and V-now columns need no fix and run as soon as LI1 to LI4 land; V-fix waits. The chat reports once at the end of each arm (not per piece), one page link.

## 8. Rulings and what is still open

Ruled by Westley, 2026-11-24 (asked by the Architect, answered in chat):
1. Arm R scan: ratio first (a), the full grid (b) only for pairs whose (a) shows a flip.
2. A failing part blocks nothing, with one exception: the movement-stopping check (an order ended short, M arm) blocks a landing. Role and layout flags stay labels (decomposition section 4(4)).
3. Arm V also covers the stage 4 sight-on layouts (L-0061, L-0080, L-0083, L-0039 sight twin), not only stage 3.
4. Arm F list: the four stage 3 features for now (chokepoint, city, slope, cover); more are added in a later round. Not asked again.
5. Context since this spec was drafted: the movement rule is variant A (`DEC-movement-sidestep-2026-11-24`, branch `s/movement-sidestep`); the column V-fix is that build. It steers flying units only; walkers (stage 3 and 4 layouts, the beta's ground era) keep their own step, so the isolation tests are also the check of whether walkers still get stuck.

Still his, all `DRAFT-` in the code: DRAFT-opening-window-40, DRAFT-seeds-20, DRAFT-same-or-changed-rule, DRAFT-idle-front-behind, DRAFT-stuck-ticks, DRAFT-clip-fps-20, DRAFT-clip-crf (the scan 8 to 48 against 16 is already his, README section 4).

Sources read: `decomposition.md`, `heuristics.md`, `README.md` sections 1 to 5, `approved.toml`, `approved_scenes.toml` (branch `s/look-judge-rig`), `ruled.md`, `crossings.md`, `decisions.md` rows DEC-stage3-layouts-2026-11-05 and DEC-one-click-2026-11-18, `plans/engine-rules-2026-11-08/spec.md`, `csrc/om_constants.h:518-526`, `scripts/skilllab/` listed above, r6-clips scripts.
