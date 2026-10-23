---
name: Primary-Tribe Psychographic Profile
description: Per-title review-theme analysis for CK3 + Wildermyth + Battle Brothers + FoG: Empires intersection; feeds WS5 progression forks, WS4 multiplayer forks, all bible_monetization marketing copy.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 1 capture
---

# Primary-Tribe Psychographic Profile

## What this brief is

Per-title psychographic snapshot of four anchor games in Ouroboros' primary tribe: Crusader Kings 3 (CK3), Wildermyth, Battle Brothers (BB), Field of Glory: Empires (FoG:E). Sharpens lieutenant_pivot_niche_brief.md's audience line from one-paragraph generality into per-title evidence — what each tribe-fragment raves about, complains about, bounces on, "bought for X" cites, and "wish this game did X" requests.

Brief feeds: WS5 progression forks (run shape, save model, lieutenant promotion granularity), WS4 multiplayer remaining forks (per-mission co-op vs persistent shared world vs async), bible_monetization marketing copy (capsule, Steam tags, DLC framing), brand positioning (T-B1 follow-up topic).

**Does NOT recommend a pick.** Research Lane surfaces inputs; Design Lane picks. No "Ouroboros should do X" statements below. Conflict-flag section only flags collisions w/ existing bible directives; doesn't resolve them.

## Method

Sources scanned (training-data floor, no live fetch):
- Steam review themes (top-voted reviews + curator quotes seen during training)
- Steam tags + tag-overlap signals
- Press coverage (Rock Paper Shotgun, PC Gamer, Eurogamer reviews + retrospectives)
- Subreddit themes (/r/CrusaderKings, /r/wildermyth, /r/BattleBrothers, /r/grandstrategy + minor presence /r/FieldOfGlory)
- YouTube creator framings (Quill18, SsethTzeentach, Many a True Nerd, Lionheart, ItalianSpartacus for FoG:E)

**Exclusions:** No live Steam scrape (WebFetch disabled). No SteamDB CCU pulls. No 2026 review-bombing event tracking. No DLC-specific review-bomb episodes (e.g., CK3 Tours & Tournaments backlash specifics treated coarsely).

**Confidence calibration.** WebFetch denied → floor REPORTED. VERIFIED reserved for verbatim quotes recalled from training data w/ high confidence on wording. Most claims REPORTED or ESTIMATED. AMBIGUOUS where multiple framings co-exist in source pool. Flag re-capture w/ live queries when WebFetch returns.

## CK3 review themes

**Positive themes (top 5).**

1. **Dynasty-as-protagonist hook.** Reviews recur on "my characters die but family continues" as core fantasy. Phrasing variants: "the king is dead, long live the king," "lost my favorite ruler and got attached to his daughter instead," "first game where I cared about a character's grandchild." REPORTED.
2. **Emergent stories.** "Crusader Kings is a story generator" — common refrain across reviews + RPS coverage. Players cite specific anecdotes ("my chancellor seduced my wife and I had to fake my own death to escape an inheritance war") as the value proposition rather than systems. REPORTED.
3. **Character schemes + interpersonal layer.** Murder plots, seduction, fostering, kidnapping — players cite "playing the politics of the bedroom" as differentiator from EU4/HoI4. REPORTED.
4. **Accessibility relative to Paradox catalog.** "Easiest Paradox game to start" cited as positive ~constantly. Tutorial + tooltip system praised vs EU4/Vic3. REPORTED.
5. **Modding ecosystem.** Game of Thrones mod, Elder Kings, Anbennar — cited as "game has 5 games inside it." Large fraction of long-tail playtime attributed to mods. REPORTED.

**Negative themes (top 5).**

