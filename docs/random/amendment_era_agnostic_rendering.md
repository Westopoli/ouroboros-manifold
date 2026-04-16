# Amendment — Era-Agnostic Rendering Architecture

> **Type:** Cross-cutting architectural amendment
> **Affects:** Stage 8 (renderer retrofit), Stage 9 (UI era-awareness audit), Stage 10 (era config from backend), Stage 11 (world view already handled by `amendment_world_view_architecture.md`)
> **Priority:** Must be completed before any further stage implementation proceeds. This amendment and Stage 8.5 together close the era-agnostic gap in the rendering pipeline.
> **Status:** OPEN
> **Companion:** This amendment defines the architectural mandate and the cross-stage audit. `stage_8_5_spec.md` defines the full implementation (resolver, manifest, renderer retrofit, asset integration, checkpoints, invariants). CC reads both documents.

---

## Problem Statement

An audit of Stages 7–11 against Sacred Design Principle #3 (era-agnostic architecture — the revenue principle) revealed that the rendering pipeline has no era-abstraction layer. The tactical engine, simulation, map generator, mission generator, and chronicle distiller are all era-blind — they emit abstract types (`"vanguard"`, `"reinforcement_structure"`, `"obstacle_density"`). But the Godot rendering layer that consumes those abstract types has no mechanism to resolve them into era-specific visuals. There is no theme resolver, no era manifest, no abstract-type-to-asset mapping.

**Specific violations found:**

1. **`unit_renderer.gd` (Stage 8)** — draws all units as colored circles. Does not read unit `type` or `tier` from the engine snapshot. When replaced with 3D models, there is no architecture preventing hardcoded Settled Reach asset paths.

2. **`terrain_renderer.gd` (Stage 8)** — draws all structures and terrain as colored circles. Same problem — no resolver, no manifest, no abstraction between "the engine says there's a reinforcement structure here" and "load this specific GLB."

3. **No era manifest schema exists.** The bible describes era packs as "JSON content libraries plus 3D assets" (`bible_monetization.md` §"Era Pack Delivery") but no stage spec defines the manifest format, the directory structure, or the loading mechanism.

4. **No faction color runtime system.** The bible specifies that faction colors are applied at runtime to `faction_color` face groups on models, with per-tier treatment (matte T1 → metallic T2 → emissive T3). No stage spec implements this. `unit_renderer.gd` uses hardcoded `FACTION_COLORS` constants applied as circle fill.

5. **No tier material system.** The bible's `bible_ai_pipeline.md` specifies exact material values per tier (hex colors, metallic, roughness, emission). No stage spec applies these from config — they would need to be hardcoded per model or per era without the resolver.

6. **Squad rendering not era-agnostic.** The bible says Strike units render as 3–5 models in formation, with the count as a visual-only property. No mechanism exists to make squad count era-configurable (different eras might use different squad sizes).

7. **Structure type consolidation needed.** The bible references three structure visual categories (Station, Military Installation, Resource Node) in `bible_world.md` and three production structure subtypes (barracks-equivalent, factory-equivalent, resource-equivalent) in `bible_monetization.md`. The actual implementation has one interactive structure type (`reinforcement_structure` spine node in Stage 7). The bible text needs updating to reflect the resolved design: one settlement structure type, three tier variants, era-skinned.

**The world view (galaxy/strategic layer) is handled separately** by `amendment_world_view_architecture.md`, which addresses the same era-agnostic concern for the between-missions visual layer. This amendment covers the tactical layer (in-mission rendering) and the cross-stage coordination.

---

## Solution: Era Theme Resolver + Stage 8.5

The solution has two parts:

1. **Stage 8.5** (full stage spec, see `stage_8_5_spec.md`) — implements the `EraThemeResolver` autoload, the per-era JSON manifest, the renderer retrofit, 3D asset integration, faction color system, tier materials, squad rendering, settlement structure models, and environment scatter. Stage 8.5 has its own checkpoints and invariants, including the critical Checkpoint G (test-era swap proving era-agnostic architecture with zero code changes).

2. **This amendment** — specifies the cross-stage implications that Stage 8.5 alone doesn't cover. Specifically: what changes in Stages 8, 9, 10, and 11's specs, what bible edits are needed, and what the ongoing era-agnostic verification discipline looks like.

---

## Part 1 — Stage 8 Spec Amendments

Stage 8 is fully built / nearly complete. The following changes are retroactive acknowledgments, not implementation tasks (Stage 8.5 does the actual work):

1. **Stage 8 "What to Build" → `unit_renderer.gd` description** — add a note: "Stage 8 ships with placeholder 2D circles. Stage 8.5 retrofits this file to consume 3D models through an era-agnostic resolver. The placeholder rendering is intentional for Stage 8's scope — it proves the WebSocket bridge and command interface work without blocking on 3D assets."

2. **Stage 8 "What to Build" → `terrain_renderer.gd` description** — same note.

