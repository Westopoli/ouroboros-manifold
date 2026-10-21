# Tool split: Workflow or Manager Mode per piece of work (Architect, 2026-10-21; Westley: "go ahead and spec the split")

Status: spec rev 1. Implementation rulings are the Architect's (Westley may veto). The evidence is `docs/northstar/plans/retro_2026-10-21/workflows_vs_manager_mode.md`.

## 1. The assessment (binding before any launch)

Every spec paragraph that will be built carries a `Tool:` line, written by the Architect from these six questions and audited with the spec. The line names the tool and the one question that decided it.

| Question | Points to a cascade (`/manager-mode`) | Points to a Workflow |
|---|---|---|
| Is there one spec, one contract and one umbrella test the work shares? | yes | no, or the contract is the piece |
| Can every unit be a failing test that runs locally without a frame (pytest under `tests/csim`, `tests/transport`, `tests/skilllab`, `tests/specfactory`)? | yes | needs Godot, a play, a screenshot or the look stage |
| Are the units file-disjoint under that umbrella? | three or more disjoint units | one or two units, or a serial wiring piece on a shared file |
| Must the build stop mid-way for Westley (a threshold, a tolerance, a live write, a design choice the spec left open)? | no: every number is in the spec or a named draft | yes: the script's STOP rules carry it |
| Does the result need post-merge live verification (playthrough, shot, look)? | still yes: the landing is a Workflow either way | yes |
| Does the work touch the frozen contracts (`csrc/ouroboros_sim.h`, the pipe frames, the save format)? | the contract piece is specced first; the cascade builds consumers after it lands | the contract piece itself |

Rule of thumb from the record: a sim-side cluster with three or more test-expressible, file-disjoint units is a cascade; anything that ends in a frame, any single piece, and every landing is a Workflow. Lab engine pieces E1 to E4, places P3, startforce placement and harness clusters are cascade-shaped; client pieces, plays, shots, screens and contract pieces are Workflow-shaped.

## 2. Roles

The Dispatcher chat (Sonnet) is the cascade's overlord: it runs `/manager-mode` (hardcore when the cascade touches a save, pipe or checksum path) in a worktree under `~/Projects/om-push/wt/<slug>` on branch `push/<slug>-cascade`, never in the live checkout and never on `main`. The Architect writes the spec, the contract and the umbrella test's assertions (the shard-test-writer writes the per-leaf tests inside the cascade). Leaves are Sonnet 5.5 doers (`DOER_BACKEND`); the test writers and auditors are Sonnet 5.5 (`TEST_WRITER`). No Fable agent is spawned by the cascade. The overlord's own context is the long-lived one; it restarts from its continuation memory past about 400k tokens like any coordinator chat, with the cascade's on-disk records as its state.

## 3. Configuration: `.claude-swarm.toml`

One file at the repo root, rewritten by a records commit at each cascade's start (the skill walks up from the worktree and finds it). Fixed across cascades:

```toml
spec_dir            = "docs/northstar/plans/cascades/"
type_contract_path  = "<the cascade's contract header, e.g. csrc/field_noise.h>"
umbrella_test_cmd   = "python3 -m pytest <the cascade's umbrella file> -q -p no:cacheprovider"
apex_test_cmd       = "scripts/specfactory/pre_gate.sh"
briefs_dir          = "docs/northstar/plans/cascades/<slug>/briefs/"
parent_owned = [
  "csrc/ouroboros_sim.h", "docs/northstar/spec_factory/signatures.toml",
  "docs/bible/**", "docs/northstar/**", "tests/**",
  "scripts/specfactory/**", "Makefile", "autoload/**", "scenes/**",
  "tests/csim/data/**", "tests/skilllab/golden_hashes.json",
]
[invariants]
max_impl_lines      = 100
max_test_assertions = 40
```

`tests/**` is parent-owned because leaves never write tests (CLAUDE.md "Tests are the spec"); the shard-test-writer writes the cascade's tests in the wave base commit, which is the overlord's, not a leaf's. `max_impl_lines` 100 is the build-unit rule. The spec, the contract and the umbrella for a cascade live under `docs/northstar/plans/cascades/<slug>/` with the briefs, `GATES.md`, sweeps and audits, and are committed with the cascade's branch so the record survives (the 2026-10-02 cascade's records did not).

## 4. Landing

The cascade's final fast-forward lands on `push/<slug>-cascade`, not on `main`. From there the existing landing Workflow runs: the landing clerk merges `main`, runs `pre_gate.sh`, takes the gate lock, runs `merge_gate.sh` (csim and transport regression, playthrough, look, status), copies shots, writes the records and pushes. One piece row per cascade (`VG-P3`, not one per leaf) owns every file the cascade touches; `owner_lint` sees the cascade as one in-flight piece. The attach flip is a records commit after the merge.

## 5. The pre-launch consistency pass (Workflows)

For Workflow pieces, the one-agent preflight stop moves out of the script: before a launch, the Dispatcher spawns one Sonnet engineer with the spec paragraph, the pieces row, the ledger rows it names, the rule pins of the tests it names and the script's own preflight list, and that engineer reports every gap in one message. The Architect answers them in one ruling. The script then launches with the gaps closed. Fifteen of the twenty spec-and-records stops of 2026-10-14 to 10-21 would have been one message each instead of a relaunch.

## 6. Pieces

- `HARNESS-swarm-config`: the `.claude-swarm.toml` rewrite above, `docs/northstar/plans/cascades/README.md` (the layout and the landing path), and the `Tool:` line check in `scripts/specfactory/status_check.py` (a WARN when a queued pieces row's spec paragraph has no `Tool:` line; DRIFT after 2026-10-28). Tests first: `tests/specfactory/test_tool_line.py` (a fixture paragraph without the line warns; with it, OK; positive control: the check is absent today).
- `HARNESS-cost-report`: `scripts/specfactory/cost_report.py`, the usage-metadata cost script (from the Architect's scratch `cost/cost.py`; reads only `timestamp`, `type`, `sessionId`, `message.model`, `message.usage`, never content; DEDUP by repeated usage tuple per file until a message-id field is used), with `--since`, `--until`, `--by session|day|role` and the rate table in the source as named drafts. Tests: a fixture of ten synthetic lines gives the expected totals and dedup count. The retro folder's numbers come from it.
- `CASCADE-P3-trial`: the first cascade, VG-P3 (places growth wired into the economy; its spec section is in the places lane spec, launched on the probe's shape report received 2026-10-21). Its measurement, recorded in `docs/northstar/plans/retro_2026-10-21/p3_trial.md`: wall clock from wave base to landing, stops and their causes, dollars by `cost_report.py`, leaves admitted and reverted, defects found by the merge gate after admission. Compared against the Workflow numbers in the evidence file. Westley reads that page before a second cascade is launched.

## 7. Records

CLAUDE.md "Workflow specs" gains the assessment as its first bullet and the Dispatcher row gains the overlord duty; `docs/northstar/plans/workflows_2026-10-07/dispatcher.md` gains the consistency pass (section 5) and the overlord paragraph (section 2); the evidence file goes to `docs/northstar/plans/retro_2026-10-21/`. Ledger row `REC-tool-split-2026-10-21`.
