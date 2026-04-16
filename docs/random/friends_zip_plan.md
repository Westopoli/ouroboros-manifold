# Friends-ZIP Playtest Plan — Stage Roadmap Integration

## Context

The decision: distribute a rough build of *Ouroboros Manifold* as a ZIP file to a small group of personally-known playtesters before any public Steam beta. This deliverable is **not the commercial product** — it is a private feedback artifact for people the developer trusts.

This document integrates the ZIP deliverable into the existing bible roadmap (`game_bible.md` → Implementation Stage Roadmap) and identifies the new stages required to support it.

## What the ZIP build is and is not

**Is:**
- The Settled Reach era, playable end-to-end through at least one full mission → time jump → mission cycle
- Distributed as a Godot export ZIP (Windows initially; Mac/Linux follow if trivial)
- Aimed at playtesters who will provide qualitative feedback verbally or in writing
- A bounded scope build intended to validate the core fantasy

**Is not:**
- A Steam release (no Steam SDK, no Steamworks, no store page work)
- A free public product (no monetization, no entitlement, no webapp)
- A polished product (no tutorial, minimal sound, expected rough edges)
- A long-term distribution channel (build is retired when public beta begins)

**Bible conflict status: NONE.** Settled Reach remains premium content per `bible_monetization.md`. A privately-distributed pre-launch playtest does not contradict the commercial model — it is a development tool, not a product.

## Session length scope — UNRESOLVED

Pending decision (carried forward from planning conversation): bounded ~3 chapters / 2-3 hours, bounded but generous ~5 chapters / 4-6 hours, fully open-ended, or bounded by faction collapse only. **This decision affects save serialization scope** (ZIP-S2) and onboarding stub content (ZIP-S1). Resolve before writing the ZIP-S2 spec.

## Existing stages — status as of planning

This section reflects current implementation state and where each stage sits relative to the ZIP deliverable. Stages must be stable before the ZIP build can incorporate them.

**Stages 1–4 — Simulation backbone.** Status: complete and stable per project memory. ZIP-blocking: no.

**Stage 5 — Chronicle pipeline, coherence ledger, library builder, naming.** Status: complete through Checkpoint I per project memory. ZIP-blocking: no.

**Stage 5.5 — Mission generation pipeline.** Status: in active flux. Per project memory, currently in Checkpoint H (invariant validation suite M1–M19 across scenarios 12–16). ZIP-blocking: yes — must complete remaining checkpoints before ZIP build is feasible.

**Stage 6 — Tactical simulation engine (headless).** Status: Checkpoints A–I pass. Checkpoint J in progress with two failing sub-claims (L1 Strike-vs-Siege, L4 flank gradient). Checkpoints K (performance) and L (final invariants) not started. ZIP-blocking: yes — combat must be stable. Realistic completion estimate is several focused sessions on the J stat rebalance, then K + L.

**Stage 7 — Map generation and tactical reinforcement.** Status: spec exists, implementation not started per planning conversation. ZIP-blocking: yes — without this, missions have no map.

**Stage 7.5 — Enemy macro behavior scripts.** Status: not started. ZIP-blocking: yes — without this, enemies have no coherent behavior, missions are not playable.

**Stage 8 — Godot renderer, command interface, game state persistence.** Status: not started. ZIP-blocking: yes — this is where the game becomes playable. Largest single stage in the bible. Includes WebSocket bridge, hybrid state sync, command input system, vertical layer rendering, simulation/tactical/onboarding persistence, and the recon phase.

**Stage 9 — UI Shell.** Status: complete with mock data per project memory. ZIP-blocking: partial — the screens exist but consume mock data through `UIDataBus`. Backend integration is required before the ZIP build.

## New stages required for ZIP delivery

Three new stages follow Stage 9. Stage numbering continues the existing convention; these can be renumbered if conflicts emerge with in-flight work.

---

### Stage 10 — Backend Integration (UIDataBus → Live Python Sim)

**Goal.** Replace the Stage 9 `UIDataBus` mock data layer with a real WebSocket bridge to the Python simulation. Every Stage 9 screen that currently reads from hardcoded mock data instead reads from live simulation state. The seam is preserved — only the bus implementation changes.

**Bible references.** `bible_simulation.md` (What the Simulation Provides to Missions), `stage_8_spec.md` (WebSocket protocol — same channel reused), `stage_9_spec.md` (UIDataBus contract).

**What to build.**
- Reuse Stage 8's WebSocket protocol — Stage 9 screens connect to the same Python sim server
- Bus methods that previously returned hardcoded data now issue WebSocket queries
- Connection lifecycle handling: sim launch on game start, sim teardown on quit
- Loading states for every screen that fetches data (mock data was synchronous; real data is async)
- Error states for every screen if the sim is unreachable (ZIP build runs sim locally as a subprocess; failure modes exist)

**Done condition.** All Stage 9 done-condition screens render correctly using live simulation data. Save slot creation persists to disk through the sim. Era Library reflects actual entitlement state (in ZIP build, hardcoded to "Settled Reach owned"). Mission Briefing pulls real generated mission data from Stage 5.5.

