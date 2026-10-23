---
name: Multiplayer Session-Model Precedents
description: Four-archetype comparison of multiplayer session models in strategy/sim/tactical games (per-mission co-op, persistent shared world lockstep, persistent shared world server-authoritative, asynchronous play-by-cloud). Combines technical session-model matrix with commercial validation data. Feeds Design Lane WS2/WS4 multiplayer forks.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane capture of 2026-05-16 Design Lane sub-agent research (two sub-agents combined; originating chat 596bc13e Design Lane session)
---

# Multiplayer Session-Model Precedents

## What this brief is

A two-part survey of multiplayer session-model precedents combining (a) a technical comparison matrix of the operational mechanics of representative session models — Steam Datagram Relay as transport substrate, Stellaris and Paradox titles as host-authoritative lockstep, Crusader Kings 3 / Europa Universalis 4 as adjacent lockstep, Foxhole as server-authoritative continuous, Arma Reforger as dedicated-server real-time, and Old World as asynchronous turn-based — and (b) a commercial validation read across four session-model archetypes with per-title sales, concurrent-user, and review data. The brief feeds Design Lane WS2 (multiplayer session-model substrate — already resolved as per-mission co-op per `docs/bible/game_bible.md ## In Flux`) and WS4 (multiplayer remaining forks F2 through F9, currently parked).

Data current as of May 2026. Sales and CCU numbers are rounded. Where a number is unknown, marked "unk." Confidence is REPORTED across most line items — primary publisher figures are flagged where available; the remainder are aggregated from SteamDB, Steambase, Steam Revenue Calculator, Gamalytic, SteamSpy, and adjacent press.

## Part 1 — Technical session-model matrix

The originating research compared six representative implementations across nine technical dimensions.

### Steam Datagram Relay (Valve)

Steam Datagram Relay is a transport layer rather than a session model. It carries peer-to-peer or game-to-dedicated traffic over Valve's backbone. Steam Datagram Relay does not address time or speed synchronization, pause authority, desync handling, save model, drop-in / drop-out, or multi-human-per-faction questions — those live above the transport. Steam Datagram Relay adds one relay hop; Valve's published material indicates the relay often beats direct routes on long paths. Traffic is encrypted and authenticated via SteamID; IP addresses are hidden between peers; the connection is rate-limited. Steam Ping Location can be used for latency estimation. No documented hard cap on simultaneous connections. The originating research's note: every game using "dedicated servers" still runs that server infrastructure itself; Steam Datagram Relay only solves the transport portion of the problem. Confidence: VERIFIED per Steamworks documentation and the public GameNetworkingSockets repository.

### Stellaris (Paradox Development Studio)

Stellaris uses a persistent shared galaxy with host-authoritative lockstep and a lobby flow with host-controlled start. Time and speed control is host-only; the engine runs lockstep at 10 turns per in-game day. Pause authority is shared — any player can pause, with a documented approximately 30-second cooldown before anyone can unpause. Desync handling is via lockstep checksum compared per-tick; mismatch raises an out-of-sync error and disconnects affected players; recovery is reload from the last sync save. Known desync regressions surfaced after the 4.0 and BioGenesis content updates. Save model is a single shared save on the host; rehosting from save is standard recovery. Drop-in / drop-out is supported via reconnect with AI fill of the missing slot mid-session. Multi-human-per-faction is not natively supported. Infrastructure is host-PC authority with Paradox cloud-lobby options. Typical player count is approximately 32 (the lockstep scaling limit). Lockstep amplifies worst-player latency; large-population events drive desync rate spikes. Confidence: REPORTED per PCGamesN multiplayer guide plus gamepressure post-4.0 coverage plus Stellaris Steam community threads.

### Crusader Kings 3 and Europa Universalis 4 (Paradox Development Studio)

CK3 and EU4 follow the same Paradox model as Stellaris — lobby plus host save, host-controlled speed, lockstep daily ticks. Each human controls a separate ruler or nation; no in-faction split is natively supported. CK3 Steam discussions indicate a "gentleman's agreement" community workaround where multiple humans coordinate decisions within a faction without engine support. AI takeover fills a disconnected slot until rejoin. EU4 also runs Nakama backend since version 1.30.6 in addition to host-PC authority. Documented pattern: 30-second unpause cooldown matching the Stellaris design. Known caveat: AI takeover can crash non-host clients in some patches. Confidence: REPORTED per Paradox forums and EU4 wiki.

### Foxhole (Siege Camp)

