# HANDOFF BRIEF — PX-17 and PX-18: can the escalator fix defects alone?

Self-contained. Handed to an implementor chat 2026-09-21. Program context: `2026-09-21-factory-program.md`.

## Context

Ouroboros Manifold is built by Agora: a local 30B model implements small cards against fenced tests; when it stalls, an **escalator** (Gemini through the `agy` CLI) writes hints. Westley's routing rule for the whole system: *only design decisions reach him; smarter models clear the path so the local model keeps moving.* Concretely, when the escalator finds that already-merged code violates a documented contract, or that a test fixture is defective, the escalator should fix it itself, unattended. Last week every such fix was made by a Claude chat by hand, and over 34 hours the queue sat idle 58% of the time waiting for one. Nothing has yet shown that Gemini can do this job. These two prototypes test that claim on five real, already-diagnosed incidents before any of it is built into Agora. A failed experiment changes the design (a stronger model in that seat, or a narrower task), not the experiment.

Design source: `docs/northstar/PLAN.md` section "The Factory" (Roles table, "Gates the worker cannot move"); decisions C4 and C6 in `docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md` (seventh round); incident rows R7a, R7d, R7f, R7l, R8 in the same file (fifth round and R8).

## Rules for the implementor

- Sub-agents are Sonnet. You and they **never write the fix yourselves**; the point is to measure what Gemini produces. You build the harness around it, run it, and score it.
- Work only in scratch: `git worktree add --detach <scratch>/<case> <commit>` from `~/Projects/ouroboros-manifold`, under `/tmp/px17/` and `/tmp/px18/`. Remove every worktree when done (`git worktree remove --force`, then `git worktree prune`). Never touch the working tree's `csrc/`, `tests/csim/`, `docs/bible/`, or anything in `~/Projects/agora` except reading. Do not stop or start `agora-dispatcher.service`. No Ollama calls (the GPU belongs to the running chain); `agy` is a cloud call and is fine.
- Python: `~/Projects/agora/.venv/bin/python`. Tests: `... -m pytest -q -p no:cacheprovider <paths>` from the worktree root; the C library builds itself through `tests/csim/conftest.py` (`make -s libouroboros.so libouroboros_dbg.so`).
- New files allowed in the ouroboros repo: `scripts/specfactory/escalator_fix_probe.py`, `tests/specfactory/test_escalator_fix_probe.py`, and the two write-ups named under Deliverables. Commit those on `main` and push (solo-dev repo, work on main). Commit trailer: `Co-Authored-By: Claude <model> <noreply@anthropic.com>`.
- Budget: at most 3 Gemini attempts per case per model, 15 cases-attempts total per model. Record every call's wall time.

## The probe tool (build first, tests first)

`scripts/specfactory/escalator_fix_probe.py`, one command per case:

1. **Inputs**: case id, pre-fix commit, the diagnosis text (verbatim from DECISIONS.md, given below), the *fence* (the one file and the named function(s) or test function the patch may touch), the target tests, the model id.
2. **Prompt to Gemini** (through `agy`, same invocation shape Agora uses: see `~/Projects/agora/scripts/agy_client.py::chat`, argv at lines ~137-142: `agy --model <id> --prompt <text> --output-format json --json-schema <schema> --dangerously-skip-permissions --sandbox`, timeout 300 s). The prompt contains: the role (you are the escalator; a diagnosed defect; fix only inside the fence), the diagnosis, the full current text of the fenced function (or test function), the relevant contract text (header comment block or the epic rule, quoted), the failing test output, and the output contract: **return the complete replacement text of the fenced function(s) only**, JSON `{"functions": [{"name": ..., "text": ...}], "rationale": "one sentence"}`. Write your own JSON schema file beside the script. No repository access for Gemini: everything it needs is in the prompt (this mirrors how the local worker is fed and keeps the fence mechanical).
3. **Apply**: splice each returned function over the existing one. For C use `~/Projects/agora/scripts/splice.py` (`extract(text, symbol=..., lines=None, lang="c")` and `replace`) by importing it with `sys.path`; for a Python test function, replace by `ast` node line span. Reject (score `fence-violation`) any reply that names a function outside the fence or contains more than the fenced functions.
4. **Gates, in order**: builds; the case's target tests pass; the whole headless suite is no worse than at the pre-fix commit (compare failing-id sets of `tests/csim` before and after: no new failures); for test fixes, the rule's assertion is still meaningful (checks below). Retry up to 3 attempts, feeding the failed gate's output back as "previous attempt" text.
5. **Output**: a JSON record per attempt (model, wall seconds, gate reached, failing ids, diff) under `<scratch>/results/`, and a one-line verdict per case: `fixed-first-try`, `fixed-after-retry`, `failed`, `fence-violation`.

