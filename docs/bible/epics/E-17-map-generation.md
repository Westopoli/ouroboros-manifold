# E-17 — Map Generation

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 8 stories, 40 rules, numbers from `algorithms.md` ALG-70 through ALG-73 and config. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 6 new flags, Q-112-01, Q-113-01, Q-115-01, Q-117-01, Q-118-01, Q-119-01. |
| Every visible-surface story has a reference | **No.** S-119 (how generated terrain reads, and the procedural architecture ambition Westley opened in Stage 1, A-157) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 6 open flags and one reference. Q-113-01 (fairness gating: designed but shipping ungated, A-393) and Q-119-01 (the procedural architecture system Westley wants to invest in, A-157) need Westley.

## Purpose

Every mission map is generated from a few hundred bytes: a spine of ten to thirty strategic waypoints, chosen from a hand-authored layout library and scaled to the canvas, plus a handful of gradient sources that fill the space between them with obstacles, cover, interference, elevation, and layer blocks. Authored bones, procedural skin. The archetype picks which layouts qualify; the region's simulation state flavors the terrain, so a war-torn frontier plays differently from a prosperous core on the same bones; the theme pack decides whether an obstacle is an asteroid or a mountain. Nodes and sources can drift during a mission, so battlefields move.

This is also where the layer system gets its terrain (E-01 S-001) and fog gets its interference (E-12 S-090).

## Obviously working in 60 seconds

Generate a Defensive Stand map for a medium canvas from seed 11 and region stability 20. The spine has 10 to 30 nodes including at least one objective, one staging, two chokepoints with a flank route each, and at least one spawn point; every node is reachable from staging by at least two routes. Obstacle density peaks near chokepoints at 0.85, vantage elevation at 0.90, an interference zone sits at the layout's ambush spot. Regenerate from seed 11: identical seed bytes. Raise stability to 90: the same layout with thinner interference and cover. In the recon phase every node type and gradient is visible.

## Stories

### S-112 — Bones from the library
As a commander, I want maps built on hand-authored strategic layouts so that every map has a chokepoint, a flank, and a reason, and I learn the vocabulary over time.

Rules
- R-112-01  Given an archetype, When candidates are gathered, Then every layout satisfying at least one of the archetype's compatibility filters (structural checklists, 2 to 3 per archetype) enters the pool.
- R-112-02  Given the pool, When one is chosen, Then it is drawn uniformly at random [Q-113-01: hints as bias, fairness as gate].
- R-112-03  Given a layout, When instantiated, Then its zone positions (percentages of canvas) scale to the canvas dimensions with jitter of up to 3 percent of canvas per zone, spatial ratios preserved.
- R-112-04  Given the instantiated nodes, When edges are laid, Then the layout's connectivity is honored, there are at least 2 distinct routes from staging to every objective, at most the layout's allowed dead ends, and every flank route connects to at least 2 non-flank nodes.
- R-112-05  Given the library at launch, When loaded, Then it holds between 10 and 20 layouts and each archetype has at least 4 compatible layouts [Q-112-01: current count].
- R-112-06  Given a layout file, When loaded, Then it contains only zone positions, relationships, chokepoint specs, node placement, and connectivity; never gradient values, era visuals, absolute coordinates, enemy behavior, or difficulty.

Inputs: archetype; layout library; seed.
Outputs: instantiated spine (nodes, edges) in the map seed.
Open flags: Q-112-01, Q-113-01.

### S-113 — Nine kinds of place
As a commander, I want every place on the map to be one of nine things, so that I can read a map I have never seen.

Rules
- R-113-01  Given any spine node, When typed, Then it is exactly one of objective, staging, transit, chokepoint, flank_route, vantage, hazard_anchor, spawn_point, extraction.
- R-113-02  Given any map, When checked, Then it has at least one objective and at least one staging node.
- R-113-03  Given a chokepoint, When checked, Then at least one flank route bypasses it.
- R-113-04  Given a vantage node, When checked, Then it is reachable from both staging and every spawn point and pre-owned by nobody.
- R-113-05  Given a chokepoint spec of width ratio w, When instantiated, Then the passable width is w × 200 wu (standard formation width).

Inputs: layout node placement.
Outputs: typed nodes in the map seed; recon render.
Open flags: none.

### S-114 — Texture from gradients
As a commander, I want the space between waypoints to feel dense or open, blind or clear, high or low, so that a map is a place and not a diagram.

Rules
- R-114-01  Given the five properties, When sampled anywhere, Then each of obstacle_density, cover_density, sensor_interference, elevation is a float in [0, 1] and layer_accessibility is binary per layer.
- R-114-02  Given a gradient source (position, type, radius, intensity, falloff), When sampled at distance r ≤ radius, Then its contribution is intensity × falloff(r/radius), and overlapping sources combine [Q-115-01: sum clamped or max].
- R-114-03  Given the instantiated spine, When sources are placed, Then obstacle density anchors at chokepoints (intensity 0.85, radius 600) and staging (0.60, 800); elevation at vantage nodes (0.90, 700); interference at hazard anchors (0.75, 500); cover at chokepoints (0.55, 550), objectives (0.50, 400), hazard anchors (0.35, 400); flank routes get light obstacles (0.35, 450) and cover (0.40, 450).
- R-114-04  Given a zone with layer restrictions, When masks are placed, Then every layer not listed gets a full-intensity blocking source of radius 600 at the zone, and accessibility at a point is open unless a blocking source's sampled value ≥ 0.5.
- R-114-05  Given obstacle density > 0.7 at a cell, When the route grid is built (E-13 R-097-01), Then the cell is blocked.

