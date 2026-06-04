# Bible Edits — Stages 11/12 Amendment Reconciliation

> **Purpose:** Edits to bible files required by the two amendments and by resolved design decisions that the hub roadmap hasn't caught up to yet. These should land alongside or shortly after the amendment implementations.

---

## 1. `game_bible.md` Hub — Implementation Roadmap

### 1a. Add Stage 8.5 entry (from era-agnostic amendment Part 5f)

**Insert between Stage 8 and Stage 9:**

> **Stage 8.5** — Era Theme Resolution and 3D Asset Integration. The era-agnostic rendering layer that makes Sacred Design Principle #3 real in the visual pipeline. `EraThemeResolver` autoload reads per-era JSON manifests mapping abstract engine types to 3D model paths, material configs, and display metadata. Tactical renderers retrofitted from Stage 8 placeholders to production 3D models. Faction colors applied at runtime to model face groups with per-tier treatment (matte/metallic/emissive). Squad rendering for Strike units. Settlement structure models (the single interactive tactical structure) produced and integrated. Environment object scatter from gradient sources. Proven era-agnostic by a test-era swap: changing one config string swaps the entire visual presentation with zero code changes.

### 1b. Update Stage 11 roadmap entry

**Replace the current Stage 11 entry with:**

> **Stage 11** — World View, Chronicle Scroll, and Seamless Transition. The macro-loop visual structure per `bible_world.md` (Galaxy View, Seamless Transition) and `bible_chronicle.md` (Chronicle Scroll). Mission end → camera pulls back → world view emerges → time jump executes with chronicle text printing → camera pushes into next region → next mission begins. One continuous flow, no loading screens. The world view uses the component architecture from `amendment_world_view_architecture.md`: `WorldViewShell` orchestrator, `WorldViewData` shared data store, per-era swappable renderers and cameras instanced via `setup_era()`. The Settled Reach renderer provides the first era's world view visuals (region nodes, territory bubbles with contoured borders, connections, military flashes). The main menu's decorative particle galaxy is a separate standalone scene. ZIP scope cuts: region tier visualization optional. Faction territory, connections, and military activity flashes all required.

### 1c. Update Stage 12 roadmap entry

**Replace the current Stage 12 entry with:**

> **Stage 12** — Loop Edges: Onboarding, Mission Debrief, Save Serialization, Bug Report Capture. Closes every open end of the game loop for the friends-ZIP build. Onboarding enhanced with archetype descriptions and expand/collapse accordion. Mission debrief inserted between tactical mission and pull-back — displays outcome band, objectives, force retention, 3D ribbon performance graphs, and simulation impact preview. Autosave wiring at three loop boundaries (post-debrief, post-narration, mid-mission quit) with single-slot, no-rewind semantics (open-ended runs, single autosave overwritten each time, restart is hard reset). Bug-report capture system with rolling 5-second tactical state buffer, command log, F12 hotkey, ZIP bundler, clipboard delivery for Discord. Tutorial fully omitted (deferred to commercial-launch scope).

### 1d. Add UI customization future note

**Append to the "Beyond Stage 13" paragraph:**

> UI layout customization: a settings mode where the player can reposition HUD elements (minimap, hotkeys bar, etc.), flip map orientation, and preview changes live within the settings screen. Scoped as post-launch polish.

---

## 2. `game_bible.md` Hub — "The Cycle" Step 2

### 2a. Fix intelligence quality reference (from era-agnostic amendment Part 5d)

**Current text (step 2):** "known enemy positions (based on intelligence quality)"

**Replace with:** "known enemy positions hidden by fog of war"

**Reason:** The bible never built an intelligence-quality system. Fog of war (sensor radius and sensor interference, implemented in Stage 6) handles enemy visibility. The "intelligence quality" phrase is vestigial.

---

## 3. `bible_monetization.md` — Structure Types

### 3a. Update production structure description (from era-agnostic amendment Part 5b)

**Current text (line 249):** "Production structure *types* are universal (barracks-equivalent, factory-equivalent, resource-equivalent)."

**Replace with:** "The production structure is a single universal type (the settlement — a population center). The *amount, placement rule, and production rate* per era are configurable."

