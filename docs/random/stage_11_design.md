# Stage 11 Design — Galaxy View, Chronicle Scroll, and Seamless Transition

> **Transient document.** This doc bridges brainstorming chats until all decisions are captured into the bible and the Stage 11 spec. Delete once the stage spec is written and all questions are [CAPTURED].
>
> **Bible references active during this effort:** `game_bible.md` (hub), `bible_world.md`, `bible_chronicle.md`, `bible_animation_strategy.md`, `bible_simulation.md`, `bible_monetization.md` (UI Aesthetic section only). Existing stage specs consulted: `stage_9_spec.md`, `stage_10_spec.md`.

---

## Handoff Note

**Session 1 (this session) — accomplished:**

Seven design questions surfaced and resolved. Six design decisions captured into the bible spoke files (`bible_chronicle.md` and `bible_world.md`). One engineering decision (Q1 keyframe data flow) captured here pending stage spec authoring. `game_bible.md` hub version bumped to v2.11 with a change summary on the Last Updated line.

**Open for next session:**

Write the Stage 11 spec itself (`docs/stage_specs/stage_11_spec.md`). The spec consumes all decisions captured here and from the bible, covers the six components (galaxy view real-world-state rendering, chronicle scroll panel, expanding layout, seamless transition choreography, territory visualization, military flash events), and defines checkpoints for CC implementation.

**No remaining open design questions for Stage 11.** All seven resolved. The stage is ready for spec authoring.

---

## Questions

### Q1 — Galaxy View Data Flow: Where Does World State Come From? [CAPTURED]

**Resolved:** Option C — Keyframe snapshots.

The sim sends an ordered list of keyframe snapshots (world state at cinematically significant moments during the time jump) plus the chronicle entries. Godot interpolates between keyframes to produce smooth animated galaxy view.

**Engineering decisions (go into stage spec, not bible):**

- Keyframe selection reuses the distiller's significance scoring — events scoring above a configurable threshold produce a keyframe.
- Ownership changes always produce a keyframe regardless of score (visually dramatic).
- Keyframe message includes: tick number, regions with ownership changes, military activity events (attack / conquest / revolt) with position data, connection changes.
- Keyframe count is a tuning value (too many = busy, too few = sparse).

**Classification:** Engineering decision (affects sim/renderer protocol shape, not player-facing mechanics). Lives in stage spec, not bible.

### Q2 — Chronicle Scroll Pacing: Who Drives the Timing? [CAPTURED]

**Resolved:** Option A — Galaxy drives, scroll follows.

Galaxy animation is the master timeline. Chronicle entries queued and begin printing when galaxy reaches their corresponding keyframe tick range. Entries have a minimum display duration to prevent rushing. Between entries, scroll holds last entry visible. If a keyframe has no corresponding chronicle entry, galaxy animates without scroll activity.

**Captured to:** `bible_chronicle.md` → "Chronicle Scroll — Visual Presentation" section.

### Q3 — Chronicle Scroll Layout: Fixed Split or Overlay? [CAPTURED]

**Resolved:** Option C — Expanding scroll.

Galaxy renders full-screen during pull-back and push-in transitions. During narration phase, scroll panel slides in from right, galaxy viewport resizes to ~60–65% width. When time jump ends, scroll panel slides back out before push-in begins. Slide animation duration is a tuning value. Camera framing adjusts when viewport resizes.

**Captured to:** `bible_chronicle.md` → "Chronicle Scroll — Visual Presentation" section.

### Q4 — Chronicle Entry Expansion: Does Click-to-Expand Pause the Flow? [CAPTURED]

**Resolved:** Option C — Pause everything; only fully-printed entries are expandable.

Three states: printing (animating, not clickable), printed (complete with blinking cursor, clickable), expanded (overlay showing full expanded form). Clicking a printed entry pauses galaxy animation and master clock. Dismissing expansion resumes exactly where paused. In-progress entries not clickable.

**Captured to:** `bible_chronicle.md` → "Chronicle Scroll — Visual Presentation" section.

### Q5 — The "Next Mission" Handoff: When Does the Push-In Start? [CAPTURED]

**Resolved:** Option B — Player-confirmed continuation + first-class exit action.