**Why before Stage 11.** Galaxy view and chronicle scroll consume live simulation data; building them on top of mock data is wasted work.

---

### Stage 11 — Galaxy View, Chronicle Scroll, and Seamless Transition

**Goal.** Build the macro-loop visual structure. The mission → galaxy view → next mission transition is one continuous camera movement per `bible_world.md` ("Seamless Transition — No Loading Screens"). The chronicle scroll prints during the time jump. This stage delivers the generational fantasy as a visible, playable thing.

**Bible references.** `bible_world.md` (Sci-Fi Era → Galaxy View, Seamless Transition), `bible_chronicle.md` (Chronicle Scroll — Visual Presentation, Distiller Algorithm), `bible_simulation.md` (Time Jump Controller — already implemented, this stage visualizes its output).

**What to build.**
- Galaxy view scene: 3D star map of the Settled Reach, system nodes, faction territory volumes, connection lines, military activity flashes, ambient particle field. The reusable particle scene (`scenes/shared/galaxy/galaxy_structure.tscn`) already exists from main menu work — extend its public API for the world-view methods that were stubbed
- Chronicle scroll UI: text printing surface alongside the galaxy view during time jumps, consuming distilled chronicle output
- Camera transition: tactical-end → pull back → galaxy emerges → time jump runs → camera pushes into next mission system → tactical materializes
- Time jump pacing: galaxy orbits slowly, faction colors shift, scroll prints in time with the camera

**Done condition.** Player completes a mission, the camera pulls back into galaxy view, the time jump executes with chronicle text printing, the camera pushes into the next system, the next mission begins. No loading screens, no abrupt scene changes. Sequence is one continuous flow.

**Why this is required.** Without it, the game ends after one mission and never demonstrates the generational structure — i.e. the entire reason the game exists.

**Scope cut acceptable for ZIP build.** The bible specifies system tier visualization and military activity flashes as part of galaxy view. For the ZIP, system nodes can render as undifferentiated points and military flashes can be omitted. Faction territory and connections are required because they are how the player reads the strategic state.

---

### Stage 12 — Loop Edges (Onboarding Stub, Mission Debrief, Save Serialization)

**Goal.** Close the three open ends of the game loop. These are scoped down from the full bible specifications because the ZIP build is bounded, but each must exist in some form for the loop to be coherent.

**Bible references.** `game_bible.md` (Onboarding and First Chapter), `bible_missions.md` (Mission Outcome Resolver — what the debrief screen displays), `bible_simulation.md` (state persistence — the simulation already has the data, this stage serializes it).

**What to build.**

*Onboarding stub.* Single screen, minimal: difficulty setting, mission preference weights (10 archetypes, up to 2 markable as rare per bible). After confirmation, opening time jump runs (20–50 years, abbreviated 3–5 entry chronicle scroll). This is the bible's `Onboarding and First Chapter` design with no additional polish. **Skip the controls overlay** — the controls card per planning conversation will live in the main game HUD as a togglable overlay built into Stage 8.

*Mission debrief.* Single screen: outcome band, key events from the mission (drawn from existing chronicle pipeline output), continue button. Triggers the time jump → galaxy view sequence in Stage 11.

*Save serialization.* Real disk persistence replacing Stage 9's in-memory mock save slots. Scope depends on session-length resolution above:
- If bounded (3 or 5 chapters): single autosave per slot, no manual saves, no rewind. Scope is small.
- If open-ended or faction-collapse: bible's full Stage 8 persistence design applies, including rewind-with-re-seed and forked slots. Scope is much larger.

**Done condition.** New game flows through onboarding, opening time jump, first mission, mission debrief, time jump, second mission. Quitting and relaunching loads the save slot at the correct point. The game has a complete loop with real edges, not stubs.

**Scope cut acceptable for ZIP build.** Tutorial is fully omitted (per planning conversation). Multi-stage tutorial across hallmark eras (`bible_monetization.md` v3.00 component 8) is launch-feature scope, not ZIP scope. Bible's "controls overlay" is a Stage 8 HUD addition, not a separate onboarding screen.

---

### Stage 13 — ZIP Build, Bundling, and Distribution Hygiene

**Goal.** Produce a self-contained Windows ZIP that a friend can extract and run. Address the gap between "works on the developer's machine" and "works on a cold install." Establish a minimal feedback collection mechanism appropriate for private distribution.

**Bible references.** None — this stage covers operational concerns the bible does not address. No new bible content required.

**What to build.**

*Build pipeline.* Godot export configuration for Windows release build (Mac/Linux follow-on if trivial). Python sim must run as a bundled subprocess — the ZIP cannot require playtesters to install Python, set up venvs, or run pip. Two viable approaches:
- PyInstaller bundle of the sim into a standalone executable that Godot launches as a child process
- Cython/Nuitka compilation if PyInstaller startup time is unacceptable

Pick one and document why in this stage's spec.

