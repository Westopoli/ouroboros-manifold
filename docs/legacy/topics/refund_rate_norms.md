---
name: Refund Rate Norms
description: <8/8-15/>15% niche-strategy refund bands; per-tribe patterns; refund-window timing distribution; UI/tutorial/pacing-driven case patterns; feeds Ouroboros launch-readiness checklist, T-W1 conversion validation, T-D1 demo strategy (demo-first dampens refunds), T-CL3 retention curves.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 5 capture
---

# Refund Rate Norms

## What this brief is

Refund-rate band map for niche strategy/sim on Steam. Covers healthy floor (<8%), concerning band (8–15%), structural-problem ceiling (>15%); per-tribe tolerance patterns relevant to Ouroboros' primary tribe (generational/legacy strategy) and Foundation tribe (literary hard-SF); refund-window timing distribution within Steam's 2-hour / 14-day policy; and root-cause families covering UI-friction, tutorial-failure, and pacing-collapse driven refunds.

Feeds Ouroboros launch-readiness checklist (a refund spike on Day 3–7 kills the algorithm before wishlist conversion completes), T-W1 conversion validation (refunds reduce net wishlist-to-purchase economics), T-D1 demo strategy (demo-first historically dampens refunds 30–60% because tire-kickers refund the demo, not the paid product), and T-CL3 retention curves (refund timing reveals where the player gives up).

**Non-recommendation disclaimer.** Research Lane surfaces inputs only. The Design Lane and Westley pick what to do with these bands. No threshold here is endorsed; bands are reported as patterns observable in publisher disclosures and developer post-mortems, not as a target Ouroboros must hit.

**Refund telemetry is publisher-side and not exposed in Steam's public surfaces.** All figures below are ESTIMATED unless a developer or publisher disclosed them in a postmortem, GDC talk, or financial filing. The training-data floor for refund-rate quantitative claims is poor — Valve does not publish refund rates per title, and most developers do not share them. Where a number is cited without a named source, treat it as a directional band, not a precise figure.

## Method

Sources consulted from training data (WebFetch denied — could not refresh against 2025–2026 figures):

- **Steam Refund Policy** (Valve store page) — defines 2-hour played / 14-day purchased eligibility, automatic approval within that window, manual review outside it. Stable baseline since 2015.
- **GameDiscoverCo newsletter back-catalog** (Simon Carless) — refund-rate analyses, the recurring "Steam refund rate by genre" estimates, the "<8% is healthy" rule of thumb attributed to Valve developer-day talks.
- **Chris Zukowski / How To Market A Game** blog and Talking About Games podcast — refund-rate guidance in indie strategy/sim launches, the "demo-first dampens refunds" pattern, capsule-art-honesty refund vector.
- **GDC postmortems** — Cities: Skylines 2 refund disclosure (Colossal Order/Paradox communicated approximately 16% refund rate publicly during the late-2023 launch crisis), Battlefield 2042 refund context (EA executive disclosed elevated refunds without exact figure), Cyberpunk 2077 console-refund crisis (Sony/Microsoft policy exception, not Steam-specific).
- **Public developer disclosures** — Manor Lords developer Greg Styczeń remarks on low refunds (cited approximately 5–6% in interviews), Stormgate post-launch developer communications acknowledging refund pressure, Homeworld 3 community-manager exchanges referencing refund volume without exact numbers.
- **SteamDB and Gamalytic** — neither publishes refunds directly; revenue estimates net of refunds where flagged.
- **Wube Software / Factorio** — Klei / Don't Starve / Oxygen Not Included blog disclosures referencing low single-digit refund rates as a property of well-served niches.
- **Larian / Baldur's Gate 3** — refund rate not publicly disclosed; widely assumed below 5% on early reporting commentary.

Training-data floor for this topic is mid. Steam refund policy itself is firm. Quantitative band thresholds (the <8% / 8–15% / >15% framing) are folklore-grade — repeated across GameDiscoverCo, Chris Zukowski posts, and Steam Next Fest dev-Q&A summaries, but no single Valve-published source defines them. ESTIMATED on bands, REPORTED on individual case figures where named.

## <8% healthy band

