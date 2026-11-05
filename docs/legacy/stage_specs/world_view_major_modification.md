# Stage 11.5 — World View 3D Territory Visualization

## Goal

Replace the 2D metaball territory plane with a 3D constellation + shell hybrid territory visualization, add a three-band zoom disclosure ladder with plateau-and-edge blending, implement player camera controls (pan/orbit/zoom/click-to-focus), add a faction list panel with hover-dim/click-isolate, and wire time-jump animation dynamics (smooth territory morphing, chronicle-linked focus, faction-colored scroll text). This is the stage that makes the world view feel like a living, navigable 3D space instead of a flat projected overlay.

## Bible References

Read the hub (`game_bible.md`) plus these spokes:

- `docs/bible_history/bible_2_00_world.md` → "Galaxy View — The Strategic Layer Between Missions" (Faction territory, Connections, Military activity visualization, Ambient particle field). Note: the "projected Voronoi influence field" paragraph (lines 399–403) is **superseded** by this spec's constellation + shell hybrid. The metaball field math survives into the 3D shell implementation. The "snap transition, masked by the accompanying combat flash VFX" sentence (line 403) is **superseded** by Q4a's smooth tween — territory changes interpolate continuously, no snapping. The "SubViewport projected onto a plane quad" implementation note (line 405) is **superseded** — the 2D plane is replaced by 3D raymarched shells.
- `docs/bible_history/bible_2_00_chronicle.md` → "Chronicle Scroll — Visual Presentation" (scroll panel layout, entry interaction states). This spec touches the scroll for faction-colored entry text and chronicle-linked focus highlight.
- `docs/bible_history/bible_2_00_animation_strategy.md` → full document. Smooth-fade-over-cuts rule applies to all zoom band transitions and territory morphing.
- `world_view_disclosure_design.md` → the design doc that produced all decisions implemented here. Authoritative for Q1–Q4 design rationale.

Also read these completed artifacts:

- `amendment_world_view_architecture.md` — defines the shell + data + renderer + camera component architecture. All work targets this architecture.
- `stage_11_spec_amended.md` — the completed Stage 11 spec. This spec builds on top of Stage 11's completed infrastructure.

Do not read other spokes or stage specs.

## Context

Stage 11 delivered the macro-loop: mission end → pull-back → world view with chronicle scroll → push-in → next mission. The world view component architecture is in place (WorldViewShell orchestrator, WorldViewData store, SettledReachRenderer, OrbitalCamera3D). The territory visualization currently uses a 2D metaball shader rendered to a SubViewport and projected onto a flat plane — functional but not the intended final look. Connections render as straight `ImmediateMesh` lines. The camera is auto-orbit only with no player input.

This stage replaces the territory visualization with a 3D system, adds player camera interaction, and enhances the scroll with faction-colored text and territory-animation synchronization.

### Prerequisite — Main Menu / World View File Separation

`world_view_structure.gd` currently serves dual duty as both the main menu galaxy and the world view renderer. Before any modifications, separate these into independent files so the main menu is never at risk:

1. **Copy** `world_view_structure.gd` → `main_menu_galaxy.gd` (identical copy, frozen — never modified by this spec or any future world view work)
2. **Copy** `world_view_structure.tscn` → `main_menu_galaxy.tscn` (update script reference to `main_menu_galaxy.gd`)
3. **Update** `main_menu.gd` to load `main_menu_galaxy.tscn` instead of `world_view_structure.tscn`
4. **Update** `loading_screen.gd` if it also references `world_view_structure.tscn` — point to `main_menu_galaxy.tscn`
5. **Verify** main menu renders identically after the rename

After this step, `world_view_structure.gd/.tscn` is exclusively the world view renderer — free to modify without risk to the main menu. `main_menu_galaxy.gd/.tscn` is the main menu's private copy — frozen, redundant code and all.

### What's Being Replaced (in `world_view_structure.gd` only — main menu unaffected)

**Removed:**
- `territory_metaball.gdshader` — the 2D canvas_item metaball shader
- `territory_voronoi.gdshader` — legacy, already superseded
- The SubViewport + ColorRect + PlaneMesh pipeline (`_setup_territory_metaball()`, `_rebuild_territory_data()`, `_territory_viewport`, `_territory_color_rect`, `_territory_plane`)
- All `_system_data_image/texture`, `_faction_colors_image/texture`, `_faction_borders_image/texture` variables and their population logic
- The straight-line connection rendering (`_on_connection_added()`, `_on_connection_removed()`, `_connection_visuals` dictionary) — replaced by constellation renderer's Bézier arc filaments

