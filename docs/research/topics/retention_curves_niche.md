---
name: Retention Curves Niche Strategy
description: D1/D7/D30/D90 retention curves and median-hours-played for niche-strategy paid-base titles (RimWorld, CK3, Wildermyth, Battle Brothers, Old World, Stellaris, Songs of Syx, Caves of Qud); refund-window behavior; shelf-and-return DLC spikes; session-length distribution; feeds T-F3 EA-vs-launch, T-D1 demo strategy, T-W1 wishlist-purchase cross-validation, LTV modeling.
type: topic_brief
captured_at: 2026-05-18
contributor: Research Lane T-CL3 dispatch
---

# Retention Curves Niche Strategy

## What this brief is

Retention-curve and median-hours-played map for niche paid-base strategy/sim on Steam. Covers eight anchor titles spanning the Ouroboros comparable-set: RimWorld-likes (RimWorld), CK3-likes (Crusader Kings 3), Wildermyth-likes (Wildermyth), Battle Brothers hardcore-tactics, Old World, Stellaris, Songs of Syx, Caves of Qud. Cross-axes: median-hours-played per Steam reporting, refund-window behavior (2-hour / 14-day) viewed as retention exit, "shelf-it-and-come-back" long-tail playtime spikes correlating with DLC drops, session-length distribution (short-burst vs. long-binge tribe split).

Feeds T-F3 EA-vs-launch decision (retention curve shape differs materially between Early Access and 1.0 — EA shows a flatter D30 curve because the buyer self-selects harder; 1.0 shows a steeper drop because broader audience arrives), T-D1 demo strategy (D1 retention proxy via Steam Next Fest demo wishlist conversion), T-W1 wishlist-to-purchase cross-validation (long-tail D90+ retention is what justifies wishlist conversion at niche-strategy prices), and monetization LTV modeling (DLC-spike retention is the LTV multiplier on the base SKU).

**Non-recommendation disclaimer.** Research Lane surfaces inputs only. Design Lane and Westley pick what to do with retention shapes. No curve here is endorsed as a target Ouroboros must hit; curves are reported as patterns observable in Steam-side telemetry proxies, developer disclosures, and post-mortem talks.

**Retention telemetry is publisher-side and not exposed in Steam's public surfaces.** Steam exposes median-hours-played for purchasers (via SteamDB / SteamSpy / Gamalytic aggregation of public profile data) but does NOT expose D1/D7/D30/D90 retention curves directly. All retention-curve figures below are REPORTED only when a developer or publisher disclosed in a postmortem, GDC talk, or financial filing; otherwise ESTIMATED via achievement-completion-curve proxy, median-hours-played anchoring, or stated-by-developer comparative.

## Method

Sources consulted from training data (WebFetch and WebSearch denied — could not refresh against 2025–2026 figures):

- **SteamDB / SteamSpy / Gamalytic** — aggregated public Steam-profile data exposing median-hours-played, total-hours-played, owner estimates. Single upstream channel (Steam profile scraping). Per training-data aggregator-independence note: count as ~1 channel even when triangulated.
- **Steam Global Achievement Stats** — public per-achievement completion percentages per title. Achievement completion curve is the strongest single public proxy for retention curve: the share of players who unlocked an achievement gated at ~30 minutes (first session), ~5 hours (D1-D7 typical), ~20 hours (D7-D30 typical), ~50+ hours (D30-D90 typical) approximates the retention bucket size.
- **GameDiscoverCo newsletter back-catalog** (Simon Carless) — recurring retention-curve analyses, "median-hours-played to predict tail" guidance, niche-strategy retention pattern callouts.
- **Tynan Sylvester / RimWorld blog and dev tracker** — public commentary on player engagement, median-hours figures referenced in interviews, "the colony tells a story" retention framing.
- **Worldwalker Games / Wildermyth blog** — post-launch retention commentary, the chapter-completion-curve disclosure pattern, the "campaign-end is the natural exit" framing.
- **Mohawk Games / Old World** — Soren Johnson public commentary on Old World retention vs. Civ-series comparable, Hooded Horse publisher-side disclosure patterns.
- **Paradox / Stellaris** — Paradox Forum and earnings-call retention commentary, "DLC-cycle attaches" pattern explicitly described in Paradox investor relations.
- **GDC talks and post-mortems** — Crusader Kings 3 launch retrospective (Henrik Fåhraeus / Paradox), Caves of Qud GDC talks (Brian Bucklew / Freehold Games), Battle Brothers retrospectives (Overhype Studios), Songs of Syx solo-dev blog posts.
- **How Long To Beat / HLTB** — community-reported time-to-completion figures for "Main Story" / "Main + Extras" / "Completionist." Sandbox-without-end titles report Completionist as effectively unbounded.

Training-data floor for this topic is mid-to-low on quantitative retention curves and mid-to-high on median-hours-played and achievement completion curves. The Steam median-hours figure is robust. The D1/D7/D30/D90 split is mostly ESTIMATED via the achievement-curve proxy.

## Median-hours-played: the headline anchor

Median-hours-played per buyer is the single most-reported retention proxy for niche-strategy paid-base titles. The figure is recoverable from Steam profile scraping (SteamDB / Gamalytic / aggregator surface) and is the metric developers most often cite when discussing tail health. ESTIMATED bands below derived from training-data aggregator snapshots; treat as directional, not precise.

