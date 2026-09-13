# Visual Identity — Design Questions

> **LEGACY MONETIZATION ASSUMPTIONS — 2026-05-09**
>
> The monetization-redesign sections of this document (subscription at $2/month,
> entry-era subscription gating, starter-bundle retirement, Roman free tier scope
> cuts, external-website checkout, in-game inspection-as-storefront with external
> redirect) describe a model that has been **scrapped**. Steam does not allow
> linking out to external payment websites from in-game. Current model: **buy-once
> base game (starting civ of every branch) + paid Steam DLC for additional eras,
> no subscription, no free tier, all transactions via Steam**. See
> `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` "Current Monetization Model" section.
> Visual identity, logo, wordmark, era branding, Canva templates, Steam page
> presentation, and capsule-art decisions in this document remain valid — only the
> commerce-flow sections are obsolete.

> **Transient working doc.** Governs the visual identity brainstorming effort
> (logo, wordmark, era branding, Steam page, Canva asset kit) and the
> monetization redesign that branched off it. Per `design_rules.md`, this
> file bridges chats. Once all questions are CAPTURED into the bible and/or
> a stage spec, this file is deleted.
>
> **Capture targets:** `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (primary), `docs/bible_history/bible_2_00_combat.md`
> (pending edits — see Pending Bible Edits below), `game_bible.md` hub.
>
> **Production outputs** (logo files, Canva templates, Steam assets) live
> outside the bible. The *rules* that govern their creation go in the bible.

---

## Production Constraints — Apply To Every Question

Hard constraints on the entire visual identity effort. Every question must
be answered within these limits.

- **Canva is the authoring tool.** Westley designs everything himself in
  Canva. Anything decided must be reproducible by one person in Canva
  without an external designer.
- **Sloyd AI is available for 3D asset generation.** Sloyd can generate
  3D forms that become visual references or be rendered to bitmaps for
  import into Canva.
- **Inkscape → bitmap → Canva pipeline.** Westley can author complex
  vector work in Inkscape, export as bitmap, and bring it into Canva.
  Workaround for Canva's limited vector tooling.
- **Westley has no marketing experience.** Reference work must be
  substantive and educational, not assumed-knowledge. When referencing
  how Paradox or Fortnite does something, explain *what* they do and
  *why* it works.
- **Solo developer.** No art team, no marketing team, no external help.
  Per-era work that takes 20 hours per era does not scale to a 20-era
  catalog.

---

## Current State (as of Steam Page Session, April 24, 2026)

**Locked and captured to bible:** Master shield logo, OUROBOROS MANIFOLD
wordmark, three launch era variants (Roman, 1980s, Settled Reach),
production tooling (Recraft V4 + escalation paths), v3.00 monetization
framework with 2-launch-branch + Roman-standalone structure (Q-mon8.1 v2 /
Q-mon8.2 v2), conversion strategy (component 11), Era Library
"Manifold Planes" navigation UI (component 12), era card template (Q3 —
eight sub-decisions covering glyph design, card layout, hover interaction,
hallmark differentiation), **Steam page presentation strategy (Q4/Q5 —
component 14: meta-identity capsule, era-alternating screenshots, era-cut
trailer, branch infographic, tag strategy).**

**Pending bible capture:** No deferred captures.

**Open work, in priority order:**

1. ~~Combat bible session~~ — **CAPTURED April 17, 2026.** Four re-open
   flags written to `docs/bible_history/bible_2_00_combat.md`. Implementation deferred to
   post-Stage 13.
2. ~~Settled Reach combat retcon planning~~ — **SCHEDULED post-Stage 13.**
   Flagged in `docs/bible_history/bible_2_00_combat.md` Stat Philosophy and Unit Stat Baselines
   sections. Listed in `game_bible.md` "Beyond Stage 13."
3. ~~Q-mon4 starter bundle resize~~ — **RESOLVED April 16, 2026.**
   Starter bundle concept retired. Subscription grants access to Era 1
   (entry era) in every branch. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 5.
4. ~~Q-mon8.3 — entry gate model per branch~~ — **RESOLVED April 16,
   2026.** Per-era gating: entry eras subscription-gated, progression
   eras grindable to permanent ownership, hallmarks/premium eras
   one-time purchase. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 5 and
   open question 10.
5. Q-mon8.5 — cross-branch prestige.
6. Q-mon8.6 — post-launch branch rollout cadence.
7. ~~Q3 era card template~~ — **RESOLVED April 22, 2026.** Eight
   sub-decisions: material-rendered compound-mark glyph (civilization's
   sacred object), portrait 2:3 ratio, glyph-plus-context layout,
   radial peek + side-sliding data hover, SC2-border mastery elaboration,
   hallmark differentiation via gold frame + glyph complexity. See Q3
   section below.
8. ~~Q4–Q5~~ resolved April 24, 2026. Q5 research pass completed
   (7 reference targets). Q4 Steam page hierarchy resolved as
   component 14 in `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/). Q6–Q7 now unblocked.
