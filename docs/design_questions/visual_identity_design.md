# Visual Identity — Design Questions

> **Transient working doc.** Governs the visual identity brainstorming effort
> (logo, wordmark, era branding, Steam page, Canva asset kit). Per
> `design_rules.md`, this file bridges chats. Once all questions are CAPTURED
> into the bible and/or a stage spec, this file is deleted.
>
> **Capture target:** `bible_monetization.md`, UI Aesthetic section and new
> subsections as needed. Cross-check against `game_bible.md` hub.
>
> **Production outputs** (logo files, Canva templates, Steam assets) live
> outside the bible. The *rules* that govern their creation go in the bible.

---

## Production Constraints (Session 1) — Apply To Every Question

These are hard constraints on the entire visual identity effort. Every
question must be answered within these limits, not around them.

- **Canva is the authoring tool.** Westley designs everything himself in
  Canva. Anything we decide must be reproducible by one person in Canva
  without an external designer. "This looks great but requires Figma +
  a designer" is not an acceptable answer.
- **Sloyd AI is available for 3D asset generation.** Westley already uses
  Sloyd for in-game 3D assets (documented in game_bible). Sloyd can
  generate 3D forms that become visual references or be rendered to
  bitmaps for import into Canva. Relevant for logo, era icons, any 3D
  brand element.
- **Inkscape → bitmap → Canva pipeline.** Westley can author complex
  vector work in Inkscape, export as bitmap, and bring it into Canva.
  This is his workaround for Canva's limited vector tooling. Anything
  too complex for Canva's native tools but doable in Inkscape is still
  in scope.
- **Westley has no marketing experience.** Research and reference work
  must be substantive and educational, not assumed-knowledge. When
  referencing how Paradox or Fortnite does something, explain *what*
  they do and *why* it works, don't just name-drop.
- **Solo developer.** No art team, no marketing team, no external help.
  The visual identity system must be operable by one person in realistic
  time budgets. Per-era work that takes 20 hours per era does not scale
  to a 20-era catalog.

---

## Session Handoff — Last Updated: Session 4 (April 14, 2026)

> **Session 4 focus: monetization research pass and Q-mon1/Q-mon2 resolution.** No visual identity work this session — all effort went into finalizing the v3.00 ownership-vs-access model and entry fee path per the Session 3 carry-forward list.

**Accomplished this session:**

- **Research pass complete.** WoW model (hard subscription gate, MMO precedent only), Paradox optional DLC subscription (closest strategy-genre precedent, hostile fan reaction even at $5/month, "own nothing pay forever" complaint pattern), Steam DLC refund window (14 days / 2 hours, recently tightened), softer-variant landscape. Key finding: **zero single-player precedents for hard-WoW ownership-vs-access**.
- **Critical context surfaced mid-session:** Paid transactions flow through Westley's external website, not Steam. Only the free Steam version exists on Steam. This neutralizes the Steam refund-cascade risk that was the largest nail in the hard-WoW coffin.
- **Q-mon1 RESOLVED — Conditional ownership model.** Three era categories in the player's library: Purchased (one-time buy, permanent playable), Earned (grinded past retention threshold while subscribed, permanent playable, survives cancel), Rented (5-era starter bundle, revoked on cancel with progress preserved server-side). Hybrid of WoW, Paradox optional-sub, and Apex Legends earned-currency unlocks.
- **Retention threshold mechanic defined.** ~15 hours of play at baseline, driven by the same mastery currency that powers the SC2-border UI elaboration system (component 10). Performance bonuses from unit retention and in-mission objectives. Starter bundle eras are eligible for retention on the same rule as grind-earned eras.
- **Subscription price locked at $2/month.** Deliberately below the Paradox outrage threshold (~$5 triggers strategy-audience hostility) and in coffee-money territory. Working target for launch, revisitable post-launch on data.
- **Q-mon2 RESOLVED — No entry fee (option a).** Free Roman player goes directly to $2/month subscription. At this price, any intermediate paywall costs more in friction than it gains in conversion.
- **Q-mon8 ADDED — Tech tree / branching progression topology.** Westley proposed World of Warships-style branching tech tree (sci-fi path, ancient path, 1700s path, WW1/WW2 path, etc.) with mechanical as well as visual differences between branches. Flagged as a major structural change to component 1 and deferred to its own design session. Captured as open question #10 in the v3.00 bible section.
- **Content distribution / security flagged as open question #11 in the bible.** Two candidate architectures: (a) ship everything locally, gate with account flags — simple but trivially pirateable; (b) download-on-purchase from website CDN — more complex but harder to pirate, smaller base install, cheaper per-era patching. Leaning toward (b), deferred to the webapp architecture spec for a technical design pass.

**Bible edits this session:**
- `bible_monetization.md` v3.00 section header updated from "Proposed" to current status.
- Component 3 rewritten from hard-WoW proposal to **conditional ownership model** with three era categories, retention threshold mechanic, and subscription price.
- Component 7 resolved as no entry fee.
- Cancellation behavior and expansion packs re-open notes updated to point to the resolved v3.00 model.
- Open questions list updated: Q-mon1 and Q-mon2 marked resolved with strikethrough; Q-mon8 (tech tree) added as #10; content distribution/security added as #11.

**Open carry-forward items (for next session), in priority order:**

1. **Resume Q3 — Era card template.** The monetization model is now stable enough that the card template design can proceed. The card needs to express: track position, hallmark/work distinction, era category (Purchased / Earned / Rented / Inspection-only), mastery progress toward retention threshold, current mastery tier, tutorial-era flag. **However**, Q-mon8 (tech tree) may change what "track position" means — if progression branches, the card might show a branch identifier. Decide at session start whether to tackle Q-mon8 before Q3 or design Q3 to accommodate either topology.
2. **Q4 — Steam page hierarchy.** Downstream of Q3.
3. **Q5 — Research pass on reference studios** (Paradox, Creative Assembly, Supergiant, Hazelight, Hades, Stellaris, Fortnite/CoD).
4. **Q6 — Canva asset kit.**
5. **Q7 — In-game era pack merchandising / store layout.**
6. **Q-mon8 — Tech tree / branching progression.** Either tackled before Q3 (if the topology affects card design meaningfully) or deferred to a dedicated session after Q3/Q4.
7. **Component 9 (special editions)** still deferred.
8. **Q-mon3 through Q-mon7** still deferred to catalog design.

**Session 4 output:** Q-mon1 and Q-mon2 resolved and captured. Monetization redesign is now stable. Next session can proceed with visual identity work (Q3 era card template) with confidence that the monetization structure the card presents is not going to shift underneath it — except possibly on tech tree topology, which is surfaced as the remaining foundational uncertainty.

---

## Session Handoff — Session 3 (April 14, 2026) — archived