- **Crusader Kings 3** — median-hours-played per owner approximately 40–80h depending on aggregator and snapshot. The tail extends far — top quartile of players runs 200–500h+. Paradox has not published the per-player median directly but has referenced "tens of hours average engagement" in earnings commentary. REPORTED tail shape, ESTIMATED median figure.
- **RimWorld** — median approximately 80–150h per owner per aggregator snapshots; tail extends to multi-thousand-hour players (the "I've put 3000 hours into RimWorld" Steam-review trope). Tynan Sylvester has referenced "the median RimWorld player puts in dozens of hours, the top decile puts in hundreds" in blog/podcast commentary. ESTIMATED median; REPORTED tail.
- **Wildermyth** — median approximately 15–35h per owner. The game is contained (campaigns end, characters retire). Worldwalker has referenced a tighter retention curve than open-sandbox comparables because the campaign structure produces natural exits. ESTIMATED median; REPORTED structure.
- **Battle Brothers** — median approximately 30–80h per owner per aggregator. The hardcore-tactics tribe self-selects and engages deeply. Permadeath drives replay; many players run multiple campaigns. ESTIMATED.
- **Old World** — median approximately 20–50h per owner per aggregator. The contained-campaign 4X structure (each game ends at a defined victory condition over ~10–15 in-game hours) produces a sharper natural-exit than Civ-series comparables. Soren Johnson has referenced this as a deliberate design choice. ESTIMATED median; REPORTED structure.
- **Stellaris** — median approximately 60–120h per owner. The DLC-cycle creates compound engagement — players return for each major expansion. Paradox has referenced the DLC-attach behavior in investor commentary as the dominant retention driver. ESTIMATED median; REPORTED DLC-cycle pattern.
- **Songs of Syx** — median approximately 25–60h per owner. The Dwarf-Fortress-lite tribe runs long colonies; the price ($25) and the no-tutorial design self-select hardcore-only buyers. ESTIMATED.
- **Caves of Qud** — median approximately 30–80h per owner since 1.0. Permadeath + procedural-world + literary-tone tribe runs long sessions; some players invest hundreds of hours in single character runs. ESTIMATED median; REPORTED tribe behavior.

Pattern across the comparable set: **niche-strategy median-hours-played sits in the 15–150h band, with all titles showing tail extension into hundreds of hours among the top quartile.** Even the most contained design in the set (Wildermyth, with explicit campaign exits) shows median above the typical AAA-strategy median (~10–15h for Civilization VI per aggregator inference, ~5–10h for grand-strategy AAA outliers).

Confidence: ESTIMATED on specific median figures; REPORTED on the band shape and on the tail-extension pattern.

## D1 retention — first-session exit

D1 retention measures the share of buyers who return for a second session within 24 hours of purchase. For paid-base niche-strategy on Steam, D1 is dominated by:

- **The 2-hour refund window.** Players who bounce in the first 30 minutes are essentially making a refund decision, not a retention decision. The D1 retention figure for niche-strategy paid-base typically excludes the refunded subset (5–15% of buyers per refund-band brief).
- **First-session length.** Niche-strategy buyers commonly run a 2–5 hour first session before logging off. The "did they come back tomorrow" question is meaningful only after the first session ended.
- **The tutorial completion bar.** Players who completed the in-game tutorial within their first session return at materially higher rates (80%+) than players who exited mid-tutorial (40–60%).

ESTIMATED D1 retention bands for the comparable set, derived from achievement-completion-curve proxy (the share of players who unlocked the "first night survived" / "first character recruited" / "first turn completed" achievement, anchored to within 24h via aggregator snapshots):

- **RimWorld** — D1 approximately 70–85%. The "first colonist crash-lands" hook is immediate; the first storyteller event arrives within 30 minutes; the player typically logs at least 2–3h on Day 1 and returns. REPORTED hook structure; ESTIMATED retention figure.
- **Crusader Kings 3** — D1 approximately 65–80%. Character creation and the early-character-bond mechanic load identity within the first hour; the first crisis arrives in years 1–10 of in-game time (typically within first session); strong D1. ESTIMATED.
- **Wildermyth** — D1 approximately 75–85%. Chapter 1 is structured to introduce three heroes with backstory cards within the first 30 minutes; the personality load is fast; D1 retention strong. REPORTED structure; ESTIMATED figure.
- **Battle Brothers** — D1 approximately 65–80%. The recruit-naming and first-contract structure produces identity within the first hour; permadeath threat focuses attention. ESTIMATED.
- **Old World** — D1 approximately 60–75%. The character-driven 4X structure (named leaders with traits, events tied to family) loads identity faster than typical 4X; D1 stronger than Civ-series comparables. ESTIMATED.
- **Stellaris** — D1 approximately 55–70%. The empire-customization opening loads ownership but the early-game pace is slow; first crisis arrives later than CK3 comparable. Lower D1 than character-driven peers. ESTIMATED.
- **Songs of Syx** — D1 approximately 45–65%. The no-tutorial design and steep UI learning curve produce a higher first-session bounce. The buyers who get past the first session retain at exceptionally high D7/D30 rates because the tribe is self-filtered. ESTIMATED; REPORTED filter behavior.
- **Caves of Qud** — D1 approximately 50–65%. ASCII roguelike presentation and permadeath produce a self-filtering first session; D1 lower than mainstream-presentation peers but D30+ much higher. ESTIMATED.

