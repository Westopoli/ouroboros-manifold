# Layers mockup QA checklist

Real measured numbers from `scripts/mockup_verify.sh` and `scripts/mockup_qa.sh` runs on
2026-09-22, Godot 4.6.3, llvmpipe, 1280x720 unless noted. This pass is a fix-and-rerun on
top of the previous green pass, after a fresh-eyes review flagged two rendering defects
and two script nits. Fixes this pass: (1) unit bodies got `TRANSPARENCY_ALPHA` set
unconditionally at spawn, so an opaque unit sorted behind the translucent blocked patch
and vanished in `transfer_before.png`; now transparency is toggled only while a unit is
actually dimmed (`layer_alpha(u.layer) < 1.0`), opaque otherwise. (2) the blocked-demo
script parked the waiting unit at the blocked patch's exact centre, which sat directly
under the opaque obstacle and hid it; now parked at `(2000, 2300)` — inside the 350wu
blocked radius, outside the obstacle's 150wu-half-extent footprint. (3) `focus1.png` was
byte-identical to `slow_mid.png`; the script now flips focus 2→1 right before the shot.
(4) confirmed the obstacle body stays opaque and undimmed in code (unaffected either way).
(5) added `ring_px` (own/other sensor ring radius in window px, for the selected unit) to
`qa_state()` and measured the screen ratio against the world 0.5 rule.

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
| DIM-8 | non-focused layer's unit alpha 0.4, focused layer's 1.0, both directions; **new this pass**: the focused (undimmed) unit's material is opaque (`TRANSPARENCY_DISABLED`), not `TRANSPARENCY_ALPHA` | PASS | no-dimming | LIVE, 2 FAIL |
| FOCUS-9 | Tab (`cycle_focus_layer`) moves focus 1→2→1, the HUD strip's highlight follows | PASS | none | n/a |
| JSON-10 | `qa_state()` round-trips JSON with every contract key (now including `ring_px`); `qa_plant("nope")` false; every `PLANTS` id true | PASS | none | n/a |

`scripts/mockup_verify.sh layers` -> `VERIFY OK`, exit 0. All 6 `--plant <id>` runs ->
`PLANT <id> LIVE`, exit 0, with the same fail counts as the previous pass (no regressions
from the fixes above). No check needed a threshold change.

## Xvfb batch: rerun clean, both harness bugs still fixed

`clean1`/`clean2`: `scripts/mockup_qa.sh run layers qa/smoke.json <out> --res 1280x720
--timeout 600`, run twice. Both `exit.txt` = 0, `errors.txt` = `count: 0`, no `UNIFORM`
line, `_qa.adapter` = `"llvmpipe (LLVM 21.1.8, 256 bits)"`, `_qa.method` =
`"gl_compatibility"`. Wall time: 6 seconds each (`date` before/after: 13:21:56→13:22:02).
Plant runs: one per id, `--res 1280x720`, default timeout, all `exit 0` / `errors: count 0`
in a few seconds each. Review batch: `--res 1920x1080`, same script, `exit 0`,
`errors: count 0`, 11 seconds (13:27:24→13:27:35).

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
| blocked_cleared | 0.000000 |

All under the 0.005 threshold. PASS. (`blocked_cleared` was 0.000041 last pass; it is
exactly 0 this pass — the unit's new parked position is not adjacent to any transparency-
sort edge case the old centre position was.)

### Xvfb oracles

A harness fact still holds: `qa_state()`'s `units_px`/`ring_px` are in the project's fixed
1920x1080 base/stretch space regardless of the run's `--res` (confirmed again: `clean1`
720p and `review1080` 1080p report identical raw numbers for the same state).

