# B.8 Scenario traces (2026-09-21)

The design's own tests. Each scenario is walked through the Factory section of `PLAN.md` as it stands after the ten prototypes and the landscape design phase, artifact by artifact, naming who acts and which gate fires. A trace ends green, or it produces a design change (applied to `PLAN.md` the same day and listed at the end), or a question for Westley (Round 8 in `harness_defects_2026-09-17/DECISIONS.md`). The short first pass in `B-design-draft.md` §B.8 (2026-09-18) said "passes" six times; this pass looks for where it does not.

## (a) A feature nobody has defined, month six, touching sim, client and content

Scenario: Westley wants weather. A front moves across the tactical map over a mission, raising sensor interference where it sits; the client draws it as a cloud bank; every era pack supplies its own cloud pieces (dust storm, nebula wisp, rain).

1. **Story.** The design lane writes S-### under E-12 or a new epic: rules with numbers (front speed in wu per tick, interference delta, band width), the visual end-state, "ways this could be wrong", a reference row. Under-defined parts become `Q-` rows. Definition of Ready holds the story until the flags close. Green.
2. **Expectation spec.** Generated from the story. A moving front is a state check at a tick (`when: step 120; then: interference at (x, y) ≥ 0.6`) plus a visual claim at the same tick. The schema already has `step` in `when` and visual claims in `then`. Green.
3. **Tests and controls.** Skeletons by script, bodies by agy, Claude owns. The control is an `OM_BUG_FRONT_STATIONARY` injection. Control liveness at queue time flags it PENDING until the feature is built, then must flip. Green.
4. **Sim cards.** The front is a new tick stage: a hook `om_step_weather` that `om_world_step` must call between telegraphs and decisions. Tick-stage closure says: any test that calls `om_world_step` and reads interference pulls the hook into its closure, and the hook is a STUB outside every card's `allowed_files` until some card owns the one-line edit to `om_world_step`. **First gap.** Today that edit is a "parent decision" the executor asks Westley about (decision A5). Under the factory it must be a card: `sim.c::om_world_step`, acceptance: a tick-order test proving the hook runs at its stage and a repeat-seed determinism gate; the chain places it before every card whose closure contains the hook. Ordinary build card, tiny, but it must exist and lint must demand it rather than block silently. Design change 1.
   Also: the feature needs `OM_FEAT_WEATHER`, and someone decides its default. Decision A4 (feature defaults follow the MVP feature set) is still open as a rule; every new feature will re-ask it. Question for Westley, Round 8.
5. **Client card.** `scenes/tactical/weather.gd`, one function, GDScript function-level splice (lands at P1). Acceptance: a headless-Godot debug-port pytest reading `state` and `tree`. The visual claim goes to the QA mission, not the card. Green once P1 has shipped the splice and the runner.
6. **Content.** Every pack gains a `weather` environment class. R-146-01's list is fixed prose today; a new class changes the pack validator, which is project code Claude owns (PX-10: the fence blocks Agora from editing it). Eleven shipped packs would fail validation the moment the class is required. R-146-03 already says a missing optional asset uses the placeholder, so the rule to make explicit is: **a content class added after a pack ships is optional, with a placeholder, until the pack is revised.** Design change 2 (goes to E-20 through the design lane; noted here so the factory's content gate implements it).
7. **QA.** The epic gate turns DONE, the per-epic campaign runs the mission generated from the spec; planted build `inject front_stationary`; the state check fails on the planted build, passes on the clean one; the vision judge sees the cloud bank in one screenshot. Detectors for "a field value at a point changes over ticks" are a project plugin (`agora/projects/ouroboros/detectors/`), not Agora code. Green.
8. **Scheduling.** The cards join the graph by closure; flag-aware queueing holds them while any `Q-` on the story is open. Green.

Verdict: green after design changes 1 and 2, plus the A4 question.

## (b) Era pack number twelve

Scenario: the offline library builder (E-21) emits `assets/eras/<id>/` with a manifest, 18 unit models, structures, environment objects, naming pools, chronicle fragments, and (after the landscape phase) two kits: the terrain mapping and the city mapping over the placer's mesh vocabulary.

1. **No worker.** Nobody implements a pack; the local model never authors art or prose. So a content card is a gate card over a directory: `kind: content`, acceptance = the validators (schema, banned words, era-name grep per R-145-01, kit mesh names against the placer vocabulary, silhouette conformance where a checker exists) plus the fenced content diff (byte-identical mechanical config, Q-146-01 closed), sized by entry count. Gate cards already run acceptance with no model call, so the harness change is a `kind` value and a path input. Design change 3 (a clarification of what already exists).
2. **Contract test.** R-145-04: one engine build loads every shipped pack. Twelve packs, one test, linear. Green.
3. **Rung gate P8.** Mechanics tests identical across packs (run the E-05 suite with pack 12 loaded; the sim never sees the pack, so this is a client-load test in practice). Content positive control: a deliberately broken pack must fail the same card (PX-10). Green.
4. **QA.** The standard missions run with pack 12 loaded; state oracles are unchanged because the sim is unchanged. Visual claims per pack are the silhouette rows and one readability screenshot per zoom band under each kit. With Gemini vision capped per campaign, twelve packs times a handful of screenshots is within a nightly budget; it is not within a per-candidate budget, so pack visual QA is campaign-level, never card-level. Green with that placement stated.
5. **Where it lives.** Packs are project-repo content; the validators are project code; the profile names the validator command. Agora untouched. Green.