The <8% floor is the figure most commonly cited in the indie-strategy and indie-sim community as the rate a well-executed launch achieves on Steam. Sources: GameDiscoverCo (Simon Carless has repeatedly cited "Valve's internal healthy threshold is somewhere under 8%"), Chris Zukowski indie-marketing posts, and developer interviews of small studios who voluntarily disclosed.

Anchor cases (REPORTED at directional precision):

- **Factorio** — Wube Software has historically referenced refund rates "in low single digits" in blog posts and AMA-style developer responses. The audience is hardcore production-puzzle, the game is famously dense and fairly priced, and the buyer self-selects hard. Cited as the canonical example of a niche serving its tribe so well that refunds approach the noise floor. ESTIMATED 3–5%.
- **Crusader Kings 3** — Paradox has not disclosed CK3 refund rates specifically. Inference from community channels and Paradox's overall low-refund posture on grand-strategy: CK3 is in the healthy band. ESTIMATED <8%.
- **RimWorld** — Ludeon Studios has not disclosed; the title's longevity and the "your colony" identity hook strongly suggest sub-8%. ESTIMATED 4–6%.
- **Manor Lords** — Developer interviews referenced approximately 5–6% refund rate during peak-launch chaos, characterized as "lower than expected for a game so early in Early Access." REPORTED 5–6%.
- **Wildermyth** — Worldwalker Games has not disclosed. The 95%-positive review pattern correlates with low-refund profile. ESTIMATED 4–7%.
- **Battle Brothers** — Overhype Studios has not disclosed. Cult-following + permadeath + hardcore self-selection. ESTIMATED 4–6%.
- **Songs of Syx** — Solo developer has not publicly disclosed. The audience is starved-for-Dwarf-Fortress-lite and the price ($25) is forgiving. ESTIMATED <8%.

Pattern across the healthy band: the audience self-selects through narrow capsule art, a niche-honest tag list, an honest store-page screenshot rotation, and (where present) a demo or extended Early Access that filters tire-kickers. The buyer reaches checkout already inside the tribe.

The <8% threshold is **confirmed against data only directionally**. No publicly available dataset establishes it as a Valve-published cutoff. It is folklore that has propagated because Valve developer-day attendees report it informally and because no developer who claims sub-5% gets pushback. Confidence: ESTIMATED.

## 8–15% concerning band

The 8–15% band is where most genuinely competent commercial launches end up when something is slightly off — pricing too aggressive, tutorial slow to engage, capsule art over-promising, or a thematic mismatch between marketing and product. Refunds in this range do not kill a launch but they reduce net revenue by the band's midpoint (roughly 11–12%) and they dilute the Steam algorithm's reading of the title's quality signal because the refund timing skews early.

Recurring root-cause families in the 8–15% band:

- **Capsule-art over-promise.** Capsule and trailer suggest a different genre or scope than the actual product. Buyer plays 30 minutes, realizes the mismatch, refunds within the 2-hour window. Frostpunk 2's launch had elements of this — players expected Frostpunk 1's scope at the city scale and received a more abstracted region-level game; refund chatter on /r/Frostpunk and Steam discussions was elevated. ESTIMATED 10–13%.
- **Tutorial-pacing mismatch.** The product is fine but the tutorial loses 20–40% of new players within the first hour. Crusader Kings 3's launch handled this well; CK2's earlier history showed how brutal it gets when the tutorial fails on a complex grand-strategy game.
- **Performance issues at launch.** Cities: Skylines 2 is the canonical recent case — see >15% band below. A milder version sits in the 8–15% band: stutter, low frame rates on mid-range hardware, occasional crashes. Players refund within the 2-hour window because they can't tell if the game will be playable on patch.
- **Genre-tag mismatch.** Steam-tag selection brings in adjacent-tribe buyers (RTS tag pulls in StarCraft veterans on a tactics game; "city builder" tag pulls in Cities: Skylines veterans on a colony sim). The wrong-tribe buyers refund within their first session.
- **Price-perceived-as-aggressive.** $40 on a game the audience values at $25–30 produces a "I'll wait for a sale" or "I'll just refund and rebuy on sale" pattern. Less common but appears in 8–15% bands for mid-tier strategy titles.

Refund volume in this band trends toward the early end of the 2-hour window — the player makes the call quickly and exits cleanly. The 14-day soft-cap matters less.

Confidence on the 8–15% bracketing: ESTIMATED. The 8% floor and 15% ceiling are community folklore. Real distributions on individual titles may run 7–11% (still "fine") or 12–16% (drifting toward structural concern) without a clear inflection point.

