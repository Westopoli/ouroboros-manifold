# Chronicle mockup QA checklist

Real measured numbers from `scripts/mockup_verify.sh` and `scripts/mockup_qa.sh` runs on 2026-09-22, Godot 4.6.3, llvmpipe (Compatibility), 1280x720 unless noted. This pass is the fix-list rerun after the fresh-eyes review (`docs/northstar/research/mockups/chronicle/README.md`): background, expansion-overlay opacity, morph salience, map richness, seed variety, plus a background-bleed HUD fix found while re-checking Q6. Numbers below are from clean runs after all six fixes.

## Check table

| id | check | clean | plant | planted |
|---|---|---|---|---|
| DET-1 | `qa_seed(11)+qa_tick(1200)` twice hashes equal; seed 12 differs | PASS | `cadence-wallclock` | PLANT LIVE (4 FAIL: printed-word mismatches, pace and pause checks) |
| COUNT-2 | both fixtures 5-10 entries; synthetic 10-entry self-test stays <=10 | PASS | `entries-duplicate` | PLANT LIVE (5 FAIL: synthetic self-test hits 11, category cap and score-order errors on both seeds) |
| ORDER-3 | entry 0 is consequence; no validation errors | PASS | `order-shuffled` | PLANT LIVE (6 FAIL: entries[0] no longer consequence on both seeds, plus downstream pace/pause failures once entry order no longer matches tick order) |
| WORDS-4 | no word/mention validation errors on either fixture | PASS | `expand-noop` | PLANT LIVE (5 FAIL: "expanded form adds no words" on every entry, both seeds, and the synthetic fixture) |
| DUP-5 | seed 11 needs no drops; synthetic near-copy dropped | PASS | `entries-duplicate` | PLANT LIVE (near-copy survives, `dropped_entries` stays empty) |
| KEY-6 | synthetic fixture with keyframes validates clean; without them, fails | PASS (self-test, no plant) | — | — |
| PACE-7 | `qa_tick(16)` prints exactly 10 words; `pace.word_interval_s==0.08` | PASS | `cadence-wallclock` | PLANT LIVE (word count wrong) |
| PAUSE-8 | click-to-pause; `qa_tick(100)` while paused is a no-op; dismiss resumes | PASS | `no-pause` | PLANT LIVE (1 FAIL: `qa_tick(100)` advances the clock while paused) |
| MORPH-9 | colour strictly between old/new at 1.0s, equals new at 2.0s | PASS | `morph-instant` | PLANT LIVE (1 FAIL: mid == before, both already the new colour) |
| LAYOUT-10 | `map_width_fraction` 0.62 at start, 1.0 at done; on-screen rows == validated count | PASS | none | — |
| JSON-11 | `qa_state()` round-trips JSON with every contract key; every `PLANTS` id activates; `nope` doesn't | PASS | none | — |
| CHECK-12 | map `WorldEnvironment.environment.background_mode == BG_COLOR` (not `BG_SKY`) and `background_color` is near-black (r<0.08, g<0.08, b<0.12) | PASS | none | — (new check added for the background fix, item 1) |

`scripts/mockup_verify.sh chronicle` -> `VERIFY OK`, exit 0. Each of the six `--plant <id>` runs -> `PLANT <id> LIVE (N FAIL)`, exit 0: `order-shuffled` (6 FAIL), `expand-noop` (5 FAIL), `no-pause` (1 FAIL), `entries-duplicate` (5 FAIL), `morph-instant` (1 FAIL), `cadence-wallclock` (4 FAIL). Unchanged from the prior pass's fault counts; CHECK-12 has no plant (it is a structural regression check, not a fault-injection target).

## Xvfb runs

`scripts/mockup_qa.sh run chronicle scenes/mockups/chronicle/qa/smoke.json <out> --res 1280x720 --timeout 100`: clean run `exit.txt`=0, `errors.txt` count=0, no `UNIFORM` line, `_qa.adapter` = `llvmpipe (LLVM 21.1.8, 256 bits)`, `_qa.method` = `gl_compatibility`. A second clean run: every `hash` in every `state` JSON matches (`boot`/`mid_print`/`printed`/`expanded`/`before_morph`/`after_morph`/`end` all hash `111134198`; `end_seed12`/`after_r` hash `1815867799`); every screenshot `diff` 0.000000 across all nine screenshots taken (`slide_in`, `mid_print`, `expanded`, `expanded_later`, `before_morph`, `morph_1s`, `after_morph`, `end_seed11`, `end_seed12`).

One run per plant, same `--res 1280x720 --timeout 100` plus `--plant <id>`: all six `exit.txt`=0, `errors.txt` count=0.

Review batch at 1920x1080 (`docs/northstar/research/mockups/chronicle/pass1/`): `exit.txt`=0, `errors.txt` count=0, 9 screenshots taken, 7 committed per the brief's list: `slide_in`, `mid_print`, `expanded`, `before_morph`, `after_morph`, `end_seed11`, `end_seed12`.

### Xvfb oracles