1. **DLC monetization fatigue.** Tours & Tournaments, Northern Lords, Royal Court — recurring complaint "feature should've been in base game." Paradox DLC model is structural risk-flag for Ouroboros' DLC-per-era plan. REPORTED. **Structural — Ouroboros faces same trap.**
2. **Late-game tedium / blob problem.** Once dynasty controls 1/3 of map, gameplay collapses to "click button, wait, click button." Common bounce point ~50hr mark. REPORTED. **Structural — applies if Ouroboros runs trend toward unopposed dominance.**
3. **Lifestyle tree imbalance.** "Stewardship/Intrigue obvious meta-pick, Learning/Diplomacy weak" — players cite same complaint across patches. REPORTED. Avoidable if Ouroboros lieutenant trait/skill design is symmetric.
4. **Combat is bad / battles are auto-resolve.** Players who came from Total War expect tactical battles; CK3 battles are abstract dice + stack math. Splits audience — half want CK3 to stay this way, half want Total War battles. REPORTED, AMBIGUOUS. **Direct hit on Ouroboros lieutenant-tactical pivot — both factions exist in same audience.**
5. **UI overwhelm / nested menus.** Especially Royal Court + Tours layered into already-busy character screen. REPORTED. Avoidable.

**Bounce themes.**

- Refund <2hr: "Too much to read, didn't grab me." Tutorial overwhelm. REPORTED.
- Refund <24hr: "Got my character to 60, died, his son was incompetent, lost interest." Heir transition is a bounce point. REPORTED.
- Never-relaunch: "Mid-game blob, lost focus, never came back." 80-150hr drop-off common. REPORTED.

## Wildermyth review themes

**Positive themes (top 5).**

1. **Procedural character bonding.** "I got attached to my characters in a way no other game has done." Recurring almost-universal positive. Transformations (eyes become starlight, arm becomes wood) cited as identity-attaching events. REPORTED, near-VERIFIED frequency.
2. **Generational handoff between chapters.** Heroes age, become legends, retire to wall; their children/apprentices take up the fight. "Legacy" mode — bringing previous campaign heroes into new campaigns — universally praised. REPORTED. **Direct fit for Ouroboros generational handoff.**
3. **Hand-illustrated comic-book art style.** "Looks like a fantasy storybook." Differentiator from typical CRPG/tactical art. REPORTED.
4. **Choice-driven narrative events.** Each chapter has branching event nodes; players cite "my choices actually mattered, not Telltale-fake-choice." REPORTED.
5. **Short campaign length (8-12hr per campaign).** Praised as "fits in a weekend, replayable." Differentiator from CK3's 80hr campaign. REPORTED. **Direct WS5 fork-relevant — run shape preference.**

**Negative themes (top 5).**

1. **Tactical combat is shallow / repetitive.** Same XCOM-lite grid combat across 3 chapters; combat doesn't evolve. REPORTED. **Structural for Ouroboros if lieutenant-tactical is single-mechanic.**
2. **Event pool exhausts after 3-5 campaigns.** "Saw the same events repeat" — narrative content cap hit by power users. REPORTED. **Structural — narrative scale problem hits any chronicle-driven game.**
3. **Difficulty curve uneven.** "Easy mode trivial, hard mode brutal, nothing in middle." REPORTED. Avoidable.
4. **No real overworld strategy layer.** Map is event-node graph, not simulated. "Wish there was a world to defend, not just nodes." REPORTED. **Ouroboros has this — opportunity, not risk.**
5. **Endgame anticlimactic.** Final chapter often "kill big bad" — doesn't match build-up of character investment. REPORTED.

**Bounce themes.**

- Refund <2hr: rare for Wildermyth — 95% positive review ratio suggests bounce population small. ESTIMATED.
- Refund <24hr: "Combat felt thin once I saw the systems." REPORTED.
- Never-relaunch: "Loved my first campaign, second felt like reruns." REPORTED.

## Battle Brothers review themes

**Positive themes (top 5).**