9. Q-mon3, ~~Q-mon5~~, Q-mon6, Q-mon7, Component 9 (special editions) all
   still deferred to catalog design. Q-mon5 **RESOLVED April 16, 2026** —
   Roman free tier: 5/10 archetypes, T2-locked, 3-faction/15-region
   world. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 4.
10. ~~Conversion strategy~~ — **RESOLVED April 22, 2026.** Tutorial taste +
    ambient inspection. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 11.
11. ~~Era Library UI layout~~ — **RESOLVED April 22, 2026.** Manifold Planes
    spatial metaphor. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 12. Also
    resolves open question 12(c) (branch-view UI layout).

---

## Resolved Decisions — Reference

> Compact summary of every CAPTURED decision. Full rationale lives in the
> bible (which is the source of truth). This section is the index, not
> the canonical record.

### Brand identity

- **Q1 — Brand color.** Gold (`#c9a84c`) is the Westopoli / Ouroboros
  Manifold brand color. Owns main menu, splash, logo, title treatment,
  Steam page meta-identity. Era accents stack on top of gold rather than
  replacing it. Cool-palette eras must coexist with gold via desaturation
  + temperature-shift, not chromatic opposition.

- **Q2 — Master logo.** Four-quarter heraldic shield with central
  ouroboros, ornate metalwork register (silver/pewter/bronze), dense
  foliate borders, "ancient artifact" feel. **B+++ hybrid:** master
  shield invariant; era variants modify only frame ornamentation and
  color treatment around the master. Era-agnostic carve-out granted to
  the master logo specifically (documented in bible to prevent drift).
  Future marquee releases may go full B++ (redrawn quarters) as an
  optional production path.

- **Q2c — Quarter labels.** Genesis / Imperium / Crepusculum / Aurora
  (Latin, heraldic tradition). Imperial arc that loops back: Aurora
  feeds Genesis. Canonical names for marketing/codex/internal use, not
  necessarily visible text on the shield.

- **Q2d — Central ouroboros style.** Greco-Roman classical form with
  Celtic/Norse interlace compositional accent. Body weaves once or twice
  before completing the bite; knot work anchors the closure point. Reads
  classical at first glance, reveals interlace on closer inspection. At
  small icon scale interlace partially drops out to a clean classical
  serpent loop. Both readings must be consistent.

- **Q-wordmark — OUROBOROS MANIFOLD typographic treatment.** Custom
  ligature on a classical display serif base (Trajan / Cinzel family),
  with the two **O** letterforms in OUROBOROS replaced by closed-loop
  ouroboros serpent marks that echo the central shield ouroboros — same
  Greco-Roman closed loop with single Celtic/Norse knot crossing, no
  literal serpent detail. Production: Recraft V4 vector typography mode
  for the base, standalone serpent-loop generation in Recraft V4 then
  Inkscape composite (stage 2a), Inkscape hand-draw fallback (stage 2b),
  fallback to plain classical serif if custom ligature fails. Must
  remain legible at Steam capsule size; closed-loop silhouette must
  survive when fine details drop out.

### Era variants (material-per-era principle)

**General rule:** Each era picks a frame material appropriate to its
own register — not a color/motif swap on the same metal substrate, but
a genuinely different material that says something about what that
era *is*. Master shield's metalwork anchors the brand; era variants are
re-cast or re-carved in the material voice of a specific civilization's
moment. For non-obvious eras: ask *"what material would this civilization
have considered permanent, valuable, or ceremonial?"*

