---
name: Paid Ad Channels + ROI
description: Reddit Promoted, Meta, YT ads, Google Search, Steam ads, podcast sponsorships, Twitch ads per-channel CPI / wishlist-CAC + viability + tribe-click patterns for niche-strategy; feeds Ouroboros paid-acquisition decision, T-W2 velocity supplement.
type: topic_brief
captured_at: 2026-05-18
contributor: Research Lane Wave 6 capture
---

# Paid Ad Channels + ROI

## What this brief is

Map paid acquisition channels for niche strategy/sim PC games on Steam. Per-channel CPI (cost-per-install proxied as cost-per-wishlist for pre-launch Steam), wishlist-CAC ranges, viability for the Ouroboros audience profile (primary tribe 30-42, generational/legacy + Foundation/literary hard-SF, ad-blind on Meta surfaces, reddit-native, creator-channel-tolerant), and where the tribe clicks vs scrolls past.

Brief is non-recommending. Surfaces options, attaches confidence tags inline, never picks. Paid spend is publisher-side knowledge with heavy variance by creative, audience-match, and seasonality — ESTIMATED floor applies aggressively here. Decisions belong to Design Lane (paid-spend allocation fork) and to Westley.

Bible context: Ouroboros targets 80,000-200,000 lifetime units (lieutenant_pivot_niche_brief.md ranked primary niche). Primary tribe demographic skews 30-42 (T-A3 brief), reddit-native, ad-blind on display formats, creator-channel-trusting. Paid acquisition in niche-strategy historically functions as a velocity supplement to organic Steam algorithm + creator coverage + community presence — not the primary funnel. The dev post-mortems cited under Method consistently report organic-Steam + creator-coverage as the dominant wishlist source, with paid contributing single-digit-percent of total wishlists on launches in this niche tier.

## Method

The brief synthesizes training-data sources, primarily:

- GameDiscoverCo (Simon Carless) paid-channel posts and the GameDiscoverCo Plus subscriber newsletter, which periodically aggregates publisher-side paid-acquisition disclosures.
- Chris Zukowski (HowToMarketAGame) ads case studies and the public archive at howtomarketagame.com covering Reddit promoted-post case studies, Meta tests, and YouTube influencer-vs-ads comparisons.
- Dev post-mortem ad-spend disclosures on r/gamedev, r/IndieDev, GDC talks, and individual developer blogs — most notably the post-mortems by Concerned Ape (Stardew Valley, who famously did not run paid), Acram Digital, Hooded Horse public statements, Slitherine paid-channel comments, and Paradox Interactive's older paid-channel disclosures.
- Hooded Horse case studies and interview content where the publisher has discussed launch marketing surfaces (Falling Frontier wishlist push, Old World launch, Manor Lords pre-launch playbook — Manor Lords is Slavic Magic + Hooded Horse).
- Slitherine paid-channel commentary in wargame post-mortems (Strategic Mind, Field of Glory, Distant Worlds 2).

WebFetch is denied in this environment. All figures below are training-data floor — drawn from public posts and disclosures in the training corpus, no live verification. Treat every CPI / CAC number as ESTIMATED with a ±50% band around publisher-side disclosed ranges. Treat "X channel works / does not work" as REPORTED — multiple sources agreeing in the training data, but not freshly verified.

Naming conventions: CPI = cost per install (mobile-style metric, not directly applicable to Steam pre-launch but used here for comparability). Wishlist-CAC = cost to acquire one Steam wishlist via the named channel. Wishlist-to-sale conversion at launch in this niche typically 0.15-0.25 (per wishlist_conversion_benchmarks_2026.md); a $5 wishlist-CAC therefore implies a $20-33 effective sale-CAC at launch.

## Reddit Promoted

