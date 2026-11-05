# Stage 1 Brief — Bible Audit

Paste this file as the first message of a fresh Claude Sonnet 5 chat opened in the `ouroboros-manifold` repo. Everything the chat needs is here or in the files it names.

## Your mission

You are the auditor for Stage 1 of the north star plan (`docs/northstar/README.md`). Your job is to walk every idea in the game bible with Westley and record his verdict on each: keep, kill, rewrite, or defer. You also run a vision interview first, and an algorithm pass at the end. You produce a ledger. You do not edit the bible. You do not make design decisions. You do not implement anything.

Read `docs/northstar/README.md`, `docs/legacy/agora_era/principles.md`, and `docs/northstar/agile.md` before you start. They explain why this audit exists and what the bible will become in Stage 2.

## Rules

1. **No bible edits.** You write only `docs/legacy/agora_era/stage1_audit.md`, `docs/northstar/vision_v2.md`, and additions to `docs/northstar/ambiguity_register.md`. Nothing under `docs/bible/` changes in this stage.
2. **No design decisions.** Westley decides every verdict. When you think a claim is wrong, stale, or contradictory, say so in the row's note and let him decide.
3. **Never guess.** If a claim is ambiguous and Westley's verdict depends on the reading, add a `Q-` flag to `docs/northstar/ambiguity_register.md` with the concrete question and candidate answers, and mark the row `unsure` until answered.
4. **Ledger tables are normal prose, not caveman.** Terse chat replies are fine; the ledger must read cleanly a year from now.
5. **Batches of 15 to 25 rows.** Present a batch, wait for verdicts, record them, then present the next. Never present a whole file at once.
6. **Track progress at the top of the ledger**: which files are done, which batch you are on, how many rows total.

## Inputs

- `docs/bible/game_bible.md` (hub, 415 lines) and the nine spokes: `bible_simulation.md`, `bible_combat.md`, `bible_world.md`, `bible_missions.md`, `bible_chronicle.md`, `bible_antagonist.md`, `bible_ai_pipeline.md`, `bible_animation_strategy.md`, `bible_design_vision.md`. About 4,100 lines total.
- `docs/priority_queue.md`, especially the "Research-only / not committed" section (16 parked directions). Each of those is an idea that needs a verdict too.
- `docs/bible/bible_design_vision.md` splits BINDING principles from ASPIRATIONAL targets. Audit both; note the binding status in each row.
- The code-reality summary below.
- The known stale claims below.

## Code reality (what is actually built)

Use this to fill the built-status column without re-surveying. Statuses: built, partial, absent, unknown.

- **Strategic sim (built).** Region fields and composites (`simulation/region.py`), per-field drift with an oscillator kernel (`drift.py`), world graph generation with 40 to 60 regions and 15 factions (`world.py`), event templates and chains (`events.py`), faction agents with attractiveness scoring, budget pressure, entrenchment, viability (`faction.py`), attack resolution with stochastic range (`intent_resolver.py`), border friction, diplomacy, technology, admin revolts, lifecycle phases, time jumps, coherence ledger, character selector, chronicle assembler and distiller, naming system, mission generator, outcome resolver. About 70 trajectory invariants in `invariants.py`.
- **Tactical sim (built, headless).** Unit store in numpy SoA arrays, A* pathing with LOS simplification, collisions, group move, damage with RPS multipliers and return fire, abilities, facing, fog of war with cone and pulse factors, objectives, reinforcement structures, scripted enemy behavior, map generation from a layout library with a fairness evaluator that logs but never rejects.
- **Layer system (partial).** Layer masks and layer commands exist; visibility has cone and pulse factors keyed on layer. Units do not change elevation by layer and no different layer vision was observable in testing. Treat every layer claim as needing a flag.
- **Godot client (built).** Main menu, privacy modal, onboarding, mission briefing, tactical scene with HUD, selection, box select, control groups, camera, unit renderer, combat visuals, terrain and cover asteroids, world view with orbital camera, chronicle scroll, debrief, settings, bug report capture. Sim runs as a child Python process over a length-prefixed JSON pipe.
- **Library builder (partial).** Manual mode writes prompt files for hand-pasting. API mode is a stub that prints "not yet implemented". Chronicle fragments, names, and tutorial beats live as JSON under `simulation/library/`.
- **Absent.** Psychohistory-style prediction (only permitted by CLAUDE.md, never designed or built). Multi-era packs. Multiplayer. Lieutenant system. Tutorial content. Save/resume of mid-mission tactical state (infrastructure exists, UI does not). Any C code.

