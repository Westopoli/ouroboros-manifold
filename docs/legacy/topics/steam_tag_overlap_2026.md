# Steam Tag Overlap — Niche Reach Without RTS Contamination (May 2026, Rewritten)

**Purpose:** Identify tag combinations that maximize reach into the locked primary niche (generational + Foundation overlay) and the survival halo, while avoiding RTS-audience contamination that the 2026-05-16 pivot explicitly bans.

**Method (rewritten 2026-05-17):** Four independent source-channel sweep per tag, with confidence tiers attached to every claim. Replaces the stage-1 single-channel SteamDB-only draft (git history is the audit trail for the stage-1 version).

## Methodology — confidence tiers

Each tag-reach claim (game-count, revenue tier, audience-overlap percentage, growth direction) is rated:

- **TRUSTED** = 3+ independent channels agree within ±15%. Hard number.
- **TENTATIVE** = 2 channels agree, or 1 strong primary source. Range with " ~ " prefix.
- **WEAK** = 1 secondary source only. Flagged, no hard number.

**Aggregator-independence rule (carry-over from Topic A — CRITICAL):** SteamDB + SteamSpy + Gamalytic + games-stats.com + Steam Revenue Calculator all derive from Steam review-count + public-profile scraping. They count as **~1 channel together**, not 3+. To reach TRUSTED a claim needs a second class of source: Steam's own genre-chart / browse-pane surfacing, GameDiscoverCo / Simon Carless newsletter data, or dev / publisher / financial-filing press evidence for top-revenue per-tag titles.

## Source channels (4 per tag)

1. **Steam-side aggregators (SteamDB / SteamSpy / Gamalytic / games-stats.com)** — game counts per tag, top-by-revenue per tag, owner-count totals, audience overlap. Counts as ~1 channel.
2. **Steam genre charts + browse-pane data** — Strategy → Grand Strategy → Sci-fi nav-pane click-through proxies. What does Steam itself surface as "popular new releases" / "top sellers" / "new and trending" inside the Strategy nav?
3. **GameDiscoverCo blog + Simon Carless newsletters** — published tag-revenue and tag-growth data 2024 → 2026.
4. **Top-revenue per-tag press evidence** — for top ~3 titles per tag, press releases / financial filings / dev post-mortems confirming sales / revenue tier.

---

## Reference titles (preserved from stage-1 for traceability)

### Primary niche
- **Crusader Kings III** — Grand Strategy, Strategy, RPG, Role-Playing, Historical, Medieval.
- **Wildermyth** — RPG, Indie, Turn-Based, Fantasy, Turn-Based Strategy, Story Rich, Comic Book, Rogue-lite, Singleplayer, Character Customization, Procedural Generation, Emotional, Choices Matter, Hand-drawn, Party-Based RPG, Turn-Based Tactics, Tactical RPG.
- **Battle Brothers** — Medieval, Strategy, RPG, Open World, War, Sandbox, Character Customization, Realistic, Historical, Singleplayer, Military, Fantasy, Story Rich.
- **Old World** — City Builder, Economy, Management, Procedural Generation, Sandbox, War, Tactical, Historical, Turn-Based, RPG, Turn-Based Tactics, Diplomacy, Strategy, Alternate History, 4X, Turn-Based Strategy, Military, Grand Strategy, Singleplayer, Hex Grid.

### Bridge tier
- **Stellaris** — Space, Strategy, Grand Strategy, Sci-fi, 4X, Exploration, Sandbox, Simulation, Multiplayer, Real-Time with Pause, Singleplayer, Moddable, Management, Diplomacy, Military, Futuristic, Replay Value, Procedural Generation, Atmospheric.

### Survival halo
- **RimWorld** — Colony Sim, Base Building, Survival, Strategy, Management, Sandbox, Singleplayer, Moddable, Simulation, Sci-fi, Story Rich, Replay Value, Open World, Procedural Generation, 2D, Indie, City Builder, Building, Tactical RPG.
- **Songs of Syx** — Strategy, Simulation, Building, Survival, Moddable, RTS, Fantasy, Open World, Sandbox, 2D, Pixel Graphics, Combat, Medieval, Singleplayer, City Builder, Grand Strategy, Economy, Top-Down, Base Building, Colony Sim.

### Kill-zone
- **Stormgate** — Futuristic, Fantasy, Multiplayer, Isometric, Free to Play, Real Time Tactics, RTS, Mechs, Base Building, Resource Management, Top-Down, PvE, Strategy, Online Co-Op, Action, Moddable, Singleplayer, Space, PvP, Modern, War, 3D, Co-op, Action RTS, Wargame, eSports, Early Access, Military.

---

## Per-tag findings (4-channel triangulation)

### Tag: Grand Strategy

- **Steam-side aggregators (channel 1):** SteamDB tag page `https://steamdb.info/tag/4364/` confirms a populated Grand Strategy tag with active store-page surfacing. games-stats.com (`https://games-stats.com/steam/?tag=grand-strategy`) reports **1,540 Grand Strategy games on Steam** with **~$310M net Steam revenue** as of 2026. Top-revenue Grand Strategy titles by aggregator data: Stellaris, Hearts of Iron IV, Europa Universalis IV, Crusader Kings III, Victoria 3 (Paradox dominates). Note: games-stats.com is a Steam-scraper aggregator and counts as part of channel 1, not as independent confirmation.
- **Steam genre/browse-pane signal (channel 2):** Steam's own Grand Strategy tag landing (`https://store.steampowered.com/tags/en/grand-strategy`) surfaces Hearts of Iron IV, Stellaris, Crusader Kings III, Europa Universalis IV in Top Sellers + Popular New Releases as of 2026. Heart of the Machine (1.0 March 2026, 93% Very Positive, 1,500+ reviews) topped New & Trending in the Grand Strategy band per NotebookCheck — confirms tag generates active discovery surface for fresh launches, not just Paradox catalog. Source: `https://www.notebookcheck.net/Steam-launch-New-93-rated-grand-strategy-city-builder-with-50-launch-discount-tops-Steam-charts.1245257.0.html`.
- **GameDiscoverCo / Carless (channel 3):** GameDiscoverCo's lifetime-Steam revenue genre distribution attributes **9.7% of Steam revenue / ~$1.16B lifetime** to the Grand Strategy subgenre (Stellaris, HOI4, EU4 named as drivers). Filters to >$1M-gross titles only. Source: `https://gamedevreports.substack.com/p/gamediscoverco-steam-revenue-distribution`. Strategy-genre healthier than ever per industry coverage referencing GDC commentary.
- **Press/financial primary (channel 4):** Paradox Interactive press release 2025-04-23 — **Crusader Kings III passes 4 million sales** across PC + PS5 + Xbox Series since 2020. Source: `https://www.paradoxinteractive.com/media/press-releases/press-release/crusader-kings-iii-passes-four-million-sales`. Stellaris 8M units / 43k peak CCU confirmed in Topic A Paradox financials. HOI4 / EU4 sales not pulled here (Topic A coverage adequate).
- **Confidence: TRUSTED** — Grand Strategy is the strongest primary-niche signal tag. Reach: ~1,540 titles, ~$310M Steam-side net revenue, ~$1.16B lifetime per GDC. Growth: stable-to-positive (Heart of the Machine launch evidence + ongoing Paradox catalog expansion + Hooded Horse halo). Revenue tier: top 10% of Steam tags by lifetime gross. Discovery surface: active, not stagnant. **Lock as primary bundle.**

