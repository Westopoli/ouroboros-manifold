# Layers mockup QA checklist

Real measured numbers from `scripts/mockup_verify.sh` and `scripts/mockup_qa.sh` runs on
2026-09-22, Godot 4.6.3, llvmpipe, 1280x720 unless noted. The Xvfb batch was run on a
severely contended shared host (see "Xvfb batch: blocked by host contention" below); every
headless number is complete and clean, the Xvfb visual batch is partial.

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

## Xvfb batch: blocked by host contention

The build host was running **31 concurrent Godot/Xvfb processes** from other agent sessions
at the time of this QA pass (`pgrep -af godot | wc -l` = 31; `uptime` load average 18-22 on a
16-core machine; `free -h` showed 833MB free of 30GB). Every `scripts/mockup_qa.sh run`
attempt — four full smoke-script runs (up to a 1500s/25min timeout) and five isolation
probes — captured the same first 4-5 screenshots within seconds, then stalled indefinitely
on the next `screenshot` call. A control probe (`ps`/`/proc/<pid>/status`) during one stall
showed the Godot process at 155% CPU with `wchan=futex_do_wait`: **busy, not deadlocked** —
genuinely CPU-starved, not a hang in the driver or my scene.

Isolation work (recorded so a re-run under a calm host doesn't have to redo it):
- A trivial static probe script (seed, camera, 5 bare `screenshot` calls, no ticks, no state
  change) reproduces the **exact same stall at the 5th screenshot** and the **exact same
  brightness curve** (0.4331/0.3867/0.3379/0.2887 mean pixel value) as the full smoke
  script. This rules out anything in this mockup's game logic — a static, near-empty scene
  degrades identically. It is a property of repeated frame capture under this host's
  software-GL stack, not of `layers_mockup.gd`/`toy_sim.gd`/`layer_view.gd`.
- Tested and ruled out: `--grab external` (X11 window grab via ImageMagick instead of
  `get_viewport().get_texture()`) shows the same darkening and is slower to the same stall.
  Disabling `DirectionalLight3D.shadow_enabled` shifts the starting brightness but not the
  curve shape or the stall point (reverted, not the cause — see the commit that reverts it).
  Godot 4.6's `Environment` has no direct auto-exposure property in this build and this
  scene never assigns `Camera3D.attributes`, so camera/environment auto-exposure is not
  the mechanism either.
- What DOES hold up under this contention: `qa_state()`'s `hash` field is **byte-identical
  across two independent process runs** (`clean1` and `clean4`, ~40 minutes apart) at every
  checkpoint both reached (tick 0, 10, 30 — see DET-1-XVFB below), and the one screenshot
  every run completes cleanly (`transfer_before`, always the 1st capture) diffs at
  **0.004270** between those two runs — under the brief's 0.005 threshold. The simulation
  and the render are both genuinely deterministic; only the *N-th-capture-in-a-process*
  degradation is new and host-specific.

None of this is in `scenes/mockups/layers/**`'s control (confirmed by the empty-scene
probe) and `scenes/mockups/_shared/qa_driver.gd`/`qa_boot.gd` are fenced — brief instruction
followed: stopped, did not patch, reporting instead. **Recommend re-running
`scripts/mockup_qa.sh run layers scenes/mockups/layers/qa/smoke.json <outdir>` and the
1920x1080 review batch once the host is not running a dozen-plus concurrent Godot
processes; nothing in this mockup needs to change first.**

### DET-1 under Xvfb (partial, real data)

| checkpoint | `clean1` hash | `clean4` hash | equal |
|---|---|---|---|
| tick 0 (transfer_before) | 3306213836 | 3306213836 | yes |
| tick 10 (transfer_mid) | 2250708452 | 2250708452 | yes |
| tick 30 (transfer_after) | 936252288 | 936252288 | yes |

`transfer_before.png` clean1 vs clean4: `diff` = 0.004270 (threshold < 0.005, fuzz 5%).

### Oracles computable from the 4 screenshots + states that did complete

