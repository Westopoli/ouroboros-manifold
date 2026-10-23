---
name: Community Translation Infrastructure
description: Survey of community-driven translation platforms (Crowdin, Lokalise, Weblate, POEditor) and small-team localization precedents (RimWorld, Stardew Valley, Wildermyth, Nebulous: Fleet Command, Paradox grand-strategy mod patterns) for solo/very-small-team niche-strategy paid-base. Cross-axes: setup cost, maintainability, QA risk, credit/recognition. Feeds T-L1 priority slate and CL4 mod/Workshop payoff.
type: topic_brief
captured_at: 2026-05-18
contributor: Research Lane T-L2 sub-agent (no web access — REPORTED/ESTIMATED floor)
---

# Community Translation Infrastructure

## What this brief is

Survey of platforms and precedents for community-driven localization in indie strategy/sim space. Ouroboros = solo or very-small-team niche-strategy paid-base targeting 80-200k primary tribe (generational/legacy) plus secondary Foundation/hard-SF tribe. T-L1 will pick the language priority slate (Simplified Chinese, Russian, German, French, Spanish-LatAm, PT-BR, Polish, Japanese candidates). T-L2 surfaces the infrastructure choices that constrain how many languages are feasible at any tier of investment, who does the work, how QA-risky community output is, and what the credit/recognition shape looks like.

Brief is non-recommendation. Four platforms catalogued (Crowdin, Lokalise, Weblate, POEditor) plus six precedent games (RimWorld, Stardew Valley, Wildermyth, Nebulous: Fleet Command, Paradox grand-strategy via mod, plus a small-team comparison cluster). Cross-axis comparison at end.

Web access denied this session. All figures are REPORTED or ESTIMATED at floor confidence. Pricing tiers and integration shapes drawn from sub-agent's prior knowledge of these platforms — figures cited should be treated as 2024-2025 directional, with the explicit caveat that SaaS pricing changes frequently and any number below should be verified before commitment. Sources list at end is illustrative of what would be checked under a normal research pass.

## Why community translation is the relevant question

Solo or 2-3 person teams cannot afford professional localization at scale. Professional translation of a strategy/sim game's full string corpus (chronicle text, event flavor, faction names, tooltip and UI strings, system messages) typically runs $0.08-$0.20 per source word for European languages and $0.10-$0.25 for Asian languages at agency rates. ESTIMATED.

A Crusader-Kings-3-scale string corpus is in the hundreds of thousands of source words. Even a much smaller Ouroboros-scale corpus — call it 30,000-80,000 source words at full content density, ESTIMATED — produces a per-language professional cost of $2,400-$20,000 at the low end and dramatically more for content-heavy titles. Eight languages multiplies that. Per-update string drift adds recurring cost. For a solo dev or 2-3 person team this is structurally not the right shape unless one specific language has a high commercial-return-on-spend case (typically Simplified Chinese for the strategy/sim niche).

Community translation collapses this cost curve to (a) the tooling/platform spend, (b) the developer's ops time managing contributors, version drift, and credit, and (c) the QA cost of either trusting community output or implementing a review tier. The brief surveys what each platform charges for (a) and the precedents that calibrate the realistic shape of (b) and (c).

## Platform: Crowdin

Crowdin is the de facto standard for community-driven game translation in the indie/mid-tier space. RimWorld, Stardew Valley, Slay the Spire, Disco Elysium, and many others use Crowdin or Crowdin-equivalent workflows. Confidence: REPORTED.

### Pricing shape

Crowdin pricing has several tiers relevant to indie devs. ESTIMATED current-state floor (subject to drift):

- **Open Source / Free tier** — free for verified open-source projects. Game source code is rarely fully open-source, but the localization project itself can sometimes qualify if strings are checked in to a public repo. Most game studios do not use this path.
- **Crowdin Enterprise / paid** — historically tiered by seats, source words, and storage. Indie tier historically started around $40-$120/month for small projects with limited seats. ESTIMATED — exact pricing has changed multiple times since 2020.
- **Crowdin for game studios** — promoted indie/SMB tier with bundled features. ESTIMATED $100-$500/month range for active projects with multiple languages.
- **Pay-as-you-go for machine translation pre-fill** — Crowdin integrates with DeepL, Google Translate, and Microsoft Translator; MT pre-fill is metered per word consumed.

Crowdin's revenue model historically allows generous free-tier community access for the contributors themselves — only the project owner pays. Contributors do not need a paid account to contribute. This is critical for community translation since it means the contributor friction is just "make a Crowdin account and submit." Confidence: REPORTED.