Inputs: spine; layout hints.
Outputs: gradient sources in the map seed; sampled fields for E-01, E-12, E-13.
Open flags: Q-115-01.

### S-115 — The region shapes the terrain
As a commander, I want a prosperous region's battlefield to be cleaner than a war-torn one's, so that I feel the galaxy's state under my feet.

Rules
- R-115-01  Given region stability s and capacity c, When baselines are set, Then interference, hazard anchor count, and cover scale with (100 − s)/100 and obstacle density with (100 − c)/100, each within a bounded multiplier [Q-117-01: exact multipliers].
- R-115-02  Given individual fields, When deltas are applied, Then economy lowers obstacle density along routes and adds cover from infrastructure, tension raises cover, military raises obstacle density near defensive positions, population scales total feature density; deltas are bounded so they never overwhelm the baseline.
- R-115-03  Given simulation coupling disabled, When a map is generated, Then layouts and hints alone produce a valid map.

Inputs: region fields and composites.
Outputs: adjusted source intensities.
Open flags: Q-117-01.

### S-116 — Canvas
As a commander, I want mission maps sized to the situation, so that a suppression is tight and a siege is vast.

Rules
- R-116-01  Given an archetype, When the canvas is chosen, Then its base category is the E-10 S-073 table, and its dimension is drawn from small [8,000, 12,000], medium [12,000, 20,000], large [20,000, 28,000] wu square [Q-118-01: bible says fixed 8/16/24k ± 30 percent].
- R-116-02  Given the region's fields, When the ±30 percent modifier applies, Then its direction is the archetype's (defensive stand grows with wealth, counterinsurgency grows with tension, suppression shrinks).

Inputs: archetype; region.
Outputs: canvas size in the map seed.
Open flags: Q-118-01.

### S-117 — Fair enough
As a commander, I want maps that do not cheat me, so that a loss is mine.

Rules
- R-117-01  Given a generated map, When the fairness evaluator runs, Then it scores route count staging-to-objective versus spawn-to-objective, mean travel time balance, vantage accessibility balance, and hazard distribution symmetry, and logs the score.
- R-117-02  Given the launch build, When the score is outside the acceptable range, Then [Q-113-01: the map is regenerated with a new seed up to 5 times (bible), or accepted and logged (code, A-393)].
- R-117-03  Given a layout in the library, When authored, Then it passes the hard constraints: no side's every approach blocked by hazards while the other's is clear; every vantage reachable by both sides.

Inputs: map seed.
Outputs: fairness log; regeneration.
Open flags: Q-113-01.

### S-118 — The battlefield moves
As a commander, I want objectives to drift and hazards to move during a mission, so that a position is never solved.

Rules
- R-118-01  Given a spine node of type objective or reinforcement_structure with a drift path, When ticks pass, Then its position follows the path (ping-pong or loop over waypoints with a period in ticks) and the objective zone moves with it.
- R-118-02  Given a gradient source with motion, When ticks pass, Then its position moves and every sampled field updates.
- R-118-03  Given a moving node, When it moves, Then no unit teleports; units path to the new position under their standing orders.

Inputs: drift specs in the map seed.
Outputs: node and source positions per tick in the delta; HUD objective marker.
Open flags: none.

### S-119 — Terrain that reads like a place
As a commander, I want generated sections to blend like real terrain, not tile like a board, so that every map feels made.

Rules
- R-119-01  Given a T2 screenshot of any generated map, When inspected, Then no repeated tile boundary is visible and gradient regions blend without hard edges.
- R-119-02  Given the procedural architecture system Westley opened in Stage 1 (A-157), When designed, Then it is era-agnostic at the section level with an era-specific kit of pieces assembled by it [Q-119-01: scope and schedule].

Inputs: map seed; era kit.
Outputs: screen.
Open flags: Q-119-01. Reference required: `references/E-17/notes.md`, missing (Minecraft and Roblox biome blending are the named references).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Archetype | E-10 | 10 archetypes | unknown fails |
| Region state | E-02 | fields and composites | |
| Layout library | E-21 | 10 to 20 layouts | invalid layout fails validation at build |
| Library hints | E-21 | optional | ignored if absent |
| Seed | Campaign | integer | |
| Era kit | Era pack | visual prefabs per abstract type | missing prefab uses a placeholder |

## Outputs

| Output | Observable where |
|---|---|
| Map seed (spine, edges, sources, canvas, drift specs) | Save file; T1 trace; replay |
| Sampled fields | E-01, E-12, E-13 queries |
| Fairness score | T1 trace |
| Rendered terrain | Screen; recon phase |

## Invariants

- Same seed and inputs, same map seed bytes.
- Every objective reachable from staging by 2 or more routes.
- No node outside the canvas.
- Map seed under 1 KB.

## Scale requirements

Proposed for Westley to confirm: generation under 50 ms; field sampling under 1 µs per query with a precomputed grid at 100 wu.

## Look and behavior references

`references/E-17/notes.md`, missing.

## Ways this could be wrong

- Layout chosen by index instead of the filtered pool.
- Jitter applied after edges are laid, breaking connectivity.
- Sources placed at layout percentages instead of instantiated positions.
- Layer masks emitted for listed layers instead of unlisted.
- Flavoring multipliers unbounded, so a dead region has no walkable space.
- Fairness evaluator rejects and silently regenerates without logging the seed.
- Drifting node moves but the objective zone stays.

## Open ambiguity flags

Q-112-01, Q-113-01, Q-115-01, Q-117-01, Q-118-01, Q-119-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-02 (region state for flavoring), E-10 (archetype and canvas), E-21 (layout library and hints), E-01, E-12, E-13 (consumers), E-15 (reinforcement structure placement), E-18 (era kit).
