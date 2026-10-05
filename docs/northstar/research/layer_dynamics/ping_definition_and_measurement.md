# The ping: what it is, and how the skill lab measures it

Status: definition restated from Westley, 2026-10-05, against E-01 S-162. The measurement method is a proposal that waits for his go. Every number here is a provisional runtime setting or a draft sweep point; none is confirmed.

## 1. What the ping is

Westley, 2026-10-05:

> "Some set of units that we define have the ability to essentially ping some place that the player picks. The ping will give them a brief snapshot of the area that they're pinging, and the ping will have a specific range outside of their vision by some margin that we decide. But not cross the map. Players will be able to choose the specific layer that they are pinging. And if an enemy is inside the ping's radius, then that unit will be visible for some amount of time that we specify. The units that got pinged will be alerted that they were pinged, but they won't know where from. Just a general direction, about 60 degrees."

> "Skilled players will use the ping system to effectively guess where their opponent's forces might be and use the series of pings that they have access to find the enemy's forces without the enemy's forces ever getting inside their vision. When I say vision, I mean like true unit vision. The ping system is designed to be the method that players can devise traps and plan surrounds, essentially plan ahead, knowing the enemy's current position and unit composition and unit formation."

This agrees with what is already written and built:

| Part | Rule | Built in the engine | Setting (provisional) |
|---|---|---|---|
| Pick a place and a layer; see that layer around that place for a moment | R-162-01 | `om_command_ping(caster, layer, x, y)`, `csrc/fog.c` | radius 500 |
| Reach is beyond the caster's sight, and is not the whole map | R-162-01 | refused beyond the reach | reach 2,000 |
| An enemy inside is visible for a set time | R-162-01, R-162-05 | a reveal disc that lives for the reveal time | reveal 2 s |
| Limit on repeated use | R-162-02 | cooldown per casting unit; no resource cost | 20 s |
| The pinged side is alerted with a sector of about 60 degrees, nothing more | R-162-03 | alert with a sector | 60 degrees |
| Only some units can ping | R-162-01 "units that can ping" | not built: any living unit can cast | open, Q-005-04 |

So the ping is decided in kind and exists in the engine. What is missing is: the numbers (Q-005-04), four questions of kind (section 6), the lab's ability to cast a ping at all, and a way to measure the skill. The rest of this file is about the last two.

## 2. How the ping differs from the five skills

The lab's five skills (README section 3) are each measured the same way: a skilled play against a naive play, scored in whole units at break-even, with "units firing per side" as the explanation. That works because each play changes directly who gets shots off.

| Skill | What the play changes | How it shows up in a fight |
|---|---|---|
| S1 Landscape | how many enemies can fire | fewer enemy units firing |
| S2 Formation | how many of your own fire at once | more own units firing |
| S3 Layers: reach by type | who can fire at whom across layers | one side fires, the other cannot |
| S3 Layers: going dark | who is seen first | who fires first |
| S5 Matchup | which type fires at which | damage per shot |
| **The ping** | **nothing in the fight itself** | **nothing, by itself** |

A ping deals no damage, blocks nothing and moves nobody. Its whole value is that it lets a player choose a better play before contact: where to set the concave, which choke or layer to hold, where to wait in ambush, which types to put in front. It is the action that turns S4 ("the other player's current position") from luck into intent, and it is the input that the plays of S1, S2 and S5 need in order to be set up in the right place.

Three consequences for measurement:

1. **A ping cannot be scored by a fight alone.** Two forces that ping and then walk into each other fight exactly as if nobody had pinged.
2. **Its value is the product of two things:** how often and how early the player learns what matters (information), and how many units that knowledge is worth once acted on (conversion).
3. **The skill is in the guesses.** The other skills have one skilled play. The ping has a policy: where, on which layer, and when to ping next, given what the last pings showed. The simulation has no dice, so "better guesses" must be shown as one policy beating another over many hidden enemy placements, not in one fight.

## 3. The measurement: two stages, then a product

### Stage A: search, with no fight (cheap, thousands of runs)

One side (the seeker) moves along its route and pings by a scripted policy. The other side (the hider) is placed, hidden, at one of many seeded placements: a position, a layer, a heading and a movement script. No one fires. Each run ends at first true-vision contact or at a time limit.

Recorded per run, for each side:

| Measure | Meaning |
|---|---|
| Found before contact | did a ping reveal the enemy before any unit was in true vision (yes or no) |
| Warning time | ticks between the first reveal and first true-vision contact; the time available to re-arrange |
| Picture quality | share of the enemy's units revealed at least once before contact; whether their layer was learned; whether each type was seen |
| Picture age | ticks since the last reveal at the moment of contact; an old picture of a moving enemy is wrong |
| Pings spent, pings that found | the cost of the search |
| Alerts given | each ping that lands on units tells the enemy a 60 degree bearing; how many times the seeker gave itself away |
| **Detection ratio** | found-before-contact rate of one side over the other's, across the placement set (Westley's proposal) |

The policies, from naive to skilled. Each is a script, the same on every placement:

| Policy | What it does |
|---|---|
| none | never pings (the control: knowledge comes only from true vision) |
| ahead | pings straight along its own route at the edge of reach, own layer, every cooldown |
| sweep | cycles through bearings and layers in a fixed order |
| likely places | pings the places the map makes likely: the far side of a choke, behind tall cover, the routes into the objective, and the layers from which each could be reached |
| reactive | as "likely places", and also: after an alert, pings back along the alert's sector; after a reveal, pings where the revealed units were heading |

The hider's counters, also scripts: stand still; relocate when alerted (so the picture goes stale); split a decoy that is meant to be found; ping back.

"Better guesses" is then a measured thing: the gap in found-before-contact, warning time and picture quality between a higher policy and a lower one, over the same placements.

