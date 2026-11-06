# Epics and stories audit, 2026-10-02: merged report

Four Engineer auditors read all 21 epics, the hub and the stories catalog against two sets of decisions: the layer, combat and movement decisions recorded by commit ce07e919 (Set L), and the economy, base and landscape decisions of 2026-10-01 and 10-02 (Set E). Brief: `BRIEF.md`. Findings, row by row with quotes and line numbers: `group_1_layers_combat.md`, `group_2_missions_maps.md`, `group_3_simulation.md`, `group_4_client_hub.md`.

## Totals

| Group | Epics | Contradicts | Stale | Missing | Touch | Rows |
|---|---|---|---|---|---|---|
| 1 | E-01, E-11, E-12, E-13 | 6 | 9 | 17 | 16 | 48 |
| 2 | E-10, E-14, E-15, E-17 | 15 | 16 | 25 | 20 | 76 |
| 3 | E-02 to E-08 | 1 | 0 | 12 | 13 | 26 |
| 4 | E-09, E-16, E-18 to E-21, hub, catalog | 9 | 25 | 27 | 32 | 93 |
| All | | 31 | 50 | 81 | 81 | 243 |

## What the audit found, by theme

1. **The economy has rules and no stories.** E-19 S-159 states the system in 21 rules. Nothing else in the bible knows about it: no worker, cost, resource or building in E-11; no economy screen or solo controls in E-16; no enemy economy in E-14; no era-pack contents for it in E-20; no base kinds, fallen-base rule or resource situation in E-10.
2. **E-17 describes a generator the project no longer intends to build.** Its stories rest on a hand-authored layout library and gradient sources. The approved landscape design is terrain-first, and S-166 adds height bands, landforms and self-built settlements. E-17 also never outputs what E-01 says the generator provides: slopes, a ground flag per layer, band heights, cover height.
3. **E-15's reinforcement structures are the old economy.** Free units, instant switching, no cost. They are now strongpoints paid for by the economy. Shipments and moving weather have no story.
4. **The layer decisions outran the client and the support epics.** The ping, going dark and reach by type have rules in E-01 and nothing in E-16 or E-18 (no alert, no sector, no controls, no visuals). No guard stance or hold-fire order exists. `algorithms.md` ALG-60 to ALG-68 predates the rewrite. E-21 still specifies a win-rate matrix where the lab uses margin and break-even.
5. **The simulation has nothing to hand the new systems.** A region has exactly four fields; no climate, landform or trouble. "Supply distance" is used and never defined. Nothing records what a mission leaves behind (a base occupied, the main base lost, damage, where the populace went).
6. **Scale.** Client budgets stop at 1,000 units; the long-term goal is thousands; workers are not counted anywhere.

## Holes in the decisions themselves

These are not stale text. The audit found places where two decisions meet and neither says what happens. Each needs Westley.

| # | Question | Why it matters |
|---|---|---|
| H1 | Space maps have no ground. How do height bands, "ground on all five layers", slopes and strongpoints apply in the Settled Reach? | The only era that exists is space. E-17 R-166-04 and R-166-06 as written cannot hold there. |
| H2 | Every launch unit flies. Walking units, slopes and strongpoints at slopes hold nothing until an era has walkers. Is a land era with walking units part of the first build, or do strongpoints mean something for flyers? | Decides whether the mountainside-city assault exists at launch. |
| H3 | What is "supply distance in the simulation"? | R-159-15 uses it to decide the kind of base. |
| H4 | The simulation fixes a mission's unit tier from the faction's technology (E-06 R-048-02). The economy player now chooses technology in the mission. How do the two relate? | A direct contradiction. |
| H5 | Are workers units? Do they count in the 20 to 40 roster and against the unit budgets? | E-11, E-16, E-18 scale numbers. |
| H6 | Are the "unit families" that counter each other the three categories (Strike, Line, Siege), the roles, or something new? | Sets the shape of Q-159-08, which resource each needs. |
| H7 | Teams of 2, 4 or 6 against lockstep's four peers. | E-19 contradicts itself. |
| H8 | On 2026-09-22: damage persists on short time jumps and rebuilds at the civilization's pace. On 2026-10-01 the economy persisting was withdrawn. Does the damage half still stand? | Decides what a mission writes back to the simulation. |
| H9 | Are a region's climate, landform and trouble stored in the simulation, or worked out from the seed when the map is made? | Stored means a change to the frozen sim contract. |
| H10 | Is the density field in the sim or only on screen? "Costs the sim nothing" and "functional as well as visual" were both said. | Decides whether dense districts slow units and give cover. |
| H11 | What is "the original main base" for an attacker, or in an archetype with no base (rear guard, evacuation)? | The partial-failure cap needs it. |
| H12 | Fitted bands make a layer step a different height on each map. Do transition times, cross-layer vision factors and reach stay fixed numbers, or scale with the step? | E-01 assumes a standard step. |
| H13 | The largest canvas: 32,000 wu in the decision, 28,000 in the code and R-116-01. | Which number is "today's size". |
| H14 | The map view allows only move and attack-move (E-16 R-161-02). Asking by pointing is a third kind of order. | Small, but a contradiction. |

