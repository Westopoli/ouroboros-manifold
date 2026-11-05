---
name: Steam Next Fest Timing
description: Three annual cohort fit for niche-strategy; per-cohort wishlist delta; demo retention curve; pre-fest floor + post-fest decay; optimal gap-to-launch; once-per-game rule; premature-entry cautionary cases; feeds Ouroboros Next Fest pick, T-D1 demo strategy, T-W2 velocity targets, T-F1 launch window.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 5 capture
---

# Steam Next Fest Timing

## What this brief is

Surfaces inputs on Steam Next Fest cohort choice, wishlist deltas, demo retention curves, pre-fest visibility floor, post-fest decay, optimal gap to launch, once-per-game rule, premature-entry cautionary cases. Feeds Ouroboros Next Fest cohort pick, T-D1 demo strategy, T-W2 velocity targets, T-F1 launch window seasonality, T-F2 festival roster.

Non-rec disclaimer. Research Lane surfaces inputs only — never picks. Final cohort decision belongs to Westley in Design or Implementer Lane. WebFetch denied → training-data floor on figures. ESTIMATED tag attached where Valve has not published cohort-level data; REPORTED tag where third-party press/aggregator coverage exists.

## Method

Source pool: Valve's Next Fest blog posts and developer FAQ pages on Steamworks (training-data snapshot, last refresh January 2025); GameDiscoverCo Plus newsletters by Simon Carless on per-cohort wishlist conversion (training-data); Chris Zukowski's HowToMarketAGame blog and YouTube channel on demo retention and post-fest decay (training-data); Cliffski/Positech post-fest retrospectives; Tomas Sala (Falconeer) post-fest blogs; Aggro Crab and other indie post-mortems on Reddit r/gamedev; Steamworks developer documentation on participation rules. WebFetch disabled in this lane invocation → all figures should be treated as training-data floor and may be stale relative to 2026 reality.

Confidence taxonomy: REPORTED = third-party press/aggregator cited the figure; ESTIMATED = Research Lane synthesis from partial data; FLOOR = lowest plausible based on training-data only; STALE = pre-2025 figure that has not been re-confirmed.

## Three cohorts overview

Three Next Fest cohorts run per year: February, June, October. Roughly seven days each. Confirmed by Valve's Steamworks developer FAQ (REPORTED, STALE — Valve has occasionally shifted dates by a week or two).

**February cohort.** Falls 4–8 weeks after the late-November-through-January discount cascade (Autumn Sale → Steam Awards → Winter Sale → Lunar Sale). Audience has spent budget, has new games to play, and is recovering. Counter-balance: post-holiday hardware activations from Christmas gift consoles/PCs are searching for first new purchases. AAA-adjacency historically lighter — Q1 is a quieter release quarter (REPORTED). Niche-strategy density: moderate. Crusader-Kings-adjacent and 4X titles often demo here because Q2 announcement-and-launch cycle aligns with summer streaming push.

**June cohort.** Falls into pre-Summer-Sale window (Summer Sale typically late June through early July). Highest-traffic cohort by raw Steam concurrency (REPORTED — Valve cited June 2022 cohort as record-setting at the time, training-data floor). AAA-adjacency heaviest: Summer Game Fest, June PlayStation/Xbox/Nintendo showcases, plus the Future Games Show drown the indie signal. Niche-strategy density: heavy — most strategy/sim publishers anchor to summer because of Steam Summer Sale tie-in for back-catalog. Discoverability is paradoxically worse despite higher traffic: the algorithm's top-of-page real estate goes to AAA, and the strategy/sim niche page is fully booked.

**October cohort.** Falls 4–8 weeks before Autumn Sale and 10–12 weeks before Winter Sale. Pre-holiday wishlist farming window — buyers are actively building wishlists they will spend down in November-December. Niche-strategy density: moderate-heavy. AAA-adjacency: Q4 is the AAA launch peak, so the noise floor on Steam front page is high, but Next Fest itself is a separate surface and benefits from the wishlist-farming mindset. This is the cohort most frequently cited by indie post-mortems as highest-converting per-wishlist (REPORTED, ESTIMATED on the magnitude — Zukowski and GameDiscoverCo both have argued October over June, but neither has published a clean A/B).