*ZIP structure.* Top-level folder with the Godot executable, the bundled sim executable, asset directory, a single `README.txt` with run instructions, and a `feedback.txt` template playtesters can fill out and email back. No installer — extract and double-click.

*Build flags.* `IS_RELEASE_BUILD = true` per Stage 9 security architecture. All debug output suppressed. Debug overlay hotkey can remain (this is a friends build, not a public one) but is off by default.

*Privacy disclosure.* First-launch modal: "This is a private playtest build of Ouroboros Manifold. By playing, you agree that the developer may receive crash reports and feedback you submit. No automatic data collection." This is appropriate scope for a friends build — heavier disclosure infrastructure (telemetry consent, data retention policy) is deferred until public beta.

*Crash reporting.* Optional: a try-except wrapper at the Godot main loop and Python sim entry point that writes a `crash.log` next to the executable on failure. Playtesters are instructed in the README to email this file if a crash occurs. No automatic upload.

*Build checklist.* Sequential pre-distribution checklist: clean build, install on a fresh VM or second machine, complete one full loop (game start → mission → time jump → mission → quit → relaunch → resume), verify no debug output, verify no developer paths leaked into save files or logs, verify Settled Reach assets all load.

**Done condition.** Developer extracts the ZIP on a machine with no development environment, runs the executable, plays through the full loop, quits, relaunches, and resumes. ZIP is then sent to the playtest group with the README instructions.

---

## Updated stage roadmap (proposed bible amendment)

The following replaces the "Beyond Stage 9" paragraph in `game_bible.md` § Implementation Stage Roadmap with a sequenced list. Stages beyond 13 (commercial-launch features) remain "Beyond Stage 13" without commitment to ordering.

```
Stage 10  — Backend Integration (UIDataBus → live Python sim)
Stage 11  — Galaxy View, Chronicle Scroll, Seamless Transition
Stage 12  — Loop Edges: onboarding stub, mission debrief, save serialization
Stage 13  — ZIP Build, Bundling, Distribution Hygiene
            ↓ FRIENDS-ZIP DELIVERY POINT
Beyond Stage 13 (commercial launch scope, ordering TBD):
  - Multi-stage tutorial across hallmark eras (bible v3.00)
  - Inspection mode for non-owned eras
  - Era Library multi-era support (Roman free tier, 1980s, etc.)
  - Steam integration (Steamworks SDK, depots, branches, achievements)
  - Webapp + entitlement server + Stripe (commercial monetization)
  - Public beta on Steam (the playtest the ZIP build feeds into)
  - Sound design, music
  - Era pack tooling for skeleton/skin expansion model
  - Mission complications
  - Crash recovery, multi-branch save tree UI, cloud saves
```

## Dependency graph

```
Stage 5.5 (finish remaining checkpoints)
        ↓
Stage 6 (finish J + K + L)
        ↓
Stage 7   ← can start once Stage 6 contracts are stable
        ↓
Stage 7.5 ← needs Stage 7 reinforcement structure mechanics
        ↓
Stage 8   ← needs everything above; the largest single stage
        ↓
Stage 9 backend integration (Stage 10)
        ↓
Stage 11 (galaxy + chronicle + transition)
        ↓
Stage 12 (loop edges) — partially parallelizable with Stage 11
        ↓
Stage 13 (ZIP build) — parallel work on build pipeline can begin earlier
        ↓
ZIP delivery to playtesters
```

## Critical path read

The longest sequential chain is **5.5 → 6 → 7 → 7.5 → 8 → 10 → 11 → 12 → 13**. Stage 8 is the largest single body of work in this chain (full Godot renderer, WebSocket bridge, command system, layer rendering, persistence). Stage 11 is the second-largest given the seamless-transition requirement.

Stages 7 and 7.5 can begin once Stage 6 contracts are stable, even before Stage 6 final checkpoints complete. Stage 13 build pipeline work (PyInstaller bundling, export configuration) can begin opportunistically at any time — it does not require the game to be feature-complete.

## Pre-Stage-13 alternative (tactical sandbox build)

If feedback is needed before the full loop is playable, a separable artifact is possible: a tactical sandbox build delivered after Stage 8. Player picks a mission scenario, fights it, sees who won. No simulation backbone, no chronicle, no time jumps, no Stage 9 UI flow.

This delivers combat-feel feedback only — not generational-fantasy feedback. Useful for validating Stage 6 + 7 + 7.5 + 8 in isolation, but does not test the actual product. Listed here as a fallback option, not a recommended path.

## Open decisions for next session

1. **Session-length scope for ZIP build** — bounded 3 chapters, bounded 5 chapters, fully open-ended, or faction-collapse-bounded. Affects Stage 12 save serialization scope significantly.
2. **Bundling approach** — PyInstaller vs Nuitka vs Cython for the Python sim. Defer to Stage 13 spec authoring.
3. **Stage renumbering** — confirm 10/11/12/13 numbering does not conflict with any in-flight work or other planning documents.
4. **Bible amendment** — does the updated roadmap above get written into `game_bible.md` now, or held until ZIP delivery is closer?