| oracle | measured | verdict |
|---|---|---|
| HEIGHT-X | `units_px["1"].y`: before 538.88, after 407.26 (fixed 1920x1080 space); delta 131.61 = 12.19% of 1080 (R-010-03 wants > 5%) | PASS |
| HEIGHT-X planted (`wrong-height`) | before 538.88, after 538.88; delta 0.00 = 0.00% | correctly on the wrong side |
| MID-X | `transfer_mid` vs `transfer_before` diff 0.008444 (differs); vs `transfer_after` diff 0.022612 (differs) | PASS |
| MID-X planted (`instant-transfer`) | `transfer_mid` vs `transfer_after` diff 0.000037 (~equal, mid already completed) | correctly on the wrong side |
| DIM-X | `focus1` vs `focus2` diff 0.212905 (≥ 0.05) | PASS |
| DIM-X planted (`no-dimming`) | `focus1` vs `focus2` diff 0.000212 (< 0.01) | correctly on the wrong side |
| RING-X | `rings["1"]`: before `#33e6ff`, after `#ff8c26` (differ) | PASS |
| RING-X planted (`ring-colour-same`) | before `#33e6ff`, after `#33e6ff` (equal) | correctly on the wrong side |
| BLOCK-X | `blocked_attempt.json` tick 260: unit 1 `layer: 1`, `pending: true`, `pos: [2000, 2300]` (arrived at the new parked cell, still blocked, 30 ticks after the transfer call) | PASS |
| BLOCK-X planted (`blocked-ignored`) | `blocked_attempt.json` tick 260: unit 1 `layer: 2`, `pending: false`, `pos: [2000, 2300]` (transfer went straight through, ignoring the block) | correctly on the wrong side |
| ERR-0 | `errors.txt` = `count: 0` in every one of clean1, clean2, all 6 plant runs, review1080 | PASS |
| GPU-0 | `_qa.adapter` contains `llvmpipe`, `_qa.method` = `gl_compatibility` in every run | PASS |

`transfer_mid` vs `transfer_before` moved from 0.007815 (previous pass) to 0.008444: unit
1's body is now actually visible and rising in `transfer_before.png` (fix 1), so there is
slightly more real pixel content changing between those two frames than when the unit was
invisible in `transfer_before.png`.

### Item 5: `ring_px` and the sensor-ring screen ratio

`ring_px.own`/`ring_px.other` (window px, project's fixed 1920x1080 space) for the
selected unit (uid 1), across every state dump in the clean run:

| state | tick | unit 1 layer | own_px | other_px | screen ratio (other/own) |
|---|---|---|---|---|---|
| transfer_before | 0 | 1 | 287.6 | 175.3 | 0.610 |
| transfer_mid | 10 | 1 (mid-transition) | 316.0 | 175.3 | 0.555 |
| transfer_after | 30 | 2 | 350.7 | 143.8 | 0.410 |
| slow_mid | 80 | 2 | 350.7 | 143.8 | 0.410 |
| focus2 | 80 | 2 | 350.7 | 143.8 | 0.410 |
| blocked_attempt | 260 | 1 | 303.5 | 187.4 | 0.617 |
| blocked_cleared | 380 | 2 | 392.5 | 157.5 | 0.401 |

World radii are exactly right: `layer_view.gd`'s `_update_sensor_rings()`/`sensor_ring_px()`
draw the own ring at `u.sensor_wu` and the other-layer ring at `u.sensor_wu * 0.5` — always
exactly half, by construction, with no separate code path to drift. The screen ratio is
*not* a flat 0.5 and it is not constant either: it is ~0.61 when the selected unit is on
layer 1 (own ring at ground height 0, other ring at layer-2 height 600 — closer to the
camera) and ~0.41 when the unit is on layer 2 (own ring at height 600, other ring at
height 0 — farther from the camera). The two rings are drawn at *different* world heights
(the unit's own current layer height and the *other* layer's height), and the camera sits
at a fixed world Y (2500) with a fixed 60° pitch, so a ring nearer that camera height
projects larger per world-unit than a ring farther from it — a straightforward perspective-
distance effect from the fixed camera geometry, the same family of effect as foreshortening
under a pitched camera, not a bug in the ring radii themselves. Conclusion: the world
radius is right; the screen ratio drifts from 0.5 by camera perspective depending on which
layer is "home," ranging 0.40–0.62 across this run rather than a single fixed number. No
code change made — this is a measurement, not a defect, per the brief's own framing.

### The two script fixes (this session)

**Blocked-demo park position (item 2).** The unit was parked at `(2000, 2000)`, the
blocked patch's exact centre — which is also the obstacle's exact centre, so the obstacle's
own opaque geometry fully hid the unit in `blocked_attempt.png`; only the HUD list proved
it was waiting. Now parked at `(2000, 2300)`: 300wu from the blocked centre (inside the
350wu radius) and 300wu outside the obstacle's z half-extent (obstacle footprint spans z
1850–2150). `blocked_attempt.png` now shows the unit directly, cyan box with its yellow
selection ring, clearly waiting beside the obstacle, HUD confirming "1 fast L1 <". See Q4.

