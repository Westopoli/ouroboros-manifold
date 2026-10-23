# Enemy macro difficulty knob: options

Three shapes for the difficulty knob promised by E-14 S-125, each one changing "how much the enemy has" without ever touching what the enemy does. None ranks or recommends; Westley picks.

## Option A — Civilization's Ledger

This option keeps the knob where the bible already puts it: on the player's own allocation. Difficulty never touches the enemy; it sets the fraction of the enemy's power your civilization can match when filling your force, per the parity band already defined for missions (E-10 R-074-03). Easy hands you a force close to the enemy's total strength; hard hands you a leaner one. The enemy force is the same size and composition at any difficulty.

*The briefing shows enemy dispositions — three armor groups, an artillery nest, a garrison — unchanged from your last run of this seed at another difficulty. Your own force is what moves: six squads and two heavies on hard, nine and three on easy. You load in; the enemy's advance starts at the same moment, same speed, same route it always takes. What's different is how many of your units meet it.*

**What the player chooses, and where.** Difficulty (easy, medium, hard) is one of two onboarding questions (E-08 S-063), asked before the first chapter, changeable later at the same screen, taking effect from the next chapter's mission onward (A-058).

**First ten minutes, easy to hard.** The enemy onscreen is identical at every difficulty; your own starting roster is visibly larger on easy, leaner on hard, so the ambush your easy force shrugs off is the moment your hard force has to choose what to sacrifice.

**What never changes, and why a loss reads as yours.** Enemy stats, abilities, and decision loop match the player's at every difficulty (R-125-02); its plan and its timing never read difficulty, and the exact moment it acts still shifts mission to mission, same as always; it never sees what the player hasn't scouted (R-123-03). You watched the same enemy do the same thing a weaker force would also have faced; the briefing named what your civilization couldn't spare (R-074-05). Only the size of your hand changed.

**Relation to force parity.** This option *is* R-074-03, not an analogy for it.

**Honors:** R-125-01, R-125-02, R-123-03; changeable later (A-058); accessibility from parity tuning (principle 6). **Strains:** none of the fixed constraints; narratively must keep explaining why the enemy never moves.

**Prior art:** the old bible's own line, "difficulty never changes the enemy's strength — only the player's allocation" (VERIFIED — `docs/bible_history/bible_2_00_combat.md:109`); closer to a resource-handicap ladder than to StarCraft 2's AI, which scales the computer's own play (Findings table).

**Tradeoffs.** Reads and explains in one sentence; a player wanting the enemy itself to visibly change with difficulty won't find that story here.

Diagram: diagrams/option-a.svg

## Option B — Full Muster

This option puts the knob on the enemy's headcount: larger on hard, smaller on easy — more of the same units, same plan, same stats — while the player's starting force stays at the mission baseline. It is closest to what StarCraft 2's numbered AI does beneath its labels: even its hardest non-cheating tiers don't make units smarter, they field more of them under the same rules.

*Your roster is the same six squads and two heavies at any difficulty. The enemy dispositions panel is what moves: two armor groups and a garrison on easy; three armor groups, an extra garrison, and an unseen patrol on hard. You scout the ridge — more bodies dug in, same tank silhouettes, same speed, same line. There is simply more of it.*

**What the player chooses, and where.** Chosen at onboarding (S-063) with mission-type preferences, revisable at the same screen; a change takes effect from the next generated mission, never mid-mission.

**First ten minutes, easy to hard.** Scouting the enemy's dispositions is the tell: more force groups, more units per group, visible the moment you get eyes on them; your own force and the terrain are unchanged.

**What never changes, and why a loss reads as yours.** Every enemy unit, at any headcount, keeps the player's stats, abilities, and decision loop (R-125-02); extra bodies grant no extra vision, no faster reaction, no command outside the four the player has (R-123-03, R-120-04). The enemy was not smarter, only larger and scoutable, and scouting told you so before you committed — a loss reads as failing to convert what you saw into a plan using ground, timing, or a flank.