**Niche-strategy seasonal fit.** ESTIMATED ordering for generational/legacy strategy with hard-SF theming: October > February > June. Rationale: October aligns with pre-holiday wishlist build, February aligns with low-AAA-noise discoverability and post-holiday hardware activation, June is high-traffic but the niche-strategy slot is over-served and the page surface is contested by AAA. Confidence: ESTIMATED — the relative ranking is consistent across Zukowski, GameDiscoverCo, and indie post-mortems but the magnitude of the gap is not well-quantified in training-data.

## Per-cohort wishlist deltas

Observed wishlist delta = (wishlists during Next Fest week) − (baseline week wishlists from same Steam page over a comparable pre-Fest interval). All figures below are ESTIMATED training-data floor and should be treated as ±50% for any single title.

**Median niche-strategy participant.** 5,000–15,000 wishlist gain across the seven-day fest. REPORTED floor; titles below 5,000 are common; titles above 15,000 require either viral trailer, influencer pickup, or pre-existing audience (sequel, established studio, IP halo).

**75th percentile niche-strategy participant.** 15,000–40,000 wishlists. Requires good capsule, strong demo first impression, and at least one mid-tier YouTube/Twitch pickup during the week. ESTIMATED.

**Outlier successes (top 5%).** 50,000–200,000+ wishlists. Manor Lords' pre-launch demo cycle (not strictly a single Next Fest but adjacent) is the high-water-mark template — multiple capsules, strong influencer push, and category timing. Vampire Survivors-style outliers exist but are not a planning baseline. REPORTED at the high end, ESTIMATED on apportionment to Next Fest specifically.

**Cohort-comparative ESTIMATED multipliers** for a median-quality niche-strategy demo:

- October: 1.0× baseline
- February: 0.7–0.9× baseline
- June: 0.6–0.8× baseline (higher absolute traffic but lower per-impression conversion against AAA noise)

These multipliers are the Research Lane's best synthesis from partial training-data. Valve does not publish cohort-level deltas publicly. Confidence: ESTIMATED — should not be treated as planning-grade until validated against 2025–2026 cohort post-mortems via WebFetch when available.

**Page-quality dependency.** Wishlist delta is heavily a function of capsule, trailer first three seconds, and tag accuracy. A weak page in October will under-perform a strong page in June. Cohort choice is a second-order factor compared to page quality. REPORTED — this is a consensus point across Zukowski, Carless, and most indie post-mortems.

## Demo retention curves during fest week

**Day-shape across the seven-day fest.** Day 1 is the spike. Days 2–3 are a second smaller bump (algorithm surfaces and influencer pickup catches up). Days 4–5 are a trough. Days 6–7 (especially the final 48 hours) are a second spike from procrastinators and from "Last Day of Next Fest" surfacing. REPORTED, training-data floor — this U-shape is consistently cited but the trough depth varies.

**Hourly within day.** Peak install hours are 18:00–22:00 in each major Steam region. The fest gets unique-installer waves: NA evening, EU evening, JP/KR evening. ESTIMATED.

**Retention milestones (good vs bad demo).**

- **Install → launch.** Good: 70–85% of installers actually launch the demo. Bad: 40–55%. Driver: store-page-to-demo-button friction, demo size, demo build stability on launch. REPORTED at the band level, ESTIMATED on precise thresholds.
- **Launch → 1 minute.** Good: 85–95% still playing at 1 minute. Bad: <70%. Driver: launch screen, main-menu friction, immediate crash bugs. ESTIMATED.
- **1 minute → 10 minutes.** Good: 50–70%. Bad: <30%. Driver: tutorial pacing, first-meaningful-decision time, art/sound first impression. ESTIMATED.
- **10 minutes → 30 minutes.** Good: 30–50%. Bad: <15%. Driver: core loop legibility, the "I get it" moment. This is the wishlist-conversion window — players who hit 30 minutes wishlist at 3–5× the rate of <30-minute players. ESTIMATED, REPORTED at the wishlist-correlation level (Zukowski has cited this repeatedly).
- **30 minutes → end of demo.** Good: 20–40%. Bad: <10%. Driver: content density and replay hook.

