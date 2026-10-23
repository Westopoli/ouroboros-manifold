# E-06 — Diplomacy and Technology

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 8 stories, 46 rules, numbers from `algorithms.md` ALG-26 through ALG-28 and ALG-38 through ALG-40. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 2 open flags on S-227: Q-173-01 and Q-159-12 (held by E-22 S-173); Q-227-02 and Q-227-03 closed 2026-10-21 (register). S-042 to S-048 have none. |
| Every visible-surface story has a reference | Not applicable. Tech tiers change unit look; that reference belongs to E-11. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** S-227 (added 2026-10-02) has not been through the gate and is blocked on Q-173-01 and Q-159-12 (held by E-22 S-173); Q-227-02 and Q-227-03 closed 2026-10-21 (register). S-042 to S-048 have no open flags; gate to be rerun.

## Purpose

Factions are hostile, neutral, or cooperative toward each other, and that stance decides whether they fight, ignore each other, or trade. Nobody negotiates. Peace grows out of behavior: two neutral neighbors who leave each other alone long enough, with calm borders, may drift into cooperation. Cooperation is never safe: every tick each partner has a small chance to betray, higher when it is stronger at the border and under pressure at home, and a betrayal is an attack plus an instant flip to hostile.

Technology is one number per faction from 0 to 100 that grows with its economy, and each archetype spends that number differently: a conqueror turns it into attack, a fortifier into defense and economy. Cooperative partners pull the weaker one upward. Tech crosses three tier boundaries that change what the faction's units are, and a faction can fall back down.

## Obviously working in 60 seconds

Two neutral fortifiers share a quiet border with stability above 35. After 80 ticks with no attack between them an overture fires; with both dispositions at 2.0 it succeeds with probability min(1, 0.5 · compatibility · stability · 4). Their shared edges become `both`, each gains the other's adjacency bonus, and the lower-tech one gains 0.1 · gap/100 tech per tick. Replace one with a conqueror at tech 60 facing a partner at military 20 with its own border military 60 and average tension 60: the per-tick betrayal chance is 0.005 · 2.5 · 3.0 · 1.2 = 0.045, so within a hundred ticks it attacks the partner's weakest border region and the pair is hostile again.

## Stories

### S-042 — Three ways to feel about a neighbor
As a commander, I want every pair of factions to be hostile, neutral, or cooperative, and for that to decide who fights and who trades, so that the map has friends and enemies, not just targets.

Rules
- R-042-01  Given any two distinct factions, When their stance is read, Then it is exactly one of hostile, neutral, cooperative, symmetric for the pair; a faction's stance toward itself reads cooperative.
- R-042-02  Given a hostile pair, When agents decide and friction applies, Then each includes the other's regions as attack candidates and friction applies on their shared borders.
- R-042-03  Given a neutral pair, When agents decide and friction applies, Then neither attacks the other, no friction applies, and no adjacency bonus crosses their edges.
- R-042-04  Given a cooperative pair, When drift and tech run, Then adjacency bonus crosses their trade edges (E-02 R-015-03), tech convergence applies (S-047), and no friction or attacks occur.
- R-042-05  Given two starting factions, When the world begins, Then their stance is hostile if their archetype pair is in the override table (conqueror with anyone; fortifier with player and opportunist; opportunist with player; schism with player, fortifier, opportunist, warlord) and neutral otherwise; at launch every starting pair is hostile.
- R-042-06  Given a breakaway faction is created, When stances are set, Then it is hostile toward every existing faction and every existing faction is hostile toward it.

Inputs: archetype pairs; stance table.
Outputs: stance table in the strategic snapshot; faction list panel (E-16) colors relationships.
Open flags: none.

### S-043 — Peace grows out of quiet
As a commander, I want two neutral neighbors who leave each other alone to drift into cooperation, so that alliances emerge from behavior and not from menus.

