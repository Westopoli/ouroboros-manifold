# North Star Plan (canonical, approved 2026-09-10)

This is the complete approved plan, kept verbatim so it outlives any chat. `README.md` in this directory is the short form; when they disagree, this file wins. Stages 3, 4, and 5 repeat per epic for the life of the project, so this document is bible-analogous: rewrite, never append. Decisions made after approval are recorded in `README.md`'s decisions table and in the scorecard, not appended here.

---

# North Star Plan — Agora-Driven E2E Development of Ouroboros Manifold

## Context

The project has been idle since 2026-06-05 (157 commits, 2026-04-02 to 2026-06-05). Near the end, Westley had a crisis about what the game should be; the bible was append-only for months and, even after the 2026-05-30 cleanse, the spokes still carry contradictions and orphaned references. Meanwhile a separate system, **Agora** (`~/Projects/agora`), now exists: an autonomous, systemd-managed loop (local `qwen3:8b` worker + `qwen3-coder:30b` planner + dollar-capped DeepSeek driver) that plans, executes, tests, and reports without a human in the loop.

The new north star: **Agora develops and QA-tests the whole game end to end, autonomously.** Claude does judgment day-side (designs the bible, the roadmap, the tests, and the escalation rules); local models do the volume work at night. The game is rewritten in C for speed, keeping the stochastic equations that make the world work.

This plan lays out five stages plus a parallel research track. It defines the goal, inputs, method, output, and done-criteria of each stage. It does not execute the stages. Executing this plan produces the durable documents that make the north star survive beyond this chat.

## Decisions already made (this session)

| Fork | Decision |
|---|---|
| C scope | Core sim is a plain C library with no Godot dependency. Phase 1 reuses today's length-prefixed JSON pipe contract, Godot untouched. Phase 2 adds a thin GDExtension binding and deletes the pipe. Tests always hit the C lib directly. |
| QA display (visual tier) | Forge, Xorg virtual screen on the RTX 3060 (nvidia xorg.conf with dummy monitor). Real GPU, unattended, no human collision. |
| QA tiers | T1 state-level QA drives the C sim directly with no rendering, detects RTS bugs from traces. T2 visual QA drives the real Godot window via xdotool + screenshots/video. T1 runs first and most; T2 catches render-only bugs. |
| Claude escalation | Flag file + evidence bundle now (Westley opens a chat by hand). Pinned-chat `/loop` watcher documented as an opt-in mode enabled manually later. Keeps Agora D16 (no unattended Claude) as the default. |
| Method | Agile. Requirements decompose into epics → stories → rules (acceptance criteria). Requirements may change as we go; a change protocol keeps bible, tests, and Agora tasks in sync. |
| Parallelism | Planning and building run in parallel. A story may be built only after it passes the Definition of Ready gate (fully mapped inputs/outputs, zero open ambiguity flags, references attached, tests written). Deep features need not be fully designed before Agora starts on the earliest, simplest ones. |

## The cautionary example: the layer system

The 2.5D vertical layer system was meant to be *the* strategic defining characteristic of the game. In code it "exists" (layer masks, layer preference commands, cone/pulse visibility factors in `simulation/fog_of_war.py`), but units never actually change elevation by layer, and in testing no different "layer vision" was observable. The feature was never defined clearly enough to be implemented, and the idea itself was never fully fleshed out.

This is the failure the plan is built to prevent. Every stage below carries a **Definition of Ready** gate and an **ambiguity register** so that a feature like this cannot enter a sprint until its "what" is nailed down: every input mapped, every output mapped, every open question either answered by Westley or explicitly deferred with the feature. The layer system is the first feature run through the gate in Stage 2, as the worked example that proves the gate catches this class of problem.

## Ground truth from the survey

**Ouroboros repo**
- 88,754 lines Python + GDScript. Zero C. No `requirements.txt`, no `pytest.ini`, no CI. Deps (numpy, matplotlib, Pillow, pytest) undeclared.
- Stochastic engine lives in: `simulation/world.py` (graph gen, starting fields), `simulation/drift.py` (per-field equations, oscillator kernel), `simulation/faction.py` (attractiveness, budget pressure, entrenchment, viability), `simulation/intent_resolver.py` (attack resolution), `simulation/border_friction.py`, `simulation/technology.py`, `simulation/admin_revolt.py`, `simulation/region.py` (composites). All randomness is `random.Random(seed)`; no `np.random`. Tactical layer (`unit.py`, `movement.py`, `damage.py`, `fog_of_war.py`, `facing.py`, `ability.py`) uses numpy SoA arrays.
- No "psychohistory prediction" system exists; CLAUDE.md only permits the concept.
- Tests: 491 `def test_` across 65 pytest files, plus ~65 print-style `test_*.py` scripts in the same flat `simulation/` dir. `simulation/invariants.py` has ~70 trajectory invariants. 13 Godot scene tests in `tests/`.
- Transport: `autoload/sim_bridge.gd` spawns `simulation/pipe_transport.py`; sim to Godot over stdout (4-byte BE length prefix + JSON); Godot to sim over a polled temp command file (Godot 4.6 bidirectional pipe bug). Delta shape in `simulation/snapshot_serializer.py`, documented in `docs/architecture.md`.
- Bible: hub `docs/bible/game_bible.md` (415 lines) + 9 spokes (3,728 lines total). Hub is clean of append markers; drift now lives in spokes and orphaned cross-refs (deleted `bible_monetization.md` still cited in `docs/architecture.md:194` and ~18 research briefs; `docs/design_lane.md` still mandates In Flux sections the hub forbids; price $10–15 in hub vs $25–35 in research; "Roman-era sci-fi" in hub Monetization). 24 historical snapshots in `docs/bible_history/`.
- Stale claims that Stage 1 must catch: CLAUDE.md protected-file list names `templates.py`, `theme_scifi.py`, `event_engine.py`, none of which exist; `autoload/tactical_bridge.gd:2` says "Owns the TCP connection" (socket server deleted); `library_builder.py --mode api` is a stub.
- Priority queue NEXT is empty. 6 Soon, 24 Backlog, 16 research-only items.