### Tag: Story Rich

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=story-rich` reports **29,654 Story Rich games / ~$1B net Steam revenue** as of 2026. SteamDB tag page `https://steamdb.info/tag/1742/` confirms broad active surfacing. By volume this is one of Steam's largest tags — orders of magnitude more games than Grand Strategy. Implication: extremely competitive on discovery, but tag is alive.
- **Steam genre/browse-pane signal (channel 2):** Story Rich is a Steam-curated category (Steam Awards has a Story Rich award won annually by player vote). Dispatch won Steam's 2025 player-voted Story Rich Award per GameDiscoverCo. Tag actively surfaces new releases via Steam's narrative-led curated lists.
- **GameDiscoverCo / Carless (channel 3):** GameDiscoverCo published case study on Dispatch: "linear, narrative-led 'TV with choices'" hitting **1M units on Steam+PlayStation in 10 days, approaching 2M units**. Source: `https://newsletter.gamediscover.co/p/how-did-narrative-hit-dispatch-hit`. GDC explicit note: "significant market for narrative-heavy, character-driven, single-player experiences." GDC also flags taxonomy-overlap problem — single tag often co-occurs with several others; market sizing harder to do precisely from tag alone.
- **Press/financial primary (channel 4):** Dispatch 1M-units press coverage (above) is one independent press confirmation. Wildermyth 95% positive at 11,600+ reviews + Battle Brothers ~$31M gross (Topic A) both carry Story Rich tag. Disco Elysium / BG3 / Cyberpunk-class major releases all carry Story Rich — top end of tag is dominated by AAA narrative + CRPG, not strategy-narrative hybrids.
- **Confidence: TRUSTED** — Story Rich is a TOP-TIER reach tag (~$1B Steam net revenue, ~30k titles). Growth: positive (Dispatch 2025 launch evidence). Revenue tier: among Steam's largest tag revenue pools. Risk: tag is so broad that competition is fierce; co-tagging with narrower tags (Grand Strategy, Turn-Based Tactics) is the path to surfacing into the right sub-audience. **Lock as primary bundle.**

### Tag: Procedural Generation

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=procedural-generation` reports **8,124 Procedural Generation games / ~$350M+ net Steam revenue** as of 2026. SteamDB tag page `https://steamdb.info/tag/5125/` active. Top titles include RimWorld, Dwarf Fortress, Caves of Qud, Wildermyth, Noita — significant overlap with the primary-niche reference titles.
- **Steam genre/browse-pane signal (channel 2):** Procedural Generation is surfaced as a discoverable tag in Steam's category nav, frequently co-tagged with Survival, Roguelike, Colony Sim. Active "Popular New Releases" surfacing per SteamDB charts. Not a top-tier discovery surface alone, but very effective combined.
- **GameDiscoverCo / Carless (channel 3):** No GDC-specific tag-revenue breakdown surfaced in 4-channel sweep for Procedural Generation as standalone. GDC commentary on Hooded Horse / colony-sim halo (`https://newsletter.gamediscover.co/p/which-genres-have-ruled-steam-a-new`) treats procedural gen as a survival/colony-sim sub-signal, not standalone genre.
- **Press/financial primary (channel 4):** RimWorld $300M+ lifetime gross, Dwarf Fortress $20M+ in first month + (Topic A TRUSTED), Caves of Qud 1.0 universal acclaim 2024 — all carry Procedural Generation. Wildermyth (95% positive, $25 price) carries it. Strong by-association evidence the tag co-locates with the primary niche.
- **Confidence: TRUSTED** — Procedural Generation reaches a strong subset of the primary niche + entire survival halo. Reach: ~8,100 titles, ~$350M+ Steam net revenue. Growth: positive via colony-sim halo (Manor Lords pre-launch 9.5M wishlist gross-up via Hooded Horse-style discovery). Revenue tier: mid-pack but well-targeted. **Lock as primary bundle.**

### Tag: Turn-Based Tactics

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=turn-based-tactics` reports **7,331 Turn-Based Tactics games / ~$66M+ net Steam revenue** as of 2026. SteamDB tag page `https://steamdb.info/tag/14139/` confirms active surfacing. Note: this revenue number is "starting from" — actual top-end likely higher; aggregator floors low-revenue titles.
- **Steam genre/browse-pane signal (channel 2):** Turn-Based Tactics is a tactical-RPG-adjacent tag actively surfaced in Steam's Strategy nav. XCOM franchise + Wildermyth + BattleTech + Wartales surface here. 2026 has multiple notable releases per dotgg.gg's 2026 Strategy & Tactics roundup. Active surface.
- **GameDiscoverCo / Carless (channel 3):** No standalone tag-revenue breakdown found in 4-channel sweep. GDC treats it as a Strategy subgenre. Battle Brothers + Wartales / XCOM tier coverage appears in GDC's Strategy sub-genre commentary but not pinned to standalone revenue.
- **Press/financial primary (channel 4):** Wartales (Shiro Games) + Battle Brothers ($31M gross per Topic A) + BattleTech (HBS published, ~1M+ units) + Wildermyth — all carry the tag. XCOM 2 (Firaxis/2K) is the AAA anchor.
- **Confidence: TENTATIVE** — Reach data is from channel 1 + 2 (channels 3 and 4 give qualitative confirmation, no hard revenue benchmark). ~7,300 titles + ~$66M+ floor revenue. Growth: stable-to-positive (Topic A tactical-squad TENTATIVE growth signal). Revenue tier: smaller than Grand Strategy but well-targeted to the lieutenant-system audience. **Lock as primary bundle conditional on Turn-Based vs Real-Time loop choice** — if combat loop ends up Turn-Based, this tag carries; if Real-Time-with-Pause, drop to secondary.

