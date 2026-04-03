# Development Acceleration Plan — Bible Restructuring + Stage Consolidation

## Part 1: Game Bible Restructuring

### The Problem

The game bible is 2,427 lines (370KB) in a single file. Every Claude Code session that needs to reference the simulation mechanics also loads 400 lines about map generation, 326 lines about mission archetypes, 272 lines about AI asset pipelines, and 176 lines about unit combat design. For a session implementing Stage 3.5 diplomacy, roughly 70% of the bible is irrelevant context that costs tokens and risks confusion.

The bible also mixes three distinct audiences in one document:
1. **Simulation implementers** (Claude Code sessions building the engine)
2. **Content/creative sessions** (chronicle authoring, naming system, theme packs)
3. **Future system designers** (missions, combat, force allocation — not yet in development)

### The Solution: Hub-and-Spoke Model

Keep the bible as the master document (the hub), but extract each major system into its own focused reference file (the spokes). The bible becomes a high-level overview that points to the detailed specs. Claude Code sessions get pointed at only the spokes they need.

### Proposed File Structure

```
game_bible.md                          # Hub — vision, principles, system summaries, cross-references
bible_simulation.md                    # Spoke — everything in "The Simulation Backbone" (583 lines)
bible_world.md                         # Spoke — world generation, topology, lifecycle, map gen (404 lines)
bible_missions.md                      # Spoke — mission archetypes, generation, objectives (326 lines)
bible_combat.md                        # Spoke — unit roster, abilities, force design (176 lines)
bible_chronicle.md                     # Spoke — chronicle system, template framework, lineage (182 lines)
bible_ai_pipeline.md                   # Spoke — AI integration, naming system, asset pipeline (272 lines)
bible_monetization.md                  # Spoke — expansion packs, distribution, pricing (105 lines)
bible_antagonist.md                    # Spoke — faction archetypes, internal threats, progression (47 lines)
```

### What Stays in the Hub (`game_bible.md`)

The hub retains:
- The modification rule, open question governance, and version history (lines 1–10)
- Vision and Identity (lines 34–66) — this is the soul of the game, everything references it
- Sacred Design Principles (lines 83–100) — non-negotiable, every session needs these
- Table of Contents that now links to spoke files instead of inline sections
- A one-paragraph summary of each spoke's scope, so a session can decide which spokes to read
- Tone and Feel (lines 1910–1925) — short, broadly relevant
- What's Unique / Blue Ocean (lines 1926–1937) — short, broadly relevant
- Open Design Questions (lines 2362–2407) — tracking list
- Document Maintenance rules (lines 2409–end)
- Transition from Previous Iteration (lines 2318–2360) — historical context

**Estimated hub size: ~300 lines.** Down from 2,427. A Claude Code session reads the hub (~300 lines) plus only the spokes it needs (typically 1–2 spokes, ~600–1,000 lines), instead of the entire 2,427-line file.

### What Goes in Each Spoke

**`bible_simulation.md`** — The primary reference for all engine work. Contains:
- Region State Model (fields, composites, thresholds, penalties)
- Per-Tick Update Model (all drift formulas)
- Event Chain Architecture (templates, triggers, pending queue)
- Tick Resolution Sequence (the 7-step loop)
- Simulation Pacing Targets
- Multi-Faction Agent Decision Model (budget, decisions, scoring, archetypes)
- Uninhabited Region Mechanics
- Diplomatic Stance (peace, betrayal)
- Technology System
- Coherence Ledger
- Stage 0/1/3 tuning observations
- What the Simulation Provides to Missions (interface contract)

This is the file Claude Code reads for any stage implementation work. 583 lines, self-contained.

**`bible_world.md`** — World generation and spatial systems:
- Scale, world generation, tiered templates
- Inter-region topology (typed adjacency graph)
- World evolution (per-faction lifecycle, civilizational lifecycle)
- Spatial navigation
- Map generation system (spine + gradient hybrid, all sub-sections)
- Visual style
- Sci-Fi Era content ("The Settled Reach")