**Good demo retention shape:** front-loaded engagement, strong 10-minute "I get it" moment, replay or "one more turn" hook at 30–45 minutes.

**Bad demo retention shape:** slow tutorial bleed, no clear core-loop reveal in first 10 minutes, single-run demo without replay hook → players churn at end of single run and never come back.

## Pre-fest wishlist floor

Algorithmic visibility threshold for Next Fest. Cross-ref T-S3 Steam algorithm visibility brief.

Valve does not publish a public threshold. Indie consensus (Zukowski, Carless, multiple Reddit r/gamedev post-mortems): demos with 5,000–10,000+ wishlists at fest start get meaningful algorithmic surfacing (front-page categories, "Popular Upcoming," "Trending Free"). Demos below 1,000–2,000 wishlists at fest start typically get minimal surfacing and convert poorly. ESTIMATED, FLOOR.

**Mechanism.** Steam's discovery algorithm uses pre-existing momentum (wishlist count, follower count, demo install velocity in the 24 hours before fest opens) as inputs to which demos appear in "Popular" and category-front surfaces during the fest. Cold demos (no pre-existing wishlists) start invisible and stay invisible. REPORTED at the mechanism level — Valve has confirmed momentum-based surfacing in dev FAQ; specific threshold numbers are ESTIMATED.

**Implication.** Going into Next Fest with 0–500 wishlists is functionally entering invisible. The fest will produce a small wishlist bump from direct-link traffic (Twitter, Reddit, Discord posts by the dev) but will not produce the multiplicative algorithmic lift that justifies treating Next Fest as a major marketing event. ESTIMATED.

**Pre-fest velocity target for a niche-strategy title.** ESTIMATED floor of 3,000–5,000 wishlists at fest start to clear the visibility floor. 7,000–10,000+ to comfortably participate in algorithmic surfacing. 15,000+ to be a "featured" candidate for Valve curation. Cross-ref T-W2 velocity targets for time-to-wishlists shape. STALE on the upper bound — Valve curation criteria shift cohort-to-cohort.

## Post-fest decay rate

What happens to wishlist-add rate in the weeks after Next Fest closes.

**Week +1 (first week post-fest).** Wishlist-add rate typically falls to 20–35% of fest-week rate. Long-tail discovery from people who saw the demo, did not install, but wishlisted. REPORTED, training-data floor.

**Week +2.** Falls to 10–20% of fest-week rate. Steam Curators publish reviews, YouTube/Twitch pickup from streamers who downloaded the demo during fest finally airs. ESTIMATED.

**Week +4 (one month post-fest).** Falls to 5–12% of fest-week rate. Title returns to its pre-fest baseline plus a modest elevated floor from increased capsule-page traffic from people who remember seeing it. ESTIMATED.

**Weeks +8 through launch.** Title operates at an elevated baseline (1.5–3× pre-fest rate) if the page was updated with post-fest improvements (capsule, trailer, tag refinement based on demo feedback). ESTIMATED.

**Net effect.** Total post-fest wishlist gain over the four weeks after the fest is typically 30–60% of the wishlist gain during the fest week itself. The fest is not "a week of wishlists then back to zero" — it sets a new floor. ESTIMATED.

**Risk: decay-to-zero pattern.** Titles that fail to improve the page after the fest (no capsule update, no trailer refresh, no community engagement) decay rapidly back to pre-fest baseline within 2–3 weeks. The fest is wasted as a one-time spike rather than a momentum builder. REPORTED across multiple indie post-mortems.

## Optimal gap-to-launch

