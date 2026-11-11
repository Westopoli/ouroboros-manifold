# E-07 — Civilizational Lifecycle

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 6 stories, 28 rules, numbers from `algorithms.md` ALG-41 through ALG-44. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | No open flags on this epic's stories. Q-220-02 (E-02 S-220) is cited; closed 2026-10-21 (register). |
| Every visible-surface story has a reference | Not applicable. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict:** no open flags; gate to be rerun. The flag that touched this epic, Q-220-02, closed 2026-10-21 (register).

## Purpose

Factions are born, grow, overreach, fracture, and die, and none of it is scripted. A revolt that entrenches, or an empire too large to govern, produces a new faction holding one region, hostile to everyone, carrying its parent's technology and a bite of its parent's army and economy. A region conquered recently may instead go home to its old owner when it revolts. A breakaway that never grows is quietly absorbed by its strongest neighbor. A faction with no regions is gone. The player's civilization is subject to all of it; when it falls, the generational structure (E-08) moves the player to another faction rather than ending the game.

There are no global eras. Each faction is in its own phase, expansion through equilibrium, and the sim can say which phase any faction is in from what it has been doing lately. That label feeds the chronicle and the mission generator so the player feels the age of the civilization they serve.

## Obviously working in 60 seconds

Take a region with military 40, economy 50, tension 70, population 60 owned by faction A, and fire Revolt Entrenched on it. With success roll in [0.50, 0.95] and population ≥ 25, a new faction `breakaway_<tick>_<region>` appears owning the region with military 16, economy 30, tension 40, population 60, hostile to all, tech equal to A's. Now do it to a region A conquered 10 ticks ago from faction B: half the time the region goes back to B instead. Leave a one-region breakaway alone for 50 ticks with budget under 20 next to a three-region neighbor: it is absorbed. Remove every region from a breakaway: five ticks later it is gone from the faction list.

## Stories

### S-049 — A revolt can birth a nation
Flag closed, rule text pending: Q-049-01, the parent faction's budget gains the stolen economy. The rule below is what the tests read today.
As a commander, I want a revolt that takes hold to create a new faction from the region, so that my enemies, and my own civilization, can come apart.

Rules
- R-049-01  Given Revolt Entrenched fires in an owned region, When resolved, Then one draw sets the success rate uniform in [0.50, 0.95] and a second draw must be ≤ that rate, else no faction forms.
  Proof: MISSING
- R-049-02  Given the success draw passes but the region's population is below 25, When resolved, Then no faction forms.
  Proof: MISSING
- R-049-03  Given a breakaway forms, When the region is split, Then the region keeps military · 0.40 and economy · 0.60 (the revolt takes 60 percent of the army and 40 percent of the economy), then tension is capped at 40, population floored at 25, economy floored at 20.
  Proof: MISSING
- R-049-04  Given a breakaway forms, When the faction is created, Then its id is `breakaway_<tick>_<region>`, archetype `breakaway`, budget 0, growth rate 0.025, attack confidence uniform in [2, 5], tech equal to the parent's, stance hostile with every faction both ways, and a color distinct from every existing faction's hue by more than 0.08.
  Proof: MISSING
- R-049-05  Given Admin Breakaway fires (E-05 S-040), When resolved, Then the success rate is 1.0 with no population check, and the archetype is one draw from conqueror, fortifier, warlord, opportunist, schism.
  Proof: MISSING
- R-049-06  Given an admin chain whose region changed owner after the chain started, When Admin Breakaway fires, Then nothing happens (the chain is pruned).
  Proof: MISSING
- R-049-07  Given the region's edges, When ownership changes to the breakaway, Then every edge touching it becomes `border`.
  Proof: MISSING

Inputs: fired faction-creating event; region fields; RNG.
Outputs: revolt record in the tick log; new faction entry; region owner.
Open flags: none.

### S-050 — Old loyalties
As a commander, I want a region I took recently to be able to go back to its old owner when it revolts, so that reconquest near a living enemy is a risk.

Rules
- R-050-01  Given a region conquered from B 15 ticks ago and B still exists, When a revolt succeeds there, Then with probability 0.5 (one draw) the region reverts to B instead of forming a breakaway.
  Proof: MISSING
- R-050-02  Given the conquest was 21 or more ticks ago, When a revolt succeeds, Then it never reverts.
  Proof: MISSING
- R-050-03  Given B no longer exists, When a revolt succeeds, Then it never reverts.
  Proof: MISSING
- R-050-04  Given a reversion, When applied, Then the region's owner is B, held-since is the current tick, previous owner is cleared, and the same split and floors as R-049-03 apply.
  Proof: MISSING
- R-050-05  Given a reversion, When the log is read, Then it records the original and restored factions and the stolen amounts.
  Proof: MISSING

Inputs: previous owner; held-since; registry; RNG.
Outputs: reversion record; ownership. Reversion on a revolt is the only allegiance change this epic has; where a populace contested in a mission ends up is Q-220-02 (E-02 S-220).
Open flags: none.

### S-051 — Nations that never were
Flag closed, rule text pending: Q-052-01, a starting faction with no regions is kept forever and marked as fallen. The rule below is what the tests read today.
As a commander, I want a breakaway that never grows to be absorbed by its strongest neighbor, and a faction with no land to disappear, so that the map does not fill with ghosts.

Rules
- R-051-01  Given a breakaway faction with zero regions, When 5 or more ticks have passed since its creation tick, Then it is removed from the registry and every faction's stance table.
  Proof: MISSING
