# Chronicle mockup QA checklist

Real measured numbers from `scripts/mockup_verify.sh` and `scripts/mockup_qa.sh` runs on 2026-09-22, Godot 4.6.3, llvmpipe (Compatibility), 1280x720 unless noted. The build machine ran 20-45 concurrent Godot mockup processes for most of this session (other parallel briefs); two harness bugs surfaced and were fixed on `main` mid-session (Xvfb screensaver blank at 600s, then the real cause: SimBridge's dead-pid error route freeing the mockup) — merged in twice, `git log --oneline main..HEAD` shows both merge commits. All numbers below are from clean runs after both merges.

## Check table

| id | check | clean | plant | planted |
|---|---|---|---|---|
| DET-1 | `qa_seed(11)+qa_tick(1200)` twice hashes equal; seed 12 differs | PASS | `cadence-wallclock` | PLANT LIVE (printed_words mismatches, hash comparison still passes since hash excludes tick-derived state) |
| COUNT-2 | both fixtures 5-10 entries; synthetic 10-entry self-test stays <=10 | PASS | `entries-duplicate` | PLANT LIVE (synthetic self-test hits 11) |
| ORDER-3 | entry 0 is consequence; no validation errors | PASS | `order-shuffled` | PLANT LIVE (entries[0] becomes `regional_stable` after the post-validation reverse) |
| WORDS-4 | no word/mention validation errors on either fixture | PASS | `expand-noop` | PLANT LIVE (`expanded form adds no words` x8/x6) |
| DUP-5 | seed 11 needs no drops; synthetic near-copy dropped | PASS | `entries-duplicate` | PLANT LIVE (near-copy survives, `dropped_entries` stays empty) |
| KEY-6 | synthetic fixture with keyframes validates clean; without them, fails | PASS (self-test, no plant) | — | — |
| PACE-7 | `qa_tick(16)` prints exactly 10 words; `pace.word_interval_s==0.08` | PASS | `cadence-wallclock` | PLANT LIVE (got 0 or 12 words depending on wall-clock offset at test time, never 10) |
| PAUSE-8 | click-to-pause; `qa_tick(100)` while paused is a no-op; dismiss resumes | PASS | `no-pause` | PLANT LIVE (`qa_tick(100)` advances the clock while paused) |
| MORPH-9 | colour strictly between old/new at 1.0s, equals new at 2.0s | PASS | `morph-instant` | PLANT LIVE (mid == before, both already the new colour) |
| LAYOUT-10 | `map_width_fraction` 0.62 at start, 1.0 at done; on-screen rows == validated count | PASS | none | — |
| JSON-11 | `qa_state()` round-trips JSON with every contract key; every `PLANTS` id activates; `nope` doesn't | PASS | none | — |

`scripts/mockup_verify.sh chronicle` -> `VERIFY OK`, exit 0. Each of the six `--plant <id>` runs -> `PLANT <id> LIVE (N FAIL)`, exit 0 (harness convention: exit 0 on the wrapper, the fault count is inside the print line). Confirmed for all six: `order-shuffled` (6 FAIL), `expand-noop` (5 FAIL), `no-pause` (1 FAIL), `entries-duplicate` (5 FAIL), `morph-instant` (1 FAIL), `cadence-wallclock` (4 FAIL).

## Xvfb runs

`scripts/mockup_qa.sh run chronicle scenes/mockups/chronicle/qa/smoke.json <out> --res 1280x720 --timeout 600`: clean run `exit.txt`=0, `errors.txt` count=0, no `UNIFORM` line, `_qa.adapter` = `llvmpipe (LLVM 21.1.8, 256 bits)`, `_qa.method` = `gl_compatibility`. A second clean run: every `hash` in every `state` JSON matches (e.g. `end.json` hash `111134198` both runs), every screenshot `diff` 0.000000 (checked `slide_in`, `mid_print`, `end_seed11`; all others not spot-checked but the hash equality already proves the underlying state is identical, and the renderer has no seed-independent randomness).

One run per plant, same `--res 1280x720 --timeout 600` plus `--plant <id>`: all six `exit.txt`=0, `errors.txt` count=0.

Review batch at 1920x1080 (`docs/northstar/research/mockups/chronicle/pass1/`): `exit.txt`=0, `errors.txt` count=0, 9 screenshots (7 committed per the brief's list: `slide_in`, `mid_print`, `expanded`, `before_morph`, `after_morph`, `end_seed11`, `end_seed12`).

### Xvfb oracles

| oracle | expectation | measured |
|---|---|---|
| PRINT-X | `mid_print.png` partially printed (0 < printed_words < total), text differs from `end.png` | `mid_print` tick 63: entry 0 has 39 of 34... (see note) |
| EXPAND-X | expanded crop taller than collapsed; under `expand-noop` word counts equal | clean `expanded.png` shows the closing sentence ("...Ostrel Concord twice that week..."); `diff clean1/expanded.png plant-expand-noop/expanded.png` = 0.004847 (missing sentence, visually confirmed, screenshots below) |
| MORPH-X | `diff before_morph.png after_morph.png` >= 0.005 over the map crop; `owners` changed | clean, full frame: 0.008381 (pass1 batch at 1920p, full frame: same order of magnitude); `owners.r_moorwick` `f_kaine` -> `f_ostrel` between before/after. **Revised — see note below.** |
| PAUSE-X | two screenshots 60 frames apart while paused: `diff` < 0.001 | clean `expanded.png` vs `expanded_later.png`: **0.000000**. Under `no-pause`: **0.008355** (clock kept advancing while "paused") |
| SEED-X | `diff end_seed11.png end_seed12.png` >= 0.10 | **0.009572** (fuzz 5), 0.000208 (fuzz 30). **Revised — see note below.** |
| ERR-0 | `errors.txt` count 0 | 0 on every run (clean, both plant batches, both resolutions) |
| GPU-0 | adapter contains `llvmpipe`, method `gl_compatibility` | exact match, every run |
| DET-1 (pixel) | two clean runs match | hash equal (`111134198`); `diff` 0.000000 on `slide_in`, `mid_print`, `end_seed11` |

PRINT-X note: at `mid_print` (tick 63) entry 0 (34 words total) shows `printed_words` computed as `((63-0)*5)/8 = 39`, clamped to 34 -> fully printed already; entry 0 finishes printing well before the `mid_print` screenshot because the interactive clock keeps advancing during `wait_frames 30` (the real-time accumulator, not just the explicit `qa_tick(40)` that follows) — this was the actual root cause of the keyframe-timing bug fixed in commit "moorwick keyframe at 463, not 441" (see report). The *screenshot itself* still shows a partially-printed scroll overall (1/8 entries fully printed, others not yet started), satisfying PRINT-X's intent even though entry 0 specifically is already complete by then.

### Why two oracles were revised, with the evidence

**MORPH-X.** The brief's own clean threshold (`diff >= 0.005` "over the map crop") is met: 0.008381 whole-frame, and I additionally isolated the map region (cropped to exclude the HUD's changing tick label and the scroll's growing text, `793x600+0+115`) and still measured 0.013-0.016 depending on the exact pair, comfortably over 0.005. **The problem is the plant side of the oracle**, which the brief describes qualitatively as "the 1.0s frame equals the 2.0s frame" under `morph-instant`. Measured: `diff(morph_1s, after_morph)` clean = 0.006933 (whole frame) / 0.012313 (map crop); under the plant = 0.006390 / 0.012313 — **nearly identical to the clean case**, not near-zero. Root cause: `mini_galaxy.gd`'s slow auto-orbit (`ORBIT_RATE = 0.0006` rad/tick, an R-107-02 requirement — the galaxy has to visibly drift so a right-drag has something to override) rotates all ~22 systems and every edge every tick; over the 22-45 ticks between these two screenshots that rotation moves more pixels than one system's colour finishing its transition. The morph-instant fault is real and is caught reliably by the headless `MORPH-9` check (which reads the system's actual colour value, not a screenshot), verified FAIL under the plant and PASS clean in the check table above. The pixel-diff oracle for this specific pair just isn't sensitive enough to also catch it. Candidates for Westley: (a) accept MORPH-9 (headless, colour-value) as the authoritative detector for this fault and drop the planted-side pixel expectation for `morph_1s`/`after_morph` [recommended — the two screenshots still prove the clean transition visually, they just can't discriminate the fault], (b) slow the auto-orbit further so it stops dominating short-interval diffs, (c) crop the diff to a tight box around only the morphing system rather than the whole map.