| oracle | expectation | measured |
|---|---|---|
| BG-X (new, item 1) | pixel sample in an empty map corner darker than (20,20,30) | (13,15,25) at three independent empty-corner samples (`(700,690)`, `(30,700)`, `(780,30)` on `slide_in.png`) — all three channels comfortably under threshold |
| PRINT-X | `mid_print.png` partially printed (0 < printed_words < total), text differs from `end.png` | at tick 63 (`mid_print`), 1/8 entries fully printed, the rest not yet started; visibly gradual, not a dump |
| EXPAND-X | expanded crop taller than collapsed; under `expand-noop` word counts equal | clean `expanded.png` shows the closing sentence continuing the same voice; `diff clean/expanded.png plant-expand-noop/expanded.png` = 0.004893 (missing sentence, visually confirmed) |
| MORPH-X | `diff before_morph.png after_morph.png` >= 0.005 over the map crop; `owners` changed | clean: 0.011270 whole-frame (up from the pre-fix pass's 0.008381 — the item-3 salience fix, a bigger ring and a scaled-up sphere, adds more differing pixels, which helps this oracle too). `owners.r_moorwick` `f_kaine` -> `f_ostrel` between before/after. Plant-side sensitivity issue previously found (auto-orbit churn dominates the 1s-2s window so `morph_1s` vs `after_morph` reads almost the same clean or planted, 0.009155 vs 0.009044) is unchanged by this pass's fixes — MORPH-9 (headless, colour-value) remains the reliable detector for `morph-instant`; see the prior pass's recorded candidates in the README, none re-decided here. |
| PAUSE-X | two screenshots 60 frames apart while paused: `diff` < 0.001 | clean `expanded.png` vs `expanded_later.png`: **0.000000**. Under `no-pause`: **0.011197** (clock kept advancing while "paused") |
| SEED-X | `diff end_seed11.png end_seed12.png` >= 0.10 | **0.009971** (default fuzz 5%), 0.017020 (fuzz 0%, most sensitive setting), 0.012316 (map-only crop). Still well under 0.10 after reshaping seed 12's galaxy (item 5); threshold not touched. See "Why SEED-X still can't clear 0.10" below. |
| ERR-0 | `errors.txt` count 0 | 0 on every run (clean x2, all six plant runs, 1920x1080 batch) |
| GPU-0 | adapter contains `llvmpipe`, method `gl_compatibility` | exact match, every run |
| DET-1 (pixel) | two clean runs match | hash equal on all 9 states; `diff` 0.000000 on all 9 screenshots checked |

### Why SEED-X still can't clear 0.10, after making seed 12 visibly different

Item 5 reshaped seed 12's galaxy: 18 systems (was 22), a 12-point flattened-ellipse outer ring with a sinusoidal radius wobble (was a near-circle at nearly the same radius as seed 11), one spoke per inner region instead of two of six, and a third faction colour (`f_dray`, green) rotated onto a third of the outer ring. By eye the two galaxies now read as clearly different layouts (compare `pass1/end_seed11.png`, a clean octagonal ring, against `pass1/end_seed12.png`, a smaller irregular spiral shape with a green node) — see those two files directly.

The raw pixel diff barely moved (0.009572 before the reshape, 0.009971 after) because the `end_seed11`/`end_seed12` screenshots are taken at `phase == "done"`, where `map_width_fraction == 1.0` hides the scroll (where the two campaigns' text differs the most), and the starfield — now 900 quads after item 4, denser than before — is seeded from a fixed constant, not the jump seed, so it is pixel-identical between the two seeds. The dominant majority of the 1280x720 (or 1920x1080) frame is therefore identical background and identical stars; only the ~18-22 system dots, their edges, and the polar grid (also seed-independent) differ, which is a small fraction of total pixels no matter how different the layout reads to a person. Checked at fuzz 0% (the most sensitive the harness's `diff` supports) it still only reaches 0.017020, and a crop restricted to the map region alone reaches 0.012316 — same order of magnitude. No threshold near 0.10 is reachable by a whole-frame or map-crop diff of this specific screenshot pair. Threshold not touched, per instructions; candidates from the prior pass (lower the number, compare mid-narration instead, or seed the starfield per-jump) remain open and are not re-decided here.

## Visual questions

- **Q1** (reads as the reference's cousin — map two-thirds left and animating, one entry at a time on the right in serif, faction names coloured): **yes, and materially stronger than the previous pass**. The previous pass's "yes" was against a flat-grey background bug (both inside and outside the map SubViewport rendered as plain grey, `(77,77,77)`, because the environment was set to `BG_SKY` with no sky assigned so it fell back to the project's default clear colour) that made the map read as a wireframe node diagram on grey, not a galaxy — the fresh-eyes review correctly caught this and it is why this pass exists. Fixed (item 1): the map now reads as near-black with a dense star field and a faint polar grid, and the scroll side is its own dark panel (`SURFACE` `#10141A`), distinct from the map's near-black. Proving shots: `pass1/mid_print.png` (map near-black with visible star field, "Halven Reach" in serif, faction colour on "Ostrel Concord"), `pass1/slide_in.png`. Pixel proof: an empty map corner sampled at `(13,15,25)`, all channels under the `(20,20,30)` darkness bar (BG-X above), versus `(77,77,77)` measured at the same point before the fix.
- **Q2** (printing pace reads as writing itself, not a dump or a crawl — 0.08s/word is ~12 words/s): **yes, readable**, unchanged from the prior pass's finding. Proving: `pass1/mid_print.png` shows entry 0 already complete and entry 1 not yet started at the same instant.
- **Q3** (morph reads as a border changing, lines up with an entry about that region): **yes, and the morphed node is now findable at a glance**, which the prior pass's should-fix flagged as missing ("the node is a 15px dot among twenty and the pulse ring has faded by the after frame, so nothing draws the eye"). Fixed (item 3): ring alpha and a new sphere scale-up now decay over 4.0s (twice the 2.0s colour-lerp window), so at the `after_morph.png` timestamp the morphed system (Moorwick) is still visibly larger with a lit ring, not a plain dot. Proving: `pass1/before_morph.png` (Moorwick a plain cyan dot, no ring yet) vs `pass1/after_morph.png` (Moorwick purple, clearly larger, ring still lit) — both captured while entry 3 ("Moorwick changed hands twice...") is the most recently printed paragraph on the right.
- **Q4** (expanded form reads as more of the same passage; everything visibly stops while open): **yes**. Fixed (item 2): the expansion overlay's `ColorRect` alpha is now 1.0 (was 0.94, and a separate layout-settle race at `wait_frames=2` after the click could still show a one-frame ghost of the row underneath even at full alpha — both are fixed; see the item-2 commit). Proving: `pass1/expanded.png` — the overlay's first two sentences are exactly entry 1's base form with no bleed-through of the row underneath, then the closing sentence continues the same voice; `phase` in `expanded.json` is `paused`, and `qa_tick(100)` while paused changes nothing (PAUSE-8, PAUSE-X 0.000000 above).
- **Q5** (entries read as fragments of a real history, with humour where it fits, never log lines or filler): **yes**, unchanged from the prior pass — no numbers or game-speak in any entry, dry humour present ("nobody had time to burn," "the best accident in Ashcombe's short memory"). Proving: the full text visible across `pass1/before_morph.png`'s three printed entries.
- **Q6** (any magenta, black, clipped, or overlapping text at 720p): **no, after one more fix found while re-checking this question**. Re-inspecting every screenshot at 500% crop for this rerun turned up a real regression from item 4's denser polar grid: at `phase == "done"` (map at full width), a grid spoke crossed directly behind the transparent-background HUD `PaceLabel`, rendering "Phase: done" as what looks like a stray apostrophe glitch, "Phase: 'done" — confirmed present in both `end_seed11.png` and `end_seed12.png` at the pre-fix crop, and confirmed absent at `mid_print.png` (0.62 width, different screen position, no line crossing there), proving it was a background-bleed issue, not a font rendering artefact. Fixed: the HUD's VBoxContainer now sits inside an opaque `PanelContainer` backdrop (alpha 0.85), same opaque-overlay pattern used for the scroll expansion in item 2. Checked every 1280x720 and 1920x1080 screenshot in this final pass at full res and at crops of every text region (HUD, scroll, expansion) — clean.

**HELD:** none — every visual question above was answerable from the screenshots.

## Timing

`timing_ms.load` (fixture parse + validate): 6.4-15.5ms across the runs sampled (boot 7.9ms, seed-11 reload 6.8ms, seed-12 load 15.5ms).

`_qa.fps_ms` (`Performance.TIME_PROCESS`, ms/frame) at 1280x720 on this shared machine: 46.8-121.8ms across one clean run's captured frames — up from the prior pass's 33.7-106.8ms range, consistent with item 4's denser star field (260 -> 900 quads) and the new polar grid geometry, still well inside the brief's "up to a second per frame" budget for llvmpipe. `--fixed-fps 30` keeps the simulation clock exact regardless of render time (confirmed again by this pass's pixel-identical repeat runs), so render-time changes affect wall-clock smoothness only, never state.

## Under-defined points found during the build

Carried over unchanged from the prior pass (not re-decided by this fix-list rerun): setup entries (Q-065-02, already open in the epic), the per-category cap of 2 (Q-065-01, already open in the epic), the expansion animation (instant show/hide, built), whether Skip also skips the morphs (yes, built), the blinking cursor (wall-clock driven, built), the fixture fields invented beyond the message contract (`category`/`region`/`score`/`keyframes`), and the `map_width_fraction`-at-"done" reading. Listed with candidates in the README's "Questions for Westley".

New from this pass, listed with candidates in the README: the MORPH-X and SEED-X pixel-oracle thresholds (see "Why SEED-X still can't clear 0.10" above and the README's MORPH-X note — both are about pixel-diff sensitivity on this specific screenshot pair, not about the underlying behaviour, which is independently proven correct by MORPH-9 and by eye).
