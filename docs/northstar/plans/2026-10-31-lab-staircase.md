<!-- Copied from ~/.claude/plans/cheerful-baking-codd.md on 2026-11-02 so the plan lives in the repo (H-062); the lab staircase of DEC-lab-staircase-2026-10-31. Rewrite this copy from now on; stage state is in ROADMAP.md section 1. -->
# The simulation lab, rebuilt as a staircase: one verified step at a time

## Context

Westley, 2026-10-31: "I've been asking for a lot of deliverables ... there has been no verified result because we've been stretching too far ... without a verifiable checkpoint, it's hard for me to discern where we're drifting." The lab today is 51 code files (8,767 lines), 190 test files, one batch ever run (2026-10-08), chart never seen. It was built all at once against the whole question (every layer skill, every condition, every headcount) and no step of it has passed his eyes.

His direction: a batched, iterative, verified pipeline. Each stage ends in something he looks at, in the game scene and in a diagram, before the next stage starts. Start at the floor: one ground layer, units move and shoot, no vision rules. Add one factor per stage until every strategic-depth factor is in. Reuse lab code where it fits; his look may change how a piece is written. He authors the situations in parallel as documents that a script turns into lab input with the expected winner.

What this turns the lab into: a pre-placed game. A layout file puts units on a field; the real C sim runs the fight; the game's own 3D scene shows it; a diagram records who won against what he predicted. Nothing in the pipeline is new science: the game already moves, shoots and kills.

Standing rules that apply unchanged: one story, one branch, one `--no-ff` landing (`docs/method/story_loop.md`); tests first by a different Sonnet; Sonnet look reviewer before any picture reaches his folder (DEC-look-reviewer-sonnet-2026-10-31); the eyes gate (no scene story lands until he reports a scene on his display, 2026-10-30); every number below is a DRAFT until he rules; Fable writes no code.

## What exists and is reused (read from origin/main b94fe97f)

| Piece | Where | Reused for |
|---|---|---|
| C engine binding: `new_world`, `register_unit_type`, `spawn`, `order_attack_move`, `order_guard`, `step`, `unit_pos`, `unit_hp`, `unit_facing`, `unit_target`, `can_see` | `scripts/skilllab/engine.py:78-366` | every fight |
| Fight runner: `_register_types`, `_spawn_side`, `_issue_orders`, `_run` sampling loop | `scripts/skilllab/fight.py:23-322` | the arena runner calls these; nothing re-derived |
| Layout file schema: id, situation, landscape, seed, predict, verdict, sides with units {role, x, y, facing, layer}; round two adds `features`, `defender`, per-unit `range` | `docs/stories/H-025.md` "Layout file", "Round two format" | the input of every stage; situations he authors become these files |
| Validity rules R1 to R5 and `check_layout` | `scripts/skilllab/catalogue/rules.toml`, `produce.py` | converter output is checked by the same function |
| 3D shot scene: reads `OM_LAYOUT`, draws units on `Ground3D` plus `Units3D`, features geometry (round two), range rings, legend, `OM_SHOT_OUT` saves a PNG, `qa_state()` | `scenes/proto/layout_shot/layout_shot.gd` (round two on branch `s/H-025-*`, not landed) | the replay scene is this scene plus a frame cursor |
| Review page and verdict apply | `scripts/skilllab/catalogue/review.py` | the stage page lists fights the same way |
| Screen proof on the real display (portal capture) | H-031 piece two (in flight) | proof that each stage's scene is visible |
| Break-even scan and charts | `scripts/skilllab/breakeven.py`, `scan.py`, `charts.py`, `diagram.py` | stage 6 only, after single fights are trusted |
| Terrain and slope knobs (`OM_TP_SLOPE_UP_DIV`, reach table, walking kind) | `scripts/skilllab/ground/scenes_ground.py`, `fight.py:13` | stages 3 and 5 |

Not used before stage 6, and not deleted: `conditions.py`, `plays.py`, `plays_space.py`, `search*.py`, `asym.py`, `transfer.py`, `coverage.py`, `depth.py`, `sweep.py`, `pool.py`, `matchup.py`, `evidence.py`, `summary.py`, `mapreport.py`. They stay in the tree; nothing in the staircase imports them. Whether they are parked or retired is a later ruling with the stage 6 evidence in hand (no deletion without parity).

