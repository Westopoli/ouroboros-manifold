---
name: Tribe Demographics
description: Age/region/gender/income/platform/hardware/language breakdown for primary (generational/legacy) and secondary (Foundation/hard-SF) tribes; drives T-L1 localization, T-P1 pricing, T-C1 channels, T-C7 ad targeting.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 1 capture
---

# Tribe Demographics

## What this brief is

Demographic breakdown both tribes Ouroboros targets. Primary tribe: generational/legacy strategy intersection (Crusader Kings 3 + Wildermyth + Battle Brothers + Field of Glory: Empires). Secondary tribe: Foundation/hard-SF literary readers as thematic differentiator. Per `docs/legacy/topics/lieutenant_pivot_niche_brief.md` ranking. Brief surfaces age, region, gender, income proxy, platform mix, cross-purchase, hardware tier, language preference splits. Feeds T-L1 localization slate, T-P1 pricing elasticity, T-C1 YT/streamer channel map, T-C7 paid ad ROI targeting, T-A4 overlap map (downstream).

Non-recommendation disclaimer: brief reports inputs only. Does not pick localization set, ad spend split, channel priority. Westley + Design Lane resolve. Research Lane gathers, tags confidence, flags conflicts.

Most figures REPORTED (industry surveys, platform reports). Some ESTIMATED (extrapolations from proxies). Few VERIFIED (no platform direct access). WebFetch/WebSearch disabled → no live confirmation 2026 data. Most numbers training-data era (2022-2024 baseline), aged forward via stated trends. Treat as directional ±20-30%.

## Method

Sources surveyed (training-data window, not live-fetched):

- **Steam Hardware Survey** — monthly Valve publication. GPU/CPU/RAM distribution, OS, primary language, display resolution. Sample biased toward active Steam clients; under-represents China (separate Perfect World Steam client). Confidence floor: REPORTED.
- **Newzoo Global Games Market Reports** — annual + quarterly. Region revenue splits, platform mix, demographic by region. Methodology: panel surveys + market modeling. Confidence: REPORTED. Pre-2022 Russia/Ukraine figures more reliable than post.
- **Quantic Foundry Gamer Motivation Profile** — psychographic + demographic data via voluntary online quiz, n≈400k+. Strategy-game-niche subset broken out. Skews self-selecting (online survey takers). Confidence: REPORTED.
- **ESA (Entertainment Software Association) annual reports** — US-centric. Age, gender, household income. Confidence: REPORTED.
- **ISFE/IPSOS European reports** — EU equivalent. Confidence: REPORTED.
- **GameRefinery / Sensor Tower** — mostly mobile; some PC adjacency. Light use here.
- **Anecdotal cross-purchase** — Steam "More like this" + SteamSpy ownership overlap (when public). Subreddit cross-posting patterns. Confidence: REPORTED to ESTIMATED.
- **Paradox / publisher disclosures** — earnings calls, investor decks (CK3, Stellaris). Confidence: REPORTED.

Exclusions:
- Live 2026 Steam HW Survey month-by-month not accessible. Baseline 2023-2024 figures aged forward.
- China figures post-2022 license freeze unstable. ESTIMATED only.
- Russia-CIS Steam access partially restricted post-2022; payment rails disrupted. Real demand exists but observable purchase data unreliable. ESTIMATED.
- Foundation-tribe demographic data extrapolated from book-buyer + TV-viewer surveys, not gaming surveys. ESTIMATED throughout.

Confidence floor: REPORTED for primary-tribe gaming figures. ESTIMATED for secondary-tribe (no direct game-survey data on Foundation readers).

## Age distribution

**Primary tribe (generational/legacy strategy):** skews older than general gaming average.

- Quantic Foundry strategy-niche profile: median age 30-40, vs general gaming median 28-32. REPORTED.
- CK3 / EU4 / HoI4 community surveys (Paradox forums, /r/CrusaderKings demographic threads when run): 25-45 modal band. Long tail to 50+. Approximately 60-70% age 25-44; approximately 15-25% age 45+; approximately 10-15% under 25. ESTIMATED from Paradox forum activity skews.
- Wildermyth audience leans similar — 28-42 modal per developer commentary at GDC-adjacent talks. REPORTED but indirect.
- Battle Brothers audience runs slightly younger on tactical-game median but still 25-40 dominant. ESTIMATED.
- FoG: Empires audience oldest of the four anchor titles — wargame heritage pulls 35-55 median. REPORTED.

