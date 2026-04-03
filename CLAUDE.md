# Ouroboros Manifold

**Tech stack:** Godot 4 (Forward+) · Python 3.14 · Cloudflare R2 CDN · `claude-sonnet-4-20250514` (library builder only, offline — never called during play)

## The Bible

The game bible is the single source of truth for what this game is. Bible files are versioned as `docs/game_bible_X_YY.md` — always use the highest-numbered version (e.g. `1_07` is newer than `1_06`). It has a table of contents — navigate to the section you need, don't read the whole thing every time. If something in any other doc conflicts with the bible, the bible wins.

Read the relevant bible section before starting work that touches game design, simulation behavior, mission structure, fleet/combat mechanics, chronicle systems, or tone.

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

## Test Checkpoints

**Never run tests yourself. Never self-verify test output.**

After any code change that requires a test run:
1. Stop.
2. Tell the user exactly what command to run.
3. Wait for the user to run it and paste or share the output.
4. Only proceed after the user has seen the output and given sign-off.

This applies to every test at every stage — unit tests, integration tests, one-off diagnostic scripts. No exceptions. The user's eyes on the output is a hard requirement, not a courtesy.

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
- `docs/bible_history/` — versioned game bibles (use highest-numbered)
- `docs/stage_specs/` — stage implementation specs
- `docs/articles/` — design essays
- `docs/website/` — marketing site
- `docs/sim_validator_plan.md` — spec for automated validation system (next major feature)
- `docs/dev_rules.md` — historical dev process doc (largely absorbed into this file)