1. **Permadeath roster ownership.** "Lost Hans the two-handed expert, cried." Per-mercenary attachment via individualized backgrounds + traits + nicknames. REPORTED, near-VERIFIED frequency. **Direct fit for Ouroboros lieutenant permadeath stakes.**
2. **Brutal difficulty / no save-scumming respected.** Ironman is default expectation in community. "Game respects you enough to let you fail." REPORTED.
3. **Strategic-tactical loop.** Contracts on overworld feed tactical battles; both layers serve each other. Closest precedent for Ouroboros' overworld→tactical handoff. REPORTED.
4. **Background variety + emergent character identity.** "My poacher with quick-hands trait + bow + crippling-strike build became the company's archer-captain." Player-named character archetypes recur. REPORTED.
5. **DLC respected — Beasts & Exploration, Warriors of the North, Blazing Deserts.** Each adds content w/o invalidating base. Counter-example to CK3's DLC complaint pattern. REPORTED. **DLC-per-era model precedent.**

**Negative themes (top 5).**

1. **UI is functional, ugly.** "Looks like a 2005 game." Bounces buyers expecting polish. REPORTED. Structural to the BB aesthetic — avoidable for Ouroboros if budget allows.
2. **Late-game (Day 200+) tedium.** Once company is strong, contracts become loot-grind. REPORTED. **Structural risk for any roster-progression game.**
3. **Difficulty too punishing in early game.** "Lost first 3 mercs in starter fight, restart simulator." REPORTED. Avoidable via difficulty curve.
4. **No campaign / no narrative arc.** Sandbox forever; some players want story. REPORTED, AMBIGUOUS — other faction explicitly buys for sandbox-no-story.
5. **Tactical RNG frustration.** Hit chances feel "XCOM bad" — misses at 90% etc. REPORTED.

**Bounce themes.**

- Refund <2hr: "Lost all my dudes fight 2, this is too hard." REPORTED.
- Refund <24hr: "Tutorial-less, didn't understand systems, gave up." REPORTED.
- Never-relaunch: "Got company to Day 100, ran out of mid-game content drive." REPORTED.

## Field of Glory: Empires review themes

**Positive themes (top 5).**

1. **Decay mechanic = cultural decline.** Empires literally rot from within at scale. "First game where dominance is a problem." Unique vs Civ/EU4. REPORTED. **Direct fit for Ouroboros collapse-rebuild run shape (Tier-1 uncontested).**
2. **Battle handoff to FoG II.** Cross-game tactical handoff novel + appreciated by hardcore. REPORTED. **Precedent for tactical-layer handoff if Ouroboros considers split-product structure.**
3. **Historical authenticity / Mediterranean classical antiquity setting.** Reviews praise "this is what classical-era strategy should be." REPORTED.
4. **Auto-resolve battles by default.** "I can play strategy without doing tactics every fight." REPORTED, AMBIGUOUS — splits w/ negative theme #1.
5. **Wide nation roster (70+ playable).** Replayability via faction choice. REPORTED.

**Negative themes (top 5).**

1. **Spreadsheet-feel UI.** "Like playing Excel: The Game." REPORTED. Structural to FoG aesthetic; bounces accessibility-seekers.
2. **Tutorial-less / opaque mechanics.** "Decay punished me for 3 hours and I never understood why." REPORTED. **Direct risk for Ouroboros if collapse-rebuild mechanics aren't legible.**
3. **No real diplomacy.** Treaties shallow vs EU4. REPORTED.
4. **Small audience / low review count (~1,000-2,000).** Discoverability problem. REPORTED.
5. **Battles in companion product = paywall annoyance.** Some buyers expected battles in-game. REPORTED. **DLC-per-era warning.**

**Bounce themes.**

- Refund <2hr: "UI too dense, couldn't engage." REPORTED.
- Refund <24hr: "Lost first empire to decay, didn't understand, refunded." REPORTED.
- Never-relaunch: low long-tail; FoG:E is short-burn for niche audience. ESTIMATED.

## Cross-cutting findings