Foxhole uses a persistent shared world with dev-hosted dedicated servers stitching 53 hex-region maps into a single war. Time and speed are real-time only with no speed control — the world runs continuously 24/7 for weeks. There is no pause. Server-authoritative architecture handles desync at the protocol layer; no client lockstep is exposed. Save model is server-side persistent state; players have no client saves. Drop-in / drop-out is free at any time; players log in and out across days and weeks. Multi-human-per-faction is the core model — 150 to 180 players per server per faction, up to approximately 4,000 concurrent across regions in a single war. Devblog 68 documents the hex-stitching infrastructure in Unreal Engine. A war runs 3 to 5 weeks on average and may run longer; faction lock holds for the entire war. Confidence: REPORTED per Foxhole FAQ and ModDB devblog.

### Arma Reforger (Bohemia Interactive)

Arma Reforger uses a lobby flow with community-rented dedicated servers; the Bohemia backend handles matchmaking and authentication. Real-time only with server tick. Server-authoritative. Save model is server-side scenario state with no default campaign persistence. Drop-in / drop-out via slot-based reconnection. Multi-human-per-faction via squad-based organization; up to 128 players per server with most tuning at 32 to 64. UDP transport with public-IP dedicated servers plus Bohemia backend microservices. AI fill via the aiLimit server setting. Caveat: backend outages disable multiplayer even on private servers. Confidence: REPORTED per community.bohemia.net wiki.

### Old World (Mohawk Games)

Old World supports hot-seat, asynchronous via cloud-turn, and live lobby up to 4 players. Asynchronous cloud sends turns when ready. No same-civilization split. Drop-in / drop-out is async by design via turn pings. Save model is cloud save per match. Latency is masked entirely by the asynchronous turn model. Confidence: REPORTED per Mohawk Games multiplayer announcement and Co-Optimus coverage.

### Cross-implementation observations

The originating research drew seven observations from the matrix.

Steam Datagram Relay is a transport substrate, not a session model — every persistent-world game in the matrix builds its own server, authentication, and state layer independently of whatever relay it uses.

The two host-PC-authoritative lockstep games (Stellaris and the CK3 / EU4 cluster) trade infrastructure simplicity for desync fragility that scales with simulation complexity. The originating research noted that Ouroboros' batch-tick macro layer would inherit this fragility if the design adopted host-authoritative lockstep.

Both persistent-world games (Stellaris and Foxhole) handle absent players differently — Paradox swaps in AI for a single seat; Foxhole simply keeps the war running with whoever logs in. The architectural divergence reflects whether the seat is a strategic decision-maker (Paradox) or a member of a player pool (Foxhole).

Pause authority diverges sharply between archetypes. Paradox titles allow any player to pause with a cooldown; real-time persistent games (Foxhole, Arma Reforger) have no pause at all. The pause-authority question is a load-bearing fork for any multiplayer strategy game.

"Multiple humans per faction" is rare and only natively solved by team-shooter-shaped games (Foxhole, Arma Reforger) where the faction is a player pool rather than a single decision-maker. Paradox titles defer this question to social convention.

Asynchronous (Old World) and continuous-persistent (Foxhole) both sidestep speed-synchronization entirely by removing the shared real-time clock — opposite ends of the same escape hatch.

Drop-in / drop-out viability tracks the authority model. Server-authoritative games make it trivial. Lockstep host-authoritative games make it a special case requiring AI fill plus rejoin handling.

## Part 2 — Commercial validation by archetype

The originating research grouped session models into four commercial archetypes and surveyed sales, concurrent-user peaks, current concurrent-user bands, review counts, and review scores per representative title.

### Archetype 1 — Per-mission co-op, drop-in tactical

This archetype is the model the 2026-05-16 multiplayer pick adopted (per `docs/bible/game_bible.md ## In Flux` multiplayer entry). The Helldivers 2 / Deep Rock Galactic / Vermintide cluster owns this shape.

Helldivers 2 (Arrowhead, 2024) shipped approximately 20 million+ lifetime units with a peak all-time concurrent-user count of 458,709 and a current 24-hour peak in the approximately 30,000 to 60,000 range. Approximately 1.14 million Steam reviews at Mostly Positive. Estimated approximately $700M+ gross revenue. Multiplayer is the primary draw — the core loop is 4-player co-op. The originating research characterized Helldivers 2 as the largest breakout in the archetype, with the launch ride still continuing at time of capture. Confidence: REPORTED.