### Integration shape

Crowdin offers (a) a web editor that contributors use directly, (b) a CLI for syncing strings to and from a developer's repo, (c) GitHub/GitLab/Bitbucket integration for automatic source-string sync on commit, (d) translation-memory and glossary persistence across versions, and (e) fuzzy-match for string-edit churn so contributors don't re-translate strings that only changed punctuation. Confidence: REPORTED.

Typical workflow: developer commits English strings; Crowdin auto-detects new/changed strings; community translates via web editor; developer pulls translated files back via CLI before each build. The fuzzy-match feature is the main lever that keeps maintenance cost reasonable when strings change during active development.

### Crowdin's strengths and weaknesses

Strengths: hosted (no ops burden on the dev), most mature community workflows in the space, contributor-friendly web editor, broad MT integration for pre-fill, version-aware fuzzy matching. Weaknesses: ongoing SaaS spend that scales with project activity, vendor lock (strings and translation memory are hosted; export requires explicit pull), and historical pricing changes that have surprised existing customers. REPORTED.

### Hosted-vs-self-hosted

Crowdin is hosted-only. There is no self-hosted Crowdin. Studios that want self-hosting go to Weblate (see below). REPORTED.

## Platform: Lokalise

Lokalise is positioned more toward commercial/SaaS app localization than community game translation, but is sometimes used by mid-size studios with paid translator teams. Confidence: REPORTED.

### Pricing shape

Lokalise historically prices in higher tiers than Crowdin for equivalent project sizes. ESTIMATED current-state floor:

- **Start / Essential** — historically around $90-$140/month for small teams, limited seats, limited project count.
- **Pro / Business** — $230-$500/month range with more seats and more features.
- **Enterprise** — custom, typically four-figure-plus per month.

Lokalise's contributor model is more seat-oriented than Crowdin's — each translator typically consumes a paid seat slot, which makes large open-community contributor pools expensive. This is the principal reason Lokalise is rarely the choice for game-community translation despite strong tooling. REPORTED.

### Integration shape

Lokalise has strong API/CLI support, GitHub/GitLab integration, MT pre-fill via DeepL/Google/Microsoft/Amazon, translation memory, glossary, screenshot-context attachment, and in-context editor overlays for web apps. Game-specific features lag behind Crowdin. Confidence: REPORTED.

### Lokalise's strengths and weaknesses

Strengths: more polished commercial tooling, better permissions and review workflows, stronger MT integration, screenshot context. Weaknesses: seat-pricing penalizes community contributor pools, more expensive than Crowdin at equivalent feature use, less indie-game social proof. REPORTED.

## Platform: Weblate

Weblate is the principal open-source self-hosted alternative. AGPL-licensed. Used by many open-source projects (e.g. F-Droid, Fedora, LibreOffice components) and a smaller set of game projects. Confidence: REPORTED.

### Pricing shape

Two paths: (a) self-host Weblate on developer-owned infrastructure — free software, but the developer pays for the VPS/server and assumes the ops burden, ESTIMATED $5-$50/month for a small instance; or (b) Hosted Weblate via the Weblate.org SaaS, which historically prices around $19-$199/month for indie tiers and higher for enterprise. ESTIMATED.

Weblate's hosted free tier exists for libre projects on weblate.org but typically requires the source strings to be in a public repo and the project to be free-software-licensed — which most commercial games are not. REPORTED.

### Integration shape

Weblate supports Git integration (pull-request-based string sync), translation memory, glossary, fuzzy matching, MT pre-fill, web-editor contributor flow, and review workflows. The contributor flow is functional but historically less polished than Crowdin's. Self-hosted Weblate gives the developer full control of contributor data, translation memory ownership, and uptime guarantees. Confidence: REPORTED.

### Weblate's strengths and weaknesses

Strengths: open-source, self-hostable, no per-seat pricing, full data ownership, AGPL license aligns with open-source-friendly devs, hosted-tier available for those who don't want ops. Weaknesses: self-hosting is real ops work (backups, upgrades, SSL, abuse moderation), web-editor polish lags Crowdin, fewer game-industry precedents to lean on, AGPL license can complicate downstream redistribution for proprietary studios who fork or modify the platform itself. REPORTED.

## Platform: POEditor

POEditor is a smaller commercial platform pitched explicitly at small teams and indie devs. Used by a long tail of small projects across game and non-game domains. Confidence: REPORTED.

### Pricing shape