**1. "World keeps moving" / "history persists" is a near-universal "bought for X" cite across all four titles.** CK3 reviews phrase it as "kingdoms rise and fall around you." Wildermyth as "the world remembers your heroes." BB as "the world doesn't care if you die." FoG:E as "empires actually decay." Frequency: high across CK3 + FoG:E, medium-high BB, present-but-secondary Wildermyth (which is more chapter-bounded). REPORTED, high confidence. **Direct match for Ouroboros' single strongest design tether per lieutenant_pivot_niche_brief.md.**

**2. UI / tutorial complaints recur across all 4 titles → structural Ouroboros risk.** Every game in primary tribe has UI bounces. CK3 mitigated via tooltip layer; BB embraced functional-ugly; Wildermyth solved via comic-art framing; FoG:E unsolved. Ouroboros must explicitly budget tutorial + UI legibility — generational/lieutenant systems are MORE complex than any of these four. REPORTED.

**3. "I wish this game did X" — bible alignment check.**
- "Wish CK3 had real battles" → bible says yes (lieutenant tactical layer). ALIGNED.
- "Wish Wildermyth had overworld strategy" → bible says yes (generational sim). ALIGNED.
- "Wish BB had narrative arc / generational progression" → bible says yes (chronicle + collapse-rebuild). ALIGNED.
- "Wish FoG:E had legible decay" → bible has collapse-rebuild explicit; legibility is design problem not concept gap. ALIGNED w/ caveat.
- "Wish CK3 had non-blob endgame" → bible's Tier-1 uncontested run shape addresses via collapse-rebuild. ALIGNED.
- "Wish all of these had hidden-society / Foundation politics" — NOT in any of the four explicitly. NEW ground for Ouroboros via Foundation thematic differentiator. ALIGNED.
- "Wish CK3 lieutenants/courtiers had real personality" → bible's named-lieutenant pivot directly addresses. ALIGNED. **Strong fit.**

**4. Tribe intersection — partially unified.** ESTIMATED:
- CK3 ∩ Wildermyth ≈ medium overlap (both generational, different scale; ~30-40% Wildermyth players own CK3 estimated).
- CK3 ∩ BB ≈ medium overlap (Paradox + tactical-curious crowd; ~25-35% BB players own CK3 estimated).
- CK3 ∩ FoG:E ≈ high overlap (grand-strategy diehards; ~50%+ FoG:E players own CK3 estimated).
- BB ∩ Wildermyth ≈ low-medium (different combat philosophy; ~15-25% estimated).
- BB ∩ FoG:E ≈ low (different scale; ~10-20% estimated).
- Wildermyth ∩ FoG:E ≈ very low (different audiences entirely; <10% estimated).
- All-4 intersection: small, ESTIMATED 5-15% of total reachable. The "passionate-niche" target is the union not the intersection.

**5. Pacing expectations diverge sharply across the four.** AMBIGUOUS:
- CK3: 50-200hr campaigns; long sessions (2-6hr).
- Wildermyth: 8-12hr per campaign; medium sessions (1-3hr); designed for finishing.
- BB: 40-150hr campaigns; medium-long sessions (2-4hr).
- FoG:E: 20-60hr campaigns; medium sessions (1-3hr).
- **WS5 fork relevance:** primary tribe has NO unified pacing expectation. Ouroboros' collapse-rebuild Tier-1 run shape lands inside the CK3/BB long-campaign expectation but outside Wildermyth chapter-bounded shape. Worth surfacing as explicit fork.

**6. Save-scumming culture varies.** BB community: ironman-default, save-scum-frowned. CK3 community: mixed, ironman optional. Wildermyth: permadeath baked in but rewind tolerated. FoG:E: save-anytime no stigma. **WS5 save-model fork directly relevant.**

**7. Multiplayer expectations.** None of the four primary tribe games have strong MP cultures. CK3 has small co-op cult; BB single-player only; Wildermyth has multiplayer co-op (3-player) but low usage; FoG:E single-player. **WS4 MP forks: primary tribe does NOT demand MP — opportunity to ship SP-first w/o backlash.** REPORTED.

