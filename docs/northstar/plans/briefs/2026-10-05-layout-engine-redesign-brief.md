# Brief: re-assess and redesign the layout engine (2026-10-05)

For a fresh Fable chat. Paste this file, or point the chat at it on origin/main. It tells you what to read and what to produce. It is not the design.

## Why this exists

The land mockup now looks good, and it rests on a layout engine designed before the game's current ideas on economy, landscape and strategic depth. Westley, 2026-10-04: the underlying issue is the layout engine; its design is old-fashioned compared with the updated game and needs to be redesigned, re-assessed "given the new constraints on economy, landscape, and strategic depth".

## Your role and product

You are an Architect. You read, re-assess what a layout engine is for under today's constraints, and design a prototype of a new one for Westley to look at. You write no game code and no mockup code.

Produce, in this order:

1. **An assessment** of the present layout engine against the three new constraints: what it specifies, what it cannot express, what in it is still right.
2. **An options page**: two or three different shapes a new layout engine could take, each with what Westley would see in a prototype. Put it in `docs/northstar/research/layout_engine/`.
3. **After he picks, a one-page prototype spec** under the Prototype gate (`docs/northstar/agile.md`), built by a Sonnet Doer on this Linux machine, with a row in `docs/northstar/ROADMAP.md` section 0 so he can run it.

Rules: flag, never guess. An open question becomes a `Q-` row in `docs/northstar/ambiguity_register.md` with two or three candidates. Rule meaning and numbers are Westley's. Do not edit the bible until he has approved a prototype. Read from origin/main, never from the live checkout `/home/westopoli/Projects/ouroboros-manifold` (it lags by over a thousand commits). Write for a narrow screen: plain words, short tables, the decision you need from him last.

## Westley's words that bind the redesign

Quote these; do not paraphrase them into something stronger. The register rows hold the full text.

- 2026-10-04: "layout comes before landscape. The layout engine should be prototyped and integrated before the landscape engine."
- Q-191-04, amended 2026-10-03: "The point of the game is that it induces strategic depth, not just random stochiacity. I want to modify my decision, the landscape engine should take the inputs from the layout engine and lean on them. For example, if the layout engine calls for something like a choke, the landscape engine is required to produce it. Mark that I want to see a prototype of the layout engine, and how the landscape engine reacts to it."
- Q-191-03, 2026-10-03: "there should be an equal distance for both players between both the significant resources and the objective. I don't care what the shape is, I only care about those numbers. However much we can vary the shapes given those constraints I encourage."
- Q-192-02, 2026-10-03: "the width should be decided by the layout engine."
- Q-192-04, 2026-10-03: "We should probably pair archetypes with layouts, the game has changed a lot since those layouts were authored. Mark that layouts need to be audited/double checked before they're implemented." A layout that offers no play is not allowed.
- Q-191-01, 2026-10-03: places are found by a scoring per kind, "but I want to see it in action in a live prototype."
- The goal the game is tuned toward (layer-lab plan, 2026-10-01): "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force."

## What to read

Paths are relative to the repo root on origin/main unless a branch is named.

### 1. The layout engine as it is

| Path | Why |
|---|---|
| `simulation/layout_library/layout_0N_*.json` (eight files) | The layouts themselves: zones with a position ratio, a node type, properties, edges, drift paths |
| `simulation/layout_library.py`, `simulation/layout_instantiator.py`, `simulation/map_generator.py`, `simulation/map_gen_contracts.py`, `simulation/spine_drift.py`, `simulation/test_layout_library.py` | The Python reference: how a layout is chosen, scaled to a canvas, and how its nodes drift |
| `csrc/tactical_mapgen.c` | The C generator the game would use. It is built and tested, and no live mission calls `om_map_generate`, so today's missions have no layout |
| `tests/csim/test_E17_S112_bones_from_the_library.py` to `test_E17_S119_terrain_that_reads_like_a_place.py` | What the present engine is held to |
| `docs/bible/algorithms.md`, ALG-70 to ALG-73 | Layout selection, gradient sources, fairness, spine drift |
| `docs/bible/epics/E-17-map-generation.md` | Stories S-112 to S-119 are the old layout design, each marked "direction changed, rewrite pending"; S-186 to S-197 are the terrain-first design added beside it |
| `docs/bible/references/E-17/notes.md` | The visual references attached to the epic |

### 2. New constraint: landscape

| Path | Why |
|---|---|
| `docs/northstar/research/landscape_design/README.md` on branch `push/proto-land-iter` | The record of every land mockup pass with Westley's reviews verbatim. Read Pass 4, the sweep, Pass 5 and Pass 6 |
| `docs/northstar/research/landscape_design/options_2026-10-03_walkable_land.md` | Why "layout first, terrain obeys" was chosen, with the numbers |
| `scenes/mockups/landscape/pass5_layout.gd`, `pass5_places.gd`, and on `push/proto-land-iter` `pass6_shape.gd`, `pass6_cliffs.gd` | How the mockup reads a layout, makes terrain react to it, finds places per kind, and checks equal distance |
| `docs/northstar/plans/archive/specs/2026-10-03-land-mockup-pass5-spec.md`, `docs/northstar/plans/briefs/2026-10-04-land-mockup-iteration-brief.md` | The specs those passes were built to; the second is the model for a prototype brief |
| `docs/northstar/research/space_landscape/README.md` | The space sister system: one open-or-blocked map per layer. A layout must work there too |

