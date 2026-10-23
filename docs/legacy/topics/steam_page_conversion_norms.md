---
name: Steam Page Conversion Norms
description: Above-fold pitch length, trailer/screenshot top-slot, feature-bullet count, GIF/static delta, About length, below-fold read-rate, dev-page, localization conversion delta for niche-strategy; feeds T-S2 capsule, T-V1 trailer, T-V2 screenshots, T-L1 localization, T-W1 wishlist conv.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 4 capture
---

# Steam Page Conversion Norms

## What this brief is

Steam store-page layout + content conversion norms for niche-strategy titles in Ouroboros' primary tribe (CK3 / Wildermyth / RimWorld / Old World / Battle Brothers / Stellaris / Foundation-adjacent hard-SF) and thematic-differentiator audience. Covers: above-fold pitch word count, trailer-vs-screenshot top slot, feature-bullet count optimum, GIF-vs-static screenshot conversion delta, "About this game" length distribution, below-fold read-rate, developer/franchise-page role, localized-page conversion delta vs English-only.

Brief feeds: T-S2 capsule copy, T-V1 trailer spec, T-V2 screenshot spec, T-L1 localization slate, T-W1 wishlist-to-purchase conversion modeling, page-build spec for marketing-implementer.

**Does NOT recommend a pick.** Research Lane surfaces conversion-norm structure; Design Lane + Marketing Lane decide page composition. No "Ouroboros should use X layout" statements. Conflict section flags bible collisions only, doesn't resolve.

**Disclaimer.** Page-level conversion telemetry (capsule CTR, page-to-wishlist conversion, scroll depth, trailer-play-through, GIF-vs-static A/B deltas) is publisher-side data. Steam does not publish aggregated visitor-behavior dashboards for non-publishers. Valve's official conversion guidance (Steamworks documentation, GDC partner talks) is high-level, not granular per-element. All quantitative claims in this brief are REPORTED or ESTIMATED — derived from GameDiscoverCo public posts, Chris Zukowski's "How To Market A Game" blog + course material, Simon Carless's GameDiscoverCo newsletter, post-mortem GDC talks (Failbetter, Hooded Horse, Stunlock, 11 bit, Mode 7), niche-launch teardown threads (r/gamedev, How to Market a Game Discord public posts), and indie-marketer Twitter threads recalled from training data. Numbers should be treated as ±20-40% directional. VERIFIED is essentially absent in this brief.

## Method

Sources scanned (training-data floor, no live fetch):