**8. Tag-distribution paragraph.** Of ~70 inline tags in this brief: roughly 70% REPORTED (training-data-derived patterns recalled w/ high confidence in pattern, lower confidence in exact wording), 20% ESTIMATED (intersection percentages + bounce-population shapes inferred from review-count + rating signals, no live data), 8% AMBIGUOUS (split-audience cases like CK3 combat preferences + FoG:E auto-resolve), <2% VERIFIED (no live Steam-text capture in env; verbatim recall floor too low to claim).

## Conflict surfaced

Checking primary-tribe expectations against bible_monetization.md L274 ("Free to play" tagline) and L292 (Fortnite reference):

- **L274 "Free to play" tagline collision:** Primary tribe pays $25-35 buy-once-base + DLC. Free-to-play framing collides w/ tribe expectation. CK3 audience experienced Paradox F2P-style live-service expansion + bristled; BB audience explicitly buys to AVOID F2P; FoG:E audience pays premium for niche content. If "Free to play" tagline is verbatim in marketing, expect Steam review backlash from primary tribe. **CONFLICT FLAGGED. Bible authority resolves — Research Lane only surfaces.**
- **L292 Fortnite reference collision:** Primary tribe psychographic is anti-Fortnite-aesthetic. None of CK3/Wildermyth/BB/FoG:E community discourse positions Fortnite favorably; references in negative reviews typically as pejorative ("don't make this Fortnite"). Bible's Fortnite reference may be invoking monetization mechanics (battle pass, season, cosmetic) which CAN coexist w/ buy-once base, but framing risk is high. **CONFLICT FLAGGED for tone/framing not necessarily mechanics. Bible authority resolves.**

No additional fresh conflict beyond #2 (DLC monetization fatigue) and #3 (UI/tutorial bounce) already noted in CK3/FoG:E review themes.

## Caveats and confidence

Distribution restated: ~70% REPORTED, ~20% ESTIMATED, ~8% AMBIGUOUS, <2% VERIFIED. WebFetch denied → zero live Steam-review text captured verbatim in this brief. All review-theme statements are training-data patterns, not 2026-current scrape. Re-capture w/ live Steam + SteamDB queries flagged in Sources.

Known unknowns:
- 2026 review-bombing events on any of the four titles not tracked.
- Post-2024 DLC reception details (e.g., CK3 Wandering Nobles, BB modern DLC) coarse-resolution only.
- Exact subscriber counts for /r/CrusaderKings, /r/wildermyth, /r/BattleBrothers, /r/grandstrategy in 2026 — cited estimates in lieutenant_pivot brief; not refreshed here.
- Wildermyth Legacy-mode usage rate vs first-campaign-only — anecdotal evidence only.
- FoG:E exact owner count + ROI — Slitherine doesn't publish.
- Steam-curator coverage overlap across the four — not analyzed.

Brief is an interpretation. Other valid interpretations of same source pool exist.

## Feeds Design Lane

Specific forks this brief feeds:

- **WS5 fork 2 (run shape granularity):** primary tribe pacing diverges (CK3 long, Wildermyth chapter-short, BB medium-long, FoG:E medium). Brief surfaces but doesn't resolve.
- **WS5 fork 5 (save model):** primary tribe save-scumming culture varies (BB ironman, CK3 mixed, Wildermyth permadeath+rewind, FoG:E save-anytime). Cross-ref with `docs/legacy/topics/blue_ocean_run_shape.md` if collapse-rebuild commits a single save model.
- **WS5 fork 6 (lieutenant promotion/death granularity):** BB permadeath roster is closest precedent; CK3 dynasty is parallel pattern; Wildermyth retirement-to-wall is third option. All three viable; tribe doesn't unify on one.
- **WS5 fork 9 (chronicle scale + content cap):** Wildermyth event-pool exhaustion at 3-5 campaigns is direct warning for Ouroboros chronicle if not procedurally regenerable. Bible's chronicle spec must address.
- **WS4 MP forks:** primary tribe is SP-default. Opportunity to ship SP-first w/o backlash. Per-mission co-op (BB-style imaginary), persistent shared world, async — none of the four have strong async culture; CK3 + Wildermyth co-op precedents exist but small.
- **bible_monetization marketing copy:** "Free to play" tagline (L274) + Fortnite reference (L292) surface as conflicts. DLC-per-era model has BB-positive precedent + CK3-negative precedent; framing matters.
- **Brand positioning (T-B1 follow-up):** sharpens "commander not king" + Foundation-thematic positioning against per-title tribe-fragment expectations. Primary tribe is anti-AAA-aesthetic, pro-authorial-voice, tolerates rough UI for simulation depth, pays $25-35 for genuine differentiation. Capsule copy and Steam-tag selection should reflect.