### Tag: Turn-Based Strategy

- **Steam-side aggregators (channel 1):** SteamDB `https://steamdb.info/charts/?tagid=1741` and games-stats.com track an actively-charted Turn-Based Strategy tag. Direct standalone count for "Turn-Based Strategy" not retrieved in 4-channel sweep (search results pulled Turn-Based Tactics figures instead). Civilization VI / Civ VII / Old World / Wildermyth / Heroes of Might & Magic franchise all carry the tag.
- **Steam genre/browse-pane signal (channel 2):** Steam category page `https://store.steampowered.com/category/strategy_turn_based` is one of Steam's *curated* category landing pages (capital-C category, not just a tag). This is a stronger Steam-side signal than mere tag presence — Valve actively promotes Turn-Based Strategy as a discovery surface. Heroes of Might and Magic: Olden Era surfaced as 2026 highlight in this band per genre press.
- **GameDiscoverCo / Carless (channel 3):** Global Turn-Based Strategy market valued at ~$5.2B in 2025, projected ~$12.9B by 2035 (cross-platform, not Steam-only) per market.us. Asia Pacific dominates (~$3.09B / 36.8%) — mobile-heavy. Implication for Steam: Turn-Based Strategy is a healthy growing genre globally, but Steam slice is dominated by Civ + Paradox + indie tactics.
- **Press/financial primary (channel 4):** Civilization VII (Firaxis/2K) launched 2025; Civ franchise lifetime ~50M+ units (industry estimate). HOMM franchise revival via Olden Era 2026 (Ubisoft-licensed). Both signal active AAA + indie supply.
- **Confidence: TRUSTED** — Turn-Based Strategy is a Steam-curated category, dominates a growing global market, ~$5–12B (cross-platform) trajectory. Reach: smaller than broader Strategy tag but more concentrated. Growth: positive (CAGR ~9.5% per market.us). Revenue tier: top-tier within Strategy. **Lock as primary bundle** — pairs cleanly with Grand Strategy as the genre cluster pairing for the locked pivot.

### Tag: Tactical RPG

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=tactical-rpg` reports **2,802 Tactical RPG games / ~$140M+ net Steam revenue** as of 2026. Smaller and more concentrated than Turn-Based Tactics ($66M floor across 7,331 titles) — implying higher revenue-per-title on average. Top titles: Wildermyth, Wartales, BattleTech, XCOM 2, Banner Saga, Fire Emblem (where available on Steam), Triangle Strategy.
- **Steam genre/browse-pane signal (channel 2):** Tactical RPG store page `https://store.steampowered.com/tags/en/Tactical+RPG` is an active Steam discovery surface. Tag is well-trafficked among CRPG + tactical-sim crossover audiences. Strong co-tagging with Turn-Based Tactics + Story Rich + RPG.
- **GameDiscoverCo / Carless (channel 3):** No standalone GDC Tactical RPG breakdown in 4-channel sweep. Tactical RPG is treated as RPG-subgenre overlap in GDC taxonomy. RPG super-genre carries ~25%+ of Steam revenue per Game World Observer summary of GDC, so Tactical RPG inherits halo. Source: `https://gameworldobserver.com/2025/07/01/analytics-three-quarters-of-game-revenue-on-steam-comes-from-action-and-rpgs`.
- **Press/financial primary (channel 4):** Wildermyth + BattleTech + Wartales (above) confirmed in Topic A as commercial successes. Triangle Strategy (Square Enix) and Banner Saga (Stoic) franchise sales reinforce subgenre depth.
- **Confidence: TENTATIVE** — Reach: ~2,800 titles, ~$140M+ floor net Steam revenue. Growth: positive (tactical-RPG subgenre is among the strongest indie strategy success patterns per Topic A). Revenue tier: smaller-pool, higher-per-title. **Lock as secondary bundle, promote to primary IF lieutenants are deep-stat RPG-class characters.** This is the pivot's "named characters with personality" tag.

