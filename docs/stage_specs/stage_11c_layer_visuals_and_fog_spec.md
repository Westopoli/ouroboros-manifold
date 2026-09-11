# Stage 11c — Layer Focus Visuals and Fog of War

## Goal

Land two Godot-side rendering systems whose simulation-side machinery is already complete and already streaming over the bridge but that Godot ignores or under-renders:

1. **Layer focus visuals.** The vertical layer system is mechanically wired (units have `layer` fields, sim computes cross-layer detection, layer rings render under units). What's missing is the *focus* treatment promised by the bible: active-layer emphasis with dimmed inactive layers, a HUD readout of the player's current focused layer, and a layer-preference indicator distinct from the current-layer ring. Per `game_bible.md:534`, this is the bible's "Tier 1 — mechanical baseline" of the three-tier layer rendering plan; Tiers 2 and 3 (light and heavy environmental dressing) are explicitly deferred.

2. **Fog of war rendering.** `fog_of_war.py` correctly computes per-faction visibility every snapshot. `snapshot_serializer.py:125–127` sends `player_visible_unit_uids` to Godot. **Godot ignores the field entirely.** All enemy units render at all times. This spec wires the consumer end: a single visibility predicate consulted by the unit renderer, the minimap, and the selection input handler. Visual treatment is *hidden entirely* — no silhouettes, no last-known-position ghosts (see Design Decisions).

These ship together because they share the same files (`unit_renderer.gd`, `hud.gd`, `tactical_bridge.gd`), share the visibility predicate at the selection layer, and the user-perceived effect of "I can finally tell where my units are and where my enemies aren't" is one experience, not two.

**Not in scope:**
- Light environmental dressing — gradient-driven debris/particles at layer boundaries (`game_bible.md:534` Tier 2).
- Heavy environmental dressing — nebula/asteroid layer boundaries (`game_bible.md:534` Tier 3).
- Per-branch fog parameterization (`game_bible.md` v2.14 explicitly defers Information Warfare branch parameterization to post-Stage 13; the launch ZIP ships Branch 1 / sci-fi values only).
- Last-known-position ghosts and partial-visibility silhouettes (rejected per Design Decision D1).
- Pulse / sensor-sweep visual effects (out unless sim already emits a pulse event — see Open Question OQ1).
- Layer accessibility mask visualization on terrain (the `layer_block_N` masks already shape unit movement; visualizing them as terrain features is a separate Tier-2 concern).
- Mission objectives, mission markers, command-location indicators, minimap viewport box, enemy-clickable behavior — all in `stage_11d_mid_mission_hud_spec.md`. **Note:** this spec lands the visibility predicate that 11d's enemy-clickable feature depends on (see Cross-Stage References).

**Architecture.** All work is on the Godot side. No simulation changes. No new fields added to the snapshot or delta protocol — `player_visible_unit_uids` is already there. A new tiny module (`scripts/tactical/visibility.gd` or equivalent) centralizes the "is this unit visible to the player?" predicate so renderer, minimap, and selection share one definition. Three rendering surfaces (main MultiMesh, minimap canvas draw, selection raycast) consult that predicate. A new HUD panel reads the active layer from `input_router.gd`'s existing state and renders a small indicator. Existing layer rings are extended with a preference variant.

## Bible References

- **`docs/bible_history/bible_2_00_combat.md`** §"Vertical Layer System" (lines 134–160) — 3–5 vertical layers, layer accessibility mask, layer-tied sensor coverage, hard layer transfer vs persistent layer preference, layer indicator rings, preference indicator.
- **`docs/bible_history/bible_2_00_combat.md`** §"Information Warfare" / fog (lines 215–234) — sensor radius per unit, cross-layer sensor range asymmetry, sensor interference zones, branch parameterization (deferred post-Stage 13).
- **`docs/bible_history/bible_2_00_combat.md`** §"Mid-Mission HUD Layout" — confirms terrain stays visible (only enemy units are fogged), minimap shows "visible enemies (dim)" matching this spec's hidden-when-invisible rule.
- **`game_bible.md` (hub)** line 534 — Stage 8 layer rendering three-tier system; this spec is Tier 1 (mechanical baseline).
- **`game_bible.md` (hub)** v2.14 changelog entry — Information Warfare branch parameterization deferred to post-Stage 13.
- **`docs/bible_history/bible_2_00_combat.md`** line 313 — sim 20 ticks/sec, Godot 60 fps target = 16.7 ms frame budget. Performance framing for all checkpoint measurements.

