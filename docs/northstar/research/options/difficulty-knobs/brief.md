# Enemy macro difficulty knobs: perception brief

## 1. Feature and status

E-14 S-125 "How hard the enemy tries" (`docs/bible/epics/E-14-enemy-macro-behavior.md:91-102`). Q-125-01 closed 2026-09-16 as "Deferred" (`docs/northstar/ambiguity_register.md:116`) while the E-14 gate still lists it as blocking (`E-14:14`). Stage 1 A-149 and A-156 record the interim plan (`docs/legacy/agora_era/stage1_audit.md:250,257`). The learned opponent is an aspirational target (old bible Target 2). MVP placement: Round 2; the difficulty card is deferred in the test-authoring plan.

## 2. Player-facing goal as documented

"As a player, I want a difficulty knob that changes how much the enemy has, not how well its units fight, so that I always lose to my own limits." (`E-14:93`)

E-14 purpose (`:18-20`): "The enemy's units think exactly like the player's. What makes an enemy feel like a plan is the layer above them: each enemy force runs a small state machine authored per mission archetype from a shared vocabulary of five behaviors and three modifiers, with timers that keep the mission moving even if the player sits still, thresholds that react to what the player does, and noise rolled once at mission start so the same script never plays the same twice... The long-term target is an opponent that feels like it reads the player (Stage 1 A-149, A-150); the launch baseline is this scripted system plus a simple difficulty knob (A-156)."

Distinctiveness row 5 (`docs/legacy/mvp/distinctiveness.md:23`): "The tragedy of understanding: mastery is knowing why you lost." Hypothesis H4: after a loss, at least 60 percent of testers name a positional or force cause; no more than 20 percent call the game unfair.

## 3. Westley's own words

Q-125-01 answer, 2026-09-16 (`ambiguity_register.md:116`): "Deferred. The old bible design for enemy AI macro behaviors will be referenced when this is specified; defer S-125 / difficulty tuning card for now."

A-149, Stage 1 (`stage1_audit.md:250`): "Westley: a trained neural network for macro opponent behavior stays on the table long-term — if the game gets testers, capture their play as training data. For now (interim, pre-data), the target is unscheduled and the current procedural JSON state-machine (built, `bible_combat.md`) ships as-is, tuned via simple knobs (e.g. unit counts) for difficulty rather than any learned model."

A-150 (`:251`): "Westley: "perfectly true, a great example of what I want from that system." Scope (target) confirmed as written — macro decisions only (when to attack, where to commit, tempo/positional reaction); explicitly not unit-level micro."

A-136 (`:237`): "knowledge is important to the game, same spirit as SC2. The game should create situations where a player's specific choices change how the opponent should respond, and should explicitly reward scouting and reasoning about the information the player has actually seen (not just theoretical uncertainty)."

Vision v2 Q6 (`docs/northstar/vision_v2.md:65`): "the goal is to construct a situation with enough variables that creates a really high skill ceiling".

Q-120-01, 2026-09-16 (`ambiguity_register.md:112`): "(b), AI postures deferred; enemy macro scripts use baseline movement/targeting speeds." Q-124-01 (`:115`): reinforcement waves ship, p = 0.07, foreshadowed.

## 4. Fixed constraints any option must honor

- R-125-01: at launch only force parity (E-10 R-074-03) changes with difficulty. R-125-02: at any difficulty the enemy's decision loop, stats, and abilities are identical to the player's. R-125-03: playtester command streams and outcomes are captured, data only (`E-14:96-98`).
- The macro layer never reads the player's visible set, never issues a command a player could not, never changes a unit's stat (R-123-03); enemy commands replay like a player's, evaluated every 2 seconds, four commands only (R-120-04).
- Difficulty never gives the enemy better units (E-10 R-080-01; A-454). The old bible scaled only the player's parity: "Difficulty never changes the enemy's strength — only the player's allocation." (`docs/bible_history/bible_2_00_combat.md:109`)
- Parity band: easy at least 0.95, hard at most 0.85, never below 0.75.
- AI postures (cautious, aggressive) deferred; scripts use baseline speeds (Q-120-01). Two script conditions dropped (Q-121-01).
- Principle 6: accessibility comes from parity tuning, opponent behavior at low difficulty, and opt-in labeled toggles, never from flattening space (`docs/bible/game_bible.md:78`).
- The learned model stays aspirational and unscheduled (A-149); no runtime API calls during play.
- Antagonists differ by config weights only, "the same engine, different knobs" (`docs/bible_history/bible_2_00_antagonist.md:13`).
- Difficulty can be changed later, not permanent (A-058).
- Determinism: same seed, same enemy commands.

