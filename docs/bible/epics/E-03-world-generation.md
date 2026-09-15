# E-03 — World Generation and Topology

## Definition-completeness gate (run 2026-09-10, re-checked 2026-09-14 and 2026-09-15 through the full Q-021/Q-022/Q-024/Q-025 fold chain)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 5 stories, 28 rules (S-021 grew from 8 to 10 rules folding the per-template shapes in; R-025-04 added folding Q-025-01; the original gate's "22 rules" count was stale even before either fold), numbers from `algorithms.md` ALG-30 and ALG-31. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 10 flags total across this epic's life (Q-021-01 through Q-021-06, Q-022-01, Q-022-02, Q-024-01, Q-025-01), all closed and folded. A Sonnet test audit caught what the first gate re-check missed: R-021-03/04 said the player's preference "raises" their chosen template's weight without giving the exact number (Q-021-06) — closed, configurable, default 2:1:1. |
| Every visible-surface story has a reference | Not applicable; the galaxy view that draws the graph is E-16. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: passed, 2026-09-15.** Zero open flags. Every story is folded and consistent with the register and with `algorithms.md`'s ALG-30/ALG-31 (the first pass at this verdict missed that ALG-31 still described the retired fixed-2-region generator; both ALG-30 and ALG-31 are now rewritten to match this epic).

## Purpose

The galaxy the player is born into is generated once per campaign and persists across every chapter and time jump. It is a graph: regions are nodes, connections are edges, and each edge says whether armies, trade, or both can flow along it. Fifteen factions each start from one of three named templates — Isolated (one home, two frontiers), Twin Colony (two homes, one or two frontiers per home), or Archipelago (one home, three sparsely-linked frontiers) — separated from each other by dark, empty space that nobody owns yet. Everything after that is earned by the simulation: colonies push into the dark, conquests redraw borders, and peace or betrayal opens or closes routes.

Two things this epic guarantees: every start is playable (no faction is boxed in, the player's home does not touch any NPC's home), and every start is different (each faction's template, the region count, layout, and starting numbers are all rolled from the seed).

## Obviously working in 60 seconds

Generate three worlds from seeds 1, 2, 3. Each has between 60 and 110 regions and 15 factions, each faction on one of the three templates (some Isolated at 3 regions, some Twin Colony at 4 to 6, some Archipelago at 4), 45 to 90 inhabited regions total depending on the roll, and the rest empty. No two homes are adjacent. Every region is reachable from every other. Every home has the higher population of its faction's regions. Regenerate seed 1: identical graph, identical template rolls, and identical starting numbers.

## Stories

### S-021 — A fresh galaxy from a seed
As a commander starting a campaign, I want a galaxy that is small enough to learn and large enough to feel vast, different every time, so that no two campaigns share a map.

Rules
- R-021-01  Given a seed, When the world is generated, Then the region count is an integer drawn uniformly from [60, 110] and the faction count is 15.
- R-021-02  Given generation, When factions are placed, Then faction 0 is the player civilization and factions 1 through 14 cycle conqueror, fortifier, opportunist in that order.
- R-021-03  Given a faction, When its template is rolled, Then it draws independently from Isolated, Twin Colony, Archipelago with equal weight by default; the player faction's weights are swayed toward their chosen preference (R-021-04) and every NPC faction always uses equal weight.
- R-021-04  Given the player, When they set a template preference before generation, Then it is one of Isolated, Twin Colony, Archipelago, or no preference; a set preference gives that template probability `WORLD_PLAYER_PREFERENCE_WEIGHT`, default 0.50, and the other two templates split the remainder equally (default 0.25 each), in the player faction's own roll only — configurable for playtesting, never locking the outcome, never affecting any NPC faction's roll.
- R-021-05  Given a faction's rolled template, When its regions are placed, Then: Isolated is one home region plus two frontier regions, both adjacent to the home; Twin Colony is two home regions adjacent to each other, each with its own count of 1 or 2 frontier regions (drawn uniformly per home) adjacent to that home; Archipelago is one home region plus three frontier regions, arranged so at least one frontier is not adjacent to the home or to another frontier (reached only through a chain of frontiers). Every region outside a faction's template is empty with no owner and no fields.
- R-021-06  Given a faction's template is placed, When corridors are laid, Then its highest-numbered frontier region (Isolated/Archipelago: numbered in placement order; Twin Colony: the second home's highest-numbered frontier) links to a chain of exactly 1 empty region, and the 15 factions' corridor ends are linked in faction order into one chain.
- R-021-07  Given generation, When the remaining empties are attached, Then each links to one already-connected region chosen uniformly at random, re-rolling up to 20 times to avoid a home region.
- R-021-08  Given a world of N regions, When extra edges are added, Then exactly max(1, floor(0.12 · N)) extra edges are attempted between distinct non-adjacent regions, never between two home regions, with at most 10 times that many draws.
- R-021-09  Given any generated world, When connectivity is checked, Then every region is reachable from every other.
- R-021-10  Given the same seed, When generated twice, Then every faction's template roll, the region ids, adjacency lists, edge types, and starting fields are identical.