Smaller points the auditors could not judge are listed at the foot of each group file.

## Proposed shape of the rewrite

Not yet done; for Westley to approve or change before any story is written.

**A new epic for the economy.** S-159 is one story holding a whole system inside the multiplayer epic. Proposed: **E-22 Economy and bases**, with S-159's 21 rules split into stories of testable size:

| Story | Holds |
|---|---|
| Resources and workers | three resources, workers, drop-offs, haul distance |
| Building and placement | lots, neighbours and yield, the city reshaping around placed buildings |
| Population | one cap for workers and soldiers |
| Production and the schedule | production buildings, planning ahead, retooling time |
| Counters | families, roles and their resources, reading the enemy's gathering |
| Disguise | hiding and disguising buildings |
| Technology | choice in the mission, and its tie to the faction's technology |
| Defenses and raid lanes | walls, gates, towers |
| Expansions and forward bases | growing settlements, forward production |
| Shipments | blind, from the civilization |
| When a base falls | occupation, retaking, falling back, the partial-failure cap |
| The economy without a player | doctrines, perfect hands and no foresight |
| The commander alone | the dial, the doctrine switch, asking by pointing, unit-mix switches |
| The enemy's economy | same rules, optional foresight |

E-19 keeps only the paired mode itself: the queue, team sizes, the universe lock, the wire, drop-out.

**E-17 rewritten terrain-first.** Retire the layout-library stories. New stories: terrain from a formula; water; landforms and the region's climate; height bands as layers with benched and natural ground; what the generator finds on the terrain (bases, objectives, resource sites, expansion sites, strongpoints, chokes, raid lanes); the density field and self-built settlements; space maps and land maps; continuous detail. S-166's rules move into these.

**Edits to existing epics.**

| Epic | Change |
|---|---|
| E-01 | fitted bands; ground fills the layers below; ground too steep to cross; sight and fire across layers blocked by ground and cover; whether a ping sees behind cover |
| E-02, E-03 | region climate, landform, trouble; supply distance; what a mission writes back |
| E-06 | faction technology against technology chosen in a mission |
| E-08 | what a pair carries forward (still open, Q-159-07) |
| E-10 | base kind by archetype and supply distance; the resource situation; fallen base and the cap |
| E-11 | workers; unit cost and resource; walls, gates and towers as things that fight and block; walking types |
| E-12 | fog for buildings and shipments; the elevation bonus against symmetric vision |
| E-13 | guard stance and hold fire; routes around buildings that appear and fall; slope edges |
| E-14 | the enemy's economy; layer commands for the enemy |
| E-15 | strongpoints replace garrisons; moving regional weather |
| E-16 | the economy player's screen; the solo commander's controls; ping and emit controls and alerts; the continuous zoom |
| E-18 | world detail by distance; settlements under construction; ping and emit visuals; budgets for thousands |
| E-20 | what an era pack must now carry |
| E-21 | margin and break-even in place of the win-rate matrix; libraries for the economy |
| Hub, catalog | the toolkit paragraph; catalog rows |
| `algorithms.md` | ALG-60 to ALG-68 |

**Order.** Holes H1 to H14 first, since the stories depend on them. Then E-22 and E-17, which everything else points at. Then the edits. Stories whose tests already exist (E-15 S-126, S-127 and others) are changed only with a ledger row, as the project's rules require.
