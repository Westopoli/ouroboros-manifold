# Layer dynamics: start here

The work to make the layer system and tactical combat carry the game's central promise. This file is the current state: the goal, the principle, the measure, what is decided, what the engine can do, and the plan. It is rewritten when things change. How it got here, with every run of the toy simulator, is `history_2026-09-30_to_10-01.md`. Runs from now on are one file each in `runs/`.

## 1. The goal

Westley, 2026-10-01: "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force". "The goal is to create a game with significant strategic depth. We get to this goal by tuning all the variables we laid out such that that sentence becomes a reality."

His original request, 2026-09-30, was for a simulator that varies everything an RTS varies (position, orientation, damage, health, vision, landscape), documents how the variables relate, and finds where the "lines cross"; in small steps, read as they come: "I think it'd be much faster to iteratively try small things, check the output, and tune repetatively."

On 2026-10-01 he added that there is more than one answer: "The *lines* can cross in multiple locations, there may be configurations where health/range/vision/ping distance is much higher/lower but the expected behavior is exhibited."

## 2. The principle

- **What decides a fight is how many units on each side can get shots off, and for how long.** "This is leading us to the core of the game: the differentiator is **can your unit get shots off**." It is the advantage over the whole fight that counts, not only the opening: "the number that we really care about is number of units firing, if A and B both have the same number of units firing than the engagement ends up even". An even exchange is not an even outcome when one side has more in reserve.
- **A skill has no fixed worth.** A play is worth what it does to the firing count in that situation: "it depends on the number of units that can get shots, not a basic ratio ... That will indicate the quality of the choke, not just that they should do *1.3x* better because it's not as simple as that." About 30 percent more army for one skill and about three times for all five are rough sizes, not pass marks.
- **Unit type is the one other factor.** It weights each shot ("not just unit values but their type as well"). Any other number that decides a fight against the firing count, such as a damage bonus for height or raw health, is "a number that's off".
- **More than one configuration can work.** The search describes every region of settings where the conditions hold, not only the first found.

## 3. Five skills

| Skill | The skilled player | Source |
|---|---|---|
| S1 Landscape | fights where terrain limits how many enemies can fire | "understanding of the landscape" |
| S2 Formation | arranges units so more of them fire at once | "unit formation" |
| S3 Layers | uses the three layer actions on purpose: the ping, going dark, reach by unit type | "layer awareness/intentionality" |
| S4 Enemy position | finds the enemy first and fires first; draws the enemy into a trap with a lesser force | "the other players current position"; "induces traps" |
| S5 Unit-type matchup | puts its own rocks on the enemy's scissors | "it's bigger than just a subset of S2" |

Skill is represented by scripted plays: a skilled play and a naive play. The naive play is measured two ways, side by side: a blob, and a line abreast (Westley, 2026-10-01). Plays and their counters, accepted in outline:

| Skill | Skilled play | Counter |
|---|---|---|
| S1 | Hold a choke: stand just behind a narrow passage so few enemies can fire at once | Go around or over it on another layer; or stand outside and outrange it |
| S1 | Hold the top of a slope, far enough past the midline that climbers cannot reach | Take another way up, or fly; or shell the top from below with a type that fires upward |
| S1 | Fight from behind tall cover | Get sight first: ping behind the cover, or move to a layer above its height |
| S2 | Concave around the point where the enemy arrives | Stop at the edge of range; or throw the whole force at one horn of the arc |
| S2 | Spread to full width so every unit is in range together | Mass the whole force on one end of the line, so only the few defenders at that end can fire, and work along it |
| S2 | Long-range units behind a screen of tough ones | Reach the back line from another layer; or send fast units around the screen |
| S3 | Ping the layer and place that matters before committing | Move after being pinged so the picture is stale (later); or show a decoy to be pinged |
| S3 | A silent striking force with an emitting decoy | Ping the likely approaches; do not chase the emitter (later) |
| S3 | Place each type where its reach covers the enemy and the enemy's does not | Change layer to leave their reach and enter yours; bring the type that fires upward |
| S4 | Find the enemy with pings and fire first | Go silent so less is found; relocate after the alert (later) |
| S4 | Take the route or layer the enemy is not watching | Watch more routes with pings; hold a reserve in the middle |
| S4 | Bait: a small group engages and falls back, the main force closes a surround (later) | Do not chase, or chase with a small detachment only (later) |
| S4 | Ambush: wait unseen and hold fire until the enemy is inside the concave (later) | Ping ahead before advancing; send a vanguard first (later) |
| S5 | Line each type up against the type it beats | Mix types evenly so there is no clean matchup; re-shuffle to mirror (later; the reactive idea) |
| S5 | Each type shoots the type it beats first | Keep the targeted type behind a screen |
| S5 | Keep the vulnerable type away from its counter | Reach it from another layer, or flank it |