When last entry finishes printing, galaxy settles into slow ambient orbit, scroll panel stays visible. Footer shows two actions: primary **Proceed to [region name]** (triggers push-in) and secondary **Exit to Main Menu** (cleanly exits the run). Neither on a countdown — player continues or exits when ready. Symmetric exit offer at post-mission boundary before pull-back begins.

Chapter boundaries are first-class save-and-quit points, consistent with the Stage 8 snapshot cadence (every time jump + every mission start and end). Save serialization on exit lands in a later stage; Stage 11 owns the offer of clean exit at these boundaries.

**Captured to:** `bible_world.md` → "Seamless Transition — No Loading Screens" section.

### Q6 — Faction Territory Visualization in 3D [CAPTURED]

**Resolved:** Option D — Influence bubbles + derived border contour.

Each owned system emits a spherical colored influence bubble with additive blending and low opacity. Radius scales with system significance. Bubbles from same faction blend visually. Neutral systems emit no bubble. A derived border contour renders at the equipotential threshold where two factions' influence intensities meet — a bright neutral-colored line (brand-gold-adjacent) drawn in front of the bubbles. When a system changes hands, bubble color interpolates over ~1 second and contour recomputes.

**Engineering decisions (bubble-radius curve, contour threshold, bubble opacity, contour brightness, transition duration) are tuning values.** Implementation technique for contour extraction (marching cubes vs. post-process shader vs. SDF) is CC's engineering choice — the spec specifies the visual contract, not the method.

**Captured to:** `bible_world.md` → "Galaxy View — The Strategic Layer Between Missions" → "Faction territory" paragraph.

### Q7 — Military Activity Flashes: Sourced from What? [CAPTURED]

**Resolved:** Option A — Attack / conquest / revolt events only.

The sim's event log during a time jump contains many event types; only combat-specific events produce flashes: **attack events, conquest events, revolt events**. Flash position: between attacker's and defender's system nodes for attacks/conquests; at the revolting region's node for revolts.

**Architecture note:** The Python backend signals *what happened and where* via the keyframe message (Q1). Godot's particle system produces the actual visual effect — flashes, duration, intensity, color, choreography are all Godot's responsibility. Sim drives occurrence and position; renderer owns everything visual.

**Captured to:** `bible_world.md` → "Galaxy View — The Strategic Layer Between Missions" → "Military activity visualization" paragraph.

---

## Decisions Deferred to Stage Spec (Engineering / Tuning)

These are not bible content; they are engineering decisions and tuning values that belong in `stage_11_spec.md` when it's written:

**Engineering decisions (Claude can default with reasoning in the spec):**

- Keyframe message schema shape (exact field list, tick ordering, ownership-change encoding).
- Protocol integration with Stage 10's stdio pipe transport (keyframe messages ride the existing length-prefixed JSON framing as a new message type).
- UIDataBus extension — new methods or signals exposing time-jump keyframe streams and chronicle entry queue to the galaxy view scene.
- Galaxy scene architecture — whether Stage 11 adds a new scene consuming `galaxy_structure.tscn`, or extends the main menu's usage of that scene. The bible already specifies `galaxy_structure.tscn` is reusable at full opacity with interactive camera for the galaxy view, so this is mostly wiring.
- Border contour implementation technique.
- Camera choreography for pull-back and push-in phases (interpolation curves, duration, framing).
- Scroll-panel slide-in / slide-out animation (reuses animation strategy's sweep_line / divider primitives where possible).
- Exit-action behavior in the absence of a save system (Stage 11 just terminates the run; Stage 12 wires save-on-exit later).

**Tuning values (deferred to playtest, spec writes defaults with reasoning):**

- Keyframe significance threshold.
- Maximum keyframe count per time jump.
- Minimum entry display duration.
- Scroll panel slide-in / slide-out duration.
- Galaxy viewport resize target (60–65%).
- Bubble opacity, radius scaling curve, falloff.
- Contour brightness, threshold, line thickness.
- Flash duration, intensity curve, base color.
- Ambient orbit speed during post-narration hold.
- Scroll entry word-by-word print speed.

---

## Files Modified This Session

- `bible_chronicle.md` — expanded "Chronicle Scroll — Visual Presentation" section with master-timeline, expanding-scroll layout, and entry interaction states.
- `bible_world.md` — expanded "Faction territory" paragraph, expanded "Military activity visualization" paragraph, rewrote "Seamless Transition — No Loading Screens" section.
- `game_bible.md` — bumped to v2.11, updated Last Updated line with change summary.
