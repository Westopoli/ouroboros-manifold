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
position moves from y=538.9 to y=407.3 in the project's fixed 1920x1080 design space, a
12.2% shift of window height — well past the R-010-03 5% bar); the slow unit visibly lags
it (proven headless, in the `qa_state` data, and — subtly, at this camera distance — in
`slow_mid.png`). Each unit's ring is one of two colours and flips only on the tick its discrete
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

## The Xvfb visual batch: complete

The first pass through this mockup hit a real stall after the fourth or fifth
screenshot, initially misread as host contention. The actual cause, found and fixed on
`main` in this session: Godot instantiates the project's 19 autoloads even under
`--script` boot; in a git worktree the `SimBridge` autoload's Python sim dies at once (no
built `libouroboros.so`), `SimBridge` routes `SceneRouter` to the error screen, whose
0.3s fade to black is the progressive per-screenshot dimming earlier builders saw, and
whose scene swap frees the mockup mid-script — which is the stall the next `screenshot`
verb waited forever on. `qa_boot.gd` now frees every autoload before instantiating the
mockup (`b65afa8`); a separate, smaller fix disabled Xvfb's screensaver (`-s 0`,
`a98c47f`), which was a reasonable suspect at the time but not the actual cause. With
both fixes on `main`, two full clean runs, all six plant runs, and the 1920x1080 review
batch each finish in 6-10 seconds, `exit 0`, zero errors, zero stalls.

Full check table, every Xvfb oracle (clean and planted), and the DET-1 pixel/hash
comparison: `scenes/mockups/layers/qa/checklist.md`. Headline: `clean1` vs `clean2`
hash-identical at every one of 9 checkpoints; every screenshot pixel-diffs at 0.000000
except `blocked_cleared.png` at 0.000041 (both under the 0.005 bar). All six plants show
every oracle on the wrong side of its threshold, confirming each fault site is live and
each check would actually catch it.

One inconsistency in the original `qa/smoke.json` was fixed this session: its
blocked-transfer demonstration ordered the unit to layer 1 (`qa_transfer 1 1`), and
`toy_sim.gd`'s blocked mask only ever applies to a transfer whose target is layer 2, so
nothing was ever actually blocked. The script now parks the unit on the blocked patch's
centre cell and orders it to layer 2 (`qa_transfer 1 2`) — genuinely blocked, 30 ticks
pending, then moved clear and completing. Screenshot names unchanged.

## What the report answers

1. **Does the two-layer idea read at this camera pitch and height spacing?** Yes: the
   layer-2 unit is unambiguously higher on screen (12.2% of the project's 1080-height
   design resolution, `transfer_after.png`), the rise reads as continuous motion, not a
   snap (`transfer_mid.png` sits strictly between before/after), and the focus
   strip/dimming pair reads cleanly (`focus1.png` vs `focus2.png`, 0.21 pixel-diff). See
   the Q1/Q3 answers in `qa/checklist.md`.
2. **250wu vs 2,000wu layer height:** not tried this pass — out of this session's scope
   (fixing the smoke script and completing the QA batch); still open below with the same
   three candidates the brief named.
3. **Does dimming or the translucent upper plane hurt reading the lower layer?** No —
   `focus1.png`/`focus2.png` show the non-focused layer legibly dimmed (alpha 0.4) without
   losing the ability to see where its units/ground are; the translucent layer-2 plane
   (alpha 0.25) keeps layer 1 visible underneath it in every screenshot that frames both.
