# E-20 — Multi-Era Skeleton, Era Packs, and Monetization

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Partly. 7 stories, 28 rules; the architecture and pricing rules are concrete, the era-transition and unlock rules carry flags. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 7 new flags, Q-145-01 through Q-150-01. |
| Every visible-surface story has a reference | Not applicable in this epic; era looks are E-18. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** vision_v2 Q7 named the era-differentiation mechanism on one skeleton as open Stage 2 work; this epic frames it and raises the flags but cannot close it without Westley. Stage 1 A-321 fixes one side: no mechanical or feel differentiation between eras at launch.

## Purpose

The engine is a skeleton that never names an era. Eras are packs: names, art, prose, unit models by tier, structure and environment assets, naming pools, chronicle and briefing fragments, and per-era config values the engine consumes uniformly. Maps, era systems, and civilizations are built as transferable systems, Fortnite-skin style, so any map, any skin, any civilization works in any era. The base game ships three eras (past, present, future) for $10 to $15 on Steam; further eras are $3 packs, some earnable through play and some exclusive. Era unlocks are the one progression unlock at launch. A campaign can move chronologically through eras the player owns.

At launch every era plays the same: same fog, same tempo, same reinforcement. Differentiation of feel is pinned for later, to be revisited only if built eras feel too alike.

## Obviously working in 60 seconds

Load the Settled Reach: a mission generates, forces spawn as sci-fi ships at Tier 2. Switch the era pack to the past era: the same seed produces the same map seed, the same unit roster with the same stats, the same objectives, drawn as that era's models, named from that era's pools, briefed in that era's prose. Grep the engine for any era name: zero hits.

## Stories

### S-145 — The engine never says "starship"
As an era designer, I want the engine to speak only in abstract terms, so that a new era is content and never code.

Rules
- R-145-01  Given the engine's source and config, When searched, Then no identifier names an era, setting, or theme (region not star system, heavy combat unit not battleship, military strength not fleet power).
- R-145-02  Given per-era variation, When implemented, Then it is a config value the engine reads uniformly; no `if era ==` branch exists anywhere.
- R-145-03  Given the bible, When engine sections are read, Then theme terms appear only in Vision and Identity and in era pack descriptions.
- R-145-04  Given a new era pack, When installed, Then the game runs it with zero engine changes; a contract test loads every shipped pack against the same engine build.

Inputs: source; packs.
Outputs: grep and contract test results.
Open flags: none.

### S-146 — What an era pack is
As an era designer, I want a checklist of exactly what a pack contains, so that every era is complete and nothing else.

Rules
- R-146-01  Given an era pack, When validated, Then it contains: identity (name, spatial scale, tone), three tier definitions, one unit model per roster type per tier and per-type silhouette conformance (E-18 S-132), 3 to 6 tiered structures, 5 to 10 environment objects, the ability visual mappings for every ability in the roster, attack visual categories per type, era-specific naming pools, era-specific chronicle and briefing fragments, a strategic view definition, and the per-era config values (unit stat profile per tier, restriction mask or none, elevation flag, reinforcement constants, fog constants).
- R-146-02  Given the launch constraint (A-321), When per-era config values are set for the three launch eras, Then they are identical across eras except art, names, and prose [Q-146-01].
- R-146-03  Given a pack, When any required entry is missing, Then the pack fails to load with the entry named; a missing optional asset uses the placeholder.
- R-146-04  Given the Era Creation Template (six layers), When a new era is designed, Then it follows those layers in order and stays within the fixed engine abstractions (three categories on a fixed rock-paper-scissors, a 20 to 40 type roster per era [Q-082-05], spine plus five gradients, abstract structure types, three tiers at 0/34/67).

Inputs: pack manifest.
Outputs: validation report; loaded pack.
Open flags: Q-146-01 (whether "identical" means byte-identical stat profiles, or only identical tempo targets; A-321 says no mechanical differentiation).

### S-147 — Three eras, one skeleton
As a player, I want a past, a present, and a future to play, all one game, so that the smallest version I buy is already history-spanning.

Rules
- R-147-01  Given the launch build, When eras are listed, Then it contains exactly three: [Q-147-01: the Settled Reach is the future; past and present are unnamed], chronologically ordered.
- R-147-02  Given any era, When a mission runs, Then the map generator, mission generator, agents, events, combat, and chronicle are the same code with the era's pack loaded.
- R-147-03  Given the same seed in two eras, When maps are generated, Then the map seeds are identical and only the rendering differs [Q-147-02: whether eras share map seeds or eras may weight layouts differently].

Inputs: pack set.
Outputs: era list; contract tests.
Open flags: Q-147-01, Q-147-02.

### S-148 — Moving through eras
As a player, I want a campaign to move chronologically through the eras I own, so that a bloodline can span the ages.