Refusing a fight is a counter: "a skilled player only takes a battle that they can win, skilled players make it so that the opponent doesn't have a choice." A play needs a counter on most maps, not all; "some situations are unbeatable (like a full surround or a trap where the door gets closed)". "Later" marks plays that need orders to change during a fight. After the prototype, if it works, a reactive version: one side or both re-form mid-fight to keep their rocks on the enemy's scissors.

## 4. The measure

- **Margin.** One signed number per fight: the share of one side's strength left, minus the other's. It replaces win rate, which is a probability in a system that has no dice.
- **Break-even, in whole units.** "16 beat 17 and lose to 18." By headcount, both sides fielding the same mix of unit types. Beating means "ending ahead by a margin", not a wipe-out.
- **Units firing, per side, through the fight.** Recorded for every fight; the firing advantage is reported beside every result. Weighted by unit type where types differ.
- **Maps.** Space maps (every unit flies; "it does have very free layers that can be taken advantage of") must pass. Land maps (ramps, walking units) are measured and reported.

Conditions on a rule set, with draft pass marks that Westley has not yet confirmed:

| # | Condition | Draft mark |
|---|---|---|
| C0 | Control: a mirrored fight is even | break-even between 0.9 and 1.1 of equal numbers |
| C1 | Skill wins the firing count | firing advantage of at least 1.2, on at least 80 percent of the maps that offer the play |
| C2 | The result follows the firing count | results rise with firing advantage (rank agreement at least 0.8); no more than one fight in five more than 25 percent off the trend |
| C3 | Skills stack | a combination beats its best part by at least 5 percent |
| C4 | No dominant skill | no single skill gives more than 60 percent of the full set's advantage |
| C5 | No dead skill | removing any one skill from the full set costs at least 10 percent |
| C6 | Counters exist | the counter takes back at least half the advantage, on at least 60 percent of maps |
| C7 | The ceiling is high | reported: the best situations, against the rough size of three times |
| C8 | Robust | C1 to C6 hold on 80 percent of space maps |
| C9 | Fights stay readable | reported: fight length against E-11 S-085 |

"Lines crossing", made concrete: a line is the edge, in the space of settings, of where one condition holds; the crossing is a region where all hold at once; there may be several such regions.

## 5. How results are read

Small batches. One page of charts per batch, in the form Westley approved on 2026-10-01 after the first draft read badly ("I had to stare at it to figure out what it meant"; of the redraw, "looks much better, especially the top graphic"). The sample is at https://claude.ai/artifact/WtQDNnNZTR8hqx6LpxBaJ2 (private to Westley).

- The heading states the finding in soldiers, not ratios.
- A line of fights by enemy size, a dot per fight, won or lost, with the break-even marked ("beats 17, loses to 18").
- Units firing through the fight, each line labelled on the chart, the gap shaded.
- A table with a plain-words column in place of any scatter plot.
- For many rule sets: a map of two settings at a time, shaded where every condition holds; a short decision-tree summary in words.

Research behind the form: `docs/research/topics/charts_for_combat_simulation_data.md`.

## 6. Layer rulings in force

Canonical text is E-01 (`docs/bible/epics/E-01-layer-system.md`) and the register. In brief:

- Five layers, always. Vision is symmetric by layer distance. Passive cross-layer vision stays, at short range.
- Three layer actions, all costing no resource: the **targeted ping** (a chosen layer at a chosen place, a very short burst, long reach; the pinged side gets an alert and a sector of about 60 degrees toward the source), **going dark** (a force emits or stays silent), **reach by unit type** (each type fires only at certain layer offsets). E-01 S-162, S-163, S-164.
- The ping replaces the seer, "or make the seer really expensive".
- A unit never fires at what it cannot see.
- A unit takes the shortest route to its goal across layers.
- Flying and swimming units change layer anywhere nothing blocks; walking units only by slopes.
- On a slope, progress is position; the cross-over is the midline; a unit is on the layer on its side of it. A transitioning unit attacks from the layer it is leaving until the cross-over.
- Abilities are out of this work for now. No faster descent in space eras.
- Ideas recorded, not decided: travel lanes (E-17 S-165); the reactive formation.

## 7. The instrument

The toy simulator (`toys/layerlab/`) is frozen. Its unit behaviour is not the game's, and results kept turning on that: units overlapping, held units that never step forward, chasing units that run through a choke. The real C sim was compiled on the Mac on 2026-10-01 and runs a 16 against 16 fight headless in 3 ms. Westley: "yes to the real engine, so long as we can accomplish the original goal from the original plan."