4. **Frame time under llvmpipe at 720p:** Godot's own per-frame CPU accounting
   (`_qa.fps_ms`) ranges 188-365ms across the 9 captured frames (heaviest at boot, settling
   to 188-222ms once warmed up) — not alarming. `ToySim.step()` itself (the actual sim
   cost, independent of rendering) is 0.0039-0.0043ms/tick — trivial, 20Hz is nowhere near
   a bottleneck. Wall time for the full clean smoke run (8 screenshots, 9 state dumps): 6
   seconds.
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
   - **Sensor ring size/legibility (Q5).** At 800wu on a 4,000wu canvas the own-layer
     sensor ring is close to 40% of the frame width — legible in every shot that shows it
     but large enough to dominate the frame. Candidates: scale the ring's *visual* radius
     down from the true sensor radius (readability over literal accuracy) vs. leave it
     literal and rely on a taller camera height by default.
   - **The blocked demonstration's parked position occludes the unit (Q4).** Fixed this
     session so the block is genuine (see above), but parking the unit at the blocked
     patch's exact centre also parks it directly under the tall obstacle box, which fully
     occludes it in `blocked_attempt.png` from the script's fixed camera angle — a viewer
     can only tell it's waiting from the HUD list, not the 3D view. Candidates: (a) park
     it at a position inside the 350wu blocked radius but outside the 150wu obstacle
     footprint (e.g. `(2000, 2300)`) so it stays visible; (b) shrink the obstacle's
     footprint relative to the blocked radius so no blocked cell is ever fully hidden
     behind it.
   - **A camera-angle-dependent transparency artifact (not fixed).** In
     `transfer_before.png`, unit 1 does not render at the `qa_camera 2500 2000 2000`
     angle used throughout the script, though its own sensor ring (correctly centred on
     it) does — confirmed by a throwaway diagnostic (camera repositioned directly over the
     unit shows it fully present, selected, correctly coloured) that this is not a
     spawn/visibility bug. At this one camera/position combination, unit 1's view ray
     passes through the blocked patch's translucent plane (both the patch and the unit
     body use `TRANSPARENCY_ALPHA`) before reaching the unit, and the transparent-pass
     sort appears to composite the patch over the unit instead of blending the two. It
     recurs nowhere else in the batch and doesn't affect any Q1-Q6 answer
     (`transfer_mid.png`/`transfer_after.png` show the same unit cleanly), so left as a
     finding rather than a fix. Candidates: stop giving opaque-alpha unit bodies
     `TRANSPARENCY_ALPHA` (only enable it when actually dimmed); or don't let a unit's
     default framing ray cross the blocked patch.
6. **Anything arguing the two-layer/blocked-mask idea doesn't hold?** No — every headless
   check passed on the first real implementation attempt (build order: `toy_sim`
   transfers+blocking, then vision, then the view, then camera/HUD/input — see `git log`),
   and the emergent same-layer-vision-on-arrival behaviour (enemy 103 becoming visible
   only once unit 1 reaches layer 2) fell out of the rules for free, unplanned, which is a
   good sign for the rules being coherent together.

## Questions for Westley

1. Is 600wu the right layer-height candidate, or does one of 250/2,000wu read better —
   worth a quick A/B (not run this pass, out of scope for the QA-batch fix)?
2. Camera pitch: keep the fixed 60° this mockup uses (height reads clearly, closer to the
   game's likely tactical camera) or match R-103-03's stated top-down interim?
3. Is the own-layer sensor ring, drawn at the unit's literal true-scale sensor radius, too
   dominant on screen at this canvas size — should sensor rings be visually de-emphasised
   independent of the real detection radius?
4. The blocked demonstration currently parks the unit exactly under the obstacle, which
   hides it behind the obstacle's own opaque geometry (see "The blocked demonstration's
   parked position occludes the unit" above) — worth a follow-up shot at a blocked-but-
   visible position, or is the HUD-only "still L1" readout enough?

## Next step

All 8 pass-1 screenshots (1920x1080, the full review batch: before, mid, after, slow mid,
focus 1, focus 2, blocked attempt, blocked cleared) are committed under `pass1/`. The
mockup is done and green (`VERIFY OK`, all 6 plants `LIVE`, both clean Xvfb runs and all
plant runs `exit 0` with zero errors) — it awaits Westley's look.

## Fresh-eyes review (2026-09-22, Sonnet reviewer, screenshots only)

Verdict: quick fix and rerun before Westley's look. Two required proofs are broken by known one-line causes: `transfer_before.png` shows only the selected unit's ring because every unit body is given alpha transparency at spawn and sorts behind the translucent blocked patch from that camera ray; `blocked_attempt.png` parks the waiting unit dead centre under the obstacle, so nothing but the HUD proves it is waiting. Nits: `focus1.png` is byte-identical to `slow_mid.png` because focus already defaulted to 1; the obstacle prism reads as three colour bands under the dimming and could pass for a third layer; the other-layer sensor ring looks nearer 35 percent of the own-layer ring than the rule's 50 percent, to be measured at a fixed camera before calling it wrong. Height, dimming, rings and the blocked mechanic are proven in the numbers.