Rules
- R-148-01  Given a campaign in era k and the player owns era k + 1, When [Q-148-01: the trigger], Then the next time jump lands in era k + 1 with the same galaxy, the same factions, and the same ledger.
- R-148-02  Given the era transition, When the world carries over, Then region fields, ownership, edges, and characters persist and tech is rescaled so that no faction arrives at late game and the leading faction still leads; only the pack changes; the chronicle frames the transition, and characters from earlier eras fade into distant myths with fewer mentions the farther the timeline moves from them.
- R-148-03  Given the last owned era, When the next time jump comes, Then history loops: the jump lands in the first owned era with the same galaxy, the same factions, and the same ledger, in solo campaigns and in matches alike [Q-148-04: what the loop does to tech, characters, and the chronicle, and how it relates to the deferred Ouroboros restart, S-054].
- R-148-04  Given a multiplayer match, When eras traverse, Then E-19 S-143 applies.

Inputs: ownership; campaign state.
Outputs: era in the save; chronicle entry.
Open flags: Q-148-01 (what triggers an era transition: elapsed years, tech, chapter count, or a choice), Q-148-04 (the loop's effect on tech, characters, and the chronicle). Q-148-02 is closed: tech rescales at the boundary, nobody arrives at late game, the leading civilization still leads.

### S-149 — Buying and earning eras
As a player, I want a fair price and the chance to earn expansions by playing, so that the game respects my time and my wallet.

Rules
- R-149-01  Given Steam, When the base game is listed, Then it is one SKU at $10 to $15 containing three eras; no subscription, no in-game store, no Workshop at launch.
- R-149-02  Given an additional era, When listed, Then it is $3.
- R-149-03  Given an earnable era, When its condition is met in play, Then it unlocks without purchase [Q-149-01: the condition, proposed: complete a campaign of 10 chapters in the preceding era].
- R-149-04  Given an exclusive era, When read, Then it is purchase-only and marked so on the store page; the launch plan names which eras are which [Q-149-02].
- R-149-05  Given the unlock system, When read, Then era unlocks are the only unlock type at launch; no player level, no unit unlocks (E-08 R-064-03).

Inputs: store; play state.
Outputs: ownership; store listing.
Open flags: Q-149-01, Q-149-02.

### S-150 — Systems, not components
As an era designer, I want maps, civilizations, and era systems to transfer between eras like skins, so that content compounds instead of forking.

Rules
- R-150-01  Given a layout in the library, When used, Then it is valid in every era with no era tag.
- R-150-02  Given a civilization (archetype weights, naming subset, colors), When used, Then it is valid in every era.
- R-150-03  Given a skin (unit model set), When applied, Then it maps to the six abstract types and three tiers and nothing else.
- R-150-04  Given the roadmap for additional era-agnostic systems (procedural architecture kit, A-157), When designed, Then the section generator is era-agnostic and the pieces are era-specific.

Inputs: content libraries.
Outputs: cross-era validity tests.
Open flags: Q-150-01 (what "civilization" content transfers across eras beyond archetypes and names; the Fortnite analogy names skins, dances, maps, and Westley extends it to civilizations).

### S-151 — Later: eras that feel different
As a player, I may someday want the ancient era to be scout-blind and the future era all-seeing, so that time changes how war feels.

Rules
- R-151-01  Deferred (A-321, A-339, A-344, A-362, A-544 through A-546). No rule at launch. Recorded so the branch-system idea is not lost: per-era fog, tempo, HP scale, and reinforcement constants would become manifest values consumed uniformly.

Inputs: none yet.
Outputs: none yet.
Open flags: none; deferred by Westley's Stage 1 decision, reopen only if built eras feel too similar.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Era pack manifest | Content | as S-146 | missing required entry fails load |
| Ownership | Steam | set of era ids | |
| Campaign era state | Save | era id, order | unknown era refuses load |

## Outputs

| Output | Observable where |
|---|---|
| Loaded pack, validation report | Log; contract tests |
| Era in campaign state | Save; briefing; chronicle |
| Store listing and unlocks | Steam; profile |

## Invariants

- Zero era names in engine source.
- Every pack passes the same contract test.
- The three launch eras share identical mechanical config (A-321) [Q-082-05: whether per-era rosters keep unit profiles identical across the launch packs].

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): pack load under 2 s; era switch in a campaign under 5 s.

## Look and behavior references

Not applicable; see E-18 per era.

## Ways this could be wrong

- An era-specific constant slips into the engine as a default.
- A pack ships with a mechanical difference and passes because the contract test does not diff config across packs.
- Era transition resets the ledger or the world.
- Earnable eras gated behind a purchase in the store metadata.

## Open ambiguity flags

Q-146-01, Q-147-01, Q-147-02, Q-148-01, Q-148-02, Q-149-01, Q-149-02, Q-150-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-08 (time jumps, unlocks), E-11 (per-tier profiles), E-17 (layouts), E-18 (looks), E-19 (cross-era matches), E-21 (pack content generation).