**Preserved:**
- System node rendering (emissive white sphere + colored halo shell in `_on_region_added`) — stays as-is
- Connection data model in `WorldViewData` — unchanged
- Conflict flashes (`_on_flash_conflict_requested`, `_on_flash_region_requested`) — unchanged, layered on top
- Highlight pulse (`_on_highlight_changed`) — unchanged
- Main menu particle galaxy (`main_menu_galaxy.tscn` instanced by `main_menu.gd`) — completely separate file, never touched
- WorldViewShell, WorldViewData, time_jump_sequencer — unchanged orchestration layer

### What's New

1. **3D constellation renderer** — faction-colored luminous filament arcs between adjacent same-faction systems
2. **3D shell renderer** — translucent metaball isosurface membranes wrapping each faction's territory volume
3. **Zoom disclosure ladder** — three-band plateau-and-edge system (Overview / Regional / Local) modulating visual properties by camera distance
4. **Player camera controls** — left-drag pan, scroll zoom, right-drag orbit, click-to-focus
5. **Faction list panel** — persistent UI with hover-dim and click-isolate
6. **Faction data panel** — whole-faction info displayed on click-to-focus or faction selection
7. **Time-jump animation dynamics** — smooth territory tween morphing, chronicle-linked focus, faction-colored scroll entry text, ambient conflict flashes
8. **Camera controls (cross-band)** — replaces auto-orbit-only with player-interactive camera

---

## Chronicle Text Rework Coordination

> **⚠ CROSS-PLAN NOTICE — Chronicle Text Rework**
>
> A separate chronicle text rework plan is being constructed. This spec touches the chronicle scroll in the following ways:
>
> **Files this spec modifies that the chronicle rework may also touch:**
> - `scenes/world/chronicle_scroll_panel.gd` — adds faction-color tinting to entry text
> - `scenes/world/chronicle_entry.gd` — adds faction-color tinting per entry based on `faction_color` field in entry data
> - `scenes/world/time_jump_sequencer.gd` — adds chronicle-linked focus highlight (brightens the system referenced by the currently-printing entry)
>
> **Files this spec does NOT touch that are chronicle-only:**
> - `scenes/world/chronicle_entry_expansion.gd`
> - Chronicle distiller (`simulation/world_view/keyframe_selector.py`, `simulation/world_view/keyframe_message.py`)
> - `docs/bible_history/bible_2_00_chronicle.md`
>
> **Data contract change:** Chronicle entry messages gain a new optional field `faction_color` (hex string or null). The scroll panel uses this to tint the entry text. If the chronicle rework changes the entry message schema, coordinate on this field.
>
> **Behavioral overlap:** The "chronicle-linked focus" feature (system brightens when its entry is printing) is driven by the `chronicle_entry_id` field on keyframe messages, which already exists. No schema change needed — just new renderer behavior on the Godot side.

---

## Design Decisions (from `world_view_disclosure_design.md`)

### Q1 — Core Territory Metaphor

**Constellation + shell hybrid.** Both visual layers always present. Neither is a mode.

1. **Constellation (skeleton):** Bright faction-colored luminous filament arcs connecting every pair of adjacent same-faction systems. Derived from the connection graph in WorldViewData (border and trade edge types). Rendered as 3D curves between system nodes, not lines on a plane. Gentle arcs through 3D space so overlapping filaments don't collide visually. Saturated core + soft bloom halo + slow traveling shimmer suggesting information flow.
2. **Shell (skin):** Thin translucent 3D membrane wrapping each faction's influence volume. Same-faction systems share one continuous shell. Rival shells maintain a visible gap (margin-of-victory, carrying forward the `gap_margin` concept). Border vs. trade filament distinction: `border`/`both` = solid bright filaments; `trade` = thinner, dimmer, dashed.

### Q2 — Zoom Disclosure Mechanism

**Three-band plateau-and-edge.** Camera distance divided into Overview / Regional / Local bands, each with a stable plateau interior and blend zones at edges.