> **Major pivot this session.** Session 3 began as a straight continuation of
> Q2e work, completed Q2e-SR and Q-wordmark, opened Q3 (era card template),
> and then pivoted into a **full monetization redesign** when Westley caught
> that designing the era card template was premature — the card is downstream
> of what the card is *for*, and the monetization structure (which the card
> presents) hadn't been fully designed. The next session picks up in the
> middle of this redesign, not back on Q2e or Q-wordmark.

**Accomplished this session (visual identity):**
- **Q2e-Settled-Reach CAPTURED:** Brushed titanium frame with engraved
  orbital mechanics ornament, positioning Settled Reach as *the
  civilization whose sacred inscriptions are engineering*. Accent
  color `#446e7e`, cool steel blue shifted toward teal to pick up
  titanium's oxidation tint. Desaturated enough to coexist with the
  warm gold brand frame per Q1's cool-palette-coexistence constraint.
- **Cool-palette-vs-gold pattern resolved in practice:** The
  resolution path is *desaturation plus teal-shift*, not chromatic
  opposition. This is now a working pattern for future cool-palette
  eras (Antarctic, underwater, future space-themed releases).
- **Q-wordmark CAPTURED:** Custom-ligature drawn letterform. Classical
  display serif base (Trajan / Cinzel family) generated via Recraft V4
  typography mode, with the two O letterforms in OUROBOROS replaced
  by closed-loop ouroboros serpent marks composited in Inkscape. The
  serpent-O's share a motif with the shield's central ouroboros at
  the same level of abstraction (Greco-Roman closed loop with one
  Celtic/Norse knot crossing, no literal serpent detail). Three-stage
  production path locked in with Inkscape hand-draw as stage 2b
  fallback and clean fallback-to-option-A clause (plain Cinzel) if
  the custom treatment can't be landed.
- **Production test list finalized:** Four hard material tests
  (master metalwork, Roman marble, 1980s canvas, Settled Reach
  titanium) plus one moderate test (Settled Reach titanium
  iridescence specifically, run side-by-side with plain stainless)
  plus two low-risk tests (wordmark stage 1 base serif, wordmark
  stage 2a abstracted serpent). Wordmark tests should run *first* in
  the Recraft first month as a confidence-builder.

**The mid-session pivot — monetization redesign:**

Westley opened Q3 (era card template) by pushing back on the framing:
designing the card is premature if the monetization model the card
presents isn't finalized. The existing bible monetization (v2.x)
treated eras as a flat catalog sold through subscription plus
one-time purchases, with mastery as a cosmetic-only reward. Westley
proposed a fundamentally different model: era catalog as a
**progression track** with work eras and hallmark eras interleaved,
grind-to-earn paths for paid players, ownership-vs-access split,
multi-stage tutorial across hallmark eras, inspection mode for all
eras, and SC2-border-style progressive UI elaboration as a mastery
reward.

The session then worked through the full shape of this redesign
across multiple turns, catching conflicts with the existing bible
and resolving several of them. The result is a proposal captured as
**v3.00 in `bible_monetization.md`** with several components locked
in and several explicitly OPEN pending research.

**v3.00 components locked in by Westley this session:**

1. **Multi-peak progression curve.** Era catalog is an ordered
   progression track with hallmarks sprinkled every ~5 positions,
   not concentrated at the end. Rough target: 3–4 hallmark eras and
   16–17 work eras for 20-era launch catalog. Reference models:
   Destiny 2, Deep Rock Galactic, World of Warcraft.
2. **Production budget is deliberately unequal.** Hallmark eras get
   1.5–2× the budget of work eras. Hallmarks get the most distinctive
   Q2e frame variant material, elaborate unit art, unusual mission
   archetypes, striking visual identity. Work eras are real content
   but have lower production ceiling.
3. **Free tier is Roman-only and deliberately scoped down.** Roman
   stays the permanent free tier but is restricted in scope (reduced
   faction count, reduced mission variety, no progression systems) to
   differentiate from the paid experience. Roman is **also** an
   on-track era for paid players, not a tack-on — paid players can
   earn Roman mastery and advance tier progression in Roman on equal
   footing with other work eras. This resolves the v2.x Roman role
   conflict.
4. **Subscription grants 5-era starter bundle plus progression track
   access.** No longer flat access to the full catalog. The
   subscriber gets 5 specific eras immediately plus the ability to
   grind non-starter eras through mastery progression.
5. **Grind pace is retention-first by design.** Tuned so continuous
   subscription is strictly better than intermittent subscription.
   Casual player (~10 hrs/month) takes 6+ months per era. Future
   pacing adjustments must be evaluated against this principle.
6. **Multi-stage tutorial — 15 minutes, sub-objectives across 3
   hallmark eras.** Settled Reach + 1980s + a third hallmark, each
   showcasing a different aspect of layer combat. Sub-objectives
   from missions, not full missions, to hit the 15-minute target.
   Player can skip the tutorial. Tutorial can be replayed **once per
   hallmark era** to prevent extraction abuse. After tutorial, all
   hallmark eras lock to inspection-only until acquired through
   normal channels.
7. **Inspection mode as first-class system.** Players can inspect
   any era at any time regardless of ownership — unit roster, map
   samples, mission archetypes, mechanics, cultural content, full
   visual identity. No missions launchable, no progression earnable.
   Reference: World of Warships ship inspection. Inspection is the
   free-preview tool; playing is the paywall.
8. **Mastery UI elaboration (SC2 border model).** Era mastery rewards
   progressive elaboration of the era's in-game UI. Base → subtle
   upgrades → significantly elaborated → full premium. Additive, not
   replacement (bones stay the same, decoration elaborates).
   Hallmark eras get more elaborate mastery UI than work eras.
   Inspection mode shows base UI; screenshots from mastered players
   show elaborated UI, which is itself a marketing moment. Only
   hallmark eras need mastered UI variants at launch; work eras can
   ship base-only and add mastered variants post-launch.

**v3.00 components OPEN pending research or design work:**

1. **Ownership-vs-access model (Q-mon1).** The WoW-style
   "purchase = own forever, subscription required to actually play"
   model is *proposed* but **blocks on a research pass**. Research
   needs to examine whether this transfers from MMO to single-player,
   whether refund risk is manageable, and whether a softer variant
   exists. The research pass is the single biggest blocker on the
   redesign.
2. **Entry fee path (Q-mon2).** Four candidates: (a) drop any entry
   fee — free Roman directly to optional subscription; (b) $3
   discounted first-month sub trial; (c) $3 permanent lifetime track
   access that still requires sub to play; (d) hybrid. Claude leans
   toward (a) as the cleanest option but this is deferred.
3. **Hallmark selection for launch catalog (Q-mon3).** Settled Reach
   and 1980s are two of the launch hallmarks. Third and fourth are
   unnamed. Meta-cosmic "Ouroboros itself" era is a candidate for
   endpoint hallmark but not committed.
4. **5-era starter bundle selection (Q-mon4).** Which specific eras
   are in the subscription immediate-access bundle? Deferred to
   catalog design.
