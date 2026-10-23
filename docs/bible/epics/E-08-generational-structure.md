# E-08 — Generational Structure

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 11 stories, 54 rules, numbers from `algorithms.md` ALG-45 through ALG-49 and Stage 1 verdicts A-050, A-052, A-058, A-061. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | No open flag on S-228 (Q-228-01 and Q-228-02 closed 2026-10-21, register); Q-159-07 and Q-159-13 are cited and held by E-22 S-182 and E-02 S-220. |
| Every visible-surface story has a reference | **No.** S-063 (onboarding screen) has a visible surface and no reference. The chronicle scroll surface is E-09. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** S-228 (added 2026-10-02) has not been through the gate and has no open flag (Q-228-01 and Q-228-02 closed 2026-10-21, register). One reference is missing (S-063). S-055 to S-064 have no open flags; gate to be rerun.

## Purpose

A campaign is a chain of chapters. Each chapter is one commander, one mission, thirty to sixty minutes. Between chapters the galaxy runs on its own for decades while the player watches the chronicle scroll. Then the player returns as someone new: usually a descendant of the last commander, sometimes a descendant of an old enemy, rarely a stranger raised by circumstance. A family holds the player for a few chapters, then the story moves on. The world never resets; the player's forces always do.

The bloodline is cosmetic by decree (vision_v2 Q3): it changes who the player is and what the chronicle says, never a single simulation number. What this epic owns is the loop itself, the time jump, the character selector, the ledger of named people, and the moment the player's civilization falls out from under them.

## Obviously working in 60 seconds

Finish a mission as commander A of lineage L in region R. The sim runs a time jump; the chronicle shows 5 to 10 entries; the map animates border changes. The selector reports chapters-in-lineage 1, so the player stays: the next commander is a living member of L within two hops of the next mission region. Finish two more chapters: with the home region quiet, the stay probability has fallen and the player rotates to a descendant of a rival tagged in chapter 1, in a different faction, with a new lineage id. Kill the commander in a mission: the next chapter is a living relative in or next to the region, or a rotation if none exists. Same seed and the same mission outcomes: the same commanders every time.

## Stories

### S-055 — One commander, one mission, then the world moves
As a player, I want each chapter to be briefing, recon, mission, resolution, time jump, new commander, in that order, so that the rhythm of the game is always the same and always earned.

Rules
- R-055-01  Given a new chapter, When it starts, Then the order is: mission briefing, recon (free camera, no mission clock), mission (real time, no pause), outcome resolution, time jump with chronicle, character selection, next briefing.
- R-055-02  Given a mission is running, When any tactical tick passes, Then no strategic tick runs; the strategic sim is stopped for the mission's duration.
- R-055-03  Given the mission resolves, When the outcome resolver applies its consequence bundle (E-10), Then those field changes land before the first tick of the time jump.
- R-055-04  Given the time jump completes, When the mission generator runs, Then the character selector runs after it and reads the chosen mission region.
- R-055-05  Given the campaign's first chapter, When the world is generated, Then an opening time jump runs before the first briefing and its chronicle shows 3 to 5 world entries only.
- R-055-06  Given the chapter counter, When read, Then the campaign starts in chapter 1, the opening jump belongs to chapter 1 and does not advance it, and the counter advances by one at the end of each time jump that follows a mission (played or refused); a retry jump with no mission (E-10 R-072-07) never advances it. At the end of such a jump the order is: collapse check (S-062), mission generator, character selector (R-055-04), chapter advance. At the end of the opening jump the mission generator and the character selector run in that order, with no collapse check and no advance. At the end of a retry jump only the mission generator runs.

Inputs: mission outcome; world state.
Outputs: chapter record (number, faction, character, start and end tick, end reason) in the save file.
Open flags: none. R-055-02 is about the strategic sim; the economy that grows during a mission (E-22 S-182) is part of the mission, and no strategic tick runs for it. The only channel from a mission to the simulation that R-055-03 names is field changes; what else a mission leaves behind is E-02 S-220.

