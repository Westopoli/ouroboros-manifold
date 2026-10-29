---
name: Localization Priority Slate
description: Per-language ROI estimates for niche-strategy paid-base titles at 80-200k @ $25-35 base. Catalogues Simplified Chinese, Russian, German, French, Spanish (LatAm/Spain), Brazilian Portuguese, Polish, Japanese, Korean, plus Italian/Turkish/Czech/Hungarian long-tail. Cross-axes: ROI methodology, day-1-paid vs delayed-paid vs community-mod tiering, T-A3 demographic remainder map, Foundation TV S3 geographic reach, 7-era DLC localization-debt compounding. Feeds T-L2 platform pick, monetization revenue model, engineering scope for localization pipeline, T-M2 DLC stress-test, Steam storefront tag/category locking.
type: topic_brief
captured_at: 2026-05-18
contributor: Research Lane T-L1 sub-agent (no web access — REPORTED/ESTIMATED floor)
---

# Localization Priority Slate

## What this brief is

Per-language ROI sizing for niche-strategy paid-base titles at the 80-200k unit @ $25-35 base price band. Ouroboros = solo or very-small-team, generational/legacy primary tribe + Foundation/hard-SF secondary, Roman-free baseline + 7-era paid DLC, structural localization-debt (every era expansion compounds the per-language translation burden).

Brief catalogues ten priority-candidate languages plus a long-tail cluster. Per-language section gives: market size signal, niche-strategy precedent ranking, ARPU/conversion-lift shape, translation-cost estimate, infrastructure modal (day-1-paid / delayed-paid / community-mod), known risks. Cross-axes after the per-language pass: ROI methodology, tiering shape, T-A3 demographic remainder, Foundation TV S3 reach, 7-era DLC debt compounding.

Brief is non-recommendation. Research Lane surfaces tiers and trade shapes. Design Lane picks the slate.

WebFetch/WebSearch denied this session. All figures REPORTED or ESTIMATED at floor confidence. No VERIFIED claims appear — sales-lift multipliers, market-share percentages, ARPU numbers all draw from sub-agent training-cutoff recall of publisher post-mortems, Steam Hardware Survey snapshots, Gamalytic/SteamSpy aggregate signal (aggregator-independence caveat per user memory: Gamalytic/SteamSpy/games-stats.com/Steam Revenue Calculator collapse to ~1 channel because they all scrape Steam upstream). Promote to VERIFIED only via publisher press release or financial filing.

## Method

Per-language ROI sized as:

`incremental_units = base_units × (language_share_of_genre_TAM) × (conversion_lift_multiplier)`

`incremental_revenue = incremental_units × language_ARPU × (1 − Steam_cut − regional_pricing_discount)`

`per_language_cost = base_translation_cost + (era_count × era_string_drift_cost) + ongoing_QA_review_cost`

`ROI = incremental_revenue / per_language_cost`

Inputs each have wide error bars. `language_share_of_genre_TAM` is the share of the niche-strategy-buying audience that prefers/requires native-language UI; this is genre-specific (grand-strategy skews more English-tolerant than colony-sim or visual-novel). `conversion_lift_multiplier` is the wishlist-to-purchase delta when storefront and game are localized vs English-only — REPORTED 1.2x to 3x for high-priority languages in strategy/sim per scattered publisher post-mortems. `language_ARPU` deflates against base price for regional-pricing markets (Russia historically ~60% of US, LatAm ~50-65%, China ~50-70%, varies by title).

`base_translation_cost` for an Ouroboros-scale string corpus (ESTIMATED 30,000-80,000 source words at full content density per `community_translation_infrastructure.md`) runs $2,400-$20,000 per language at professional agency rates of $0.08-$0.25/word. ESTIMATED. Community translation collapses base cost to platform spend ($0-$500/month) plus dev ops time, but adds QA risk and completion-percentage variance.

`era_count × era_string_drift_cost`: Ouroboros has 7 paid-DLC eras post-launch. If each era adds ~5,000-15,000 new source words (event flavor, faction names, tech/system text, tooltip/UI strings), ESTIMATED per-language re-translation cost per era is $400-$3,750 at professional rates. Compounded over 7 eras, per-language lifetime cost runs $2,800-$26,250 of additional translation spend after launch. Community pipeline collapses this to $0 incremental tooling but pushes contributor-fatigue risk over multi-year windows.

`Steam_cut` = 30% standard, drops to 25% above $10M lifetime revenue per title. Out of scope for per-language slate sizing — applies uniformly.

`regional_pricing_discount` per Steam's recommended regional pricing matrix (REPORTED): Russia ~40-50% discount off US price historically, China ~35-50% off, LatAm ~40-55% off, India ~50-65% off, Turkey ~50-70% off, Brazil ~45-55% off. This compresses per-unit revenue meaningfully for several of the priority languages.

Method assumes a single Steam storefront with multi-language interface — not multi-storefront (Epic, GOG) launches. Multi-storefront raises both opportunity and overhead but is out of T-L1 scope.

## Simplified Chinese

**Market size signal.** Steam's largest non-English language by user count since approximately 2017. REPORTED ~25-35% of Steam monthly active users select Simplified Chinese as interface language per Steam Hardware Survey, with the figure having dropped slightly post-2022 after Chinese government tightening of overseas-platform access but still the single largest non-English bucket. ESTIMATED.

**Niche-strategy precedent.** Crusader Kings 3, Stellaris, Europa Universalis 4, RimWorld, Manor Lords, Workers & Resources all have official Simplified Chinese. RimWorld's CN community is one of its largest. The grand-strategy/colony-sim cluster has strong CN tribe presence. REPORTED.

