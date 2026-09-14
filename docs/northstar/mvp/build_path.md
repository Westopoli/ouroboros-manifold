# Build path: how Agora builds the cut, compared with the current plan

Status: proposal, 2026-09-14. Nothing here has reordered `../backlog.md` yet. When Westley approves the Round 1 bet (`Q-MVP-01`), the backlog changes described below land in their own PR.

## Where the build stands today

- C sim: `csrc/region.c` is stubs; `csrc/sim.c` does not exist; `tests/csim/` is red with 52 errors on undefined symbols. Functionally zero.
- Agora on Ouroboros: one card (`200-e02-region-state`), three runs on 2026-09-14, INCOMPLETE, best 0 of 7, $0.013. The failure was the brief (no `rules_file`), fixed the same day. Cards completed for this project: zero.
- Agora capability: the worker writes C against pytest-via-ctypes tests (probes A, B, E, F pass). It has never written GDScript or a `.tscn`. Probe D's click delivery to a real Godot window is unverified on the GPU screen; probe G is unrun for the same reason.
- Client: the new Godot client for the C sim does not exist. The legacy client is not on the path.

Every forecast built on this is a guess. The plan therefore states sequence and gates and requires a measured velocity before any date is discussed.

## What changes in the backlog

1. **A Round column** on every story row in `../backlog.md`: 1, 2, 3, or later, from `feature_mvps.md`. Prototype stories (`S-P##`) get rows too, marked prototype.
2. **Round-major ordering.** Today's ladders are dependency-major: the whole strategic sim, then the whole tactical sim, then integration, then the client last. Under Track L the order is round-major, dependency-minor: every Round 1 story across its epics goes through Stage 3, Stage 5, and Agora before any Round 2 story, in dependency order within the round.
3. **Concrete differences from today's ladder.**
   - E-06 (diplomacy and technology) drops out of the first pass entirely; a fixed-stance stand-in takes its place in Round 1.
   - The client is no longer "only after the sim ladders are green." Round 1 has a minimal client slice (galaxy view, chronicle page, decision screen, main menu, autosave) because a tester cannot play a trace.
   - E-10 enters Round 1 with a stand-in mission instead of waiting for the whole tactical ladder.
   - E-22 (playtest delivery and telemetry) is new and sits in Round 1.
   - E-21's pipeline stories move to Round 2; Round 1 reuses the existing chronicle corpus.
4. **Round 1 story set**, in the order they would enter Stage 3 (dependency order within the round):
   - E-02 (Ready, tests red): S-012 to S-020.
   - E-03: S-021, S-022, S-025.
   - E-04: S-026, S-027, S-030.
   - E-05: S-032, S-035, S-037, S-038, stand-in personality.
   - E-07: S-049, S-052, stand-in `S-P03`.
   - E-06 stand-in `S-P02`.
   - E-08: S-055, S-058, S-059, S-064, stand-ins `S-P04`, `S-P05`.
   - E-10: S-073, S-077, S-078, stand-in `S-P01`.
   - E-09: S-065, S-066, S-068, S-071.
   - E-21: S-152, S-158.
   - E-16: S-106, S-107, S-110, S-111, stand-in `S-P09`.
   - E-22: the five Round 1 stories.
   That is 42 real stories, 9 prototype stories, and 8 epics with Stage 3 work to do (E-02 is done).

## Stage 3 cost, honestly

E-02's e2e file is 111 lines for 43 rules on the simplest, flag-free, UI-free epic. Round 1 needs e2e work on seven more epics plus E-22, and E-16 has visible surfaces that need references. Two rules keep this tractable:

- **Round-scoped e2e files are allowed.** An e2e file may cover only the round's stories, provided it lists the epic's other stories under a heading "Not in this file" so nobody reads Ready onto them. When a later round pulls those stories, the file is rewritten, not appended.
- **Open flags are excluded, not answered in a hurry.** Where a Round 1 story carries an open flag (S-021, S-065), Westley answers it or the story moves to Round 2 and a stand-in takes its place. Track L never guesses to hit a round.

## New proving-ground probes

Written under `../proving_ground/` as `PH-*.md` and `PI-*.md` by a follow-up, in the existing probe format (what it proves, fixture, task spec verbatim, pass criterion, fail look-fors, negative control, what changes if it fails).

**Probe H: GDScript build to fenced Godot tests.**
- Fixture: a toy Godot 4.6 project with one scene, one script, and a fenced headless test (`godot --headless --script tests/test_toy.gd`) that fails until the script is changed. Planted defect in a second build: the test passes only if the worker edits the `.tscn` as well as the `.gd`.
- Pass: green within the card's budget; only `.gd` and `.tscn` files touched; tests untouched; worktree branch only.
- Negative control: a clean toy passes silently with zero edits.
- What it decides: whether `qwen3-coder:30b` can write GDScript at all. If the probe fails after the brief is verified correct, the plan says so before any client card exists, and the options are a different local model, DeepSeek as the primary client worker under its budget, or a documented exception. That decision is Westley's and goes in the README table.
- Needs from Agora: a Godot worktree profile (project path, headless test command), `rules_file` on client cards, and a fence list covering `tests/*.gd`.

**Probe I: headless export card.**
- Fixture: the toy from H plus an `export_presets.cfg` checked into the toy repo.
- Task: run `godot --headless --export-release "Windows Release" ...`, produce a ZIP, launch the result on the Xorg virtual screen, read one value from the debug port, screenshot.
- Pass: ZIP boots to the toy's main scene and the debug port answers. Negative control: a preset with a wrong feature tag fails the boot and the card reports it.
- Needs from Agora: an export tool type, or the build card gaining a post-step; the Xorg screen from probe D.

Neither probe touches Ouroboros code. Both must pass before any E-16 or E-22 card opens. Until they pass, Round 1's sim stories can still be built and T1-tested; only the client waits.

## Throughput gate

No round has a date. The gate to open Round 1 is "every Round 1 story Built, probes H and I passed, one cold-machine smoke test by a friend." To give Westley any sense of when, Track L requires a velocity measurement first:

- Two weeks of Agora nights on Ouroboros cards, recorded in `../proving_ground/BUILD_LEDGER.md`: cards attempted, cards done, wall minutes per done card, DeepSeek spend per done card, INCOMPLETE and SPEC-INVALID ratio, and the reason for each non-done card (brief, model, harness).
- Only after that number exists may a forecast be shown, and it is shown as a range with the measured rate and the story count, never as a date.
- If the measured rate is zero after two weeks, that is a Track R and proving-ground finding, not a Track L one: the answer is to fix the brief or the harness, not to cut the round further.

## Agora changes this implies

Listed as Agora PRs for the Research Lane, not done here:

- Godot worktree profile and headless test command for `projects/ouroboros`.
- `rules_file` required on client cards, as it already is on sim cards.
- Export tool type or build-card post-step for probe I.
- A QA reader for the telemetry file so T2 sessions can assert on what the client recorded, not only on pixels.
- Fence entries for `tests/*.gd`, `docs/northstar/mvp/`, and the feedback form.

## What does not change

Tests are the spec. Fences hold. Determinism from the first sprint. No runtime model calls. Scale gates and speed budgets as set in Stage 3. The layer-system design phase and its sequencing. Agora D16 (no unattended Claude) and D17 (rules files, never the bible). The bible is still the source of truth for what the game is; Track L only decides what gets built next and records what players said about it.