## Open questions for further research

- Live Steam review text capture (top 20 helpful + top 20 negative per title) — REPORTED claims need verbatim verification.
- 2026 subreddit subscriber counts + recent thread-velocity for /r/CrusaderKings, /r/wildermyth, /r/BattleBrothers, /r/grandstrategy.
- Wildermyth Legacy-mode telemetry — what % of players use carry-over feature? Direct read on generational-handoff demand.
- DLC review-bomb pattern frequency for CK3 vs BB — quantify "fatigue vs respect" split for Ouroboros DLC-per-era risk modeling.
- Foundation TV-show audience size + spillover wishlist activity on Foundation-adjacent Steam pages 2024-2026.
- Steam-tag-overlap analysis for current Ouroboros tag candidates (Grand Strategy + Sci-fi + Simulation + Procedural Generation + Narrative + Story Rich + Generations + Strategy).

## Sources

Training-data-only — flag for re-capture w/ live Steam/SteamDB queries when WebFetch returns.

- Steam store pages (recalled from training):
  - Crusader Kings III — https://store.steampowered.com/app/1158310/
  - Wildermyth — https://store.steampowered.com/app/763890/
  - Battle Brothers — https://store.steampowered.com/app/365360/
  - Field of Glory: Empires — https://store.steampowered.com/app/1011390/
- Steam community hubs (themes recalled, not verbatim).
- Subreddit themes (training-data patterns, no 2026 refresh):
  - /r/CrusaderKings, /r/wildermyth, /r/BattleBrothers, /r/grandstrategy, /r/paradoxplaza
- Press coverage referenced from training:
  - Rock Paper Shotgun CK3 review + retrospectives
  - Eurogamer CK3 + Wildermyth coverage
  - PC Gamer Battle Brothers reviews + DLC coverage
  - Wargamer / Strategy Gamer FoG:E coverage
  - Wildermyth (Wikipedia) — https://en.wikipedia.org/wiki/Wildermyth
- YouTube creator framings (training-recall, no verbatim transcripts):
  - Quill18 CK3 + FoG:E
  - SsethTzeentach Battle Brothers + CK3
  - Many a True Nerd CK3
  - ItalianSpartacus FoG:E
  - Lionheart BB
- Cross-reference within Ouroboros docs:
  - `docs/legacy/topics/lieutenant_pivot_niche_brief.md` — parent brief; this one sharpens its audience line
  - `docs/legacy/topics/blue_ocean_run_shape.md` — collapse-rebuild Tier-1 lock; pacing fork cross-ref
  - `docs/bible/game_bible.md ## In Flux` — Lieutenant System + RTS-framing-kill 2026-05-16 entry
  - `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` L274 + L292 — conflict-flag targets

**Re-capture stamp.** All review-theme + bounce-pattern + intersection-overlap claims in this brief are training-data-derived as of cutoff. Live Steam scrape + SteamDB CCU pull + 2026 subreddit sampling required to upgrade REPORTED → VERIFIED. Flag for Research Lane re-capture when WebFetch is restored.
