# StarCraft 2 movement and targeting, against our rules (2026-11-11)

Requested by Westley: find out what StarCraft 2 does, report, and after his approval write it into the bible and check the stories against it. Two researchers read the wiki's rule pages, Blizzard's guides and the map editor's documentation. Their notes, with every claim marked verified (page read, link), reported (second hand) or unverified, are beside this file: `2026-11-11-starcraft2/appendix-a-targeting.md` and `appendix-b-movement.md`. Nothing in the bible has been changed by this report.

Limits: the wiki cut the researchers off after a few pages, and two other sites refused them. Five behaviours are documented nowhere they could reach (section 4). The numbers below are StarCraft 2's; ours are in world units (wu) and are Westley's.

## 1. What StarCraft 2 does (verified unless marked)

Targeting
- **Which orders auto-target.** Stop (idle), hold position, patrol and attack-move. Not move, and not attack-this-target.
- **How far a unit notices an enemy.** Its weapon range plus a small margin: the larger of 5 or weapon range, raised for most ground units to weapon range + 0.5. It is not sight range. The same distance applies whether the unit is idle, holding, patrolling or attack-moving.
- **Which enemy it picks.** In order: an enemy that can hurt it before one that cannot; then the higher priority class (fighting units and defences before other buildings); then one its main weapon can hit; then, only when it has just lost its previous target, the closest. Closest is the last tie-break, not the rule.
- **When it changes target.** It keeps its target until the target stops being valid (dies, turns invisible, goes up a ramp out of sight), leaves weapon range, or a more important target comes in. A nearer enemy of equal importance never takes over.
- **Chasing.** An idle unit engages and chases what attacks it; the editor has a leash distance after which it gives up and walks back to where it stood (no number published). Hold position fires at what is in range and never moves.
- **Being hit.** Idle fighting units fight back, non-fighting units flee. Hold position does neither. An attack-moving unit ignores what it cannot attack.
- **Firing while moving.** Ordinary weapons stop to fire. A few special weapons may fire on the move; none is named in the sources.
- **High ground.** High ground sees low ground. Ground units below cannot see or target ground units above until something gives them sight. A unit that attacks from above shows where it is, without giving sight of itself. The old miss chance is gone (reported).

Movement
- **Move** ignores enemies. **Attack-move** attacks what comes within its notice distance on the way and continues to its point after a kill.
- **Pushing.** Allied units push each other aside by a per-unit priority number; a unit on hold position resists being pushed; enemy units are never pushed.
- **Obstacles.** Buildings block ground paths.
- **Ramps.** Halfway up a ramp a unit gains its full view of the top.
- **Arrival.** Units ordered to one point clump there; each moves at its own speed.

## 2. Where our rules already match

| Behaviour | Ours |
|---|---|
| Move never acquires; a player order wins | R-087-02, R-096-01 |
| Attack-move resumes toward its point after an engagement | R-096-02, R-087-06 |
| A nearer enemy does not take a held target | R-087-03 (Westley 2026-11-08, confirmed 2026-11-11) |
| A target that dies or is lost from sight ends the lock | R-087-03 |
| A chase has a leash and the unit returns to where it stood | R-087-05, DEC-leash-anchor-return-2026-11-01 |
| A unit stops to fire | R-087-04, R-096-02; built in Round 1 |
| High ground sees down, low ground does not see up; the view opens at the ramp's halfway line | R-005-09; Westley 2026-10-05, 2026-10-22 |
| Idle friendly units step aside for moving ones | DEC-Q087-02-2026-10-22 |

So the thing Westley saw on 2026-11-11, blue ignoring a Warden that walked up close, is also what StarCraft 2 does when both targets are of equal importance.

## 3. Where our rules differ, each needing his word