### Stage B: what knowledge is worth (few fights, uses the existing plays)

For a scene where the enemy may come by one of several routes or layers, fight three cases with the same forces:

| Case | The defender's play is set up | Result |
|---|---|---|
| informed | at the enemy's true route and layer (as if a ping had shown it in time) | break-even, in whole units |
| uninformed | at each possible route and layer in turn; the mean is what a guess is worth | break-even, in whole units |
| stale | at where the enemy was N seconds ago, the enemy having relocated | break-even, in whole units |

**Value of knowing** = informed minus uninformed, in whole units. It is measured once per play (the S1 choke, the S2 concave, the S4 ambush, an S5 type line-up), with no ping cast at all. It answers: if the ping worked perfectly, how many units is it worth? If this number is near zero for a play, no ping setting can matter for that play, and the cause lies in the play or the terrain, not in the ping.

### The product

**Units gained by a ping policy** = (share of placements found with enough warning to re-arrange) x (value of knowing), less the cost of what the alerts gave away (measured by running the hider's "relocate" and "ping back" counters).

"Enough warning" is the time the play needs to be set up, measured in Stage B by moving the informed setup later and later until its advantage is gone.

Splitting it this way keeps the work small: fights are expensive and are run a few hundred times; searches have no combat and can be run in the tens of thousands across the settings.

## 4. Which settings induce strategic depth

A setting is a tuple: reach, radius, reveal time, cooldown (the frequency), how many units can cast, and the alert rule. The lab reports, for each tuple, these five readings. Which values count as passing is Westley's (Q-162-05).

| Reading | Depth is present when | It fails when |
|---|---|---|
| **Policy spread**: found-before-contact of the best policy minus that of "ahead" | the gap is large: guessing well is rewarded | the ping is so big or so frequent that every policy finds the enemy (no skill), or so small that none does (a lottery) |
| **Counter cost**: how much "relocate when alerted" and "decoy" reduce the seeker's picture, and what they cost the hider in time and position | the counter works and costs something | the counter is free and total (pinging is pointless), or does nothing (being pinged is a death sentence) |
| **Value of knowing**, Stage B | knowledge is worth whole units for at least the trap plays | it is worth nothing: the ping is decoration |
| **Warning time against set-up time** | the best policy usually gives enough time to re-arrange; "ahead" usually does not | everyone has time, or no one does |
| **Give-away**: alerts per find, and the enemy's found-before-contact when it pings back along the sector | pinging carelessly gets the pinger found | pinging has no risk, so the best policy is "ping everything, always" |

One number predicts most of this before any run and is the axis the sweep should be laid out on:

**Coverage rate** = (casters x area of one ping) / (cooldown x area within reach x layers to search).

It is the share of the searchable volume a force can look at per second. Near 1, the map is simply visible and the ping is a wider sight radius. Near 0, finding anything is luck. Depth lives in between, where there are more places worth looking than pings to look with, so the choice of place and layer is the skill. The five layers matter here: they multiply the volume by five, which is what makes "which layer" a real guess.

Draft sweep points (drafts, not confirmed; the first pass is Stage A only, so it is cheap):

| Setting | Points |
|---|---|
| reach, as a multiple of true vision | 1.5, 2, 3 |
| radius | 250, 500, 1,000 |
| reveal time | 1 s, 2 s, 5 s |
| cooldown per caster | 5 s, 10 s, 20 s, 40 s |
| casters in a force of 16 | 1, 2, 4 |
| alert | on every ping that lands on units (today); on every ping, found or not |

## 5. Putting it into the simulation

The engine needs almost nothing. The lab needs four pieces, in this order. Each is small and has a positive control.

| Step | Piece | Where | Control |
|---|---|---|---|
| 1 | Bind `om_command_ping` in the lab's engine wrapper, with read-outs: which enemy units a side currently sees by ping and by true vision, and the alerts a side received | `scripts/skilllab/engine.py` (the calls exist in the library; if no public read-out separates "seen by ping" from "seen by sight", that is a contract piece first) | a ping on a known enemy reveals it and only on the pinged layer; one beyond reach is refused; the alert's sector contains the true bearing |
| 2 | Casters: the lab restricts which of its units may cast (a list per group), since the engine lets any unit cast | lab only; an engine rule waits for Q-005-04 | a non-caster's ping is never issued |
| 3 | The search scene and the policies: a no-fire scene, a seeded placement set, the five policies and four counters as controllers stepped at an interval (the lab already steps a per-interval rule for re-orders) | `scripts/skilllab/` new files | on a placement directly ahead, "ahead" finds it; on one behind cover on another layer, "ahead" does not and "likely places" does |
| 4 | The value-of-knowing batch: the informed, uninformed and stale cases for each play | `scripts/skilllab/batches.py` and the plays | informed is never worse than the mean of uninformed |

Step 4 depends on the lab's terrain being on the units' layer and on the plays of S1, S2, S4 and S5 being registered (both found missing on 2026-10-05; see the run notes). Steps 1 to 3 depend on neither and can start at once.

Output: one chart page per stage. Stage A: found-before-contact by policy against coverage rate, one line per policy; the gap between the lines is the skill. Stage B: value of knowing per play, in whole units.

## 6. Open questions (Westley's)

| Row | Question |
|---|---|
| Q-005-04 (1) | which units can cast; the numbers |
| Q-162-01 | does a ping see behind cover or ground |
| Q-162-02 | does the reveal stay with the place, or follow the units it caught |
| Q-162-03 | is the limit a cooldown per casting unit, or a pool of pings per player |
| Q-162-04 | is the alert sent on every ping, or only when it lands on units |
| Q-162-05 | what readings count as "induces strategic depth" for the ping |