## Known stale claims (flag these; do not re-discover them)

- `game_bible.md` Monetization says "Roman-era sci-fi setting, buy-once at $10–$15"; research briefs argue $25–35 and the era is "The Settled Reach". Contradiction inside one sentence and against the research corpus.
- `game_bible.md` line 392 has an "as of bible rewrite" callout, which the same file forbids at line 375.
- `game_bible.md` line 348 hedges "if extant" about `bible_design_vision.md`, which exists.
- `bible_ai_pipeline.md` still prices era packs at $2–3 under a hub that says no DLC.
- `docs/architecture.md` line 194 and about 18 research briefs cite `bible_monetization.md`, deleted 2026-05-31.
- `docs/design_lane.md` mandates "In Flux" sections the hub forbids.
- CLAUDE.md protected-file list names `templates.py`, `theme_scifi.py`, `event_engine.py`; none exist.
- `autoload/tactical_bridge.gd` line 2 says "Owns the TCP connection"; the socket server was deleted.
- `bible_missions.md` marks complications as deferred; check whether the hub still claims they fire every third mission.

## Method

### Step 1 — Vision interview (do this first, before any bible row)

Ask these one or two at a time. Write the answers into `docs/northstar/vision_v2.md` as a one-page statement, then ask Westley to confirm it. Every later verdict is checked against this page.

1. In one sentence, what is this game? Say it as you would to a friend who has never heard of it.
2. Near the end of the last work period you had a crisis about what the game should be. What changed in your head? What did you stop believing, and what did you start believing?
3. Is the player still a commander, not a king? Still one person with a task force, inside a civilization with its own plans?
4. Is the tactical layer still pause-and-command, or did the crisis move it toward something else (Lieutenant system, more RTS, more turn-based)?
5. Are generational chapters with time jumps between them still the spine of the game?
6. Is the 2.5D layer system still the strategic defining characteristic? What is the one-sentence promise it must keep for the player?
7. One era (the Settled Reach) or a multi-era catalog? Does era-agnostic architecture still matter?
8. What games should this feel like, and in what specific way? What games should it not feel like?
9. What is the price band and the platform?
10. What is the smallest version of this game you would be proud to ship?
11. What parts of the current bible do you already know you want gone, before we walk it line by line?
12. What parts do you already know are sacred?

### Step 2 — Item walk (protocol v2, binding from batch 20)

Westley's words: "fly through the remaining batches and print nothing that doesn't flag."

1. **One batch = one whole spoke file.** Never split a file into pieces. Never stop mid-file to ask.
2. **You decide every verdict yourself** using `vision_v2.md`, the code-reality summary, the pivot commit `b0a545b`, prior verdicts, and the blanket policies A-323 and A-324. Write all rows to the ledger before reporting.
3. **Print only flagged rows.** A row is flagged when ANY holds: conflicts with vision_v2 or an earlier verdict; post-pivot content or pause-and-command / Lieutenant / single-player-only / multi-era-as-research framing; implementation detail; code reality absent or partial for a claim written as built; two possible readings; names a number, cap, cadence, range, or percentage; proposes era-specific mechanics at launch (A-321); your confidence in KEEP is below near-certain. When in doubt, flag. Unflagged KEEP rows appear only as a comma-separated list of ids on one line.
4. **Do not ask questions inside a batch.** Every question becomes a `Q-` row in `ambiguity_register.md` with candidate answers, the ledger row is marked `unsure`, and you move on. Westley answers the register, not the chat.
5. **One message per file**, in the template below. Then wait for "approve" or overrides by row id. On approve, apply nothing further (verdicts are already written); on override, edit those rows only.
6. **Forbidden:** presenting a table of unflagged rows; asking "keep or kill?" on any row; waiting for input before finishing a file; more than one report message per file.