3. **Stage 8 "Integration Points" section** — add: "Stage 8.5 handoff: `unit_renderer.gd` and `terrain_renderer.gd` are retrofitted in Stage 8.5 to replace 2D placeholder rendering with 3D models loaded through `EraThemeResolver`. The bridge protocol (`TacticalBridge` snapshots/deltas) is unchanged — Stage 8.5 is purely a renderer-side change."

4. **Stage 8 "Done Condition"** — no change. Stage 8's done condition is met with placeholders. The 3D asset integration is Stage 8.5's done condition.

---

## Part 2 — Stage 9 Spec Amendments

Stage 9 has era awareness in two places that need auditing:

### 2a. `ThemeConstants` era accent colors

**Current:** `ThemeConstants.gd` has a hardcoded dictionary mapping era IDs to accent colors:
```gdscript
"roman" → #c9a84c
"settled_reach" → #4a9eb8
"1980s" → #8b9a3c
```

**Problem:** This is hardcoded era data in application code. Adding a new era requires editing `ThemeConstants.gd`.

**Fix:** `ThemeConstants` should read era accent colors from the era manifest (via `EraThemeResolver.get_era_display()`) rather than maintaining its own hardcoded dictionary. The resolver's manifest already contains `era_accent_color`. `ThemeConstants.get_era_accent(era_id)` becomes a passthrough to the resolver.

**Implementation note:** This is a small change — replace the dictionary lookup with a resolver call. The fallback (neutral gray for unknown eras) is preserved. Stage 9's existing screens don't change — they still call `ThemeConstants.get_era_accent()`, they just don't know the data source changed behind it.

**Priority:** Low. The hardcoded dictionary works for the friends-ZIP build. This is tech debt, not a blocker. Flag it for cleanup when convenient.

### 2b. `UIDataBus` era data

**Current:** `UIDataBus.get_all_eras()` and `get_era_detail()` return mock data with hardcoded era metadata (name, description, unit roster with era-specific display names).