What the real engine can do today: headless fights through its public calls, with the game's own unit rules (acquire, anchor, the 200 leash, return fire), group moves, hard collision, unit stats changed at run time, abilities switched off. It is fully deterministic.

What it cannot, each a gap against its own bible:

| Gap | Rule it misses | What it blocks |
|---|---|---|
| Units walk straight; obstacles do not block movement; no routing | E-13 R-097-01 | landscape: no choke can exist |
| Targeting ignores fog and line of sight | E-12 R-093-02, E-01 R-008-04 | enemy position; all vision work |
| No layer changes, slopes, ping, going dark or reach by type; same-layer fire only | E-01 S-002, S-004, S-162 to S-164 | layers |
| Rule numbers are fixed when the library is compiled | none (tooling) | tuning anything but unit stats |
| The first-spawned side shoots first; nothing varies between seeds | a property of the engine | honest measurement, unless the harness swaps sides and shifts positions |
| The root `Makefile` does not build on an arm64 Mac | determinism contract | building on the Mac |

## 8. The plan

1. This record.
2. The **skill lab**: a harness in `scripts/skilllab/` that only calls the real library. It runs fights, counts units able to fire, finds break-evens in whole units, and writes the chart page. Tests first.
3. One **controls batch** on today's engine (mirror, numbers, a planted reach advantage), to prove the harness and keep a before-picture.
4. One **engine cascade** that closes the gaps: a portable build; rule numbers settable at run time; solid terrain with routing; targeting by sight; layer changes; reach by type; going dark; the ping. Tests first, Sonnet sub-agents throughout, with separate test writers and auditors.
5. **Small batches** on the finished engine, one skill at a time, each read by Westley: formation, matchup, landscape, enemy position, layers, then the knobs, then combinations and counters.
6. The **search** for every region of settings where the conditions hold, two ways side by side: all settings at once, and step by step ("start the prototype with 2 variables, tune them until the expected behavior is exhibited, and then just keep iteratively adding and tuning").

The build brief for steps 2 to 4 is `docs/northstar/plans/2026-10-02-skill-lab-cascade.md`.

## 9. Two machines

The Mac and the Linux machine work on this repo at the same time.

- No machine paths in code; the harness finds the repo root from its own file.
- The library builds by architecture; a committed file of result hashes for the control fights must match on both machines. A mismatch is a determinism finding.
- Scripts guard their entry point and pass plain data to worker processes; the two systems start workers differently.
- Work lands on `main` in small units. Merge, never rebase. Pull before editing a shared file. Cascade branches and worktrees stay local.
- One file per run in `runs/`; register edits one row at a time.
- Nothing generated is committed: libraries, result tables and pictures, Godot import files.

## 10. What the toy showed

Kept as leads, to be re-measured on the real engine (transfer class T2 or T3):

- A layer alone gives nothing under symmetric vision. Reach and damage penalties for firing up are steep: decisive within 20 percent.
- Width matters, curvature barely: against a blob, a line or a concave is worth three units in sixteen; a concave is worth one unit against a line.
- Holding a choke gave nothing, for three reasons: walls did not block sight; no stance between never moving and chasing anywhere; reach of only four unit-widths, so few units can focus one spot.
- For the ideal choke (attackers held to c firing, D defenders all firing) the arithmetic is D(D+1)/(2c).

## 11. Lessons about method

- Check what is written against Westley's own words (`crosscheck_2026-09-30.md`, `crosscheck_2026-10-01.md`).
- Look at what a scripted play actually does before measuring it.
- One skill, one map, one size; then widen.
- A surprising result is first a question about the instrument.
- Win rate misleads in a system without dice.

## 12. Open

Register: `Q-008-02`, `Q-008-03` (close when the lab's numbers fold into E-01 S-008 and `algorithms.md`), `Q-009-02`, `Q-165-01`. Provisional, to be tuned: `Q-001-05`, `Q-005-04`. Not yet ruled by Westley: the draft pass marks in section 4; how refusing a fight is checked when the larger side is made to attack; whether abilities join the acceptance bar.

## 13. Where things are

| What | Where |
|---|---|
| Rules of the layer system | `docs/bible/epics/E-01-layer-system.md` |
| Open and closed questions | `docs/northstar/ambiguity_register.md` |
| Research: combat theory; active vision in other games; charts | `docs/research/topics/lanchester_and_combat_theory.md`, `active_layer_vision_mechanics.md`, `charts_for_combat_simulation_data.md` |
| History, the dimension map, every toy run | `history_2026-09-30_to_10-01.md` |
| The build brief | `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` |
| The frozen toy | `toys/layerlab/` |
| The real engine | `csrc/` |