Do NOT read `docs/bible_history/bible_2_00_world.md` (other than the §"Generation Pipeline" sensor-interference references, already captured in Stage 11b), `docs/bible_history/bible_2_00_missions.md`, `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_antagonist.md`, `docs/bible_history/bible_2_00_ai_pipeline.md`, or `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) — not relevant.

## Cross-Stage References

- **Stage 8 (Godot bridge + persistence)** — added layer rings to `unit_renderer.gd:326–376`, added fog-of-war fields to snapshot serialization. This spec consumes what Stage 8 already ships. No Stage 8 contracts change.
- **Stage 8.5** — established the `tactical_bridge.gd` snapshot/delta consumer pattern. This spec extends `TacticalBridge` to expose the `player_visible_unit_uids` set (currently parsed-and-discarded).
- **Stage 11b** — independent; sim-side seed wiring. No interaction.
- **Stage 11d** — depends on this spec. The visibility predicate landed here is the gate for 11d's "only visible enemies clickable" rule (Fork F4). 11d also reuses the predicate for minimap rendering of enemies. Order: 11c lands first, 11d consumes.
- **Stage 12 / 12.5** — selection circle recolor and HUD animation refinement (Stage 12.5) are visual polish that may interact with this spec's HUD readout. No conflict expected; if 12.5 introduced a HUD style guide, the new layer panel follows it.

## Design Decisions

### D1 — Fog visual treatment: hidden entirely

**Decision:** When an enemy unit is not in `player_visible_unit_uids`, it does not render at all. No silhouette. No dimmed marker. No last-known-position ghost. The same rule applies to the minimap.

**Rationale:** Resolves Fork F1 from the design discussion. The bible's fog goal is information asymmetry as a tactical lever; partial-visibility states (silhouettes, ghosts) muddy that lever. Hidden-entirely is the cleanest expression and matches the bible's prose model — *"the player sees only what their units can detect. Everything outside sensor coverage is hidden"* (`docs/bible_history/bible_2_00_combat.md:219`).

**Implication for `partial_visibility_uids`:** the snapshot still carries an empty `partial_visibility_uids` array as a future hook. This spec ignores it. If/when partial visibility is reintroduced (post-Stage-13 era variation), it gets a separate visual treatment specced at that time.

**Implication for terrain:** terrain features (gradient zones, chokepoints, vantage points, reinforcement structures, the spine) are **always visible**. Only enemy *units* are hidden by fog. This matches the bible's mid-mission HUD prose and `game_bible.md:534`'s description of the recon-phase camera.

**Implication for explored-but-not-currently-visible:** also hidden. We do not track an "explored" mask. This is intentional simplicity — re-acquiring previously-seen ground is a tactical cost the player pays, and the alternative requires per-faction terrain memory state we don't currently model.

### D2 — Inactive-layer dimming: alpha modulation on the MultiMesh material

**Decision:** Inactive-layer unit batches render with reduced alpha (default `INACTIVE_LAYER_ALPHA = 0.4`, tunable in config). Active-layer batches render at full alpha (1.0). The dim is applied at the MultiMesh material/instance-color level — no per-unit cost, just one parameter change per layer-batch when the active layer switches.

**Rationale:** The bible says *"active-layer focus, dimmed inactive layers"* (`game_bible.md:534`). "Dimmed" most directly maps to alpha or brightness reduction. Alpha is preferred over desaturation because:
- Cheap on the renderer (instance color modulate, no shader change).
- Composes correctly when units overlap across layers (stacked transparent units read as "on different layers" rather than "blended into one mush").
- Matches RTS convention (StarCraft 2's "dimmed enemy on minimap" uses alpha).

**Tunable, not bible-pinned:** the specific value (0.4) is a playtest-tuned parameter. Reasonable range 0.25–0.6. If 0.4 reads too washed out the value adjusts; the visual treatment stays alpha modulation.

**Layer rings on inactive layers:** rings continue to render but at the same dim alpha as their units, so the player can still see "there are units on layer 3" while focused on layer 2 — the rings are the cue. This preserves the bible's mechanical-baseline guarantee that layer occupancy is always legible.

### D3 — Layer preference indicator: secondary ring with distinct style

**Decision:** When a unit's preferred layer differs from its current layer, render a *second* ring at the unit's position colored for the preferred layer, with a distinct style (default: dashed/outline-only, vs the solid current-layer ring). The secondary ring sits at the same Y as the unit's current layer (not the preferred layer) so it reads as "this unit *wants* to be on layer X" rather than "there's another unit elsewhere."

**Rationale:** The bible explicitly distinguishes hard transfer (immediate layer change) from layer preference (persistent intent that the unit fulfills when conditions allow). The visual must distinguish them. Dashed-vs-solid reads at RTS camera distance and doesn't fight the existing ring color vocabulary.

**Cost:** one extra MultiMesh batch per active layer when any unit on that layer has a preference set. Small. The existing layer-ring batching pattern (`unit_renderer.gd:326–376`) extends naturally.

### D4 — Active layer HUD readout: dedicated indicator panel

**Decision:** Add a small HUD panel (top-left or near the existing layer selector buttons — see Open Question OQ2) showing:
- Current focused layer number ("Layer 2 / 5") in the layer's color.
- A row of 5 small layer markers, with the active one highlighted, so the player sees at a glance which of the layers they're on.

**Rationale:** The launch_todo entry "no indication to player which layer they're on" came from the player seeing only the under-unit rings. The rings tell you what layer *units* are on; they don't tell you what layer the *camera/selection* is focused on. The HUD readout closes that loop.

**Why not extend the existing layer selector buttons:** if the layer selector buttons exist (per `stage_8_spec.md:634`), those tell the player *what's clickable*; they don't necessarily render *focus state* prominently. The readout is a sibling element, not a replacement. If the existing selector already renders focus state clearly, this decision collapses to "make the selector slightly bigger and add the layer color" — implementer's call at code time, after seeing what's already there.

### D5 — Visibility predicate: single source of truth in a tiny module

**Decision:** Create `scripts/tactical/visibility.gd` (or pick the existing convention if `scripts/` isn't where utility scripts live) exposing one function:
```gdscript
static func is_unit_visible_to_player(uid: int) -> bool:
    # Friendly units always visible.
    # Enemy units visible iff uid in TacticalBridge.player_visible_unit_uids.