POEditor's pricing is positioned below Crowdin and Lokalise for small projects. ESTIMATED current-state floor:

- **Free** — limited strings (historically 1,000 strings), unlimited languages and contributors.
- **Start** — $14.99/month for 3,000 strings, ESTIMATED.
- **Solo / Pro / Business** tiers escalating in string count from approximately 10,000 to 100,000+ strings, ESTIMATED $30-$200+/month range.

String count is the principal pricing axis rather than seats — which makes POEditor more contributor-friendly than Lokalise for community pools. REPORTED.

### Integration shape

POEditor offers GitHub/GitLab/Bitbucket integration, an API and CLI, MT pre-fill, translation memory, glossary, and a web editor. Feature depth is below Crowdin and Lokalise but adequate for small projects. Confidence: REPORTED.

### POEditor's strengths and weaknesses

Strengths: cheapest commercial tier at small-project scale, no seat pricing, simple model for indie devs. Weaknesses: less feature depth, fewer game-specific precedents, smaller community of game-studio users than Crowdin. REPORTED.

## Precedent: RimWorld (Ludeon Studios)

RimWorld is the canonical large-scale community-translation precedent in the strategy/sim space. Confidence: REPORTED.

RimWorld uses Crowdin for community translation. The project supports a large and growing set of languages — REPORTED as covering most major European languages plus Simplified Chinese, Japanese, Korean, Russian, Polish, and several long-tail languages, primarily contributed by community volunteers credited in-game and on the official wiki. ESTIMATED 15-25+ languages with varying completion percentages.

Workflow: Ludeon commits English source strings to Crowdin; community contributors translate via the Crowdin web editor; Ludeon periodically pulls translated string files back into the build before each release. Tynan Sylvester (sole founder, with team expansion since) has historically credited translators in the Steam page and in-game credits. REPORTED.

The RimWorld pattern is the most-cited reference for indie strategy/sim community translation. Key features that made it work: (a) Crowdin's hosted-and-free-for-contributors model removed contributor friction, (b) the game's deep mod and community culture pre-existed and supplied a contributor pool, (c) string-key freezing was managed via version branches in Crowdin so that ongoing English-side dev didn't break stable translations, and (d) credit was given visibly (in-game credits + Steam page mentions) which sustained contributor motivation. REPORTED.

Caveat: RimWorld's contributor base is unusually large because the game's primary tribe (colony-sim narrative emergence) overlaps heavily with bilingual technical-curious users. Niche-strategy paid-base may or may not draw the same contributor density. ESTIMATED — no hard data on contributor-pool size by genre.

## Precedent: Stardew Valley (ConcernedApe / Eric Barone)

Stardew Valley historically launched English-only and added language support over time via a mix of paid professional translators and community volunteers. Confidence: REPORTED.

Stardew's translation infrastructure is less publicly documented than RimWorld's. Some translations were paid commissions; others were community contributions credited in-game. Barone has spoken publicly about hiring translators for specific languages (Japanese, Korean, Russian, others) while accepting community submissions for additional coverage. ESTIMATED — exact split of paid versus community is not public.

The Stardew pattern shows the **hybrid model**: pay for high-commercial-priority languages (Japanese, Simplified Chinese, Korean, the languages that drive significant sales lift in those markets) while accepting community translation for everything else. This is the pattern any solo dev with one breakout commercial language should consider. REPORTED.

## Precedent: Wildermyth (Worldwalker Games)

Wildermyth localization is community-contributor-heavy with limited paid coverage. REPORTED.

Wildermyth's per-character generative narrative makes its string corpus structurally larger than a fixed-script narrative game — every event has parameterized substitutions, every character has pronoun and name slots, every chapter has branches. This makes the per-language translation cost substantially higher than a fixed-script game of equivalent runtime length. ESTIMATED.

Worldwalker has historically accepted community-translation contributions, credited contributors, and has not localized the game to a full professional standard across all major languages. The 95%-positive review rate plus 11,600 reviews suggests the audience accepts partial-localization-by-community for this niche. REPORTED — but this audience self-selects for English-tolerance heavily; not a clean transfer to a market where localization is more decisive (e.g. Simplified Chinese strategy/sim).

The Wildermyth pattern is the most directly relevant to Ouroboros in terms of string-corpus shape (generative, parameterized, chronicle-style narrative) and team size (6 developers, ESTIMATED). REPORTED.

## Precedent: Nebulous: Fleet Command (Eridanus Industries)