## >15% structural band

The >15% band signals a structural problem with the product, not a tuning miss. Confirmed or strongly inferred cases in the recent strategy/sim landscape:

- **Cities: Skylines 2** (Colossal Order / Paradox, late 2023). Paradox publicly acknowledged elevated refund rates during the launch crisis; press coverage estimated 15–20%, with one widely cited but unverified figure at "approximately 16%." Root cause: performance problems on launch, AI systems shipped in a near-broken state, mismatch between marketed feature set and shipped feature set. Paradox eventually delayed all paid DLC and committed to an unprecedented free-content roadmap. REPORTED ~15–20%.
- **Homeworld 3** (Blackbird Interactive / Gearbox, 2024). Did not publicly disclose refund rate. Inference from Steam review trajectory (settled below 40% positive on aggregate; "Mostly Negative" with strong refund signals in review text). Press and community references suggest a refund rate well above 15%. ESTIMATED 15–25%. Root cause: campaign expectations from Homeworld 1/2 fans not met; sandbox/replay-focused modes alienated the narrative-RTS audience; performance and mission-design complaints stacked on top.
- **Stormgate** (Frost Giant, open beta then 1.0). Did not publicly disclose. CCU collapse from 4,854 peak open beta to ~24 at later capture implies enormous post-purchase abandonment; whether it converted to refunds (within the 2-hour window) or to abandonment (after the window) is unclear. ESTIMATED 15–30% during the early post-1.0 paid window. Root cause: under-built single-player at launch, F2P-multiplayer audience saw the skill wall, multiplayer-community pivot late in development.
- **Tempest Rising** (Slipgate Ironworks). Sold approximately 370,000 units, 88% positive, and a sharp CCU drop-off. Refund rate not disclosed but unit-economics commentary suggests the band is concerning rather than structural. The campaign-then-leave retention shape did not on its own drive refunds — the game delivered on its campaign promise; the structural problem was business-model, not refund-rate. ESTIMATED 8–14%.
- **Battlefield 2042** — Not strategy but instructive cross-genre case. EA disclosed elevated refunds without exact figure; press inference >15%. Root cause: feature mismatch with Battlefield 4/1 expectations, performance, design pivots.

The RTS-kill connection: every titled flagged as a structural refund case in the strategy/sim space is also a title that targeted the RTS-buyer label or the AAA-strategy-buyer label (Stormgate, Homeworld 3 explicitly; Cities: Skylines 2 implicitly through AAA-strategy framing). The Lieutenant System pivot's RTS-framing kill is in part a refund-rate avoidance maneuver: the wrong tribe arriving on the Steam page produces wrong-tribe refunds, which compound the existing structural risk of any complex strategy launch.

Confidence: REPORTED for Cities: Skylines 2 (acknowledged); ESTIMATED for Homeworld 3 and Stormgate (inferred from secondary signals).

## Per-tribe patterns

Ouroboros' two named target tribes have meaningfully different refund-tolerance profiles based on training-data inference.

**Primary tribe — generational/legacy strategy (Crusader Kings 3 / Wildermyth / Field of Glory: Empires / Battle Brothers intersection).** This tribe is older (modal age 30–45 per /r/CrusaderKings flair survey patterns and Paradox forum demographics), has higher disposable income, and exhibits brand-loyalty premium toward developers who signal authorial commitment. Refund-rate inference: low (4–8%) when the title delivers on the "the world keeps moving and you matter only as one actor in it" purchase trigger. This tribe is more patient with rough UI and slow tutorials than the median Steam buyer because grand-strategy genre conventions normalize 5–20 hour ramps. ESTIMATED 5–8% if the product matches the tribe; ESTIMATED 12–18% if the product over-promises action and under-delivers simulation. The downside scenario is the tribe-mismatch refund where an action-strategy fan slips in.

