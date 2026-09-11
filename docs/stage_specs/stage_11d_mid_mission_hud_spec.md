# Stage 11d — Mid-Mission HUD: Objectives, Markers, Command Indicators, Selection, Minimap

## Goal

Close the in-mission HUD gaps that cumulatively account for "the player has no idea what to do or where things are once a mission starts." The pre-mission briefing is already wired (`launch_todo.md` 2026-04-24); the gaps are all on the mid-mission tactical surface. Five sub-goals, all small individually but collectively forming the "you are now playing a real RTS" experience:

1. **Mission objectives rendering — fidelity pass.** Objectives flow sim → bridge → HUD → text labels today (data plumbing works), but they render as raw `id  progress%  status` strings — no descriptions, no progress bars, no primary-vs-secondary distinction. This spec lifts the rendering to MVP fidelity per Fork F3: human-readable description, visual progress bar, primary/secondary distinction.

2. **Mission markers on the world map and minimap.** Objective locations (zone centers, extraction points, target positions) live in `objectives.py` but `snapshot_serializer.py:349–358` strips them before sending to Godot. This spec adds location data to the wire, then renders waypoint markers on the main view (in-world chrome) and on the minimap.

3. **Command location indicators.** When the player issues a move or attack-move command, no visual marker appears at the target. This spec adds in-world indicators (ground decal / waypoint flag / ping — pick one at implementation time per Open Question OQ1).

4. **Enemy unit clickability with fog gating.** Currently enemies are not clickable; `_is_selectable()` blocks them via `selection_eligible == false`. Per Fork F4, this spec lifts the friendly-only gate while leaving Stage 11c's fog gate underneath. Net behavior: visible enemies clickable for inspection (HP, type readout); invisible enemies remain unselectable.

5. **Minimap viewport box.** Per the StarCraft-2-style standard, draw a rectangle on the minimap showing the camera's current viewport bounds. Closes the "where am I looking?" question without requiring the player to scan the main view.

These ship together because they all live in `hud.gd`, all share the same UIDataBus / `TacticalBridge` consumer pattern, and the markers + viewport box + clickability are all interactions with the same minimap and selection surfaces.

