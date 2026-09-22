# Layers mockup QA checklist

Real measured numbers from `scripts/mockup_verify.sh` and `scripts/mockup_qa.sh` runs on
2026-09-22, Godot 4.6.3, llvmpipe, 1280x720 unless noted. This pass reran the full batch
after two harness fixes landed on `main`: `-s 0` (Xvfb screensaver off) and the qa_boot
autoload-free fix (`b65afa8` — the real cause of the earlier stall: in a worktree the
Python sim dies at once, `SimBridge` routed `SceneRouter` to the error screen, whose fade
dimmed successive screenshots and whose scene swap froze the next `screenshot` verb). Both
clean runs and all six plant runs finished in ~6-10 seconds each, `exit 0`, no stall.

## Headless checks (`scripts/mockup_verify.sh layers`)

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | same seed/stream twice, hash + transition start/end ticks equal; self-test proves a global-RNG variant would NOT pass | PASS | none (self-test) | n/a |
| DUR-2 | fast completes at exactly tick 20, slow at exactly tick 100, fast first | PASS | instant-transfer | LIVE, 8 FAIL |
| BLOCK-3 | transfer onto a blocked cell stays pending, `layer` unchanged; starts once the unit reaches an open cell, completes after the duration | PASS | blocked-ignored | LIVE, 2 FAIL |
| SAME-4 | same-layer transfer: no transition, no pending, no layer change | PASS | none | n/a |
| VIS-5 | fast unit sees a layer-2 enemy at 350wu (400wu effective radius), not at 450wu, not the far layer-1 enemy; slow unit sees neither cross-layer enemy | PASS | cross-layer-full-range | LIVE, 1 FAIL |
| HEIGHT-6 | mid-transition y strictly between the two layer heights; completed y equals `layer_height_wu` (+ the unit box's own half-extent) | PASS | wrong-height | LIVE, 2 FAIL |
| RING-7 | ring colour unchanged before the completion tick, flips exactly at it, two layers differ | PASS | ring-colour-same | LIVE, 1 FAIL |
| DIM-8 | non-focused layer's unit alpha 0.4, focused layer's 1.0, both directions | PASS | no-dimming | LIVE, 2 FAIL |
| FOCUS-9 | Tab (`cycle_focus_layer`) moves focus 1→2→1, the HUD strip's highlight follows | PASS | none | n/a |
| JSON-10 | `qa_state()` round-trips JSON with every contract key; `qa_plant("nope")` false; every `PLANTS` id true | PASS | none | n/a |

`scripts/mockup_verify.sh layers` -> `VERIFY OK`, exit 0. All 6 `--plant <id>` runs -> `PLANT <id> LIVE`, exit 0. No check needed a threshold change from the brief's candidates.

## Xvfb batch: complete, both harness bugs fixed

`clean1`/`clean2`: `scripts/mockup_qa.sh run layers qa/smoke.json <out> --res 1280x720
--timeout 600`, run twice. Both `exit.txt` = 0, `errors.txt` = `count: 0`, no `UNIFORM`
line, `_qa.adapter` = `"llvmpipe (LLVM 21.1.8, 256 bits)"`, `_qa.method` =
`"gl_compatibility"`. Wall time: 6 seconds each (`date` before/after: 11:13:42→11:13:48).
Plant runs: one per id, `--res 1280x720`, default timeout, all `exit 0` / `errors: count 0`
in 6-10s each. Review batch: `--res 1920x1080`, same script, `exit 0`, `errors: count 0`,
10 seconds.

### DET-1 pixel (clean1 vs clean2)

Every `hash` in every state file (`boot`, `transfer_before`, `transfer_mid`,
`transfer_after`, `slow_mid`, `focus2`, `blocked_attempt`, `blocked_cleared`, `after_r`)
is byte-identical between the two runs. `scripts/mockup_qa.sh diff` on every one of the 8
screenshots:

| screenshot | diff |
|---|---|
| transfer_before | 0.000000 |
| transfer_mid | 0.000000 |
| transfer_after | 0.000000 |
| slow_mid | 0.000000 |
| focus1 | 0.000000 |
| focus2 | 0.000000 |
| blocked_attempt | 0.000000 |
| blocked_cleared | 0.000041 |

All under the 0.005 threshold. PASS.

### Xvfb oracles

A harness fact worth recording: `qa_state()`'s `units_px` is **not** in the run's actual
`--res` window-pixel space. `cam.unproject_position()` returns coordinates in the
project's configured base/stretch resolution (1920x1080, `canvas_items`/`expand`),
independent of the OS window size passed to `--resolution` — confirmed by `clean1` (720p)
and `review1080` (1080p) reporting the *identical* raw `units_px` numbers for the same
state. This only matters for the "percent of window height" arithmetic below; the
underlying oracle (does the delta clear a real threshold) is unaffected either way. Since
1920x1080 is also the project's actual fullscreen resolution (what Westley's `--scene`
launch renders), that is the correct denominator, not the QA run's own `--res`.