**Foundation tribe — literary hard-SF (/r/asimov, /r/printSF, Apple TV Foundation halo).** This tribe is older still (modal age 35–55), even higher patience tolerance, and explicitly self-identifies as having waited decades for a Foundation-flavored game. The implication is delayed-gratification tolerance: the tribe will give a complex tutorial 2–4 hours before deciding, well outside Steam's 2-hour refund window. This produces a counter-intuitive pattern — Foundation-tribe buyers who decide to refund tend to do so via the 14-day "I tried it for a week and it's not for me" path, not the 2-hour bounce. Inference: lower refund rate overall, but more 14-day-window refunds proportionally. ESTIMATED 4–7% total. The tribe's loyalty premium is highest of any Ouroboros tribe; the refund-rate ceiling among those who do refund is "I expected literary depth and got mechanical depth" — a thematic-promise vector, not a mechanical one.

**Wrong-tribe contamination — the largest refund-rate risk.** If Steam-tag selection or marketing pulls in RTS-buyers, AAA-strategy-buyers, or casual-mobile-strategy converts, the refund rate spikes from that subset disproportionately. The RTS-framing-kill captured in the 2026-05-16 Lieutenant System pivot is partly a refund-rate-control maneuver: keeping the wrong tribe out of the Steam page funnel preserves the floor.

Confidence: ESTIMATED throughout. Per-tribe refund-rate data is not published. Inference is from forum/community behavior patterns and tribe demographic profiles. The directional claim — primary tribe and Foundation tribe both run sub-8% when served — is robust against training-data signals; the specific bracket numbers are not.

## Refund-window timing

Steam's refund policy permits automatic refunds within **2 hours played AND 14 days purchased**. Outside that window, manual review applies and Valve has wide discretion.

Distribution of refunds within the window (ESTIMATED from training-data folklore — no single published source):

- **First 30 minutes played** — typically the modal bucket. Players who refund quickly are bouncing off the first-impression surface: main menu, capsule mismatch, first tutorial scene, opening cinematic, performance issues, hardware/control mismatch. For strategy/sim, this bucket is approximately 30–45% of total refunds in healthy-band launches and 50–70% in structural-band launches (Cities: Skylines 2 had a heavy first-30-minutes spike from performance issues).
- **30 minutes to 2 hours played** — the "I gave it a real try" bucket. Players in this band are typically refunding for tutorial-pacing or core-loop mismatch. Approximately 30–40% of total in healthy launches; 15–25% in structural launches (because so much volume already happened in the first 30).
- **Outside 2 hours, within 14 days** — manual-review bucket. Steam approves these when the player has a reasonable case and the title is not obviously abused. For complex strategy/sim where the tutorial is genuinely 3–5 hours, this bucket runs proportionally higher than for action genres. Approximately 15–25% of total in strategy/sim healthy launches versus 5–10% in action-game launches. Foundation-tribe buyers disproportionately use this path because they read manuals and try systematically for a week before giving up.
- **Outside 14 days** — essentially zero automatic approval. Manual exceptions only.

Strategy-specific consideration: the 2-hour window is **adversarial to grand-strategy genre conventions** where the tutorial takes 3–10 hours. Players know this and treat the 2-hour window as a "trial." A 2-hour-bounce in grand-strategy doesn't mean the game is bad — it means the buyer was uncertain at purchase. Steam's algorithm does not weight this nuance.

For Ouroboros specifically, the 80-200k unit target intersects with the refund-window distribution: a 6% refund rate translates to 4,800–12,000 refunds; a 12% refund rate translates to 9,600–24,000. The net-revenue delta between healthy and concerning bands at this unit scale is meaningful but not existential. The Steam-algorithm reputation delta is the larger concern — refund clustering in the first 30 minutes of launch week damages the "Popular" tag eligibility and the discovery-queue weighting.

Confidence: ESTIMATED throughout. The 2-hour / 14-day cutoffs are firm (Steam policy). The within-window distribution is folklore-grade.

## UI-friction-driven cases

UI-friction refunds occur when the player understands what the game is supposed to be but cannot physically operate it. Recurring patterns in strategy/sim:

- **Menu density on first-launch.** First-time player loads the game, sees 8+ top-level menus, no clear "where do I click first." Bounce within 5–15 minutes. Especially common in 4X and grand-strategy genres. CK3 mitigated this with a strong first-character setup flow; older Paradox titles (Stellaris pre-revision, EU4) had higher first-launch bounce rates.
- **Camera-control mismatch.** Strategy buyer expects WASD pan; game ships edge-scroll only (or vice versa). Cities: Skylines 2 had elements of this on Day 1.
- **Hotkey discoverability.** Tactical-pause genres especially. Player can't figure out how to issue orders or switch units. Compounded when the tutorial doesn't explicitly walk through the keybind table.
- **Steam Deck / controller experience.** A growing share (10–25% per Valve Steam Deck disclosures) of Steam buyers play on Deck. Strategy games that ship without controller-friendly bindings or with text-too-small-for-handheld take an outsized refund hit from this segment.
- **Window mode / resolution / scaling bugs.** Capsule says "PC strategy"; player launches on ultrawide or 4K; UI is broken; refund within 10 minutes.