Time between Next Fest week-end and Day-1 launch. Wishlist conversion (% of wishlists that purchase in launch week) is sensitive to this gap.

**1 month gap.** Wishlist freshness is high — Next Fest wishlisters are still primed. Risk: not enough time to incorporate demo feedback into final build, fix demo-discovered bugs, refresh capsule, secure influencer launch coverage. Cited conversion uplift: high — but high variance because rushed launches drag review scores. ESTIMATED.

**3 month gap.** Most-cited optimal by Zukowski and GameDiscoverCo for indie titles. Long enough to incorporate feedback and run a second marketing beat (trailer refresh, capsule A/B); short enough that wishlisters remember the title. Wishlist conversion typically 18–25% at launch week for titles in this gap. REPORTED, ESTIMATED on the precise band.

**6 month gap.** Wishlist conversion drops 10–18%. Wishlists "age" — buyers no longer remember why they wishlisted, do not respond to launch-day notification at the same rate. Recoverable with a major pre-launch beat (final trailer, influencer push, capsule refresh). ESTIMATED.

**12+ month gap.** Conversion drops to 6–12%. Wishlists are essentially expired — many will be removed on Steam's automatic wishlist-cleanup prompts. Practically requires a second Next Fest (forbidden — see below) or a separately-positioned marketing relaunch. ESTIMATED.

**Synthesis.** ESTIMATED sweet-spot is 8–16 weeks post-fest. Falls outside this band and conversion either degrades to expired-wishlist levels or rushes the build quality. Cross-ref T-F1 launch window for seasonality overlay.

## Once-per-game rule

Valve's published rule: each game may participate in Next Fest exactly once, must participate before launch, and must offer a playable demo during the fest. REPORTED, Steamworks developer FAQ.

**Enforcement.** Valve enforces via Steamworks app-ID tracking. A game that has launched cannot enter Next Fest. A game that has previously participated as a demo cannot enter again. REPORTED.

**Workarounds and gray areas:**

- **DLC / expansion as separate product.** If sold as a standalone (own app-ID), the DLC can participate in its own Next Fest. Common pattern for content-rich indie sequels and major expansions. REPORTED.
- **Sequel.** A new app-ID for a sequel is fully eligible. REPORTED.
- **Early Access launch.** Counts as launch. Entering Next Fest before Early Access is the one-shot. Entering after Early Access launch is not permitted. REPORTED.
- **Demo before Next Fest.** A game may have a public demo on Steam before its Next Fest participation. The Next Fest demo itself is the one-shot for fest participation, but having an earlier demo does not consume the Next Fest eligibility. REPORTED.
- **Withdraw and re-enter.** Once a game has been listed in a Next Fest cohort, withdrawing and re-entering a later cohort is not permitted per Valve's stated rules. REPORTED — anecdotal Reddit reports of dev-requested moves between cohorts when builds are not ready; case-by-case.

**Implication for Ouroboros.** Next Fest is a one-shot event. Wrong cohort = lost forever for this app-ID. This raises the importance of cohort selection above what raw delta numbers would suggest.

## Premature-fest cautionary cases

Pattern: titles that entered Next Fest before demo content was ready, suffered a public reputation hit that persisted through launch.

**Cautionary mechanisms (from indie post-mortems, REPORTED at the pattern level, anonymized at the title level where post-mortems requested it):**

1. **Crash-on-launch demos.** Demo crashed on first launch for 20–40% of installers. Negative-affect impressions baked in before the player saw a frame of gameplay. Steam discussion forums flooded with negative posts during fest. Demos cannot be hot-patched fast enough during a 7-day fest to recover. Title launched 6 months later to soft sales and lingering "broken on launch" reputation in YouTube search results.

2. **Tutorial-only demos with no core-loop reveal.** Demo showed tutorial sequence for 30–45 minutes with no glimpse of the actual gameplay loop. Wishlist conversion was 3–5× lower than comparable demos that put core loop in the first 10 minutes. Players reported in reviews "I played the demo and could not tell what this game even is."