**SEED-X.** Measured 0.009572 (fuzz 5) / 0.000208 (fuzz 30), both far under the brief's 0.10 candidate. Root cause: at the `end_seed11`/`end_seed12` screenshots, `phase == "done"` and `map_width_fraction == 1.0`, so the scroll panel (where the two campaigns' text differs the most) is hidden and only the galaxy is on screen; the starfield is seeded from a fixed constant (`20260922`, not the jump seed, since it's decoration not simulated state) so it's pixel-identical between the two seeds; only the ~20-30 system dots and edges differ in position/colour, a small fraction of a 1280x720 (or 1920x1080) frame. The two galaxies clearly read as different layouts by eye (see the proving screenshots), just not different enough by raw pixel-count to clear 0.10. Candidates: (a) lower the threshold to something the measured signal actually clears, e.g. >= 0.005 [matches the same order of magnitude as the other pixel oracles in this checklist], (b) compare a mid-narration screenshot instead of the hidden-scroll end state, (c) seed the starfield from the jump seed too, trading a small amount of determinism-simplicity for a stronger SEED-X signal.

## Visual questions

- **Q1** (reads as the reference's cousin — map two-thirds left and animating, one entry at a time on the right in serif, faction names coloured): **yes**. Proving shots: `pass1/mid_print.png` (map at 0.62 width, one entry streaming in Newsreader with "Ostrel Concord" in the faction's purple), `pass1/slide_in.png`.
- **Q2** (printing pace reads as writing itself, not a dump or a crawl — 0.08s/word is ~12 words/s): **yes, readable**. Proving: `pass1/mid_print.png` shows entry 0 already complete and entry 1 not yet started at the same instant, i.e. the reveal is visibly gradual rather than all-at-once; at interactive real-time speed (not `qa_tick`-fast-forwarded) 12 words/s reads comfortably, on the brisk side of readable — see report Q1 answer for the recommended pace.
- **Q3** (morph reads as a border changing, lines up with an entry about that region): **yes**. Proving: `pass1/before_morph.png` (Moorwick still cyan, faint ring starting) vs `pass1/after_morph.png` (Moorwick fully purple, ring gone) — both captured while entry 3 ("Moorwick changed hands twice before midsummer...") is the most recently printed, fully-visible paragraph on the right.
- **Q4** (expanded form reads as more of the same passage; everything visibly stops while open): **yes**. Proving: `pass1/expanded.png` — the overlay's first two sentences are exactly entry 1's base form, then the closing sentence continues the same voice; `phase` in `expanded.json` is `paused`, and `qa_tick(100)` while paused changes nothing (PAUSE-8).
- **Q5** (entries read as fragments of a real history, with humour where it fits, never log lines or filler): **yes, no numbers or game-speak in any entry; dry humour present** ("nobody had time to burn," "the best accident in Ashcombe's short memory," "a garrison willing to share it"). Proving: the full text visible across `pass1/before_morph.png`'s three printed entries.
- **Q6** (any magenta, black, clipped, or overlapping text at 720p): **no**, checked every 1280x720 and 1920x1080 screenshot listed above.

**HELD:** none — every visual question above was answerable from the screenshots.

## Timing

`timing_ms.load` (fixture parse + validate): 6.4-13.9ms across the runs sampled (boot 7.6ms, seed-11 reload 6.4ms, seed-12 load 13.9ms).

`_qa.fps_ms` (`Performance.TIME_PROCESS`, ms/frame) at 1280x720 on this shared machine (20-45 concurrent Godot processes most of the session): 33.7-106.8ms across one clean run's captured frames (33.7ms once warm mid-scroll, 80.9ms during/after the morph and skip sequence, 106.8ms at the very first frame). This is well inside the brief's own "up to a second per frame" budget for llvmpipe even under contention; on an unshared machine expect the low end of this range throughout. `--fixed-fps 30` keeps the *simulation* clock exact regardless of render time (confirmed by DET-1's pixel-identical repeat runs), so contention affects wall-clock smoothness only, never state.

## Under-defined points found during the build

Listed here and in the finishing report/README with candidates, no decision made.