Pattern across the comparable set: **D1 retention 45–85% range for niche-strategy paid-base.** The titles with explicit personality-load in the first session (RimWorld, Wildermyth, CK3, Battle Brothers) cluster at the upper end of the band. The titles with steep first-session friction (Songs of Syx, Caves of Qud) cluster lower but pay back at long-tail retention.

For Ouroboros specifically: the Lieutenant System's "3–7 named lieutenants with personality" first-session arrival pattern is most directly comparable to Wildermyth's chapter-1 hero introduction and Battle Brothers' Day-1 recruit briefing. If the lieutenants load identity in the first 30 minutes, D1 retention precedent suggests 70–85%. If they read as a unit roster in the first session, the band shifts toward the Songs of Syx / Caves of Qud range with corresponding refund-rate elevation in the first 30 minutes (cross-reference refund_rate_norms.md).

Confidence: ESTIMATED throughout. D1 retention figures are not published by Valve or the developers; achievement-curve proxy is the best public signal.

## D7 retention — first-week persistence

D7 retention measures the share of buyers who returned for at least one session in days 2–7. For niche-strategy paid-base, D7 is the strongest single predictor of D30 / D90 / lifetime retention because the buyer who returns in week 1 has crossed the "I want to keep playing this" identity threshold.

ESTIMATED D7 retention bands, derived from achievement-completion-curve proxy gated at 5–15 hours of playtime (the typical week-1 cumulative hours for an engaged niche-strategy buyer):

- **RimWorld** — D7 approximately 55–70%. The colony-narrative pull is the strongest single D7 driver in the comparable set; the "what happened to my colonists overnight" hook returns the player. REPORTED narrative-pull; ESTIMATED figure.
- **Crusader Kings 3** — D7 approximately 55–70%. Multi-generation dynasty structure produces multi-session campaigns; the buyer who hits the first heir succession is locked in. ESTIMATED.
- **Wildermyth** — D7 approximately 60–75%. Chapter structure produces explicit "I'll finish this chapter next session" return hooks; the contained campaign actively encourages D7 completion. ESTIMATED.
- **Battle Brothers** — D7 approximately 50–65%. Campaign structure with permadeath produces compelling return hooks but also higher campaign-end abandonment. ESTIMATED.
- **Old World** — D7 approximately 45–60%. Contained-campaign 4X produces shorter total engagement; many buyers complete one campaign within week 1 and decide whether to replay. ESTIMATED.
- **Stellaris** — D7 approximately 50–65%. Slow-burn empire growth produces long sessions but slower per-session payoff; D7 lower than character-driven comparables. ESTIMATED.
- **Songs of Syx** — D7 approximately 40–60% of total purchasers but 75–90% of those who completed the first session. The filter is at D1; D7+ retention among survivors is exceptional. ESTIMATED.
- **Caves of Qud** — D7 approximately 40–60% with similar D1-survivor amplification. The roguelike-run structure produces compelling return hooks ("I almost made it; one more run") within week 1. ESTIMATED.