**Relation to force parity.** A second, independent lever: parity still sets the player's force against the mission's baseline enemy; this option scales that baseline before parity applies, so the two can combine.

**Honors:** R-125-01/02 (identical units, no behavior change); R-123-03; changeable later; onboarding placement (S-063). **Strains:** R-074-03 reads as the only difficulty lever at launch (E-14 gate, Q-125-01 deferred); this lever needs that scope revisited when S-125 is scheduled.

**Prior art:** StarCraft 2's non-cheating tiers (Very Easy through Elite) scale the AI's own force size, worker count, and attack frequency without changing unit stats (REPORTED — Findings table); its Cheater tiers add resource and vision cheats this option excludes (VERIFIED for the exclusion; REPORTED for the SC2 mechanism).

**Tradeoffs.** A legible, scoutable "how big is this fight" read that rewards scouting (principle 6, A-136); risks a numbers-wall feel where a mission's terrain gives a smaller force nowhere to make the extra bodies count.

Diagram: diagrams/option-b.svg

## Option C — The Long Supply Line (wild)

No shipped RTS ties its difficulty knob to a quantity that only grows over the mission and that the player can cut off by playing well. Here difficulty changes how fast the enemy's reinforcement structures resupply them over time — the same system that already resupplies both sides (E-15) — not what either side starts with. At the opening moment, easy and hard look identical; the gap opens minute by minute as the enemy's held reinforcement points feed them replacements faster on hard, and it closes the moment the player takes a point away.

*Minute zero: the enemy's opening force looks like it always does — you can't tell the difficulty yet. You grind down their forward group by minute six; on another day this would already be a rout. Instead fresh units keep trickling in from a structure behind the ridge. You peel off a squad, take the structure, and the trickle stops mid-fight. It feels harder not because the enemy got smarter, but because you let their supply line run for six minutes.*

**What the player chooses, and where.** Chosen at onboarding (S-063), changeable later for the next mission (A-058); a briefing line names which reinforcement structures are the enemy's, so the option is legible before commitment, not a mid-fight twist.

**First ten minutes, easy to hard.** Nothing to see at the opening moment — both starting forces are the mission baseline, identical across difficulties. From roughly minute three, a watchful player notices the enemy's replacement rate: convoys or spawns arriving more often at a held structure that was always on the map and always capturable.

**What never changes, and why a loss reads as yours.** Arriving units keep the same stats, abilities, and decision loop as everything else on the field (R-125-02); the structures grant no vision the player hasn't earned by scouting (R-123-03); the enemy's plan and timing are untouched — only how often that plan gets fresh units. The mechanism working against you is the one available to you the whole match (E-15), named in the briefing; a loss reads as having let a visible, capturable, non-cheating advantage run uncontested, the same reading the game already asks for when a player loses local production and fights with a fifth of a force (game bible, "The Player's Toolkit").

**Relation to force parity.** Independent of it. Parity still sets the player's starting allocation against the baseline; this option never touches either side's starting count, so it can run under parity, on top of it, or alone.

**Honors:** R-125-01 in spirit (how much, never how well); R-125-02 and R-123-03 exactly; changeable later; rewards positional and scouting skill directly (principle 6, A-136); reuses an existing system (E-15). **Strains:** R-074-03 as scoped covers only starting allocation, not a runtime rate; E-14 and E-15 would need extending to make reinforcement rate a difficulty-scaled value, which neither states today.

**Prior art:** none found for a difficulty knob expressed as an interdictable resupply rate rather than a starting quantity. Darkest Dungeon's Radiant/Stygian modes are the closest adjacent shape, scaling resource curves and run length rather than a live, capturable throughput (REPORTED — `docs/legacy/games/darkest_dungeon.md:32`); StarCraft 2's Cheater tiers scale a passive economy bonus the human can never touch (REPORTED, Findings), inverted here into something the player can take away.

**Tradeoffs.** Turns difficulty into an in-mission verb, deny the reinforcement point, rewarding the stated skill ceiling directly; asks more of early map awareness, and a player who never finds the structure experiences hard difficulty as a mystery escalation.

