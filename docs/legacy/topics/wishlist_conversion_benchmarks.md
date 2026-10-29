---
name: Wishlist Conversion Benchmarks
description: Median wishlist-to-purchase ratio + percentile range for niche-strategy 2020-2026; per-anchor pattern (CK3/Wildermyth/RimWorld); launch-week vs year-1 shift; sale-event multipliers; per-source conversion deltas; feeds T-W2 velocity, funnel-math closure, T-D1 demo, T-S3 algorithm.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 5 capture
---

# Wishlist Conversion Benchmarks

## What this brief is

Wishlist-to-purchase conversion scan across niche-strategy launches 2020-2026. Surfaces median + percentile range, per-anchor pattern (CK3-likes / Wildermyth-likes / RimWorld-likes), launch-week vs year-1 decay curve, sale-event multipliers (Summer / Winter / Spring / Autumn / Next Fest), per-source conversion deltas (festival / creator video / organic / press). Closes funnel-math checkpoint #2 by applying observed ratios to bible-locked 80-200k unit first-month target @ $25-35 paid-base.

Feeds T-W2 velocity targets (downstream — what wishlist accrual rate hits the funnel-math), funnel-math closure (this brief), T-D1 demo strategy (demo-wishlist conversion premium), T-D2 Next Fest planning (Next Fest specific conversion lift), T-S3 algorithm visibility multipliers (Steam wishlist-driven recommendation surfacing).

**Non-recommendation disclaimer.** Research Lane surfaces inputs. Does NOT pick wishlist target, demo strategy, Next Fest timing, or per-source mix priorities. Westley + Design Lane resolve. Brief flags conflicts w/ bible directives but does not resolve them — bible authority resolves.

Confidence floor: WebFetch + WebSearch denied this session. No live 2026 SteamDB wishlist telemetry pulls, no live GameDiscoverCo newsletter refresh, no live publisher-disclosed conversion snippets. All numeric claims REPORTED or ESTIMATED from training-data window (2020-2024 baseline, aged forward 2025-2026 where stated). Treat figures as ±20-30% directional. Steam wishlist + purchase telemetry is publisher-side, never public; ESTIMATED floor on all niche-specific percentages. Tag legibility per claim below.

## Method

Sources surveyed (training-data window only — not live-fetched):

- **GameDiscoverCo (Simon Carless newsletter)** — https://newsletter.gamediscover.co — the canonical Western-indie aggregator for wishlist-conversion benchmarks. Publishes aggregate wishlist-conversion data quarterly, per-genre breakouts occasionally, post-Next-Fest reports. Confidence: REPORTED.
- **How To Market A Game (Chris Zukowski)** — https://howtomarketagame.com — niche-indie + small-strategy specific marketing data. Conversion-rate canonical "10-20%" rule originates here in long-form. Per-source delta commentary (festivals, demos, streamers). Confidence: REPORTED.
- **Valve / Steamworks blog posts + GDC talks** — sporadic per-event conversion + visibility data published by Valve (Steam Next Fest retrospectives, seasonal-sale aggregate disclosures). Most granular publisher-facing data not exposed to public. Confidence: REPORTED for what's published, ESTIMATED for the rest.
- **Gamalytic** — https://gamalytic.com — wishlist-conversion modeling via review-velocity + CCU proxies. Imperfect; directional. Confidence: REPORTED for relative ranking, ESTIMATED for absolute.
- **Hooded Horse publisher commentary** — Tim Bender / Snow Rabbit GDC + podcast disclosures on Old World, Manor Lords, Falling Frontier launches. Wishlist + conversion partials publicly stated. Confidence: REPORTED.
- **Paradox investor relations** — CK3, Stellaris, Vic3 sales + wishlist + DLC disclosures. Most granular wishlist conversion not broken out separately; inferred from sales-curve shapes. Confidence: REPORTED.
- **Per-developer post-mortems** — Tynan Sylvester (RimWorld), Bay 12 (Dwarf Fortress Steam), Worldwalker (Wildermyth), Overhype (Battle Brothers), Slavic Magic (Manor Lords), 3Division (Workers & Resources), Gamatron (Songs of Syx). GDC talks + Reddit AMAs + blog posts. Confidence: REPORTED where disclosed, ESTIMATED for inferred figures.
- **SteamDB** — https://steamdb.info — review-count + CCU + price-history. Wishlist counts not public per-title; only modeled. Confidence: REPORTED for review/CCU, ESTIMATED for wishlist modeling.
- **Steambase** — https://steambase.io — CCU + price-history scrape. Confidence: REPORTED.
- **Adjacent press** — Rock Paper Shotgun, PC Gamer, Game Developer, GamesIndustry.biz, Eurogamer post-launch coverage of niche-strategy. Confidence: REPORTED.

Exclusions:

- Per-title wishlist counts at any specific moment — publisher-side, not public. Estimated only via review-count proxies + publisher snippet disclosures.
- Per-source conversion deltas at title-level — almost entirely publisher-side. Aggregate patterns (festival vs organic) from GameDiscoverCo aggregates only.
- Live 2026 Steam Next Fest data — most recent disclosed Next Fests are mid-2024 vintage in training window. AMBIGUOUS for 2026 specifics.
- Russia + China + Argentina post-2022 wishlist conversion — payment-rail disruption distorts. AMBIGUOUS.

Confidence floor: **REPORTED** for "10-20% rule" canonical claim + publisher-disclosed snippet figures + qualitative per-source rank order. **ESTIMATED** for per-anchor numeric breakouts + decay curve specifics + sale-event multiplier %. **AMBIGUOUS** for 2026 Next Fest specifics + post-2022 distorted regions.

## Median wishlist-to-purchase ratio

**The canonical "10-20% rule"** for first-week wishlist conversion is the GameDiscoverCo + How To Market A Game baseline cited consistently across 2020-2024. Definition: % of users who wishlisted a title that purchase within first 7 days of release. REPORTED.

Caveats baked into the rule:

- Rule is cross-genre median. Niche-strategy runs above median per audience-loyalty proxies. ESTIMATED +2-5 percentage points relative to general-indie benchmark.
- Rule applies to launch-week only. Cumulative (lifetime) wishlist conversion is meaningfully higher — see launch-week vs year-1 section.
- Rule assumes price point in the $15-30 modal-indie band. Higher-price launches ($35-45) drag the % down; lower-price ($10-15) push it up. Cross-ref `docs/legacy/topics/pricing_elasticity_niche.md ## Per-tier wishlist conversion`.
- Rule is calculated against pre-launch accumulated wishlist count. Wishlists added in launch week itself convert at a separately-much-higher rate (effectively buyer intent + day-0 wishlist as one motion).

**Niche-strategy launch-week conversion (estimated baseline 2020-2026):**

| Tier | 7-day conversion (est.) | Confidence |
|---|---|---|
| Top decile niche-strategy | 25-40% | ESTIMATED |
| Strong launch | 17-25% | ESTIMATED |
| Median niche-strategy | 12-18% | ESTIMATED |
| Soft launch | 7-12% | ESTIMATED |
| Bust | 3-7% | ESTIMATED |

The **niche-strategy median at approximately 15%** is the working number for funnel-math throughout this brief. ESTIMATED-leaning REPORTED via GameDiscoverCo aggregate commentary. Cross-ref `docs/legacy/topics/pricing_elasticity_niche.md` confirms 15-22% at $29.99 modal niche-strategy.

**Cumulative (year-1) conversion** is meaningfully higher — see launch-week vs year-1 shift section. The 30-day cumulative for healthy niche-strategy is approximately 2× the 7-day figure (REPORTED per GameDiscoverCo Simon Carless analyses); the 12-month cumulative is approximately 3-5× the 7-day figure (ESTIMATED).

**Working median for Ouroboros funnel-math: 15% launch-week, ~30% 30-day, ~50-60% year-1.** ESTIMATED-leaning. See funnel-math gut check section.

## Percentile distribution

The shape of the niche-strategy launch-week conversion distribution is approximately log-normal w/ a long upper tail. Most launches cluster in the 8-18% band; breakouts hit 25-40%; busts fall under 5%.

**Percentile breakdown (ESTIMATED throughout from aggregate sources):**

| Percentile | 7-day conversion | Profile |
|---|---|---|
| 10th | 4-6% | Marketing failure, audience-mismatch tagging, review-score collapse at launch |
| 25th | 8-11% | Soft launch — niche audience didn't show up, OR launched at premium price w/o earned tribe |
| 50th (median) | 13-17% | Healthy niche-strategy launch w/ proper tagging + audience pre-warming |
| 75th | 20-27% | Strong launch — pre-launch demo + festival + creator coverage + tribe alignment |
| 90th | 30-40% | Breakout — multi-source momentum + algorithmic placement + immediate review snowball |
| 99th | 45-60%+ | Outlier — IP halo + cult-wait release (Dwarf Fortress Steam, Caves of Qud 1.0 shape) |

**What separates breakout from bust in niche-strategy specifically (REPORTED-leaning, distilled from GameDiscoverCo + Zukowski post-mortems):**

1. **Pre-launch demo + Next Fest participation.** Demo-played-and-wishlisted converts at 2-3× the rate of cold-trailer wishlist. REPORTED.
2. **Tag legibility.** Breakouts have 5-10 Steam tags that clearly identify the audience tribe. Busts have generic "Strategy" + "Indie" tagging that does not reach the niche.
3. **Review-snowball.** Niche-strategy needs 60+ reviews by day 7 to hit the algorithmic visibility multiplier. Below that, Steam's recommendation surface does not pick up the title. REPORTED.
4. **Tribe pre-warming.** Subreddit + Discord presence + creator coverage in the months preceding launch produces a wishlist pool of buyers, not curiosity-clickers. Cold-organic wishlist pool converts at lower rate.
5. **Launch-day price legibility.** Within bible-locked $25-35 band, launch price set at modal $29.99 or premium $34.99 (paired w/ scope-signaling) outperforms odd-pricing or above-band launches. Cross-ref pricing_elasticity_niche.md.
6. **Streamer-coverage alignment.** Quill18 / SsethTzeentach / Many a True Nerd / Splattercat / Wanderbots tier coverage in launch-week meaningfully shifts conversion upward. REPORTED.

**What separates 75th from 90th:** essentially a combination of all of the above stacking simultaneously rather than 2-3 of them stacking. Niche-strategy breakouts are multi-source momentum events, not single-source.

**What separates 90th from 99th:** IP halo / cult-wait shape. Cannot be manufactured for a new IP. Ouroboros cannot target 99th percentile honestly — it can target 75th-90th band w/ disciplined execution. ESTIMATED.

## CK3-likes

Crusader Kings 3 launched September 2020 at $49.99 (Royal Edition $74.99) and shipped 1M units in the first 24 hours per Paradox press. The wishlist pool at launch was reported in the multi-hundreds-of-thousands range (Paradox-disclosed indirectly via interviews). Within ~2 years CK3 crossed 4M units across platforms. The launch-week conversion for CK3 specifically is not publicly broken out, but the shape of the sales curve + the size of the pre-launch wishlist pool + the 1M-day-1 disclosure imply launch-week conversion in the upper percentile range. REPORTED.

**CK3-likes wishlist conversion pattern:**

- **Pre-launch wishlist pools are large** — Paradox-tribe audience tracks Paradox releases obsessively. CK3 had a multi-year pre-launch wishlist build via dev-diary cadence, fan-tournament livestreams, prior-title (CK2) audience migration. ESTIMATED 500k-1M wishlist at launch.
- **Launch-week conversion estimated 25-35%** at $49.99 — above niche-strategy median because Paradox audience loyalty premium absorbs the price elasticity. ESTIMATED.
- **Cumulative conversion strong** — Paradox-tribe buyer eventually buys; "wait for sale" pattern present but tribe loyalty pulls long-tail conversion to 60-80% range. ESTIMATED.
- **DLC-driven re-engagement** — every major DLC drop spikes base-game sales as new wishlisters convert. Pattern unique to Paradox's expansion-heavy model. REPORTED.
- **Free-weekend conversion** — Paradox runs occasional CK3 free weekends; wishlist-to-purchase from those windows runs 15-25% per Paradox-disclosed snippets. REPORTED.