```
Overview plateau: dist ≥ ~75
Overview → Regional blend: ~65 ≤ dist < ~75
Regional plateau: ~40 ≤ dist < ~65 (widest — default band)
Regional → Local blend: ~25 ≤ dist < ~40
Local plateau: dist < ~25
```

All threshold values are tuning parameters.

### Q2.5a — Regional Plateau Look

**Constellation-dominant, shells subordinate, rival-shell border glow as signature accent.**

Visual hierarchy (most to least prominent): border glows → constellation filaments → system nodes → faction shells (8–15% opacity) → galaxy particles. Overall impression: four glowing webs of light, each a different color; where they touch, they spark brightly.

### Q2.5b — Overview Plateau Look

**Shell-dominant, constellation subordinate, opaque enough to occlude.**

Shells at 40–60% opacity — front-facing surfaces render opaque enough to occlude factions behind. Constellation filaments dim to faint glow/thin lines. Border glow softens (Regional's signature, not Overview's). System nodes shrink to small points. Faction names or sigils float at shell center-of-mass. Orbital rotation is meaningful — player rotates to see behind occluding shells.

### Q2.5c — Local Plateau Look

**Click-to-focus, neighborhood spotlight, soft muted vignette.**

Player clicks a system to center camera and enter Local. The focal system brightens; its direct constellation filaments thicken and brighten, but connected neighbor system nodes do NOT brighten (consistent with Q3a hover behavior — filaments glow, nodes don't). Shells reduce to subtle ground-fog. Distant systems desaturate and dim but remain visible. Faction data panel shows whole-faction info.

### Q3 — Hover and Focus Interactions

- **Q3a — System hover:** Highlight + tooltip (system name, owner). Hovered system's direct filaments brighten. Connected neighbors do NOT brighten.
- **Q3b — Filament hover:** None. Filaments are visual texture, not interactive.
- **Q3c — Shell hover:** None. Shells are atmospheric, not interactive.
- **Q3d — Band sensitivity:** Hover is band-sensitive. Tooltip content adapts per plateau (specifics deferred to tuning).

### Q4 — Time-Jump Animation Dynamics

- **Q4a — Shell morphing:** Smooth tween. Shell isosurfaces interpolate continuously. Territory changes are slow and gradual.
- **Q4b — Chronicle-linked highlight:** System referenced by current chronicle entry brightens subtly. Chronicle entry text tinted/wrapped in faction color. Combat flashes pulse constantly wherever conflicts are active (ambient, not tied to specific entries).
- **Q4c — Simultaneous events:** All events in a keyframe animate at once. Works because smooth tween makes simultaneous changes gradual and legible.

### Camera Controls (cross-band)

- Left-click drag → pan (slides camera look target, no repositioning)
- Scroll → zoom (moves camera along forward axis)
- Right-click drag → orbit (repositions camera around look target)
- Click system → focus (center camera + zoom to Local band)

---

## What to Build

### New files

```
scenes/shared/world_view/renderers/
├── constellation_renderer.gd          - 3D filament arc rendering between same-faction systems
├── shell_renderer.gd                  - 3D metaball isosurface membrane per faction
├── shell_metaball.gdshader            - 3D raymarched metaball shell shader (spatial shader)
├── constellation_filament.gdshader    - Filament glow shader (spatial shader)

scenes/shared/world_view/
├── zoom_disclosure_controller.gd      - Plateau-and-edge band logic, blend factor computation

scenes/world/
├── faction_list_panel.tscn            - Persistent UI: faction names + color swatches
├── faction_list_panel.gd
├── faction_data_panel.tscn            - Faction info display (opposite side from list)
├── faction_data_panel.gd
```

### Modified files

```
scenes/shared/world_view/renderers/
└── settled_reach_renderer.gd          - Gut territory metaball pipeline.
                                         Instance constellation_renderer and shell_renderer.
                                         Connect to ZoomDisclosureController for band-driven
                                         property modulation (opacity, filament width, etc.).
                                         Add smooth territory tween morphing on territory_updated.
                                         Add chronicle-linked focus highlight.

scenes/shared/world_view/
├── main_menu_galaxy.gd                - NEW (exact copy of current world_view_structure.gd — frozen,
                                         never modified by this or any future world view spec)
├── main_menu_galaxy.tscn              - NEW (exact copy of current world_view_structure.tscn, script
                                         reference updated to main_menu_galaxy.gd — frozen)
├── world_view_structure.gd            - Remove _setup_territory_metaball(), _rebuild_territory_data(),
                                         all SubViewport/plane/texture variables.
                                         Remove territory_voronoi/metaball shader references.
                                         Remove _on_connection_added(), _on_connection_removed(),
                                         _connection_visuals (replaced by constellation renderer).
                                         This file is now exclusively the world view renderer.
                                         The main menu uses main_menu_galaxy.gd instead.
├── world_view_data.gd                 - Add faction-level aggregate data (system count, territory
                                         percentage) for the faction data panel.
                                         Add signal: faction_data_changed(faction_id: String).
└── world_view_shell.gd                - Add faction list/data panel management.
                                         Add zoom disclosure controller instantiation.
                                         Expose click-to-focus and faction-isolate API.

scenes/shared/world_view/cameras/
└── orbital_camera_3d.gd               - Add mouse input: left-drag pan, right-drag orbit,
                                         scroll zoom. Add click-to-focus (raycast → system node
                                         → center + zoom to Local). Integrate with
                                         ZoomDisclosureController (report current distance).

scenes/world/
├── chronicle_scroll_panel.gd          - Add faction-color tinting to entries.
├── chronicle_entry.gd                 - Accept faction_color from entry data, tint text.
└── time_jump_sequencer.gd             - Add chronicle-linked focus: on chronicle_entry signal,
                                         resolve region_id from entry, brighten that system node
                                         via shell API. Add ambient conflict flash cycling during
                                         time jumps (constant background flashes).

scenes/shared/world_view/renderers/
├── territory_metaball.gdshader        - DELETE
└── territory_voronoi.gdshader         - DELETE (if still present)
```

### Files explicitly NOT modified

- Main menu scene (`main_menu.gd` updated ONCE to load `main_menu_galaxy.tscn`; `main_menu_galaxy.gd/.tscn` frozen after creation — never modified)
- Chronicle distiller, keyframe selector, keyframe message — no sim-side changes
- UIDataBus signals — no new signals needed
- Tactical scene — unaffected
- `docs/bible_history/bible_2_00_chronicle.md` — no bible changes in this spec (bible capture is a separate step)

---

## Input/Output Shapes

### Chronicle entry message — data contract addition

Existing `chronicle_entry` message gains one optional field:

```json
{
  "type": "chronicle_entry",
  "entry_id": "ce_0017",
  "faction_color": "#3a7bd5",
  ...existing fields...
}
```

`faction_color` is nullable. When present, the scroll panel tints entry text with this color. When null, default text color is used. The sim side populates this from the faction that is the primary subject of the entry.

### ZoomDisclosureController output

The controller exposes a read-only state that other components poll or subscribe to:

```gdscript
var current_band: String  # "overview" | "regional" | "local"
var blend_factor: float   # 0.0 = pure current band, 1.0 = pure adjacent band
var blend_direction: String  # "up" (toward overview) | "down" (toward local) | "none"

signal band_changed(new_band: String, old_band: String)
```

The renderer reads `current_band` and `blend_factor` each frame to modulate visual properties.

---

## Engineering Decisions and Defaults

### Shell rendering technique

**Raymarched metaball isosurface** via a spatial shader on a large enclosing box mesh (one per faction). The 2D metaball math from `territory_metaball.gdshader` (influence formula `R² / (d² + R²)`, faction field summation, gap margin) ports to 3D by evaluating the field at raymarched sample points along view rays. The isosurface renders where the field crosses the threshold. Shell opacity, color, and glow are modulated by the zoom disclosure controller.

Performance budget: 8 factions × 20–30 systems. The raymarched box can be tightly fitted per faction (bounding box of faction's systems + influence radius margin). Step count is a tuning value (start at 32 steps, reduce if needed).

If raymarching proves too expensive at 8 factions, fallback is marching-cubes mesh generation on territory change (not per-frame). This is an engineering decision for CC to evaluate during implementation.

### Constellation filament rendering

**Tube meshes with emissive material + bloom.** Each filament is a low-poly tube mesh (8-sided cross-section) following a cubic Bézier curve between system positions. The curve's control points are offset perpendicular to the direct line so filaments arc through 3D space. Core uses faction-colored emissive material. Bloom halo comes from Godot's built-in glow post-process (already enabled for the galaxy scene).

Traveling shimmer: a UV-scrolling noise texture on the filament's emissive intensity, creating a slow pulse that travels along the filament length. Speed is a tuning value.

Trade vs. border distinction: `border`/`both` connections = full-width tube; `trade` = half-width tube with dashed pattern (alpha mask on UV.x).

### Zoom disclosure interpolation

**Per-property blend curves stored in the ZoomDisclosureController.** Each visual property (shell opacity, filament width, filament alpha, border glow intensity, node scale, label visibility) has a value at each plateau. The controller computes `blend_factor` from camera distance and the renderer lerps each property between plateau values using that factor.

### Player camera input

Mouse input handled in `orbital_camera_3d.gd`. During time-jump auto-orbit, player input overrides auto-orbit (per bible: "player can click-drag to override auto-orbit at any time"). When not in time-jump, camera is fully player-controlled.

Click-to-focus uses `PhysicsRayQuery3D` from camera through mouse position. System nodes have `StaticBody3D` + `CollisionShape3D` children for raycasting. On hit, camera animates to Local band centered on the clicked system.

### Faction list panel

Godot `Control` node, always visible during world view. Positioned at screen left (or right — tuning). Each faction entry is a `HBoxContainer` with color swatch + faction name label. Mouse enter → emit hover signal. Click → emit isolate signal. The shell relays these to the renderer, which modulates constellation/shell visibility per faction.

### Territory morphing during time jumps

When a `time_jump_keyframe` arrives with `ownership_changes`, the renderer does NOT snap territory. Instead:
1. The shell's metaball field parameters (which systems belong to which faction) are updated immediately in the data model.
2. The visual shell mesh lerps from old isosurface to new isosurface over `TERRITORY_MORPH_DURATION_SEC` (tuning value, default 2.0s).
3. Constellation filaments for changed connections fade out (old) and fade in (new) over the same duration.

This produces the "one color slowly eating into another" effect from Q4a.

---

## Tuning Values (defaults; added to `simulation/config.py` or `world_view_config.py`)

```python
# Zoom disclosure bands
ZOOM_OVERVIEW_PLATEAU_MIN = 75.0
ZOOM_OVERVIEW_REGIONAL_BLEND_START = 65.0
ZOOM_REGIONAL_PLATEAU_MIN = 40.0
ZOOM_REGIONAL_LOCAL_BLEND_START = 25.0
ZOOM_LOCAL_PLATEAU_MAX = 25.0

# Shell opacity per band
SHELL_OPACITY_OVERVIEW = 0.50
SHELL_OPACITY_REGIONAL = 0.12
SHELL_OPACITY_LOCAL = 0.05

# Constellation per band
CONSTELLATION_WIDTH_OVERVIEW = 0.05      # thin/faint
CONSTELLATION_WIDTH_REGIONAL = 0.15      # full prominence
CONSTELLATION_WIDTH_LOCAL = 0.20         # thickened for focal connections
CONSTELLATION_ALPHA_OVERVIEW = 0.3
CONSTELLATION_ALPHA_REGIONAL = 1.0
CONSTELLATION_ALPHA_LOCAL = 1.0
CONSTELLATION_SHIMMER_SPEED = 0.3        # UV scroll speed

# Border glow
BORDER_GLOW_INTENSITY_OVERVIEW = 0.3
BORDER_GLOW_INTENSITY_REGIONAL = 1.0     # Regional signature
BORDER_GLOW_INTENSITY_LOCAL = 0.5

# Node scale per band
NODE_SCALE_OVERVIEW = 0.5
NODE_SCALE_REGIONAL = 1.0
NODE_SCALE_LOCAL = 1.2

# Floating faction labels (Overview only)
FACTION_LABEL_ALPHA_OVERVIEW = 1.0
FACTION_LABEL_ALPHA_REGIONAL = 0.0        # invisible at Regional and Local
FACTION_LABEL_FONT_SIZE = 24

# Territory morphing
TERRITORY_MORPH_DURATION_SEC = 2.0

# Faction list panel
FACTION_LIST_HOVER_DIM_ALPHA = 0.3       # other factions dim to this
FACTION_LIST_ISOLATE_HIDE_ALPHA = 0.05   # other factions nearly invisible

# Camera
CAMERA_PAN_SPEED = 0.5
CAMERA_ORBIT_SPEED = 0.01
CAMERA_ZOOM_SPEED = 2.0
CAMERA_ZOOM_MIN = 15.0
CAMERA_ZOOM_MAX = 120.0
CAMERA_FOCUS_DURATION_SEC = 1.5

# Chronicle-linked focus
CHRONICLE_FOCUS_BRIGHTNESS_BOOST = 2.0   # emission multiplier on the focal system
CHRONICLE_FOCUS_FADE_DURATION_SEC = 0.5

# Ambient conflict flashes during time jumps
AMBIENT_FLASH_MIN_INTERVAL_SEC = 0.5
AMBIENT_FLASH_MAX_INTERVAL_SEC = 2.0
AMBIENT_FLASH_INTENSITY = 0.4
```

---

## Checkpoints

Each checkpoint is a STOP point per `dev_rules.md`.

### Checkpoint A — Main Menu / World View File Separation

**New files:**
- `scenes/shared/world_view/main_menu_galaxy.gd` (exact copy of current `world_view_structure.gd`)
- `scenes/shared/world_view/main_menu_galaxy.tscn` (exact copy of current `world_view_structure.tscn`, script path updated)

**Modified files:**
- `scenes/main_menu/main_menu.gd` — change load path from `world_view_structure.tscn` to `main_menu_galaxy.tscn`
- `loading_screen.gd` — same load path update if applicable

**Build:**
1. Copy `world_view_structure.gd` → `main_menu_galaxy.gd`. No code changes.
2. Copy `world_view_structure.tscn` → `main_menu_galaxy.tscn`. Update script reference to `main_menu_galaxy.gd`.
3. Update all main menu / loading screen references to point to the new files.
4. `world_view_structure.gd/.tscn` remains in place — it is now exclusively the world view renderer.
5. `main_menu_galaxy.gd/.tscn` is frozen from this point forward. No future world view spec may modify it.

**Prove-it:** Launch game. Main menu renders identically — same particle galaxy, same camera moods, same title heartbeat. No visual change whatsoever. Then run the existing `scenes/debug/test_world_view.tscn` harness — world view still renders regions, territory, connections, and flashes as before the split. Both scenes work independently.

⛔ STOP.

### Checkpoint B — Zoom Disclosure Controller + Camera Controls

**New files:**
- `scenes/shared/world_view/zoom_disclosure_controller.gd`

**Modified files:**
- `orbital_camera_3d.gd` — add mouse input handling (pan, orbit, zoom), click raycast, distance reporting

**Build:**
1. ZoomDisclosureController: takes camera distance each frame, computes `current_band`, `blend_factor`, `blend_direction`. Emits `band_changed` signal on plateau transitions.
2. Camera input: left-drag pan, right-drag orbit, scroll zoom. Click raycast against system node collision shapes. On hit, animate camera to Local band centered on clicked system.
3. During time-jump auto-orbit, player input pauses auto-orbit and resumes on mouse release (or after timeout).

**Prove-it:** Test harness with mock system nodes. Scroll through all three bands — console prints band transitions and blend factors. Click a system — camera animates to Local. Pan, orbit, zoom all responsive. Westley reviews.

⛔ STOP.

### Checkpoint C — Constellation Renderer

**New files:**
- `scenes/shared/world_view/renderers/constellation_renderer.gd`
- `scenes/shared/world_view/renderers/constellation_filament.gdshader`

**Build:**
1. For each same-faction connection in WorldViewData, generate a tube mesh following a cubic Bézier arc between the two system positions.
2. Apply faction-colored emissive material with bloom halo.
3. UV-scrolling shimmer on emissive intensity.
4. Border/both connections = full width. Trade connections = half width + dashed alpha.
5. Connect to ZoomDisclosureController: modulate filament width and alpha per band.

**Prove-it:** Test harness with 3 factions, connections between systems. Filaments render as colored arcs with visible bloom. Trade connections visually distinct from border. Zoom in/out — filaments modulate per band. Westley reviews.

⛔ STOP.

### Checkpoint D — Shell Renderer

**New files:**
- `scenes/shared/world_view/renderers/shell_renderer.gd`
- `scenes/shared/world_view/renderers/shell_metaball.gdshader`

**Modified files:**
- `world_view_structure.gd` — remove all 2D territory pipeline code (`_setup_territory_metaball`, `_rebuild_territory_data`, SubViewport, plane, texture variables) AND all straight-line connection rendering code (`_on_connection_added`, `_on_connection_removed`, `_connection_visuals`)
- `settled_reach_renderer.gd` — remove territory metaball setup, add constellation_renderer + shell_renderer instantiation

**Build:**
1. Port 2D metaball field math to 3D raymarched spatial shader. Influence formula stays `R² / (d² + R²)` evaluated at 3D sample points. Gap margin preserves faction separation.
2. One enclosing box mesh per faction, tightly fitted to faction's system bounding box + influence radius margin. Shader raymarches from camera through the box.
3. Shell renders as translucent colored surface at the isosurface threshold. Front-face rendering only (back-face culled for occlusion behavior at Overview).
4. Connect to ZoomDisclosureController: shell opacity modulates per band (50% at Overview, 12% at Regional, 5% at Local).
5. Border glow: where two rival faction shells nearly meet, a bright luminous seam. Intensity modulates per band (strongest at Regional).
6. Floating faction labels: at Overview plateau, each faction's name or sigil renders as a billboard label at the shell's center-of-mass. Labels fade in during the Overview→Regional blend zone and are invisible at Regional and Local. Labels are `Label3D` nodes with billboard mode, positioned at the centroid of each faction's system positions.

**Prove-it:** Test harness with 4 factions. Shells render as colored 3D volumes. Gap visible between rival factions. Zoom to Overview — shells occlude, opacity high, faction name labels visible at shell centroids. Zoom to Regional — shells fade, constellation dominates, labels fade out. Zoom to Local — shells nearly invisible, no labels. Westley reviews.

⛔ STOP.

### Checkpoint E — Faction List Panel + Data Panel + Isolate/Hover

**New files:**
- `scenes/world/faction_list_panel.tscn + .gd`
- `scenes/world/faction_data_panel.tscn + .gd`

**Modified files:**
- `world_view_shell.gd` — instantiate panels, relay hover/isolate signals to renderer
- `world_view_data.gd` — add faction-level aggregate data computation and `faction_data_changed` signal
- `settled_reach_renderer.gd` — add faction dim/isolate visual logic (modulate constellation + shell alpha per faction)

**Build:**
1. Faction list panel: always visible during world view. Lists all factions with color swatch + name. Hover → emit signal, renderer dims other factions to `FACTION_LIST_HOVER_DIM_ALPHA`. Click → isolate, other factions to `FACTION_LIST_ISOLATE_HIDE_ALPHA`. Click again to deselect.
2. Faction data panel: appears on opposite side of screen. Shows whole-faction stats (name, system count, territory percentage). Populated when a faction is hovered/selected or when click-to-focus selects a system. Region-specific data deferred.
3. Works at all three zoom bands.

**Prove-it:** Test harness with 4 factions. Hover faction in list — others dim. Click — others nearly invisible. Click again — restore. Data panel shows correct info. Works at all zoom levels. Westley reviews.

⛔ STOP.

### Checkpoint F — Time-Jump Animation Dynamics

**Modified files:**
- `settled_reach_renderer.gd` — add smooth territory morphing (lerp shell from old to new state over `TERRITORY_MORPH_DURATION_SEC`). Add constellation fade-in/fade-out on connection changes.
- `time_jump_sequencer.gd` — add chronicle-linked focus (brighten system for current entry). Add ambient conflict flash cycling.
- `chronicle_scroll_panel.gd` — accept `faction_color` in entry data, pass to entries
- `chronicle_entry.gd` — tint text with `faction_color` when present

**Build:**
1. Territory morphing: on `territory_updated` or ownership change, shell renderer interpolates from old field state to new over `TERRITORY_MORPH_DURATION_SEC`. All simultaneous changes animate together.
2. Chronicle-linked focus: when `chronicle_entry` signal fires, sequencer resolves the entry's associated region (via `chronicle_entry_id` ↔ keyframe's `regions_snapshot`), calls `highlight_region()` or custom focus-brighten on that system. Subtle — emission boost, not spotlight.
3. Faction-colored scroll text: `chronicle_entry.gd` reads `faction_color` from entry data, applies as text color modulate. Null = default color.
4. Ambient conflict flashes: during time jumps, sequencer fires random low-intensity flashes at systems with active military events every `AMBIENT_FLASH_MIN/MAX_INTERVAL_SEC`. These are background texture, not scroll-synchronized.

**Prove-it:** Scripted fake time jump with 3 keyframes, ownership changes, entries with faction colors. Territory morphs smoothly (no snapping). Scroll text is faction-colored. Focal system brightens during its entry. Ambient flashes pulse in background. Westley reviews.

⛔ STOP.

### Checkpoint G — Integration with Live Pipeline

Wire to live Stage 10/11 pipeline. Play a full mission → time jump with real data. Verify:
- 3D constellation + shells render correctly with real faction data
- Zoom disclosure bands work during time jump (player can zoom/pan while auto-orbit runs)
- Territory morphs smoothly on real ownership changes
- Faction list hover/click works during and after time jump
- Chronicle focus highlight fires on real entries
- Performance acceptable

**Prove-it:** Westley plays one full cycle with the 3D territory system.

⛔ STOP.

### Checkpoint H — Performance Budget

60 FPS at 1920×1080 during busy time jump (10 keyframes, 8 factions, 40 regions, 60 connections, 3 simultaneous territory morphs). Shell raymarching ≤ 6ms total across all factions. Constellation ≤ 2ms. Zoom disclosure controller ≤ 0.1ms.

If raymarching exceeds budget, implement marching-cubes mesh fallback for shell rendering.

**Prove-it:** Profiler screenshot, numerical table.

⛔ STOP.

---

## Done Condition

Westley orbits the world view. Colored 3D shells wrap each faction's territory — at Overview they're opaque clouds, at Regional they're faint haze behind bright constellation webs, at Local they're barely visible. Constellation filaments arc between systems with traveling shimmer. Border glows spark where rival factions meet. The faction list panel shows all factions; hovering dims others, clicking isolates. Clicking a system zooms to Local and shows its neighborhood. During time jumps, territory morphs smoothly as factions expand and contract. The scroll prints faction-colored text while the referenced system subtly brightens. Ambient conflict flashes pulse across the galaxy. 60 FPS at 1920×1080.

Westley signs off before Stage 12.5 begins.

---

## Era-Agnostic Note

All new rendering components (constellation_renderer, shell_renderer, zoom_disclosure_controller, faction_list_panel, faction_data_panel) are instantiated by the SettledReachRenderer or the WorldViewShell — they are part of the Settled Reach era's world view, not the engine. Other space-themed eras (Mars, solar system, multi-system) can reuse these components. Non-space eras (Roman provinces, 1980s globe) will have entirely different renderers and may not use constellation/shell at all. The zoom disclosure controller is reusable by any era that wants band-based visual modulation. The faction list and data panels are era-agnostic UI — they read from WorldViewData and work with any renderer.

Sacred Design Principle #3 is preserved: no era-specific logic in the engine. The constellation + shell rendering is era-specific content living in the renderer layer, consumed through the standard WorldViewData signal interface.

---

## Key File Reference

| Purpose | Path |
|---------|------|
| World view shell | `scenes/shared/world_view/world_view_shell.gd` |
| World view data | `scenes/shared/world_view/world_view_data.gd` |
| Settled Reach renderer | `scenes/shared/world_view/renderers/settled_reach_renderer.gd` |
| Constellation renderer | `scenes/shared/world_view/renderers/constellation_renderer.gd` (NEW) |
| Shell renderer | `scenes/shared/world_view/renderers/shell_renderer.gd` (NEW) |
| Shell shader | `scenes/shared/world_view/renderers/shell_metaball.gdshader` (NEW) |
| Filament shader | `scenes/shared/world_view/renderers/constellation_filament.gdshader` (NEW) |
| Zoom controller | `scenes/shared/world_view/zoom_disclosure_controller.gd` (NEW) |
| Orbital camera | `scenes/shared/world_view/cameras/orbital_camera_3d.gd` |
| Faction list panel | `scenes/world/faction_list_panel.gd` (NEW) |
| Faction data panel | `scenes/world/faction_data_panel.gd` (NEW) |
| Chronicle scroll | `scenes/world/chronicle_scroll_panel.gd` |
| Chronicle entry | `scenes/world/chronicle_entry.gd` |
| Time jump sequencer | `scenes/world/time_jump_sequencer.gd` |
| Main menu galaxy | `scenes/shared/world_view/main_menu_galaxy.gd` (NEW — frozen copy, never modified) |
| World view renderer | `scenes/shared/world_view/world_view_structure.gd` (MODIFIED — world view only) |
| Config | `simulation/config.py` |