5. **Roman free tier scope limitations (Q-mon5).** Specific
   restrictions on the free Roman experience. Deferred to Roman
   free tier design.
6. **Third hallmark for multi-stage tutorial (Q-mon6).** The tutorial
   needs a third hallmark era beyond Settled Reach and 1980s.
7. **Tutorial sub-objective design (Q-mon7).** Which specific
   tactical moments from each hallmark does the tutorial showcase?

**Bible edits this session:**

- `bible_monetization.md` Brand Logo System subsection: Q2e-SR
  captured, Q-wordmark captured (4 new paragraphs), Settled Reach
  accent color resolved in UI Aesthetic bullet.
- `bible_monetization.md` Monetization Model section: RE-OPEN NOTES
  added to Free version, New player trial period, Subscription,
  Cancellation behavior, and Expansion packs paragraphs — each
  pointing to the new v3.00 section.
- `bible_monetization.md` **new major section added:** "Progression
  Track Redesign (v3.00 Proposed)" inserted after Monetization Model
  and before Access Key System. Contains 10 components (6 locked, 4
  proposed pending research), cross-references and overwrites, 8
  open questions, and a research pass scope.
- `bible_monetization.md` Era Mastery Grind section: **explicit
  re-open note added** flagging the v2.05 decision as overwritten.
  Per design_rules.md anti-pattern #7. v2.05 paragraphs preserved
  for history; new resolution lives in v3.00 section above.

**Q3 (era card template) is paused**, not abandoned. The card
template design resumes after the monetization redesign research
pass because the card has to express: track position, hallmark/work
distinction, inspection availability, mastery level (current and
max), tutorial-era flag, special-edition flag, accent color, era
logo variant. All of these slots only exist because of the
redesigned monetization. Designing the card before the monetization
is settled would produce a template that has to be rebuilt.

**Open carry-forward items (for next session), in priority order:**

