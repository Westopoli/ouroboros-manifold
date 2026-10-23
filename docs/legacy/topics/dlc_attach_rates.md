---
name: DLC Attach Rates
description: DLC attach-rate survey across niche-strategy paid-base titles (Paradox CK3/Stellaris/EU4/HOI4, RimWorld, Wildermyth Omenroad, Battle Brothers, Old World, Total War); first-expansion attach pattern, decay curve, cosmetic-tier attach, identity-deviation under-attach signal; feeds T-M2 7-tier DLC stress-test, monetization revenue model, T-P3 DLC pricing ladders cross-validation; substrate for Ouroboros 7-era + Roman-free ladder revenue floor/median/ceiling at 80-200k base @ $25-35.
type: topic_brief
captured_at: 2026-05-18
contributor: Research Lane T-CL2 capture
---

# DLC Attach Rates

## What this brief is

Per-DLC attach-rate survey across niche-strategy paid-base titles. Pulls first-expansion attach, decay curve across 2nd / 3rd / 4th+ items, cosmetic-tier attach floor, flavor-pack attach, identity-deviation under-attach signal. Cross-references sibling brief `dlc_pricing_ladders.md` (T-P3) which holds the per-SKU price-point map; this brief holds the per-SKU attach signal underneath those price points. Feeds T-M2 7-tier DLC stress-test, monetization revenue model, T-P3 cross-validation, and the Ouroboros 7-era + Roman-free substrate.

Non-recommendation disclaimer: Research Lane surfaces inputs, does not pick. Anything below that reads like a pick is data preserved from cited source, not endorsement. Design Lane decides 7-era ladder shape; bible (`docs/bible/game_bible.md`, `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)`) is authority on conflicts surfaced below.

## Method

Sources: Steam DLC catalog listings, Paradox press releases, Steam Spy / VGInsights estimates (where reachable in training data), Steam achievement percentages (proxy for attach), publisher communications (Ludeon, Worldwalker, Overhype, Mohawk Games, Creative Assembly), community discussion of attach signals, sibling Wave 3 game cards (`docs/legacy/games/*.md`). WebFetch/WebSearch denied during capture — every figure floors at REPORTED or ESTIMATED unless backed by widely documented public record (then VERIFIED).

Critical method caveat: **no publisher in the surveyed set publicly discloses per-DLC attach rates.** Paradox, Ludeon, Worldwalker, Overhype, Mohawk, Creative Assembly all withhold per-DLC sell-through. All attach rate figures below are ESTIMATED, derived from one or more of:
- Steam achievement % proxy (fraction of base-game owners with a DLC-gated achievement unlocked)
- SteamDB / VGInsights / SteamSpy estimates (third-party scraping; aggregator-independence caveat applies — see `feedback_aggregator_independence`)
- Concurrent-player pre/post-DLC delta (re-engagement spike proxy)
- Review-volume delta around DLC launch window
- Analyst commentary referencing internal numbers without source citation

Confidence tag convention: VERIFIED (publisher/financial filing/press release), REPORTED (training-data widely-documented), ESTIMATED (proxy-derived or analyst inference), AMBIGUOUS (conflicting signal or unresolved tier classification).

Game-card cross-refs read before writing this brief:
- `docs/legacy/games/ck3_dlc_ladder.md`
- `docs/legacy/games/stellaris_dlc_ladder.md`
- `docs/legacy/games/rimworld_dlc_ladder.md`
- `docs/legacy/games/wildermyth_omenroad.md`
- `docs/legacy/games/battle_brothers.md`
- `docs/legacy/games/old_world.md`
- `docs/legacy/games/total_war_franchise.md`
- `docs/legacy/topics/dlc_pricing_ladders.md` (sibling brief)

EU4 and HOI4 do not yet have dedicated game cards. Figures below training-data inline, REPORTED floor, flag for Wave 4.

## Paradox first-expansion attach pattern (60-80% claim, calibrated)

Public claim circulating in strategy-game commentary: Paradox first-expansion attach 60-80% of active base. Calibration against surveyed data:

**Stellaris Utopia (April 2017, first true expansion):** ESTIMATED 40-60% of active player base at peak. Source: `stellaris_dlc_ladder.md` line 56. AMBIGUOUS — no confirmed Paradox figure. Note "active player base" (concurrent-player-window snapshot) differs from "lifetime owners" — attach against active is higher because lapsed owners are excluded from denominator. Against lifetime owners ESTIMATED 25-40%. Confidence: ESTIMATED.

**CK3 Royal Court (February 2022, first major expansion):** ESTIMATED 30-50% of active owners at launch window. Source: `ck3_dlc_ladder.md` line 48. Sticker shock factor — Royal Court launched at $29.99 vs Stellaris Utopia at $19.99, plausibly suppressing attach 10-15 percentage points relative to a $19.99 launch. Confidence: ESTIMATED.

**EU4 first expansion (Conquest of Paradise, 2014):** No card yet. Training-data inline: EU4's first expansion attached strongly given EU4's tight strategy-niche audience; ESTIMATED 50-70% of 2014-era active base. Caveat: EU4 base was smaller in 2014 than later catalog windows, so absolute revenue smaller despite higher attach %. Confidence: ESTIMATED. AMBIGUOUS — early-catalog Paradox attach numbers are particularly opaque.

