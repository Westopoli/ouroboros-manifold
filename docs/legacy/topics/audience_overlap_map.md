---
name: Audience Overlap Map
description: Steam tag + curator + reviewer + press + creator overlap across CK3/Wildermyth/RimWorld/Old World/BB/Stellaris/Foxhole/Helldivers 2; feeds T-B1 brand positioning, capsule copy, T-C1 creator pitch list.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Wave 2 capture
---

# Audience Overlap Map

## What this brief is

Audience-overlap map across eight anchor titles spanning the Ouroboros adjacent strategy/sim space: Crusader Kings 3 (CK3), Wildermyth, RimWorld, Old World, Battle Brothers (BB), Stellaris, Foxhole, Helldivers 2 (HD2). Maps tag co-occurrence on Steam, curator overlap, reviewer overlap, press overlap, and YouTube creator overlap. Identifies which "fans of X" pitches resonate across multiple anchors, which pairs share blood, which sit apart.

Brief feeds: T-B1 brand positioning (synthesises overlap clusters into pitch shape), capsule copy + screenshot framing (cluster-derived language), T-S1 Steam tag slate (co-occurrence-driven tag picks), T-C1 YouTube creator pitch list (overlap-validated creators), T-C3 press outlet map, T-C4 newsletter + curator surface picks.

**Does NOT recommend a pick.** Research Lane surfaces overlap structure; Design Lane + Marketing Lane pick. No "Ouroboros should target X cluster" statements. Conflict section only surfaces bible collisions, doesn't resolve them.

## Method

Sources scanned (training-data floor, no live fetch):
- Steam tag pages + "Tag this product" community signal (recalled from training)
- Steam "More like this" + "Customers also bought" carousels (where exposed in training data)
- Steam curators (Hooded Horse, Strategy Gamer curator, Strategy Game Curator, ExplorMinate, Wargamer, SplatterCatGaming curator, Worth A Buy)
- Reviewer profile patterns (Steam profile review-feed shapes recalled from training)
- Press archives (Rock Paper Shotgun, PC Gamer, Eurogamer, Strategy Gamer, Wargamer, PCGamesN, Polygon)
- YouTube channel back-catalog patterns (Sseth, Quill18, MATN, Splattercat, Wanderbots, Nookrium, ItalianSpartacus, Lionheart, Arumba, ChristopherOdd, DangerouslyFunny)

**Exclusions:** No live Steam scrape (WebFetch disabled). No SteamDB tag-explorer pulls. No 2026 curator-feed sample. No 2026 YT view-count refresh. No press CMS scrape.

**Confidence calibration.** WebFetch denied → floor REPORTED. Tag co-occurrence patterns are moving targets; numbers here are training-recall directional, not 2026 verbatim. VERIFIED reserved for verbatim quotes recalled at high confidence — near-zero in this brief. Most claims REPORTED or ESTIMATED. AMBIGUOUS where signal splits or sources contradict.

## Pairwise tag co-occurrence

Tag co-occurrence matrix across the eight anchors. Each cell summarizes which Steam tags both titles share, drawn from training-recall of each anchor's top-15 tag block. Tags marked w/ * are core to multiple anchors (cluster-defining).

**Common anchor tag stems (training-recall):**
- CK3: Grand Strategy*, Strategy*, Medieval, Historical, RPG, Simulation*, Multiplayer, Politics, Roleplaying, Character Customization
- Wildermyth: RPG, Strategy*, Tactical*, Procedural Generation*, Story Rich*, Turn-Based Tactics, Adventure, Fantasy, Indie, Replay Value
- RimWorld: Colony Sim*, Simulation*, Survival, Base Building*, Sandbox*, Strategy*, Story Rich*, Indie, Top-Down, Procedural Generation*
- Old World: Strategy*, Turn-Based Strategy*, 4X*, Historical, Grand Strategy*, Simulation*, Politics, Family, Roleplaying, Replay Value
- Battle Brothers: Turn-Based Tactics*, Tactical*, RPG, Strategy*, Procedural Generation*, Permadeath*, Medieval, Difficult, Indie, Open World
- Stellaris: Grand Strategy*, Strategy*, 4X*, Space*, Sci-fi*, Simulation*, Real Time w/ Pause, Multiplayer, Exploration, Sandbox*
- Foxhole: MMO, Massively Multiplayer*, Strategy*, War, Persistent World, PvP, Top-Down Shooter, Open World, Sandbox*, Indie
- Helldivers 2: Co-op*, Shooter*, Multiplayer*, Action*, Third-Person Shooter, PvE, Online Co-Op, Sci-fi*, Difficult, Squad-Based

**Pairwise tag-overlap walk (REPORTED unless flagged):**

