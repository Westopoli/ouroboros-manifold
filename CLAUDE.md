# Ouroboros Manifold

## North Star (read first)

The game is rebuilt under an autonomous development method. **Agora** (`~/Projects/agora`, local Ollama models plus a dollar-capped DeepSeek driver) implements and QA-tests the game unattended. **Claude designs and tests**: the bible, the end-to-end behavior definitions, the roadmap, the fenced test suite, and the escalation rules. The simulation is rewritten in C with the stochastic equations preserved verbatim (`docs/bible/algorithms.md`). Requirements are agile epics, stories, and rules; a story is built only after it passes the Definition of Ready.

Full method: `docs/northstar/README.md` (short form), `docs/northstar/PLAN.md` (canonical), `docs/northstar/principles.md`, `docs/northstar/agile.md`. Where any other doc disagrees with `docs/northstar/`, the north star wins.

**Tech stack:** C simulation library (pipe contract first, GDExtension later) · Godot 4 (Forward+) client · Python 3.14 test harness and library builder · Cloudflare R2 CDN · `claude-sonnet-4-20250514` (library builder only, offline, never called during play)

Long-term project. No ship deadline. One story at a time, done well.

## Model Usage

Default to `claude-opus-4-6` for design and test-authoring work in this repo.

## The Bible

`docs/bible/` is the single source of truth for what the game is:

- `game_bible.md` — hub: vision, sacred principles, game shape, tone, monetization. Human-facing, short.
- `stories.md` — the story catalog. One row per user-facing behavior (`S-###`), its epic, status, and depth pointer. No design in this file.
- `epics/E-##-<slug>.md` — one file per feature area: completeness gate result, purpose, end-state (what done looks like technically and visually, authored before the epic is queued), stories with Given/When/Then rules (`R-###-##`), inputs, outputs, invariants, scale requirements, references, ways this could be wrong, open flags, dependencies.
- `references/E-##/` — screenshots, clips, and `notes.md` naming which games a story should look and feel like. Visual ground truth for T2 QA.
- `algorithms.md` — the retained equations with constants. The C rewrite reproduces them bit for bit.
- `docs/northstar/ambiguity_register.md` — every open `[NEEDS WESTLEY]` question (`Q-###-##`) with candidate answers. An epic with an open flag is not built.

Reading discipline: hub first, then only the epic you are touching. Previous versions: `docs/bible_history/` (monolithic snapshots `game_bible_X_YY.md`; the retired spokes as `bible_2_00_*.md`). If anything conflicts with the bible, the bible wins.

### Bible discipline: rewrite, never append

Append-only is forbidden. When direction changes, old text is deleted, not annotated. No "PIVOT" markers, no "In Flux" sections, no "as of" callouts. History is `docs/bible_history/` and `git log`. Months of append-only edits produced stacked contradictions that leaked into new chats; this rule and the stale-doc tripwire are the two defenses.

### Ambiguity is flagged, never guessed

When a behavior is under-defined, add a `Q-` row to the ambiguity register with the concrete question and two or three candidate answers. Never pick silently. Local models never see an open flag; `scripts/derive_agora_rules.py` skips epics that have one.

## Workflow

How the game gets built lives in `docs/northstar/`, not here. In brief: Stages 0 to 2 are done or in progress once; Stages 3 (end-to-end definition), 4 (roadmap and sprints), and 5 (tests) repeat per epic; Agora builds Tested stories in dependency order; escalation is a ladder with a top (`docs/northstar/escalation.md` once R3 lands). The old one-queue workflow is retired; `docs/priority_queue.md` is a pointer and `docs/northstar/backlog_seed.md` holds what it used to carry until the Stage 4 backlog exists. The Design Lane and Research Lane playbooks (`docs/design_lane.md`, `docs/research_lane.md`) describe how parallel chats feed the register and `docs/research/`.

Git: work directly on `main` and push after each meaningful unit; Westley is a solo developer and Agora is autonomous, so branches and PRs exist only for extenuating cases (a multi-day code change, an experiment he may discard) and the reason is stated. When parallel chats conflict, merge and resolve on `main` yourself; never hand Westley a conflict. Guardrails in `.claude/settings.json` and `.claude/hooks/git-guard.sh` deny destructive ops, `--no-verify`, `--amend`, force pushes, and rebases. Westley's working-tree changes may be uncommitted: never stage files you did not change, and confirm before any op that could touch them. If a legit op is blocked, ask.

Commit and push every ledger, register, or epic update as one meaningful unit; Westley reads them on GitHub.

## The Rules

### No runtime API calls during play

The game never calls a model API. Missing library entries fall back to a placeholder; play never blocks. The library builder runs offline, stores JSON, the game reads it. Builder discipline:

```python
if library_exists(content_type, entry_id):
    return library_get(content_type, entry_id)
result = ai_dispatcher.dispatch(...)
library_set(content_type, entry_id, result)
```

### No IP exposure

No character names, place names, or plot elements from any existing fiction. Mechanical concepts inspired by source material (psychohistory-like prediction, hidden-society roles, eternal observers) are fine. Commercial release.

### Tick delta shape is documented first

Any change to the snapshot, delta, or command JSON shape is posted to `docs/architecture.md` before implementation. Phase 1 of the C rewrite reproduces today's shapes exactly so Godot is untouched.

### Determinism is a contract

Same seed, same command stream, byte-identical trace on Windows, macOS, and Linux, with a checksum every 10 ticks. No fast-math, no platform transcendental calls without a deterministic implementation, no hash-order or wall-clock input to the sim. Required from the first sprint; it cannot be added later.