### S-056 — Decades pass while I am gone
Flag closed, rule text pending: Q-056-01, the jump length is uniform random in [20, 100] with no state input, flagged for tuning after testing. The rule below is what the tests read today.
As a player, I want the gap between chapters to be decades long and decided by the world, not by me, so that each return feels like history happened.

Rules
- R-056-01  Given a time jump, When its length is chosen, Then it is an integer number of ticks in [20, 100], one tick being one in-world year [Q-056-01: code uses a fixed 50].
- R-056-02  Given the jump length, When the jump runs, Then exactly that many strategic ticks run with the full tick sequence (ALG tick sequence), and the player cannot shorten, lengthen, or interrupt it.
- R-056-03  Given the jump, When it ends, Then the report lists territory changes, faction births and deaths, conquests, colonizations, revolts, per-faction average field deltas, the chronicle entries, and an ownership snapshot every 2 ticks for the map animation.
- R-056-04  Given the opening jump, When its length is chosen, Then it is in [20, 50].
- R-056-05  Given the jump, When it ends, Then lineage members are generated (S-059) and natural deaths processed (S-060) once, at the end tick.

Inputs: world state at jump start; config bounds.
Outputs: time jump report; chronicle input (E-09); map animation input (E-16).
Open flags: none here. No rule here calls a jump short or long; whether damage persisting across a jump depends on its length is part of Q-159-13 (E-02 S-220).

### S-057 — Stay with the family or move on
Flag closed, rule text pending: Q-057-01, declined as an implementation decision: no curve is chosen, the builder picks it and the tests on the decaying stay probability gate it. The rule below is what the tests read today.
As a player, I want to stay with a bloodline while its story is alive and move on when it goes quiet, so that lineages feel like arcs and not like a counter.

Rules
- R-057-01  Given a lineage with no living members, or a dead commander with no living lineage member within 2 hops of the mission region, When selection runs, Then rotation is forced with reason `forced`.
- R-057-02  Given the lineage has fewer than 2 chapters played, When selection runs, Then the player stays.
- R-057-03  Given the home region's total field delta over the jump is D, When the base rotation probability is computed, Then p = 0.8 + min(1, D/200) · (0.1 − 0.8), so a quiet jump (D = 0) rotates at 0.8 and an active one (D ≥ 200) at 0.1.
- R-057-04  Given chapters played in the lineage is c ≥ 2, When the stay probability is computed, Then it decays with c and never reaches 0 or a hard cap [Q-057-01: proposed p_rotate = base p + (1 − base p) · (1 − 0.75^(c − 2))].
- R-057-05  Given the roll says rotate and the lineage home region's stability is below 20, When selection runs, Then the rotation is vetoed and the player stays.
- R-057-06  Given the player stays, When the commander is chosen, Then it is the first living lineage member within 2 hops of the mission region, else the current commander if alive.
- R-057-07  Given the home region, When it is looked up, Then it is the first region in the lineage's history.
- R-057-08  Given a rotation, When it is recorded, Then the chapter counter for the new lineage starts at 1 and the record carries the reason (`forced`, `normal`, `commander_death`) and the pool used.
- R-057-09  Given the campaign has no commander yet (the selection at the end of the opening jump), When selection runs, Then it is a forced rotation (R-057-01) whose previous and nemesis pools are empty, so the unrelated pool (R-058-04) creates the first commander and the first lineage in the mission region; the lineage's chapter counter starts at 1.

Inputs: lineage members; chapter counter; home region delta and stability; RNG.
Outputs: commander selection record in the save file and chronicle framing.
Open flags: none.

### S-058 — Who I come back as
As a player, I want my next commander to usually be family, sometimes an old enemy's heir, and rarely a stranger, so that the cast of the galaxy stays connected.

