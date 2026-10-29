# Cascades

A cascade is a `/manager-mode` build: the Dispatcher chat as overlord, Sonnet leaves, for a sim-side cluster of file-disjoint units that share one spec, one contract and one umbrella test (`docs/northstar/plans/2026-10-21-tool-split-spec.md`).

See also: `.claude-swarm.toml` (the config a records commit rewrites), pieces row HARNESS-swarm-config.

## Layout

- `.claude-swarm.toml` sits at the repo root; the skill walks up from the worktree and finds it. A records commit rewrites it at each cascade's start: `type_contract_path`, `umbrella_test_cmd` and `briefs_dir` are set per cascade, the rest is fixed across cascades.
- `spec_dir` is this folder, `docs/northstar/plans/cascades/`.
- Each cascade has a folder `docs/northstar/plans/cascades/<slug>/` holding its spec, its contract, its umbrella, `briefs/` (the leaf briefs, the `briefs_dir`), `GATES.md`, sweeps and audits.
- That folder is committed with the cascade's branch, so the record survives.
- `tests/**` is parent-owned: leaves never write tests. The shard-test-writer writes the cascade's tests in the wave base commit, which is the overlord's.

## Landing

- The cascade's final fast-forward lands on `push/<slug>-cascade`, not on `main`.
- From there the existing landing Workflow runs: the landing clerk merges `main`, runs `pre_gate.sh`, takes the gate lock, runs `merge_gate.sh`, copies shots, writes the records and pushes.
- One piece row per cascade owns every file the cascade touches, so `owner_lint` sees the cascade as one in-flight piece.
- The attach flip is a records commit after the merge.