**HOI4 Together for Victory (2016, first expansion at $14.99):** No card yet. Lower price point ($14.99 vs $19.99 modal) plausibly drove higher attach. Training-data inline ESTIMATED 50-70% of active. Confidence: ESTIMATED.

**Calibrated 60-80% claim:** the 60-80% figure appears to be **upper-bound when measured against active concurrent-player base in launch-week window**, NOT lifetime owners. Against lifetime owners the more defensible range is 25-45% for first expansion at $19.99. The two denominator choices produce roughly 2x-3x different "attach" numbers for the same purchase. Anyone citing 60-80% should be checked for denominator. Confidence: ESTIMATED, with denominator-disambiguation REPORTED.

Substrate input for Ouroboros revenue modeling: at 80-200k base @ $25-35, **first-paid-era attach against active base** is the more relevant lever — Ouroboros' "active base" at era-1 paid DLC release will be a subset of the 80-200k base owners (those still playing or returning at era-1 launch). At ESTIMATED 30-50% attach against active, with active = 40-60% of base at DLC launch (re-engagement spike applied), the per-era-1 paid units sit in the range:
- Floor: 80k × 40% active × 30% attach = 9,600 units
- Median: 140k × 50% active × 40% attach = 28,000 units
- Ceiling: 200k × 60% active × 50% attach = 60,000 units

All three ESTIMATED. Multiplied by per-DLC price ($14.99 mid-tier or $19.99 expansion-tier per sibling `dlc_pricing_ladders.md`), gross revenue per era-1 DLC ranges $144k floor to $1.2M ceiling before platform cut. AMBIGUOUS — model sensitive to active-base assumption.

## Per-DLC decay curve

Claim: 1st 60-80%, 2nd 40-60%, 3rd 30-45%, 4th+ 20-35%. Calibration:

**Stellaris decay (10-year catalog, 30+ SKUs):**
- 1st expansion (Utopia 2017): ESTIMATED 40-60% active. REPORTED.
- Mid-catalog expansions 2018-2021 (Apocalypse, MegaCorp, Federations, Nemesis, Overlord): ESTIMATED 20-35% of owner base. Source: `stellaris_dlc_ladder.md` line 57. Decay reflects base-game install base growing faster than DLC purchasers.
- Late-catalog species/cosmetic packs: ESTIMATED 10-20% of owner base. Source: `stellaris_dlc_ladder.md` line 58. Cosmetic packs require less player commitment but pull lower attach because casual / lapsed players rarely return for cosmetics.
- Very late catalog 2022-2024: ceiling effect when full-catalog price hits $200+. New buyers buy base + one or two expansions, not full ladder. REPORTED.

**RimWorld decay (4 expansions, flat $24.99):**
- Royalty (2020, 1st): ESTIMATED 30-40% attach. Source: `rimworld_dlc_ladder.md` line 36. Weakest of four — psycast/royal-title polarized.
- Ideology (2021, 2nd): ESTIMATED 40-60% attach. Source: line 37. STRONGEST reception of four. Note: **2nd-expansion attach exceeded 1st-expansion attach for RimWorld** — inverts the standard decay claim. Reason: Royalty's polarized reception suppressed 1st, Ideology's belief-builder thematic fit drove higher attach. REPORTED.
- Biotech (2022, 3rd): ESTIMATED 35-55% attach. Source: line 38. Second-strongest — gene-modding appeals to systems-player core.
- Anomaly (2024, 4th): ESTIMATED 30-45% attach at launch window. Source: line 39. Identity-deviation toward survival-horror suppressed attach. REPORTED.

**RimWorld pattern key observation:** the decay claim does NOT hold for RimWorld. Sequence is 30-40% / 40-60% / 35-55% / 30-45% — roughly flat with quality-driven variance, not monotonic decline. This is a critical exception to the "monotonic decay" framing. Likely driver: RimWorld's short catalog (4 items) does not hit the cumulative-cost ceiling that suppresses Stellaris late-catalog attach. ESTIMATED.

**CK3 decay (10 DLC over 4 years):**
- Royal Court (1st major, 2022): ESTIMATED 30-50% attach. Source: `ck3_dlc_ladder.md` line 48.
- Tours & Tournaments (mid-tier, 2023): ESTIMATED 25-40% attach. Lower price ($14.99) likely raised attach % vs Royal Court despite later catalog position.
- Roads to Power (2024): ESTIMATED 20-35% attach. Source-derived. AMBIGUOUS — Roads to Power's $19.99 sticker (below Royal Court's $29.99 ceiling) may have driven attach above pure-decay prediction.
- Flavor packs (Northern Lords, Fate of Iberia, etc.): ESTIMATED 15-25% per pack with decay as catalog grows. Source: `ck3_dlc_ladder.md` line 48.