- **Q2e-Roman.** Carved travertine marble frame, low-relief
  architectural carving. Border motif: classical architectural ornament
  (egg-and-dart, meander). Accent color: **oxblood `#6b2a2a`**.
  Positioning: civilization that built things meant to outlast it
  (rejects generic bronze-and-laurel military register).

- **Q2e-1980s.** Heavy military canvas / cotton duck frame, visible
  weave and stitched edges. Border motif: stenciled military equipment
  markings (serial numbers, hazard diamonds, classification bars).
  Accent color: **olive drab `#5a5f3a`**. Positioning: Cold War
  classified-equipment register, deliberately rejects Miami-Vice
  consumer 1980s. Strongest material dissonance with master shield —
  intentional, managed by keeping shield quarters and ouroboros
  visually dominant.

- **Q2e-SR (Settled Reach).** Brushed titanium frame with directional
  grain and subtle warm-cool oxidation iridescence. Border motif:
  engraved orbital mechanics (orbital paths, Lagrange notation, delta-v,
  trajectory geometry). Accent color: **`#446e7e`**, cool steel blue
  shifted toward teal. Positioning: civilization whose sacred
  inscriptions are engineering — aerospace precision as ornament
  tradition. Establishes the cool-palette-vs-gold pattern via
  desaturation + teal-shift.

  > **Session 6 note:** Visual positioning unchanged. *Tactical*
  > positioning shifts under Q-mon8.1 v2 — Branch 1 fast/short-decisive
  > combat moves Settled Reach from "careful targeting" toward "rapid
  > strike / high-lethality precision." Combat retcon is a dev_rules
  > consequence; visual identity unaffected.

### Production tooling

