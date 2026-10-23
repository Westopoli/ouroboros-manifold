# Audit: the tactical rules against the goal of strategic depth, 2026-10-04

Requested by Westley, 2026-10-04: audit the current rules "against the intent of the goal of inducing strategic depth based on the pillars that define skilled gameplay and our method of measuring it based in research on military strategy. There's been several compacts since work has started, and I feel that we've lost the focus a little bit. This audit is meant to align us."

Read-only audit, origin/main at 69adce65. Nothing is decided here; rule meaning and numbers are Westley's. Verdicts below are read from rule text and the code where a rule is ambiguous; no fight was run. Where a claim rests on arithmetic from the unit table it says so.

## 1. Largest misalignments, in order

1. Seeing is not shooting, and shooting is not closing. Every non-Siege unit senses 700 to 1,000 wu and fires at 200 to 350 wu; after A199 sight changes nothing a unit does. S4 (find the enemy first) has nothing to buy except for Siege, the ping and cross-layer sight.
2. Fights end in standoffs the players did not choose (A199 with R-096-02): the group ends once every member has engaged, idle survivors engage only inside attack range, nobody closes. Firing is taken away by a rule gap, and the instrument then drops these fights as "stalemate" instead of scoring them.
3. Landscape (S1) and layers (S3) are absent from the game as it stands: no generated map content (P4 held), reach by layer defaults to 0 up and 0 down, the provisional layer numbers are the design chat's, not his. The two skills the goal names first and third cannot yet change a firing count in play.
4. Formation (S2) is weak by geometry and taxed by rules: ranges of 200 to 350 wu cover 7 to 12 slot widths so almost everything fires in a blob as well as a line; the scatter fallback (R-095-03) collapses a line of about 30 units or more; give-up (R-099-05) leaves rim units pacing.
5. The exposed side has no reply at all. Fire needs sight (R-008-04), firing never reveals (R-007-03), an unseen attacker makes the victim flinch away (R-087-01). The theory says a hidden side's edge is bounded (about sqrt 2, or 100 percent more kill rate at zero information); here the exposed side's kill rate is zero, which is unbounded.
6. Unit-type matchup (S5) is the only skill that works by rule alone and is probably dominant: a 7.5 to 1 category edge (Strike over Siege, 1.5 against 0.20) beside 2 to 1 edges elsewhere, with Q-081-01 (0.20 or 0.75) still open.
7. The measure cannot see the failures above: the firing count is binary, same-layer only and unweighted; stalemate and cap fights are excluded from decided cells; the lab runs with abilities off while the game runs them on; a one-hp survivor of 16 reads "even" under the 0.05 margin.
8. Identical forces do not tie (one Raider mirror, 94 to 66, finding g): a tie-break (id order, cohort order, spawn order) decides a fight no player influenced; C0 depends on this being cleared.
9. Several rules contradict each other or the code: group pace is "base speed" in R-095-01 but effective speed (0 when braced or in backswing) in the code; ALG-62 still describes pursuit on sight; guard is closed in R-096-08 and open in S-208; hiding in a storm blinds the hider (R-090-03).
10. Nothing implements the research's cheapest depth: a hold-fire order (ambush), a partial-information reply for the exposed side, and a scoring of cap fights.

## 2. The intent, in one place

- Goal (Westley, 2026-10-01): "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force".
- Principle (2026-09-30): "the differentiator is **can your unit get shots off**"; "the number that we really care about is number of units firing, if A and B both have the same number of units firing than the engagement ends up even"; and "it depends on the number of units that can get shots, not a basic ratio".
- A number that decides a fight against the firing count is "a number that's off" (plan, Part 1).
- Unit type is the one other factor: "not just unit values but their type as well" (2026-09-30).
- Refusing a fight counts: "a skilled player only takes a battle that they can win, skilled players make it so that the opponent doesn't have a choice" (2026-10-01). A play needs a counter on most maps, not all.
- Position: "A real battle isn't going to be a line feeding into each other, it's going to be a blob if they're mediocre players, or a spread out line if they're skilled players" (2026-10-02).

## 3. Skill by skill (question 1)

Theory column names the principle from `docs/legacy/topics/lanchester_and_combat_theory.md` (L) and `active_layer_vision_mechanics.md` (V). "Firing count" means units able to fire, through time.