**focus1 real post-flip frame (item 3).** `qa/smoke.json` now sets focus to 2 and then
back to 1 immediately before the `focus1` screenshot. Measured result: `focus1.png` is
*still* byte-identical to `slow_mid.png` (diff 0.000000, both runs). This is expected on
inspection, not a leftover bug: rendering in `layer_view.gd` is a pure function of
`(tick, unit positions/layers, focus_layer, camera, selection)`, with no additional
hidden state; flipping focus to 2 and back to 1 ends at the exact same tuple `slow_mid.png`
was captured at (same tick 80, same positions, same camera, focus_layer back to 1), so the
same tuple renders the same pixels regardless of the path taken to reach it. The fix does
exercise the toggle code path for real (proven by `focus2.png` differing from both by
0.21), it just cannot make the *final* frame differ from an earlier frame that already
shared every value the renderer reads. If a genuinely distinct `focus1` frame is wanted, it
would need either a different tick or different camera/selection state at capture time —
noted as a candidate for a future pass, not built here (out of the five-item list).

## Visual questions

Judged from the full 1920x1080 review batch in `docs/northstar/research/mockups/layers/pass1/`.

- **Q1** (layer 2 unit reads as higher, not just a different colour): **yes** — proving
  screenshot `transfer_after.png`: unit 1 (now layer 2, orange ring, visible and elevated)
  sits clearly above the ground and above unit 2 (still layer 1, cyan ring, grounded) in
  the same frame. Numerically HEIGHT-X above (12.19% of window height).
- **Q2** (rise reads as motion; slow type visibly lags fast): **yes** — `transfer_mid.png`
  shows unit 1 partway up, strictly between `transfer_before.png` and `transfer_after.png`
  (own sensor rings visibly at different heights across the three frames). The slow unit's
  lag: `slow_mid.png` shows unit 2 mid-transition (tick 80, `ticks_left: 50` of 100) while
  unit 1 finished at tick 20; unit 2's own screen position moves from (786.9, 631.9) at
  rest to (768.9, 578.9) mid-transition — a real ~53px rise at the halfway point, matching
  its own half-progress, though visually subtle at this camera distance since the two
  friendlies sit far enough apart in z that a direct glance doesn't immediately read it.
  Read as: proven, but subtle (same finding as last pass; unaffected by this pass's fixes).
- **Q3** (ring shows layer, strip shows focus, dimming shows focus): **yes** — ring colour
  half: `transfer_after.png`'s `qa_state` (`rings["1"]` `#33e6ff`→`#ff8c26`). Dimming/strip
  half: `focus1.png` (`L1*` highlighted, layer-2 units washed out) vs `focus2.png` (`L2*`
  highlighted, reversed) — same units, same camera, flips cleanly, DIM-X confirms
  numerically (0.21 diff). One nuance found this pass, not fixed (out of the five-item
  list): for the *selected* unit specifically, the layer-colour ring (7wu thick) sits only
  7wu inside the white/yellow selection ring (6wu thick, itself rendered with a yellow tint
  from the Compatibility renderer's tonemap on a fully-emissive white material, not a
  colour set anywhere in code) — at this camera distance the two rings' ~3px gap
  anti-aliases into one pale band, so the selected unit's own layer-colour ring is hard to
  read directly off it (crop-verified: unit 2, not selected, shows a clean solid cyan
  ring). The HUD list's per-unit colour swatch (never touched by selection) is unambiguous
  regardless.
- **Q4** (blocked region reads as blocked, waiting unit reads as waiting): **yes, fixed
  this pass** — `blocked_attempt.png` (new parked position `(2000, 2300)`): the unit is
  now fully visible, cyan box with its yellow selection ring, sitting beside (not under)
  the obstacle, inside the red-tinted blocked patch, HUD confirming "1 fast L1 <" (still
  layer 1, still pending). `blocked_cleared.png` recovers cleanly: unit visible, elevated,
  layer 2, HUD "1 fast L2 <". Previous pass's "partial" (HUD-only proof, unit hidden behind
  the obstacle) is resolved.