REPORTED — reddit promoted-post ads are the highest-cited paid channel for niche-strategy/sim Steam launches in dev post-mortems. Reddit's targeting allows subreddit-specific promotion (r/grandstrategy, r/4xgaming, r/CrusaderKings, r/RimWorld, r/asimov, r/printSF, r/gamingsuggestions) which maps tightly to the Ouroboros tribe surfaces enumerated in primary_tribe_psychographic_profile.md and audience_overlap_map.md.

ESTIMATED CPI / wishlist-CAC: $1-3 per wishlist on well-matched subreddit targeting with native-format creative (text post + short video, mimicking organic post style). Wider targeting or banner-style creative pushes the figure to $5-10+ per wishlist. The variance is creative-driven: native-styled reddit ads outperform banner-styled ads by reported 3-5x in case studies.

Strengths the sources cite:

- Audience match. r/grandstrategy (approx 80k subscribers), r/4xgaming (approx 250k), r/CrusaderKings (approx 250k), r/RimWorld (approx 700k), r/asimov (approx 70k), r/printSF (approx 250k) are precisely the tribe surfaces. Promoted posts in these subreddits reach buyers who self-identify as the audience.
- Native-feeling format. Reddit users tolerate promoted posts that look like organic posts more than they tolerate banner-style ads. Authentic gameplay-snippet videos with developer voice outperform polished trailers.
- Direct wishlist click-through. Reddit's link format encourages click-through to Steam pages.
- Comment-section engagement. Promoted posts that get organic comments compound — replies surface the post to non-subscribers, effectively converting paid into hybrid paid-organic reach.

Weaknesses:

- Reddit users are ad-skeptical. Posts visibly promoted with sponsored-tag underperform near-organic developer-account posts (the latter is not paid but is the gold standard r/grandstrategy expects). If the creative doesn't match the subreddit's culture, the post downvotes hard and CPI spikes 5-10x.
- Subreddit moderators sometimes disallow promoted posts entirely. r/RimWorld and r/CrusaderKings have selectively allowed and disallowed promoted gaming content over the years.
- Scale ceiling. The total reachable wishlist pool via reddit promoted in the named subreddits is approximately 5,000-15,000 wishlists per launch window across multiple sustained campaigns, ESTIMATED — not enough to be a primary funnel for an 80-200k unit target, but meaningful as a velocity supplement.

Tribe-click pattern: high click rate on native gameplay-clip posts framed as "I built this because I wanted X" (developer voice, problem statement, brief solution snippet). Low click rate on polished trailers or banner-style creative. The tribe scrolls past anything that looks like a marketing department wrote it.

## Meta (FB/Insta)

REPORTED — Meta is the most-cited paid channel that does NOT work for niche-strategy PC games. Dev post-mortems in this niche consistently report Meta CAC at $20+ per wishlist on PC strategy/sim titles, often $30-50 for hard-SF or grand-strategy targeting. The same post-mortems usually conclude Meta spend was cut after the first test.

ESTIMATED CAC: $20-50 per wishlist on lookalike audience targeting + interest-based targeting (4X games, grand strategy, Crusader Kings, Stellaris). Cost-per-click is competitive ($0.50-1.50) but conversion to wishlist is poor.

Why Meta underperforms for this audience:

- Demographic mismatch. The Ouroboros primary tribe is 30-42, reddit-native. Meta's PC-gaming-engaged audience skews mobile-game-focused and younger or older; the strategy-PC-gamer 30-42 cohort is not concentrated on Meta surfaces.
- Ad-blindness. The 30-42 reddit-native tribe explicitly scrolls past Meta ads. T-A3 psychographic profile (primary_tribe_psychographic_profile.md) flags this directly — the tribe self-identifies as ad-resistant on Meta surfaces.
- Creative format mismatch. Meta favors vertical short-form video, which is a poor fit for strategy/sim gameplay where the appeal is map state, simulation depth, or long-time-horizon storytelling — none of which compress to 9:16 well.
- Conversion tracking weakness post-iOS 14.5. Attribution from Meta click to Steam wishlist is degraded; publishers report cannot reliably measure CAC, which depresses spend confidence.