- GameDiscoverCo (Simon Carless) newsletter archive — Steam discoverability + page-element analyses.
- Chris Zukowski "How To Market A Game" blog (howtomarketagame.com) — page-build guidance + capsule + screenshot teardowns.
- Steamworks documentation (partner.steamgames.com) — store-page best practices, asset specs.
- GDC vault post-mortems — Hooded Horse (Old World, Manor Lords, Falling Frontier), Failbetter Games, 11 bit (Frostpunk 2), Larian (Baldur's Gate 3), Klei (RimWorld-adjacent), Mode 7, Stunlock.
- Indie-marketer Twitter threads + r/gamedev post-mortems w/ page-conversion data (Tinybuild publisher-side posts, Raw Fury post-mortems, Hooded Horse public-facing performance figures).
- Niche-launch teardown threads (How to Market a Game Discord public threads, IndieDB post-mortems, dev-blog conversion-rate disclosures from solo devs).
- Steam page reference set: CK3 + Wildermyth + RimWorld + Old World + Battle Brothers + Stellaris + Songs of Syx + Workers & Resources + Sea Power + Nebulous + Manor Lords + Frostpunk 2 + Caves of Qud + HighFleet (training-recall, layout-pattern level).

**Exclusions:** No live Steam page fetch (WebFetch denied). No SteamDB pull. No 2026 conversion-rate refresh. No publisher-side dashboard access. No A/B test of competing capsules. No verbatim quote of any GameDiscoverCo paywalled report.

**Confidence calibration.** WebFetch denied → floor REPORTED. Page-level conversion data is publisher-side → ESTIMATED floor for any quantitative conversion-rate claim. VERIFIED reserved for Valve-published asset-spec numbers (image dimensions, char limits) recalled with high confidence. AMBIGUOUS where indie-marketer guidance contradicts publisher-side post-mortem data.

## Above-fold pitch length

Above-fold pitch = the visible text at top of Steam page when visitor lands: short description (limit 300 chars per Valve), tags (visible above-fold on most resolutions), and the first 1-2 sentences of "About this game" that may peek above the fold depending on viewport.

**Steam short description.** Valve caps at 300 characters. Niche-strategy successful pages cluster in 140-220 character range — long enough to land one concrete differentiator + one genre anchor, short enough to read in one breath. VERIFIED on the 300-char cap (Steamworks spec). REPORTED on the 140-220 cluster from teardown data.

Examples recalled from training (paraphrase, not verbatim):
- CK3: ~190 chars, leads w/ "Paradox grand strategy" + "your dynasty across centuries." REPORTED.
- Wildermyth: ~180 chars, leads w/ "character-driven, procedurally-generated tactical RPG" + "where the choices you make shape your heroes." REPORTED.
- RimWorld: ~210 chars, leads w/ "sci-fi colony sim driven by an intelligent AI storyteller." REPORTED.
- Battle Brothers: ~220 chars, leads w/ "turn-based tactical RPG" + "lead a mercenary company in a gritty, low-fantasy world." REPORTED.
- Old World: ~180 chars, leads w/ "historical 4X" + "ruling a dynasty through history." REPORTED.
- Stellaris: ~180 chars, leads w/ "explore a galaxy full of wonders" + "grand strategy." REPORTED.

**Word-count distribution across primary-tribe reference set:** ESTIMATED median ~28-35 words, range ~20-45 words. Below 20 words tends to under-pitch (no differentiator); above 45 risks truncation in some Steam UI placements (carousel hover, mobile). REPORTED.

**Chris Zukowski / GameDiscoverCo guidance pattern.** Multiple posts converge on: (1) lead with the genre anchor in the first 4-7 words so genre-shoppers recognize fit; (2) include one concrete noun that signals authorial differentiation ("dynasty," "permadeath," "decay," "psychohistory"); (3) avoid abstract value language ("immerse yourself in an epic journey"); (4) avoid front-loading the studio name. REPORTED, high-confidence pattern across multiple sources.

**Optimal word-count for niche-strategy: ESTIMATED 25-35 words / 150-200 characters.** Sits inside the observed primary-tribe cluster, leaves room for one differentiator-noun + one genre anchor + one micro-stake. AMBIGUOUS at the edges — 40-word pitches work for established-IP cases (Stellaris) where genre recognition is preloaded, but cold visitors to a no-IP page benefit from shorter copy.

**Above-fold extras.** Tags carry conversion weight as a secondary above-fold signal — visitors who don't read the short description scan tags to confirm genre fit. T-S1 tag slate work (cross-ref `docs/legacy/topics/audience_overlap_map.md` cluster-derived tag picks) is the second above-fold lever. REPORTED.

**Caveman summary.** 25-35 words. Genre anchor first 4-7 words. One concrete differentiator-noun. No filler. No studio name. ESTIMATED optimum.

## Trailer vs screenshot top slot

Steam's main media slot (top-left of the page) defaults to the trailer (video carousel item set as "highlight" or first asset). Below the trailer, screenshot carousel. Above the carousel is the capsule image + short description.

**Trailer-as-top-slot pattern.** Almost all primary-tribe successful pages place a 60-90 second trailer in the top slot. CK3, Wildermyth, RimWorld, Old World, Battle Brothers, Stellaris, Songs of Syx, Manor Lords, Frostpunk 2, Caves of Qud, Sea Power — all default to trailer top slot. REPORTED.

**Conversion delta — what GameDiscoverCo / How To Market A Game patterns claim.** Trailer-as-top-slot drives higher wishlist conversion than screenshot-as-top-slot when the trailer is good. Indie post-mortems (recalled from training) cluster around "trailer top slot increased wishlist conversion by 20-40% over screenshot-only" in A/B comparisons reported by solo devs and small studios. ESTIMATED — these are self-reported, low-sample, not Valve-aggregated. REPORTED floor on the direction (trailer > screenshot for top-slot conversion when trailer quality is acceptable). AMBIGUOUS on the magnitude.

**Counter-pattern.** When trailer is weak (low production value, no gameplay, vague mood reel), screenshot-as-top-slot can outperform — the trailer actively repels conversion. Zukowski's repeated guidance: "If your trailer doesn't show gameplay in the first 5 seconds, your trailer is hurting you." Several indie post-mortems confirm pulling a bad trailer and replacing w/ a screenshot top-slot increased wishlist rate. REPORTED. AMBIGUOUS magnitude — depends entirely on trailer quality.

**Niche-strategy trailer norms.** 60-90 second length. Open w/ a hook frame (UI, character, or system in motion). Show actual gameplay in seconds 0-10. Avoid logo-stings + "from the developer of X" intros (kill engagement). Include text overlays calling out the differentiator-noun the capsule used. Close on capsule logo + wishlist CTA. REPORTED, near-universal across teardowns.

**Top-slot recommendation defaults (lane-level, not for Ouroboros pick).** Default to trailer if trailer is at or above niche-tier production quality; default to screenshot top slot if trailer is weak; never run with no media in the top slot. REPORTED.

**Caveman summary.** Trailer top-slot if trailer good. Screenshot top-slot if trailer bad. 60-90s trailer. Gameplay seconds 0-10. ESTIMATED +20-40% wishlist conversion vs screenshot-only when trailer is competent.

## Feature-bullet count

Feature bullets appear in two Steam-page locations: (1) in the "About this game" section as a stylized bullet block (formatted text inside the long description); (2) as a separate bulleted list above the long description in some page layouts. Valve has no hard cap on bullet count — convention only.

**Observed feature-bullet counts in primary-tribe reference set (training-recall, ESTIMATED):**
- CK3: ~6-8 bullets, each ~10-20 words.
- Wildermyth: ~5-6 bullets, each ~15-25 words.
- RimWorld: ~7-9 bullets, each ~12-22 words.
- Old World: ~6-7 bullets.
- Battle Brothers: ~6-8 bullets.
- Stellaris: ~8-10 bullets.
- Songs of Syx: ~5-7 bullets.
- Manor Lords: ~6-8 bullets.
- Frostpunk 2: ~5-7 bullets.
- Caves of Qud: ~6-8 bullets.

**Cluster:** 5-9 bullets is the dominant range. Outliers either compress to 3-4 (rare, signals minimalism) or expand to 10-12 (signals feature-grab, often correlates with feature-list-as-tutorial pages that under-perform). REPORTED.

**Sweet-spot evidence.** GameDiscoverCo + Zukowski guidance converges on 5-8 bullets as the optimum for niche/indie strategy pages. Below 5, the page reads "thin." Above 8-9, visitors skim and lose the differentiator signal in noise. REPORTED.

**Bullet-count vs conversion data.** Direct A/B data is scarce. Indie post-mortems anecdotally report no meaningful conversion delta between 6 and 8 bullets when content quality is held constant. The delta appears at the extremes (under 5 / over 12). ESTIMATED — no Valve-aggregated data confirms. AMBIGUOUS on whether bullet count itself drives conversion vs the implied "page completeness" signal.

**Bullet-content pattern.** Each bullet leads with a verb or concrete noun. Avoid abstract value language. Tie each bullet to a screenshot beat (so screenshots and bullets reinforce, not redundantly state). Lead bullet should restate the differentiator-noun from the short description. REPORTED.

**Caveman summary.** 5-8 bullets. Sweet spot 6-7. Lead verb or noun. Tie to screenshot beats. ESTIMATED — no Valve data confirms precise count.

## GIF vs static screenshot

Steam supports both animated GIF/short-video and static screenshot assets in the screenshot carousel. Animated assets are recently more common — Valve added "convert MP4 → carousel slot" tooling around 2019-2020, and adoption grew through 2022-2024 in indie strategy.

**Conversion-delta data.** GameDiscoverCo + Zukowski + multiple indie post-mortems report animated/GIF-style assets in the screenshot carousel outperform static screenshots on conversion. Magnitude estimates from training-recall post-mortems cluster in the +10-30% wishlist conversion range when animated assets replace static. ESTIMATED — self-reported, not Valve-aggregated. AMBIGUOUS on whether the lift is from motion-attention or from animated assets typically showing systems-in-action that static screenshots can't.

**Niche-strategy specific.** Strategy games are uniquely well-served by animated assets because static screenshots of strategy UIs read as "Excel screenshot" to genre-curious visitors (cross-ref `primary_tribe_psychographic_profile.md` FoG:E negative-theme #1 "spreadsheet-feel UI"). Animation signals "this is alive, things move." Old World, Manor Lords, Frostpunk 2, Stellaris, Songs of Syx (later in lifecycle), Caves of Qud all use animated assets in the carousel. REPORTED.

**Best-practice pattern.**
- Slot 1: animated (most attention-grabbing slot after trailer).
- Slot 2-3: static if static reads cleanly; animated if static reads as UI-dense.
- Slot 4-6: mix; show distinct gameplay systems.
- Final 1-2 slots: feature-callout overlay screenshots (text on screenshot, calling out a system).
- Never lead with text-overlay-only screenshots (read as ad copy, suppresses conversion).
REPORTED, multiple sources.

**Asset spec recall (Valve documentation).** Carousel screenshot dimensions 1920×1080 preferred (16:9). Animated assets typically MP4 video, file-size constraints apply (couple of MB per slot recommended). VERIFIED on 1920×1080 (Steamworks spec); REPORTED on animated-asset upload mechanics.

**Caveman summary.** Animated > static for strategy. Lift ~+10-30% ESTIMATED. Slot 1 animated. Mix slots 2-6. Never text-overlay-only first slot.

## "About this game" length

The "About this game" section is the long-form descriptive block below the screenshot carousel. Valve has no hard cap on length, but page-rendering and visitor scroll-depth impose soft caps.

**Length distribution across niche-strategy successful pages (training-recall, ESTIMATED word counts):**
- CK3: ~400-500 words.
- Wildermyth: ~350-450 words.
- RimWorld: ~600-800 words (long, structured w/ headers + bullet sub-sections).
- Old World: ~450-600 words.
- Battle Brothers: ~500-700 words.
- Stellaris: ~600-900 words.
- Songs of Syx: ~400-500 words.
- Workers & Resources: ~600-800 words.
- Manor Lords: ~300-450 words.
- Frostpunk 2: ~400-600 words.
- Caves of Qud: ~500-700 words.
- HighFleet: ~400-500 words.
- Sea Power: ~500-700 words.
- Nebulous: Fleet Command: ~400-600 words.

**Cluster:** 400-700 words is the dominant range for niche-strategy. Outliers go shorter (~250-350 for very-minimalist pages, less common for strategy) or longer (~900-1200 for complex-system pages that lean into "this game has a lot of depth to dig into").

**Structure pattern.** Successful long pages use clear sub-section headers (H2-style, formatted via Steam's bbcode). Common section header patterns:
- "Lead a [thing]" / "Build your [thing]" / "Survive [thing]" — gameplay-loop framing.
- "Features" — bulleted feature list (cross-ref previous section).
- "Story" or "World" — narrative/setting paragraph.
- "Modding" or "Community" — long-tail engagement signal (where applicable).
REPORTED.

**Bounce vs depth-signal — the trade-off.** Short About (under 300 words) reads as "thin," may suppress conversion among depth-seekers (primary tribe is depth-seeking per psychographic brief). Long About (over 800 words) increases scroll-depth requirement and may suppress conversion among casual scanners. Niche-strategy primary tribe is the rare audience that rewards long About — they read, they want depth signal. REPORTED. AMBIGUOUS — no direct A/B data confirms the inflection point.

**Bullet block placement inside About.** Successful pages place the feature-bullet block either (1) at the top of About, immediately after a 2-3 sentence framing paragraph, or (2) midway, after an introductory section + before a story/world section. Pattern (1) is more common for genre-shopper pages (visitor wants to know "what do I do?"); pattern (2) is more common for narrative-strategy pages (visitor wants to feel the world first). REPORTED.

**Niche-strategy optimum.** ESTIMATED 450-650 words, structured w/ 3-4 sub-section headers, feature-bullet block in pattern (1) or (2). Sits inside the observed primary-tribe cluster, signals depth without exceeding scroll tolerance.

**Caveman summary.** 450-650 words optimum. 3-4 sub-section headers. Feature bullets at top or mid. Primary tribe rewards depth signal. AMBIGUOUS on exact inflection.

## Below-fold read-rate

Below-fold = content that requires scroll to reach. Includes most of About this game (depending on viewport), franchise/dev block, system requirements, reviews module, more-like-this carousel, mature content disclosure, DLC list.

**Read-rate estimates.** Page-visit-to-scroll-past-first-viewport rates are publisher-side data. Indirect estimates from indie post-mortems + GameDiscoverCo guidance cluster:
- ~40-60% of visitors scroll past the first viewport on niche-strategy pages (where above-fold pitch is strong enough to invite exploration). ESTIMATED.
- ~20-35% of visitors scroll to the bottom of About this game. ESTIMATED.
- ~10-20% scroll to system requirements / franchise block. ESTIMATED.
- Wishlist-button clicks happen disproportionately above or near the top of the page (button is in the top-right capsule area); scroll-depth does not strongly correlate with wishlist click. REPORTED — visitors who decide to wishlist often do so without scrolling deep.

**Implications.** The top viewport (capsule, short description, trailer, tags) does the load-bearing conversion work. Below-fold content (About, franchise block, system reqs) serves the depth-seeker fraction — primary tribe over-indexes here vs casual visitors. REPORTED.

**Above-fold conversion priority.** Multiple GameDiscoverCo / How To Market A Game posts emphasize: "Optimize for the visitor who never scrolls. Then optimize for the visitor who does." REPORTED.

**Below-fold value.** For niche-strategy, below-fold content (esp. About, feature bullets, story/world section) functions as conversion-confirmation for the depth-seeker who already half-decided above the fold. Removing below-fold content does not save the wrong audience; weakening it can lose the right audience. REPORTED, less data-backed.

**Caveman summary.** ~40-60% scroll past viewport 1. ~20-35% reach bottom of About. ~10-20% reach franchise block. Top viewport carries conversion. Below-fold confirms for depth-seekers. ESTIMATED throughout.

## Developer / franchise page

Steam supports two related but distinct page-types: developer pages (publisher-owned aggregator pages showing all titles by a developer/publisher) and franchise pages (cross-title hubs grouping a single franchise's entries).

**Conversion role.** Developer/franchise pages function as cross-sell engines + brand-credibility signals. Three patterns observed:

**Hooded Horse pattern.** Hooded Horse runs an actively-maintained publisher curator + developer page surfacing every Hooded Horse title (Old World, Manor Lords, Falling Frontier, Workers & Resources, Terra Invicta, Galactic Civilizations IV, etc.). Niche-strategy buyers who've bought one Hooded Horse title overwhelmingly cross-buy others — publisher-as-curated-trust is a real conversion lever for this audience. Hooded Horse public-facing posts cite cross-buy rates as a key part of their portfolio strategy. REPORTED. ESTIMATED cross-buy lift +15-30% among existing Hooded Horse customers vs cold visitors for a new Hooded Horse title.

**Paradox pattern.** Paradox franchise page + dev page surfaces CK3, EU4, HoI4, Vic3, Stellaris, Imperator, plus DLC. Cross-buy rate inside the Paradox catalog is high — primary-tribe psychographic brief estimated 50-65% CK3 ↔ Stellaris cross-ownership. Paradox uses franchise pages to surface new DLC + cross-promote between mainline titles. REPORTED.

**Worldwalker (Wildermyth) pattern.** Solo-studio developer pages for small teams with single titles serve mostly as credibility + future-launch wishlist surfaces. Worldwalker's page surfaces Wildermyth + any future titles + dev-blog posts. Cross-buy doesn't apply (one title) but follow-the-studio behavior is real among primary tribe — Wildermyth fans wishlist Worldwalker's next title sight-unseen at a meaningful rate. ESTIMATED.

**Conversion lift estimates.** Indie post-mortems suggest dev-page-driven traffic converts at higher wishlist rates than cold-Steam-discovery traffic by ~20-50% margin — visitors who navigate to a dev page have pre-filtered. ESTIMATED, large variance.

**For Ouroboros context.** Solo or small-studio publisher status means dev-page strategy looks more like Worldwalker than Paradox/Hooded Horse. Building a dev-page presence pre-launch (single title, dev-blog updates, news posts) serves the follow-the-studio audience that converts at higher rates. Future-DLC + future-title cross-sell apply when DLC ships. REPORTED.

**Franchise page applicability.** Franchise page is for multi-title franchise IP. Ouroboros at first release is single-title; franchise page is N/A until era-DLC or future-game expands the franchise. Possibility down-stream — 7-era DLC + Roman-free arc + any future titles in same world could justify a franchise page. ESTIMATED future relevance.

**Caveman summary.** Dev page worth setting up pre-launch even solo. Follow-the-studio behavior real in primary tribe. Hooded Horse + Paradox cross-buy lift +15-30% ESTIMATED. Franchise page N/A until multi-title.

## Localized store page

Steam supports per-language store pages (capsule, short description, About, screenshots, trailer subtitles/dubs). Default visitor view is the Steam client's set language; English-only pages serve non-English visitors a degraded experience (English capsule + machine-translated About in some cases, or English-only outright).

**Conversion delta — English-only vs localized.** Valve has stated in partner communications and GDC talks that localized store pages outperform English-only in non-English markets by a wide margin. Magnitude estimates from publisher-side data leaks + GDC talks cluster:
- German, French, Spanish (Spain + LATAM), Brazilian Portuguese, Italian — store-page localization typically lifts conversion +20-50% in those markets vs English-only. ESTIMATED.
- Russian, Polish, Czech — similar lift, +20-40%, with the caveat that Russian-language store strategy is complicated post-2022 by sanctions + payment-region changes. ESTIMATED.
- Simplified Chinese — store-page localization is critical; lift +50-100% or more vs English-only in CN market. ESTIMATED. Note: CN market also has unique discovery surfaces (Bilibili, Weibo) that go beyond store-page.
- Korean, Japanese — store-page localization typically lifts conversion +30-60%. ESTIMATED.
- Turkish — variable; lift +20-40% but market size + payment-region issues complicate. ESTIMATED.

**Localization scope levels.**
1. **Capsule + short description + tags only** — cheapest, lowest lift. Useful for testing market viability.
2. **Capsule + short description + About this game** — mid-tier, captures most store-page conversion lift.
3. **Capsule + About + screenshot text overlays + trailer subtitles** — full store-page localization, captures full lift.
4. **Full game UI + in-game text localized** — beyond store-page scope; affects review sentiment + long-tail retention but is separate spend.

Cluster: most indie niche-strategy launches do level 2 or 3 for top-5 languages (DE, FR, ES, IT, BR-PT, ZH-CN, RU pre-2022), level 1 for opportunistic languages. REPORTED.

**Niche-strategy specifics.** Primary tribe (CK3, Wildermyth, BB, Old World) audiences skew Western European + North American + smaller Latin American + Eastern European pockets. CK3 in particular has strong German + French + Russian audiences. Stellaris has strong Chinese audience. Wildermyth + Battle Brothers more North American + Western European. Foundation/hard-SF differentiator audience has Foundation TV halo in multiple markets (Apple TV is in 100+ countries, Foundation has international viewership). REPORTED.

**Localization conversion lift vs cost.** GameDiscoverCo + indie post-mortem patterns suggest: store-page localization (level 2-3) for top 5-7 languages typically pays back within first 30-60 days of launch for niche-strategy titles at $25-35 price point. Solo-dev / small-studio post-mortems anecdotally report 15-30% of lifetime sales come from non-English markets when localized. ESTIMATED.

**For Ouroboros context.** Bible-locked $25-35 paid-base + 7-era DLC + Roman-free strategy. Primary-tribe audience skews CK3/Wildermyth/BB-aligned (Western EU + NA + EE). Foundation-thematic differentiator adds international Foundation-TV halo. Localization slate priority candidates (Research Lane surfaces, doesn't pick): German, French, Spanish (ES+LATAM), Brazilian Portuguese, Italian, Polish, Russian (subject to payment-region viability), Simplified Chinese, Korean, Japanese. T-L1 follow-up topic will deepen. REPORTED.

**Caveman summary.** Localized > English-only +20-50% non-English markets ESTIMATED. ZH-CN biggest lift +50-100%+. Top-5 languages pays back in 30-60 days. Niche-strategy 15-30% lifetime sales non-English when localized.

## Cross-cutting findings

1. **Above-fold does the load-bearing conversion work.** Capsule + short description + trailer + tags + first viewport carry most of the wishlist-conversion signal. Below-fold confirms for depth-seekers (primary tribe over-indexes here) but doesn't rescue weak above-fold. ESTIMATED. REPORTED direction.

2. **Niche-strategy primary tribe rewards depth-signal more than casual audiences.** Long About (450-650 words structured w/ headers), 5-8 feature bullets, animated screenshots, modding/community mentions — all signal "this game has more under the hood" which the depth-seeking primary tribe (per `primary_tribe_psychographic_profile.md`) explicitly buys for. REPORTED.

3. **Trailer quality dominates trailer placement.** Trailer-as-top-slot lifts wishlist conversion +20-40% ESTIMATED *when trailer is good*. Bad trailer top-slot actively hurts. T-V1 trailer spec is upstream of page-layout decisions. REPORTED.

4. **Animated screenshot assets outperform static for strategy.** Strategy UIs read as "spreadsheet" in static; animation rescues. ESTIMATED +10-30% lift when animated replaces static in slot 1. Cross-ref `audience_overlap_map.md` for "spreadsheet-feel UI" bounce concern in primary tribe. REPORTED.

5. **Localization is high-ROI for niche-strategy at $25-35 price point.** Top-5 language localization pays back in 30-60 days ESTIMATED; ZH-CN biggest single-market lift; primary tribe has German + French + Russian (pre-2022) + Chinese (via Stellaris-overlap) strength. T-L1 follow-up will deepen.

6. **Developer page is worth setting up pre-launch even for solo/small studios.** Follow-the-studio behavior is real in primary tribe (Worldwalker pattern). Hooded Horse + Paradox cross-buy patterns extend later if multi-title or DLC-shipping. REPORTED.

## Conflict surfaced

Bible cross-check against page-shape directives if any. Cross-ref `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` + `docs/bible/game_bible.md` + active In Flux entries.

- **bible_monetization.md L274 "Free to play" tagline.** Steam-page short description / capsule copy must comply with monetization framing. If "Free to play" tagline survives bible cleanup, it collides with $25-35 paid-base reality and with primary-tribe expectations per `primary_tribe_psychographic_profile.md` L169 conflict. Short-description copy cannot honestly invoke "Free to play" if game is $25-35 paid. **CONFLICT flagged. Bible authority resolves — cleanup pending per project_current_focus.md.**

- **bible_monetization.md L292 Fortnite reference.** Steam-page copy invoking Fortnite as positioning collides with primary-tribe anti-Fortnite-aesthetic per psychographic brief. Page-copy framing must avoid Fortnite positioning regardless of monetization-mechanic borrowing. **CONFLICT flagged. Bible authority resolves.**

- **RTS framing kill (In Flux 2026-05-16).** Steam-page short description, About this game, feature bullets, and trailer text overlays must NOT use "RTS" framing per bible lock. Tactical-layer descriptions must frame as "tactical missions in your civilization's history" / "named lieutenants commanding cohorts" / similar lieutenant-system language. Page copy is downstream of this lock. **No conflict per se — flag as constraint for marketing-implementer when drafting page copy.**

- **Lieutenant System lock (In Flux 2026-05-16).** Page copy should reflect 3-7 named lieutenants w/ personality as tactical-layer pitch. T-V2 screenshot spec should include lieutenant-name overlay screenshots in carousel. T-V1 trailer should feature at least one named lieutenant beat. **Constraint flag, not bible conflict.**

- **7-era DLC + Roman-free.** Page copy + DLC list section needs to reflect era-DLC structure when DLC ships. Pre-launch page won't have DLC list; post-launch page picks up DLC blocks. **Constraint flag for marketing-implementer DLC-ship cycles.**

No fresh bible conflict surfaced beyond L274 + L292 already flagged across multiple briefs.

## Caveats and confidence

Distribution: ~5% VERIFIED (Valve-published asset-spec numbers — image dims, char limits), ~55% REPORTED (training-recall patterns from GameDiscoverCo, Zukowski, GDC talks, indie post-mortems — high confidence in direction, lower in exact magnitude), ~35% ESTIMATED (conversion-lift percentages, word-count clusters, market-specific localization deltas — publisher-side data is the only ground truth and not publicly aggregated), ~5% AMBIGUOUS (trade-offs where indie-marketer guidance contradicts publisher-side post-mortem data, e.g., About-length inflection point, GIF-vs-static magnitude variance).

**Page-level conversion telemetry is publisher-side, ESTIMATED floor.** Valve does not publish aggregated per-element conversion dashboards for non-publishers. Any quantitative conversion-rate claim in this brief should be treated as ±20-40% directional. The direction of effect (trailer > screenshot for top slot when trailer is good, animated > static for strategy, localized > English-only in non-English markets, long About rewards primary tribe) is high-confidence REPORTED. The magnitudes are ESTIMATED and vary widely across publishers, niches, price points, and launch contexts.

**Known unknowns.**
- 2026 Steam UI changes affecting above-fold layout (Steam regularly updates store-page rendering; precise viewport boundaries shift).
- 2026 algorithmic-discovery changes affecting tag-driven traffic vs short-description-driven traffic.
- Post-2024 publisher data on era-DLC vs season-pass page layouts (relevant to Ouroboros 7-era DLC structure but no public data on optimum).
- Foundation-TV halo magnitude on Foundation-adjacent Steam wishlist conversion (not measured publicly).
- Steam Direct + Curator algorithm shifts post-2024 affecting niche-strategy discoverability.
- Lieutenant-system-style page-copy A/B data (no precedent — Ouroboros is new in framing).
- Solo-dev vs publisher-backed page-copy conversion delta at $25-35 price point in 2026.

Brief is one interpretation. Other valid interpretations of same source pool exist — particularly on About length (some marketers argue for shorter pages w/ external-link long-form content; this brief sides with the primary-tribe-depth-signal reading).

**Re-capture flagged when WebFetch returns:** GameDiscoverCo public archive crawl, Chris Zukowski blog crawl for recent posts, Steamworks documentation refresh for asset-spec confirmation, primary-tribe-anchor Steam page snapshot for current word counts + bullet counts + screenshot counts, indie post-mortem aggregation for 2025-2026 conversion data, Hooded Horse + Paradox publisher data where publicly disclosed.

## Feeds Design Lane

This brief feeds:

- **T-S2 capsule copy** — short description optimum 25-35 words / 150-200 chars; lead w/ genre anchor first 4-7 words; include one concrete differentiator-noun (candidates from `audience_overlap_map.md` cluster language: "dynasty," "centuries," "civilization," "lieutenants"); avoid abstract value language + studio name front-loading.
- **T-V1 trailer spec** — 60-90 second length; open w/ gameplay-visible hook in seconds 0-10; text-overlay calls out differentiator-noun matching capsule; include named-lieutenant beat per Lieutenant System lock; close on logo + wishlist CTA. Trailer-quality dominates trailer-placement decision.
- **T-V2 screenshot spec** — animated assets in slot 1; mix animated + static slots 2-6; never text-overlay-only first slot; tie screenshots to feature-bullet beats; include lieutenant-name overlay screenshots per Lieutenant System lock; show systems-in-action to defeat "spreadsheet-feel" bounce.
- **T-L1 localization slate** — priority candidates (Research Lane surfaces, Design Lane picks): German, French, Spanish (ES+LATAM), Brazilian Portuguese, Italian, Polish, Russian (subject to payment-region viability), Simplified Chinese, Korean, Japanese. Level 2-3 scope (capsule + About + screenshot text + trailer subtitles). Pays back in 30-60 days ESTIMATED.
- **T-W1 wishlist conversion** — page above-fold carries most wishlist-click weight; trailer quality + capsule short description + tags are top three levers; below-fold serves depth-seekers (primary tribe over-indexes here, rewards depth-signal).
- **Page-build spec for marketing-implementer** — About this game 450-650 words structured w/ 3-4 sub-section headers; 5-8 feature bullets (sweet spot 6-7); developer page setup pre-launch even for solo; franchise page N/A until multi-title or era-DLC expansion; RTS framing prohibited everywhere on page per bible lock; Lieutenant System lock applies to all page copy + assets; L274 + L292 cleanup pending before page goes live.

## Open questions for further research

- **Lieutenant-system-style page-copy A/B test design** — no precedent for this pitch shape on Steam; what counterfactual copy benchmarks against? Possibly cross-test "named lieutenants" vs "named characters" vs "named heroes" capsule variants.
- **Foundation-TV halo measurable lift on Foundation-adjacent wishlist activity** — Apple TV viewership figures + Foundation-IP-adjacent Steam page conversion data 2024-2026.
- **Era-DLC vs season-pass page-layout best practice** — Ouroboros' 7-era DLC structure has limited Steam-page precedent; closest analogues are Paradox era-DLC (CK3 + Stellaris + EU4) but their page-layout-conversion deltas across DLC strategies are publisher-side.
- **Primary-tribe wishlist-to-purchase conversion at $25-35** — T-W1 follow-up; what wishlist-conversion benchmarks apply for niche-strategy at this price point launching solo vs publisher-backed?
- **Animated-screenshot magnitude refinement for strategy specifically** — most A/B data is cross-genre; strategy-specific animated-vs-static A/B data would tighten the +10-30% estimate.
- **Localized store page Russian-market viability post-2022 sanctions + payment-region changes** — T-L1 input; Russian-language store strategy is more complicated than other languages and needs separate research thread.

## Sources

Training-data-only — flag for re-capture w/ live crawl of GameDiscoverCo, Chris Zukowski blog, Steamworks documentation, primary-tribe-anchor Steam pages, indie post-mortem archives, and GDC vault when WebFetch returns.

- GameDiscoverCo newsletter (Simon Carless) — https://newsletter.gamediscover.co/
- How To Market A Game (Chris Zukowski) blog — https://howtomarketagame.com/
- Steamworks Documentation (Valve) — https://partner.steamgames.com/doc/store/assets
- GDC Vault — https://gdcvault.com/ (post-mortems referenced: Hooded Horse Old World/Manor Lords, 11 bit Frostpunk 2, Larian Baldur's Gate 3, Failbetter Games, Mode 7, Stunlock)
- Steam page reference set (recalled from training, not verbatim crawl):
  - Crusader Kings III — https://store.steampowered.com/app/1158310/
  - Wildermyth — https://store.steampowered.com/app/763890/
  - RimWorld — https://store.steampowered.com/app/294100/
  - Old World — https://store.steampowered.com/app/597180/
  - Battle Brothers — https://store.steampowered.com/app/365360/
  - Stellaris — https://store.steampowered.com/app/281990/
  - Songs of Syx — https://store.steampowered.com/app/1162750/
  - Workers & Resources: Soviet Republic — https://store.steampowered.com/app/784150/
  - Manor Lords — https://store.steampowered.com/app/1363080/
  - Frostpunk 2 — https://store.steampowered.com/app/1601580/
  - Caves of Qud — https://store.steampowered.com/app/333640/
  - HighFleet — https://store.steampowered.com/app/1434950/
  - Sea Power — Steam app page (training-recall, app id not confirmed)
  - Nebulous: Fleet Command — https://store.steampowered.com/app/887570/
- Publisher developer pages (recalled, not verbatim crawl):
  - Hooded Horse publisher page on Steam
  - Paradox Interactive publisher page on Steam
  - Worldwalker Games developer page on Steam
- Indie-marketer Twitter threads + r/gamedev post-mortems (training-recall, no verbatim quotes):
  - Tinybuild publisher-side conversion posts
  - Raw Fury post-mortems
  - Hooded Horse public-facing performance disclosures
  - Solo-dev wishlist-conversion-rate posts on r/gamedev + IndieDB
- Cross-reference within Ouroboros docs:
  - `docs/legacy/topics/lieutenant_pivot_niche_brief.md` — parent brief; primary tribe + thematic differentiator ranking + niche cluster framing
  - `docs/legacy/topics/audience_overlap_map.md` — tag + curator + creator + press overlap; cluster-derived pitch-language list feeds capsule copy
  - `docs/legacy/topics/primary_tribe_psychographic_profile.md` — per-anchor review themes; "spreadsheet-feel UI" + depth-seeker patterns feed page-build choices
  - `docs/bible/game_bible.md ## In Flux` — Lieutenant System + RTS-framing-kill 2026-05-16 entry
  - `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` L274 + L292 — conflict-flag targets

**Re-capture stamp.** All conversion-rate magnitudes, word-count clusters, bullet-count optima, GIF/static deltas, About-length distributions, below-fold read-rate estimates, dev-page cross-buy lifts, and localized-page conversion deltas in this brief are training-data-derived as of cutoff. Live Steamworks documentation pull + GameDiscoverCo + Chris Zukowski post crawl + primary-tribe-anchor Steam page snapshot + 2025-2026 indie post-mortem aggregation required to upgrade REPORTED/ESTIMATED → VERIFIED. Flag for Research Lane re-capture when WebFetch is restored.
