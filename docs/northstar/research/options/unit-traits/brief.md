# Unit passive traits: perception brief

## 1. Feature and status

E-11 S-083 "Stats, traits, ability" (`docs/bible/epics/E-11-units-and-combat.md:66-76`). Q-083-01 closed 2026-09-16: traits deferred to post-launch balance passes; launch units are base stats plus one active signature ability (`docs/northstar/ambiguity_register.md:86`). The rules R-083-01 and R-083-02 still describe traits. The AI-generated per-civilization variety that would have filled the trait pool is deferred as a cluster (A-278, A-279; E-21 S-157). MVP placement: Round 2 (`docs/legacy/mvp/feature_mvps.md:70`). This brief is about the post-launch version.

## 2. Player-facing goal as documented

"As a commander, I want each unit to be its stats plus one or two passive traits plus one ability, so that units within a category differ in kind and not only in number." (`E-11:67`)

E-11 purpose (`:18`): "Six unit types, two per category, on a soft rock-paper-scissors: Strike flanks Siege, Siege crushes Line, Line absorbs Strike. Every unit has stats, exactly one ability, and a role nobody else fills... Abilities are the mastery layer: ignorable by a new player, decisive in skilled hands, every one a commitment with a tradeoff."

Old bible definition (`docs/bible_history/bible_2_00_combat.md:28`): "Traits — passive characteristics. A unit might have "hardened hull" (extra resistance to Strike damage) or "long-range sensors" (sees further). One or two per unit type, AI-generated from a constrained trait pool."

## 3. Westley's own words

Q-083-01 answer, 2026-09-16 (`ambiguity_register.md:86`): "(a), defer passive traits to post-launch playtest balance passes. Launch units have their core base stats + 1 active signature ability only."

Q-084-01, 2026-09-12 (`:87`), on the one surviving passive, the Warden aura: "(c), Diminish. First Warden: 0.10 damage reduction. Second Warden: 0.05 reduction (diminishing returns). Healing stacks normally per Warden."

Q-082-01, 2026-09-12 (`:85`): "(b), author them now, 0.8 and 1.2 sound good. Tier 1 = 0.8× Tier 2 (HP and damage), Tier 3 = 1.2× Tier 2, all other ratios scale uniformly. Ship all three tiers at launch."

Q-006-01 (`:28`): "Give the interceptor the pulse, mark it as a 'for now' ability, we'll modify units a lot when we have playtesters."

A-278, Stage 1 (`docs/legacy/agora_era/stage1_audit.md:438`): "AI-Generated Unit Variety: engine owns fixed mechanics (6 types, abilities, roles); AI tunes numbers per civilization trait (militaristic → higher firepower, expansionist → faster/lighter, declining → degraded stats/improvised traits)... Deferred: not part of initial build... keep as a later epic to add per-civilization stat flavor once the base game is proven."

A-279 (`:444`): "Deferred: Westley conceived this without appreciating implementation complexity — pinned as an idea needing serious testing/tuning, not an implementation goal right now."

A-261 (`:421`): "unit stats/damage-multipliers/etc. are tuned by running headless C simulations... iterated rapidly until the system settles at the desired behavior (equilibrium). Tuning is a deliberate simulation-driven loop, not AI-generated-per-civilization stat variance."

## 4. Fixed constraints any option must honor

- Roster: on 2026-09-22 Westley amended the six-type rule; an era pack carries 20 to 40 unit types in the register of Age of Empires 3 and Age of Empires Online, balanced by a scoring mechanism still to be designed (register Q-082-02, open flags Q-082-03 to Q-082-05). Categories, one ability per unit, and per-type silhouettes are under review with those flags.
- Roster invariants: every Strike faster than every Line, every Line faster than every Siege; Bastion has at least twice the next HP; both Strike see farther than both Siege; only the Bombard has area damage (R-082-02 to 05, `E-11:56-59`).
- R-083-01: a profile has stats, zero to two traits, exactly one ability. R-083-02: a trait modifies one stat or one multiplier by a fixed amount stated in the profile (`E-11:70-71`).
- Warden aura: 10 percent damage reduction within 300 wu, diminishing with a second Warden (R-083-03; Q-084-01).
- Tier 1 is 0.8 and Tier 3 is 1.2 of Tier 2 (Q-082-01).
- Numbers are tuned by headless simulation, not by hand (A-261); stats live in engine config (A-343).
- No mechanical differentiation between eras at launch (A-321); an expansion adds a type by declaring category, role, stats, and one ability with no engine change (R-082-06).
- Both sides draw from the same profiles; nothing differs by difficulty (E-10 R-080-01).
- Per-civilization AI-generated variety is deferred as a cluster (A-278, A-279, E-21 S-157).
- Opt-in complexity (principle 4): a new player plays without reading traits.