Rules
- R-058-01  Given a rotation, When the pool is rolled, Then one draw picks previous-descendant with probability 0.70, nemesis-descendant 0.20, unrelated 0.10; if the rolled pool is empty the search falls through in the order previous, nemesis, unrelated.
- R-058-02  Given the previous-descendant pool, When candidates are scored, Then each previously played lineage with a living member within 2 hops of the mission region, last played at least 1 chapter ago, scores gap · 0.6 + density · 0.4 with gap = min(chapters ago, 4)/4 and density = min(living nearby, 5)/5; a member is drawn with probability proportional to its lineage's score.
- R-058-03  Given the nemesis pool, When candidates are gathered, Then they are living descendants, within 2 hops, of characters tagged as rivals of any previous commander, excluding the rivals themselves; one is drawn uniformly.
- R-058-04  Given the unrelated pool, When used, Then a new character is created in the mission region's owning faction with a new lineage id.
- R-058-05  Given a mission ends, When rivals are tagged, Then every named enemy-faction character in the mission region gains a rival tag pointing at the player's commander.
- R-058-06  Given any selection, When it completes, Then the commander is marked as a main character so its name is reserved longer after death (E-21 naming).

Inputs: ledger; chapter history; mission region; RNG.
Outputs: selection record with pool rolled and pool used.
Open flags: none.

### S-059 — The family grows while I am away
As a player, I want my bloodline to have descendants when I return, spread across nearby regions, so that there is always someone to come back as.

Rules
- R-059-01  Given a lineage with n living members and a jump of T ticks, When members are generated at the jump's end, Then max(1, floor(n · 0.03 · T)) descendants are created.
- R-059-02  Given each descendant, When placed, Then its parent is a uniform draw among living members, its faction is the parent's, and with probability 0.1 it is placed in a uniform-random inhabited neighbor of the parent's region, else the parent's region.
- R-059-03  Given a descendant, When recorded, Then it has a name, region, faction, birth tick equal to the jump's end tick, lifespan, lineage id, parent id, and generation = parent's + 1; nothing else.
- R-059-04  Given a lineage with no living members, When generation runs, Then nothing is created.

Inputs: lineage; jump length; world; RNG.
Outputs: ledger records.
Open flags: none.

### S-060 — Named leaders live and die
Flag closed, rule text pending: Q-060-01, natural deaths are processed per tick. The rule below is what the tests read today.
As a player, I want the people the chronicle names to be born, serve, age, and die, with someone taking their place, so that the galaxy has faces and not just factions.

Rules
- R-060-01  Given a faction is created, When named, Then it gets a supreme commander in its first region; Given a region is colonized or conquered, When named, Then it gets a regional commander.
- R-060-02  Given a character is created, When its lifespan is rolled, Then it is a uniform integer in [150, 350] ticks.
- R-060-03  Given a character's age reaches its lifespan, When natural deaths are processed, Then it becomes historical with a death tick, and if its rank is supreme or regional commander a successor is created with a fresh name and lifespan in the same faction and region (regional only if the faction still owns the region).
- R-060-04  Given natural deaths, When processed, Then it happens once at the end of each time jump, not every tick [Q-060-01].
- R-060-05  Given an event of significance tier 3 or higher fires in a region, When logged, Then the region's named characters are attached to the event record; the ledger never stores event history itself.
- R-060-06  Given any character record, When read, Then it holds exactly: id, name, faction, region, rank (supreme_commander, regional_commander, garrison_officer, lineage_member), birth tick, lifespan, status, death tick, lineage id, parent id, generation, rival tags, children.

Inputs: faction and region events; tick; RNG.
Outputs: ledger; event attachments in the tick log; chronicle input.
Open flags: none.

### S-061 — When my commander dies
As a player, I want a fallen commander's place taken by a relative nearby if one exists, so that death is a chapter in the family's story and not the end of it.

