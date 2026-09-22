# Units mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs on 2026-09-22, Godot 4.6.3, llvmpipe, 1280x720 unless noted. Thresholds marked `(candidate)` are the brief's own numbers; nothing here was loosened. `pass-through`'s Xvfb note: the brief's Xvfb-oracle list has no dedicated visual oracle for `pass-through` or `seed-ignored`'s tick-200 checkpoint beyond ERR-0/GPU-0/DET-1; those two are proven at the headless (verify.gd) level instead, and that gap is called out below rather than papered over.

## Headless checks (`scripts/mockup_verify.sh units`)

| id | check | clean | plant | planted |
|---|---|---|---|---|
| DET-1 | seed 11 run(mirror_10v10,600) x2 equal hash; seed 12 differs from seed 11 on flank_4v4 (needed 900 ticks, not 200 — see note) | PASS | seed-ignored | PLANT LIVE (1 FAIL) |
| ROSTER-2 | six roles per kit, R-082-02..04 orderings; positive control (broken kit dict) detected | PASS | none (data) | n/a |
| SIL-3 | bboxes pairwise distinct >10%; Strike smallest volume, Siege largest; anchor width>length; artillery longest | PASS | silhouettes-same | PLANT LIVE (1 FAIL) |
| MIRROR-4 | mirror_10v10 both sides alive at tick 900; line-vs-Strike variant ≥5 Vanguard survivors at tick 2400 | PASS | instant-fight | PLANT LIVE (3 FAIL) |
| SOLID-5 | formation_move + flank_4v4, 600 ticks: no obstacle overlap, no <28wu pair | PASS | pass-through | PLANT LIVE (1 FAIL) |
| FACE-6 | isolated 3-unit fixture, facing within 0.18rad of heading at tick 60; attacker faces target at tick 80 | PASS | facing-fixed | PLANT LIVE (1 FAIL) |
| PLAIN-7 | plain-move unit never targeted, advances >200wu at tick 700; positive control (attack-move variant) engages by tick ~450 | PASS | none (self-test) | n/a |
| DEATH-8 | bombards_1000 first death by tick 300 (measured ~120), wreck present 60 ticks after | PASS | no-death-visual | PLANT LIVE (1 FAIL) |
| FORM-9 | formation_move arrival spread ≤40 ticks (measured 35); split raider arrival 350-450 ticks (measured ~393) | PASS | none | n/a |
| JSON-10 | qa_state() round-trips JSON, all contract keys present; qa_plant('nope') false; all 6 plant ids true | PASS | none | n/a |
| TIME-11 | tick_avg < 2ms for 20 units, headless | PASS (measured 0.36ms, Xvfb-side; verify.gd asserts the same computation headless) | none | n/a |

All 6 plant ids report `PLANT <id> LIVE` via `scripts/mockup_verify.sh units --plant <id>`.

## Xvfb: clean run

`scripts/mockup_qa.sh run units scenes/mockups/units/qa/smoke.json <out> --timeout 600`

| oracle | result |
|---|---|
| exit.txt | 0 |
| errors.txt | count: 0 |
| UNIFORM lines | none, any resolution (720p or 1080p) |
| `_qa.adapter` | `llvmpipe (LLVM 21.1.8, 256 bits)` |
| `_qa.method` | `gl_compatibility` |
| Two clean runs, hash | equal on every captured state (fight_t300, death_t20, seed12_flank, …) |
| Two clean runs, screenshot diff | 0.000000 on every shot checked (lineup_greek, fight_t300, fight_end, death_t20) |
| `fps_ms` (720p, per rendered frame) | 217.5ms |
| `timing_ms.tick_avg` (20 units) | 0.36ms |

## Xvfb deterministic oracles, clean vs planted