- **Q5** (two sensor rings legible, full own-layer + half other-layer): **yes** — visible
  in `transfer_mid.png` and `blocked_cleared.png`: the own-layer ring is large relative to
  the 4,000wu canvas and the half-radius other-layer ring is clearly nested and
  distinguishable inside it. See "Item 5" above for the precise screen-space ratio, which
  is not a flat 50% due to camera perspective (0.40–0.62 depending on the unit's current
  layer) even though the world radius is exactly 50% by construction.
- **Q6** (magenta/black/clipped/overlapping text at 720p): **no** — no magenta, no solid-
  black frames, no clipped or overlapping HUD text in any of the 8 screenshots.

**Item 1 fix confirmed** (`transfer_before.png`): unit 1 (selected, layer 1, standing near
the obstacle) now renders correctly from the `qa_camera 2500 2000 2000` angle used
throughout the script — the previous pass's finding ("unit 1 does not render at all... its
own sensor ring is visible but the unit's box is not") is gone; the small cyan box is
visible at the edge of the blocked patch, right where the sensor ring's own edge crosses
it. Root cause confirmed exactly as suspected: `_spawn_unit_node()` set
`TRANSPARENCY_ALPHA` unconditionally at spawn, so the opaque-looking body was actually in
the engine's transparent render pass and sorted behind the translucent blocked-patch plane
along that specific camera ray; now transparency is only enabled while `layer_alpha(...) <
1.0` (i.e. while the unit is genuinely dimmed), so an undimmed body renders in the opaque
pass and cannot lose a depth-sort fight with a translucent plane.

**Item 4 confirmed, no code change needed**: the obstacle's material (`_build_obstacle()`)
is never touched by `layer_alpha()` or any dimming/focus logic — verified by grep (no
`_obstacle` reference outside `_build_obstacle()`) and by screenshot (`focus1.png` vs
`focus2.png`: the obstacle's pixels are byte-for-byte identical despite the dimming flip).
The obstacle *does* still show a visible three-tone banding in every screenshot that frames
it (top tan / mid tan / lower red-tinted band) — but this is a **separate, pre-existing**
rendering artifact from the translucent `GroundLayer2` plane and the red blocked-patch
plane (both still `TRANSPARENCY_ALPHA`, both crossing through the obstacle's opaque
geometry at its mid-height) compositing over the opaque box at this camera angle — the same
family of transparent-over-opaque sort issue item 1 fixed for unit bodies, not yet applied
to the ground/patch planes crossing the obstacle. Confirmed unrelated to focus/dimming, so
it does not read as "a third *layer*" in the R-009/R-010 sense the item was guarding
against, but it is a visible artifact worth flagging for a future pass (out of this
session's five-item list; same family as the already-known "camera-angle-dependent
transparency artifact" from the previous pass's README).

**HELD:** none outright. Q2 stays "subtle" (unchanged from last pass, unaffected by this
pass's fixes). The item-3 focus1/slow_mid finding is not a HELD item — it's an explained,
expected result of the instructed fix, recorded above rather than guessed at.

## Timings

- `timing_ms.tick_avg` (pure `ToySim.step()` cost, CPU-bound): 0.0ms (tick 0) →
  0.0041ms/tick (tick 10) → 0.0045ms/tick (tick 30) → 0.0041ms/tick (tick 80) →
  0.0040ms/tick (tick 260) → 0.0040ms/tick (tick 380). Negligible; 20Hz sim is nowhere
  near the bottleneck.
- `_qa.fps_ms` (Godot's own per-process-frame CPU accounting, llvmpipe/Compatibility,
  720p): 283.9ms (boot) → 205.9ms (mid/after/slow_mid) → 195.4ms (focus2/blocked_attempt/
  blocked_cleared) → 226.3ms (after_r).
- Wall time, one full clean run (`smoke.json`, 8 screenshots + 9 state dumps, 720p):
  **6 seconds** (`date` bracketing `clean1`: 13:21:56 → 13:22:02).
- Wall time, 1920x1080 review batch: **11 seconds** (13:27:24 → 13:27:35).