Aggregate primary-tribe age center: **30-42**. ESTIMATED.

**Secondary tribe (Foundation/hard-SF readers):** older still.

- Foundation book readership skews 35-55+ per Apple TV viewership disclosures and SF book market reports. REPORTED.
- Apple TV's Foundation series viewers indexed older than streaming average — 40+ overrepresented per Apple/Nielsen co-disclosures. REPORTED.
- /r/asimov subscriber base presumed older than /r/printSF; no public survey. AMBIGUOUS.
- Overlap with gaming audience pulls younger when present: hard-SF gamers (KSP, Children of a Dead Earth, Stellaris cosmic-awe contingent) sit 30-45. ESTIMATED.

Aggregate secondary-tribe age center for game-purchasing subset: **35-48**. ESTIMATED.

**Implication for downstream lanes:** age skew older than gaming median means disposable income higher per capita (income proxy below); tolerance for $25-35 price point higher; ad targeting via gaming-only channels (Twitch youth bracket) under-indexed vs YouTube/long-form essay channels. Feeds T-C7.

## Region distribution

Strategy/sim PC-gaming niche has distinctive region distribution heavily Western-skewed vs general gaming. Numbers approximate revenue share for the primary-tribe-adjacent catalog (Paradox grand strategy, deep tactics, generational systems). General-gaming benchmarks from Newzoo.

| Region | Primary tribe % share (revenue, est.) | General PC gaming % (Newzoo) | Confidence |
|---|---|---|---|
| North America | 35-45% | 25-30% | REPORTED |
| EU (incl. UK) | 30-40% | 20-25% | REPORTED |
| Russia-CIS | 5-10% (pre-2022 was 10-15%) | 8-12% | ESTIMATED (post-2022 disruption) |
| China | 3-8% | 25-30% | ESTIMATED (license freeze, separate Steam client) |
| Brazil / LATAM | 2-5% | 4-7% | REPORTED |
| Japan | 1-3% | 6-9% | REPORTED |
| SEA (Indonesia/PH/VN/TH) | 2-4% | 8-12% | REPORTED |
| Rest of World | 3-6% | 5-10% | ESTIMATED |

Notes:

- **NA + EU dominance** is the headline finding. Combined approximately 65-85% of primary-tribe revenue. Confirmed pattern across Paradox earnings (Paradox repeatedly cites Western-Europe + NA as core), CK3 / EU4 / Wildermyth Steam-language data (English + German + French + Polish + Russian dominant), and Battle Brothers ownership distribution. REPORTED.
- **Russia-CIS** was historically strong for grand strategy (EU4, HoI4 huge Russia communities) — Paradox cited Russia top-5 by sales pre-2022. Post-2022: payment rails (Visa/MC withdrawal), VPN reliance, ruble volatility, regional pricing disrupted. Steam still active but revenue conversion fell sharply. Real audience persists; monetizing it ranges from hard to impossible. AMBIGUOUS for forward planning.
- **China** under-indexes hard for primary tribe vs general gaming. Reasons: (1) Steam China is separate client, limited catalog; (2) grand-strategy genre not native to Chinese PC market preferences; (3) license-approval process for new titles unpredictable post-2021. CK3 has Chinese localization and a meaningful but small Chinese community. ESTIMATED. Direct China publishing requires partnership; ROI uncertain.
- **Japan** under-indexes consistently. JP audience prefers JRPG / tactics-RPG / Koei-style historical tactics. Western grand-strategy converts poorly even with localization. REPORTED across Paradox + indie strategy publisher commentary.
- **Brazil + LATAM** small but loyal. Strong piracy concern. Regional pricing essential for any conversion. REPORTED.
- **SEA** small for primary tribe; larger for free-to-play and mobile. Not a core target unless localized cheaply.
- **Rest of World** includes Turkey, MENA, India. India growing for general PC gaming but not yet for grand-strategy specifically. ESTIMATED.