Verdict: green; design change 3 states the content card shape.

## (c) A multiplayer desync report

Scenario: two players' clients diverge at tick 4,120 of a lockstep match. Rung P9 exists; the game writes, per client, the seed, the full command stream and a checksum every ten ticks (the determinism contract).

1. **The report arrives with data or it is not a finding.** Without both trace files there is nothing to replay; the client must write them on every match and a report is the two files. Green if P9's expectation spec says so (it must; noted for the P9 rung).
2. **Classification by replay.** The desync detector (PX-05) runs both command streams through two sim instances in one process on Westley's machine. Two outcomes:
   - checksums diverge offline at the same tick: a sim determinism defect (uninitialised memory, a platform transcendental, hash order, a `float` promoted differently). The gcc/clang and -O0/-O2 gates localise the class; sanitizers catch the first two.
   - checksums agree offline: the sim is deterministic and the transport dropped, reordered or duplicated a command. Client and network defect; the peer-command injection hook (P9) reproduces it.
3. **Who fixes it. Second gap.** The chain has no card for it: it is a finding on merged code. The Factory text says the escalator may fix one named upstream function under the parent-patch fence, and the revision artifact is a change-protocol PR by Claude. A desync fix is often one function, but not always, and a hand PR by Claude is the thing the routing rule exists to avoid. The consistent closure is the one Stage 5 already implies: **a confirmed finding on merged code becomes a fenced regression test (here: seed, command stream, expected checksum at tick 4,120) and a repair card whose acceptance is that test, generated by the transcriber like any card; the escalator's direct fix stays allowed only when the test is red and the diagnosis names one function.** Design change 4. The repair card enters the graph with the normal gates (whole-suite regression, determinism, sanitizers), so the fix cannot regress anything silently.
4. **Cross-platform. Third gap.** "Byte-identical on Windows, macOS and Linux" is the contract, and every determinism gate in the factory runs on Linux. The only Windows the factory can reach is the `win11edu` VM on Tuesdays and Thursdays, and the only macOS is Westley's laptop. A Windows determinism gate scheduled into the VM window (build with MSVC or clang-cl, run the seed sweep, compare checksums against the Linux trace) is buildable; macOS is manual until a machine exists. Question for Westley, Round 8: is the VM window the Windows gate, and how often.

Verdict: green after design change 4; one platform question.

## (d) A QA finding that is really a story defect

Scenario: the P6 layer campaign runs a mission "hold the ridge on layer 3". Every state check for R-E01 vision passes, and the mission still fails its objective every time: under the rules as written, a unit on layer 3 cannot see the approach on layer 1 at any range, so the ridge cannot be held. Nothing in the code is wrong; the rule is.