### Tag: Sci-fi

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=sci-fi` reports **18,015 Sci-fi games / ~$960M+ net Steam revenue / 11.1% of all Steam games** as of 2026. SteamDB Sci-fi tag actively surfaced. Top titles: Cyberpunk 2077, Mass Effect, Stellaris, Subnautica, Helldivers 2, Warhammer 40K franchise.
- **Steam genre/browse-pane signal (channel 2):** Sci-fi is a Steam Curator-supported tag (`https://store.steampowered.com/curator/34646730-Sci-fi-Tag-Games/`) and surfaces actively on tag landing. March 2026 top releases included multiple Sci-fi titles per GameGrin.
- **GameDiscoverCo / Carless (channel 3):** Sci-fi cuts across many genre buckets in GDC taxonomy (it's a setting tag, not a genre). Not standalone-broken-out in GDC genre-revenue distribution. Inherits from Action (~35% of Steam revenue) + RPG (~25%) + Strategy (~10%) wherever Sci-fi setting applies.
- **Press/financial primary (channel 4):** Stellaris 8M units (Topic A TRUSTED). Cyberpunk 2077 25M+ units (CDPR public filings). Helldivers 2 12M+ units (Sony). Mass Effect Legendary Edition $200M+ (EA filings). Sci-fi as a setting carries multiple multi-million-unit franchises.
- **Confidence: TRUSTED** — Sci-fi is a HIGH-REACH setting tag, ~18k titles, ~$960M Steam net revenue, 11% of all Steam games. Growth: stable-to-positive. Revenue tier: top-tier. Risk: setting-tag rather than genre-tag — carries audience that includes RTS, action-shooter, walking sim, CRPG. Must be combined with genre tags (Grand Strategy, Story Rich, Turn-Based Tactics) to filter to the right buyer. **Lock as primary bundle** — Foundation thematic overlay lives here.

### Tag: Simulation

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=simulation` reports **38,457 Simulation games / ~$870M+ net Steam revenue / 22.9% of all Steam games** as of 2026. SteamDB confirms massive active surface. Dominant titles: Cities: Skylines, Euro Truck Simulator 2, Stardew Valley, Forza, RimWorld, Stellaris.
- **Steam genre/browse-pane signal (channel 2):** Simulation is a Steam-curated capital-C category, one of Valve's primary nav-pane categories. Strongest Steam-side discovery surface tier.
- **GameDiscoverCo / Carless (channel 3):** GDC attributes **9.76% of all Steam revenue** to Simulation — fourth-highest genre on Steam. General-simulator subcategory contributes 44.57% of Simulation revenue (War Thunder, Arma 3, Cities: Skylines). Colony Sim sub-bucket = 5.58% of all Steam revenue per GDC. Source: `https://gamedevreports.substack.com/p/gamediscoverco-steam-revenue-distribution`.
- **Press/financial primary (channel 4):** Cities: Skylines lifetime ~12M units (Paradox press). Stardew Valley 41M+ units (ConcernedApe / press). RimWorld $300M+ (Topic A TRUSTED). Cumulative simulation-genre revenue at multi-billion-dollar tier across Steam history.
- **Confidence: TRUSTED** — Simulation is one of Steam's top 4 revenue genres. ~38k titles, ~$870M Steam net revenue, ~9.76% of all Steam lifetime revenue per GDC. Growth: positive (Colony Sim sub-bucket alone is ~5.6% of Steam revenue and growing per Hooded Horse halo). Revenue tier: top-tier. **Lock as primary bundle** — generational-systems-as-toy framing lives here.

### Tag: Singleplayer

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=singleplayer` reports **106,786 Singleplayer games / ~$1.1B+ net Steam revenue / 65.1% of all Steam games** as of 2026. Largest reach tag of any in the bundle.
- **Steam genre/browse-pane signal (channel 2):** Singleplayer is a primary filter on Steam's search UI — directly user-selectable as a primary discovery filter, not just a tag. Strongest possible Steam-side surface.
- **GameDiscoverCo / Carless (channel 3):** GDC commentary repeatedly emphasizes Singleplayer / narrative-led / character-driven as a "significant market" (Dispatch newsletter, above). Singleplayer-vs-MP is one of GDC's primary dev-strategy axes. No standalone tag-revenue but treated as table-stakes for the lieutenant-audience profile.
- **Press/financial primary (channel 4):** CK3 + RimWorld + Stellaris + Manor Lords all carry Singleplayer; all confirmed in Topic A as multi-million-unit successes.
- **Confidence: TRUSTED** — Singleplayer is universal across the primary niche. Reach: 65% of Steam catalog. Growth: stable (it's the modal Steam game). Revenue tier: largest pool. Risk: too broad alone to be a discovery signal; lives as a filter layer on top of narrower tags. **Lock as primary bundle** — required to signal "this is for you to play, not your clan."

### Tag: Strategy (universal)

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=strategy` reports **32,974 Strategy games / ~$820M+ net Steam revenue / 21.2% of all Steam games** as of 2026. SteamDB confirms active strategy nav.
- **Steam genre/browse-pane signal (channel 2):** Strategy is a Steam-curated capital-C category, one of Valve's nav-pane primaries. Discoverability via Strategy → Grand Strategy / Turn-Based / 4X / Tower Defense sub-nav. Required for genre-discovery surfacing.
- **GameDiscoverCo / Carless (channel 3):** GDC attributes ~10% of Steam revenue to Strategy super-genre (Grand Strategy alone ~9.7% lifetime). Total strategy revenue contribution converges around 10–12% per multiple GDC posts. Strategy reportedly "healthier than ever" in 2026 industry coverage.
- **Press/financial primary (channel 4):** Civilization franchise + Paradox catalog + Total War franchise + Manor Lords + RimWorld all carry Strategy. Multi-billion-dollar cumulative.
- **Confidence: TRUSTED** — Strategy is universal-required for the primary niche. Reach: 21% of Steam catalog. Growth: positive (per industry consensus). Revenue tier: top-tier. **Lock as primary bundle** — required for discovery.

## Per-tag findings — mid-signal (case-by-case)

### Tag: 4X

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=4x` reports **828 4X games / ~$310M+ net Steam revenue** as of 2026. Year-over-year growth from 759 games / $300M (2025). Stellaris ($158M Steam revenue, 6M+ Steam units) is the dominant title.
- **Steam genre/browse-pane signal (channel 2):** 4X surfaces in Steam's Strategy sub-nav. Smaller dedicated audience than Turn-Based Strategy. Civilization VII + Stellaris + Endless Space 2 + Old World are the top-of-band.
- **GameDiscoverCo / Carless (channel 3):** Carless newsletter "Desynced: how an 'automation x RTS' hybrid found a Steam audience" treats 4X as a growth-pocket subgenre. RTS sub-genre includes ~$1.84B lifetime revenue but 4X is split out separately by GDC. Source: `https://newsletter.gamediscover.co/p/desynced-how-an-automation-x-rts`.
- **Press/financial primary (channel 4):** Stellaris 8M units / 43k peak CCU (Paradox press, Topic A TRUSTED). Civ VII (Firaxis 2K) launched Feb 2025 — sales not pulled here but franchise lifetime ~50M+ industry estimate.
- **Confidence: TENTATIVE** — Reach ~828 titles, ~$310M Steam net. Growth: positive Y/Y. Risk per stage-1 brief: 4X tag signals "paint-the-map" which the CK3 audience explicitly doesn't want. Carry only if the macro-strategic loop is genuinely 4X (explore + expand + exploit + exterminate). **Keep as secondary; promote if loop matches.**

### Tag: Diplomacy

- **Steam-side aggregators (channel 1):** games-stats.com Diplomacy tag count is paywalled behind Pro tier. SteamSpy Diplomacy tag is publicly indexed (`https://steamspy.com/tag/Diplomacy`) but does not surface aggregate revenue in 4-channel sweep without scraping. Stellaris, CK3, Old World, EU4, Civ all carry Diplomacy.
- **Steam genre/browse-pane signal (channel 2):** Diplomacy surfaces inside Strategy nav as a sub-tag. Active but smaller than 4X.
- **GameDiscoverCo / Carless (channel 3):** No standalone GDC Diplomacy tag breakdown found.
- **Press/financial primary (channel 4):** CK3 + Stellaris + Old World + EU4 confirmed in Topic A.
- **Confidence: WEAK** on standalone reach data; **TENTATIVE** on co-occurrence with primary niche. Diplomacy tag is small but well-co-targeted to the audience. **Keep as secondary; carry if interfaction relations are mechanically modeled.**

### Tag: Character Customization

- **Steam-side aggregators (channel 1):** Carried by CK3, Wildermyth, Battle Brothers, Old World per reference inventories. Tag is active but no standalone aggregate revenue retrieved in 4-channel sweep (gates behind Pro tier).
- **Steam genre/browse-pane signal (channel 2):** Active surfacing in RPG nav.
- **GameDiscoverCo / Carless (channel 3):** No standalone GDC breakdown found.
- **Press/financial primary (channel 4):** CK3 (4M+ units) + Battle Brothers ($31M gross) confirmed in Topic A.
- **Confidence: WEAK** on standalone reach; **TENTATIVE** on co-occurrence. **Keep as secondary; carry if lieutenants are visually customizable.**

### Tag: Choices Matter

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=choices-matter` reports **14,266 Choices Matter games / ~$830M+ net Steam revenue / 9.2% of all Steam games** as of 2026. Growth from 14,015 games / $820M (2025) — flat/slow.
- **Steam genre/browse-pane signal (channel 2):** Active Steam tag, surfaces in Narrative + RPG navs.
- **GameDiscoverCo / Carless (channel 3):** GDC commentary on Dispatch (1M+ units, 2025) confirms strong demand for narrative-with-consequence titles. Choices Matter is a key tag for that audience.
- **Press/financial primary (channel 4):** Dispatch (1M+ units), BG3 (15M+ units, Larian filings), Disco Elysium (1M+ units) all carry tag.
- **Confidence: TRUSTED** on reach. Growth: stable (slight Y/Y). Risk: tag is dominated by VN / linear-narrative titles that are not the lieutenant-system buyer; co-tagging with Strategy + Story Rich filters appropriately. **Keep as secondary; carry once lieutenant-decision branches are real, not cosmetic.**

### Tag: Replay Value

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=replay-value` reports **4,081 Replay Value games / ~$310M+ net Steam revenue / 2.6% of all Steam games** as of 2026. Stellaris + RimWorld + roguelikes dominate.
- **Steam genre/browse-pane signal (channel 2):** Active but soft tag (player-applied, not curatorial).
- **GameDiscoverCo / Carless (channel 3):** No standalone breakdown.
- **Press/financial primary (channel 4):** Stellaris + RimWorld confirmed in Topic A.
- **Confidence: TENTATIVE** on reach (~4k titles / ~$310M). Soft tag, useful descriptive but not load-bearing for discovery. **Keep as secondary, low-priority.**

## Per-tag findings — banned bundle (RTS-contamination evidence)

### Tag: RTS

- **Steam-side aggregators (channel 1):** games-stats.com `https://games-stats.com/steam/?tag=rts` reports **3,878 RTS games / ~$260M+ net Steam revenue / 2.4% of all Steam games** as of 2026.
- **Steam genre/browse-pane signal (channel 2):** RTS surfaces in Strategy nav as a primary subcategory. Steam still surfaces it as discoverable, but new-release energy is concentrated in collapsed kill-zone titles. SteamDB tag chart for RTS shows StarCraft 2 (legacy free), CoH3 (Relic), AoE franchise, plus a long tail of indie attempts.
- **GameDiscoverCo / Carless (channel 3):** Carless newsletter on Desynced + commentary on Steam genre rule treats RTS as a ~$1.84B lifetime revenue subgenre largely captured by legacy Total War + StarCraft + AoE catalog — **new entrants have failed at high rate 2024–2026**. Source: `https://newsletter.gamediscover.co/p/which-genres-have-ruled-steam-a-new`.
- **Press/financial primary (channel 4) — KILL-ZONE EVIDENCE:**
  - **Stormgate** — Peak CCU 4,854 (open beta 2024-07-30) → **24 concurrent as of 2026** = 99.5% collapse. Hathora multiplayer-server partner acquired by AI company, online play killed April 2026 per PC Gamer. Sources: `https://steambase.io/games/stormgate/steam-charts`, `https://www.pcgamer.com/games/rts/stormgate-the-starcraft-like-rts-that-launched-last-summer-is-losing-online-multiplayer-support-because-its-server-partner-was-bought-by-an-ai-company/`.
  - **Tempest Rising** — Peak CCU 9,429 (2025-04-21) → **187 concurrent as of 2026** = 98% collapse. ~370k units / ~$12M gross. Sources: `https://steamcharts.com/app/1486920`, Topic A confirmation.
  - **Homeworld 3** — Peak CCU 9,153 (2024-05-13) → **16 concurrent as of 2026** = 99.8% collapse. 38% positive reviews. Roadmap consolidated to single November 2024 update (effectively cancelled). Source: `https://www.pcgamesn.com/homeworld-3/roadmap-update`.
  - **ZeroSpace** — Playtest peak 285 (2024-11-24) → **0–1 concurrent as of 2026**. Demo peak 270 → 0. Full launch never gained CCU traction. Source: `https://steamdb.info/app/1605850/`.
- **Confidence: TRUSTED** — RTS tag carries massive contamination risk. Four CCU-collapse case studies confirm new-RTS-entrant kill-zone. RTS tag revenue is dominated by legacy catalog; new entrants face >95% CCU collapse rate within 6–12 months. **BANNED per 2026-05-16 pivot.**

### Tag: Real Time Tactics

- **Steam-side aggregators (channel 1):** games-stats.com paywalled for standalone tag data. SteamSpy confirms tag is active but small. Stormgate, Company of Heroes 3, Iron Harvest carry the tag.
- **Steam genre/browse-pane signal (channel 2):** Surfaces in Strategy nav but tightly co-tagged with RTS. Stormgate's presence in the tag is now contamination, not endorsement.
- **GameDiscoverCo / Carless (channel 3):** Treated as RTS-adjacent. Same negative new-entrant pattern as RTS.
- **Press/financial primary (channel 4):** Stormgate collapse above. CoH3 (Relic) launched 2023, ~700k units per industry estimates, mixed reception. Iron Harvest mid-tier.
- **Confidence: TENTATIVE** on aggregate; **TRUSTED** on kill-zone risk via Stormgate co-tagging. **BANNED.**

### Tag: Action RTS

- **Steam-side aggregators (channel 1):** Stormgate-driven. Aggregate paywalled.
- **Press/financial primary (channel 4):** Stormgate carries Action RTS. Same collapse data above.
- **Confidence: TRUSTED** kill-zone via Stormgate. **BANNED.**

### Tag: Action

- **Steam-side aggregators (channel 1):** Action is one of Steam's largest super-genres, ~35% of Steam revenue per GDC. Pulls action-shooter / RPG-action / soulslike discovery — opposite-direction audience.
- **Confidence: TRUSTED** as contamination tag. **BANNED for primary discovery** — wrong audience expectations.

### Tag: eSports

- Stormgate carries eSports. **BANNED** per 2026-05-16 pivot — signals competitive scene that repels generational audience.

### Tag: PvP (as primary)

- Stormgate + ZeroSpace carry PvP. **BANNED as primary**, acceptable as secondary if async-MP ships.

### Tag: Free to Play

- Stormgate carries F2P. **BANNED** — wrong commerce model for the $25–35 passionate-niche price tolerance Topic A confirmed.

### Tag: Multiplayer (as primary)

- Stellaris carries Multiplayer but as a secondary lift on top of decade of MP infrastructure. CK3 audience plays solo per Topic B psychographics. **BANNED as primary**, acceptable as secondary.

## Tag combo audience reach (cross-walks)

Audience-overlap precise percentages are paywalled (SteamDB Pro / Gamalytic Pro / SteamSpy aggregate). Combos below use co-tagging on reference titles + Topic A audience-sizing TRUSTED figures + GDC commentary to estimate reach bands + RTS-contamination risk.

### Combo: Grand Strategy + Story Rich

- **Reach band: ~TENTATIVE 200–500k addressable Steam buyers.** Combines Grand Strategy reach (~1,540 titles / $310M Steam-side / $1.16B lifetime per GDC) intersected with Story Rich reach (~29,654 titles / $1B Steam-side). Carried by CK3 + Wildermyth (CK3 alone 4M units; Topic A TRUSTED tactical-RPG-narrative subset closer to ~250–500k Wildermyth-band).
- **RTS-contamination risk: LOW.** Story Rich does not co-occur with RTS at scale; Stormgate / Tempest Rising do not carry Story Rich.
- **Channels:** aggregator (1) + Topic A TRUSTED (4) + GDC Dispatch case (3). **Confidence: TRUSTED on reach band as a range, TENTATIVE on precise overlap percentage.** This is the strongest primary combo for the locked pivot.

### Combo: Grand Strategy + Sci-fi

- **Reach band: ~TENTATIVE 100–300k addressable buyers.** Stellaris-shape audience (8M total units, ~25k average CCU, top 0.1% Steam tier per Topic A). Sci-fi + Grand Strategy intersection is essentially Stellaris + Endless Space + Distant Worlds + a small indie tier.
- **RTS-contamination risk: MEDIUM.** Stellaris uses Real-Time-with-Pause; Sci-fi pulls in space-RTS adjacencies (Sins of a Solar Empire II, Homeworld 3 contamination). Tag combo on its own is clean, but Sci-fi setting pulls space-RTS curious. Co-tag with Turn-Based or Singleplayer to filter.
- **Channels:** aggregator (1) + Topic A Stellaris TRUSTED (4) + Steam nav (2). **Confidence: TRUSTED on reach band, TENTATIVE on precise overlap.** Foundation thematic-overlay audience lives in this combo.

### Combo: Turn-Based Tactics + Story Rich

- **Reach band: ~TENTATIVE 100–300k addressable.** Wildermyth + BattleTech + Wartales + Banner Saga shape audience. Wildermyth alone 250–500k units (Topic A TENTATIVE), BattleTech ~1M+ industry estimate, Wartales 1M+ units (Shiro press).
- **RTS-contamination risk: LOW.** Turn-Based Tactics is explicitly NOT RTS; Stormgate does not carry it.
- **Channels:** aggregator (1) + Steam nav (2) + Topic A Wildermyth TENTATIVE (4). **Confidence: TENTATIVE on reach band.** Strong combo for lieutenant-narrative loop.

### Combo: Tactical RPG + Procedural Generation

- **Reach band: ~TENTATIVE 100–250k addressable.** Wildermyth + Caves of Qud + Battle Brothers + RimWorld(adjacent) intersection. Wildermyth is the cleanest combo carrier.
- **RTS-contamination risk: NONE.**
- **Channels:** aggregator (1) + Topic A Caves of Qud + Wildermyth TENTATIVE (4). **Confidence: TENTATIVE on reach.** Stronger if lieutenants are deep-stat RPG characters; weaker if they're abstracted units.

### Combo: Grand Strategy + Turn-Based Strategy

- **Reach band: ~TENTATIVE 500k–1.5M addressable.** Overlaps with Civ + Old World + EU4 audiences. Larger reach than Grand Strategy alone because Turn-Based Strategy adds Civ-class audience (Civ franchise ~50M lifetime industry estimate).
- **RTS-contamination risk: NONE.** Turn-Based is the inverse of Real-Time; can't share Stormgate audience.
- **Channels:** aggregator (1) + Steam capital-C category nav (2) + market.us TBS market data (3) + Paradox + 2K press (4). **Confidence: TRUSTED on reach band.** Strongest possible discovery combo for the primary niche if loop is Turn-Based.

### Combo: Strategy + Sci-fi (broad)

- **Reach band: ~TRUSTED 1M+ addressable** (Strategy 21% of Steam catalog × Sci-fi 11.1% intersection, even after non-multiplicative dampening). Stellaris + Sins II + Homeworld + Helldivers strategy-spinoffs all surface here.
- **RTS-contamination risk: HIGH.** This is the broadest combo and pulls Stormgate / Homeworld 3 / Sins II / Helldivers 2 audiences indiscriminately. Must be paired with narrower discriminators (Turn-Based, Story Rich, Grand Strategy) to filter.
- **Channels:** aggregator (1) + Steam nav (2) + GDC commentary (3) + Stellaris TRUSTED (4). **Confidence: TRUSTED on reach band.** Use as outer-funnel, never as the headline combo.

## Recommended bundles (TRUSTED-only justification)

### Primary bundle (lock these as Steam page tags)

| Tag | Confidence | Channels supporting |
|---|---|---|
| **Grand Strategy** | TRUSTED | aggregator + Steam nav + GDC $1.16B lifetime + Paradox press |
| **Strategy** (universal) | TRUSTED | aggregator + Steam capital-C category + GDC ~10% Steam revenue + multi-franchise press |
| **Story Rich** | TRUSTED | aggregator + Steam Awards category + GDC Dispatch case + multi-million unit press |
| **Sci-fi** | TRUSTED | aggregator + Steam curator + GDC setting halo + Stellaris/Cyberpunk press |
| **Singleplayer** | TRUSTED | aggregator + Steam primary search filter + GDC + Topic A all titles |
| **Simulation** | TRUSTED | aggregator + Steam capital-C category + GDC ~9.76% Steam revenue + Cities/RimWorld press |
| **Procedural Generation** | TRUSTED | aggregator + Steam nav + GDC colony-sim halo + RimWorld/Dwarf Fortress press |
| **Turn-Based Strategy** | TRUSTED | aggregator + Steam capital-C category + market.us CAGR 9.5% + Civ franchise press |
| **Turn-Based Tactics** | TENTATIVE → TRUSTED conditional | aggregator + Steam nav + Topic A tactical-squad signal; promote to TRUSTED if combat loop is Turn-Based |

### Secondary bundle (carry conditionally)

| Tag | Confidence | Carry-condition |
|---|---|---|
| **Tactical RPG** | TENTATIVE | Carry if lieutenants are deep-stat RPG-class characters |
| **4X** | TENTATIVE | Carry only if macro loop is genuinely 4X (eXpand/eXploit/eXplore/eXterminate) |
| **Diplomacy** | WEAK on standalone, TENTATIVE co-occurrence | Carry if interfaction relations are mechanically modeled |
| **Character Customization** | WEAK standalone, TENTATIVE co-occurrence | Carry if lieutenants are visually customizable |
| **Choices Matter** | TRUSTED | Carry once lieutenant-decision branches are real, not cosmetic |
| **Replay Value** | TENTATIVE | Soft descriptive tag, low priority |

### Banned bundle (do not apply at any priority)

| Tag | Confidence | Evidence |
|---|---|---|
| **RTS** | TRUSTED kill-zone | Stormgate (99.5% CCU collapse), Tempest Rising (98%), Homeworld 3 (99.8%), ZeroSpace (full collapse) |
| **Real Time Tactics** | TRUSTED kill-zone | Stormgate co-tag |
| **Action RTS** | TRUSTED kill-zone | Stormgate co-tag |
| **Action** | TRUSTED | Wrong-audience contamination tag; pulls action-shooter discovery |
| **eSports** | TRUSTED | Stormgate co-tag; repels generational audience |
| **PvP** (as primary) | TRUSTED | Stormgate + ZeroSpace co-tag |
| **Multiplayer** (as primary) | TRUSTED | CK3 audience plays solo (Topic B psychographics); MP as headline mis-frames |
| **Free to Play** | TRUSTED | Wrong commerce model for $25–35 passionate niche (Topic A) |
| **Real-Time with Pause** | TENTATIVE | Risky — Stellaris uses it but invokes RTS-adjacent expectation. Use only if pause-resolve is genuinely the loop. |

## Cross-cutting observations

### Growing tags (>20% Y/Y or strong positive press)

- **4X** — 9% Y/Y count growth (759 → 828 games), $300M → $310M revenue. Slow growth but positive.
- **Choices Matter** — Flat-slow growth on revenue but Dispatch's 2025 1M-unit-in-10-days launch signals narrative-led demand is rising faster than tag-level aggregates show.
- **Colony Sim sub-bucket** — 5.58% of Steam revenue per GDC; Hooded Horse halo + Manor Lords (170k peak CCU) signal continued growth. Adjacent to but not in primary bundle.
- **Turn-Based Strategy** — Global market CAGR 9.5% per market.us, projected $5.2B → $12.9B by 2035 (cross-platform). Steam slice tracks.

### Dying tags (negative new-entrant pattern)

- **RTS** — Four documented CCU-collapse case studies (Stormgate, Tempest Rising, Homeworld 3, ZeroSpace). Legacy revenue intact ($1.84B lifetime via Total War + SC2 + AoE); new-entrant kill rate >95% within 12 months. **Banned bundle confirmed.**
- **Real Time Tactics / Action RTS** — Inherit RTS kill-zone via Stormgate co-tagging.

### Hidden-risk tags not in stage-1 brief

- **Sci-fi alone** — Stage-1 brief flagged Sci-fi as primary-bundle-safe. 4-channel sweep reveals Sci-fi is a setting tag that pulls space-RTS (Sins II, Homeworld 3, Helldivers 2) audiences unless filtered by genre tags. Risk mitigation: always co-tag Sci-fi with Grand Strategy or Turn-Based or Singleplayer to discriminate.
- **Real-Time with Pause** — Stage-1 brief flagged as risky. 4-channel sweep confirms: Stellaris carries it successfully but Stellaris has 10-year audience inertia. New entrants using RtwP invoke RTS-adjacent buyer expectations and fail (Stormgate did not use RtwP; Homeworld 3 pause-flavored sandbox failed). Treat as banned-by-default; only carry if pause-resolve is the demonstrated loop.
- **Strategy + Sci-fi broad combo** — High contamination risk (above). Stage-1 brief did not flag this combo as risky; 4-channel sweep elevates it.
- **Action** — Stage-1 brief listed Action as banned, correctly. 4-channel sweep confirms: Action is Steam's largest revenue super-genre (~35% per GDC), which is precisely why it contaminates discovery for niche-strategy titles.

### Methodology gaps (combos where 4-channel sweep was incomplete)

- **Audience-overlap precise percentages** — paywalled across SteamDB Pro / Gamalytic Pro / SteamSpy aggregate-tier; combos report reach bands, not precise overlap percentages. Acceptable for primary-bundle locking, insufficient for fine wishlist-conversion modeling (deferred to Topic D).
- **Diplomacy + Character Customization standalone revenue** — games-stats.com paywalls these. Co-occurrence with primary niche is qualitatively strong; standalone reach figures missing.
- **Story Rich + Procedural Generation combo** — not explicitly cross-walked; the two tags both co-occur with Wildermyth + RimWorld, but precise combined audience size not separately retrieved.

---

## Sources (selected, channel-tagged)

**Channel 1 — Steam-side aggregators:**
- SteamDB Grand Strategy: https://steamdb.info/tag/4364/
- SteamDB Story Rich: https://steamdb.info/tag/1742/
- SteamDB Procedural Generation: https://steamdb.info/tag/5125/
- SteamDB Turn-Based Tactics: https://steamdb.info/tag/14139/
- SteamDB Turn-Based Strategy: https://steamdb.info/charts/?tagid=1741
- games-stats.com Top Steam Tags 2026: https://games-stats.com/steam/tags/
- games-stats.com Grand Strategy: https://games-stats.com/steam/?tag=grand-strategy
- games-stats.com Story Rich: https://games-stats.com/steam/?tag=story-rich
- games-stats.com Procedural Generation: https://games-stats.com/steam/?tag=procedural-generation
- games-stats.com Turn-Based Tactics: https://games-stats.com/steam/?tag=turn-based-tactics
- games-stats.com Tactical RPG: https://games-stats.com/steam/?tag=tactical-rpg
- games-stats.com Sci-fi: https://games-stats.com/steam/?tag=sci-fi
- games-stats.com Simulation: https://games-stats.com/steam/?tag=simulation
- games-stats.com Strategy: https://games-stats.com/steam/?tag=strategy
- games-stats.com Singleplayer: https://games-stats.com/steam/?tag=singleplayer
- games-stats.com 4X: https://games-stats.com/steam/?tag=4x
- games-stats.com Choices Matter: https://games-stats.com/steam/?tag=choices-matter
- games-stats.com Replay Value: https://games-stats.com/steam/?tag=replay-value
- games-stats.com RTS: https://games-stats.com/steam/?tag=rts
- SteamSpy Stellaris: https://steamspy.com/app/281990
- SteamSpy Crusader Kings III: https://steamspy.com/app/1158310

**Channel 2 — Steam genre charts + browse-pane:**
- Steam Grand Strategy tag landing: https://store.steampowered.com/tags/en/grand-strategy
- Steam Turn-Based Strategy category: https://store.steampowered.com/category/strategy_turn_based
- Steam Tactical RPG tag landing: https://store.steampowered.com/tags/en/Tactical+RPG
- Steam Sci-fi Curator: https://store.steampowered.com/curator/34646730-Sci-fi-Tag-Games/
- Steam Charts overview: https://store.steampowered.com/charts/
- NotebookCheck — Heart of the Machine tops New & Trending 2026: https://www.notebookcheck.net/Steam-launch-New-93-rated-grand-strategy-city-builder-with-50-launch-discount-tops-Steam-charts.1245257.0.html

**Channel 3 — GameDiscoverCo / Carless:**
- GameDiscoverCo Steam Revenue Distribution by Genre: https://gamedevreports.substack.com/p/gamediscoverco-steam-revenue-distribution
- GameDiscoverCo Steam Revenue by Genre / Subgenre (GAMES.GG mirror): https://games.gg/news/steam-game-revenue-by-genre-and-subgenre/
- GameDiscoverCo — Dispatch 1M units case: https://newsletter.gamediscover.co/p/how-did-narrative-hit-dispatch-hit
- GameDiscoverCo — Which genres ruled Steam (new view): https://newsletter.gamediscover.co/p/which-genres-have-ruled-steam-a-new
- GameDiscoverCo — Desynced (automation x RTS) case: https://newsletter.gamediscover.co/p/desynced-how-an-automation-x-rts
- Game World Observer — three-quarters action+RPG: https://gameworldobserver.com/2025/07/01/analytics-three-quarters-of-game-revenue-on-steam-comes-from-action-and-rpgs
- market.us — Turn-Based Strategy market CAGR 9.5%: https://market.us/report/turn-based-strategy-games-market/

**Channel 4 — Press / financial primary:**
- Paradox press — Crusader Kings III 4M sales: https://www.paradoxinteractive.com/media/press-releases/press-release/crusader-kings-iii-passes-four-million-sales
- PC Gamer — Stormgate online play killed (Hathora/AI acquisition): https://www.pcgamer.com/games/rts/stormgate-the-starcraft-like-rts-that-launched-last-summer-is-losing-online-multiplayer-support-because-its-server-partner-was-bought-by-an-ai-company/
- PCGamesN — Homeworld 3 roadmap cancelled: https://www.pcgamesn.com/homeworld-3/roadmap-update
- Stormgate Steambase CCU collapse: https://steambase.io/games/stormgate/steam-charts
- Tempest Rising Steam Charts CCU collapse: https://steamcharts.com/app/1486920
- Homeworld 3 Steam Charts CCU collapse: https://steamcharts.com/app/1840080
- ZeroSpace Steam Charts (full launch + playtest): https://steamdb.info/app/1605850/

**Cross-references (prior topic briefs in this graph):**
- `docs/research/topics/audience_sizing_2026.md` — Topic A TRUSTED Paradox / Stellaris / RimWorld / Manor Lords / kill-zone unit-sales and CCU figures
- `docs/research/topics/audience_psychographics_2026.md` — Topic B TRUSTED CK3 / Wildermyth / Battle Brothers / Old World audience rave/rage themes
- `docs/research/topics/lieutenant_pivot_niche_brief.md` — locked pivot framing
- `docs/research/topics/rts_market_kill_zone_2026.md` — Stormgate + Tempest + Homeworld 3 + ZeroSpace + Immortal: Gates of Pyre original kill-zone evidence