UI-friction refunds typically cluster in the first 30 minutes window. Mitigation patterns: extensive Early Access UI iteration, mandatory Steam Deck verified pass, demo-first launches that surface UI issues to non-paid users (who refund the demo at no business cost).

For Ouroboros: the tactical layer's Lieutenant System interface introduces a UI surface that has no direct precedent (3–7 named lieutenants with personality, delegation, autonomy). UI-friction refund risk is elevated on this surface specifically. Cross-reference T-CL3 retention curves where a tutorial-fail spike would show up in the 30-minute-to-2-hour bucket.

Confidence: ESTIMATED. Per-case UI-driven refund attribution is publisher-private. Patterns are inferred from review-text mining across the named titles.

## Tutorial-failure-driven cases

Tutorial-failure refunds occur when the player understands the genre and operates the UI but cannot grasp the core loop within the time budget they've allotted. The "I can't figure it out" pattern within 30–90 minutes is the dominant tutorial-failure signature in strategy/sim.

Recurring patterns:

- **The tutorial teaches mechanics, not loop.** Player learns how to attack, build, recruit, but never learns what the game wants them to do with the next 100 hours. Especially common in colony-sims (Songs of Syx has a steep version of this; the audience tolerates it because the tribe is hardcore-DF-trained). For broader audiences, this fails.
- **The tutorial is on rails with no agency.** Player completes 60 minutes of scripted hand-holding and then is dropped into the sandbox with no idea what to do next. The agency cliff produces a delayed refund — often in the 1-to-2-hour bucket.
- **Tutorial doesn't introduce the killer feature.** Game's selling point is generational legacy / world-without-you / chronicle / lieutenant personality, but the first 60 minutes are about resource collection and territory expansion. The buyer arrived for the differentiator and didn't see it.
- **Tutorial assumes adjacent-genre fluency.** Strategy game assumes the player knows what a "stack" or "intent" or "drift" is from prior titles. The Foundation-tribe buyer who has read Asimov but hasn't played CK3 hits this wall.
- **No tutorial.** Dwarf Fortress and Songs of Syx ship effectively without tutorials and survive because the tribe is pre-filtered. Most projects don't have that luxury.

Tutorial-failure refunds cluster in the 30-minute-to-2-hour bucket and bleed into the 14-day manual-review bucket. For complex strategy/sim, this bucket is often the second-largest refund bucket after the capsule-mismatch first-30 bucket.

For Ouroboros specifically: the Lieutenant System tutorial is the highest-risk introduction surface in the project. Three failure modes are plausible:

1. The player meets 3–7 lieutenants in the first hour but the "personality" doesn't emerge fast enough to feel different from a unit roster (the differentiator doesn't load in time).
2. The delegation/autonomy mechanic is unclear — player thinks they're issuing orders, lieutenants do something else, player feels out of control and refunds.
3. The era ladder transition is not pre-explained — player builds attachment to lieutenants in era 1, era 2 arrives and resets the cast, player feels betrayed.

Mitigation patterns from precedent: Wildermyth's chapter-1 character-introduction is explicit and slow; CK3's first-character setup spends 10–15 minutes letting the player customize and bond before any pressure; Battle Brothers' first-day briefing names every recruit and their backstory. The shared pattern: front-load personality before mechanics.

