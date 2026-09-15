# E-03 — World Generation and Topology

## Definition-completeness gate (run 2026-09-10, re-checked 2026-09-14 after the Q-021/Q-022/Q-024/Q-025 fold)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 5 stories, 26 rules (R-025-04 added folding Q-025-01; the original gate's "22 rules" count was stale even before this fold), numbers from `algorithms.md` ALG-30 and ALG-31. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | Original 5 flags (Q-021-01 through Q-025-01) closed and folded. Folding Q-021-01 and Q-022-01 surfaced 2 new flags, Q-021-03 and Q-022-02, not yet answered. |
| Every visible-surface story has a reference | Not applicable; the galaxy view that draws the graph is E-16. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 2 open flags. Q-021-03 (how the three named templates apply across 15 factions) decides whether R-021-03 through R-021-06 get rewritten or stay as the per-faction generic shape; Q-022-02 (Fortifier and Opportunist starting ranges) blocks finishing R-022-05's fold. Both need Westley's answer before this epic is Ready.

## Purpose

The galaxy the player is born into is generated once per campaign and persists across every chapter and time jump. It is a graph: regions are nodes, connections are edges, and each edge says whether armies, trade, or both can flow along it. Fifteen factions each start with a small, established home and one weaker frontier, separated from each other by dark, empty space that nobody owns yet. Everything after that is earned by the simulation: colonies push into the dark, conquests redraw borders, and peace or betrayal opens or closes routes.

Two things this epic guarantees: every start is playable (no faction is boxed in, the player's home does not touch any NPC's home), and every start is different (region count, layout, and starting numbers are rolled from the seed).

## Obviously working in 60 seconds

Generate three worlds from seeds 1, 2, 3. Each has between 40 and 60 regions, 15 factions, 30 inhabited regions, and the rest empty. No two homes are adjacent. Every region is reachable from every other. Each faction's home has the higher population of its pair. Regenerate seed 1: identical graph and identical starting numbers.

## Stories

### S-021 — A fresh galaxy from a seed
As a commander starting a campaign, I want a galaxy that is small enough to learn and large enough to feel vast, different every time, so that no two campaigns share a map.

Rules
- R-021-01  Given a seed, When the world is generated, Then the region count is an integer drawn uniformly from [40, 60] and the faction count is 15.
- R-021-02  Given generation, When factions are placed, Then faction 0 is the player civilization and factions 1 through 14 cycle conqueror, fortifier, opportunist in that order.
- R-021-03  Given generation, When tiers are assigned, Then each faction owns exactly one home and one frontier region linked to each other, and every remaining region is empty with no owner and no fields.
- R-021-04  Given generation, When corridors are laid, Then each faction's frontier links to a chain of exactly 1 empty region, and the 15 corridor ends are linked in faction order into one chain.
- R-021-05  Given generation, When the remaining empties are attached, Then each links to one already-connected region chosen uniformly at random, re-rolling up to 20 times to avoid a home region.
- R-021-06  Given a world of N regions, When extra edges are added, Then exactly max(1, floor(0.12 · N)) extra edges are attempted between distinct non-adjacent regions, never home to home, with at most 10 times that many draws.
- R-021-07  Given any generated world, When connectivity is checked, Then every region is reachable from every other.
- R-021-08  Given the same seed, When generated twice, Then the region ids, adjacency lists, edge types, and starting fields are identical.

Inputs: seed (64-bit integer); config ranges.
Outputs: world graph in the strategic snapshot; galaxy view (E-16).
Open flags: Q-021-03. R-021-03 through R-021-06 below describe the generic per-faction generator, which Q-021-01 (Westley, 2026-09-14) retired in favor of three named templates (Isolated, Twin Colony, Archipelago) — but how those templates apply across 15 factions is not yet answered (Q-021-03), so these rules are the last-known-good design, not yet rewritten. Q-021-02 (player preference sways template choice) is answered but not folded in below pending Q-021-03, since the weighting mechanism depends on how many factions roll a template.

### S-022 — Homes are strong, frontiers are new
As a commander, I want my home region to feel established and my frontier to feel recently settled, so that the starting shape of my civilization tells a story.