Run the land mockup before you design: the command is in `docs/northstar/ROADMAP.md`, section 0.

### 3. New constraint: economy

| Path | Why |
|---|---|
| `docs/bible/epics/E-22-economy-and-bases.md` | S-175 (expansions and forward works), S-177 (every side has a base; rich resources lie away from the objective), S-178 (a fallen base is occupied) |
| `docs/bible/epics/E-10-missions.md` | R-073-01 (the ten archetypes with canvas, objective type and outcomes), S-210 (the base each side starts from), S-211 (resources fit the situation), S-214 (more players, bigger map) |
| `docs/bible/epics/E-15-reinforcement-supply-and-hazards.md` | S-218: strongpoints at the slopes between height bands |
| `docs/northstar/research/economy_design/` | Start with `README.md`, `base_and_objective_options.md`, `map_scale_comparison.md`, `settlement_generation_options.md` |

### 4. New constraint: strategic depth

| Path | Why |
|---|---|
| `docs/legacy/claude_exchange/plans/2026-09-30_layer-lab-plan_pasted-content-id-bf70-the-player-vivid-gizmo.md` | The goal, the principle (who gets shots off, and for how long), the five skills and their plays |
| `docs/northstar/research/layer_dynamics/README.md`, sections 4 and 4.1a | The accepted table of plays and counters a map must make possible |
| `docs/northstar/research/layer_dynamics/audits/2026-10-04_rules_against_strategic_depth.md` | Verdict per skill. Landscape is "absent in play" because no map has a choke |
| `docs/northstar/research/layer_dynamics/audits/2026-10-04_plan_drift.md` | How this work drifted from its plan; do not repeat it |
| `docs/legacy/topics/lanchester_and_combat_theory.md` | Why a choke, a flank and high ground matter: square and linear laws, defeat in detail, height as initiative |
| `docs/bible/epics/E-01-layer-system.md` | Five layers, slopes, vantages, what terrain blocks |
| `docs/northstar/research/layer_dynamics/runs/2026-10-04_formation_read.html` | The first lab chart Westley saw: on open ground formation is worth about three soldiers in sixteen. Terrain is where the rest must come from |

### 5. Open flags the redesign inherits

`docs/northstar/ambiguity_register.md`: Q-191-05 (choke widths, landform bias per archetype, site counts and spacing, the equal-distance measure and tolerance), Q-188-01 (smallest real layer step), Q-189-04 (what makes a place unreasonably hard to reach), Q-118-02 and Q-118-03 (canvas push per archetype; whether a strongpoint may drift), Q-177-01 to Q-177-05 (bases and resources per situation). Check each row's status before relying on it.

### 6. Method

`CLAUDE.md`; `docs/northstar/ROADMAP.md` (section 0 for running prototypes, section 5 for the order: layout engine before landscape engine); `docs/northstar/agile.md` (Prototype gate; three passes without approval means an options page); `docs/northstar/PLAN.md` principles 16 to 18.

## Findings to start from, not to re-derive

- Carving a layout into terrain generated without it leaves broken edges and wide cut routes (pass 5). Shaping the terrain from the layout as it is generated works better (pass 6).
- After pass 6, edges to vantages are still not walkable on layout 8 (seeds 11 and 12) and layout 5 (seed 11). The cause was never measured.
- All eight layouts are assaults with the objective beside one side, so none can meet the equal-distance rule for the objective. Westley has not yet ruled whether the objective moves or the starts become symmetric.
- Layout 07 (scattered outposts) has no choke and no vantage. The library has no node kind for a slope top or for tall cover, and gives choke width only as the words "narrow" and "moderate".
- The library predates bases, expansions, economic sites, significant resources, neutral settlements, strongpoints, and raid and shipment lanes. None of them is a node kind.
- Relief stays near 4,500 wu on any canvas, so mountains shrink on big maps; units cross a "32,000 wu" map in about three minutes. Scale is unsettled.
- Canvas sizes now run to 64,000 wu for 4 to 6 players (S-195, S-214).

## Questions the redesign must answer

State each as an option set for Westley; answer none of them yourself.

1. What must a layout specify now? Candidates to place: a base per side by archetype and supply distance, the objective, significant resources at equal distance, expansion sites, economic sites, neutral settlements, chokes with widths, vantages, strongpoints at slopes, routes for raids and shipments.
2. What must it leave to the terrain?
3. Which plays of each of the five skills must every layout offer, and how is that checked?
4. Do layouts stay hand-authored graphs, become generated from rules, or become constraints solved per map?
5. How does one layout scale from 16,000 to 64,000 wu and from 2 players to 4 or 6?
6. How does a deliberately slanted archetype (a defender with the better ground) stay fair, and by what measure?
7. What do the nine old node types become?
8. What is a layout on a space map, where the terrain is open or blocked per layer?
9. How is a layout paired with an archetype, and what happens to the eight old ones?

## Limits

- Do not edit `scenes/mockups/landscape/` or the branch `push/proto-land-iter`; its chat is paused and owns them. A new prototype goes in new files.
- Prototypes are built on the Linux machine (ruling A208) by a Sonnet Doer from a one-page spec. Sub-agents are Sonnet, named explicitly, one small step each.
- Record Westley's answers verbatim in the register and tell the planner chat (`Agora-Fable-Planner`) when a prototype is approved.
