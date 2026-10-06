# Terrain and force geometry in military doctrine: what a game rule could test

Research synthesis, 2026-10-06, for Westley. Nothing here is a decision. Every number is prior art from the history of war or from operations-research papers, not a game number; Westley owns the game's numbers.

Source: the Gemini deep research, `terrain_in_military_doctrine_deep_research_2026-10-06.md` (called DR; prompt in `terrain_in_military_doctrine_gemini_prompt.md`). Skills S1 to S5 are those of `docs/northstar/research/layer_dynamics/README.md` section 3 (S1 landscape, S2 formation, S3 layers, S4 enemy position, S5 unit-type matchup). Pillars P1 to P8 are those of `docs/northstar/research/map_design/README.md`. The yardstick is the game's own: who gets shots off, and for how long.

## 1. How far to trust the source

DR is a model's report, not a checked bibliography. I did not re-verify its figures against the books it cites. What I did: read it against itself and against what I remember of the history, and mark each principle below **solid**, **contested** or **weak**. The marks are mine and are not from the research. Four findings change how much weight a principle can carry:

- **Kursk numbers read backwards.** DR cites daily losses of 1.25 percent for the attacking Germans and 5.83 percent for the Soviet defenders as its best number for defence in depth. Those figures say the defenders lost more, which does not support the claim. Do not use it as evidence for the principle.
- **The "2.4x" in section 9 is not Dupuy's figure as stated.** DR's table gives terrain 1.3 to 1.5 and hasty defence 1.5 to 1.6, "aggregate 2.4". Its game translation then adds +0.5, +0.5 and +1.4 to reach 2.4, a different sum with a matchup term that is not in Dupuy's table. Multiplying the table's two terms gives about 2.0 to 2.4. Treat 2.4 as an order of magnitude, not a value.
- **Several battle figures are the weak ends of wide ranges.** DR itself marks Kalka (a Mongol force of 20,000, an allied army of 80,000, 75,000 dead) as "highly estimated", and Cannae and Thermopylae as contested. Passchendaele's casualties are flagged contested in the source. Leuthen's Austrian strength (DR: 80,000) is usually given nearer 65,000, and Pavlov's House is usually dated 58 days, not 59 (both from my memory).
- **DR's "game translation" paragraphs describe game behaviour the record does not confirm.** For example, that an attack-move blob "natively forms a column", or that "the enemy's ping stops at the crest". Neither is in the bible. I have rewritten each translation in terms of rules the bible does state and the lab's existing plays.

DR's own ranked list stops at five entries. The ranking in section 5 is mine.

## 2. The ten principles

Each entry: the claim; the cases with their numbers; the source DR gives; when it holds; the rule a lab could test, in the game's terms (five layers, chokes, tall cover, "high ground sees down", the ping, group pace at the slowest member's speed, firing count weighted by unit type).