Inputs: seed (64-bit integer); config ranges; player template preference (optional).
Outputs: world graph in the strategic snapshot; galaxy view (E-16); each faction's rolled template (T1 trace, save file).
Open flags: none. Q-021-01 through Q-021-06 are closed and folded: every faction independently rolls one of the three named templates, keeping the templates' own region counts (3 for Isolated, 4 to 6 for Twin Colony, 4 for Archipelago) rather than rescaling to a fixed two regions; the galaxy region-count range is [60, 110], confirmed; the player's preference weight is a configurable parameter, default 2:1:1 (0.50/0.25/0.25).

### S-022 — Homes are strong, frontiers are new
As a commander, I want my home region to feel established and my frontier to feel recently settled, so that the starting shape of my civilization tells a story.

Rules
- R-022-01  Given a home region, When its fields are rolled, Then population is uniform in [55, 75]; Given a frontier region, Then population is uniform in [25, 50].
- R-022-02  Given population p, When the other fields derive, Then economy = clamp(p · 1.1 + j₁), military = clamp(p · 0.7 + j₂), tension = clamp(p · 0.3 + j₃), each jᵢ an independent uniform draw in [−5, 5], clamp to [0, 100].
- R-022-03  Given a region, When phase offsets are drawn, Then economy phase and tension phase are independent uniform draws in [0, 2π).
- R-022-04  Given the draw order population, j₁, j₂, j₃, economy phase, tension phase, When a region is generated, Then the RNG is consumed in exactly that order (determinism contract).
- R-022-05  Given a home region, When its military and economy are rolled, Then the archetype's own range replaces R-022-02's general clamp targets: Conqueror military 50–65, economy 40–55; Fortifier military 40–50, economy 50–65; Opportunist military 45–55, economy 45–55; the player faction and tension/population keep R-022-01/R-022-02's general ranges. Frontier regions keep R-022-01's newly-settled ranges regardless of archetype. Starting tech = average starting population of its regions · 0.25.

Inputs: tier, RNG, faction archetype.
Outputs: starting fields per region; starting tech per faction.
Open flags: none. Closed by Q-022-01 and Q-022-02 (Westley, 2026-09-14): per-archetype home ranges are the design, numbers above; frontier regions are archetype-independent.

### S-023 — Routes carry armies, trade, or both
As a commander, I want a connection between two regions to be a military route, a trade route, or both, so that a region can be rich but exposed, or safe but poor.

Rules
- R-023-01  Given generation is complete, When edge types are assigned, Then an edge between two regions of the same faction is `both` and every other edge (including any edge touching an empty region) is `border`.
- R-023-02  Given a query for neighbors of type `border`, When evaluated, Then it returns neighbors whose edge is `border` or `both`; a query for `trade` returns `trade` or `both`; a query with no type returns all.
- R-023-03  Given every "nearby" or "adjacent" read in the sim (drift adjacency, border friction, faction targeting, event propagation, character selector), When it runs, Then it names an edge type; drift adjacency reads `trade`, border friction reads `border`, faction targeting reads all.
- R-023-04  Given an edge set to a type, When read from either endpoint, Then both directions report the same type.

Inputs: edge type per edge (`border`, `trade`, `both`).
Outputs: neighbor query results; edge type in the strategic snapshot; drawn as distinct filament styles in the galaxy view (E-16).
Open flags: none.

### S-024 — Politics redraws the routes
As a commander, I want peace to open trade and betrayal or conquest to close it, so that the map's connections follow the story.

Rules
- R-024-01  Given two factions form a cooperative peace, When it resolves, Then every edge between their regions becomes `both`.
- R-024-02  Given one faction betrays another, When it resolves, Then every edge between their regions becomes `border`.
- R-024-03  Given a region is conquered, When ownership changes, Then its edges to the conqueror's own regions become `both`, its edges to the former owner's regions become `border`, and its edges to regions of the conqueror's cooperative partners become `both`.
- R-024-04  Given a region is colonized, When ownership is set, Then its edges to the colonizer's regions and to its cooperative partners' regions become `both`.
- R-024-05  Given no diplomatic or ownership change on a tick, When the tick ends, Then no edge type changed.