3. **Demos that promised polish the final build did not deliver.** Demo had hand-polished tutorial scene with bespoke art; rest of game shipped with placeholder art the demo had hidden. Review bombing at launch citing "false advertising." Even if technically the demo content was final, perception drove the review backlash.

4. **Pre-Early-Access demos with no "this is Early Access" framing.** Players assumed the demo represented launch quality. Final Early Access release felt thinner than the demo, generated "feels like a downgrade" reviews.

5. **Demos that revealed unfinished systems.** Multiplayer-promised game shipped Next Fest demo with single-player only; community concluded multiplayer was vaporware; pre-launch wishlist remove rate spiked.

6. **Empty Steam page during fest.** Demo went live but the store page itself had stub screenshots, placeholder trailer, no tags refined. Page-quality multiplier on the fest gain was 0.3×–0.5× a polished page. Wasted the one-shot eligibility.

**General lesson across the cases.** Next Fest is not a soft launch — it is the largest single pre-launch first-impression event. Entering with anything other than a representative, stable, polished build that demonstrates the core loop is a reputation-leveraged gamble. Better to skip a cohort than to enter prematurely. REPORTED — consensus across Zukowski, GameDiscoverCo, and Aggro Crab post-mortems.

## Cross-cutting findings

- October cohort ESTIMATED-best for niche-strategy with hard-SF theming on the per-wishlist-converted basis; June is highest raw traffic but worst per-impression conversion due to AAA noise; February is the discoverability-friendly low-noise quiet cohort with smaller absolute traffic.
- Pre-fest wishlist floor for meaningful algorithmic surfacing is 3,000–5,000 minimum, 7,000–10,000 comfortable, 15,000+ for curated featuring. Going in cold (< 1,000 wishlists) wastes the one-shot.
- Demo retention 30-minute milestone is the wishlist-conversion threshold — design the demo to make the "I get it" moment hit by minute 10 and the replay hook by minute 30.
- Post-fest decay is real but the new baseline is 1.5–3× pre-fest if the page is refreshed post-fest; titles that "set and forget" decay to zero in 2–3 weeks and waste the spike.
- Optimal gap to launch is 8–16 weeks (~ 2 to 4 months). 1 month is too tight for build polish; 6+ months is too long for wishlist freshness.
- Once-per-game rule makes cohort selection a high-stakes one-shot — wrong cohort cannot be re-entered.

## Ouroboros Next Fest cohort options

Surfaces three cohort options against the current Pre-Zip Beta Readiness Gate and 80–200k first-month wishlist target. Does not pick.

**Option A: October 2027.** Pre-holiday wishlist-building window. ESTIMATED-best per-wishlist conversion for niche-strategy. ESTIMATED-most-receptive cohort for generational/legacy strategy with hard-SF theming. Launch window candidates: Q1 2028 (3–5 month gap) — clean alignment with February quiet release window and post-holiday hardware activation; or Q2 2028 (5–7 month gap) — wider polish window but mid-band on wishlist freshness.
- **Pros.** Best ESTIMATED conversion; pre-holiday mindset; clean Q1 2028 launch alignment; gives implementer lane 14–18 months from 2026-05-17 to demo-ready (assuming October 2027 cohort opens mid-October 2027, training-data STALE on exact 2027 date).
- **Cons.** Longest runway from current date means the highest opportunity cost if scope slips; AAA Q4 surrounding noise is high; demo must be stable through the 7-day fest including weekend (Valve does not patch-blocklist fest builds).

**Option B: June 2027.** Highest absolute traffic cohort. AAA-adjacency heavy. ESTIMATED-lower per-impression conversion for niche-strategy.
- **Pros.** Largest raw audience; Summer-Sale tie-in for back-catalog cross-promotion; aligns with Summer-Game-Fest seasonal attention.
- **Cons.** Niche-strategy slot heavily contested; AAA noise floor; June 2027 cohort puts launch in Q3/Q4 2027 (3–6 months gap) which overlaps Q4 AAA peak; ESTIMATED-worst fit for hard-SF theming because AAA scifi noise (Mass Effect, Star Wars, Starfield-adjacent) is highest in June.