Unit tests (`tests/specfactory/test_escalator_fix_probe.py`, RED first): a fake `agy` runner returning a canned reply; fence violation rejected; splice applied only to the named function; "no worse" suite comparison logic; retry feeds back the gate output. Existing specfactory suite must stay green (`tests/specfactory/`, ~90 tests).

## PX-17 — upstream code defects (three cases)

For each: worktree at the **parent** of the human fix; the human fix commit is the comparison, never shown to Gemini.

| Case | Pre-fix commit | Human fix | Fence | Diagnosis to give (from DECISIONS.md) | Target tests |
|---|---|---|---|---|---|
| R7a | `e024dde` | `4945db8` | `csrc/resolve.c`, include block only | "Every candidate fails to compile: `csrc/resolve.c: implicit declaration of function 'fmin'`; function-level splice cannot add `#include` lines, so the skeleton must carry `math.h`." | `make -s libouroboros.so` succeeds; `tests/csim/test_E05_*.py` collects and runs (no compile failure) |
| R7d | `bdf3ead` | `ecfcffe` | `csrc/agent.c::om_step_decisions` | The R7d row: 3d's telegraph-versus-surprise draw reads `w->rng_state` directly and never checks `w->rng_forced_len`, violating the header contract "every consumer of the stream takes from the same queue"; pattern to follow exists in `csrc/faction.c::om_faction_set`. Quote the header's RNG contract block (`csrc/ouroboros_sim.h`, "the world RNG contract"). | Build a minimal failing check yourself from the R7d row (a forced draw intended for 3d must be consumed by 3d, not 3e): a scratch pytest in the worktree, not committed to the repo; plus `tests/csim` no worse |
| R8 | `212ba88` | `30e86bb` | `csrc/resolve.c::om_intent_inject` and `csrc/agent.c::om_step_decisions` (two functions, two files: run as two sequential fenced tasks, agent.c first) | The R8 section: the header's "intent injection (fixture)" contract (quote it: injected intent enters as if decided in 3d; a telegraphed one enters the pending list and resolves at tick + 3; "a faction with an injected intent this tick skips its own 3d decision"); the code wipes `decisions_n` and recomputes, never writes `w->telegraphs[]`. REINFORCE consumer is out of scope. | The tests that call `inject_intent` and pass at `30e86bb` (run them at `30e86bb` to get the list; expect a subset of the 15 named in R8); `tests/csim` no worse |

Scoring per case: verdict; attempts used; wall time; whether the patch is semantically equivalent to the human fix (read both diffs and say: same, different-but-correct, or passes-tests-but-wrong, with the reason). "Passes tests but wrong" is the important failure class: check it by running the human fix's added tests or controls (R8 added `tests/csim/controls/test_control_e05_inject_ignored.py`) against Gemini's patch.

## PX-18 — test and fixture defects (two cases)

The escalator may edit a fenced test when a finding is classed `test-defect`. The danger is "fixing" a test by weakening it. So the gate is stricter than green.