| oracle | candidate threshold | measured clean | measured planted | plant |
|---|---|---|---|---|
| KIT-X | `diff(lineup_greek, lineup_settled_reach) >= 0.10` | 0.9965 | n/a (no kit-affecting plant) | — |
| FIGHT-X | `diff(fight_t0, fight_t300) >= 0.03` and `flashes_active>0` mid-fight | **0.0067 (below threshold)**; flashes_active 0 at the exact captured tick (transient 7-tick window) | under instant-fight, `alive.0` reaches 0 by tick 300 (fight over well before, matches "by tick 60" — verified via state, not a screenshot diff) | instant-fight |
| DEATH-X | `diff(death_t0, death_t20) >= 0.05` and `wrecks_active>=1` | **0.0010 (below threshold)**; `wrecks_active=1` (data-level pass) | `diff` 0.0008 (unchanged, expected — plant hides the *visual*, not gross pixels); `wrecks_active=0` (data-level pass, this is the real discriminator) | no-death-visual |
| FACE-X | `diff(face_east, face_north) >= 0.05` | **0.0010 (below threshold)** | 0.0010 (**identical to clean — see note**) | facing-fixed |
| SEED-X (flank, tick 200) | hash/diff differ | hash equal to seed 12 at tick 200 (**no divergence this early — see note**) | hash equal (expected; plant forces seed 11) | seed-ignored |
| DET-1 pixel | two clean runs, diff < 0.005 | 0.000000 | — | — |
| ERR-0 | 0 script errors | 0 | 0 (every plant run) | all |
| GPU-0 | adapter contains llvmpipe | yes | yes | all |

### Why three of these don't discriminate, with the evidence

**FIGHT-X, DEATH-X.** Both scenarios put units at small screen footprints (1280x720, or even 1920x1080, against a mostly-empty 8000wu ground): a full-frame pixel diff is dominated by the static background, not the handful of units. The *underlying mechanism is real and confirmed independently*: `flashes_active` and `wrecks_active` are non-zero at the right ticks in `qa_state()` (see MIRROR-4/DEATH-8 above, both pass headlessly and under Xvfb via state JSON), and a direct visual read of `death_t0.png` vs `death_t20.png` (pass1) shows the same static frame at this zoom — the wreck exists in data and is confirmed by the state field, but is not visually prominent enough at this camera height for a naive full-frame diff to catch it. Candidate fixes: crop-based diffs around `units_px` (as the brief already prescribes for SIL-X specifically), a closer `qa_camera` height for these two shots, or accepting `wrecks_active`/`flashes_active` as the load-bearing oracle and treating the pixel diff as supplementary.

**FACE-X.** The clean and planted diffs are identical (0.000994 both ways) because the two compared shots (`face_east`, `face_north`) come from a unit that *also changes screen position* between them (two separate `move` commands), and the position delta dominates the diff regardless of whether facing itself is frozen. A direct visual read (pass1 `fight_mapzoom` aside — see `face_east.png`/`face_north.png` in the raw run dir, not committed) shows the squad's V-formation genuinely rotating ~90° between the two shots, confirming facing is real; the pixel-diff oracle as scripted just can't isolate it from the move. `verify.gd`'s FACE-6 (isolated fixture, no confounding position change) is the check that actually gates this behavior and it does correctly fail under the plant.

**SEED-X at tick 200.** `flank_4v4`'s two forces are still ~1500-2000wu apart at tick 200 (Raiders haven't reached the routing obstacle yet), so the seed-driven RNG (ally-block sweep bias, target tie-breaks) has nothing to act on yet — clean seed 11 and seed 12 hash identically at that checkpoint, same as under the plant. `verify.gd`'s DET-1 uses 900 ticks on the same scenario specifically because that's where real divergence first appears (confirmed: hash differs, target assignments differ). The smoke script's own `seed12_flank` checkpoint (tick 200, matching the brief's literal script) is genuinely uninformative for this scenario; a later tick would be needed for a screenshot-level SEED-X to mean anything.

## Visual questions