**Sales-lift shape.** REPORTED 1.5x-3x sales lift figures for grand-strategy adding Simplified Chinese exist in folk wisdom and scattered publisher quotes (Hooded Horse, Paradox, various indies). Lift is typically biggest at launch (Steam algorithm pushes localized titles in CN store) and decays as the title ages out of new-and-trending. Wishlist conversion in CN is REPORTED comparable to or higher than English baseline conditional on (a) interface localized, (b) Steam page localized, (c) Simplified Chinese tag and reviews present. ESTIMATED.

**ARPU shape.** Regional pricing discounts ~35-50% off US for CN per Steam recommended matrix. Effective per-unit revenue therefore ~$13-$23 on a $25-$35 base after discount. REPORTED. Volume offsets per-unit lower than English in many strategy/sim cases — total CN revenue can match or exceed German/French/Spanish combined for the genre. ESTIMATED.

**Translation cost.** Professional agency rates for English→Simplified Chinese typically $0.10-$0.25/source word; community-translator availability is high (RimWorld, Paradox titles all have active CN community translator pools). Base professional cost for Ouroboros corpus ESTIMATED $3,000-$20,000. Community-pipeline cost approaches zero plus tooling.

**Risks.** (a) **Banhammer / discoverability.** Steam's CN-side discoverability is sensitive to content flags and platform-policy compliance — historical post-2021 tightening around content categories (gore, politics, supernatural/horror, certain historical periods) has produced post-launch removal incidents for some titles. Ouroboros's Roman-free baseline + 7-era civilizational frame is unlikely to hit content flags but the eras themselves (especially anything resembling 20th-century political content) should be content-reviewed pre-launch. REPORTED. (b) **Refund/review-bombing patterns.** CN review-bomb incidents have historically been triggered by translation quality issues, perceived political content, or platform-policy events. Mitigation: ship professional or professional-reviewed CN, not raw community translation. REPORTED. (c) **Foundation TV S3 China reach.** Apple TV+ is not officially available in mainland China; Foundation S3 reach into the CN market is therefore via VPN-piracy or word-of-mouth from overseas viewership. ESTIMATED low direct halo into Ouroboros's CN-tribe surface vs the rest of Asimov-aware markets. The CN scifi-literary audience exists (Liu Cixin / Three-Body-Problem cohort, large and active) but Foundation-specific awareness is low relative to English-language markets.

**Tier signal.** REPORTED across niche-strategy publisher post-mortems: Simplified Chinese is the language with the strongest case for day-1 paid translation in this genre.

## Russian

**Market size signal.** Historically the second or third largest non-English Steam language by user count, REPORTED 8-12% of Steam MAU pre-2022. Post-2022 sanctions and Russian payment-card removal from Steam compressed effective addressable market significantly — REPORTED Steam suspended ruble pricing, removed Visa/Mastercard payment options for Russian accounts, restricted some titles from sale in Russia, and Russian Steam users shifted toward gift-purchasing, VPN-routing, or platform alternatives. ESTIMATED 30-60% reduction in addressable Russian sales-throughput vs pre-2022 baseline, with high variance per title.

**Niche-strategy precedent.** CK3, Stellaris, HOI4, EU4, Victoria 3 all have official Russian. The Paradox grand-strategy tribe in Russia is one of the strongest per-capita worldwide — REPORTED. RimWorld and similar colony-sims have active RU communities, often via community translation. Hearts of Iron 4 historically had outsized Russian playerbase.

**Sales-lift shape.** Pre-2022: REPORTED 1.3x-2x lift for grand-strategy adding Russian, with passionate community engagement on translation issues. Post-2022: lift compressed by payment friction, gray-market routing, and reduced wishlist conversion on Russian-language stores. ESTIMATED current 0.5x-1.3x of pre-2022 levels per title. Wide variance — some titles report negligible RU revenue post-2022, others report sustained community engagement even at reduced unit count.

**ARPU shape.** Regional pricing pre-2022 ~40-50% discount off US. Post-2022 Steam removed ruble pricing; current RU sales route through gift-purchasing, foreign-account workarounds, or platform alternatives, complicating per-unit revenue accounting. ESTIMATED effective ARPU $5-$15 on a $25-35 base for RU-region purchases — wide error bars.

**Translation cost.** Professional rates $0.08-$0.15/source word for EN→RU; large active community-translator pool for strategy/sim genres. Base professional cost ESTIMATED $2,400-$12,000.

**Risks.** (a) **Payment friction.** Steam's post-2022 RU payment infrastructure remains partially broken; commercial revenue capture is meaningfully degraded vs other major languages. REPORTED. (b) **Community-translation modal.** Russian community-translation pools are robust — Paradox-mod translation pattern for RU is very mature, and Crowdin-style RU community contribution is high-density. The infrastructure tier for RU is REPORTED low-friction if going community-pipeline. (c) **Political-content review-bomb risk.** RU community has historically review-bombed titles perceived as politically hostile; conversely titles perceived as Russia-neutral or Russia-favorable have benefited. Ouroboros's abstract-civilizational frame is low-political-content. ESTIMATED low risk. (d) **Sanctions/geopolitical drift.** The legal and platform status of selling to Russia may shift further; T-L1 planning should treat the RU revenue forecast as high-variance.

**Tier signal.** Strong community-translation case (high contributor density, low ops friction). Day-1 paid case is weaker than pre-2022 given payment-throughput degradation. Multiple titles in the niche-strategy space are taking the "ship community-translated Russian, accept variance" path.

## German

**Market size signal.** REPORTED 4-7% of Steam MAU select German interface; consistent second/third largest European-language bucket after English. German-speaking DACH region (Germany, Austria, Switzerland) is REPORTED the largest European single-language market for PC gaming by revenue.