**1. Chokes and defiles. Mark: solid in principle, numbers contested.**
- Claim: a narrow front caps how many of the larger force can fire, so numbers stop mattering; fighting strength then grows with the width engaged, not with the square of the force (Lanchester's square law versus his linear law).
- Cases: Thermopylae, 480 BC (DR: a Greek force of about 7,000 against 100,000 to 300,000; about 4,000 Greek and 20,000 Persian dead, until the position was outflanked). Morgarten, 1315 (about 1,500 Swiss against about 9,000 Austrians in a defile; about 2,000 Austrian dead). Failure case: Passchendaele, 1917 (narrow passable strips pre-targeted by artillery; 200,000 to 400,000 casualties per side, contested).
- Source: MacKay, *Lanchester Combat Models* (2006); Winkler, *The Battle of Morgarten in 1315* (2008); Edmonds, official history (1948).
- Holds when: the flanks are impassable and the attacker has neither indirect fire nor another way round.
- Testable: with the lab's S1 play "hold a choke", the attacker's units firing per tick are bounded by the choke's mouth, not by its headcount. The counters in the plays table (go around or over on another layer; stand outside and outrange) take back at least half the advantage, which is the lab's draft condition C6.

**2. High ground and reverse slope. Mark: solid.**
- Claim: height gives sight, range and a slower climb for the attacker. Against long-range fire, a position behind the crest (the reverse slope) breaks the enemy's line of sight until the enemy is close.
- Cases: Waterloo, 1815 (Wellington's about 68,000 behind the Mont-Saint-Jean ridge against about 80,000 French, shielded from the main battery until the infantry crested the ridge). Dien Bien Phu, 1954 (Viet Minh guns dug into reverse-slope bunkers; DR: about 2,200 French dead and 10,000 captured, about 8,000 Viet Minh dead). Bunker Hill, 1775 (British over 1,000 casualties out of about 3,000 attacking uphill; the British did take the hill, which DR does not say).
- Source: Fall, *Hell in a Very Small Place* (1967); Clausewitz, *On War*.
- Holds when: the crest blocks the weapons' trajectories and the enemy has no aerial or other eye over it.
- Testable: ground eras only (the ping is space-only, E-01 R-005-12). A defender behind the top of a slope sees units cresting before they see it (R-005-09: high ground sees down, low ground never sees up); the lab's S1 play "hold the top of a slope past the midline" measures the firing-count gap. The counters are in the plays table: another way up, flying, or shelling from below with a type that fires upward. Bears on Q-MAP-01 (what height does beyond vision).

**3. Concave and envelopment. Mark: solid (Cannae and Cowpens), contested numbers.**
- Claim: a concave arc lets every unit on it fire inward without hitting its own side, while the enveloped force masks itself and only its outer ring fires.
- Cases: Cannae, 216 BC (about 50,000 Carthaginians against about 86,000 Romans; 50,000 to 70,000 Romans dead). Cowpens, 1781 (1,025 Americans against 1,100 British; British 110 dead, 229 wounded, 629 captured; 72 American casualties). Tannenberg, 1914 (150,000 Germans against 230,000 Russians; about 170,000 Russian casualties).
- Source: Polybius, *Histories* (numbers contested); Babits, *A Devil of a Whipping* (1998); Biddle, *Military Power* (2004) on differential concentration (DR's attribution to the book's "modern system" is not one I can confirm).
- Holds when: the centre holds until the flanks close.
- Testable: the lab's S2 play "concave around the point where the enemy arrives" against a blob: units firing on the concave side against units firing on the blob side. The counters: stop at the edge of range, or mass on one horn.

**4. Frontage: line against column. Mark: solid for musket-era linear tactics, weak as a general rule.**
- Claim: a wide line brings all its weapons to bear; a deep column brings only the front ranks.
- Cases: Maida, 1806 (5,196 British in line against 6,440 French in column; DR's French loss of 490 killed, 870 wounded and 722 captured against 327 British; the figures vary by source). Leuthen, 1757 (about 36,000 Prussians in oblique order against Austrians DR puts at 80,000). Operation Michael, 1918: DR's account is muddled and I would not use it.
- Source: Oman, *A History of the Peninsular War* (1902); Biddle (2004).
- Holds when: the line's flanks are anchored or protected.
- Testable: the lab's S2 play "spread to full width" against a blob, with the lab measuring units firing per side. Whether an attack order produces a column at all depends on the movement and formation rules and is not recorded in the bible; check it in the lab before relying on it. The counter: mass on one end of the line.

**5. Defence in depth, screens and reserves. Mark: contested (DR's best number is unusable, see section 1).**
- Claim: a forward screen forces the attacker to stop and deploy while long-range forces behind it attrit him; uncommitted reserves finish the job.
- Cases: Kursk, 1943 (Soviet belts up to 300 km deep; discard the loss figures). Goodwood, 1944 (over 1,000 British tanks; over 300 lost and 3,000 casualties for about 7 miles). Cowpens, 1781 (three layers: sharpshooters, militia, regulars).
- Source: Dupuy, *Understanding War* (1987); Biddle (2004).
- Holds when: the defender has depth to trade and the screen cannot be bypassed from above.
- Testable: the lab's S2 play "long-range units behind a screen of tough ones". Fire and sight cross layers only by unit-type reach (E-01 S-164), so a screen on one layer shields a back line the front cannot reach. The counters: reach the back line from another layer, or send fast units round the screen.

**6. Reconnaissance, surprise, ambush and bait. Mark: solid in mechanism (Hastings, Cowpens), the Kalka numbers weak.**
- Claim: surprise multiplies relative power by catching the enemy un-deployed. A feigned retreat is the way to manufacture it against a larger force.
- Cases: Hastings, 1066 (Norman feigned retreats). Kalka River, 1223 (DR: about 20,000 Mongols drew about 80,000 into a nine-day pursuit; about 75,000 dead; DR says "highly estimated"). Cowpens, 1781 (two volleys and a retreat that read as a rout).
- Source: Gabriel, *Subotai the Valiant* (2004); Dupuy (1987), who gives surprise a multiplier of up to 2.0 (DR's figure, see section 9).
- Holds when: the enemy advances without scouting ahead and will not decline the fight.
- Testable: the plays-table S4 plays (bait, ambush; both marked "later" because they need orders to change during a fight). They are measurable once the engine supports it. Surprise is not a game multiplier; in this game it works through who finds whom first and who fires first, so test it there.

**7. Combined arms and unit matchup. Mark: solid.**
- Claim: types that cover each other's weaknesses beat a larger force of one type.
- Cases: Cambrai, 1917 (476 tanks with infantry, a creeping barrage and aircraft; about 5 miles in hours). Pavia, 1525 (arquebusiers and pikes against heavy cavalry). Bekaa Valley, 1982 (29 SAM batteries and 82 aircraft destroyed with minimal losses; not a matchup of types in the game's sense, more a combination of sight, jamming and strike).
- Source: Biddle (2004); Taylor, *Lanchester Models of Warfare* (1983).
- Holds when: the specialists stay with their protectors.
- Testable: the lab's S5 plays: line each type up against the type it beats; keep the vulnerable type away from its counter. The matchup is already the game's fixed triangle (Strike flanks Siege, Siege crushes Line, Line absorbs Strike, E-11 S-081). The counter: mix evenly, or isolate the specialist.

**8. Vertical and three-dimensional terrain. Mark: solid but analogical.**
- Claim: units on a different level than the enemy see and are seen differently, and crossing levels is costly.
- Cases: Pavlov's House, Stalingrad, 1942 (25 Soviet infantry held a four-storey building for 58 to 59 days). Manila, 1945 and the Dupuy Institute's urban studies (an advance rate down by 50 to 66 percent in cities). Falklands, 1982 (one submarine kept a surface fleet in port).
- Source: Chuikov, *The Battle for Stalingrad* (1964); Dupuy Institute urban combat report (2002).
- Holds when: the structure is not levelled.
- Testable: the lab's S3 plays ("place each type where its reach covers the enemy and the enemy's does not"). The space lab has free layers; the ground lab waits. Real urban fighting has no free movement between levels, which is closer to the ground-era layers than the space-era ones.

**9. Force ratio. Mark: solid in direction, numbers weak.**
- Claim: the "3-to-1 rule" for attackers is not borne out; outcomes follow terrain, posture and systems effects.
- Evidence: the Dupuy Institute's 752-case division-level database (1904 to 1991): attackers won more than half of engagements at ratios from 1.00 to 1.49 to 1 (DR). Dupuy's Quantified Judgment Model gives terrain about 1.3 to 1.5, hasty defence about 1.5 to 1.6 and surprise up to 2.0 (DR's table). Golan Heights, 1973: about 100 Israeli tanks held against 500 or more Syrian tanks.
- Source: Dupuy, *Numbers, Predictions and War* (1979); Lawrence, *War by Numbers* (2017).
- Holds when: the small side keeps the conditions that gave it the multiplier.
- Testable: this is the lab's yardstick, not a play. Condition C7 reports the best situations against rough sizes of 2x and 3x; the lab's first target, from Westley's answer, was "about 2x" for all five skills together. DR's multipliers are prior art to compare a lab result against, not values to use. Bears on Q-MAP-01 and Q-MAP-02.

**10. Counter-cases. Mark: solid.**
- Claim: a geometric advantage collapses if the attacker can bypass it, outrange it, or see through its concealment.
- Cases: the Maginot Line, 1940 (bypassed through the Ardennes). 73 Easting, 1991 (dug-in reverse-slope positions defeated by thermal sights and range). Passchendaele (see 1).
- Source: Biddle (2004).
- Holds when: the attacker has mobility, range or better sensors.
- Testable: every skilled play in the lab already has a counter, and condition C6 requires the counter to take back at least half the advantage on at least 60 percent of maps (draft, not confirmed). This principle is the reason for C6 and for map pillar P8.

## 3. Mapping to the map pillars and the five skills

| # | Principle | Map pillar | Skill | Lab plays | Era kind |
|---|---|---|---|---|---|
| 1 | Chokes and defiles | P3 chokes that bind; P4 several routes (the counter) | S1 | hold a choke; go around or over | both |
| 2 | High ground, reverse slope | P5 height with a rule; P6 cover and sightlines | S1, S3 | hold the top of a slope; get sight first | ground (the ping is space-only) |
| 3 | Concave, envelopment | P6 open ground to wrap on; P4 routes to rotate | S2 | concave; mass on one horn (the counter) | both |
| 4 | Line against column, frontage | P3 frontage; P6 open and sheltered ground | S2 | spread to full width; mass on one end (the counter) | both |
| 5 | Depth, screens, reserves | P2 paced distance (space to trade); P4 | S2, S3 | long range behind a screen | both |
| 6 | Recon, ambush, bait | P6 cover and sightlines; P4 the unwatched route | S4 | ambush; bait; find first | both |
| 7 | Combined arms | P8 every strong position has a counter; the composition-against-choke-count finding in the pillars page, section 3 | S5 | line each type up; keep the weak type away | both |
| 8 | Vertical terrain | P5 height with a rule, and a readable reference | S3, S1 | place each type by its reach | space (free layers); ground analogue |
| 9 | Force ratio | none; it is the measure | all | conditions C0 to C2, C7 | both |
| 10 | Counter-cases | P8 every strong position has a counter | all | the counters of the plays table; C6 | both |

Pillars with no principle in DR: P1 equal numbers with free shapes, P2's pacing bands as a rush-distance matter (only touched by principle 5), and P7 escalating exposure. DR is about fighting, not about layout fairness or the economy.

## 4. What the research changes in the existing record

- It supports the hub's promise with a long history, not a new rule: terrain and geometry move the firing count, and the strongest historical cases (Morgarten, Cowpens, Cannae, Dien Bien Phu) are the ones where the weaker side set the shape of the fight before it began.
- It gives the lab no new play. All ten principles map onto plays already in the plays table (sections 2 and 3 above). It does supply historical counter-cases for the plays' counters.
- It raises two points for Westley, as candidates and not recommendations. First, Dupuy's terrain and posture multipliers (about 1.3 to 1.5 and 1.5 to 1.6) are a published scale for the Q-MAP-01 and Q-MAP-02 candidates (what height and cover do beyond vision); they are prior art and not game numbers. Second, DR does not address how the game's group movement at the slowest member's pace changes the line-against-column principle, so that one needs a lab run.

## 5. Ranked list: what is most useful for making "small beats large" possible and learnable

Ranked by three things: how directly the principle moves the firing count, whether a lab play for it already exists, and whether the engine has the mechanism today. This is my ranking; DR ranked five principles in a different order and put line against column first on a claim about pathfinding that the bible does not make.

1. **Chokes and frontage (1, 4).** The most direct control of firing count, and a lab play exists now.
2. **Formation: concave, spread line, screen (3, 4, 5).** The player's own control of how many fire at once; lab plays exist now.
3. **Unit-type matchup (7).** Already fixed in the game's triangle, so it is cheap to build and easy to read.
4. **Height and reverse slope (2).** Needs the ground lab, which waits for the engine to have ground.
5. **Recon, ambush and bait (6).** The strongest historical stories, but the lab's two plays for it need orders that change during a fight.
6. **Vertical terrain (8).** The space lab covers the free layers; the ground analogue waits.
7. **Counter-cases (10).** Not a feature but a standing requirement: nothing on this list ships without its counter.
8. **Force ratio (9).** A yardstick for the lab's results, not a mechanic.
