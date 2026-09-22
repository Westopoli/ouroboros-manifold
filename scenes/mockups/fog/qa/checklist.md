# Fog mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs on 2026-09-22, Godot 4.6.3, llvmpipe (Compatibility/`gl_compatibility`), 1280x720 unless noted. This machine was under heavy contention while these were measured (~30 concurrent Godot QA processes from other agent sessions, load average 18-23 on 16 cores) — see the report's "Environmental finding" for what that did to the run strategy. Every threshold here is a candidate; Westley owns the final number.

## Check table

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | seed 11 x2 equal, seed 12 differs (hash + 300-tick step) | hash 11 == hash 11; hash 11 != hash 12 (`VERIFY OK`) | seed-ignored | `PLANT seed-ignored LIVE (1 FAIL)` |
| VIS-2 | sensor 700 sees 650 not 750; interference 0.5 sees 350 not 351; union of two friendlies | all 5 sub-conditions true (`VERIFY OK`) | radius-ignored | `PLANT radius-ignored LIVE (1 FAIL)` |
| LOS-3 | enemy behind tall obstacle not visible; visible once obstacle removed | both true (`VERIFY OK`) | los-ignored | `PLANT los-ignored LIVE (1 FAIL)` |
| VIEW-4 | 3 of 8 enemies in `view_enemy_uids`; `FogView` enemy-node count == 3; no leaked uid | true (`VERIFY OK`) | fog-leak | `PLANT fog-leak LIVE (2 FAIL)` |
| RECON-5 | recon: all cells `visible` for terrain, `view_enemy_uids` empty, hash unchanged over 20 ticks, tick stays 0; Begin: most cells `never_seen`, terrain nodes still drawn | true (`VERIFY OK`) | recon-shows-enemy | `PLANT recon-shows-enemy LIVE (1 FAIL)` |
| MEM-6 | visible→explored→stays explored (memory on); visible→never_seen (memory off) | true (`VERIFY OK`) | no-memory | `PLANT no-memory LIVE (2 FAIL)` |
| STRUCT-7 | structure in explored cell drawn (darkened); structure in never_seen not drawn; enemy units in explored cells not drawn | true (`VERIFY OK`) | fog-leak | `PLANT fog-leak LIVE (2 FAIL)` |
| SYM-8 | A (r=700) sees B at 500wu; B (r=200) does not see A back | true (`VERIFY OK`) | none, self-test | n/a |
| JSON-9 | `qa_state()` round-trips JSON with every contract key; `qa_plant("nope")` false; every `PLANTS` id true | true (`VERIFY OK`) | none, self-test | n/a |
| TIME-10 | `tick_avg` for 8 friendlies/12 enemies/64x64 grid, 200-iteration average | **0.5347 ms** (< 3ms) | none, self-test | n/a |

`scripts/mockup_verify.sh fog` → `VERIFY OK`, exit 0. All 6 `--plant <id>` runs → `PLANT <id> LIVE`, exit 0 (see the finishing report for the exact command block).

## Xvfb oracles (real screenshots + `qa_state()` JSON, not simulated)

| oracle | clean | planted | plant | verdict |
|---|---|---|---|---|
| ERR-0 | `errors.txt` count 0 on every one of 18 real Xvfb runs (clean + 6 plants + probes) | — | — | pass |
| GPU-0 | `_qa.adapter` = `llvmpipe (LLVM 21.1.8, 256 bits)`, `_qa.method` = `gl_compatibility` on every run | — | — | pass |
| DET-1 (pixel) | two independent clean recon.png runs: hash 4183577953 == 4183577953, `diff` **0.000000** (fuzz 5) | — | — | pass |
| RECON-X | pixel probe at `enemies_px["102"]` (834,30): 0 enemy-red hits in a 50x50 window, clean `recon.png` | same coordinate: **403 red-pixel hits** under `recon-shows-enemy` | recon-shows-enemy | LIVE |
| HIDDEN-X | pixel probe at `enemies_px["102"]` (834,30) in `mission_t100.png`: 0 red hits (102 not in `visible_enemy_uids`) | same coordinate: **347 red-pixel hits** under `fog-leak` | fog-leak | LIVE |
| TRAIL-X | `diff mission_t100.png mission_t300.png` = **0.041955** (fuzz 5, ≥0.02 — units visibly moved) | `cells.explored` **held flat at 433** both ticks — see HELD below | — | partial |
| MEM-X | `diff memory_on.png memory_off.png` = **0.071710** (fuzz 5, ≥0.05); `cells.explored` 433→0 with memory off | with `no-memory` plant even with the checkbox on: `cells.explored` stuck at **0** instead of 433; `diff` vs clean memory-on = 0.026225 | no-memory | LIVE |
| RING-X | `circles["1"]` 700wu open ground → **350wu** inside the interference zone (confirmed by cropping `close_ring.png`) | `circles["1"]` stays **700wu** in the same spot | radius-ignored | LIVE; `diff` = 0.614409 |