Nebulous: Fleet Command is a tiny-team (1-3 devs, ESTIMATED) hardcore-niche game with a devoted but small audience (3,120 reviews at 81% positive, REPORTED per the lieutenant pivot brief). The game's localization footprint is small — historically English-primary with limited community-driven translation. REPORTED — exact language coverage not verified this session.

The Nebulous pattern is the **no-community-translation case**: tiny team, niche audience, narrow language coverage, no significant localization infrastructure. The game succeeds in its niche without addressing the language question seriously. Any team considering this path should note that it caps the addressable market to English-readers and a tail of bilingual non-native speakers in target markets. REPORTED.

## Precedent: Paradox grand-strategy mod-as-translation pattern

Crusader Kings 3, Stellaris, Europa Universalis 4, Hearts of Iron 4, and Victoria 3 are officially localized to a fixed set of languages (typically English, French, German, Spanish, Russian, Simplified Chinese, with Polish, Portuguese-BR, Japanese, and Korean varying by title). REPORTED.

For unsupported languages, Paradox's community has historically produced **translation mods** distributed via the Steam Workshop. The community-translation-mod pattern is well established for Polish, Czech, Hungarian, Turkish, Arabic, Hebrew, Vietnamese, Thai, Italian (when not officially supported), Korean (when not officially supported), and similar markets. REPORTED.

The mod-as-translation pattern has structural properties worth noting:

- **Zero infrastructure cost to the developer** — the work happens entirely in the Workshop ecosystem; the dev does no Crowdin/Weblate setup, no contributor management, no string-key versioning.
- **Discoverability via Workshop tags and curation** — translation mods rank in Workshop search and are surfaced to users in target markets.
- **QA risk is fully externalized** — the developer makes no claim about translation quality; the mod author owns reputation. Bad translation = bad mod, not bad game review.
- **Per-update churn is the modder's problem** — when the developer pushes a content patch, the translation mod breaks until the modder updates it. The developer pays no maintenance cost; the player community pressures the modder.
- **No in-game credit channel** — credit lives in Workshop description and player word-of-mouth; the developer typically does not list translation modders in official credits.
- **The pattern requires moddable string files** — strings must live in editable files (YAML, CSV, JSON) that mods can override, with no string hard-coding in scripts or compiled assets.

This is the lowest-cost translation infrastructure pattern available, conditional on (a) the game having Workshop or equivalent mod distribution, and (b) the game's text layer being externalized to mod-friendly files. REPORTED.

For Ouroboros, the mod-as-translation pattern is contingent on CL4 Workshop payoff being designed in. If Workshop support is feasible (cross-reference `docs/legacy/topics/` for any future CL4 mod brief) then translation-as-mod becomes a real option for the long-tail languages that don't justify even Crowdin investment.

## Cross-axis comparison

The four platforms and the mod-as-translation pattern compared on the four cross-axes the topic brief calls for. All figures ESTIMATED unless otherwise noted.

### Cost to set up (tooling + ops time)

- **Crowdin** — $0-$500/month tooling, ESTIMATED 10-30 hours initial setup (project structure, integration with repo, glossary, MT config), then approximately 2-8 hours/month ongoing ops (string sync, contributor management, version branching).
- **Lokalise** — $90-$500+/month tooling at small scale, similar setup-hour profile, but per-seat pricing makes community contributor pools expensive — practically capped at small paid-translator teams unless higher tier purchased.
- **Weblate (self-hosted)** — $5-$50/month VPS, ESTIMATED 20-60 hours initial setup (server provisioning, instance config, SSL, integration with repo, backup config), then approximately 4-12 hours/month ongoing ops including server maintenance and instance upgrades.
- **Weblate (hosted)** — $19-$199/month tooling, similar setup profile to Crowdin minus the ops burden.
- **POEditor** — $0-$200/month tooling, ESTIMATED 5-20 hours initial setup, similar ongoing ops profile to Crowdin.
- **Mod-as-translation (Workshop)** — $0 tooling cost (assumes Workshop integration already exists for CL4 reasons); ESTIMATED 0-5 hours per release to verify string files remain mod-friendly; no contributor management.

### Maintainability (string-key freezing during dev, version-tracking, fuzzy-match)

