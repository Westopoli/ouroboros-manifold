---
name: DLC Pricing Ladders
description: Per-DLC price ladder analysis across CK3 / Stellaris / EU4 / HOI4 / RimWorld / Wildermyth; flavor-pack tier; sub-pass uptake; bundle splits; feeds T-CL2 attach rates, T-M2 per-era 7-tier ladder stress-test, T-P2 launch discount, Ouroboros 7-era + Roman-free substrate.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 3 capture
---

# DLC Pricing Ladders

## What this brief is

Per-DLC price ladder survey across six niche-relevant titles: CK3, Stellaris, EU4, HOI4, RimWorld, Wildermyth (Omenroad). Pulls per-SKU price points, tier shapes (expansion / mid-tier / flavor / cosmetic), bundle and pass SKUs, subscription experiments, and reported attach signals. Cross-references the just-landed G-16 (Stellaris), G-17 (CK3), G-18 (Wildermyth Omenroad), G-19 (RimWorld), G-20 (free-anchor precedents) game cards. Feeds T-CL2 (DLC attach rates), T-M2 (per-era 7-tier ladder stress-test), T-P2 (launch discount norms), T-M1 (free-tier precedents), and the 7-era + Roman-free substrate lock pending in `bible_monetization`.

Non-recommendation disclaimer: Research Lane surfaces inputs, does not pick. Anything below that reads like a pick is data preserved from the cited source, not an endorsement. The Design Lane decides what shape Ouroboros' 7-era ladder takes; the bible (`docs/bible/game_bible.md` and `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)`) is the authority on conflicts surfaced below.

## Method

Sources: Steam DLC catalog listings (per-title), Paradox press releases and storefront organization, publisher communications (Ludeon, Worldwalker), SteamDB price history (where reachable in training data), and community discussion of attach rates. WebFetch denied during capture — every figure floors at REPORTED or ESTIMATED unless backed by widely documented public record (then VERIFIED). Pre-2018 price history patchy because SteamDB-era price tracking improved coverage from approximately 2018 forward; older catalog entries (EU4 2013-2017, Stellaris 2016-2017) carry weaker price provenance.

Game-card cross-refs read before writing this brief:
- `docs/legacy/games/ck3_dlc_ladder.md`
- `docs/legacy/games/stellaris_dlc_ladder.md`
- `docs/legacy/games/rimworld_dlc_ladder.md`
- `docs/legacy/games/wildermyth_omenroad.md`
- `docs/legacy/games/free_anchor_precedents.md`

EU4 and HOI4 do not yet have dedicated game cards in `docs/legacy/games/`. Figures below are training-data sourced, REPORTED floor, and should be confirmed against a Paradox catalog pull when a Wave 4 capture covers those titles.

## Paradox expansion-tier ladder

Paradox runs the most-developed multi-tier DLC ladder in the niche. Four titles surveyed; per-DLC price points and tier classification follow.

### Crusader Kings III (2020-2026)

Major Expansion tier: $29.99 launch (Royal Court February 2022, Roads to Power September 2024 at $19.99 — note Roads to Power is below the major-expansion ceiling, classified by Paradox marketing as a major expansion despite $19.99 sticker; ESTIMATED tier classification, AMBIGUOUS whether Paradox intended it as a step-down or as a price test). Confidence: REPORTED (per `ck3_dlc_ladder.md` lines 27-38).

Mid-tier Expansion: $14.99 (Tours & Tournaments May 2023, Legends of the Dead February 2024). Confidence: REPORTED.

Flavor Pack: $6.99 (Northern Lords March 2021, Fate of Iberia May 2022, Friends & Foes September 2022, Wards & Wardens August 2023, Wandering Nobles ~2025). Confidence: REPORTED for older entries, ESTIMATED for Wandering Nobles.

Cosmetic Pack: $4.99 (Tower of Domination ~2024). Confidence: REPORTED.

Three-tier ladder ($6.99 / $14.99 / $29.99) inside CK3 is the cleanest example in the Paradox catalog of intentional tier separation. Source: `ck3_dlc_ladder.md` line 22-24.

### Stellaris (2016-2026)