**Niche-strategy precedent.** Field of Glory: Empires, Crusader Kings 3, Stellaris, Wildermyth, Workers & Resources, Manor Lords, Anno series all have official German. The grand-strategy/wargame/builder tribe in DACH is one of the strongest in Europe. REPORTED.

**Sales-lift shape.** REPORTED 1.2x-1.6x lift for grand-strategy adding German. DACH audience is REPORTED relatively English-tolerant compared to French or LatAm Spanish — many DACH strategy gamers will buy English-only — but native-German UI improves wishlist conversion and Steam algorithm placement in DE/AT/CH stores. ESTIMATED.

**ARPU shape.** Germany is full-EU-price tier — no regional discount. Per-unit revenue at full $25-35 base. REPORTED.

**Translation cost.** Professional rates $0.10-$0.20/source word for EN→DE. **Word-count expansion ~20%** vs English — German compound nouns and full grammatical inflection inflate the target word count, which also affects UI layout (long German strings break tooltips and buttons that English fits). REPORTED. Base professional cost ESTIMATED $3,000-$15,000 plus UI-layout testing overhead.

**Risks.** (a) **UI breakage from word expansion.** Implementer scope: every UI element needs to either accommodate ~25% string expansion or have a German-specific shorter variant. Cross-reference engineering scope per `community_translation_infrastructure.md`. (b) **DACH expectations of localization polish.** German-language reviews tend to call out translation quality more explicitly than some markets; raw machine translation or low-quality community translation generates negative reviews. ESTIMATED moderate QA-sensitivity. (c) **Niche-strategy DACH tribe is English-tolerant.** Some titles in the genre have shipped English-only and still done well in DACH — the floor on missing German is not catastrophic, unlike CN where missing localization significantly caps market reach.

**Tier signal.** Day-1 paid is the strong precedent for this genre. Delayed-paid is viable. Community-translation is risk-bearing because DACH audience is QA-sensitive but viable if a strong volunteer language-lead is available.

## French

**Market size signal.** REPORTED 3-5% of Steam MAU select French interface; the French-speaking market spans France, French-speaking Belgium, French-speaking Switzerland, Quebec, and parts of West Africa. Niche-strategy French audience is REPORTED slightly smaller than German for grand-strategy specifically.

**Niche-strategy precedent.** CK3, Stellaris, EU4, HOI4, Victoria 3 all have official French. RimWorld has community French. Paradox-titles are traditionally well-served in French. REPORTED.

**Sales-lift shape.** REPORTED 1.15x-1.4x lift for grand-strategy adding French. French audience is REPORTED somewhat less English-tolerant than DACH but more so than Spanish or Brazilian Portuguese — bilingual capacity is high in technical/strategy-gamer cohort. ESTIMATED.

**ARPU shape.** France full-EU-price tier. Per-unit revenue at full $25-35 base. REPORTED.

**Translation cost.** Professional rates $0.10-$0.20/source word for EN→FR. Word-count expansion ~10-15% over English. REPORTED. Base professional cost ESTIMATED $3,000-$15,000.

**Risks.** (a) **Quality expectations.** French audience is REPORTED among the more linguistically critical for game translation — Académie-française cultural context plus active gaming press in French amplifies QA sensitivity. Community-translation acceptability is moderate. (b) **Smaller commercial return than German for the genre.** REPORTED French grand-strategy market is approximately 70-90% of the German market size for this genre, ESTIMATED.

**Tier signal.** Day-1 paid for Paradox-traditional titles. Delayed-paid is acceptable for solo-dev scale. Community-translation works if a French language-lead emerges, with above-average QA pressure.

## Spanish (LatAm + Spain split)

**Market size signal.** REPORTED 3-6% of Steam MAU select Spanish interface. The Spanish-language audience splits geographically into Spain (~46M population, full-EU-price tier) and Latin America (~450M population across multiple countries, deep regional-pricing discount tier). ESTIMATED Steam Spanish-language users skew LatAm-majority by user count but Spain-leaning by revenue per user.

**Niche-strategy precedent.** CK3, Stellaris, EU4, RimWorld all have official Spanish (Latin America variant is most common). REPORTED. Wildermyth has community Spanish.

**Sales-lift shape.** REPORTED 1.2x-1.7x lift for adding Spanish, with the lift weighted toward LatAm wishlist conversion. Spain conversion is somewhat lower because Spain audience is REPORTED relatively English-tolerant. ESTIMATED. LatAm conversion lift is REPORTED among the larger relative lifts because LatAm Steam audience is less English-tolerant than DACH or Nordic markets and the wishlist density in LatAm is high for grand-strategy specifically (RimWorld, CK3, Stellaris LatAm tribes are large per various publisher mentions).

**ARPU shape.** Spain full-EU-price tier (~$25-$35 base). LatAm regional-pricing ~40-55% off US price → ~$13-$20 per unit. ESTIMATED weighted blended Spanish ARPU $15-$22 per unit if LatAm dominates unit volume. REPORTED.

**Translation cost.** Single Spanish (Latin America) translation typically covers both markets adequately; some publishers split LatAm and Spain (Castilian) translations for top-tier polish but most niche-strategy titles ship one Spanish track. **Cost-effective via single translator** — REPORTED. Professional rates $0.08-$0.18/source word for EN→ES. Base professional cost ESTIMATED $2,400-$13,500.

**Risks.** (a) **LatAm wishlist conversion concentration.** REPORTED LatAm wishlist density skews younger demographic, more price-sensitive, more refund-prone in some genres. Niche-strategy LatAm tribe is REPORTED relatively mature and well-converting but the broader pattern is worth flagging. (b) **Spain vs LatAm dialect choices.** Shipping one Spanish track means making a dialect call — most titles pick LatAm-neutral, some pick Castilian. The unchosen audience occasionally surfaces complaints. ESTIMATED low impact in this genre. (c) **Per-unit revenue compression.** Volume offsets per-unit lower than Northern Europe — total Spanish-track revenue is REPORTED comparable to or below German despite larger unit volume.