- **Crowdin** — strong fuzzy-match, version branching, translation memory persistence across versions, glossary enforcement. Best-in-class for active-development churn. REPORTED.
- **Lokalise** — equivalent or better fuzzy-match and version control, with screenshot-context that Crowdin lacks. REPORTED.
- **Weblate** — fuzzy-match and translation memory present, version control via Git-native branching. Polish slightly behind Crowdin/Lokalise but mechanically equivalent. REPORTED.
- **POEditor** — fuzzy-match and translation memory present, version control adequate, depth below Crowdin/Lokalise. REPORTED.
- **Mod-as-translation** — maintainability is fully outsourced to mod authors. The developer's only obligation is to keep the string-file format stable. Per-update churn risk is borne by the mod author and the player. ESTIMATED.

### QA risk (community translation quality variance)

- **All hosted platforms** — community translation quality variance is a function of contributor base, not platform. Variance is high in any community-translation regime. Mitigations across all platforms include: (a) two-tier contribution model (translator + reviewer roles), (b) glossary enforcement to lock terminology, (c) Paradox-style "fan translation may contain errors" disclaimer in language picker, (d) explicit "this language is community-translated, report errors here" UI affordance.
- **Mod-as-translation** — QA risk is fully externalized; the developer makes no claim about quality. The risk surface shifts from "bad review of the game" to "bad review of the mod." This is structurally lower commercial risk to the developer.
- **Paid professional** — lowest QA variance, highest cost; out of scope for community-translation infrastructure.

The QA risk is least sensitive to platform choice and most sensitive to (a) contributor density in the target language, (b) the presence of a paid or volunteer language-lead per language who can review submissions, and (c) the visibility of the "this is community-translated" framing in the game's UI. REPORTED.

### Credit and recognition models