Rules
- R-043-01  Given a neutral pair that shares at least one border edge, When a tick passes with no attack between them, Then their non-aggression counter increments by 1; an attack between them resets it to 0.
- R-043-02  Given a neutral pair that shares no border, When ticks pass, Then the counter does not move.
- R-043-03  Given the counter reaches 80, When peace formation is checked, Then an overture fires if both sides' average border-region stability is at least 35; otherwise the counter resets to 0 with no overture.
- R-043-04  Given an overture between factions with average economies 60 and 40, minimum border stability 50, dispositions 2.0 and 1.5, When success is rolled, Then p = min(1, 0.5 · (1 − 0.2) · 0.5 · 2.0 · 1.5) = 0.6, one draw.
- R-043-05  Given the overture succeeds, When applied, Then the pair becomes cooperative, cooperative-since is the current tick, and every shared edge becomes `both`.
- R-043-06  Given the overture fails, When applied, Then the pair stays neutral and the counter resets to 0.
- R-043-07  Given dispositions, When read, Then conqueror 0.1, fortifier 2.0, warlord 0.2, opportunist 1.0, schism 0.3, player 1.5, breakaway 0.8.

Inputs: stance table counters; border stability; economies; dispositions.
Outputs: diplomatic events in the tick log; stance change; edge changes.
Open flags: none.

### S-044 — Peace is never safe
Flag closed, rule text pending: Q-045-01, the betrayal attack commits the betrayer's full budget at surprise efficiency (half efficiency, 0 defender warning window). The rule below is what the tests read today.
As a commander, I want a cooperative partner to be able to turn on me when it is stronger and under pressure, so that peace is a bet and not a guarantee.

