# Ouroboros Manifold

**Tech stack:** Godot 4 (Forward+) · Python 3.14 · Cloudflare R2 CDN · `claude-sonnet-4-20250514` (library builder only, offline — never called during play)

## The Bible

The game bible is the single source of truth for what this game is. It uses a **hub-and-spoke architecture** in `docs/bible/`:

- **Hub:** `docs/bible/game_bible.md` — vision, principles, generational structure, player toolkit, tone, and summary paragraphs pointing to spokes
- **Spokes:** `docs/bible/bible_*.md` — full reference for each major system (simulation, missions, combat, world, chronicle, antagonist, monetization, AI pipeline)

**Reading discipline:** Read the hub first. Then read only the spoke(s) relevant to your task — stage specs list which spokes to read in their "Bible References" section. Don't read every spoke every time.

**Design decisions:** When facing a design fork — "should this feel punishing or dramatic?", "does the player control this or does the civilization?" — check the **Design Experience Guide** section in the hub. It has heuristics and litmus tests for resolving ambiguity without reading 200 lines of vision docs.

**Previous versions:** Monolithic bible versions are archived in `docs/bible_history/game_bible_X_YY.md`.

If something in any other doc conflicts with the bible (hub or any spoke), the bible wins.

## Model Usage

Default to `claude-opus-4-6` for all implementation work.

## The Rules

### No runtime API calls during play

`simulation/` never calls the Claude API. No exceptions. Missing library entries fall back to a generic placeholder — never block gameplay to generate content. The library builder pipeline runs offline, generates content, stores it in JSON. Runtime reads from the library. That's the contract.

Library builder caching — always check before dispatching:
```python
if library_exists(content_type, entry_id):
    return library_get(content_type, entry_id)
result = ai_dispatcher.dispatch(...)
library_set(content_type, entry_id, result)
```

### No IP exposure

No Asimov character names, place names, or plot elements. All lore is original. Mechanical concepts inspired by the source material (psychohistory-like prediction, hidden-society roles, eternal observer roles) are fine. The game is targeting commercial release.

### Socket server is protected

`simulation/socket_server.py` requires explicit user confirmation before any changes.

### Tick delta shape is documented first

Any change to the tick delta JSON shape must be posted to `docs/architecture.md` before implementation.

## Code Quality

### No stink

- No docstrings, inline comments, or block comments unless logic is genuinely non-obvious. No file-level header blocks.
- No over-engineering. Don't add abstraction layers, wrapper functions, helper classes, or config patterns that weren't asked for. Write the simplest code that does the job. If a pattern is needed, it'll be asked for.
- No cosmetic refactoring. If you're touching a file to fix or build something, fix or build that thing. Don't reorganize imports, rename variables, split classes, or "improve" unrelated code in the same file. Clean diffs only.

### Traceability

This is critical. If system A isn't working and you build system B to solve the problem, the connection between A and B must be obvious. Specifically:

- If you add a workaround, fix, or secondary system that changes how an existing system behaves, **leave a comment at both sites** pointing to the other. `# See also: path/to/other_file.gd — handles X because Y` is enough.
- If you disable, bypass, or replace existing code instead of fixing it, say so explicitly. Don't leave dead code that looks like it should work but silently doesn't.
- If a new file exists because of a problem in an old file, the old file should make that clear.

The goal: Westley should never have to wonder "why doesn't this work" or "why does this exist" when reading any file. The code should explain its own organizational logic.

### Scope discipline

Do what was asked. If you notice something else that needs fixing, mention it — don't fix it. The only exception is if the asked-for change literally cannot work without the other fix, in which case explain the dependency before making both changes.

## Stages and Complexity

The game is built in implementation stages defined in the stage docs (`docs/stage_specs/`). Each stage has specific milestones.

### Stage rules

1. **Complete the current stage before starting the next.** No skipping ahead, no "laying groundwork" for future stages.
2. **Features marked `[OPTIONAL]` are built only after the stage's core milestone passes cleanly.** If an optional feature causes instability, remove it entirely and leave a `# OPTIONAL: [feature] — not implemented` comment. Never spend more than one session debugging an optional system.
3. **The base game must be stable before any optional system is added.** A working simple version always beats a broken complex one.
4. **Do not refactor code without user's (Westley) permission.** If something need to be fixed, flag it and ask for input on what to do.

## Debugging

**No shotgun fixes.** Don't change values, swap implementations, or try different approaches without first confirming what's actually wrong.

Workflow for any bug:
1. Form a hypothesis
2. Add print statements or logging that would confirm or refute it
3. Have the user run the game and share output
4. Only then make the fix, targeted to the confirmed cause