- **Q-tools — Recraft V4** is the primary AI image tool for the entire
  visual identity pipeline. $10/month Basic with commercial license,
  vector output, brand-style reference upload, palette constraint
  injection, no training-data lawsuit exposure. Era variants are
  deliberately less ornate than the master, collapsing the
  scalability-vs-ornament tension.

  **Escalation tree:**
  - Path 1: Recraft alone, self-polish in Inkscape (~$10, expected to
    hit 70–90% of bible target).
  - Path 2: Recraft → cheap freelance touchup ($50–150 Fiverr/Dribbble,
    refinement-not-invention brief). Used if Path 1 plateaus below target.
  - Path 3 (paper fallback): Midjourney/Nano Banana Pro one-month
    photoreal render → human vectorization → Recraft reference. Only if
    Paths 1 and 2 both fail.

  **Production test order for first Recraft month:**
  1. Wordmark stage 1 — classical display serif (low risk, confidence builder)
  2. Wordmark stage 2a — abstracted ouroboros serpent mark (low)
  3. Master shield — ornate metalwork in vector (hard)
  4. Roman variant — travertine marble in vector (hard)
  5. 1980s variant — canvas weave and stitching in vector (hard)
  6. Settled Reach variant — titanium iridescence in vector (moderate)

  Bible documents the *principle* ("vector-first AI generation with
  brand-style reference locking") rather than the specific tool name to
  avoid bible-rot if Recraft is superseded.

- **Q-commission — moot.** Master logo is self-produced via Recraft with
  Path 2 touchup as escalation. Full from-scratch commission ($200–500)
  is not on the path.

### Monetization (v3.00)

- **Q-mon1 — Conditional ownership model.** Three era categories in the
  player's library: **Purchased** (one-time buy, permanent), **Earned**
  (grinded past retention threshold while subscribed, permanent, survives
  cancel), **Rented** (starter bundle, revoked on cancel with progress
  preserved server-side).
  - Retention threshold: ~15 hours of play at baseline, driven by the
    same mastery currency that powers the SC2-border UI elaboration
    system (component 10). Performance bonuses from unit retention and
    in-mission objectives. Starter bundle eras eligible for retention
    on the same rule as grind-earned eras.
  - Subscription: **$2/month**, deliberately below Paradox outrage
    threshold (~$5).
  - Paid transactions flow through Westley's external website, not
    Steam. Only the free Steam version is on Steam — neutralizes Steam
    refund-cascade risk.

- **Q-mon2 — No entry fee.** Free Roman player goes directly to $2/mo
  subscription. At this price, intermediate paywalls cost more in
  friction than they gain in conversion.

- **Q-mon8.1 v2 — Branch mechanical identity, multi-axis hybrid.**
  Three-axis differentiation layered per branch:
  - **Axis A — Tempo / pacing** (engagement duration, movement, action
    density).
  - **Axis B — Information warfare** (fog density, sensor range,
    cross-layer sight, scout vs. sensor).
  - **Axis D — Attrition / economy** (reinforcement rate, structure
    density, replacement pace, force preservation value).

  All branches retain cross-layer detection, engagement, and movement
  as capabilities. The layer system exists universally. What varies
  is how *fast*, how *informed*, and with *how much force replacement*
  each branch fights.

  **Branch signature stances:**
  - **Branch 1 (sci-fi/future):** fast tempo (30–45s engagements);
    near-total awareness (sensor dominance, free cross-layer sight,
    counter-stealth as active cost); small quantities + rapid recovery
    (force preservation matters less, plan quality matters more).
    *Player feel: "Plan the strike, execute it fast, reconstitute, go
    again."*
  - **Branch 2 (modern/recent history):** medium tempo (1–2min
    engagements); partial sensor asymmetry (radar/intel/recon all
    partial, ECM and scouts matter); industrial replacement (moderate
    quantities, doctrine and logistics decide campaigns). *Player feel:
    "Combined arms, manage information, outproduce or outmaneuver."*
  - **Branch 3 (ancient history, post-launch):** slow tempo (2min+
    attritional grind); heavy fog + scout-dependent (recon is king,
    ambush is real, sensors largely absent); slow reinforcement
    (casualties hurt, force preservation matters). *Player feel:
    "Scout carefully, preserve your force, position decides the fight."*

  **Roman:** outside branch structure (Q-mon8.2 v2). Mechanically sits
  closest to Branch 3. Specific stance is a Q-mon5 decision; working
  assumption is Branch-3-adjacent tempo and attrition with reduced
  information-warfare depth for free-tier onboarding simplicity.

  **Symmetric ruleset** — both player and enemy play under the same
  branch rules. **Cross-branch faction interaction** out of scope for
  launch. **Difficulty orthogonal** to branch — branch is "which game,"
  difficulty is "how hard the game is." Bible principle "difficulty
  never changes enemy strength" still holds within a branch.

  **Sacred Principle #3 compatibility — config-driven, not code-branched.**
  Engine is branch-blind (no `if branch == "scifi"` anywhere). All
  mechanical variation lives in per-era config parameters the engine
  consumes uniformly. Branches are a monetization/progression catalog
  concept, not an engine concept. The 6 base unit types are present in
  every era; production structure types are universal; only their
  amounts/rates/stats differ per era. Hub clarification added Session 6.

  **Tuning infrastructure requirement.** Large-scale branch tuning
  requires organized test directories, staged execution, strict modern
  vs. legacy test management. CC must report seed counts and confidence
  intervals for branch tuning, not point estimates — stochastic noise
  across multiplied configuration space is real. "80% over 10 seeds" is
  meaningless; 100 seeds with tight CI is real signal.

  > Q-mon8.1 was originally resolved as Option D (full cross-layer
  > gradient with Branch 3 having no cross-layer capabilities) in
  > Session 5; reversed in Session 6 to the Option E hybrid above.
  > See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) for current state.

- **Q-mon8.2 v2 — Branch count and Roman relationship.** **2 launch
  branches + Roman standalone = 7 launch eras total.**
  - Branch 1 (sci-fi/future): 3 eras at launch incl. Settled Reach
    hallmark; extends to 5+ post-launch.
  - Branch 2 (modern/recent history): 3 eras at launch incl. 1980s
    hallmark; extends to 5+ post-launch.
  - Roman: standalone free tier outside any branch. `branch_id = null`
    or `"free_tier"` in data model. Not part of any branch's linear
    sequence. Permanent free-to-play onboarding.
  - Branch 3 (ancient history, non-Roman): **deferred to first
    post-launch expansion.** Candidate civilizations: Han China,
    Achaemenid Persia, New Kingdom Egypt, Classical Greece, Mauryan
    India (not committed). Cleanest cut because it's least-developed —
    Settled Reach and 1980s already have captured visual identity;
    Branch 3 hallmark has none.

  **Rationale:** fastest path to player feedback; Branch 3 cuts the
  least committed work; Branch 3 becomes the first concrete case study
  for Q-mon8.6 (post-launch rollout cadence).