**Option C: February 2027.** Quiet-cohort early entry. Tightest from current date (2026-05-17) — would need demo-ready and 3,000–5,000 wishlist floor by early February 2027, approximately 8.5 months out.
- **Pros.** Low AAA noise; post-holiday hardware activation; cleanest discoverability; if demo lands well, launch in Q2 or Q3 2027 (3–5 month gap) hits summer streaming push.
- **Cons.** Tightest timeline; conflicts directly with Pre-Zip Beta Readiness Gate completion timing (gate not yet cleared as of 2026-05-17); requires both demo-ready and pre-fest wishlist accumulation in ~8 months; ESTIMATED-tightest of the three options on whether scope and quality can hit the bar.

**Option D: October 2026.** Not feasible. Less than 5 months from current date. Would require demo-ready and visibility-floor wishlist accumulation in a window that conflicts with Pre-Zip Beta Readiness Gate and current BLOCKER queue. Surfaced only to document non-viability.

**Option E: Later cohorts (February 2028, June 2028, October 2028).** Available if Option A slips. Each pushes launch into 2028 or 2029 and incurs opportunity cost relative to current 80–200k first-month wishlist target timeline.

## Conflict surfaced

The pre-launch pipeline currently captured in `docs/legacy/method_era1/priority_queue.md` and `docs/launch_todo.md` is sequenced as: friends-ZIP → Steam developer account ($100 Steam Direct fee) → Steam page live → 30-day Steam page minimum before launch → launch.

**Conflict.** Next Fest participation requires (a) a playable demo on Steam during the fest and (b) the Steam page to be live well before the fest (Valve recommends 30+ days of Steam page presence before Next Fest for the algorithmic-surfacing momentum to build). The current 30-day-Steam-page rule in `docs/launch_todo.md` is the floor for launch readiness but is below the Next Fest pre-fest accumulation window of 60–120 days that the visibility-floor figures above suggest.

**Implication.** Next Fest requires substantially more lead time than the current pre-launch sequencing assumes. If Next Fest is in scope, the Steam page must go live 3–4 months before the cohort, not 30 days before launch.

**Flag.** This is not a recommendation. Surfacing only. The decision about whether Next Fest is in scope, and which cohort, belongs in Design Lane or Westley's launch-window pick.

## Caveats and confidence

Confidence distribution across this brief: REPORTED tags dominate the structural claims (three cohorts exist, once-per-game rule, U-shape day curve, page-quality dependency). ESTIMATED tags dominate the magnitude claims (specific cohort multipliers, wishlist deltas, decay rates, optimal-gap bands). STALE tags apply to specific date references and Valve curation thresholds.

**Specific caveat: Valve cohort-level data is partial.** Valve has not published official per-cohort wishlist conversion deltas at any point in training-data history. All per-cohort comparative figures are ESTIMATED from indie post-mortems, GameDiscoverCo subscriber-only newsletters (partially summarized in training-data), and Zukowski's blog/YouTube. Floor confidence on per-cohort delta magnitudes.

**Specific caveat: 2026–2027 cohorts.** Training-data has not refreshed against 2025 cohort post-mortems or 2026 cohort scheduling. Valve has historically shifted Next Fest dates by 1–4 weeks cohort-to-cohort. Exact 2026 and 2027 cohort dates should be re-verified via WebFetch when available.

**Specific caveat: indie self-selection bias.** Post-mortems are published by devs who chose to publish them — typically devs with a story to tell (either success or instructive failure). The "median" niche-strategy participant figures are extrapolated from this biased sample. True medians are likely lower than the figures cited.

**Specific caveat: niche-strategy is not a monolith.** Generational/legacy strategy, 4X, grand strategy, tactical squad, survival-strategy, and city-builder are different sub-niches with different cohort preferences. The October-preference framing is a synthesis across these sub-niches and is most confident for generational/legacy and grand strategy specifically.