Full Expansion: $19.99 (Utopia 2017 through Galactic Paragons 2023). The Machine Age (May 2024) at $29.99 represents the first price-ceiling test for a Stellaris major expansion. Confidence: REPORTED, with The Machine Age $29.99 specifically VERIFIED (price increase widely commented on at launch).

Story Pack: $9.99 (Leviathans 2016, Synthetic Dawn 2017, Distant Stars 2018, Ancient Relics 2019, Toxoids 2022, First Contact 2023, Astral Planes 2023, Grand Archive 2024, Cosmic Storms early 2025). Confidence: REPORTED. Note Synthetic Dawn launched at Story Pack tier price but reclassified by some community sources as expansion-equivalent given its civics-overhaul depth — AMBIGUOUS reclassification.

Species Pack: $7.99 (Lithoids 2019, Necroids 2020, Aquatics 2021, Humanoids v2 2022). Confidence: REPORTED.

Total catalog approximately 30+ paid SKUs by early 2026. Source: `stellaris_dlc_ladder.md` line 61.

### Europa Universalis IV (2013-2024, EU5 2025)

Major Expansion tier: $19.99-$24.99. Notable entries: Cossacks (2015 $19.99), Mare Nostrum (2016 $14.99), Rights of Man (2016 $19.99), Mandate of Heaven (2017 $19.99), Third Rome (2017 immersion pack $9.99), Cradle of Civilization (2017 $19.99), Rule Britannia (2018 immersion pack $9.99), Dharma (2018 $19.99), Golden Century (2018 immersion pack $9.99), Emperor (2020 $19.99), Leviathan (2021 $19.99 — review-bombed at launch over bugs), Origins (2021 immersion pack $9.99), Lions of the North (2022 immersion pack $9.99), Domination (2023 $29.99), King of Kings (2024 $19.99). Confidence: REPORTED. ESTIMATED for exact launch prices on entries prior to 2018 — SteamDB coverage thinner pre-2018.

Immersion Pack tier (EU4-specific tier name, equivalent to Stellaris Story Pack): $9.99 typical. Six confirmed immersion packs in catalog.

Content Pack / cosmetic tier: $4.99-$7.99. Unit pack and music pack SKUs scatter through catalog. Confidence: REPORTED.

EU4 catalog approximately 30+ paid SKUs over 11-year DLC run before EU5 launch in November 2025. EU5 release ends EU4 DLC cadence. Confidence: REPORTED.

### Hearts of Iron IV (2016-2026)

Major Expansion (Country Pack tier, HOI4-specific framing): $19.99-$24.99. Notable: Together for Victory (2016 $14.99), Death or Dishonor (2017 $9.99), Waking the Tiger (2018 $19.99), Man the Guns (2019 $19.99), La Resistance (2020 $19.99), Battle for the Bosporus (2020 country pack $9.99), No Step Back (2021 $19.99), By Blood Alone (2022 $19.99), Arms Against Tyranny (2023 $19.99), Trial of Allegiance (2024 country pack $14.99), Götterdämmerung (2024 $24.99), Graveyard of Empires (2025 $29.99 — ESTIMATED, late catalog entry). Confidence: REPORTED for 2018-2024, ESTIMATED for 2025 entries.

Country Pack tier (HOI4-specific equivalent of flavor pack): $9.99-$14.99. Smaller-scope regional focus packs.

Cosmetic / Unit / Music packs: $3.99-$7.99 scattered across catalog. Confidence: REPORTED.

HOI4 catalog approximately 15-20 paid SKUs by early 2026. Smaller per-year cadence than Stellaris or CK3.

### Paradox tier summary

Tier price points cluster tightly across all four Paradox titles:
- Major Expansion: $19.99 modal, $29.99 ceiling (CK3 Royal Court, Stellaris Machine Age, EU4 Domination, HOI4 Götterdämmerung+Graveyard).
- Mid-tier / Immersion / Country Pack: $9.99-$14.99 band.
- Flavor / Story / Species Pack: $6.99-$9.99 band.
- Cosmetic / Unit / Music: $3.99-$7.99 floor.