- **Q-mon8.3 — Entry gate model.** Mix of WoT-style free entry,
  Destiny-style expansion gate, and Stellaris-style commitment gate.
  Player can pay for basically everything. Specific gate per branch
  is OPEN.

- **Q-mon8.4 — Intra-branch ordering.** **Linear sequences, no
  sub-splits.** Rationale: RTS players are trained on linear campaign
  ordering (SC2, AoE, Halo Wars); sub-splits are a 2× production
  multiplier; linear gives a clean integer "track position" for the
  Q3 era card. WoWS pattern retained: full branch visible from branch
  entry — all 3 (eventually 5) eras displayed upfront with inspection
  available regardless of progress.

### Q-mon8 research findings (kept for reference)

Ten lessons from the Session 5 research pass across WoWS, WoT, Warframe,
PoE, Fortnite, CoD, Destiny 2, Stellaris, Civ. These continue to inform
open Q-mon8 sub-questions:

1. Branch identity must be mechanical, not just thematic.
2. 3–5 branches is the sweet spot for strategy-genre branching with
   mechanical identity.
3. Completed branch positions must remain accessible after advancement
   (PoE is the outlier and players hate it).
4. Entry choice and commitment are separable design levers.
5. New branches should launch as expansion events (Destiny Stasis/Strand,
   Stellaris Utopia/Machine Age).
6. Branches need a visible apex that rewards commitment (WoWS Superships,
   WoT Mastery Tanks, Destiny Exotic class items, etc.).
7. Cross-branch prestige is a real long-term retention mechanic (WoWS
   Research Bureau, Destiny Prismatic, CoD cross-class mastery).
8. UI: tech tree screen is separate from the play surface (WoWS Port vs.
   Tech Tree, Destiny Director vs. subclass menu).
9. Inspection must be first-class from the tech tree view itself.
10. Battle pass lesson that transplants: visible progression bar with
    known endpoint and valuable apex (each branch needs its own
    progression bar — "3/5 eras earned in the Ancient branch").

**What the research rules out:** Fortnite-style cosmetic-only branching;
PoE-style forced commitment with punishing respec; more than 5 branches
at launch; Civ-style in-game tech trees (wrong model — branches are a
meta-catalog navigated across sessions).

---

## Pending Bible Edits

### Combat bible re-opens (CAPTURED April 17, 2026)

All four re-open flags have been written into `docs/bible_history/bible_2_00_combat.md`:

1. ✅ **Tactical Reinforcement section** — per-era config flag added.
2. ✅ **Combat pacing / engagement duration targets** — per-branch targets flag added to Stat Philosophy.
3. ✅ **Stat philosophy / unit HP** — per-era tunable flag added to Unit Stat Baselines, Settled Reach retcon noted.
4. ✅ **Information warfare / fog-of-war / sensor** — new discrete section added with per-branch signature defaults.

All four flag implementation as **deferred to post-Stage 13**. Friends-ZIP ships single era with current values unchanged. `game_bible.md` "Beyond Stage 13" updated with branch parameterization and Settled Reach retcon entries (v2.14).

### Other deferred captures