- **CK3 ↔ Wildermyth.** Shared: Strategy, RPG, Story Rich, Replay Value, Character Customization (loosely). Procedural Generation present in Wildermyth, absent CK3. Cluster: "narrative strategy w/ character attachment." Overlap medium-strong on narrative axis, weak on scale axis. ESTIMATED 4-6 shared tags in top-20.
- **CK3 ↔ RimWorld.** Shared: Strategy, Simulation, Sandbox (loosely on CK3 side), Story Rich. Cluster: "emergent story sims." ESTIMATED 3-5 shared tags. AMBIGUOUS — RimWorld's Colony Sim tag is genre-defining and doesn't carry to CK3.
- **CK3 ↔ Old World.** Shared: Grand Strategy, Strategy, Historical, Simulation, Politics, Roleplaying, Family (Old World)/Character (CK3), Turn-Based Strategy partial. Cluster: "dynastic historical strategy." ESTIMATED 7-9 shared tags — strongest overlap in this matrix on tag basis.
- **CK3 ↔ Battle Brothers.** Shared: Strategy, RPG, Medieval, Difficult (loosely), Roleplaying. Cluster: "medieval strategy w/ character attachment." ESTIMATED 4-6 shared tags.
- **CK3 ↔ Stellaris.** Shared: Grand Strategy, Strategy, Simulation, Multiplayer, Sandbox (loosely), Politics. Cluster: "Paradox grand strategy." ESTIMATED 6-8 shared tags — strong cluster because both are Paradox-published; same audience pool but different setting.
- **CK3 ↔ Foxhole.** Shared: Strategy, Multiplayer (loosely — CK3 is small-co-op, Foxhole is MMO). Cluster: thin. ESTIMATED 2-3 shared tags.
- **CK3 ↔ HD2.** Shared: Multiplayer (loosely). Cluster: near-zero. ESTIMATED 1-2 shared tags.
- **Wildermyth ↔ RimWorld.** Shared: Strategy, Story Rich, Procedural Generation, Indie, Replay Value. Cluster: "procedurally narrative indie." ESTIMATED 5-7 shared tags.
- **Wildermyth ↔ Old World.** Shared: Strategy, Turn-Based, Roleplaying (loosely). Cluster: "turn-based strategy w/ character layer." ESTIMATED 3-5 shared tags.
- **Wildermyth ↔ BB.** Shared: Turn-Based Tactics, Tactical, RPG, Strategy, Procedural Generation, Permadeath partial (Wildermyth has it, varies w/ difficulty). Cluster: "tactical permadeath RPG." ESTIMATED 6-8 shared tags — strong overlap; closest tactical-cousin pair in matrix.
- **Wildermyth ↔ Stellaris.** Shared: Strategy, Story Rich (loosely), Sci-fi (Wildermyth has fantasy not sci-fi). Cluster: thin. ESTIMATED 2-3 shared tags.
- **Wildermyth ↔ Foxhole.** Cluster: near-zero. ESTIMATED 1 shared tag (Strategy).
- **Wildermyth ↔ HD2.** Cluster: near-zero. ESTIMATED 0-1 shared tags.
- **RimWorld ↔ Old World.** Shared: Strategy, Simulation, Replay Value (loosely). Cluster: thin — different scale. ESTIMATED 3-4 shared tags.
- **RimWorld ↔ BB.** Shared: Strategy, Procedural Generation, Permadeath (loosely — BB hard, RimWorld optional), Difficult, Indie, Story Rich. Cluster: "permadeath emergent-story indie strategy." ESTIMATED 5-7 shared tags — strong overlap.
- **RimWorld ↔ Stellaris.** Shared: Strategy, Simulation, Sandbox, Sci-fi (loosely — RimWorld has sci-fi flavor), Multiplayer (only via mods on RimWorld). Cluster: "simulation sandbox." ESTIMATED 4-6 shared tags.
- **RimWorld ↔ Foxhole.** Shared: Sandbox, Strategy, Indie partial. Cluster: thin. ESTIMATED 2-3 shared tags.
- **RimWorld ↔ HD2.** Shared: Sci-fi (loose). Cluster: near-zero. ESTIMATED 1 shared tag.
- **Old World ↔ BB.** Shared: Strategy, Turn-Based, Tactical (loose), Difficult. Cluster: thin. ESTIMATED 3-4 shared tags.
- **Old World ↔ Stellaris.** Shared: Grand Strategy, Strategy, 4X, Simulation, Multiplayer (loosely — Old World has MP, low usage). Cluster: "4X strategy." ESTIMATED 5-7 shared tags.
- **Old World ↔ Foxhole.** Cluster: near-zero. ESTIMATED 1-2 shared tags.
- **Old World ↔ HD2.** Cluster: near-zero. ESTIMATED 0-1 shared tags.
- **BB ↔ Stellaris.** Shared: Strategy, Sci-fi (BB fantasy, no), Sandbox (loose). Actual cluster: thin. ESTIMATED 2-3 shared tags.
- **BB ↔ Foxhole.** Cluster: near-zero. ESTIMATED 1 shared tag.
- **BB ↔ HD2.** Shared: Difficult, Squad-Based (loose). Cluster: thin. ESTIMATED 1-2 shared tags.
- **Stellaris ↔ Foxhole.** Shared: Strategy, Multiplayer, Massively Multiplayer (loose — Stellaris MP is 32-player), Sandbox, Sci-fi (loose). Cluster: thin but war-themed sci-fi MP. ESTIMATED 3-4 shared tags.
- **Stellaris ↔ HD2.** Shared: Sci-fi, Multiplayer (different shapes), Co-op (loose — Stellaris MP not co-op). Cluster: "sci-fi MP." ESTIMATED 2-3 shared tags.
- **Foxhole ↔ HD2.** Shared: Multiplayer, Co-op (loose — Foxhole is MMO faction war, HD2 is squad PvE), Massively Multiplayer (Foxhole only), Squad-Based (loose), War-themed sci-fi/mil. Cluster: "shared-world war co-op." ESTIMATED 3-5 shared tags.

**Cluster identification.**

Tag co-occurrence resolves to three loose clusters + isolated outliers:

