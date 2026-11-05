# A3 — Map Cover Audit (read-only)

Date: 2026-05-20

## Map generator entry points

- `simulation/map_generator.py:21` — `generate_map(generator_input, layout_library)` is the single tactical-map entry point. Picks a layout via `archetype_filters.matching_layouts`, instantiates it, then layers gradients + masks.
- `simulation/archetype_filters.py:233` — `ARCHETYPE_FILTERS` decides which layout JSONs are compatible with a given archetype.
- `simulation/gradient_placer.py:25` — `place_gradients(inst)` is the only place `cover_density` sources are emitted on the tactical map.
- `simulation/layer_masks.py:23` — `place_layer_masks(inst)` emits layer-block sources (height/blocking), not cover.
- `simulation/layout_library/layout_0[1-8]_*.json` — 8 hand-authored layouts. Each is a spine of typed zones (`staging`, `chokepoint`, `flank_route`, `vantage`, `hazard_zone_anchor`, `objective`, `spawn_point`, `transit`, `reinforcement_structure`) plus typed edges.
- `simulation/pipe_transport.py:394` — runtime entry. Wraps `generate_map` in `try/except`; on any failure (including unknown archetype) builds an EMPTY `TacticalMap(width=4000, height=4000, layers=1, spine_nodes=[], gradient_sources=[])`.
- `scenes/tactical/terrain_renderer.gd:217` — Godot-side scatter. Only `obstacle_density` sources scatter real props. Cover-density and sensor-interference are listed as "placeholder assets — skip until real GLBs exist." Visual cover is currently a red gradient tint with NO meshes spawned.

## Cover model (how it works today)

Cover on the tactical map is purely a **continuous scalar field** (`cover_density: 0.0–1.0`) sampled at any (x,y). It only exists where a gradient source emits it. Two source types emit cover today:

- `staging` zones → `cover_density` radius 800, intensity 0.60 (defensible entry area)
- `flank_route` zones → `cover_density` radius 450, intensity 0.40 (mild concealment)

That is the entire cover surface. No other zone type contributes cover. There are no discrete cover props on the sim side — units sample `tmap.cover_density(x,y)` and `combat.damage_per_attack` multiplies by `(1 - cover_density)` (per `docs/bible_history/bible_2_00_combat.md:421`). On the Godot side, even the `obstacle_density` field is the only thing that gets visible meshes; cover is currently invisible.

## Per-archetype findings

Cover today = which gradient sources will actually be emitted for layouts compatible with this archetype. "Layouts" = the `tags`-matching subset of the 8 hand-authored JSONs.

