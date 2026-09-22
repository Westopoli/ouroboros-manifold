# Era feel differentiation: perception brief

## 1. Feature and status

E-20 S-151 "Later: eras that feel different" (`docs/bible/epics/E-20-multi-era-and-monetization.md:106-114`). Deferred by Stage 1 A-321 and its cluster (A-339, A-344, A-362, A-544 to A-546); no rule at launch. Q-146-01 closed: byte-identical mechanical config across the three launch packs (`docs/northstar/ambiguity_register.md:135`). Vision v2 Q7 named the mechanism as open Stage 2 work. Historical design material exists in `docs/design_questions/era_mechanical_axes.md` (eight-axis matrix, written under the scrapped subscription model).

## 2. Player-facing goal as documented

"As a player, I may someday want the ancient era to be scout-blind and the future era all-seeing, so that time changes how war feels." (`E-20:107`)

"At launch every era plays the same: same fog, same tempo, same reinforcement. Differentiation of feel is pinned for later, to be revisited only if built eras feel too alike." (`E-20:20`) R-151-01: "per-era fog, tempo, HP scale, and reinforcement constants would become manifest values consumed uniformly." (`:110`)

## 3. Westley's own words

Vision v2 Q7, 2026-09-10 (`docs/northstar/vision_v2.md:73`): "Yes, we cannot build a different 'game' for every era, that task would be massive. However, I don't believe that the bible fully fleshed out how exactly we're going to accomplish the level of 'difference' across eras while still using the same 'skeleton' if you will. This will likely be an area that we need too investigate/hash out further in stage 2."

D9, 2026-09-19 (`docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md:109`): "D9: Q146: exact idential for MVP, different as we get farther into the game."

A-321, Stage 1 (`docs/northstar/stage1_audit.md:500`): "Per-branch fog/sensor differentiation (sci-fi near-total awareness, modern partial asymmetry, ancient heavy fog/scout-dependent, Roman shallow-ancient). Deferred, pinned as an idea for later: no mechanical/feel differentiation between eras at initial launch. Applies across the whole era system, not just fog/sensor — the broader "each era has its own feel" plan is pinned for now, to revisit only if eras end up feeling too similar to each other once built."

Q-099-01, 2026-09-14 (`ambiguity_register.md:97`), on terrain slowing units: "slows when it's ships; I don't care about it slowing in eras where it's units on the ground." (Built era-uniform to satisfy A-321.)

Q-E01-01 (`:9`): "There should always be 5 layers, regardless of era."

Landscape answer 1, 2026-09-21 (`docs/northstar/research/landscape_design/README.md:11`): "everything we're building should be era-agnostic to prove they can be used cross-era."

## 4. Fixed constraints any option must honor

- A-321: no mechanical or feel differentiation at launch; the three launch packs are byte-identical in mechanical config (Q-146-01). Options describe the post-MVP game.
- Sacred principle 3: any per-era variation is config the engine consumes uniformly; no engine branch on era (`docs/bible/game_bible.md:75`; R-145-02). The production filter in `docs/design_questions/era_mechanical_axes.md:37-49`: dials must be cheap config, a player must be able to describe the difference without numbers, 5 to 7 axes at most, teachable once.
- Fixed abstractions: 6 unit types with fixed silhouettes across every era (A-413), fixed rock-paper-scissors, three tiers, five layers always, spine plus five gradients (R-146-04).
- Any map, civilization, or skin works in any era (R-150).
- Tempo targets at launch are the same in every era (E-11 S-085); per-era tempo is deferred (A-339, A-344).
- No IP.

## 5. Prior art already named

StarCraft 2, Age of Empires 3, Halo Wars for the baseline RTS feel (vision Q8). The eight-axis matrix in `docs/design_questions/era_mechanical_axes.md:550-635` (tempo, information war, attrition, layer access, force scale, terrain expressiveness, environmental threat, cross-layer engagement) with Roman, 1980s, and Settled Reach columns; its "Sacred Principle #3" production filter is still valid, its access-tier annotations are not. Old bible branch system (`docs/bible_history/bible_2_00_combat.md:574`). Age of Empires 3 massed formations and The Expanse register in `docs/design_questions/era_selection_design.md:87,108-109` (historical).

## 6. Contradictions, as questions for Westley

1. A-321 reads as "revisit only if built eras feel too similar"; D9 reads "different as we get farther into the game". Is later differentiation intended regardless, or conditional on eras feeling alike?
2. `era_mechanical_axes.md` is marked open and claims the launch eras are "mechanically distinct on every axis" (`:616`), which A-321 overrides. Is that document history, or a live input the options should build on?
3. What may differ: only feel through numbers (fog range, tempo, reinforcement rate), or also which layers a unit type can use (restriction masks, "submarines on layers 1 and 2"), or also what a mission is (archetype weights per era)?
4. Should a player who has learned one era be able to read another at a glance (fixed silhouettes say yes), or is confusion at an era boundary part of the point?

## 7. Proposed option width

Three options, one wild. Each option describes what a player notices in the first minute of a mission in a new era, what they have to relearn, and what stays exactly the same.

## 8. Westley confirms

(empty until batch 2)
