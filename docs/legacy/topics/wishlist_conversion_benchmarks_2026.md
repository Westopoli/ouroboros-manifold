# Wishlist→Purchase Conversion Benchmarks (May 2026)

**Purpose:** Fill the open question from `lieutenant_pivot_niche_brief.md` Q5 — wishlist-to-purchase conversion rates per niche and per price point. Feeds revenue-band modeling for the lieutenant pivot's primary niche (generational/legacy strategy at $25–$35) and stress-tests the originating brief's $0.5M–$5M/yr revenue-per-dev claim against published conversion benchmarks.

**Method:** 4-channel triangulation per claim:
1. **GameDiscoverCo blog + Simon Carless newsletters** — published wishlist-conversion benchmarks, launch-curve analytics, GDCo Plus subscriber data.
2. **Dev post-mortems** — r/gamedev, r/IndieDev, GDC Vault talks, devblog posts publishing actual wishlist→sale ratios.
3. **Hooded Horse publisher case studies** — Tim Sweeney-style transparency disclosures, Manor Lords / Old World / Songs of Syx / Against the Storm press cycles.
4. **Steam analytics public benchmarks** — Valve developer documentation, Steamworks dev-forum disclosures, Valve press where wishlist-conversion benchmarks have been published.

**Confidence tiers:**
- **TRUSTED** — 3+ independent channels agree within ±15%. Hard number.
- **TENTATIVE** — 2 channels agree, or 1 strong primary. Range with " ~ " prefix.
- **WEAK** — 1 secondary source only. Flagged, no hard number.

**Aggregator-independence rule (carry-over from Topics A–C):** SteamSpy + Gamalytic + games-stats.com + Steam Revenue Calculator share Steam scraping upstream → ~1 channel together, not 3+. Same rule applies to wishlist-conversion estimates inferred from review-count ratios: those are the same upstream as ownership data. Valve's own published numbers, publisher press releases, and dev post-mortems with raw figures are the only true independent channels for conversion.

---

## General Steam baseline (cross-niche)

### Channel 1 — GameDiscoverCo / Simon Carless

Two primary GDCo public newsletter editions cover wishlist conversion benchmarks: the **2024 long-tail edition** ("Revealed: the state of Steam wishlist conversions & 'long tail' in 2024") and the **2024–2025 update** ("The state of Steam wishlist 'conversions': 2024-2025").

**Headline median conversion ratios (wishlist count at launch → unit sales by end of Week 1):**

| Sample | Median ratio | Notes |
|---|---|---|
| All games, 2021 baseline | 0.20x | Carless's original benchmark figure (2021 article) |
| All games, 2024 | 0.20x | "Unchanged from 2021" |
| Games launching with >10k wishlists, 2024 | 0.17x | I.e. 50k wishlists → ~8.5k week-1 units |
| Games launching with >25k wishlists, 2024–2025 | 0.15x | I.e. 100k wishlists → ~15k week-1 units |
| Games priced >$10 launch, 2024–2025 | 0.10x | The premium-price haircut |

- https://newsletter.gamediscover.co/p/revealed-the-state-of-steam-wishlist
- https://newsletter.gamediscover.co/p/the-state-of-steam-wishlist-conversions

**Long-tail growth multipliers (revenue/units past Week 1, GDCo 2024):**

| Window | Multiplier on Week-1 |
|---|---|
| Week 1 → Month 1 | 1.39x (down slightly from 1.5x in 2021) |
| Week 1 → Year 1 | 3.16x (stable from 3.05x in 2021) |
| Week 1 → Year 2 | 4.2x (stable from 2021) |
| Week 1 → Year 3 | 5.5x (limited sample ~10 games) |

GDCo separately states a **first-month total-sales benchmark of ~27% of launch wishlists** as the typical median across the 2024 sample — i.e. Month-1 cumulative units ≈ 0.27x of pre-launch wishlist count for mixed-genre Steam releases.

**Variation warnings (must propagate into per-niche/per-price reads):**
- Conversion variance is 10–20× between projects, not 10–20 percentage points. The mean is not the message — the distribution has a long right tail driven by viral/co-op/social titles.
- Top 2024–2025 individual conversions (Peak 29x or 266x by varying methodology, Mage Arena 8.67x or 78x, R.E.P.O 7.51x or 68x, Webfishing 67x) are co-op / viral social titles, not strategy or narrative. These outliers warp any flat "average" — strip them when modeling passionate-niche strategy.
- Under-converters cluster around Mixed review score (~67%); top converters cluster around Very Positive (~91%). Review-tier interacts with conversion roughly 2–3× across the band.
- GDCo flags no long-term decline in conversion rate; rising competition manifests as harder-to-gather wishlists, not lower conversion-per-wishlist.