Cross-title price-point discipline is high — players moving from Stellaris to CK3 see roughly the same tier prices despite different DLC catalog shapes. Confidence: REPORTED.

## Paradox flavor-pack / story-pack tier

The $4.99-$9.99 lower-tier sits at a deliberately accessible price point per `ck3_dlc_ladder.md` line 66: "the $6.99 entry point is low enough that casual fans buy flavor packs as 'supporting the devs' gestures, not just for content." Per-game patterns:

CK3 flavor packs ($6.99) target geography/culture niches inside the medieval timeline — Northern Lords for Norse players, Fate of Iberia for Iberian players, Friends & Foes for relationship-event players. Niche-targeted not era-targeted. Estimated attach 15-25% per pack with decay as catalog grows (`ck3_dlc_ladder.md` line 48). Confidence: ESTIMATED.

Stellaris story packs ($9.99) and species packs ($7.99) are the most numerous tier in that catalog. Story packs add event chains and minor mechanics; species packs add cosmetic + minor traits. Steam community language characterizes the lower tier as "flavor packs exist for revenue" (`stellaris_dlc_ladder.md` line 79). Confidence: REPORTED.

EU4 immersion packs ($9.99) are the closest EU equivalent — regional focus packs (Third Rome, Rule Britannia, Origins, Lions of the North). Region-targeted not era-targeted.

HOI4 country packs ($9.99-$14.99) are the smallest-scope HOI4 DLCs, often single-nation focal (Death or Dishonor, Battle for the Bosporus, Trial of Allegiance).

Common pattern across all four Paradox titles: lower-tier DLC fills cadence between major expansion releases and targets sub-audiences. Lower per-pack revenue but cumulative-catalog revenue is meaningful. Confidence: REPORTED.

## RimWorld DLC

Flat $24.99 across four expansions. Royalty (March 2020), Ideology (July 2021), Biotech (October 2022), Anomaly (April 2024). No flavor packs, no cosmetics, no story packs, no species packs. Source: `rimworld_dlc_ladder.md` lines 22-32. Confidence: VERIFIED.

Pricing rationale (interpreted from `rimworld_dlc_ladder.md` line 53): flat pricing signals consistent value. Each expansion at $24.99 tells the buyer "this is a real expansion, same size as the others." No tier-decision fatigue. The price is a quality signal.