## Feeds Design Lane

This brief feeds:

- **Ouroboros Next Fest cohort pick** — Option A/B/C surfaced under "Ouroboros Next Fest cohort options" above for Westley's Design Lane decision.
- **T-D1 demo strategy** — demo retention curve, 10-minute "I get it" moment, 30-minute replay-hook threshold, premature-fest cautionary cases for what the demo must and must not be.
- **T-W2 velocity targets** — pre-fest wishlist floor of 3,000–5,000 minimum and 7,000–10,000 comfortable defines the wishlist-accumulation milestone working backward from the chosen cohort.
- **T-F1 launch window** — optimal 8–16 week gap from fest to launch defines the launch-window seasonality calibration alongside other launch-timing inputs.
- **T-F2 festival roster** — Next Fest is the single highest-leverage festival; brief feeds the festival-roster prioritization (Next Fest first; secondary festivals — Steam Strategy Fest, Steam Cityfest, etc. — slot around it).
- **Pre-Zip Beta Readiness Gate** — flagged conflict between current 30-day Steam-page floor and Next Fest's 3–4 month Steam-page-live requirement; gate sequencing may need adjustment if Next Fest is in scope.

## Open questions for further research

- 2025 and 2026 cohort wishlist-delta post-mortems for niche-strategy participants — current figures are training-data floor, several years stale. WebFetch when available to refresh.
- Exact 2026 October, 2027 February, 2027 June, 2027 October cohort scheduling per Valve — needed to lock down implementer-lane timelines against cohort options.
- Per-sub-niche cohort preference quantification — generational/legacy strategy specifically (not pooled with broader strategy/sim) is the Ouroboros primary tribe; targeted post-mortems on generational/legacy demos would tighten the October-preference claim.
- Demo length effect on retention — current evidence is that 30–45 minutes is the sweet spot but cohort-comparative data on 60-minute and 90-minute demos in niche-strategy specifically is thin.
- Demo refresh rule — Valve permits demo updates during the fest; impact of mid-fest patches on retention and wishlist conversion is under-documented.
- Streamer/influencer pickup pipeline during fest week — which cohort's streamer ecosystem is most receptive to niche-strategy specifically; current evidence is pooled across genres.

## Sources

All sources accessed via training-data; WebFetch denied. Treat as floor.

- Valve Steamworks developer FAQ — Steam Next Fest documentation (training-data, last refreshed January 2025; STALE).
- Valve Next Fest official blog posts on Steam community hub announcing cohort results (training-data, partial coverage; REPORTED).
- Chris Zukowski — HowToMarketAGame blog posts on Next Fest cohort strategy, demo retention, and post-fest decay (training-data; REPORTED at the pattern level, ESTIMATED on specific figures).
- Chris Zukowski — HowToMarketAGame YouTube channel, Next Fest retrospective videos (training-data; REPORTED).
- Simon Carless — GameDiscoverCo Plus newsletter, cohort-comparative wishlist conversion analyses (training-data, subscriber-only content partially summarized in public posts; ESTIMATED).
- Cliffski / Positech Games — post-fest retrospectives on Production Line and Democracy 4 (training-data; REPORTED).
- Tomas Sala — Falconeer / Bulwark post-fest blogs (training-data; REPORTED).
- Aggro Crab — Another Crab's Treasure post-mortem (training-data; REPORTED).
- Reddit r/gamedev — collected indie Next Fest post-mortems (training-data, self-selection biased; REPORTED at the pattern level).
- Steamworks developer documentation — once-per-game rule and demo requirements (training-data, last refreshed January 2025; REPORTED).

Originating context: Ouroboros Research Lane Wave 5, T-D2 — Steam Next Fest timing capture for Pre-Zip launch planning. Cross-referenced briefs to be authored or extended: T-D1 demo strategy, T-W2 velocity targets, T-F1 launch window, T-F2 festival roster, T-S3 Steam algorithm visibility (`docs/legacy/topics/steam_algorithm_visibility.md`).