## The staircase

Each stage is one `H-` story (same template as H-025: a sentence in his words, flag, files, numbers, scene run line, tests, `## Machine lines`). Each stage has four parts that build in parallel on separate files, then one landing, then his look. A stage is **Seen** when he says the fights he watched make physical sense and the winners agree with the predictions he wrote (or every disagreement has a one-line reason he accepts). No stage starts building until the one below it is Seen.

### Stage 0: the floor is visible (already in flight, nothing added)

H-031 piece two (portal screen proof), H-038 part 2 (first scene drawn whatever the window size), H-025 round two landing (the shot scene with geometry). His pending verdicts: H-023 stage window, the twelve round-two pictures, the slab question. Stage 1 branches from main once H-025 is landed; its builder may merge `s/H-025-*` earlier to start.

### Stage 1: two blobs on a flat field

"I place two groups of one unit type on an open field, both attack-move, and I watch the fight happen in the game and see who won against who I said would win."

- Field: `open_field` preset, one layer, no features, no slope, no cover.
- Units: one role per side (DRAFT: Vanguard both sides), headcounts from the layout, both sides `attack_move` to the other's centroid at tick 0.
- Vision: off. DRAFT-sight-off: the arena registers every type with sight radius 1e6 world units, so every unit sees every enemy from tick 0 (the stat is passed in `_register_types`; no C change). If the sim has no sight stat the builder reports it and the stage stops for a ruling.
- Four parts (files, owners, parallel):
  1. **Snapshot contract** (lands first, half a day, its own `H-` story): `docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md` and `scripts/skilllab/arena/snapshot.py` define `fight.json`: `layout_id`, `seed`, `tick_rate`, `frames: [{tick, units: [{id, side, role, x, y, facing, hp, alive, target}]}]`, `result: {winner, survivors_a, survivors_b, ticks, predict, agree}`. Frames every DRAFT-snapshot-seconds 5 s of sim time plus the first and last tick; DRAFT-snapshot-count 10 to 20 per fight (Westley 2026-10-30: 10 to 20 snapshots). Positive control: a frame missing `hp` fails `validate()`.
  2. **Arena runner** (`scripts/skilllab/arena/run.py`, new): `python3 -m scripts.skilllab.arena.run --layout <toml> --seed N --out <dir>` reads a layout, builds a `Setup` through the existing `fight.py` helpers, runs `engine.step` to death or DRAFT-fight-cap 600 s, writes `fight.json` and a `result.md` row. Deterministic: same layout and seed give a byte-identical `fight.json` (test).
  3. **Replay scene** (`scenes/proto/fight_replay/`, new, built on `layout_shot.gd`): reads `OM_FIGHT` (the `fight.json`), draws frame 0 like the layout shot, steps frames with Space or `OM_AUTOPLAY=1` at DRAFT-replay-fps 1 frame per second, shows tick, alive counts and the result line; `OM_SHOT_OUT=<dir>` saves one PNG per frame and quits. Dead units drawn as a flat marker, not removed (he sees where they fell). `qa_state()` keys: `fight_id`, `frame`, `frame_count`, `alive_a`, `alive_b`, `result`.
  4. **Stage page** (`scripts/skilllab/arena/page.py`, new, same shape as `review.py build`): one row per fight: layout id, headcounts, predicted, actual, agree, the frame strip (every PNG in order), the fall map (last frame). Written to `docs/northstar/research/layer_dynamics/arena/stage1/`.
- Scene run line (his): `scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn` with `OM_FIGHT=<path>` (play.sh passes the environment through; the story confirms this or adds `--env`).
- Layouts for the stage: DRAFT 6, his or converted from his documents: open_field at 16:16, 16:32, 32:16, 8:64, 64:8, 128:128, predicted winner each.
- Tests: `tests/skilllab/arena/test_snapshot.py`, `test_run.py` (determinism, cap, result agrees with hp), `tests/qa/test_fight_replay.py` (headless, `qa_state` frame count equals file, PNG per frame not blank; positive control: a `fight.json` with one frame removed changes `frame_count`).
- Done when: he has watched at least three of the six fights in the replay scene on his display, the page is in his folder after a LOOK OK, and he writes a verdict per fight.