**Reason:** The tactical map has one interactive structure type (the settlement, as implemented in Stage 7 and confirmed in Stage 8.5). The three-subtype model was never built and the single-type design is final.

---

## 4. `bible_world.md` — Tactical Map Structures

### 4a. Clarify settlement as single interactive structure (from era-agnostic amendment Part 5a)

**In the "Tactical Map Structures" section**, add a clarifying note:

> The single interactive structure type on the tactical map is the **settlement** (a population center that the player captures for unit production). Settlements have three tier variants matching the bible's three-tier visual progression. Other structure visual categories (Station, Military Installation, Resource Node) may persist as non-interactive visual dressing for spine node markers (objectives, staging areas) but are distinct from the capturable settlement. The settlement has its own silhouette archetype (compact, symmetric, clearly inhabited) distinct from all six unit silhouettes.

### 4b. Fix Recon Phase reference (from era-agnostic amendment Part 5d)

**In the hub's reference to step 2 ("Recon phase")**, if there is a standalone recon description in `bible_world.md`, correct "enemy positions based on intelligence quality" to "enemy positions hidden." Per Stage 6's fog-of-war implementation, enemy visibility is handled through sensor radius and sensor interference, not an intelligence-quality system.

---

## 5. `bible_combat.md` — Stage 7 Roadmap Description

### 5a. Verify macro behavior description (from era-agnostic amendment Part 5e / memory edits)

**Check:** The phrase "per-archetype enemy scripted behaviors (advance, defend, patrol, ambush, retreat)" should not appear in the Stage 7 roadmap description or anywhere in `bible_combat.md`. Enemy macro behavior uses a shared behavior script system with reactive hooks (5 base behaviors + 3 modifiers, timer/threshold/noise transitions, shared trigger bus), not per-archetype state machines.

**If still present:** Remove and replace with a reference to the shared behavior script system as described in the "Enemy Macro Behavior" section of `bible_combat.md`.

**Status:** This was flagged in memory edits and in the era-agnostic amendment. Verify it has landed. The `bible_combat.md` content I reviewed describes the correct shared-script architecture in the macro behavior section — the issue may be in a roadmap summary elsewhere in the file.

---

## 6. `bible_world.md` — Ambient Particle Field Reference

### 6a. Update galaxy scene reference for consistency

**Current text (line ~411):** "The particle structure is implemented as a reusable scene (`scenes/shared/galaxy/galaxy_structure.tscn`)"

**Replace path with:** `scenes/shared/world_view/world_view_structure.tscn`

**Also update:** "The same scene serves as the main menu background... and will serve as the galaxy view background" → "The scene serves as the main menu background (at 70% opacity with autonomous camera choreography). The world view between missions uses a separate component architecture (see `amendment_world_view_architecture.md`) with per-era swappable renderers — the main menu's particle galaxy and the world view are not the same scene."

**Reason:** The world view amendment established that the main menu galaxy and the in-game world view are architecturally separate. The bible's description of a shared reusable scene is now incorrect.

---

## Edit Verification Checklist

After all edits land, verify:

- [ ] `game_bible.md` hub roadmap includes Stage 8.5 between 8 and 9
- [ ] Stage 11 roadmap entry references world view shell architecture, not monolithic galaxy scene
- [ ] Stage 12 roadmap entry reflects resolved session-length (open-ended, single autosave, no rewind) and bug report system
- [ ] "Beyond Stage 13" includes UI customization note
- [ ] "The Cycle" step 2 says "hidden by fog of war" not "based on intelligence quality"
- [ ] `bible_monetization.md` references single settlement type, not three subtypes
- [ ] `bible_world.md` clarifies settlement as the single interactive structure
- [ ] `bible_world.md` ambient particle field section reflects the main-menu / world-view separation
- [ ] `bible_combat.md` has no vestigial "per-archetype enemy scripted behaviors" text
- [ ] `grep -r "galaxy_structure\|system_node\|highlight_system" bible_*.md game_bible.md` returns only historically accurate references (e.g., in archived version notes), not active design descriptions