| oracle | measured | verdict |
|---|---|---|
| HEIGHT-X | `units_px[1].y`: before 538.88px, after 407.26px; delta 131.6px = 18.3% of the 720px window (> 5%, R-010-03) | PASS |
| MID-X | `units_px[1].y` mid-transition 479.57px, strictly between 538.88 and 407.26 | PASS |
| RING-X | `rings["1"]`: before `#33e6ff`, mid (tick 10, still pending completion) `#33e6ff` unchanged, after (tick 30, completed) `#ff8c26` | PASS |
| DIM-X | **HELD** — needs `focus1.png`/`focus2.png`, never rendered (5th/6th screenshot) |
| BLOCK-X | **HELD** — needs `blocked_attempt.png`, never rendered (11th screenshot); proven instead by the headless BLOCK-3 check (see note below) |
| ERR-0 | every run exits 124 (killed by the wrapper's own timeout, not a script error); `errors.txt` count is 0 in every run that got far enough to be scanned | PARTIAL — no run reached its own `exit 0` |
| GPU-0 | `_qa.adapter` = `"llvmpipe (LLVM 21.1.8, 256 bits)"`, `_qa.method` = `"gl_compatibility"` in every state dump captured | PASS |

**Note on `qa_transfer 1 1` / `blocked_attempt`:** the smoke script's own final block
sequence orders the already-layer-2 unit *down* to layer 1 (`call qa_transfer 1 1`), but
`toy_sim.gd`'s blocked mask exists only on layer 2 (spec'd that way: "a blocked mask on
layer 2"), so layer 1 can never itself be blocked and that specific call always succeeds
uneventfully once the harness gets that far. See "Under-defined points" in the README —
`BLOCK-3`'s actual pending/resolve behaviour (R-002-02) is proven directly, headless,
against a unit ordered *up* into the blocked cell.

## Visual questions

Judged from the 4 screenshots that did render (`transfer_before`, `transfer_mid`,
`transfer_after`, `slow_mid`) at `<scratch>/layers/clean4/`, later copied to
`docs/northstar/research/mockups/layers/pass1/`. `slow_mid.png` rendered fully black
(the N-th-capture darkening above) and could not be judged visually; its state JSON was
still usable for HEIGHT-X/RING-X-style data where relevant.

- **Q1** (layer 2 unit reads as higher, not just a different colour): **yes**, in
  `transfer_after.png` — proving screenshot: `transfer_after.png` (unit 1, now on layer 2,
  sits visibly above the ground plane and above unit 2, which is still on layer 1; also
  confirmed numerically, HEIGHT-X above).
- **Q2** (rise reads as motion; slow type visibly lags fast): **yes** for the rise
  (`transfer_mid.png` shows unit 1 partway up, between `transfer_before.png` and
  `transfer_after.png`). **HELD** for "does the slow type visibly lag" — `slow_mid.png`
  (the shot meant to show it) rendered black; the state JSON confirms it numerically
  (unit 2 mid-transition, `ticks_left: 50` of 100, at tick 80, while unit 1 finished at
  tick 20) but that is not a visual judgement.
- **Q3** (ring shows layer, strip shows focus, dimming shows focus): **HELD** —
  `focus1.png`/`focus2.png` never rendered. The ring-colour half (RING-X) is proven
  visually in `transfer_after.png` (unit 1's ring is visibly a different colour/hue than
  unit 2's) and numerically (RING-X table above); the dimming half is HELD.
- **Q4** (blocked region reads as blocked, waiting unit reads as waiting): **HELD** —
  `blocked_attempt.png`/`blocked_cleared.png` never rendered. `transfer_before.png` does
  show the red-tinted blocked patch on the layer-2 plane and the grey obstacle box, so the
  *marking* is visible; a waiting (pending) unit was never captured on screen.
  R-002-02 pending/resolve behaviour itself is proven headless (BLOCK-3).
- **Q5** (two sensor rings legible, full own-layer + half other-layer): **partial** —
  visible in `transfer_mid.png` (own-layer ring is very large relative to the 4,000wu
  canvas, ~40% of the frame width at 800wu radius; the half-radius other-layer ring is
  clearly nested inside it and distinguishable). Legible, but the own-layer ring's sheer
  size is worth flagging — see "Under-defined points."
- **Q6** (magenta/black/clipped/overlapping text at 720p): **no** magenta; **HELD** on
  "black" strictly because `slow_mid.png` itself is solid black (the darkening artifact,
  not a content bug — see above); no clipped or overlapping HUD text in any of the 4
  renderable screenshots.

**HELD:** DIM-X, BLOCK-X (Xvfb), Q3 (dimming half), Q4 (waiting-unit half), Q6 (strictly
on the black frame) — all blocked on the same host-contention stall, not a content
question. Q2's "slow lags" half is HELD as a *visual* judgement only; the same fact is
proven numerically.

## Timings

- `timing_ms.tick_avg` (pure `ToySim.step()` cost, CPU-bound, host-load-independent):
  0.0ms (no ticks yet) → 0.0067ms/tick at tick 10 → 0.0059ms/tick at tick 30 →
  0.0047ms/tick at tick 80. Negligible; 20Hz sim easily keeps up.
- `_qa.fps_ms` (Godot's own per-process-frame CPU time, not wall clock): 339ms → 258ms →
  258ms → 239ms across the 4 frames that rendered. This is Godot's *own* accounting of the
  CPU time it was scheduled for, not wall-clock time between frames — under the load
  average above, wall-clock time per frame was far higher (each of the 4 frames still took
  several real seconds; the later, never-captured frames took minutes to never).
- No clean run reached its own `exit 0` today; wall-clock time to render 4 screenshots
  plus advance to the stall point: 3-18 minutes across 4 attempts, all on the same
  severely contended host.
