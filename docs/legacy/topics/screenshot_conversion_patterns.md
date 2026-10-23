---
name: Screenshot Conversion Patterns
description: Niche-strategy screenshot count, slot-1 share, UI/cinematic mix, annotation, per-cluster subject patterns, GIF slot use, in-image localization, refresh cadence; feeds screenshot-build spec, T-S4 page sequence, T-L1 localization-in-image decision.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 4 capture
---

# Screenshot Conversion Patterns

## What this brief is

Topic brief on Steam screenshot conversion behavior for niche strategy/sim titles. Feeds screenshot-build spec, T-S4 page-sequence decision, T-L1 localization-in-image decision, T-V1 trailer key-frame alignment, T-S2 capsule subject alignment. Surfaces patterns on optimal count, slot-1 viewing share, UI-vs-cinematic mix, annotation lift, per-cluster subject choice (dynastic / emergent-story / grand-spatial), animated GIF slot use, in-image localization, and pre/post-launch refresh cadence.

Non-rec disclaimer. Lane surfaces inputs, does not pick. Westley + Design Lane decide which screenshot-build path Ouroboros adopts. Numbers below tagged inline with confidence floor. WebFetch denied at capture time → all figures REPORTED or ESTIMATED from training-data recall, no live verification.

## Method

Sources drawn from training-data recall of:

- Chris Zukowski (HowToMarketAGame, GameDiscoverCo guest posts) screenshot teardowns 2020–2024 — repeated coverage of screenshot ordering, slot-1 weight, capsule/screenshot consistency.
- Simon Carless (GameDiscoverCo newsletter) — wishlist conversion telemetry, store-page interaction patterns, screenshot heatmap reporting from Valve-partner data.
- Steam Business Update talks (Alden Kroll, Tom Giardino, Erik Peterson 2019–2023) — slot-1 importance, capsule-screenshot continuity, the "five screenshots" rule of thumb.
- Niche-launch page archives — RimWorld, Battle Brothers, Wildermyth, Songs of Syx, Manor Lords, Caves of Qud, Frostpunk 2, Crusader Kings 3 store pages as remembered from training data.
- Before/after screenshot threads on r/gamedev, r/IndieDev, TIGSource, and HowToMarketAGame community posts.
- Steam UI shape itself: 5 visible slots above the fold on default desktop, up to 12 slots filled, mobile/Big Picture variations.

WebFetch denied. No 2026 page captures. Anything labeled REPORTED is from training-data recall of an analyst statement; ESTIMATED means derived/extrapolated, not direct quote. Publisher-side A/B test data on screenshots is rarely shared publicly — most A/B claims float at ESTIMATED floor.

## Count optimum

Steam allows up to 20 screenshots; default desktop layout shows 5 above the fold in the main carousel; the "view more" interaction reveals the rest. The 5 / 8 / 12 question is really "where does marginal screenshot value go to zero."

**5 screenshots.** The absolute minimum. Every screenshot in this set carries enormous load; one weak slot drops conversion measurably. Zukowski's repeated guidance: if you only have 5, every one must do a job — genre signal, subject diversity, scale shot, UI shot, money shot. REPORTED. Confidence: REPORTED.

**8 screenshots.** GameDiscoverCo and Zukowski's modal recommendation for indie strategy/sim. Hits the inflection where adding more does not meaningfully improve conversion but does let you cover multi-feature games without overloading any one slot. Eight gives you room for: hook shot, two map shots, one combat/event shot, one UI/depth shot, one chronicle/narrative shot, one variety shot, one closer. REPORTED. Confidence: REPORTED.

**12 screenshots.** Recommended for content-dense games (grand strategy, 4X, deep sim) where players want to see breadth before wishlisting. Crusader Kings 3, Stellaris, RimWorld pages typically use 10–14. Marginal value above 12 is near zero for almost all titles; the carousel becomes a graveyard nobody clicks through. ESTIMATED. Confidence: ESTIMATED.

**Max-attention curve shape.** Slot 1 carries roughly 40–60% of total screenshot attention. Slots 2–5 split most of the remainder. Slots 6–12 receive long-tail attention from already-interested visitors (the wishlist-curious deep-readers). Slots 13+ are effectively invisible except to streamers and reviewers. ESTIMATED (publisher-side telemetry rarely shared, but pattern consistent across Zukowski/GDC public talks).

**Niche-strategy implication.** Ouroboros multi-era + lieutenants + chronicle is content-dense. 8 is the floor; 10–12 is the comfort range. Below 8 you cannot signal 7-era span + lieutenant + chronicle in slot-3-to-5; above 12 the back half does not earn its keep.