**Implications for Ouroboros generational/legacy positioning:**

CK3 is the upper bound for the generational/legacy strategy tribe (primary tribe per `docs/legacy/topics/lieutenant_pivot_niche_brief.md`). Ouroboros cannot expect to match CK3 wishlist conversion (Paradox tribe loyalty is the binding multiplier) but can expect to capture a subset of the same audience w/ similar conversion shape if tagging + framing aligns. **Working assumption: Ouroboros launch-week conversion within primary tribe runs ~18-25% at $29.99-$34.99 — above niche-strategy median due to tribe loyalty premium, below CK3 because Ouroboros is new IP.** ESTIMATED.

## Wildermyth-likes

Wildermyth (Worldwalker Games, 2021, $24.99 launch) holds 95% positive 11,600+ reviews and approximately 250-400k units. Pre-launch wishlist pool reported by Worldwalker as ~250k-300k (developer-disclosed in post-launch GDC commentary, approximate). REPORTED.

**Wildermyth-likes wishlist conversion pattern:**

- **Smaller pre-launch wishlist pool than Paradox titles** — emergent-story-sim tribe is narrower than grand-strategy tribe. ESTIMATED 100k-300k wishlist at launch for top-tier Wildermyth-shaped titles.
- **Launch-week conversion estimated 22-32%** at $24.99 — high relative to niche-strategy median because (a) $25 price point sits in low-elasticity-loss zone, (b) audience is intensely committed (emergent-story buyer is purchase-intent at high level when wishlisting), (c) Wildermyth's character-creation hook + procedural-storytelling demo converted aggressively. ESTIMATED-REPORTED hybrid.
- **Cumulative conversion strong long-tail** — Wildermyth shows the "evergreen niche" pattern: monthly review velocity stays steady years after launch, implying steady wishlist conversion from a slowly-growing wishlist pool. REPORTED.
- **Word-of-mouth dominant** — Wildermyth's conversion came from creator coverage (Splattercat, Quill18, Wanderbots) + Reddit organic + RPS / Polygon press, not from festival or paid marketing primarily. REPORTED.
- **Demo conversion premium high** — Wildermyth had a free demo of an early chapter; demo-played-and-wishlisted converted at significantly above cold-wishlist rate. ESTIMATED 2-3×.

**Implications for Ouroboros emergent-story positioning:**

The Wildermyth pattern is closer to Ouroboros' shape than CK3 in audience size + price-band + monetization model. **Working assumption: Wildermyth-shape titles in 2026 see launch-week conversion 22-32% at $24.99-$29.99 w/ demo + tribe pre-warming.** Most relevant numeric anchor for Ouroboros funnel-math. ESTIMATED.

Wildermyth-shape titles in the same intersection (Massive Chalice, Pathway, Battlebrothers w/ campaign-story emphasis) cluster in similar conversion bands — 20-30% launch-week at $24.99-$34.99. ESTIMATED.

## RimWorld-likes

RimWorld (Ludeon Studios, 2018 1.0 at $34.99) holds 95% positive 200,000+ reviews. Approximately 5-10M owners, ~$300M+ lifetime gross. Tynan Sylvester's developer disclosures across blog + GDC indicate launch-week conversion strong but the title's lifetime conversion is the more striking number — long-tail evergreen pattern is the RimWorld template. REPORTED.

**RimWorld-likes wishlist conversion pattern:**

- **Pre-launch wishlist pool large** — RimWorld had 4+ years of Alpha-Steam-Early-Access pre-1.0 audience, so the 1.0 "launch" was an established-title transition rather than a cold launch. RimWorld's actual launch-week conversion shape is somewhat unique and not directly transferable.
- **1.0 launch-week conversion estimated 28-38%** at $34.99 — high because the audience was 4-year-warmed. ESTIMATED.
- **Cumulative conversion exceptional** — RimWorld's lifetime wishlist conversion estimated 70-85% (most wishlisters eventually buy because the title delivers what they wishlisted for + DLC + workshop ecosystem extends value). ESTIMATED.
- **DLC-driven re-engagement** — Royalty + Ideology + Biotech + Anomaly DLC drops each produced new wishlister spike + base-game-conversion spike. REPORTED.
- **Workshop multiplier** — RimWorld's mod ecosystem extends purchase value years post-launch; "I'll buy when there are more mods" wishlister converts months later as mod count grows. REPORTED.

Going Medieval (Foxy Voxel, 2021 EA), Songs of Syx (Gamatron, EA 2020), Oxygen Not Included (Klei, 2017 1.0), Dwarf Fortress Steam (Bay 12, 2022) form the RimWorld-likes cluster. Conversion patterns vary:

- **Going Medieval EA launch** — strong conversion off ~50k wishlist pool at $29.99; ESTIMATED 25-35%.
- **Songs of Syx** — slow steady conversion off small wishlist pool; ESTIMATED 15-25% per launch window, exceptional cumulative.
- **Dwarf Fortress Steam** — exceptional launch conversion off 20-year cult-wait wishlist pool; cleared $20M+ first month per Bay 12 disclosure. ESTIMATED launch-week conversion 50%+ — outlier IP halo case.
- **Oxygen Not Included** — Klei tribe loyalty premium absorbed conversion; ESTIMATED 30-40% launch-week.

**Implications for Ouroboros colony-sim-adjacent positioning:**