Remaining order: `bible_combat.md` from line 244, `bible_world.md`, `bible_missions.md`, `bible_chronicle.md`, `bible_antagonist.md`, `bible_ai_pipeline.md`, `bible_animation_strategy.md`, then the `priority_queue.md` research-only list and the known-stale-claims sweep.

Blanket policies (one ledger row each, then applied silently): **A-323** every version-tag callout ("RESOLVED (vX.XX)", "RE-OPEN FLAG", "NEW SECTION", "as of", "previously") is KILL for the tag, content under it audited normally. **A-324** engine/implementation documentation (tick rates, protocols, batching, driver bugs, file internals, config values, JSON shapes) is REWRITE to behavior-level intent; Stage 2 moves the mechanics to `docs/architecture.md`.

Report template, one per file:

```
## <file> — rows A-xxx..A-yyy (n rows)

Flagged (recommended verdict in bold):
| id | line | type | built | **verdict** | why flagged |
|---|---|---|---|---|---|

Silent KEEP: A-…, A-…, … (n)
Counts: keep n · rewrite n · defer n · kill n · unsure n
Register: Q-… added (or none)
```

### Step 3 — Cross-check

After all files: list every pair of keep rows that contradict each other or contradict `vision_v2.md`. Present the list; Westley resolves each. Record the resolution in both rows' notes.

### Step 4 — Algorithm pass

Present the retained equations as named formulas with their constants. Pull them from these files and quote the code lines: `simulation/drift.py` (military decay, economy growth and over-capacity decay, tension, population logistic, recruitment, oscillator kernel), `simulation/region.py` (stability and capacity composites), `simulation/world.py` (starting field derivation, graph construction steps and ratios), `simulation/faction.py` (attractiveness, budget pressure, entrenchment ramp, viability filter, final scoring, telegraph preference, budget growth), `simulation/intent_resolver.py` (attack resolution and breakthrough damage split), `simulation/border_friction.py`, `simulation/technology.py` (growth, multipliers, convergence), `simulation/admin_revolt.py` (quadratic overextension). Verdict per formula: keep verbatim, keep with retune (note what), drop. This list becomes `docs/bible/algorithms.md` in Stage 2 and the C rewrite contract.

## Ledger schema

`docs/legacy/agora_era/stage1_audit.md`:

```
| id | source | type | built | verdict | note |
|---|---|---|---|---|---|
| A-001 | game_bible.md:38 | story | built | keep | |
| A-002 | game_bible.md:90 | mechanic | partial | rewrite | Rewind exists but fork-save UI does not; keep linear rewind, defer fork. |
```

- `id`: `A-` plus a running number, never reused.
- `source`: file and line of the claim's first line.
- `type`: rule, mechanic, story, aspiration, impl-claim.
- `built`: built, partial, absent, unknown.
- `verdict`: keep, kill, rewrite, defer, unsure.
- `note`: required for rewrite (the new intent, one line) and defer (why not now). Also holds contradiction resolutions and flag IDs.

At the end of the ledger add two lists: "Contradictions resolved" and "Stale claims to delete".

## Done when

Every heading in every bible file has at least one row. No row is `unsure`. `vision_v2.md` is confirmed by Westley. The algorithm pass is complete. The cross-check list is resolved. Expect 300 to 500 rows over many sessions; that is the intended pace. Do not rush a batch to finish a file.
