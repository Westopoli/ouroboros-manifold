---
name: Steam Algorithm Visibility
description: Popular Upcoming triggers, Discovery Queue weighting, New & Trending thresholds, wishlist-velocity multiplier, review-recency weighting, demo lift, festival boost, page-penalty patterns; feeds T-W2 wishlist velocity, T-D2 Next Fest, T-F2 festival roster, launch-week visibility plan.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 4 capture
---

# Steam Algorithm Visibility

## What this brief is

Surfaces Steam algorithm signals relevant to Ouroboros Manifold's pre-launch and launch-week visibility plan. Covers Popular Upcoming trigger criteria, Discovery Queue weighting factors, New & Trending threshold for niche strategy, wishlist-velocity multiplier on launch-day visibility, recent-vs-all-time review weighting, demo-presence lift, festival-participation boost duration, and patterns that get a Steam page penalized.

Feeds T-W2 wishlist velocity targets, T-D2 Next Fest timing, T-F2 festival roster selection, T-S1 tag slate (no-penalty surface), and the launch-week visibility playbook.

Brief surfaces inputs and does not recommend a pick. Steam algorithm is opaque; Valve discloses parts; everything below the REPORTED line is ESTIMATED — directional only. Do not load-bear on specific thresholds without re-confirming against current data close to launch.

## Method

Sources: Valve developer posts (Steamworks docs, Steam Business Update blog), Chris Zukowski analyses (How To Market A Game blog, podcast, GDC talks), GameDiscoverCo (Simon Carless newsletter and segmentation reports), GDC business-track talks, post-mortem threads on /r/gamedev and /r/IndieDev, indie developer blog posts with published wishlist/visibility numbers.

WebFetch denied this session. All material below draws on training-data floor: items published up to and slightly before model knowledge cutoff. Anything dated 2025+ is ESTIMATED via trend extrapolation. Specific numbers (e.g. "approximately 7,000 wishlists") treat as ±30% band. Mechanisms without numbers treat as REPORTED-pattern with no current-year calibration.

## Popular Upcoming

Popular Upcoming list appears on Steam front page for users browsing pre-release titles. Historically drives roughly 1,500 to 4,000 additional wishlists per day while title sits on list, depending on slot position and traffic. Confidence: REPORTED mechanism, ESTIMATED per-day band.

Trigger criteria are wishlist-count-driven plus release-date-proximity gated. Three threshold bands recur in indie post-mortems and Zukowski analyses:

- **Lower band — approximately 4,000 wishlists.** Sometimes hits Popular Upcoming for narrow categories or off-peak release weeks. Confidence: ESTIMATED.
- **Middle band — approximately 7,000 wishlists.** Most commonly-cited "soft floor" for Popular Upcoming visibility in mainstream release weeks. Confidence: REPORTED (multiple independent post-mortems converge).
- **Upper band — approximately 10,000+ wishlists.** Level that historically guarantees Popular Upcoming placement for several days regardless of competing releases. Confidence: ESTIMATED.

Release-date proximity is the second gate. Algorithm weights list more heavily as titles enter final 7-day window pre-launch, peaking in final 48 hours. Titles set more than approximately 8 weeks out get marginal Popular Upcoming visibility even at high wishlist counts. Confidence: REPORTED.

Third factor — wishlist velocity at time of evaluation, not just total — influences placement. Page adding 500 wishlists/day in final pre-launch week treated more favorably than same total at 50/day. Confidence: ESTIMATED. See § Wishlist-velocity multiplier.