- **`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) v3.00 component 2** hallmark count
  language still says "3–4 hallmarks at launch" — needs tightening
  to "2 at launch." (Low priority — does not block any work.)

---

## Open Questions

### Q3 — Era Card Template [RESOLVED April 22, 2026]

The era card is the reusable visual unit that represents an era across all surfaces: Manifold Planes nodes, Steam page, social media, in-game Era Library. Eight sub-questions resolved in a single session.

**Q3-1 — Hero visual element.** The card foregrounds a **per-era symbol** (the era glyph defined below). No cinematic scene, no unit showcase on the card itself. Units, structures, and maps appear only on hover interaction.

**Q3-2 — Aspect ratio.** **Portrait 2:3.** Matches Steam Library Capsule (600×900). Crops cleanly to circular/square for Manifold Planes nodes. Trading-card feel reinforces era-as-collectible identity.

**Q3-3 — Per-era symbol type.** **Era Glyph with Material Rendering.** Abstract geometric mark per era, rendered in the era's signature material (travertine for Roman, canvas for 1980s, etched titanium for Settled Reach). Ties into the existing material-per-era principle from Q2e logo variants. The glyph is the era's "insignia" — the informal identity mark, sibling to the logo variant's formal "coat of arms." Both share material language, serve different purposes.

**Q3-4 — Hover interaction.** **Radial Peek + Side-Sliding Data.** On hover: symbol lifts with slight parallax shift; 3–4 asset thumbnails (units, structures, environments) radiate outward from center. Simultaneously, structured era data (name, branch position, mastery progress, ownership status, tagline) slides in from the sides. Full rosters and deep inspection remain behind click-through.

**Q3-5 — Glyph design language.** **Compound Mark (geometric core + detail halo).** Bold geometric core shape for small-size readability, surrounded by a fine detail halo of era-specific notations (Roman: architectural measurement lines, Latin fragments; 1980s: stenciled serial numbers, classification markings; Settled Reach: trajectory calculations, coordinate notations). Core carries material rendering; halo gets lighter treatment (etched, faded, ghosted). Two-scale behavior: at Manifold Planes node size the core reads alone; at full card size the halo detail appears. Production via **Recraft V4** — core shape is well within Recraft's vector strengths; halo detail may require Inkscape cleanup. No freelance touchup expected for era glyphs (escalation path reserved for master logo).

**Q3-6 — Glyph subject matter.** **Civilization's Sacred Object.** Each glyph depicts what the civilization worshiped through its works — not its weapon, but its aspirational artifact.

- **Roman:** The arch — Rome's signature architectural form, abstracted to pure geometry. Rome worshiped permanence through engineering.
- **1980s:** The satellite dish / radar array — the Cold War's sacred instrument of information dominance.
- **Settled Reach:** The orbital ring / Lagrange point marker — the far-future's sacred geometry of precision and coexistence with gravity.

Material rendering carries instant era recognition; the shape carries deeper thematic meaning. Post-launch eras follow the same principle: ask "what single object would this civilization have put on its own flag?"

**Q3-7 — Card layout.** **Glyph-Plus-Context.** Glyph occupies upper half of card. Lower half: structured metadata panel with era name (Newsreader serif), branch name and position ("Branch 1 — Era 2 of 3"), ownership status badge, mastery progress bar, one-line tagline. Era logo variant at top edge as header mark. Hover interaction expands upon metadata rather than introducing it for the first time.

**SC2 ranked border inspiration.** Mastery progression visibly transforms the card's visual treatment — the difference between a base-tier card and a max-mastery card should feel like the difference between SC2 Gold and Grandmaster borders. Earned, aspirational, a status symbol. Mastery UI elaboration (component 10) applies to the card frame: higher mastery = more elaborate border treatment, richer glow, additional decorative elements. The mastered card is something the player is proud to have.

**Q3-8 — Hallmark vs. work era differentiation.** **Frame Treatment + Glyph Complexity (B+C hybrid).** Two simultaneous differentiators:

- **Frame:** Hallmark cards get a gold brand-color frame treatment (thin gold rule or glow, not heavy border). Work-era cards get no frame or a subtle accent-color hairline. Gold = premium, readable at any size, on any surface.
- **Glyph complexity:** Hallmark glyphs get a richer compound mark — more detailed halo, finer secondary lines, additional satellite elements. Work-era glyphs are cleaner, simpler versions of the same design language. The distinction lives in the art itself, not just the frame.

The combination ensures the hallmark/work distinction is visible both structurally (frame) and artistically (glyph richness).

**Card data slots (updated):** `branch_id` (1, 2, or null for Roman/standalone), `branch_position` (1–3 for branch eras, null for Roman), `era_category` (Purchased / Earned / Rented / Inspection-only), `mastery_tier` (drives frame elaboration per SC2 border model), `tutorial_flag`, `is_hallmark` (drives gold frame + rich glyph), `era_glyph_asset` (compound mark image ref), `era_tagline` (one-line descriptor).

---

### Q4 — Steam Page Hierarchy [RESOLVED April 24, 2026]

Steam page presentation strategy resolved as component 14 in
`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/). Key decisions: meta-identity-first capsule
art (master shield or composite glyph, not single-era), era-alternating
screenshots unified by the layer system as visual thread, era-cut
montage trailer (~60s, hard cuts between eras, works muted), branch
progression infographic as spatial map (not price list), tag strategy
prioritizing "Story Rich" and "Atmospheric," "About this game"
hierarchy (pitch → infographic → features → screenshots → long
description). No monetization details on Steam page — Steam sells
the download, external website sells the subscription. See
`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 14 for full specification.

---

### Q5 — Research Pass — Reference Studios [RESOLVED April 24, 2026]

Research completed covering all seven targets: Paradox Interactive
(DLC-driven long-tail, $5/month subscription backlash, community buying
guide failure mode), Creative Assembly / Total War (era-specific visual
language, Saga as work-era analog, franchise page as era timeline),
Supergiant / Hades (25-person studio premium visual identity, consistent
cross-surface branding, short confident Steam copy), Fortnite / CoD
(master brand + seasonal variants, battle pass endpoint visibility,
clear category separation between grindable and purchase-only),
Stellaris (closest competitor positioning, "Story Rich" tagging, lead
with feeling not mechanics), Deep Rock Galactic (promotion stars as
mastery visualization, non-competitive prestige in single-player,
free players see paid rewards), Steam page best practices 2025–2026
(capsule CTR as algorithm currency, first 4 screenshots on hover,
45–75s trailer, mobile readability at 35–45% of visits).

Synthesis captured in `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 14. Full
research document: `q5_research_synthesis.md` (transient, deletable
after Q4 capture).