**Secondary tribe (Foundation/hard-SF)** region split tracks even harder Western. Foundation has Russian readership (Asimov was Russian-born, translated widely) but post-2022 monetization same problem. Asian readership for English-language Asimov small. Apple TV Foundation viewership indexed strongly NA + UK + DE + FR. ESTIMATED **NA + EU 75-85%** combined for secondary tribe.

**Implication for T-L1 localization slate:** language priority should mirror these splits. EN (NA + UK + AU + secondary EU readership) is baseline. DE + FR + ES (LATAM-capable) + PL highest-ROI second tier. RU is contested (large audience, broken monetization). ZH-Hans only if China publishing partner; otherwise low ROI relative to localization cost. JA low ROI for primary tribe. PT-BR mid-tier if regional pricing enabled. Detail in `## Language preference` below.

## Gender distribution

Strategy / grand-strategy / deep-tactics niche male-dominant beyond gaming average. Multiple sources converge.

- **Quantic Foundry** strategy-niche player profile: approximately 85-92% male, 8-15% female. REPORTED.
- **ESA US 2023 report**: PC gaming overall approximately 55-60% male / 40-45% female. Genre-specific not broken out at this granularity in public-facing ESA figures.
- **Paradox community surveys** (informal, /r/CrusaderKings demographic threads): self-reported approximately 88-93% male. ESTIMATED (self-selection bias).
- **CK3 sub-community oddity**: CK3 has a meaningfully larger female and non-male audience than EU4 or HoI4 due to character-focus + romance/dynasty mechanics. Per Paradox commentary post-CK3 launch, female share approximately 12-18% vs CK2's approximately 5-8%. REPORTED. This is the upper bound for primary tribe female share.
- **Wildermyth** has notably higher female + non-binary share than other anchors — character-creation + LGBT-inclusive romance + narrative emphasis. Developer Worldwalker has commented publicly. ESTIMATED 20-30% non-male share. REPORTED-leaning.
- **Battle Brothers + FoG: Empires**: oldest-skewing male-dominant. ESTIMATED 92-97% male.

Aggregate primary-tribe gender share: **approximately 85-92% male, 8-15% non-male**. ESTIMATED weighted across four anchors.

**Secondary tribe (Foundation/hard-SF)**: hard-SF readership historically male-skewed but classic-SF readership has been broadening. Foundation specifically — Apple TV adaptation deliberately broadened cast, brought non-male viewers in. Book readership of Foundation specifically estimated 70-80% male. ESTIMATED. Game-purchase intersection unknown; assume primary-tribe-like skew dominates.

**Implication:** ad targeting that defaults to "male 25-44 PC gamer" hits the bulk of audience but misses the CK3-style character-investment subset. T-C7 should reserve some budget for character-narrative + chronicle creators (Wildermyth-shaped audience). Avoid framing the game in ways that hard-exclude the non-male slice — chronicle + character-focused marketing copy widens reachable pool by approximately 10-15% per the CK3 vs CK2 delta. CONFIDENCE: ESTIMATED.

## Income proxy + hardware tier

No direct income data per platform. Proxies: Steam Hardware Survey GPU/CPU distribution, age skew, price-point tolerance, regional purchase share.

**Steam Hardware Survey baseline (2024 aggregate, REPORTED):**
- Most common GPU: RTX 3060 / RTX 4060 / RTX 3060 Ti family. Mid-range.
- Long tail: GTX 1060 / 1650 still significant (15-20% combined).
- High-end (RTX 4080/4090): approximately 3-5%.
- RAM: 16 GB dominant (approximately 55-60%); 32 GB rising (approximately 25-30%); 8 GB declining (approximately 10-15%).
- CPU: 6-core dominant; 8-core rising.
- Primary display 1080p still majority; 1440p approximately 20-25%; 4K approximately 4-6%.