**Problem:** In mock mode, this is fine — it's intentionally fake. In live mode (Stage 10), this data needs to come from the era manifest or the backend. The question is whether `UIDataBus` should read era metadata from the resolver's manifest (keeping it consistent with the tactical renderer's era data) or from a separate backend endpoint.

**Fix:** When `USE_LIVE_SIM = true`, `UIDataBus.get_era_detail(era_id)` should incorporate data from `EraThemeResolver`'s manifest for the fields the manifest covers (accent color, unit roster with abstract types). Era-specific display names (e.g., "Legionary" for Roman Vanguard) live in the manifest's unit entries as an optional `display_name` field — added to the manifest schema in Stage 8.5 or a follow-up. Fields the manifest doesn't cover (description prose, sample chronicle text, marketing copy) come from the backend or a separate era metadata file.

**Priority:** Medium. Needed before multi-era support ships. Not needed for the friends-ZIP build (single era, mock data).

---

## Part 3 — Stage 10 Spec Amendments

### 3a. Era config from backend

**Current (Stage 8.5):** `EraConfig.ACTIVE_ERA_ID` is a hardcoded constant.

**Stage 10 change:** When the sim bridge connects, the active era ID comes from the save file / sim state (which era the player's current campaign is using). `EraConfig.ACTIVE_ERA_ID` is replaced by a value read from the sim's initial state message.

**Implementation:** `SimBridgeDataSource` reads the era ID from the sim's `ready` or first `sim_state` message and writes it to `EraConfig`. `EraThemeResolver` reads it during `_ready()`. The resolver's `_ready()` must run after the bridge has received the era ID — either by deferring resolver initialization until the bridge is ready, or by having the resolver listen for a `sim_ready` signal and loading the manifest at that point.

**Priority:** Required for Stage 10. The friends-ZIP build hardcodes Settled Reach, but the architecture must support the value coming from the backend.

### 3b. Era asset delivery

**Current:** Assets live in `res://assets/eras/settled_reach/` as part of the Godot project.

**Future (beyond friends-ZIP):** Era packs are downloaded from Cloudflare R2 on purchase per `bible_monetization.md` §"Era Pack Delivery." Downloaded era packs are unpacked into a local content directory. The resolver needs to load assets from both the bundled `res://` path (for the base era) and a user-writable `user://` path (for downloaded eras).

**Implementation note:** This is beyond Stage 10's scope but the resolver's path-resolution logic should not hard-assume `res://` — it should support a configurable base path per era. Stage 8.5 can ship with `res://` only; the path configurability is a one-line change when download-based delivery lands.

**Priority:** Post-friends-ZIP. Note it here so the resolver doesn't paint itself into a corner.

---

## Part 4 — Stage 11 Spec Amendments

Stage 11's world view era-agnosticism is fully covered by `amendment_world_view_architecture.md`. No additional changes from this amendment.

The two amendments are complementary:
- `amendment_world_view_architecture.md` — world view (between missions): shell + data + per-era renderer + per-era camera.
- This amendment + `stage_8_5_spec.md` — tactical view (during missions): `EraThemeResolver` + manifest + per-era 3D assets.

Together they close the era-agnostic gap across the entire visual pipeline.

---

## Part 5 — Bible Edits Required

These edits resolve inconsistencies surfaced during the audit. They should land alongside Stage 8.5 implementation:

### 5a. `bible_world.md` — Tactical Map Structures

**Current:** The "Tactical Map Structures — Sci-Fi Theme Pack Assets" section describes three point-of-interest structure types with tier variants: Station, Military Installation, Resource Node.

**Edit:** Clarify that the single interactive structure type on the tactical map is the **settlement** (a population center that the player captures for unit production). Stations, Military Installations, and Resource Nodes may persist as non-interactive visual dressing for other spine node types (objectives, staging areas, etc.) but are distinct from the capturable settlement. The settlement has its own silhouette archetype (compact, symmetric, clearly inhabited) distinct from all six unit silhouettes.

### 5b. `bible_monetization.md` — Structure Types

**Current (line 249):** "Production structure *types* are universal (barracks-equivalent, factory-equivalent, resource-equivalent)."

**Edit:** Update to: "The production structure is a single universal type (the settlement — a population center). The *amount, placement rule, and production rate* per era are configurable." Remove the three-subtype parenthetical.

### 5c. `bible_ai_pipeline.md` — Asset Manifest

**Current:** Lists "3 types × 3 tiers = 9" for point-of-interest structures per era.

**Edit:** Update to "1 type × 3 tiers = 3 settlement models" per era. Update total asset count accordingly. Add a note that non-interactive structure visuals (stations, installations) are environment dressing shared with spine node markers, not separate production assets.

### 5d. `bible_world.md` — Recon Phase

**Current (hub "The Cycle" step 2):** "enemy positions based on intelligence quality."

**Edit:** Correct to "enemy positions hidden." Per Stage 8 Bible Capture Pending item #7 — the bible never built an intelligence-quality system. Fog of war (implemented in Stage 6) handles enemy visibility through sensor radius and sensor interference.

### 5e. `bible_combat.md` — Stage 7 Roadmap Description

**Current (from memory edits):** "Remove 'per-archetype enemy scripted behaviors (advance, defend, patrol, ambush, retreat)' from Stage 7 roadmap description."

**Edit:** Already flagged in memory. Confirm this edit has landed. Enemy macro behavior uses a shared behavior script system with reactive hooks, not per-archetype state machines.

### 5f. `game_bible.md` Hub — Implementation Roadmap

**Edit:** Add Stage 8.5 entry between Stage 8 and Stage 9: "**Stage 8.5** — Era Theme Resolution and 3D Asset Integration. The era-agnostic rendering layer that makes Sacred Design Principle #3 real in the visual pipeline. `EraThemeResolver` autoload reads per-era JSON manifests mapping abstract engine types to 3D model paths, material configs, and display metadata. Tactical renderers retrofitted from Stage 8 placeholders to production 3D models. Faction colors applied at runtime to model face groups with per-tier treatment (matte/metallic/emissive). Squad rendering for Strike units. Settlement structure models (the single interactive tactical structure) produced and integrated. Environment object scatter from gradient sources. Proven era-agnostic by a test-era swap: changing one config string swaps the entire visual presentation with zero code changes."

---

## Part 6 — Ongoing Era-Agnostic Verification Discipline

To prevent future stages from introducing era-specific assumptions, the following discipline applies to all stages from 8.5 onward:

### Invariant checks for every future stage

Any stage that modifies rendering code, UI code, or adds visual content must include in its invariant list:

> **I-ERA — Era-agnostic rendering.** `git grep` for era-specific strings (`"settled_reach"`, `"SetReach"`, `"roman"`, `"1980s"`, any era name or era-specific asset name) in all `.gd` files outside of `era_config.gd`, manifest JSONs, and `amendment_*.md` / `stage_*_spec.md` documentation returns zero hits. Era identity enters the codebase through `EraConfig.ACTIVE_ERA_ID` and exits through `EraThemeResolver` and the world view shell's `setup_era()`. No other code path is permitted to reference era identity.

### Code review rule

CC sessions modifying visual code must run the grep check before declaring a checkpoint passed. If an era-specific string appears in a non-config, non-manifest file, the checkpoint fails regardless of whether the feature works.

### Manifest-first rule

When adding new visual content types (new unit abilities with VFX, new structure types, new environment categories), the abstract type must be added to the manifest schema first, then consumed through the resolver. Direct asset path references in `.gd` files are a violation of I-ERA.

---

## Relationship to Stage 8.5

This amendment document is the "why and what changes across stages." `stage_8_5_spec.md` is the "how to build the solution." CC reads both:

- **This amendment** tells CC: the rendering pipeline has an era-agnostic gap, here's what's wrong in each stage, here are the bible edits, here's the ongoing discipline.
- **`stage_8_5_spec.md`** tells CC: build the resolver, retrofit the renderers, integrate the assets, prove it with checkpoints, pass the invariants.

When Stage 8.5 is complete and the bible edits from Part 5 have landed, this amendment can be archived. The ongoing discipline (Part 6) transfers into `dev_rules.md` as a permanent rule.