Rules
- R-022-01  Given a home region, When its fields are rolled, Then population is uniform in [55, 75]; Given a frontier region, Then population is uniform in [25, 50].
- R-022-02  Given population p, When the other fields derive, Then economy = clamp(p · 1.1 + j₁), military = clamp(p · 0.7 + j₂), tension = clamp(p · 0.3 + j₃), each jᵢ an independent uniform draw in [−5, 5], clamp to [0, 100].
- R-022-03  Given a region, When phase offsets are drawn, Then economy phase and tension phase are independent uniform draws in [0, 2π).
- R-022-04  Given the draw order population, j₁, j₂, j₃, economy phase, tension phase, When a region is generated, Then the RNG is consumed in exactly that order (determinism contract).
- R-022-05  Given any faction, When its starting fields are rolled, Then it uses the same ranges and ratios as every other faction; starting tech = average starting population of its regions · 0.25.

Inputs: tier, RNG.
Outputs: starting fields per region; starting tech per faction.
Open flags: Q-022-02. Q-022-01 (Westley, 2026-09-14) confirmed per-archetype starting ranges are the design (Conqueror home military 50–65, economy 40–55), but Fortifier's and Opportunist's ranges are not specified anywhere (Q-022-02). R-022-05 below still describes the old same-ranges-for-everyone behavior until both archetypes' ranges are known.

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
- R-025-04  Given an extra edge would be drawn between the player's home or frontier and any NPC faction's home or frontier during generation, Then that draw is rejected and re-rolled (R-021-06's re-roll budget applies); this check does not apply between two NPC factions.

Inputs: generated graph.
Outputs: adjacency; a generation-time check that rejects and re-rolls a violating extra edge (R-025-04).
Open flags: none. Closed by Q-025-01 (Westley, 2026-09-12): the buffer is player-to-NPC only, checked at generation time only — NPC factions may end generation adjacent to each other, and any faction pair may become adjacent later through conquest or colonization (E-05, E-06).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Seed | Campaign start | any 64-bit integer | none |
| Region count range | Config | (40, 60) | count < 2 · factions + 1 fails generation |
| Factions per game | Config | 15 at launch | < 2 fails generation |
| Extra edge ratio | Config | 0.12 | < 0 fails generation |
| Population ranges, ratios, jitter | Config | as ALG-30 | ranges outside [0, 100] fail generation |
| Template choice | Player or random | [Q-021-02] | not applicable until Q-021-01 answers |

## Outputs

| Output | Observable where |
|---|---|
| Region list with id, tier, owner, fields, phase offsets | Strategic snapshot `regions`; save file |
| Adjacency and edge types | Strategic snapshot `adjacency`, `edge_types`; galaxy view filaments |
| Faction list with archetype, starting tech, confidence | Strategic snapshot `factions` |
| Generation report | T1 trace: seed, N, edge count, buffer check result |

## Invariants

- Every region reachable from every other.
- No home adjacent to a home; no foreign inhabited regions adjacent at generation.
- Each faction owns exactly two regions at tick 0.
- Same seed, same world, all platforms.
- Empty regions carry no fields and no owner until colonized.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): generate a 60-region world in under 5 ms; generation is O(N + E).

## Look and behavior references

None required in this epic. The galaxy view is E-16.

## Ways this could be wrong

- Generator consumes the RNG in a different order, so the same seed yields a different galaxy.
- Extra-edge loop links a home to a foreign frontier.
- Corridor chaining leaves a faction unreachable when the empty count is small.
- Edge type defaults to `both` for empty-region edges, letting empties count as trade neighbors.
- Frontier rolled from the home range.
- Factions all get the same phase offsets because the RNG was reseeded per region.

## Open ambiguity flags

Q-021-03 (how the three named templates apply across 15 factions), Q-022-02 (Fortifier and Opportunist starting field ranges). Details in `docs/northstar/ambiguity_register.md`. Q-021-01, Q-021-02, Q-022-01, Q-024-01, Q-025-01 are closed and folded above.

## Depends on

- E-02 Region fields (what a region's fields are).
- E-05 Faction agents (archetypes, colonize, conquest ownership changes).
- E-06 Diplomacy (peace and betrayal edge changes).
- E-08 Generational structure (the world persists across chapters; ruins accumulate).
