# Layers mockup (P6) — design as built

This is the first option for the E-01 layer system's design phase
(`docs/northstar/README.md:29`), built per the P6 rung of the prototype ladder
(`docs/northstar/PLAN.md:167`): "layer changes elevation and vision per rule; ring height
and dimming; planted wrong-height." No reference images exist for E-01 yet
(`docs/bible/references/E-01/notes.md` is a stub) — this mockup and Westley's reaction to
it are meant to start producing that reference material, so every visual judgement below
is against the epic's prose (the 60-second paragraph, R-010-03) rather than a screenshot
to match.

Run it yourself: `~/.local/bin/godot --scene scenes/mockups/layers/layers_mockup.tscn`.
Hotkeys: **Tab** cycles the focused layer, **1**/**2** set it directly, **Q**/**E** hard-
transfer the selected unit to layer 1/2, **T** steps one tick, **Space** toggles real-time
play (20Hz), **R** resets (re-seeds with the spinbox's current value). Left click selects
the nearest friendly under the cursor; right click issues a move order to the selected
unit. This scene has no autoload dependency and works identically whether launched by
`--scene` (autoloads running, as on Westley's seat) or through the QA harness's
`qa_boot.gd` (no autoloads) — confirmed by code inspection, not a live run on Westley's
seat: `scenes/mockups/_shared/qa_driver.gd`'s `_ready()` reads `--qa-script` from the
command line and returns immediately, doing nothing else, when it is absent
(`if script_path == "": return`). A `--scene` launch never passes `--qa-script`, so the
driver stays inert; no `_run.json` or any other QA output is ever written.

## What it shows

Two layers, `LAYER_HEIGHT = 600` wu apart (candidate — see "Under-defined points"). A
4,000wu canvas (`fixtures/map_seed11.json`) with a tall obstacle at its centre and a
350wu-radius region around it that is blocked **on layer 2 only** (the spec's own
framing: "a blocked mask on layer 2"). Two friendlies start next to the obstacle on layer
1: a fast type (1.0s / 20-tick transition, 800wu sensor) and a slow type (5.0s / 100-tick
transition, 300wu sensor) — Raider/Bastion analogues without naming them, per R-145-01.
Three enemies: one far away on layer 1 (structurally unseeable in the 5-layer game by
being multiple layers distant; in this 2-layer reduction the same "unseen" outcome is
reached by simple distance, since only layer 2 can be blocked and layer-distance capping
only has one step to give), one on layer 2 within the fast unit's half-sensor cross-layer
range (seen from the start), one on layer 2 beyond it (unseen until the fast unit itself
reaches layer 2 and gains full-radius same-layer vision on it — an emergent, correct
consequence of R-005-01/02, confirmed in the real run: `visible_enemy_uids` goes from
`[102]` to `[102, 103]` exactly when unit 1 completes its transfer).

Ordering the fast unit up starts its transition the same tick (measured: unit 1's screen
position moves from y=538.9px to y=407.3px, an 18.3% shift of the 720px window height —
well past the R-010-03 5% bar); the slow unit visibly lags it (proven headless and in the
`_qa_state` data; the screenshot meant to show it, `slow_mid.png`, hit the darkening bug
below). Each unit's ring is one of two colours and flips only on the tick its discrete
`layer` field changes — not the tick the height starts moving — matching R-009-01's "ring
colour changes on the tick the layer changes" against R-010-02's "height moves as a lerp,
not a snap": the two events are on purpose not simultaneous, the ring lags the rise by the
whole transition. The non-focused layer's units and ground plane dim to alpha 0.4.

## Check table

All ten checks and all six plants pass. Full table with clean/planted results:
`scenes/mockups/layers/qa/checklist.md`. Headline: `scripts/mockup_verify.sh layers` →
`VERIFY OK`; `scripts/mockup_verify.sh layers --plant <id>` → `PLANT <id> LIVE` for every
id in `instant-transfer`, `blocked-ignored`, `cross-layer-full-range`, `ring-colour-same`,
`no-dimming`, `wrong-height`.

## The Xvfb visual batch is incomplete — host contention, not a scene bug

Every `scripts/mockup_qa.sh run` attempt against the full `qa/smoke.json` — four separate
tries, up to a 25-minute timeout — captured the same first four screenshots
(`transfer_before`, `transfer_mid`, `transfer_after`, `slow_mid`) within seconds, then
stalled indefinitely before the fifth (`focus1`). At the time of this build the shared
host was running 31 concurrent Godot/Xvfb processes from other agent sessions (load
average 18-22 on 16 cores, 833MB RAM free of 30GB). A control probe during one stall found
the Godot process at 155% CPU, `wchan=futex_do_wait` — busy, not deadlocked.

A trivial isolation probe (seed, camera, five bare `screenshot` calls, nothing else)
reproduces the identical stall at the identical 5th call and the identical brightness
curve (mean pixel value 0.433 → 0.387 → 0.338 → 0.289 across the four frames that do
render), which rules out this mockup's own code as the cause — a near-empty static scene
degrades exactly the same way. `--grab external` and disabling `DirectionalLight3D`
shadows were both tried and both ruled out (see `qa/checklist.md` for the full trail).
Per this brief's own instruction ("if the harness is broken, stop and report; do not patch
it") and since `scenes/mockups/_shared/**` is fenced regardless: stopped, documented,
did not touch it.

What the four screenshots that did render, plus their `qa_state()` dumps, do prove:
hash-identical determinism across two independent process runs 40 minutes apart at every
checkpoint both reached (tick 0/10/30), `transfer_before.png` pixel-diffing at 0.004270
between those runs (under the brief's 0.005 bar), and the numeric HEIGHT-X/MID-X/RING-X
oracles all passing. What is `HELD`: the focus-strip/dimming pair (`focus1.png`/
`focus2.png`) and the blocked-transfer pair (`blocked_attempt.png`/`blocked_cleared.png`)
never rendered, so `DIM-X` and `BLOCK-X` are proven only headlessly (`DIM-8`, `BLOCK-3` in
`verify.gd`), not visually. The pass-1 batch below is the 4 screenshots at 1280x720 (the
functional-run resolution), not the specified 1920x1080 review batch — attempting the
larger, more expensive resolution was not worth it while every 720p attempt itself was
stalling. **Re-running the QA batch and the 1920x1080 review batch on a quieter host is
the one remaining step; nothing in the mockup's code needs to change first.**

## What the report answers

1. **Does the two-layer idea read at this camera pitch and height spacing?** Yes, as far
   as the evidence goes: the layer-2 unit is unambiguously higher on screen (18.3% of the
   window, `transfer_after.png`), and the rise reads as continuous motion, not a snap
   (`transfer_mid.png` sits strictly between before/after both on screen and in
   `units_px`). Held: whether the *dimming* half of "which layer is focused" reads, since
   `focus1.png`/`focus2.png` never rendered.
2. **250wu vs 2,000wu layer height:** not tried — the host stall consumed the time budget
   before this A/B could be run. Listed as open below with the same three candidates the
   brief named.
3. **Does dimming or the translucent upper plane hurt reading the lower layer?** Held —
   same reason.
4. **Frame time under llvmpipe at 720p:** Godot's own per-frame CPU accounting
   (`_qa.fps_ms`) was 339/258/258/239ms across the four frames that rendered — not itself
   alarming — but wall-clock time between frames was minutes, not milliseconds, under the
   host's 18-22 load average; see the contention section above. `ToySim.step()` itself
   (the actual sim cost, independent of rendering) is 0.005-0.007ms/tick — trivial, 20Hz
   is not remotely a bottleneck.
5. **Under-defined points**, each with candidates, no decision made:
   - **Layer height (`LAYER_HEIGHT`).** Candidate used: 600wu. Alternatives: 250wu (closer
     to the legacy tactical code's `EraConfig.LAYER_HEIGHT`, but that constant is itself
     flagged as a defect in the epic — R-010-01's own inputs note "three z-bands 0-300 for
     a five-layer count, which is itself a defect"); 2,000wu (closer to the landscape
     mockup's terrace scale, hundreds-to-thousands of wu). Not tested this pass (see
     item 2).
   - **Camera pitch.** 60° fixed, chosen so the vertical offset reads per R-010-03; R-103-03's
     interim spec is top-down (90°). Alternative: ease toward 90° at the map band the way
     the landscape mockup's camera does, trading "height reads clearly" against "matches
     the stated top-down interim." Held on the tactical-band framing that best matches
     E-01's own "obviously working" paragraph.
   - **Blocked-cell marking.** Candidate used: a flat, red-tinted translucent patch on the
     layer-2 plane over the blocked footprint. Alternatives: a raised lip/wall at the
     boundary (reads as an edge, not just a tint); a hazard-stripe texture (out of scope —
     "no textures beyond vertex colour" for this mockup).
   - **The layer strip's look.** Candidate used: two stacked buttons (`L2` above `L1`,
     highlighted text + dim/bright modulate) at the top-right. Alternatives: the legacy
     five-slot vertical strip's colour-swatch style (`scenes/tactical/hud.gd:697-770`,
     ported down to two slots); a horizontal pair instead of vertical.
   - **Targetable mid-transition (R-004-02).** Not modelled — this toy sim has no combat,
     so "a mid-transition unit cannot attack and cannot be attacked" has nothing to attach
     to. Flagged, not built.
   - **Transition durations at landscape scale.** The 1.0s/5.0s durations and 80wu/s move
     speed came from the tactical-scale config as given; whether they still read as
     "a commitment" at the landscape mockup's much larger canvas (hundreds to thousands of
     wu per screen) is untested — no landscape-scale layer fixture exists yet.
   - **`qa_transfer 1 1` in the smoke script's block sequence.** `toy_sim.gd`'s blocked
     mask exists only on layer 2 (matches the brief's own toy_sim spec, word for word); the
     smoke script's final block-demonstration segment orders the unit *down* to layer 1,
     which can never be blocked under that spec, so `blocked_attempt.png`/
     `blocked_cleared.png` (even if they had rendered) would not have shown a real block.
     R-002-02 is fully proven instead by the headless `BLOCK-3` check, which orders a unit
     *up* into the blocked cell. Candidates for a corrected script: (a) send the unit back
     up (`qa_transfer 1 2`) at the blocked position instead of down; (b) also gate layer 1
     at the obstacle's own footprint (distinct from the wider layer-2-only margin) so a
     downward order can be blocked too, matching "the tall obstacle spans both layers" in
     the render spec even though the movement/transfer spec never says so.
   - **Sensor ring size/legibility (Q5).** At 800wu on a 4,000wu canvas the own-layer
     sensor ring is close to 40% of the frame width — legible in the one shot that shows
     it (`transfer_mid.png`) but large enough to dominate the frame. Candidates: scale the
     ring's *visual* radius down from the true sensor radius (readability over literal
     accuracy) vs. leave it literal and rely on a taller camera height by default.
