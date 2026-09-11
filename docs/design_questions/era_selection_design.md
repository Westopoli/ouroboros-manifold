# Era Selection Design — Working Document

> **LEGACY MONETIZATION ASSUMPTIONS — 2026-05-09**
>
> This doc was written under the **subscription + per-era purchase** model
> ("Subscription-gated", "free tier", starter bundle, etc.). That model has
> been **scrapped** — Steam does not permit external payment links from in-game.
> Current model: **buy-once base game (starting civ of every branch) + paid Steam
> DLC for additional eras within each branch, no subscription, no free tier**.
> See `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` "Current Monetization Model" section.
> Branch-structure decisions in this document remain useful as design context;
> the access-tier columns (Free / Subscription-gated) are obsolete.

> **Transient working doc.** Captures design decisions from the era selection
> brainstorming session (April 22, 2026). Once all decisions are captured
> into `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/), this file is deleted.
>
> **Capture targets:** `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (component 1 rewrite, Branch
> System extension, open question 3 resolution, open question 13a resolution).
>
> **Source docs consulted:** `game_bible.md`, `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/),
> `design_rules.md`, `era_mechanical_axes.md`, `visual_identity_design.md`.

---

## Resolved Decisions

### 1. Hallmark placement within branch track — RESOLVED

**Decision:** Hallmark at position 3 (end of track).

Work Era 1 → Work Era 2 → Hallmark. Classic tech-tree payoff structure.
The hallmark is the aspirational apex the player works toward. Work eras
are not filler — they are mechanically distinct, strategically deep
experiences in their own right. The ramp is about expanding the branch's
hallmark-exclusive axes, not about quality escalation.

Aligns with the bible's governing principle: "aspiration plus access."
Reference model: WoWS Tier X / Fortnite battle pass final tier.

### 2. Work era mechanical graduation — RESOLVED

**Decision:** Graduated positions (Option B).

The two work eras per branch take *graduated* positions on the hallmark-
exclusive axes, stepping toward the hallmark's full expression:

- **Position 1 (entry era):** Most constrained on hallmark-exclusive axes.
  Subscription-gated access.
- **Position 2 (bridge era):** Partially open on hallmark-exclusive axes.
  Grindable to permanent ownership (15hr play).
- **Position 3 (hallmark):** Full expression of all hallmark-exclusive axes.
  Premium-purchased.

Each step adds mechanical freedom. The player's journey through a branch
is a deliberate escalation in the branch's unique identity.

### 3. Branch 1 work era selection — RESOLVED

**Branch 1 — Sci-fi / Future lineup (positions 1 → 2 → 3):**

1. **Planetary Colonization / Frontier World** (~2200–2400)
   - Surface warfare on colonized worlds and stations: Mars colonies,
     orbital stations, asteroid belt installations, Earth-orbit facilities.
   - **Hallmark-exclusive axis positions (most constrained):**
     - Layer access: single-layer ground/surface combat with terrain-elevation.
     - Environmental threat: rare.
     - Cross-layer engagement: ground-bound.
   - **Branch 1 DNA (inherited):** Fast tempo, near-total sensor awareness,
     rapid recovery, squad/taskforce scale (20–60 units).
   - Thematic identity: frontier scrappiness, high-tech but confined to
     surfaces. The accessible introduction to sci-fi combat.

2. **Interplanetary / Solar System Warfare** (~2400–2700)
   - Combat across the inner solar system — every planet. Earth-Moon-Mars-
     Belt-Jupiter-Saturn and beyond.
   - **Hallmark-exclusive axis positions (partially open):**
     - Layer access: partial traversal (atmosphere-capable ships vs.
       space-only ships; planetary gravity wells restrict some units).
     - Environmental threat: occasional (solar flares, asteroid debris
       fields, planetary storms).
     - Cross-layer engagement: asymmetric matrix (orbital bombardment
       platforms can hit surface but not vice versa without specialized
       anti-orbital units).
   - **Branch 1 DNA (inherited):** Fast tempo, near-total sensor awareness,
     rapid recovery, squad/taskforce scale (20–60 units).
   - Thematic identity: The Expanse-register interplanetary conflict.
     Stepping stone to SR's galaxy-spanning scope. Introduces layers
     through the natural space-vs-atmosphere divide.

3. **Settled Reach** (hallmark, ~3000+)
   - Multi-system, galaxy-spanning, post-scarcity civilization.
   - **Hallmark-exclusive axis positions (fully open):**
     - Layer access: free traversal (all unit types, all layers).
     - Environmental threat: common (capped at 1-in-2 missions).
     - Cross-layer engagement: fully reciprocal.
   - **Branch 1 DNA (inherited):** Fast tempo, near-total sensor awareness,
     rapid recovery, squad/taskforce scale (20–60 units).

**Scope ramp:** Stations/colonies → Solar system → Galaxy.
Each step opens up layers, engagement freedom, and environmental intensity.

### 4. Branch 2 work era selection — RESOLVED

**Branch 2 — Modern / Recent History lineup (positions 1 → 2 → 3):**

1. **Colonial / Independence Era** (~1750–1820)
   - Large-formation ground combat in the AoE3 register: line infantry,
     cavalry, artillery batteries, musket volleys, formation tactics.
     Colonial expansion, revolutionary wars, independence movements.
   - **Hallmark-exclusive axis positions (most constrained):**
     - Layer access: single-layer ground combat with terrain-elevation
       pseudo-layers (hills, fortifications, ridgelines).
     - Cross-layer engagement: ground-bound (no layer puzzle).
   - **Branch 2 DNA (inherited):** Medium tempo, partial sensor asymmetry
     (cavalry screens, scout pickets, high-ground observation), industrial
     replacement.
   - **Force scale:** Large — company-to-legion range (200–600 units).
     Deliberately above Branch 2's default company/battlegroup (100–300)
     to deliver the AoE3 massed-battle feel of ranked formations clashing.
     This is a per-era config override, not a Branch DNA violation — force
     scale is per-era tunable within a branch.
   - Environmental threat: rare.
   - Thematic identity: AoE3 homage. Large massed battles. Recognizable
     units and formations. The accessible introduction to modern military
     history.

2. **World War II** (~1939–1945)
   - Ground-dominant combined arms with partial layer access. Armor,
     infantry, artillery as the ground core. Paratroopers, amphibious
     landings, and close air support introduce partial layer crossing.
   - **Hallmark-exclusive axis positions (partially open):**
     - Layer access: partial layer lock (some units cross layers —
       paratroopers deploy air-to-ground, amphibious vehicles cross
       water-to-land, fighter-bombers strafe — but most units are
       layer-locked).
     - Cross-layer engagement: mostly reciprocal with asymmetric
       exceptions (air-to-ground is powerful, ground-to-air requires
       specialized AA; naval bombardment hits shore but shore batteries
       are specialized).
   - **Branch 2 DNA (inherited):** Medium tempo, partial sensor asymmetry
     (radio intercepts, reconnaissance, Ultra-style intelligence),
     industrial replacement (the era's defining economic reality).
   - Force scale: company/battlegroup (100–300 units, Branch 2 DNA).
   - Environmental threat: occasional (weather affecting operations,
     winter conditions, storms).
   - Thematic identity: The most commercially proven military setting in
     gaming. Huge asset vocabulary. Wide terrain spread (Europe, Pacific,
     North Africa, Eastern Front). Introduces layers through natural
     combined-arms vocabulary.

3. **The 1980s** (hallmark)
   - Full multi-domain Cold War warfare. Submarines, surface vessels,
     aircraft as fully independent combat domains.
   - **Hallmark-exclusive axis positions (fully open):**
     - Layer access: strict layer lock (subs are sub-only, surface is
       surface-only, aircraft are air-only — no crossing).
     - Cross-layer engagement: asymmetric matrix (specific layer pairs
       are mechanically impossible; specialized units handle cross-layer
       engagements — ASW helicopters, anti-air batteries, etc.).
   - **Branch 2 DNA (inherited):** Medium tempo, partial sensor asymmetry,
     industrial replacement.
   - Environmental threat: occasional.
   - Thematic identity: Cold War proxy warfare across global theaters.
     Wide terrain spread (naval, jungle, desert, urban, arctic).

**Chronological ramp:** 1750s → 1940s → 1980s.
Each step adds military complexity. The player walks through the evolution
of modern warfare — muskets to mechanized to multi-domain.

### 5. Land/sea combined warfare as hallmark-exclusive feature — RESOLVED

**Decision:** Hallmark eras (Settled Reach, 1980s) feature combined
land/sea warfare as a hallmark-exclusive mechanical differentiator.

- Sea units have their **own production structures** separate from land
  production structures.
- Sea and land units have **distinct models and movement styles** — they
  are visibly and mechanically different systems, not reskinned ground units.
- Work eras do NOT have combined land/sea warfare. Their combat occurs
  on a single domain (land or space) even if partial layer access exists
  for other reasons (paratroopers, orbital bombardment, etc.).
- This gives hallmark eras a visible, aspirational feature that work eras
  lack: two parallel military systems (land + sea) with their own
  production, their own unit roster, their own movement rules, interacting
  on the same battlefield.

**Implementation note:** This is a hallmark-exclusive feature expressed
through per-era config (which production structure types are available,
which unit movement models are active). The engine supports both land and
sea unit types universally; hallmark eras enable both, work eras enable
only one. Compatible with Sacred Principle #3.

---

## Full 7-Era Launch Catalog Summary

| # | Era | Branch | Position | Access Model |
|---|---|---|---|---|
| 1 | Roman | Standalone (free tier) | — | Free-to-play |
| 2 | Planetary Colonization | Branch 1 | 1 (entry) | Subscription-gated |
| 3 | Interplanetary | Branch 1 | 2 (bridge) | Grindable to permanent (15hr) |
| 4 | Settled Reach | Branch 1 | 3 (hallmark) | Premium-purchased |
| 5 | Colonial / Independence | Branch 2 | 1 (entry) | Subscription-gated |
| 6 | World War II | Branch 2 | 2 (bridge) | Grindable to permanent (15hr) |
| 7 | The 1980s | Branch 2 | 3 (hallmark) | Premium-purchased |

---

## Bible Capture Targets

The following edits need to be applied to `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/):