Rules
- R-044-01  Given a cooperative pair, When betrayal is checked, Then each faction rolls once per tick as the potential betrayer, in pair order, and at most one betrayal happens per pair per tick.
- R-044-02  Given a conqueror with border military 60 facing a partner's border military 20, average tension 60, When its chance is computed, Then p = 0.005 · 2.5 · min(3.0, 3.0) · max(1, 1.2) = 0.045.
- R-044-03  Given the partner's border military is 0, When computed, Then the opportunity factor is 3.0.
- R-044-04  Given border military 20 facing 60 and tension 20, When computed, Then opportunity = 1.0 and pressure = 1.0, so p = 0.005 · weight.
- R-044-05  Given weights, When read, Then conqueror 2.5, fortifier 0.3, warlord 2.0, opportunist 2.0, schism 1.5, player 0.5, breakaway 1.0.
- R-044-06  Given a betrayal fires, When applied, Then the pair is hostile at once, every shared edge becomes `border`, and the betrayer attacks the victim's weakest bordering region.
- R-044-07  Given the betrayal attack, When resolved, Then [Q-045-01 decides commit and mode: current code commits the betrayer's entire budget at full efficiency; the bible says a surprise attack].

Inputs: stance table; border military; tension; weights.
Outputs: betrayal event; attack resolution; stance and edge changes.
Open flags: none.

### S-045 — A faction's technology is one number
As a commander, I want each faction's technology to be a single level that grows with its economy, so that a thriving civilization pulls ahead and a ruined one stalls.

Rules
- R-045-01  Given a faction with average economy 60 and average population 50, When tech grows, Then Δtech = 0.35 · 0.6 · 0.5 = 0.105.
- R-045-02  Given average population 10, When tech grows, Then the population factor is 0.3, not 0.1.
- R-045-03  Given tech 99.95 and growth 0.105, When applied, Then tech is 100.0.
- R-045-04  Given a faction with no regions, When tech grows, Then nothing changes.
- R-045-05  Given a starting faction, When tech is set, Then it equals the average starting population of its regions · 0.25.
- R-045-06  Given a breakaway is created, When its tech is set, Then it equals the parent's tech at that tick.
- R-045-07  Given a faction whose average economy over its inhabited regions is below 20.0, or whose average population has fallen by 10.0 or more over the last 50 ticks, When the technology step runs on a tick at least 100 ticks after its last Knowledge Lost, Then one uniform draw is made and if it is below 0.03 a Knowledge Lost event fires: tech −5.0 (floored at 0), a fired-event record with template Knowledge Lost, the faction's highest-population region, and the next chain tag, and the faction's last-Knowledge-Lost tick set to now.
- R-045-08  Given a faction not eligible under R-045-07, When the technology step runs, Then no draw is made and tech never falls.
- R-045-09  Given a 5,000-tick run with 50 factions and the launch config, When Knowledge Lost events are counted per 50-tick window, Then the mean over all windows is between 1.0 and 2.0; individual windows may be far outside that (the rate is stochastic and only the mean is asserted).

Inputs: owned regions' economy and population.
Outputs: tech level in the faction entry.
Open flags: none. Knowledge Lost is stochastic and its constants (eligibility 20.0 economy or a 10.0 population fall over 50 ticks, probability 0.03 per eligible tick, tech −5.0, cooldown 100) are a first tuning; R-045-09 is the target Westley set and the number to retune against.

### S-046 — Archetypes spend tech differently
Flag closed: Q-048-01, the economy multiplier is wired into ALG-05 growth. The rule below is what the tests read today.
As a commander, I want a conqueror's technology to show up as firepower and a fortifier's as walls and wealth, so that the same number tells different stories.

Rules
- R-046-01  Given a conqueror at tech 60, When multipliers are read, Then attack 1.096, defense 1.012, economy 1.012.
- R-046-02  Given a fortifier at tech 60, When read, Then attack 1.018, defense 1.054, economy 1.048.
- R-046-03  Given any archetype at tech 0, When read, Then all three multipliers are 1.0.
- R-046-04  Given the attack multiplier, When an attack resolves (E-05 S-037), Then effective attack is multiplied by it; the defender's defense multiplier multiplies effective defense.
- R-046-05  Given the economy multiplier, When a faction's budget accumulates (E-05 R-033-01), Then the gain is scaled by it (DEC-C15-2026-10-22).

Inputs: archetype; tech.
Outputs: multipliers used in attack resolution.
Open flags: none here. The mission-level economy (E-22) reads the faction's economy and technology tier for its starting scale (E-05 R-226-01).

### S-047 — Friends share knowledge
As a commander, I want the weaker partner in a cooperative pair to catch up toward the stronger, but never past it, so that peace has a tangible reward for the one who needs it.

Rules
- R-047-01  Given faction A at tech 30 cooperative with B at tech 70 and C at tech 50, When convergence runs for A, Then bonus = 0.1 · 40/100 = 0.04 from B only.
- R-047-02  Given A at tech 70 and every partner below 70, When convergence runs, Then bonus is 0.
- R-047-03  Given A and B neutral or hostile, When convergence runs, Then bonus is 0.
- R-047-04  Given tech growth and convergence on the same tick, When applied, Then growth applies first, then convergence reads the updated levels in faction order.

Inputs: stance table; partner tech.
Outputs: convergence record in the tick log.
Open flags: none.

### S-048 — Three tiers of technology
As a commander, I want my faction's units to change in kind, not just in number, when its technology crosses a tier line, and to fall back if it slips, so that progress and decline are visible on the battlefield.

Direction changed 2026-10-02, rewrite pending: a mission's starting technology is derived only slightly from the simulation's technology level, and what technology does in a mission is undecided (E-22 S-173, Q-159-12; the reconciliation is S-227). The rules below are what the game does today.

Rules
- R-048-01  Given tech in [0, 34), When the tier is read, Then it is 1; in [34, 67) it is 2; in [67, 100] it is 3.
- R-048-02  Given a faction crosses from 33.9 to 34.1, When the next mission generates its forces, Then units use the tier 2 profile; units already fielded in a running mission do not change.
- R-048-03  Given a faction's tech falls from 67.5 to 66.5, When the next mission generates forces, Then units use the tier 2 profile.
- R-048-04  Given a tier change on tick t, When the chronicle distills the window containing t, Then a tier-transition entry is a candidate (E-09).

Inputs: tech; tier boundaries [0, 34, 67].
Outputs: tier in the faction entry; unit profile selection (E-11); chronicle candidate.
Open flags: none. The per-tier unit profiles are E-11 content.

### S-227 — A mission starts from the faction's technology, only slightly
As a commander, I want the technology my side starts a mission with to follow the faction's technology only a little, so that a long campaign shows in the field without deciding the match before it starts.

Decided in part 2026-10-02 (DECISIONS H4); the rest is open. Not scheduled for building. What technology does is E-22 S-173 (Q-159-12).

Rules
- R-227-01  Given a mission generates, When a side's starting technology is set, Then it is derived from the faction's technology level (S-045), only slightly [Q-173-01: the mapping from the faction's number to the mission's starting technology, and how slight is slight].
- R-227-02  Given an era has a wide range of technology levels (for example 1 to 5), When a normal timed single match is played, Then a side has time to climb one or two levels, as a tech-up does in StarCraft 2.
- R-227-03  Given a mission ends, When the technology a side reached in it is read, Then [Q-227-02: whether anything flows back into the faction's number (S-045), and whether Knowledge Lost (R-045-07) touches a mission's technology].
- R-227-04  Given the three tiers of R-048-01 and an era's range of levels, When both are read, Then [Q-227-03: how the three tiers relate to the era's levels, for example 1 to 5].