Rules
- R-061-01  Given the commander died in the mission, When the next selection runs, Then a living lineage member (not a supreme commander) in the mission region is chosen first, then one in an adjacent region, then, only if the lineage has fewer than 2 chapters played, any living member anywhere.
- R-061-02  Given a successor is found, When assigned, Then the successor becomes the commander of the same lineage and the chapter counter continues.
- R-061-03  Given no successor, When selection runs, Then rotation happens with reason `commander_death`.
- R-061-04  Given a commander death, When recorded, Then the ledger records the region and outcome band and the chronicle frames it (E-09).

Inputs: commander status from the outcome resolver (E-10).
Outputs: succession or rotation record.
Open flags: none.

### S-062 — When my civilization falls
As a player, I want to keep playing in a surviving faction when mine is gone, so that the fall is a story beat and not a game over.

Rules
- R-062-01  Given the player's faction has zero regions or no longer exists at the end of a time jump, When collapse is checked, Then the chapter ends with reason `faction_collapsed`.
- R-062-02  Given collapse, When the new faction is chosen, Then the rotation pools of R-058-01 to R-058-03 run restricted to candidates in surviving factions, with the 2-hop distance measured from the last mission's region, and the player joins the faction of the candidate drawn; if both pools are empty, the surviving faction with the most regions is chosen, uniform among ties (Q-062-01).
- R-062-03  Given no faction with any region survives, When collapse is checked, Then the campaign ends with reason `no_surviving_factions` (interim until S-054 is designed).
- R-062-04  Given reassignment, When recorded, Then the chronicle carries a major entry framing the fall.

Inputs: registry; ownership.
Outputs: reassignment record; chronicle.
Open flags: none.

### S-063 — My two choices at the start
Flag closed, rule text pending: Q-063-01, there is no limit on rare marks, but at least one archetype stays unmarked. The rule below is what the tests read today.
Flag closed, rule text pending: Q-063-02, difficulty and preferences are set once at campaign creation and fixed for the whole campaign, with no mid-campaign change. The rule below is what the tests read today.
As a player, I want to pick a difficulty and which kinds of missions I prefer before the first chapter, and change my mind later, so that the game bends to how I like to play without locking me in.

Rules
- R-063-01  Given the onboarding screen, When shown, Then it offers difficulty (easy, medium, hard) and, for each of the 10 mission archetypes, a preference.
- R-063-02  Given the player confirms, When saved, Then the choices are stored per save slot and read by the mission generator (E-10) and difficulty scaling.
- R-063-03  Given the player wants to change the choices later, When they do, Then [Q-063-02: where and when; Westley removed permanence, A-058].
- R-063-04  Given a new campaign after a terminal condition (S-054), When it starts, Then the onboarding screen shows again.

Inputs: player choices.
Outputs: onboarding record in the save file; mission generator weights.
Open flags: none. Reference required: `references/E-08/notes.md`, missing.

### S-064 — What carries over
As a player, I want the world to remember everything and my character to start fresh, so that my legacy is in the galaxy and not in a stat sheet.

Nothing carries forward between missions in the beta (E-22 S-182; Westley, 2026-10-07); R-064-02 and R-064-03 stay true, and are rewritten if a post-beta carry-forward is chosen. A carried deck, ability or economy would also have to enter the save and the determinism trace of R-064-04.

Rules
- R-064-01  Given any chapter transition, When the next chapter starts, Then every region field, ownership, faction, tech level, edge type, event queue, and ledger record persists unchanged except by the sim itself.
- R-064-02  Given a new chapter, When forces are assigned, Then they come only from the mission generator's allocation (E-10); nothing carries from the previous mission's surviving units.
- R-064-03  Given progression, When read, Then there is no player level and no stat carried between commanders; the unlock types are era unlocks (E-20) at launch and trait cards (E-11 S-083) after launch.
- R-064-04  Given a save and load between chapters, When loaded, Then the next time jump produces the same trace as if never saved (determinism includes the RNG state and the chain tag counter).

Inputs: none.
Outputs: save file; determinism trace.
Open flags: none.