Estimated attach rates per `rimworld_dlc_ladder.md` lines 36-39:
- Royalty: 30-40% (weakest reception of the four — psycast/royal-title additions polarized).
- Ideology: 40-60% (strongest community reception).
- Biotech: 35-55% (second-strongest, gene-modding appeals to RimWorld's systems-player core).
- Anomaly: 30-45% (tonal deviation toward survival-horror caused visible minority pushback).

All four attach figures ESTIMATED. Ludeon does not disclose per-DLC attach rates.

Why flat vs Paradox tiered: small-studio single-developer constraint. Tynan Sylvester ships one expansion per 12-18 months. A single principal designer cannot sustain a Paradox-shape catalog of 10+ SKUs per title. Flat pricing matches the single-tier development reality. Confidence: REPORTED.

Complete RimWorld catalog at full price: $34.99 base + 4 × $24.99 = $134.95. Uncomfortable but not prohibitive (contrast Stellaris full catalog ceiling $200+ flagged in `stellaris_dlc_ladder.md` line 59). Confidence: VERIFIED.

No bundle SKU, no season pass, no Game Pass exposure. Direct-purchase only, plus Steam sale bundles during sale events. Source: `rimworld_dlc_ladder.md` lines 43, 77.

## Wildermyth Omenroad

Single major DLC: Omenroad (2024) at $9.99. Source: `wildermyth_omenroad.md` lines 13-17. Confidence: REPORTED (price and release year from training data, not independently verified).

Base game Wildermyth $24.99. Omenroad priced at less than half the base game, below standard Paradox expansion tier, above cosmetic tier — `wildermyth_omenroad.md` line 46 frames the $9.99 point as "easy yes" zone for fans.

Attach rate not publicly disclosed. ESTIMATED 10-25% of active players (`wildermyth_omenroad.md` line 26). AMBIGUOUS — Worldwalker has not published attach figures, base game owner count itself is 500k-1M estimate range.

Worldwalker is small-team scale (2-5 developers per `wildermyth_omenroad.md` line 28). Single DLC over three-plus years of post-launch support is the maximum cadence at that team size. For Ouroboros' planned 7-era ladder, Omenroad cadence implies 7 × 3 years = 21 years to ship full ladder at Worldwalker-equivalent throughput. Source-derived inference, ESTIMATED.

Reception nuance (`wildermyth_omenroad.md` line 24): Omenroad chose roguelite mode rather than additional authored campaigns. Community reception "Very Positive" — strong but not the base game's "Overwhelmingly Positive." Identity-deviation pattern: DLC that extends core identity attaches better than DLC that adds a mechanically adjacent mode. Direct parallel to RimWorld Anomaly's tonal-deviation finding.

## "DLC priced above base game" pattern

Paradox flavor and story packs at $6.99-$9.99 sit below base game price ($39.99-$49.99 for CK3/Stellaris/EU4/HOI4). No "DLC priced above base game" Paradox case in the surveyed catalog at sticker.

Total catalog price above base game: yes, all four Paradox titles. Stellaris full catalog $200+ at full price vs $39.99 base. CK3 full catalog approximately $150+ at full price vs $49.99 base. EU4 full catalog $300+ at full price vs $39.99 base. HOI4 full catalog approximately $200+ at full price vs $39.99 base. Confidence: REPORTED (rough catalog-sum math).

Niche reaction: documented "DLC fatigue" language in Stellaris reviews (`stellaris_dlc_ladder.md` line 59) by late catalog (2022-2024). Paradox Plus subscription was partly a response — give access to historical DLC without forcing buyers to face the $200+ sticker. Confidence: REPORTED.

Review-bombing precedent: EU4 Leviathan (2021) was review-bombed at launch — primarily over bugs at release, not pricing directly, but the bug-driven bombing was sharper because Leviathan was a $19.99 major expansion in a series with mature catalog. The pricing context amplified the bug reception. Confidence: REPORTED. AMBIGUOUS whether pricing or quality drove the bombing — likely both.

CK3 Royal Court (2022) launched at $29.99, the first CK3 expansion to hit that price ceiling. Community reception was mixed at launch — 3D throne room rendering received "is this what we waited two years for" pushback before the deeper grandeur mechanics landed in patches. Pricing-vs-value tension is documented. Confidence: REPORTED.

No catastrophic "DLC priced above base" rejection cases in the surveyed catalog. The niche accepts cumulative high catalog cost more readily than a single high sticker. Confidence: REPORTED.

## Bundle vs à-la-carte revenue split

Paradox routinely sells Expansion Pass / Chapter Pass bundles. CK3 Chapter Passes bundle a major expansion plus two or three smaller packs at $29.99-$39.99 for content that would cost $40-$55 individually (`ck3_dlc_ladder.md` line 42). Confidence: REPORTED.

Stellaris Expansion Pass bundles ($30-$60 range) bundle upcoming expansion with smaller packs (`stellaris_dlc_ladder.md` line 81). Confidence: REPORTED.

Bundle-vs-à-la-carte revenue split not publicly disclosed by Paradox for any title. AMBIGUOUS.

CK3 Royal Edition (a base + DLC bundle SKU) exists. Pricing has fluctuated, typically $79.99-$99.99 for base plus first wave of DLC. Confidence: REPORTED.

RimWorld bundles: Steam-sale-only base + DLC combinations. No publisher-curated season pass. No bundle pre-buy. Source: `rimworld_dlc_ladder.md` line 71. Bundle revenue at RimWorld likely a smaller fraction of total than at Paradox, given the absence of a pre-buy SKU. ESTIMATED.

Wildermyth: no Omenroad-inclusive bundle distinct from base + DLC Steam sale pairings. Single-DLC catalog does not require a bundle structure. AMBIGUOUS — Worldwalker may have shipped a discounted pairing during sales not documented in training data.

Cross-cutting: bundles capture pre-buy revenue (buyer commits to future content at a discount, reducing per-item decision friction) but also lock in a specific catalog roadmap that the developer must deliver. Paradox uses bundles aggressively; RimWorld and Worldwalker do not. The trade-off is pre-buy revenue vs roadmap flexibility. Confidence: REPORTED.

## Subscription-pass patterns

Paradox Plus (also called Paradox Grand Strategy subscription / Paradox subscription at different windows) is the explicit subscription experiment in the niche. Monthly fee approximately $4.99-$9.99 (varies by tier and window). Provides rotating access to base games plus older DLC for included titles. Confidence: REPORTED (`stellaris_dlc_ladder.md` line 63, `ck3_dlc_ladder.md` line 46).

Uptake: not publicly disclosed by Paradox. AMBIGUOUS. Community signal suggests adoption is non-trivial but a minority of Paradox player base. Paradox has not killed the program, which is a directional positive signal for uptake; but Paradox has also not made it the primary purchase model, which is a directional ceiling signal. Confidence: ESTIMATED.

Adoption resistance: documented in CK3 and Stellaris community discussion (`ck3_dlc_ladder.md` line 74). Players who paid $29.99 for Royal Court see it included in subscription after a window, perceiving devaluation. Subscription-vs-individual-purchase tension is a known friction in the Paradox model. Confidence: REPORTED.

CK3 has been available via Xbox Game Pass / PC Game Pass at various windows (`ck3_dlc_ladder.md` line 44). Game Pass affects base-game reach but Game Pass subscribers convert to DLC at lower rates than direct-purchase owners. Confidence: REPORTED. Exact conversion-rate gap not publicly disclosed.

RimWorld has no subscription, no Game Pass. Direct-purchase only. Source: `rimworld_dlc_ladder.md` line 77.

Wildermyth has no subscription. Has appeared on Xbox Game Pass / PC Game Pass at points; conversion data not disclosed.

Albion Online's Premium subscription ($9.99/month, soft-mandatory competitive advantage) is the closest non-Paradox subscription precedent in the cross-referenced cards (`free_anchor_precedents.md` line 60). Hardcore niche audience converts to subscription at ESTIMATED 20-35% of active players — much higher than broad F2P 2-10% conversion baseline.

Subscription model uptake range across the surveyed precedents: 2-35% of active players, varying massively by audience type. Niche-hardcore audiences subscribe more reliably than broad casual audiences. Confidence: ESTIMATED.

## DLC price-increase frequency over catalog lifetime

Paradox: nominal prices flat across catalog lifetime, real-dollar prices declining due to inflation. The Machine Age (Stellaris 2024 at $29.99) is the first explicit nominal price increase above the $19.99 major expansion ceiling that held 2017-2023 — a six-year flat-nominal window. Domination (EU4 2023 at $29.99) is the EU equivalent. Confidence: REPORTED.

CK3 has not raised the $29.99 major expansion ceiling since Royal Court (2022). Flat-nominal for four years. Mid-tier ($14.99) and flavor-pack ($6.99) tiers held flat across the entire CK3 catalog. Confidence: REPORTED.

RimWorld: flat $24.99 across all four expansions over 2020-2024 catalog window. Zero nominal price increases. Source: `rimworld_dlc_ladder.md` line 33. Confidence: VERIFIED.

Wildermyth Omenroad: single DLC, no price-history pattern to observe.

Pattern: Paradox-niche tolerance for price increases is low. Stellaris held $19.99 ceiling for six years before testing $29.99. CK3 has not yet tested above $29.99. RimWorld has never raised. The niche treats price-increase tests as visible events that require justification (Machine Age's "this is a bigger expansion than usual" framing). Confidence: REPORTED.

Real-dollar decline: nominal-flat pricing across a 6-10 year catalog window equals a meaningful real-dollar decline given 2020-2026 inflation. Paradox absorbs this rather than passing it through to per-SKU prices. Confidence: REPORTED. AMBIGUOUS whether this is a deliberate strategy or a community-pressure equilibrium.

## Cross-cutting findings

Six bullets, what the niche tolerates vs revolts against based on the surveyed catalogs:

- **Tiered ladders are tolerated when tier boundaries are predictable.** CK3's $6.99 / $14.99 / $29.99 ladder works because buyers can predict roughly what tier a new DLC will land in based on its scope framing. Stellaris' less-disciplined accretion is more friction-prone but still tolerated. Confidence: REPORTED.
- **Flat pricing signals quality consistency.** RimWorld's flat $24.99 reduces per-purchase decision friction and signals "every expansion is the same size." Trade-off: no low-friction $6.99 entry point for casual fans. Confidence: REPORTED.
- **Cumulative catalog cost has a ceiling.** Stellaris hit "DLC fatigue" language in reviews around 15-20 paid items (`stellaris_dlc_ladder.md` line 99). Catalog-sum prices above $200 suppress new-buyer attach for individual items. RimWorld's 4-item catalog at $134.95 stays under this ceiling. EU4's $300+ catalog is over. Confidence: REPORTED.
- **Identity-deviation DLC under-attaches.** RimWorld Anomaly (tonal deviation toward horror) and Wildermyth Omenroad (mode deviation toward roguelite) both attached lower than identity-extending alternatives would have. The niche buys "more of what I loved," not "adjacent mode." Confidence: REPORTED.
- **Subscriptions exist but are not the primary model.** Paradox Plus did not displace per-DLC purchase. Game Pass exposure does not eliminate DLC sell-through (CK3 retains direct-purchase revenue despite Game Pass availability). Niche-hardcore audiences subscribe more reliably than broad audiences but neither replaces the à-la-carte SKU. Confidence: REPORTED.
- **Price-increase tests are slow and visible.** Stellaris held $19.99 for six years before $29.99. CK3 held $29.99 ceiling for four years and counting. The niche treats every nominal price jump as a referendum on the studio's relationship to its audience. Real-dollar decline absorbed by studios rather than passed through. Confidence: REPORTED.

## Ouroboros 7-era ladder implications

Substrate inputs only — Research Lane does not pick the per-era pricing.

Per-era $X tier reads against the precedents as follows:

- Major-expansion-tier per-era pricing ($19.99-$24.99): matches RimWorld's flat $24.99 model and Paradox's major-expansion-tier $19.99 modal. Six paid eras × $19.99 = $119.94 cumulative DLC. Below the Stellaris fatigue ceiling, comparable to RimWorld's $99.96 catalog DLC sum. Roman free tier makes per-era purchase a discrete content unlock per era. Confidence: REPORTED — data fits, decision is Design Lane's.
- Mid-tier per-era pricing ($9.99-$14.99): matches Paradox immersion-pack / story-pack tier. Six paid eras × $14.99 = $89.94 cumulative. Lower per-era revenue but higher per-era attach (more casual purchases at lower price). Confidence: REPORTED.
- Flat per-era vs scaling per-era: RimWorld flat-pricing precedent supports a flat per-era price; Paradox tiered-pricing precedent supports varying per-era price by content scope. Indie scale (`wildermyth_omenroad.md` line 28 ~2-5 developers) tilts toward flat by execution constraint — varying per-era scope assessment requires more upfront design clarity than Worldwalker-scale studios typically carry. AMBIGUOUS — depends on Ouroboros' realized studio scale at DLC cadence.

Bundle SKU shape: a 7-era "Eras Pass" bundling all six paid eras at a discount is the Paradox Chapter Pass / Expansion Pass equivalent. Pre-buy revenue captures interested buyers at a single decision moment. Trade-off: locks the 7-era roadmap into a delivered-content commitment. Confidence: REPORTED.

Roman free tier as discovery surface: `free_anchor_precedents.md` line 109 frames the free-anchor-as-trial pattern — "free Roman era functions as a discovery trial leading to paid DLC purchase rather than a permanent free tier leading to cosmetic conversion." This is closer to a demo / extended-free-trial model than a true F2P model. Conversion math is not the PoE/Warframe 2-10% cosmetic-only conversion; it is closer to Game-Pass-to-DLC conversion (lower than direct-purchase but non-trivial). Confidence: ESTIMATED. AMBIGUOUS — no direct precedent in the cross-ref cards for "free permanent base era + paid expansion eras." This shape is novel.

Roman-free framing as substrate input: flagged as substrate, NOT a Research Lane pick. The bible's authority sits with `bible_monetization` once locked. Currently per the kickoff brief, "buy-once base @ $25-35 + DLC-per-era (7 eras, Roman free-tier)" is bible-locked, with the L274 "Free to play. Infinite eras." tagline conflicting internally with the paid-base assumption. See Conflict surfaced below.

## Conflict surfaced

Bible context per kickoff brief:
- `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) L274 "Free to play. Infinite eras." tagline.
- `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) L292 Fortnite "master brand + seasonal variant" reference.
- Bible-locked monetization: buy-once base @ $25-35 + DLC-per-era (7 eras, Roman free-tier).

Conflict 1: L274 "Free to play" tagline conflicts internally with the paid-base ($25-35) assumption in the bible-locked monetization model. T-P1 is already surfacing this; this brief notes it as substrate. The precedents above (PoE/Warframe pure-F2P vs RimWorld/Paradox premium-DLC) do not bridge cleanly — "free to play" as a marketing tagline does not match the surveyed indie premium-DLC model. Resolution requires either (a) Roman-free as a permanent free tier with sufficient content to honor "free to play" framing while paid eras follow, or (b) tagline revision. Research Lane surfaces; Design Lane + bible authority resolve. Confidence: AMBIGUOUS.

Conflict 2: L292 Fortnite "master brand + seasonal variant" framing partially collides with the surveyed niche tolerance pattern. Fortnite's seasonal-variant model assumes (a) very large player base churning seasons, (b) low per-season commitment cost, (c) cosmetic-driven engagement. The surveyed niche (CK3/Stellaris/EU4/HOI4/RimWorld/Wildermyth buyers) does not fit any of those three premises. Seasonal-variant framing transplanted to a 7-era ladder risks the identity-deviation penalty documented in RimWorld Anomaly and Wildermyth Omenroad cases — the niche may read "seasonal variant" as a tonal violation rather than a master-brand benefit. Confidence: REPORTED. AMBIGUOUS whether the L292 reference is meant literally or as a structural-only analog.

Bible wins on resolution per `CLAUDE.md` "If something in any other doc conflicts with the bible (hub or any spoke), the bible wins." Research Lane only flags.

## Caveats and confidence

Tag distribution across this brief: VERIFIED ~10% (RimWorld dates and pricing, Paradox tier-structure observation, PoE cosmetic-only model). REPORTED ~65% (most per-DLC prices, tier classifications, bundle structures, subscription existence). ESTIMATED ~20% (attach rates, conversion rates, catalog-sum math, late-catalog entries, novel-model fits). AMBIGUOUS ~5% (unresolved tier classifications, subscription uptake figures, bundle revenue splits, novel-shape precedent matching).

Price history pre-SteamDB-2018 is patchy; EU4 entries from 2013-2017 and Stellaris entries from 2016-2017 carry ESTIMATED floor on launch price. Confirmation against a Paradox catalog pull would tighten these to REPORTED.

WebFetch denied during this capture — every figure floors at training-data confidence. A Wave 4 capture with web access could verify late-catalog 2025-2026 entries (Cosmic Storms, Graveyard of Empires, Wandering Nobles), confirm Paradox Plus current pricing, and pull SteamDB price history for the older entries.

EU4 and HOI4 do not yet have dedicated game cards. Wave 4 work to add `eu4_dlc_ladder.md` and `hoi4_dlc_ladder.md` would let cross-references in this brief resolve to actual cards rather than training-data inline.

## Feeds Design Lane

This brief feeds:

- **T-CL2 (DLC attach rates):** per-tier attach signals across the four Paradox titles plus RimWorld plus Wildermyth; flat-vs-tiered attach pattern; identity-deviation under-attach signal (Anomaly, Omenroad).
- **T-M2 (per-era 7-tier ladder stress-test):** the data substrate for "what tier does each era land in, what cumulative catalog cost does the player see, where is the fatigue ceiling." CK3 tier discipline plus RimWorld flat pricing plus Stellaris catalog-ceiling warning are the three load-bearing precedents.
- **T-P2 (launch discount norms):** Paradox launch-discount cadence (typically 10% launch-week off for new DLC, larger discounts at franchise sales) is the niche-standard pattern. RimWorld and Wildermyth do not discount at launch — full price holds at launch, sale discounts apply later. This brief does not deep-dive launch discounts (out of scope for this topic) but flags the pattern split.
- **T-M1 (free-tier precedents):** Roman-free-tier substrate via `free_anchor_precedents.md` cross-ref; Albion niche-tribe subscription pattern as nearest analog; PoE/Warframe pure-F2P as ceiling.
- **7-era ladder bible-lock in `bible_monetization`:** substrate for the per-era price-point pick, the bundle-SKU pick (Eras Pass vs à-la-carte only), the subscription-pass pick (Paradox-Plus analog vs no subscription).

## Open questions for further research

Six bullets:

- EU4 and HOI4 dedicated game cards — captured in this brief inline as training-data prices; Wave 4 should resolve to full cards with SteamDB price-history confirmation for pre-2018 entries.
- Paradox per-DLC attach rate disclosure — any GDC talk or investor presentation 2019-2026 that includes directional attach figures for Royal Court, The Machine Age, or any individual DLC would substantially upgrade T-CL2 from ESTIMATED to REPORTED.
- Paradox Plus subscription uptake — published or leaked figures for monthly subscriber count, retention rate, and DLC-attach impact on subscribers vs non-subscribers. Currently AMBIGUOUS across all four Paradox titles.
- Game Pass conversion gap — quantified delta between direct-purchase DLC attach and Game-Pass-source DLC attach. CK3 and Wildermyth both have Game Pass exposure; comparison would calibrate Ouroboros' Roman-free-as-discovery conversion expectation.
- Bundle vs à-la-carte revenue split — any Paradox disclosure of Chapter Pass / Expansion Pass revenue share vs individual DLC sell-through. Currently AMBIGUOUS across all surveyed titles.
- RimWorld decision-not-to-bundle and decision-not-to-cosmetic — Tynan Sylvester's public statements on these design choices would clarify whether the simplicity is a values decision, business decision, or audience-fit decision. Direct relevance to Ouroboros' bundle-SKU pick.

## Sources

Training-data flagged throughout — WebFetch denied during capture, all per-SKU prices and dates sourced from training-data references to Steam DLC catalog listings, Paradox press releases, publisher communications, SteamDB price tracking (where reachable in training data), and community Steam-forum discussion.

Game-card cross-refs (Research Lane Wave 0 captures, in this repository):

- `docs/legacy/games/ck3_dlc_ladder.md` — CK3 full tier structure, flavor-pack pattern, Chapter Pass shape, subscription tension. Read in full before writing this brief.
- `docs/legacy/games/stellaris_dlc_ladder.md` — Stellaris 10-year catalog, three-tier structure, attach decay curve, Paradox Plus subscription, DLC fatigue at 15-20 SKUs. Read in full.
- `docs/legacy/games/rimworld_dlc_ladder.md` — flat $24.99 four-expansion model, no-bundle / no-cosmetic precedent, retention-multiplier dynamic, Anomaly identity-deviation case. Read in full.
- `docs/legacy/games/wildermyth_omenroad.md` — single-DLC small-studio $9.99 model, roguelite identity-deviation case, single-developer cadence ceiling. Read in full.
- `docs/legacy/games/free_anchor_precedents.md` — PoE/Warframe/Albion F2P + paid-content shapes, niche-tribe subscription receptivity, free-anchor as discovery surface vs revenue model. Read in full.

EU4 and HOI4 inline references in this brief are training-data only — no dedicated game cards exist yet in `docs/legacy/games/`. Flag for Wave 4 capture.

Bible authority sources:

- `docs/bible/game_bible.md` — hub authority on conflict resolution.
- `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` (L274 tagline, L292 Fortnite reference, bible-locked 7-era + Roman-free model) — authority on the monetization shape, surfaced as conflict-input only above.