| oracle | measured | verdict |
|---|---|---|
| HEIGHT-X | `units_px["1"].y`: before 538.88, after 407.26 (fixed 1920x1080 space); delta 131.61 = 12.19% of 1080 (R-010-03 wants > 5%) | PASS |
| HEIGHT-X planted (`wrong-height`) | before 538.88, after 538.88; delta 0.00 = 0.00% | correctly on the wrong side |
| MID-X | `transfer_mid` vs `transfer_before` diff 0.007815 (differs); vs `transfer_after` diff 0.022612 (differs) | PASS |
| MID-X planted (`instant-transfer`) | `transfer_mid` vs `transfer_after` diff 0.000037 (~equal, mid already completed) | correctly on the wrong side |
| DIM-X | `focus1` vs `focus2` diff 0.212905 (≥ 0.05) | PASS |
| DIM-X planted (`no-dimming`) | `focus1` vs `focus2` diff 0.000212 (< 0.01) | correctly on the wrong side |
| RING-X | `rings["1"]`: before `#33e6ff`, after `#ff8c26` (differ) | PASS |
| RING-X planted (`ring-colour-same`) | before `#33e6ff`, after `#33e6ff` (equal) | correctly on the wrong side |
| BLOCK-X | `blocked_attempt.json` tick 260: unit 1 `layer: 1`, `pending: true`, `pos: [2000, 2000]` (unmoved, still blocked, 30 ticks after the transfer call) | PASS |
| BLOCK-X planted (`blocked-ignored`) | `blocked_attempt.json` tick 260: unit 1 `layer: 2`, `pending: false` (transfer went straight through, ignoring the block) | correctly on the wrong side |
| ERR-0 | `errors.txt` = `count: 0` in every one of clean1, clean2, all 6 plant runs, review1080 | PASS |
| GPU-0 | `_qa.adapter` contains `llvmpipe`, `_qa.method` = `gl_compatibility` in every run | PASS |

### The smoke-script fix (this session)

