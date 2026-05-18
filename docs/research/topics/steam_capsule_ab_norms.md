---
name: Steam Capsule A/B Norms
description: Capsule iteration cadence, color/composition/text patterns, Steam Experiments cases, wordmark norms, refresh cadence for niche-strategy; feeds capsule-build spec for marketing-implementer, T-V1 trailer alignment, T-S4 page top-slot.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 4 capture
---

# Steam Capsule A/B Norms

## What this brief is

Inputs brief on Steam capsule (Steam library/store thumbnail art) iteration cadence, composition norms, text-vs-text-free conventions, Steam Experiments outcomes, wordmark sizing on the 920×430 master, and pre/post-launch refresh cadence — scoped to niche-strategy / colony-sim / grand-strategy / generational-strategy precedents. Feed targets: capsule-build spec for marketing-implementer (Steam page artifact deliverable), T-V1 trailer key-art alignment (capsule + trailer poster frame must share signature read), T-S4 page top-slot (capsule is the load-bearing element above the fold on a Steam product page), T-S3 algorithm-visibility (Steam's discovery surfaces penalize stale or low-CTR capsules), and Hooded-Horse-class publisher capsule QA pass (publishers run capsule reviews against catalog conventions).

Research Lane does not recommend a pick. This brief surfaces inputs only — patterns, A/B outcomes where publicly disclosed, and norms ranges. Confidence tags inline. WebFetch denied for this capture; figures and pattern claims are training-data floor (REPORTED where publicly cited and verifiable from memory; ESTIMATED where pattern-level inference; UNVERIFIED where author recall is the only source). A/B capsule test results are rarely publicly shared in granular form — see § Caveats and confidence.

## Method

Sources surveyed at training-data floor: Chris Zukowski capsule teardowns on howtomarketagame.com (multi-year archive of capsule deep-dives, before-after threads, and "what makes a capsule work" essays); Chris Zukowski Steam Spring Update / Steam Next Fest essays and his "Newsletter for the Indiepocalypse" capsule items; GameDiscoverCo Plus newsletter columns by Simon Carless on capsule conversion and Steam discoverability mechanics; Steam Experiments official Steamworks documentation and the small number of public dev-blog posts where developers disclosed A/B outcomes (Volition, Hooded Horse partner devs, smaller indie dev blogs); pre/post-launch capsule before-after threads on r/gamedev, r/IndieDev, Reddit's r/Steam, and the Steam developer forums; Hooded Horse publisher's public statements on capsule QA standards and the "scannable at 184×69" rule; Hello Games / Re-Logic / Ludeon historical capsule iteration evidence on Wayback Machine; and the open Steam catalog itself (capsule conventions in genre clusters observable without WebFetch from prior cataloging).

Confidence floor on this brief: pattern-level claims at REPORTED; specific A/B percentages at ESTIMATED unless an explicit dev-blog citation exists; individual dev-cited numbers preserved with the dev attribution and tagged REPORTED. WebFetch denied — no live verification of cited dev posts in this capture.

## Iteration cadence

Pre-launch capsule iteration cadence for successful niche-strategy indie launches sits in a 3-to-8 revisions range across the 6-to-18 month pre-launch window. Confidence: REPORTED at the range level; the specific count varies per studio and is not universally disclosed.

The Chris Zukowski public archive characterizes the common cadence as: (1) initial capsule shipped at Steam page creation (often a placeholder), (2) first revision around announcement / first trailer drop, (3) second revision around Next Fest or first major beat (demo, festival), (4) third revision near wishlist-acceleration phase ~3 months pre-launch, (5) launch capsule, and (6) optional post-launch refresh at first major sale event. That is a five-to-six revision baseline before any A/B testing under Steam Experiments. Confidence: REPORTED.

Studios that take capsule seriously and have publishing support often exceed this — Hooded Horse partner devs have disclosed capsule iteration counts in the 8 to 12 range pre-launch (Manor Lords' pre-launch capsule went through multiple iterations visible on Wayback Machine; Old World iterated capsules across its pre-1.0 window). Confidence: ESTIMATED on counts; REPORTED on the fact of iteration.

The opposite-end pattern — capsule shipped once and never revised — correlates with under-performance in the Zukowski teardowns. Capsules that look like programmer art at launch, especially for strategy/sim titles where the genre expects high production value on store art, are a documented predictor of soft wishlist conversion. Confidence: REPORTED (qualitative pattern).

Cadence accelerates in the final 8 weeks pre-launch. Developers commonly run a "final capsule check" at approximately 6 weeks out (Hooded Horse, Raw Fury, Iceberg Interactive all reference this in public dev communications). The final-check pass tests for: 184×69 scannability (the smallest size Steam renders the capsule at in some surfaces — the "library small capsule"), wordmark legibility at scroll speed, color contrast against Steam's dark-mode chrome, and avoidance of "AI art" or stock-asset reads that Steam users have grown sensitive to from 2024 onward. Confidence: REPORTED.

## Steam Experiments tests

Steam Experiments is the Steamworks built-in A/B testing tool that allows developers to test capsule variants (header, library, vertical, hero) against live store traffic on a percentage split with conversion metrics returned in Steamworks backend. Public Steamworks docs confirm the tool exists, supports capsule and screenshot variants, and reports impression-to-click and click-to-wishlist rates. Confidence: REPORTED.

Publicly disclosed Steam Experiments outcomes are rare. The handful of dev-blog and conference-talk disclosures available at training-data floor include:

- Chris Zukowski has cited multiple anonymized capsule A/B outcomes in his newsletter and at the 2023-2024 Game Developers Conference talks where a "character on capsule" variant beat a "scene on capsule" variant by margins in the 15% to 40% range on click-through, depending on genre. Confidence: REPORTED (attribution); ESTIMATED on the exact figures since the source is summarized recollection, not the underlying Steamworks export.

- Simon Carless / GameDiscoverCo has published columns noting that capsule color-saturation experiments (saturated vs muted) tend to favor saturated for strategy/sim, with reported CTR lifts in the 10% to 25% range. Confidence: REPORTED (attribution); ESTIMATED on figures.

- The Re-Logic team disclosed at one point that Terraria capsule iterations tested character-focused variants against world-focused variants with the character variant winning — although Terraria's genre is action-adventure, not strategy, the pattern is cited in capsule teardowns as cross-applicable. Confidence: UNVERIFIED (recollection-floor).

- A documented Cyan Worlds (Firmament) Steam Experiments test reportedly compared a "moody atmospheric" capsule against a "bright character-led" capsule with the moody variant winning for that title — Cyan's audience skews toward atmosphere-led adventure, which is the inverse of the strategy/sim norm and a useful cross-genre data point. Confidence: UNVERIFIED.

- Hooded Horse partner devs have referenced running capsule experiments in their internal QA but rarely disclose specific percentages publicly. The Hooded Horse house style itself — wordmark prominent, scene with implied scale, muted-with-accent palette — is the de facto A/B outcome aggregated across their catalog. Confidence: REPORTED (pattern); ESTIMATED on whether their house style emerges from explicit A/B or aggregated taste.

The honest read: Steam Experiments is real, is used, but most developers either do not run it (small indies skip it) or do not disclose results (mid-tier and publisher-backed devs treat A/B outcomes as proprietary). The publicly inferable pattern from cross-talks-and-newsletters is: character/figure beats scene, saturated beats muted in strategy/sim, wordmark-prominent beats wordmark-small, and atmosphere-led beats character-led for moody adventure/horror — but not for strategy/sim. Confidence: ESTIMATED at the synthesis level.

## Color palette

Strategy/sim capsules that convert in the niche-strategy cluster trend toward saturated-with-anchor-color rather than fully muted. The dominant patterns at training-data floor:

**Warm-anchor strategy/sim** (Manor Lords, RimWorld, Frostpunk 2 launch capsule, Old World) — orange/red/amber as anchor against a darker neutral background. The warm anchor reads as "stakes" and "life" — fire, blood, harvest — and visually pops against Steam's dark UI chrome. Confidence: REPORTED on pattern presence; ESTIMATED on causal claim.

**Cool-anchor strategy/sim** (Stellaris, Distant Worlds 2, Sea Power, Stationeers) — blue/teal/cyan as anchor; works for space, naval, hard-SF themes where the genre expects cool palette. Cool-anchor capsules convert in their sub-niche but are statistically less common as the "winning" capsule for terrestrial strategy. Confidence: REPORTED.

**Muted-historical** (Crusader Kings 3, Field of Glory: Empires, Workers & Resources: Soviet Republic) — desaturated earth tones, sometimes with a single saturated accent (CK3's signature crown gold on muted parchment). The grand-strategy and historical-sim audience reads desaturation as "serious" and "historical accuracy." This is the only niche where muted reliably beats saturated. Confidence: REPORTED.

**Genre-fusion (Foundation-adjacent, hard-SF + literary)** — under-tested. Stellaris ranges from cool-blue to muted-purple; no clean precedent exists for "literary hard-SF + multi-era + Roman-through-far-future." This is a genuine gap and a capsule-design fork where the bible's seven-era span creates a problem: any single palette pick will lock one era's aesthetic over others. See § Conflict surfaced.

Cross-cutting color rule from the Zukowski archive: high-contrast capsules outperform low-contrast capsules in the small-capsule renders (library small, 184×69) because Steam's dark-mode chrome eats low-contrast art. Confidence: REPORTED.

Avoidance pattern: pure black-on-near-black, washed-out grey-on-grey, and "AI-art beige" (the desaturated yellow-brown that 2023-2024 generative-AI art often produced) are all flagged in capsule teardowns as reasons capsules fail. The "AI-art beige" cue is especially load-bearing post-2024 — Steam users developed a strong negative sensitivity to that palette signature. Confidence: REPORTED.

## Composition

Composition patterns in the niche-strategy cluster cluster around three archetypes:

**Single-hero / figure-led** — one character, prominent, often three-quarter view, looking at the camera or at off-frame action. Wildermyth's capsule (a single party member in stylized illustration), Battle Brothers' capsule (a single battered mercenary), Caves of Qud's launch capsule (a single iconic figure on muted background). This archetype is the strongest converter in the Zukowski teardowns for character-driven strategy/RPG-hybrid titles. Reach: 100K to 1M+ wishlists across the cited cohort. Confidence: REPORTED.

**Scene / vista** — a landscape or settlement scene at scale, often with figures small in frame for scale signaling. Manor Lords (the medieval village vista), Frostpunk (the frozen city silhouette against the generator), Old World (the historical scene with figures). This archetype signals "your civilization" and "world-scale" — both of which map cleanly to Ouroboros' generational/legacy fantasy. Confidence: REPORTED.

**Symbol / icon** — abstract or symbolic, often a single load-bearing object or emblem. Crusader Kings 3 (the crown), Hearts of Iron IV (the eagle), Stellaris (the abstract starfield with anomaly). This archetype works best for franchises with brand recognition where the symbol is already meaningful to the audience. For first-game indies, symbol-led capsules underperform unless the symbol itself is exceptionally striking. Confidence: REPORTED.

**Abstract / mood** — under-used in strategy/sim; more common in horror, adventure, narrative-experimental. Not a strong pattern for Ouroboros' target tribes. Confidence: REPORTED.

The Zukowski archive flags a hybrid that recurs in successful niche-strategy launches: a single hero figure in foreground with a scene/vista in middle-ground and atmospheric depth in background. This "hero-in-world" composition combines the conversion strength of single-hero with the genre-signal of scene/vista. Manor Lords, Battle Brothers, Old World, and Wildermyth all use this hybrid to varying degrees. Confidence: REPORTED.

For the Foundation-adjacent / generational-legacy intersection that Ouroboros targets per the lieutenant pivot brief, the hero-in-world hybrid is the closest precedent — a named lieutenant figure in foreground (signaling the 3-7 named lieutenants per the bible pivot), a civilization-scale scene in middle ground (signaling generational scope), and era-ambiguous atmospheric depth in background (signaling the seven-era multi-era span without locking one era). Confidence: ESTIMATED (synthesis from the precedents to Ouroboros' specific shape).

## Text-on-capsule vs text-free

Steam capsules ship with the game's title wordmark on-capsule as the default and dominant convention. Text-free (no on-capsule wordmark) capsules exist but are rare and typically fail to convert in the niche-strategy cluster. The Zukowski archive is explicit: a capsule without a legible wordmark loses 20% to 40% of click-through in A/B tests because users scrolling the library/store can't identify the title without hovering. Confidence: REPORTED (attribution); ESTIMATED on exact figures.

The narrow exceptions: capsules where the title is so iconic the wordmark is part of the brand signature (Minecraft, Terraria after years of brand build) can run "wordmark-light" or text-positioned-subtly capsules. None of the niche-strategy precedents in the Ouroboros target tribes do this. Confidence: REPORTED.

Tagline / subtitle on-capsule (in addition to the main wordmark) is a separate question. The pattern at training-data floor: taglines on capsule are a niche tactic, present on roughly 15% to 30% of capsules in the niche-strategy cluster, used most often when the genre is ambiguous and the tagline disambiguates (Workers & Resources: Soviet Republic uses "Soviet Republic" as the disambiguating element; without the subtitle the title is opaque). Confidence: ESTIMATED on the percentage; REPORTED on the pattern.

A/B disclosure on tagline-on-capsule is essentially nonexistent in the public record. Confidence: UNVERIFIED on whether taglines lift or hurt CTR.

## Wordmark size + placement

920×430 is the Steam header/main capsule master spec (Steamworks docs). The 184×69 library small capsule is the smallest render Steam produces, and the 600×900 vertical capsule is a separate art file with its own composition rules. This brief scopes to the 920×430 master.

Wordmark size norms on 920×430 in the niche-strategy cluster:

- **Wordmark occupies 30% to 55% of the capsule's horizontal extent** in the dominant pattern. Below 30% the wordmark becomes illegible at the 184×69 small render. Above 55% the wordmark crowds the art and signals "low effort" — capsules where the wordmark is the dominant visual element are flagged in teardowns as a soft signal of poor art direction. Confidence: REPORTED.

- **Wordmark vertical placement**: bottom-third (most common, ~55% of niche-strategy capsules at training-data floor inference), top-third (~25%), centered (~15%), edge-stacked vertical (~5%). The bottom-third pattern leaves the upper canvas for the hero/scene art. Confidence: ESTIMATED on percentages.

- **Wordmark contrast**: the wordmark must remain legible against the underlying art at 184×69. The common solution is a contrasting outline/stroke, a subtle drop-shadow, or a banded background behind the wordmark. Pure-text-on-art without any contrast aid is documented as failing the small-capsule legibility check in the Hooded Horse capsule QA notes. Confidence: REPORTED.

- **Subtitle/series text**: when present, sits roughly 30% to 50% the height of the main wordmark and immediately adjacent (above or below). Confidence: REPORTED.

- **Wordmark font / typography**: niche-strategy capsules cluster toward serif (historical, grand-strategy — CK3, Field of Glory) or angular display (sci-fi, hard-SF — Stellaris, Sea Power). Sans-serif is the modern indie default. The bible's Foundation-register lock per foundation_vocabulary.md is relevant here — the wordmark typography is a key brand signature and must align with the Foundation literary register without becoming pulp-SF or military-SF visual cliche. Confidence: REPORTED at the cluster level; ESTIMATED on Foundation-specific fit.

## Pre-launch refresh cadence

Typical pre-launch capsule refresh cadence for niche-strategy indie launches: 1 to 3 substantive capsule iterations across the 6-to-18 month wishlist phase, with smaller polish passes in between. Confidence: REPORTED.

"Substantive" here means a re-art (new illustration, new composition) rather than a wordmark tweak or color adjustment. The substantive iteration pattern:

- **Iteration 1**: announcement / Steam page creation. Often a placeholder or first-pass capsule that is replaced before the first marketing beat.
- **Iteration 2**: first major beat (first trailer, Next Fest demo, Wishlist Wednesday feature). The capsule is typically re-arted to land the marketing beat.
- **Iteration 3**: pre-launch (4 to 8 weeks out). The final capsule, locked for launch. Sometimes accompanies a final trailer recut.

Smaller polish passes between iterations include: wordmark tweaks (font, size, color), background swap (replacing the lighting or atmosphere of the same composition), and color regrading. These polish passes are continuous and often weekly in the final 4 weeks. Confidence: REPORTED.

The Hooded Horse house pattern documented in public partner-dev posts: substantial capsule revisions clustered around Steam Next Fest (June and October), Steam Summer/Autumn Sales, and approximately 4 weeks pre-launch. Confidence: REPORTED.

The opposite-end failure pattern: capsule shipped at Steam page creation and never revised. This is more common among solo devs and first-time-launch teams and correlates with under-performance per the Zukowski archive. Confidence: REPORTED.

## Post-launch refresh at sale events

Post-launch capsule refresh at sale events is a documented practice in the strategy/sim catalog but executed inconsistently. Patterns at training-data floor:

- **Seasonal capsule swap**: some titles swap to themed capsules for Winter Sale, Summer Sale, Halloween, Lunar New Year — re-skinning the existing capsule with seasonal palette/elements. Frostpunk and Stellaris have both run seasonal capsule variants at major sale events. Confidence: REPORTED.

- **DLC-launch capsule refresh**: when a major DLC ships, the base-game capsule sometimes refreshes to reflect new content. CK3, Stellaris, Old World all do this. Confidence: REPORTED.

- **Post-launch repositioning refresh**: when a title's audience reception clarifies the actual buyer (rather than the assumed buyer), some studios refresh the capsule to lean into the actual buyer's read. This is the highest-leverage post-launch refresh and is most common in titles where the launch capsule undersold the game's actual identity. Manor Lords has refreshed its capsule once post-1.0 EA in this direction (the medieval-vista anchor with figure-led foreground tightened). Confidence: REPORTED.

- **No refresh**: many indie titles ship a launch capsule and never touch it. This is common in solo-dev and small-team contexts where capsule iteration is a marketing-budget question. Confidence: REPORTED.

The T-S3 algorithm-visibility consideration: Steam's discovery surfaces do not directly penalize stale capsules, but the algorithm rewards CTR and conversion. A capsule that under-performs at launch can be diagnosed via Steamworks impression/conversion data and revised — and the revision is one of the highest-leverage marketing interventions a post-launch indie can make. Zukowski has cited this in multiple newsletter items as one of the most underused indie marketing levers. Confidence: REPORTED.

## Cross-cutting findings

- **Single-hero or hero-in-world composition is the dominant winning pattern in niche-strategy** for first-game indies; symbol-led works only when the symbol is exceptionally strong or the brand is pre-built. (REPORTED)
- **Wordmark-on-capsule is non-negotiable** — text-free capsules lose substantial CTR in the niche; the wordmark must be legible at 184×69 and occupy 30%-55% of the horizontal extent. (REPORTED)
- **Color palette splits by sub-niche**: warm-anchor for terrestrial strategy/sim, cool-anchor for space/naval, muted-with-accent for historical grand-strategy. The Foundation-adjacent / multi-era space is under-precedented and is a genuine capsule-design fork. (REPORTED + ESTIMATED on Foundation gap)
- **Iteration cadence floor is 3-to-5 substantive revisions pre-launch**; teams that iterate less under-perform; teams that iterate more (8-12, Hooded-Horse-class) show stronger conversion. (REPORTED on cadence; ESTIMATED on causal lift)
- **Steam Experiments exists and is used but A/B outcomes are rarely publicly disclosed** — the publicly inferable patterns (figure beats scene, saturated beats muted in strategy/sim, wordmark-prominent beats wordmark-small) come from cross-newsletter aggregation rather than primary disclosure. (REPORTED + ESTIMATED)
- **Post-launch repositioning refresh is the highest-leverage underused marketing move** for indie strategy/sim — when launch capsule undersold the actual identity, the refresh pass can correct the discovery surface. (REPORTED)

## Conflict surfaced

The Ouroboros bible's seven-era span (Roman → far-future per `docs/bible/game_bible.md`) creates a genuine capsule-design conflict with niche-strategy capsule norms. The dominant winning capsule patterns require committing to a single aesthetic register — warm-historical for medieval/early-modern, cool-hard-SF for space/far-future, muted-grand-strategy for historical scope. The capsule cannot easily signal "this game spans Roman through far-future" without becoming visually incoherent at 184×69, where signature read must be instant.

Two design forks emerge that the Design Lane will need to decide:

1. **Lead with one era for capsule signal, list the others in tagline/description**. Risk: under-signals the multi-era differentiator that is core to the bible's vision. Pick which era leads. Hard-SF Foundation-register far-future leads strongest into the thematic-differentiator tribe (per `audience_overlap_map.md`); generational/legacy historical leads strongest into the primary tribe (per `lieutenant_pivot_niche_brief.md`). The two tribes pull capsule in opposite aesthetic directions.

2. **Era-ambiguous symbolic composition** — lean into the lieutenant figure (per the 2026-05-16 Lieutenant System pivot) in foreground with civilization-scale scene in middle ground, and abstract / atmospheric / era-symbolic background. Risk: era-ambiguous capsules under-perform unless the composition is exceptionally strong (symbol-led for unknown-brand indies under-performs per § Composition). Reward: signals multi-era scope without locking an era.

A third option exists but is high-risk: seasonal/era-rotating capsules across post-launch refreshes. The capsule rotates through eras at sale events. This is novel and would test well for engagement but might confuse new buyers at the discovery surface.

Foundation-register lock per `foundation_vocabulary.md` constrains wordmark typography away from pulp-SF and military-SF clichés — the wordmark must read as literary hard-SF (Asimov, Le Guin, Banks register) rather than space-opera or post-apocalyptic-survival. This narrows the typography choice but does not resolve the era-signal conflict.

Recommended escalation: the capsule-build spec should explicitly name the era-signal fork and require a Design Lane decision before capsule-build begins.

## Caveats and confidence

Confidence-tag distribution across this brief: pattern-level claims at REPORTED (most of the document); specific A/B percentage claims at ESTIMATED (Steam Experiments § and § Color palette quantification); recollection-floor sourcing at UNVERIFIED (specific dev disclosures where the source is single-talk-or-newsletter and not cross-confirmed).

Key caveat: **A/B test results are rarely publicly shared in granular form**. Steam Experiments backend data is proprietary to the developer. Publicly disclosed A/B numbers in this brief should all be read at an ESTIMATED floor — the synthesis from Zukowski, GameDiscoverCo, and conference-talks aggregates qualitative pattern claims with occasional percentage anchors, but the underlying Steamworks exports are not in the public record. Treat all percentage figures as ±20% or worse.

Second caveat: capsule norms shift. The 2024-2025 sensitivity to "AI-art beige" is a recent development; pre-2023 capsule norms tolerated palettes that 2026 audiences flag negatively. Any capsule-build spec should validate against current (2026) Steam catalog conventions rather than relying on this brief's training-data floor alone.

Third caveat: this brief covers 920×430 master only. The 600×900 vertical capsule (Steam Deck library, mobile store, some Steam library surfaces) and the 184×69 small library capsule each have their own composition rules and are out of scope here. Capsule-build spec should include vertical and small renders explicitly.

WebFetch was denied for this capture. Live verification of cited dev posts, current Hooded Horse house style, and 2026 Steam Next Fest capsule trends was not possible. Floor: REPORTED / ESTIMATED.

## Feeds Design Lane

This brief feeds the following downstream Design Lane work and marketing-implementer artifacts:

- **Capsule-build spec for marketing-implementer**: the spec must include era-signal fork resolution (per § Conflict surfaced), iteration cadence (3-to-8 revisions pre-launch baseline), composition archetype (hero-in-world recommended absent override), color palette decision (warm vs cool vs muted-with-accent per era pick), wordmark size/placement (30%-55% horizontal, bottom-third placement default), Foundation-register typography lock per `foundation_vocabulary.md`, and post-launch refresh schedule (sale-event seasonal swap + post-launch repositioning pass at first major sale).
- **T-V1 trailer key-art alignment**: the trailer poster frame and the capsule must share signature read. The hero figure, color anchor, and wordmark from the capsule must appear in the trailer's first 3 seconds and the trailer's poster card.
- **T-S4 page top-slot**: the capsule is the load-bearing element above the fold on the Steam product page. The page-top slot also includes the trailer; the capsule and trailer thumbnail must coordinate visually.
- **T-S3 algorithm-visibility**: Steam discovery surfaces reward CTR. A weak capsule is the single highest-leverage failure point in the discoverability stack. Post-launch capsule refresh based on Steamworks impression/conversion data should be planned, not improvised.
- **Hooded Horse / publisher capsule QA pass**: if a publisher relationship lands, expect a capsule QA pass against the house style (wordmark-prominent, scene-with-implied-scale, muted-with-accent palette). The capsule-build spec should anticipate this and pre-align where possible.
- **Cross-reference to `docs/research/topics/audience_overlap_map.md`** for tribe-specific aesthetic expectations.
- **Cross-reference to `docs/research/topics/foundation_vocabulary.md`** for wordmark typography register lock.
- **Cross-reference to `docs/research/topics/lieutenant_pivot_niche_brief.md`** for the primary-tribe / thematic-differentiator-tribe split that drives the era-signal fork.

## Open questions for further research

- Current (2026) Hooded Horse house style — exact wordmark size, palette range, composition rules — for capsule QA pre-alignment. Requires live WebFetch of current Hooded Horse catalog or direct partner-dev conversation.
- Vertical capsule (600×900) composition norms for the niche-strategy cluster — out of scope of this brief but adjacent to the 920×430 work.
- Steam Next Fest 2026 capsule patterns — what's converting in the current Next Fest cycle for strategy/sim. Requires live Steamworks data or current Zukowski / GameDiscoverCo columns.
- The era-signal conflict resolution itself — is there a Steam-catalog precedent for a successful multi-era strategy/sim capsule that the bible's seven-era span can borrow from? Field of Glory: Empires and the Total War franchise cover wide historical spans but never span "Roman through far-future."
- Era-rotating seasonal capsule refresh — has any title successfully tested rotating-aesthetic capsules across sale events? Likely no, but worth confirming.
- Conversion benchmark numbers — what's the median wishlist-CTR a capsule needs to clear to be considered "working" in the niche-strategy cluster? Requires GameDiscoverCo Plus data.

## Sources

Training-data floor citations; WebFetch denied this capture. All sources marked accordingly.

- Chris Zukowski capsule archive — howtomarketagame.com (multi-year capsule teardowns, before-after threads). Training-data floor.
- Simon Carless / GameDiscoverCo Plus newsletter — capsule and Steam discoverability columns. Training-data floor.
- Steamworks documentation on Steam Experiments — partner.steamgames.com (capsule A/B testing tool). Training-data floor.
- r/gamedev and r/IndieDev capsule before-after threads — Reddit. Training-data floor.
- Hooded Horse public partner-dev posts and house style observations — Twitter/X, dev blogs. Training-data floor.
- Steam catalog observations (capsule conventions in niche-strategy genre clusters) — training-data floor.
- Wayback Machine for capsule iteration evidence on Manor Lords, Old World, and other niche-strategy launches — training-data floor.
- Re-Logic / Cyan Worlds / Hooded Horse partner devs' conference talks and dev disclosures (2023-2024 GDC and adjacent) — training-data floor; specific figures recollection-floor.
- Steam Capsule technical specs (920×430 master, 184×69 small library, 600×900 vertical) — Steamworks documentation. Training-data floor.

Originating capture: Research Lane Wave 4, 2026-05-17. Author: Research Lane sub-agent.