### Stage 2: roles and ranges

"Six roles with their real ranges and speeds, mixed on each side, on the same flat field; I see ranges drawn, who fires first, and whether the composition I thought wins does win."

- Adds: all six roles, per-unit `range` from the layout (round two schema), range rings in the replay, `target` arrows in each frame, a per-role survivors table on the page.
- No vision rules yet (sight still 1e6).
- Layouts: his, DRAFT 8: Bombard screen versus Raider rush, Bastion wall versus Vanguard line, equal mixed, and so on; headcounts his.
- Done when: three fights watched, page verdicts written; a role whose behaviour looks wrong to him becomes a game story, not a lab fix.

### Stage 3: the ground pushes back (movement only)

"Walls, buildings, cover boxes and slopes shape where units can walk and how fast; still everyone sees everyone."

- Adds: features geometry from the layout becomes sim obstacles (chokepoint walls, city buildings, cover boxes as blocks; slope band with `OM_TP_SLOPE_UP_DIV`; one travel layer, terrain tiers not planes per R-001-06/07). The arena asks the engine for blocking (the ground lab's preflight route check in `scenes_ground.py` is the pattern) and refuses a layout whose attackers cannot reach the defenders (REJECT line, test).
- Replay draws the same geometry as the layout shot (shared code, no second drawing).
- Layouts: his chokepoint, city, cover, slope situations from the round-two set, with his predictions.
- Done when: he watches a choke fight and a slope fight and agrees the units respect the ground.

### Stage 4: sight

"Fog: units see by sight range, eye height and cover; vantage sees further; the defender on guard waits until it sees something."

- Adds: real sight (the 1e6 override removed), `can_see` recorded per frame (`seen` list per unit), defender uses `order_guard` (round two `defender` key), cover reduces hits per the sim's rule. Replay draws sight as a faint disc per selected unit and marks unseen enemies hollow.
- Layouts: vantage, cover, staging, trap situations.
- Done when: he watches a vantage fight and a trap and agrees who saw whom first.

### Stage 5: facing, arcs and height bands

"Units have fronts; fire cones matter; a height band is a slower climb and a longer sight."

- Adds: `set_cone` arcs from the layout (`facing` is already in the schema), `transition_progress` shown while climbing, band changes in the frame (`layer`).
- Layouts: flank_route (the ridge), slope top versus foot, objective ring.
- Done when: he sees a flank hit a side and the climb slow the attacker.

### Stage 6: where positioning stops deciding (the scan)

"For each layout I approved, scale the headcounts until the better position loses, and show me the break-even on one diagram with arrows at the evidence."

- Adds nothing to the sim. Reuses `breakeven.py` and `scan.py` over the arena runner; `diagram.py` draws one picture per layout with the break-even headcounts and an arrow to the frame strip that shows it (feedback-lab-charts-show-layouts). Headcounts 8 to 256 per side independently (feedback-lab-unit-counts-and-snapshots).
- Done when: he reads the diagram for three layouts and the numbers match what he watched.

### Stage 7 and after: objectives, hazards, time limits, then space

Capture radius and mission objectives (ALG-71, ALG-75), hazard discs, staging timers; then the space era (five layers, flyers, the ping), where the parked space lab (`plays_space.py`, conditions) is re-read against stage 6's evidence and kept or retired. Specified only after stage 6 is Seen.

## His authoring lane (starts now, independent of every stage)

- Folder `docs/northstar/research/layer_dynamics/situations/`, one file per situation `SIT-0001-<kind>.md` from a template `TEMPLATE.md` (written in the stage 1 spec): kind, field preset, feature geometry in words plus the numbers from the round-two schema, side A and side B rows (role, count, where, facing, range), defender, predicted winner and one sentence why, which stage it is for.
- Converter `scripts/skilllab/arena/situations.py` (stage 1 part 5, small): reads `SIT-*.md` tables, writes `L-NNNN.toml` and `.json`, runs `check_layout`, prints `CONVERTED <sit> <layout>` or `REJECT <sit> <rule>`. He writes words and tables; the script makes numbers. A situation that needs a feature the current stage has not reached is converted and queued, not run.
- His verdicts go in the existing `verdicts.md` shape, one row per fight, in his words.

## Analysis: does this build fast and in parallel under the method?

- **Story size.** Every stage is under 1,000 implementation lines. Stage 1's four code parts are about 150 (snapshot), 250 (runner), 300 (replay scene), 150 (page), 120 (converter); each part is one builder on one worktree with no shared file; the contract part lands first. Stage 1 is four parallel builds behind one half-day contract landing, one landing clerk per part. That is the DRAFT-build-slots 3 number plus one; the fourth queues.
- **Why single sessions work now.** A part is one file set, one test file, one red line pasted, one green, one `pre_gate.sh`, one push. No part needs the whole lab in context; the builder card plus the story is the brief.
- **Test writers in parallel with the contract.** The contract's `SNAPSHOT.md` is enough for all four test writers to write red tests the same morning.
- **Where it would stall.** (1) Eyes gate: his look is the serial step; the pipeline makes it one look per stage, not per picture. (2) H-025 unlanded: stage 1's replay scene builds on round two's scene; the builder merges the `s/H-025-*` branch into its branch if H-025 has not landed, and the landing waits for H-025 (no two stories edit `layout_shot.gd`; the replay scene is new files that `preload` it). (3) Sight-off knob: if the sim has no sight stat, stage 1 stops for one ruling; the builder reports, no work-around.
- **Cost.** Stage 1 is about one day of Sonnet build and tests plus one Architect spec morning; stages 2 to 5 are each smaller (one new factor, one new frame key, a few drawn marks). The 50% build-plus-tests rule is met by construction: no records clerks, no pieces rows, pictures through the Sonnet look reviewer.
- **What the method already gives.** Branch per stage part, `Land H-###` trailers, status.sh shows what waits on him, the nightly play opens main, the sweep catches a stage breaking an older one.
- **Drift check.** Each stage's "done when" is his sentence; a stage with no watched fight is not Seen, whatever the tests say. The arena imports only `engine.py`, `fight.py` helpers, `rules.toml`/`check_layout`, and the shot scene; a stage that imports anything from the "not used" list before stage 6 is a scope drift the clerk rejects (one grep in the stage's tests).

