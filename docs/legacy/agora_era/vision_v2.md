# Vision v2 — Stage 1 Interview

Status: CONFIRMED by Westley, 2026-09-10. This file is the check every later Stage 1 verdict is measured against.

## One-page statement (confirmed)

Ouroboros Manifold is a multiplayer strategic RTS. The player commands a task force — never a whole civilization — inside a galaxy that runs its own simulation with its own plans. Missions are won or lost on positional skill: a smaller force that understands surrounds, high ground, and the 2.5D layer/vision system beats a larger force that doesn't. That is the skill ceiling, turned up past StarCraft 2's bar, which is the closest comp for feel and unit interaction (alongside Age of Empires 3 and Halo Wars). Art of Rally sets the visual target; Halo CE sets the storytelling/world-building bar; music is AI-generated in the Combat Evolved spirit.

Every mission's outcome feeds two things at once: the galaxy simulation (persistent, mechanical) and a bloodline/family story (cosmetic — legacy and legend only, never mechanical). Time jumps of roughly 20-100 years, derived from simulation state rather than fixed, carry a family's story and the galaxy's simulated state forward together between generational chapters.

The game ships across multiple eras as expansion content — $10-15 base on Steam, $3 per era expansion, expansions earnable through play as well as purchase, some exclusive. Matched players who all own the same era packs can play a match that traverses eras chronologically. This demands one shared architecture across eras — maps, era systems, civilizations built as transferable, reusable systems (Fortnite-skin-style cross-compatibility), not bespoke per-era builds — and the bible does not yet define how that differentiation actually works on one skeleton; that is open Stage 2 work, not yet solved.

Combat is full real-time, no pause — SC2/chess-without-turns continuous, multiplayer-consistent. Classic RTS control is reaffirmed. The Lieutenant system, any turn-based direction, and the bible's current "pause-and-command"/deliberate-pace framing (`game_bible.md:71,75,88,229`) are all killed — products of a since-reversed crisis pivot chasing commercial safety over the strategic RTS Westley actually wants to build. Bible content and commits from after that pivot are suspect by default and need individual verdicts during the item walk.

Smallest proud-to-ship version: 3 eras, past/present/future.

---

## Q1

**Question asked:** In one sentence, what is this game? Say it as you would to a friend who has never heard of it.

**Literal answer:** "It's a multiplayer strategic RTS based in an environment where the user plays out the story of various 'bloodlines' or 'families' through the galaxy, and the actions they take in any given mission effects both the simulation of the whole galaxy, AND the story associated with their character (and thus their perception over time). The game has a complex 2.5D layer system with generative maps that induce difficult tactical situations, including dynamic objectives, or situations induced by events elsewhere in the galaxy. The game is based off of Starcraft 2, Age of Empires 3, Art of Rally (for visuals), and Isaac Asimov's 'Foundation' books (while avoiding copyright terms). The game has many different 'eras' available, so that players can play in many different time periods over time available as expansion packs, and if all the users in the match have the same multiple packs their 'match' can actually traverse through time chronologically."

**Interpretation:** Multiplayer strategic RTS. Bloodline/family story layer runs parallel to galaxy simulation — mission outcomes affect both. 2.5D layer system + generative maps drive tactical difficulty, with dynamic objectives and cross-galaxy event effects. Influences: SC2, AoE3, Art of Rally (visuals), Foundation (theme only, no IP). Multi-era expansion pack model; matched players with the same packs can traverse eras chronologically within one match.

## Q2

**Question asked:** Near the end of the last work period you had a crisis about what the game should be. What changed in your head? What did you stop believing, and what did you start believing?

**Literal answer:** "I started to change away from RTS because I wanted to make something successful. At this point I just want to make something I enjoy myself, and that's a highly strategic RTS game. Anything that went away from RTS was the crisis."

**Interpretation:** The crisis was chasing commercial safety away from RTS. Correction: build what he enjoys — a highly strategic RTS — and treat any past drift away from RTS as the mistake to undo.

## Q3

**Question asked:** Is the player still a commander, not a king? Still one person with a task force, inside a civilization with its own plans?