| Case | Pre-fix commit | Human fix | Fence | Diagnosis to give | Gates beyond green |
|---|---|---|---|---|---|
| R7f | `3f183d7` | `d3273fa` | `tests/csim/test_E05_S036_declared_or_sprung.py`, functions `test_R_036_05*` and `test_R_036_06*` only | The R7e and R7f rows: case `w_alt` gives the defender (Fortifier, budget 100) enough budget to counter-attack under the bible's no-scripted-villain rule, so `len(read_reinforces(...)) == 1` is confounded; `w_cap`'s attacker budget falls below the viability bar so no telegraph is ever declared. Quote rule R-036-05 and R-036-06 from `docs/bible/epics/E-05-faction-agents-and-conflict.md`. | (1) No assertion removed or loosened: compare the set of `assert` statements and numeric literals asserted before and after; every original assertion about the rule's own quantities (commit, headroom, base, delta, probability gate) must survive; (2) the test still fails against the stub (run it at the pre-fix commit's C code: it must be red for the right reason, not green); (3) `scripts/specfactory/fixture_defects.py`'s `two_agent_confound` no longer flags it; (4) the human fix's version and Gemini's version both pass against the reference logic at `d3273fa`'s tree |
| R7l | current `main` (never fixed) | none | `tests/csim/controls/test_control_e05_garrison_before_damage.py` | The R7l row: the control reuses military 20.0, damage -16.0, garrison 27.3; `military + damage = 4.0` never reaches the `fmax(0.0, ...)` clamp, so `max(0, m + d) + g` and `max(0, m + g + d)` give the same number; a fixture with military low enough to clamp (the row suggests 10.0) distinguishes them, but the scenario's commit, effective attack and effective defence must be reworked so it still lands in a clean breakthrough. Quote ALG-20, ALG-21, ALG-22 from `docs/bible/algorithms.md`. | (1) `fixture_defects.py`'s `branch_coverage_of_control` no longer reports `VACUOUS_CONTROL`; (2) the two formulas evaluated with the new numbers differ by more than 1e-6; (3) the scenario still produces a breakthrough under ALG-20/21 (compute by hand in the write-up, and by running the clean build: the resolved attack's band must be breakthrough); (4) note that `OM_BUG_GARRISON_BEFORE_DAMAGE` (106) has no branch in `csrc/` yet, so full liveness (`scripts/specfactory/control_liveness.py <control>`) cannot pass; report what it says and do not add the C branch |

## Model comparison

Run every case with `gemini-3.7-flash-high` (the model Agora's build-intervene uses today). For any case it fails, rerun with `gemini-3.1-pro-high` (check `agy models` for exact ids). That answers "is the routing rule real with today's model, and if not, is a stronger seat enough".

## Deliverables

1. `scripts/specfactory/escalator_fix_probe.py` and its tests, committed and pushed.
2. `docs/legacy/proving_ground/PX-17-escalator-fixes-code.md` and `PX-18-escalator-fixes-tests.md`, in the style of the existing `PX-*.md` files there (claim, result, table, limits, design consequences left blank for the design lane to fill) — normal prose, no caveman. One row each appended to `docs/northstar/proving_ground/SCORECARD.md`.
3. A finishing report for Westley to carry back, containing: per case and model the verdict, attempts, wall seconds, equivalence judgement against the human fix, every "passes tests but wrong" instance with the diff excerpt, every fence violation, every weakened-assertion attempt in PX-18, total Gemini calls and wall time, and anything that argues against the claim. Do not recommend design changes; report evidence.

## Verification

- `pytest tests/specfactory/` green including the new tests.
- `git worktree list` in ouroboros shows no `/tmp/px17` or `/tmp/px18` entries afterwards; `git status --short` shows only the deliverable files before commit.
- E-02 baseline untouched: `pytest tests/csim/test_E02_S0*.py tests/csim/test_E02_gate_drift_trajectory.py tests/csim/test_E02_S160_drift_gate.py` on `main` still 52 passed / 4 skipped.
- The results JSON under scratch is copied into the write-ups' evidence (small; commit it under `docs/northstar/proving_ground/evidence/px17/` and `px18/`).

---