- R-051-02  Given a breakaway with exactly one region, created 50 or more ticks ago, with budget below 20, When cleanup runs, Then its region passes to the bordering faction with the most regions, held-since resets, previous owner is the breakaway, and the breakaway is removed.
  Proof: MISSING
- R-051-03  Given the same breakaway with budget 20 or more, or with two or more regions, or created fewer than 50 ticks ago, When cleanup runs, Then nothing happens.
  Proof: MISSING
- R-051-04  Given a breakaway that conquered a region this tick, When cleanup runs, Then it is skipped this tick.
  Proof: MISSING
- R-051-05  Given a non-breakaway faction (starting faction) with zero regions, When cleanup runs, Then it is never removed.
  Proof: MISSING
- R-051-06  Given a removed faction still owned regions, When removal happens, Then those regions become unowned with held-since cleared.
  Proof: MISSING

Inputs: registry; region ownership; conquest list this tick.
Outputs: absorption records in the tick log; registry and ownership changes.
Open flags: none.

### S-052 — No plot armor
As a commander, I want my own civilization to be able to fall, so that the stakes are real and the chronicle can tell its end.

Rules
- R-052-01  Given the player civilization loses its last region, When the tick ends, Then it has zero regions, its budget still accumulates as 0, and the generational structure (E-08) handles the player's next chapter.
  Proof: MISSING
- R-052-02  Given any faction, When attacked, revolted, or absorbed, Then no rule anywhere checks whether it is the player's.
  Proof: MISSING

Inputs: none beyond E-05 and this epic.
Outputs: faction region count in the strategic snapshot.
Open flags: none.

### S-053 — Every faction has an age
As a commander, I want the sim to know whether my civilization is expanding, consolidating, at war, overextended, fragmenting, or settled, so that missions and the chronicle can speak to the moment.

Rules
- R-053-01  Given a faction's recent event window, When the revolt-and-reversion share of events is at least 0.02, Then its phase is fragmentation.
  Proof: MISSING
- R-053-02  Given not fragmentation, When maintenance (regions · 8) divided by total economy exceeds 0.4, Then its phase is overextension.
  Proof: MISSING
- R-053-03  Given neither, When the share of attack events is at least 0.05, Then conflict.
  Proof: MISSING
- R-053-04  Given none of the above, When empty regions bordering the faction number at least 30 percent of all inhabited regions, Then expansion.
  Proof: MISSING
- R-053-05  Given none of the above, When the window holds colonizations and no attacks, Then consolidation.
  Proof: MISSING
- R-053-06  Given none of the above, or a faction with no regions, Then equilibrium.
  Proof: MISSING
- R-053-07  Given the six checks, When evaluated, Then they are evaluated in exactly this order and the first match wins.
  Proof: MISSING

Inputs: recent event window; owned regions; world.
Outputs: phase label in the faction entry; consumed by E-09 and E-10. It does not feed the density of self-built settlements for now (E-02 S-222).
Open flags: none.

### S-054 — Where a civilization ends up
Flag closed, rule text pending: Q-054-01, S-054 stays deferred to post-launch and expansions; S-049 to S-053 are the complete launch lifecycle scope. The rule below is what the tests read today.
As a commander, I want a civilization's story to be able to end in survival, escape, or extinction with only relics left, so that the long arc has an ending.

Rules
- R-054-01  Deferred with the feature. No rule until Q-054-01 is answered.
  Proof: unbuilt

Inputs: none yet.
Outputs: none yet.
Open flags: none. Interim: history loops back to the first owned era after the last (E-20 R-148-03).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Faction-creating events | E-04 | Revolt Entrenched, Admin Breakaway | others ignored |
| Region fields, previous owner, held-since | E-02, E-05 | | |
| Registry | E-05 | | |
| Recent event window | Tick log | last N ticks [Q: window size is whatever the caller passes; the chronicle passes the time-jump window] | |
| RNG | World stream | | |

## Outputs

| Output | Observable where |
|---|---|
| Revolt, reversion, absorption records | Tick log `revolts`, `factions_absorbed`; chronicle |
| New faction entries and removals | Strategic snapshot `factions`; world view faction list |
| Phase label | Faction entry; mission briefing (E-10); chronicle (E-09) |

## Invariants

- A region has at most one owner; a removed faction owns nothing.
  Proof: MISSING
- A breakaway's tech at creation equals its parent's.
  Proof: MISSING
- Breakaway stances are hostile everywhere at creation.
  Proof: MISSING
- Same seed, same births and deaths, all platforms.
  Proof: MISSING
- Faction count never exceeds 15 plus the number of revolt and admin events that fired.
  Proof: MISSING

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): cleanup over 60 factions in under 50 µs per tick.

## Look and behavior references

None required in this epic.

## Ways this could be wrong

- Success roll made before the population check, or the population check reads the post-split value.
- Reversion draw made when the previous owner is dead.
- Breakaway colors collide with an existing faction.
- Absorption picks the neighbor with the most military instead of the most regions.
- Ghost removal counts from creation tick instead of the tick regions were lost.
- Phase order evaluated differently, so an overextended faction reads as conflict.

## Open ambiguity flags

Q-220-02 as cited in S-050. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-04 Events (the faction-creating templates).
- E-05 Faction agents (admin revolt roll; conquest sets previous owner and held-since).
- E-06 Diplomacy (stances for new factions; tech inheritance).
- E-08 Generational structure (player rotation when the player's faction falls).
- E-09 Chronicle (consumer of phase labels and lifecycle records).
- E-02 S-220 and S-222 (what a mission leaves in a region; whether the phase label feeds settlement growth).