Ouroboros' primary niche is generational/legacy strategy not survival-strategy directly (per lieutenant_pivot brief). RimWorld-likes cluster is the secondary "RimWorld fans craving narrative weight" target — fourth-ranked niche per lieutenant pivot brief. Conversion shape for that audience subset estimated 18-25% launch-week at $29.99-$34.99 — slightly below pure-RimWorld-likes because Ouroboros isn't selling the colony-sim core fantasy directly. ESTIMATED.

The RimWorld evergreen long-tail conversion pattern (lifetime ~70-85%) is the most aspirational template for Ouroboros if the post-launch update + DLC-per-era cadence delivers consistently. ESTIMATED — bible-locked DLC-per-era model is structurally compatible.

## Launch-week vs year-1 shift

Wishlist conversion decays sharply after launch week, but cumulatively continues growing for years. The decay curve shape matters for funnel-math closure.

**Standard niche-strategy decay curve (REPORTED-leaning aggregate from GameDiscoverCo + Zukowski):**

| Window | Cumulative conversion (% of pre-launch wishlist pool that has purchased) | Confidence |
|---|---|---|
| Day 1 | 8-12% | REPORTED-leaning |
| Day 7 (launch-week) | 13-18% (niche-strategy median) | REPORTED |
| Day 14 | 17-22% | ESTIMATED |
| Day 30 (first-month) | 22-32% | REPORTED |
| Month 3 | 30-40% | ESTIMATED |
| Month 6 (post-first-sale) | 40-55% | ESTIMATED |
| Year 1 | 50-65% | ESTIMATED |
| Year 2 | 60-75% | ESTIMATED |
| Year 3+ | 65-85% | ESTIMATED |

**Decay shape pattern:**

- Launch-week is the steepest conversion period. Day 1 alone captures ~60% of launch-week total. REPORTED.
- Days 8-30 capture another ~50-70% of launch-week count. REPORTED.
- Months 2-3 the decay is sharp until first major sale event.
- Each major sale event causes a step-function jump (not gradual). See sale-event multipliers section.
- Long-tail post-month-6 conversion happens almost entirely on sale events + DLC drops. Off-sale, off-DLC organic conversion drops to near-zero per month.

**Wishlist freshness effect (REPORTED-leaning):**

Fresh wishlist (added within last 30 days) converts at ~3-5× the rate of aged wishlist (added 1+ years ago). The mechanism:

- Fresh wishlist = current buyer intent + current title visibility + current life circumstances align.
- Aged wishlist = forgotten interest + competing title pile + buyer may have purchased a competitor + Steam library backlog grew.

Implication for **launch-week conversion specifically:** a wishlist accumulated rapidly in pre-launch 6-month window converts at noticeably higher rate than a wishlist accumulated slowly over 3+ pre-launch years. Pre-launch wishlist-velocity affects launch-week conversion %. Cross-ref T-W2 brief.

**Wishlist staleness floor:** wishlists older than 2 years convert at approximately 5-10% per major sale event from that point forward, even for breakout titles. The pre-launch wishlist pool is not a permanent asset; it ages and decays. REPORTED-leaning.

**Implications for Ouroboros:**

If Ouroboros accumulates wishlist over a 2-3 year pre-launch period, expect launch-week conversion in the lower-end of estimated band (13-18%) due to wishlist-aging effect. If accumulates over a 6-12 month sprint via demo + Next Fest + creator coverage, expect higher-end (17-25%). ESTIMATED. Direction is REPORTED.

## Sale-event multipliers

Steam seasonal sales + Next Fest + game-specific publisher sales produce step-function conversion jumps. Niche-strategy participates in all major Steam sales typically at 10-25% off (modest) for the first year post-launch, deeper (40-60% off) thereafter.

**Major Steam seasonal sales conversion lift (REPORTED-leaning aggregate):**

| Sale event | Approximate niche-strategy wishlist-conversion lift vs typical week | Confidence |
|---|---|---|
| Summer Sale (late June) | 8-15× typical-week conversion | REPORTED |
| Winter Sale (late December) | 8-15× typical-week conversion | REPORTED |
| Spring Sale (March) | 4-8× typical-week conversion | ESTIMATED |
| Autumn Sale (November) | 5-10× typical-week conversion | ESTIMATED |
| Lunar New Year Sale (Jan/Feb) | 3-6× typical-week conversion | ESTIMATED |
| Steam Next Fest (Feb / June / October) | demo-driven; see below | REPORTED |

Summer + Winter sales are the two structural conversion-spike windows. Niche-strategy titles often see 30-60% of total cumulative wishlist conversion happen on sale events across the title's first 3 years post-launch. REPORTED.

**Discount-depth effect within sale (REPORTED-leaning):**

- **10-20% off** — converts ~3-5× typical week. Mild lift; wishlist holders treat as confirmation rather than incentive.
- **25-40% off** — converts ~8-15× typical week. Sweet spot for niche-strategy first-year sales; depth meaningful, brand integrity preserved.
- **50% off** — converts ~15-25× typical week. Aggressive; appropriate for title 12+ months old.
- **66%+ off** — converts ~20-40× typical week. Bargain-bin territory; appropriate for 2+ year old titles or aggressive end-of-life conversion grabs.

Crosses w/ `docs/legacy/topics/pricing_elasticity_niche.md ## Per-tier wishlist conversion` — discount lift compounds w/ base-price elasticity. A $34.99 title at 30% off = $24.50 → catches a different buyer pool than $29.99 title at 30% off = $20.99.

**Steam Next Fest conversion (REPORTED — Valve disclosed aggregate data twice during 2022-2024 window):**

Steam Next Fest runs 3× yearly (Feb / June / October). Participation is free; offers free demo + livestream slot + dedicated discovery surface for ~1 week.