1. **Component 1 — Launch branch catalog section.** Update Branch 1 and
   Branch 2 descriptions to include specific work era names and positions.
   Mark work era selection as RESOLVED.

2. **Component 1 — Hallmark placement.** Add "Hallmark at position 3"
   as a resolved structural decision within the branching progression
   description.

3. **Component 1 — Graduated mechanical ramp.** Add the graduated-position
   model (entry → bridge → hallmark on hallmark-exclusive axes) as a
   resolved structural decision.

4. **Open question 3 (hallmark selection for launch catalog).** Mark as
   FULLY RESOLVED. Work era selection is no longer open.

5. **Open question 13a (era/branch content plan).** Mark as RESOLVED.

6. **Branch System subsection.** Add land/sea combined warfare as a
   hallmark-exclusive feature. Add note about separate production
   structures and distinct movement models.

7. **Status line.** Update to reflect era selection resolution.

---

## Still Open (not resolved this session)

- Q-mon8.5 (cross-branch prestige) — remains open.
- Q-mon8.6 (post-launch branch rollout cadence) — remains open.
- Open question 6 (third hallmark era for tutorial) — remains open.
- Open question 9 (special edition eras) — remains open.
- Open question 13b (website point-of-sale design) — remains open.
- Open question 13c (Steam page presentation) — remains open.
- Open question 13d (in-game purchase flow integration) — remains open.
- Per-era visual identity work for new eras (Planetary Colonization,
  Interplanetary, Colonial/Independence, WWII) — not started.
- **Full `era_mechanical_axes.md` capture into bible — pending dedicated
  session.** The 8-axis framework (axes 4–8: layer access, force scale,
  terrain expressiveness, environmental threat, cross-layer engagement),
  the 8×3 matrix, and the Branch DNA vs. hallmark-exclusive formal
  annotations all need to be written into `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (Branch
  System extension) and `docs/bible_history/bible_2_00_combat.md` (per-era parameterization
  re-opens). The bible currently only describes 3 axes in the Branch
  System subsection; the actual design uses 8. The graduated ramp
  paragraph references the axes doc but the doc itself is transient.
  This is a substantial capture task — recommend its own session.
- Axes doc Batch 4 (Branch DNA vs. hallmark-exclusive formal lock) — 
  not yet done (matrix annotations are "candidate" status).
- Axes doc Batch 5 (rejected + stretch axes) — not yet done.
- Land/sea production structure design details — flagged for combat bible.
- Colonial/Independence force scale (200–600) exceeding Branch 2 DNA
  default (100–300) — noted as per-era config override, compatible with
  Sacred Principle #3. May need engine performance validation at 600
  units (current MAX_UNITS = 400).