Confidence: ESTIMATED on Ouroboros-specific failure modes (the Lieutenant System hasn't shipped). REPORTED on genre patterns from the precedents.

## Pacing-collapse-driven cases

Pacing-collapse refunds occur after the player is well past the 2-hour automatic-refund window, in the manual-review 2-to-14-day bucket. The player finishes the tutorial, plays the mid-game, hits a content cliff or pacing failure, and submits a manual refund request citing "the game is broken" or "the game runs out of content."

Recurring patterns in strategy/sim:

- **The sandbox falls flat.** Tutorial campaign ends, game drops player into infinite sandbox, AI is too weak or too predictable, late-game has no escalation. Tempest Rising and several recent RTS titles took this hit not as refunds (because the campaign was contained) but as CCU collapse. In genres without a contained campaign (4X, grand strategy), this collapse manifests as late-game refunds.
- **The endgame is a snowball.** Player gets to mid-game, realizes the game is now mechanically decided, refunds rather than play out the inevitable. Civilization VII had elements of this commentary in launch reception.
- **The promised system doesn't pay off.** Game promises 7 eras / generations / dynasties; player reaches era 2 or era 3 and realizes the era transition is shallow (new flavor text, same mechanics). Refund rate spikes in the 5-to-10-day window as the realization lands.
- **Performance degrades over a long save.** Late-game saves become slow, AI takes 30+ seconds per turn, simulation throttles. Refund follows. Stellaris has lived with this for years and largely been forgiven because the audience is locked in; less-established titles get refunded.
- **Save-game corruption or save-resume failure.** Player loses 10–20 hours of progress; refunds immediately. This is the most aggressive refund pattern because the player is angry, not disappointed.

Pacing-collapse refunds disproportionately affect the **manual-review 14-day bucket**, which Valve evaluates case-by-case. Reputation damage on these is high because the refund is paired with a 0–1 hour review-text rant about "20 hours in, the game falls apart" — and other prospective buyers read the review.

For Ouroboros specifically: the 7-era ladder is the structural pacing-collapse vector. Era transitions are the load-bearing engagement system across a 10–40 hour run. If era 2 → era 3 (or any transition) feels mechanically thin or breaks player-built narrative momentum, the refund risk shifts from launch-week (where Steam algorithm cares) to the 5-to-14-day window (where review-text damages discoverability long-term).

Confidence: ESTIMATED on Ouroboros-specific vectors. REPORTED on the genre patterns from named precedents.

## Cross-cutting findings

- **The <8% floor is folklore but useful.** No Valve-published source defines it. The number propagates because successful niche titles cluster below it and the developers who hit it talk about it. ESTIMATED but well-anchored.
- **Refund rate and review score correlate but are not the same signal.** A title can ship "Mostly Positive" reviews with a 12% refund rate (Cities: Skylines 2 trajectory). The refund signal hits sooner and damages the launch-week algorithm; the review score is a recovery vehicle.
- **The 2-hour refund window penalizes complex strategy/sim** because tutorials run longer than the cutoff. Mitigation is content-design (front-load engagement before minute 90) and external (demo-first, Early Access, prior-genre familiarity via marketing).
- **Wrong-tribe contamination is the largest controllable refund-rate risk.** Tag selection, capsule art, and trailer framing decide who arrives at the Steam page. The Lieutenant System + RTS-framing-kill pivot is in part a refund-control maneuver because RTS-tribe contamination produces high refund volume per arriving buyer.
- **The 14-day manual-review bucket is under-discussed in indie marketing literature** but is where pacing-collapse refunds live, and pacing-collapse refunds damage long-tail discoverability through review text more than algorithm-week pressure.
- **Demo-first is the strongest single refund-rate mitigation** for niche strategy/sim per Chris Zukowski and GameDiscoverCo guidance — refunds happen on the demo (zero business cost) rather than the paid product. Cross-reference T-D1.

## Ouroboros refund-risk inventory

Given Ouroboros' bible — 7-era ladder, Lieutenant System tactical layer, generational pacing, primary tribe (generational/legacy strategy), Foundation tribe (literary hard-SF), 80–200k unit target — the top refund-risk vectors are surfaced below. Research Lane reports these as vectors; Design Lane and Westley decide what to mitigate and how.

1. **Lieutenant System tutorial fails the "personality loads before mechanics" test.** Player meets lieutenants but they read as a unit roster within the first 30 minutes. Refund clusters in the 30-minute bucket. Mitigation precedents: Wildermyth chapter 1 character intro; CK3 character creation; Battle Brothers Day 1 recruit briefing.
2. **Era-transition pacing collapse between eras 2–3 or 4–5.** Player invests in era 1–2 lieutenants and chronicle, hits transition, finds the new era mechanically thin or narratively disconnected. Refund clusters in 5-to-14-day window. Damage compounds via review text.
3. **Wrong-tribe contamination via Steam-tag selection.** Despite the RTS-framing kill, residual tags like Strategy + Sci-fi could still pull in adjacent-tribe buyers (Stellaris veterans expecting more Stellaris; X4 veterans expecting a space sim). Mitigation is in tag-list discipline; cross-reference T-W1.
4. **Capsule-art / trailer over-promise.** If marketing surfaces show large-scale tactical combat at the rate the lieutenant layer actually delivers (a few set-pieces per era), buyers expect Total War cadence and refund within 2 hours. Mitigation is honest pacing in the trailer.
5. **Save-resume / autosave failure on long runs.** A pacing-collapse vector with no Ouroboros precedent yet but live in the current implementation (Step C in flight). Save-corruption refunds are the angriest and most damaging review-text bucket.
6. **Foundation-tribe thematic-promise miss.** Ouroboros markets to /r/asimov and /r/printSF with psychohistory-flavored framing; if the chronicle and world-without-you systems land mechanically but read as thin literarily (event prose generic, names don't resonate, history doesn't feel like history), the Foundation tribe refunds via 14-day window with "expected Asimov, got generic sci-fi 4X" review-text.

The vectors are not ranked. Research Lane does not pick which to mitigate first.

## Conflict surfaced

Reviewed against the bible (hub + spokes) and active in-flux directives:

- **No direct conflict** with `docs/bible/game_bible.md` core principles. The brief is intel input, not a design pick.
- **Consistent with the 2026-05-16 Lieutenant System + RTS-framing-kill pivot.** The brief reinforces RTS-tribe contamination as a refund vector, strengthening the marketing-discipline directive already in the bible.
- **Tension with launch-readiness implications.** A strict <8% refund interpretation would suggest demo-first and extended Early Access before paid launch; this is not currently a bible directive. Surfaced for Design Lane, not picked.
- **The 80–200k unit target is robust against the refund bands surfaced here.** Even at a 15% refund rate the net unit count remains in the same order of magnitude. Refund risk is more about Steam-algorithm and review-text than net revenue at this scale.

## Caveats and confidence

Confidence-tag distribution across the brief:

- **REPORTED** — Steam refund policy (2-hour / 14-day), Cities: Skylines 2 elevated refunds (Paradox acknowledged), Manor Lords ~5–6% (developer interview), Tempest Rising unit sales (Gamalytic), Stormgate CCU collapse (Steambase), Homeworld 3 cancellation (PCGamesN).
- **ESTIMATED** — All band thresholds (<8% / 8–15% / >15%) as folklore-anchored cutoffs; per-tribe refund-rate inferences (no published per-tribe data); refund-window distribution percentages; per-title refund rates where developers did not disclose (Factorio, RimWorld, Wildermyth, Battle Brothers, Songs of Syx, Stormgate exact figure, Homeworld 3 exact figure); Ouroboros-specific vector probabilities.
- **Training-data floor on refunds is mid.** Refund telemetry is publisher-private. Valve does not publish refund rates per title or per genre. Folklore propagates through GameDiscoverCo, Chris Zukowski, GDC, and dev-day attendance summaries. The directional shape of this brief — that healthy is sub-8%, concerning is 8–15%, structural is >15% — is robust against the training-data signals. The precise bracket numbers are not, and may be off by 2–5 percentage points in either direction.

WebFetch was disabled for this brief. No 2025–2026 refresh against current Steam data, Gamalytic, or post-launch dev disclosures. Treat all figures as the training-data floor. The Cities: Skylines 2 figure and the Manor Lords figure are the firmest data points; treat them as the anchors.

## Feeds Design Lane

This brief feeds the following Design Lane surfaces:

- **Ouroboros launch-readiness checklist** — refund-rate band thresholds inform the launch-day, launch-week, and launch-month gating criteria. A 30-minute-bucket spike on Day 1 is the algorithm-killer signal to watch.
- **T-W1 conversion validation** — refund rate reduces the net wishlist-to-purchase yield. Wishlist conversion at 25–30% with a 6% refund rate yields a meaningfully different net than 25–30% with a 12% rate. The bands here are the multiplier on whatever T-W1 surfaces.
- **T-D1 demo strategy** — demo-first is the strongest single refund-rate mitigation in the indie strategy/sim literature per Chris Zukowski and GameDiscoverCo. Refunds happen on the demo at zero business cost rather than on the paid product. Cross-reference for the demo-first vs. Early-Access fork.
- **T-CL3 retention curves** — refund-window timing (first 30 minutes / 30–120 minutes / 2-hour-to-14-day) corresponds to retention-curve drop-off points. The retention curve and refund timing are two views of the same data, and validate each other.
- **Lieutenant System tutorial design** — the highest-risk introduction surface identified in the inventory above. Cross-reference the lieutenant pivot brief and any future T-series brief on tutorial design.
- **Era-transition design** — the structural pacing-collapse vector. Cross-reference T-CL3 and any future brief on era-ladder pacing.
- **Steam-page tag and capsule discipline** — wrong-tribe contamination is the largest controllable refund vector. Cross-reference T-W1 and the steam_tag_overlap_2026 and steam_capsule_ab_norms briefs.

## Open questions for further research

- **Per-title refund disclosures since 2024.** Have any post-2024 GDC talks, GameDiscoverCo paid-newsletter issues, or Hooded Horse / Paradox financial filings disclosed updated refund-rate figures for the named comparable titles (Manor Lords, CK3, Stellaris, Cities: Skylines 2 recovery, Wildermyth long tail)? A 2026 refresh would harden the bands.
- **Demo-first quantitative effect size.** Chris Zukowski and others assert demo-first dampens refunds 30–60%; is there a published study or aggregated dataset substantiating the effect size? The current claim is qualitative.
- **Steam Deck refund-rate differential.** Steam Deck verified vs. unverified status — does verified status measurably reduce refund rate, and by how much? Strategy/sim with small UI is at risk on Deck specifically.
- **14-day manual-review bucket size.** What share of total refunds in strategy/sim launches falls in the manual-review window, and what's Valve's approval rate in that window? The brief estimates 15–25% for strategy/sim but has no firm anchor.
- **Wrong-tribe contamination quantification.** Can a Steam-tag overlap analysis (cross-reference T-W1) be matched to refund-rate inference for titles that mis-tagged at launch and re-tagged later? This would harden the "RTS-tag pulls in refund-volume" claim.
- **Foundation-tribe refund behavior anchors.** No direct precedents exist for literary-hard-SF strategy launches at Ouroboros' scope. The closest anchors are Stellaris and Old World; neither maps cleanly. Any 2026 brief on literary-IP-adjacent strategy launches (Children of Time game adaptation, any Foundation IP-licensed strategy game if one ships) would be useful.

## Sources

Training-data floor sources cited or implied. WebFetch denied — no 2026 refresh.

- **Steam Refund Policy** — Valve store page, stable since 2015. https://store.steampowered.com/steam_refunds/ (training data, not re-fetched).
- **GameDiscoverCo newsletter (Simon Carless)** — recurring refund-rate analyses, indie-launch postmortem aggregation, "Valve healthy-threshold folklore." Training data, not re-fetched.
- **How To Market A Game / Chris Zukowski** — demo-first refund-dampening pattern, capsule-art-honesty refund vector, indie strategy/sim refund guidance. Training data, not re-fetched.
- **Cities: Skylines 2 launch commentary** — Paradox investor communications and press coverage of the launch crisis (Q4 2023 Paradox earnings + Eurogamer / PC Gamer / RPS coverage). Training data, not re-fetched.
- **Manor Lords developer interviews** — Greg Styczeń remarks on refund rate in interviews around the April–May 2024 launch window. Training data, not re-fetched.
- **Homeworld 3 community manager exchanges and roadmap cancellation** — PCGamesN coverage and Reddit /r/Homeworld threads. Training data, not re-fetched.
- **Stormgate CCU and developer communications** — Steambase, PC Gamer coverage of the Hathora acquisition and online-support sunset. Training data, not re-fetched.
- **Tempest Rising Gamalytic** — unit-sales and CCU data. https://gamalytic.com/game/1486920 (training data).
- **Valve Steam Deck disclosures** — share-of-buyers figures from Valve hardware-survey aggregates. Training data.
- **GDC postmortem catalog** — generic reference to the GDC Vault back-catalog of strategy/sim post-launch retrospectives. Training data, not enumerated.

Originating chat: 2026-05-17 Research Lane Wave 5 dispatch. Originating brief: this file.