**Tier signal.** Day-1 paid is increasingly the niche-strategy norm because cost is moderate and reach is high. Community-translation is well-supported in the contributor base. Cost-effectiveness from single-translator coverage of both regional markets is the principal argument for this language.

## Brazilian Portuguese

**Market size signal.** REPORTED 2-4% of Steam MAU select Portuguese-Brazil interface. Brazil is consistently among the top 10 Steam markets by user count, often top 5. REPORTED. European Portuguese (Portugal) is a separate-but-related track typically not separately localized for niche games — most ship PT-BR only.

**Niche-strategy precedent.** RimWorld has strong PT-BR community translation. CK3, Stellaris, EU4 all have official PT-BR. REPORTED. The strategy/sim tribe in Brazil overlaps heavily with the global grand-strategy + colony-sim tribe per publisher mentions.

**Sales-lift shape.** REPORTED 1.3x-1.8x lift for niche-strategy adding PT-BR, with **high wishlist conversion** characteristic — PT-BR audience converts wishlists at above-average rates per several indie post-mortems. ESTIMATED. The pattern is partly genre-driven (colony-sim and grand-strategy are popular in Brazil) and partly price-sensitivity-driven (regional-discounted base price plus strong sale conversion).

**ARPU shape.** Brazil regional-pricing ~45-55% off US per Steam recommended matrix → ~$11-$18 per unit on $25-$35 base. REPORTED. **Lower ARPU** than full-price European tier but offset by high conversion rate.

**Translation cost.** Professional rates $0.08-$0.15/source word for EN→PT-BR; strong community-translator pool for strategy/sim. Base professional cost ESTIMATED $2,400-$10,000. RimWorld's PT-BR community translation is the canonical precedent that this market can be served well via community pipeline.

**Risks.** (a) **Lower per-unit revenue.** Volume must be substantial to compete with full-price European markets on absolute revenue. ESTIMATED. (b) **Refund-rate variance.** REPORTED Brazil has somewhat above-average refund rates in some genres; niche-strategy is less affected than action/adventure but worth flagging. (c) **Payment-method friction.** Steam's Brazilian payment options have historically been adequate but occasionally degrade — Boleto and PIX have been variably available.

**Tier signal.** Strong community-translation case (RimWorld precedent, high contributor density, high conversion lift relative to translation cost). Day-1 paid is viable if budget allows. Delayed-paid is acceptable. This language is REPORTED one of the higher-ROI community-translation targets for niche strategy/sim.

## Polish

**Market size signal.** REPORTED 1.5-3% of Steam MAU select Polish interface. Poland is REPORTED among the top 15 Steam markets globally, with disproportionate strategy/RPG enthusiasm per CD Projekt Red / Witcher / Cyberpunk legacy and the Frostpunk / This War of Mine indie-strategy cluster.

**Niche-strategy precedent.** CK3, Stellaris, EU4, HOI4 all have official Polish. The Polish grand-strategy tribe is REPORTED one of the most engaged per-capita worldwide. Polish indie-strategy output (Frostpunk, This War of Mine, Phantom Brigade) creates a robust local audience baseline. REPORTED.

**Sales-lift shape.** REPORTED 1.2x-1.5x lift for grand-strategy adding Polish. Polish audience is REPORTED less English-tolerant than DACH or Nordic markets, more so than France — bilingual capacity in strategy-gamer cohort is moderate. ESTIMATED.

**ARPU shape.** Poland regional-pricing ~30-40% off US per Steam matrix → ~$16-$25 per unit on $25-$35 base. REPORTED.

**Translation cost.** Professional rates $0.08-$0.16/source word for EN→PL. Polish has rich grammatical inflection (7 cases, gender, aspect) which produces fewer word-count expansion issues than German but more parameterized-string complexity (any string with a noun in any slot needs case-aware substitution). For Ouroboros's generative chronicle text this could be meaningful. ESTIMATED. Base professional cost $2,400-$13,000.

**Risks.** (a) **Inflection-heavy parameterized strings.** Wildermyth-style generative narrative makes Polish translation harder than fixed-script narrative; community translators familiar with strategy/sim conventions are available but the work-per-string is higher. ESTIMATED. (b) **TAM size.** Absolute Polish unit volume is medium-small; per-unit revenue is moderate. Total revenue per language typically below German and Spanish.

**Tier signal.** Community-translation is the dominant precedent for indie scale; day-1 paid is the Paradox-tier precedent. Polish is REPORTED a strong community-translation candidate because the Polish community is highly active and Polish is one of the most-translated mod languages for Paradox titles.

## Japanese

**Market size signal.** REPORTED 1-3% of Steam MAU select Japanese interface — Steam penetration in Japan is REPORTED lower than market share would suggest because console and mobile dominate Japanese gaming spend. Steam Japan has grown steadily but remains a smaller bucket than DACH or France for niche-strategy specifically.

**Niche-strategy precedent.** REPORTED CK3, Stellaris, Civilization VI all have official Japanese; Manor Lords, Workers & Resources, Wildermyth do not. Grand-strategy Japanese tribe is REPORTED small relative to Western markets — historical Koei Tecmo / Romance of the Three Kingdoms tradition exists but Western-grand-strategy adoption in Japan is modest. ESTIMATED.