## 5. Prior art already named

ARMA's macro-tempo AI; Tron Bike Wars community high-skill play as an existence proof that simple rules plus intelligent opposition sustain a skill ceiling (`docs/bible_history/bible_2_00_design_vision.md:97`). StarCraft 2 scouting and knowledge asymmetry (A-136). Helldivers 2's "Joel" adjusting to player behavior, tagged ambiguous (`docs/legacy/games/helldivers_2.md:32`). Darkest Dungeon's Radiant and Stygian modes (`docs/legacy/games/darkest_dungeon.md:32`). Difficulty-readability complaints in Battle Brothers reviews (`docs/legacy/topics/audience_psychographics_2026.md:152`).

## 6. Contradictions, as questions for Westley

1. The old bible scaled only the player's parity; "unit counts" for the enemy (A-149, A-156) is a new idea. Is the knob on the player side, the enemy side, or both?
2. Q-125-01 is marked closed as "Deferred" while the E-14 gate lists it open. For this pass, design the knob for the version that ships once S-125 is scheduled?
3. May a knob change how the enemy behaves (which script modifiers it draws, how often it probes, how it reacts to scouting) as long as its units are identical, or only how much it has?
4. What must never happen at any difficulty besides better enemy units: cheating vision, reading the player's orders, faster reactions than a human could manage?

## 7. Proposed option width

Three options, one wild. Each option describes what the player chooses, what they notice changes from easy to hard in the first ten minutes, and how a loss on hard still reads as their own limit.

## 8. Westley confirms

Batch 3, 2026-09-22, verbatim: "within reason, we don't want to have to design a whole LLM to play the game. For now we can use the Starcraft 2 model, we'll need to find out how they had those AI make decisions and play the game. 2: yes 3: not yet 4: cheating vision"

Folded into the brief:

- Reference model: StarCraft 2's built-in AI. The sub-agent researches how those opponents decide and play at each difficulty level and uses that as the primary prior art. No learned model, no LLM; "within reason".
- Question 2: design the knob for the version that ships when S-125 is scheduled.
- Question 3: the knob does not change enemy behavior yet; it changes how much the enemy has.
- Question 4: cheating vision must never happen at any difficulty.
- Question 1 (player side, enemy side, or both): answered by the StarCraft 2 reference and "how much the enemy has"; options may place the knob on either side or both and say so.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 3, of which 1 wild.
- Primary prior art: StarCraft 2's built-in AI difficulty levels. Research how those opponents decide and play at each level, with citations; no learned model, no LLM.
- The knob changes how much the enemy has, not how it behaves, for now. Cheating vision never happens at any difficulty.
- Each option says what the player chooses, what changes in the first ten minutes from easy to hard, and how a loss on hard still reads as the player's own limit.

## 10. Decision (2026-09-23)

Westley, verbatim: "For enemy macro, I don't like either of those. I think that there are two places that we need to scale the AI's ability: economic prosperity (more resources), and multi-layer intelligence. I had an idea that I want you to record as a desired piece of the layer system: players can invest (though costly) in units that give them better vision, a unit like the units in Starcraft that were invisible, but could see. The intelligent player gets one but has a slightly smaller army, but wins the fight because they knew where the opponents army was and created an intelligent surround with units on specific layers organized so that the opponent couldn't see it until it was too late. This is something the AI's should strive for when they're on hard mode, positional awareness and awareness of what combination of units would need to be on what layers in order to trump the other player's units given what layers those units are on."

Recorded as: Neither. Difficulty scales the enemy's economic prosperity and its multi-layer intelligence; a costly seer unit is a desired piece of the layer system (Q-125-02, Q-125-03, Q-E12-01).