The brief's builder ordered the blocked-transfer demonstration's final leg with
`call qa_transfer 1 1` — a transfer *to layer 1*, and `toy_sim.gd`'s blocked mask only
ever applies to a transfer whose *target* is layer 2 (`is_blocked()`: `if layer != 2:
return false`), so that call could never be blocked no matter where the unit stood.
Fixed: the script now brings unit 1 back to layer 1 (`qa_transfer 1 1`, itself unblocked,
just repositioning), walks it onto the blocked patch's centre cell (`qa_move 1 2000
2000`), orders it to layer 2 (`qa_transfer 1 2`) — now genuinely inside the blocked
region — waits 30 ticks (confirmed still `pending: true`, `layer: 1`,
`blocked_attempt.png`), then walks it clear (`qa_move 1 2000 2500`, outside the 350wu
blocked radius) and waits for the transfer to resolve and complete
(`blocked_cleared.png`, `layer: 2`, `pending: false`). Screenshot names unchanged.

## Visual questions

Judged from the full 1920x1080 review batch in `docs/northstar/research/mockups/layers/pass1/`.

- **Q1** (layer 2 unit reads as higher, not just a different colour): **yes** — proving
  screenshot `transfer_after.png`: unit 1 (now layer 2, orange ring) sits visibly above
  the ground and above unit 2 (still layer 1, cyan ring, grounded) in the same frame.
  Numerically HEIGHT-X above.
- **Q2** (rise reads as motion; slow type visibly lags fast): **yes** — `transfer_mid.png`
  shows unit 1 partway up, strictly between `transfer_before.png` and
  `transfer_after.png`. The slow unit's lag: `slow_mid.png` shows unit 2 mid-transition
  (tick 80, `ticks_left: 50` of 100) while unit 1 finished at tick 20; comparing unit 2's
  *own* screen position at rest (`units_px` 786.9, 631.9 at boot/transfer_after) against
  mid-transition (786.9→768.9 x, 631.9→578.9 y) is a real ~53px rise at the halfway point,
  matching its own half-progress — but it is a visually subtle rise at this camera
  distance/angle since the two friendlies are far enough apart in z that a direct A/B
  frame comparison at a glance is not as immediate as unit 1's own before/after. Read as:
  proven, but subtle.
- **Q3** (ring shows layer, strip shows focus, dimming shows focus): **yes** — ring colour
  half: `transfer_after.png` (unit 1 orange vs unit 2 cyan). Dimming/strip half:
  `focus1.png` (`L1*` highlighted, unit 1/layer-2 units washed out, unit 2/layer-1 units
  full brightness) vs `focus2.png` (`L2*` highlighted, reversed) — same units, same
  camera, flips cleanly. DIM-X above confirms it numerically (0.21 diff, well past 0.05).
- **Q4** (blocked region reads as blocked, waiting unit reads as waiting): **partial** —
  the red-tinted patch and grey obstacle read clearly as "blocked" in every screenshot
  that frames them (e.g. `transfer_before.png`, `blocked_attempt.png`). The *waiting unit*
  half is weaker than intended: to guarantee the block deterministically, unit 1 was
  parked at the blocked patch's exact centre — which is also directly under the tall
  obstacle box, so the unit itself is fully occluded by the obstacle's own opaque geometry
  from this camera angle (confirmed by a diagnostic camera reposition: the unit is
  correctly there, cyan, with its selection ring, when viewed from directly above — see
  the scratch diagnostic, not committed). In `blocked_attempt.png` a viewer can only infer
  "unit 1 is waiting" from the HUD list still reading "1 fast L1" (not "L2") — the box
  itself is invisible. `blocked_cleared.png` recovers cleanly: unit 1 is visible, elevated,
  layer 2, HUD reads "1 fast L2 <". Candidate fix for a future pass: block the unit at a
  position inside the 350wu blocked radius but outside the 150wu obstacle footprint (e.g.
  `(2000, 2300)`) so it stays visible while still guaranteed-blocked.
- **Q5** (two sensor rings legible, full own-layer + half other-layer): **yes** — visible
  in `transfer_mid.png` and `blocked_cleared.png`: the own-layer ring is large relative to
  the 4,000wu canvas (~40% of frame width at 800wu radius) and the half-radius other-layer
  ring is clearly nested and distinguishable inside it. Legible, but the own-layer ring's
  size dominates the frame — worth flagging, see "Under-defined points."
- **Q6** (magenta/black/clipped/overlapping text at 720p): **no** — no magenta, no solid-
  black frames, no clipped or overlapping HUD text in any of the 8 screenshots.

One rendering finding, not fixed (see reasoning below): in `transfer_before.png`, unit 1
(selected, layer 1, standing near the obstacle) does not render at all from the
`qa_camera 2500 2000 2000` angle used throughout the script — its own big sensor ring is
visible (correctly centred on it) but the unit's box is not. Diagnosed via a throwaway
camera-angle probe (not committed): repositioning the camera directly over the unit shows
it fully present, selected, correctly coloured — so this is not a spawn/visibility logic
bug. It reproduces because unit 1's camera ray, at this specific angle, passes through the
blocked patch's translucent plane (`TRANSPARENCY_ALPHA` on both the patch and the unit
body) before reaching the unit, and Godot's transparent-pass sort appears to composite the
patch over the unit instead of blending it, at this one camera/position combination. It
does not recur in any other screenshot (units elsewhere in the script are not on this
exact ray) and does not affect any Q1-Q6 answer, since `transfer_mid.png`/
`transfer_after.png` show the same unit clearly. Left unfixed per the brief ("fix nothing
... unless a screenshot shows a defect" that blocks an answer) — flagged here as a
candidate for the design phase: either avoid `TRANSPARENCY_ALPHA` on opaque-alpha unit
bodies, or don't route a unit's default camera ray through the blocked patch.

**HELD:** none outright; Q2 and Q4 are marked "subtle"/"partial" above rather than a clean
yes, with the reasoning and a candidate fix recorded instead of guessing.

## Timings

- `timing_ms.tick_avg` (pure `ToySim.step()` cost, CPU-bound): 0.0ms (tick 0) →
  0.0043ms/tick (tick 10) → 0.0039ms/tick (tick 30) → 0.0040ms/tick (tick 80) →
  0.0040ms/tick (tick 260) → 0.0043ms/tick (tick 380). Negligible; 20Hz sim is nowhere
  near the bottleneck.
- `_qa.fps_ms` (Godot's own per-process-frame CPU accounting, llvmpipe/Compatibility,
  720p): 364.8ms (boot) → 218.2ms (mid/after/slow_mid) → 188.3ms (blocked_attempt) →
  222.6ms (blocked_cleared).
- Wall time, one full clean run (`smoke.json`, 8 screenshots + 9 state dumps, 720p):
  **6 seconds** (`date` bracketing `clean1`: 11:13:42 → 11:13:48).