1. **Who can say "the rule is wrong". Fourth gap.** The verifier is Gemini and it never reads the bible (the story's fence: "Agora never reads the bible"). It reads the expectation spec and the mission. So it cannot classify `story-defect`; that needs the bible and Westley. What it can see is a **contradiction**: every check of rule X passes on the clean build, and the mission objective (itself a spec entry) fails on the same build; or two rules' checks cannot both pass in one state. Design change 5: the verifier's classes are `bug`, `test-defect`, `false_positive`, `harness-error` and `contradiction`; a `contradiction` must cite the two spec entries and show both pass their own tests, or it is a `bug`. The design lane turns a `contradiction` into a `Q-` row with candidate answers and it reaches Westley as a design decision, which is exactly what the routing rule says a story defect is.
2. **Guard against misfiling.** A real bug filed as a contradiction would sit on Westley's desk. The evidence rule above (both cited entries green on their own tests) is the guard; a contradiction without it is routed back as a bug. A `test-defect` that looks like a contradiction (a fixture that makes the objective unreachable) is caught first by the fixture-defect detectors (PX-13) when the mission was generated.
3. **After Westley answers.** The story is rewritten (rewrite, never annotate); the spec regenerates; the drift check goes red on every fenced test whose rule text changed, which is the signal to re-author those tests; the cards touching the rule are re-cut; a repair card (design change 4) carries the code change. Flag-aware queueing holds all of it while the `Q-` is open, and the graph keeps other cards running. Green.

Verdict: green after design change 5.

## (e) A second project with no game: a web app

Scenario: the salesmen web app already in `agora/` is onboarded. Stories exist as Given/When/Then; tests are pytest and Playwright; there is no sim, no tick, no era.

1. **Profile.** `agora/projects/salesmen/`: language table (Python and TypeScript), test command, fences, chain order, rules files, detectors (the existing web-app shell set, which is what QA had before the RTS catalog), personas, planted-bug catalog behind an env flag. Data. Green.
2. **Cards and splice.** Function-level splice exists for C and (after P1) GDScript. Python and TypeScript need a splice entry each; the Factory text allows "a language table entry" as a generic Agora change. Mutation gate likewise needs a mutator per language. Both generic. Green, counted by PX-11.
3. **Gates that do not apply. Fifth gap.** Tick-stage closure assumes an orchestrator symbol; determinism gates assume a seed and a checksum; sanitizers assume C. Nothing in the text says how a gate is switched off for a project that has no such thing. If gates are hard-coded, the profile cannot express "no orchestrator" and lint fails or lies. Design change 6: **the gate set is declared in the profile with every gate on by default; `orchestrators` is a list that may be empty; switching a gate off is by name and appears in the run ledger.** A gate that is off for a project is visible, never silently absent.
4. **QA.** The daemon protocol allows "the subset it has": `state` becomes an HTTP endpoint, `screenshot` comes from the browser backend, no `pause` or `step`. The input-liveness precheck applies (PX-03). Vision judge unchanged. Green.
5. **Count.** Agora code changes: two language table entries, two mutators, and the chain-out-of-`next.py` move already listed. All generic. PX-11 measures whether the number of project-specific changes is zero.

Verdict: green after design change 6.

## (f) Agora idle because Tested stories run dry

Scenario: the chain's last card goes DONE at 03:00 on a Saturday; no story is Tested; the GPU sits.

1. **What idle means here.** The idle alarm in the pipelining rule covers a parked head with eligible work behind it. An empty graph is different: no escalator can author a story, and the transcriber can only drain stories that are already Tested. This is a day-side starvation, not a harness fault.
2. **What the machine can still do unattended.** Work that produces findings without new stories: the nightly explorer QA campaign on the latest rung (takes the GPU slot when the chain is empty); a mutation sweep over the whole merged suite, not just the last diff (CPU; names under-tested merged code as test-authoring tasks for Claude); sanitizer and memcheck full runs; determinism soaks over long seed sweeps; planted-build campaigns for every epic gate that has one; refiner scoring over the archive. Design change 7: **an empty-chain work list in the profile, run in priority order when no card is eligible, each producing ledger rows, never cards.**
3. **What Westley needs to see.** A runway number: Tested stories ahead of the chain times the measured build time per card (52 minutes today), reported in the ledger daily and alarmed below a threshold, so starvation is visible days ahead rather than at 03:00. Threshold is Westley's call; 24 hours is the candidate. Question for Westley, Round 8.

Verdict: green after design change 7 and the threshold question.

## Design changes applied to `PLAN.md` (2026-09-21)

1. Orchestrator wiring is a card: when tick-stage closure finds a hook no card owns, lint names the wiring card that must exist (`om_world_step`, one line, tick-order test), and the chain places it first.
2. A content class added after packs ship is optional with a placeholder until each pack is revised (E-20 rule; the content gate implements it).
3. `kind: content` is a gate card over a pack directory: validators plus the fenced content diff, sized by entry count, no model call.
4. Repair cards: a confirmed finding on merged code becomes a fenced regression test and a card generated by the transcriber; the escalator's direct fix stays allowed only when the test is red and the diagnosis names one function.
5. The verifier classifies `bug`, `test-defect`, `false_positive`, `harness-error`, `contradiction`; a contradiction cites two spec entries that each pass their own tests; the design lane turns it into a `Q-` row; `story-defect` is assigned there, never by the verifier.
6. The gate set is profile data, all on by default, `orchestrators` may be empty, a gate switched off is named in the ledger.
7. An empty-chain work list (explorer campaign, whole-suite mutation sweep, sanitizer and memcheck runs, determinism soaks, planted-build campaigns, refiner scoring) and a runway number reported daily.

## Questions for Westley (Round 8)

- A4 as a rule: every new feature adds an `OM_FEAT_*` and asks its default. Candidate rule: the MVP feature set is the list of features on by default, kept as data the header is generated from; a feature outside it is off until its story is Tested.
- Windows determinism: is the Tuesday/Thursday `win11edu` window the Windows gate (MSVC or clang-cl build, seed sweep, checksum diff against the Linux trace), and how often must it pass: per epic gate, or weekly? macOS stays manual until a machine exists.
- Runway alarm threshold: 24 hours of Tested work ahead, or another number.