Deep Rock Galactic (Ghost Ship Games, 2018 with 1.0 in 2020) achieved approximately 8 million+ lifetime sales with peak approximately 54,000 concurrent users and a current 24-hour peak in the approximately 10,000 to 25,000 range. Approximately 360,000 to 375,000 Steam reviews at Overwhelmingly Positive (approximately 97% positive). Lifetime revenue unknown but characterized as large and sustained. Multiplayer-primary (1 to 4 player co-op). The originating research identifies Deep Rock Galactic as the reference case for "co-op evergreen." Confidence: REPORTED.

Vermintide 2 (Fatshark, 2018) sold an unknown total in the multi-million range with peak approximately 104,000 concurrent users and current 24-hour peak approximately 3,000 to 8,000. Very Positive Steam reviews. Multiplayer-primary 4-player co-op. Long-tail co-op evergreen. Confidence: REPORTED.

Darktide (Fatshark, 2022) is the same-studio same-shape successor. Peak approximately 108,000 concurrent users; current 24-hour peak approximately 5,000 to 15,000. Mixed-to-Mostly Positive reviews. Confidence: REPORTED.

Hell Let Loose (Black Matter / Team17, 2021) sold approximately 2 to 5 million owners with peak approximately 21,800 concurrent users and current 24-hour peak approximately 2,000 to 7,000. Mostly Positive reviews. The originating research notes this title is more PvP-MIL-sim than co-op but session-model adjacent. Confidence: REPORTED.

Squad (Offworld Industries, 2020 1.0 from 2015 early access) sold approximately 6.7 million units with peak 38,573 concurrent users (September 2024) and current 24-hour peak approximately 5,000 to 15,000. Very Positive reviews. Estimated approximately $170M revenue. Multiplayer-primary large-scale tactical PvP, session-based. Confidence: REPORTED.

The originating research's archetype roll-up: lifetime sales across anchors easily clear approximately 40 million combined (Helldivers 2 alone is approximately 20 million; Squad approximately 6.7 million; Deep Rock Galactic approximately 8 million; plus the Vermintide titles and Hell Let Loose at several million each). All-time peak CCU summed approximately 750,000+. Review-score average is Very Positive to Overwhelmingly Positive — the strongest review sentiment of any archetype. Trending up sharply, driven by Helldivers 2 reigniting PvE co-op shooter as a 2024–2026 category. Multiplayer is the primary draw in every anchor — owners-to-multiplayer-engagement ratio approaches 1:1.

### Archetype 2 — Persistent shared world, lockstep host-authoritative (Paradox-shape)

The Paradox catalog defines this archetype. The originating research surveyed the major titles.

Stellaris (Paradox Development Studio, 2016) sold approximately 6 million+ on Steam (and 3 million+ across other platforms in earlier press; Steam totals have grown since). Peak all-time concurrent users 68,510. Current 24-hour peak approximately 15,000 to 30,000. Approximately 193,000 Steam reviews at Very Positive. Steam revenue alone approximately $158M+. Multiplayer is supported but single-player-dominant. The originating research characterized Stellaris as the most relevant anchor for Ouroboros' shape comparisons. Confidence: REPORTED.

Europa Universalis IV (Paradox, 2013) sold an unknown total — known to have cleared 1 million+ by 2016 and likely 5 million+ at time of capture. Peak concurrent users high (approximately 50,000+ range), current 24-hour peak in low thousands. Very Positive Steam reviews. Substantial DLC-engine revenue tail. Single-player dominant. Long DLC tail. Confidence: REPORTED.

Europa Universalis V (Paradox, 2025) is a recent launch; lifetime sales unknown. Peak all-time concurrent users 77,320 (November 4, 2025). Included in Paradox's 23% year-over-year revenue lift in 2025 financial reporting. Recent launch signals franchise health. Confidence: REPORTED per Paradox annual financial filings and SteamDB / WN Hub.

Crusader Kings 3 (Paradox, 2020) sold 4 million+ units across platforms as of April 2025 per Paradox press release. Peak all-time concurrent users 98,695. Current 24-hour peak approximately 10,000 to 30,000. Very Positive Steam reviews. Substantial revenue. Same Paradox single-player-majority pattern. Confidence: VERIFIED on the 4M figure per primary publisher disclosure.

Hearts of Iron IV (Paradox, 2016) sold 7 million+ on Steam as of November 2025. Peak approximately 93,000 concurrent users (November 2024). Current 24-hour peak approximately 30,000 to 40,000. Very Positive reviews. Substantial revenue. Strong WW2 multiplayer community but still single-player majority. Confidence: REPORTED.