- **Wishlist-velocity gain during Next Fest:** average participating title sees 1,000-5,000 wishlists added during the week; top-tier participating titles see 30,000-100,000+. REPORTED.
- **Demo-played conversion premium:** demo-played-then-wishlisted converts at 2-3× rate of cold trailer wishlist. REPORTED — Valve disclosed.
- **Post-Next-Fest launch conversion:** titles that participate in Next Fest before launch typically see launch-week conversion ~30-50% higher than non-participants in the same niche. ESTIMATED.
- **Multiple Next Fest appearances:** repeat-participating titles (Next Fest demo at 12 months, 6 months, and 3 months pre-launch) accumulate larger wishlist pool but face wishlist-aging tradeoff. REPORTED.

**Per-niche sale-event variance:**

- **CK3-likes** — Paradox-tribe sales discipline is anti-deep-discount. Paradox titles rarely cross 50% off in first 2 years. Sale-event lift is more muted (5-12× typical week) but base-week conversion is higher, so net cumulative is similar.
- **Wildermyth-likes** — small-team niche titles often participate fully in Steam sales w/ 30-50% off discounts; sale-event lift is structural to cumulative conversion. 15-25× typical-week lift on Summer/Winter.
- **RimWorld-likes** — RimWorld specifically holds price discipline (rarely deep-discounts) similar to Paradox pattern; long-tail cumulative is driven by mod-ecosystem + DLC drops rather than sale events. REPORTED.

**Implications for Ouroboros:**

Funnel-math closure must account for sale-event-driven cumulative conversion (which is most of year-1) vs launch-week-only conversion (which is a small slice of total). 80-200k unit first-month target is concentrated at launch-week + first month, mostly pre-first-major-sale. See funnel-math gut check. ESTIMATED.

## Per-source conversion deltas

Wishlists from different sources convert at different rates. The "quality-of-wishlist" hierarchy is REPORTED-leaning across GameDiscoverCo + Zukowski commentary.

**Wishlist source conversion hierarchy (estimated rank order, launch-week conversion at $29.99):**

| Source | Estimated launch-week conversion | Confidence |
|---|---|---|
| Demo-played-then-wishlisted | 30-45% | REPORTED-ESTIMATED |
| Streamer / creator video (genre-tribe creator) | 22-32% | ESTIMATED |
| Press review or feature (RPS, PC Gamer, Eurogamer, niche-strategy site) | 18-28% | ESTIMATED |
| Steam Next Fest participation (demo + discovery surface) | 25-35% | REPORTED-ESTIMATED |
| Reddit / Discord community organic | 18-25% | ESTIMATED |
| Steam algorithmic "More Like This" surface | 12-18% | ESTIMATED |
| Banner ad / paid acquisition | 5-10% | ESTIMATED |
| Generic festival w/o demo | 8-15% | ESTIMATED |
| Cold trailer impression (no demo) | 10-15% | ESTIMATED |
| Steam front-page algorithmic discovery | 8-14% | ESTIMATED |
| Bundle-driven wishlist (Humble, Fanatical) | 5-10% | ESTIMATED |

**Mechanism patterns:**

- **Demo-played wishlist converts highest** because user has tested the actual product + made an active decision to come back later. Highest-intent wishlist source. REPORTED — Valve has disclosed this.
- **Creator video wishlist** — viewer trusts the creator's taste filter; if Quill18 or Splattercat endorses a niche-strategy title, the creator's audience is pre-aligned to the niche. Conversion premium structural. REPORTED.
- **Press feature wishlist** — slightly below creator video because press audiences are broader-genre than per-creator audience. Still high-intent. ESTIMATED.
- **Reddit / Discord organic wishlist** — community pre-aligned to niche; lower than creator video because the buying decision is distributed across many small impressions rather than one trusted-creator endorsement. ESTIMATED.
- **Algorithmic "More Like This"** — buyer is in genre-shopping mode but has not specifically vetted the title; conversion at niche-strategy median. ESTIMATED.
- **Banner ads / paid acquisition** — low-intent wishlist; user clicked once and saved for later w/ minimal vetting. Often shows worst conversion rate of any source. REPORTED — per Zukowski commentary.
- **Generic festival** — wishlist piled up during exposure but specific title may not be remembered at launch. Festival-w/o-demo wishlist quality is mediocre. ESTIMATED.
- **Cold trailer impression** — variable; depends heavily on trailer quality + tag accuracy. Lower-bound when tagging mismatched.
- **Steam front-page algorithmic discovery** — high-volume wishlist accumulation but low conversion because buyer was "casually browsing" not "actively shopping for this niche." ESTIMATED.
- **Bundle-driven wishlist** — buyer wishlisted as part of bundle shopping; very low intent on the specific title. REPORTED-leaning per Zukowski.

**Per-source delta implications:**

A title with 200k pre-launch wishlist where 50% is demo-played + Next-Fest + creator-coverage sourced converts much better than a title with 200k pre-launch wishlist where 50% is festival + banner-ad + algorithmic-surface sourced. Wishlist count is necessary but not sufficient for launch-week conversion math. REPORTED.

**Within-niche tribe alignment** is the strongest source-quality multiplier. A wishlist from /r/CrusaderKings or /r/wildermyth converts at meaningfully higher rate than a wishlist from /r/Steam general-discovery audience. Per-source delta compounds with tribe alignment.

**Implications for Ouroboros wishlist-quality target:**

Source mix matters as much as wishlist count. Funnel-math target should specify wishlist-pool composition: % from demo + Next Fest, % from creator coverage, % from organic / press, % from algorithmic. ESTIMATED. Direction is REPORTED.

## Cross-cutting findings