**Calibrated decay claim:** the 60-80% / 40-60% / 30-45% / 20-35% sequence holds **directionally for Stellaris-shape catalogs** (long open-ended accretion). Holds **weakly for RimWorld-shape catalogs** (short flat-price ladders where quality variance dominates). Per-tier price differentiation (CK3) can invert pure decay — a lower-priced mid-tier DLC can attach higher than a higher-priced earlier major expansion. Confidence: REPORTED for Stellaris-shape, AMBIGUOUS for short-ladder fits.

Substrate input for Ouroboros 7-era ladder: if Ouroboros' shape resembles **RimWorld-flat** (per-era $19.99-$24.99 flat), decay claim should NOT be used as planning baseline — flat-with-variance is more defensible. If Ouroboros' shape resembles **Paradox-tiered** (mixed major/mid/flavor per era), Stellaris decay is the closer reference but cumulative-cost ceiling applies sooner with 7 paid eras than with Stellaris' open-ended catalog. AMBIGUOUS — depends on Design Lane ladder shape pick (T-M2).

## Cosmetic-pack attach (low single-digit to ~20%)

**Stellaris species packs ($7.99: Lithoids 2019, Necroids 2020, Aquatics 2021, Humanoids v2 2022):** ESTIMATED 10-20% of owner base. Source: `stellaris_dlc_ladder.md` line 58. Confidence: ESTIMATED.

**Stellaris portrait/music micro-DLC:** below the species-pack threshold; ESTIMATED 5-12% attach. AMBIGUOUS — Paradox bundles music/portrait into species packs more than as standalone SKUs in recent catalog.

**CK3 Tower of Domination ($4.99 cosmetic, ~2024):** ESTIMATED 5-15% attach. AMBIGUOUS — cosmetic-only pack at lowest price point in CK3 catalog. Source: `ck3_dlc_ladder.md` line 37.

**CK3 Ruler Designer (free patch + paid cosmetic adjacencies):** Ruler Designer itself is free; paid cosmetic adjacencies bundled into flavor packs rather than sold standalone. Attach figure not separable. AMBIGUOUS.

**EU4 cosmetic / unit / music packs ($4.99-$7.99):** ESTIMATED 5-15% attach per cosmetic SKU. Training-data inline. EU4's cosmetic tier is the most extensively populated of the surveyed Paradox catalogs (unit packs by era, music packs by region). REPORTED that the tier exists; ESTIMATED on per-SKU attach.

**HOI4 cosmetic / unit / music packs ($3.99-$7.99):** ESTIMATED 5-15% attach. Training-data inline.

**Calibrated cosmetic-tier attach:** **5-20% of owner base** is the defensible range across all four Paradox titles. Confidence: ESTIMATED. Low single-digit floor is when cosmetic packs target very narrow niches; ~20% ceiling is when cosmetic packs ride a major-expansion bundle wave.

**Cosmetic-tier revenue contribution:** despite low attach, cosmetic packs at $4.99-$7.99 can contribute meaningfully to cumulative-catalog revenue when (a) production cost is low (single artist + a few weeks vs major-expansion year-of-dev), (b) catalog accumulates 5-10 cosmetic SKUs over time, (c) bundle SKUs roll cosmetics into Chapter Pass pre-buys. Confidence: REPORTED. AMBIGUOUS on exact revenue share — Paradox does not disclose tier-revenue splits.

**RimWorld zero-cosmetic precedent:** Ludeon has shipped zero cosmetic packs across 6 years of post-launch DLC. Source: `rimworld_dlc_ladder.md` line 31. Either Ludeon judged the audience non-cosmetic-receptive OR judged the dev-cost-to-revenue ratio insufficient OR a values decision. Open question per `rimworld_dlc_ladder.md` line 93 — Tynan Sylvester has not publicly addressed the choice. AMBIGUOUS.

## RimWorld attach signal (achievement-% proxy)

Steam achievement percentages provide partial attach proxy for RimWorld DLC. Each expansion adds DLC-gated achievements; the % of base-game owners who have unlocked at least one DLC-gated achievement floors the active-DLC-owner share.

