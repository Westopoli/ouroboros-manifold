# Objectives mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs, 2026-09-22, Godot 4.6.3, llvmpipe/Compatibility, 1280x720 unless noted. This session ran under severe concurrent-session CPU/memory contention on the shared machine (up to 8 other `godot` processes, system swap 7+/8GB used for most of the session) — timings reflect that, not the mockup's own cost.

## Headless checks (`scripts/mockup_verify.sh objectives [--plant id]`)

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | same seed/archetype/fixture hashes equal twice | PASS — two full Xvfb runs (`final_clean1`/`final_clean2`) hash-matched on every one of 12 captured states | seed-ignored | LIVE (SEED-2 fails under it) |
| SEED-2 | seed 11 vs 12 differ in hash for >= 6/10 archetypes | PASS — exactly 6/10 differ (the 3 destroy_targets + 2 eliminate_force + 1 escort archetypes; the 4 hold_zone archetypes are deliberately seed-invariant, see finding 6) | seed-ignored | LIVE — `FAIL: SEED-2 only 0/10 archetypes differ` |
| KIND-3 | objective kind equals table kind for all 10 | PASS | kind-mapping-random | LIVE — 9/10 mismatched |
| PLACE-4 | placement matches kind's expected node type | PASS | objective-on-spawn | LIVE — 10/10 mismatched |
| SAT-5 | all 10 archetypes satisfiable on all 3 fixtures, >=2000wu from spawn | PASS — 30/30, zero skips | objective-on-spawn | LIVE — 30/30 unsatisfiable |
| ROUTE-6 | blocked route exceeds straight line; walled objective unsatisfiable+skip | PASS — synthetic detour route > straight line; synthetic fully-walled objective reports unsatisfiable with 1 skip | route-ignored | LIVE — walled case now reports satisfiable, no skip |
| NAME-7 | 1 marker label, Label3D text non-empty and matches objective name | PASS (after scoping the search to the `Marker` subtree — `_draw_places()` added 13 more Label3D nodes for place names, which the original whole-tree count would have miscounted) | marker-unnamed | LIVE — label text `''` vs expected `'Hold the core'` |
| PROG-8 | tick(600) progress in (0,1), monotone, pauses in enemy window, completes | PASS | progress-static | LIVE — `tick(600)=0.0` |
| SHAPE-9 | objective dict has exactly id/type/progress/status/is_primary/location | PASS | none | — |
| JSON-10 | qa_state() round-trips JSON; qa_plant contract correct | PASS | none | — |
| TIME-11 | timing_ms.gen < 200ms headless | PASS — 22.6-36ms measured across all runs | none | — |

All 6 plants independently confirmed `PLANT <id> LIVE` via `scripts/mockup_verify.sh objectives --plant <id>`.

## Xvfb oracles

