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
   - Every epic except E-19 has Round 1 work, because Round 1 is every major feature at its smallest (`Q-MVP-01`). Today's ladder finishes the whole strategic sim before touching tactical, and the client last; Round 1 instead takes the thinnest slice of each ladder in order: sim core, then tactical, then client.
   - E-01 enters Round 1 as a two-layer prototype (`S-P10`), which is the first option in the layer design phase rather than something built after it (README decision revised 2026-09-14).
   - E-16 enters Round 1 with three prototypes (camera, HUD, selection) plus the galaxy view, menu, and autosave, because a tester cannot play a trace.
   - E-17 enters Round 1 as a prototype generator (`S-P06`), not the layout library.
   - E-10 carries an auto-resolved mission card (`S-P01`, `Q-MVP-02`) only until the tactical slice is Built inside Round 1.
   - E-22 (playtest delivery and telemetry) is new and sits in Round 1.
   - E-21's pipeline stories move to Round 2; Round 1 reuses the existing chronicle corpus.
4. **Round 1 story set**, in the order it enters Stage 3 (dependency order within the round):
   - E-02 (Ready, tests red): S-012 to S-020.
   - E-03: S-021, S-022, S-025.
   - E-04: S-026, S-027, S-030.
   - E-05: S-032, S-035, S-036, S-037, S-038.
   - E-06: S-043, S-045.
   - E-07: S-049, S-052, S-053.
   - E-08: S-055, S-056, S-058, S-059, S-062, S-063 (minimal), S-064.
   - E-10: S-073, S-075, S-077, S-078, S-079 (minimal), `S-P01`.
   - E-09: S-065, S-066, S-068, S-069 (minimal), S-071.
   - E-21: S-152, S-158.
   - E-11: S-082, S-084, S-085, S-087.
   - E-13: S-096, S-097, S-100, S-102.
   - E-12: S-089, S-092, S-093.
   - E-17: S-113, `S-P06`.
   - E-14: S-123, `S-P07`.
   - E-15: S-126, S-127.
   - E-01: `S-P10`.
   - E-16: S-103, S-105, S-106, S-107, S-110, S-111, `S-P12`.
   - E-18: S-132, S-138 (minimal).
   - E-20: S-145 (by construction).
   - E-22: five Round 1 stories.
   That is 68 real stories, 5 prototype stories, and 19 epics with Stage 3 work to do (E-02 is done, E-19 has none). Every flag on a Round 1 real story is answered as of 2026-09-14 except Q-026-01 (direction given, resolution at Stage 3) and Q-046-01 (deferred to the E-06 spec).

## Stage 3 cost, honestly

E-02's e2e file is 111 lines for 43 rules on the simplest, flag-free, UI-free epic. Round 1 needs e2e work on eighteen more epics plus E-22, and E-16, E-18, E-01, and E-09 have visible surfaces that need references or prototype end-states. This is the cost of "every major feature, minimal": Stage 3 throughput, not Agora throughput, is the likely bottleneck for Round 1, and the two rules below exist to keep each e2e file small. Two rules keep this tractable:

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
- Fence entries for `tests/*.gd`, `docs/legacy/mvp/`, and the feedback form.

## What does not change

Tests are the spec. Fences hold. Determinism from the first sprint. No runtime model calls. Scale gates and speed budgets as set in Stage 3. The layer-system design phase and its sequencing. Agora D16 (no unattended Claude) and D17 (rules files, never the bible). The bible is still the source of truth for what the game is; Track L only decides what gets built next and records what players said about it.
