# Era transitions: perception brief

## 1. Feature and status

E-20 S-147 "Three eras, one skeleton", S-148 "Moving through eras", S-149 "Buying and earning eras", S-150 "Systems, not components" (`docs/bible/epics/E-20-multi-era-and-monetization.md`), and E-19 S-143 "Eras in sequence" (`docs/bible/epics/E-19-multiplayer.md:80-90`). Open flags: Q-147-01 (past and present eras unnamed), Q-147-02 (shared map seeds), Q-148-01 (the trigger), Q-148-02 (tech at the boundary), Q-149-01 (earn condition), Q-149-02 (which eras are purchase-only), Q-150-01 (what civilization content transfers) (`docs/northstar/ambiguity_register.md:136-142`). E-20 gate not passed. Ladder position P8 "Eras as data", second to last rung.

## 2. Player-facing goal as documented

"As a player, I want a campaign to move chronologically through the eras I own, so that a bloodline can span the ages." (`E-20:67`)

"The engine is a skeleton that never names an era. Eras are packs: names, art, prose, unit models by tier, structure and environment assets, naming pools, chronicle and briefing fragments, and per-era config values the engine consumes uniformly... The base game ships three eras (past, present, future) for $10 to $15 on Steam; further eras are $3 packs, some earnable through play and some exclusive. Era unlocks are the one progression unlock at launch. A campaign can move chronologically through eras the player owns." (`E-20:18`)

R-148-02: "Given the era transition, When the world carries over, Then region fields, ownership, tech, edges, and characters persist; only the pack changes; the chronicle frames the transition." (`E-20:71`)

## 3. Westley's own words

Vision v2 Q1, 2026-09-10 (`docs/northstar/vision_v2.md:23`): "The game has many different 'eras' available, so that players can play in many different time periods over time available as expansion packs, and if all the users in the match have the same multiple packs their 'match' can actually traverse through time chronologically."

Vision v2 Q5 (`:57`): "the time jump is calculated based on the simulation state, based on variables that is convenient at that time. Whether it's getting to the end of a run for an 'ancestor' and the 'family' needs to change (and whether the 'current' time contains such a family), The time jumps are anywhere between 20 - 100 years if I remember correctly, there's a range. Regardless of the literal jump, the story should and simulation still be noticeably effected by the outcome of the prior mission."

Vision v2 Q7 (`:73`): "Yes, we cannot build a different 'game' for every era, that task would be massive. However, I don't believe that the bible fully fleshed out how exactly we're going to accomplish the level of 'difference' across eras while still using the same 'skeleton' if you will."

Vision v2 Q8 (`:81`): "Fortnite for it's skin cross-compatability. Any skin, any dance, any map, it's all transferrable. The maps generation system, the era system, the specific civilizations, all need to be 'transferrable' between eras like fortnite skins, that's where the idea came from. Like we're building 'systems' instead of individual components, systems that can be used for many use-cases down the road (OOP)."

Vision v2 Q9 (`:89`): "$10-15 on steam, $3 per expansion, expansions are grindable, some are exclusive but not all." Q10 (`:97`): "3 eras, past/present/future."

A-061, Stage 1 (`docs/legacy/agora_era/stage1_audit.md:133`): "Westley: unlocks DO exist — unlocking other eras is the one scoped unlock type right now, and he's not opposed to more later."

A-071, new from Westley (`:141`): "once the timeline reaches its chronologically last/final era, the game continues indefinitely in that era's state rather than collapsing to extinction and restarting. Technology level oscillates over time — periodic mild regression followed by recovery, sine-wave pattern — instead of a hard collapse/reset."

A-063 (`:135`), on the Ouroboros restart: "Westley: mark as an idea, not built yet — he hasn't worked out how a continuous single-timeline playthrough should handle this, and doing it authentically needs a lot of new assets."

Q-147-01 answer column (`ambiguity_register.md:136`): "Westley to name and brief them (Era Creation Template layers 1 and 2)".

## 4. Fixed constraints any option must honor