1. **Research pass — monetization redesign (Q-mon1).** Target
   references:
   - WoW ownership-vs-access model and whether it transfers to
     single-player (any precedents? refund rates?)
   - Multi-peak progression in long-tail games (Destiny 2, Deep
     Rock Galactic, Path of Exile, WoW)
   - Single-player battle-pass-adjacent systems (Deep Rock, Hades
     heat, Slay the Spire ascension, Monster Train)
   - Inspection-mode conversion mechanics (World of Warships,
     Warframe, Path of Exile stash browsing)
   - Multi-stage tutorials as marketing (Destiny 2 New Light, WoW
     Exile's Reach)
   - Tier-skip economics (Deep Rock, Warframe, Destiny 2)
   - Prestige UI as retention (SC2 ladder borders, LoL honor,
     Deep Rock promotions)
   - Single-player pricing models and the $3 entry fee question
2. **Resolve Q-mon1 (ownership-vs-access)** based on research
   findings — either commit to the WoW model, adopt a softer
   variant, or drop it.
3. **Resolve Q-mon2 (entry fee path)** based on research findings.
4. **Capture Q-mon1 and Q-mon2 resolutions** into the v3.00 section
   of `bible_monetization.md`, removing "pending research" markers.
5. **Resume Q3 (era card template)** with the finalized monetization
   redesign as context.
6. **Q4 (Steam page hierarchy)** after Q3.
7. **Q5, Q6, Q7** after Q4.
8. **Q-mon3 through Q-mon7** are deferred to catalog design and do
   not block Q3/Q4/Q5/Q6/Q7.

**Session 3 output:** All Q2e era variant work complete for launch
wave. Q-wordmark complete. Monetization redesign proposal captured
in the bible as v3.00 with explicit re-open flags on v2.x content
that's being overwritten. Next session opens with the research pass.

---

## Session Handoff — Session 2 (April 14, 2026) — archived

**Accomplished this session:**
- Q-tools CAPTURED: Recraft V4 is the primary AI image tool for the
  entire visual identity pipeline. $10/mo Basic plan with commercial
  licensing. Native SVG output, brand-style reference upload for
  series consistency, palette constraint enforcement. Chosen over
  Midjourney (raster + lawsuits), Nano Banana Pro (raster), and
  GPT Image 1.5 (raster) because vector output is the single biggest
  practical advantage across a game dev pipeline.
- Option A+ escalation path locked in: Recraft V4 alone first
  (self-polish in Inkscape), cheap freelance touchup (~$50–$150) on
  the master shield only if Recraft plateaus below the bible target,
  Midjourney/Nano Banana Pro one-month render as fallback-of-last-
  resort.
- New Session 2 constraint surfaced: **only the master shield needs
  the full ornate heraldic metalwork density**. Era logo variants are
  deliberately significantly less ornate. This collapses the
  scalability-vs-ornament tension that had been the central
  complication in Q-tools and justifies single-tool Recraft for the
  entire pipeline rather than a split-register approach.
- Q-commission CAPTURED as moot — answered by Q-tools A+.
- **Q2e-Roman CAPTURED:** Travertine marble frame with architectural
  relief ornament (egg-and-dart, meander), positioning Roman as the
  *civic monument* era rather than the generic bronze-and-laurel
  military register. Oxblood accent color (`#6b2a2a`), historically
  authentic and harmonizing warm-on-warm with the gold brand frame.
- **Q2e-1980s CAPTURED:** Heavy military canvas / cotton duck frame
  with stenciled equipment markings (serial numbers, hazard diamonds,
  classification bars), positioning the 1980s as the *Cold War
  classified-equipment* era and deliberately rejecting the consumer/
  pop 1980s register. Olive drab accent color (`#5a5f3a`), warm
  enough to harmonize with gold. Strongest material dissonance with
  the master shield of any era variant so far — intentional per the
  material-per-era principle.
- **Q1b CAPTURED** in the same edit as Q2e-Roman. Roman's accent is
  resolved, no longer a pending carry-forward item.
- **Material-per-era principle** surfaced and elevated to a general
  rule for all era variants. Each era picks a frame material
  appropriate to its own register, not just a color/motif swap on
  a metal substrate. This is now a binding constraint on all future
  era variant visual identity work.
- Q7 added to roadmap: in-game era pack merchandising / store
  layout. Scheduled after Q3 and Q4 so the in-game store consumes
  an already-established visual vocabulary.
- Bible edit DONE (this session): `bible_monetization.md` Brand Logo
  System subsection now contains (a) Ornamentation Density note,
  (b) Production Pipeline paragraph naming Recraft V4, (c)
  Material-per-era principle paragraph, (d) Roman era variant
  paragraph, (e) TBD placeholders for 1980s and Settled Reach, and
  the UI Aesthetic accent colors bullet has Roman resolved to
  oxblood `#6b2a2a`.

**Open carry-forward items (for next session):**
- **Bible edit DONE** (this session): see Accomplished list above.
  All Roman and 1980s era variant details plus the material-per-era
  principle are now in `bible_monetization.md`.
- **Q2e-Settled-Reach** — apply the material-per-era principle to
  Settled Reach. Likely material register: brushed steel, dark
  chrome, or glass (near-future infrastructure). Accent color
  resolution in same question. This is the last remaining Q2e
  question and should open the next session.
- **Q-wordmark** — OUROBOROS MANIFOLD custom/display font. Can run
  parallel to or after Q2e-Settled-Reach.
- **Q3** — era card template. Opens the session after Q-wordmark.
- **Q7** — in-game era pack merchandising layout. Downstream of
  Q3 and Q4.

**Natural next session ordering:**
1. Q2e-Settled-Reach (closes out all Q2e work)
2. Q-wordmark
3. Q3 (era card template)

**Session 2 output:** Production pipeline decision locked. The
visual identity effort now has a concrete answer to "what tool
produces this?" — Recraft V4 as substrate, human touchup as
escalation. All future questions about what to build can assume
this production path without re-litigation.

---

## Session Handoff — Session 1 (April 14, 2026) — archived

**Accomplished this session:**
- Established question roadmap and working process
- Captured production constraints (Canva, Sloyd, Inkscape pipeline, no
  marketing experience, solo dev)
- Q1 CAPTURED: gold is the Westopoli / Ouroboros Manifold brand color
- Q2 CAPTURED: four-quarter heraldic shield with central ouroboros,
  ornate metalwork register, abstract/esoteric quarter content,
  B+++ hybrid production approach (master ships once, era variants
  modify only frame/color/material). Era-agnostic exception documented
  explicitly in bible as a narrow carve-out limited to the master brand
  logo. Reference image preserved as
  `visual_identity_reference_shield.png` in outputs.
- Q2c CAPTURED: four phase labels are **Genesis / Imperium /
  Crepusculum / Aurora** (Latin, heraldic tradition). Imperial arc
  that loops back: Aurora feeds Genesis. Labels are canonical names
  for marketing/codex/internal use, not necessarily visible text on
  the shield.
- Q2d CAPTURED: central ouroboros is **Greco-Roman classical form
  with Celtic/Norse interlace compositional accent**. Body weaves
  once or twice over itself before completing the bite; knot work
  anchors the closure point. Reads classical at first glance,
  reveals interlace complexity on closer inspection. At small icon
  scale the interlace partially drops out, leaving a clean classical
  serpent loop — both readings must be consistent.
- Hub cross-check complete. Only spoke edits needed.
- Q-wordmark, Q-tools, Q-commission queued.

**Session 1 output:** A complete, bible-captured spec for the master
brand logo: ornate heraldic shield, four Latin-labeled quarters
(Genesis / Imperium / Crepusculum / Aurora), central Greco-Roman
ouroboros with interlace accent, gold as brand color, era-agnostic
carve-out documented.

---

## Question Roadmap

The full arc of this brainstorming effort. Order is rough; later items may
be reordered based on what earlier answers surface.

| # | Question | State |
|---|---|---|
| Q1 | Shell identity vs. era identity — is the Westopoli brand neutral or does it own a color? | CAPTURED |
| Q1b | What is Roman's new accent color (now that gold is brand-level)? | CAPTURED |
| Q-wordmark | Custom/display font for OUROBOROS MANIFOLD wordmark | CAPTURED |
| Q2 | Logo system — master + era variants; heraldic/shield direction | CAPTURED |
| Q2a | Reframing — phases of humanity vs. phases of civilization | CAPTURED |
| Q2b | B+++ hybrid vs. pure B+ vs. B++ | CAPTURED |
| Q2c | What are the four specific phases? (rise/peak/fall/renewal, early/mid/future/super-future, etc.) | CAPTURED |
| Q2d | What does the central ouroboros look like? Style and stance. | CAPTURED |
| Q2e-Roman | Roman era frame treatment & accent color | CAPTURED |
| Q2e-1980s | 1980s era frame treatment & accent color | CAPTURED |
| Q2e-SR | Settled Reach era frame treatment & accent color | CAPTURED |
| Q-tools | AI generative tools for logo creation — research pass | CAPTURED |
| Q-commission | Should the master logo element be commissioned vs. self-produced? | CAPTURED (moot) |
| Q3 | Era card template — the reusable visual unit that sells an era | OPEN (paused pending monetization redesign) |
| Q4 | Steam page hierarchy — capsule, header, screenshots, trailer structure | OPEN |
| Q5 | Research pass — reference studios and proven single-player DLC marketing strategies | OPEN |
| Q6 | Canva asset kit — specific templates needed and what goes in each | OPEN |
| Q7 | In-game era pack merchandising / store layout | OPEN |
| Q-mon1 | Monetization redesign — ownership-vs-access (resolved as conditional ownership model) | CAPTURED |
| Q-mon2 | Entry fee path — resolved as no entry fee | CAPTURED |
| Q-mon3 | Hallmark era selection for 20-era launch catalog | OPEN |
| Q-mon4 | 5-era subscription starter bundle selection | OPEN |
| Q-mon5 | Roman free tier scope limitations | OPEN |
| Q-mon6 | Third hallmark era for multi-stage tutorial | OPEN |
| Q-mon7 | Tutorial sub-objective design — which moments from each hallmark | OPEN |
| Q-mon8 | Tech tree / branching progression topology (WoWS-style) | OPEN |

---

## Question Log

### Q1 — Shell Identity vs. Era Identity [CAPTURED]

**Resolved:** Gold (`#c9a84c` or nearby) is the **Westopoli studio / Ouroboros
Manifold brand color**. It owns the main menu, studio splash, logo, title
treatment, and Steam page meta-identity. Era accents stack on top of the
gold brand rather than replacing it.

Rationale (Westley's call): keep the existing main menu identity, take
advantage of gold's universal premium-value connotations, follow the
Nintendo/Fortnite/CoD model where the master brand is a fixed identity and
seasonal content riffs within it.

**Downstream effects:**
- Roman era loses its claim to gold. Needs a new warm accent color (→ Q1b).
- All future era accent colors must coexist with a gold brand frame.
  Constraint on era palette selection: no era can claim gold, and era
  accents should harmonize or contrast cleanly with gold rather than fight
  it. Cool-palette eras (Settled Reach teal, potential Antarctic or
  underwater eras) will need careful execution to avoid clashing with the
  warm shell.
- Bible edit applied to `bible_monetization.md` "UI Aesthetic — Terminal
  Meets Glass" section. Hub cross-check against `game_bible.md` pending.

---

### Q1b — Roman's New Accent Color [OPEN, deferred]

Roman needs a warm accent that is distinctly *not* gold. Candidates to
explore: deep bronze (`#8c6a3d`-ish), terracotta (`#b2573a`), oxblood
(`#6b2f2a`), Tyrian purple (`#66023c` — historically accurate for Roman
elite), warm rust (`#a0502a`).

Deferred until after Q2 (logo direction), because logo color exploration
may surface constraints or synergies that affect the choice.

---

### Q-wordmark — Custom Font for OUROBOROS MANIFOLD [CAPTURED]

**Resolved (Session 3):** **Option C — custom ligature / drawn
letterform.** The wordmark is a classical display serif base
(Trajan / Cinzel family) with the two **O** letterforms in OUROBOROS
replaced by closed-loop ouroboros serpent marks that visually echo
the central ouroboros of the master shield. The wordmark and the
shield share a motif, not merely a register — this is the pattern
that separates memorable game wordmarks (Skyrim, Mass Effect, Halo)
from forgettable ones, and it's what makes the wordmark part of the
brand identity rather than adjacent to it.

**Serpent-O abstraction level (load-bearing detail):** The
serpent-O's are rendered at the same level of abstraction as the
shield's central ouroboros — Greco-Roman classical closed loop with
a single Celtic/Norse knot crossing at the closure point. No literal
serpent detail: no eyes, no scales, no ornamental features beyond
the single knot. The failure mode to avoid is the serpent-O reading
as cartoon or cute rather than as an elegant mark. The abstraction
specification is the guardrail against that failure mode, and the
capture is explicit about it because the wordmark direction depends
entirely on execution landing at the right abstraction level.

**Production path:**
- **Stage 1** — Generate the base wordmark in Recraft V4's vector
  typography mode. Classical display serif, wide proportions, strong
  serifs, chiseled-capital stance. Expect to discard generations for
  spelling errors as well as aesthetic reasons — Recraft occasionally
  misspells or runs letters together on long strings, and "OUROBOROS
  MANIFOLD" is sixteen letters with a repeated-O pattern that can
  confuse typographic generation. Over-generate.
- **Stage 2a** — Generate standalone abstracted ouroboros serpent
  loop marks in Recraft V4 (not part of the wordmark, generated as
  standalone symbols). Pick the one whose proportions and abstraction
  match the shield's central ouroboros. Composite into the two O
  positions in Inkscape via scale/placement.
- **Stage 2b fallback** — If Recraft cannot produce acceptably
  abstracted serpent loops (keeps giving cute/detailed serpents),
  hand-draw the serpent loops directly in Inkscape using the shield's
  central ouroboros as visual reference. Inkscape handles simple
  closed curves with one knot crossing natively.
- **Fallback-to-option-A clause** — If the custom ouroboros-O
  treatment cannot be landed cleanly via either 2a or 2b, the
  wordmark falls back to the base classical serif (Cinzel or
  equivalent licensing-clean display serif) with no custom
  modifications. This ensures the wordmark ships regardless of
  whether the custom ligature succeeds. Option A is the safety net
  under option C.

**Scale requirement:** The wordmark must remain legible down to
Steam capsule size. The custom serpent-O's must remain recognizable
as closed loops even when fine details drop out — at small scales
the knot crossing may disappear but the closed-loop silhouette must
survive. This is why closed-loop serpent abstraction is preferred
over serpents with elaborated detail: closed loops scale, detailed
serpents do not. At sizes where even the closed-loop reading breaks
down (favicons, avatars), the shield drops in as the primary mark
and the wordmark is omitted entirely.

**Why Recraft V4 is actually well-suited for this task:** Recraft's
dedicated typography mode generates text as real editable vector
paths (not raster approximations of text), meaning Inkscape can
directly manipulate the output. For a custom-ligature wordmark this
is the ideal pipeline — generate the base, modify two letters, done.
The wordmark is *less* production-risky than the master shield
because classical display serifs are easier for Recraft than ornate
heraldic metalwork. The master shield is the hard test; the wordmark
is the warmup.

**In-game font system is not affected.** The bible's two-font
in-game system (JetBrains Mono for data, Newsreader for narrative)
is a separate concern. The wordmark is a *branding* element that
sits outside that system. A third font for the wordmark is already
documented in the bible as an explicit permitted exception.

**Bible capture target:** `bible_monetization.md` Brand Logo System
subsection. DONE this session:
- New "Wordmark — OUROBOROS MANIFOLD typographic treatment" paragraph
  inserted after the Ornamentation Density paragraph, documenting
  custom-ligature approach, serpent-O abstraction level, and
  classical-serif base register.
- New "Wordmark production path" paragraph documenting Stage 1 /
  Stage 2a / Stage 2b / fallback-to-option-A clause.
- New "Wordmark scale requirement" paragraph documenting Steam
  capsule legibility constraint and the closed-loop-over-detail
  rationale.
- New "Wordmark production test flag (low)" paragraph documenting
  the spelling-error quirk on long strings and positioning the
  wordmark as a confidence-builder test before the harder material
  tests.

**Downstream effects:**
- Added to the production test list for the first Recraft month as
  a low-risk test. Full list now:
  1. Master shield — ornate metalwork in vector (hard)
  2. Roman variant — travertine marble in vector (hard)
  3. 1980s variant — canvas weave and stitching in vector (hard)
  4. Settled Reach variant — titanium iridescence in vector (moderate)
  5. Wordmark stage 1 — classical display serif generation (low)
  6. Wordmark stage 2a — abstracted ouroboros serpent mark (low)
- The wordmark production test should be run *first* in the Recraft
  month as a confidence-builder before attempting the harder material
  tests.

---

### Q2 — Logo System [ANSWERED, capture pending]

**Resolved (Session 1):** Master logo is a **four-quarter heraldic
shield with a central ouroboros**, rendered in the register of ornate
metalwork (silver/pewter/bronze) with dense foliate borders — the
aesthetic target is an "ancient artifact" feel rather than an
illustration. Reference image shared by Westley in Session 1 shows the
exact intensity and craft level intended: see
`visual_identity_reference_shield.png` if preserved, or note that the
reference was a silver-pewter ornate shield with rampant creatures
flanking a central charge, foliate scrollwork borders, and decorative
finials.

**Quarter content (Q2c deferred):** The four quarters represent "phases
of humanity" (early → mid → future → super-future). Depictions are
**esoteric, abstract, and open to interpretation** — stylized symbolic
forms, not literal illustrations. A viewer should feel "ancient and
meaningful" without being able to point at a quarter and name specific
imagery. This protects the era-agnostic thesis by letting the quarters
read multiple ways to different viewers.

**Era-agnostic exception granted.** Westley explicitly permitted the
master logo to be "slightly era-nostic" — i.e., to carry a mild
humanist / linear-progression framing even though Sacred Principle #3
governs the engine and content systems as era-agnostic. The carve-out
is that the logo represents Ouroboros Manifold as a product (made by
humans, marketed to humans) at a meta-layer above the engine. The
engine, simulation, content generators, and in-game systems remain
strictly era-agnostic per Sacred Principle #3. Only the master brand
logo carries this carve-out. This exception must be documented
explicitly in the bible to prevent future drift.

**Q2b resolved — B+++ hybrid approach:**
- Master logo: four-quarter shield + central ouroboros + ornate
  heraldic metalwork frame (fixed, invariant across all era variants).
- Era variants in the launch wave (Roman, Settled Reach, 1980s): modify
  only the **frame ornamentation and color treatment** around the
  master shield. Do not redraw the quarters. This is the
  Assassin's Creed model applied to the existing shield — low per-era
  effort, preserves the central brand mark.
- Future marquee releases (post-launch, revenue permitting): have the
  *option* to go full B++ — redrawing the four quarters in
  era-specific imagery for a premium marketing moment. This path is
  reserved as a future production option, not a launch commitment.

**Production path (pending Q-tools research):** The master shield is
the single highest-stakes visual asset in the game's brand. Its
production path (AI generative tool, freelance commission, or hybrid)
is a real decision that needs evidence. Q-tools research must complete
before committing to a production approach, and Q-commission decision
follows Q-tools.

**Downstream open questions from Q2:**
- Q2c — **CAPTURED.** Four phase labels: **Genesis / Imperium /
  Crepusculum / Aurora** (Latin, heraldic tradition). Tells an imperial
  arc — birth, rule, decline, rebirth — that loops back on itself
  (Aurora feeds Genesis). Labels do not necessarily appear as visible
  text on the shield; they are the canonical names for marketing copy,
  press, codex entries, internal docs. Captured in
  `bible_monetization.md` Brand Logo System subsection.
- Q2d — **CAPTURED.** Central ouroboros style: Greco-Roman form with
  Celtic/Norse compositional accent. Classical serpentine proportions
  and naturalistic-but-stylized form (Greco-Roman base), but the body
  weaves once or twice over itself before completing the bite, with
  knot work anchoring the head-and-tail closure point (Northern
  interlace accent). Reads as classical at first glance, reveals
  interlaced complexity on closer inspection. Pairs the Mediterranean
  register of the Latin quarter labels with the ornamental density of
  the shield borders. At small icon scale the interlace partially
  drops out, leaving a clean classical serpent loop. Both readings
  must be consistent. Captured in `bible_monetization.md` Brand Logo
  System subsection.
- Q2e — For era variants (frame/color modifications), what specific
  dimensions vary? Frame material (bronze for Roman, olive-drab patch
  for 1980s, brushed steel for Settled Reach)? Border motif (laurel,
  stencil, circuit)? Inner metal color? Background texture?

### Q2 — Archived framing (Session 1)

Original four-option framing (A fixed silhouette / B fixed central
symbol / C fixed wordmark + badge / D modular system) served as the
anchor for the brainstorming. Westley's answer hybridized B and D with
a four-quarter shield. Archived here for reference in case future
revisits want the full option landscape.

---

### Q2e-Roman — Roman Era Frame Treatment & Accent Color [CAPTURED]

**Resolved (Session 2):**

- **Frame material:** **carved travertine marble**, rendered as low-relief
  architectural carving rather than metalwork. The creamy off-white
  stone of Roman public architecture (Colosseum, Forum, temple
  pediments).
- **Border motif:** classical architectural ornament — egg-and-dart,
  meander / Greek key, or similar — replacing the metalwork scrollwork
  of the master shield. Exact motif finalized at generation time in
  Recraft.
- **Accent color:** **oxblood**, approximately `#6b2a2a`. The deep
  desaturated red of Pompeian frescoes, Roman military leather, and
  red ochre pigment. Chosen over Tyrian purple (temperature clash
  with gold) and terracotta (too close to the brand gold's warmth to
  read as distinct).
- **Positioning:** Roman is the *civic monument* era — the civilization
  that built things meant to outlast it. This reframes Roman away from
  the generic "bronze-and-laurel military conqueror" register that
  most strategy games reach for by default.

**General rule surfaced and captured:** The Roman decision established
a **material-per-era principle** that applies to the entire era
variant catalog. Each era picks a frame material appropriate to its
own register — not just a different color or motif applied to the
same metal substrate, but a genuinely different material that says
something about what that era *is*. The master shield's
ancient-artifact metalwork anchors the brand; era variants are
rendered as if the same shield were re-cast or re-carved in the
material voice of a specific civilization's moment. This is a
binding principle for all future era variant work. For non-obvious
eras (far-future, heavily abstract), the material choice is made by
asking *"what material would this civilization have considered
permanent, valuable, or ceremonial?"*

**Bible capture target:** `bible_monetization.md` Brand Logo System
subsection. DONE this session:
- New "Material-per-era principle" paragraph inserted after the
  Era Variants paragraph.
- New "Roman era variant" paragraph documenting marble + architectural
  ornament + oxblood, replacing the prior bronze/laurel sketch.
- UI Aesthetic section's Era-owned accent colors bullet updated:
  Roman's accent color resolved from "TBD — candidates include..." to
  `#6b2a2a` with rationale.
- Placeholder paragraphs added for 1980s and Settled Reach era
  variants noting the material-per-era principle and likely
  material registers, with explicit "TBD in next visual identity
  session" markers.

**Downstream effects:**
- Q1b resolved in the same edit. No longer a separate open question.
- Q2e-1980s and Q2e-Settled-Reach now exist as separate open questions
  in the roadmap, each of which applies the material-per-era rule
  within its own material register.
- **Production test for Recraft:** The marble material choice is the
  hardest thing we've asked Recraft to do so far (vector doesn't
  render stone micro-texture natively). First production run should
  test marble rendering early on the $10 first month — if Recraft
  can't hit the marble register acceptably, this is the first real
  test of the Path 2 escalation from Q-tools (cheap freelance touchup
  on a Recraft base).

---

### Q2e-1980s — 1980s Era Frame Treatment & Accent Color [CAPTURED]

**Resolved (Session 2):**

- **Frame material:** **heavy military canvas / cotton duck**, the
  coarse-weave fabric of Cold War field packs, combat uniforms, and
  equipment covers. Rendered as if the shield were stitched onto or
  patched into a piece of issued kit — visible weave, stitched edges,
  slight wear.
- **Border motif:** **stenciled military equipment markings** —
  serial numbers, unit designations, hazard diamonds, arrow-and-T
  inventory marks, classification bars. The frame reads as property
  of the state.
- **Accent color:** **olive drab**, approximately `#5a5f3a`. US Army
  OD from the Cold War era. Warm enough to harmonize with the gold
  brand frame (warm-on-warm). Chosen over amber (too close to the
  existing terminal-aesthetic UI palette, risk of collapsing into the
  game's base UI voice) and signal red (color collision with the
  semantic red in the UI palette, harder color pairing with gold).
- **Positioning:** The 1980s is the *Cold War geopolitical chessboard*
  era per the bible's framing — proxy wars, intelligence, classified
  operations. This choice leans into that register and deliberately
  rejects the consumer/pop 1980s (MTV, neon, malls). The 1980s is
  *classified equipment and field gear*, not *Miami Vice*.
- **Material-dissonance note:** The canvas-over-metal register has the
  strongest material dissonance with the master shield's ornate
  metalwork of any era variant so far. This is intentional and
  consistent with the material-per-era principle: each era's material
  is what *that civilization* considered significant, not what the
  brand considers significant. The dissonance is managed by keeping
  the shield quarters and central ouroboros visually dominant — the
  canvas and stencils are a frame treatment around the master mark,
  not a replacement of it. Captured in the bible paragraph.

**Production note for Recraft:** Canvas weave texture and stitched
edges are the specific vector-rendering challenges here. Canvas is
a texture-heavy material, which vector handles less gracefully than
flat metalwork. Worth a focused test generation early in the $10
first month alongside the Roman marble test — both are material
registers that exercise Recraft's ability to render non-flat
surfaces in vector.

**Bible capture target:** `bible_monetization.md` Brand Logo System
subsection. DONE this session:
- "1980s era variant" paragraph replaced the TBD placeholder with
  full canvas / stenciled motif / olive drab resolution.
- UI Aesthetic accent colors bullet updated: 1980s resolved from
  "military olive or amber (TBD)" to `#5a5f3a` with rationale.

**Downstream effects:**
- Q2e-Settled-Reach is now the last remaining Q2e question. Settled
  Reach will need a material that is neither ancient (Roman's marble)
  nor mid-20th-century utility (1980s canvas) — the obvious path is
  the near-future register of brushed steel, dark chrome, or glass.

---

### Q2e-SR — Settled Reach Era Frame Treatment & Accent Color [CAPTURED]

**Resolved (Session 3):**

- **Frame material:** **brushed titanium**, rendered with directional
  grain and the faint warm-cool iridescence real titanium develops as
  it oxidizes. Chosen over brushed stainless (too generic), dark
  anodized aluminum (dark-frame specular highlights are a harder
  vector render and saturated teal accent fought gold), and optical
  glass (serious Path 2/3 production risk, catastrophic failure mode
  if iridescence missed). Titanium is the aerospace metal — on
  civilizational register in a way stainless isn't.
- **Border motif:** **engraved orbital mechanics** — fine-line
  inscribed diagrams of orbital paths, Lagrange point notation,
  delta-v calculations, trajectory geometry. The ornament tradition
  of a civilization that permanently records mathematics onto its
  ceremonial surfaces. This is the civilizational-register analog
  to Roman's egg-and-dart / meander (architectural ornament on civic
  marble) — engineering inscriptions on aerospace metal.
- **Accent color:** `#446e7e`, cool steel blue shifted slightly
  toward teal to pick up the titanium frame's natural oxidation tint.
  Desaturated enough to coexist with the warm gold master brand frame
  per the Q1 cool-palette-coexistence constraint, while carrying
  enough chroma to read as a distinct era identity rather than as
  neutral steel.
- **Positioning:** Settled Reach is *the civilization whose sacred
  inscriptions are engineering* — not generic sci-fi. The specific
  register is aerospace precision as ornament tradition. The master
  shield's heraldic metalwork is reframed as titanium; the foliate
  scrollwork is replaced by engraved math.

**Cool-palette-vs-gold pattern surfaced:** Q1 flagged cool-palette
eras as the hard case for coexistence with the warm gold brand frame.
Settled Reach resolved this by *desaturation plus teal-shift*, not
chromatic opposition — the accent reads as cool but carries enough
warmth from the teal shift to sit beside gold without fighting it.
This is now a working pattern for future cool-palette era additions
(Antarctic, underwater, any future space-themed release).

**Production test flag (moderate):** Titanium iridescence is a new
material property to exercise Recraft V4 on. The subtle warm-cool
specular shift is something vector rendering tends to flatten. First
production run should generate a plain brushed-stainless variant
side-by-side with a titanium variant to verify the oxidation tint is
rendering. Fallback reading is "brushed steel," which remains an
acceptable baseline — no catastrophic failure mode, unlike glass or
dark-anodized picks would have carried. This adds a fourth item to
the production test list alongside the three hard material tests
(master metalwork, Roman marble, 1980s canvas).

**Bible capture target:** `bible_monetization.md` Brand Logo System
subsection. DONE this session:
- "Settled Reach era variant" paragraph replaced the TBD placeholder
  with full titanium / engraved orbital mechanics / `#446e7e`
  resolution, including the civilizational-register framing and the
  production test flag.
- UI Aesthetic Era-owned accent colors bullet updated: Settled Reach
  resolved from "cool blue-teal (TBD)" to `#446e7e` with rationale.

**Downstream effects:**
- All Q2e era variant work is complete for the launch wave. Roman
  (marble + oxblood), 1980s (canvas + olive drab), and Settled Reach
  (titanium + cool steel blue) all captured. No Q2e questions remain.
- The cool-palette-coexistence pattern from Q1 now has a working
  implementation — future cool-palette eras can reference this
  resolution rather than re-litigating the constraint.

---

### Q-tools — AI Generative Tools for Logo Production [CAPTURED]

**Resolved (Session 2):** **Recraft V4** is the primary AI image tool
for the entire visual identity pipeline — master logo, era logo
variants, era card template art, Steam marketing assets, and any
in-game decorative art generated via AI. Basic plan at $10/month with
commercial licensing. Escalation path: if Recraft cannot hit the
bible's "ancient artifact / ornate metalwork" target for the master
shield specifically, the master gets a cheap freelance touchup
(~$50–$150 on Fiverr/Dribbble, refinement-not-invention brief) rather
than a full commission. Era logo variants are deliberately less
ornate than the master per Westley's constraint — only the master
shield needs the full "dense heraldic metalwork" register, which
collapses the scalability-vs-ornament tension that initially
complicated this question.

**April 2026 landscape snapshot (for future reference):**
- **Recraft V4** — #1 on HuggingFace logo benchmarks. Native SVG
  output (true editable Bezier paths, not raster-wrapped SVG). Brand
  style upload (lock a reference image, every subsequent generation
  inherits visual DNA). Custom RGB palette enforcement per
  generation. $10/mo Basic includes commercial license. Built with
  designers for commercial work — no lawsuit exposure.
- **Midjourney V7/V8** — aesthetic ceiling leader, rendered metalwork
  champion, but raster-only, no official API, and active copyright
  lawsuits from Disney/Universal/Warner Bros. Real commercial risk
  flag for a Steam product.
- **Nano Banana Pro** (Google Gemini 3 Pro Image) — only tool in 2026
  that solved identity consistency across a series without
  fine-tuning. Raster only. Strong fallback if Recraft's consistency
  isn't tight enough in practice.
- **GPT Image 1.5** — prompt-understanding and text-rendering leader.
  Raster. Useful if text elements need to render inside artwork.

**Rationale for Recraft over alternatives:**
1. **Vector output is the single biggest practical advantage** for a
   game dev pipeline. SVG scales from favicon to billboard, edits
   cleanly in Inkscape, imports into Godot and Canva without
   resolution concerns, survives every downstream format conversion.
2. **Brand-style reference upload** mechanically enforces series
   consistency across era variants. Upload the master shield once,
   every subsequent era logo inherits its visual family.
3. **Palette constraint injection** mechanically enforces the
   gold-brand + era-accent coexistence rule from Q1 capture. No
   manual color correction needed.
4. **Commercial licensing clean** — no training-data lawsuit
   exposure, which matters for a paid Steam product.
5. **Within realistic indie budget** ($10/mo, cancelable, keep what
   you generated).

**Escalation tree (when to go beyond Recraft alone):**
- Path 1 — **Recraft V4 alone, self-polish in Inkscape.** First
  attempt. Iterate cheaply until a candidate is close enough; clean
  up paths, tighten composition, add metalwork bevel manually in
  Inkscape if needed. Realistic outcome: 70–90% of the way to the
  bible target for ~$10 and a few hours.
- Path 2 — **Recraft V4 → cheap freelance touchup (~$50–$150).** If
  path 1 plateaus below the bible target, hand the best Recraft SVG
  candidate to a Fiverr/Dribbble illustrator with a
  refinement-not-invention brief ("add foliate metalwork border
  detail, preserve quarter composition and ouroboros center, render
  to silver/pewter finish, deliver as SVG"). Dramatically cheaper
  than from-scratch commission because the illustrator has a concrete
  starting point. Final SVG becomes the Recraft brand-style anchor
  that feeds all downstream generations.
- Path 3 (fallback, not pre-committed) — **Midjourney/Nano Banana Pro
  one-month render → human vectorize → Recraft reference.** Only if
  paths 1 and 2 both fail to hit the bible target. Buy one month of
  Midjourney or Nano Banana Pro, generate a photoreal ornate master,
  cancel, hand the raster to a vectorization freelancer. Flagged here
  so the fallback exists on paper, not as an active plan.

**Downstream effects:**
- Q-commission is **moot** — answered by the Option A+ escalation
  path. The master is not pre-commissioned; it's self-produced via
  Recraft with an optional cheap touchup if needed. A full
  $200–$500 commission is not on the path.
- All future visual identity questions (Q2e era frame variants,
  Q3 era card template, Q6 Canva asset kit) should assume Recraft
  V4 SVG as the production substrate.
- Era logo variants per Westley's Session 2 clarification can be
  **significantly less ornate than the master** — only the master
  shield carries the full heraldic metalwork density. This is a
  constraint on Q2e and should be documented in the bible's Brand
  Logo System subsection.

**Bible capture target:** `bible_monetization.md` Brand Logo System
subsection gets a new note on (a) era variant ornamentation density
being lower than the master, and (b) the production pipeline being
Recraft-V4-based. The specific tool name in the bible is a
borderline call — tools change, the bible is append-only. Leaning
toward documenting the *principle* ("vector-first AI generation with
brand-style reference locking") rather than the specific tool name,
so the bible doesn't rot if Recraft is superseded. Flagging this as
a capture-detail question to confirm with Westley before writing
the bible edit.

---

### Q-commission — Commission vs. Self-Produce the Master Logo [CAPTURED]

**Resolved (Session 2):** **Moot — answered by Q-tools Option A+.**
The master logo is self-produced via Recraft V4, with a cheap
freelance *touchup* (~$50–$150) as the escalation path if needed. A
full from-scratch commission ($200–$500) is not on the path. The
distinction is meaningful: touchup means paying an illustrator to
refine a generated starting point, which is dramatically cheaper
and faster than paying for invention from scratch, and it
de-risks the "locked aesthetic before playtesting" concern because
the starting point is cheap to regenerate if direction shifts.

No bible edit needed — this question resolved internally within the
production pipeline decision captured under Q-tools.

---

### Q3 — Era Card Template [OPEN]

**Open framing (from Session 1):** What goes on the reusable visual unit
that sells an era? Westley's initial candidates, in his words:
*"Some art of a unit? A logo? A map?"* — plus other possibilities worth
exploring: composition/moodboard, chronicle excerpt, simulation
screenshot, character portrait, faction crest, era-specific environment
shot. Westley explicitly flagged this as needing research into what
actually converts for single-player strategy DLC — he wants
evidence-based answers, not speculation.

---

### Q4 — Steam Page Hierarchy [OPEN]

**Open framing:** Capsule art, header, screenshot order, trailer
structure, feature list hierarchy, DLC page design. Requires research
pass on what converts in the strategy genre specifically.

---

### Q5 — Research Pass — Reference Studios [OPEN]

**Targets to research:**
- Paradox Interactive (DLC-driven long-tail strategy game marketing)
- Creative Assembly / Total War (historical + fantasy era variety)
- Supergiant (single-player narrative premium indie presentation)
- Hazelight (single-player distinctive visual identity)
- Hades 1 & 2 (indie strategy-adjacent with strong brand)
- Stellaris specifically (closest competitive neighbor per bible)
- Fortnite/CoD seasonal model (master brand + chapter variants — relevant
  to the B decision on Q1)

Research output: a synthesis doc summarizing what each reference does,
what's reusable for Ouroboros Manifold, and what's not.

---

### Q6 — Canva Asset Kit [OPEN]

**Open framing:** Downstream of everything above. Once visual system is
decided, spec out the specific Canva templates needed: logo variants,
era card template, Steam capsule, social post templates, Discord assets,
trailer thumbnails. Each template's purpose, dimensions, and content
slots.

---

### Q7 — In-Game Era Pack Merchandising / Store Layout [OPEN]

**Open framing (surfaced Session 2):** Westley flagged that the
in-game layout/branding strategy for selling era packs is
unresearched. How are era packs presented inside the game itself —
within the Era Library, on an in-game store page, in the main menu?
What visual language sells an era pack to a player who is already
in the game? How does it relate to (but not duplicate) the Steam
page presentation?

**Scheduled downstream of Q3 and Q4** because the in-game store
layout *consumes* the visual assets established by the era card
template (Q3) and the Steam page hierarchy (Q4). The in-game store
should reuse or echo the era card vocabulary rather than invent a
third visual register. Research targets likely include: Paradox
in-game DLC storefronts, Total War's historical pack presentation,
Deep Rock Galactic's season/cosmetic merchandising, and whatever
patterns work in single-player strategy games specifically.

---

## Anti-pattern watchlist

Things to avoid in this brainstorming effort (from `design_rules.md`):

- Making design decisions without surfacing them to Westley
- Batching questions before an answer lands
- Letting answers live only in chat (every ANSWERED must become CAPTURED)
- Sliding into implementation (no code, no actual Canva design work —
  just decisions about what to build)
- Silently re-opening captured decisions