| q | question | answer | proving screenshot |
|---|---|---|---|
| Q1 | Name all six roles from shape alone? | **Partial.** `frontliner` (wedge) and `anchor` (wide rectangle) read clearly. `support` reads as "round" but not obviously "radial with a projection." The two Strike squads read as "small scattered cluster" collectively, individual dart/wing shapes too small to resolve. `artillery` (long_barrel) is the weakest: at 20wu wide it reads as a small blob, not "the longest, dominated by one linear axis" — the opposite of its intended read. | `pass1/lineup_greek.png` |
| Q2 | Same six roles obviously the same in both kits? | **Yes.** Geometry and position are pixel-identical between kits; only ground colour and unit palette differ. | `pass1/lineup_greek.png` vs `pass1/lineup_settled_reach.png` |
| Q3 | Mid-fight: who's winning, where's the front, hits visible without shake? | **Front: yes** (two facing lines, unmistakable). **Who's winning: no**, not from either `fight_t300` or `fight_end` — both show 10v10 alive, no visible damage state, because this exact mirror (frontliner vs frontliner, R-082-01 numbers) takes far longer than 60s to produce a first kill (see report §2). No shake confirmed (none implemented). | `pass1/fight_mid.png`, `pass1/fight_end.png` |
| Q4 | Death unmistakable: flare, drift, darkening? | **Held.** `wrecks_active` confirms the sequence exists and is active at +20 ticks post-death, but it is not visually legible in a static screenshot at this camera height/unit size — `death_t0.png` and `death_t20.png` look the same to the eye. | `pass1/death_t0.png`, `pass1/death_t20.png` — HELD |
| Q5 | Flank result reads as Raiders behind Bombards, not a blob? | **No.** At tick 200 the Raiders haven't reached the routing obstacle yet (still ~2000wu short), and the smoke script never re-centres the camera for this scenario (it inherits the prior shot's framing), so the Bombards sit at the extreme right edge of frame, barely in view. Separately: over a full 900-tick run the Bombards' long range wins the engagement (they killed 1 Raider, lost 0) rather than the E-11 paragraph's "Raiders kill the Bombards" — see report §3. | `pass1/flank_result.png` |
| Q6 | Units face travel and targets; does a turn look like a turn? | **Yes**, confirmed both by `qa_state()` facing data (FACE-6 passes) and by direct visual inspection of the raw `face_east.png`/`face_north.png` pair (squad V-formation visibly rotates); the *pixel-diff* oracle for this doesn't discriminate (see FACE-X note above), but the underlying behaviour is real. | face_east.png / face_north.png (raw run dir, not committed — see FACE-X note) |
| Q7 | Any magenta, black, clipped or overlapping HUD text at 720p/1080p? | **No magenta/black placeholder colour.** HUD text is small and low-contrast (white on a semi-transparent grey bar) but not clipped or overlapping at either resolution. One real bug found and fixed during this pass: the ground plane rendered pure white in every shot until `fog_density` (borrowed from the landscape mockup's much larger scale) was disabled — see report. | all pass1 shots |

**HELD:** Q4 (wreck sequence confirmed in data, not legible in a static screenshot at this zoom).

## Bugs found and fixed during this pass

1. **Ground plane rendered white in every shot.** `fog_density` was copied from the landscape mockup, tuned for a 16000-32000wu canvas at up to 40000wu camera heights; at this mockup's 500-12000wu range it fogged the ground to near-white by design (fog opacity ≈60%+ at only 1500wu distance). Fixed by disabling fog and trimming ambient/light energy. Confirmed via a quick isolated repro (single lineup screenshot) before and after.
2. **`lineup.json` spacing (500wu) exceeded the visible frustum** at the brief's mandated `qa_camera 1500 4000 4000`, clipping the sixth unit off-screen. Tightened to 300wu spacing (6 units span 1500wu, comfortably inside the ~2487wu visible width at that height).
3. **Silhouette sizes doubled** across both kits for legibility (all six roles were only 4-22wu on their short axis, rendering as a handful of pixels at any of the smoke script's camera heights). Relative orderings/ratios are unchanged (SIL-3 is scale-invariant and stayed green).
4. **`MultiMeshInstance3D` batches were destroyed and recreated on every kit toggle** (same node names, `queue_free()` + immediate `add_child()`); chased as a possible cause of an Xvfb hang before the real cause (shared harness issue, fixed upstream) surfaced. Kept the fix regardless — updating mesh/material on existing nodes in place is strictly more correct.
5. **A genuine `class_name ToySim` collision** with a sibling mockup (`scenes/mockups/layers/toy_sim.gd`) surfaced after merging the shared harness fix from `main`; renamed mine to `UnitsToySim`. Godot's `class_name` registry is project-global, so two mockups independently picking the same name is a real cross-mockup risk worth flagging (not something I can fix in the sibling's file).