Diagram: diagrams/option-c.svg

## Findings

Brief constraints not honored, in any option, and why:

- Westley's reference model (Section 8) points at StarCraft 2's ladder as a whole, but its non-cheating tiers differentiate mainly through decision quality and reaction speed — faster worker splits, quicker macro cycles, wider build-order variety — exactly the "how it behaves" axis closed off for this pass ("3: not yet"). None of the three options can honor that mechanism; each instead translates SC2's outcome (a bigger, better-run opponent) into a pure quantity axis, so none fully replicates the felt gap between, say, SC2's Hard and Very Hard tiers, which is reportedly more about tempo than roster size. Named here rather than silently substituted.

What StarCraft 2's built-in AI levels actually do, cited:

| Tier | Name | Non-cheat behavior | Cheat granted | Confidence | Citation |
|---|---|---|---|---|---|
| 1 | Very Easy | Minimal aggression, slow or absent attacks | none | REPORTED | [Liquipedia: Artificial Intelligence](https://liquipedia.net/starcraft2/Artificial_Intelligence) |
| 2 | Easy | Basic attacks, simple build order | none | REPORTED | [Liquipedia: Artificial Intelligence](https://liquipedia.net/starcraft2/Artificial_Intelligence) |
| 3 | Medium | More consistent attacks and expansion | none | REPORTED | [Liquipedia: Artificial Intelligence](https://liquipedia.net/starcraft2/Artificial_Intelligence) |
| 4 | Hard | Faster build order, more frequent attacks and harassment | none | REPORTED | [Liquipedia: Artificial Intelligence](https://liquipedia.net/starcraft2/Artificial_Intelligence) |
| 5 | Harder | Added between Very Hard and Hard in Heart of the Swarm; more aggressive timing | none | REPORTED | [Liquipedia: Artificial Intelligence](https://liquipedia.net/starcraft2/Artificial_Intelligence) |
| 6 | Very Hard | Quicker macro cycles, wider build-order variety, active harassment (drops) | none | REPORTED | [Liquipedia: Artificial Intelligence](https://liquipedia.net/starcraft2/Artificial_Intelligence) |
| 7 | Elite | Fastest non-cheating decision loop and most consistent macro; still plays under the same rules as a human | none | VERIFIED (named as the last non-cheating tier) | [TStarBots, arXiv:1809.07193](https://arxiv.org/abs/1809.07193) |
| 8 | Cheater 1 (Vision) | Same as Elite | Full map vision | VERIFIED | [TStarBots, arXiv:1809.07193](https://arxiv.org/abs/1809.07193) |
| 9 | Cheater 2 (Resources) | Same as Elite | Full map vision plus mining 2 extra minerals and 2 extra gas per trip without depleting the node faster | REPORTED (bonus figures) / VERIFIED (vision + resource boost exists) | [TStarBots, arXiv:1809.07193](https://arxiv.org/abs/1809.07193); resource figures via community reporting, no primary Blizzard source retrievable this pass |
| 10 | Cheater 3 (Insane) | Same as Elite | Full map vision plus resource mining boost, combined; estimated Platinum-to-Diamond human skill equivalent | VERIFIED (tier exists, skill estimate) | [TStarBots, arXiv:1809.07193](https://arxiv.org/abs/1809.07193) |

Wings of Liberty shipped six tiers (Very Easy, Easy, Medium, Hard, Very Hard, Insane); Heart of the Swarm added Harder and Elite and split Insane into the three Cheater variants above (REPORTED — [Liquipedia: Artificial Intelligence](https://liquipedia.net/starcraft2/Artificial_Intelligence)). Liquipedia and the StarCraft Fandom wiki were blocked to direct retrieval this pass (HTTP 403, 402); the table above comes from search-result summaries of those pages plus the one primary source that loaded, the TStarBots paper, which independently confirms the ten-tier structure and the Cheater tiers' nature.
