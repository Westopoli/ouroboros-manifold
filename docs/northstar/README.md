# North Star — Agora-Driven Development of Ouroboros Manifold

This directory is the current development method for the project. The complete approved plan is `PLAN.md` (canonical; this README is the short form). It overrides the workflow sections of `CLAUDE.md` and `docs/legacy/method_era1/workflow.md` wherever they disagree. The game bible (`docs/bible/`) remains the source of truth for *what the game is*; this directory is the source of truth for *how it gets built*.

## The north star

Agora (`~/Projects/agora`, an autonomous loop of local Ollama models plus a dollar-capped DeepSeek driver) develops and QA-tests the whole game end to end, unattended. Claude does judgment day-side: designs the bible, defines every behavior end to end, writes the tests, plans the sprints, and writes the escalation rules. The game is rewritten in C for speed, keeping the stochastic equations that make the world work.

Principles that persist beyond any chat are in `principles.md`. The agile method, ID scheme, change protocol, and Definition of Ready are in `agile.md`. Open design questions that block building are in `ambiguity_register.md`.

## Current position (2026-09-13)

**Stage 2 complete.** The bible is reformatted into 21 epics, a story catalog, algorithms, and references; CLAUDE.md/workflow rewritten; `priority_queue.md` retired; the rules-derivation script written; all 21 epics ran the completeness gate. Westley's ambiguity-register answers are recorded (64 rows answered/deferred), so E-02, E-04, E-05, E-06, E-08, E-09, E-10, E-11, E-12, E-17 have empty registers.

**Stage 3 active, per epic.** E-02 (region fields, composites, drift) is **Ready** (2026-09-14): e2e file `e2e/E-02.md` authored, three flags folded, scale gates confirmed, stories S-012 … S-020 Ready. Next: Stage 5 writes E-02's 43 failing tests, which first needs the C sim-core test-harness contract defined (the pytest-via-ctypes ABI and T1 trace format). E-03 (world generation) is the next epic through Stage 3, once its register answers are on main (PR #40) and its last open flag is answered. Stage 4 (roadmap/backlog/sprints) has not started.

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
| Epic end-state (2026-09-12) | Before an epic is queued, Claude or the design chat writes what "done" looks like both technically (fixed-seed trajectories, checksums, perf, trace facts) and visually (what the finished screen shows the player, or an explicit "none direct"). A required Definition-of-Ready gate; mechanics in `agile.md`. Slows queueing a little; buys better tests and a build target to converge on. |
| Layer system prototype and design phase (2026-09-13, revised 2026-09-14) | The layer system (E-01) is the game's most distinctive mechanic and hard to change once built, so it gets a real design phase instead of a reference pull. Round 1 of Track L ships a **two-layer prototype** (marked prototype story, replaced not extended) as the first design-phase option, so friends see layers from the first build. On that prototype Claude builds further interactive options for Westley and testers to compare; the chosen option becomes E-01's visual end-state. E-01's own stories are not queued until that choice is made. |
| UI surfaces are TBD design, not references (2026-09-13) | Main menu, HUD-beyond-IGoP, mission briefing/debrief (E-10), and generational setup (E-08) are highly modifiable and start simple, iterated on player feedback; they get simple mockups/prototypes, not other-game screenshots. The existing in-game galaxy view (good animation) is reused for E-09. Contrast with the layer system, which is front-loaded because it is hard to change later. |
| Combined gating test (2026-09-14) | Each story's gating test proves behavior, speed, and scale together in one test — a fast-but-wrong, correct-but-slow, or correct-but-undersized run all fail it. Exact-value algebra rules with no speed/scale axis stay separate single-leg unit tests. Amended into PLAN.md (principle 5, Stage 5 test layers, Done-when) and the Definition of Ready. |
| Trivial decisions and flag hygiene (2026-09-14) | Claude decides trivial design choices (nothing a player would notice, nothing another story depends on) without a flag and records them in the rule text. Before raising a flag, Claude checks `algorithms.md`, the Stage 1 ledger, and closed register rows; a duplicate flag is a defect. Every flag carries a recommended candidate; Westley answers per epic with "approve" or overrides by id. Mechanics in `agile.md`. |
| Lean MVP loop, Track L (2026-09-14) | Playtest rounds (friends, Discord cohort, Steam Playtest) decide build order. Substrate is the C sim and new Godot client only; the legacy Python slice is not used for playtests. Agora builds client and packaging too, after a GDScript probe (H) and an export probe (I) pass. Stories are cut by omission, never thinned. Rounds open on evidence, not dates. Method, ranking, per-epic cuts, build path, and the experiment log are in `mvp/`; Track L's own flags are `Q-MVP-##`. |
| Spec factory, gemini compute, playtester site (2026-09-14) | Westley's spare Google AI Pro capacity runs transcription-class Stage 3/5 steps (fold answers, draft e2e, fill tests, card briefs) via `agy` (Antigravity CLI), subscription-only, no API key; Claude still authors, gates, flags, and reviews every diff. Register protocol v3: every flag carries a recommended candidate, Westley answers "approve defaults" or overrides by id. Scripts and the pipeline are in `spec_factory.md`; the `agy` spike is `research/gemini_compute.md`. A separate `ouroboros-site` repo on fly.io shows playtesters the roadmap and concept art as targets, never promises. |