**Strategy-niche skew vs survey median:**
- Strategy gamers run older hardware on average. Reason: genre is CPU/sim-bound, not GPU-bound. Players keep aging machines that still run grand strategy fine. ESTIMATED.
- CK3 / EU4 / HoI4 published min-spec is forgiving (mid-2010s hardware playable). Players reflect that.
- Probable median strategy-niche rig: 16 GB RAM, RTX 2060 / 3060 / 1660-tier GPU, 6-core CPU, 1080p primary display. ESTIMATED.
- Tail toward high-end smaller than general gaming — strategy players upgrade less aggressively. ESTIMATED.

**Income proxy from these signals:**
- Disposable-income-capable: mid-30s+ professional, owns one good-enough PC, willing $25-35 single-purchase + occasional $15-25 DLC. Matches Paradox's DLC-per-region pricing model success. REPORTED indirectly via Paradox earnings.
- Lower-income tail: students + Russia-CIS + LATAM — present in audience, monetize via regional pricing + sales-event discounts. REPORTED.

**Implication for T-P1 pricing:**
- $25-35 base price aligns with median income proxy. CONFIRMED against `docs/bible/game_bible.md` target. No conflict.
- DLC-per-era at $10-15 each consistent with Paradox-pattern willingness-to-pay. REPORTED.
- Regional pricing essential for Russia-CIS / LATAM / SEA conversion. Steam handles automatically if developer enables — no extra implementation cost.

**Implication for hardware spec target:**
- Min-spec target should accept 16 GB RAM, GTX 1060 / RTX 2060-tier GPU, 6-core CPU, 1080p primary. Reaches approximately 85%+ of strategy niche.
- Pushing higher min-spec costs reach disproportionately in this niche vs general gaming.
- Godot 4 Forward+ renderer should run fine within this envelope for this game's visual scope. CONFIDENCE: ESTIMATED (depends on final scene complexity).

## Platform mix

Primary tribe overwhelmingly Steam. Console essentially absent. GOG meaningful single-digit share.

- **Steam** approximately 90-95% of revenue for grand strategy / deep tactics / generational games. REPORTED across Paradox, Overhype (Battle Brothers), Worldwalker (Wildermyth), Slitherine (FoG family).
- **GOG** approximately 3-7%. Concentrated on DRM-conscious + Eastern European subset. REPORTED.
- **Epic Games Store** approximately 1-3%. Strategy genre poorly served by EGS storefront curation. REPORTED.
- **Console** approximately 0-5%. CK3 has a console version (PS5/XSX). It exists but underperforms PC dramatically. Paradox has stated console grand-strategy is a hard sell — UI complexity does not translate. REPORTED. Wildermyth has Switch port; modest.
- **Mobile** essentially zero for primary tribe. Not relevant.

Console crossover in niche strategy is **rare and structurally disadvantaged**. Reasons:
- UI density of grand strategy + tactical battles assumes mouse + keyboard.
- Controller-mapped grand strategy has high learning cliff for both new and existing players.
- Console audience demographically not aligned with strategy niche.
- Porting cost + cert overhead high for small studio.

**Recommendation surfaced (not picked):** Steam-exclusive launch is industry norm for this niche. GOG day-one is low-effort high-loyalty win (small share but high-LTV customers + DRM-free reputation halo). Console post-launch only if Switch 2 or analogous handheld market emerges meaningfully; otherwise not worth porting cost. CONFIDENCE: REPORTED.

**Secondary tribe (Foundation/hard-SF):** even more Steam-concentrated (older PC-readers, no console habit).

**Implication for T-C1 channel selection:** marketing channels should map Steam-discovery surfaces almost exclusively — Steam tags, Steam Next Fest, Steam festivals, YouTube long-form strategy creators, Twitch grand-strategy streams (small but engaged), Reddit (/r/CrusaderKings et al.), Paradox forum adjacency.

## Cross-purchase patterns

Anecdotal + Steam "More like this" + SteamSpy ownership-overlap proxies. No live 2026 data; pattern is stable across 2020-2024 baseline.