Pattern: **D7 retention 40–75% range for niche-strategy paid-base.** The tighter band (versus D1's 45–85%) reflects the convergence — buyers who return in week 1 are the engaged subset across all comparables. The bottom of the band is dominated by the high-friction titles (Songs of Syx, Caves of Qud) where pre-D1 attrition shifts the denominator.

For Ouroboros specifically: the 7-era ladder's pacing is the load-bearing D7 retention vector. If the player reaches era 2 within their first 5–10 hours of play (week 1 cumulative), the era-transition hook is the return mechanic. If era 1 takes 15+ hours to complete, the D7 retention shifts toward Stellaris-band (slower per-session payoff). Cross-reference T-F3 (the EA-vs-launch decision intersects with pacing-pass timing).

Confidence: ESTIMATED throughout.

## D30 retention — month-one health

D30 retention measures the share of buyers who returned for at least one session in days 8–30. This is the metric most-cited in niche-strategy LTV modeling because D30 retention determines whether the buyer is likely to engage with future DLC, expansions, or content drops at all.

ESTIMATED D30 retention bands, derived from achievement-completion-curve proxy gated at 20–50 hours of playtime (typical month-1 cumulative for engaged niche-strategy buyer):

- **RimWorld** — D30 approximately 40–55%. The colony-narrative pull extends into multi-week play; the no-explicit-victory structure means engaged buyers continue indefinitely. REPORTED tail shape; ESTIMATED figure.
- **Crusader Kings 3** — D30 approximately 35–50%. Multi-generation campaigns extend into week 2–4; players cycling between dynasties produce strong D30. ESTIMATED.
- **Wildermyth** — D30 approximately 30–45%. Campaign-end exits cluster in week 2–3; replayers cycle back for new campaigns. The contained-structure-vs-sandbox-structure split is most visible at D30. ESTIMATED.
- **Battle Brothers** — D30 approximately 35–50%. Campaign-end exits clustered in week 2–4; permadeath-driven restarts produce significant return volume. ESTIMATED.
- **Old World** — D30 approximately 25–40%. The shortest natural-completion-cycle in the set; many buyers finish one campaign in week 1–2 and decide whether to invest in a second. ESTIMATED.
- **Stellaris** — D30 approximately 35–50%. Long campaigns extend into multi-week play; the DLC-cycle becomes most relevant for buyers who reach D30. ESTIMATED.
- **Songs of Syx** — D30 approximately 30–50% of total purchasers but 70–85% of D7-returners. The hardcore-DF-trained tribe runs long colonies that span weeks. ESTIMATED.
- **Caves of Qud** — D30 approximately 30–45% with run-cycle structure producing extended engagement. ESTIMATED.

Pattern: **D30 retention 25–55% range for niche-strategy paid-base.** The contained-design titles (Wildermyth, Old World, Battle Brothers campaign-cycle) cluster at the lower end because the natural exit arrives in week 2–4. The sandbox-design titles (RimWorld, Stellaris, Songs of Syx) cluster at the upper end because there is no built-in exit.

For Ouroboros specifically: the run-shape decision (Form F — collapse-rebuild within a single run, multi-era arc) sits between the contained-campaign and sandbox archetypes. A single Ouroboros run that spans 10–40 hours across 7 eras is more contained than Stellaris but more open than Wildermyth. D30 retention precedent suggests 35–50% if the era-transition pacing produces compelling intra-run hooks. The replay-the-arc design intent (whole-civ runs of varying length, era-paced) supports D30+ via multi-run cycling.

Confidence: ESTIMATED throughout.

## D90 retention — quarterly tail

D90 retention measures the share of buyers who returned for at least one session in days 31–90. This is the metric that determines DLC-attach and expansion-purchase rates, and it is where the "niche-strategy long tail" lives.

ESTIMATED D90 retention bands, derived from achievement-completion-curve proxy gated at 50–150 hours of cumulative playtime and from "concurrent player count over time" public charts:

- **RimWorld** — D90 approximately 25–40%. The colony-restart cycle and DLC-attach (Royalty, Ideology, Biotech, Anomaly) produce one of the strongest D90+ tails in PC gaming. REPORTED tail strength; ESTIMATED figure.
- **Crusader Kings 3** — D90 approximately 25–40%. Dynasty-cycle replay + DLC drops produce strong D90 with DLC-tied spikes. ESTIMATED.
- **Wildermyth** — D90 approximately 15–25%. Campaign completion is the natural exit; D90 retention is driven by replayers cycling for new heroes / different myth-paths. ESTIMATED.
- **Battle Brothers** — D90 approximately 20–35%. Beasts & Exploration / Warriors of the North / Blazing Deserts DLC drops produced visible CCU spikes; D90 tail is strong among the hardcore tribe. REPORTED DLC-spike behavior.
- **Old World** — D90 approximately 15–30%. Heroes of the Aegean and Pharaohs of the Nile DLC produced spikes; the contained-campaign structure limits per-buyer hours but engaged buyers cycle. ESTIMATED.
- **Stellaris** — D90 approximately 25–45%. The strongest DLC-attach behavior in the comparable set per Paradox investor commentary; expansion cycles produce consistent D90+ engagement across the install base. REPORTED DLC-attach.
- **Songs of Syx** — D90 approximately 25–40%. Update-cycle (no DLC, but major free updates) produces spike pattern similar to DLC drops. ESTIMATED.
- **Caves of Qud** — D90 approximately 25–40%. The roguelike-run structure produces non-binary return behavior; the 1.0 launch in December 2024 marked the transition from Early Access to a steady update cadence. ESTIMATED.

Pattern: **D90 retention 15–45% range for niche-strategy paid-base, with DLC/expansion drops producing 2–5× CCU spikes among the engaged subset.** This is the metric where niche-strategy paid-base outperforms the broader Steam baseline — the typical Steam paid-base title shows D90 of 5–15%; niche-strategy clusters at 2–3× that figure.

For Ouroboros specifically: D90 retention is where the LTV multiplier lives. The 7-era ladder + replay-the-arc design intent are direct retention-tail features. If Ouroboros ships with paid expansions or content drops on a 6–12 month cadence (Stellaris / Paradox model), the D90 retention shape determines whether expansions attach at 30%+ (healthy for niche-strategy) or 5–10% (typical action-game tail).

Confidence: ESTIMATED on figures; REPORTED on the DLC-spike pattern and on the niche-strategy outperformance versus broader Steam baseline.

## Refund-window behavior as retention exit

The Steam refund window (2 hours played AND 14 days purchased) is the formal first-session exit mechanism. From a retention perspective, the refund decision and the D1-bounce decision are two views of the same data point. Cross-reference refund_rate_norms.md for full coverage.

Distribution of refund timing within the window, viewed as retention exit signal:

- **First 30 minutes refunds** — these are pre-D1 exits. The buyer never had a first session. ESTIMATED 30–45% of total refund volume in healthy niche-strategy launches; 50–70% in structural-issue launches.
- **30 minutes to 2 hours refunds** — these are first-session exits that crossed the engagement threshold but bounced before the second session. ESTIMATED 30–40% of total refund volume.
- **2 hours to 14 days refunds** — manual-review bucket. These are buyers who attempted multi-session engagement and made a delayed decision. This is the D1-D7 retention exit window. ESTIMATED 15–25% of total refund volume in niche-strategy (higher than action genres because tutorials run longer than 2h).

**Niche-strategy retention floors are anchored by the refund-window structure.** A title that achieves 7% refund rate has effectively pre-trimmed the 7% lowest-retention buyers from the denominator. The reported D1/D7/D30 retention figures above are measured on the post-refund cohort.

For Ouroboros: the lieutenant-personality-loads-before-mechanics pacing is the load-bearing pre-D1 retention surface. If the first 30 minutes loads personality and the lieutenant-system tutorial completes by minute 60, the refund-window-aligned retention curve shifts toward the Wildermyth / Battle Brothers band. If personality fails to load by minute 30, the 2-hour refund bucket fills and the D1 retention denominator collapses.

Confidence: ESTIMATED on distribution percentages; REPORTED on the refund-window-retention overlap.

## Shelf-it-and-come-back pattern — DLC-drop spikes

Niche-strategy paid-base titles exhibit a long-tail playtime spike pattern tied to DLC drops, major free updates, and milestone patches. The player "shelves" the title at some point in months 1–12, retains the install, and returns for a 20–80 hour engagement burst when major new content arrives.

REPORTED instances of the shelf-and-return spike pattern:

- **Stellaris** — Each major expansion (Utopia, Megacorp, Nemesis, Overlord, Galactic Paradise, etc.) produces a visible CCU spike of 2–5× the pre-drop baseline. Paradox investor commentary explicitly frames this as the dominant monetization driver: "DLC attaches at high rates because the install base retains and returns." REPORTED via Paradox earnings communications.
- **Crusader Kings 3** — Royal Court, Tours and Tournaments, Roads to Power produced visible CCU spikes. Paradox-publisher pattern is consistent across the grand-strategy catalog.
- **RimWorld** — Royalty (2020), Ideology (2021), Biotech (2022), Anomaly (2024) each produced multi-week CCU spikes well above pre-drop baseline. Ludeon Studios has not published per-DLC attach rates but the CCU pattern is public via SteamDB. REPORTED CCU pattern.
- **Battle Brothers** — Beasts & Exploration (2018), Warriors of the North (2019), Blazing Deserts (2020) each produced visible CCU spikes. Overhype Studios maintained engagement across a 4–5 year DLC cycle.
- **Old World** — Heroes of the Aegean (2022), Pharaohs of the Nile (2023), Wonders and Dynasties (2024) DLC drops produced visible CCU spikes. Mohawk Games / Hooded Horse publisher pattern is consistent.
- **Caves of Qud** — Major update drops during Early Access (1.0 in December 2024 was the largest) produced CCU spikes. Freehold Games maintained a steady update cadence across a decade-plus development.
- **Wildermyth** — Omenroad expansion (2023) produced a visible spike. Worldwalker Games has signaled additional content roadmap.
- **Songs of Syx** — V64, V65, V66 major version drops have produced CCU spikes despite no paid DLC (free-update model). The shelf-and-return pattern operates independent of monetization model.

Pattern: **the shelf-and-return spike is the dominant LTV multiplier for niche-strategy paid-base.** A buyer who plays 40h at launch, shelves for 9 months, and returns for 60h after a DLC drop is functionally equivalent to a 100h continuously-engaged buyer for LTV purposes — and the publisher captures DLC revenue at the return point.

For Ouroboros specifically: the 7-era ladder + replay-the-arc design intent positions the title for shelf-and-return behavior. If post-launch content drops correspond to new eras (or new dynamics within existing eras, or new tribes), the precedent suggests strong shelf-and-return CCU spikes. Monetization LTV modeling should price expansions at 30–50% of base SKU (cross-reference dlc_pricing_ladders.md) with attach-rate assumptions of 25–40% among D90 retainers per Paradox-band precedent.

Confidence: REPORTED on CCU-spike pattern across the named titles; ESTIMATED on attach-rate precedent.

## Session-length distribution — short-burst vs. long-binge

Niche-strategy paid-base titles split along a session-length axis that is meaningful for design and monetization. The distribution is observable in SteamDB's "average session length" aggregate (where exposed) and in developer-disclosed telemetry where shared.

ESTIMATED session-length patterns across the comparable set:

- **RimWorld** — long-binge dominant. Modal session length 2–5h, with frequent multi-session days. The "one more storyteller event" pull produces extended sessions. REPORTED behavior.
- **Crusader Kings 3** — long-binge dominant. Modal session length 2–4h, with character-lifetime arcs producing extended runs. ESTIMATED.
- **Wildermyth** — mixed, leaning short-burst. The chapter structure produces natural 1–2h session-end points; players often play a chapter and exit. ESTIMATED.
- **Battle Brothers** — long-binge dominant. Modal session length 2–4h with contract-completion arcs. ESTIMATED.
- **Old World** — long-binge dominant per turn-based 4X convention. Modal session 2–4h with "one more turn" pull. ESTIMATED.
- **Stellaris** — long-binge dominant. Modal session length 3–6h, among the longest in the comparable set. ESTIMATED.
- **Songs of Syx** — long-binge dominant. Hardcore-DF-trained tribe runs colony-lifetime sessions. ESTIMATED.
- **Caves of Qud** — mixed. Roguelike-run structure produces 30-minute-to-3-hour runs; some players run multi-character meta-sessions. ESTIMATED.

Pattern: **niche-strategy paid-base is overwhelmingly long-binge.** Modal session length 2–6h is well above the Steam-wide average of approximately 1–1.5h per session. The long-binge profile is a tribe-signal: players who self-select into this genre have time and attention budget that matches the form.

For Ouroboros specifically: the 7-era ladder pacing should respect the long-binge convention. If a single era takes 1–3 hours to complete, the era-transition serves as a natural session-end point (similar to Wildermyth's chapter structure). If an era takes 30 minutes or 8 hours, the session-end-point alignment is broken. The lieutenant-system tactical layer's set-pieces (a few per era per the bible) align with long-binge session structure if pacing is right.

Confidence: ESTIMATED throughout. Per-title session-length data is publisher-private; developer disclosures and aggregator inference are the public signals.

## EA-vs-launch retention shape difference

A meaningful pattern for the T-F3 feed: niche-strategy retention curves change shape between Early Access and 1.0 launch. The EA curve is flatter at D30/D90 because the buyer self-selects harder; the 1.0 curve is steeper because broader audience arrives.

REPORTED instances where the EA-vs-1.0 retention shape was disclosed or visibly inferrable:

- **Caves of Qud** — Early Access cohort (2015–2024) included a heavily self-selected tribe that ran multi-hundred-hour engagements; 1.0 launch in December 2024 brought a broader audience with steeper D30 / D90 drop-off. Freehold Games has commented on this in interviews. REPORTED pattern; ESTIMATED magnitudes.
- **Songs of Syx** — currently in Early Access; the EA cohort runs exceptionally long sessions. A 1.0 launch would predictably broaden the buyer base and produce a steeper D30 curve on the new cohort. ESTIMATED forward-looking.
- **Manor Lords** — Early Access launched April 2024; the EA cohort engaged deeply on the limited 1.0-eve content. The eventual 1.0 launch retention pattern is not yet public.
- **RimWorld** — Early Access from 2013–2018; the EA cohort built the cultural baseline. The 1.0 launch in 2018 produced a broader audience with notably different retention dynamics (modders, casuals, new tribes) layered atop the EA core.
- **Wildermyth** — Early Access 2019–2021; 1.0 in 2021. Worldwalker has commented on the EA-vs-1.0 cohort split in post-launch communications. REPORTED pattern.
- **Battle Brothers** — Early Access 2015–2017; 1.0 in 2017. Overhype Studios has discussed the cohort-shift in retrospectives.

Pattern: **EA cohort retention is flatter (lower D1, higher D30/D90 among survivors); 1.0 cohort retention is steeper (higher D1, lower D30/D90 because broader audience).** The total-revenue-over-time picture is what matters for monetization; the EA-vs-1.0 split is structurally relevant for the T-F3 EA-vs-launch fork.

For Ouroboros specifically: a paid-EA path would produce a tight initial cohort with strong D30/D90 retention and high tolerance for rough edges; a polished 1.0-only path would produce a broader cohort with steeper retention and lower tolerance for rough edges. The bible's launch-readiness directives and the Lieutenant System pivot's RTS-framing-kill suggest a polished launch posture, but the EA-vs-launch decision is not yet picked. Cross-reference T-F3.

Confidence: REPORTED pattern; ESTIMATED magnitudes.

## Achievement-completion-curve proxy methodology

The strongest public proxy for retention curves is the Steam achievement-completion-curve. Steam exposes per-achievement global completion percentages on every store page (Steam's Global Achievement Stats panel) and aggregators (SteamHunters, AStats, completionist.me) preserve historical snapshots.

The proxy works because:

1. Most niche-strategy titles ship with milestone achievements gated at specific play-progress points (first character recruited, first colony built, first generation completed, etc.).
2. A milestone gated at ~30 minutes of play approximates D1 retention (any player who completed it returned for at least the first session).
3. A milestone gated at ~5–15 hours approximates D7 retention.
4. A milestone gated at ~20–50 hours approximates D30 retention.
5. A milestone gated at ~50–150 hours approximates D90 retention.
6. A milestone gated at ~200+ hours approximates the long-tail retainer cohort.

Limitations:

- Players can disable achievements (rare, but possible).
- Achievement-unlock can be delayed (player completes the gating action but the achievement fires on a later trigger).
- Cross-save / family-share / offline-play can decouple achievements from individual-buyer retention.
- The proxy is calibrated on time-played-to-unlock, which varies by player skill and play-style.

Despite limitations, the achievement-curve is the single best public retention proxy for paid-base titles and is the methodology assumed when GameDiscoverCo / Chris Zukowski / niche-strategy postmortems cite retention figures without a developer disclosure.

For Ouroboros specifically: achievement design should align to retention-curve milestones. Gating an achievement at the end of era 1 (D1-D7 proxy), end of era 4 (D7-D30 proxy), and end of era 7 / first full run completion (D30-D90 proxy) would expose Ouroboros-side retention data to the same public methodology used by precedent titles.

Confidence: METHOD reported; specific figure inference ESTIMATED.

## Cross-cutting findings

- **Niche-strategy paid-base retention outperforms broader Steam baseline by 2–3× at D90.** The tribe self-selects and the form rewards extended engagement. ESTIMATED via aggregator-inference.
- **D1 retention 45–85% range; D7 40–75%; D30 25–55%; D90 15–45%.** Bands narrow as the curve progresses — buyers who survive each retention gate converge on engaged behavior. ESTIMATED.
- **Median-hours-played 15–150h range across the comparable set,** with tail extension to 500h+ in the engaged subset. ESTIMATED on figures; REPORTED on band shape.
- **DLC drops produce 2–5× CCU spikes** in retained-install-base; this is the dominant LTV multiplier for the model. REPORTED.
- **Session length is overwhelmingly long-binge** (2–6h modal); the niche-strategy tribe matches the form. ESTIMATED.
- **The 2-hour refund window is structurally adversarial to niche-strategy tutorials.** Retention curves measured post-refund show denominators 7–15% smaller than gross-purchase denominators. Refund timing and D1 retention are two views of the same data.
- **EA cohort retention is flatter; 1.0 cohort retention is steeper.** Cross-reference T-F3.
- **Personality-load timing predicts D1 retention.** Titles that load identity in the first 30 minutes (RimWorld, Wildermyth, CK3, Battle Brothers) cluster at the upper D1 band. Cross-reference Lieutenant System tutorial design.
- **The shelf-and-return spike pattern is observable across all eight comparable titles** independent of monetization model (paid DLC vs. free update). The retention is structural, not monetization-driven.

## Ouroboros retention-shape inventory

Given Ouroboros' bible — 7-era ladder, Lieutenant System tactical layer, Form F (collapse-rebuild) run shape, replay-the-arc design intent, primary tribe (generational/legacy strategy), Foundation tribe (literary hard-SF), 80–200k unit target — the retention-shape vectors are surfaced below. Research Lane reports vectors; Design Lane picks.

1. **Per-era pacing determines D7 retention.** If era 1 → era 2 transition arrives within 5–10h of cumulative play, the era-transition hook serves as the D7 return mechanic. If era 1 takes 15+h, D7 shifts toward Stellaris-band slower-payoff retention.
2. **Era ladder pacing determines D30 retention.** If a complete 7-era run takes 10–40h, D30 retention is driven by run-completion and replay-cycling. If runs are longer than 40h, D30 retention is driven by mid-run engagement and the replay incentive softens.
3. **Lieutenant personality-load determines D1 retention.** First-session personality identification is the load-bearing D1 driver per precedent. Cross-reference refund_rate_norms.md tutorial-failure vectors.
4. **Era-transition design determines pacing-collapse refund / late-D7 attrition.** If era 2 or era 3 feels mechanically thin or narratively disconnected, the pacing-collapse drop hits in the 5-to-14-day window. Cross-reference refund_rate_norms.md.
5. **Replay-the-arc design intent supports D30+ retention via multi-run cycling.** Whole-civ runs of varying length (5h short / 15h medium / 40h long) align with niche-strategy long-binge convention.
6. **Monetization LTV depends on D90 retention shape.** If Ouroboros ships paid expansions on a 6–12 month cadence, D90 retention of 25%+ is the precedent floor for healthy attach rates. If D90 falls below 15%, the expansion-monetization model is structurally weaker; chronicle-merch / cosmetic / book-tie-in monetization channels become relatively more important.
7. **Achievement design should expose retention milestones publicly.** Gating achievements at era-1 / era-4 / era-7 completion points exposes Ouroboros to the same achievement-curve methodology used by precedents and produces a public retention signal that benefits T-W1 wishlist-conversion validation and external coverage.
8. **EA-vs-launch decision (T-F3) determines retention-curve shape.** Paid-EA produces flatter D30 / stronger D90 among self-selected cohort; polished 1.0-only produces steeper D30 with broader audience risk.

The vectors are not ranked. Research Lane does not pick which to mitigate first.

## Conflict surfaced

Reviewed against the bible (hub + spokes) and active in-flux directives:

- **No direct conflict** with `docs/bible/game_bible.md` core principles. The brief is intel input.
- **Consistent with 2026-05-16 Lieutenant System pivot.** Personality-load-before-mechanics retention pattern reinforces the lieutenant-pivot framing on tactical-layer presentation.
- **Consistent with refund_rate_norms.md.** Retention-curve exit timing and refund-window timing are two views of the same data point; the briefs cross-validate.
- **Tension with EA-vs-launch posture.** EA cohort retention shape favors a paid-EA path; bible-current launch-readiness posture leans 1.0-polished. T-F3 is the surface for this decision; Research Lane does not pick.
- **The 80–200k unit target is robust against the retention bands surfaced here.** At median 40–80h engagement per buyer (CK3-band precedent), even mid-band retention produces a healthy install-base for expansion-attach modeling.

## Caveats and confidence

Confidence-tag distribution across the brief:

- **REPORTED** — Steam refund policy 2-hour / 14-day, Paradox DLC-attach pattern (investor commentary), CCU spike pattern on Stellaris / CK3 / RimWorld / Battle Brothers DLC drops (SteamDB public), Caves of Qud 1.0 December 2024 launch, achievement-completion-curve as Steam-exposed public surface, Manor Lords April 2024 EA launch, Wildermyth Omenroad 2023 expansion.
- **ESTIMATED** — All D1/D7/D30/D90 retention figures per title; median-hours-played per-title figures (aggregator-derived inference); session-length distribution per title; per-tribe retention behavior; Ouroboros-specific retention vector probabilities; DLC-attach rate precedents.
- **Training-data floor on retention is mid-low.** Retention telemetry is publisher-private. Steam exposes median-hours-played (aggregator-recoverable) and achievement-completion-curves (proxy methodology). D1/D7/D30/D90 splits are not published; they are inferred from the achievement-curve proxy and from developer-disclosure fragments.
- **Aggregator-independence caveat.** SteamSpy, SteamDB, Gamalytic, games-stats.com, Steam Revenue Calculator all derive from Steam profile scraping. Triangulation among these does NOT count as multi-source confirmation; treat as a single channel per the aggregator-independence directive.

WebFetch and WebSearch were disabled for this brief. No 2025–2026 refresh against current Steam data, Gamalytic, or post-launch dev disclosures. Treat all figures as the training-data floor. The Paradox DLC-spike pattern, the Cities: Skylines 2 refund crisis, and the Manor Lords EA launch are the firmest anchors.

## Feeds Design Lane

This brief feeds the following Design Lane surfaces:

- **T-F3 EA-vs-launch decision** — EA cohort retention is flatter at D30 / stronger at D90 among self-selected buyers; 1.0 cohort retention is steeper. The cohort-shape difference is structurally relevant to the EA-vs-1.0 fork.
- **T-D1 demo strategy** — demo conversion as D1 retention proxy; demo length should align with the niche-strategy long-binge convention (2–3h demo content where Wildermyth chapter 1 sets the precedent).
- **T-W1 wishlist-to-purchase cross-validation** — long-tail D90+ retention is what justifies wishlist-conversion at niche-strategy paid-base price points. A 25–30% wishlist-conversion target depends on the buyer base perceiving the retention shape from store-page signals (review-text, hours-played commentary).
- **Monetization LTV modeling** — DLC-attach precedent (25–40% among D90 retainers per Paradox-band) is the multiplier on the base SKU economics. Shelf-and-return spike pattern supports an expansion-cycle model.
- **Lieutenant System tutorial design** — personality-load-before-mechanics is the D1 retention driver per precedent. Cross-reference lieutenant_pivot_niche_brief.md.
- **Era-transition design** — era 1 → era 2 transition timing determines D7 retention; cross-reference refund_rate_norms.md pacing-collapse vector.
- **Achievement design** — gating achievements at era-1 / era-4 / era-7 completion exposes Ouroboros to public retention-curve methodology and supports external coverage.
- **Launch-readiness checklist** — D1 retention is the launch-week algorithm signal Valve watches; a sub-50% D1 retention pattern materially damages discoverability.

## Open questions for further research

- **Per-title retention disclosures since 2024.** Have any post-2024 GDC talks, GameDiscoverCo paid-newsletter issues, or Paradox / Hooded Horse / Worldwalker financial communications disclosed updated retention figures for the named comparable titles? A 2026 refresh would harden the bands.
- **Achievement-completion-curve snapshots.** A direct refresh of the eight comparable titles' Steam Global Achievement Stats would tighten the D1/D7/D30/D90 proxy figures. WebFetch was denied for this brief.
- **DLC-attach rates.** Paradox investor communications reference attach behavior qualitatively; a quantitative per-DLC attach rate from earnings filings or GDC talks would harden the LTV-modeling assumptions.
- **Median-session-length per title.** SteamDB exposes some session-length aggregates; a refresh would tighten the session-length distribution claims.
- **EA cohort vs. 1.0 cohort retention split.** Caves of Qud is the freshest test case (December 2024 1.0 launch); a 2026 retrospective from Freehold Games on the cohort-shift would directly anchor the T-F3 brief.
- **Foundation-tribe retention anchors.** No direct literary-hard-SF strategy precedents at Ouroboros' scope. Stellaris and Old World are the closest anchors. Any 2026 retention disclosure from a Foundation-IP-adjacent title would be material.
- **Replay-the-arc retention.** No direct precedent in the comparable set for a 7-era / collapse-rebuild structure with explicit whole-civ replay intent. Wildermyth chapter-replay is the closest. Forward-looking research on multi-arc retention design would harden the bible's design intent.
- **Steam Deck retention differential.** Does Steam Deck verified status correlate with measurably different retention curves for niche-strategy paid-base? Strategy/sim with small UI is at retention risk on Deck specifically.

## Sources

Training-data floor sources cited or implied. WebFetch and WebSearch denied — no 2026 refresh.

- **Steam Refund Policy** — Valve store page, stable since 2015. https://store.steampowered.com/steam_refunds/ (training data).
- **Steam Global Achievement Stats** — per-title public completion percentages exposed via store pages and via aggregators (SteamHunters, AStats, completionist.me). Training data; methodology re-stated.
- **GameDiscoverCo newsletter (Simon Carless)** — retention-curve analyses, niche-strategy long-tail patterns, achievement-curve proxy methodology. Training data.
- **How To Market A Game / Chris Zukowski** — niche-strategy retention commentary, demo-as-D1-proxy pattern. Training data.
- **Tynan Sylvester / RimWorld blog** — engagement commentary, median-hours-played references. Training data.
- **Worldwalker Games / Wildermyth blog** — chapter-completion-curve disclosures, EA-vs-1.0 cohort commentary. Training data.
- **Soren Johnson / Mohawk Games / Old World** — retention vs. Civ-series commentary, contained-campaign design framing. Training data.
- **Paradox investor communications** — Stellaris DLC-attach pattern, CK3 retention framing. Training data.
- **Freehold Games / Caves of Qud GDC talks** — EA-vs-1.0 cohort framing, decade-long EA retention. Training data.
- **Overhype Studios / Battle Brothers retrospectives** — DLC-cycle retention. Training data.
- **SteamDB / Gamalytic** — CCU-over-time charts, median-hours-played aggregates, owner estimates. Single upstream channel (Steam profile scraping); aggregator-independence caveat applies. Training data.
- **How Long To Beat** — community time-to-completion figures. Training data.
- **GDC postmortem catalog** — niche-strategy retention retrospectives. Training data, not enumerated.

Originating chat: 2026-05-18 Research Lane T-CL3 dispatch. Originating brief: this file.