---

### Q6 — Canva Asset Kit [RESOLVED April 24, 2026]

Seven-template full kit captured as component 15 in
`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/). Templates: era card (2:3), Steam capsule
master (4 export sizes), social post (1:1), Discord/profile banner,
trailer thumbnail, branch progression infographic, screenshot
annotation overlay. All share gold-frame + dark-background + accent-color
slot-fill system. Per-era production is ~15 min per template per era.
Production order: era card → Steam capsule → social post → infographic
→ remaining four.

---

### Q7 — In-Game Era Pack Merchandising / Store Layout [RESOLVED April 24, 2026]

Inspection mode IS the store page (component 9 content does the selling).
Three additions for conversion: (1) persistent SC2-Masters-register
acquisition banner at bottom of inspection screen — compact, metallic
sheen, animated glow, always visible, adapts label to era access model;
(2) contrast moments at 2–3 scroll points showing Roman vs. target era
split comparisons; (3) external website redirect on button click.
Non-aggressive — no timers, no modals, no FOMO. See component 16 in
`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/).

---

### Q-mon3 — Hallmark Era Selection [PARTIALLY RESOLVED]

2 launch hallmarks locked: **Settled Reach** (Branch 1) and **1980s**
(Branch 2). Third hallmark waits for Branch 3 post-launch. Catalog
design (which non-hallmark eras populate each branch's remaining 2
launch slots) is the remaining open work.

---

### Q-mon4 — Subscription Starter Bundle Selection [RESOLVED April 16, 2026]

~~The original 5-era starter bundle from v3.00 is **71% of a 7-era launch
catalog** — structurally incoherent as a "starter."~~

**Resolution:** The starter bundle concept is retired. Subscribing grants access to Era 1 (entry era) in every branch — no separate bundle to select or resize. The "what do I get when I subscribe?" answer is: access to every branch's entry era, plus the ability to grind toward everything else. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 5.

---

### Q-mon5 — Roman Free Tier Scope Limitations [RESOLVED April 16, 2026]

**Resolution:** Three cuts that reinforce each other: (1) 5/10 mission archetypes (Defensive Stand, Assault, Reconquest, Siege Breaking, Evacuation — excludes Multi-Front Defense, Interception, Containment, Counterinsurgency, Suppression); (2) locked to Tier 2 for all factions (no tier progression visible); (3) capped world size (3 factions, ~15 regions, Isolated Start only). Roman keeps full simulation, full combat, full chronicle, full generational loop, and inspection mode for all paid eras. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 4.