### S-228 — More than one player in a chapter
As a player in a team of 2 or 4, I want the chapter, the ledger and the world to know I am in a team, so that my pair is a part of the story and not a rider on someone else's.

Direction decided in part 2026-10-02 (DECISIONS H7; E-19 R-159-01): more teammates mean bigger maps, more to do, more resources and more enemies; each player is a sub-commander; each pair is a sub-civilization inside the over-arching civilization. The simulation has no notion of either. Not scheduled for building. S-055 to S-064 are written for one player and one commander and stay as written for it.

Rules
- R-228-01  Given a chapter played by a team of 2 or 4, When the chapter record, the ledger and the character selector are used, Then only the commanding seat has a ledger character; the economy seat has none (Westley 2026-10-21).
- R-228-02  Given a team of 4, When each pair is read as a sub-civilization inside the civilization, Then [Q-228-02: how a pair maps onto the simulation, which has one faction per civilization and no sub-civilization; whether onto a faction, a set of regions, or only the chapter].

Inputs: team size and pairs (E-19 S-159).
Outputs: none until the flags are answered.
Open flags: none. Q-228-02 closed 2026-10-21 (register: map the pair onto the chapter only).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Mission outcome, commander fate | E-10 | outcome band; survived, wounded, killed | unknown band fails resolution |
| Mission region | E-10 mission generator | region id | unknown id fails selection |
| Jump length | S-056 | [20, 100] | clamped into range |
| Home region delta | Time jump report | ≥ 0 | |
| Onboarding choices | Player | difficulty in {easy, medium, hard}; rare marks < 10 | invalid values rejected at save |
| RNG | World stream | | |

## Outputs

| Output | Observable where |
|---|---|
| Chapter records | Save file; debrief screen (E-16) |
| Commander selection with pool and reason | Save file; chronicle rotation framing; briefing header |
| Time jump report | Chronicle scroll (E-09); map animation (E-16); T1 trace |
| Ledger records and attachments | Save file; chronicle names; briefing |
| Onboarding record | Save file |

## Invariants

- Exactly one commander per chapter; the commander is a living ledger character at chapter start.
- Chapter numbers are consecutive from 1.
- A lineage's chapter counter never exceeds the number of chapters played.
- The bloodline never changes a simulation field, budget, stance, or tech (vision_v2 Q3).
- Same seed and same mission outcomes give the same commanders and the same jump reports.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): a 100-tick jump on 60 regions and 15 factions completes, including chronicle distillation, in under 2 s; ledger with 5,000 characters selects a commander in under 5 ms.

## Look and behavior references

`references/E-08/notes.md`, missing: the onboarding screen (difficulty and archetype preference, 2 to 5 screenshots of games whose setup screens read the way Westley wants).

## Ways this could be wrong

- Selector runs before the mission generator, reading a stale region.
- Rotation probability inverted (active regions rotate more).
- Hard cap still enforced after Westley removed it.
- Successor search ignores the 2-hop limit or the supreme-commander exclusion.
- Lineage counter incremented twice on a stay.
- Natural deaths never processed, so the ledger only grows.
- Rival tags applied to friendly characters.
- Reassignment picks the player's own dead faction.
- Onboarding permanence still enforced.

## Open ambiguity flags

Q-228-02 (S-228), with Q-159-07 and Q-159-13 held by E-22 S-182 and E-02 S-220. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-02 through E-07 (the sim that runs during the jump).
- E-09 Chronicle (the scroll the jump produces).
- E-10 Missions (mission generation, outcome resolver, commander fate).
- E-16 Client (briefing, debrief, map animation, onboarding screen).
- E-20 Multi-era (era unlocks).
- E-21 Offline AI pipeline (naming library).
- E-19 Multiplayer (S-159 teams, pairs and the economy seat, S-228).
- E-22 Economy and bases (S-182 what carries forward).
- E-02 S-220 (what a mission leaves in a region).