### Sub-agents implement, never design

Sub-agents (Explore, general-purpose, Plan, cavecrew variants, and `agy`/Antigravity CLI — see `docs/northstar/research/gemini_compute.md`) execute against an existing spec. They may not make architectural or API decisions, expand scope, edit `docs/bible/**`, `docs/northstar/**`, `CLAUDE.md`, or any test threshold, or decide what is tested. On ambiguity they return findings plus a proposed change; the main agent decides.

### Sub-agents use caveman mode for prose

Append to every sub-agent prompt: *"Report-back caveman mode (drop articles/filler/hedging, fragments OK). Markdown docs/briefs you write: caveman. Commit messages: caveman. Code, tests, config: normal prose."* Code and tests stay normal so names, assertions, and runtime strings do not degrade. The bible and its epics are normal prose.

### Stale-doc tripwire is mandatory

A change that lands a behavior change also deletes or rewrites every doc claim it makes wrong, in the same PR. This is part of the Definition of Done.

### Tests are the spec

Every story exists as failing tests before Agora touches code. Tests live in fenced paths Agora cannot edit. Every test names the `S-###`/`R-###-##` it proves. A test that cannot fail is a defect: every detector ships with a positive control.

## Code Quality

### No stink

No docstrings, inline comments, or header blocks unless logic is genuinely non-obvious. No abstraction layers, wrappers, or config patterns that were not asked for. No cosmetic refactoring in a change that fixes or builds something else. Minimal diffs.

### Traceability

If system A is not working and system B is built to solve it, the connection is obvious at both sites: `# See also: path/to/other — handles X because Y`. If code is disabled, bypassed, or replaced instead of fixed, say so; leave no dead code that looks live. `simulation/border_friction.py` is the standing example of what not to leave behind (dead module the Stage 1 audit mistook for live).

### Scope discipline

Do what was asked. Mention what else needs fixing; do not fix it, unless the asked-for change cannot work without it, in which case explain the dependency first.

## Debugging

No shotgun fixes. Hypothesis, then logging that would confirm or refute it, then the run, then the targeted fix. One fix at a time.

## Test Checkpoints

### Testing rigor

Every system has both an isolation test (system alone, everything else hard-fixtured) and an integration test (realistic scene with pathing, AI, fog, vision, scale). Before asserting: list every actor and variable in the scene; verify the fixture works before asserting on the system; a failing assertion is a system bug only when the fixture is proven clean. Both levels; more tests cannot hurt.

### Protected engine files

Changes to the live Python equations need Westley's approval until the C rewrite replaces them: `tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `intent_resolver.py`, `technology.py`, `diplomacy.py`, `world.py`, `admin_revolt.py`. (`border_friction.py` is dead code; the live friction is in `tick.py`.)

### Invariant modification rules

When an invariant fails: adjust config, escalate a real bug, or recalibrate the invariant. You may narrow an invariant's scope without approval (skip cases it was never meant to check). You may not widen thresholds, extend windows, or loosen tolerances without presenting the change to Westley. You may never reclassify a real finding as a skip, and never weaken a test to make the current implementation pass.

## Tone

The game has a sense of humor: playful, occasionally absurd, never cringe. Easter eggs welcome. Dry wit welcome. Chronicle and event writing still read as fragments of a real history, and real history is frequently funny. Playful is not unserious: civilizations still rise and fall over centuries.

## Documentation

Docs describe what the game does right now. A behavior change updates the epic, the catalog, and any spec, in the same PR. No doc updates for internal refactors, visual tweaks, or fixes that do not touch documented behavior.

## Simulation File Map

`simulation/` is the Python reference implementation the C rewrite replaces, and the pytest-via-ctypes harness lives beside it.

- Core loop: `tick.py` (tick sequence, live border friction, revolt creation, zombie cleanup), `config.py` (all constants), `drift.py`, `events.py` (26 templates, triggers, pending queue)
- World and entities: `region.py`, `world.py`, `faction.py`, `technology.py`, `diplomacy.py`, `admin_revolt.py`, `lifecycle.py`
- Generational: `time_jump.py`, `generational.py`, `character_selector.py`, `coherence_ledger.py`, `naming_system.py`
- Chronicle: `chronicle_distiller.py`, `chronicle_assembler.py`, `library/`
- Missions: `mission_generator.py`, `objectives.py`, `outcome_resolver.py`, `force_allocator.py`, `mission_briefing.py`, `onboarding_store.py`
- Tactical: `tactical_engine.py`, `unit.py`, `movement.py`, `damage.py`, `fog_of_war.py`, `facing.py`, `ability.py`, `command.py`, `command_ingest.py`, `reinforcement.py`, `behavior_runner.py`, `script_schema.py`, `trigger_bus.py`, `spine_drift.py`
- Map generation: `map_generator.py`, `layout_library.py`, `layout_instantiator.py`, `gradient_placer.py`, `layer_masks.py`, `fairness_evaluator.py`, `archetype_filters.py`, `tactical_map.py`, `sim_flavoring.py`
- Transport and saves: `pipe_transport.py`, `snapshot_serializer.py`, `save_writer.py`, `save_loader.py`
- Tuning and analysis: `sim_tuner.py`, `sim_graph.py`, `invariants.py`, `sim_validator.py`
- Generated (gitignored): `tuning_output/`, `__pycache__/`

Docs layout: `docs/bible/` (hub, catalog, epics, references, algorithms), `docs/bible_history/`, `docs/northstar/` (method, register, research, proving ground), `docs/architecture.md`, `docs/stage_specs/` (historical stage record), `docs/research/`, `docs/design_questions/` (historical).