---

### Q-mon6 — Third Hallmark Era for Multi-Stage Tutorial [OPEN, deferred]

Original v3.00 plan: tutorial spans three hallmark eras. With only 2
hallmarks at launch, third stage is deferred. Options when Branch 3 ships:
extend tutorial to include Branch 3 hallmark, or finalize as 2-stage
tutorial and treat Branch 3 hallmark as a separate post-launch tutorial
extension.

---

### Q-mon7 — Tutorial Sub-Objective Design [OPEN]

Which specific moments from each hallmark anchor the tutorial sub-objectives.
Deferred to catalog design.

---

### Q-mon8.3 — Entry Gate Model Per Branch [RESOLVED April 16, 2026]

**Resolution:** Per-era gating replaces per-branch gating. Entry eras (Era 1 in each branch) are subscription-gated — accessible while subscribed, revoked on cancel. Progression eras (Era 2+) are grindable to permanent ownership while subscribed (15hr retention threshold). Hallmarks and select premium eras are one-time purchases, permanent ownership. Any era can be tagged premium regardless of branch position. Launch branches use free entry (subscription unlocks both). Post-launch branches follow the same model — no separate expansion gate needed; the branch is open via subscription, hallmark is premium. See `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) component 5 and open question 10.

---

### Q-mon8.5 — Cross-Branch Prestige [OPEN]

What does completing multiple branches reward? Does Ouroboros Manifold
have a "finished every branch" terminal state? Research surfaced this as
a real retention lever (WoWS Research Bureau, Destiny Prismatic, CoD
cross-class mastery) but no design direction committed. Needs research
pass and dedicated session.

---

### Q-mon8.6 — Post-Launch Branch Rollout Cadence [OPEN]

How does a new branch ship — as an expansion event tied to a new hallmark
era (Destiny/Stellaris model), or as a content drop slotting into the
existing tree? Now immediately relevant because Branch 3 is explicitly a
post-launch rollout. Research targets: Destiny Stasis/Strand/Prismatic
launch playbook, Stellaris Utopia/Machine Age playbook.

---

### Settled Reach combat retcon planning [SCHEDULED — post-Stage 13]

~~Not a design question but a downstream consequence of Q-mon8.1 v2 that
needs scheduling.~~ **Scheduled post-Stage 13.** Settled Reach's current
slow/high-HP/methodical combat identity inverts under Branch 1 fast tempo.
HP values drop; engagement duration targets shift from 2min+ toward
30–45s; aerospace-precision register shifts from "careful targeting"
toward "rapid strike." Flagged in `docs/bible_history/bible_2_00_combat.md` Stat Philosophy and
Unit Stat Baselines re-open flags. Listed in `game_bible.md` "Beyond
Stage 13." Friends-ZIP ships with current Settled Reach values unchanged.

---

### Production architecture parameterization [SCHEDULED — post-Stage 13]

~~Not a design question but a downstream consequence of Q-mon8.1 v2 axis D.~~
**Scheduled post-Stage 13.** Current in-mission production (reinforcement
structure amount, placement, rate, cost) parameters move from hardcoded
constants to per-era config. Compatible with Sacred Principle #3 — branch
mechanical variation lives as config-driven content, not code-branched
engine logic. No engine knows about branches; the engine consumes per-era
parameters uniformly. Flagged in `docs/bible_history/bible_2_00_combat.md` Tactical Reinforcement
re-open flag. Friends-ZIP ships with current hardcoded values unchanged.

---

### Component 9 (special editions) [OPEN, deferred]

Still deferred. Revisit after Q3–Q7 settle so special-edition presentation
inherits an established visual vocabulary.

---

## Anti-pattern watchlist

From `design_rules.md`:

- Making design decisions without surfacing them to Westley
- Batching questions before an answer lands
- Letting answers live only in chat (every ANSWERED must become CAPTURED)
- Sliding into implementation (no code, no actual Canva design work —
  just decisions about what to build)
- Silently re-opening captured decisions
