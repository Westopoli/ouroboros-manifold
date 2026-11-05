# C4 model — MVP version

## Purpose

This is the first C4 model of Ouroboros Manifold, required by `CLAUDE.md`'s "C4 model per version"
rule: drawn before the MVP becomes the full game, kept beside the bible, read before designing a
manager-mode cascade or authoring Agora tests. It is **descriptive, not aspirational**: every
element and relationship here is traceable to a file on `origin/main`, or is explicitly marked
`planned` (bible/doc only, no code) or `unverified` (claimed by a doc but no call site found).
It documents the system as of:

```
commit 47bfaeed63a17d6cbde4d138700c66ba9ccfc9fd
origin/main, read 2026-09-28
```

This is not a redesign and does not resolve any open design question. Where the model surfaces a
question the code cannot answer (an ambiguous boundary, a duplicated responsibility, a doc that no
longer matches the code), it goes in `gaps.md`, not into an invented answer.

## How to read this model

- `1-context.md` — Level 1 (System Context): the player, Westley, Agora's QA loop, the offline
  library builder, and any external services (storefront, CDN) the code actually references.
- `2-containers.md` — Level 2 (Containers): the Godot client, the C sim library, the pipe
  transport process, save files, the generated content library, the legacy Python reference sim,
  the test harness, and Agora, with the protocol and entry point for each relationship.
- `3-components-sim.md` — Level 3 for the C simulation library: one component per `csrc/<module>.c`
  file, grouped by owning epic, with the real tick-order call trace.
- `3-components-client.md` — Level 3 for the Godot client: autoloads, scene groups, how scenes
  reach the sim, and the QA daemon.
- `4-flows.md` — three runtime sequence flows (new game → galaxy; briefing → deploy → tactical →
  debrief; time jump → chronicle), each step naming the pipe command and the handler function.
- `gaps.md` — every place the model and the running code disagree, a boundary is unclear, a
  bible-named container does not exist yet, or a responsibility is duplicated. Cited to file:line.

Every diagram is Mermaid (`C4Context`/`C4Container`/`C4Component`, or `flowchart` where the C4
syntax cannot express something — GitHub and most Markdown viewers render Mermaid inline). Every
diagram is followed by a table repeating each element with its source file, so the model is
checkable without a renderer.

## Status legend

Used throughout this model to classify every component, entry point, and container:

| Status | Meaning |
|---|---|
| **built** | Code exists on `origin/main` and is reached by the running game (the live scene-router flow, the pipe's command dispatch, or the strategic/tactical tick) — not merely present in a source file. |
| **wired-untested** | Code exists and something in the running game calls it, but no test exercises that call path directly (rare in this codebase; most wired code has a fenced test — flag explicitly where this applies). |
| **tested-unwired** | Code exists and is covered by tests (`tests/csim/*.py`, `tests/*.gd`), but nothing in the running game (tick, pipe dispatch, scene graph) ever calls it. A real function, provably unreached. |
| **planned** | Named in the bible or `docs/northstar/` but no corresponding code exists in this checkout. |

A component can be `built` for some entry points and `tested-unwired` for others in the same file
(e.g. `csrc/tactical_mapgen.c`: `om_map_add_cover`/`om_map_add_obstacle` are built; most
`om_map_get_*` accessors are `/* STUB */`). Where that split matters, the component tables call it
out per entry point rather than giving the whole module one status.

## Sources read

`CLAUDE.md`, `docs/bible/game_bible.md`, `docs/architecture.md`, `docs/northstar/PLAN.md` ("The
Factory"), `docs/northstar/plans/push/pieces.toml`, `docs/northstar/spec_factory/symbol_modules.toml`,
`csrc/*.c`, `csrc/ouroboros_sim.h`, `csrc/om_internal.h`, `csrc/pipe/om_pipe.c`, `Makefile`,
`project.godot`, `autoload/*.gd`, `scenes/**` (top-level folders), `scripts/library/`,
`scripts/qa_harness.sh`, `autoload/qa_daemon.gd`, `simulation/` (read for what still calls it),
and `~/Projects/agora/projects/ouroboros/qa.toml` plus `~/Projects/agora/scripts/qa_explore.py`
(read-only, outside this repo).