**`bible_missions.md`** — Mission system design:
- Mission generation algorithm
- All 10 mission archetypes with full specs
- Mission objectives
- Difficulty scaling, era scaling, preference system
- Mission briefing
- Complications
- Mission outcome resolver

**Other spokes** follow the same pattern — each is a self-contained reference for its system.

### Implementation Steps for Claude Code

1. Create all spoke files by extracting the relevant sections from the current bible verbatim. No rewriting — just cut and paste into the new files.
2. Add a header to each spoke file:
   ```markdown
   # Ouroboros Manifold — Simulation Backbone Reference
   
   > **Extracted from game_bible.md v1.22.** This file is authoritative for simulation 
   > mechanics. If this file conflicts with game_bible.md, flag it for Westley — do not 
   > silently resolve the conflict.
   >
   > **Modification rule:** Same as the master bible — append-only unless Westley approves 
   > deletion. Resolved open questions get written here AND reflected back to the hub.
   ```
3. Replace the inline sections in `game_bible.md` with summary paragraphs and cross-references:
   ```markdown
   ## The Simulation Backbone
   
   > **Full reference: `bible_simulation.md`**
   
   The simulation runs a system-dynamics model with stochastic event chains across a world 
   of connected regions. Each region tracks four granular fields (military, economy, tension, 
   population) and two composite axes (stability, capacity). Faction agents accumulate budget, 
   evaluate targets, and take actions (attack, colonize, reinforce, accumulate) through a 
   scored decision model with per-archetype weights. See `bible_simulation.md` for all 
   formulas, tick sequence, event architecture, and agent model.
   ```
4. Verify: the hub file should be ~300 lines. Each spoke should be readable independently.

### Rules for Future Bible Updates

- Design decisions go into the relevant spoke file first, then get a one-line note in the hub's summary paragraph if they change the system's scope.
- The hub's version number increments whenever any spoke changes.
- Claude Code sessions are told which spoke(s) to read in the stage spec or task description:
  ```
  **Read:** bible_simulation.md sections "Multi-Faction Agent Decision Model" and 
  "Diplomatic Stance" before implementing.
  ```

---

## Part 2: Aggressive Stage Consolidation

### The Problem

The current stage-by-stage approach has been invaluable for building trust and proving mechanics incrementally. But at this point in development (Stage 3.5 underway, core simulation proven), the overhead of fine-grained staging is becoming a bottleneck:

- Each stage spec is 400–600 lines with 10–20 checkpoints
- Each checkpoint requires Westley to review terminal output and sign off
- Mechanics that are tightly coupled get split across stages (diplomacy and technology are in 3.5 together, but lifecycle stages, which depend on both, will be a separate stage)
- Claude Code starts each session by reading the current stage spec + the bible + the relevant prior stage specs — that's 3,000+ lines of context before it writes a line of code

### The Solution: Broader Stage Specs with Validator Coverage

Now that the invariant system exists, checkpoints don't need to be manual. The new approach:

1. **Spec broader stages** that cover a complete behavioral system, not individual sub-mechanics
2. **Define the invariants for the stage in the spec itself** — these replace manual checkpoints
3. **Claude Code implements, runs the validator, and iterates** until all invariants pass
4. **Westley reviews the final validator report + graphs**, not intermediate terminal output

### Proposed Remaining Stages

Instead of continuing the current granular numbering (Stage 4, 4.5, 5, 5.5...), consolidate the remaining work into broader stages:

**Stage 4: Civilizational Lifecycle and Generational Structure**