Achievement-% proxy caveat: this proxy systematically **underestimates** attach because (a) some DLC owners never trigger any gated achievement (especially Anomaly's horror content which players may avoid), (b) early-catalog DLC has had more years to accumulate achievement unlocks. Achievement-% is a floor not a ceiling estimate. Confidence: ESTIMATED.

Per `rimworld_dlc_ladder.md` lines 36-39:
- Royalty achievement-floor: roughly aligned with 30-40% attach ESTIMATE.
- Ideology achievement-floor: roughly aligned with 40-60% attach ESTIMATE — highest of the four.
- Biotech achievement-floor: 35-55% attach ESTIMATE.
- Anomaly achievement-floor: 30-45% but with widest uncertainty band — tonal-deviation suppresses voluntary engagement.

**Ludeon non-disclosure note:** despite RimWorld being a single-developer title with high transparency culture, Ludeon does not publish per-DLC unit counts. Tynan Sylvester's developer blog discusses design philosophy but not sales mix. Open question per `rimworld_dlc_ladder.md` line 89. AMBIGUOUS.

**Re-engagement multiplier:** `rimworld_dlc_ladder.md` lines 57, 75 — each RimWorld expansion launch pulls lapsed players back to active before the purchase decision. The "active base" denominator at DLC launch is thus inflated relative to mid-cadence active base. Attach % expressed against re-engagement-inflated active is the most flattering denominator; attach % against lifetime owners is the most conservative. The 2x-3x denominator spread applies here too. Confidence: REPORTED.

## Wildermyth Omenroad single-major-DLC attach signal

Omenroad (2024) at $9.99. Source: `wildermyth_omenroad.md`. ESTIMATED 10-25% attach of active players per `wildermyth_omenroad.md` line 26.

**Key signal not the attach % itself but the suppression cause:** Omenroad chose roguelite mode rather than additional authored campaigns. Community reception "Very Positive" (strong but below base game's "Overwhelmingly Positive"). Identity-deviation pattern — DLC that extends core identity attaches better than DLC that adds adjacent mode. Source: sibling `dlc_pricing_ladders.md` line 130, `wildermyth_omenroad.md` line 24. REPORTED.

Worldwalker is 2-5 dev team per `wildermyth_omenroad.md` line 28. Single-DLC-per-3-years cadence at this scale. Direct parallel to Ouroboros' planned indie team size. **For Ouroboros' 7-era ladder, Omenroad cadence implies 21 years to ship full ladder at Worldwalker-equivalent throughput.** This is a load-bearing constraint flag for T-M2 stress-test. Source-derived inference. ESTIMATED.

AMBIGUOUS — base-game owner count for Wildermyth itself is 500k-1M ESTIMATE range, so attach % uncertainty multiplies with base-uncertainty.

## Stellaris flavor-pack micro-DLC vs full expansion

Already covered in decay section. Tier-attach summary:
- Full expansion ($19.99-$29.99): ESTIMATED 20-35% attach mid-catalog.
- Story pack ($9.99): ESTIMATED 15-25% attach mid-catalog. Source-derived from `stellaris_dlc_ladder.md` lines 56-58.
- Species pack ($7.99): ESTIMATED 10-20% attach mid-catalog.

Stellaris story packs (Distant Stars, Ancient Relics, First Contact, Astral Planes, Grand Archive, Cosmic Storms) sit at higher attach % than species packs but below full expansions. The story-pack tier is closest to a "cheap meaningful content add" — lower commitment than expansion, more content than cosmetic. AMBIGUOUS on exact tier-distinguishing attach delta.

Steam community language for story packs: "$9.99 for a couple of event chains is fair." For species packs: "$7.99 for portraits is borderline." Source: community discussion paraphrased through training data. Subjective floor — sentiment language not a sales figure. REPORTED.

## Battle Brothers DLC attach signals

Battle Brothers DLC catalog: Beasts & Exploration (2018, $9.99), Warriors of the North (2019, $9.99), Blazing Deserts (2020, $14.99). Source: `battle_brothers.md` line 20. Confidence: VERIFIED on prices.

Lifetime revenue estimated ~$31M. Source: `battle_brothers.md` line 18. ESTIMATED. **`battle_brothers.md` line 64 flags directly:** "DLC attachment rate for Battle Brothers — what fraction of the ~$31M came from DLC vs. base game?" is an open question. AMBIGUOUS.

Steam achievement proxy + community discussion: ESTIMATED 30-50% attach for Beasts & Exploration (1st DLC), ESTIMATED 25-40% for Warriors of the North (2nd), ESTIMATED 20-35% for Blazing Deserts (3rd). All ESTIMATED with wide uncertainty bands.

Overhype Studios is 2-3 person team per `battle_brothers.md` line 30. Three DLC over 3 years post-launch is the achieved cadence — between Wildermyth's single-DLC and RimWorld's 4-expansion-over-4-years pace. Substrate input for Ouroboros team-scale planning. REPORTED.

## Old World DLC attach signals

Old World base game $39.99. DLC catalog: Wonders and Dynasties, Heroes of the Aegean, Behind the Throne, Sacred and Profane, Pharaohs of the Nile (Egypt and Mesopotamia framing). Source: `old_world.md` line 18. Modest DLC footprint relative to Paradox titles. REPORTED.

Old World base game review count ESTIMATED 4-6k Steam reviews per `old_world.md` line 16. Substantially smaller commercial scale than CK3. ESTIMATED on attach: 25-40% for first major DLC, decaying to 15-25% for later DLCs. All ESTIMATED with wide bands.

`old_world.md` line 63 flags directly: "Does Old World's DLC model... provide additional succession/family mechanics, or purely content?" — relevant to Ouroboros DLC progression model design. Open question. AMBIGUOUS.

Old World's smaller commercial scale relative to CK3 (~5k reviews vs ~80k+) means absolute DLC unit counts are 1-2 orders of magnitude smaller despite similar attach %. Confidence: REPORTED.

## Total War campaign-pack attach signals

Total War operates on a fundamentally different attach model: each Total War game launches at $59.99 AAA-tier price, with campaign packs, lord packs, race packs sold at $7.99-$19.99 each. Source: `total_war_franchise.md`. REPORTED.

**Warhammer trilogy DLC attach:** estimated to have generated "hundreds of millions of dollars in revenue including DLC" per `total_war_franchise.md` line 30. ESTIMATED. The Warhammer DLC catalog is among the largest in strategy gaming — 30+ paid SKUs across Warhammer I/II/III.

**Per-SKU attach pattern:** lord packs (single legendary lord + units, $7.99-$9.99) ESTIMATED 15-30% attach; campaign packs (new race + campaign mechanics, $14.99-$19.99) ESTIMATED 25-40% attach. Race packs in Warhammer II's "Lords Pack" cadence attached strongly because Total War's audience is heavily faction-loyalist (players pick favorite race and want more content for that race). REPORTED on cadence pattern, ESTIMATED on per-SKU attach.

**Pharaoh underperformance:** `total_war_franchise.md` line 38 — Pharaoh (2023) received mixed reviews and is considered commercial underperformer. DLC attach for Pharaoh's post-launch content has been visibly weaker than Warhammer III post-launch — base-game-quality determines DLC-attach ceiling. Source-derived inference. REPORTED.

**Different price-point regime:** Total War's $59.99 base + $14.99-$19.99 campaign packs is not directly substitutable for Ouroboros' planned $25-35 base + DLC-per-era pricing. Total War audience accepts higher absolute spend; Ouroboros target audience overlap with Paradox/RimWorld players who anchor at lower base-price expectations. Confidence: REPORTED.

## Cross-cutting findings

Six bullets, attach-rate dynamics across surveyed titles:

- **First-expansion attach claim 60-80% is denominator-dependent.** Against active-concurrent-player window at launch the upper-bound holds for tightest Paradox cases (EU4 early-catalog, HOI4 first). Against lifetime owners the defensible range collapses to 25-45%. Anyone modeling Ouroboros revenue from this figure must specify denominator. Confidence: REPORTED on the denominator distinction, ESTIMATED on the % bands.
- **Decay curve holds for long open-ended catalogs, breaks for short flat-price ladders.** Stellaris 10-year accretion shows monotonic decay; RimWorld's 4-expansion flat-price catalog shows quality-driven variance (2nd > 1st). 7-era finite ladder is closer to RimWorld-shape than Stellaris-shape — decay claim is not a defensible planning baseline for Ouroboros without quality-variance modeling. Confidence: REPORTED.
- **Identity-deviation suppresses attach.** RimWorld Anomaly (horror tonal-deviation) and Wildermyth Omenroad (roguelite mode-deviation) both attached lower than identity-extending alternatives would have. Per-era DLC for Ouroboros that maintains foundation/generational identity will attach better than DLC that introduces adjacent modes. Confidence: REPORTED.
- **Cosmetic-tier attach 5-20% of owner base.** Wide range driven by audience type (systems-player audiences buy fewer cosmetics; identity-builder audiences buy more) and price-point ($4.99 cosmetics attach higher than $7.99). RimWorld's zero-cosmetic precedent shows the floor; Stellaris species-pack cadence shows the ceiling. AMBIGUOUS for Ouroboros — audience cosmetic-receptivity not yet measured. Confidence: ESTIMATED.
- **Re-engagement multiplier inflates "active" denominator at DLC launch.** Each major-expansion launch pulls lapsed players back to active state before the purchase decision. RimWorld documents this most clearly per `rimworld_dlc_ladder.md` line 57. Inflated denominator can boost reported attach % 1.5x-3x relative to mid-cadence active-base measurement. Confidence: REPORTED.
- **Solo-dev vs studio attach differentiator is reach not %.** Per-DLC attach % is roughly comparable across solo-dev (Ludeon RimWorld 30-60%) and studio-scale (Paradox first-expansion 30-50%, accounting for denominator). The differentiator is absolute reach — Paradox titles ship to 1M+ owners, RimWorld to 3-5M, Wildermyth to 500k-1M, Old World to ~50-150k. Same attach % multiplies to vastly different revenue. Confidence: REPORTED.

## Factors driving attach

**Price elasticity:** lower price point increases attach % roughly logarithmically — $6.99 flavor pack ESTIMATED 15-25% attach, $9.99 story pack ESTIMATED 15-25%, $14.99 mid-tier ESTIMATED 25-40%, $19.99 expansion ESTIMATED 30-50%, $29.99 ceiling expansion ESTIMATED 25-40% (price-shock suppresses). Source: synthesis across cards. REPORTED.

**Content-density perception:** RimWorld flat $24.99 attach (30-60% range) outperforms Paradox $19.99 expansions (20-35%) likely because RimWorld's "real expansion" framing signals quality consistency vs Paradox's "flavor pack exists for revenue" community perception. Source: `rimworld_dlc_ladder.md` line 53. REPORTED.

**Time-since-launch:** Stellaris decay shows ~5-10 percentage point attach decline per year of catalog age, controlling for tier. Ouroboros' 7-era ladder shipped over ~3-7 years post-launch will face similar time-decay unless re-engagement-multiplier mechanics offset. Confidence: ESTIMATED.

**Mainline tie-in vs flavor:** mainline expansions (Royal Court, Utopia, Royalty) attach 2x-3x higher than flavor packs. Flavor packs serve cadence-fill + revenue role, not core revenue. Source: sibling brief. REPORTED.

**Re-engagement design:** DLC that includes a major free patch alongside (Paradox's "2.x" patches, RimWorld's free updates with DLC) pulls lapsed players back BEFORE the purchase decision, inflating active-denominator and raising apparent attach. Source: `stellaris_dlc_ladder.md` line 85, `rimworld_dlc_ladder.md` line 57. REPORTED.

**Reception quality:** RimWorld Ideology (strongest reception) attached ~1.5x Royalty (weakest reception) at similar price and catalog position. Quality dominates pure catalog-position decay. REPORTED.

## Solo-dev vs studio attach-rate differences

**Solo-dev (Ludeon RimWorld, Worldwalker Wildermyth, Overhype Battle Brothers):**
- Cadence: 1 DLC per 1-3 years.
- Per-DLC attach %: 25-50% range typical (RimWorld 30-60%, Wildermyth 10-25%, Battle Brothers 20-40%).
- Catalog ceiling: 3-5 DLC over post-launch life.
- Pricing: flat or near-flat ($24.99 RimWorld, $9.99 Omenroad, $9.99-$14.99 Battle Brothers).
- Revenue model: high per-DLC attach × moderate base size = moderate per-DLC revenue.

**Studio (Paradox CK3/Stellaris/EU4/HOI4):**
- Cadence: 2-4 DLC per year.
- Per-DLC attach %: 10-40% range (decays across catalog age).
- Catalog ceiling: 30+ SKUs over 6-10 year post-launch life.
- Pricing: tiered ($6.99 flavor / $9.99 story / $14.99 mid / $19.99 expansion / $29.99 ceiling).
- Revenue model: moderate per-DLC attach × large base size × many SKUs = high cumulative revenue.

**Studio (Creative Assembly Total War):**
- Cadence: 5-10 DLC per Total War title over 3-5 year post-launch life, plus new mainline titles.
- Per-DLC attach %: 15-40% range.
- Pricing: $7.99-$19.99 mid-tier dominant.
- Revenue model: AAA base ($59.99) × moderate per-DLC attach × many SKUs × franchise multi-title aggregation.

**Substrate input for Ouroboros:** Ouroboros' planned indie scale (per kickoff brief context, team size implied by CLAUDE.md "indie" framing) sits closer to solo-dev / Worldwalker-scale than to Paradox-studio scale. Per-era DLC cadence at 1-2 years per era is consistent with solo-dev observed cadence. The 7-era finite ladder requires 7-14 years of post-launch development at solo-dev cadence — long-tail planning constraint. Confidence: REPORTED.

## Ouroboros 7-era ladder revenue floor/median/ceiling estimates

Substrate inputs only — Research Lane does not pick. All figures ESTIMATED. Conditional on:
- Base owner count: 80k floor / 140k median / 200k ceiling (per kickoff brief)
- Base price: $25 floor / $30 median / $35 ceiling
- Per-era DLC price: $14.99 mid-tier / $19.99 expansion-tier / $24.99 RimWorld-flat
- Active-base at DLC launch: 30% floor / 50% median / 70% ceiling (re-engagement-inflated)
- Per-era attach against active: 25% floor / 40% median / 55% ceiling
- Roman free era serves as discovery anchor — does NOT generate direct DLC revenue but expands base reach (free-to-paid conversion modeled separately in T-M1)

**Per-era-1 paid DLC gross revenue estimate (first paid era after Roman free anchor):**
- Floor: 80k × 30% active × 25% attach × $14.99 = $89,940
- Median: 140k × 50% active × 40% attach × $19.99 = $559,720
- Ceiling: 200k × 70% active × 55% attach × $24.99 = $1,923,231

**Per-era decay assumption (Stellaris-shape, monotonic decline 70%-50%-35%-25%-20%-15% across eras 1-6):**
Cumulative 6-paid-era DLC gross revenue:
- Floor: ~$330,000
- Median: ~$2.0M
- Ceiling: ~$7.0M

**Per-era decay assumption (RimWorld-shape, flat-with-variance averaging 40% attach across eras 1-6):**
Cumulative 6-paid-era DLC gross revenue:
- Floor: ~$430,000
- Median: ~$3.4M
- Ceiling: ~$11.5M

All figures ESTIMATED. Gross revenue before platform cut (~30% Steam), refund (~5-10% per T-refund-norms), VAT/regional pricing adjustments. Net revenue floor roughly 50-60% of gross.

Bundle SKU revenue not modeled separately above — if Ouroboros ships a 6-paid-era "Eras Pass" bundle at 20-30% discount, pre-buy revenue may shift the timing curve forward but does not materially change cumulative ceiling. Confidence: ESTIMATED.

**Critical sensitivity:** the model is most sensitive to the **active-base at DLC launch** assumption. If Ouroboros maintains a strong free-patch + Roman-free-era re-engagement cadence, active-base can hit 70%+ at era launches (RimWorld-shape). If Ouroboros' free Roman era underperforms as a discovery anchor, active-base may sit at 20-30% by era 3+. The 3x spread between floor and ceiling is dominated by this assumption. AMBIGUOUS.

## Conflict surfaced

Bible context per kickoff brief:
- 80-200k base @ $25-35 is the bible-locked sizing target.
- 7-era ladder + Roman free anchor is bible-locked monetization shape.
- `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) L274 "Free to play. Infinite eras." tagline conflicts with the paid-base assumption (already flagged in sibling brief `dlc_pricing_ladders.md`).

Conflict surfaced specific to attach-rate modeling:

**Conflict A: "Infinite eras" tagline vs 7-era finite ladder.** If Ouroboros ships eras 8-14 as additional post-launch DLC beyond the bible-locked 7-era ladder, attach-rate decay extends accordingly. Stellaris-shape decay would suppress attach below 15% by era 8+. The "infinite eras" tagline may imply a sustaining-content model that requires either (a) sub-monthly cadence at solo-dev impossible scale or (b) procedurally generated era content with low marginal cost. Source: bible L274. Resolution: bible authority. AMBIGUOUS.

**Conflict B: Roman-free discovery anchor vs cosmetic-tier conversion model.** Per `dlc_pricing_ladders.md` Conflict 2, the bible's Fortnite "master brand + seasonal variant" L292 framing implies a cosmetic-driven engagement model. The cosmetic-tier attach 5-20% in this brief sits well below the 40-55% per-era attach assumed in the revenue model. If Ouroboros' Roman-free model functions like cosmetic-conversion (PoE/Warframe 2-10% conversion floor) rather than discovery-to-paid (Game-Pass-to-DLC conversion ESTIMATED 20-30%), revenue floor drops 3-5x. Source: sibling brief Conflict 2, bible L292. Resolution: bible + Design Lane. AMBIGUOUS.

**Conflict C: 80-200k base vs Paradox/RimWorld reference scale.** Ouroboros' bible-locked 80-200k base sits 1-2 orders of magnitude below the Paradox/RimWorld reference scales (1M+ to 3-5M). At this base size, even ceiling attach % multiplies to absolute revenue far below the Paradox/RimWorld revenue scales used as substrate above. The attach % patterns transfer; the absolute revenue numbers do not. This is a calibration warning not a conflict — Design Lane should not over-anchor on Paradox-scale DLC revenue. REPORTED.

Bible wins on resolution per `CLAUDE.md` "If something in any other doc conflicts with the bible (hub or any spoke), the bible wins." Research Lane only flags.

## Caveats and confidence

Tag distribution: VERIFIED ~5% (RimWorld DLC dates and prices, Battle Brothers release, base-game review statuses). REPORTED ~30% (tier structures, pricing patterns, cadence observations, decay direction). ESTIMATED ~55% (all per-DLC attach %, achievement-% proxies, revenue model figures, free-to-paid conversion). AMBIGUOUS ~10% (cosmetic-tier attach floor, identity-deviation magnitude, denominator-disambiguated 60-80% claim, conflict resolution).

**Critical caveat 1: zero publisher discloses per-DLC attach.** Every attach % in this brief is third-party-estimated, achievement-proxy-derived, or analyst-inferred. The model floor is "no first-party data exists." Any Wave 4 capture that surfaces a Paradox GDC talk, investor presentation, or Ludeon developer post with directional attach figures would upgrade large fractions of this brief from ESTIMATED to REPORTED.

**Critical caveat 2: aggregator-independence.** SteamSpy, VGInsights, Gamalytic, Steam Revenue Calculator all scrape Steam upstream. Per memory `feedback_aggregator_independence.md`, these are effectively one channel for sourcing purposes. The "third-party estimates" cited above mostly trace to this single channel. TRUSTED-tier validation requires press release or financial filing — none available for the surveyed titles' per-DLC numbers.

**Critical caveat 3: denominator ambiguity.** Active-concurrent-player-window vs lifetime owners produces 2x-3x different attach numbers for the same purchase. Most published "60-80%" claims do not specify denominator. Revenue modeling for Ouroboros must specify denominator at every step.

**Critical caveat 4: WebFetch denied.** Late-catalog 2025-2026 entries (Cosmic Storms, Graveyard of Empires, Wandering Nobles, Pharaoh post-launch DLC, any new Old World DLC) carry ESTIMATED floor. Wave 4 with web access could verify.

**Critical caveat 5: EU4 and HOI4 inline references.** No dedicated game cards. Training-data inline floor. Wave 4 should add `eu4_dlc_ladder.md` and `hoi4_dlc_ladder.md`.

## Feeds Design Lane

- **T-CL2 (this brief):** the primary attach-rate data surface; floor/median/ceiling estimates for Ouroboros revenue modeling at 80-200k base @ $25-35.
- **T-M2 (per-era 7-tier DLC stress-test):** decay-curve analysis directly feeds the stress-test — Stellaris-shape vs RimWorld-shape decay produces 2x-3x different cumulative revenue. Solo-dev cadence (1-3 years per DLC) bounds the 7-era ladder ship timeline at 7-21 years. Identity-deviation under-attach signal feeds the "does each era feel sufficiently distinct" stress-test question.
- **Monetization revenue model (`bible_monetization`):** floor/median/ceiling figures above provide a substrate revenue band. Design Lane + bible authority pick the actual model.
- **T-P3 (DLC pricing ladders) cross-validation:** sibling brief holds the per-SKU price-point map; this brief validates the price-point picks against the attach signal they would produce. Cosmetic-tier 5-20% attach × $4.99 price = small per-SKU revenue; expansion-tier 30-50% attach × $19.99 price = order-of-magnitude larger per-SKU revenue. The pricing ladder pick determines which tier carries Ouroboros revenue.
- **T-M1 (free-tier precedents):** Roman-free discovery anchor conversion model. Cosmetic-conversion (PoE/Warframe 2-10%) vs Game-Pass-to-DLC (ESTIMATED 20-30%) is the key fork. AMBIGUOUS resolution.

## Open questions for further research

Six bullets:

- Paradox GDC talks / investor presentations 2019-2026 with directional per-DLC attach figures. Currently zero confirmed disclosure across all four Paradox titles. Would upgrade large fraction of brief from ESTIMATED to REPORTED.
- Ludeon / Tynan Sylvester public statements on RimWorld per-DLC attach. Open per `rimworld_dlc_ladder.md` line 89. Even single-expansion attach disclosure would calibrate flat-price model.
- Wildermyth / Worldwalker public statements on Omenroad attach rate. Currently AMBIGUOUS due to base-game owner-count uncertainty multiplying with per-DLC attach uncertainty.
- Total War Warhammer trilogy per-SKU attach disclosure. Aggregate trilogy-revenue estimates exist (`total_war_franchise.md` line 30) but per-SKU breakdown is not public. Most relevant Total War case for Ouroboros is per-faction race-pack attach since faction-loyalty parallels era-loyalty.
- Game Pass / Paradox Plus conversion gap. Direct-purchase DLC attach vs Game-Pass-source DLC attach delta. CK3 and Wildermyth both have Game Pass exposure. Critical for Ouroboros Roman-free-as-discovery conversion expectation. Open per sibling `dlc_pricing_ladders.md` line 261.
- Steam achievement-% proxy validation. A study comparing achievement-% proxy against confirmed DLC unit sales for any title would calibrate the proxy's bias direction. The proxy is presumed to underestimate but the bias magnitude is unknown. AMBIGUOUS.

## Sources

Training-data flagged throughout — WebFetch/WebSearch denied during capture. All per-DLC prices, dates, attach estimates, and revenue figures sourced from training-data references to Steam DLC catalog listings, Paradox press releases, publisher communications, Steam Spy / VGInsights estimates, Steam achievement page data, community Steam-forum and Reddit discussion, and analyst commentary.

Game-card cross-refs (Research Lane Wave 0 + Wave 3 captures, in this repository):

- `docs/legacy/games/ck3_dlc_ladder.md` — CK3 full tier structure, flavor-pack attach pattern, Royal Court 30-50% first-expansion estimate, subscription tension. Read in full.
- `docs/legacy/games/stellaris_dlc_ladder.md` — Stellaris 10-year catalog, three-tier structure, attach decay curve mid-catalog 20-35%, late-catalog 10-20%, cumulative-cost ceiling effect. Read in full.
- `docs/legacy/games/rimworld_dlc_ladder.md` — flat $24.99 four-expansion attach pattern (30-60% range with quality variance), re-engagement multiplier dynamic, Anomaly identity-deviation case. Read in full.
- `docs/legacy/games/wildermyth_omenroad.md` — single-DLC small-studio $9.99 attach 10-25%, identity-deviation case, cadence-ceiling constraint. Read in full.
- `docs/legacy/games/battle_brothers.md` — three-DLC small-studio catalog, ~$31M lifetime revenue (DLC/base split unknown), open question on attach. Read in full.
- `docs/legacy/games/old_world.md` — modest-scale dynasty-4X DLC catalog, attach estimates 25-40% first DLC, open question on DLC-mechanics depth. Read in full.
- `docs/legacy/games/total_war_franchise.md` — AAA-tier $59.99 base + $7.99-$19.99 DLC, Warhammer trilogy aggregate revenue estimates, Pharaoh underperformance signal. Read in full.

Sibling brief cross-ref:

- `docs/legacy/topics/dlc_pricing_ladders.md` — sibling brief holding the per-SKU price-point map. Read in full before writing this brief. The two briefs are paired — pricing ladders define the price-points, attach rates define the % conversion at each price-point.

EU4 and HOI4 inline references in this brief are training-data only — no dedicated game cards exist yet in `docs/legacy/games/`. Flag for Wave 4 capture.

Bible authority sources:

- `docs/bible/game_bible.md` — hub authority on conflict resolution.
- `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` (L274 "Free to play" tagline, L292 Fortnite reference, bible-locked 7-era + Roman-free + 80-200k base @ $25-35) — authority on the monetization shape, surfaced as conflict-input only above.

Memory cross-refs:

- `feedback_aggregator_independence.md` — SteamSpy / Gamalytic / VGInsights aggregator-independence caveat applied throughout.
- `feedback_scalable_over_easy.md` — substrate framing assumes Design Lane will default to long-term-correct over smaller-diff option.
- `feedback_no_skip_design_goals.md` — every bible directive in scope enumerated; default to include.