- Sacred principle 3, era-agnostic architecture: no code branches on era (`docs/bible/game_bible.md:75`); R-145-02 (`E-20:33`).
- R-147-02: the same code runs every era, a pack is loaded (`E-20:59`).
- R-148-02: the world carries over; only the pack changes; the chronicle frames the transition (`E-20:71`).
- R-148-03: the last owned era continues indefinitely with tech oscillating (A-071) until S-054 is designed (`E-20:72`).
- R-149: one Steam SKU with three eras, $3 packs, some earnable, no subscription or store; era unlocks are the only unlock (`E-20:83-87`).
- R-143-01 to 03: a match traverses only eras every peer owns, chronologically; a transition is a time jump to the next owned era (`E-19:84-86`).
- R-150: layouts, civilizations, skins valid in every era, no era tag (`E-20:97-99`).
- R-146-04: the Era Creation Template's six layers and fixed abstractions (6 unit types, fixed rock-paper-scissors, spine plus five gradients, three tiers) (`E-20:48`).
- Time jumps are 20 to 100 years, uniform random, state input possible later (Q-056-01).
- Always 5 layers in every era (Q-E01-01). Cross-era silhouettes fixed per unit type (A-413).
- Scale gate: pack load under 2 s; era switch in a campaign under 5 s (`E-20:140`).
- The three launch eras play identically (A-321); this brief is about the transition, not the feel; see `../era-feel/`.
- No IP: no names, places, or plots from existing fiction.

## 5. Prior art already named

Fortnite's cross-compatible content (vision Q8). Counter-model: Total War, where different eras are different titles (`docs/legacy/games/total_war_franchise.md:16`). Wildermyth legacy heroes carried across campaigns (`docs/legacy/games/wildermyth.md:26,77`). Old branch-ladder design in `docs/legacy/design_questions/era_selection_design.md` (historical, subscription framing scrapped). Refund risk of shallow era transitions (`docs/legacy/topics/refund_rate_norms.md:161,167`).

## 6. Contradictions, as questions for Westley

1. The trigger is open (Q-148-01) but E-19 R-143-02 already says a transition "is a time jump whose destination era is the next owned era". Confirm the time jump is the vehicle, and that the open question is only what decides which jump crosses the boundary (elapsed years, tech, chapter count, player choice, or something else).
2. R-148-02 says tech persists across the boundary; Q-148-02 still asks whether tech resets, carries, or rescales. Which is the working assumption for the options?
3. Past and present eras are unnamed (Q-147-01). May the options propose what the boundary feels like without naming the eras, or do you want candidate settings proposed as part of this pass?
4. In a match, who experiences the transition together, and what does a player who does not own the next era see (R-143-03 limits the match, but the moment itself is undescribed)?

## 7. Proposed option width

Three options, one wild. Each option describes what the player experiences at the boundary: what they see in the galaxy view and chronicle, what they recognize afterward (their bloodline, their factions, their map), what changed, and how they knew a boundary was coming.

## 8. Westley confirms

Batch 2, 2026-09-22, verbatim: "Rescale tech, if players are a part of the same civilization, a multi-civ rescale isn't needed. The teams shoudln't immediately jump to late game after an era jump, but the civ that was "leading" should still be leading. If a player lacks a pack, they can't "go" to that next era, and the time jump will go through all of history (looping through eras) until every player has an era. The chronicle will record old characters as "distant myths/legends" with smaller and smaller mentions the farther out you go."

Folded into the brief:

- Tech at the boundary (question 2): rescale. Nobody arrives in the new era at late game; the civilization that was leading still leads. Players in one civilization share the rescale; a multi-civilization rescale is not needed.
- A missing pack (question 4): a player without the next era cannot go there. The time jump keeps going through history, looping through the eras, until it lands on an era every player owns. History is a loop, not a line that ends. Confirmed 2026-09-22, verbatim "history loop through eras: yes in solo campaigns": the loop replaces the Stage 1 interim in which the last era continued indefinitely (A-071); E-20 R-148-03 is rewritten and the loop's mechanics are flagged (Q-148-04).
- The chronicle: characters from earlier eras become distant myths and legends, mentioned less and less the farther the timeline moves from them.
- The vehicle (question 1): the time jump carries the transition. What decides which jump crosses the boundary stays open; options may propose it.
- Names (question 3): not answered. Options describe the boundary without naming the past and present eras.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 3, of which 1 wild.
- Tech rescales at the boundary: nobody arrives at late game, the leading civilization still leads.
- History loops: after the last owned era the next time jump returns to the first, in solo campaigns as well as matches; when a peer lacks the next pack the jump keeps going until an era every peer owns. Options show what the player sees when history comes around again: the same galaxy and ledger, characters faded to myth.
- Earlier characters fade into distant myths and legends in the chronicle, mentioned less the farther the timeline moves.
- Propose what decides which time jump crosses the boundary. Do not name the past and present eras.

## 10. Decision (2026-09-23)

Westley, verbatim: "For era transitions I like the long horizon."

Recorded as: The Long Horizon (Q-148-01 closed; the reach measure is Q-148-05).