## The cautionary example: the layer system

The 2.5D vertical layer system was meant to be the strategic defining characteristic of the game. In code it exists (layer masks, layer preference commands, cone and pulse visibility factors in `simulation/fog_of_war.py`), but units never change elevation by layer, and in testing no different layer vision was observable. The feature was never defined clearly enough to be implemented, and the idea itself was never fully fleshed out.

Every stage below carries a Definition of Ready gate and an ambiguity register so a feature like this cannot enter a sprint until its "what" is nailed down: every input mapped, every output mapped, every open question answered by Westley or explicitly deferred with the feature. The layer system is the first epic run through the gate in Stage 2, as the worked example that proves the gate catches this class of problem.

## Stages

```
Stage 0  Proving ground   Toy tasks + planted bugs; Agora must pass before Sprint 0   -> proving_ground/
Stage 1  Bible audit      Sonnet 5 chat, Westley confirms keep/kill per idea          -> stage1_audit.md, vision_v2.md
Stage 2  Bible reformat   Rewrite bible as epics/stories/rules + references           -> docs/bible/**, generated Agora rules
Stage 3  E2E definition   Per epic: inputs, outputs, rules, edges, scale, DoR         -> e2e/E-##.md
Stage 4  Roadmap          Prototype ladder, the chain as backlog, escalation ladder    -> PLAN.md Factory section, sprints/
Stage 5  TDD tests        Claude writes the fenced test suite per story               -> tests/
Track R  Research         R1 QA driving, R2 C rewrite, R3 escalation, R4 RTS bugs     -> research/
Track L  Lean MVP loop    Rounds to testers; ranks and cuts; owns Stage 3 order     -> mvp/
```

Stages 1 and 2 run once, in full, because they produce the source of truth. Track R runs alongside them. Stage 0 runs after the R1 and R2 spikes and before any sprint. Stages 3, 4, and 5 are a per-epic pipeline that repeats for the life of the project: an epic enters Stage 3 when the roadmap prioritizes it, passes the Definition of Ready, gets its tests in Stage 5, and then Agora builds it while Claude runs the next epic through the pipeline.

Agora may begin Sprint 0 (toolchain) once the R1 and R2 spikes pass and Stage 0 probes A through E are green. It may begin the first strategic-sim rungs (region fields, composites, drift equations, world graph) once Stage 1's algorithm pass and the Stage 2 epic files for those rungs are Ready. Nothing waits on the whole bible being defined; everything waits on its own epic being Ready.

### Stage 0 — Proving ground

Toy tasks with planted defects that prove Agora can build C against fenced tests, obey a scale gate, detect each RTS bug class from traces, drive a real Godot window, escalate to a flag, and absorb a requirement change. Lives in a separate toy repo. Details and the probe table: `proving_ground/README.md`. Sprint 0 opens only when probes A through E pass.

### Stage 1 — Bible audit

A separate Claude Sonnet 5 chat walks every bible file and produces a ledger with one row per idea (rule, mechanic, story, aspiration, implementation claim) and Westley's verdict: keep, kill, rewrite, defer. A vision interview runs first and produces `vision_v2.md`, which every later verdict is checked against. An algorithm pass gives a verdict per retained equation. No bible edits happen in this stage. The chat's briefing is `stage1_brief.md`. Done when every heading has a ledger row, no row is unsure, vision_v2 is confirmed, and the algorithm pass is complete.

