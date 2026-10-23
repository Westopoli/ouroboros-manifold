# Mission complications: perception brief

## 1. Feature and status

E-10 S-080 "Difficulty is scarcity, not stronger enemies" (`docs/bible/epics/E-10-missions.md:155-166`) carries the difficulty compression ramp whose content half is complications. Q-080-01 closed 2026-09-12: ship the full ramp at launch, design now (`docs/northstar/ambiguity_register.md:83`); the epic rules were never rewritten to match. Complication templates are library-builder output (E-21 S-153, `docs/bible/epics/E-21-offline-ai-pipeline.md:45`, "deferred until complications exist"). Stage 1 A-459 records the old design and a "Stage 7 plus" deferral (`docs/northstar/stage1_audit.md:664`). No complication exists in code. MVP placement: Round 3.

## 2. Player-facing goal as documented

"As a commander, I want hard mode to give me less to work with, never to give the enemy better units, so that I always lose to my own limits." (`E-10:157`)

Old bible (`docs/bible_history/bible_2_00_missions.md:286`): "As pressure mounts across generations, the simulation compresses what the player has to work with: time gets shorter, resources get thinner, objectives get compound, complications get more frequent, and stakes get heavier. A late-game defense mission and an early-game defense mission use the same archetype, but the late-game version is a desperate nightmare because you have half the force, two extra problems, and twenty fewer years of civilization health backing you up."

Old bible (`:320-322`): "Mid-mission complications are rare and pre-computed, not driven by a live simulation. The simulation is stopped during missions. When a mission is generated, the archetype's complication table identifies what could go wrong based on the current world state. Probability determines whether a complication actually fires — roughly every third mission, not every mission. If one fires, the timing and nature are determined at generation, not dynamically. This means complications feel like memorable disruptions, not background noise. A faction collapsing mid-evacuation is a story the player tells later. It shouldn't happen often enough to become routine."

Examples from the earliest bible (`docs/bible_history/game_bible_1_12.md:614`): "Defense missions might get "reinforcements from unexpected vector" or "political order to abandon position." Exploration missions might get "anomaly is not what it seemed" or "first contact goes sideways.""

## 3. Westley's own words

Q-080-01 answer, 2026-09-12 (`ambiguity_register.md:83`): "(c), full ramp. Ship the full compression ramp at launch (time width, resource generosity, complication frequency, ramp all difficulty-gated). Design now, not deferred."

Q-079-01, 2026-09-12 (`:82`): "Single-player team model. Player count fixed at campaign start. Host chooses preferences for team; host is "main" character, teammates are "side" characters (comrades/military staff). From simulation's perspective it's always single-player game."

A-058, Stage 1 (`stage1_audit.md:130`): "Westley: these choices don't need to be permanent... player should be able to change them later."

Q-124-01, 2026-09-16 (`ambiguity_register.md:115`), the one shipping surprise: "(a), external reinforcement waves ship at launch, p = 0.07 per mission, scheduled at generation and foreshadowed in briefing."

A-118 research flag (`stage1_audit.md:210`), on story quality: "the chronicle/story output read as "constructed and unnatural" in testing, not like a real story. Idea to explore later: a small LLM or neural net running either locally on the player's machine or on Westley's own servers... Mechanism TBD, explicitly deferred to a later stage."

## 4. Fixed constraints any option must honor

- R-080-01: both sides draw the same unit profiles; no stat differs by difficulty (`E-10:160`). Difficulty gives the player less, never the enemy more (A-454).
- Parity band: easy at least 0.95, hard at most 0.85, never below 0.75 (R-074-03, `E-10:77`).
- The strategic simulation is stopped during a mission; a complication is decided at mission generation, not live (A-459; old bible `:320`).
- Rare: about one mission in three, memorable, never routine (A-459).
- Difficulty and mission preferences can be changed later, not permanent (A-058; hub `game_bible.md:91`).
- Difficulty compresses time width, resource generosity, complication frequency, and the ramp across generations; it never changes the simulation, the archetypes, or narrative quality (Q-080-01; old bible `:290`).
- Content comes from the offline library builder; no runtime API calls (A-118; CLAUDE.md). Where complication templates live is open (Q-153-01, `ambiguity_register.md:144`).
- Briefing and debrief text contains no raw field numbers (R-079-04).
- Same seed, same mission and forces (E-10 invariant).
- A rare archetype stays selectable (R-080-03).
- The external reinforcement wave (p = 0.07, foreshadowed) already ships (E-14 S-124).
- Missions are 30 to 60 minutes of continuous real-time play, no pause in multiplayer.

## 5. Prior art already named

None for complications. `docs/bible/references/E-10/notes.md:3`: "TBD by design... start super simple and expand on player feedback." Difficulty-curve failure modes in the research corpus: `docs/legacy/topics/primary_tribe_psychographic_profile.md:70` ("Easy mode trivial, hard mode brutal, nothing in middle."), `docs/legacy/topics/audience_psychographics_2026.md:444`. Against the Storm's difficulty tiers (`docs/legacy/games/against_the_storm.md:26-28`).

## 6. Contradictions, as questions for Westley

1. Q-080-01 says "full ramp, design now"; A-459 says complications are deferred to "Stage 7 plus, after core missions work". Which holds for this pass: design the launch version, or the version that lands once missions work?
2. Is the old cadence still the intent: about one mission in three, decided at generation, timing fixed in advance, never reacting live to what the player does?
3. Is E-14's foreshadowed reinforcement wave (p = 0.07) a complication, the first complication, or a separate thing?
4. Should a complication be foreshadowed in the briefing (as the wave is), hinted mid-mission, or a true surprise?
5. Old bible mentions "complication frequency and overlap"; the register answer dropped "overlap". Can two fire in one mission?

## 7. Proposed option width

Two options, one wild, surface level (reduced in batch 3). Each option describes what a complication is to the player: how it announces itself, what it changes on the field, what decision it forces, how it reads in the debrief and the chronicle, and how difficulty changes its presence.

## 8. Westley confirms

Batch 3, 2026-09-22, verbatim: "every third mission is a little often, we want this to be a rarity and celebrated (like an easter egg), 1% chance. 1: surface level now, not too deep on this one since yes we want the core missions work designed first. 2: decided at generation 4: true surprise. 5: no"

Folded into the brief:

- Cadence: about 1 percent of missions, a celebrated rarity in the spirit of an easter egg, not one in three.
- Question 1: surface level in this pass; core missions are designed first. Width reduced to two options, one wild, with a shorter cap.
- Question 2: decided at mission generation, never live.
- Question 4: a true surprise, not foreshadowed.
- Question 5: no overlap; at most one per mission.
- Question 3 (the reinforcement wave's relation to complications): not answered; options may treat the wave as separate.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 2, of which 1 wild.
- Surface level. About 1 percent of missions, a celebrated rarity like an easter egg. Decided at generation, a true surprise, at most one per mission.
- Cap: 400 to 700 words plus tables.

## 10. Decision (2026-09-23)

Westley, verbatim: "For mission complications, I like crossed signals, let's do that."

Recorded as: Crossed Signals (Q-080-02).