Diff fuzz: the tool's own default (5%) was used throughout; at fuzz 30 the MEM-X pair fell under its own 0.05 candidate (0.002738), so 5% is the fuzz that actually discriminates these particular pairs — the opposite finding from the landscape mockup's checklist, which needed fuzz 30 to suppress its own placer's per-run mesh-order noise. This mockup has no such per-run non-determinism (fixed primitive meshes, not a randomized piece placer), so the low-fuzz default works directly.

## Visual questions

Screenshots at `docs/northstar/research/mockups/fog/pass1/` (1920x1080).

- **Q1** (three states tellable apart at a glance): **yes**. Proving shot: `mission_t300.png` — pure black outside any circle, a visibly dimmer grey-green band around the patrol trail, and full-brightness terrain inside the two current-vision circles. Dim level used: 60% black overlay (alpha 0.6) on the explored band. This seems about right — legible but not so dark it reads as "still black." Candidate to revisit: 50% if Westley wants explored to read lighter.
- **Q2** (can see where units have been, no enemy drawn there): **yes**. Proving shot: `mission_t300.png` — the dim halo below/left of the top-right circle is the explored trail; no enemy sits in it. Caveat: in this specific fixture the patrol loop is short enough that `cells.explored` does not grow between tick 100 and tick 300 (see TRAIL-X above) — the trail is visible but not still expanding by t300.
- **Q3** (enemy structure visible but darkened in explored space): **yes**. Proving shot: `mission_t300.png`, top-right circle — the red structure box sits at full brightness while inside current vision; STRUCT-7's data (headless) confirms it darkens (`ENEMY_COLOR.darkened(0.6)`) once the cell drops to `explored`. Not separately screenshotted at that exact moment in the pass1 batch — HELD below.
- **Q4** (recon: every obstacle/zone/node readable, no enemy anywhere): **yes**. Proving shot: `recon.png` — all three obstacles, all three zones (purple interference, dark-green cover, olive hazard), all five node markers with labels, and both friendlies are visible; zero enemies. Confirmed also via pixel probe (0 enemy-red hits at any `enemies_px` coordinate).
- **Q5** (ring reads smaller inside interference; zone reads as a third treatment): **yes**. Proving shot: `close_ring.png` — the friendly's ring is visibly smaller than the interference zone's own boundary, and the zone's purple tint is clearly distinct from both black (never-seen) and grey-dim (explored). Data: `circles["1"]` 700wu → 350wu (exactly the 0.5 intensity halving).
- **Q6** (memory off: everything without current vision black): **yes** for the ground/fog layer. Proving shot: `memory_off.png` vs `memory_on.png` — the dim halo disappears entirely with memory off. **Caveat that reads like a bug at first glance**: obstacle boxes, zone patches, and node markers stay fully lit in `memory_off.png` even in pure-black areas, because §3 of the brief says to draw terrain features "always." This contradicts the derived rule in `references/E-12/notes.md` ("never seen: pure black, no terrain"). Flagged below as a real tension, not silently resolved.
- **Q7** (hygiene: magenta, black-where-shouldn't-be, clipped/overlapping text): **no** issues found in any of the 8 pass1 shots or the ~30 QA-run screenshots reviewed. HUD text is small at 1280x720 but fully legible and not clipped at 1920x1080.

## HELD

- **Q3**: structure-darkening is proven by data (STRUCT-7, headless) but not captured in its own dedicated pass1 screenshot at the exact explored (not visible) moment — the pass1 batch's mission shots all happen to have the structure in current vision. Not a failure, just an uncaptured angle.
- **TRAIL-X**: the diff threshold (≥0.02, unit positions moved) holds, but the "cells.explored grew" half of the candidate oracle does not — this fixture's patrol rectangle is small enough that its whole loop is explored well before tick 100, so t100→t300 shows movement but no new territory. A future revision wanting to demonstrate growing exploration should use a longer patrol path or measure explored growth over tick 0→100 instead of 100→300.

## Timings

- `TIME-10` (8 friendlies, 12 enemies, 64x64 grid, `compute_visibility()` + `FogCellGrid.update()`, 200-iteration average, headless): **0.5347 ms**, well under the 3ms budget.
- Interactive `timing_ms.tick_avg` (2 friendlies, 8 enemies, real fixture, `qa_tick`'s own rolling average incl. `_sync_view()`'s node rebuild): **3.9-4.2 ms/tick** across several runs.
- `fps_ms` (`Performance.TIME_PROCESS`, rendered frame time) at 1280x720: **217-1380 ms**, wide range. This machine had ~30 concurrent Godot QA processes from other agent sessions during every measurement (load average 18-23 on 16 cores) — see the report's environmental finding. The brief's own "up to a second per rendered frame" expectation for llvmpipe roughly holds even under that load.