Civilization VI (Firaxis / 2K, 2016) sold approximately 10 to 11 million units (Steam approximately 10.2 million). Peak all-time concurrent users 162,657. Current 24-hour peak approximately 30,000 to 50,000. Very Positive reviews. Steam revenue approximately $358M. Multiplayer exists but is single-player-dominant; the largest civilization-simulation seller in the matrix. Confidence: REPORTED.

The originating research's archetype roll-up: lifetime sales across anchors approximately 30 million+ combined. All-time peak concurrent-user sum approximately 500,000. Review-score average Very Positive. Trending flat-to-up (EU5 launch at 77,000 CCU shows franchise health; Paradox revenue up 23% year-over-year in 2025). A critical caveat: in this archetype the multiplayer feature is shipped but minority-used. The broad heuristic the originating research cited is roughly 20% of strategy-game owners ever touch multiplayer, and active multiplayer sessions are likely a low single-digit percentage of concurrent users on any given day. Buyers buy these games for the single-player fantasy; multiplayer is a long-tail social mode.

### Archetype 3 — Persistent shared world, server-authoritative continuous (faction-as-team)

Foxhole, EVE Online, and Albion Online represent this archetype.

Foxhole (Siege Camp, 2017 early access through 2022 1.0) sold approximately 2 million owners with peak all-time concurrent 17,704 (February 2026). Current 24-hour peak approximately 3,000 to 7,000. Approximately 51,000 reviews tracked / 29,000 store. Reviews Very Positive to Mostly Positive. Approximately $35M base revenue estimated. Multiplayer is the only mode. The originating research identifies Foxhole as the closest design analog to a persistent-world Ouroboros — though the originating research notes that Foxhole's commercial scale is an order of magnitude smaller than Archetype 1 or 2. Confidence: REPORTED.

EVE Online (CCP Games, 2003) operates on subscription/free-to-play hybrid. Steam peak modest at approximately 5,000 to 7,000; total concurrent across all clients approximately 24,000 to 40,000. Monthly active users approximately 26,000 to 42,000 concurrent. Steam-side review count unknown; Mostly Positive. Approximately $300M+ lifetime revenue; approximately $70M in 2025. Multiplayer-primary; the originating research characterizes EVE as the "extreme survivor case" at 22 years of operation. Confidence: REPORTED.

Albion Online (Sandbox Interactive, 2017 with Steam 2018) is free-to-play. Steam peak approximately 27,000 (April 2024); total daily active users approximately 350,000 across all clients (May 2024). Steam 24-hour peak approximately 5,000 to 10,000. Mixed to Mostly Positive reviews. Revenue unknown. Multiplayer-primary sandbox MMO with faction warfare components. Confidence: REPORTED.

Conqueror's Blade (Booming Games, 2019) is free-to-play. Peak all-time concurrent approximately 19,000 on Steam, current 24-hour peak approximately 1,000 to 3,000. Mixed reviews. Multiplayer-primary MMO strategy. Trending down. Confidence: REPORTED.

The originating research's archetype roll-up: lifetime sales / owners approximately 5 million for Foxhole plus free-to-play monthly active users for EVE and Albion. Combined all-time peak Steam concurrent approximately 50,000 — an order of magnitude smaller than archetypes 1 and 2. Review-score average Mostly Positive — more polarized and cult-skewing. Trending flat to mildly up (Foxhole hit a fresh all-time peak in February 2026; EVE 2025 revenue rose versus 2024 lows). Every player here engages with multiplayer because there is no single-player mode, but the total addressable market is dramatically smaller than the other persistent archetypes.

### Archetype 4 — Asynchronous / play-by-cloud

Civilization VI's Play By Cloud mode, Civilization V's third-party play-by-email plus hot-seat, Old World, and Total War's turn-based asynchronous embed represent this archetype.

Civilization VI Play By Cloud mode (rolled up in the Civ VI line above for sales) has mode-level usage unknown. The originating research notes that the community describes Play By Cloud as a "failure" — buggy, disabled at times, per Bleeding Cool coverage. Confidence: REPORTED.

Civilization V's play-by-email mode is active via the Play Your Damn Turn third-party community service. The franchise lifetime is approximately 14 million units. Per-mode usage unknown. Confidence: REPORTED.

Old World (Mohawk Games, 2021) sold an unknown small / niche total. Steam concurrent peak under 1,000; current 24-hour peak in the low hundreds. Very Positive reviews. Small revenue. Play-by-cloud is a bonus mode rather than a primary draw. The originating research characterizes Old World as critically loved but commercially niche. Confidence: REPORTED.