Covers everything needed for the simulation to run a complete civilizational arc:
- Per-faction lifecycle stages (Growth → Peak → Decline → Collapse/Rebirth)
- Player civilization mortality (the player's faction can die)
- Cross-faction lineage rotation (when your faction dies, you continue as someone in another faction)
- Administrative revolt system (quadratic territory scaling)
- Home region vulnerability
- Terminal conditions (Survival, Exodus, Extinction with Amnesia)
- Time jump mechanics (what happens between chapters)

Why these belong together: they're all about the macro arc. Lifecycle stages drive terminal conditions. Player mortality drives lineage rotation. Time jumps need lifecycle stages to produce meaningful between-chapter evolution. Splitting these into 3 separate stages means each one is tested in isolation without the others, then integration issues surface later.

**Stage 5: Chronicle and Coherence**

Covers the narrative layer that reads the simulation:
- Coherence ledger (named character registry, character lifecycles)
- Chronicle template authoring (fragment structure, variable slots, category taxonomy)
- Chronicle generation from simulation events
- Chronicle scroll distiller algorithm
- Lineage entanglement

Why these belong together: the chronicle reads the coherence ledger which reads simulation events. Testing chronicle generation without the coherence ledger is testing plumbing without water.

**Stage 6: Mission System**

Covers the player-facing interaction layer:
- Mission generation algorithm
- Mission archetypes (all 10)
- Mission briefing generation
- Force allocation
- Mission outcome resolver
- Difficulty and era scaling
- Character selector algorithm

Why these belong together: the mission system is the player's interface to the simulation. It reads simulation state, generates a mission, allocates forces, and resolves outcomes back into the simulation. Every piece depends on every other piece.

### Stage Spec Format Under the New Model

Each consolidated stage spec should follow this structure:

```markdown
# Stage N — [Name]

## Goal
One paragraph: what this stage proves.

## Bible References
Exactly which spoke files and sections to read. Nothing else.

## What to Build
Files to create, files to modify. Same as current specs.

## Behavioral Claims
The plain-English list of "if X then Y" statements from the spec.
These become the invariants. Use the format from the Invariant Authoring Blueprint:

  Claim 1: [statement]
    When: [trigger]
    Then: [expected outcome]
    Over: [time window]
    Invariant pattern: threshold / relational / trajectory shape
    Governing configs: [list]
    Severity: critical / warning

## Invariants to Implement
The claims above, written as invariant function signatures with descriptions.
Claude Code implements these in invariants.py as part of the stage work.

## Scenarios to Add
Any new sim_tuner.py scenarios needed to exercise this stage's mechanics.

## Validation Criteria
Instead of N manual checkpoints:
  - All new invariants pass across 3+ seeds
  - All existing invariants still pass (no regressions)
  - Graphs show [qualitative description of expected visual patterns]
  - Westley reviews final report and graphs

## Done Condition
All validation criteria met. Westley signs off on the report, not on terminal output.
```

### What This Changes About Claude Code's Workflow

Before (current):
1. Read stage spec (500 lines) + bible (2,400 lines) + prior specs
2. Implement checkpoint 1
3. Stop, print output, wait for Westley
4. Westley reads output, says "pass" or "fix X"
5. Repeat 15–20 times per stage

After (proposed):
1. Read stage spec (300–400 lines) + relevant bible spoke (500–600 lines)
2. Implement the full mechanic
3. Implement the stage's invariants
4. Run the validator
5. If invariants fail: diagnose, adjust config (or escalate), re-run
6. When all invariants pass: generate graphs, output final report
7. Westley reviews report + graphs once, signs off

The per-stage human review drops from 15–20 touchpoints to 1–2 (initial review of the spec's behavioral claims, then final sign-off on the report). Claude Code's context window usage drops because it reads one spoke instead of the whole bible. And the validator catches regressions automatically, so you don't have to re-verify stages 1–3 behavior every time a new stage lands.

### Migration Path

You don't have to restructure everything at once. The immediate steps:

1. **Finish Stage 3.5 under the current model.** It's already in progress, don't disrupt it.
2. **Restructure the bible** (Part 1 of this plan). This is a mechanical task — extracting sections into files.
3. **Write the Stage 4 spec in the new format** using the consolidated structure above. This is the first test of the new approach.
4. **Claude Code implements Stage 4** with the validator loop instead of manual checkpoints.
5. **Evaluate:** Was Stage 4 faster? Did the validator catch what manual review would have caught? Adjust the approach if needed before Stage 5.