6. **Anything arguing the two-layer/blocked-mask idea doesn't hold?** No — every headless
   check passed on the first real implementation attempt (build order: `toy_sim`
   transfers+blocking, then vision, then the view, then camera/HUD/input — see `git log`),
   and the emergent same-layer-vision-on-arrival behaviour (enemy 103 becoming visible
   only once unit 1 reaches layer 2) fell out of the rules for free, unplanned, which is a
   good sign for the rules being coherent together.

## Questions for Westley

1. Is 600wu the right layer-height candidate, or does one of 250/2,000wu read better —
   worth a quick A/B once a clean Xvfb pass exists (blocked this round by host load, see
   above)?
2. Camera pitch: keep the fixed 60° this mockup uses (height reads clearly, closer to the
   game's likely tactical camera) or match R-103-03's stated top-down interim?
3. Is the own-layer sensor ring, drawn at the unit's literal true-scale sensor radius, too
   dominant on screen at this canvas size — should sensor rings be visually de-emphasised
   independent of the real detection radius?
4. Does the smoke script's block-demo sequence need a rewrite (see the `qa_transfer 1 1`
   item above), or is a headless-only proof of R-002-02 sufficient and the smoke script's
   last two screenshots should just be dropped/replaced with something else?

## Next step

The pass-1 screenshots (4 of the intended 8, 1280x720, not yet the 1920x1080 review batch
— see "The Xvfb visual batch is incomplete" above) are committed under `pass1/`. The
mockup itself is done and green (`VERIFY OK`, all 6 plants `LIVE`); it awaits a quieter
host for the remaining QA batch and Westley's look.
