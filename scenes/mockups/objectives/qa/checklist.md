# Objectives mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs, 2026-09-22, Godot 4.6.3, llvmpipe/Compatibility, 1280x720 unless noted. This pass is the fix-first round after the fresh-eyes review (see README "Design as built" and "Fix pass" for what changed and why); this session ran on a quieter machine than the original build session, so `fps_ms` here is materially faster.

## Headless checks (`scripts/mockup_verify.sh objectives [--plant id]`)

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | same seed/archetype/fixture hashes equal twice | PASS — two full Xvfb runs (`final_clean1`/`final_clean2`) hash-matched on every one of 12 captured states | seed-ignored | LIVE (SEED-2 fails under it) |
| SEED-2 | seed 11 vs 12 differ in hash for >= 6/10 archetypes | PASS — exactly 6/10 differ (the 3 destroy_targets + 2 eliminate_force + 1 escort archetypes; the 4 hold_zone archetypes are deliberately seed-invariant, see finding 6) | seed-ignored | LIVE — `FAIL: SEED-2 only 0/10 archetypes differ` |
| KIND-3 | objective kind equals table kind for all 10 | PASS | kind-mapping-random | LIVE — 9/10 mismatched |
| PLACE-4 | placement matches kind's expected node type | PASS | objective-on-spawn | LIVE — 10/10 mismatched |
| SAT-5 | all 10 archetypes satisfiable on all 3 fixtures, >=2000wu from spawn | PASS — 30/30, zero skips | objective-on-spawn | LIVE — 30/30 unsatisfiable |
| ROUTE-6 | blocked route exceeds straight line; walled objective unsatisfiable+skip | PASS — synthetic detour route > straight line; synthetic fully-walled objective reports unsatisfiable with 1 skip | route-ignored | LIVE — walled case now reports satisfiable, no skip |
| NAME-7 | 1 marker label, Label3D text non-empty and matches objective name | PASS | marker-unnamed | LIVE — label text `''` vs expected `'Hold the core'` |
| PROG-8 | tick(600) progress in (0,1), monotone, pauses in enemy window, completes | PASS | progress-static | LIVE — `tick(600)=0.0` |
| SHAPE-9 | objective dict has exactly id/type/progress/status/is_primary/location | PASS | none | — |
| JSON-10 | qa_state() round-trips JSON; qa_plant contract correct | PASS | none | — |
| TIME-11 | timing_ms.gen < 200ms headless | PASS — 22.5-29.3ms measured across all runs | none | — |
| LABEL-12 (new) | every `Label3D` in the scene has `pixel_size >= 0.5` and non-empty text | PASS — 14 Label3D nodes (1 marker + 13 place labels), all pixel_size 1.6 or 2.2, all non-empty | marker-unnamed | LIVE — marker label `pixel_size=2.200 text=''` (pixel_size unaffected, text blanked by the plant) |

All 6 plants independently confirmed `PLANT <id> LIVE` via `scripts/mockup_verify.sh objectives --plant <id>`; LABEL-12 reuses `marker-unnamed` rather than adding a 7th plant, since that plant already blanks the one piece of state (marker label text) this check needed to see break.

## Xvfb oracles