**Literal answer:** "Yes commander not king, given a task force big or small, civ has it's own plans, meant to emulate reality. Bloodline framing is 'cosmetic' in that the bloodline is only 'story' oriented, the bloodline does not effect the simulation or civilization, just the story/legacy/legend associated with the character."

**Interpretation:** Commander-not-king framing holds. Bloodline/family layer is purely narrative/legacy — zero mechanical effect on simulation or civilization state.

## Q4

**Question asked:** Is the tactical layer still pause-and-command, or did the crisis move it toward something else (Lieutenant system, more RTS, more turn-based)?

**Literal answer:** "Crisis moved it toward pause-and-command, not the other way around. Lieutenant system was part of the crisis, and it's being thrown out the window at least for now. Classic RTS style is what we're going for, the expansion on it is the 2.5D layer and vision mechanics associated with it that give it a high skill ceiling."

**Interpretation:** Classic RTS pacing reaffirmed — Lieutenant system was a crisis-era detour, killed for now. The layer/vision system is the sanctioned expansion beyond classic RTS control.

**Correction (post-interview):** initial interpretation wrongly carried over the brief question's own "pause-and-command" phrase, which is the bible's *current* term (`game_bible.md:71,75,88,229`) for a deliberate-pace, pause-to-read-field, not-RTS-in-the-marketing-sense design — the opposite of what Westley means. Asked directly: tactical combat is full real-time, no pause, SC2/chess-without-turns continuous. This also fits the multiplayer requirement from Q1 (a stop-the-world pause doesn't work with other live players). The bible's current "pause-and-command" framing is now a confirmed kill/rewrite target, not a keep — goes into the item walk as a flagged row against `game_bible.md:71,75,88,229`, not a fresh ambiguity.

## Q5

**Question asked:** Are generational chapters with time jumps between them still the spine of the game?

**Literal answer:** "This is laid out in the bible, the time jump is calculated based on the simulation state, based on variables that is convenient at that time. Whether it's getting to the end of a run for an 'ancestor' and the 'family' needs to change (and whether the 'current' time contains such a family), The time jumps are anywhere between 20 - 100 years if I remember correctly, there's a range. Regardless of the literal jump, the story should and simulation still be noticeably effected by the outcome of the prior mission."

**Interpretation:** Yes, still the spine. Jump length is derived from simulation state (e.g. end of an ancestor's run, family continuity), not fixed — range roughly 20-100 years per Westley's recollection, needs bible verification. Prior mission outcome must visibly affect both story and simulation regardless of jump length.

## Q6

**Question asked:** Is the 2.5D layer system still the strategic defining characteristic? What is the one-sentence promise it must keep for the player?

**Literal answer:** "A player with an inferior force but understanding of positional tactics (surround, high ground, game theory positioning) can overcome the opposition, the goal is to construct a situation with enough variables that creates a really high skill ceiling, and significantly favors players with an understanding of the layer system, specific units, and such. (we're really heavily basing based off of Starcraft 2 here, surrounds and high ground were really important in that game, we're trying to turn it up to 11 in our game)."

**Interpretation:** Yes, still the defining characteristic. Promise: skill and positional understanding (surround, high ground, layer knowledge) beats raw force. SC2's surround/high-ground dynamics, intensified.

## Q7

**Question asked:** One era (the Settled Reach) or a multi-era catalog? Does era-agnostic architecture still matter?

**Literal answer:** "Yes, we cannot build a different 'game' for every era, that task would be massive. However, I don't believe that the bible fully fleshed out how exactly we're going to accomplish the level of 'difference' across eras while still using the same 'skeleton' if you will. This will likely be an area that we need too investigate/hash out further in stage 2."

**Interpretation:** Multi-era catalog confirmed, era-agnostic architecture is a hard constraint (not optional/later). Open problem: bible does not yet define the mechanism for making eras feel meaningfully different on one shared skeleton — flagged as a Stage 2 investigation item, not resolved here.

## Q8

**Question asked:** What games should this feel like, and in what specific way? What games should it not feel like?

**Literal answer:** "Stacraft 2, Age of Empires 3, Halo Wars, for their RTS large scale style battles and the way you interact with the units. Art of Rally look. Halo CE level storyline/storytelling/world building. We'll use an AI music generator for music just like Combat Evolved. Fortnite for it's skin cross-compatability. Any skin, any dance, any map, it's all transferrable. The maps generation system, the era system, the specific civilizations, all need to be 'transferrable' between eras like fortnite skins, that's where the idea came from. Like we're building 'systems' instead of individual components, systems that can be used for many use-cases down the road (OOP). I recorded a youtube video that described this idae to the bible, the guy built a great game and did it 'intelligently' by building re-useable efficient systems."

**Interpretation:** RTS feel/unit interaction from SC2, AoE3, Halo Wars. Visual style from Art of Rally. Storytelling/world-building bar set by Halo CE. Music: AI-generated, Halo CE precedent. Architecture philosophy borrowed from Fortnite's skin/cosmetic cross-compatibility — map generation, era system, and civilizations should all be built as transferable "systems," not one-off content, i.e. reusable engine components (OOP-style) rather than bespoke per-era builds. This directly informs the Q7 open problem (era-agnostic skeleton) — same underlying principle, not yet operationalized in the bible.

## Q9

**Question asked:** What is the price band and the platform?

**Literal answer:** "$10-15 on steam, $3 per expansion, expansions are grindable, some are exclusive but not all."

**Interpretation:** Base game $10-15, Steam. Expansions $3 each, earnable via grind (not purely paid-only). Some expansions are premium-exclusive, others grindable — mixed model, not uniform.

## Q10

**Question asked:** What is the smallest version of this game you would be proud to ship?

**Literal answer:** "3 eras, past/present/future."

**Interpretation:** MVP scope is 3 eras spanning past/present/future, not just the single Settled Reach era.

## Q11

**Question asked:** What parts of the current bible do you already know you want gone, before we walk it line by line?

**Literal answer:** "I know I want the leutenant system gone, and the turn-based idea. A lot of the stuff from the commits after the 'pivot' (crisis) is a different direction than that one I want to go."

**Interpretation:** Lieutenant system: kill. Turn-based direction: kill. Broadly: anything introduced in the post-pivot/crisis commits is suspect and likely points away from the reasserted RTS direction — needs identifying during the item walk (git log around the pivot date is the way to locate the boundary).

## Q12

**Question asked:** What parts do you already know are sacred?

**Literal answer:** "Basically everything from Q1 is sacred, I'm 90% sure nothing there conflicts with anything from Q11."

**Interpretation:** The Q1 one-sentence description (multiplayer RTS, bloodline/family story layer, galaxy simulation, 2.5D layer system, generative maps, dynamic objectives, multi-era expansion model with chronological match traversal) is sacred. Westley flags ~90% confidence of no conflict with the Q11 kill list (Lieutenant system, turn-based) — worth a light check during cross-check, not re-litigating.

---

## Cross-check flags (recorded live, not resolved)

1. Q1/Q7 answers (multiplayer, multi-era chronological match traversal as core, not research-only) diverge sharply from:
   - Code-reality baseline: multiplayer marked **absent**, not built.
   - `docs/legacy/method_era1/priority_queue.md` "Research-only / not committed" section: multi-era DLC ladder, branch system, etc. currently parked as research, not committed.
   - Bible/CLAUDE.md single-player "commander" framing assumptions in places.
   Not resolved here — goes to Step 3 cross-check list for Westley to rule on scope/sequencing (e.g. is multiplayer core-vision-but-later-stage, or core-and-blocking).

2. Q7/Q8: bible does not currently define the mechanism for era-to-era differentiation on a shared architecture ("systems, not components"). This is a real gap, not just a phrasing issue — flag for Stage 2 epic work, likely its own epic or a cross-cutting architecture principle.

3. Q9 resolves the known stale price claim from the Stage 1 brief: `game_bible.md`'s $10-15 figure is CONFIRMED current vision. Research briefs arguing $25-35 are superseded by this answer, not the other way around. Also new: $3/expansion, mixed grindable/exclusive model — not in the bible at all yet, needs to land in Stage 2.

4. Q10 (MVP = 3 eras, past/present/future) conflicts with `docs/legacy/method_era1/priority_queue.md`'s framing of multi-era as "research-only / not committed" and with the single-era "Settled Reach" framing elsewhere in the bible. Same underlying tension as flag 1 — multi-era is core vision, not a stretch goal.

## Remaining questions (9-12)

Not yet asked/answered.