## 5. Prior art already named

None trait-specific. StarCraft 2, Age of Empires 3, Halo Wars for unit interaction (vision Q8). E-18 visual register and E-13 grouping (one unit reads as a cluster of models under one bar) for how a unit reads.

## 6. Contradictions, as questions for Westley

1. The register's candidate (a) was worded "delete traits"; your answer says "defer to post-launch playtest balance passes". Deferred, not deleted? Should this pass design the post-launch version?
2. Old bible traits were per unit type and AI-generated per civilization (A-278). Post-launch, do traits belong to the unit type (every Raider everywhere), to the civilization (this civilization's Raiders), to the era pack, or to the individual unit in a mission?
3. "Differ in kind and not only in number": is a trait allowed to change a rule (ignores terrain slow, sees one layer further) or only a number (10 percent more HP)?
4. Should the player see traits on the HUD at all, or only feel them?

## 7. Proposed option width

Two options, one wild. Each option describes what a trait is to the player: where it comes from, where they read it, how it changes a fight they can recognize, and how many they must learn.

## 8. Westley confirms

Batch 3, 2026-09-22, verbatim: "1: yes design here 2: traits in addition to the increased unit number, think Dead-by-daylight level customizability, users will have  so many cards that each can be pretty individualized to their playstyle, if certain ones get abused we'll nerf them. 3: it can change a rule 4: depends on trait"

Folded into the brief:

- Question 1: deferred, not deleted; this pass designs the post-launch version.
- Question 2: traits exist on top of the 20 to 40 unit roster. The register is Dead by Daylight's perk customization: many cards, so each player's force can be individualized to their playstyle, with abused cards nerfed after launch. Whether a card attaches to a unit type, a unit, the commander, or the force loadout is not stated; options say where cards come from, who holds them, and whether the enemy fields them too, and must reconcile with "no persistent player level" (A-061) and "both sides draw the same profiles" (R-080-01), naming what they strain.
- Question 3: a trait may change a rule, not only a number.
- Question 4: whether a trait shows on the HUD depends on the trait.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 2, of which 1 wild.
- Design the post-launch version: perk-card customization in the Dead by Daylight register, on top of a 20 to 40 unit roster, individualized to a player's style, nerfed when abused.
- A trait may change a rule. HUD visibility depends on the trait.
- Each option says where cards come from, who holds them (unit type, unit, commander, force), whether the enemy fields them, and how it squares with no persistent player level (A-061) and both sides drawing the same profiles (R-080-01).

## 10. Decision (2026-09-23)

Westley, verbatim: "For passive traits, I'd kinda like them to be unlockable, like Dead by Daylight or Age of Empires 3. However, traits and abilities are never more powerful than a player's positioning ability, this is a core rule for the game: a player with "weak" abilities/traits that understands strategy and the layer system better will trump any player with "strong" abilities/traits that doesn't. Layer system damage is weighted much more heavily than abilities/passives, and we'll minimize traits/abilities that are unlockable that give players an "edge" in terms of vision across layers. This one is pretty decided (we'll make the cards cool so the players have a desire to unlock them), no need for a second pass on this decision."

Recorded as: Unlockable trait cards (Dead by Daylight, Age of Empires 3 register) under a core rule: cards and abilities never outrank positioning, layer damage weighs more, cross-layer-vision cards minimized. Decided, no second pass (Q-083-02, Q-083-03).