| archetype | map gen function | cover today? | cover kind | seed source | recommendation |
|---|---|---|---|---|---|
| defensive_stand | `generate_map` → layouts 01, 04, 05 | Y | staging blob + 1 flank blob (layout 01) or alley flank (04) or inland flank (05); no cover near objective/chokepoints | seeded; deterministic per mission via `setup.map_params.seed` | add cover gradient to `chokepoint` + `objective` zones — bible says "prepared positions with cover" near defended ground; today the defender's own line has no cover |
| siege_breaking | `generate_map` → **NO layout tagged `siege_breaking`** → `ValueError` → empty 4000x4000 map | N | none — empty open field fallback at runtime | n/a, generator crashes before seeding | author at least one siege layout (besiegers' rings + fortified core); cover on the fortified core; until then this archetype ships broken |
| reconquest | `generate_map` → **NO layout tagged `reconquest`** → `ValueError` → empty 4000x4000 map | N | none — empty open field fallback at runtime | n/a, generator crashes before seeding | author reconquest layouts (former-friendly infra, partial fortification); add `damaged_infrastructure` zone type with mid cover; until then ships broken |
| assault | `generate_map` → layouts 01, 02, 04, 05, 06 | partial | staging blob (player rear) + flank cover; defender side has NO cover even though bible says "prepared positions, fortified chokepoints, established infrastructure" | seeded; deterministic per mission | add `cover_density` emission at `chokepoint` and `objective` zones so the defender's fortified line actually has cover; tune so attacker's open approach feels exposed |
| suppression | `generate_map` → **NO layout tagged `suppression`** → `ValueError` → empty 4000x4000 map | N | none — empty open field fallback at runtime | n/a, generator crashes before seeding | author suppression layouts (revolted territory, damaged infra, dispersed positions); scattered low-cover patches; until then ships broken |
| multi_front_defense | `generate_map` → layouts 03, 08 | N | NONE — layouts 03 and 08 have ZERO `staging` cover blob within useful range of the fight (staging is central, fronts radiate); no `flank_route` zones at all | seeded; deterministic per mission | add cover to chokepoints on each front (bible: "defensive infrastructure radiating outward"); this archetype currently has the worst cover coverage of all defended archetypes |
| interception | `generate_map` → **NO filter defined in `ARCHETYPE_FILTERS`** → `KeyError` → empty 4000x4000 map | N | none — empty open field fallback at runtime | n/a, generator crashes before seeding | bible explicitly says "Open terrain… Terrain features provide tactical options (cover, elevation, sensor interference) but neither side has fortifications." Author a layout with sparse `vantage` + sparse cover patches; no fortifications |
| evacuation | `generate_map` → **NO filter defined in `ARCHETYPE_FILTERS`** → `KeyError` → empty 4000x4000 map | N | none — empty open field fallback at runtime | n/a, generator crashes before seeding | author evacuation layouts (defensive perimeter + extraction points at rear); cover at fallback positions; until then ships broken |
| containment | `generate_map` → **NO filter defined in `ARCHETYPE_FILTERS`** → `KeyError` → empty 4000x4000 map | N | none — empty open field fallback at runtime | n/a, generator crashes before seeding | bible: "Terrain features create natural defensive positions but with gaps between them." Author wide-front layouts with chokepoints + cover at each; until then ships broken |
| counterinsurgency | `generate_map` → layout 07 only | N | layout 07 has staging cover blob but ZERO `flank_route` zones; all other zones are `hazard_zone_anchor` (sensor interference, not cover) and `transit` (no gradient) | seeded; deterministic per mission | bible: "Insurgent forces are initially hidden — scattered across the map in sensor interference zones, behind cover, in defensible pockets." Add `cover_density` emission at `hazard_zone_anchor` zones for counterinsurgency, OR add a new `cover_pocket` zone type and seed several per layout. This is the archetype whose B2/B3 copy promised cover most loudly. |

## Bible directives found

- `docs/bible_history/bible_2_00_missions.md:74` (defensive_stand): "Defensible terrain. Chokepoints between enemy approach vectors and the objective. Prepared positions with cover. Multiple approach routes so the player must choose where to concentrate defense."
- `docs/bible_history/bible_2_00_missions.md:137` (assault): "Enemy territory. The defender has prepared positions, fortified chokepoints, established infrastructure."
- `docs/bible_history/bible_2_00_missions.md:179` (multi_front_defense): "Multiple enemy approach vectors from different directions. The player's position is central with defensive infrastructure radiating outward."
- `docs/bible_history/bible_2_00_missions.md:200` (interception): "Open terrain. No prepared positions for either side… Terrain features provide tactical options (cover, elevation, sensor interference) but neither side has fortifications."
- `docs/bible_history/bible_2_00_missions.md:221` (evacuation): "Collapsing perimeter. The player starts in a defensive position with evacuation points behind them and enemy forces approaching from the front."
- `docs/bible_history/bible_2_00_missions.md:242` (containment): "Terrain features create natural defensive positions but with gaps between them."
- `docs/bible_history/bible_2_00_missions.md:263` (counterinsurgency): "Insurgent forces are initially hidden — scattered across the map in sensor interference zones, behind cover, in defensible pockets… Destroying infrastructure (objectives, cover positions) is mechanically possible but counterproductive."
- `docs/bible_history/bible_2_00_combat.md:421`: damage formula uses `(1.0 - cover_density_at_position)` — so cover already has mechanical bite; the only missing piece is map generation actually placing it.
- `docs/bible_history/bible_2_00_combat.md:578` (ambush state): "hold at a hidden position (ideally in a sensor interference zone or behind cover)" — enemy AI also assumes cover exists.

## Cross-archetype patterns

All maps go through one generator (`generate_map`) and one cover-source emitter (`place_gradients`). Cover today comes from exactly two zone types: `staging` (player rear, big blob) and `flank_route` (mild flank concealment). That means cover is co-located with the player's spawn area or with the flank — never with the defender's line, the objective, urban blocks, hazard zones, or chokepoints. Four of the ten bible archetypes have NO map gen path at all (`siege_breaking`, `reconquest`, `suppression` have no layouts tagged for them; `interception`, `evacuation`, `containment` have no filter entry) and silently fall back to a completely empty 4000x4000 field with zero spine nodes. The gap to "every map has cover" is therefore two-fold: (1) cover gradient placement is too narrow on the six archetypes that DO generate (only staging + flank), and (2) four-to-six archetypes ship as empty fields because their plumbing is missing. The Godot side also does not yet render cover meshes — `cover_density` is invisible until terrain_renderer.gd gets real cover GLBs wired into `PROPERTY_CATEGORIES`.

## Recommended Phase 1 scope (agent's lean — Westley decides)

- **Option A (narrow, fast):** Extend `place_gradients` to emit a `cover_density` source at `chokepoint`, `objective`, and `hazard_zone_anchor` zones with tuned radius/intensity per archetype. No new layouts, no new zone types. Existing 6 archetypes immediately get plausible cover; the 4 broken archetypes still ship as empty fields.
- **Option B (medium, recommended):** Option A + author the 4 missing archetype filter entries (interception, evacuation, containment in `ARCHETYPE_FILTERS`; layouts tagged for siege_breaking, reconquest, suppression). Each can reuse existing layouts as a stopgap by adding tags. Closes the empty-field fallback for all 10 archetypes.
- **Option C (long-term-correct):** Option B + (a) new zone type `cover_pocket` for discrete cover placement, (b) Godot-side cover GLB wiring so cover is visible, (c) one purpose-authored layout per archetype that doesn't have one. Most aligned with the B2/B3 marketing copy ("every building, every patch of cover") but largest scope.

## Files to edit if Westley picks any option above

- `simulation/gradient_placer.py` — Options A/B/C: add `cover_density` emission for `chokepoint`, `objective`, `hazard_zone_anchor` (and `cover_pocket` for C).
- `simulation/config.py` — Options A/B/C: add new `GRADIENT_*_RADIUS` and `GRADIENT_*_INTENSITY` constants for any newly cover-emitting zone type.
- `simulation/archetype_filters.py` — Options B/C: add real `ARCHETYPE_FILTERS` entries for `interception`, `evacuation`, `containment` (and remove or rename the stub `raid`/`rear_guard` entries that don't match the canonical 10). Also add `BASELINE_OWNERSHIP` rows.
- `simulation/layout_library/*.json` — Options B/C: add archetype tags so existing layouts cover the 4 currently-broken archetypes; Option C also authors purpose-built JSONs.
- `simulation/map_gen_contracts.py` — Option C: if a new zone type `cover_pocket` is introduced, may need to register it as a recognized `node_type`.
- `simulation/pipe_transport.py:397-399` — Options B/C: tighten the silent fallback so an unknown archetype crashes loudly during dev instead of producing an empty map.
- `scenes/tactical/terrain_renderer.gd:217-220` — Option C only: extend `PROPERTY_CATEGORIES` so `cover_density` actually scatters cover meshes; requires cover GLB assets in the manifest.
- `simulation/fairness_evaluator.py` — Options B/C: confirm the hazard/vantage ratio metrics still pass for the newly-tagged or newly-authored layouts; may need fairness profile retune.