| Skill | The play | Rules that carry it | Rules that fight it | Theory predicts | Verdict |
|---|---|---|---|---|---|
| S1 landscape | Hold a choke; top of a slope; behind tall cover | R-097-01 (cells blocked above density 0.7); R-098-02 (walls and cover block fire as they block sight); R-007-01/02 (cover by height); R-096-08 guard (holds post, never pursues); E-13 S-207 slopes (land only, not scheduled) | Map content with chokes is held (P4, A125); R-007-07 cross-layer cover open (Q-007-01); R-098-01 friends never block fire so depth is not a jam; sensor 700 vs range 300 means cover cannot hide a held line from sight before fire | A cap on engaged width switches square to linear: with both below the cap the fight is square; above, linear; a one-sided cap worsens the other's parity by mu(2-mu), half engaged gives 3/4; Kress narrow passage needs attackers of about the square of the defender (L section 1). Reserves wait unexposed and replace casualties | Absent in play (mechanism ruled and partly built, no map has the play); unknown until a hand-placed map is measured |
| S2 formation | Spread to full width; concave; ranged behind screens | R-095-01/02 slots from centroid offsets; R-087-04 (A199) holds slots until in attack range; R-098-01 back rank fires over front; R-087-03 nearest target so a screen is the target | R-095-03 scatter (every unit to the raw click if any is over 450 wu from the centroid); R-099-05 give-up only within 75 wu of the slot; R-097-10 stopped units push moving ones; R-096-02 group ends after all engage; ranges (200 to 350) are long against line widths | Frontage matters only when it caps engagement; with long reach almost everything engages and the law is square regardless of shape (L section 1). Focus fire raises the attrition exponent (about 1.56, StarCraft fit) | Weak. Shape survives to contact since A199, but the geometry gives little and the group rules cost it back. Toy found 3 units in 16 for a line over a blob, a concave 1 over a line (README section 10, not re-measured) |
| S3 layers | Ping before committing; go dark; place each type where its reach covers them and theirs does not | E-01 R-004-01/02 (transition time, exposed halfway), R-162 (ping, alert and 60-degree sector), R-163 (emit or silent), R-164-01 reach table, R-005 vision by layer distance, R-008-04 | Reach defaults to 0 up and 0 down in the built-in roster (cascade brief, section 5); numbers are the design chat's, unconfirmed (brief section 6); ping is free (R-162-02) with only a 20 s cooldown per unit and Q-005-04 asks what limits spam; R-001-05 engine picks the layer on the route; Q-008-03 damage and range by offset open; E-01 R-007-07 | Height is initiative, not a number (Malan, Shaw): the lower side "work below the bogey, make it come down to engage"; a layer wins by making the other side commit and pay; V: free reveals are underused when priced low and a forced layer feels like a tax when the game chooses it | Absent in the shipped defaults; the mechanisms are rules, the effect on the firing count is unknown |
| S4 enemy position | Find first and fire first; bait into a trap; ambush | R-089-01 sight; R-093-02 fire needs sight; R-162-03 pinged side is alerted (Hughes' alertness); R-084-01 first attack ready on the tick the target is first in range (first strike goes to whoever gets the target in range first); R-087-05 leash lets a bait pull | Sensors exceed ranges for every non-Siege type (Raider 800/200, Interceptor 1000/250, Vanguard 700/300, Warden 800/350); A199 removes pursuit on sight so sight moves nobody; no hold-fire order (R-208-02, Q-208-01 open) so an ambush cannot wait; R-208-01 guard steps up on sight; R-090-03 storm blinds the hider only | First detection is a one-time head start: undetected for one mean kill time lifts the win chance from 0.50 to about 0.82 (L section 3); the hidden side's edge is bounded (sqrt 2 in Deitchman's normal form); scouting decides who attacks effectively first (Hughes) | Weak for the six Settled Reach types on the same layer (the only live S4 is Siege plus a spotter, cross-layer sight and the ping); absent for ambush and bait |
| S5 unit-type matchup | Line each type against the one it beats; keep the vulnerable one away | R-081-01 matrix (1.5, 0.75, 0.20 in code); R-082-02 speed order; R-084 flat damage; R-087-03 nearest target; Q-008-07 asks how the measure weights it | Q-081-01 (Siege to Strike 0.20 in code, 0.75 in the bible); nearest-target pulls fire onto the screen not the intended victim; group pace R-095-01 slows Strike to Line pace | Quality enters the square law as a multiplier on the square: a 2 to 1 numbers deficit needs 4 times the effect under square, 2 times under linear | Works, likely dominant (see section 6, question 4) |

## 4. Rules that decide a fight against the firing count (question 2)

"Numbers that are off", or firing removed for a reason no player controls. Each is stated as the rule, then what it does.

| Rule | Effect |
|---|---|
| R-087-04 (A199) and R-096-02: attack-move halts only for an enemy in attack range; the group ends once every member has engaged | After a clash, survivors stand out of range and fire zero. Not a player decision; only a re-order restarts the count. The harness reports 3 of 480 formation fights at the tick cap (A201) |
| R-099-05 gives up only within 75 wu; R-097-10 stopped units are immovable | Units walled in by stopped friends further than 75 wu from their slot push or pace; a 32-unit crowd at 30 wu spacing has a radius of about 90 wu (arithmetic from the spacing), so the rim paces. A unit that stopped 100 wu short would still be inside range 200 to 350 and firing; one that paces does not |
| R-095-03 scatter fallback | Any unit over 450 wu from the centroid sends every unit to the raw click. A straight line spans 450 wu half-width at about 31 units at 30 wu spacing; fewer at wider spacing. The skilled formation (a spread line) is the one it breaks, at the size where skill should pay most |
| R-095-01 pace (finding b) | Text: "capped at the slowest member's base speed, fixed at order time". Code (`unit.c`, `om_unit_effective_speed`, called by the group order in `tactical_move.c`): 0.0 during backswing, and 0.0 for a Vanguard in any Brace phase. A group ordered while one member is in backswing or braced gets speed cap 0. Rule and code disagree; the base-speed reading is the text |
| R-007-03, R-008-04, R-087-01 | The hidden side fires; the exposed side cannot, and flinches 200 wu away. Unbounded edge, against the theory's bounded one. It follows Westley's ruling "no blind fire" (README section 6), so the tension is between that ruling and the research |
| R-086-03 Brace (damage taken times 0.5, dealt times 1.3, immobile) with R-084-01 reduction sum capped at 0.9, R-086-06 Fortify 0.20, R-083-03 Warden 0.10 | Multipliers that move a fight without moving the firing count. Westley: "let's leave specific abilities out of this calculation for now" (2026-09-30), but the engine runs them; the lab turns them off (`om_tactical_disable_abilities`) |
| R-081-01 matrix | Legitimate (type weights each shot) but Siege to Strike at 0.20 makes a Bombard nearly harmless to a Raider (17.5 x 0.2 = 3.5 per 3.0 s) whatever the firing count |
| Identical forces, one side 94 to 66 (finding g) | Order of acquisition by id and cohort (R-087-08), spawn order, or simultaneous resolution (A178) gives one side the first volley. A control that is not a tie |
| ALG-76 rout at 0.35 of starting hit points (enemy macro force only) | A force stops fighting at 65 percent loss regardless of what its units could still shoot; applies to the enemy only. Missions only; the lab fights to annihilation. Flagged, not weighed |
| Harness: `max_ticks` 6,000 (8,000 at 32 a side), quiet stalemate at 400 ticks | Instrument limits, not game rules, but they set which fights count (section 7) |

## 5. Rules that remove decisions, and rules that demand busywork (question 3)

Removing decisions (the engine does the skilled thing, so skill cannot show):

- Target choice: nearest, kept while alive and in range (R-087-03). Westley (A125, 2026-10-02): "I had imagined that units would only... just fire at the closest unit and we wouldn't have any other way. And I want to retain that." Focus fire as a lab switch gained 0.3 to 0.4 units in 16 (A200). Attack-target (R-096-04) is already the player's way to focus. Theory: focus fire is what raises attrition above order 1 (StarCraft 1.56).
- Layer along a route: the unit "takes the shortest route to its goal across layers" (R-001-05); the player holds a layer only by a preference (S-003). Research reason 3 for a layered game feeling like a gimmick: "the game chooses the altitude for the player" (V section 3).
- Retreat from unseen fire (R-087-01) and return fire (R-087-06): automatic.
- Leash (R-087-05): the engine decides how far a fight pulls a unit (200 wu from its anchor).
- Formation: slots are offsets from the centroid at order time and never updated (R-095-02); shape is whatever was arranged before the order. By design, but it makes S2 a pre-order skill.

Demanding busywork (the player must re-issue to get sensible behaviour):

- A199 and R-096-02: re-issue attack-move after every clash. Each re-issue builds a new group from the current positions, so the offsets are those of the survivors; with R-095-03 a spread group scatters. Chains of re-orders are what keep a line a line.
- R-099-05: units outside 75 wu of a blocked slot keep pacing until re-ordered.
- Ping (R-162-02): 20 s per unit, so holding vision means rotating pingers; free of cost so there is no decision beyond when.
- Brace toggles with a 2 s windup (R-086-03) and a group speed cap that is 0 while it lasts (finding b).
- A fast element must be split off by hand (R-095-06); a retreat of a mixed group runs at the slowest member's pace (R-095-01) and Strike enemies are faster than every Line unit (R-082-02), so refusing a fight with a mixed group is the hard case.

A199 in both directions. What it protects: formation is the player's choice (A198 traced the shape being lost at ticks 1 to 4, when sides spawn inside each other's sensor range); Westley (2026-10-03): "Attack move should hold formation until shooting, yes, rather than sight. But this is something we might change when it comes to play testing." What it costs: sight stops mattering to movement (S4); the first side whose units come into range gets the first volley; the post-clash stand-off; and re-ordering as the only recovery. The cost falls where the research says depth lives: the engagement decision. The research's linear-versus-square switch assumes units are engaged or waiting by reason of a cap, not stranded by a movement rule.

## 6. Counters, dominant plays, dead plays (question 4)

| Play | Counter in the rules | On most maps? | Note |
|---|---|---|---|
| S1 hold a choke | Go around (routing exists), go over (reach default 0), outrange (Bombard 1,200 and Bastion 800 against walls: R-098-02 blocks) | Cannot say: no map has chokes | Guard (R-096-08) makes the hold possible |
| S1 slope, tall cover | Land only; Q-007-01 and Q-162-01 open | No | Out of space scope |
| S2 spread line | Mass one end (README table); no rule prevents it, the scatter fallback hurts the line | Yes in open ground | Unmeasured |
| S2 concave | Stop at range edge | Yes (A199 helps the stopper) | The same A199 makes a stop at range edge a stand-off |
| S2 ranged behind screen | Flank by speed (R-099-01, Strike arrives first) | Yes | Needs group split |
| S3 ping then commit | Move after (stale picture), decoy | Rules exist, defaults off | |
| S3 silent force | Ping the approaches | Yes if ping is free | Free ping may dominate S4 |
| S4 find and fire first | Go silent, relocate after alert | Partial | Fire first needs range, not sight, for non-Siege |
| S4 bait | Do not chase | Yes (refusal) | Leash 200 is the bait's hook; no rule pulls the main force in |
| S4 ambush | Ping ahead | No ambush exists (no hold fire) | |
| S5 type on type | Mix evenly; screen; reach from another layer | Mix and screen exist | Triangle strengths unequal |
| Refusal | Retreat (R-085-05 requires 30 percent to escape at the 45 s mark) | Weak against faster types | Group pace and flinch; Q-008-06 asks how the lab checks it |

Dominant, as far as rules alone can tell (arithmetic from the table in R-082-01, R-081-01, no fights run):

- Siege with a spotter: range 1,200 against every other range at most 350, sensor 300 so it needs a Raider (sensor 800) as eyes. AoE total capped at 4 x base (70) per volley. Counter: Strike flank at 150 wu/s. This matches the research (strike first, the one with reach).
- Strike over Siege at 1.5 against 0.20: 7.5 to 1 per hit. Siege over Line 1.5 against 0.75 and Line over Strike 1.5 against 0.75 are 2 to 1. The triangle is not symmetric; if Q-081-01 lands at 0.75 it is 2 to 1 on all three edges.
- Vanguard against Raider by the table: Vanguard deals 7.5 x 1.5 / 1.2 s = 9.4 per second, Raider 9 x 0.75 / 0.8 s = 8.4; Raider has half the hit points and 200 against 300 range. The Raider's counter is flank speed, not a head-on fight.

Dead, as far as rules alone can tell:

- S1 and S3 in play (above). S4 for non-Siege on one layer (sensors exceed range, no pursuit on sight). Ambush and trap (no hold fire).
- Elevation sensor bonus (R-091-02, built flag 0.15 per tier, "nothing in code reads this", Q-092-01): height as initiative has no sensing rule behind it.

## 7. The measure against the research (question 5)

What the harness counts (`scripts/skilllab/firing.py`, `fight.py`, `contract.py`):

- Firing count: a living unit with an enemy on its own layer inside its range that the engine says it can shoot, sampled; binary per unit. Cross-layer targets are skipped (`elayer != layer`), so reach by layer does not enter the count. Not weighted by damage, interval, matchup or backswing, so it cannot say "Raiders firing at Vanguards" from "Raiders firing at Raiders" (Q-008-07). It does not count how many shooters share one target (focus), which the research ties to the attrition exponent.
- Margin: sum of surviving hit-point fractions over starting head count, per side, subtracted. A damaged survivor counts partly; every head counts the same whatever the type.
- A win: margin above 0.05. For 16 units that is 0.8 of one unit's hit points, so one survivor at under 80 percent reads "even".
- Draw (same-tick double kill): half a win each. Cap (still active at `max_ticks`) and quiet stalemate (no hp change for 400 ticks): in `scan.py` a cell is "decided" only if no fight is stalemate or cap, so they leave the break-even.

Does it capture what the theory says matters?

| Theory | Captured? |
|---|---|
| Units engaged and for how long (square, linear, cap) | Yes: series of firing counts, though binary and same-layer |
| Defeat in detail (arrival in parts) | Not directly; the series shows it indirectly |
| First strike and staying power | Margin only; no first-volley measure; Hughes' instability (high strike, low staying power) not detected |
| Bounded edge of concealment (information as a continuum) | No: no information variable and the exposed side has none to scale |
| Height as initiative | No: cost of committing to a layer is not measured |
| Focus (attrition exponent) | No (Q-008-05); A200 measured it as a separate batch |

Where the measure calls a fight even or decided for a reason unrelated to skill:

1. Cap and stalemate fights are removed rather than scored, so the A199 stand-off, a rule outcome, disappears from the answer.
2. The 0.05 margin hides a lone damaged survivor.
3. Abilities off in the lab, on in the game; the measured balance is not the balance played.
4. Spawn side, id order and cohort order decide identical fights (finding g), so a near break-even is partly a tie-break. Side swap and position replicates control for it but do not remove it.
5. Space maps are open and flat; C1 asks for skill to win "on at least 80 percent of the maps that offer the play", which is vacuous where no map offers it.
6. Headcount, not power, makes the break-even (Westley's ruling, 2026-10-01), so a lost Raider equals a lost Bastion; mixed-type fights (S5) mix scales.
7. A deterministic engine has no dice; break-even is a step in whole units and any tie-break shows as a step.

The goal also needs a number the plan names (C7, ceiling): the best situations against the rough sizes 2x and 3x. Under the square law and equal quality the break-even is at equal numbers, so the skilled side must hold the other's firing count under about half (for a 2 to 1 force) for the whole fight. Only a cap (choke), a hidden first volley or type multipliers can do that; this is the budget the rules must supply, and today only the type multiplier does.

## 8. Contradictions (question 6)

1. A199 against ALG-62. R-087-04: "does not walk toward an enemy it merely sees in sensor range; the formation holds until shooting, not until sight (Westley, 2026-10-03, A199; marked for review in playtesting)". `algorithms.md` ALG-62: "an attack-moving unit with sensor radius > attack range acquires the nearest visible same-layer enemy within sensor radius and moves toward it", marked "what the game does today". The bible hub is stale or the C is.
2. R-087-04 against R-096-02. R-087-04: the unit "keeps marching on its slot and route". R-096-02: "once every member of the group has engaged, the group ends and its members do not resume the march." The second is the stand-off.
3. R-095-01 against the code. Text: "capped at the slowest member's base speed, fixed at order time". Code: `om_unit_effective_speed` is 0 in backswing and in any Vanguard Brace phase, and the group order takes the minimum of it.
4. Guard: R-096-08 (closed provisionally, A170) against S-208 ("How it works is open (Q-096-01)"), against R-096-06 (hold rejected) and the story title "Four commands". A170 also called the rule R-096-05, which is the ability command.
5. Storm: story S-090, "a zone of interference to shrink what units inside it can see and what outsiders can see into it". R-090-03: "only the observer's own interference applies". The inhabitant is blinded, not hidden. Q-090-01.
6. Memory: R-089-04 "there is no memory of last-seen positions" and R-206-02 against R-096-04 "moves to E's last known position".
7. Return fire against side sight: R-093-02 "a unit ... acquires, pursues or fires at a target ... in its side's visible set" against R-087-06 return fire; A188 notes return fire stays ungated "until the morning read". Still open in the text.
8. ALG-66: "ARRIVAL_TOLERANCE_MULT = 1.5 . UNIT_COLLISION_RADIUS = 15" while R-097-05 gives a radius of 15 (so 22.5); the group ends at 22.5 (R-095-05, finding e) and a route's last waypoint at 30 (R-099-04, A180). Finding (e) is these two numbers; the text says both.
9. R-081 intro "none of it a death sentence" against Siege to Strike at 0.20 (Q-081-01); R-081-02 requires Strike to beat Siege "from the flank" with 30 percent left, which a 0.20 reply makes easy.
10. Principle against ability rules: "a number that decides a fight against the firing count is a number that's off" (plan) against R-086-03 (times 2.6 on durability and damage when braced, by arithmetic) and the others in section 4, with abilities "left out of this calculation for now" (2026-09-30).
11. Westley's "no blind fire" (README section 6) against the research (L section 3): the exposed side needs a finite increase, not an infinite one, and the whole literature models imperfect information as a continuum.
12. R-099-05 ("a unit never paces with no end") against its own 75 wu limit: outside the disc the count never starts.

## 9. What the research recommends that no rule implements (question 7)

In order of depth gained for the least rule text.

1. Hold fire (one flag). An ambush window gives a first volley worth the move from 0.50 to about 0.82 in the duel model, the one-time head start, and makes S4's trap and bait playable. Already asked as R-208-02, Q-208-01.
2. A partial-information reply (a few lines). The exposed side fires at reduced effect at the direction of fire, a ping-revealed point or the last seen contact; the research gives a continuum from mu = 0 (blind) to 1 (aimed), where a small information increase is worth more than the same proportional kill-rate increase when information is poor. This bounds the hidden side's edge. Conflicts with "no blind fire", so his.
3. A rule that gets engaged groups to close or stand by choice rather than by a stall (a line or two, A199's follow-on). The theory assumes units are engaged or in reserve by a cap; stranded units are neither.
4. Scoring of cap and stalemate fights (instrument, no rule text): a stalemate scored even stops a rule-caused loss of firing hiding.
5. Cost of committing to a layer visible in the measure (height as initiative): transition exposure exists (R-004-02); the count does not value it.
6. Firing arc or facing that matters (crossing the T: "all one's big guns bear while the enemy's do not"). Facing exists (S-100) and is cosmetic; whether fire waits for a turn is unknown from the rules and was not traced.
7. Reserve rule: units behind the cap wait unexposed. R-098-01 lets everyone fire over friends to range, so a reserve exists only behind a wall.
8. Weighting the firing count by type and by target (Hughes: hits per salvo net of defence; Q-008-07).

## 10. Decisions this audit asks of Westley

None is recommended. Effects are on the firing count and are read from rule text and arithmetic, not from runs.

1. Attack-move after the first contact (A199, R-096-02). (a) Keep as is: survivors out of range fire zero until re-ordered; skill is re-ordering. (b) The group persists with its slots until its last member dies or the order is replaced, and a unit with no target in range steps to the nearest enemy in sight only while its group has a member firing: firing returns after a clash, formation holds only until first contact. (c) Same as (b) with a stated bound (for example up to the unit's own sensor radius, a number for him): fewer stranded units, shape lost only inside that bound.
2. Scatter fallback (R-095-03). (a) Keep 450 wu. (b) Remove it: slots are always offsets, an unwalkable slot uses the nearest open cell; a 32-unit line holds its width, all units reach their firing positions together. (c) Raise the radius with the group size or the widest slot spacing; same effect up to the new limit.
3. Give-up on a blocked slot (R-099-05). (a) Keep 75 wu for 40 ticks: rim units pace and fire nothing. (b) Give up wherever a unit has been blocked by a stopped friend for 2 s: more units stop inside their range, firing count up for large groups. (c) Nearest free spot: needs bookkeeping, fewest gaps; most rule text.
4. Hold fire (R-208-02, Q-208-01). (a) None: ambush and bait stay unplayable, the first volley goes to whoever closes first. (b) A per-group hold-fire flag: a hidden side's first volley is its whole force at once; the exposed side's count starts at zero for that volley. (c) Guard with hold fire as one order: the same, with the choke hold and ambush together.
5. The exposed side's reply (README section 6 "no blind fire"). (a) Keep: the hidden side's firing count is unbounded over the exposed side's zero. (b) Return fire at reduced effect toward an attacker's direction for a short time: bounds the edge; the exposed side's count rises from zero to a fraction. (c) A ping alert grants area fire at the alerted sector for a set time: ties S3 and S4 together.
6. Siege to Strike at 0.20 or 0.75 (Q-081-01). (a) 0.20: S5 is steep (Strike over Siege 7.5 to 1) and a Bombard cannot answer a Raider flank in the firing count. (b) 0.75: all three edges 2 to 1, S5 remains meaningful and a flank no longer wipes the count. (c) A third value he sets.
7. Abilities in the measure. (a) Out, as now: the lab number is not the played number; Brace and Fortify decide fights the firing count does not see. (b) In, with the firing count weighted by the ability's modifier: the count is honest, the search space grows. (c) Out of the lab, and the abilities that multiply durability or damage are dropped from the game until the bar is met.
8. Storm interference (R-090-03, Q-090-01). (a) Keep, observer's position only: sitting in a storm blinds you; the "hiding" play is inverted. (b) Also scale an outsider's radius by the target's interference: a force hidden in a storm cannot be seen from outside; S1 and S4 gain a hiding place, and the exposed side's reply (decision 5) matters more. (c) Take the larger of both.
9. Stalemate and cap fights in the measure. (a) Excluded, as now (hides rule-caused stalls). (b) Scored as even, margin zero: a rule that strands units lowers the measured advantage. (c) Scored by hit-point margin at the cap, with their share reported beside every result: strands show up as a count of undecided fights per cell.
10. The identical-force tie-break (finding g). (a) Accept it: side swap controls it in the lab, the game keeps the order. (b) Alternate which side's cohort or id order goes first by tick or by seed: removes a non-skill firing advantage; changes recorded hashes. (c) Resolve all attacks of a tick from the same pre-tick state with no side order, as A178 already states: if the 94 to 66 persists it is another cause, to be traced first.

Also raised, not a decision: the group pace bug (finding b) is a mismatch between rule text and code; the text says base speed. Placing it here keeps it on the record.

## 11. What was and was not read

Read whole: the 2026-09-30 plan, both research briefs, the layer-dynamics README, E-11, E-12, E-13, the E-01 rules S-008 and S-162 to S-164 (headings and rule lines of the rest), the algorithms entries ALG-61 to 69 and 76, Rulings A125, A168 to A172, A174, A187, A188, A191, A195 to A201, A209, A210. Code read: `csrc/unit.c` (effective speed, ability phases), `csrc/tactical_move.c` (group order), `scripts/skilllab/firing.py`, `fight.py`, `contract.py`. Westley's words from the transcripts: a keyword scan of his typed messages only; the quotes above are those already in the README, the plan and the rulings, checked against that scan. Not traced: why identical forces split 94 to 66; whether fire waits for a turn; whether the 16 v 16 in-range fraction of a line against a blob matches the toy; the exact cross-layer state of the shipped game beyond the defaults in the cascade brief.