**Not in scope:**
- Objective UI polish beyond MVP — band-transition highlights, animated progress, success-condition spectrum visualization (Fork F3 explicitly defers these).
- Mission objective *generation* changes — `objectives.py` and `mission_generator.py:500–511` are correct; this spec only changes serialization (adding location data) and rendering.
- Layer visuals, fog of war rendering — `stage_11c_layer_visuals_and_fog_spec.md`. **Note:** this spec depends on 11c's visibility predicate for both enemy clickability (sub-goal 4) and minimap fog filtering (sub-goal 2's minimap rendering). Order: 11c lands first, 11d consumes.
- Map variety — `stage_11b_map_variety_spec.md`. Independent; can land in parallel.
- The pre-mission map preview UI — separate future spec.
- Hotkey auto-assignment, shift-click-add-to-selection, double-click-select-all-of-type, command queuing — all on `launch_todo.md` but not folded into this plan (they're independent UX concerns, not gap-fixes for the broken core experience).
- In-game tutorial, chronicle skip controls — `launch_todo.md`, separate.

**Architecture.** Two small contract additions on the simulation side (objective location data on the wire, command target acknowledgement event), the rest Godot-side. No new tick-delta shapes — the additions extend existing snapshot fields. `architecture.md` updated for the contract changes per CLAUDE.md ("Tick delta shape is documented first" — applied here to the snapshot extension).

## Bible References

- **`docs/bible_history/bible_2_00_missions.md`** — mission objective structure (primary objective, success-condition spectrum, outcome bands). Read fully; this spec is the rendering pass for what that spoke specifies.
- **`docs/bible_history/bible_2_00_combat.md`** §"Mid-Mission HUD Layout" — the HUD's persistent info column with mission objectives list and progress indicators; in-world chrome layered onto the world view (pings, decals, waypoint flags); minimap contents (friendly bright, visible enemies dim, terrain contours, **objective markers**, reinforcement-structure icons).
- **`docs/bible_history/bible_2_00_combat.md`** §"Information Warfare" / fog (lines 215–234) — visibility model that gates enemy selection; consumed via Stage 11c's predicate.
- **`game_bible.md` (hub)** §"Stage 8" line 534 — three-tier layer system mention; only relevant here insofar as the HUD readout from Stage 11c shares HUD real estate with this spec's panels.
- **`docs/bible_history/bible_2_00_combat.md`** line 313 — sim 20 ticks/sec, Godot 60 fps target = 16.7 ms frame budget. Performance framing.

Do NOT read `docs/bible_history/bible_2_00_world.md`, `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_antagonist.md`, `docs/bible_history/bible_2_00_ai_pipeline.md`, or `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) — not relevant.

## Cross-Stage References

- **Stage 5.5 (mission generation)** — produces `ObjectiveSpec` with location-bearing params (`zone_x`, `zone_y`, `target_uids`, `extraction_x`, `extraction_y`). Unchanged. This spec just stops dropping those fields at serialization.
- **Stage 7 / 7.5 (tactical engine + behavior scripts)** — owns `objectives.py` and the tick-by-tick objective progress update. Unchanged.
- **Stage 8 (Godot bridge + HUD + persistence)** — built the HUD root, the minimap (`hud.gd:528–558`), the objective panel (`hud.gd:223–257`), the selection-eligible flag in `_is_selectable()`. This spec extends what Stage 8 ships.
- **Stage 9 (UI Shell)** — established the broader UI animation language (`animation_strategy.md`). The new HUD elements in this spec follow that language; the spec doesn't redefine it.
- **Stage 11b** — independent. No interaction.
- **Stage 11c** — **dependency**. Sub-goals 2 (minimap), 4 (enemy click), and 5 (viewport box) all consume 11c's `Visibility.is_unit_visible_to_player()` predicate. **Do not start this spec's checkpoints until 11c Checkpoint C lands** (the predicate exists). If implementation begins before 11c, **STOP and escalate**.
- **Stage 12 / 12.5** — selection circle recolor, HUD animation refinement. The new HUD panels in this spec follow whatever style 12.5 established. If conflict, escalate.

## Design Decisions

### D1 — Objective rendering MVP fidelity (Fork F3)

**Decision:** Each objective renders with three elements:
1. **Human-readable description** — derived from objective `type` + `params` via a small lookup. E.g., type `"eliminate_force"` with `target_uids` → "Destroy enemy force." Type `"hold_zone"` with `zone_x/y` → "Hold the central plateau" (using region-flavored names if available, generic otherwise). Lookup table lives client-side in `hud.gd` or a sibling resource — content authored, not generated.
2. **Visual progress bar** — a horizontal bar under the description, fill width = `objective.progress` (0.0–1.0), color = primary objective accent vs secondary objective accent.
3. **Primary/secondary distinction** — primary objectives render larger / bolder / on top of the panel; secondary objectives smaller / under primary, in a muted accent. The `is_primary` field already exists on `ObjectiveSpec`; this is a rendering distinction only.

**Rationale:** Fork F3 = MVP. The bible's full objective UX (band-transition highlights, animated progress, success-condition spectrum visualization) is deferred. The current text labels are the bug; description + bar + primary distinction is the minimum that makes objectives readable at a glance.

**Out:** animated progress (jumps to new value, no tween), band visualization, completion celebrations, audio cues, objective expansion on click. All can be added later as a polish pass.

### D2 — Objective location serialization: extend the snapshot, not the delta

**Decision:** Add an optional `location` field to the per-objective snapshot entry in `snapshot_serializer.py`. Shape:
```python
{
  "id": "...",
  "type": "...",
  "progress": 0.42,
  "status": "in_progress",
  "location": {"x": 1234, "y": 567, "layer": 2}  # OPTIONAL
}
```
Location is computed from the objective's params at serialization time:
- `hold_zone` / `clear_zone` → `(zone_x, zone_y, layer)`.
- `extract_unit` → `(extraction_x, extraction_y, layer)`.
- `eliminate_force` → centroid of `target_uids` positions (computed once at snapshot time; if all targets are dead, omit `location`).
- Other objective types → omit `location` if no obvious geometric center exists. Renderer must tolerate missing location.

**Why on the snapshot, not the delta:** objective locations rarely change mid-mission (zones are static; only `eliminate_force` centroids drift, slowly). Sending location on every snapshot (every few seconds) is cheap; sending in deltas would require change tracking we don't need. Snapshot-only matches the existing pattern.

**Why optional:** some objective types have no location ("survive 60 seconds"). Renderer must check presence, not assume it.

### D3 — Mission marker visual: in-world ground beacon + minimap dot

**Decision:**
- **In-world (main view):** a vertical light beam / ground decal at the objective location, colored by primary (vivid accent) vs secondary (muted), with a label floating at the unit's eye level showing the objective short-name. Beam is always visible (not occluded by terrain) per RTS convention.
- **Minimap:** a small icon at the objective location, same color scheme. Icon shape distinguishes objective types (square = hold/clear zone, triangle = extraction, diamond = eliminate-force-centroid). Always visible on minimap regardless of fog (objectives are intel the player has from the briefing, not perceived through sensors).

**Rationale:** This matches `docs/bible_history/bible_2_00_combat.md` §"Mid-Mission HUD Layout" prose — in-world chrome plus minimap markers — and resolves the bible's ambiguity between "ping" and "decal" by saying "both, in different surfaces." The vertical beam is the dominant RTS convention (StarCraft, Company of Heroes); the minimap icon is the at-a-glance reference.

**Performance:** beams are MeshInstance3D with a simple emission material. One per active objective with a location, typically 1–3 per mission. Negligible cost.

### D4 — Command location indicator: ground decal at target with brief animation

**Decision:** When the player issues a move or attack-move command, render a temporary ground decal at the target position. Decal:
- Shape: a circle (move) or crosshair (attack-move), colored by command type.
- Lifetime: ~1.0–1.5 seconds, then fades out.
- Stacked: if the player issues multiple commands in quick succession, each gets its own decal (no replacement).

**Rationale:** Matches the launch_todo description ("ping, ground decal, or waypoint flag — pick one"). Ground decal is the cheapest and reads cleanly at RTS camera distance. Animation is a fade-out; no bouncing or spinning.

**Open question OQ2:** does the existing `tactical_engine.py` emit a "command acknowledged" event Godot can subscribe to, or does the renderer need to render the indicator at click time (before sim acknowledgment)? Click-time is simpler but can mislead the player if the command is rejected (e.g., target on impassable terrain). Implementation prefers the engine event if it exists; otherwise click-time with a "fade red" treatment if the engine subsequently rejects. Resolve at start of Checkpoint E; if neither path is clean, escalate.

### D5 — Enemy clickability: lift the friendly gate, keep the fog gate (Fork F4)

**Decision:** Modify `_is_selectable()` so it no longer requires `selection_eligible == true` for enemy units; instead, all units (friendly, enemy, neutral) become selectable subject to the existing visibility predicate from Stage 11c. Net effect: visible enemies clickable for inspection, invisible enemies still gated.

**Rationale:** Resolves Fork F4. Cleaner than special-casing enemy click in input_router because the visibility predicate is already authoritative.

**Inspection UX:** clicking an enemy populates the existing selection-info panel with the enemy's HP, type, faction, and any other safe-to-show fields (e.g., layer, current order if exposed by the sim). Multi-select with mixed friendly/enemy: existing convention of "selection prefers friendlies for command issuance" — enemy units in selection are display-only. If existing selection model conflicts, escalate; do not invent a new one.

**Out:** detailed enemy intel (squad composition breakdowns, behavior-script state, predicted next action). The MVP is what Stage 8's selection-info panel can already render for friendlies, applied to enemies.

### D6 — Minimap viewport box: rectangle from camera frustum projection

**Decision:** On every frame, project the camera's view frustum onto the minimap-equivalent ground plane and draw the resulting quadrilateral as a thin outlined rectangle on the minimap canvas. Color: a soft white/gray, semi-transparent, no fill. Update is per-frame because the camera moves continuously.

**Rationale:** Matches StarCraft 2's behavior, which is the bible's implicit reference (`launch_todo.md`'s "(like StarCraft 2)"). Per-frame update is necessary for smooth tracking.

**Performance:** four `Vector3 → Vector2` projections per frame plus a `draw_polyline` call. Negligible.

**Edge cases:** at extreme camera angles or zoom levels the projected quad may extend off-minimap. Clip to minimap bounds. If clip math is non-obvious, **escalate at implementation time** rather than guess.

### D7 — Performance framing

All HUD work targets the 16.7 ms Godot frame budget per `docs/bible_history/bible_2_00_combat.md:313`. Per-frame surfaces touched:
- Objective panel: redraws only on objective state change (rare). Effectively zero per-frame cost.
- Mission marker beams: 1–3 MeshInstance3D draws per frame. Trivial.
- Command indicators: one decal per active command, ~1.5 second lifetime, typically 0–3 active. Trivial.
- Minimap: redraws once per frame (already does). Adds objective icons, viewport box, fog-gated enemy filter — each O(small). The minimap dirty-redraw is already the pattern; this spec stays inside it.
- Selection: extra check per click, not per frame. Zero per-frame cost.

**Expected frame-time impact: negligible (< 0.5 ms).** Verified at Checkpoint H.

## Open Questions

- **OQ1 — Command indicator visual choice.** D4 specifies "ground decal." If the renderer's existing decal pipeline is awkward (e.g., decals don't compose with the existing terrain shader), fall back to a small flat mesh quad with a transparent texture. If neither is clean, escalate.
- **OQ2 — Command acknowledgment event.** Per D4, prefer the sim's command-ack event if it exists. Verify at start of Checkpoint E. If absent, choose between click-time render with a rejection animation, or sim-side change to emit the event. Sim-side change is **out of scope** of this spec — escalate to Westley with a recommendation rather than implementing.
- **OQ3 — Objective short-name source.** D3's in-world beam carries a label. The label text comes from the objective's human-readable description (D1). If the description is too long for an in-world label, a separate `short_name` may be useful. Decide at implementation; if a short_name field is needed, it's an additive change to D2's snapshot extension and should be flagged before implementing.

## What to Build

### Files to modify (simulation side)

**`simulation/snapshot_serializer.py`** — extend `_objective_entry()` (~lines 349–358) to include the optional `location` field per D2.
- Add a small helper that maps objective type → location lookup, using the objective's params and (for `eliminate_force`) the unit position registry.
- Maintain backward compatibility: `location` field is optional; old code that doesn't send it stays valid (relevant for save loads of pre-spec missions).
- Add a `# See also: scenes/tactical/hud.gd — consumes objective.location for marker rendering` comment.

**`docs/architecture.md`** — document the snapshot extension.
- Add a short subsection under the objective serialization area describing the `location` field, when it's emitted, and what the renderer does with it.
- Per CLAUDE.md, this lands **before** code changes if the change is to tick delta shape. Snapshot extensions are softer (additive), but the same discipline is healthy. **Author the doc update at the start of Checkpoint C.**

### Files to modify (Godot side)

**`autoload/tactical_bridge.gd`** — surface objective locations.
- Update the objective parser (lines 222, 321–324 per gap report) to read the optional `location` field and store it on the Bridge's objective entry.
- Existing field shape extends naturally; no new top-level state.

**`scenes/tactical/hud.gd`** — multiple changes:
- **Objective panel rebuild (~lines 223–257):** replace the raw text label with a description + progress bar widget. Author the type→description lookup as a constant dictionary at the top of the file or in a sibling resource.
- **Primary/secondary distinction:** sort objectives so primary first, render with distinct styling (font size, accent color).
- **Minimap (`_Minimap` class, ~lines 528–558):** add objective icon drawing per D3; viewport box drawing per D6.
- **HUD style consistency:** match the panel-construction pattern used at `:392–393` (objectives) and `:447–449` (minimap). Don't invent new HUD chrome conventions.

**`scenes/tactical/input_router.gd`** — modify `_is_selectable()` (~lines 262–263).
- Remove the `selection_eligible` requirement for enemy units (or invert: require either `is_friendly` OR `Visibility.is_unit_visible_to_player(uid)`). Exact form depends on what the existing `selection_eligible` flag means in mission setup; verify before changing.
- Friendly units must remain unconditionally selectable (their `selection_eligible` flag was set by the engine for a reason — confirm that's only the friendly/enemy distinction and not some other gate; if it's another gate, escalate before changing).

**`scenes/tactical/tactical.gd`** (or wherever the main tactical scene root lives) — host the new in-world chrome.
- Add a `MissionMarkers` node (Node3D parent for objective beam meshes).
- Add a `CommandIndicators` node (Node3D parent for transient command decals).
- Wire to `TacticalBridge` signals: subscribe to objective updates, redraw markers on change. Subscribe to command-issuance events (or wire from `input_router.gd` directly), spawn decals.

### Files to create

**`scenes/tactical/mission_marker.tscn` + `mission_marker.gd`** — the in-world objective beam.
- Single MeshInstance3D with a vertical beam shape and an emission material.
- Script handles label rendering (Label3D or sprite-billboarded text), color application based on `is_primary`, position update if location changes.
- Lightweight; one instance per active objective with a location.

**`scenes/tactical/command_indicator.tscn` + `command_indicator.gd`** — transient ground decal for commands.
- Quad mesh with a circle/crosshair texture per D4.
- Script handles fade-out tween and self-deletion after lifetime expires.
- Color and shape per command type.

**`scenes/dev/hud_test.tscn` + `hud_test.gd`** — checkpoint dev scene.
- Spawns a fixed mission with 2 objectives (1 primary `hold_zone`, 1 secondary `eliminate_force`).
- Used for Checkpoints A, C, D, F, G — all the visual verifications.
- Saves screenshots to `tuning_output/stage11d/` automatically.

**`tuning_output/stage11d/`** (gitignored) — checkpoint output directory.

## Checkpoints

> **Escalation rule — read this before running any checkpoint.**
>
> When a checkpoint's after-state measurement does **not** match this spec's expected outcome — whether a test fails, a baseline doesn't reproduce, a perf number regresses outside the stated tolerance, a schema check rejects something it shouldn't, or any output is unexpected enough that the implementer would be guessing at the cause — **STOP**. Do not modify the implementation, the test, or the spec to make it pass. Do not iterate on a fix.
>
> **FLAG the discrepancy and bring it to Westley.** Include: which checkpoint, what was measured, what was expected, what was observed, and the implementer's hypothesis if any. Wait for guidance.
>
> The cost of a wrong silent fix is a debugging session three weeks from now without context; the cost of a five-minute escalation is five minutes. Default to escalation.
>
> This rule exists per CLAUDE.md ("No shotgun fixes" and "One confirmed diagnosis is worth ten guesses") and applies uniformly to every checkpoint below.

Each checkpoint follows the **measure → change → re-measure** pattern.

**Hard prerequisite:** Stage 11c Checkpoint C (the visibility predicate) must be complete before this spec begins. The predicate is a dependency of Checkpoints F, E (minimap), and H. If 11c hasn't landed, **STOP and escalate** rather than building a duplicate predicate locally.

### ✅ Checkpoint A — Baseline confirmation: all five gaps reproduce

**Purpose:** Verify the gap report's findings hold on the current build.

**Baseline measurement:**
1. Launch a tactical mission with at least one primary objective (`hold_zone` or `eliminate_force`) and one secondary.
2. Record evidence of:
   - **G1 — Objective panel raw:** screenshot showing objectives rendered as raw `id  progress%  status` text labels with no descriptions, no bars, no primary/secondary distinction.
   - **G2 — No mission markers:** screenshot of the main view and minimap showing no objective markers anywhere.
   - **G3 — No command indicator:** issue a move command. Screenshot/video showing no visual feedback at the target position.
   - **G4 — Enemy not clickable:** click a visible enemy. Screenshot showing the click had no effect (selection unchanged).
   - **G5 — No minimap viewport box:** pan the camera; minimap shows no rectangle indicating the viewing area.
3. Save evidence to `tuning_output/stage11d/baseline/`.

**Pass condition:** all five gaps reproduce. **If any gap fails to reproduce, STOP and escalate** — gap report may be stale.

**No code change in this checkpoint.**

### ✅ Checkpoint B — Sim contract: objective locations on the wire

**Purpose:** Land the snapshot extension before any Godot consumer needs it.

**Baseline measurement:**
- Run a mission. Capture a snapshot via the existing snapshot logging (or add a one-shot dump). Confirm the `objectives` array entries currently lack `location`.

**Change:**
- Update `architecture.md` with the new field (per D2 and "Files to modify" guidance — author the doc update **first**).
- Extend `_objective_entry()` in `snapshot_serializer.py` per D2.

**After-state measurement:**
- Re-run mission. Capture a snapshot. For each objective with a location-bearing type (`hold_zone`, `extract_unit`, `eliminate_force` with live targets), assert the `location` field is present with `x`, `y`, `layer` keys. For others, assert the field is absent or null per the chosen convention.
- Confirm `architecture.md` reflects the new field.

**Pass condition:** snapshot carries `location` on the right entries; doc reflects the contract. **If the location values look wrong (e.g., always 0, 0), STOP and escalate** — likely indicates the params lookup is missing fields.

### ✅ Checkpoint C — Objective panel rendering: description + bar + primary distinction (Sub-goal 1)

**Purpose:** First user-visible win. Objective panel becomes readable.

**Baseline measurement:**
- Dev scene `scenes/dev/hud_test.tscn` (build it as a Checkpoint C deliverable). Spawn a mission with one primary `hold_zone` and one secondary `eliminate_force`. Screenshot the current objective panel — raw text labels.

**Change:**
- Author the type→description lookup table.
- Replace the raw text label widget with a description-plus-progress-bar widget per D1.
- Apply primary/secondary styling.

**After-state measurement:**
- Re-run dev scene. Screenshot the panel. Visual checks:
  - Primary objective: human-readable description ("Hold the central plateau") with bold/large styling, accent-colored progress bar.
  - Secondary objective: smaller, muted styling.
  - Progress bar fills proportional to `progress`.
- Programmatic check: in code, drive `progress` from 0.0 to 1.0 over a few seconds and assert the bar fill width animates accordingly. (D1 says no tween, but the bar should reflect the new value immediately on each update.)

**Pass condition:** visual evidence + programmatic progress-fill check both pass. **If the type→description lookup misses an objective type, STOP and escalate** — adding new descriptions on the fly without Westley's approval risks tone mismatch.

### ✅ Checkpoint D — Mission markers (in-world + minimap) (Sub-goal 2)

**Purpose:** Player can find the objectives.

**Baseline measurement:**
- Dev scene with both objectives. Confirm: no in-world beams, no minimap icons. (Should match Checkpoint A G2.)

**Change:**
- Implement `mission_marker.tscn` + `.gd`.
- Wire `MissionMarkers` Node3D in `tactical.gd` to subscribe to `TacticalBridge` objective updates; spawn/update/remove markers as objectives' `location` and `status` change.
- Add minimap icon drawing in `_Minimap` per D3.

**After-state measurement:**
- Dev scene: in-world beams visible at correct positions for both objectives, primary distinct color from secondary, label text matches description.
- Minimap: icons at correct positions, primary vs secondary color, shape matches type (square = `hold_zone`, diamond = `eliminate_force`).
- Move the camera; markers stay anchored to world positions (not screen positions). Save screenshot from two camera angles.
- Trigger an objective complete (e.g., kill all targets in `eliminate_force`); confirm the marker either fades out or transitions to "completed" styling per the implementer's choice within D3 — **but flag the chosen completion treatment to Westley** since D3 doesn't specify it. Default safe choice: marker disappears on complete.

**Pass condition:** markers in correct positions; primary/secondary distinguishable; marker behavior on completion documented and approved. **If marker positions are visibly wrong (e.g., offset by canvas-scaling factor), STOP and escalate** — likely a coordinate-system mismatch between sim and renderer.

### ✅ Checkpoint E — Command location indicators (Sub-goal 3)

**Purpose:** Player gets visual feedback for issued commands.

**Baseline measurement:**
- Dev scene. Issue a move command on a friendly. Confirm: no visual feedback (per Checkpoint A G3).

**Resolve OQ2 first:** at the start of this checkpoint, look at the existing command pipeline. Determine whether the engine emits a command-acknowledgment event. If yes → render on event. If no → render on click + render rejection if the engine subsequently rejects. **If the answer is unclear or requires a sim change, STOP and escalate.**

**Change:**
- Implement `command_indicator.tscn` + `.gd` per D4.
- Wire `CommandIndicators` Node3D in `tactical.gd` to spawn indicators on the chosen trigger.

**After-state measurement:**
- Dev scene: issue a move command on flat terrain. Indicator appears at the target position, fades out over ~1.5s. Save video.
- Issue an attack-move. Different indicator shape/color than move.
- Issue several commands rapidly; each indicator stacks (no replacement). Save video.
- If using the click-time path: issue a command on impassable terrain or invalid target. Confirm rejection treatment (red fade or similar). Save video.

**Pass condition:** indicators appear, distinguish move vs attack-move, fade properly, stack on rapid input. **If indicators flicker, lag the click, or appear at wrong positions, STOP and escalate.**

### ✅ Checkpoint F — Enemy clickability with fog gating (Sub-goal 4)

**Purpose:** Visible enemies become clickable; invisible enemies remain unselectable.

**Hard prerequisite:** Stage 11c Checkpoint F (selection respects fog) must already be in place. The visibility predicate is consulted there. This checkpoint relaxes the friendly-only gate while leaving 11c's fog gate underneath.

**Baseline measurement:**
- Dev scene with friendly + enemy units, fog filter active (per 11c). Try to click a visible enemy. Confirm: no selection happens (G4). Try to click an invisible enemy. Confirm: still no selection (also expected — 11c's gate already catches it).

**Change:**
- Modify `_is_selectable()` per D5 to lift the friendly-only gate.

**After-state measurement:**
- Click a visible enemy. Selection-info panel populates with that enemy's HP, type, faction. Save screenshot.
- Click an invisible enemy. No selection happens (visibility predicate from 11c gates it). Save evidence (e.g., a controlled scene where the click target's visibility flips and behavior tracks).
- Multi-select: box-select a region containing both friendlies and visible enemies. Selection includes both. Issuing a move command operates on friendlies only (per D5's "selection prefers friendlies for command issuance"). If existing selection model handles this differently, **escalate before changing it.**

**Pass condition:** visible enemies clickable for inspection; invisible enemies not selectable; mixed selection respects existing command-issuance convention. **If clicking enemies causes commands to fire at them as targets (rather than inspection), STOP and escalate** — this would mean selection's downstream consumers need adjustment that's outside this spec.

### ✅ Checkpoint G — Minimap viewport box (Sub-goal 5)

**Purpose:** Player knows where they're looking.

**Baseline measurement:**
- Dev scene. Pan and zoom the camera. Minimap shows no viewport indication.

**Change:**
- Implement viewport-box drawing in `_Minimap` per D6.
- Per-frame redraw — `_Minimap`'s redraw is already per-frame for unit dots; the box adds to it.

**After-state measurement:**
- Pan camera; box on minimap moves correspondingly. Zoom in; box shrinks. Zoom out; box grows (clipped to minimap bounds at extreme zoom-out).
- Save 4 screenshots: zoomed in, zoomed out, panned to corner, default.
- Programmatic check: log the four projected vertices each frame for one second; assert they form a convex quad and lie within (or are correctly clipped to) the minimap canvas.

**Pass condition:** box tracks camera smoothly; clipping is correct at extremes. **If the box lags the camera by visible frames, STOP and escalate** — likely a draw-order or signal-timing issue; per-frame redraw should be tight.

### ✅ Checkpoint H — Stage close: full integration + perf measurement

**Purpose:** End-to-end demonstration plus 16.7 ms frame budget verification.

**Measurement:**
- Run a real mission from start through ~30 seconds of active combat. Record:
  - Video showing all five sub-goals working: objective panel, mission markers, command indicators, enemy click inspection, minimap viewport box.
  - Godot frame time: average and 99th percentile over the recording window. Compare against a pre-this-spec baseline (capture at start of Checkpoint A).
  - Confirm no errors/warnings in the Godot log.
- Save evidence to `tuning_output/stage11d/stage_close/`.

**Pass condition:**
- All five baseline gaps (G1–G5) visibly closed; new behaviors visibly present and behaving per the per-checkpoint expectations.
- Average frame time within +0.5 ms of pre-spec baseline (D7's expected impact).
- 99th-percentile frame time within +1 ms of pre-spec baseline.
- No new errors or warnings in the Godot log.

**If frame time regresses beyond tolerance, STOP and escalate.** Likely culprits (for Westley's diagnosis, not implementer fix attempts): per-frame minimap canvas redraw spiking on objective marker draws, command indicator decals leaking (failing to free), or per-frame predicate calls vs cached lookups.

## Performance Notes

Total per-frame surfaces this spec touches: minimap canvas (already redrawn per frame; this adds objective icons, viewport box, fog filter — all O(small)), in-world chrome (constant-bounded count of beams and decals), HUD panel (event-driven redraws, not per-frame). Selection adds an O(1) check per click, not per frame.

The simulation contract change (objective `location` on the wire) is sim-side and runs at snapshot time, not per frame on either side. Snapshot serialization cost is dominated by per-unit serialization; adding a per-objective location lookup is negligible.

**Total expected frame-time impact: < 0.5 ms.** Verified at Checkpoint H.

If Checkpoint H shows regression, candidate causes (escalation path, not fix list):
- Mission marker beams using shaders incompatible with the existing render pipeline (e.g., transparent shader queue ordering issues).
- Command indicators failing to free, accumulating over time.
- Minimap viewport-box draw being called per drawn dot rather than once per frame.

Each is a diagnostic question, not an implementer fix.

## Forward References

- **Objective UI polish pass** (post-launch / post-MVP): band-transition highlights when an objective crosses an outcome threshold, animated progress (tweened bar fills), success-condition spectrum visualization showing how close the player is to each outcome band, completion celebrations (audio + particle effects). All deferred per Fork F3.
- **Pre-mission map preview UI** (separate future spec, blocked on Stage 11b): per the design discussion, the preview will show archetype-dependent **spawn locations** instead of actual unit positions, preserving fog asymmetry. Mission markers from this spec are the in-mission counterpart to those preview spawn-location indicators.
- **Command queuing** (`launch_todo.md`): shift-queuing multiple commands. Each queued command would render its own indicator decal at its target — D4's stacking behavior naturally extends. Future spec.
- **Hotkey auto-assignment, shift-click-add-to-selection, double-click-select-all-of-type** (`launch_todo.md`): selection-model UX improvements; independent of this spec.
- **Detailed enemy intel panels:** D5's MVP shows HP / type / faction. Future polish could add squad composition, behavior-script state, predicted next action — but only if those don't break the bible's information-asymmetry stance. Design conversation, not implementation work.

## Out of Scope (reaffirmed)

- **Objective UI polish beyond MVP** — Fork F3.
- **Mission objective generation logic** — `objectives.py` and `mission_generator.py` unchanged.
- **Layer visuals and fog of war rendering** — `stage_11c_layer_visuals_and_fog_spec.md`. This spec consumes 11c's predicate.
- **Map variety wiring** — `stage_11b_map_variety_spec.md`.
- **Pre-mission map preview UI** — separate future spec.
- **Hotkey auto-assignment, shift-select, double-click-select, command queuing, in-game tutorial, chronicle skip controls** — all on `launch_todo.md`, separate concerns.
- **Detailed enemy intel beyond Stage 8's existing selection-info panel content** — future polish.
- **New tick delta shapes** — none required. The snapshot extension (objective `location`) is additive and optional.

## File Map (summary)

**Modify (sim):**
- `simulation/snapshot_serializer.py` — extend `_objective_entry()` with optional `location`.
- `docs/architecture.md` — document the snapshot extension.

**Modify (Godot):**
- `autoload/tactical_bridge.gd` — surface objective locations.
- `scenes/tactical/hud.gd` — objective panel rebuild, minimap icon and viewport-box drawing.
- `scenes/tactical/input_router.gd` — relax `_is_selectable()` per D5.
- `scenes/tactical/tactical.gd` (or main tactical scene root) — host `MissionMarkers` and `CommandIndicators` Node3D parents.

**Create (Godot):**
- `scenes/tactical/mission_marker.tscn` + `mission_marker.gd` — in-world objective beam.
- `scenes/tactical/command_indicator.tscn` + `command_indicator.gd` — transient ground decal.
- `scenes/dev/hud_test.tscn` + `hud_test.gd` — checkpoint dev scene.
- `tuning_output/stage11d/` (gitignored) — checkpoint output directory.

**Bible:** no changes required. All references already documented.

**Estimated size:** ~30 lines of Python (snapshot extension), ~150 lines of GDScript (HUD changes, new nodes, dev scene). Active code surface is moderate; the spec is long because each sub-goal needs its own checkpoint and the escalation rule pins each one.