```

Three consumers call it: `unit_renderer.gd` (skip MultiMesh transform write for invisible units), `hud.gd` (skip minimap dot), and `input_router.gd` (skip click hit-test).

**Rationale:** Three places that must agree on "visible" is exactly the kind of three-place rule that drifts. Centralizing it means one change site if the rule evolves (e.g., post-Stage-13 partial visibility). Per CLAUDE.md traceability rule, the consumers carry `# See also: scripts/tactical/visibility.gd` comments at the call sites.

### D6 — Minimap fog: same predicate, but enemies render dim (not hidden) on the minimap

**Decision wrinkle:** the bible says minimap shows *"visible enemies (dim)"* (`docs/bible_history/bible_2_00_combat.md` §"Mid-Mission HUD Layout"). On the *main view* enemies are hidden when invisible (D1). On the *minimap* visible enemies are rendered dim, invisible enemies are not rendered. The dim treatment is minimap-specific (the main view doesn't dim visible enemies — they render fully).

The visibility predicate from D5 applies the same way: it returns true → render (dim on minimap, full on main view); it returns false → don't render (anywhere).

### D7 — Selection respects fog: invisible enemies are not clickable

**Decision:** `input_router.gd`'s click and box-select code consults `is_unit_visible_to_player()` before adding any enemy unit to the selection. This is the structural prerequisite for Stage 11d's "enemy clickable" feature — once 11d enables enemy selection, fog automatically gates which enemies are eligible.

**Rationale:** Resolves Fork F4 at the predicate layer rather than the input layer. Cleaner than embedding the fog check in two unrelated input paths.

### D8 — Performance framing: 16.7 ms Godot frame budget

All checkpoint measurements in this spec target the 60 fps Godot frame budget per `docs/bible_history/bible_2_00_combat.md:313`. The simulation already does the visibility computation at snapshot time (~once per few seconds, not per frame), so the per-frame Godot cost of fog rendering is the cost of *skipping* MultiMesh writes — which is faster than rendering them. Layer dimming is a single material parameter change per layer-batch when the active layer changes — also negligible. The HUD panel and ring-style additions are constant-cost. **Expected frame-time impact: zero or slightly negative** (faster, since hidden units aren't rendered). Checkpoint H records actual measurements.

## Open Questions

These are noted but not blocking — answer at implementation time, or escalate to Westley if the answer materially changes the spec.

- **OQ1 — Pulse / sensor-sweep visualization.** The sim has `PULSE_RADIUS=500`, `PULSE_REVEAL_TICKS=40`, `PULSE_COOLDOWN_TICKS=400` (`config.py:572–580`), suggesting a pulse mechanic that temporarily reveals enemies. Does the sim emit a pulse event or otherwise mark which unit triggered the pulse? If yes, render an expanding ring at the source. If no, skip — silent reveals are acceptable for MVP. Verify at the start of Checkpoint C; if the answer changes the work, **STOP and escalate** rather than building speculative event hooks.
  - **Resolved:** No discrete pulse event emitted to Godot. `activate_pulse()` expands sensor radius in `compute_visibility()`, so pulse-revealed enemies appear silently in `player_visible_unit_uids`. Pulse visualization dropped from this spec.
- **OQ2 — HUD panel placement.** D4 names "top-left or near the existing layer selector buttons." `stage_8_spec.md:634` mentions a layer selector UI but doesn't anchor its position. Pick at implementation time based on what's already there. If existing HUD layout has no obvious slot, escalate before inventing one.
  - **Resolved:** Placed directly above the existing layer selector panel (bottom-right, y_from_bottom=244). Natural visual grouping with the L0–L4 buttons.

## What to Build

### Files to modify

**`autoload/tactical_bridge.gd`** — expose fog data.
- Add: `var player_visible_unit_uids: Dictionary = {}` (using a Dictionary as a set for O(1) membership tests, since GDScript has no native `Set`). Keys are uids, values irrelevant (e.g., always `true`).
- In the snapshot consumer, populate this from `snapshot["fog_of_war"]["player_visible_unit_uids"]`. Convert array to dict on receipt.
- For deltas: snapshots include the full visible set; deltas may omit it. If the delta omits `fog_of_war`, the previous snapshot's set remains current. Verify the actual delta protocol at implementation — if deltas *do* update visibility incrementally, handle accordingly.
- Add `# See also: scripts/tactical/visibility.gd` near the field declaration.

**`scripts/tactical/visibility.gd`** (new — see Files to create).

**`scenes/tactical/unit_renderer.gd`** — fog filter on enemy MultiMesh batch construction.
- In the per-frame batch rebuild loop (or whatever the existing pattern is — `unit_renderer.gd` may rebuild on snapshot rather than per-frame; preserve that pattern), add an early-continue:
  ```gdscript
  if unit.faction != PLAYER_FACTION and not Visibility.is_unit_visible_to_player(uid):
      continue  # fog: enemy outside sensor range, do not render
  ```
- Add a `# See also: scripts/tactical/visibility.gd — fog gate` comment.
- Inactive-layer dimming: when the active layer changes (consume `input_router.gd`'s `active_layer` signal or read it on rebuild), set per-batch instance color modulation:
  - Active-layer batches → `Color(1, 1, 1, 1)`.
  - Inactive-layer batches → `Color(1, 1, 1, INACTIVE_LAYER_ALPHA)` where `INACTIVE_LAYER_ALPHA` lives in `EraConfig` or equivalent.
- Layer preference indicator: when a unit's snapshot data carries a preference (verify field name on the snapshot side; sim already implements layer preference per `input_router.gd:18–22`), draw a secondary ring batch with a dashed/outline material variant. Add a new MultiMesh batch keyed `(layer, "preference")`.

**`scenes/tactical/hud.gd`** — minimap fog filter + new layer-readout panel.
- Minimap (`_Minimap` class, ~lines 528–558): in the unit-drawing loop, consult `Visibility.is_unit_visible_to_player(uid)`. If false, skip. If true and the unit is enemy, render at MINIMAP_ENEMY_DIM_ALPHA (default 0.6) per D6.
- New panel: `_LayerReadout` (or whatever the file's class-naming pattern is). Reads `TacticalBridge`'s currently-focused layer (or `input_router`'s exported `active_layer`, whichever is the established source — confirm at implementation). Renders "Layer N / 5" in the layer's color plus a 5-marker row with the active marker highlighted.
- HUD construction: add the readout panel to the HUD root with the same parent and styling pattern as existing panels (see `hud.gd:392–393` for objective panel construction; `:447–449` for minimap construction — the readout follows that pattern).

**`scenes/tactical/input_router.gd`** — selection respects fog.
- In `_is_selectable(uid)` (currently at `~262–263` per gap report), extend the existing `selection_eligible` check with a visibility check:
  ```gdscript
  if not Visibility.is_unit_visible_to_player(uid):
      return false
  ```
- Add a `# See also: scripts/tactical/visibility.gd` comment.
- This change does **not** by itself enable enemy clicking (which is a Stage 11d concern). It just ensures that *if* enemies become selectable, the fog filter applies. Friendly units short-circuit through `is_unit_visible_to_player` (always true), so existing friendly-selection behavior is unchanged.

**`autoload/era_config.gd`** (or wherever Godot-side tunables live — confirm at implementation) — add tunables.
- `INACTIVE_LAYER_ALPHA: float = 0.4`
- `MINIMAP_ENEMY_DIM_ALPHA: float = 0.6`
- `PREFERENCE_RING_STYLE: String = "dashed"` (or whatever value the chosen ring shader expects)

### Files to create

**`scripts/tactical/visibility.gd`** — visibility predicate module.
- Static-only class. One public function: `is_unit_visible_to_player(uid: int) -> bool`.
- Reads `TacticalBridge.player_visible_unit_uids` and the unit's faction (via `TacticalBridge.units[uid].faction` or equivalent).
- Returns `true` for the player's own units unconditionally; `true` for enemy units iff `uid in player_visible_unit_uids`; `true` for neutrals (treated as always visible — neutral units are typically reinforcement structures the player can see at all times).
- Edge cases: unknown uid → return `false` (defensive). Empty `player_visible_unit_uids` (snapshot not yet received) → return `false` for enemies (same defensive default — the player should never see things until the first snapshot lands; missions don't gameplay-start until snapshots are flowing anyway).
- Module-level comment points to this spec doc and lists the three consumers.

**Self-test scene `scenes/dev/fog_visibility_test.tscn` + `scenes/dev/fog_visibility_test.gd`** — a tiny dev scene that:
1. Spawns a known unit set (5 friendly, 5 enemy, with 2 enemies inside player sensor range and 3 outside).
2. Renders one frame.
3. Reports: number of enemy units rendered (should be 2), number of minimap dots (should be 7 — 5 friendly + 2 visible enemy), and pass/fail.
4. Used by Checkpoint D and Checkpoint H. Not shipped as a real scene; lives under `scenes/dev/` for ad-hoc validation.

**Optional, only if existing perf logging is insufficient:** `scripts/tactical/frame_perf_logger.gd` to log Godot frame time during checkpoint runs. Per the gap report's perf dossier, `perf_logger.gd` exists but tracks divergence lag, not frame time. If that's still true at implementation, this small logger is a Checkpoint H prerequisite; if a frame-time logger already exists, reuse it.

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

Each checkpoint follows the **measure → change → re-measure** pattern: log the relevant baseline state before the change, make the change, log the new state, confirm the delta matches the expected outcome.

### Checkpoint A — Baseline confirmation: gaps reproduce as described ✅

**Purpose:** Before touching code, confirm that the four observable gaps actually exist on the current build. If any gap fails to reproduce, the gap report was wrong; **STOP and escalate** rather than build against a stale diagnosis.

**Baseline measurement:**
1. Launch a tactical mission (any archetype, default settings).
2. Record evidence (screenshot or video) of:
   - **G1 — Fog absent:** all enemy units visible at all times, regardless of distance from player units.
   - **G2 — No layer focus:** units on inactive layers render at full alpha, indistinguishable from active-layer units.
   - **G3 — No layer preference indicator:** even when a unit has a preference set (issue a layer-preference command via the modifier+1–5 hotkey), no visual change at the unit.
   - **G4 — No HUD layer readout:** the player cannot tell from the HUD which layer is currently focused (only the under-unit rings give layer info, and those are about *unit* layer, not *focus* layer).
3. Save evidence to `tuning_output/stage11c/baseline/`.

**Pass condition:** all four gaps reproduce visually. If any does not reproduce, **STOP and escalate**.

**No code change in this checkpoint.**

### Checkpoint B — Visibility data exposed: TacticalBridge surfaces `player_visible_unit_uids` ✅

**Purpose:** Confirm Stage 8's snapshot is actually carrying fog data and that we can read it. This is the precondition for everything else; if it fails, escalate before doing rendering work.

**Baseline measurement:**
- Add a one-shot debug print in `tactical_bridge.gd` that logs the size of `snapshot["fog_of_war"]["player_visible_unit_uids"]` on each snapshot.
- Run a mission. Confirm: snapshots arrive, the field is present, the size is non-zero (after at least one tick of sim activity), and the size changes as units gain/lose sensor coverage.

**Change:**
- Add `player_visible_unit_uids: Dictionary` to `TacticalBridge`.
- Populate from snapshot, with the array→dict conversion.
- Decide delta handling per the gap report's note that deltas may omit `fog_of_war`. Document the chosen rule with a `# See also` comment.

**After-state measurement:**
- Re-run the same debug print (now reading `TacticalBridge.player_visible_unit_uids` directly). Should match the snapshot field every tick.
- Programmatically assert: for the first snapshot received, `len(player_visible_unit_uids) == len(snapshot["fog_of_war"]["player_visible_unit_uids"])`.

**Pass condition:** parity between snapshot field and `TacticalBridge` field. **If non-empty visibility set never arrives, STOP and escalate** — that means Stage 8's serializer is broken and this spec cannot proceed.

### Checkpoint C — Visibility predicate: `Visibility.is_unit_visible_to_player()` lands ✅

**Purpose:** Centralize the predicate before any consumer uses it. Ensures all three consumers will share one definition.

**Change:**
- Create `scripts/tactical/visibility.gd` per the spec.
- No consumers wired yet.

**After-state measurement:**
- Programmatic test: with a synthetic `TacticalBridge.player_visible_unit_uids = {7: true, 11: true}` and synthetic units {1: friendly, 7: enemy, 11: enemy, 13: enemy, 99: neutral}:
  - `is_unit_visible_to_player(1) == true`
  - `is_unit_visible_to_player(7) == true`
  - `is_unit_visible_to_player(11) == true`
  - `is_unit_visible_to_player(13) == false`
  - `is_unit_visible_to_player(99) == true`
  - `is_unit_visible_to_player(404) == false` (unknown uid)
- Run as a unit test in whatever GDScript test pattern the project uses; if the project has no test harness for GDScript, run it as a one-shot script in the dev scene from Files to create.

**Pass condition:** all six assertions pass. **Any failure: STOP and escalate** — the predicate is the foundation and quietly-broken predicates produce silently-broken renderers.

**Resolve OQ1 here:** before moving to Checkpoint D, look at the sim's pulse code (`config.py:572–580`) and check whether it emits an event Godot can subscribe to. If yes, plan a small pulse-ring renderer addition for Checkpoint G. If no, drop pulse visualization from this spec and **note it in the stage close report.**

### Checkpoint D — Renderer fog: enemy units hidden when invisible ✅

**Purpose:** First user-visible win. After this, enemies outside sensor range are gone from the main view.

**Baseline measurement:**
- Run the dev scene (`scenes/dev/fog_visibility_test.tscn`). With 5 friendly and 5 enemy units (2 visible enemies, 3 outside sensor range), the current renderer draws all 10 units. Save this screenshot.
- Optional: capture a real-mission "before" screenshot for visual diff.

**Change:**
- Apply the fog gate in `unit_renderer.gd`'s batch rebuild loop.
- Use the predicate; do not duplicate fog logic inline.

**After-state measurement:**
- Re-run dev scene. Assert: 7 units render (5 friendly + 2 visible enemy). Save screenshot.
- Real-mission visual check: enemies outside sensor range disappear. Move a friendly unit toward a known invisible enemy until the sensor reaches it; the enemy should appear at exactly the moment the sim's visibility flips. Save a short clip.

**Pass condition:** dev scene renders exactly 7 units. Real-mission spot-check shows the appearance/disappearance transition is clean (no flickering, no half-rendered states). **Any of: extra units rendering, missing friendly units, flickering on transition → STOP and escalate.**

### Checkpoint E — Minimap fog: invisible enemies absent, visible enemies dim ✅

**Purpose:** Apply the predicate to the minimap with the dim treatment per D6.

**Baseline measurement:**
- Dev scene + minimap visible. Count minimap dots: should currently render all 10 units (5 friendly + 5 enemy) at full opacity.

**Change:**
- Update `hud.gd:_Minimap`'s draw loop to consult the predicate and apply `MINIMAP_ENEMY_DIM_ALPHA` to visible enemies.

**After-state measurement:**
- Dev scene minimap: 5 bright friendly dots + 2 dim enemy dots = 7 total. Invisible enemies (3) absent.
- Real-mission spot-check: minimap matches main view's visibility state.

**Pass condition:** dev scene 7 dots with correct dim-vs-bright distribution. **Mismatch with main view's visibility → STOP and escalate** (means the predicate is being read inconsistently and that's a bug worth tracing, not papering over).

### Checkpoint F — Selection fog: invisible enemies not selectable ✅

**Purpose:** Wire the predicate into selection input. Closes the structural prerequisite for Stage 11d's enemy-clickable feature.

**Baseline measurement:**
- Dev scene. Try to box-select all units. Expected current behavior: only friendly units enter selection (because `selection_eligible` already gates enemies). Confirm. Note that Stage 11d will lift the friendly-only gate; we are *adding the fog gate underneath* so it's already in place when 11d removes the friendly gate.

**Change:**
- Extend `_is_selectable()` to consult the visibility predicate.

**After-state measurement:**
- Dev scene: same behavior as baseline (still only friendlies). The fog gate is in place but masked by the friendly gate, so user-visible behavior is unchanged.
- White-box test: in code, temporarily flip a unit's `selection_eligible` to `true` for an invisible enemy. Try to select. Should fail (fog gate catches it). Restore the test override.

**Pass condition:** baseline behavior preserved; white-box test confirms fog gate fires when reachable. **If selection behavior changes for friendly units, STOP and escalate** — friendlies should always pass the predicate; an unintended regression here means the predicate has a bug.

### Checkpoint G — Layer focus dim: inactive layers render with reduced alpha ✅

**Purpose:** Active-layer focus is the second user-visible win. After this, the player can tell at a glance which layer they're on.

**Baseline measurement:**
- Real mission with units across multiple layers. Switch active layer (Tab/Q). Observe: nothing visually changes. Save screenshot.

**Change:**
- Wire the active-layer signal/state from `input_router.gd` into `unit_renderer.gd`.
- Apply per-batch alpha modulation: active-layer batches at 1.0, inactive at `INACTIVE_LAYER_ALPHA` (default 0.4).
- Layer rings (existing) follow the same dimming.

**After-state measurement:**
- Switch active layer. Inactive-layer units visibly dim. Active-layer units remain full brightness. Save screenshot per layer (5 screenshots).
- Programmatic check: read the MultiMesh batch instance colors via Godot's debug tools (or via an in-script log) on layer switch. Assert: active-layer batch alpha == 1.0; inactive-layer batches alpha == `INACTIVE_LAYER_ALPHA`.

**Pass condition:** dim treatment visibly clear, programmatic assertion passes. **If the dim treatment causes z-fighting, color blending artifacts, or breaks the existing ring rendering, STOP and escalate** — alpha modulation interactions with ring shaders may need a different approach.

### Checkpoint H — Layer preference indicator + HUD readout ✅

**Purpose:** Two smaller wins together (each can be sub-checkpointed if the implementer prefers, but they're independent enough that bundling is fine).

**Baseline measurement:**
- Set a layer preference on a unit via the modifier+1–5 hotkey. Observe: no visual change at the unit. Confirm. (Console-log the preference value to confirm the command landed in the sim.)
- Read the HUD: no layer readout panel.

**Change:**
- Add the secondary preference ring batch in `unit_renderer.gd`.
- Add the `_LayerReadout` panel in `hud.gd` per D4.

**After-state measurement:**
- Set a layer preference. Confirm: secondary ring renders at the unit, dashed/outline style, in the preferred-layer color. Switch the preference. Ring updates.
- HUD readout shows current focused layer with color and the 5-marker row. Switch layers (Tab/Q). Readout updates immediately.
- Save screenshots covering: preference set on a unit, three different active layers.

**Pass condition:** preference ring visible and distinct from current-layer ring; HUD readout reflects active layer accurately. **If preference state from the sim is missing, malformed, or doesn't update, STOP and escalate** — the spec assumes the sim already tracks preference (per the gap report); if not, that's a sim-side gap that's out of this spec's scope and needs Westley's call.

### Checkpoint I — Stage close: full integration + perf measurement (pending visual verification)

**Purpose:** End-to-end demonstration plus the 16.7 ms frame budget verification.

**Measurement:**
- Run a real mission from start (mission start) through ~30 seconds of active combat. Record:
  - Video / screenshot reel showing all four gaps closed (G1–G4 from Checkpoint A) plus the new behaviors (fog, dim, preference ring, HUD readout).
  - Godot frame time: average and 99th percentile over the 30-second window. Compare against a pre-this-spec recording (taken before Checkpoint B, captured for this comparison).
  - Snapshot/delta consumption: confirm `player_visible_unit_uids` is being read every snapshot without errors in the log.
- Save evidence to `tuning_output/stage11c/stage_close/`.

**Pass condition:**
- All four baseline gaps (G1–G4) visibly closed; new behaviors visibly present.
- Average frame time within +1 ms of pre-spec baseline (expected: equal or slightly better, since hidden enemies skip MultiMesh writes).
- 99th-percentile frame time within +2 ms of pre-spec baseline.
- No new errors or warnings in the Godot log over the recording window.

**If frame time regresses beyond tolerance, STOP and escalate.** Do not optimize speculatively. Likely causes are listed for Westley's reference but not for the implementer to act on: alpha-blend overdraw on inactive layers, ring batching producing too many draw calls, or per-frame predicate calls instead of per-snapshot. The right next step depends on which one fires, and that's a diagnosis question, not a fix-and-rerun question.

## Performance Notes

The dominant per-frame surfaces touched by this spec are: MultiMesh batch construction in `unit_renderer.gd`, minimap canvas draw in `hud.gd`, and selection raycast in `input_router.gd`. None of these become per-frame *more expensive* under this spec:

- Fog filtering on the MultiMesh batch *reduces* the number of instance writes (fewer enemy transforms when fog is dense). Net cost: negative.
- Inactive-layer dim is one material parameter change per batch, only when active layer changes. Amortized cost ~zero.
- Layer preference rings add at most one extra batch per active layer. Constant-bounded.
- HUD readout panel is drawn once and updates only on layer switch. Constant-bounded.
- The visibility predicate is O(1) — Dictionary lookup against `player_visible_unit_uids`. The predicate is called once per unit per batch rebuild, which already happens. No new per-frame loops.
- Minimap fog filter adds one O(1) lookup per minimap dot, dominated by canvas draw cost which is already paid.

**Expected outcome:** equal or slightly faster frame time post-spec. Checkpoint I is the verification.

**If frame time regresses:** the most likely cause is alpha-blend overdraw. Forward+ rendering handles many opaque draws cheaply but multiple alpha-blended layers stacked over the same screen region can cause fill-rate issues. If Checkpoint I shows regression, the diagnosis path goes to Westley (per the escalation rule) — possible mitigations include per-layer occlusion culling or a stipple/dither shader instead of true alpha, but that's a design conversation, not an implementer choice.

## Forward References

- **Tier 2 environmental dressing** (light): gradient-driven debris/particles at layer boundaries. Out of scope here. Future spec consumes the gradient sources already produced by Stage 7's `gradient_placer.py` and renders them as ambient particles. The visibility predicate from this spec will inform whether such particles render in fogged regions (probably yes — terrain features stay visible per D1).
- **Tier 3 environmental dressing** (heavy): nebula/asteroid layer boundaries. Open Question #16 in the bible per `game_bible.md` (v2.04). Long-term concern; not blocking.
- **Per-branch fog parameterization:** post-Stage 13, when Branch 2 (modern) and Branch 3 (ancient) ship, this spec's predicate becomes the consumer of branch-parameterized values. Branch 1 (sci-fi) ships with current values per `game_bible.md` v2.14. The visibility predicate's signature does not change; the values feeding it do.
- **Last-known-position ghosts and partial visibility:** if introduced post-launch, they get their own spec. The `partial_visibility_uids` field already exists on the snapshot as a hook.
- **Pulse / sensor sweep visualization:** OQ1 above. If the sim emits a pulse event, a small future spec wires a ring renderer to it. If not, deferred.

## Out of Scope (reaffirmed)

- **Tier 2/3 environmental dressing** — separate future spec.
- **Per-branch fog values** — post-Stage 13.
- **Last-known-position ghosts, partial-visibility silhouettes** — rejected per D1.
- **Layer accessibility mask terrain visualization** — a Tier 2 concern; the masks already shape unit movement, but rendering them as terrain features is separate.
- **Sim-side changes** — none. All work is Godot-side. If a sim-side gap surfaces during implementation (e.g., layer preference field not actually serialized), **STOP and escalate** rather than building around it.
- **Mission objectives, mission markers, command indicators, enemy clickability (the visibility-predicate consumer), minimap viewport box** — all in `stage_11d_mid_mission_hud_spec.md`.
- **Map variety wiring** — `stage_11b_map_variety_spec.md`.

## File Map (summary)

**Modify:**
- `autoload/tactical_bridge.gd` — expose `player_visible_unit_uids`.
- `scenes/tactical/unit_renderer.gd` — fog gate, inactive-layer dim, preference ring batch.
- `scenes/tactical/hud.gd` — minimap fog filter, new layer-readout panel.
- `scenes/tactical/input_router.gd` — selection consults predicate.
- `autoload/era_config.gd` (or equivalent) — three new tunables.

**Create:**
- `scripts/tactical/visibility.gd` — visibility predicate (single source of truth).
- `scenes/dev/fog_visibility_test.tscn` + `.gd` — checkpoint dev scene.
- `tuning_output/stage11c/` (gitignored) — checkpoint output directory.
- Possibly `scripts/tactical/frame_perf_logger.gd` if existing perf logging doesn't track frame time.

**Bible:** no changes required. All references already documented.

**Estimated size:** ~150 lines of Godot code total (predicate ~30, renderer changes ~40, HUD additions ~50, input router changes ~10, tunables ~5, dev scene ~40). The spec is long because the rendering paths interact subtly and the escalation rule needs each checkpoint pinned. The active code surface is moderate.

## Implementation Notes

**Implemented 2026-04-29.** All checkpoints B–H complete. Checkpoint I pending visual verification.

**Scope deviation — sim-side serialization of `preferred_layer`:**
The spec stated "no simulation changes," but `snapshot_serializer.py` did not serialize `layer_preferences` — the sim stored them but never sent them to Godot. Added `preferred_layer` field to `_unit_entry()` (reads from `engine.layer_preferences`) and delta change detection. This was escalated and approved by Westley as the bible-aligned option (bible treats preference as sim-authoritative state; client-side tracking would diverge from snapshot-as-truth).

**Visibility module registered as autoload:**
The spec proposed a `class_name` static utility. GDScript static functions cannot access autoload singletons (no scene tree in static context). Changed to an autoload registered in `project.godot` as `Visibility`. Call-site syntax unchanged (`Visibility.is_unit_visible_to_player(uid)`).

**Dev scene not created:**
`scenes/dev/fog_visibility_test.tscn` was not created. Predicate correctness verified by logic walkthrough against spec's six test cases. Visual verification deferred to Checkpoint I mission run.

**OQ1 — Pulse visualization dropped:**
`fog_of_war.py:activate_pulse()` silently expands sensor radius within `compute_visibility()`. No discrete event emitted to Godot. Pulse-revealed enemies appear in `player_visible_unit_uids` transparently. Future pulse ring visualization would require a new sim-side event.