Total War (Creative Assembly / Sega, ongoing) franchise sells tens of millions cumulatively. Turn-phase concurrent users are not separable from full-game concurrent users in public data. Async turns are embedded in multiplayer rather than a primary mode. Confidence: REPORTED.

The originating research's archetype roll-up: no standalone commercial anchor at scale. The Civ VI Play By Cloud experience is community-described as broken or abandoned; Old World's mode is a feature on a niche commercially-modest title; third-party services (Play Your Damn Turn) carry the load. Trending flat to down as a primary mode. Review and sales averages are not meaningful at the archetype level — this is a feature, not a genre.

## Cross-archetype observations

The originating research drew nine cross-archetype observations.

The largest total active player population sits in Archetype 1 (per-mission co-op), driven by Helldivers 2's 458,000 peak and Deep Rock Galactic's evergreen 10,000 to 25,000 daily band. Archetype 2 is close on owners but well behind on engaged multiplayer concurrent users.

The most successful breakout in the last 5 years is Helldivers 2 (2024) at approximately 20 million sales and approximately $700M gross. No other archetype has produced anything in this revenue class since 2021.

Growth is concentrated in co-op PvE shooters (Archetype 1) and the Paradox catalog (Archetype 2 — EU5 launched at 77,000 concurrent users and Paradox 2025 revenue up 23% year-over-year). Archetype 3 is stable but niche. Archetype 4 is dormant as a primary mode.

A survivorship-bias caveat applies. Archetype 1's totals are heavily skewed by one outlier (Helldivers 2 represents approximately half of the archetype's lifetime sales). Stripping Helldivers 2 the archetype averages look much closer to Archetype 2. Similarly Archetype 3 is distorted by EVE Online's 22-year longevity — Foxhole, the only direct shape-analog to a persistent-world Ouroboros, is a small commercial entity at approximately $35M base revenue.

The single-player versus multiplayer usage gap in Archetype 2 is wide. Stellaris, CK3, HoI4, and EU sell millions but active multiplayer concurrent users on any given evening represent a low fraction of total concurrent users. A shipped multiplayer mode in this archetype is rarely the headline reason a copy gets sold; it is a retention and social feature on top of a single-player game.

Foxhole-shape addressable market is the only commercially-validated "persistent shared world, faction-as-team, drop-in" RTS-adjacent title is Foxhole itself. Peak concurrent users approximately 17,000 after 9 years of operation. EVE and Albion are MMOs from a different audience.

Review-score signal: co-op (Archetype 1) consistently rates highest; Paradox (Archetype 2) consistently Very Positive; Foxhole-shape (Archetype 3) more polarized; asynchronous (Archetype 4) too small to read meaningfully.