| id | oracle | clean | plant | planted |
|---|---|---|---|---|
| ERR-0 | `errors.txt` count, `exit.txt`, no UNIFORM | count 0, exit 0, no UNIFORM (10-shot clean run x2, 6 planted runs, the 1920x1080 batch) | none | — |
| GPU-0 | `_qa.adapter` contains llvmpipe, method gl_compatibility | `llvmpipe (LLVM 21.1.8, 256 bits)`, `gl_compatibility` | none | — |
| DET-1 pixel | `diff` on the same shot, two full clean runs | every one of 9 screenshots: 0.000029-0.000084 (noise floor) | — | — |
| SEED-X (`kind_defensive_stand` vs `seed12`, both height 3000 now that map_zoom no longer confounds this pairing) | `diff` seed 11 vs 12, hold_zone | 0.000029 — at/below noise floor, confirms hold_zone is seed-invariant by design (single "objective" candidate, no jitter) | seed-ignored | not separately re-measured; SEED-2 headless already proves the plant |
| PROG-X | `diff` on the HUD bar crop (320x6 `ColorRect`, not the text line), p30 vs p90 | 0.252083, comfortably above the 0.002 candidate | progress-static | not separately captured; PROG-8 headless already proves the plant (`tick(600)=0.0`) |
| KIND-X | pairwise `diff` among the 5 kind shots | defensive_stand vs siege_breaking 0.019703; siege_breaking vs rear_guard 0.028192; rear_guard vs suppression 0.031383; suppression vs survive_duration 0.020093; defensive_stand vs survive_duration 0.018916 — **all 5 pairs now clear the >=0.01 candidate** (the 5th exemplar is survive_duration, not the former hold-on-hold duplicate, see finding 6) | none | — |
| MARKER-X | marker colour within 6px of `marker.px`, heights 3000 and 12000 | height 3000 (`kind_defensive_stand`): pixel at marker.px `(640, 360)` is `(77,217,255)`, clearly the cyan label/glyph, not background. Height 12000 (`map_zoom`, now camera-locked to the objective via `qa_camera_at_objective`): marker.px is also `(640, 360)` (dead centre); the exact pixel lands in the ring's hollow interior (background), but a 13x13px crop around it shows clear cyan text/glyph pixels — pass within the 6px window | marker-unnamed | not applicable (colour presence unaffected by this plant) |

## Visual questions

Read against `docs/bible/references/E-17/E-17-8-wows-map-view.png` (grid, terrain shapes, group icons, drawn arrows, objective circles) and the E-10 60-second paragraph.