**A. How far a unit notices an enemy.** StarCraft 2: weapon range plus a small margin. Westley 2026-11-11: "within attack radius, not vision radius", which agrees. Our rule text says sensor radius (R-087-04) and a decision says the larger of sensor and weapon range (2026-11-01); both are wrong by this.
- What changes in play: a Vanguard sees at 700 wu and shoots at 300. Today it walks toward an enemy seen at 600. Under StarCraft 2's rule it stands until the enemy is at about 300.
- This retires Westley's 2026-11-01 sentence ("whenever a unit sees an enemy unit ... it attacks the unit it sees in its vision") and his 2026-10-20 line that an attack-mover goes for the closest target in its vision regardless of direction.
- The margin matters: on 2026-11-01 two formations stood 5 wu out of range of each other for ever. StarCraft 2's margin is 0.5 on a typical range of 5, one tenth. A tenth of our 300 wu is 30 wu, which covers that case. The number is his.
- Recommendation: adopt StarCraft 2's rule with a margin of one tenth of the weapon range as a draft.

**B. A target that walks out of weapon range.** StarCraft 2 drops it and picks again. Westley's ruling lists three ways a lock ends (sight lost, death, his order) and not this one. Without it, and with A, a unit would keep chasing a target it noticed at 300 out to its leash.
- Recommendation: add "leaves weapon range" as a fourth way a lock ends, as StarCraft 2 has it; the leash then governs only chasing an attacker.

**C. Threat first.** StarCraft 2 picks an enemy that can hurt the unit before one that cannot, and switches to one when it comes in range. We pick by distance alone, so a unit will shoot a nearer supply unit while a Bombard shells it.
- Recommendation: adopt it: among enemies in notice distance, those that can hurt the unit come first, then the nearest; a threat arriving takes over from a non-threat. This is the only case where a target changes without the lock breaking.

**D. Priority classes.** StarCraft 2 ranks fighting units and defences above other buildings. We have no buildings in fights yet (the economy is unbuilt).
- Recommendation: note it in the economy epic for when structures become targets; build nothing now.

**E. Shots and bodies.** In StarCraft 2 units do not block each other's shots (unverified, but no source says they do). Ours: a line of fire is blocked by units, cover or ground, and the unit looks for a firing spot (R-087-09, Westley 2026-10-07).
- This is a deliberate difference and is already his rule. Recommendation: keep it, marked in the bible as a difference from StarCraft 2.

**F. Guard.** StarCraft 2's hold position never moves. Our guard steps up to 200 wu from its post (R-096-08, Westley 2026-10-13 and 2026-11-08).
- A deliberate difference, already his rule. Recommendation: keep it, marked as a difference.

**G. An attacker shows itself.** In StarCraft 2 a unit firing from high ground shows its position to its target without giving sight. We have no such rule; our unit hit by something unseen moves 200 wu away (R-087-01, Westley 2026-11-06).
- Recommendation: keep his rule; decide later whether the attacker's position should show on the map (a client question).

## 4. Not documented anywhere reachable

1. What an idle fighting unit does when hit by something it cannot see or reach. (Ours: moves 200 wu away, R-087-01.)
2. What happens when a destination cannot be reached, or the path is blocked by units that will not move.
3. The group-move rule (units keeping their relative places when the click falls inside their group). Only Brood War numbers exist.
4. How far apart a group settles on arrival, and when a unit counts as arrived.
5. The leash distance and how often a unit re-checks its target.

For each the choice is Westley's ruling or a few minutes in the game itself. Until then our existing rule stands where one exists (1 and 5), and the rest stay open questions.

## 5. What happens after approval

- The bible: rewrite R-087-03, R-087-04, R-087-05 and R-087-08 for A, B and C; mark E, F and G as differences; correct the two decisions; one `Q-` row for each of the five undocumented items that has no rule.
- The stories and tests: every rule and test under engage-on-sight, the lock and the leash checked against the new text (the audit of 2026-11-11 already lists them); tests first, then the engine change, as one small piece after Round 2.
- The lab: fights will change again (units no longer walk toward everything they see), so the stage 4 pictures are re-made once more after that piece.