Edge cases where Meta has been reported to work in niche-strategy:

- Casual-strategy crossover titles (Stardew-adjacent, cozy-management) where the audience overlaps with mobile-game-engaged demographics.
- Re-targeting wishlisters at launch with a launch-discount-aware creative — this is a small spend pocket that some publishers report positive ROI on.

Tribe-click pattern: scroll past. The Ouroboros tribe does not click on Meta gaming ads. Confidence: REPORTED, widely consistent across sources.

## YouTube ads (TrueView / in-stream)

REPORTED — YouTube ads have moderate viability for niche-strategy, with strong variance by targeting precision. The key lever is whether the campaign targets specific strategy-channel viewerships (SsethTzeentach, Quill18, Many a True Nerd, Pravus, ItsRose, Generalkidd, etc.) versus broad "gaming interest" targeting.

ESTIMATED CAC: $8-20 per wishlist on tight strategy-channel-viewership targeting with skippable in-stream pre-roll creative. Broad targeting pushes CAC to $30+. Bumper ads (6-second non-skippable) underperform for strategy where the pitch requires more than 6 seconds.

Strengths:

- Pre-roll on strategy channels reaches the tribe with attention. A SsethTzeentach viewer queuing up a 45-minute Crusader Kings deep-dive is in strategy-mode and will tolerate a 30-second strategy game ad.
- TrueView's skip mechanic acts as a filter — viewers who don't skip self-identify as interested.
- Trailer assets re-use directly; YouTube ads can run the same trailer assets developed for the Steam page, lowering creative-production cost.

Weaknesses:

- Targeting precision via YouTube's audience tools is coarser than reddit's subreddit targeting. "Strategy game enthusiast" is broader than "r/grandstrategy subscriber."
- Influencer coverage (organic or paid sponsorship within the creator's content) historically outperforms TrueView ads on the same channel — the audience trusts the creator more than the brand. This pushes spend toward sponsorship/integration rather than pre-roll.
- Skippable ads have a built-in 5-second skip. Strategy game pitches that need to establish mechanics in those first 5 seconds underperform aesthetic-pitch trailers.

Tribe-click pattern: pre-roll on strategy-creator content is tolerated and clicked at moderate rates. Display ads in the YouTube right rail are scrolled past. Bumper ads are universally ignored.

Confidence: ESTIMATED on CAC; REPORTED on the influencer-integration-outperforms-pre-roll pattern.

## Google Search

REPORTED — Google Search ads split into two patterns for niche-strategy.

Branded terms (the game's own name + adjacent variations): high-ROI defensive spend. Reported CAC for branded keywords typically $0.50-2 per click with strong conversion-to-wishlist (15-30% click-to-wishlist). Used primarily to prevent competitor or scam-site bids from outranking the publisher's own Steam page in search results. Spend ceiling is small ($50-500/month for niche-strategy titles) but ROI is positive.

Competitor terms (bidding on "crusader kings 3", "stellaris", "rimworld", "wildermyth"): moderate-ROI but contested. Reported CAC $5-15 per wishlist when the creative explicitly positions the title as "for fans of X who want Y" rather than "X but better." Direct comparison creative ("better than Stellaris") underperforms — the searching user already loves Stellaris.

Adjacent intent terms ("grand strategy game", "4X game", "civilization-like"): typically lower ROI than competitor terms because intent is weaker and the cohort is broader.

Strengths:

- Intent-driven traffic. Users searching for specific strategy game names or genre terms are in active-discovery mode.
- Conversion paths are short — search click → Steam page → wishlist.

Weaknesses:

- Total search volume in niche-strategy is small. Even saturating branded + competitor terms caps spend at a few thousand dollars per month.
- Quality-score penalties on competitor-term bidding can inflate CPC.

Tribe-click pattern: high click rate on text ads that read like organic Steam results (game name, genre tagline, mention of release date or demo availability). Low click rate on aggressive promotional creative.

Confidence: REPORTED on branded-ROI; ESTIMATED on competitor-term CAC.

## Steam ads

ESTIMATED — Steam itself does not run a self-serve paid-acquisition product exposed to indie developers in the way Meta or Google do. The "Steam ads" surfaces that exist are:

- Discovery Queue placement, which is algorithm-driven, not paid.
- Front-page banners and featured slots, which are curated by Valve and not directly purchasable.
- Sale event participation (Steam Next Fest, seasonal sales, themed sales) which is free but requires Valve curation acceptance.
- Capsule-art testing, free to all developers via Steam Labs.
- Daily Deal / Weeklong Deal slots, which are negotiated between Valve and publishers with no transparent price.

Some larger publishers report negotiated front-page banner placements as part of broader Valve relationships — these are not exposed to small/indie developers as a self-serve product. Hooded Horse and Paradox-tier publishers operate in this band; solo or sub-10-dev teams typically do not.

What is available to indies:

- Visibility Round bonuses tied to wishlists at launch (the Steam algorithm grants visibility-round impressions based on wishlist depth and conversion velocity).
- Sale event opt-in placements during themed sales (strategy fest, simulation fest, etc.) where the placement is editorial, not paid.

Implication: there is no meaningful "buy Steam ads" lever for Ouroboros. The Steam-side levers are algorithmic (wishlist velocity, tag matching, capsule conversion) and editorial (Next Fest acceptance, themed-sale curation). The Steam-related work in T-W2 (wishlist velocity supplement) is therefore mostly about feeding the algorithm through other channels, not buying Steam-side ads directly.

Confidence: REPORTED on the absence of self-serve indie paid surfaces; ESTIMATED on negotiated-banner-tier availability.

## Podcast sponsorships

REPORTED — podcast sponsorships are a small but high-affinity channel for niche-strategy and hard-SF audiences. The Ouroboros tribe overlap with podcast listening is high based on T-A3 psychographics (audiobook-leaning, long-form-content-tolerant, commute/walk listening common in the 30-42 cohort).

Relevant podcast surfaces:

- Strategy/gaming podcasts: Three Moves Ahead (sadly defunct but historical reference), The Wargamer Podcast, Bombcast (broader but strategy-friendly), GameSpot After Dark, The Sausage Factory.
- SF / literary podcasts: Coode Street Podcast, Our Opinions Are Correct, Imaginary Worlds, The Drift Hour, Hugos There, Beyond the Sea (Foundation-adjacent listenership).
- Adjacent culture podcasts: Hardcore History (strategy/historical audience overlap), Tides of History, Fall of Civilizations.

ESTIMATED costs: niche podcasts in the 5,000-50,000 download-per-episode range typically charge $20-50 CPM (cost per thousand listens) for host-read pre-roll/mid-roll spots. A 30,000-listener podcast at $30 CPM = $900 per episode. Larger podcasts (Hardcore History tier, 1M+ listens) charge $40-80 CPM and are typically out of indie-budget range unless episodic micro-buys at network rates are negotiable.

Wishlist-CAC is hard to attribute on podcasts; tracking requires custom URLs or promo codes. Reported (publisher-side, scattered) wishlist-CAC on host-read spots in well-matched podcasts: $5-20 per wishlist, with extreme variance.

Strengths:

- Host-read trust. The host's endorsement carries weight the brand cannot replicate. In the SF / literary cluster, a Foundation-themed podcast host endorsing Ouroboros as "the closest game I've seen to the feeling of reading Foundation" is the kind of signal the tribe actively responds to.
- Long-form attention. Podcast listeners are in 30-60 minute attention mode; a 60-second host-read can fully establish a strategy game's pitch.
- Cumulative reach. Podcast episodes have long tails; sponsorships continue accruing impressions over months.

Weaknesses:

- Attribution is murky. Custom URLs help but the lift is hard to measure cleanly.
- Inventory is sparse in the most-aligned podcasts (Foundation-adjacent SF podcasts are few; strategy gaming podcasts in 2026 are thin after Three Moves Ahead).
- Production-quality dependency. A poorly-written host-read undermines the brand more than a missing ad.

Tribe-click pattern: the tribe doesn't "click" on podcast ads — they take a note, hear the URL, and search for the game later. This makes attribution worse but does not mean the channel doesn't work.

Confidence: REPORTED on the channel's existence and general dynamics; ESTIMATED on per-channel CPM and wishlist-CAC.

## Twitch ads

ESTIMATED — Twitch's paid ad surfaces split into platform-level pre-roll/display (Twitch Ads Manager, self-serve) and streamer-direct sponsorships (negotiated with individual streamers).

Platform-level pre-roll on Twitch performs poorly for niche-strategy. CPC is low ($0.10-0.50) but conversion is also low; the audience is in lean-back viewing mode and pre-roll on a streamer's channel is associated with the platform, not the streamer's endorsement. Reported wishlist-CAC: $15-40 per wishlist on broad gaming targeting, ESTIMATED.

Streamer-direct sponsorships are the higher-ROI lever on Twitch. Sponsored streams of the game (where a strategy streamer plays it as a 2-4 hour featured stream) function similarly to YouTube creator integrations and are priced similarly — typically $500-5,000 per streamer for niche-strategy streamers (5k-50k average concurrent viewers). Wishlist-CAC on sponsored streams with well-matched streamers can be competitive ($3-10 per wishlist) but with high creative dependency.

Strategy streamers relevant to the Ouroboros niche:

- Quill18 (multi-platform; YouTube + Twitch crossover)
- Lathrix
- Pravus
- ItsRose
- Generalkidd
- DasTactic
- DasErzimperator (wargame-adjacent)

Strengths:

- Live demonstration. Strategy games benefit from being seen played for hours; a sponsored stream is closer to a live demo than any other paid format.
- VOD long tail. Streamed gameplay becomes YouTube VODs and clips, multiplying reach.

Weaknesses:

- Effectiveness depends on the streamer being a genuine fit. Sponsored streams where the streamer doesn't enjoy the game are visible and counterproductive.
- Twitch ad-blocker prevalence among the 30-42 strategy-PC audience is high; platform pre-roll is frequently never seen.
- Smaller strategy streamers have higher tribe-match but smaller reach; budget tradeoff is sharp.

Tribe-click pattern: the tribe watches strategy streamers actively, especially during launch/discovery windows. Sponsored streams convert. Platform-level pre-roll ads on those streams are universally scrolled past or ad-blocked.

Confidence: ESTIMATED on CAC figures; REPORTED on the streamer-direct-outperforms-platform-pre-roll pattern.

## Where niche tribes click vs scroll

Cross-channel pattern recognition from the surveyed sources:

Click surfaces (the tribe engages):

- Reddit native-styled promoted posts on tribe subreddits with developer-voice creative.
- YouTube pre-roll on strategy-channel creator content with a 5-second hook that establishes "this is for grand-strategy people."
- Google Search results that read like organic Steam links.
- Podcast host-read spots from trusted hosts in adjacent SF / strategy podcasts.
- Sponsored streams from strategy streamers the tribe already follows.
- Creator integrations / dedicated coverage (not technically paid in the same sense, but the channel where the tribe converts hardest — covered separately in creator-coverage briefs).

Scroll-past surfaces (the tribe ignores):

- Meta (Facebook/Instagram) ads in any format.
- YouTube display ads in the right rail.
- Twitch platform pre-roll on non-sponsored streams.
- Banner-style reddit promoted posts that look like marketing.
- TikTok ads (not surveyed in detail; tribe presence on TikTok is low for 30-42 strategy-PC demographic per psychographic profile, but training-data signal suggests TikTok works for cozy/casual-strategy crossovers and not for grand-strategy or hard-SF).
- Generic gaming-news-site display banners.

Underlying mechanism the sources keep returning to: the 30-42 strategy-PC tribe trusts other humans (creators, hosts, fellow redditors) and distrusts brands. Paid formats that route through a trusted human (host-read podcast, sponsored streamer playing the game, native-styled subreddit post with developer voice) function. Paid formats that route directly from brand to user (display banner, platform pre-roll, lookalike-audience Meta ad) get scrolled past.

This is the load-bearing pattern for any Ouroboros paid-acquisition decision.

## Cross-cutting findings

- Paid acquisition in niche-strategy historically supplies single-digit-percent of total wishlists at launch — the channel is a velocity supplement, not a primary funnel. Organic Steam algorithm + creator coverage + community presence drive the bulk. (REPORTED across multiple dev post-mortems.)
- The wishlist-CAC band that delineates "viable" from "non-viable" in this niche sits around $5-10 per wishlist. Below $5, the channel is buying velocity efficiently. Above $15, the channel is bleeding budget. (ESTIMATED, source-aligned.)
- Channel ROI tracks creative-fit-to-channel more than raw audience size. Reddit native posts > YouTube pre-roll > Meta lookalike for this tribe, but the gap closes if Meta creative is unusually well-matched and reddit creative is generic.
- Attribution is consistently the weakest link. Wishlist-CAC numbers across all channels carry ±50% uncertainty even when publishers disclose figures, because Steam's attribution surface is weak post-cookie-deprecation.
- Spend concentration > spend dispersion. Post-mortems repeatedly report better outcomes from concentrating $X on one well-matched channel (typically reddit or strategy-creator integrations) than from spreading $X across five channels.
- Launch-week paid push outperforms pre-launch paid push in this niche. Wishlist-conversion benefits from a paid-driven launch-day spike that amplifies the Steam algorithm's visibility-round response. (REPORTED, GameDiscoverCo + dev post-mortems agree.)

## Ouroboros paid-acquisition options

Surface 3-5 spend allocations. Research Lane does not pick.

**Option A — Reddit-only, native-format, concentrated launch-window spend.** Allocate full paid budget to reddit promoted posts on r/grandstrategy, r/4xgaming, r/CrusaderKings, r/RimWorld, r/asimov, r/printSF during the launch week and the two weeks prior. Creative: developer-voice posts with gameplay clips, no banner styling. Expected wishlist contribution: ESTIMATED 3,000-8,000 wishlists at $1-3 CAC, depending on budget. Strength: highest tribe-match. Weakness: subreddit-mod-discretion risk, scale ceiling.

**Option B — Creator integrations primary + reddit secondary.** Allocate 60-70% of paid budget to negotiated sponsored streams and YouTube integrations with strategy creators (Quill18, SsethTzeentach if accessible, Lathrix, ItsRose, DasTactic), 30-40% to reddit promoted as velocity backstop. Expected wishlist contribution: harder to ESTIMATE — creator integrations have higher variance but higher ceiling. A single SsethTzeentach video covering the game (if organically picked up or paid-integrated) can drive 20,000+ wishlists; failures drive near-zero. Strength: tribe-trust channel. Weakness: creator-fit dependency, attribution fog.

**Option C — Podcast sponsorships + Google Search defensive only.** Allocate budget to host-read sponsorships in 3-5 well-matched podcasts (SF-adjacent + strategy-adjacent) and to branded Google Search defensive bidding. Skip Reddit and creator-direct entirely. Expected wishlist contribution: small in absolute terms (ESTIMATED 1,000-4,000 wishlists) but high-quality. Strength: long-tail accrual, tribe-trust via host endorsement. Weakness: small scale, attribution opaque.

**Option D — No paid spend, organic + earned only.** Zero paid budget. Concentrate effort on Steam page polish, capsule A/B testing, Steam Next Fest participation, organic creator outreach (free review codes + press kit), community presence on tribe subreddits via developer accounts (not promoted), and demo-driven wishlist conversion. Several of the success-pattern titles in lieutenant_pivot_niche_brief.md (RimWorld, Songs of Syx, Dwarf Fortress) achieved their results with effectively zero paid spend; this option is a viable shape. Strength: zero cash risk, forces dependence on the channels that actually drive niche-strategy success. Weakness: zero velocity supplement, no launch-day paid amplification of the algorithm.

**Option E — Mixed portfolio with hard cutoff rules.** Allocate budget across reddit + creator integrations + branded Google Search, with hard wishlist-CAC cutoffs (e.g., kill any campaign exceeding $10 wishlist-CAC at 2-week measurement). Expected wishlist contribution: moderate, depending on which channels survive the cutoff filter. Strength: lets data pick winners. Weakness: requires attribution discipline that is hard to achieve on Steam-side surfaces; the cutoff rule may kill campaigns prematurely before creative iteration converges.

Research Lane does not pick. Westley + Design Lane decide.

## Conflict surfaced

No direct conflict with the bible. The bible's marketing-direction directives (RTS-framing-kill in `docs/bible/game_bible.md ## In Flux`, Lieutenant System pivot's audience-pinning to generational/legacy + Foundation tribes) are compatible with all five surfaced options above. The brief does not introduce new audience-pinning claims; it inherits tribe definitions from lieutenant_pivot_niche_brief.md, primary_tribe_psychographic_profile.md, and audience_overlap_map.md.

Minor framing tension worth noting: the bible characterizes paid acquisition implicitly as supplementary to organic + earned channels (consistent with the cross-cutting finding that paid is single-digit-percent of wishlists in this niche). If a future Design Lane decision allocates paid-primary spend rather than paid-supplemental, that would be a new framing the bible currently does not codify; flag for Design Lane attention if Option B or E moves toward primary-channel status.

## Caveats and confidence

Confidence tag distribution across this brief:

- REPORTED (multiple training-data sources align, no live verification): channel viability patterns, tribe-click-vs-scroll patterns, attribution-weakness pattern, paid-as-velocity-supplement framing, the "trusted human" mechanism.
- ESTIMATED (training-data figures with publisher-side variance, treat as ±50%): all CPI / wishlist-CAC numbers, all per-channel CPM figures, all spend ranges per option.
- INFERRED (not directly stated in sources, derived by Research Lane from adjacent signals): the Option A through E framings above, the cross-channel ROI ranking, the suggested cutoff-rule heuristics in Option E.

Ad ROI is publisher-side knowledge with structural opacity. Publishers who disclose figures select for confirmation bias (success disclosed, failure quiet). Attribution post-cookie-deprecation is weak. Steam's wishlist attribution is non-deterministic. Treat the ESTIMATED floor heavily; treat the REPORTED patterns as the safer half of the brief.

The brief does not surface 2026-specific live data — WebFetch denied, training-data corpus only. If a Design Lane decision moves toward live paid spend, a live-data pull (GameDiscoverCo Plus subscription, fresh Hooded Horse / Slitherine commentary, recent dev post-mortems within 6 months of the launch window) is the next step.

## Feeds Design Lane

This brief feeds the following live Design Lane forks and adjacent research consumers:

- **Ouroboros paid-acquisition decision** — primary consumer. Westley + Design Lane select among Options A-E (or a hybrid) once a paid-spend ceiling is set. Recommend Design Lane scope this fork after T-W2 (wishlist velocity targets) lands, so the paid-supplement contribution can be sized against the organic + earned baseline.
- **T-W2 velocity supplement** — paid spend, if any, is the velocity amplifier on top of the organic wishlist velocity targets in `docs/research/topics/wishlist_velocity_targets.md`. The cross-cutting finding on launch-week paid push is the direct linkage.
- **T-C1 organic Steam algorithm** — paid spend interacts with the algorithm by amplifying launch-week wishlist conversion velocity. Allocation decisions affect algorithm response.
- **T-C2 creator coverage** — Option B and E intersect directly with creator-coverage strategy. Paid creator integrations vs organic creator outreach is the same audience surface bought two different ways.
- **T-C5 community presence** — reddit native posts (Option A and E) require developer-account community presence as the credibility substrate. Promoting from a cold developer account underperforms promoting from an account with organic comment history on the tribe subreddits.

## Open questions for further research

- Live 2026 paid-channel disclosures from publishers in the named tier (Hooded Horse, Slitherine, smaller indie successes like Mechabellum's publisher-side spend, recent Songs of Syx / Workers & Resources / Field of Glory: Empires post-mortems). Training-data floor only on the figures above.
- Per-podcast CPM and host-read pricing for the specific named SF / strategy podcasts. Confirmed inventory availability for Coode Street, Imaginary Worlds, Tides of History, Hardcore History, Bombcast, The Wargamer Podcast.
- Steam-side wishlist attribution improvements (if any) in 2026 — has the Steam Partner backend exposed any new attribution surfaces that make paid-channel measurement cleaner?
- Reddit promoted-post creative templates that survive subreddit-mod review in 2026. Which subreddits have currently permissive policies versus restrictive policies for game-launch promotion?
- TikTok ad effectiveness for niche-strategy in 2026 — not surveyed in detail above. Training-data signal weak; live check recommended if Design Lane wants to consider TikTok exposure.
- Wishlist-CAC benchmarks specifically for hard-SF / Foundation-tribe targeting versus generic grand-strategy targeting. The current brief blends them; the two cohorts may have meaningfully different CAC profiles.
- Influencer-integration pricing in 2026 for the named strategy creators (Quill18, SsethTzeentach, Lathrix, ItsRose, DasTactic). Sponsored-content rates have moved post-2023 and the training-data figures may be stale.
- Hooded-Horse / Slitherine paid-acquisition playbook specifics — both publishers operate in this niche and have likely refined paid-channel playbooks that are not fully public.

## Sources

Training-data corpus only. WebFetch denied in this environment. All sources cited below are training-data references, not freshly fetched.

- GameDiscoverCo (Simon Carless) — paid-channel coverage in the GameDiscoverCo Plus newsletter and public posts at gamediscover.co. Sample posts on reddit promoted ROI, creator-integration pricing, and post-cookie attribution.
- Chris Zukowski / HowToMarketAGame — ads case studies at howtomarketagame.com covering reddit promoted experiments, Meta tests for indie games, YouTube influencer-vs-ads comparisons.
- Dev post-mortems on r/gamedev, r/IndieDev, and individual developer blogs. Specific post-mortems referenced (training data): Concerned Ape on Stardew Valley marketing (no paid spend), Acram Digital on Strategic Mind paid spend, various Hooded Horse / Slitherine public statements.
- Hooded Horse public commentary on launch marketing — interviews, podcast appearances, post-launch threads on r/games.
- Slitherine paid-channel commentary in wargame post-mortems (Strategic Mind series, Field of Glory series, Distant Worlds 2).
- Paradox Interactive's older paid-channel disclosures around Crusader Kings 3 and Stellaris launch periods.
- Adjacent strategy-streamer rate cards and sponsorship pricing as publicly disclosed by some creators (most rates are private; figures cited are ESTIMATED from anecdotal public mentions).
- Podcast advertising rate references — generic CPM bands from the podcast-advertising industry rather than per-show disclosures, applied to the named SF / strategy podcasts as ESTIMATED.

Training-data flag: all of the above are corpus references with no live 2026 verification. ESTIMATED figures should be treated as ±50% and REPORTED patterns as the safer half. Live-data pull recommended before any spend decision exceeding a small experimental tier.