**Agora** (`~/Projects/agora`)
- Entry point `scripts/next.py`, one unit of work per tick: QA session, then burner (`burn.py`), then optimizer, then proposer, then digest, then DeepSeek driver (`driver.py`).
- Task = `queue/NNN-slug.md` with YAML frontmatter: `project`, `goal`, `acceptance:` (list of executable commands, ground truth), `constraints`, `max_iterations`, `max_wall_minutes`, `pace`. Template at `queue/TEMPLATE.md`.
- Campaign = `campaigns/todo/NNN-slug.md` with `tool:`, `project:`, `profile:`, `budget_usd`, `budget_sessions`, `converge_after_sessions`.
- Per-project profile `projects/<slug>/qa.toml` + distilled per-feature rules `projects/<slug>/rules/*.md` (overlord-written, "ways this could be wrong" section). D17: DeepSeek reads rules files, never the target's own bible.
- Escalation: `stall_threshold = 3`, modes `solve-direct` / `reorganize`, `propose_after = 3`, watchdog every 20 sessions, `BUDGET-HALT.md` on cap. Budgets `nightly_max_usd = 0.50`, `monthly_max_usd = 5.00`.
- Worker isolation via git worktrees, branch prefix `agora/`, nothing merges without acceptance pass, human merge gate.
- Precedent for the bible format Agora consumes: `~/Projects/the-best-salesmen/bible.md` §16 "Expected Behaviors — User-Perspective Catalog" (one row per user-facing behavior: id, user's words, status, depth pointer) + §12 Given/When/Then acceptance criteria.
- QA driving today = Playwright (browser only). Nothing drives a desktop app.
- Machine: 16 cores, 30 GiB RAM, RTX 3060 12 GB. No DISPLAY in shell. Godot not installed. gcc + make present; no cmake, clang, ninja, xdotool, ffmpeg, tesseract.

## Core principles (persist beyond this chat)

These go into `docs/legacy/agora_era/principles.md` and get a pointer from CLAUDE.md.

1. **Autonomy is the product.** The system (Agora: local models + DeepSeek) builds and QA-tests the game unattended. Anything a human must do mid-loop is a design defect in the plan, not a task for Westley.
2. **Claude does judgment, day-side only.** Claude designs the bible, the E2E behavior definitions, the roadmap, the tests, and the escalation rules. Claude never runs in an unattended path by default (Agora D16). Opt-in loop watcher is a documented exception Westley enables by hand.
3. **Tests are the spec.** Every feature exists as failing tests before Agora touches code. Tests are fenced; Agora cannot edit them. A failing test always has a reason and the loop keeps iterating until green. Every detector has a positive control proving it can fail.
4. **Small bites, upward.** Sprints feed tiny features in dependency order. One task = one feature = one acceptance command set, bounded by Agora's `max_impl_lines`. QA runs on every task, not at the end.
5. **Scale is a test, together with behavior and speed.** Tests induce high input (units, regions, ticks) with hard thresholds. Under-threshold means the sprint is not done. Scale is never measured apart from behavior: a story's gating test runs at the confirmed scale and asserts, in one test, that the result is behaviorally correct, within the speed budget, and at the required scale. A fast-but-wrong, a correct-but-slow, and a correct-but-undersized run all fail the same test.
6. **C for speed, equations preserved.** The sim is rewritten in C. The stochastic equations (drift, world gen, faction scoring, attack resolution, friction, tech) are retained verbatim as named formulas unless Stage 1 kills them. Determinism via seeded RNG is a contract.
7. **The model is the user.** QA drives the game the way a player does and watches for what a player hates (rubber-banding, stuck units, backwards walking, dropped orders, and the rest of the RTS bug catalog). Two tiers: T1 state traces, T2 visual.
8. **Escalation is a ladder with a top.** The local model stalls; the escalator (Gemini via `agy`) hints, resets, or declares the card unsatisfiable; a plateau (distinct candidates, identical failing set) stops the run early; an upstream defect named by the escalator becomes its own fix task; the cap parks the card and writes an English flag with evidence. Only design decisions reach Westley. "Start over" is a defined protocol, not a panic.
9. **Bible describes now.** Rewrite, never append. Machine-consumable structure (stable IDs, story catalog, per-epic rules) so Agora artifacts derive from it by script.
10. **Agile, not waterfall.** Requirements are epics → stories → rules. They may change while building. A change runs the change protocol (story revised → bible rewritten → tests revised by Claude → Agora task respec'd) in one pass, never partially.
11. **Definition of Ready gates building.** Nothing enters a sprint until its inputs and outputs are fully mapped, its ambiguity register is empty, its look-and-behavior references are attached, and its tests exist. A story that fails the gate is a planning task, not a build task.
12. **Ambiguity is flagged, never guessed.** When Claude finds an under-defined behavior, it raises a `[NEEDS WESTLEY]` flag in the ambiguity register with the concrete question and candidate answers. Local models never see an open flag; they only see resolved rules.
13. **Prove the tool before trusting it.** Before Agora touches the game, it passes toy probes with planted defects: build to fenced tests, obey a scale gate, catch each RTS bug class, drive a real Godot window, escalate to a flag, absorb a requirement change. A capability that has not been shown to fail on a planted defect is not a capability the plan may rely on.
14. **The harness is a tenant of the project, never the reverse.** Everything that names the game lives in the project or its profile; Agora stays product-blind so a second project onboards with data, not a fork, and an undefined future feature needs no harness code.
15. **A QA pass that cannot fail is not a QA pass.** Every session proves its inputs land, every scenario has a planted variant where it must fail, a session whose actions never mutate state ends `harness-error` and never counts as clean, and a planted-build campaign with zero findings is a harness failure.
16. **Width, not length.** Token cost is context size times calls; a cached re-read is cheap per token but still about a tenth of fresh input, and the cache lasts one hour. Parallel work is many short-lived agents with small contexts (one file, a brief under a page, one report), run back to back. Measured: the 2026-09-22 workflow day averaged about 270,000 tokens re-read per call and cost roughly three times more per landed line than the 2026-10-02 relay at about 87,000.
17. **Parallel lanes never share a file; wiring is queued.** New systems are built in new files behind a frozen header, one lane per file. Each lane ends with a small wiring piece on the shared file, landed one at a time, and the playthrough runs after each. The 2026-09-22 push was fast because it was file-disjoint, and it left 480 of 682 tested symbols unreachable from play because nobody owned the wiring.
18. **Seen before planned.** A feature whose rightness is judged by eye or by feel gets a rough prototype that Westley approves before any integration plan, story test or workflow is written for it. The prototype is disposable; what it produces is his decisions. The gate is in `agile.md`, Prototype gate.

## Stage overview

```
Stage 0  Proving ground       Toy tasks + planted bugs; Agora must pass before Sprint 0 -> proving_ground/P#.md + SCORECARD
Stage 1  Bible audit          Sonnet 5 chat, Westley confirms keep/kill per idea   -> stage1_audit.md ledger + vision v2
Stage 2  Bible reformat       Rewrite bible as epics/stories/rules + references    -> new docs/bible/** + generated agora rules
Stage 3  E2E definition       Per epic: inputs, outputs, rules, edges, scale, DoR  -> docs/northstar/e2e/E-##.md
Stage 4  Roadmap              Product backlog, sprints, escalation ladder          -> docs/northstar/roadmap.md + sprint files
Stage 5  TDD tests            Claude writes the fenced test suite per story        -> tests/ (C, Python harness, QA scenarios)
Track R  Research (parallel)  R1 QA driving, R2 C rewrite, R3 escalation, R4 RTS bug catalog -> docs/northstar/research/*.md
Track L  Lean MVP loop (parallel) Rank, cut, ship to testers, measure, re-plan; owns Stage 3 order -> docs/legacy/mvp/
```

**Global stages vs per-epic pipeline.** Stages 1 and 2 run once, in full, because they produce the source of truth. Track R runs alongside them. Stages 3, 4, 5 are a **per-epic pipeline** that repeats for the life of the project: an epic enters Stage 3 when the roadmap prioritizes it, passes the Definition of Ready, gets its tests in Stage 5, and then Agora builds it while Claude runs the next epic through the pipeline.

**Earliest build start.** Agora may begin Sprint 0 (toolchain) as soon as Track R1/R2 spikes pass and Stage 0 probes A–E are green, and may begin the first strategic-sim rungs (region fields, composites, drift equations, world graph) as soon as Stage 1's algorithm pass and the Stage 2 epic files for those rungs are Ready. Tactical, integration, and client epics keep being defined while those build. Nothing waits on the whole bible being e2e-defined; everything waits on its own epic being Ready.

**Layer system (E-01) design phase and its sequencing.** The layer system is the game's most distinctive mechanic and is hard to change once built, so it does not go straight from epic to build. The earliest tactical work ships **basic unit movement on a single layer first** (no layer mechanic), giving a working simple prototype of the game. Only after the first couple of epics have produced that prototype does the layer system enter its design phase: Claude plans and builds several interactive layer-system options in Godot on top of the prototype, Westley plays with them and chooses, and the chosen option becomes E-01's visual end-state. So single-layer movement is an early rung; the full layer mechanic is deliberately deferred behind a working prototype and a real design pass, not defined blind. (Decision 2026-09-13; recorded in `README.md`'s decisions table.)

## The Factory — how Agora builds and verifies autonomously

This section is the operating model for everything after Stage 2. It was designed on 2026-09-17 to 19 from the harness defect investigation, seven research memos and the mining of 77 real runs (`research/harness_defects_2026-09-17/`, `research/factory/`); the decisions behind each line are in `research/harness_defects_2026-09-17/DECISIONS.md`. Two requirements shape it beyond the principles: it must absorb features nobody has defined yet without harness code changes, and it must serve a second project with a profile and a bible, not a fork.

### One chain, nine artifacts

Every artifact has a schema, one owner, a fence (who may not edit it) and a positive control (a way to show it can be wrong). No schema names Ouroboros.

| Artifact | Owner | Fence | Positive control |
|---|---|---|---|
| Story: rules as Given/When/Then, visual end-state, "ways this could be wrong", references | Claude, Westley confirms | Agora never reads the bible | Definition of Ready |
| Expectation spec: per rule, `given` (fixture, seed, switches), `when` (directives), `then` (state checks; invariant ids; visual claims, declared empty when none), scale gate | Script, generated from the story, never hand-edited | Drift check: a test whose rule has no entry, or a fenced test changed without its epic, fails | A wrong number in the spec must make its test red |
| Tests and controls, fenced | Skeletons by script, bodies by agy, Claude owns | The worker cannot edit; fence check on every diff | red check; every control trips on its planted build |
| Card: kind (build, gate, content, repair), one file, symbols, acceptance commands, allowed files, brief, header slice, size. A content card is a gate over a pack directory (validators plus the fenced content diff, no model call). A repair card is generated from a confirmed finding on merged code: the finding becomes a fenced regression test and the card's acceptance is that test | Script; lint gates | Worker sees brief, slice and skeleton only | Card lint; fail-first gate |
| Candidate: the worker's reply and its spliced diff | Local 30B, Gemini hints | Only the named function(s) in one file change | Diff-revert, shadow fixture, diff-scoped mutation |
| Merge | Harness | Whole headless suite stays green | A known-bad merge replayed must be rejected |
| Gate result: story, epic or rung gate, no model | Harness | Red stops the chain | A planted-bug build turns a gate red |
| QA mission and finding: mission from the spec, session log, evidence, verdict (`bug`, `test-defect`, `false_positive`, `harness-error`, `contradiction`), fingerprint, replay bundle. A `contradiction` cites two spec entries that each pass their own tests; the design lane turns it into a `Q-` row, and `story-defect` is assigned there, never by the verifier, which does not read the bible | Scripted actor first, 30B on escalation; verifier separate | The actor never writes verdicts; `harness-error` never counts as clean | A planted-build campaign must produce findings |
| Revision and proposal: change-protocol PR; refiner proposal, never auto-applied | Claude; Gemini proposes; Westley applies | Thresholds, fences, allowed files, controls move only through Westley | A proposal that stops a control tripping is disqualified |

### Roles

| Role | Who | May change | May not |
|---|---|---|---|
| Specifier | Claude, day-side | Bible, stories, e2e, tests, controls, gate lists, chain order, profile data | Anything at runtime |
| Transcriber | Scripts, Claude-triggered until rung P2 is proven, then an Agora scheduled step that drains Tested stories into cards | Generated caches, cards, rules files | Their sources |
| Implementer | The local model (a profile setting; qwen3-coder:30b today) | The named function(s) in the card's file | Everything else; sees no tests |
| Escalator | A seat, not a model: the profile lists models in order with a dollar cap each (Gemini via agy, DeepSeek via the direct API, a Claude model), a call falls through on quota or timeout, and the ledger names which answered (PX-17: every agy group was empty for 45 hours, shared across accounts; `deepseek-v4-flash` did the job for cents) | The next brief; may declare a card unsatisfiable; may fix one named upstream function under the parent-patch fence when a fenced test is red and the diagnosis names that function, with the `card_slice` header slice in its prompt (PX-17: without it the model invents enum and struct names); more than one function, or a symptom-level diagnosis, becomes a repair card; may fix a test or a mission when a finding is classed `test-defect` or `false_positive` and the fix is a filter, a guard or one number, under the test-fix gate (every original assertion preserved, still red against the stub, fixture-defect detectors clear); a test whose scenario must be re-derived goes to Claude's test-authoring ledger (PX-18: R7l anchored on example numbers three times); every edit gets a ledger row reviewed at the epic architecture review | Cards, thresholds, allowed files, story text |
| Verifier and refiner | Gemini via agy, never the actor of the same mission | Verdicts, findings, replay bundles; proposal files per epic | Live prompts, config, fences |
| Judge of last resort | Westley | Everything, through flags and applied proposals | — |

Routing rule: only design decisions reach Westley (a story is a design decision, so a `story-defect` does; a `test-defect` or `false_positive` does not). Smarter models clear the path so the local model keeps moving.

### Three homes

If it names the game, it is not Agora's.

- `agora/`: dispatch and the release chain mechanics, the build loop (card parser, sizing constants, ladder, splice per language, fail-first, baseline, diff-revert, fence, regression gate, escalation, archive), the QA loop (action vocabulary, backends, protocol client, oracle framework, fingerprints, verifier, replay, refiner, harness positive controls), and lint tools that read a project only through its profile.
- `agora/projects/<slug>/`: profile, rules files, expectation specs, detector plugins, personas, planted-bug catalog, the chain order, campaigns, the gate set (every gate on by default; `orchestrators` is a list that may be empty; a gate switched off is named in the profile and appears in every run ledger), and the empty-chain work list. Data only. (The chain currently hard-coded in `next.py` moves here.)
- The project repo: bible, tests and controls, the code Agora edits, the dev-only debug hook, and the generators that emit the profile's data.

The boundary test is onboarding a second project with zero Agora code changes; a change that turns out to be needed goes into Agora generically (a new backend, language table entry or oracle class), never a project branch.

### Gates the worker cannot move

Fail-first (the tests must fail before), baseline, card lint (symbol closure and tick-stage closure: when a test calls an orchestrator such as `om_world_step`, every hook it runs joins the closure, and the chain is ordered by hook stage; a hook no card owns is not a silent block: lint names the wiring card that must exist, one line in the orchestrator with a tick-order test, and the chain places it first), control-coverage lint (a function's card carries the controls for the rules that function owns), control liveness (a story's own controls must flip between the clean build and their own injected build, or they are dead and block its card; a control whose feature is not built yet is pending, not defective; R7h, R7l and R9 were three dead controls that each cost a card its whole attempt budget, and a sweep of the 119 control files found only 10 live), sizing cap (five symbols, eighty lines; content cards sized by pack entry count), diff-revert (the diff must matter), shadow fixture (a hard-coded answer fails a perturbed fixture), diff-scoped mutation (mutating the candidate's changed lines, skipping comments and strings, must break a test, or the card is under-tested and does not merge; the report names which changed line no test constrains, and the run happens in the CPU slot before merge), fence (one file), whole-suite regression after every DONE with revert on any new failure, story and epic gates, sanitizer builds (UBSan; ASan via preload; sampled memcheck; never MSan through ctypes), determinism gates on every C card (repeat seed, traced versus untraced, gcc versus clang, -O0 versus -O2). Plateau (three distinct candidates failing on an identical test set) forces an escalator diagnosis call: a named cause (upstream defect, unsatisfiable fixture, contradiction) ends the run and routes the finding; otherwise the run continues with a hint (PX-08: stopping outright had false stops on cards that later passed). An identical reply resubmitted (same hash) ends the attempt at once; the retry budget is for distinct candidates. Diagnoses handed to the escalator are generated from the detector's report on the actual fixture, carry no example numbers from another configuration, and the reply must state the pair of values its fix separates so the gate can check it before applying anything. A hint that identifies an upstream defect aborts and hands the escalator a fix task. Parent patches obey the same ownership check as cards; hand-implementing a card is an escalation recorded in the ledger and signed off by Westley.

### QA architecture

- **Game-side hook**, one dev-only autoload daemon speaking the desktop-QA protocol: `state` (canonical, from the sim, not the UI), `tree`, `nav`, `seed`, `fixture`, `pause`, `step <n>`, `screenshot`, `inject <bug-id>` (planted bugs, present only when the debug port is enabled), `input` fallback. A web app or CLI implements the subset it has.
- **Actor**: scripted scenarios and personas first; the local model only translates a directive scripting cannot express; vocabulary `click fill goto reload back submit press drag wait read_state screenshot hotkey box_select camera_pan`, allowed per project and mission; the game is paused while the model thinks and stepped by tick between actions; step budgets; state-hash loop detection; a directive needing a verb the mission does not allow is a harness condition, never a product finding.
- **Oracles, in order of trust**: state checks from the spec; T1 trace detectors and invariants over the trace API; metamorphic relations (save and load, two seeds, replay determinism, desync as two sim instances in one process); visual claims judged by Gemini vision via agy, capped, a local model only if it measurably fits beside the worker. A finding needs at least one deterministic oracle; a vision-only claim files as `held` and asks for Westley's eyes.
- **Verifier**: replays the action log from the seed before filing; classifies `harness-error` (input never mutated state, verb unavailable, scene not loaded, port dead) as its own terminal status that never counts toward convergence. Every session writes a replay bundle (seed, fixture, action log, state reads, screenshots, mission and verdict text) and a one-command replay that reproduces the same scene and steps on Westley's display: what the model saw, he can see.
- **Control liveness**: the same rule the QA session applies to itself applies to every planted-bug control in the test suite: it must behave differently on the clean and injected builds, or it proves nothing.
- **Harness positive controls**: input-liveness precheck every session (mandatory for desktop profiles; PX-03 showed it, not the mid-session detector, catches real dead-input sessions); every scenario has a planted-build variant where it must fail; a planted-build campaign producing zero findings is a harness failure and blocks convergence; the escalator seat runs one canned fix case (known diagnosis, known fix) before any real fix task, and a failing canned case is a harness error (PX-17: a prompt heading bug produced four false fence violations before it was caught).
- **Scheduling**: a per-epic QA campaign activates when the epic's gate card is DONE; a nightly explorer campaign runs on the latest merged rung; a rung cannot close without its QA mission having run.
- **Regression tiers**: per candidate, the whole headless suite (seconds); per rung gate, the earlier rungs' QA missions (minutes); per epic gate, everything including planted-build campaigns (hours, off-peak).
- **Pipelining (the drive-thru rule).** The machine has one GPU, so there is one GPU slot (one model call at a time) and one CPU slot for everything else: worktree creation, baseline, lint, header slice, brief check, gate cards, T1 QA runs, replays, escalator diagnosis through agy, archive scoring. The CPU slot works ahead: when a build starts, the next eligible card is prepared end to end (worktree, baseline, lint, prompt assembled and measured) so the next attempt starts within one tick of the current card ending. The worker model stays resident (`OLLAMA_KEEP_ALIVE=-1`) while the chain has work. The chain is a dependency graph derived from tick-stage closure over stubs, not a hand-kept list; a dependency cycle or a symbol with two owning cards fails lint when the graph is built (PX-16 found both in the E-04 cut), and an escalated card never idles the GPU: the next independent card runs while diagnosis proceeds in a scratch worktree. Idle with a parked head is an alarm, first to the escalator, then to Westley. An empty graph is a different condition: the profile's empty-chain work list runs in priority order (the explorer campaign on the latest rung, a mutation sweep over the whole merged suite, sanitizer and memcheck full runs, determinism soaks, planted-build campaigns, refiner scoring), each producing ledger rows and never cards, and the ledger reports runway daily (Tested stories ahead times the measured minutes per shipped card); below 24 hours the alarm goes to Westley, so starvation is visible a day ahead. (Measured 2026-09-18/19 over 34 hours: 57.7% idle with nothing eligible behind a blocked chain head, in stretches of 4h21, 5h54 and 3h12; 32.7% building, most of it on cards later shown defective, 5.6 h on one; 9.6% stopped by hand; building time per shipped card about 52 minutes, which is the expectation. The loss was scheduling, not model speed: `research/factory/A9-throughput-timeline.md`.)

### The prototype ladder

The order of entry into Stage 3 is a ladder of small, observable increments, never a jump to the MVP. Each rung has a functional expectation (T1, exact numbers), a visual expectation (T2), a QA target with planted bugs, and a gate that re-runs every earlier rung. A rung opens when the previous rung's gate is green on a clean build and red on its planted build. Track L's rounds attach to rungs.

| Rung | Built | Gate |
|---|---|---|
| P0 Sim runs | C sim headless: regions, drift, factions; determinism trace | 5,000 ticks under budget; same seed same checksum; invariants hold; T1 detectors trip on planted builds |
| P1 Galaxy view | Thin C pipe server over the sim library; the galaxy view rewritten as small fresh GDScript files (points, edges, owner colour, pan, zoom, click to inspect; theme, palette and shaders reused; main menu kept); GDScript function-level splice lands first | State read through the hook equals the sim's snapshot; a region's colour matches its owner; planted client bugs caught; input liveness |
| P2 Landscape | Opens with a design phase Westley joins (biome and landscape generation and its sister system: economy, buildings, civilisation cities) and a Godot mockup he approves before any test is authored; then map generation with biomes and palette | Fairness within bounds over a seed sweep (failures logged until the generator is tuned); a generated map reads as terrain |
| P3 Objectives | Mission generator places objectives | Objectives satisfiable; markers visible and named |
| P4 Units | Six units, movement and combat on one layer | RTS bug-catalog T1 rows clean over scripted command streams; units move where sent, face travel, die visibly; planted rubber-band, stuck, dropped order |
| P5 Fog | Fog and sensors | Visibility set matches state; unseen units not drawn |
| P6 Layers | Two-layer prototype (the layer design phase) | Layer changes elevation and vision per rule; ring height and dimming; planted wrong-height |
| P7 Chronicle | Time jump and chronicle, once E-04, E-06, E-07 exist | Entries reference real state; deterministic per seed; readable pace |
| P8 Eras as data | A second era pack differing only in art, names and prose | Mechanics tests identical across packs; content validators as acceptance; content positive control |
| P9 Multiplayer | Two clients, lockstep | Checksums agree per tick; desync detector silent; two-window QA session |

Strategic-sim epics not needed for a rung keep building in the chain's background slots; rung order only fixes what must be green before the next rung's QA opens.

### Content and multiplayer are not special cases

A content card's acceptance commands are validators and a fenced content diff (byte-identical mechanical config across packs for the MVP, swappable to within-band later); content is authored by the offline library builder (E-21) and only verified by Agora, sized by pack entry count. A content class added after packs have shipped is optional with a placeholder until each pack is revised, so a new feature never invalidates the shipped packs. Pack visual claims (silhouettes, one readability screenshot per zoom band and kit) are judged at campaign level, never per candidate. Determinism is a T1 detector class from rung P0: the desync detector runs two sim instances in one process with a bit-flip positive control; the game later gains a peer-command injection hook for transport QA.

### Self-improvement, bounded

The refiner generalises the existing propose-only move: it reads the run archive (per candidate: model, reason, tests, wall, tokens, prompt hash, hint used, regression result) and writes a proposal file per epic under `agora/proposals/`, never live config. Three tiers: prompt and hint wording (propose, Westley applies); strategy knobs such as ladder attempts and when to call Gemini (held-out A/B, and the planted controls must still trip); thresholds, fences and the definition of done (never). Metrics: candidates to green, wall per DONE card, escalator calls per card, QA false-positive rate, regression escapes, cost per story; each checked against the fixed control set and capped, not merely measured.

### Failure modes the factory guards against

From the incidents of 2026-09-17 to 19: a reply outgrowing the context (function-level splice, measured prompts); dropped includes (skeletons carry them); dead input read as product bugs (`harness-error`); stale run markers (archived by the recut tool); tests spanning another card's stub by symbol or by tick order (lint closures); cards already satisfied (fail-first); a function whose card tests one field of it (control coverage, mutation); controls unsatisfiable by construction or vacuous in their numbers, two-agent confounds (fixture-defect detectors, plateau early-stop); merged code violating a documented contract (mutation, whole-suite regression); parent patches implementing another card's scope (fence); hints that name an upstream defect and route around it (`upstream_defect` aborts); briefs with wrong numbers (verbatim from the spec, read-only check); tests edited without their epic (drift check); an open flag taxing card after card (flag-aware queueing holds a card whose tests touch an open `Q-`); no QA ever pointed at the game (per-epic campaign trigger). The full table with detectors and owners is `research/factory/B-design-draft.md` §B.7.

### Proving the factory before trusting it

Principle 13 applies to the factory itself. Each load-bearing claim above has a toy-scale experiment (`proving_ground/PX-*.md`, results on the scorecard) with a hypothesis, a fixture, a pass number, and positive and negative controls: harness-error on dead input; verbs and pause/step; spec to mission; tick-stage closure and the plateau stop replayed over the real Round 5 runs; T1 detectors on the C trace; the desync detector; under-test detection by shadow fixture and mutation; whole-suite regression replayed over a known-bad merge; the refiner scored offline against a held-out card; a content card with a broken pack; a second project onboarded through the profile alone; the vision judge measured on planted rendering defects; fixture-defect detectors and the parent-patch fence replayed over their incidents. A claim that fails its experiment changes the design, not the experiment. The design was also walked through six scenarios (`research/factory/B8-scenario-traces.md`: an undefined feature at month six, era pack twelve, a desync report, a finding that is really a story defect, a web app as second project, a starved chain); each ended green or produced one of the changes now in this section.

---

## Requirement hierarchy (agile)

| Level | ID | What it is | Lives in |
|---|---|---|---|
| Epic | `E-##` | A feature area (e.g. Layer System, Fog and Vision, Faction Agents). One file. | `docs/bible/epics/E-##-<slug>.md` |
| Story | `S-###` | One user-facing behavior in the user's words: "As a commander, I want …, so that …". One row in the catalog, one section in its epic. | `docs/bible/stories.md` (catalog) + epic file |
| Rule | `R-###-##` | One acceptance criterion for a story, Given/When/Then. Maps 1:1 to at least one test. | epic file |
| Ambiguity flag | `Q-###-##` | An open question on a story, `[NEEDS WESTLEY]`, with candidate answers. Blocks Ready. | `docs/northstar/ambiguity_register.md` |
| Reference | — | Screenshot, clip, or note about a similar game that shows how a story should look or behave. | `docs/bible/references/E-##/` |

**Change protocol.** When a requirement changes (Westley's call, or a build revealing the story was wrong): rewrite the story and rules in the epic file → update the catalog row status → Claude revises the tests → the Agora task is respec'd (or parked and re-queued) → `derive_agora_rules.py` regenerates the rules file. One pass, one PR. The bible never lags the tests, and the tests never lag the bible.

---

## Stage 1 — Bible audit (what stays, what goes)

**Goal.** Produce a complete ledger of every idea in the bible (rule, mechanic, user story, aspiration, implementation claim) with Westley's verdict on each, plus a fresh one-page vision statement that resolves the end-of-project crisis. No bible edits happen in this stage.

**Where.** A separate Claude Sonnet 5 chat. This chat writes the briefing that chat starts from.

**Inputs.**
- `docs/bible/game_bible.md` + the 9 spokes (4,143 lines).
- `docs/priority_queue.md` "Research-only" section (16 parked directions) and Soon/Backlog.
- `docs/bible/bible_design_vision.md` split (BINDING principles vs ASPIRATIONAL targets).
- A code-reality summary (embedded in the brief): which bible systems are built, partial, or absent, taken from the survey above.
- Known stale claims list (above) so the auditor flags them without re-discovering.

**Method.**
1. Vision interview first (before any item walk): 8–12 questions on what the game is. Commander-not-king still true? Pause-and-command tactical still true? Generational chapters still true? Single era or multi-era? Sci-fi Settled Reach or something else? Price band? What did the crisis change? Output: `vision_v2.md` draft, confirmed by Westley. Every later verdict is checked against it.
2. Item walk, one whole spoke file per batch. Claude verdicts every row itself against vision_v2, code reality, the pivot commit, prior verdicts, and the blanket policies; prints only flagged rows (conflict, post-pivot framing, implementation detail, built-status mismatch, two readings, any number or cadence, era-specific mechanics at launch, or confidence below near-certain) with a recommended verdict; lists silent KEEPs by id on one line; never asks a question inside a batch (questions go to the ambiguity register as `Q-` rows). Westley replies "approve" or overrides by row id. (Protocol v2, 2026-09-10; the first 19 batches ran row by row and 83% were straight KEEP.)
3. Cross-check pass: for every keep, confirm it does not contradict vision_v2 or another keep. Contradictions surface as a short list for Westley to resolve.
4. Algorithm pass: the retained equations (from `drift.py`, `world.py`, `faction.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `admin_revolt.py`, `region.py` composites) presented as named formulas with constants. Verdict per formula: keep verbatim / keep with retune / drop. This feeds R2 and Stage 3.

**Output.** `docs/legacy/agora_era/stage1_audit.md`:
- One row per item: `id` (A-001…), source `file:line`, type (rule / mechanic / story / aspiration / impl-claim), built-status (built / partial / absent / unknown), verdict, note.
- `docs/northstar/vision_v2.md` (one page).
- A "contradictions resolved" list and a "stale claims to delete" list.

**Done when.** Every heading in every bible file has at least one ledger row; no row is `unsure`; vision_v2 confirmed; algorithm pass complete. Estimated 500–700 rows; under protocol v2 the remaining spokes are one batch each.

**Brief for the Sonnet chat.** This chat writes `docs/legacy/agora_era/stage1_brief.md`: mission, rules (no bible edits, no design decisions, ledger only, caveman off for the ledger table), the input list, the code-reality summary, the batch protocol, the ledger schema, and the vision-interview question list. Westley pastes the brief as the first message.

---

## Stage 2 — Bible reformat for autonomous development

**Goal.** Rewrite `docs/bible/**` so that (a) a human reads vision and principles, (b) a machine reads a stable, ID-addressed story catalog and per-epic rules, (c) the "what" of each story is defined hard enough that Stages 3 and 5 can write tests from it without guessing, (d) Agora's per-epic rules files derive from the bible by script rather than by hand.

**Inputs.** Stage 1 ledger, vision_v2, R2 algorithm keep list, the-best-salesmen §16/§12 precedent, Agora `projects/salesmen/rules/*.md` format, Westley's references (below).

**Target structure.**
- `docs/bible/game_bible.md` (hub): vision_v2, sacred principles, game shape, tone, monetization. Human-facing, short.
- `docs/bible/stories.md`: the story catalog. One row per story: `S-###`, epic, user's words, status (Spec'd / Ready / Building / Built / Revised), depth pointer. Every story enters here first. No design in this file.
- `docs/bible/epics/E-##-<slug>.md`: one file per epic. Fixed sections: Purpose and why it matters to the game; Stories (each with its rules `R-###-##` as Given/When/Then); Inputs (every player action, every sim input, with ranges); Outputs (every state change, render expectation, chronicle effect); Invariants; Scale requirements; Look and behavior references (pointers into `references/E-##/`); Ways this could be wrong; Open ambiguity flags (`Q-###-##`, or "none"); Depends on. Written so a rules file for Agora can be cut from it mechanically.
- `docs/bible/references/E-##/`: screenshots, short clips, and a `notes.md` per epic describing which similar games it should feel like and in what specific way (camera angle, unit scale, HUD density, how layers read on screen, how fog looks). These are the visual ground truth for T2 tests.
- `docs/bible/algorithms.md`: retained equations as named formulas with constants and their config names. This is the "what stays" contract for the C rewrite.
- `docs/northstar/ambiguity_register.md`: every `[NEEDS WESTLEY]` flag across all epics, with the question, candidate answers, the stories it blocks, and Westley's answer once given. Empty per epic is a Ready precondition.
- `docs/bible_history/` untouched; current spokes archived there as `bible_2_00_*` before deletion.
- `scripts/derive_agora_rules.py` (in ouroboros): generates `~/Projects/agora/projects/ouroboros/rules/E-##.md` from epic files, only for epics with zero open flags. Generated files carry a "do not edit, derived from" header. Resolves Agora D17 (bible fenced, rules distilled) without hand-copying.

**Reference-gathering segment.** For every epic with a visible surface (tactical view, layers, fog, HUD, world view, chronicle scroll, menus, unit look and motion), Claude asks Westley for: 2–5 screenshots or clips from games that show what he wants, one sentence each on *what specifically* in that image is the target, and one sentence on what in that image he does *not* want. Claude writes `references/E-##/notes.md` from the answers and cites it from the epic's rules. Stories with a visible surface and no reference are not Ready.

**Definition-completeness gate (the "what" check).** Before an epic leaves Stage 2, Claude runs it against a fixed checklist and records the result at the top of the epic file:
- Every story has at least one rule; every rule is Given/When/Then with concrete values, not adjectives.
- Every input a player or the sim can produce is listed with its range and its rejection behavior.
- Every output is listed with where it is observable (state field, screen region, chronicle, save).
- Anything the epic implies but does not state is turned into a flag, not left implicit.
- Every visible-surface story has a reference.
- The epic names what "obviously working" looks like in a 60-second play session, in plain words, so T2 QA has a target.

**Worked example: Layer System.** Stage 2 runs the Layer System epic through the gate first, before any other epic, as the proof that the gate works. Expected flags include: what elevation each layer maps to on screen; whether a unit visibly moves when its layer changes and over how long; what a unit on layer 2 can see on layers 1 and 3 and at what range; whether layers change pathing, damage, or cover; what the player sees in the HUD about a unit's layer; what an enemy on another layer looks like under fog. Every one of these becomes a `Q-###-##` until Westley answers, and the answers become rules. If the gate produces fewer than a handful of flags on this epic, the gate is too weak and gets tightened before proceeding.

**Also in this stage.** Rewrite CLAUDE.md for the new development style (Agora is the implementer, Claude is designer/tester; agile method and change protocol stated; protected-file list corrected; workflow section replaced by pointer to `docs/northstar/`). Rewrite `docs/workflow.md`, delete or rewrite `docs/design_lane.md` In Flux mandate, fix orphaned `bible_monetization.md` references, retire `docs/priority_queue.md` in favor of the Stage 4 product backlog (or reduce it to a pointer).

**Done when.** Every keep/rewrite row from Stage 1 maps to exactly one story, rule, or hub paragraph; every kill row's text is gone; every epic has run the completeness gate; the Layer System epic has passed it with all flags answered; `derive_agora_rules.py` runs clean for every flag-free epic; no doc in `docs/` references a deleted file (grep verified); CLAUDE.md describes the new style. Epics may reach Done individually; sim-core epics reach Done first so building can start.

---

## Stage 3 — End-to-end behavior definition (per epic, repeating; Claude judges, the spec factory drafts the transcription)

**Goal.** For each epic the roadmap pulls, define exhaustively what the user can do, what the system must do in response, every rule, every edge, and the scale each must survive. This is the document the local models read to know what "correct" means, and the document Stage 5 turns into tests. Runs per epic, in roadmap order, in parallel with Agora building earlier epics. Claude still authors the epic, runs the completeness gate, and raises flags — the judgment steps `docs/northstar/spec_factory.md` never delegates. Folding Westley's answers into rule text and drafting the e2e file are transcription-class once the epic carries concrete numbers; `agy` (Antigravity CLI, `docs/northstar/research/gemini_compute.md`) drafts those, Claude reviews every diff.

**Inputs.** The epic's Stage 2 file (gate passed, flags answered), its references, R1 (what QA can observe), R2 (C architecture, algorithm contract, determinism rules), R4 (RTS bug catalog mapped to epics).

**Definition of Ready (exit of Stage 3, entry to Stage 5).** An epic's stories are Ready when: the completeness gate passed; the epic's end-state is written and complete (technical end-state with concrete values, and a visual end-state authored or an explicit "none direct" naming the rendering epic); the e2e file has no empty section; every input and output is mapped; the ambiguity register has zero open flags for the epic; scale gates have numbers Westley confirmed; every visible-surface story has a reference; R4 watch-fors are assigned. Only Ready stories may have tests written and only tested stories may be queued to Agora. (`agile.md` carries the same list.)

**Per-epic content** (`docs/northstar/e2e/E-##.md`):
- Actor and surface: player action (click, drag, hotkey, command), sim event, or time-jump batch.
- Input space: every command with parameters and ranges; invalid inputs and expected rejection.
- Output space: state delta fields, render expectations, chronicle entries, saves.
- Rules as Given/When/Then, one per `R-###-##`.
- Edge cases: empty, max, concurrent, mid-pause, mid-save, post-rewind.
- Scale gates: hard numbers (e.g. tick time at N units on M regions, path query count per second, memory). Numbers set here, never loosened by Agora.
- QA watch-fors: which R4 bug signatures apply and which tier (T1 trace rule or T2 visual) detects each.
- Failure evidence: what to capture when it fails (trace window, screenshot, seed, command log).

**Also in this stage (once, with the first sim-core epics).** Finalize the C algorithm keep/drop list into `docs/bible/algorithms.md` (Stage 2 draft, R2 evidence, Westley confirms). Document the T1 trace format and the T2 command/observation API the game must expose (debug port: spawn, teleport, read unit state, set seed, set time scale, screenshot trigger).

**Ambiguity handling.** Any question Claude cannot answer from the epic file, the references, or vision_v2 becomes a `Q-###-##` flag in the register, with the concrete question and 2–3 candidate answers. Claude never picks silently. Flags are batched and presented to Westley per epic; the epic stays in Stage 3 until the batch is answered.

**Done when (per epic).** The epic meets the Definition of Ready above. Done for the project means every epic in the backlog has passed through, which happens over the life of the build, not before it starts.

---

## Stage 4 — Roadmap, product backlog, and sprints

**Goal.** Order the epics into a dependency ladder and the stories into sprints that start tiny and build upward, so Agora never bites off more than one acceptance-tested story at a time. Keep a living product backlog so requirements can change without breaking the build. Define the escalation ladder that runs the loop.

**Inputs.** Stage 2 epic files (dependency sections), Stage 3 e2e files as they become Ready, R1–R4, Agora task/campaign formats and budgets.

**Product backlog** (`docs/legacy/agora_era/backlog.md`): every story, ordered by priority, with status (Spec'd / Ready / Tested / Queued / Building / Built / Revised). Sprints pull only from Tested. Claude's planning work each cycle is to move the next stories from Spec'd to Tested faster than Agora drains Tested; if Tested runs dry, Agora idles (Agora D13: no unattributed work) and the flag notes it.

**Roadmap shape** (`docs/northstar/roadmap.md` + `docs/northstar/sprints/S##.md`):
- **Sprint 0 — Toolchain.** C build (gcc + make; cmake added if R2 says so), test harness (pytest via ctypes against the C lib, or ctest; R2 decides), Godot 4.6 on forge, Xorg virtual screen on nvidia, xdotool + ffmpeg, Agora `projects/ouroboros/qa.toml`, Agora desktop-QA tool (new `tool:` type beyond Playwright), fences (bible, tests, roadmap), escalation flag writer. Exit: one C unit test green from an Agora task, one T2 screenshot round-trip from an Agora QA session.
- **Strategic sim ladder.** Region fields and composites → drift equations → world graph generation → events and chains → faction agents → intent resolution → border friction → diplomacy → technology → lifecycle → time jump → coherence ledger and character selector → chronicle. Each rung = one or more sprints; each sprint = a handful of Tested stories in dependency order.
- **Tactical sim ladder.** Unit store (SoA) → movement and pathing → collision → fog and vision → damage and RPS → abilities → facing → objectives → reinforcement structures → enemy macro behavior → map generation → outcome resolver.
- **Integration ladder.** Pipe contract in C (snapshot, delta, commands) → Godot binding unchanged → save/load → GDExtension binding → pipe removed.
- **Client ladder.** Only after sim ladders are green: HUD, selection, camera, world view, chronicle scroll, onboarding, debrief. Each with T2 visual QA.
- Per sprint file: stories in scope, dependencies, tests required (pointer to Stage 5), scale gates, QA tier, Agora task spec stubs (`queue/NNN-*.md` bodies), exit criteria, budget (`max_iterations`, `max_wall_minutes`, DeepSeek cap).
- **Sizing rule (The 30B Sizing Contract).** One task = one micro-behavior:
  1. **Public API / Symbol Cap**: A single card must define or implement no more than 3 to 5 public C functions/symbols.
  2. **Algorithm Family Isolation**: Exactly ONE mathematical formula or discrete algorithm per card. Never mix state mutations, RNG draws, and multi-entity matrix updates in one card.
  3. **Implementation Line Budget**: `expected_lines` must not exceed 40–80 lines (diluted down from 250). If a story requires more, split the story in the epic file into sub-stories (e.g. S-032a, S-032b).
  4. **Acceptance Test Scope**: 5 to 15 focused test assertions directly covering the card's single behavior. Acceptance suites must not span unrelated modules.
- **Parallel rule.** A sprint may open while later epics are still in Stage 2 or 3, provided every story in the sprint is Tested and its epic's dependencies are Built. The first sprints (toolchain, region fields, drift, world graph) are chosen precisely because they depend on almost nothing and can be Ready early.
- **Prototype rule.** Early sprints may target throwaway prototypes (e.g. a headless C world that only drifts, a Godot scene that only draws unit dots on layers) when that is the fastest way to validate a story's rules against reality. Prototype stories are marked as such in the backlog and are replaced, not extended, when the real story is Ready.

**Escalation ladder** (`docs/legacy/research/escalation.md`, from R3; the Factory section above holds the gates):
1. **Runs 1-2, fast local ladder**: the local model alone (qwen3-coder:30b, three attempts). A plateau (three distinct candidates, one identical failing set) forces a diagnosis call from the escalator; only a named cause ends the run.
2. **Runs 3-9, guided**: the escalator (Gemini via `agy`) reads the failed candidates and writes a terse hint into the next brief; a hint that names an upstream defect aborts the run and becomes a fix task for the escalator under the parent-patch fence; a contradiction in the tests aborts as unsatisfiable and routes the finding (`story-defect` to Westley, `test-defect` to the escalator).
3. **Run 10, cap**: the card parks, `escalate.py` writes `ESCALATION.md` with evidence, Westley is notified.
4. Westley decides: respec, split, revert, or "start over" (discard the `agora/` branch, restore the card with a new spec). Hand-implementing a card is this rung, recorded in the ledger.
5. Opt-in: a pinned chat on `/loop` polling the flag at a long interval. Documented, off by default.

**The backlog is the chain.** `RELEASE_CHAIN` (moving from `next.py` into the project profile) is the living backlog: cards in dependency order, one released per tick when its predecessor is DONE; story gates after a story's last card, epic gates after an epic's, rung gates per the prototype ladder; a QA campaign activates when an epic's gate is DONE. Sprint files and `backlog.md` describe intent; the chain is what runs.

**Done when (initial).** Every epic sits on the ladder; the product backlog exists with every story from Stage 2; the first three sprints are fully specified with exit criteria and task stubs; Sprint 0 has a checklist Westley can run; escalation doc complete; Westley confirms the ladder and the first sprints. After that the roadmap is a living document, re-planned each time a sprint closes or a requirement changes.

---

## Stage 5 — TDD test authoring (spec factory drafts, Claude reviews and owns the suite, Agora obeys)

**Goal.** Before a story is queued, its full failing test set exists from the Stage 3 e2e file. Tests are the task's `acceptance:` commands. Agora iterates until green. Repeats per story for the life of the project, and re-runs under the change protocol whenever a story is revised. `docs/northstar/spec_factory.md`'s scripts generate the test and control skeletons per rule and per QA watch-for; `agy` fills the arrange/act/assert bodies from the rules file; Claude reviews the filled tests and is the only one who decides what gets tested (the per-file Sonnet audit was trialled and closed on 2026-09-17; it could not see the defect classes that mattered). Before Agora sees a card, scripts prove what a review cannot: `red_check.py` (every new test fails on the stub), `card_lint.py` (symbol and tick-stage closure, sizing, control coverage), the fixture-defect detectors (a control unsatisfiable by tick order, a control whose numbers never reach its branch, a two-agent confound), the drift check between epic, expectation spec and tests, and flag-aware queueing (a card whose tests touch an open `Q-` is held). `green_check.py` exists for diagnosis after a card fails, never as a routine pre-queue step: Claude does not write a card's implementation to prove it passable.

**Tests as the anti-layer-system guard.** A story like "units on different layers have different vision" gets tests that make the behavior *observable*: a unit on layer 2 sees a target on layer 1 at range X and not at range Y; the unit's world position changes by the layer's elevation within N ticks of a layer command; a T2 screenshot at a fixed camera shows the unit at the expected screen height. If a test like that cannot be written, the story is not Ready and goes back to Stage 3 with a flag.

**Test layers.**
- **Unit (C).** Per function and per equation; determinism (same seed → identical trace); boundary and clamp behavior.
- **Invariant / trajectory.** Port the intent of `simulation/invariants.py` (~70 invariants) to the C sim: run N ticks, assert on the trace. Same modification rules as CLAUDE.md today: narrow scope allowed, loosen thresholds forbidden.
- **Combined gating test (behavior + speed + scale in one).** Each story's gating test is the integration run that exercises the bulk loop at the confirmed scale and asserts, in a single test, that the result is behaviorally correct (its rules and invariants hold), within the speed budget, and at the required scale. A fast-but-wrong, a correct-but-slow, and a correct-but-undersized run all fail the same test — you cannot pass by being any one of them. Exact-value unit rules with no meaningful speed or scale axis (a pure-function algebra identity on one entity) stay as separate single-leg unit tests above; do not wrap them in a scaled run. The scale thresholds and speed budgets come from Stage 3 and are never loosened by Agora.
- **T1 QA scenarios.** Scripted player sessions against the C sim (command stream + trace assertions): rubber-band detector, stuck detector, backwards-walk detector, dropped-order detector, and the rest of R4. Each detector ships with a positive control (a seeded scenario that must trigger it).
- **T2 QA scenarios.** Agora director-mode missions for the Godot client: ordered directives + expected observations (screenshot diff regions, HUD text, unit counts via debug port).
- **Contract tests.** Snapshot/delta/command JSON shape (Phase 1 pipe) and later GDExtension API.

**Rules.** Tests live in fenced paths Agora cannot edit. Every test names the `S-###`/`R-###-##` it proves. A test that cannot fail is a defect (positive control required). Test code is normal prose, no caveman.

**Done when (per story).** Every rule has at least one test; the story's gating test proves behavior, speed, and scale together (a fast-but-wrong or correct-but-slow run fails it); every applicable R4 detector has a positive control; the pre-queue checks pass (red, lint closures, control coverage, fixture-defect detectors, drift); the story's expectation spec is generated and its QA mission derived from it, with a planted-bug variant where the mission must fail; the set is red against the current implementation and the Agora task spec references the exact commands. The story moves to Tested in the backlog.

---

## Track L — Lean MVP loop (parallel with Stages 3–5, owns their order)

**Goal.** Get a playable cut into testers' hands as early as the C/Agora path allows, in rounds, and let measured player response decide what is built next. The point is to stop spending build time on ideas players do not value, and to learn what player satisfaction actually is for this game rather than what the bible assumes it is.

**Decisions (2026-09-14).** Substrate is the C sim and the new Godot client only; the legacy Python slice is not used for playtests. Client and packaging are Agora work like everything else, gated on a proving-ground probe that shows Agora can build GDScript against fenced Godot tests. Testers come in three rounds: friends, then a Discord cohort, then Steam Playtest. The first round's bet is recorded as an open flag (`Q-MVP-01`) with a recommendation, not decided here.

**What Track L changes.** It maps its rounds onto the prototype ladder (Factory section, "The prototype ladder"), which fixes the order of entry into Stage 3 rung by rung; within a rung it picks which stories are pulled first. It does not change what Ready, Tested, or Built mean. Stories cut from a round are omitted, never thinned: a rule that is in a round keeps its full Given/When/Then and its full test. Where an epic is needed for a round but not built, a stand-in is a prototype story under Stage 4's prototype rule: marked as such in the backlog, replaced not extended when the real story is Ready.

**Rounds.** Round 0 is planning and instrumentation (hypotheses, metrics, feedback instruments, a two-week Agora velocity baseline). Round 1 ships to friends. Round 2 ships to a Discord cohort. Round 3 ships to Steam Playtest. Each round has hypotheses with kill criteria, a metric set, feedback instruments, a build gate, and a gap review. Rounds open on evidence, never on dates: Agora's throughput on this project is unmeasured (zero cards done at the time of writing), so the plan states sequence and gates only.

**Gates that still apply.** Definition of Ready, fenced tests, Agora-only builds, no runtime model calls, determinism, scale gates set by Claude with Westley. Probe H (GDScript build to fenced Godot tests) and probe I (headless export card) must pass before any client or packaging card opens.

**The lean step: gap review.** After each round, a table with one row per hypothesis: what the bible assumed players value, what testers said and did, the gap, and the action. Every gap row becomes exactly one of: a change-protocol PR (story rewritten, tests revised, card respec'd), a new `Q-` flag, or a kill. Killed ideas are recorded in `docs/legacy/mvp/experiments.md` so they do not return silently. Confirmed ideas are recorded too, so the bible's claims accumulate evidence.

**What Track L may not do.** Weaken a rule or a test to fit a round; loosen a scale gate; build on the legacy slice; call a model at runtime; put a human in the build loop; claim Ready for a story that is outside a round's scope.

**Files.** `docs/legacy/mvp/README.md` (method, rounds, metrics, instruments, gap-review template); `docs/legacy/mvp/distinctiveness.md` (ranked list of what the game offers, with a falsifiable hypothesis per item); `docs/legacy/mvp/feature_mvps.md` (per-epic cut by round); `docs/legacy/mvp/build_path.md` (how Agora builds the cut compared with the current backlog ladder, new probes, throughput gate); `docs/legacy/mvp/experiments.md` (living hypothesis and result log).

---

## Track R — Research (parallel with Stages 1–2, feeds Stage 3)

Each produces `docs/northstar/research/<name>.md` and, where marked, a spike proof.

**R1 — QA driving on forge.** How the local model "is the user."
- Install: Godot 4.6 Linux binary, nvidia Xorg virtual screen config, xdotool, ffmpeg, optional tesseract. Systemd user service env for DISPLAY.
- Game-side hooks: debug command port (spawn, teleport, read state, set seed, set time scale, trigger screenshot), deterministic replay from command log.
- Observation: screenshot cadence, video capture windows around actions, which local vision model (12 GB VRAM budget: evaluate qwen2.5-vl 7B class) vs DeepSeek vision for T2 judgments; when to prefer T1 trace rules over vision.
- Mapping "what the user watches for" to detectors: for each R4 entry, T1 rule or T2 check, evidence captured.
- Spike proof: Agora session launches Godot on the virtual screen, clicks a menu button via xdotool, saves a screenshot, writes a finding row. Exit criterion for Sprint 0.

**R2 — C rewrite plan.**
- Toolchain: gcc + make baseline; decide cmake vs plain make; test harness choice (pytest + ctypes against `libouroboros.so` recommended, keeps Agora's existing pytest acceptance path) vs ctest.
- Architecture: C library with C ABI; SoA data layout for units; seeded RNG contract (PCG or xoshiro, documented); tick loop mirrors the 7-step sequence; snapshot/delta/command serialization in Phase 1 identical to today's JSON so Godot stays untouched; GDExtension binding sketch for Phase 2.
- Algorithm inventory: every equation from the survey quoted with constants and file:line, proposed keep/drop for Stage 1's algorithm pass.
- Perf targets to propose for Stage 3 scale gates (tick time at 1k / 10k units; world tick at 60 regions × 15 factions × 5k ticks).

**R3 — Escalation and the Claude flag.**
- Spiral detection signals and thresholds (from Agora `runs/metrics.jsonl` and `campaigns/*/assertions`).
- Flag file spec (`ESCALATION.md`): English summary, evidence bundle layout, seed and replay command.
- Notification path with zero unattended Claude: ntfy/email/Tailscale push from forge; PushNotification when a Claude session is open.
- "Start over" protocol and respec template.
- Opt-in loop watcher: how a pinned chat would poll (interval, usage estimate), what it may and may not do without Westley.
- Any Agora changes required (new tool type for desktop QA, fences, project profile). Listed as Agora PRs, not done here.

**R4 — RTS bug catalog.** Visual and behavioral bugs players hate, each with signature, T1/T2 detector, evidence: rubber-banding, stuck units, backwards walking, path oscillation, unit overlap/clumping, formation break, dropped or delayed orders, selection misses, box-select failures, control-group loss, camera jitter, fog pop-in, LOS wrong through cover, projectile miss/desync, HP desync between sim and HUD, HUD stale after delta, pause desync, save/load drift, rewind divergence beyond design, frame hitches at scale.

---

## Stage 0 — Proving ground (Agora must pass before any sprint opens)

**Goal.** Prove, with toy tasks and planted bugs, that Agora can do what the plan assumes: build C against fenced tests, obey scale gates, detect the RTS bug classes from traces, drive the computer and see a Godot window, escalate correctly when stuck, and absorb a requirement change. Each probe is a controlled experiment with a positive control (the planted defect must be caught) and a negative control (a clean build must pass silently). No probe touches Ouroboros code.

**Where.** A separate toy repo, `~/Projects/agora-proving-ground`, registered as an Agora project (`projects/proving-ground/qa.toml`, `rules/`). Separate so Ouroboros stays clean and so the probes mirror exactly how Agora will target the real project. The toy sim is written in C from the start so the probes also shake down the C toolchain and the pytest-via-ctypes harness (R2).

**Sequence.** Track R spikes (R1 display round-trip, R2 harness choice) → Stage 0 probes → scorecard → Sprint 0. Probes A–C need only R2; D needs R1; E–G need Agora config only.

**Probe structure.** Every probe is one file `docs/northstar/proving_ground/P#-<slug>.md` with: what it proves about the plan; fixture (files, seed, planted defect); the Agora task spec verbatim (`goal`, `acceptance:` commands, `constraints`, budget); pass criterion (a number or an observable, never "looks right"); fail-look-fors; negative control; what to change in the plan if it fails. Results land in a scorecard table in `docs/northstar/proving_ground/SCORECARD.md`: probe, date, run id, pass/fail, iterations used, DeepSeek spend, notes.

**The probes.**

| # | Probe | Fixture | Planted condition | Pass criterion | Proves |
|---|---|---|---|---|---|
| A | Build C to fenced tests | Toy `libtoy.so`: seeded PRNG + one drift equation on a 1-region struct; failing pytest via ctypes | None (clean TDD) | Green within `max_iterations`; tests untouched (fence enforced); worktree branch only | Local worker can write C against tests; harness works; fences hold |
| B | Scale gate obedience | Neighbor query over N points with a perf test: must run under T ms at N=10,000 | Task prompt nudges toward an O(n²) solution | Worker iterates past the first green-but-slow attempt and lands an under-threshold solution; perf test never edited | Loop treats a perf threshold as a real failure, not "done" |
| C | T1 detectors, positive and negative controls | Toy mover sim in C: units with position, velocity, facing, path target; command stream; trace writer | Four builds: clean; rubber-band (position snaps back every K ticks); stuck (path active, zero progress); backwards (velocity opposes facing); dropped order (command acknowledged, never applied) | Each detector fires on exactly its planted build and stays silent on clean; fingerprint stable across two seeds | The R4 detectors work and cannot lie |
| D | T2 computer driving | Toy Godot 4.6 scene on the Xorg virtual screen: a button, a label that updates on click, a dot that moves between two layer heights on a hotkey, a debug port reporting state | Two builds: clean; visual bug (dot drawn at layer-1 height while state says layer 2; label stale after click) | Agora session launches the scene, clicks via xdotool, presses the hotkey, screenshots, reads state via debug port, and writes a finding on the buggy build only | Model can be the user: launch, click, key, look, compare state to pixels |
| E | Escalation ladder | Task whose acceptance is unsatisfiable (two tests assert contradictory outputs) | The contradiction | Stall detected at `stall_threshold`; DeepSeek attempt logged with mode and cost; task parked within budget; `ESCALATION.md` written with English summary + failing output + diff + run ids; notification received | The ladder has a top and reaches it without spinning or overspending |
| F | Change protocol mid-run | Probe A repeated; after first green, the story's rule is revised and the test rewritten | Requirement change | Old branch discarded per protocol; new task picks up new acceptance; regenerated rules file reflects the change; green again | Agile change does not break the loop |
| G | Rules-file comprehension (director mode) | Toy rules file for the D scene with a "ways this could be wrong" list of 5 items | None | DeepSeek director mission covers all 5 items with concrete directives; local executor performs each; verdict backed by evidence | Distilled rules files are enough for the models to know what to test |

**Scoring and go/no-go.** Sprint 0 opens only when A–E pass. F and G may pass after Sprint 0 opens but before the first sim sprint. A failed probe is a plan defect: fix the plan (toolchain, detector, Agora config, task-spec template, rules format), re-run the probe, log both runs on the scorecard. No probe result is ever "close enough."

**Open choices for Westley at the time Stage 0 is written.** Whether probe C's toy mover is generalized into the real T1 harness (recommended: yes, it becomes `tests/qa/t1/`) or thrown away; whether probe D's scene doubles as the first Layer System prototype (recommended: yes, it is the cheapest way to see the layer elevation question answered on screen); which notification channel probe E validates (ntfy vs email vs both, from R3).

**Done when.** Seven probe files written and reviewed by Westley; fixture repo builds; scorecard shows A–E pass with run ids; any plan changes triggered by failures are in the north-star docs.

## Executing this plan (what happens on approval)

Branch `wn/docs-northstar-plan` off `main`. Files:

1. `docs/northstar/README.md` — this plan, trimmed to the stage definitions, the requirement hierarchy, the parallel rules, and the layer-system example (persisted north star).
2. `docs/legacy/agora_era/principles.md` — the twelve core principles.
3. `docs/northstar/agile.md` — epic/story/rule/flag definitions, ID scheme, story template, change protocol, Definition of Ready, definition-completeness checklist.
4. `docs/northstar/ambiguity_register.md` — empty register with schema, seeded with the Layer System questions listed above as the first `[NEEDS WESTLEY]` flags.
5. `docs/legacy/agora_era/stage1_brief.md` — the Sonnet 5 chat briefing (mission, rules, inputs, code-reality summary, batch protocol, ledger schema, vision-interview questions, instruction to raise `[NEEDS WESTLEY]` flags rather than guess).
6. `docs/northstar/research/` — four stub files with the R1–R4 questions above, ready for the Research Lane chat.
6b. `docs/northstar/proving_ground/README.md` — the probe structure, the A–G table, scoring rules, and the open choices; individual `P#-*.md` files are written in Stage 0 itself after Westley picks the open choices.
7. `CLAUDE.md` — add a short "North Star" section at the top pointing at `docs/northstar/README.md` and stating the new development style (Agora builds, Claude designs and tests, agile stories, Definition of Ready gates building). No other CLAUDE.md edits yet (Stage 2 owns the rewrite).
8. `docs/priority_queue.md` — set NEXT to "Stage 1 — Bible audit (Sonnet chat)".
9. Memory: save the north-star decisions (C path, QA tiers, escalation vehicle, agile + parallel build, layer-system lesson) as project memories.

PR with the test deliverable: open the brief, paste into a fresh Sonnet 5 chat, confirm the chat asks the vision-interview questions first and presents batch 1 of the hub as a ledger table.

## Verification

- `ls docs/northstar/` shows README, principles, agile, ambiguity_register, stage1_brief, research/{qa_driving,c_rewrite,escalation,rts_bug_catalog}.md, proving_ground/README.md.
- `ambiguity_register.md` lists the Layer System flags with status open.
- `grep -n "North Star" CLAUDE.md` hits the new section; CLAUDE.md still passes a read-through with no contradiction to the section it points at.
- `docs/priority_queue.md` NEXT names Stage 1.
- Westley pastes `stage1_brief.md` into a Sonnet 5 chat; first reply is the vision interview, not a bible edit.

## Out of scope for this plan's execution

No bible edits, no code changes, no Agora repo changes, no toolchain installs. Those belong to Stages 1–5 and Track R. Stale claims found in the survey are listed for Stage 1, not fixed here.