**Sales-lift shape.** REPORTED 1.1x-1.3x lift for grand-strategy adding Japanese — lower than the major European languages because of the smaller addressable audience and the high English-tolerance of the Japanese Steam audience (Steam Japan users are REPORTED a self-selected English-tolerant cohort because Steam isn't the default Japanese gaming platform). ESTIMATED.

**Foundation/hard-SF tribe angle.** **Asimov has historical Japanese literary presence** — Foundation has been translated and reprinted in Japanese multiple times since the 1960s. Hayakawa Publishing's SF imprint has carried Asimov consistently. The Japanese hard-SF literary tribe is REPORTED active and overlapping with the broader Foundation/hard-SF audience. ESTIMATED. Foundation TV S3 reach into Japan is via Apple TV+ Japan (REPORTED available since 2019); audience size unknown but the platform-availability case is structurally stronger than for CN.

**ARPU shape.** Japan full-price tier or near-full — Steam recommended pricing in JPY converts to approximately full US-price-equivalent. REPORTED ~$25-$35 per unit on $25-$35 base.

**Translation cost.** **High translation cost** — REPORTED $0.12-$0.30/source word for EN→JA at professional rates, the highest cost band among the priority languages. Japanese community-translator pool for niche-strategy is REPORTED smaller than CN, RU, DE, FR community pools. Base professional cost ESTIMATED $3,600-$24,000.

**Risks.** (a) **High cost, low ROI for grand-strategy.** Sales lift × ARPU × unit volume is unlikely to recover the high translation cost for a niche-strategy title without strong secondary-tribe halo from Foundation IP awareness. REPORTED low-confidence ROI signal. (b) **Smaller community-translation contributor density.** Risk that community pipeline produces incomplete or stalled JA coverage. ESTIMATED. (c) **Vertical text and font issues.** Japanese game UI conventions sometimes diverge from European fonts and layouts — engineering scope is non-trivial.

**Tier signal.** REPORTED "skip-or-late" for the niche-strategy genre baseline. The Foundation/hard-SF secondary-tribe angle is the principal argument for elevating Japanese above the strict grand-strategy ROI signal — if Foundation S3 Japan reach produces measurable wishlist signal from Japanese surfaces, the case shifts upward. Sub-agent flags this as the language where T-L1 most depends on T-A2 / Foundation TV S3 input.

## Korean

**Market size signal.** REPORTED 1-2% of Steam MAU select Korean interface — Korea's gaming spend is dominated by mobile and free-to-play PC, with Steam a smaller-but-present slice. ESTIMATED Korean grand-strategy audience is **very small** in absolute terms.

**Niche-strategy precedent.** REPORTED Civilization VI has official Korean; CK3, Stellaris, EU4 do not officially support Korean (some have community translation mods, REPORTED active). RimWorld has community Korean. Korean grand-strategy tribe is REPORTED small but engaged, with high per-capita activity in the surfaces that do exist.

**Sales-lift shape.** REPORTED 1.05x-1.2x lift for grand-strategy adding Korean — small absolute lift, but **high ARPU when present**. Korean players who do buy niche-strategy titles are REPORTED among the higher-spending cohorts per indie publisher mentions. ESTIMATED.

**ARPU shape.** Korea full-price or near-full tier — ~$25-$30 per unit on $25-$35 base. REPORTED.

**Translation cost.** Professional rates $0.10-$0.22/source word for EN→KO. Community-translator pool for niche-strategy is small. Base professional cost ESTIMATED $3,000-$17,500.

**Risks.** (a) **Small absolute audience.** ROI math is structurally bad unless community-translation pipeline can deliver near-zero cost. (b) **Font and layout overhead.** Korean UI conventions add engineering scope similar to JA, somewhat less. (c) **High community-translation availability for Paradox titles but variable quality.** REPORTED mixed signal.

**Tier signal.** REPORTED **"skip-or-late"** for niche-strategy baseline. Community-translation modal is the most likely path if any KO coverage is targeted. Day-1 paid is REPORTED rare in this genre at the solo-dev / very-small-team scale.

## Italian / Turkish / Czech / Hungarian — long-tail

**Italian.** Approximately 1-2% of Steam MAU. Italy has a real strategy-gaming tribe (Total War, CK, Civ have decent IT presence) but TAM is medium-small. Professional cost $0.08-$0.18/word EN→IT, expansion ~10-15%. Community pool is moderate. ESTIMATED day-1 paid case is below DE/FR/ES/PT-BR. REPORTED community-translation precedent in Paradox-mod ecosystem is strong.

**Turkish.** Approximately 1-2% of Steam MAU but disproportionate growth post-2018 per regional pricing aggressive discounting (~50-70% off US). Turkish strategy-gaming tribe is REPORTED engaged for CK3/EU4/HOI4 specifically (Ottoman content is a strong draw, possibly relevant to Ouroboros's faction archetypes). Professional cost $0.08-$0.15/word EN→TR. Community pool moderate-to-strong. Per-unit revenue heavily compressed by regional discount (~$8-$15 per unit) — total revenue ROI is structurally weak unless volume is very high. ESTIMATED community-mod modal is the dominant precedent.

**Czech.** Approximately 0.3-0.7% of Steam MAU but disproportionate strategy/sim enthusiasm per Bohemia Interactive (Arma, DayZ) cultural baseline. Czech grand-strategy tribe is REPORTED small but devoted. Professional cost $0.08-$0.16/word EN→CS. Community pool small but active in Paradox-mod ecosystem. Per-unit revenue moderate. ESTIMATED community-mod modal.

**Hungarian.** Approximately 0.2-0.5% of Steam MAU. Hungarian grand-strategy tribe is REPORTED small but engaged, particularly for HOI4/EU4. Professional cost $0.08-$0.15/word EN→HU. Community pool small. ESTIMATED community-mod modal — Hungarian translation mods for Paradox titles are well-established.

**Tier signal for long-tail cluster.** Community-mod-only is REPORTED the dominant precedent across this cluster for niche-strategy at solo-dev / very-small-team scale. Day-1 paid is rare. Delayed-paid is rare. The pattern is: ship moddable string files, accept Workshop translation mods, credit modders, do not invest professional translation budget. Cross-reference `community_translation_infrastructure.md` for the mod-as-translation pattern.

## Cross-axis: ROI estimate methodology

The per-language sections above each have an implicit ROI calculation. Surfaced explicitly here:

**Step 1 — sized addressable audience.** Per-language Steam MAU share × niche-strategy genre concentration in that language. The genre concentration multiplier varies — REPORTED Russian, German, Polish, Brazilian Portuguese, French audiences are over-indexed for grand-strategy specifically vs Steam baseline. Simplified Chinese is over-indexed for colony-sim and grand-strategy. Japanese and Korean are under-indexed for grand-strategy specifically. The genre-concentration multiplier is REPORTED 1.2x-2.0x for over-indexed languages and 0.5x-0.8x for under-indexed.

**Step 2 — conversion-lift multiplier.** Wishlist conversion rate with native-language UI / Steam page / reviews vs English-only. REPORTED ranges:
- CN: 1.5x-3x lift (high)
- RU pre-2022: 1.3x-2x; post-2022: 0.5x-1.3x (degraded)
- DE: 1.2x-1.6x
- FR: 1.15x-1.4x
- ES (LatAm-weighted): 1.2x-1.7x
- PT-BR: 1.3x-1.8x (high relative)
- PL: 1.2x-1.5x
- JA: 1.1x-1.3x (low)
- KO: 1.05x-1.2x (very low)
- IT/TR/CS/HU: 1.05x-1.3x

**Step 3 — per-unit revenue.** Base price × (1 − regional discount) × (1 − Steam cut). Heaviest compression for RU, TR, BR, LatAm-ES. Full price for DE, FR, Spain-ES, PL (lightly discounted), JA, KO.

**Step 4 — translation cost.** Professional base cost $2,400-$24,000 per language depending on word count and rates; community-pipeline cost approaches zero plus tooling and ops time.

**Step 5 — DLC compounding.** Multiply ongoing per-language cost by 7-era expansion roadmap. Per-era re-translation cost $400-$3,750 professional; community pipeline near-zero per era but with contributor-fatigue risk over multi-year horizons. Cross-reference DLC localization-debt cross-axis below.

**Step 6 — ROI ranking.** ROI = (incremental_revenue) / (per_language_cost). The math produces a rough ranking that REPORTED across niche-strategy publisher post-mortems lands consistently as: CN > {DE, ES, PT-BR} ≈ tier-2 > {RU, FR, PL} ≈ tier-3 > {JA, KO} ≈ tier-4, with the long-tail cluster (IT, TR, CS, HU) below tier-4 unless community-mod modal collapses cost to zero. This ranking is highly sensitive to assumptions about CN content-policy risk, RU payment-throughput recovery, JA Foundation-tribe halo lift, and Workshop-mod infrastructure availability.

## Cross-axis: Day-1 paid vs delayed-paid vs community-mod tiering

Three infrastructure tiers per language:

**Day-1-paid.** Professional translation shipped at launch. Maximum reach, maximum launch-week algorithm boost in target store, maximum QA control. Cost: $2,400-$24,000 base + 7-era ongoing. Use case: REPORTED canonical for CN in this genre; defensible for DE, ES, PT-BR if budget allows; rare for everything else at solo-dev scale.

**Delayed-paid.** Launch English-only or English-plus-community; commission professional translation later when sales-data confirms language demand. Lower upfront cost, deferred algorithm boost, slower wishlist conversion in target market during early months. REPORTED pattern: Stardew Valley, many indie strategy/sim titles. Use case: viable for any priority language; standard for DE/ES/PT-BR/FR at solo-dev scale.

**Community-mod-only.** Never commission professional translation; rely on Workshop translation mods (if Workshop is supported per CL4) or Crowdin/POEditor/Weblate community-contributor pipelines (per T-L2). Zero or near-zero direct translation cost; ops time for contributor management; QA externalized to the community. REPORTED canonical for Paradox long-tail (Hungarian, Czech, Turkish, etc.) and dominant for niche-strategy at very-small-team scale across most non-CN languages.

The tiering decision intersects with T-L2 platform pick. If T-L2 picks Crowdin or Weblate, all three tiers are available. If T-L2 picks "no platform, Workshop-mod-only," then only the community-mod-only tier is technically supported and day-1-paid plus delayed-paid become limited to whichever language is professionally translated outside the platform (most likely CN if any).

## Cross-axis: T-A3 demographic remainder map

T-A3 demographics report REPORTED 65-85% of niche-strategy audience is NA + EU (English + DACH + France + LatAm-Spain + Nordic + UK). The remaining 15-35% maps approximately as follows. ESTIMATED:

- **CN-Asia.** Largest single non-NA/EU cohort. Simplified Chinese maps directly. ESTIMATED ~8-15% of the remainder.
- **LatAm.** Spanish (LatAm variant) + Brazilian Portuguese map here. ESTIMATED ~4-10% of the remainder.
- **Russia/CIS.** Russian maps here. ESTIMATED ~2-6% of the remainder, compressed post-2022.
- **Japan + Korea + Taiwan + SEA.** Japanese, Korean, plus Traditional Chinese (Taiwan/HK) and English-tolerant SEA audiences. ESTIMATED ~2-5% of the remainder.
- **Turkey + Middle East.** Turkish maps here, Arabic potentially relevant but rare in niche-strategy. ESTIMATED ~1-3% of the remainder.
- **Poland + Czechia + Hungary + adjacent Central Europe.** Polish dominant, Czech and Hungarian secondary. ESTIMATED ~2-5% of the remainder.
- **Italy.** Italian maps here. ESTIMATED ~1-3% of the remainder.

This mapping suggests the priority slate naturally clusters around Simplified Chinese (largest single non-EN/EU bucket), Russian + Spanish + Brazilian Portuguese (next-tier), then the European long-tail. Japanese/Korean align with the smaller Asia-Pacific bucket and depend heavily on whether secondary-tribe Foundation halo offsets low genre TAM. ESTIMATED.

## Cross-axis: Foundation TV S3 / Apple TV reach geographic spread (T-A2 input)

Foundation TV is on Apple TV+. Apple TV+ availability and reach per region is REPORTED:

- **NA + UK + Western Europe.** Apple TV+ broad availability; Foundation S1/S2 viewership concentrated here. REPORTED.
- **Latin America.** Apple TV+ available across most LatAm markets. ESTIMATED moderate Foundation reach.
- **Russia.** Apple TV+ withdrew from Russia 2022. REPORTED low direct Foundation reach into RU market via official channels.
- **China (mainland).** Apple TV+ not officially available. REPORTED low direct reach; some VPN-piracy access exists but the Asimov-aware audience in CN comes primarily from book-tradition (Hayakawa-equivalent CN imprint) and Liu Cixin / Three-Body cultural neighborhood rather than Foundation TV.
- **Japan.** Apple TV+ available; REPORTED moderate Foundation reach overlapping with the historical Hayakawa Asimov-reader cohort.
- **Korea.** Apple TV+ available; REPORTED low-to-moderate Foundation reach, smaller hard-SF literary tradition than Japan.
- **Brazil + Spanish LatAm.** Apple TV+ available; ESTIMATED moderate reach, Foundation-aware audience exists.
- **DACH / France / Poland / Italy / Turkey.** Apple TV+ available; ESTIMATED variable reach correlating with Apple TV+ subscriber density in each market.

Implication for T-L1: Foundation S3 halo lift is **strongest in NA/EU and Japan**, **weakest in CN and Russia**, **moderate in LatAm + DACH/FR/PL**. This argues for elevating Japanese in the slate above its strict grand-strategy-ROI ranking IF the Foundation secondary-tribe halo is load-bearing for the marketing pitch. Argues for not over-rotating toward CN-Foundation halo (the CN audience reach Foundation has there is via book-tradition rather than TV, and the Asimov-aware CN cohort is small relative to the Liu-Cixin / Three-Body cohort).

## Cross-axis: 7-era DLC localization-debt compounding (string-mass per era)

Ouroboros's 7-era paid DLC roadmap means localization is not a one-time cost but a compounding recurring cost. ESTIMATED per-era string-mass:

- **Per era new strings.** 5,000-15,000 new source words per era (faction names, event flavor, tech text, system messages, tooltip/UI strings for era-specific content). ESTIMATED. Generative chronicle text inflates the parameterized-substitution count per era.
- **Per-language per-era cost.** Professional: $400-$3,750. Community pipeline: $0 incremental tooling but contributor-fatigue risk across 7 release windows.
- **Lifetime per-language cost.** Professional, 7 eras: $2,800-$26,250 cumulative on top of base launch cost. Community pipeline, 7 eras: $0-$2,000 cumulative tooling cost plus dev ops time, with completion-percentage risk increasing per era.
- **Slate-wide compounding.** 8 priority languages × 7 eras = 56 per-language-per-era translation events. At professional rates the lifetime localization spend across the slate runs $22,400 to $210,000 of pure translation cost ESTIMATED, plus base launch cost, plus tooling, plus ops time. At community-pipeline rates this collapses to platform tooling ($1,000-$5,000/year) plus dev ops time.

The 7-era compounding is the principal structural argument for community-pipeline modal over professional modal at solo-dev / very-small-team scale. Day-1-paid for CN plus community-pipeline for everything else is REPORTED the most common compromise shape in this genre.

T-CL1 content-cadence pick interacts here: faster cadence (more frequent smaller content drops) compounds per-language per-drop re-translation overhead even within the community pipeline; slower cadence (larger less-frequent eras) reduces ops friction but increases per-drop string-mass.

## Conflict surfaced

Two specific design forks this brief surfaces for Design Lane:

**Fork 1: CN day-1-paid vs CN deferred.** CN has the strongest ROI signal but the highest content-policy and review-bomb risk in this genre. Day-1-paid CN means professional translation budget ($3,000-$20,000 base + 7-era compounding) plus content-policy pre-review. Deferred CN means launching without the largest non-English market localized and forecasting a delayed wishlist conversion lift. REPORTED publisher pattern: CN day-1 is the niche-strategy norm but a non-trivial minority defer CN until post-launch sales-data warrants the spend.

**Fork 2: Japanese inclusion based on Foundation halo.** Japanese fails the strict grand-strategy ROI test but the Foundation secondary-tribe angle materially shifts the case. If the marketing pitch leans hard on Foundation aesthetic adjacency and Japan is one of the regions where Foundation S3 viewership lands meaningfully, including Japanese costs $3,600-$24,000 base + 7-era compounding to capture a smaller but tribe-aligned audience. If the pitch leans on generational/legacy primary tribe instead, Japanese loses out on slate ROI alone.

## Caveats and confidence

All figures REPORTED or ESTIMATED. No VERIFIED claims. Aggregator-independence caveat: Gamalytic/SteamSpy/games-stats.com/Steam Revenue Calculator collapse to ~1 channel. Sales-lift multipliers come from scattered publisher post-mortems, indie developer tweets, and folk wisdom; promotion to VERIFIED requires publisher press release or financial filing.

Confidence on this brief overall: REPORTED to ESTIMATED. Structural framing (10 priority languages + long-tail, three-tier infrastructure modal, five cross-axes) is robust independent of figure drift. Specific multipliers, market-share percentages, and per-word costs should be verified before commitment when WebFetch/WebSearch is restored.

Sub-agent training cutoff January 2025; some 2025-2026 platform-policy changes (Steam CN content review tightening, Steam RU payment status, Apple TV+ regional drift) may have shifted since cutoff.

## Feeds Design Lane and other lanes

- **T-L2 community translation infrastructure** — slate constrains platform choice. If slate is "CN day-1 paid + everything else community," Crowdin or POEditor is natural fit. If slate is "all community," self-hosted Weblate or Crowdin mid-tier is natural fit. If slate is "English-only + Workshop-mod-only," T-L2 collapses to Workshop integration plus moddable string files.
- **Monetization revenue model** — per-language ARPU × conversion lift × unit volume feeds into the 80-200k unit / $25-35 base revenue forecast. Slate decision shifts forecast meaningfully — CN day-1 adds $200,000-$800,000 ESTIMATED lifetime revenue at 80-200k base; PT-BR adds $50,000-$200,000 ESTIMATED; long-tail community-mod-only languages add marginal revenue but maintain market presence at near-zero cost.
- **Engineering scope for localization pipeline** — slate scope determines whether localization is a 1-week engineering task (one paid language, manual export) or a 1-month task (full pipeline, multiple languages, version-branching, parameterized-string substitution support, UI elasticity for word-count expansion).
- **T-M2 7-tier DLC stress-test** — per-era localization debt is one of the structural overheads T-M2 should weight against the DLC revenue forecast.
- **Steam storefront tag/category locking** — per-language Steam page localization, language matrix declarations, regional pricing decisions all gate on the slate. Steam's interface/audio/subtitles matrix has no native "community-translated" flag, so framing happens via marketing copy and in-game UI affordances.

## Open questions for further research

Items needing follow-up via web research (when WebFetch/WebSearch is restored), publisher post-mortems, or developer interviews:

- **Actual 2026 Steam Hardware Survey language breakdown** — REPORTED figures above are training-cutoff recall; verify current Simplified Chinese / Russian / German / French / Spanish / PT-BR / Polish / Japanese / Korean shares.
- **Niche-strategy per-language sales-lift case studies** — specific publisher numbers from Hooded Horse, Paradox, Slitherine, MicroProse for CN, DE, RU, PT-BR, ES on grand-strategy titles. Folk wisdom 1.5x-3x for CN needs calibration.
- **Steam regional pricing 2026 matrix** — exact recommended discount per region; RU/TR/BR/LatAm/PL discount levels have shifted multiple times since 2022.
- **Steam CN content review state 2026** — current state of Steam's CN-side content gating, banhammer incidents in recent strategy/sim launches, review-bomb pattern data.
- **Steam RU payment infrastructure 2026** — current state of Russian payment options, gift-purchase routing, gray-market sizing.
- **Foundation TV S3 viewership by region** — Apple TV+ does not publish viewer numbers but third-party panel data (Nielsen, Antenna) may have leaked figures. Per-region reach calibrates Japanese-inclusion fork and the size of the Foundation-halo bonus in each market.
- **Apple TV+ Japan subscriber density** — sizing the Japanese Foundation-halo audience requires Apple TV+ Japan reach data.
- **Per-language Steam wishlist conversion rate data** — niche-strategy specific, REPORTED scattered in indie publisher tweets and Hooded Horse public statements.
- **Translation cost benchmarks 2026** — LocalizeDirect, LAI Global, GALA published per-word rates; verify 2026 figures.
- **DLC localization debt empirical** — Paradox grand-strategy DLC cadence and per-era localization scope, Stellaris/CK3 publisher quotes on per-DLC translation cost.
- **Community contributor density by language for indie strategy** — RimWorld Crowdin translator headcount per language, Wildermyth community translation state, Paradox translation-mod subscriber counts per language. Calibrates community-pipeline modal viability per language.
- **Steam algorithm boost from launch-day localization** — REPORTED Steam pushes localized titles in target-language store during launch window; the actual multiplier on impressions and wishlists is not publicly documented.

## Sources

Sub-agent had no web access this session. Source classes that would be consulted under a normal research pass:

- Steam Hardware Survey, monthly language-share snapshots.
- Steam recommended regional pricing matrix, published in Steamworks documentation.
- Gamalytic, SteamSpy, games-stats.com, Steam Revenue Calculator — single aggregator channel per user memory, used for cross-reference only.
- Hooded Horse public statements and developer blog (Sebastian Lague, Hooded Horse founder Tim Bender) on niche-strategy publishing and localization decisions.
- Paradox Interactive financial reports — per-language revenue breakdown where disclosed.
- Indie developer post-mortems on r/gamedev, GDC vault talks, IndieDB articles on per-language sales-lift.
- LocalizeDirect, LAI Global, GALA — translation-cost benchmark publishers.
- Apple TV+ third-party panel viewership leaks (Variety, Deadline, Nielsen/Antenna mentions) for Foundation S1/S2/S3 reach data.
- RimWorld Crowdin public project page for community-translator headcount per language.
- Paradox Steam Workshop translation-mod subscriber counts.
- Hayakawa Publishing catalog for Asimov Japanese reprint history.
- Steam community discussions on CN content review and RU payment friction post-2022.
- Press coverage of Steam's 2022 actions on Russia and ongoing payment-throughput state.
- T-A2 Foundation TV S3 brief (this Research Lane), T-A3 demographics brief (this Research Lane), T-L2 community translation infrastructure brief (`community_translation_infrastructure.md`), CL4 mod/Workshop payoff brief (when produced), T-M2 DLC stress-test brief (when produced).

Confidence on this brief overall: REPORTED to ESTIMATED. Structural framing is robust; specific figures need verification when web access is restored.