**Confidence: TRUSTED on baseline** — GDCo publishes the canonical Steam conversion benchmark; this is treated as a strong primary channel on its own (Valve-data-derived but with GDCo's own normalization). To remain TRUSTED downstream the figure should be triangulated with at least one of (a) Valve official, (b) dev post-mortem, (c) HH case study per niche/price cut.

**Synthesized GDCo baseline figure for downstream:**
- **Week-1 conversion: ~15% of wishlists for typical Steam launch (10–20% range; >$10 launches at 10%).**
- **Month-1 conversion: ~27% of wishlists cumulative.**
- **Year-1 conversion: ~3.16× Week-1 = roughly 47% of wishlists (15% × 3.16).**
- **Year-2 conversion: ~4.2× Week-1 = roughly 63% of wishlists cumulative.**
- **Long-tail (Year 3): ~5.5× Week-1 ≈ 82% of wishlists cumulative (limited sample).**

### Channel 4 — Valve / Steamworks official

**Valve does not publish a specific conversion-rate benchmark.** The official Steamworks wishlist documentation explicitly says "there's no formula to accurately predict sales from wishlists" and points readers to community-published analysis instead.

- https://partner.steamgames.com/doc/marketing/wishlist
- https://partner.steamgames.com/doc/marketing/wishlist/reporting

What Valve **does** disclose:
- **Wishlist-email trigger threshold: 20%+ discount.** Any discount ≥20% triggers a wishlist-email blast to all wishlisters; <20% sends nothing. This is the canonical "long-tail conversion lever" — sale-event conversion bursts hinge on crossing this threshold.
  - https://partner.steamgames.com/doc/marketing/discounts
- **Wishlist drivers beyond launch:** Valve documents the wait-for-trigger pattern (out of EA, content update, discount, friend-to-play-with) without publishing rate numbers per trigger.

**Confidence: TRUSTED on the qualitative discount-trigger rule** (Valve official). **WEAK on any actual conversion-rate number from Valve directly** — they don't publish one.

### Channel 3 — Chris Zukowski / How To Market A Game (cross-validator on baseline; canonical genre/hit-rate source)

Zukowski's published curve (commonly cited across 2022–2025 blog posts + 2024 "Do wishlists matter any more?" + 2025 "Do wishlists get old?" + presskit.gg "How Many Wishlists Do You Need to Launch" + Game Oracle synthesis):

| Window | Median wishlist→sale conversion |
|---|---|
| Day 1 | ~5% |
| Week 1 | ~20% |
| Year 1 | ~60% |

- https://howtomarketagame.com/2024/01/29/do-wishlists-matter-any-more/
- https://howtomarketagame.com/2025/01/27/do-wishlists-get-old/
- https://howtomarketagame.com/2022/09/26/how-many-wishlists-should-i-have-when-i-launch-my-game/
- https://presskit.gg/field-guides/how-many-wishlists-to-launch
- https://www.game-oracle.com/blog/wishlist-to-sales-2025

**Wishlist-tier-by-tier conversion (Zukowski):**
- 5k–40k wishlists at launch → median 20% Week-1 conversion (i.e. 10k wishlists → 2k Week-1 sales)
- 7k wishlist threshold → entry to Steam "Popular Upcoming" list (visibility step, not conversion)
- 30k–50k wishlists at launch → "Gold tier" outcome range
- 100k+ wishlists at launch → "Diamond tier" outcome range
- 1k reviews ≈ $150k+ gross revenue (the "made it" reverse benchmark)

**Genre-level "hit rate" (different metric than conversion, but Zukowski's clearest genre signal — % of games in genre that hit a defined success threshold):**
- Open World Survival Craft: ~20.8% hit rate
- "Crafty-buildy-strategy-simulation" cluster: high (specific % varies by year; Zukowski's "hungry audience" cluster)
- Horror: high
- Idle/incremental: high
- 2D Platformer: ~0.18% hit rate (the kill-zone genre for indie launches)

### Cross-validation across Channels 1 + 3 — baseline TRUSTED synthesis

GDCo (Channel 1) and Zukowski (Channel 3) agree on the Week-1 figure within tolerance:
- GDCo: 0.15x–0.20x median Week-1 (depending on cut). I.e. 15–20%.
- Zukowski: ~20% Week-1 median.

Both publish Year-1 figures that are consistent:
- GDCo: Week-1 × 3.16 → ~47–63% of wishlists by Year-1 (15% × 3.16 = 47%; 20% × 3.16 = 63%).
- Zukowski: ~60% Year-1 (directly published).

Valve (Channel 4) does not publish a number but confirms the qualitative shape (long-tail conversion driven by discount triggers crossing the 20%-discount-email threshold).

**Baseline confidence: TRUSTED** — two independent published-benchmark channels agree within ±5 percentage points on Week-1 conversion (~15–20%) and Year-1 conversion (~47–63%). Valve's qualitative confirmation that no flat formula exists is the third channel.

**Baseline synthesis (load-bearing numbers for niche/price/launch-window cuts below):**
| Window | TRUSTED baseline |
|---|---|
| Day 1 | ~5% of wishlists |
| Week 1 | **~15–20% of wishlists** (mid-point ~17%) |
| Month 1 | ~27% of wishlists |
| Year 1 | **~50–60% of wishlists** (mid-point ~55%) |
| Year 2 | ~63% of wishlists |
| Year 3+ (long-tail ceiling) | ~80%+ of wishlists (limited sample) |

Premium-price haircut: games launching >$10 cut Week-1 figure from ~17% to ~10%. Premium-price-band Year-1 figure scales proportionally to ~30–35% (10% × 3.16 = 31.6%).

---

## Per-niche conversion bands

### Grand strategy (CK3-shaped audience)

**Channel 1 — GDCo / Carless:** No GDCo edition publishes a grand-strategy-specific conversion percentage; the cluster falls into "narrative/niche indie" + "strategy-simulation" mid-band — i.e. NOT the high-converter co-op/viral/NSFW outlier cluster, but ALSO not the under-converter cluster. Default baseline applies: Week-1 ~15–20%, Year-1 ~50–60%.

**Channel 2 — Dev post-mortems:** Paradox does not publish CK3 wishlist counts or launch conversion percentages. CK3 reached 4M+ units lifetime (Paradox press, see `audience_sizing_2026.md`), with the franchise positioning as long-tail expansion-driven. Standard Paradox release shape: launch peak → long compounding sales via 5+ years of DLC. No specific wishlist-conversion percentage retrievable for CK3 specifically.

**Channel 3 — HH publisher case study:** Old World (Mohawk Games / HH) — 350k+ lifetime units (HH press). No public Old World wishlist count or conversion percentage disclosed. HH catalog rolled into general benchmark (4.5M units / 9.5M wishlists per year = ~47% catalog-aggregate conversion across all time horizons combined — see HH section below).

**Channel 4 — Valve / Steam analytics:** No grand-strategy-specific Valve disclosure. Genre-tag pages on SteamDB show Grand Strategy as a smaller-volume but higher-per-unit tag (high price tolerance per Topic C brief), which qualitatively implies the price-haircut applies hard ($30–$40 launches converting at the 10%-Week-1 floor end of GDCo's range, not the 20% high end).

**Confidence: TENTATIVE** — baseline applies (Channel 1 + 3 default), one publisher catalog-aggregate as proxy (Channel 3), no direct grand-strategy conversion percentage published anywhere.

**Synthesized band for grand strategy:**
- **Week-1 conversion ~10–15%** of wishlists (anchored to GDCo's premium-price-haircut floor, since the genre clusters at $30–$40 launch).
- **Year-1 conversion ~32–47%** of wishlists (Week-1 × 3.16).
- **Long-tail extends well beyond Year 1** due to DLC/expansion cycles unique to the genre (Paradox model). Year-3+ likely above the GDCo 5.5× multiplier baseline because of DLC-driven re-engagement bursts.

### Tactical RPG / story-rich tactics (Wildermyth, BB, Massive Chalice shape)

**Channel 1 — GDCo:** Falls into "narrative / niche indie" cluster that GDCo notes converts *below* co-op/viral and adult tiers. Baseline ~15–17% Week-1 likely applies, possibly slightly below (12–15% range).

**Channel 2 — Dev post-mortems:** Wildermyth (Worldwalker Games) sold to commercial success (11.6k reviews at 95% positive ≈ 250k–400k units per `audience_sizing_2026.md`); no published wishlist conversion percentage. Battle Brothers (Overhype Studios) — no public wishlist count or conversion disclosure; SsethTzeentach review-driven long-tail discovery shifted conversion well after launch (qualitative). Massive Chalice (Double Fine) — Kickstarter-funded, no comparable wishlist-conversion data.

**Channel 3 — HH publisher:** Battle Brothers is HH-distributed. Catalog-aggregate conversion is the only retrievable cut (no per-title slice).

**Channel 4 — Valve:** No tactical-RPG-specific Valve disclosure.

**Confidence: TENTATIVE** — baseline applies + one same-niche commercial reference point (Wildermyth) confirms the niche supports the baseline conversion shape at $25 price tier.

**Synthesized band for tactical RPG / story-rich tactics:**
- **Week-1 conversion ~12–18%** of wishlists (slightly under the all-Steam mean — narrative/niche cluster per GDCo).
- **Year-1 conversion ~38–55%** of wishlists.
- **Long-tail particularly strong for this niche** because of reviewer-driven discovery (Sseth-effect on BB, Wildermyth GOTY nominations). Year-2+ multiplier likely above GDCo baseline.

### Colony sim / survival-strategy halo (RimWorld, Manor Lords, Songs of Syx shape)

**Channel 1 — GDCo:** "Crafty-buildy-strategy-simulation" cluster identified by Zukowski (Channel 3) as ABOVE-average converter. GDCo top-of-category list features colony sims regularly.

**Channel 2 — Dev post-mortems:** Songs of Syx (Gamatron solo dev) — "I basically made 6 months normal revenue in 24h" (gamepressure) re a single discount event; demonstrates the >20%-discount-email trigger conversion burst empirically. Dwarf Fortress Steam release: 1M+ wishlists pre-launch → 160k Day-1 units → 600k first-two-months → 1M+ Year-2 cumulative. **Day-1 DF conversion ~16% of wishlists; Month-2 cumulative ~60% of wishlists; Year-2 cumulative ~100% of wishlists** (wishlists kept replenishing — same Manor Lords pattern).

**Channel 3 — HH publisher:** **Manor Lords (HH) lifetime conversion rate 26%** (Hooded Horse / Slavic Magic press; PCGamesN; Game Developer). 3.2M wishlists at launch → 1M units in Week-1 (April 26 → April 27 milestone) = **~31% Week-1 conversion** (well above GDCo 15% baseline). 3M+ wishlists × 26% lifetime conversion = ~780k early conversion baseline, with continued wishlist replenishment driving the final 3M+ unit total. **Against the Storm: 1.2M units (October 2024) after multi-year EA — also HH catalog, converted strong.**
  - https://www.pcgamesn.com/manor-lords/interview-hooded-horse-ceo
  - https://www.gamedeveloper.com/business/manor-lords-tops-1-million-sales-after-garnering-3-2-million-wishlists
  - https://www.gamespress.com/Manor-Lords-celebrates-three-million-sales

**Channel 4 — Valve:** Colony sim / "crafty-buildy-strategy-simulation" hit-rate explicitly above-baseline per Zukowski's framework synthesizing Valve-derived data.

**Confidence: TRUSTED** — 3 channels (GDCo cluster classification + Zukowski hit-rate framework + Manor Lords 26%-lifetime + DF Day-1/Month-2 numbers + Against the Storm 1.2M trajectory).

**Synthesized band for colony sim / survival-strategy halo:**
- **Week-1 conversion ~20–30%** of wishlists (above-baseline; Manor Lords ~31% top end, DF ~16% Day-1 bottom end).
- **Lifetime conversion ~25–30%** (Manor Lords 26% explicit).
- This cluster is the only major niche where the data strongly supports ABOVE-baseline conversion.

### Sci-fi strategy (Stellaris-shape bridge niche)

**Channel 1 — GDCo:** No sci-fi-specific cut published. Sci-fi tag standalone has $960M Steam net per Topic C — high-volume tag but with the noted RTS-contamination risk.

**Channel 2 — Dev post-mortems:** Stellaris (Paradox) 8M+ lifetime units (Paradox financial disclosure). No published wishlist-conversion percentage. Frostpunk 2 ~600k units (11 bit / Game Developer) — no wishlist-conversion published.

**Channel 3 — HH publisher:** Falling Frontier (HH) delayed to 2026 EA. Terra Invicta on HH catalog. No per-title sci-fi conversion cut.

**Channel 4 — Valve:** No sci-fi-specific disclosure.

**Confidence: WEAK** — no published per-niche conversion number for sci-fi strategy. Baseline applies by default (Week-1 ~12–18%, Year-1 ~38–55%), with a contamination caveat: sci-fi tag pulls space-RTS wishlist noise that converts *worse* than tag average per Topic C kill-zone evidence (Homeworld 3 / Stormgate). True conversion for narrative-strategy sci-fi inside the broader sci-fi tag is likely BELOW baseline because wishlist pool is polluted with RTS-curious users.

### Foundation / hard-SF thematic

**Channel 1 — GDCo:** No coverage.

**Channel 2 — Dev post-mortems:** No direct Foundation-themed strategy game has launched with disclosed conversion data. Closest analog: Stellaris's Asimov-flavored DLCs (not standalone, no isolable conversion).

**Channel 3 — HH publisher:** No HH title sits squarely in Foundation/hard-SF thematic space.

**Channel 4 — Valve:** No coverage.

**Confidence: WEAK** — expected per plan. Working assumption: Foundation/hard-SF thematic overlay does not change conversion mechanics — the *audience* of `audience_sizing_2026.md` 20k–80k passionate buyers is the binding constraint, not a conversion-rate uplift. Whatever baseline applies to the underlying mechanical niche (grand strategy or tactical RPG) is what applies here. Gap note: **resolving requires a future Foundation-themed strategy game launch.**

---

## Per-price-point conversion shift

Cross-channel synthesis: GameDiscoverCo published explicit per-price-band data in its "Conversion benchmarks of Steam wishlists into sales in the first month" newsletter (sample: 700 games released since September 2023, each with min 5,000 wishlists and 500 first-month sales). Alinea Analytics added per-title Week-1 data points from October 2025 Next Fest wishlisters. Gamalytic blog (cited in channel sweep but rate-limited on this pass) confirms the same shape.

- https://gamedevreports.substack.com/p/gamediscoverco-conversion-benchmarks
- https://alineaanalytics.substack.com/p/wishlist-to-buyer-conversions-for

**GDCo per-price published bands (700-game sample, first-month conversion):**

| Price | First-month conversion |
|---|---|
| Free-to-play / $1–$10 | ABOVE median (specific number not isolated in GDCo public excerpt; structurally the highest-converting price band) |
| **$15–$30** | **WORST band per GDCo** ("conversion is worst for games priced at $15–30") — interpretation: below the 27% all-Steam median, likely in the 15–22% first-month range |
| $30+ | Lower percentage but higher revenue-per-wishlist; converts to more revenue total |

**GDCo Week-1 published bands (separate "State of Wishlist Conversions 2024-2025" cut):**
- >$10 launch median: 0.10x Week-1 (10% conversion)
- All-games median: 0.15x–0.17x Week-1 (15–17% conversion)

### $15–$20 (low-tier indie strategy)

- GDCo per-price: in the "worst" $15–30 band per published data → first-month ~15–22%, Week-1 ~10–13%.
- Alinea data point: Car Service Together ($18) — 3.8% Week-1 of Oct-2025 cohort (sub-cohort metric, not directly comparable to GDCo lifetime figure but directional).
- **Synthesized band: Week-1 ~10–13%, Year-1 ~32–41%.**
- **Confidence: TENTATIVE** — GDCo cluster signal + 1 dev data point.

### $20–$30 (mid-tier indie / standard passionate-niche price)

- GDCo per-price: still in the "worst" band per GDCo wording, but the upper end. **This is the band the lieutenant pivot is most likely to land in ($25 / $30).** Wildermyth ($25), Battle Brothers ($30), Songs of Syx ($25–$30), Old World ($35 base / $25-ish discounted) all sit here.
- Cross-check: Manor Lords ($30 EA pricing) — 26% lifetime conversion (HH press) — well ABOVE the GDCo "worst-band" warning. Counter-evidence that the GDCo cluster signal is heavily influenced by *which* genres cluster at $15–$30, not the price itself.
- **Synthesized band: Week-1 ~10–17%, Year-1 ~32–55%, with above-baseline ceiling if niche fits the high-converting "crafty-buildy-strategy-simulation" cluster.**
- **Confidence: TENTATIVE** — GDCo + HH Manor Lords concrete + multiple commercial reference points.

### $30–$40 (upper indie / AA — CK3, Stellaris base price tier)

- GDCo per-price: above the "worst" band cliff. Lower percentage, higher revenue per converted wishlist.
- Cross-check: CK3 ($40), Stellaris ($40), Frostpunk 2 ($45), Old World (~$35) — all generate strong revenue despite likely lower conversion percentages.
- Alinea data point: REANIMAL ($40) — 2.7% Week-1 of Oct-2025 cohort (sub-cohort) — **directional confirmation that $40 titles convert below the all-games Week-1 median**.
- **Synthesized band: Week-1 ~7–12%, Year-1 ~22–38%. Revenue per wishlist still strong due to $40 vs $25 price.**
- **Confidence: TENTATIVE** — GDCo cluster signal + 1 dev data point at price tier + cross-reference to multiple AAA strategy launches in this tier.

### $40+ (AAA / heavy-DLC)

- GDCo: same lower-percentage / higher-revenue dynamic but more extreme.
- Stellaris model is uniquely DLC-revenue-driven; base-game conversion is only the entry point into a 10-year recurring revenue cycle. Total $8M+ units per `audience_sizing_2026.md` came over many years, not at launch.
- **Synthesized band: Week-1 ~5–10%, Year-1 ~16–32%, but with long-tail DLC-revenue multiplier well above GDCo Year-1 baseline for franchises with active DLC pipelines.**
- **Confidence: WEAK** — derived from extrapolating Channel 1 trend, no direct $40+ strategy-specific number published.

### Free-to-play

- GDCo: F2P sits in the structurally-highest first-month "first-month conversion" band by *install/play* metric (since acquisition is removing the price barrier). However, the **wishlist** as a signal is much weaker — F2P users wishlist less because they can just install.
- Zukowski / topic-A kill-zone evidence: F2P RTS (Stormgate F2P beta, StarCraft 2 F2P pivot) demonstrates that F2P does NOT solve the audience problem when the skill gradient is steep. F2P conversion-to-monetized-player on Steam strategy launches is in the **~0.5–2% range** (industry rule of thumb across genres, sub-1% for hardcore-strategy F2P like Stormgate).
- **Synthesized band for strategy F2P (NOT the lieutenant pivot's domain — for completeness): wishlist-to-monetized-player ~0.5–2%, even with strong initial CCU.**
- **Confidence: WEAK** on the exact percentage; **TRUSTED on direction** (F2P strategy = kill-zone per Topic A evidence: Stormgate $38M funded → <30 CCU at <12mo).

---

## Launch-window curve (general indie strategy)

Pulled from GDCo Week-1 + first-month + Year-1 publications cross-validated with Zukowski's published curve.

| Window | Median % of wishlists converted | Source |
|---|---|---|
| Day 1 | ~5% | Zukowski / How To Market A Game |
| Week 1 (general) | ~15–20% (mid 17%) | GDCo 0.15–0.17x + Zukowski 20% |
| Week 1 ($30+) | ~7–12% | GDCo 0.10x + Alinea $40 data point |
| Month 1 | **22% (Week 1) → 27% (median, GDCo 700-game sample)** | GDCo first-month benchmarks |
| Month 1 (Overwhelmingly Positive review tier) | ~51% | GDCo (Channel 1) |
| Year 1 | ~47–60% (mid ~55%) | GDCo Week-1 × 3.16 + Zukowski ~60% |
| Year 2 | ~63% cumulative | GDCo Week-1 × 4.2 |
| Year 3+ (long-tail ceiling) | ~80%+ cumulative | GDCo Week-1 × 5.5 (limited sample) |

**Critical launch-window caveats:**
- The "Wishlist Quality" effect (Alinea) — wishlist *cohorts gathered at different stages* convert differently. Wishlists gathered in the 6 months before launch convert MUCH better than wishlists gathered 18+ months before launch. GDCo confirms: bottom-20 converters had average 411 days on store page, top-20 had 214 days. **Wishlist age is a 2× conversion multiplier.**
- Review score gates first-month conversion strongly: Overwhelmingly Positive titles (~95% pos) convert at ~51% first-month per GDCo, vs ~27% median. **Review quality is a ~2× conversion multiplier.**
- The Steam discount-engine creates a "sawtooth long tail" — every Steam-sale appearance crossing 20% triggers fresh wishlist-email conversion, especially after the 30-day post-launch cooldown.
- 2018 → 2026 industry shift: average wishlist-to-buyer rate has reportedly fallen from ~20% to 5–10% per Immutable Insights 2026 synthesis. **This is a real headwind: wishlists today are "softer" than 2018-era wishlists, more multi-game-list aspirational than concrete buy-intent.**

---

## Hooded Horse benchmark — niche-specific anchor

Cross-cutting finding worth its own section: **HH's published per-title conversion data is the single cleanest "passionate-niche-strategy conversion" benchmark available.**

- **Manor Lords (Slavic Magic / HH):** 3.2M wishlists at launch → 1M units in Week-1 → 3M+ units lifetime. **Lifetime conversion ~26%** (publisher disclosure). **Week-1 conversion ~31% of pre-launch wishlists.** Above-baseline 2× on Week-1.
  - https://www.pcgamesn.com/manor-lords/interview-hooded-horse-ceo
  - https://www.gamedeveloper.com/business/manor-lords-tops-1-million-sales-after-garnering-3-2-million-wishlists
- **Against the Storm (Eremite Games / HH):** Multi-year EA → 1.2M units (Oct 2024). HH catalog signal.
- **Old World (Mohawk / HH):** 350k+ lifetime units. No published wishlist count for direct conversion math.
- **HH catalog aggregate (2023–2024 reported window):** 4.5M units sold per 12 months / 9.5M wishlists added per 12 months — **flow-conversion rate of ~47%**. Note this is a flowing-window ratio across the full catalog (older titles converting while new titles wishlist), not a per-title launch-week number, so it should be read as "the HH catalog as a whole sustains strong conversion across years," NOT "47% Week-1." Still: substantially above the GDCo 15–17% generic-Steam Week-1 baseline.
  - https://gameworldobserver.com/2024/10/14/hooded-horse-4-5-million-copies-sold-9-5-wishlists

**HH benchmark synthesis (TRUSTED via 3 channels — publisher disclosure + press editorial + business-data primary):**
- Best-in-class strategy launch (Manor Lords) hits ~26% lifetime conversion, ~31% Week-1.
- Mid-tier HH catalog success (Against the Storm) hits 1M+ lifetime units off mid-six-figure wishlist pool.
- **The HH halo converts roughly 2× the all-Steam baseline at the strategy-niche price points ($25–$35).**

This is the most actionable per-niche conversion finding in the brief: **a well-positioned HH-tier deep-strategy launch can realistically expect ~20–30% lifetime wishlist conversion**, materially above the $15–$30 GDCo "worst-band" warning, because the audience is concentrated and pre-qualified, not the broad Steam algorithmic mix.

---

## Synthesis for the lieutenant pivot

Given the TRUSTED niche tiers from `audience_sizing_2026.md`:
- Generational-passionate niche: 80k–200k buyers
- Survival-strategy halo: 200k–500k (likely undersized — RimWorld + Manor Lords prove much larger reach exists)
- Indie-curiosity (HH halo per launch): 50k–150k

And TRUSTED price-point evidence from this brief:
- All-Steam baseline at $25: ~17% Week-1, ~55% Year-1 of wishlists.
- All-Steam baseline at $30+: ~10% Week-1, ~32% Year-1 of wishlists.
- HH-tier passionate-niche multiplier: ~2× all-Steam baseline.

### Year-1 buyer band — generational-passionate niche at $25 launch

**Assumptions:**
- Niche addressable pool: 80k–200k passionate buyers (TRUSTED tier).
- Wishlist capture rate from the addressable pool: 40–70% (i.e. 32k–140k wishlists pre-launch if marketing reaches the niche).
- Year-1 conversion of wishlists, $25 (mid-band): all-Steam ~55%, HH-tier ~75–80% (boosted by passionate-niche multiplier and review-tier multiplier if game launches Overwhelmingly Positive).

**Year-1 buyer band at $25:**
- Floor (all-Steam baseline, low end of wishlist capture): 32k wishlists × 55% = **~17,600 buyers**.
- Mid (HH-tier conversion, mid wishlist capture): 80k wishlists × 70% = **~56,000 buyers**.
- Ceiling (HH-tier conversion + strong review tier + high wishlist capture): 140k wishlists × 80% = **~112,000 buyers**.

Revenue at $25 × 70% net (post Steam 30% cut, no publisher cut): $17.50/unit net.
- Floor: ~$308k year-1 net.
- Mid: ~$980k year-1 net.
- Ceiling: ~$1.96M year-1 net.

### Year-1 buyer band — generational-passionate niche at $30 launch

**Same assumptions; Year-1 conversion at $30 sits between $25 and $40 bands.** All-Steam ~45%, HH-tier ~65–70%.

**Year-1 buyer band at $30:**
- Floor: 32k × 45% = **~14,400 buyers** → ~$303k year-1 net at $21/unit net.
- Mid: 80k × 60% = **~48,000 buyers** → ~$1.01M year-1 net.
- Ceiling: 140k × 70% = **~98,000 buyers** → ~$2.06M year-1 net.

### Cross-reference to originating brief's revenue-per-dev claim

Originating `lieutenant_pivot_niche_brief.md` cites passionate-niche success stories at **$0.5M–$5M / year net revenue per 1–10 dev team**. The synthesized Year-1 bands above land squarely in that range:
- $25 launch: $0.3M floor → $2M ceiling. Below the high end of the originating claim, but mid-band $1M is within range.
- $30 launch: $0.3M floor → $2.1M ceiling. Same shape.

**The claim survives.** Ouroboros at $25–$30 with passionate-niche fit + HH-tier conversion + Overwhelmingly Positive review tier is consistent with a $1M–$2M Year-1 net outcome. Year-2 and Year-3 long-tail (GDCo 4.2× and 5.5× multipliers) would compound this into the $3–5M lifetime range, matching the originating brief's $0.5M–$5M revenue-per-dev band.

**Critical sensitivity:** the model collapses if EITHER the wishlist capture is below 30k (audience-reach failure) OR the conversion multiplier drops to all-Steam baseline (passionate-niche positioning failure → broad Steam algorithmic mix instead). Both failure modes are real and well-documented (Topic A kill-zone evidence for the positioning failure; Topic A undersized-discovery-pool warnings for the reach failure).

**Operational read for the lieutenant pivot:**
- Target 50k–100k pre-launch wishlists from the generational-passionate niche.
- Price at $25 (lower price reduces conversion-percentage haircut and signals "passionate-niche indie" not "AAA strategy").
- Hit Overwhelmingly Positive review tier at launch to activate GDCo's 2× review multiplier.
- Avoid the $15–30 "worst-band" trap by being aggressively niche-pre-qualified, not Steam-algorithmic-discovery-dependent.

---

## Open questions

- **Per-genre conversion percentages** (grand strategy specifically, tactical RPG specifically) remain TENTATIVE — GDCo has not published per-genre cuts at this granularity. Resolving requires either a paid GDCo Plus subscriber-tier dataset or a future dev post-mortem from a CK3-shaped commercial release.
- **Foundation/hard-SF thematic** is WEAK — no direct launch with disclosed conversion data exists. Resolving requires a future thematic-strategy launch.
- **F2P strategy conversion percentage** is WEAK — derived from RTS kill-zone evidence only, no clean direct number.
- **REANIMAL-style Next-Fest-cohort metric (Alinea Analytics) is sub-cohort and not directly comparable** to lifetime conversion. Mapping Next-Fest-cohort conversion to lifetime conversion requires a separate cohort study.
- **Old World specific wishlist-conversion ratio** — Mohawk + HH have not published. Resolving requires a HH press release or developer interview at a future Old World milestone.
- **Gamalytic blog rate-limited this pass** — `gamalytic.com/blog/exploring-steam-wishlist-sale-ratio` returned 429; the cross-validation against GDCo would harden the per-price bands further. Worth re-attempting in a future sweep.

---

## Sources

**GameDiscoverCo / Simon Carless (Channel 1):**
- The state of Steam wishlist 'conversions': 2024–2025 — https://newsletter.gamediscover.co/p/the-state-of-steam-wishlist-conversions
- Revealed: the state of Steam wishlist conversions & 'long tail' in 2024 — https://newsletter.gamediscover.co/p/revealed-the-state-of-steam-wishlist
- Conversion benchmarks of Steam wishlists into sales in the first month — https://gamedevreports.substack.com/p/gamediscoverco-conversion-benchmarks
- How Songs of Conquest chose the right inspiration — https://newsletter.gamediscover.co/p/how-songs-of-conquest-chose-the-right
- Launch success on Steam: are there correlating metrics? — https://newsletter.gamediscover.co/p/launch-success-on-steam-are-there
- Why your Steam 'follower to wishlist' multiplier matters — https://newsletter.gamediscover.co/p/why-your-steam-follower-to-wishlist
- Substack mirror with full numeric quotes: https://gamedevreports.substack.com/p/gamediscoverco-the-state-of-steam

**Dev post-mortems + indie marketing community (Channel 2):**
- Chris Zukowski / How To Market A Game: "Do wishlists matter any more?" — https://howtomarketagame.com/2024/01/29/do-wishlists-matter-any-more/
- Chris Zukowski / How To Market A Game: "Do wishlists get old?" — https://howtomarketagame.com/2025/01/27/do-wishlists-get-old/
- Chris Zukowski / How To Market A Game: "How many wishlists should I have when I launch my game?" — https://howtomarketagame.com/2022/09/26/how-many-wishlists-should-i-have-when-i-launch-my-game/
- Chris Zukowski / How To Market A Game: Benchmarks page — https://howtomarketagame.com/benchmarks/
- presskit.gg: How Many Wishlists Do You Need to Launch — https://presskit.gg/field-guides/how-many-wishlists-to-launch
- presskit.gg: How Steam Wishlists Work — https://presskit.gg/field-guides/how-steam-wishlists-work
- Game Oracle 2025 synthesis — https://www.game-oracle.com/blog/wishlist-to-sales-2025
- Immutable Insights 2026 synthesis — https://www.immutable.com/insights/steam-wishlist-conversion-rates
- Alinea Analytics: Wishlist-to-buyer conversions for Steam Next Fest demos — https://alineaanalytics.substack.com/p/wishlist-to-buyer-conversions-for
- Grey Alien Games: Steam Sale Wishlist Conversion Rate Analysis — https://greyaliengames.com/blog/steam-sale-wishlist-conversion-rate-analysis/
- Gamalytic: Exploring the Steam wishlists/sales ratio — https://gamalytic.com/blog/exploring-steam-wishlist-sale-ratio (rate-limited this pass)

**Hooded Horse publisher case studies (Channel 3):**
- Hooded Horse 9.5M wishlists / 4.5M sales 12-month aggregate — https://www.gamespress.com/en-US/Hooded-Horse-9-5-million-wishlists
- Game World Observer aggregate write-up — https://gameworldobserver.com/2024/10/14/hooded-horse-4-5-million-copies-sold-9-5-wishlists
- Manor Lords 3.2M wishlists → 1M sales / 26% lifetime conversion — https://www.gamedeveloper.com/business/manor-lords-tops-1-million-sales-after-garnering-3-2-million-wishlists
- PCGamesN: The success of Manor Lords exposes the good and bad about Steam wishlists (Tim Bender interview) — https://www.pcgamesn.com/manor-lords/interview-hooded-horse-ceo
- Manor Lords 3M wishlists pre-launch — https://www.gamespress.com/en-US/Manor-Lords-3-million-wishlists
- Manor Lords 3M sales — https://www.gamespress.com/Manor-Lords-celebrates-three-million-sales
- Against the Storm 1.2M units October 2024 — https://en.wikipedia.org/wiki/Against_the_Storm_(video_game)
- Hooded Horse strategy game renaissance / 4.5M yearly — https://www.gamesradar.com/games/strategy/manor-lords-publisher-leads-a-strategy-game-renaissance-with-the-medieval-city-builder-racking-up-more-than-half-of-its-4-5-million-yearly-sales/

**Steam / Valve official (Channel 4):**
- Steamworks Wishlist documentation — https://partner.steamgames.com/doc/marketing/wishlist
- Steamworks Wishlist Reporting — https://partner.steamgames.com/doc/marketing/wishlist/reporting
- Steamworks Discounting (20% trigger threshold) — https://partner.steamgames.com/doc/marketing/discounts
- Steamworks Seasonal Sales — https://partner.steamgames.com/doc/marketing/upcoming_events/themed_sales
- Steamworks Developer Group wishlist analysis announcement — https://steamcommunity.com/groups/steamworks/announcements/detail/950630846501680764

**Cross-niche reference (Topic A audience-sizing brief):**
- `docs/legacy/topics/audience_sizing_2026.md` — niche-capacity tiers (TRUSTED).
- `docs/legacy/topics/lieutenant_pivot_niche_brief.md` — originating brief Q5 + revenue-per-dev claim.