### Stage 2 — Bible reformat

Rewrite `docs/bible/**` into: a short human-facing hub; `stories.md`, the story catalog; `epics/E-##-<slug>.md`, one file per epic with stories, rules, inputs, outputs, invariants, scale requirements, references, ways this could be wrong, open flags, and dependencies; `references/E-##/` with screenshots and notes from games Westley points at; `algorithms.md`, the retained equations as named formulas. A script derives Agora's per-epic rules files from the epic files. Every epic runs the definition-completeness gate in `agile.md` before leaving this stage; the Layer System epic goes first. Also rewrites `CLAUDE.md`, `docs/legacy/method_era1/workflow.md`, and retires `docs/legacy/method_era1/priority_queue.md` in favor of the backlog.

The reference-gathering segment: for every epic with a visible surface, Claude asks Westley for two to five screenshots or clips from games that show what he wants, one sentence on what specifically in each is the target, and one sentence on what he does not want. Stories with a visible surface and no reference are not Ready.

### Stage 3 — End-to-end definition (per epic)

For each epic the roadmap pulls: actor and surface; the full input space with ranges and rejection behavior; the full output space; rules as Given/When/Then; edge cases; scale gates with hard numbers; which R4 bug signatures apply and which tier detects each; what evidence to capture on failure; and the epic's **end-state** — what done looks like technically (fixed-seed trajectories, checksums, perf, trace facts) and visually (what the finished screen shows the player, or an explicit "none direct" for a pure-sim epic). Any question Claude cannot answer becomes a `Q-###-##` flag with candidate answers; Claude never picks silently. Exit is the Definition of Ready in `agile.md`, which now requires the end-state before an epic can be queued.

### Stage 4 — Roadmap, backlog, sprints

A product backlog of every story with status (Spec'd, Ready, Tested, Queued, Building, Built, Revised). Sprints pull only from Tested. The roadmap orders epics on four ladders: strategic sim, tactical sim, integration (pipe in C, then GDExtension), and client (only after the sim ladders are green). Sprint 0 is toolchain. One task equals one story bounded by Agora's `max_impl_lines`. A sprint may open while later epics are still being defined, provided every story in it is Tested and its dependencies are Built. Early sprints may target throwaway prototypes. The escalation ladder (worker retry, DeepSeek reorganize or solve-direct, spiral detection, flag file, Westley, opt-in loop watcher) is defined in `escalation.md` once R3 lands.

### Stage 5 — TDD tests (per story)

Before a story is queued, Claude writes its failing tests from the e2e file: C unit tests, invariant and trajectory tests, scale benchmarks, T1 QA scenarios with positive controls, T2 director-mode missions, and contract tests. Tests live in fenced paths Agora cannot edit. Every test names the story and rule it proves. A test that cannot fail is a defect. Tests become the task's `acceptance:` commands.

### Track R — Research

Four briefs in `research/`: `qa_driving.md` (how the model is the user on forge), `c_rewrite.md` (toolchain, harness, architecture, algorithm inventory, perf targets), `escalation.md` (spiral signals, flag file, notification, start-over protocol, opt-in watcher), `rts_bug_catalog.md` (every bug class with detector tier and evidence). R1 and R2 each end in a spike proof that gates Stage 0.

**Research tooling.** Westley has an unused Gemini Pro subscription. Track R may dispatch scoped deep-research questions (vendor comparisons, exact setup steps, nitty-gritty technical options for a stated use-case) to Gemini via its API, CLI, or Deep Research mode, then Claude verifies the output before it enters `research/`. Wiring Gemini in is a Research Lane task; usage volume is not a constraint.

### Track L — Lean MVP loop

A parallel track that decides which epics and stories enter Stage 3 next by shipping cuts to playtesters in rounds (friends, Discord cohort, Steam Playtest) and measuring what players actually value against what the bible assumes. Cuts are by story omission; gates are unchanged; client and packaging work goes through Agora after probes H and I pass. Full definition in `PLAN.md` Track L; method, the ranked list of what the game offers, per-epic cuts, the build path, and the living experiment log in `mvp/`.