Competing-release count matters. Quiet release weeks clear lower wishlist bar. Niche-strategy titles releasing in known-quiet windows (early August, mid-January, week between Christmas and New Year's) historically clear placement at lower counts. Confidence: REPORTED.

For Ouroboros 80k–200k unit target: wishlist floor for Popular Upcoming sits in 7,000–10,000 band assuming normal release week, with accelerating curve in final 14 days pre-launch to compound velocity weighting.

## Discovery Queue

Discovery Queue surfaces pre-release and recently-released titles to logged-in users in personalized batches of approximately 12 titles/day. Drives small but compounding wishlist growth across pre-release — typical indie titles report 50 to 300 wishlists/day attributed to Discovery Queue, sustained over months. Confidence: REPORTED mechanism, ESTIMATED per-day band.

Weighting factors known and inferred:

- **Tag overlap with viewer's history.** Heavy weight on tag match against games user owned, wishlisted, or played. Confidence: REPORTED.
- **Recency of page.** Newer pages get more impressions in first 4–8 weeks after publication. Confidence: REPORTED.
- **Page health signals.** Pages with capsule art, trailer, screenshots, longer description, active news posts get more impressions than pages missing any. Confidence: ESTIMATED — not disclosed but indie testing converges.
- **Wishlist count and trajectory.** Higher-wishlist pages get more impressions; curve flattens above approximately 10,000 wishlists. Below 1,000, traffic sparse. Confidence: ESTIMATED.
- **Tag affinity tightness.** Pages with tight, coherent slate (5–7 micro-niche-aligned tags) appear to outperform scattered slate of 10–15 weakly-related tags. Confidence: ESTIMATED. Connects to T-S1.
- **Negative tags on viewer profile.** Users mark tags they don't want; Queue respects. Page with problematic tag loses impressions to users who downvoted it. Confidence: REPORTED.
- **Geography and language.** Pages with localized store descriptions surfaced more often to matching locales. Confidence: REPORTED.

Practical inference: Discovery Queue is compounding pre-launch surface — small per-day yield, large cumulative yield if page lives on Steam 6–9 months pre-launch with active news cadence and tight tag slate.

## New & Trending

New & Trending appears in storefront category and tag-filtered views (visit Strategy tag, see New & Trending Strategy). Placement drives 100 to 1,000 wishlists/day during placement, with higher yield post-launch (turns into sales velocity). Confidence: REPORTED.

Threshold is wishlist-driven pre-release, sales-velocity-driven post-launch. Niche-strategy thresholds appear lower than mainstream-genre thresholds because absolute traffic in niche tags is smaller; algorithm normalizes against tag's typical volume.

ESTIMATED first-week-post-launch threshold for New & Trending in niche-strategy tag (Grand Strategy, 4X, Hard Sci-Fi): approximately 5,000–15,000 first-week units, or sustained first-week revenue approximately $100k–$300k. Lower end applies to less-trafficked tags; upper to higher-traffic. Confidence: ESTIMATED — niche thresholds not disclosed.

Pre-launch placement on New & Trending for relevant tag opens once wishlist count clears approximately 3,000 and accelerates entering final-week pre-launch window. Confidence: ESTIMATED.

Niche-specific notes:

- Grand Strategy tag has lower traffic than Strategy; New & Trending Grand Strategy easier at lower absolute counts. Confidence: REPORTED-pattern.
- 4X tag clusters mid-traffic — easier than Strategy, harder than Grand Strategy.
- Hard Sci-Fi tag overlap with strategy is sparse; titles that tag-cluster into Hard Sci-Fi + Strategy historically clear New & Trending in Hard Sci-Fi at very low absolute counts (low thousands first week). Confidence: ESTIMATED.

For Ouroboros 80k–200k target: hitting New & Trending in relevant niche tag in launch week is realistic if T-S1 slate is tight and launch-week sales clear lower-band threshold.

## Wishlist-velocity multiplier

Wishlist velocity — rate of accumulation in days/weeks before launch — multiplies launch-day visibility independently of total. Mechanism Zukowski and GameDiscoverCo describe: algorithm reads slope of wishlist curve, weights steepening-slope titles more heavily for launch-week surface allocation than flat-slope titles at equivalent totals.

ESTIMATED multiplier band:

- 10,000 wishlists over 18 months at flat 20/day rate: baseline launch-week visibility — 1.0x.
- 10,000 wishlists with most accumulated in final 8 weeks (steep curve, 50/day accelerating to 200/day): approximately 1.5x–2.5x baseline. Confidence: ESTIMATED.
- 10,000 wishlists where final-week rate plateaued or declined (flat/falling slope): approximately 0.7x–0.9x baseline. Confidence: ESTIMATED.

Mechanism interpreted as algorithm using velocity as proxy for "audience excitement" — bet is accelerating page indicates momentum continuing post-launch.

Practical implication for launch-week visibility plan: front-load major marketing beats (Next Fest, trailer drops, festival placements, streamer waves) into final 6–10 weeks pre-launch rather than spreading evenly. Pre-launch curve accelerating into launch outperforms curve front-loaded early.

For Ouroboros: argues for Next Fest placement timed approximately 6–10 weeks pre-launch, festival roster placements clustered in final 8 weeks, announcement/capsule-refresh beats spaced to drive visibly accelerating curve. See T-D2, T-F2, T-W2.

## Review-recency vs all-time

Steam displays Recent Reviews (default 30-day window) and All Reviews (lifetime). Algorithm appears to weight Recent more heavily than All for post-launch visibility decisions, especially for New & Trending and Discovery Queue surfacing beyond week ~4.

ESTIMATED weighting: Recent contributes approximately 60–70% of visibility-relevant review signal, All contributes remainder, in post-launch window beyond week 4. Confidence: ESTIMATED — exact weighting not disclosed.

Default 30-day window applies; algorithm appears to use default.

Consequences:

- Title shipping at 85% positive degrading to 65% in recent window loses visibility significantly even if all-time stays at 80%. Confidence: REPORTED-pattern.
- Title shipping at 70% improving to 85% recent (via patches and community work) gains compounding visibility. Confidence: REPORTED-pattern.
- Summary labels (Mostly Positive, Mixed, Mostly Negative) used as filters by users browsing tags. Falling from Mostly Positive to Mixed (below 70%) is visible cliff. Mixed to Mostly Negative (below 40%) is another.
- Review-bombing windows compress recent percent-positive disproportionately. Steam off-topic review tooling exists but does not always activate quickly.

For Ouroboros: post-launch patch cadence and community management directly affect visibility for months. Patch cadence maintaining/improving recent-reviews score is part of visibility plan, not separate workstream.

## Demo presence

Demo presence lifts base-game visibility through two mechanisms:

1. **Direct cross-link.** Demo and base-game pages link to each other; users discovering demo wishlist base game one click. Demos discovered via Discovery Queue, festival surfaces, or curators feed base-game wishlists. ESTIMATED yield: 30–60% of demo downloads convert to base-game wishlists for niche strategy titles. Confidence: REPORTED-pattern with niche variance.
2. **Algorithm signal.** Active demos contribute to base-game page's perceived health/activity. Pages with live demo, regular demo updates, demo-page news posts appear to get more Discovery Queue impressions on base-game page than equivalent pages without demo. Confidence: ESTIMATED.

Demo presence also unlocks Next Fest participation, a major standalone visibility beat (see § Festival boost). Next Fest requires working demo as entry.

Cross-effect with Next Fest is primary value driver. Demo for Next Fest week alone gets approximately 5,000–50,000 downloads during Fest for niche strategy titles (ESTIMATED, wide variance), translating to approximately 1,500–25,000 wishlists added during Fest week. Confidence: ESTIMATED.

Demos persisting after Next Fest drive base-game wishlists at lower compounding rate — typical 20–100 wishlists/day for demo lifetime, depending on tag-search traffic and demo discoverability. Confidence: REPORTED-pattern.

For Ouroboros: demo prepared for Next Fest and maintained as permanent free demo compounds with every other visibility surface. Demo presence is multiplicative with festival placement, wishlist velocity, Discovery Queue surfacing.

## Festival boost

Steam festivals (Next Fest, themed festivals like Strategy Fest, publisher-curated festivals, seasonal sales events) provide algorithm boosts to participants during festival window. Boost is real but time-limited; post-festival decay is steep.

Duration and decay pattern:

- **Festival week.** Participating titles get major Discovery Queue impression boosts, dedicated festival hub placement, and (Next Fest) live-stream surface placement. ESTIMATED wishlist yield for niche strategy titles during 7-day Next Fest: approximately 2,000–15,000 wishlists for title with competent demo and tight tag slate. Confidence: ESTIMATED, wide variance.
- **Week +1 post-festival.** Approximately 30–50% residual boost — algorithm continues surfacing page in Discovery Queue at elevated rates as recently-fest-featured signal decays.
- **Week +2 post-festival.** Approximately 10–20% residual.
- **Week +4 post-festival.** Algorithm returns to baseline; only wishlists added during festival persist as structural gain.

Confidence: REPORTED curve shape, ESTIMATED percent residual.

Participation criteria vary. Next Fest requires working demo, has scheduled entry windows (typically three Fests per year, each with entry deadline), limits titles to one Next Fest appearance per pre-launch lifetime. Themed festivals (Strategy Fest, Sci-Fi Fest) typically require matching tag and may have curator-style entry. Publisher-curated festivals follow publisher selection.

Single Next Fest at optimal pre-launch window (6–10 weeks pre-launch — close enough to leverage wishlist velocity into launch, far enough out that velocity boost compounds into launch-week surface) is the single highest-ROI pre-launch visibility beat available to indie titles. Confidence: REPORTED.

For Ouroboros: T-D2 Next Fest timing should target the Next Fest cycle approximately 6–10 weeks before launch. T-F2 festival roster should layer themed-festival placements in final 8 weeks to compound velocity into launch-week.

## Page penalties

Patterns documented as triggering visibility suppression. Mechanism rarely an explicit "penalty" — more typically reduction in Discovery Queue impressions, demotion from New & Trending, reduced algorithm trust over time.

Documented or strongly-suspected triggers:

- **Tag mis-fit.** Pages with tags not matching content (casual puzzle tagged Hardcore, Souls-like, or RPG to chase traffic) get user-downvoted via tag-downvote mechanism. Once critical mass of users downvote a tag on a page, tag effectively stops surfacing the page in that tag's filter. Continued fighting historically results in reduced Queue trust. Connects to T-S1 — slate must accurately reflect content. Confidence: REPORTED.
- **Capsule reuse.** Capsule closely matching another existing Steam product (intentional copycatting) historically triggers manual review and sometimes removal. Automated systems also suppress visibility on pages whose capsules match templates flagged for asset-flip families. Confidence: REPORTED.
- **Dormant updates.** Pages with no news posts, no patches, no community engagement for extended periods (multiple months) lose Queue impression weight. Algorithm interprets dormancy as inactive. For pre-launch matters less; post-launch matters significantly. Confidence: ESTIMATED.
- **Low-quality flag.** Steam automated system identifies pages appearing as asset flips, AI-generated shovelware, or low-effort (sparse description, recycled screenshots, no trailer, generic capsule). Pages flagged are suppressed from Queue almost entirely, depend on direct-search traffic. Confidence: REPORTED.
- **Review manipulation flags.** Pages where Steam detects coordinated review activity (review-for-key trades, friends-and-family review brigades, off-topic review bombing) get flagged. Reviews may be filtered or visibility reduced. Confidence: REPORTED.
- **Refund-rate signal.** Persistent high refund rates (typically above 15% in title's first month) appear to feed back into visibility weighting. Confidence: ESTIMATED — refund weighting not disclosed but pattern recurs in post-mortems.
- **Repeated price-history manipulation.** Pages frequently setting high MSRP and immediately discounting as fake-discount tactic appear flagged by Steam's discount-validation system; suppresses titles from sale-event surfaces. Confidence: ESTIMATED.

For Ouroboros: T-S1 tag slate must be content-honest, capsule original, news-post cadence active pre-launch and beyond, production quality clearing automated low-quality detection comfortably. Structural floors, not aspirations.

## Cross-cutting findings

- Wishlist velocity (slope) outperforms wishlist total (height) as launch-week visibility predictor; front-load marketing beats into final 6–10 weeks pre-launch.
- Discovery Queue is slow compounding surface, not launch-week surface; value accrues over months of pre-launch presence with active news cadence and tight tag slate.
- Next Fest is single highest-ROI pre-launch visibility beat; one shot per title, requires demo, 6–10 weeks pre-launch optimal for compounding into launch velocity.
- Recent Reviews weighs more heavily than All Reviews for post-launch visibility; community management and patch cadence are visibility levers, not separate workstreams.
- Demo presence compounds with everything else — Next Fest entry, base-game Discovery Queue, page-health signal, wishlist conversion. Multiplier on every other surface.
- Page penalty triggers are mostly structural floors (content-honest tags, original capsule, active news, no review manipulation, low refund rate) rather than tactical traps. Cost of clearing is page-craft discipline, not budget.

## Conflict surfaced

Check against T-S1 tag slate (`docs/research/topics/steam_tag_search_behavior_2026.md`): penalty surface around tag mis-fit must inform T-S1 final slate. If T-S1 recommends tags that materially overreach against actual Ouroboros content, tag-downvote risk and Queue trust loss flagged here applies. T-S1 needs content-honesty check pass before launch.

No other direct conflicts surfaced against current Wave 4 briefs.

## Caveats and confidence

Tag distribution across this brief:

- **REPORTED** — mechanisms with multiple independent indie post-mortems converging, or directly disclosed by Valve / Steamworks docs. Approximately 40% of claims.
- **REPORTED-pattern** — widely observed across indie reporting but without explicit Valve disclosure. Approximately 25%.
- **ESTIMATED** — specific numbers, thresholds, multipliers, weightings inferred from indie post-mortem ranges and analyst commentary. Approximately 35%.

Steam algorithm is opaque. Valve discloses parts through developer docs and conference talks; full weighting is not public and changes over time. Specific threshold bands (Popular Upcoming 4k/7k/10k, New & Trending 5k–15k first-week, Next Fest residual 30–50% week +1) are **directional bands**, not measured constants. Every specific number in this brief should be treated as ±30% minimum, with algorithm potentially shifting bands in either direction without notice between briefing and Ouroboros launch.

Re-confirm against current data 3–6 months before launch. 2026-05-17 capture is snapshot; pre-launch planning should refresh thresholds against current post-mortems close to launch decision point.

## Feeds Design Lane

- **T-W2 wishlist velocity** — targets should reflect velocity multiplier finding: total count matters less than accelerating curve into launch. Target accelerating curve 6–10 weeks pre-launch rather than flat at same total. Floor wishlist target approximately 7,000–10,000 at release for niche strategy aligns with Popular Upcoming band.
- **T-D2 Next Fest timing** — target Next Fest cycle approximately 6–10 weeks before launch to compound velocity. One shot per title; do not burn early.
- **T-F2 festival roster** — layer themed-festival placements (Strategy Fest, Sci-Fi Fest, publisher-curated) in final 8 weeks pre-launch to compound velocity. Avoid clustering festivals more than 12 weeks pre-launch where lift won't carry into launch.
- **T-S1 tag slate** — slate must be content-honest to avoid tag-downvote penalty. Tight slate of 5–7 micro-niche-aligned tags outperforms scattered slate of 10–15 weakly-related tags in Queue surfacing.
- **Launch-week visibility playbook** — front-load marketing beats into final 6–10 weeks pre-launch. Maintain active news cadence from page-publish through launch. Demo persists as permanent free demo after Next Fest. Post-launch patch cadence is part of visibility plan via Recent Reviews weighting.

## Open questions for further research

- Current (2026-mid) actual Popular Upcoming wishlist band — does 7k/10k floor still apply, or have thresholds shifted as platform traffic has grown? Requires fresh post-mortem data closer to launch.
- Specific New & Trending threshold for actual tag combination Ouroboros ships with — niche-tag-specific thresholds not disclosed, depend on T-S1 slate.
- Next Fest entry restrictions on previously-shown titles (publisher fests, Early Access) — confirm against current Steamworks docs closer to launch.
- Whether Steam Queue weighting has shifted to favor or disfavor AI-related content disclosures — currently uncertain whether AI-disclosure surface affects algorithm trust.
- Whether festival residual-boost curve has changed as Valve adds more themed festivals to the calendar — more festivals may dilute per-festival lift.
- Whether refund-rate weighting has formalized into visibility algorithm or remains soft pattern — affects post-launch demo-vs-base-game-quality risk planning.

## Sources

All sources accessed via training-data floor; WebFetch denied this session. Confirm against current versions closer to launch.

- Valve Steamworks documentation — developer portal sections on visibility, Discovery Queue, Next Fest [training-data]
- Steam Business Update blog posts — Valve's periodic disclosures about algorithm changes [training-data]
- Chris Zukowski — How To Market A Game blog posts on Popular Upcoming, wishlist velocity, Next Fest timing, tag strategy [training-data]
- Chris Zukowski — GDC talks and podcast appearances on Steam algorithm visibility [training-data]
- GameDiscoverCo / Simon Carless — newsletter and segmentation reports on Steam discovery surfaces and audience-tag overlap [training-data]
- GDC business-track talks — recorded sessions on Steam algorithm and indie launch playbooks [training-data]
- Post-mortem threads on /r/gamedev and /r/IndieDev — wishlist and visibility numbers self-reported by indie devs [training-data]
- Indie developer blog posts publishing wishlist curves and launch-week telemetry — various titles in strategy and 4X niches [training-data]