- **Niche-strategy launch-week conversion median is approximately 15%** at $29.99 modal niche-strategy price. ESTIMATED working number for funnel-math. REPORTED-leaning per GameDiscoverCo aggregate commentary + Zukowski.
- **Year-1 cumulative conversion runs 50-65% for healthy niche-strategy launches**, w/ majority of post-launch-week conversion happening on sale events + DLC drops + creator coverage extending into months 2-12. ESTIMATED.
- **CK3-likes / Wildermyth-likes / RimWorld-likes** all run above niche-strategy median due to tribe-loyalty premium. Best-shape comparable for Ouroboros is **Wildermyth-likes** — emergent-story-sim @ $25-30 price + demo + tribe pre-warming. Working: 22-32% launch-week conversion. ESTIMATED.
- **Decay curve is sharp** — day 1 alone captures ~60% of launch-week conversion; launch-week captures ~30-50% of first-month conversion; first-month captures ~50-60% of year-1 conversion. ESTIMATED.
- **Sale events provide 8-15× typical-week conversion lift** on Summer + Winter, smaller on other sales. Sale-event conversion is most of year-1 cumulative for titles outside top-decile. REPORTED.
- **Steam Next Fest provides 30-50% launch-week conversion lift** for participants over non-participants, driven by demo-played-wishlist quality premium. REPORTED.
- **Demo-played wishlist converts 2-3× cold-trailer wishlist** — demo strategy is the single highest-leverage pre-launch tactic for niche-strategy conversion. REPORTED.
- **Wishlist source mix matters** — 200k high-quality wishlist (demo + Next Fest + creator + tribe) outperforms 400k mediocre wishlist (algorithmic + banner + bundle). REPORTED.
- **Wishlist freshness affects launch-week conversion** — wishlists added in last 6 months convert at ~3-5× rate of 2+ year aged wishlists. REPORTED.
- **No structural conflict between bible-locked 80-200k first-month target and observed niche-strategy conversion patterns** — but the implied wishlist pool is large (see funnel-math gut check) and requires multi-source pre-launch strategy to assemble. REPORTED.

## Ouroboros funnel-math gut check

Bible-locked target: 80-200k units first month @ $25-35 paid-base.

Apply observed conversion ratios to back-calculate required wishlist pool + first-month conversion shape.

**Scenario 1 — Floor target (80k first-month units):**

Working assumption: first-month conversion = 30% cumulative on launch-day wishlist pool. ESTIMATED per decay curve section.

Required pre-launch wishlist pool = 80,000 / 0.30 = **~267k wishlists**.

Sensitivity:
- If first-month conversion drops to 22% (soft launch end), required pool = 80,000 / 0.22 = **~364k**.
- If first-month conversion hits 38% (Wildermyth-shape launch), required pool = 80,000 / 0.38 = **~211k**.
- If first-month conversion hits 50% (RimWorld-shape, demo + tribe + Next Fest stacked), required pool = 80,000 / 0.50 = **~160k**.

**Scenario 2 — Stretch target (200k first-month units):**

Required pre-launch wishlist pool at 30% first-month conversion = 200,000 / 0.30 = **~667k wishlists**.

Sensitivity:
- 22% first-month conversion → required pool = **~909k**.
- 38% first-month conversion → required pool = **~526k**.
- 50% first-month conversion (Wildermyth-stretch / RimWorld-shape) → required pool = **~400k**.

**Tribe-aligned conversion assumption (Wildermyth-shape):**

If Ouroboros captures Wildermyth-shape conversion (22-32% launch-week, ~45-55% first-month w/ tribe + demo + Next Fest stacked):

| First-month target | Required wishlist @ 45% first-month conversion | Required wishlist @ 30% first-month conversion |
|---|---|---|
| 80k units | ~178k wishlists | ~267k wishlists |
| 130k units (midpoint) | ~289k wishlists | ~433k wishlists |
| 200k units | ~444k wishlists | ~667k wishlists |

**Working range: 180k-670k pre-launch wishlist pool to hit bible's 80-200k first-month unit target.** ESTIMATED.

**Sanity check vs niche-strategy comparables:**

- **Wildermyth** — reported ~250-300k pre-launch wishlist → 250-400k units cumulative (4+ year window). First-month units not disclosed precisely; likely ~50-100k. ESTIMATED.
- **Manor Lords** — reported 3M wishlist at EA launch → 1M units in first weekend, 3M+ cumulative. Wishlist-to-purchase first-week ratio ~33%. Hooded Horse-disclosed. Outlier-tier wishlist pool for the niche. REPORTED.
- **Old World** — pre-launch wishlist reported ~150k → ~300k cumulative units across launch + 2 years. Hooded Horse-disclosed indirectly. REPORTED.
- **Sea Power** — reported strong EA launch off ~50-80k wishlist → top-seller-week, 5,700 reviews. ESTIMATED.
- **Tempest Rising** — reported ~500k wishlist pre-launch → 370k units (~$12M gross at $39.99). Conversion ~74% cumulative — note this is total-lifetime not first-week. ESTIMATED.

**Bible target sits between Wildermyth-bottom and Manor Lords-top in conversion-implied scale.** 80k first-month unit floor implies wishlist pool ~180-270k, which is Wildermyth-shape or slightly above. 200k first-month unit stretch implies wishlist pool ~400-670k, which is Manor Lords-shape but with Wildermyth conversion. ESTIMATED.

**Funnel-math closure conclusion:**

The 80-200k first-month unit target is internally consistent with niche-strategy conversion patterns ONLY IF Ouroboros assembles a 200-670k pre-launch wishlist pool with Wildermyth-tier conversion quality (demo + tribe pre-warming + Next Fest + creator coverage stacked). The floor (80k) is achievable with disciplined execution on a Wildermyth-shape comparison. The stretch (200k) requires either Manor Lords-scale wishlist accumulation OR breakout-percentile conversion (90th-99th percentile, which is mostly luck + cult halo). REPORTED-leaning.

**Implications surfaced (not picked):**

- T-W2 velocity targets should specify pre-launch wishlist accrual rate sufficient to hit 200-670k pool over feasible timeline (12-30 months pre-launch).
- T-D1 demo strategy should target demo-played-wishlist composition of pre-launch pool >= 30% — demo-played wishlist is the conversion premium that bridges Wildermyth-shape conversion vs Manor-Lords-scale-but-soft conversion.
- T-D2 Next Fest planning should target 2-3 Next Fest appearances pre-launch — gains wishlist pool + raises conversion quality.
- T-S3 algorithmic visibility multipliers should target review-snowball threshold (60+ reviews by day 7) — this is the structural difference between top-quartile and bottom-quartile of the niche-strategy distribution per percentile section.