Inputs: peace, betrayal, conquest, colonization events (E-05, E-06).
Outputs: edge types in the strategic snapshot.
Open flags: none. Closed by Q-024-01 (Westley, 2026-09-12): instability-driven edge collapse is a future story, not this epic's Round 1 scope — no rule here implements it. Proposed trigger for that future story: an edge collapses `both`/`trade` → `border` when either endpoint's stability is below 20 for 50 consecutive ticks.

### S-025 — Nobody starts on your doorstep
As a commander, I want empty space between me and every other faction at the start, so that first contact is something that happens, not something I spawn into.

Rules
- R-025-01  Given generation is complete, When the player's inhabited regions and any NPC faction's inhabited regions are checked, Then they are not adjacent. NPC-to-NPC inhabited regions may be adjacent.
- R-025-02  Given generation is complete, When the player's home region and any NPC faction's home region are checked, Then they are not adjacent. NPC-to-NPC home regions may be adjacent.
- R-025-03  Given generation is complete, When the shortest path from the player's inhabited regions to any NPC faction's inhabited regions is computed, Then it passes through at least one empty region.
- R-025-04  Given an extra edge would be drawn between the player's home or frontier and any NPC faction's home or frontier during generation, Then that draw is rejected and re-rolled (R-021-08's re-roll budget applies); this check does not apply between two NPC factions.

Inputs: generated graph.
Outputs: adjacency; a generation-time check that rejects and re-rolls a violating extra edge (R-025-04).
Open flags: none. Closed by Q-025-01 (Westley, 2026-09-12): the buffer is player-to-NPC only, checked at generation time only — NPC factions may end generation adjacent to each other, and any faction pair may become adjacent later through conquest or colonization (E-05, E-06).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Seed | Campaign start | any 64-bit integer | none |
| Region count range | Config | (60, 110), confirmed | count < sum of every rolled faction's template size + 1 fails generation |
| Factions per game | Config | 15 at launch | < 2 fails generation |
| Extra edge ratio | Config | 0.12 | < 0 fails generation |
| Population ranges, ratios, jitter | Config | as ALG-30, per-archetype home ranges as R-022-05 | ranges outside [0, 100] fail generation |
| Template choice | Config: Isolated, Twin Colony, Archipelago | equal weight (1/3 each) per faction by default | player's optional preference (R-021-04) reweights only their own roll: preferred 0.50 (configurable), others 0.25 each; never affects NPC rolls |

## Outputs

| Output | Observable where |
|---|---|
| Region list with id, tier, owner, fields, phase offsets | Strategic snapshot `regions`; save file |
| Adjacency and edge types | Strategic snapshot `adjacency`, `edge_types`; galaxy view filaments |
| Faction list with archetype, starting tech, confidence | Strategic snapshot `factions` |
| Generation report | T1 trace: seed, N, edge count, buffer check result |

## Invariants

- Every region reachable from every other.
- The player's home is never adjacent to any NPC's home; the player's inhabited regions are never adjacent to any NPC's inhabited regions at generation (NPC-to-NPC may be).
- Each faction owns exactly the regions its rolled template defines at tick 0: 3 for Isolated, 4 to 6 for Twin Colony, 4 for Archipelago.
- Same seed, same world (including every faction's template roll), all platforms.
- Empty regions carry no fields and no owner until colonized.

## Scale requirements

Confirmed by Westley, 2026-09-15 (never loosened by Agora; a miss is escalated): generate a 110-region world in under 5 ms; generation is O(N + E). Re-timed from the original 60-region figure (2026-09-14) after the region-count range widened to [60, 110] folding Q-021-04 (variable per-template region counts) — 110 is the new range's max, per Q-021-05.

## Look and behavior references

None required in this epic. The galaxy view is E-16.

## Ways this could be wrong

- Generator consumes the RNG in a different order, so the same seed yields a different galaxy.
- Extra-edge loop links a home to a foreign frontier.
- Corridor chaining leaves a faction unreachable when the empty count is small.
- Edge type defaults to `both` for empty-region edges, letting empties count as trade neighbors.
- Frontier rolled from the home range.
- Factions all get the same phase offsets because the RNG was reseeded per region.
- Twin Colony's second home rolls from the frontier population range instead of the home range.
- Archipelago's "at least one sparse frontier" requirement is skipped, generating a fully-adjacent cluster indistinguishable from Isolated with an extra region.
- A faction's own template roll changes the region-count budget after the total has already been fixed, silently over- or under-filling the galaxy.

## Open ambiguity flags

None. Q-021-01 through Q-021-06, Q-022-01, Q-022-02, Q-024-01, Q-025-01 are closed and folded above.

## Depends on

- E-02 Region fields (what a region's fields are).
- E-05 Faction agents (archetypes, colonize, conquest ownership changes).
- E-06 Diplomacy (peace and betrayal edge changes).
- E-08 Generational structure (the world persists across chapters; ruins accumulate).