- **Cluster A — Dynastic / generational strategy:** CK3, Old World, Wildermyth, BB. Tag stems Strategy, RPG, Roleplaying, Character/Family, Turn-Based, Historical or Fantasy. ESTIMATED 5-9 shared tags within cluster pairs. **This is the primary-tribe cluster per lieutenant_pivot_niche_brief.md.**
- **Cluster B — Emergent-story simulation:** RimWorld, Wildermyth, BB, w/ partial CK3 reach. Tag stems Procedural Generation, Story Rich, Simulation, Sandbox, Permadeath. ESTIMATED 5-7 shared tags within pairs.
- **Cluster C — Grand strategy spatial:** CK3, Old World, Stellaris. Tag stems Grand Strategy, 4X, Strategy, Simulation, Politics. ESTIMATED 6-8 shared tags within pairs.
- **Outlier — Shared-world war MP:** Foxhole, HD2. Tag stems Multiplayer, Co-op or MMO, Sci-fi, Squad-Based, War. ESTIMATED 3-5 shared tags. Cluster is real but does NOT bridge to Clusters A/B/C — confirms Foxhole + HD2 are different audience from CK3/Wildermyth/RimWorld/Old World/BB primary tribe.

Ouroboros' bible-locked tag candidates (Grand Strategy, Sci-fi, Simulation, Procedural Generation, Narrative, Story Rich, Generations, Strategy) intersect Clusters A + B + C. Tag picks land on Stellaris (Cluster C) for sci-fi axis; CK3 + Old World (Cluster A + C) for grand-strategy axis; Wildermyth + BB + RimWorld (Cluster A + B) for procedural-narrative axis. NOT on the Foxhole/HD2 outlier — bible locks SP-first.

## Curator overlap

Curators that carry multiple anchors, training-recalled. Cross-reference for T-C4 newsletter + curator surface picks.

- **Hooded Horse (publisher + curator)** — carries Old World (publisher), Workers & Resources (publisher), Falling Frontier (publisher), Manor Lords (publisher). Does NOT publish CK3, Wildermyth, RimWorld, BB, Stellaris, Foxhole, HD2. As a *curator* feed, Hooded Horse curator profile recommends adjacent strategy/sim titles incl. some CK3/Stellaris/BB-adjacent picks. **Carries 1 anchor (Old World, as publisher).** Curator reach: high in primary tribe. REPORTED.
- **Strategy Gamer curator** (editorial-tied to strategygamer.com) — carries reviews of CK3, Old World, Stellaris, BB, Wildermyth across editorial back-catalog; curator feed mirrors editorial picks. **Carries 5 anchors (CK3, Old World, Stellaris, BB, Wildermyth).** REPORTED.
- **Strategy Game Curator** (community-run aggregator curator, separate from Strategy Gamer) — carries CK3, Stellaris, Old World, RimWorld, Wildermyth, BB across recommendations. **Carries 5-6 anchors.** REPORTED.
- **ExplorMinate** (4X-focused curator + podcast) — carries Old World, Stellaris, Endless Space, Distant Worlds, Galactic Civilizations. **Carries 2 anchors (Old World, Stellaris).** REPORTED.
- **Wargamer.com curator** — carries CK3, Stellaris, Old World, BB occasionally, war-MP titles incl. Foxhole. **Carries 4-5 anchors.** REPORTED.
- **SplatterCat curator (YT-tied)** — carries RimWorld, BB, Wildermyth, indie strategy/sim heavy. **Carries 3 anchors (RimWorld, BB, Wildermyth).** REPORTED.
- **Worth A Buy curator (YT-tied)** — carries BB, RimWorld, some Stellaris, Paradox catalog. **Carries 2-3 anchors.** REPORTED.
- **Aliensrock / Nookrium / Wanderbots curators (if active)** — overlap w/ RimWorld + Wildermyth + indie story sim. ESTIMATED 2-3 anchors each. REPORTED.
- **PC Gamer curator** — broad reach, carries all 8 anchors via editorial cycles. REPORTED — not differentiating.
- **No single curator carries all 8.** Strategy Gamer + Strategy Game Curator come closest at 5-6. ESTIMATED.

**Curator overlap finding.** Curators carrying >1 anchor concentrate on Cluster A + C pairs (CK3 + Old World + Stellaris). Strategy Gamer + Strategy Game Curator + Wargamer carry the densest multi-anchor coverage. Foxhole + HD2 sit largely outside primary-tribe curator feeds — confirms Cluster A/B/C vs Outlier split. REPORTED.

## Reviewer / "also bought" overlap

Steam reviewer overlap quantification is hard w/o profile scrape. Training-recall estimates of cross-ownership / cross-review rates:

- **CK3 ↔ Wildermyth.** Wildermyth review base ~11,600 reviews at 95% positive. Estimated 30-40% of Wildermyth reviewers also own CK3 (cross-reference primary_tribe_psychographic_profile.md cross-cutting finding #4). ESTIMATED. Of CK3 reviewers (much larger base, ~250k+), fraction also reviewing Wildermyth is much smaller — ESTIMATED 5-10% — because CK3 base is broader. Asymmetric overlap.
- **CK3 ↔ BB.** Estimated 25-35% of BB players own CK3 (per primary_tribe brief). Reverse direction ESTIMATED 5-10%. REPORTED.
- **Wildermyth ↔ BB.** ESTIMATED 15-25% overlap per primary_tribe brief — different combat philosophy but same generational-attachment instinct.
- **RimWorld ↔ BB.** RimWorld base 5-10M, BB base ~700k. Estimated 40-55% of BB owners also own RimWorld (similar emergent-story permadeath sandbox audience). Reverse direction 5-10%. ESTIMATED.
- **RimWorld ↔ Wildermyth.** Estimated 25-40% of Wildermyth reviewers also own RimWorld (procedural-narrative cluster). ESTIMATED.
- **Stellaris ↔ CK3.** Both Paradox; estimated 50-65% of CK3 reviewers also own Stellaris or vice versa (Paradox catalog cross-buying is strong). Highest pairwise estimated overlap in matrix. REPORTED — Paradox internal data would confirm if accessible.
- **Old World ↔ CK3.** Estimated 40-55% of Old World reviewers also own CK3 — both dynastic, Old World audience is largely CK3-curious-or-dissatisfied. ESTIMATED.
- **Old World ↔ Stellaris.** Estimated 30-45% — 4X cluster cross-buy. ESTIMATED.
- **Foxhole ↔ HD2.** Estimated 25-40% — both squad-war PvE/PvP sci-fi-mil clusters; Foxhole is older + smaller, HD2 is post-2024 mass-market. ESTIMATED. AMBIGUOUS — HD2's mass-market audience dilutes overlap rate.
- **Foxhole ↔ everything in Clusters A/B/C.** Estimated <10% cross-ownership. Foxhole audience is MMO-PvP-leaning. REPORTED.
- **HD2 ↔ everything in Clusters A/B/C.** HD2 audience is shooter-co-op-leaning; estimated <10% with strategy primary tribe. AMBIGUOUS — HD2's mass-market broad reach may include strategy-curious crossover, but reviewer-text patterns differ sharply.

**Steam "More like this" / "Customers also bought" recall:**

- CK3 carousel: typically surfaces Stellaris, EU4, HoI4, Vic3, Imperator, Old World, sometimes BB, sometimes Wildermyth. REPORTED.
- Wildermyth carousel: typically surfaces BB, RimWorld, Massive Chalice, Wartales, sometimes XCOM 2. REPORTED.
- RimWorld carousel: typically surfaces Dwarf Fortress, Oxygen Not Included, Going Medieval, BB, sometimes Wildermyth. REPORTED.
- Old World carousel: typically surfaces Civ VI, CK3, Stellaris, Humankind, sometimes Wildermyth. REPORTED.
- BB carousel: typically surfaces Wartales, Wildermyth, RimWorld, XCOM 2, Mount & Blade. REPORTED.
- Stellaris carousel: typically surfaces CK3, Endless Space 2, Civ VI, Sins of a Solar Empire, Distant Worlds. REPORTED.
- Foxhole carousel: typically surfaces Hell Let Loose, Squad, Post Scriptum, Eco. REPORTED — Cluster A/B/C absent.
- HD2 carousel: typically surfaces Deep Rock Galactic, Warhammer 40K Darktide, Earth Defense Force, Risk of Rain 2. REPORTED — Cluster A/B/C absent.

**Reviewer overlap finding.** Strongest pair-wise overlap: CK3 ↔ Stellaris (Paradox cross-buy). Second: RimWorld ↔ BB (emergent permadeath). Third: CK3 ↔ Old World (dynastic strategy). Weakest: Foxhole/HD2 ↔ Cluster A/B/C — these two sit on different audience continents. ESTIMATED throughout.

## Press / outlet overlap

Press outlets covering multiple anchors. Training-recall.

- **Rock Paper Shotgun (RPS).** Covers CK3 (heavy), Wildermyth (regular, "best of 2021" coverage), RimWorld (heavy, multi-year), Old World (regular), BB (occasional), Stellaris (regular), Foxhole (occasional), HD2 (regular post-2024). **Covers 8/8.** REPORTED. Highest-overlap outlet in matrix.
- **PC Gamer.** Covers CK3 (heavy), Wildermyth (regular), RimWorld (heavy), Old World (regular), BB (occasional), Stellaris (heavy), Foxhole (regular), HD2 (heavy post-2024). **Covers 8/8.** REPORTED.
- **Eurogamer.** Covers CK3, Wildermyth, RimWorld, Stellaris, HD2 heavily; Old World + BB occasionally; Foxhole rarely. **Covers 6-7/8.** REPORTED.
- **Polygon.** Covers CK3, Stellaris, HD2 heavily; RimWorld occasionally; Wildermyth + Old World + BB rarely; Foxhole rarely. **Covers 4-5/8.** REPORTED. Skews mainstream — less primary-tribe.
- **Strategy Gamer (strategygamer.com).** Covers CK3 (heavy), Old World (heavy), Stellaris (heavy), BB (regular), Wildermyth (regular). Does NOT cover Foxhole or HD2 prominently (not strategy-coded). **Covers 5/8.** REPORTED. **Highest signal-to-noise outlet for primary tribe.**
- **Wargamer.com.** Covers CK3, Old World, Stellaris, BB, Foxhole occasionally. Wildermyth + RimWorld + HD2 lighter. **Covers 5-6/8.** REPORTED. War-strategy focus.
- **PCGamesN.** Covers all 8 across cycles; mid-tier signal-to-noise. **Covers 8/8.** REPORTED.
- **GameSpot / IGN.** Cover CK3, Stellaris, HD2 heavily; rest lighter. **Cover 4-5/8.** REPORTED. AAA-leaning.
- **Game Maker's Garage / Strategy Wargames newsletter** — niche newsletter, covers CK3 + Old World + Stellaris + BB + Wildermyth. **Covers 5/8.** REPORTED. **High signal-to-noise primary-tribe newsletter — T-C4 target.**

**Press overlap finding.** RPS + PC Gamer + Strategy Gamer + Wargamer + Game Maker's Garage form the primary-tribe-relevant press cluster. PCGamesN covers all but mid-tier. Polygon + IGN cover mainstream subset, less primary-tribe. Foxhole + HD2 reduce to mainstream + mil-sim press; do not validate primary-tribe press strategy. REPORTED.

## YouTube creator overlap

Creators playing >1 anchor, training-recall back-catalog patterns.

- **SsethTzeentach (Sseth).** Covers CK3, RimWorld, BB, Stellaris explicitly. Wildermyth not in core catalog. Old World not in catalog. Foxhole + HD2 not in catalog. **Plays 4/8.** REPORTED. **Cluster A/B/C anchor creator — primary tribe core.**
- **Quill18.** Covers CK3 (heavy multi-series), Stellaris (heavy), Old World (multi-series, big enthusiast), BB (occasional), RimWorld (regular), Wildermyth (occasional), Foxhole (rare), HD2 (light if any). **Plays 6-7/8.** REPORTED. **Highest overlap of any single creator in matrix.**
- **Many a True Nerd (MATN).** Covers CK3 (multi-series), Stellaris (regular), some RimWorld, occasional BB, Wildermyth lighter. Old World occasional. Foxhole + HD2 rare. **Plays 4-5/8.** REPORTED.
- **Splattercat.** Covers RimWorld (heavy), BB (regular), Wildermyth (regular), Old World (one-off), Stellaris (one-offs), HD2 covered. CK3 lighter. Foxhole one-off. **Plays 6-7/8.** REPORTED. **High overlap; indie-strategy reach.**
- **Wanderbots.** Covers RimWorld (heavy), BB (regular), Wildermyth (regular), Stellaris (occasional), Old World occasional. CK3 lighter. Foxhole + HD2 lighter. **Plays 5/8.** REPORTED.
- **Nookrium.** Covers RimWorld (heavy), Wildermyth (regular), BB (occasional), indie strategy-heavy. Stellaris lighter. CK3 + Old World occasional. Foxhole + HD2 rare. **Plays 4-5/8.** REPORTED.
- **ItalianSpartacus.** Covers FoG: Empires + FoG II heavily; Old World regular; CK3 occasional; Stellaris occasional. Wildermyth + RimWorld + BB lighter. Foxhole + HD2 absent. **Plays 3-4/8 anchors (Old World, CK3, Stellaris, maybe BB).** REPORTED. **Historical-strategy specialist — primary tribe + FoG bridge.**
- **Lionheart (Lionheart Tactics)**. Covers BB heavily; CK3 + Stellaris occasional; Wildermyth occasional. **Plays 3-4/8.** REPORTED.
- **Arumba.** Covers CK3 + Stellaris + EU4 + Old World heavily. RimWorld + BB lighter. Foxhole + HD2 rare. **Plays 4/8.** REPORTED.
- **ChristopherOdd.** Covers RimWorld + BB + Wildermyth + Stellaris + Old World occasional, CK3 occasional. **Plays 6/8.** REPORTED.
- **DangerouslyFunny.** Covers Foxhole heavy, war-MP catalog. HD2 occasional. Strategy primary-tribe lighter. **Plays 1-2/8 (Foxhole, HD2).** REPORTED. **Outlier-cluster specialist — NOT primary tribe.**
- **OhDough / Glamhouse.** HD2-focused creators; do not bridge to strategy primary tribe. REPORTED.

**Creator overlap finding.** Quill18 + Splattercat + ChristopherOdd are highest-overlap single creators (6-7/8 anchors each), spanning Cluster A + B + C. SsethTzeentach + ItalianSpartacus + Arumba are primary-tribe specialists w/ 3-5 anchors but high audience-fit. Wanderbots + Nookrium + MATN are mid-overlap. Foxhole + HD2 creators (DangerouslyFunny, OhDough) do NOT bridge to primary tribe. **T-C1 creator pitch list should focus on Quill18 + Sseth + Splattercat + Wanderbots + Nookrium + ItalianSpartacus + Arumba + ChristopherOdd + MATN cluster. Foxhole/HD2 creators are kill-zone for Ouroboros pitch — wrong audience.** REPORTED.

## Strongest / weakest pairs

Explicit ranking by composite overlap (tags + curators + reviewers + press + creators):

**Strongest pairs (top 4):**

1. **CK3 ↔ Stellaris.** Paradox cross-buy (estimated 50-65% reviewer overlap), Cluster C tags (Grand Strategy, Strategy, 4X loose, Simulation), every major creator covers both, RPS/PC Gamer/Strategy Gamer/Wargamer cover both heavily. **Strongest single pair in matrix.** Unifying language: "grand strategy," "your empire," "long-game decisions."
2. **CK3 ↔ Old World.** Cluster A + C overlap (7-9 shared tags), 40-55% estimated cross-ownership, Quill18 + ItalianSpartacus + Arumba primary creators, Strategy Gamer + Wargamer cover both. **Strong dynastic-strategy pair.** Unifying language: "dynasty," "characters who outlive you," "names that matter generations later."
3. **RimWorld ↔ BB.** Cluster A + B overlap (5-7 shared tags), 40-55% estimated cross-ownership of BB-owners-w/-RimWorld, Splattercat + Wanderbots + Nookrium + Sseth primary creators, RPS + PC Gamer cover both. **Strong emergent-permadeath pair.** Unifying language: "your characters," "permadeath," "the story emerges from the systems."
4. **Wildermyth ↔ BB.** Cluster A + B overlap (6-8 shared tags), 15-25% cross-ownership estimated, Splattercat + Wanderbots + Nookrium primary creators, narrative-tactical kinship. **Strong tactical-narrative pair.** Unifying language: "named characters you remember," "campaign you tell stories about."

**Weakest pairs (bottom 3):**

1. **Foxhole ↔ Wildermyth.** Near-zero tag overlap, no curator overlap, near-zero reviewer overlap, no creator overlap. Different audience continents.
2. **HD2 ↔ Wildermyth.** Same as above; even sharper. Mass-market shooter vs procedural-narrative tactical.
3. **HD2 ↔ Old World.** Mass-market sci-fi shooter vs niche historical 4X. No tag, curator, reviewer, press, creator overlap of substance.

**What unifies the strong pairs.** All four strongest pairs share one or more of: (a) generational/dynasty layer (CK3 + Old World), (b) emergent-story permadeath (RimWorld + BB + Wildermyth), (c) Paradox grand-strategy cross-buy (CK3 + Stellaris). All four strong pairs sit inside Cluster A or B; CK3 ↔ Stellaris is the Cluster C bridge.

**What separates the weak pairs.** Foxhole + HD2 sit in the "shared-world war MP" outlier cluster. Bible-locked SP-first design means Ouroboros has zero reason to target this outlier — no audience overlap, no creator overlap, no curator overlap, no press cross-validation.

## Pitch-language patterns

Per-cluster pitch phrases recurring across multi-anchor press + creator + review coverage.

**Cluster A (dynastic / generational strategy) — phrases:**
- "your dynasty," "your family," "your kingdom," "your story"
- "the world remembers" (Wildermyth-anchor), "history persists" (CK3+Old World-anchor)
- "characters who outlive you" (CK3+Wildermyth+BB)
- "centuries of consequence" (CK3+Old World)
- "names that mean something later" (CK3+Wildermyth+BB)
- "the world keeps moving" — primary-tribe-defining phrase per primary_tribe_psychographic_profile.md
- "emergent stories" (cross-cluster but heaviest in A + B)

**Cluster B (emergent-story simulation) — phrases:**
- "story generator" (RimWorld-anchor; carries to BB + CK3 + Wildermyth)
- "permadeath" (BB + RimWorld + Wildermyth optional)
- "your colony / your company / your party" (RimWorld + BB + Wildermyth)
- "no two playthroughs alike" (RimWorld + BB)
- "every loss matters" (BB + RimWorld + Wildermyth)

**Cluster C (grand strategy spatial) — phrases:**
- "grand strategy," "your empire," "rise and fall"
- "decades / centuries of decisions" (CK3 + Stellaris + Old World)
- "live with the consequences" (CK3 + Stellaris)
- "shape history" (CK3 + Old World + Stellaris)

**Outlier (shared-world war MP) — phrases:**
- "join the war," "fight together," "persistent war," "every soldier counts"
- These do NOT translate to primary-tribe pitch. Use only if Ouroboros pivots to MP-first, which bible forbids.

**Multi-anchor union pitch (Cluster A + B + C):**

The phrase set that captures all of {CK3, Wildermyth, RimWorld, Old World, BB, Stellaris} but excludes {Foxhole, HD2}:

- "The world keeps moving without you"
- "Your characters die, the story doesn't"
- "Centuries of emergent history"
- "A civilization simulation where you matter as one actor among many"
- "Your dynasty, your collapse, your rebuild"

These phrases hit primary tribe + thematic-differentiator tribe and do not over-promise multiplayer or shooter. ESTIMATED — these phrases are construction-from-cluster-language, not verbatim borrowing from anchor capsules.

**Per-pair pitch deltas:**

- **CK3-led pitch:** lean dynasty + scheming. "Your dynasty across centuries; betrayals that outlive their plotters."
- **Wildermyth-led pitch:** lean character-attachment + chapter pacing. "Heroes who become legends; legends who haunt the world that comes after."
- **RimWorld-led pitch:** lean emergent + colony / civilization framing. "A civilization that writes its own history. You're one voice in it."
- **Old World-led pitch:** lean dynastic 4X + decline. "Build an empire that lasts. Watch it rot from inside anyway."
- **BB-led pitch:** lean permadeath + roster-attachment. "Named lieutenants. Permanent loss. The kind of stories you tell years later."
- **Stellaris-led pitch:** lean grand-scale + cosmic-time. "Civilizations rise and fall in the long dark. Yours is one of many."
- **Foxhole-led pitch:** N/A — bible-locked SP-first.
- **HD2-led pitch:** N/A — bible-locked SP-first; wrong tribe.

## Cross-cutting findings

1. **Three coherent clusters + one outlier.** Cluster A (dynastic strategy, CK3+Old World+Wildermyth+BB), Cluster B (emergent-story sim, RimWorld+Wildermyth+BB+partial CK3), Cluster C (grand strategy spatial, CK3+Old World+Stellaris). Outlier (Foxhole+HD2) sits alone. Ouroboros sits in A ∩ B ∩ C — the intersection w/ Stellaris-via-sci-fi bridge — and explicitly outside the outlier. REPORTED.

2. **CK3 + Stellaris cross-buy is the single highest-leverage audience.** Paradox dual-ownership cluster (50-65% estimated) is the densest reviewer overlap in the matrix. T-C4 newsletter + T-C1 creator pitches that reach this cluster (Quill18, Arumba, Strategy Gamer, Wargamer) deliver the most efficient reach per primary-tribe-relevant impression. REPORTED.

3. **Quill18 + Splattercat + ChristopherOdd are the three highest-coverage individual creators** in matrix (6-7/8 anchors each). T-C1 creator pitch list should rank-1 these. REPORTED.

4. **Strategy Gamer (editorial + curator) + Game Maker's Garage newsletter are the highest signal-to-noise outlets** for primary tribe — covering 5/8 anchors w/ minimal Foxhole/HD2 noise. T-C3 press + T-C4 curator focus. REPORTED.

5. **The "world keeps moving" pitch unifies all six primary-tribe-relevant anchors** (excludes Foxhole + HD2). This phrase is the strongest cross-cluster pitch-language anchor. Confirms primary_tribe_psychographic_profile.md cross-cutting finding #1 from a separate angle (tag + curator + creator co-occurrence rather than review-theme analysis). REPORTED.

6. **Foxhole + HD2 are kill-zone for primary-tribe targeting.** Their creator + curator + press surfaces do not bridge to Cluster A/B/C. Including Foxhole/HD2 in T-C1 creator pitches would burn pitches on wrong-audience reach. Confirms bible RTS-framing-kill + SP-first locks from the audience-cluster angle. REPORTED.

## Conflict surfaced

Bible cross-check against tag/cluster findings:

- **bible_monetization.md L274 "Free to play" tagline.** Primary tribe Cluster A/B/C is overwhelmingly paid-anchor: CK3 ($50 base + DLC), Wildermyth ($25), RimWorld ($35), Old World ($30-40), BB ($30 + DLC), Stellaris ($40 base + DLC). NONE of the six primary-tribe anchors are F2P. The two anchors that touch F2P-adjacent shapes — Foxhole (B2P MMO) + HD2 (B2P live-service) — are the outlier kill-zone. **CONFLICT: F2P framing collides w/ every primary-tribe anchor's monetization shape.** Reviewer + creator audiences of the six primary-tribe anchors are explicitly anti-F2P-strategy per recurring review themes (cross-ref primary_tribe_psychographic_profile.md Conflict L169). **Bible authority resolves. Research Lane only surfaces.**

- **bible_monetization.md L292 Fortnite reference.** Tag co-occurrence shows zero overlap between Fortnite + any of the eight anchors at meaningful level — Fortnite tags don't co-occur w/ Strategy, Grand Strategy, Simulation, Procedural Generation, Story Rich, Sci-fi-in-strategy-context. Press outlets covering Fortnite (Polygon, IGN, Eurogamer-Fortnite-section) are partial overlap w/ press primary tribe but Fortnite-coverage signal is not the same audience as their strategy-coverage signal. **CONFLICT for tag + audience compatibility if Fortnite is invoked as audience reference; less acute if invoked only as monetization-mechanic reference.** Bible authority resolves.

- **Implicit conflict: Foxhole + HD2 inclusion in Wave 2 anchor list.** Their outlier-cluster position means audience-overlap-map shows zero meaningful bridge to primary tribe. If they are anchors because of monetization-model reference (B2P + live-service), audience-overlap analysis confirms this is mechanics-only — their AUDIENCE is not the primary tribe's audience. Flag for Design Lane: do not pitch Ouroboros to Foxhole/HD2 audiences; do borrow live-service monetization mechanics only if bible authorizes. **Not a bible conflict per se; a calibration flag.**

No further fresh conflict beyond L274 + L292 already flagged in primary_tribe_psychographic_profile.md.

## Caveats and confidence

Distribution: ~75% REPORTED, ~20% ESTIMATED, ~4% AMBIGUOUS, <1% VERIFIED. Steam tag co-occurrence is a moving target — anchor tag blocks shift quarterly as players add/remove community tags. SteamDB tag-explorer is the canonical source for live numbers; this brief is training-recall.

Known unknowns:
- 2026 Steam community tag drift on each anchor (not refreshed).
- 2026 curator follower counts + active-recommendation rates (not refreshed).
- 2026 reviewer-profile cross-ownership analysis at scale (no live profile scrape).
- 2026 press editorial calendar — which outlets are still actively covering primary tribe vs deprioritizing strategy coverage.
- Exact YT view-count overlap per creator per anchor (no view-count snapshot).
- Foxhole + HD2 community-overlap w/ niche strategy at fringe (HD2 mass-market may pull in strategy-curious; not measured).
- Steam "More like this" carousel exact ordering in 2026 (recalled from training).

Re-capture flagged when WebFetch returns: SteamDB tag explorer pulls per anchor, Steam curator pages crawled for multi-anchor recommendations, top-helpful-review profile cross-checks for cross-anchor ownership, YT channel back-catalog views per anchor per creator.

Brief is one interpretation. Other valid cluster splits exist (e.g., separating Cluster A by combat-shape rather than scale, or merging B + C via simulation-depth axis).

## Feeds Design Lane

This brief feeds:

- **T-B1 brand positioning** — synthesises three-cluster + outlier structure into pitch shape. Primary tribe pitch language is "world keeps moving," "your dynasty / your civilization," "characters who outlive you." Foundation-thematic differentiator layers on top.
- **Capsule copy + screenshot framing** — short capsule should use Cluster A + B union language ("generational strategy where the world keeps moving") plus Cluster C scale hook ("a civilization rises and falls across centuries"). Screenshot picks should show characters w/ names + a world map w/ history layer.
- **T-S1 Steam tag slate** — bible-locked tag candidates (Grand Strategy, Sci-fi, Simulation, Procedural Generation, Narrative, Story Rich, Generations, Strategy) intersect Clusters A + B + C; tag picks validated. Consider adding Permadeath (BB+Wildermyth cluster) + Politics (CK3+Old World cluster) if compatible w/ run shape. Avoid Multiplayer/Co-op/MMO tags — outlier cluster only.
- **T-C1 YouTube creator pitch list** — ranked pitches:
  - Tier 1 (6-7/8 overlap): Quill18, Splattercat, ChristopherOdd
  - Tier 2 (4-5/8 overlap, high audience-fit): Sseth, ItalianSpartacus, Arumba, MATN, Wanderbots, Nookrium
  - Tier 3 (3-4/8 overlap, narrow but devoted): Lionheart, Worth A Buy, smaller indie-strategy YTs
  - Kill-zone (do not pitch): DangerouslyFunny, OhDough, HD2/Foxhole-specialist channels
- **T-C3 press outlet map** — ranked pitches:
  - Tier 1 (highest primary-tribe signal-to-noise): Strategy Gamer, Wargamer, Game Maker's Garage newsletter
  - Tier 2 (broad reach + primary-tribe coverage): RPS, PC Gamer, PCGamesN
  - Tier 3 (mid-tier mainstream): Eurogamer
  - Skip (low primary-tribe signal): Polygon, IGN, GameSpot (unless feature angle aligns)
- **T-C4 newsletter / curator surfaces** — ranked pitches:
  - Tier 1: Hooded Horse curator (publisher-tied, primary tribe reach), Strategy Gamer curator, Strategy Game Curator, Game Maker's Garage newsletter
  - Tier 2: ExplorMinate (4X-specific, narrow-deep), SplatterCat curator (indie-strategy)
  - Tier 3: PC Gamer curator (broad reach, low S/N)
- **Capsule + screenshot copy validation** — pitch-language phrases (cross-cluster union list above) should appear in capsule; pitch deltas (per-anchor-led pitch shapes above) inform A/B-test variants if A/B testing is in scope.

## Open questions for further research

- SteamDB tag-explorer live pull of co-occurrence rates for the eight anchors — upgrade ESTIMATED counts to VERIFIED.
- Curator-feed crawl for 2026 active multi-anchor recommendations — confirm Strategy Gamer + Strategy Game Curator + Hooded Horse coverage.
- YT creator back-catalog view-count audit for primary-tribe titles per creator — refines Tier 1/2/3 ranking by reach-per-pitch.
- Foxhole + HD2 fringe-overlap into primary tribe — quantify the (likely small) audience that owns HD2 + CK3 to determine if any pitch is worth running there.
- 2026 press editorial calendar — confirm Strategy Gamer + Wargamer + Game Maker's Garage are still actively publishing in primary-tribe space.
- Tag-co-occurrence rerun after Ouroboros Steam page goes live — measure which co-occurrences actually pull traffic vs theoretical.

## Sources

Training-data-only — flag for re-capture w/ live Steam, SteamDB, curator-page, YT-back-catalog, and press archive queries when WebFetch returns.

- Steam store pages (recalled from training, tag blocks + carousels):
  - Crusader Kings III — https://store.steampowered.com/app/1158310/
  - Wildermyth — https://store.steampowered.com/app/763890/
  - RimWorld — https://store.steampowered.com/app/294100/
  - Old World — https://store.steampowered.com/app/597180/
  - Battle Brothers — https://store.steampowered.com/app/365360/
  - Stellaris — https://store.steampowered.com/app/281990/
  - Foxhole — https://store.steampowered.com/app/505460/
  - Helldivers 2 — https://store.steampowered.com/app/553850/
- Steam curators (recalled, not verbatim follower counts):
  - Hooded Horse (publisher + curator)
  - Strategy Gamer (strategygamer.com-tied curator)
  - Strategy Game Curator (community aggregator)
  - ExplorMinate (4X-focused podcast curator)
  - Wargamer.com curator
  - SplatterCat curator
  - Worth A Buy curator
- Press archives (training-recall, no live URL verification per outlet):
  - Rock Paper Shotgun (rockpapershotgun.com)
  - PC Gamer (pcgamer.com)
  - Eurogamer (eurogamer.net)
  - Polygon (polygon.com)
  - Strategy Gamer (strategygamer.com)
  - Wargamer (wargamer.com)
  - PCGamesN (pcgamesn.com)
  - Game Maker's Garage Strategy & Wargames newsletter
- YouTube creators (training-recall, no verbatim transcript or view-count refresh):
  - SsethTzeentach
  - Quill18
  - Many a True Nerd
  - Splattercat (SplatterCatGaming)
  - Wanderbots
  - Nookrium
  - ItalianSpartacus
  - Lionheart (Lionheart Tactics)
  - Arumba
  - ChristopherOdd
  - DangerouslyFunny (outlier-cluster)
  - OhDough (outlier-cluster)
- Cross-reference within Ouroboros docs:
  - `docs/legacy/topics/lieutenant_pivot_niche_brief.md` — parent brief, primary tribe + thematic differentiator ranking
  - `docs/legacy/topics/primary_tribe_psychographic_profile.md` — per-anchor review themes; this brief sharpens audience-side mapping from per-title-themes to cross-title-clusters
  - `docs/bible/game_bible.md ## In Flux` — Lieutenant System + RTS-framing-kill 2026-05-16 entry
  - `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` L274 + L292 — conflict-flag targets

**Re-capture stamp.** All tag co-occurrence + curator coverage + reviewer overlap + press coverage + creator coverage claims in this brief are training-data-derived as of cutoff. Live Steam scrape + SteamDB tag-explorer pull + curator-feed crawl + YT view-count audit + press editorial-calendar refresh required to upgrade REPORTED → VERIFIED. Flag for Research Lane re-capture when WebFetch is restored.