Inputs: the faction's technology (S-045); the era's range of levels.
Outputs: a mission's starting technology (E-10 mission generator, E-22 S-173).
Open flags: Q-173-01, Q-159-12. Q-227-02 and Q-227-03 closed 2026-10-21 (register: nothing flows back; tiers stay the coarse sim reading).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Stance table | Diplomacy state | one entry per unordered pair | missing pair reads hostile |
| Border stability, economy, military, tension | E-02 | [0, 100] | |
| Dispositions, betrayal weights, tech weights | Config per archetype | as `algorithms.md` | unknown archetype: disposition 1.0, weight 1.0, tech weights 0 |
| Tick log of this tick | Tick loop | | |
| RNG | World stream | | |

## Outputs

| Output | Observable where |
|---|---|
| Stance table, counters, cooperative-since | Strategic snapshot; save file |
| Overture and betrayal events | Tick log `diplomatic_events`, `betrayals`; chronicle |
| Tech level, tier, multipliers | Faction entry; world view faction data panel; unit profiles in missions |
| Convergence records | Tick log `tech_growth` |

## Invariants

- Stances are symmetric.
- Cooperative implies every shared edge is `both`; hostile implies every shared edge is `border`.
- Tech in [0, 100]; never rises by more than 0.35 + 0.1 per tick.
- Convergence never lifts a faction above its best partner.
- Same seed, same diplomacy, all platforms.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): stance updates for 105 pairs (15 factions) in under 50 µs per tick; betrayal and peace checks O(pairs · border regions).

## Look and behavior references

None required in this epic.

## Ways this could be wrong

- Counter increments for pairs that share no border.
- Overture rolled before the stability check, consuming RNG on a reset.
- Betrayal opportunity computed from whole-faction military instead of border regions.
- Both partners betray in the same tick.
- Convergence pulls toward the sum of partners instead of the best one.
- Tier computed with inclusive upper bounds, so tech 34.0 reads tier 1.
- Breakaway tech copied before the parent's growth this tick, or not copied at all.

## Open ambiguity flags

Q-173-01, Q-227-02, Q-227-03 (S-227), with Q-159-12 held by E-22 S-173. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-02 Region fields (stability, economy, tension inputs).
- E-03 World generation (border edges, edge type changes).
- E-05 Faction agents (attack resolution for betrayals; tech multipliers consumed there).
- E-07 Civilizational lifecycle (breakaway creation sets stances and tech).
- E-11 Units (tier profiles).
- E-22 Economy and bases (S-173 technology in a mission, S-227).
- E-10 Missions (the mission generator that sets a mission's starting technology, S-227).
