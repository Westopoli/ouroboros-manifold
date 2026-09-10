# North Star — Agora-Driven Development of Ouroboros Manifold

This directory is the current development method for the project. It overrides the workflow sections of `CLAUDE.md` and `docs/workflow.md` wherever they disagree. The game bible (`docs/bible/`) remains the source of truth for *what the game is*; this directory is the source of truth for *how it gets built*.

## The north star

Agora (`~/Projects/agora`, an autonomous loop of local Ollama models plus a dollar-capped DeepSeek driver) develops and QA-tests the whole game end to end, unattended. Claude does judgment day-side: designs the bible, defines every behavior end to end, writes the tests, plans the sprints, and writes the escalation rules. The game is rewritten in C for speed, keeping the stochastic equations that make the world work.

Principles that persist beyond any chat are in `principles.md`. The agile method, ID scheme, change protocol, and Definition of Ready are in `agile.md`. Open design questions that block building are in `ambiguity_register.md`.

## Decisions made

| Fork | Decision |
|---|---|
| C scope | Core sim is a plain C library with no Godot dependency. Phase 1 reuses today's length-prefixed JSON pipe contract so Godot is untouched. Phase 2 adds a thin GDExtension binding and deletes the pipe. Tests always hit the C lib directly. |
| QA display | Forge, Xorg virtual screen on the RTX 3060 (nvidia xorg.conf with dummy monitor). Real GPU, unattended, no human collision. |
| QA tiers | T1 state-level QA drives the C sim with no rendering and detects RTS bugs from traces. T2 visual QA drives the real Godot window via xdotool plus screenshots and video. T1 runs first and most; T2 catches render-only bugs. |
| Claude escalation | Flag file plus evidence bundle; Westley opens a chat by hand. A pinned-chat `/loop` watcher is documented as an opt-in mode, off by default. Agora decision D16 (no unattended Claude) stays. |
| Method | Agile. Epics, stories, rules. Requirements may change; the change protocol keeps bible, tests, and Agora tasks in sync. |
| Determinism | The C sim is bit-deterministic across Windows, macOS, and Linux from the first sprint, with a checksum hook. Keeps lockstep co-op over Steam Datagram Relay possible; see `research/c_rewrite.md` and `research/multiplayer_sdr.md`. |
| Parallelism | Planning and building run in parallel. A story is built only after it passes the Definition of Ready. Deep features need not be fully designed before Agora starts on the earliest, simplest ones. |

## The cautionary example: the layer system

The 2.5D vertical layer system was meant to be the strategic defining characteristic of the game. In code it exists (layer masks, layer preference commands, cone and pulse visibility factors in `simulation/fog_of_war.py`), but units never change elevation by layer, and in testing no different layer vision was observable. The feature was never defined clearly enough to be implemented, and the idea itself was never fully fleshed out.

Every stage below carries a Definition of Ready gate and an ambiguity register so a feature like this cannot enter a sprint until its "what" is nailed down: every input mapped, every output mapped, every open question answered by Westley or explicitly deferred with the feature. The layer system is the first epic run through the gate in Stage 2, as the worked example that proves the gate catches this class of problem.

## Stages

```
Stage 0  Proving ground   Toy tasks + planted bugs; Agora must pass before Sprint 0   -> proving_ground/
Stage 1  Bible audit      Sonnet 5 chat, Westley confirms keep/kill per idea          -> stage1_audit.md, vision_v2.md
Stage 2  Bible reformat   Rewrite bible as epics/stories/rules + references           -> docs/bible/**, generated Agora rules
Stage 3  E2E definition   Per epic: inputs, outputs, rules, edges, scale, DoR         -> e2e/E-##.md
Stage 4  Roadmap          Product backlog, sprints, escalation ladder                 -> roadmap.md, backlog.md, sprints/
Stage 5  TDD tests        Claude writes the fenced test suite per story               -> tests/
Track R  Research         R1 QA driving, R2 C rewrite, R3 escalation, R4 RTS bugs     -> research/
```

Stages 1 and 2 run once, in full, because they produce the source of truth. Track R runs alongside them. Stage 0 runs after the R1 and R2 spikes and before any sprint. Stages 3, 4, and 5 are a per-epic pipeline that repeats for the life of the project: an epic enters Stage 3 when the roadmap prioritizes it, passes the Definition of Ready, gets its tests in Stage 5, and then Agora builds it while Claude runs the next epic through the pipeline.