| id | oracle | clean | plant | planted |
|---|---|---|---|---|
| ERR-0 | `errors.txt` count, `exit.txt`, no UNIFORM | count 0, exit 0, no UNIFORM (10-shot clean run and the 1920x1080 batch) | none | — |
| GPU-0 | `_qa.adapter` contains llvmpipe, method gl_compatibility | `llvmpipe (LLVM 21.1.8, 256 bits)`, `gl_compatibility` | none | — |
| DET-1 pixel | `diff` on the same shot, two full clean runs | `map_zoom.png`: 0.000000 (byte-identical) | — | — |
| SEED-X | `diff` on the brief's literal seed11/seed12 pairing (`kind_defensive_stand.png` vs `seed12.png`) | 0.227249 — **confounded**, see finding 8 below: those two shots are at different camera heights (3000 vs 12000, inherited from the brief's own smoke script), not just different seeds | seed-ignored | not separately re-measured with this confounded pair; the fair same-height comparison below is the real signal |
| SEED-X (fair, same height, hold_zone) | `diff` seed 11 vs 12, same camera, `defensive_stand` | 0.000050 — at/below noise floor, confirms hold_zone is seed-invariant by design (single "objective" candidate, no jitter) | seed-ignored | 0.000055 — indistinguishable from clean, as expected (nothing to break) |
| SEED-X (fair, same height, destroy_targets) | `diff` seed 11 vs 12, same camera, `siege_breaking` | 0.001666 — 33x the hold_zone number, real but modest (candidate re-pick + jitter, still below the brief's 0.05 candidate threshold) | not measured | not measured |
| PROG-X | `diff` on the HUD bar crop, p30 vs p90 | 0.083590, comfortably above the 0.002 candidate | progress-static | not separately captured; PROG-8 headless already proves the plant (`tick(600)=0.0`) |
| KIND-X | pairwise `diff` among the 5 kind shots | defensive_stand vs siege_breaking 0.255817; siege_breaking vs rear_guard 0.276862; rear_guard vs suppression 0.802862; **defensive_stand vs multi_front_defense 0.000683 — fails the >=0.01 candidate**, both are hold_zone at the identical objective-node position (see finding 6) | none | — |
| MARKER-X | marker colour within 6px of `marker.px`, heights 3000 and 12000 | height 3000 (`kind_defensive_stand`): pixel at marker.px is `(27,76,89)`, clearly cyan-family, not background — pass by inspection. Height 12000: the brief's literal `map_zoom` shot pans the camera to a fixed map-survey point, not the current objective, so `marker.px` for that shot is `(916.6, 786.5)` — **off the 720p/1080p frame entirely**, cannot be sampled. A supplementary direct test (camera centred on the objective at height 12000) shows the ring/glyph clearly, confirming the marker itself renders correctly at that height — the "failure" is a framing choice in the smoke script, not a rendering bug | marker-unnamed | not applicable (colour presence unaffected by this plant) |

## Visual questions

Read against `docs/bible/references/E-17/E-17-8-wows-map-view.png` (grid, terrain shapes, group icons, drawn arrows, objective circles) and the E-10 60-second paragraph.

- **Q1** (objective is first thing the eye lands on at tactical zoom, name readable): **partial**. The ring + glyph are unmistakably the only saturated colour in frame and read first — proving shot `pass1/kind_defensive_stand.png`. The **name is not readable**: the 3D `Label3D` text does not render at all in this Xvfb/Compatibility/llvmpipe environment (see finding 7); confirmed by cropping directly above the ring in `pass1/kind_defensive_stand.png` at 1920x1080 — no glyphs, not even faint ones.
- **Q2** (five kinds tellable apart from marker alone, no HUD line): **partial — 4 of 5**. hold_zone (ring+cube), destroy_targets (diamond+3 scattered boxes), escort_to_extraction (cone+box trail), eliminate_force (cross+8 scattered boxes+ring) are all visually distinct — proving shots `pass1/kind_siege_breaking.png`, `pass1/kind_rear_guard.png`, `pass1/kind_suppression.png` vs `pass1/kind_defensive_stand.png`. The 5th shot, `multi_front_defense`, is **pixel-identical to `defensive_stand`** (both hold_zone, same objective-node position) — see finding 6, this is a consequence of R-073-01's table, not a marker-design defect.
- **Q3** (at map zoom, marker/ring still read; escort route reads as a route): **yes for the route, held for the marker**. `pass1/map_zoom.png` shows only background at the camera's fixed survey point (the current objective is off-frame there, see MARKER-X above); a direct objective-centred height-12000 shot (not in the committed batch, diagnostic only) shows the ring reading clearly, small but legible. The escort route (`pass1/kind_rear_guard.png`) reads unambiguously as a dotted trail of boxes from spawn to extraction.
- **Q4** (HUD line shows kind/name/progress in one glance): **partial**. "PRIMARY Hold the core [bar] 79%" — the archetype's kind description and the numeric percentage are both instantly readable (proving shot `pass1/hud_p90.png`). The `▮`/`▯` fill characters inside the text label render as tofu boxes (missing glyphs in the default Control theme font) — but the actual `ColorRect` progress bar directly below the text renders correctly and is the real signal, so the HUD still shows "what done looks like" at a glance even though the text-art bar is broken.
- **Q5** (map reads as places, named node boxes, not a blank plane): **partial**. After fixing a real gap (see finding 6.5 / commit `24384ec`: `places.gd`'s "draw every node as a box+label" spec was never wired into the render), the map does now show named-node geometry: 13 gray boxes at the fixture's actual node positions, matching `chokepoint`/`staging`/`extraction`/etc. — proving shot `pass1/kind_defensive_stand.png` (3 boxes visible near the ring at tactical zoom) and the diagnostic tactical-zoom shots taken during debugging. The **labels on those boxes don't render** for the same reason as Q1 (finding 7), so it reads as "places" (distinct box shapes at distinct spots) but not yet "named places."
- **Q6** (magenta/black/clipped/overlapping text at 720p): **no outright hygiene failures**, but two real findings: (a) the `▮`/`▯` tofu-box glyphs noted in Q4; (b) a soft background gradient behind the 3D scene at every zoom (finding 8) — not magenta/black/clipped, but worth Westley's own look since its cause wasn't fully isolated.

**HELD:** Q1 and Q5's label-visibility sub-question (finding 7 — needs investigation outside this brief's scope or Westley's own Forward+/RTX seat to know if it's an Xvfb-only artifact); Q3's marker-at-map-zoom sub-question (needs either a smoke-script change or Westley's steer on what `map_zoom` should frame).

## Timings

- `timing_ms.gen` (places load + mission_gen.build): 22.6-36ms across every capture, comfortably under the 200ms headless budget (TIME-11).
- `fps_ms` (`Performance.TIME_PROCESS`) under llvmpipe/Compatibility at 1280x720, this session's heavy contention: 198-310ms/frame. Note this session ran with up to 8 concurrent `godot` processes and 7+/8GB swap in use system-wide; a quiet machine should be much faster (the brief's own "~1s/frame" estimate was a worse-case baseline this mockup did not need).
- One full clean smoke run (9 screenshots, 3 regenerates, 2 tick batches): completed within a 600s wrapper timeout on a quiet-ish pass; multiple earlier attempts hit the 300-1800s wrapper cap under worse contention and, separately, two real harness bugs (Xvfb screensaver blanking after 600s, fixed upstream `a98c47f`; SimBridge's dead-pid error-route fade-to-black freeing the mockup mid-script, fixed upstream `b65afa8`) before this branch merged both fixes from `main`.

## Node-skip count

0 skips across all 30 (10 archetypes x 3 fixtures) satisfiability checks in the clean pass (SAT-5). The skip/fallback path is only exercised by the synthetic ROUTE-6 fixture and the `objective-on-spawn`/`route-ignored` plants.