- **Q1** (objective is first thing the eye lands on at tactical zoom, name readable): **yes**. The ring + glyph are the only saturated colour in frame and read first, and the name is now legible: `pixel_size` was the bug (set but left at the Label3D default 0.01, making 64px text under 1wu tall), fixed to 2.2 on the marker label — proving shot `pass1/kind_defensive_stand.png` shows "Hold the core" clearly in cyan.
- **Q2** (five kinds tellable apart from marker alone, no HUD line): **yes, 5 of 5**. hold_zone (ring+cube, `pass1/kind_defensive_stand.png`), destroy_targets (diamond+3 orange scattered boxes, `pass1/kind_siege_breaking.png`), escort_to_extraction (cone+green box trail, `pass1/kind_rear_guard.png`), eliminate_force (cross+ring+8 red scattered boxes, `pass1/kind_suppression.png`), survive_duration (sphere+purple ring, `pass1/kind_survive_duration.png`) are all visually distinct in both glyph shape and colour. The 5th exemplar is now a hand-forced survive_duration (`qa_set("kind", ...)`) instead of the former multi_front_defense, which was pixel-identical to defensive_stand (both hold_zone at the same node — a fact about R-073-01's table, not the marker kit).
- **Q3** (at map zoom, marker/ring still read; escort route reads as a route): **yes, both**. `pass1/map_zoom.png` now shows the ring, glyph, and "Hold the core" label centred in frame (`qa_camera_at_objective` replaced the smoke script's fixed 12000/12000 survey point). The escort route (`pass1/kind_rear_guard.png`) reads unambiguously as a dotted trail of green boxes spanning most of the frame, with the "Escort to extraction" label and cone glyph also in frame (camera now pans to 75% along the route toward the objective end, not the raw endpoint).
- **Q4** (HUD line shows kind/name/progress in one glance): **yes**. "PRIMARY Hold the core ########-- 79%" — kind, name, ASCII bar, and percentage are all instantly readable (proving shot `pass1/hud_p90.png`). Switched the bar's fill glyphs from `▮`/`▯` (JetBrainsMono has the filled glyph but not the light one, so half the bar tofu'd) to plain `#`/`-`, which every font renders.
- **Q5** (map reads as places, named node boxes, not a blank plane): **yes**. `pass1/kind_defensive_stand.png` shows 3 named gray boxes ("objective", "chokepoint" x2, "extraction") near the ring, all legible now that place labels also have `pixel_size` set (1.6).
- **Q6** (magenta/black/clipped/overlapping text at 720p and 1080p): **no hygiene failures**, one cosmetic note: at 1080p the escort marker's "Escort to extraction" label is large enough to nearly touch the left frame edge (`pass1/kind_rear_guard.png`) — legible, not clipped, but close; a smaller `pixel_size` or a less-extreme pan-target percentage would give it more margin if Westley wants it tighter. The grey background gradient reported in the fresh-eyes review did not reproduce on any clean re-run this session, at any camera height, under either Sky or flat-Color background mode (see README "Fix pass" item 4).

**HELD:** none. Both prior HELD items (Label3D visibility, map-zoom framing) were root-caused and fixed this pass.

## Timings

- `timing_ms.gen` (places load + mission_gen.build): 22.5-29.3ms across every capture, comfortably under the 200ms headless budget (TIME-11).
- `fps_ms` (`Performance.TIME_PROCESS`) under llvmpipe/Compatibility at 1280x720, this session (quieter machine than the original build session): 100.4-170.4ms/frame.
- Every clean/planted smoke run (9 screenshots, 3 regenerates, 2 tick batches) and the 1920x1080 review batch completed well inside the 300-400s wrapper timeout, no retries needed.

## Pass 2 (2026-09-22, mockup review 1 fixes)

Fixes edge-scroll (right/bottom dead) and regenerate (same-seed no-op); see README "Mockup review 1 fixes" for root causes and evidence.

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| EDGE-13 (new) | centred `_mouse_pos` (bounds space) does not pan; `_mouse_pos` at `bounds.x-10`/`bounds.y-10` pans camera.x/z positively | PASS under `--headless` | none | — |
| DET-1 to LABEL-12 | unchanged since pass 1 | PASS, re-ran clean + all 6 plants after the camera_rig.gd/hud.gd/objectives_mockup.gd edits, still LIVE | (all 6) | LIVE, same fails as pass 1's table above |

Xvfb, `--res 2560x1440`, `qa/edges.json`, camera parked at `(12000, 12000)` height 3000: move `(2540, 720)` -> `camera.x` `12000 -> 13550`; move `(1280, 1420)` -> `camera.z` `12000 -> 13550`; move `(20, 720)` -> `camera.x` `13550 -> 12000`; move `(1280, 20)` -> `camera.z` `13550 -> 12000`. All four edges pan; `errors.txt` count 0.

Regenerate, `qa/smoke.json`'s own `after_r` checkpoint (`defensive_stand`/`hold_zone`, fixture 12): `fixture12` state `seed=12 regen_count=10 hash=3757886768` -> `after_r` state `seed=13 regen_count=11 hash=3757886768` — seed and regen_count advance, hash is unchanged because `hold_zone` archetypes are deliberately seed-invariant (same finding as pass 1's SEED-2 row), not a residual bug. Separately reproduced with a seed-sensitive archetype (`siege_breaking`): hash `3289694821` (seed 11) -> `2334985817` (seed 12).

`scripts/mockup_verify.sh objectives` clean and all 6 `--plant` runs: still `PLANT <id> LIVE` with the same fail sets as the pass-1 table above (unaffected by this pass's edits, re-confirmed). Two clean `qa/smoke.json` runs at 1280x720: both exit 0, `errors.txt` count 0, and `after_r`'s `hash`/`seed` match between the two runs (`3757886768`/`13`). All 6 plants also re-run once each through `mockup_qa.sh run` under Xvfb at 1280x720 (`qa/plant_check.json`): exit 0, `errors.txt` count 0 for every one.

Re-shot the 1920x1080 `qa/smoke.json` batch and diffed every pass-1 screenshot against it: all 9 (10 counting the `seed11`/`kind_defensive_stand` alias) land at 0.000027-0.000078, the same noise floor as pass 1's own DET-1 pixel check — neither fix touches a rendered frame (`qa/smoke.json` never moves the mouse, and its only `key R` press happens after the last screenshot). `pass1/` is unchanged, nothing re-shot.

## Node-skip count

0 skips across all 30 (10 archetypes x 3 fixtures) satisfiability checks in the clean pass (SAT-5). The skip/fallback path is only exercised by the synthetic ROUTE-6 fixture and the `objective-on-spawn`/`route-ignored` plants.
