# Fog mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs, re-measured 2026-09-22 (pass-2, post fixes) on Godot 4.6.3, llvmpipe (Compatibility/`gl_compatibility`), 1280x720 unless noted, after merging main's `b65afa8` (qa_boot frees autoloads before instantiating the mockup; the earlier "hangs after 4-5 shots" was that bug, not machine contention — see the report). The full `qa/smoke.json` now runs single-shot inside its 600s timeout. Every threshold here is a candidate; Westley owns the final number.

## Check table

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | seed 11 x2 equal, seed 12 differs (hash + 300-tick step) | hash 11 == hash 11; hash 11 != hash 12 (`VERIFY OK`) | seed-ignored | `PLANT seed-ignored LIVE (1 FAIL)` |
| VIS-2 | sensor 700 sees 650 not 750; interference 0.5 sees 350 not 351; union of two friendlies | all 5 sub-conditions true (`VERIFY OK`) | radius-ignored | `PLANT radius-ignored LIVE (1 FAIL)` |
| LOS-3 | enemy behind tall obstacle not visible; visible once obstacle removed | both true (`VERIFY OK`) | los-ignored | `PLANT los-ignored LIVE (1 FAIL)` |
| VIEW-4 | 3 of 8 enemies in `view_enemy_uids`; `FogView` enemy-node count == 3; no leaked uid | true (`VERIFY OK`) | fog-leak | `PLANT fog-leak LIVE (2 FAIL)` |
| RECON-5 | recon: all cells `visible` for terrain, `view_enemy_uids` empty, HUD readout text == 0, hash unchanged over 20 ticks, tick stays 0; Begin: most cells `never_seen`, terrain nodes still drawn, HUD readout == `view_enemy_uids.size()`, every `MapNodes` `Label3D` has non-empty text | true (`VERIFY OK`) | recon-shows-enemy | `PLANT recon-shows-enemy LIVE (1 FAIL)` |
| MEM-6 | visible→explored→stays explored (memory on); visible→never_seen (memory off) | true (`VERIFY OK`) | no-memory | `PLANT no-memory LIVE (2 FAIL)` |
| STRUCT-7 | structure in explored cell drawn (darkened); structure in never_seen not drawn; enemy units in explored cells not drawn | true (`VERIFY OK`) | fog-leak | `PLANT fog-leak LIVE (2 FAIL)` |
| SYM-8 | A (r=700) sees B at 500wu; B (r=200) does not see A back | true (`VERIFY OK`) | none, self-test | n/a |
| JSON-9 | `qa_state()` round-trips JSON with every contract key; `qa_plant("nope")` false; every `PLANTS` id true | true (`VERIFY OK`) | none, self-test | n/a |
| TIME-10 | `tick_avg` for 8 friendlies/12 enemies/64x64 grid, 200-iteration average | **0.5096 ms** (< 3ms) | none, self-test | n/a |

`scripts/mockup_verify.sh fog` → `VERIFY OK`, exit 0. All 6 `--plant <id>` runs → `PLANT <id> LIVE`, exit 0 (see the finishing report for the exact command block).

## Xvfb oracles (real screenshots + `qa_state()` JSON, not simulated)