Agora may begin Sprint 0 (toolchain) once the R1 and R2 spikes pass and Stage 0 probes A through E are green. It may begin the first strategic-sim rungs (region fields, composites, drift equations, world graph) once Stage 1's algorithm pass and the Stage 2 epic files for those rungs are Ready. Nothing waits on the whole bible being defined; everything waits on its own epic being Ready.

### Stage 0 — Proving ground

Toy tasks with planted defects that prove Agora can build C against fenced tests, obey a scale gate, detect each RTS bug class from traces, drive a real Godot window, escalate to a flag, and absorb a requirement change. Lives in a separate toy repo. Details and the probe table: `proving_ground/README.md`. Sprint 0 opens only when probes A through E pass.

### Stage 1 — Bible audit

A separate Claude Sonnet 5 chat walks every bible file and produces a ledger with one row per idea (rule, mechanic, story, aspiration, implementation claim) and Westley's verdict: keep, kill, rewrite, defer. A vision interview runs first and produces `vision_v2.md`, which every later verdict is checked against. An algorithm pass gives a verdict per retained equation. No bible edits happen in this stage. The chat's briefing is `stage1_brief.md`. Done when every heading has a ledger row, no row is unsure, vision_v2 is confirmed, and the algorithm pass is complete.

### Stage 2 — Bible reformat

Rewrite `docs/bible/**` into: a short human-facing hub; `stories.md`, the story catalog; `epics/E-##-<slug>.md`, one file per epic with stories, rules, inputs, outputs, invariants, scale requirements, references, ways this could be wrong, open flags, and dependencies; `references/E-##/` with screenshots and notes from games Westley points at; `algorithms.md`, the retained equations as named formulas. A script derives Agora's per-epic rules files from the epic files. Every epic runs the definition-completeness gate in `agile.md` before leaving this stage; the Layer System epic goes first. Also rewrites `CLAUDE.md`, `docs/workflow.md`, and retires `docs/priority_queue.md` in favor of the backlog.

The reference-gathering segment: for every epic with a visible surface, Claude asks Westley for two to five screenshots or clips from games that show what he wants, one sentence on what specifically in each is the target, and one sentence on what he does not want. Stories with a visible surface and no reference are not Ready.

### Stage 3 — End-to-end definition (per epic)

For each epic the roadmap pulls: actor and surface; the full input space with ranges and rejection behavior; the full output space; rules as Given/When/Then; edge cases; scale gates with hard numbers; which R4 bug signatures apply and which tier detects each; what evidence to capture on failure. Any question Claude cannot answer becomes a `Q-###-##` flag with candidate answers; Claude never picks silently. Exit is the Definition of Ready in `agile.md`.

### Stage 4 — Roadmap, backlog, sprints

A product backlog of every story with status (Spec'd, Ready, Tested, Queued, Building, Built, Revised). Sprints pull only from Tested. The roadmap orders epics on four ladders: strategic sim, tactical sim, integration (pipe in C, then GDExtension), and client (only after the sim ladders are green). Sprint 0 is toolchain. One task equals one story bounded by Agora's `max_impl_lines`. A sprint may open while later epics are still being defined, provided every story in it is Tested and its dependencies are Built. Early sprints may target throwaway prototypes. The escalation ladder (worker retry, DeepSeek reorganize or solve-direct, spiral detection, flag file, Westley, opt-in loop watcher) is defined in `escalation.md` once R3 lands.

### Stage 5 — TDD tests (per story)

Before a story is queued, Claude writes its failing tests from the e2e file: C unit tests, invariant and trajectory tests, scale benchmarks, T1 QA scenarios with positive controls, T2 director-mode missions, and contract tests. Tests live in fenced paths Agora cannot edit. Every test names the story and rule it proves. A test that cannot fail is a defect. Tests become the task's `acceptance:` commands.

### Track R — Research

Four briefs in `research/`: `qa_driving.md` (how the model is the user on forge), `c_rewrite.md` (toolchain, harness, architecture, algorithm inventory, perf targets), `escalation.md` (spiral signals, flag file, notification, start-over protocol, opt-in watcher), `rts_bug_catalog.md` (every bug class with detector tier and evidence). R1 and R2 each end in a spike proof that gates Stage 0.

**Research tooling.** Westley has an unused Gemini Pro subscription. Track R may dispatch scoped deep-research questions (vendor comparisons, exact setup steps, nitty-gritty technical options for a stated use-case) to Gemini via its API, CLI, or Deep Research mode, then Claude verifies the output before it enters `research/`. Wiring Gemini in is a Research Lane task; usage volume is not a constraint.