Genre momentum 2024–2026: co-op shooter up sharply, grand-strategy single-player-with-multiplayer up moderately (EU5 momentum), persistent-world faction MMO flat (Foxhole's 2026 spike is the exception), asynchronous play-by-cloud down or abandoned.

Production cost rough ordering: Archetype 3 carries the highest infrastructure-and-operations burden (24/7 server, faction balance live-ops). Archetype 2 carries the lowest infrastructure burden (host-authoritative). Archetype 1 sits in the middle (matchmaking plus session servers). The originating research presents this as observable market reality rather than recommendation.

## Open questions for further research

- Helldivers 2's retention curve at 12, 18, 24 months post-launch. The $700M figure depends on retention; if the curve looks like Tempest Rising's (collapse after campaign completion), the archetype's robustness is overstated.
- The 20% multiplayer-engagement heuristic for Paradox titles — is this still accurate post-EU5, or has the Paradox audience's multiplayer participation rate shifted with their improved netcode and lobby flow.
- Foxhole's specific revenue model and operating margin — the $35M base revenue figure does not include ongoing live-ops costs. Net contribution per developer-year for a Foxhole-scale operation would calibrate the viability of Archetype 3 for indie scale.
- Steam Datagram Relay performance benchmarks for batch-tick simulation traffic — the originating research treats Steam Datagram Relay as transport-only, but did not run quantitative latency or packet-loss measurements against typical strategy-game payload sizes.
- Old World's play-by-cloud retention specifically — community sentiment on the mode would calibrate whether asynchronous as a feature (rather than primary mode) has commercial viability inside a single-player-dominant strategy title.

## Sources

Technical session-model matrix:

- Steam Datagram Relay (Steamworks) — https://partner.steamgames.com/doc/features/multiplayer/steamdatagramrelay
- GameNetworkingSockets repository — https://github.com/valvesoftware/gamenetworkingsockets
- Stellaris multiplayer guide (PCGamesN) — https://www.pcgamesn.com/stellaris/multiplayer
- Stellaris post-4.0 desyncs (gamepressure) — https://www.gamepressure.com/newsroom/number-of-desyncs-in-stellaris-after-biogenesis-and-40-update-sky/z17e3b
- Europa Universalis IV multiplayer wiki — https://eu4.paradoxwikis.com/Multiplayer
- Foxhole FAQ — https://www.foxholegame.com/faq
- Foxhole Devblog 68 — https://www.moddb.com/games/foxhole/news/devblog-68-making-a-hex-world-logistics-vehicles-and-more
- Arma Reforger server hosting (Bohemia) — https://community.bohemia.net/wiki/Arma_Reforger:Server_Hosting
- Old World multiplayer (Mohawk) — https://mohawkgames.com/2020/09/16/old-world-multiplayer-unlocked/

Commercial validation:

- Helldivers 2 SteamDB — https://steamdb.info/app/553850/charts/
- Helldivers 2 20M sales (Gamingbolt) — https://gamingbolt.com/helldivers-2-reportedly-crossed-20-million-lifetime-sales-this-month
- Deep Rock Galactic Steamcharts — https://steamcharts.com/app/548430
- Stellaris statistics (Levvvel) — https://levvvel.com/stellaris-statistics/
- Paradox 2025 year-end report — https://www.paradoxinteractive.com/investors/financial-reports/year-end-report-january-december-2025
- Paradox FY2025 (InvestGame) — https://investgame.net/news/pdf/2026-04-13-paradox_interactive_annual_report_for_2025_wp/
- EU5 launch peak (SteamDB / WN Hub) — https://wnhub.io/news/stores-and-publishing/item-49217
- Crusader Kings III 4M sales (Paradox press) — https://www.paradoxinteractive.com/media/press-releases/press-release/crusader-kings-iii-passes-four-million-sales
- HoI4 Gamalytic — https://gamalytic.com/game/394360
- Civ VI sales / CCU (Levvvel) — https://levvvel.com/civilization-statistics/
- Foxhole SteamDB — https://steamdb.info/app/505460/charts/
- Foxhole Gamalytic — https://gamalytic.com/game/505460
- EVE Online SteamDB — https://steamdb.info/app/8500/
- CCP Games rebrand (PC Gamer) — https://www.pcgamer.com/gaming-industry/ccp-games-is-no-more-eve-online-studio-changes-its-name-as-it-goes-independent-and-enters-an-ai-research-partnership-with-google-deepmind/
- Albion player count — https://activeplayer.io/albion-online/
- Conqueror's Blade Steamcharts — https://steamcharts.com/app/905370
- Squad Gamalytic — https://gamalytic.com/game/393380
- Hell Let Loose Steamcharts — https://steamcharts.com/app/686810
- Vermintide / Darktide Steamcharts — https://steamcharts.com/app/552500
- Civ VI Play By Cloud critique (Bleeding Cool) — https://bleedingcool.com/games/heres-why-play-by-cloud-multiplayer-isnt-working-in-civilization-vi/
- Play Your Damn Turn — https://www.playyourdamnturn.com/

Originating chat session: `596bc13e-55c8-45e8-a241-86bc59bcf3ce.jsonl` (Design Lane session, 2026-05-16). Originating sub-agents: a14b2f4b6eda29d8f (matrix) and a2bfe3b1ba9a62838 (validation brief).

## Feeds Design Lane

- WS2 multiplayer session-model substrate fork — already resolved 2026-05-16 in `docs/bible/game_bible.md ## In Flux` as per-mission co-op (Archetype 1). This brief is the substrate evidence behind that pick.
- WS4 multiplayer remaining forks F2 through F9 (mission eligibility, invitation model, mid-mission join, DLC parity, chronicle attribution, mission outcome ownership, rewind behavior in co-op, disconnect handling) — parked pending Lieutenant System Q1 cost resolution; this brief is the persistent reference when those forks open.
- Cross-references `docs/legacy/topics/lieutenant_pivot_niche_brief.md` (the audience the multiplayer model serves) and `docs/legacy/topics/delegated_command_precedents.md` (the lieutenant-system substrate the multiplayer co-op model depends on for strategic-depth preservation under unit splitting).