| oracle | clean | planted | plant | verdict |
|---|---|---|---|---|
| ERR-0 | `errors.txt` count 0 on every one of 12 real Xvfb runs this pass (clean 1280x720 + 1920x1080 review + map_zoom + 3 oracle plants + 1 DET-1 repeat) | — | — | pass |
| GPU-0 | `_qa.adapter` = `llvmpipe (LLVM 21.1.8, 256 bits)`, `_qa.method` = `gl_compatibility` on every run | — | — | pass |
| DET-1 (pixel) | two independent clean recon.png runs: hash 4183577953 == 4183577953 (identical to pass-1's hash, confirming the HUD/label/camera fixes changed no sim state), `diff` **0.000000** (fuzz 5) | — | — | pass |
| RECON-X | pixel probe at `enemies_px["102"]` (786,87 — moved from pass-1's (834,30) because the standard camera moved, item 3): 0 enemy-red hits in a 50x50 window, clean `recon.png`; HUD readout also reads "visible enemies 0 of 8" (was wrongly "3 of 8" pre-fix, item 1) | same coordinate: **216 red-pixel hits** under `recon-shows-enemy`, HUD readout reads "3 of 8" | recon-shows-enemy | LIVE |
| HIDDEN-X | pixel probe at `enemies_px["102"]` (786,87) in `mission_t100.png`: 0 red hits (102 not in `visible_enemy_uids`) | same coordinate: **190 red-pixel hits** under `fog-leak` | fog-leak | LIVE |
| TRAIL-X | `diff mission_t100.png mission_t300.png` = **0.034728** (fuzz 5, ≥0.02 — units visibly moved) | `cells.explored` **held flat at 433** both ticks — see HELD below | — | partial |
| MEM-X | `diff memory_on.png memory_off.png` = **0.060932** (fuzz 5, ≥0.05); `cells.explored` 433→0 with memory off; new `memory_off_full.png` (item 4, map height 8000) shows only the two friendlies' current-vision discs lit against pure black | with `no-memory` plant even with the checkbox on: `cells.explored` stuck at 0 instead of 433 (unchanged from pass-1) | no-memory | LIVE |
| RING-X | `circles["1"]` 700wu open ground → **350wu** inside the interference zone (confirmed by cropping `close_ring.png`) | `circles["1"]` stays **700wu** in the same spot; `diff` vs clean `close_ring.png` = **0.416238** | radius-ignored | LIVE |

Diff fuzz: the tool's own default (5%) was used throughout; at fuzz 30 the MEM-X pair fell under its own 0.05 candidate (0.002738), so 5% is the fuzz that actually discriminates these particular pairs — the opposite finding from the landscape mockup's checklist, which needed fuzz 30 to suppress its own placer's per-run mesh-order noise. This mockup has no such per-run non-determinism (fixed primitive meshes, not a randomized piece placer), so the low-fuzz default works directly.

## Visual questions

Screenshots at `docs/northstar/research/mockups/fog/pass1/` (1920x1080).

- **Q1** (three states tellable apart at a glance): **yes**. Proving shot: `mission_t300.png` — pure black outside any circle, a visibly dimmer grey-green band around the patrol trail, and full-brightness terrain inside the two current-vision circles. Dim level used: 60% black overlay (alpha 0.6) on the explored band. This seems about right — legible but not so dark it reads as "still black." Candidate to revisit: 50% if Westley wants explored to read lighter.
- **Q2** (can see where units have been, no enemy drawn there): **yes**, and now provable at map scale too. Proving shots: `mission_t300.png` — the dim halo around each circle is the explored trail, no enemy sits in it; `memory_off_full.png` (new, item 4) — zoomed to map height with memory off, only the two friendlies' current-vision discs are lit, confirming the "trail" in `mission_t300.png` really is memory, not something else leaking through. Caveat unchanged from pass-1: this fixture's patrol loop is short enough that `cells.explored` does not grow between tick 100 and tick 300 (TRAIL-X above) — the trail is visible but not still expanding by t300 (see HELD).
- **Q3** (enemy structure visible but darkened in explored space): **yes**. Proving shot: `mission_t300.png`, top-right circle — the red structure box sits at full brightness while inside current vision; STRUCT-7's data (headless) confirms it darkens (`ENEMY_COLOR.darkened(0.6)`) once the cell drops to `explored`. Still not separately screenshotted at that exact moment — HELD below (unchanged; this pass's fixes did not touch structure rendering).
- **Q4** (recon: every obstacle/zone/node readable, no enemy anywhere): **yes, and now the HUD agrees.** Proving shot: `recon.png` — all three obstacles, all three zones (purple interference, dark-green cover, olive hazard), all five node markers with legible `Label3D` type text (`chokepoint`, `extraction`, `staging`, `objective`, `vantage` — item 2), and both friendlies are visible; zero enemies. Pass-1 had a real bug here that this pass fixes (item 1): the HUD read "visible enemies 3 of 8" during recon even though nothing was drawn, because it read `qa_state().visible_enemy_uids` (truth, phase-blind) instead of `view_enemy_uids` (the filtered set the view actually holds). `recon.png` now reads "visible enemies 0 of 8" — RECON-X's pixel probe confirms 0 enemy-red hits at every `enemies_px` coordinate, and the readout now matches.
- **Q5** (ring reads smaller inside interference; zone reads as a third treatment): **yes**. Proving shot: `close_ring.png` — the friendly's ring is visibly smaller than the interference zone's own boundary, and the zone's purple tint is clearly distinct from both black (never-seen) and grey-dim (explored). Data: `circles["1"]` 700wu → 350wu (exactly the 0.5 intensity halving).
- **Q6** (memory off: everything without current vision black): **yes for the ground/fog layer, confirmed at two zoom levels now.** Proving shots: `memory_off.png` (standard camera) and the new `memory_off_full.png` (item 4, map height 8000) — both show the dim halo gone entirely, only the two friendlies' current-vision discs lit, everything else pure black. **Caveat, unchanged and still open** (item 5, deliberately not resolved this pass): obstacle boxes, zone patches, and node markers stay fully lit in both memory-off shots even in pure-black areas, because §3 of the brief says to draw terrain features "always," which contradicts the derived rule in `references/E-12/notes.md` ("never seen: pure black, no terrain"). See "Questions for Westley" #1 in the README — left as a flagged tension, not silently resolved.
- **Q7** (hygiene: magenta, black-where-shouldn't-be, clipped/overlapping text): **no** issues found in any of the 9 pass1 shots. HUD text and the now-larger node labels (`pixel_size` 0.55→2.2, item 2) are legible at both 1280x720 and 1920x1080 with no clipping or overlap.

## HELD

- **Q3**: structure-darkening is proven by data (STRUCT-7, headless) but not captured in its own dedicated pass1 screenshot at the exact explored (not visible) moment — the pass1 batch's mission shots all happen to have the structure in current vision. Not a failure, just an uncaptured angle.
- **TRAIL-X**: the diff threshold (≥0.02, unit positions moved) holds, but the "cells.explored grew" half of the candidate oracle does not — this fixture's patrol rectangle is small enough that its whole loop is explored well before tick 100, so t100→t300 shows movement but no new territory. A future revision wanting to demonstrate growing exploration should use a longer patrol path or measure explored growth over tick 0→100 instead of 100→300.

## Timings

- `TIME-10` (8 friendlies, 12 enemies, 64x64 grid, `compute_visibility()` + `FogCellGrid.update()`, 200-iteration average, headless): **0.5096 ms**, well under the 3ms budget.
- Interactive `timing_ms.tick_avg` (2 friendlies, 8 enemies, real fixture, `qa_tick`'s own rolling average incl. `_sync_view()`'s node rebuild): **2.64-2.81 ms/tick** across the clean run's state captures.
- `fps_ms` (`Performance.TIME_PROCESS`, rendered frame time) at 1280x720: **263-706 ms** across this pass's runs, llvmpipe under ordinary shared-machine load (no longer the ~30-process contention pass-1 saw). The brief's own "up to a second per rendered frame" expectation for llvmpipe holds comfortably.