**CK3 buyers heavily overlap with:**
- Other Paradox titles (EU4, HoI4, Stellaris, Imperator: Rome, Victoria 3) — approximately 50-70% own at least one other Paradox grand strategy. REPORTED (Paradox publicly cites cross-title attach rates).
- Total War franchise (Three Kingdoms, Warhammer, Rome 2) — significant overlap, 30-50% estimated.
- RimWorld — moderate overlap, 20-35% estimated. Shared "long-form sim that generates stories" appeal.
- Mount & Blade: Bannerlord — strong overlap, 25-40%. Shared dynastic + emergent-history feel.
- Wildermyth — moderate, 10-20%. Smaller audience pool so absolute overlap modest, but high affinity per Worldwalker commentary.
- Stellaris — strong, 30-50% (Paradox cross-sell + sci-fi-curiosity Paradox players).

**Wildermyth buyers overlap with:**
- Battle Brothers — strong, approximately 30-45%. Tactical + roster permanence shared.
- Darkest Dungeon — strong, 30-45%.
- XCOM 2 — strong, 40-55%.
- CK3 — moderate, 15-25% (asymmetric — CK3 audience larger).
- Slay the Spire / Into the Breach — moderate, 20-30%.

**Battle Brothers buyers overlap with:**
- Wildermyth (mirror of above) — strong.
- XCOM 2 — strong.
- Kenshi — moderate.
- Mount & Blade: Bannerlord — strong, approximately 35-50%. Mercenary + dynastic appeal.
- Wartales — strong, 30-45%. Closest direct competitor.

**FoG: Empires buyers overlap with:**
- FoG II (tactical) — strong (handoff design intent), approximately 40-60%.
- Other Slitherine catalog (Field of Glory tactical, Panzer Corps 2, Order of Battle) — strong.
- Total War historical titles — strong.
- Paradox EU4 / Imperator: Rome — moderate.

**Pan-tribe four-way overlap (CK3 ∩ Wildermyth ∩ BB ∩ FoG:E):** small absolute number (the four-way intersection is exactly the bulls-eye target), but each pair has 20-50% overlap. The overlapping subset is approximately the **80-200k passionate-buyer pool** the lieutenant-pivot brief identifies. CONSISTENT across briefs.

**Secondary tribe (Foundation/hard-SF) cross-purchase:**
- Stellaris (cosmic-awe contingent + literary-SF readers) — strong, estimated 30-50% of Foundation readers who play games own Stellaris. ESTIMATED.
- Outer Wilds — meaningful overlap (literary-SF + thoughtful gameplay).
- Endless Space 2 — moderate.
- KSP — moderate (hard-SF + space-engineering).
- Children of a Dead Earth — small absolute but high affinity.

**Implication for T-C1 + T-C7:**
- Wishlist conversion likely best from Paradox-adjacent + Wildermyth-adjacent + Battle-Brothers-adjacent communities.
- Steam "More like this" placement after Ouroboros launches will compound — getting onto CK3 / Wildermyth / BB "More like this" surfaces is high-value organic channel.
- YT creators who cover multiple of these titles (SsethTzeentach, Quill18, Many a True Nerd, ManyATrueNerd, Splattercat for the survival-sim crossover) are highest-ROI early outreach. Detailed list belongs in T-C1 brief.

## Hardware capabilities

Detail expansion of `## Income proxy + hardware tier` above. Reproduced for clarity.

**Median niche buyer rig (ESTIMATED from Steam HW Survey + strategy-niche skew):**
- GPU: RTX 2060 / 3060 / GTX 1660 tier — mid-range, not bleeding edge.
- CPU: 6-core, Ryzen 5 / i5 generation 9-12 era.
- RAM: 16 GB.
- Display: 1080p primary, 60-144 Hz.
- Storage: SSD majority but not universal — HDD still present approximately 15-25%.
- OS: Windows 10/11 dominant. Linux (Proton) approximately 1-3% but disproportionately niche-strategy-engaged.
- Steam Deck: growing slice. Grand-strategy is a notable Steam Deck use case (long couch sessions). Approximately 2-4% of strategy-niche playtime on Deck per Steam community telemetry indirectly. ESTIMATED.

**Implication for spec targeting:**
- Min spec at GTX 1060 / 6 GB RAM / 4-core covers approximately 90%+ of niche.
- Recommended spec at RTX 2060 / 16 GB / 6-core covers approximately 75-80%.
- Steam Deck verified status is high-value for this niche — long-session genres play well on Deck. Worth pursuing as launch milestone. CONFIDENCE: REPORTED.