One confirmed diagnosis is worth ten guesses.

**One fix at a time.** When multiple issues are identified, fix one, have the user run and verify, then move to the next. Batching fixes reduces the ability to isolate which change caused a new problem or resolved an old one.

## Test Checkpoints

**Never run tests yourself. Never self-verify test output.**

After any code change that requires a test run:
1. Stop.
2. Tell the user exactly what command to run.
3. Wait for the user to run it and paste or share the output.
4. Only proceed after the user has seen the output and given sign-off.

This applies to every test at every stage — unit tests, integration tests, one-off diagnostic scripts. The user's eyes on the output is a hard requirement, not a courtesy.

### Exception: Simulation Validator

The simulation validator (`simulation/sim_validator.py` / `simulation/test_validate.py`) is the one test system you run yourself. After implementing or changing simulation code:
1. Run the validator yourself.
2. Analyze the results.
3. If invariants fail: diagnose and adjust `config.py` values within defined bounds, then re-run. Iterate until the report is clean. **`config.py` is the only engine file you may modify during validator tuning.** All other engine files (see protected list below) require Westley's approval.
4. If you find a bug or design flaw that you can't resolve through config tuning, **escalate to Westley** — don't silently work around it.
5. When all invariants pass, present the final report to Westley for sign-off.

**Protected engine files.** These files are read-only during validator tuning. If a fix requires changing one of them, escalate to Westley:
`tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py`

**Invariant modification rules.** When an invariant fails, there are three valid responses: adjust config, escalate a real bug, or recalibrate the invariant. Rules for the third:
- **You may** narrow an invariant's scope without approval — skipping cases it was never meant to check (empty regions, factions with zero territory, runs shorter than the invariant's window).
- **You may not** widen thresholds, extend time windows, or loosen tolerances without presenting the change to Westley first. This includes any change that makes the invariant more permissive for cases it IS supposed to catch.
- **You may never** reclassify a real finding as a skip. If the simulation has a bug and the invariant caught it, the answer is escalate — not adjust the invariant to stop catching it.

This replaces the manual checkpoint loop for simulation work. Westley reviews the final validator report, not intermediate terminal output.

## Tone

The game has a sense of humor. It should feel like someone who enjoys what they're building actually built it — playful, occasionally absurd, never cringe. Easter eggs are welcome. Dry wit is welcome. The chronicle and event writing should still feel like fragments of a real history, but real history is frequently funny.

Don't mistake "playful" for "unserious." The civilization is still rising and falling over centuries. The player still feels the weight of time. But the game winks at you sometimes.

## Documentation

Docs are a first-class artifact. If a session changes game behavior, update the relevant docs before closing. The principle: **the docs should always describe what the game actually does right now.** If a bug fix changes documented behavior, update the doc. If a new system is built, it goes in project_state.md and the relevant stage doc.

Don't update docs for: internal refactors with no behavior change, visual tweaks, or bug fixes that don't affect documented behavior.

## Simulation File Map

All simulation code lives in `simulation/`. Here's the live engine:

### Core loop
- `tick.py` — 7-step tick resolution sequence (events → agents → friction → drift → composites)
- `config.py` — all tunable constants, feature flags, archetype definitions
- `drift.py` — per-region field drift (military decay, economy growth, tension, population)
- `events.py` — event templates, threshold triggers, chain spawns, PendingQueue, `_next_chain_tag()`

### World & entities
- `region.py` — Region class (fields, composites, tier)
- `world.py` — World class, template generators (s1_isolated, contested_border, four_way, etc.)
- `faction.py` — Faction class, agent decision logic, archetype behavior, budget management
- `technology.py` — per-faction tech growth from economy/population

### Resolution
- `intent_resolver.py` — resolves faction intents (attack, reinforce, colonize), collision detection
- `border_friction.py` — per-region tension/economy drag from hostile borders

### Theming
- `theme_scifi.py` — region/faction display names (will expand with era system)

### Tuning & analysis
- `sim_tuner.py` — scenario runner, config override system, graph generation harness
- `sim_graph.py` — matplotlib graph functions (overlay, side-by-side, field comparison)

### Generated (gitignored)
- `tuning_output/` — PNGs from sim_tuner runs
- `__pycache__/` — Python bytecode

### Docs layout
- `docs/bible/` — game bible hub + spoke files (active reference)
- `docs/bible_history/` — archived monolithic bible versions
- `docs/stage_specs/` — stage implementation specs
- `docs/articles/` — design essays
- `docs/website/` — marketing site
- `docs/sim_validator_plan.md` — spec for automated validation system (next major feature)
- `docs/dev_rules.md` — historical dev process doc (largely absorbed into this file)
