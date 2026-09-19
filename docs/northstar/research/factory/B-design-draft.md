# The Factory: design draft (Phase B, working copy)

Status: drafting 2026-09-18; amended 2026-09-19 after the Round 5 audit (see the plan file's "Amendments" section): tick-stage closure replaces symbol closure, mutation and control-coverage gates added, plateau early-stop, fixture-defect class, parent-patch fence, Gemini vision by default, MSan dropped. Sections B.1, B.2, B.4, B.6, B.7, B.8 wait on the memos; B.3 and B.5 drafted from Stage 1 evidence and Westley's constraints.

## B.3 The project boundary

Three homes. A rule for deciding: if it names the game, it is not Agora's.

**Agora (`~/Projects/agora`), generic, project-blind.**
- Dispatch and scheduling: `next.py`, release chain mechanics (a chain file is data per project), gate cards, campaigns, budgets, BUDGET-HALT.
- Build loop: card format and parser, sizing contract constants, ladder, splice by language (C, GDScript, Python; more via a language table), fail-first, baseline, diff-revert, fence, regression gate, `truncated`/`dlopen`/`regression` reasons, escalation to Gemini, run archive.
- QA loop: action vocabulary (product-agnostic verbs), backends (browser, desktop; a CLI backend later), debug-port protocol client, oracle framework (state check, expectation, invariant hook, metamorphic runner, vision judge hook), fingerprinting and ledger, verifier and replay, refiner proposals, harness positive controls (input liveness, scenario-can-fail, planted-build campaigns).
- Tools that read a project only through its profile: `card_lint` (needs a symbol-resolution plugin per language), `card_slice` (per language), rules-file cap handling.

**Project profile (`agora/projects/<slug>/`), data only.**
- `qa.toml`: target, backend, launch, window, display, scenarios, `[director]` features, budgets.
- `rules/E-##.md` derived from the project's bible by the project's own script.
- `missions/` expectation specs (generated from the project's stories; Given/When/Then; state checks name the project's state keys).
- `detectors/` project-specific detector plugins (a Python module registering functions over the state or trace), personas, planted-bug catalog (`bugs.toml`: id, build flag, expected detector).
- `chain.toml` or the chain list: card order, gates, QA campaigns per epic.
- `campaigns/`: director and fix-loop campaign files.

**Project repo (`~/Projects/<project>`), owned by Claude and Westley.**
- Bible and stories, epics, e2e files, register; fenced tests; positive controls; the code Agora edits; the debug hook (dev-only daemon) implementing the protocol; generators (`derive_agora_rules.py`, spec factory) that emit the profile's data.

**Onboarding a second project (the boundary test).** (1) Write a bible-like source of stories with rules. (2) Generate rules files and expectation specs into `projects/<slug>/`. (3) Write fenced tests and positive controls in the project repo. (4) Implement the debug hook for the product (web: none needed beyond the browser backend; desktop app: the daemon; CLI: a CLI backend). (5) Write `qa.toml`, `bugs.toml`, personas. (6) Generate cards, run `card_lint`, chain them. (7) Run the harness positive controls; only then start the chain. No Agora code change. If any step needs one, the boundary is wrong and the change goes into Agora generically (a new backend, a new language table entry, a new oracle class), never a project branch.

**Cut rule (amended).** A card's boundary is the smallest (file, function family) whose acceptance closure, including every hook an orchestrator in the closure runs, stays inside it or inside already-DONE cards earlier in the chain. Lint computes the closure; the chain is ordered by hook stage.

**Smells to watch for.** A verb only one project uses; a detector living in agora/scripts; a card field only one language needs without a language table; a prompt that mentions Godot or C; a chain hard-coded in `next.py` (today's `RELEASE_CHAIN` is a smell to fix: move to the profile).

## B.5 The prototype ladder

Principle: each rung is a small, playable-or-observable increment with its own functional expectation (T1, headless, exact numbers), visual expectation (T2, what a player sees, judged from screenshots and state), and QA target (which detectors, which planted bugs); every rung's gate re-runs all earlier rungs' tests and QA missions. A rung opens when the previous rung's gate is green on a clean build and red on its planted build. Track L's rounds attach to rungs (Round 1 = through P7 at minimal scope) rather than replacing this order.

| Rung | Built | Functional expectation (T1) | Visual expectation (T2) | QA target | Depends on |
|---|---|---|---|---|---|
| P0 Sim runs | C sim headless: regions, drift, factions (E-02, E-05 done or in chain), determinism trace | 5,000 ticks under budget; same seed same checksum; invariants hold; every merged epic's gate green | none (headless) | T1 detectors ported from probe C on the C trace; determinism gates; planted `OM_BUG_*` builds trip controls | E-02, E-05 chain, T1 detector port |
| P1 Galaxy view | Pipe or binding from `libouroboros.so` to Godot; galaxy view renders regions as points, edges as lines, owner as color; pan, zoom, click to inspect (E-16 S-106/S-107 minimal) | State read through the debug hook equals the sim's snapshot for every region | A region's color matches its owner; hover shows its six numbers; zoom keeps labels legible; nothing rubber-bands | First real T2 target: state-vs-pixels missions from E-16's visual end-state; planted client bugs (wrong color map, stale panel); input liveness | integration ladder rung 1 (pipe contract in C), harness daemon, E-16 minimal cards |
| P2 Chronicle | Time jump runs N years; chronicle prints five to ten entries (E-08/E-09 minimal) | Chronicle entries reference real state changes; deterministic per seed | Entries print in order at a readable pace; galaxy animates during the jump | Missions: "watch a jump, read the chronicle, check each entry against state"; planted: entry naming a faction that does not exist | P1, E-08/E-09 cards |
| P3 Landscape | Tactical map generation with biomes/terrain (E-17 minimal generator, E-18 palette) | Fairness evaluator within bounds over 1,000 seeds; generation under budget | A generated map reads as terrain: distinct biomes, legible layers off | Seed sweep detectors; visual judge on sampled seeds; planted: fairness off by design | P2, E-17 cards |
| P4 Objectives | Mission generator places objectives (E-10 minimal) | Objectives satisfiable; outcome resolver maps to region changes | Objective markers visible and named; briefing matches | Missions from E-10 stories; planted: objective off-map | P3, E-10 cards |
| P5 Units | Six units, movement, combat on one layer (E-11, E-13 minimal) | RTS bug catalog T1 rows clean over scripted command streams | Units move where sent, face travel direction, die visibly | Probe C detectors live against the game; personas (attacker, idler, spammer); planted: rubber-band, stuck, dropped order | P4, E-11/E-13 cards, pause/step hook |
| P6 Fog | Fog and sensors (E-12 minimal) | Visibility set matches state | Unseen units not drawn; explored-but-dark shading | Planted: unit drawn while invisible | P5 |
| P7 Layers | Two-layer prototype (E-01 S-P10) | Layer changes elevation and vision per rules | Unit ring height and dimming per layer | Planted: drawn at wrong layer height (probe D's bug, now real) | P6, layer design decision |
| P8 Eras as data | Second era pack differing only in art, names, prose (E-20/E-21) | Mechanics tests identical across packs; pack schema valid | Style holds; names never leak IP | Content validators as acceptance; content positive control | P7, A6 memo |
| P9 Multiplayer | Two clients, lockstep (E-19) | Checksums agree per tick across peers; desync detector silent | Both windows show the same world | Two-window QA session; planted desync | P8, A7 memo |

What this changes now: the chain after E-05 should interleave the integration rung (pipe contract in C) and E-16's minimal galaxy view before E-03/E-04's remaining sim cards, so P1 exists early and T2 QA is proven on the real game months earlier. Sim epics not needed for a rung keep building in the background slots of the chain.

Open flags to raise: the bridge path for P1 (D2); whether P2 precedes P3 (chronicle needs E-08 generational structure, a large epic) or P3 comes first with a stub jump; the layer design phase timing relative to P7.

## B.1 Artifacts and the pipeline

One chain, nine artifacts. Every artifact has a schema, one owner, a fence (who may not edit it), and a positive control (a way to show it can be wrong). Nothing in the schema names a project.

| # | Artifact | Schema (core fields) | Owner | Fence | Positive control |
|---|---|---|---|---|---|
| 1 | Story | id, epic, actor, narrative, rules R-###-## as Given/When/Then, visual end-state, "ways this could be wrong", references | Claude, Westley confirms | Agora never reads the bible directly | Definition of Ready (empty section or open flag blocks it) |
| 2 | Expectation spec (generated cache) | per rule: given (fixture, seed, switches), when (directives), then.state_checks (field, op, value), then.invariant_ids, then.visual_claims (region, judge question), scale_gate | Script from 1; Claude reviews the epic, never the cache | Regenerated only; drift check fails a test whose rule id has no entry or that changed without its epic | A spec with a deliberately wrong number must make its test red |
| 3 | Tests and controls (fenced) | pytest files naming S-###/R-###-##; one control per "way this could be wrong" naming a planted bug id | Script skeletons, agy fills, Claude owns | Agora cannot edit; fence check on every candidate diff | red_check (fails on stub); every control trips on its planted build |
| 4 | Card | id, kind (build, gate, content), target file, symbols, acceptance commands, allowed files, brief, header slice, size fields, chain position | Script from 2 and 3; card_lint gates | Worker sees only brief, slice, skeleton; never tests | card_lint (symbol and tick-stage closure, sizing, control coverage); fail-first gate |
| 5 | Candidate | reply, spliced diff, per-attempt row (model, reason, passed/failed, wall, tokens, hint used) | Local 30B; Gemini hints | Only the named function(s) in one file change | diff-revert (must matter), shadow fixture, diff-scoped mutation |
| 6 | Merge | branch, auto-merge commit, regression gate result | Harness | Whole headless suite must stay green; parent patches obey the same ownership check | Replay of a known-bad merge must be rejected |
| 7 | Gate result | story or epic or rung gate: every acceptance command's outcome, no model | Harness | Red stops the chain; nobody edits a gate's list without the story changing | A planted-bug build must turn a gate red |
| 8 | QA mission and finding | mission (from 2: setup, directives, expected observations), session log, evidence (state reads, trace, screenshots), verdict in {finding, held, inconclusive, harness-error}, fingerprint, replay bundle | Scripted actor first, 30B on escalation; verifier separate | Actor never writes verdicts; harness-error never counts as clean | Planted-build campaign must produce findings; dead-input session must end harness-error |
| 9 | Revision and proposal | change-protocol PR (story, tests, card together); refiner proposal diff (never auto-applied) | Claude for stories; Gemini for proposals; Westley applies | Thresholds, fences, allowed files, controls never move without Westley | A proposal that stops a control tripping is disqualified |

Flow between them is mechanical except at three points: writing a story (1), reviewing spec and tests (2, 3), and applying a proposal (9). Those are Claude and Westley; everything else runs unattended.

## B.2 Roles and models

| Role | Who | May change | May not change |
|---|---|---|---|
| Specifier | Claude, day-side | Bible, stories, e2e, tests and controls, gate lists, chain order, profile data | Nothing at runtime; never in the unattended path |
| Transcriber | Scripts (`derive_agora_rules.py`, spec factory, card generators, lint, slice); later an Agora scheduled step that drains Tested stories | Generated caches, cards, rules files | Sources they read from |
| Implementer | Local 30B (qwen3-coder today; the model is a profile setting) | The named function(s) in the card's one file | Anything else; sees no tests |
| Escalator | Gemini via agy: intervene hints, resets, cross-run advisor, abort on contradiction | The brief the worker sees next; may declare a card unsatisfiable | Code, tests, cards, thresholds |
| Verifier | Separate model call (Gemini via agy) plus deterministic oracles | Verdicts, findings, replay bundles | The actor's actions; never both acts and judges one mission |
| Refiner | Gemini via agy, per epic | Proposal files only | Live prompts, config, fences, thresholds |
| Judge of last resort | Westley | Everything, through flags and applied proposals | — |

Model identity is data (profile and config), so a stronger local model or a different API replaces a line in a file, not a code path.

## B.4 QA architecture

**Game-side hook (dev build only, one autoload daemon speaking the desktop-QA protocol):** `state` (canonical snapshot from the sim, not the UI), `tree` (UI elements with screen coords), `nav`, `seed`, `fixture <name>`, `pause`, `step <n>` (advance exactly n ticks), `screenshot`, `inject <bug-id>` (planted bugs, gated by `QA_DEBUG_PORT` so a player build never has it), `input <event>` (fallback when xdotool cannot). Sentinel-framed replies, stable error codes. A web app or CLI implements the subset it has; unknown commands ack as no-op.

**Actor:** scripted scenarios and personas first (coverage, deterministic replay), the 30B only to translate a directive scripting cannot express; vocabulary `click fill goto reload back submit press drag wait read_state screenshot hotkey box_select camera_pan`, each allowed per project and per mission; the game is paused while the model thinks and stepped by tick between actions; step budgets; state-hash loop detection.

**Oracles, in order of trust:** (1) state checks from the expectation spec over the debug port; (2) T1 trace detectors and invariants over `om_trace_read` (probe C ported; the catalog's T1 rows); (3) metamorphic relations: save/load, two seeds, replay determinism, desync as two sim instances in one process; (4) visual claims judged by Gemini vision via agy (capped), local model only if PF-12's number allows; pixel diff only for golden regressions. A finding needs at least one deterministic oracle; a vision-only claim files as `held`.

**Verifier:** replays the action log from the seed before filing; classifies `harness-error` (input never mutated state, verb unavailable, scene not loaded, port dead) as its own terminal status that can never count toward convergence; fingerprints by bug kind, not instance.

**Harness positive controls:** input-liveness precheck every session; every scenario has a planted-build variant where it must fail; a planted-build campaign that produces zero findings is a harness failure and blocks convergence; `qa_control` daily controls extended to the game backend.

**Scheduling:** per-epic QA campaign activated when the epic's gate card is DONE (chain-end trigger generalised to per-epic triggers); nightly explorer campaign on the latest merged rung; findings that trace to a story go through the change protocol, findings that trace to the harness go to `agora/proposals/`.

**Regression tiers:** per candidate, the whole headless suite (seconds); per rung gate, the earlier rungs' QA missions (minutes); per epic gate, everything including planted-build campaigns (hours, off-peak).

## B.6 Scale and cost model

Measured (A8, 2026-09-18/19, 77 runs): a qwen3-coder candidate costs 68 s of GPU time, a build cycle 8.7 min including tests; a card that is passable and correctly cut goes DONE in 1-3 attempts (203a1, 203e, 204a1 after its recut); a card with an upstream defect burns its whole cap (204b1: 30 cycles, 5.6 h) and produces nothing. Gemini spend on Ouroboros in the window: $0. So the cost that matters is wall time on the one GPU, and it is dominated entirely by defective inputs, not by model retries on good inputs.

Per story, steady state (once the pre-queue checks exist): Claude authors story, reviews spec and tests (the only strong-model tokens; today roughly 15-30k per story including doer-run lint and brief checks); scripts generate spec cache, tests skeletons, controls, cards; the chain runs 2-6 cards per story at 1-3 attempts each (10-60 GPU-minutes); story gate seconds; QA mission per story minutes. Per epic: an epic gate, a QA campaign (hours, off-peak), one refiner pass, one architecture review (Claude, day-side).

What grows with the game: cards (linear in rules), tests (linear), QA missions (linear in stories), content packs (linear in eras and landscapes: manifests, validator runs, matrix rows). What stays flat: Agora code, the oracle framework, validators, the sim engine, the C build, the action vocabulary. Multiplayer adds one detector class and a two-instance run per determinism gate, not a new pipeline.

Budget rule: GPU wall per DONE card is the throughput metric; a card over 10 attempts is a defect of its inputs by definition (A8: zero cases of "the model could not do it" once the target was passable). Gemini calls capped per card and per night as today; the vision judge capped the same way.

## B.7 Failure modes and controls

Every incident since 2026-09-17, by class, with the control that fires before a human would.

| Class | Mode | How it showed | Detector / control | Owner |
|---|---|---|---|---|
| Harness | Whole-file rewrite outgrows context; truncation; format rejects | 75% gpt-oss failures, 0 passes (D6, D9) | Function-level splice; `truncated` reason; prompt size measured per card | Agora |
| Harness | Reply drops helpers/includes; skeleton lacks standard includes | fmax/fmin implicit declaration (D8, R7a) | Hoisting; skeletons carry `math.h` etc.; compile error is its own reason | Agora, project skeleton generator |
| Harness | Dead input, missing verb, scene not loaded read as product bugs | Probes D/G retracted; campaign 004 converged on it | Input-liveness precheck; `harness-error` terminal status excluded from convergence; verb availability check per mission | Agora |
| Harness | Stale terminal markers stall the chain | R7g idle for four cycles | Superseded runs archived by the recut tool, not by hand; `next.py` ignores markers older than the card's file | Agora |
| Cut | Test spans another card's stub (symbol) | 202b2, six 204-207 cards | `card_lint` symbol closure | Project scripts |
| Cut | Test executes hooks of another card's stub (tick order); circular cards | R7b, R7c | Tick-stage closure in lint; chain ordered by hook stage | Project scripts |
| Cut | Card already satisfied by a sibling | 203b2, 203d, 8 SPEC-INVALID | Fail-first gate (exists); SPEC-INVALID terminal | Agora |
| Cut | Function assigned to a card whose tests cover one field of it | R7g root cause | Control-coverage lint; diff-scoped mutation gate | Project scripts, Agora |
| Fixture | Control unsatisfiable by construction (tick order) | R7h, 204b3 | Tick-order reachability check on controls; advisor abort on contradiction (exists, fires inconsistently: A8 gap 1) | Project scripts, Agora |
| Fixture | Control vacuous (numbers never reach the branch) | R7l | Branch-coverage of a control's numbers against a reference stub; control must fail on its planted build | Project scripts |
| Fixture | Two-agent confound (the "defender" acts) | R7e | Two-agent fixture warning; assertion filtered to the entity under test (R7f pattern) | Claude (Stage 5) |
| Fixture | Same-tick re-targeting (open rule) | R7i, R7k, 204b3 | Plateau early-stop plus flag escalation; the rule itself is a `Q-` for Westley (recurs until answered: A8 gap 5) | Westley, Claude |
| Merged code | Violates documented contract while its own test passes | R7d (forced RNG ignored), R7g (five formulas) | Diff-scoped mutation; control coverage; whole-suite regression after DONE | Agora |
| Merged code | Parent patch implements another card's scope | R7j, `c3aa447` | Parent-patch fence (ownership check on hand patches); hand-implementation needs Westley's sign-off and a ledger row | Agora, Westley |
| Escalation | Advisor names the cause but tells the worker to route around it | 204b1 hints five hours before R7j (A8 gap 2) | Hint schema gains `upstream_defect: true` which aborts the run and escalates instead of hinting | Agora |
| Escalation | Ladder burns the full cap on an upstream defect | 204a3 23 candidates same failing set; 204b1 30 cycles | Plateau early-stop: N distinct candidates, identical failing set → stop, escalate (A8: mean plateau 2.6, worst 23) | Agora |
| Regression | Later card breaks an earlier card's test | 203b1 → 203a1 | Whole headless suite after every DONE (fired once in A8's window, correctly); rung and epic gates | Agora |
| Spec | Brief numbers wrong, prose flaps | 203a2 weights, 202b2 expected_lines | Verbatim briefs from the card; read-only brief check; numbers generated from the spec cache | Project scripts, Claude |
| Spec | Tests edited without the epic (drift) | R7f | Drift check: rule id ↔ spec entry; fenced test change requires an epic change in the same commit | Project scripts |
| Spec | Open bible flag keeps taxing new cards | same-tick re-targeting, three cards | Flag-aware queueing: a card whose tests touch an open `Q-` is held (lint reads the register) | Project scripts |
| QA | Zero QA sessions ever targeted the game | A8 | Per-epic campaign trigger; a rung cannot close without its QA mission having run | Agora |
| QA | Vision-only claim files as a bug or is never checked | none yet (design) | Finding needs one deterministic oracle; vision claims judged by Gemini, filed `held` | Agora |
| Self-improvement | Model games its own metric or edits live config | DGM, SICA, Continual Harness (literature) | Propose-only; controls must still trip; thresholds and fences never in scope | Agora, Westley |
| Content | Pack passes schema, plays badly; IP leak; balance drift | none yet (design) | Validators as acceptance; chapter-loop QA; diversity metric; denylist edit distance; content diff fence | Project scripts |
| Determinism | Fast-math, transcendental, hash order, uninit reads, peer order | none yet (design) | Repeat-seed, traced/untraced, gcc/clang, -O0/-O2 gates per C card; UBSan, banned calls; desync detector with bit-flip control | Agora, project |

## B.8 Scenario traces

(a) **A feature nobody defined, month 6, touching sim, client and content.** Claude writes the story with rules, visual end-state, ways-it-could-be-wrong, references; DoR passes; spec cache regenerates; skeleton tests and controls generate; agy fills; Claude reviews; cards generate per file and function family (sim cards C, client cards GDScript, a content card if it adds pack fields); lint runs symbol and tick closures against the current stubs; chain positions follow hook stage; the story gate and its QA mission are generated from the spec. Agora code untouched. Passes, provided the client card kind (GDScript function-level splice) exists by then: today GDScript is whole-file, so that is a design change to schedule before the first client rung, not a gap in the pipeline shape.

(b) **Era pack twelve.** Library builder (Claude-side) emits the manifest; content card with validators and the diff fence as acceptance; chapter-loop QA mission with the pack loaded; chronicle validator; visual claims judged on sampled screenshots; win-rate matrix diffed. No code card. Passes; scale is linear in validator runs only.

(c) **A multiplayer desync report from a tester.** Replay bundle (seed, command stream) attached to the finding; two-instance detector reproduces the divergence tick; T1 test written from the bundle joins the suite as a regression; gcc/clang and -O0/-O2 gates localise the cause class; a card fixes the function the trace names. Passes once P9's injection hook exists; before that the two-instance detector still runs on the sim alone.

(d) **A QA finding that is really a story defect.** Verifier files it with replay; triage compares against the spec; the state check itself is wrong relative to the bible; change protocol rewrites the rule, regenerates spec cache and test, respecs the card; the finding closes as `spec-defect`, a status the ledger needs (today it has none). Design change: add `spec-defect` and `false_positive` to finding status.

(e) **A second project with no game (a web app).** Profile with browser backend, rules from its own story source, spec cache, tests in its repo, no daemon needed, no T1 trace detectors, generic detectors plus its own plugin, planted bugs via its own env flag. Every step is data. The one Agora change it would force today: `RELEASE_CHAIN` lives in `next.py`; moving it to the profile is already listed as a smell to fix. After that, zero.

(f) **Agora idle because Tested runs dry.** Dispatcher logs idle; the refiner and the nightly explorer still run; a flag row tells Westley the pipeline is starved at Stage 5, with the count of Spec'd stories waiting. Passes; the transcription step (Claude-triggered or scheduled) is the lever.

Traces (a) and (e) each produced a design change (GDScript function-level splice before the client rung; chain into the profile); (d) produced a status addition. The rest end green.