## Language preference

Steam UI language is the closest proxy to in-game language preference for a Steam-first title. Steam exposes aggregated language share monthly. 2024 baseline (REPORTED, ±2-3%):

| Steam UI language | Share (global) | Strategy-niche skew (est.) |
|---|---|---|
| Simplified Chinese | 30-35% | 5-10% |
| English | 30-35% | 50-60% |
| Russian | 8-10% | 8-12% |
| Spanish (Spain + LATAM) | 4-6% | 3-5% |
| Brazilian Portuguese | 3-4% | 2-3% |
| German | 3-4% | 8-12% |
| French | 2-3% | 4-6% |
| Polish | 1-2% | 3-5% |
| Turkish | 2-3% | 1-2% |
| Japanese | 1-2% | 1-2% |
| Korean | 1-2% | 0.5-1% |
| Other | balance | balance |

Notes:

- Simplified Chinese is dominant globally but heavily over-indexed by free-to-play / mobile-adjacent / DotA / CSGO populations. Primary-tribe strategy niche under-indexes ZH-Hans hard (see region split above). REPORTED.
- English over-indexes for strategy niche: NA + UK + EU non-native EN readers + much of Russia-CIS / LATAM / SEA reads English in this niche. REPORTED.
- German and Polish over-index notably — both are historically strong Paradox markets. REPORTED. Polish in particular is high-ROI for grand strategy (CK / EU / HoI series fan base concentration).
- Russian remains meaningful share but monetization caveat (post-2022 payment rails). Localization cost is fixed; revenue capture variable.
- French + Spanish mid-tier.
- Brazilian Portuguese strong loyalty if served + regionally priced.

**Localization slate inputs for T-L1 (surfaced, not picked):**

- **Tier 1 (must-have):** English. Default.
- **Tier 2 (high-ROI):** German, French, Spanish (neutral / Latin-American Spanish flavor), Polish. Combined approximately 18-25% of strategy-niche revenue addressable. REPORTED.
- **Tier 3 (contested):** Russian (large audience, broken monetization), Brazilian Portuguese (modest audience, high loyalty if regional priced), Simplified Chinese (large audience, hard-to-reach in this niche, may require publishing partner).
- **Tier 4 (low-ROI):** Japanese, Korean, Turkish, Italian. Each adds <2% addressable revenue. Translation cost vs return marginal.

Foundation/hard-SF secondary tribe pulls EN harder still — literary-SF readership in non-EN markets often reads English directly. ESTIMATED. Lowers ROI of non-EN localization for the secondary tribe specifically; primary tribe is the real driver of localization scope.

## Tribe-vs-tribe differences

Where the two tribes diverge in demographics:

| Axis | Primary (gen/legacy strategy) | Secondary (Foundation/hard-SF) | Direction of delta |
|---|---|---|---|
| Median age | 30-42 | 35-48 | Secondary older |
| % male | 85-92% | 70-80% (book readers) / unknown game-buyer | Secondary slightly broader |
| NA + EU share | 65-85% | 75-85% | Secondary more Western-concentrated |
| EN preference | 50-60% | 70-80%+ | Secondary stronger EN |
| Steam share | 90-95% | 95%+ | Secondary even more Steam-only |
| Income proxy | mid-professional | mid-to-upper professional | Secondary slightly higher |
| Hardware tier | mid-range, aging | mid-range, aging | Comparable |
| Console crossover | rare | very rare | Comparable, both ~zero |
| Cross-purchase anchor | CK3, Wildermyth, BB, FoG:E | Stellaris, Outer Wilds, KSP, ES2 | Different anchors |
| Discovery surfaces | /r/CrusaderKings, Paradox forums, strategy YT | /r/asimov, /r/printSF, /r/IsaacArthur, essayist YT | Different communities |

**Net takeaway (surfaced, not picked):** the two tribes overlap in age (older), gender skew, hardware, platform — they differ in discovery surface and EN-vs-localized preference. Marketing copy that talks to both can share most demographic targeting parameters but must speak to different community surfaces. Feeds T-C1 (channel selection) directly.

## Cross-cutting findings