## Rulings this plan needs from Westley (none block his authoring lane)

1. Stage order above, and stage 1's floor (Vanguard only, attack-move both sides, sight off).
2. DRAFT-snapshot-seconds 5, DRAFT-snapshot-count 10 to 20, DRAFT-fight-cap 600 s, DRAFT-replay-fps 1.
3. Stage 1 layouts: the six open-field pairs, or his own set.
4. Replay in the game scene plus a frame strip on the page, as drafted; or the strip alone.
5. The "not used before stage 6" list stays in the tree untouched until stage 6 (recommended), or is parked now.

## Verification

- Stage 1 end to end on a fresh worktree: six layouts converted (`CONVERTED` lines), six fights run twice with byte-identical `fight.json`, replay scene opens through `scripts/play.sh` on his display with the portal proof line `PLAY proof <path> portal`, PNG per frame not blank, page lists six rows with predicted and actual, Sonnet look reviewer `LOOK OK` per picture, then his verdicts in `verdicts.md`.
- Positive controls: a frame missing `hp` fails `validate()`; a layout breaking R2 is rejected by the converter; a `fight.json` with a frame removed changes `frame_count`.
- Determinism test runs in the sweep so a later stage cannot change stage 1's fights silently.

## What happens first after approval

1. Architect writes `docs/stories/H-039.md` (stage 1 snapshot contract, with `SNAPSHOT.md` text and the situation `TEMPLATE.md`) and `docs/stories/H-040.md` (stage 1 arena: runner, replay, page, converter as four parts), rows in `harness.md`, DEC rows for the staircase and the drafts above, pushed as records under `gate.lock`.
2. Dispatcher d39baa: test writer then builder then clerk for H-039; four test writers and four builders for H-040 parts once H-039 lands; clerks per part; look reviewer; pictures to his folder.
3. Westley: writes the first situations from `TEMPLATE.md` whenever he likes; watches stage 1 fights when the Dispatcher reports the scene line.