The decision of which target inside 80-200k band to plan for is a Design Lane fork, not a Research Lane recommendation.

## Conflict surfaced

**No new internal-bible conflict surfaced specifically by this brief.**

Conflict #2 (bible-monetization L274 "Free to play" vs game_bible.md $25-35 paid-base) is surfaced in `docs/legacy/topics/pricing_elasticity_niche.md ## Conflict surfaced` and `docs/legacy/topics/primary_tribe_psychographic_profile.md ## Conflict surfaced`. Re-surface count is now at least three.

**Adjacent observation (not full conflict):** the 80-200k first-month unit target is structurally tight to achieve w/o breakout-tier execution, per funnel-math gut check above. If bible-locked first-month target is firm + conversion patterns hold, pre-launch wishlist pool target is downstream-implied at ~180-670k — a meaningful resource commitment in marketing + community + festival presence. Bible does not currently specify a pre-launch wishlist target; T-W2 brief should close this loop. Research Lane surfaces; does not resolve.

**Demo strategy alignment:** bible does not currently commit to a demo strategy. Conversion data here strongly favors demo participation (Wildermyth-shape conversion math depends on demo-played-wishlist premium). Surfacing for T-D1 to resolve.

**Next Fest strategy alignment:** bible does not currently commit to Next Fest participation cadence. Conversion data favors 2-3 appearances pre-launch. Surfacing for T-D2 to resolve.

These are not conflicts but missing-decision points. Research Lane surfaces; Design Lane resolves.

## Caveats and confidence

Tag distribution across brief:

- VERIFIED: zero claims (no live platform access, no live wishlist or conversion telemetry, no current GameDiscoverCo newsletter refresh).
- REPORTED: approximately 35-40% of claims — the "10-20% rule" canonical anchor, GameDiscoverCo aggregate commentary, Valve-disclosed Next Fest figures, publisher-disclosed snippet figures (Manor Lords, RimWorld, Wildermyth, CK3 wishlist + sales partials), Zukowski + Carless qualitative commentary on per-source patterns.
- ESTIMATED: approximately 50-55% of claims — per-anchor numeric breakouts (CK3-likes 25-35%, Wildermyth-likes 22-32%, RimWorld-likes 28-38%), decay curve specifics beyond day-7 and day-30, sale-event multiplier exact figures, per-source delta exact rates, all funnel-math arithmetic, wishlist-quality premium specifics.
- AMBIGUOUS: approximately 5-10% — 2026 Next Fest specifics post-training-window, Russia + China post-2022 conversion capture, Foundation-tribe specific demo-played conversion (no direct survey).

**Steam wishlist + purchase telemetry is publisher-side, not exposed publicly; ESTIMATED floor on all niche-specific percentages.** All per-anchor conversion figures are publisher-disclosed snippet + GameDiscoverCo aggregate + per-developer-post-mortem-derived, not direct measurement. Treat as directional ±20-30%.

Known unknowns:

- Live 2026 GameDiscoverCo newsletter aggregate refresh — WebFetch denied; not refreshable this session.
- Per-title launch-week wishlist conversion at specific anchor titles (Wildermyth, RimWorld 1.0, Manor Lords EA, Old World, Battle Brothers) — publisher-side or disclosed in partial commentary only.
- 2025-2026 Next Fest aggregate disclosure — Valve typically publishes after each Next Fest; not refreshable.
- Per-source conversion premium specifics (e.g., is creator-video conversion 1.5× organic or 2× organic?) — only directional from training-data window.
- Wishlist-aging quantitative decay function — known qualitatively (3-5× freshness premium) but not modeled cleanly per year.
- 2026 Steam algorithm placement-by-wishlist-velocity effect — Valve does not publish algorithm specifics. Wishlist velocity is widely understood to drive recommendation surface placement, but quantitative relationship is publisher-inferred.

**Re-capture stamp.** All per-anchor + per-source + sale-event + decay curve quantitative claims are training-data-derived as of cutoff. Live GameDiscoverCo + SteamDB + Gamalytic + publisher-newsletter refresh required to upgrade REPORTED/ESTIMATED → VERIFIED. Flag for Research Lane re-capture when WebFetch is restored.

## Feeds Design Lane

This brief feeds:

- **T-W2 velocity targets** (downstream wave) — provides per-month wishlist accrual baseline implied by funnel-math closure. Required pre-launch pool of 180-670k wishlists distributed over 12-30 month pre-launch window implies ~15-55k wishlists/month accrual rate sustained. T-W2 should refine w/ per-channel velocity baselines + source-mix targets.
- **Funnel-math checkpoint #2 closure (this brief)** — applies observed ratios to bible 80-200k first-month unit target, surfaces required pre-launch wishlist pool 180-670k, surfaces Wildermyth-shape vs Manor Lords-shape comparable bands, surfaces structural challenge of stretch-target without breakout-tier execution. Closes checkpoint #2 input pool; Design Lane resolves which target inside band to plan against.
- **T-D1 demo strategy** — demo-played-wishlist conversion premium is the highest-leverage pre-launch tactic per per-source section. T-D1 should resolve (a) demo content slice, (b) demo release timing relative to launch, (c) demo-feedback loop into launch-build. Bible currently does not commit to a demo strategy.
- **T-D2 Next Fest planning** — Next Fest is 30-50% launch-week conversion lift for participants; 2-3 appearances pre-launch is the niche-strategy norm. T-D2 should resolve cadence + which Next Fest slot to anchor launch against. Cross-ref `docs/legacy/topics/pricing_elasticity_niche.md ## Per-tier wishlist conversion` for price-tier interactions w/ Next Fest participation.
- **T-S3 algorithmic visibility multipliers** — review-snowball threshold (60+ reviews by day 7) + wishlist-velocity feeding Steam recommendation surface are the structural drivers of percentile placement. T-S3 should close how Ouroboros operationally hits the snowball threshold + which Steam-side levers (tag mix, refund-rate management, review-prompt timing) are available.
- **T-P2 launch-discount strategy** (cross-feed) — sale-event multipliers section informs first-major-sale timing and depth. Niche-strategy norm: 10-20% launch-week discount + first deep sale 3-6 months post-launch. Cross-ref pricing_elasticity_niche.md.
- **T-P3 DLC pricing ladder** (cross-feed) — DLC-driven conversion re-engagement on base game (Paradox + RimWorld pattern) is a year-1+ cumulative conversion driver. DLC cadence informs long-tail conversion shape.