## Slot-1 conversion share

Slot 1 is the dominant screenshot. Multiple Valve-public statements and Zukowski teardowns converge on the same shape: the lead screenshot is seen by close to 100% of store-page visitors who don't bounce on capsule; subsequent screenshots are seen by progressively fewer.

**Reported share figures.** Zukowski's repeated estimate is that 60–80% of visitors only ever look at the capsule + slot 1 before deciding to read description or bounce. REPORTED. GameDiscoverCo's heatmap-style reporting suggests slot-1 dwell time is 3–5x slot-2 dwell time on median pages. ESTIMATED. Steam internal telemetry has not been shared publicly with named percentages — the floor is REPORTED via analyst statements, ESTIMATED on exact figures.

**What slot 1 must do.** Genre signal (visitor identifies what they're looking at within 1 second), subject hook (the most desirable thing in the game), and capsule-continuity (visual cohesion with the capsule artwork so the visitor doesn't think they're on the wrong page). Zukowski's repeated formulation: "slot 1 is the wishlist screenshot." REPORTED.

**Niche-strategy slot-1 patterns.** RimWorld slot 1 is a colony in mid-crisis with story-fragment overlay. Manor Lords slot 1 is a sweeping medieval village with crowd. Crusader Kings 3 slot 1 is a portrait scene with dynastic UI visible. Battle Brothers slot 1 is a battle in progress with party UI legible. ESTIMATED (recalled from training-data exposure to those store pages, not freshly verified).

**Ouroboros implication.** Slot 1 must signal multi-era civilizational scope + lieutenant character moment OR chronicle fragment, ideally both. The slot-1 candidate is the single most important art deliverable on the entire page. If slot 1 only shows a single-era space scene, single-era buyers wishlist for the wrong reasons and bounce on screenshot 2 when they see a different era.

## UI-heavy vs cinematic mix

Two competing forces. Cinematic shots sell mood, scale, atmosphere — what the game feels like. UI-heavy shots sell depth — what the game does, how many systems are in play, whether the visitor's strategy-sim itch will be scratched.

**Niche-strategy tolerance for UI.** Higher than average. Strategy/sim buyers actively want to see UI; a screenshot with zero UI on a grand-strategy page reads as "this game is shallow" or "this is not the genre I thought." Crusader Kings 3, Stellaris, Hearts of Iron IV all lead with UI-prominent slots after slot 1. REPORTED.

**Cinematic role.** Slot 1 and one other slot (typically slot 5 or 8 — the "second wind" slot) carry the cinematic load. Cinematic shots establish mood and scale; UI shots establish depth and competence. ESTIMATED on slot-position pattern.

**Mix ratio.** Zukowski's heuristic for strategy/sim: roughly 1 cinematic : 2 UI-bearing across the set. So an 8-screenshot set carries 2–3 cinematic shots and 5–6 UI-bearing shots. REPORTED. The UI in the UI-bearing shots should be legible at thumbnail size, not cluttered — a single readable panel beats five overlapping tooltips.

**Cluster-specific patterns.**

- **Cluster A (dynastic / Crusader Kings 3 audience).** Higher UI tolerance still — character sheets, family trees, decision modals are expected. Cluster A buyers read UI. REPORTED.
- **Cluster B (emergent-story / RimWorld + Wildermyth audience).** Mid UI tolerance — wants to see UI proving system depth, but cinematic story-moment shots carry equal weight. The chronicle-fragment overlay shot bridges both. ESTIMATED.
- **Cluster C (grand-spatial / Stellaris + Manor Lords audience).** Lower UI tolerance — wants the sweep shot, the map, the scale. UI shots are still required but should be at thumbnail-legible density, not maximum density. REPORTED.

**Ouroboros implication.** 8-screenshot set: 2 cinematic (slot 1 + one back-half breath), 6 UI-bearing distributed across lieutenant UI, chronicle UI, map UI, mission UI, command UI. Multi-era variety taken in the UI-bearing slots, not the cinematic ones (cinematic spend on era confusion is too high).

## Annotated vs clean

Text overlays, arrows, callouts, and labels on screenshots. The "annotated" variant adds explanatory text in-image; the "clean" variant lets the screenshot speak for itself.

**Conversion delta — REPORTED.** Zukowski's repeated finding from before/after teardowns: annotated screenshots outperform clean screenshots on wishlist conversion for complex strategy/sim titles, typically by 10–30% in the slot-2-through-5 range. ESTIMATED on exact figure; the directional finding is REPORTED across multiple HowToMarketAGame posts.

**Why annotation works.** Strategy/sim screenshots are dense. Without annotation, a visitor scanning at 1–2 seconds per slot cannot parse what they're looking at. A short annotation ("Your dynasty's last loyal lieutenant turns on you") gives the visitor a story handle and a reason to dwell. REPORTED.

**Annotation pitfalls.** Over-annotation reads as a tutorial slide — bad. Annotation that obscures the underlying art — bad. Annotation that contradicts the trailer voiceover or capsule promise — bad. The sweet spot is one short line of in-world prose or one explanatory pointer per annotated slot, not full paragraphs. ESTIMATED.

**Clean-screenshot defensible cases.** Slot 1 should usually be clean or very lightly annotated — the cinematic load is the job, and any text fights the immediate visual hook. Capsule-art slot, if used, clean. Money-shot late-set slot can be clean. ESTIMATED.

**Niche precedents.** Hooded Horse + Manor Lords use light annotation on a couple of slots. Frostpunk 2 uses heavy annotation/UI capture across most slots. Caves of Qud uses near-zero annotation and lets the UI itself be the annotation. RimWorld uses light story-fragment overlays on event screenshots. ESTIMATED on per-title pattern.

**Cluster split.** Cluster A (dynastic) tolerates more text annotation — buyers read text. Cluster B (emergent-story) wants in-world prose annotation (chronicle-fragment shape) more than UI annotation. Cluster C (grand-spatial) tolerates the least annotation — wants the sweep clean. ESTIMATED.

**Ouroboros implication.** 8-set: slot 1 clean (or one-line tagline only), slots 2–6 mix of UI-natural-annotation (the UI itself labels what's happening) and one-line in-world prose annotation on chronicle/lieutenant moment shots, slot 7–8 back to clean for breath shots. Chronicle-fragment overlay shots are a natural Ouroboros fit and align with the Cluster B pattern.

## Per-cluster subject patterns

The three audience clusters identified in `docs/research/topics/audience_overlap_map.md` (Cluster A dynastic, Cluster B emergent-story, Cluster C grand-spatial) each have characteristic subject patterns observed on successful niche-strategy store pages.

**Cluster A — Dynastic (Crusader Kings 3 audience).** Characteristic subjects:

- Portrait shot of named character with stats/relations/traits visible. Crusader Kings 3 slot pattern. REPORTED.
- Family-tree or genealogy shot showing multi-generational sweep. REPORTED.
- Character event modal — a decision point with consequence text. REPORTED.
- "Court" or "council" scene with named lieutenants visible — the Lieutenant System pivot enables this on the Ouroboros page. ESTIMATED.
- Death/succession dramatic moment. REPORTED.

Subject density should foreground individual named humans. The screenshots must feel like the game is about people, not abstract numbers.

**Cluster B — Emergent-story (RimWorld / Wildermyth audience).** Characteristic subjects:

- Story-moment shot — a single dramatic scene with chronicle/log/narrative text overlay. RimWorld's "your colonist died of heatstroke after refusing to wear the parka" pattern. REPORTED.
- Character-moment shot — close on a single character or small group at a turning point. Wildermyth's hand-drawn character panels. REPORTED.
- Consequence shot — visible aftermath of a player decision, ideally with timeline/log fragment. ESTIMATED.
- Mid-crisis shot — colony/civilization under threat, story-stakes legible. REPORTED.
- Chronicle/journal page shot — the player's accumulated history as artifact. ESTIMATED. Direct Ouroboros fit per bible chronicle spoke.

Subject density should foreground specific named events with story handles, not statistics.

**Cluster C — Grand-spatial (Stellaris / Manor Lords audience).** Characteristic subjects:

- Sweep shot — full map or wide vista showing scale. Manor Lords aerial village shot. REPORTED.
- Border/territory shot — political map with player's domain visible. Stellaris galaxy map. REPORTED.
- City/settlement scale shot — population/economy visible. Manor Lords' market square pattern. REPORTED.
- Combat-at-scale shot — armies clashing across terrain rather than tactical close-up. ESTIMATED.
- "Zoom" shot — close detail showing depth at small scale, paired with sweep shot. ESTIMATED.

Subject density should foreground space, terrain, and visible reach of the player's domain.

**Ouroboros multi-era subject constraint.** Bible context: 7-era span. Screenshot mix must show multi-era without confusing single-era-buyers. Pattern from training-data on multi-era titles (Civilization series, Humankind): use the cinematic slot to show one signature era (the most visually arresting one — likely an interstellar or post-collapse era for Ouroboros), then dedicate 2–3 UI-bearing slots to subtly different eras, with era-clarity in either UI text or a small era-label corner annotation. ESTIMATED. The risk pattern from Humankind's launch page: showing 6 eras across 8 screenshots reads as "I don't know what this game is" to scanners. The mitigated pattern: lead with the era that wishlists best for the primary tribe (likely the Foundation-register interstellar era given bible primary-tribe Foundation/hard-SF secondary), use UI continuity (same UI shell across eras) to signal that era is a feature, not a confusion. ESTIMATED.

**Lieutenant System enables Cluster A patterns.** Per bible context the Lieutenant System unlocks portrait + character-event + court-scene shots that were not viable pre-pivot. Cluster A pattern adoption now possible. The chronicle is a bible feature → Cluster B chronicle-fragment shot also viable. Cluster C grand-spatial is the bible's existing strength via map/border/civilization visualization. Ouroboros is one of the few titles in the niche-strategy space that can credibly run all three cluster patterns. ESTIMATED. The downside: subject diversity must not become subject confusion — slot 1 has to commit to one cluster's hook even as slots 2–8 mix patterns.

## Animated GIF slots

Steam supports animated screenshots in the form of MP4-backed slots that loop silently. Functionally these are short GIFs in user-facing terms.

**Conversion impact — REPORTED.** Multiple Zukowski + Carless statements: animated slots, especially in slot 1 or slot 2, lift wishlist conversion by 10–25% when the motion shows something the static shot cannot. ESTIMATED on exact figure; directional finding REPORTED.

**Why GIFs help.** Strategy/sim screenshots often fail to convey that the game is alive. A 4-second loop showing a battle unfolding, a city growing, a lieutenant turning toward camera, or a chronicle line typing in solves the "is this a screenshot or a board game" problem in one slot. REPORTED.

**Tradeoffs.**

- File-size cost — Steam capsule-loaded animated slots cost real CDN time, slowing page load on slower connections. Steam's own slot caps mitigate this but a heavy GIF can still hurt mobile. ESTIMATED.
- Production cost — capturing a clean 4–6 second loop that reads at thumbnail size is substantially harder than capturing a still. ESTIMATED.
- Looping pitfalls — a poorly looped GIF (visible jump-cut, action mid-frame at the loop point) reads as cheap and hurts. REPORTED.
- Slot-1 GIF risk — if slot 1 is animated and the loop is busy/confusing, you lose more than a static slot 1 would have lost. ESTIMATED.

**Niche precedents.** Manor Lords used animated slots prominently at launch. Frostpunk 2 used animated slots showing weather/city evolution. RimWorld's page used static shots historically — generation of audience already knew the game; less GIF dependency. ESTIMATED.

**Ouroboros implication.** 1–2 animated slots is the modal recommendation for niche-strategy 2026 launches. Strong candidates: a chronicle line typing across the screen (Cluster B alignment), a multi-era era-transition cut (handles the multi-era confusion problem by making era progression visible), or a lieutenant turning toward camera with a stat-flicker (Cluster A alignment). ESTIMATED — the chronicle-typing GIF is novel for the niche and has highest differentiation potential.

## In-image localization

Annotated screenshots contain text. If the text is in English only, the localized Steam pages (German, French, Spanish, Russian, Simplified Chinese, etc.) lose the annotation lift on visitors whose first language is not English.

**Cost vs lift.** Localizing in-image text means producing N variants of each annotated screenshot (one per supported language). For 5 annotated slots × 8 languages = 40 variants. Substantial art ops cost. ESTIMATED.

**Lift figure — ESTIMATED floor.** No reliable public publisher-side A/B data on per-language annotated-screenshot lift. Carless has discussed localization-of-marketing in general terms but specific screenshot-localization conversion deltas are not in the public record this lane can recall. ESTIMATED floor: 5–15% wishlist conversion lift in localized markets when annotation is localized vs English-only, based on the general localized-marketing lift figure of approximately 20–30% applied with discount to the screenshot-text subset. Confidence: ESTIMATED — directional only.

**Cluster patterns.** Cluster A (dynastic, broadly distributed audience) benefits most from localization — Crusader Kings 3 audience is heavily international. Cluster B (emergent-story) chronicle text is often poetic/voice-driven and harder to localize well; either commit to full localization or leave English-only with subtitle/caption underneath. Cluster C (grand-spatial) has less in-image text to localize. ESTIMATED.

**Niche precedents.** Crusader Kings 3 localized screenshot text. Manor Lords used relatively text-light screenshots. RimWorld did not heavily localize in-image text. Frostpunk 2 localized prominently. ESTIMATED.

**Ouroboros decision shape.** The decision feeds T-L1. Two viable paths surfaced (lane does not pick): (a) commit to full in-image localization for 5–8 supported languages from launch, accepting the art-ops cost; (b) keep screenshot annotation English-only and lean on Steam's per-language description field for the depth-conveyance work. Path (a) is closer to the Frostpunk 2 / Crusader Kings 3 playbook; path (b) is closer to the RimWorld / Caves of Qud playbook. The choice depends on which clusters the screenshot-build spec prioritizes and how much chronicle-fragment text appears in annotation.

## Refresh cadence

Screenshots are not static across the page's lifetime.

**Pre-launch iteration.** Zukowski's repeated guidance: refresh screenshots every 4–8 weeks during the pre-launch wishlist-accumulation phase. Each refresh tests new subjects, new annotation styles, new slot orders against the conversion baseline of the previous set. ESTIMATED on cadence; the underlying "iterate, don't set-and-forget" finding is REPORTED. Wishlist-velocity changes after a screenshot refresh are observable in the Steam partner dashboard and used to validate or revert.

**Pre-launch milestones for refresh.** Initial Coming Soon page → first refresh after first trailer cut → refresh at each Next Fest entry → refresh after any major bible/scope shift visible to art → refresh ~2 weeks before launch with the launch screenshot set. ESTIMATED. The Lieutenant System pivot is a refresh-triggering event for Ouroboros — the pre-pivot screenshot set, if any, will not match the post-pivot product.

**Post-launch sale-event refresh.** Steam sale events (Summer Sale, Autumn Sale, Winter Sale, genre-specific events like Strategy Fest) drive elevated impressions. Many publishers swap to a sale-tuned screenshot set during these windows — typically rotating in a newer screenshot that highlights post-launch content updates and pushing the older "launch hero" slot down. ESTIMATED. Sale-event screenshot refresh lift is in the 5–15% conversion-during-sale range per Zukowski. ESTIMATED.

**Long-tail refresh.** Major content updates, DLC drops, and version milestones each warrant a screenshot refresh. The page's screenshots should reflect what the current build looks like, not the launch build. RimWorld's Steam page has cycled screenshots multiple times across its lifetime. REPORTED.

**Ouroboros implication.** Plan for at least 3 pre-launch screenshot iterations and a sale-event refresh playbook from day one. The art-ops budget should not be "one screenshot set and done" — it should be a screenshot pipeline.

## Cross-cutting findings

- Slot 1 is the single highest-leverage art deliverable on the entire store page. 40–60% of visitors only ever see slot 1. ESTIMATED but consistently reported across analyst sources.
- 8 screenshots is the modal niche-strategy count; 10–12 is the content-dense ceiling; <5 is malpractice for the genre. REPORTED.
- Annotated screenshots outperform clean screenshots in slots 2–5 for strategy/sim, by ESTIMATED 10–30%. Slot 1 typically clean or one-line only.
- Animated slots lift conversion by ESTIMATED 10–25% when the motion shows something the static cannot — chronicle-typing or era-transition cuts are strong novel candidates for Ouroboros.
- Multi-era games face a confusion-vs-feature tradeoff. Mitigation pattern: UI shell continuity across eras + one signature-era cinematic + small era-label annotations.
- Lieutenant System pivot + chronicle feature together unlock all three cluster patterns (A dynastic, B emergent-story, C grand-spatial) for Ouroboros simultaneously — rare in the niche.
- Refresh cadence is iterative not one-and-done. Pre-launch every 4–8 weeks; sale-event swaps; post-launch on each major content drop.

## Conflict surfaced

Check vs bible art directives. Two latent conflicts surfaced; lane does not pick.

- **Multi-era subject spread vs primary-tribe focus.** Bible primary tribe is generational/legacy; secondary is Foundation/hard-SF. Slot-1 cinematic must commit to one era. Showing 7 eras across 8 slots risks reading as identity confusion. If the bible art directive elsewhere mandates equal-era representation in marketing, that conflicts with the slot-1 single-era-commitment pattern. Status: not verified against bible art spoke at capture time. FLAG for design.
- **Chronicle-fragment overlay vs "in-world voice" purity.** Cluster B chronicle-fragment screenshots overlay chronicle prose on the screenshot. If the bible has a directive that chronicle text appears only in-engine, never as marketing overlay, that constrains the strongest novel Ouroboros screenshot pattern. Status: not verified. FLAG for design.

## Caveats and confidence

Tag distribution across this brief:

- REPORTED ~ 40% (Zukowski directional findings, GameDiscoverCo public talks, Steam Business Update guidance).
- ESTIMATED ~ 55% (exact conversion deltas, per-cluster pattern fit, Ouroboros-specific implications, niche precedent recall).
- VERIFIED ~ 0% (no live store-page captures this session due to WebFetch denial).
- IGNORE ~ 5% (anecdotal/r-gamedev style claims kept directional only).

Specific caveat: **screenshot A/B publisher-side data sits at ESTIMATED floor.** Valve does not publicly release per-slot conversion telemetry; publisher-side A/B testing on screenshots is rarely shared in named-number form. All exact percentages in this brief should be treated as directional only and validated against Ouroboros's own Steam partner dashboard once the page is live and instrumented.

Recall caveat: training-data exposure to specific store pages (RimWorld, Manor Lords, Crusader Kings 3, Frostpunk 2, Caves of Qud, Wildermyth) is from pre-2026 snapshots. Pages have likely refreshed since. Any "this title's slot N showed X" claim is at ESTIMATED floor.

## Feeds Design Lane

- **Screenshot-build spec.** Slot count, slot-1 commitment, UI/cinematic mix, annotation policy, GIF count, era-spread plan, chronicle-fragment overlay decision.
- **T-S4 page sequence.** Order of screenshot slots, hand-off from capsule to slot 1 to back-half.
- **T-L1 localization-in-image decision.** Whether to localize in-image annotation across N languages.
- **T-V1 trailer key-frame alignment.** Trailer cuts that match screenshot subjects (capsule + slot 1 + trailer hero shot should triangulate).
- **T-S2 capsule subject alignment.** Capsule and slot 1 should be visually cohesive — same era, same primary subject family, same color register.

## Open questions for further research

- Per-language screenshot-annotation A/B data — does anyone publish named-number lift for in-image localization? Currently ESTIMATED floor only.
- Chronicle-fragment-overlay precedents — has any title used a typed-chronicle animated slot? Closest comp is RimWorld's static event-log overlays; no recalled GIF-based chronicle precedent.
- Lieutenant-portrait subject pattern hit-rate for non-licensed (no-pre-existing-IP) titles — Crusader Kings 3 audience is established but does a fresh-IP lieutenant-portrait shot convert?
- Multi-era page-presentation A/B data — does the Civilization VII or Humankind launch page have any published telemetry on era-spread vs era-focus screenshot mixes?
- Sale-event screenshot-refresh lift figures — Zukowski has discussed; named-number publisher data sparse. Worth a targeted dig.
- Big Picture / Steam Deck screenshot rendering — slot order and thumbnail rendering differ in Deck mode. Audience overlap with Ouroboros primary tribe likely non-trivial.

## Sources

- Chris Zukowski — HowToMarketAGame blog posts and GameDiscoverCo guest posts on screenshot ordering, slot-1 importance, annotation, refresh cadence. Training-data recall, no 2026 verification.
- Simon Carless — GameDiscoverCo newsletter, Valve-partner heatmap reporting on store-page interaction patterns. Training-data recall.
- Alden Kroll / Tom Giardino / Erik Peterson — Steam Business Update talks 2019–2023 on store-page conventions, screenshot slot counts, capsule-screenshot continuity. Training-data recall.
- Niche-strategy store pages — RimWorld, Battle Brothers, Wildermyth, Songs of Syx, Manor Lords, Caves of Qud, Frostpunk 2, Crusader Kings 3, Stellaris, Workers & Resources. Training-data recall pre-2026 snapshots.
- r/gamedev, r/IndieDev, TIGSource, HowToMarketAGame community before/after screenshot threads. Training-data recall, anecdotal floor.
- Cross-reference inputs: `/Users/westley/ouroboros/docs/research/topics/audience_overlap_map.md` (cluster identity); `/Users/westley/ouroboros/docs/bible/game_bible.md` (7-era span, primary tribe, lieutenant pivot, chronicle feature).

All sources flagged: training-data floor at capture time. No WebFetch verification this session. Lane disclaimer: surfaces inputs, does not pick.
