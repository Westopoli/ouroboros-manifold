# Era feel differentiation: perception brief

## 1. Feature and status

E-20 S-151 "Later: eras that feel different" (`docs/bible/epics/E-20-multi-era-and-monetization.md:106-114`). Deferred by Stage 1 A-321 and its cluster (A-339, A-344, A-362, A-544 to A-546); no rule at launch. Q-146-01 closed: byte-identical mechanical config across the three launch packs (`docs/northstar/ambiguity_register.md:135`). Vision v2 Q7 named the mechanism as open Stage 2 work. Historical design material exists in `docs/legacy/design_questions/era_mechanical_axes.md` (eight-axis matrix, written under the scrapped subscription model).

## 2. Player-facing goal as documented

"As a player, I may someday want the ancient era to be scout-blind and the future era all-seeing, so that time changes how war feels." (`E-20:107`)

"At launch every era plays the same: same fog, same tempo, same reinforcement. Differentiation of feel is pinned for later, to be revisited only if built eras feel too alike." (`E-20:20`) R-151-01: "per-era fog, tempo, HP scale, and reinforcement constants would become manifest values consumed uniformly." (`:110`)

## 3. Westley's own words

Vision v2 Q7, 2026-09-10 (`docs/northstar/vision_v2.md:73`): "Yes, we cannot build a different 'game' for every era, that task would be massive. However, I don't believe that the bible fully fleshed out how exactly we're going to accomplish the level of 'difference' across eras while still using the same 'skeleton' if you will. This will likely be an area that we need too investigate/hash out further in stage 2."

D9, 2026-09-19 (`docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md:109`): "D9: Q146: exact idential for MVP, different as we get farther into the game."

A-321, Stage 1 (`docs/legacy/agora_era/stage1_audit.md:500`): "Per-branch fog/sensor differentiation (sci-fi near-total awareness, modern partial asymmetry, ancient heavy fog/scout-dependent, Roman shallow-ancient). Deferred, pinned as an idea for later: no mechanical/feel differentiation between eras at initial launch. Applies across the whole era system, not just fog/sensor — the broader "each era has its own feel" plan is pinned for now, to revisit only if eras end up feeling too similar to each other once built."

Q-099-01, 2026-09-14 (`ambiguity_register.md:97`), on terrain slowing units: "slows when it's ships; I don't care about it slowing in eras where it's units on the ground." (Built era-uniform to satisfy A-321.)

Q-E01-01 (`:9`): "There should always be 5 layers, regardless of era."

Landscape answer 1, 2026-09-21 (`docs/northstar/research/landscape_design/README.md:11`): "everything we're building should be era-agnostic to prove they can be used cross-era."

## 4. Fixed constraints any option must honor

- A-321: no mechanical or feel differentiation at launch; the three launch packs are byte-identical in mechanical config (Q-146-01). Options describe the post-MVP game.
- Sacred principle 3: any per-era variation is config the engine consumes uniformly; no engine branch on era (`docs/bible/game_bible.md:75`; R-145-02). The production filter in `docs/legacy/design_questions/era_mechanical_axes.md:37-49`: dials must be cheap config, a player must be able to describe the difference without numbers, 5 to 7 axes at most, teachable once.
- Fixed abstractions: 6 unit types with fixed silhouettes across every era (A-413), fixed rock-paper-scissors, three tiers, five layers always, spine plus five gradients (R-146-04).
- Any map, civilization, or skin works in any era (R-150).
- Tempo targets at launch are the same in every era (E-11 S-085); per-era tempo is deferred (A-339, A-344).
- No IP.

## 5. Prior art already named

StarCraft 2, Age of Empires 3, Halo Wars for the baseline RTS feel (vision Q8). The eight-axis matrix in `docs/legacy/design_questions/era_mechanical_axes.md:550-635` (tempo, information war, attrition, layer access, force scale, terrain expressiveness, environmental threat, cross-layer engagement) with Roman, 1980s, and Settled Reach columns; its "Sacred Principle #3" production filter is still valid, its access-tier annotations are not. Old bible branch system (`docs/bible_history/bible_2_00_combat.md:574`). Age of Empires 3 massed formations and The Expanse register in `docs/legacy/design_questions/era_selection_design.md:87,108-109` (historical).

## 6. Contradictions, as questions for Westley

1. A-321 reads as "revisit only if built eras feel too similar"; D9 reads "different as we get farther into the game". Is later differentiation intended regardless, or conditional on eras feeling alike?
2. `era_mechanical_axes.md` is marked open and claims the launch eras are "mechanically distinct on every axis" (`:616`), which A-321 overrides. Is that document history, or a live input the options should build on?
3. What may differ: only feel through numbers (fog range, tempo, reinforcement rate), or also which layers a unit type can use (restriction masks, "submarines on layers 1 and 2"), or also what a mission is (archetype weights per era)?
4. Should a player who has learned one era be able to read another at a glance (fixed silhouettes say yes), or is confusion at an era boundary part of the point?

## 7. Proposed option width

Four options, two wild (raised from three and one in batch 2). Each option describes what a player notices in the first minute of a mission in a new era, what they have to relearn, and what stays exactly the same.

## 8. Westley confirms

Batch 2, 2026-09-22, verbatim: "I want to modify the bible on the "only 6 types" rule, given how we're building this, I want to make it like Age of Empires 3 or AOE Online where there are many many units, many options. We'll need to design a mechanism to make sure units are balanced (scoring system has been documented in old bible before), but the goal is 20-40 different units per-era, with eras swinging hard if there was a specific conflict we're focusing on for that era (like Romans vs Greeks, or WW2 Axis vs Allies). Find and make that ammendment into the bible, record the decision date and time. For your Qs for this one, I'm going to leave them open and see what I like from what the agents return (I haven't decided, so wider option variance means I can pull more wheat from the chaff)."

Folded into the brief:

- The six-unit-type rule is amended in the bible (decision 2026-09-22 14:27 EDT, register row Q-082-02): an era pack carries 20 to 40 unit types, in the register of Age of Empires 3 and Age of Empires Online; a balance scoring mechanism (the old bible's power rating, A-279) is to be designed; an era built around a specific conflict (Romans against Greeks, a world war's two alliances) may swing its roster hard toward that conflict. Section 4's "six unit types" constraint no longer holds; the fixed silhouette rule per type is under review (Q-132-02).
- A per-era roster of 20 to 40 units is itself a feel mechanism the options may use: eras differ by what fights in them, not only by fog and tempo.
- Questions 1 to 4: deliberately left open. Westley wants wide variance to pick from. Width raised to four options, two wild.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 4, of which 2 wild.
- Every question in section 6 is deliberately open; Westley wants wide variance. Go wide.
- A roster of 20 to 40 unit types per era (Q-082-02) is available as a feel lever: eras may differ by what fights in them.
- Every difference must be expressible as pack content or config the engine consumes uniformly; no engine branch on era.

## 10. Decision (2026-09-23)

Westley, verbatim: "For era feel, I like the climate of war, but I'm confused by "the long look", I don't understand how a loading screen insertion is supposed to account for the whole differentiation across eras, it seems like more of a side-note than a strategy for era differentiation. This is a good idea though, mark down as a decision that I'd like to make the loading screens interesting in some manner, sharing with the users information that usually would just be wallpaper art or a loading animation. What exactly we'll show, don't know yet, but pre-launch we'll come up with something like The Long Horizon (pairs well with the chronicle story, could be sourced from there)."

Recorded as: The Climate of War (Q-151-01). The Long Look is not an era-feel strategy; its idea became a decision that loading screens carry interesting information (E-16 R-110-04, Q-110-03).