- **Crowdin** — supports a contributor list export that developers paste into in-game credits or a website credits page. RimWorld's pattern. REPORTED.
- **Lokalise** — equivalent contributor tracking; less common in community-translation case because of seat pricing.
- **Weblate** — Git-commit-style attribution is native (each translation lands as a commit with the contributor's name), which makes credit-by-commit-log automatic.
- **POEditor** — contributor lists available via API.
- **Mod-as-translation** — credit lives entirely in Workshop. Developer can optionally surface translation mods in a "community translations" section of the Steam page or in-game; some games do this, most do not. REPORTED.

The credit/recognition model is more about developer choice than platform constraint. Every platform supports contributor-name export; whether the developer surfaces it in-game is independent of the platform. The strongest precedent (RimWorld) gives translators visible in-game credit, which is widely considered the floor for sustaining contributor motivation in long-running projects. REPORTED.

## Solo-dev / very-small-team practical shape

For a solo dev or 2-3 person team building toward an 80-200k primary-tribe niche-strategy paid-base with a Foundation/hard-SF secondary tribe, the platform decision intersects with the language-priority slate (T-L1) in the following structural way. ESTIMATED.

- **No translation at launch** — English-only ship, mod-as-translation pattern for any future language support. Lowest cost, lowest market reach, viable for the Nebulous-pattern niche. Caps Simplified Chinese / Russian / German / French markets significantly. REPORTED across small-team launches in the strategy/sim niche.
- **One paid language plus community** — pay for the one language with the strongest commercial case (typically Simplified Chinese for the strategy/sim niche, REPORTED), accept community contributions for everything else via Crowdin or POEditor. Stardew-pattern hybrid. ESTIMATED $5,000-$25,000 one-time per paid language plus $500-$3,000/year ongoing tooling, plus the dev's ops time.
- **Full community pipeline** — Crowdin or Weblate as the platform, accept community contributions for all priority languages, accept variance in completion percentage and quality. RimWorld pattern. ESTIMATED $1,200-$6,000/year ongoing tooling for hosted Crowdin/POEditor, or $0-$600/year for self-hosted Weblate plus the dev's ops time.
- **Workshop-only translation** — no Crowdin or equivalent; all translation lives in mods. Paradox pattern at the long tail. Requires CL4 Workshop integration as prerequisite. ESTIMATED $0 incremental cost. Caps the addressable market by language to whatever the mod community produces.

The choice between these is downstream of T-L1's priority slate. If the priority slate is "Simplified Chinese paid + everything else community," the Crowdin or POEditor path is the natural fit. If the slate is "all 8 community," self-hosted Weblate or Crowdin's mid-tier is the natural fit. If the slate is "English-only launch," the mod-as-translation pattern is the natural fit and the platform decision deferrs to post-launch.

## Feeds Design Lane and other lanes

This brief feeds:

- **T-L1 localization priority slate** — infrastructure choice constrains language scope. The cost curves above let T-L1 size the trade between language coverage and ops/tooling budget. Without T-L2, T-L1's priority slate is unconstrained by feasibility.
- **CL4 mod/Workshop payoff** — mod-as-translation is one of the load-bearing payoffs of Workshop integration. If CL4 evaluates Workshop integration without considering its localization payoff, the value of Workshop is undercounted. Cross-reference any future CL4 brief.
- **Engineering scope for localization pipeline** — the implementer-lane scope of "build localization infrastructure" depends on platform choice. Crowdin via CLI integration is approximately 1-3 days of engineering work to wire up. Self-hosted Weblate is approximately 1-2 weeks including server setup and integration. Mod-as-translation is approximately 0-3 days conditional on string files already being mod-friendly. ESTIMATED.
- **Marketing-surface decisions** — Steam page language declarations, the "Audio / Interface / Subtitles" matrix that Steam shows, and the in-game language picker UI all depend on which languages are present at launch and which are flagged community-translated. Steam's language matrix has no native "community-translated" flag, so the framing happens via the game's marketing copy and in-game UI affordances.

## Open questions for further research

The following items need follow-up either via web research (when WebFetch/WebSearch is restored), via developer-interview sourcing, or via vendor outreach:

- **Current Crowdin pricing for game studios** — exact 2026 tier pricing, including any indie-specific bundle, the source-words-per-month and seats-per-tier caps. The figures above are best-effort floor confidence.
- **Lokalise current pricing and seat model** — same gap.
- **Weblate-hosted current pricing** — same gap.
- **POEditor current pricing** — same gap.
- **RimWorld translator headcount, language coverage percentages, and contributor-credit footprint** — exact 2026 state of the project on Crowdin.
- **Stardew Valley paid-versus-community split** — which languages were paid, which were community, what the per-language sales-lift evidence looks like.
- **Wildermyth localization state** — current language coverage, contributor mix, and any developer interviews on the pattern.
- **Nebulous: Fleet Command localization state** — any community translation present, or English-only as ESTIMATED.
- **Paradox translation-mod ecosystem sizing** — top translation mods by subscriber count for Crusader Kings 3, Stellaris, Europa Universalis 4, by target language. This calibrates the realistic reach of mod-as-translation in the strategy/sim Workshop ecosystem.
- **Per-language sales-lift evidence in strategy/sim** — Simplified Chinese is the canonical "this language moves the needle" example for the genre, but the actual lift multipliers (1.2x? 1.5x? 2x?) are folk wisdom and need calibration against publisher post-mortems or Gamalytic-style aggregate data. Cross-reference any future T-L1 brief.
- **Aggregator independence caveat** — per `feedback_aggregator_independence.md` in user memory, any sales-lift figure from Gamalytic / SteamSpy / games-stats.com / Steam Revenue Calculator should be treated as a single channel; press releases or publisher filings are the TRUSTED-tier source.
- **Engineering-pipeline reference implementations** — open-source Godot localization pipelines that integrate with Crowdin / Weblate / POEditor specifically. Godot has built-in CSV/PO translation support but the integration polish with each platform varies.

## Sources

Sub-agent had no web access this session. The following are the source classes that would be consulted under a normal research pass, listed for traceability when a future pass restores web access:

- Crowdin pricing page and game-studio case studies (RimWorld, Stardew Valley, Disco Elysium, etc.).
- Lokalise pricing page and SMB/indie case studies.
- Weblate.org pricing and self-hosting documentation; Weblate GitHub for AGPL-license confirmation.
- POEditor pricing page and small-team case studies.
- Ludeon Studios (RimWorld) — Tynan Sylvester developer blog posts and Steam community discussions on translation.
- ConcernedApe (Stardew Valley) — developer blog posts and interviews on localization decisions.
- Worldwalker Games (Wildermyth) — Steam community and Reddit discussions on translation.
- Eridanus Industries (Nebulous: Fleet Command) — Steam community on localization state.
- Paradox Forums and Steam Workshop search for translation mods on Crusader Kings 3, Stellaris, Europa Universalis 4, Hearts of Iron 4, Victoria 3.
- Godot Engine documentation on localization import (CSV, PO) and any community-contributed Crowdin / Weblate / POEditor integration tooling.
- Game-industry localization-cost surveys (LocalizeDirect, LAI Global, GALA) for per-word pricing benchmarks.
- Per-language sales-lift case studies — typically published by Hooded Horse, Paradox, or large indie publishers when post-mortems are made public.

Confidence on this brief overall: REPORTED to ESTIMATED. No figures should be acted on without verification when web access is restored. The structural framing (four platform options, six precedent patterns, four cross-axes, four launch-shape scenarios) is robust independent of figure drift.