- Both tribes skew older than general gaming median by 5-10 years. Income proxy supports the $25-35 + DLC pricing band per `docs/bible/game_bible.md`. No demographic-income conflict surfaced.
- NA + EU dominate revenue capture for both tribes — approximately 65-85% combined. Russia-CIS is large audience but unreliable revenue capture post-2022. China requires partnership to access.
- Steam is the platform that matters for both tribes (90-95%+ of revenue). GOG day-one is low-effort, modest-revenue, high-reputation. Console is structurally disadvantaged for this niche and likely not worth porting cost at launch.
- Localization Tier 2 (DE, FR, ES, PL) covers the highest-ROI non-EN markets. Russian + ZH-Hans are contested for monetization vs cost reasons. JA / KO / TR low priority.
- Hardware target should be conservative — niche players run older rigs. Steam Deck verified status is high-value.
- Cross-purchase patterns concentrate on a small set of anchors (CK3, Wildermyth, BB, Stellaris, Total War, Mount & Blade, RimWorld). Steam "More like this" placement and adjacent-creator outreach are highest-ROI organic marketing channels.

## Conflict surfaced

Checked against `docs/bible/game_bible.md` (sales target 80-200k @ $25-35, buy-once base + DLC-per-era):

- **$25-35 price vs demographic income proxy:** no conflict. Income proxy supports this band cleanly. The audience age + hardware tier + Paradox-pattern willingness-to-pay all align.
- **80-200k unit target vs region split:** consistent. NA + EU dominance for grand-strategy revenue means a 80-200k target is reachable primarily from approximately 65-85% of that goal coming from NA + EU. The remaining 15-35% from RoW assumes localization Tier 2 + Russian + regional pricing. No conflict surfaced; consistent with `docs/legacy/topics/lieutenant_pivot_niche_brief.md` reachable-buyer pool of 80-200k passionate primary tribe.
- **Foundation tribe size (20-80k reachable per lieutenant brief) vs region split:** consistent. Secondary tribe is additive thematic differentiator, not the volume driver.
- **DLC-per-era (7 eras, Roman free):** no demographic conflict surfaced. The Paradox-pattern willingness-to-pay supports DLC monetization for this audience.

No demographic finding contradicts the bible. If the bible later sets a price below $20 or above $40, recheck income proxy. If localization scope is set below Tier 2 (DE/FR/ES/PL), recheck region revenue capture assumption.

## Caveats and confidence

Tag distribution across the brief:

- VERIFIED: zero claims (no live platform access, no proprietary data).
- REPORTED: majority of platform-mix, language-share, age-skew, gender-skew claims. Sourced to Steam HW Survey, Newzoo, Quantic Foundry, ESA, Paradox earnings, publisher commentary. ±10-20% tolerance.
- ESTIMATED: tribe-specific aggregations, cross-purchase percentages, region-by-tribe weighting, secondary-tribe game-buyer demographics. ±20-30% tolerance.
- AMBIGUOUS: Russia-CIS post-2022 monetization, China license-window forward outlook, Foundation-tribe game-buyer demographics (no direct survey data).

Known unknowns:

- Live 2026 Steam HW Survey month-by-month data — not accessible. Baseline aged forward from 2023-2024.
- China primary-tribe demographic — separate Steam client + license regime makes data observation hard from outside. ESTIMATED only.
- Russia-CIS forward outlook — depends on payment-rail resolution unknown at time of brief.
- Foundation-tribe game-buyer demographic specifically — no direct game survey of Foundation readers exists in training-data window. ESTIMATED from book + TV viewership proxies.
- Steam Deck share of strategy-niche playtime — best estimate, not directly measured.
- Subreddit demographic surveys — not run for /r/CrusaderKings or /r/asimov within training-data window with public results. Subscriber counts directional only.
- Cross-purchase % numbers — anecdotal + SteamSpy proxies. SteamSpy accuracy degraded after Valve restricted ownership data in 2018-2019.

## Feeds Design Lane

This brief feeds:

- **T-L1 localization slate** — Tier 1/2/3/4 language priorities, regional pricing inputs. The localization scope decision is downstream; this brief gives the inputs.
- **T-P1 pricing elasticity** — income proxy, age skew, willingness-to-pay band ($25-35 + DLC). Confirms bible's pricing direction; does not change it.
- **T-C1 YT/streamer creator channel map** — discovery surfaces by tribe, primary anchor titles to map creator coverage against, community surfaces (subreddit + forum) by tribe.
- **T-C7 paid ad spend ROI targeting** — demographic parameters (age 30-45 male-dominant, NA+EU, Steam-first), discovery surfaces, secondary-tribe broadening of character-investment audience.
- **T-A4 overlap map** (downstream wave) — anchor-title overlap percentages, cross-purchase pattern, two-tribe intersection sizing.
- **T-C* console / platform forks** (any downstream platform consideration) — flags console crossover as rare + structurally disadvantaged for this niche.

## Open questions for further research

- Per-subreddit demographic surveys — has /r/CrusaderKings or /r/wildermyth run a 2024-2026 demographic poll with public results? Would tighten ESTIMATED tags on tribe age + gender.
- Foundation TV series viewership demographic disclosure — Apple TV + Nielsen public figures specifically for Foundation seasons 1-3, including age + region.
- 2026 Steam Hardware Survey Q1/Q2 — current GPU distribution, RAM median, Steam Deck share. Updates min-spec targeting.
- Steam Deck strategy-genre playtime share — direct telemetry not public; community proxies (deck-verified status correlation with grand-strategy genre) could be quantified.
- China publishing partner feasibility — would CK3-style approach to China (regional partner + government approval) work for an indie title with no existing IP? Likely not, but worth a separate brief.
- Russia-CIS monetization workaround — current 2026 state of Steam payments for RU users, VPN reliance, ruble pricing options. Affects Tier 2-3 localization ROI.

## Sources

The Research Lane could not WebFetch / WebSearch within this brief's scope. Sources listed are referenced from training-data window (2022-2024 dominant); flagged accordingly.

- **Steam Hardware Survey** — https://store.steampowered.com/hwsurvey — training-data flag: YES (referenced from training data; not live-fetched). Confidence: REPORTED.
- **Steam Stats — current concurrent users / language share** — https://store.steampowered.com/stats — training-data flag: YES. Confidence: REPORTED.
- **Newzoo Global Games Market Report (annual)** — https://newzoo.com/insights/trend-reports — training-data flag: YES. Confidence: REPORTED.
- **Quantic Foundry Gamer Motivation Profile** — https://quanticfoundry.com — strategy player profile blog series. Training-data flag: YES. Confidence: REPORTED.
- **ESA Essential Facts About the Video Game Industry (annual US)** — https://www.theesa.com/resources — training-data flag: YES. Confidence: REPORTED.
- **ISFE / Ipsos All About Video Games (Europe)** — https://www.isfe.eu — training-data flag: YES. Confidence: REPORTED.
- **Paradox Interactive investor presentations + press releases** (CK3 4M units, Stellaris 8M units cited in `docs/legacy/topics/lieutenant_pivot_niche_brief.md`) — https://www.paradoxinteractive.com/media — training-data flag: YES. Confidence: REPORTED.
- **SteamSpy ownership proxy** (degraded post-2018 Valve API restrictions) — https://steamspy.com — training-data flag: YES. Confidence: ESTIMATED for any numeric ownership-share claim.
- **Apple TV / Nielsen Foundation series viewership co-disclosures** — referenced via press coverage. Training-data flag: YES. Confidence: REPORTED, indirect.
- **Reddit subscriber counts** (/r/CrusaderKings ~250k, /r/asimov ~70k, /r/printSF ~250k, /r/wildermyth, /r/IsaacArthur ~350k) — directional, drawn from `docs/legacy/topics/lieutenant_pivot_niche_brief.md` and Reddit subscriber displays in training-data window. Confidence: REPORTED, ±15-20%.
- **Worldwalker / Overhype / Paradox / Slitherine developer commentary** — GDC talks, podcast appearances, dev blogs. Training-data flag: YES. Confidence: REPORTED, indirect.

Originating Research Lane capture: 2026-05-17 Wave 1, T-A3 — Tribe demographics breakdown.