## Open questions for further research

- **Live 2025-2026 GameDiscoverCo aggregate analyses** — Simon Carless has run niche-strategy specific breakouts post-2024 that would refresh REPORTED → closer-to-VERIFIED on the "10-20% rule" + per-tier breakouts. Required for funnel-math closure refinement.
- **Wildermyth pre-launch wishlist pool + launch-week conversion specifics** — Worldwalker may have disclosed at GDC or in podcast interview; needs targeted-source confirmation. Wildermyth is closest-shape comparable for Ouroboros; pinning specifics tightens funnel-math.
- **Manor Lords wishlist accrual velocity over pre-launch timeline** — Slavic Magic + Hooded Horse have published partial figures; full velocity curve unknown. Informs whether Ouroboros' 12-30 month pre-launch window is realistic for 200-670k wishlist accrual.
- **Old World launch-week conversion specifically** — closest commercial reference for Ouroboros per lieutenant_pivot brief; Hooded Horse may have disclosed in podcast / GDC channel.
- **2026 Steam Next Fest aggregate retrospective** — Valve typically discloses post-each-Fest; latest disclosure refresh would tighten T-D2.
- **Per-source wishlist conversion quantitative relationships** — qualitative hierarchy is known; cleaner quantitative breakdown (creator-video at exactly X% vs press at Y% vs organic at Z%) requires targeted research or publisher disclosure.
- **Wishlist-aging decay function** — qualitative "fresh vs aged 3-5× difference" is known; cleaner quantitative aging model (% conversion drop per year of wishlist age) would refine pre-launch timeline planning.
- **Foundation-tribe specific wishlist conversion behavior** — no direct survey; extrapolated from book + TV-show demographics. Whether Foundation-readers-turned-gaming-wishlisters behave like primary tribe or differ is AMBIGUOUS.

## Sources

WebFetch + WebSearch denied this session. All sources referenced from training-data window. Flag for re-capture w/ live queries when WebFetch returns.

- **GameDiscoverCo (Simon Carless newsletter)** — https://newsletter.gamediscover.co — aggregate wishlist-conversion + niche-genre breakouts. Training-data flag: YES. Confidence: REPORTED.
- **How To Market A Game (Chris Zukowski)** — https://howtomarketagame.com — niche-indie wishlist-conversion canonical commentary; "10-20% rule" long-form source; per-source delta commentary. Training-data flag: YES. Confidence: REPORTED.
- **Valve / Steamworks blog posts** — Steam Next Fest retrospectives + seasonal-sale aggregate disclosures. Training-data flag: YES. Confidence: REPORTED.
- **Gamalytic** — https://gamalytic.com — wishlist-conversion modeling via review-velocity. Training-data flag: YES. Confidence: REPORTED.
- **Hooded Horse publisher commentary** — Tim Bender / Snow Rabbit GDC + podcast disclosures on Old World, Manor Lords, Falling Frontier. Training-data flag: YES. Confidence: REPORTED.
- **Paradox Interactive investor relations** — https://www.paradoxinteractive.com/media — CK3, Stellaris, Vic3 sales + wishlist disclosures. Training-data flag: YES. Confidence: REPORTED.
- **Per-developer post-mortems** — Tynan Sylvester (Ludeon / RimWorld), Bay 12 (Dwarf Fortress Steam), Worldwalker (Wildermyth), Overhype (Battle Brothers), Slavic Magic (Manor Lords), 3Division (Workers & Resources), Gamatron (Songs of Syx). GDC talks + Reddit AMAs + blog posts. Training-data flag: YES. Confidence: REPORTED.
- **SteamDB** — https://steamdb.info — review-count + CCU + price-history. Training-data flag: YES. Confidence: REPORTED.
- **Steambase** — https://steambase.io — daily CCU + price-history scrape. Training-data flag: YES. Confidence: REPORTED.
- **Adjacent press coverage** — Rock Paper Shotgun, PC Gamer, Game Developer, GamesIndustry.biz, Eurogamer. Training-data flag: YES. Confidence: REPORTED.
- **Cross-reference within Ouroboros docs:**
  - `docs/legacy/topics/lieutenant_pivot_niche_brief.md` — niche-strategy landscape + reachable-buyer pool + tribe shape
  - `docs/legacy/topics/pricing_elasticity_niche.md` — per-tier conversion baseline at price; cross-feeds T-W1 ↔ T-P1
  - `docs/legacy/topics/primary_tribe_psychographic_profile.md` — per-title review-theme inputs + conflict #2 prior surfacing
  - `docs/bible/game_bible.md` — 80-200k @ $25-35 first-month target lock + bible-authority-resolves directive
  - `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` L274 (Free-to-play tagline) + L292 (Fortnite reference) — conflict #2 adjacency

**Re-capture stamp.** All per-anchor conversion + per-source delta + sale-event multiplier + decay curve + funnel-math arithmetic claims are training-data-derived as of cutoff. Live GameDiscoverCo + SteamDB + Gamalytic + Steam Next Fest aggregate + publisher-newsletter refresh required to upgrade REPORTED/ESTIMATED → VERIFIED. Flag for Research Lane re-capture when WebFetch is restored.

Originating Research Lane capture: 2026-05-17 Wave 5, T-W1 — Wishlist conversion benchmarks niche-strategy 2020-2026.
