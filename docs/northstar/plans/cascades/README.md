# Cascades

A cascade is a `/manager-mode` build: a Sonnet 5.5 chat as overlord, Sonnet 5.5 leaves, for a cluster of file-disjoint units that share one spec, one contract and one umbrella test (method: `docs/method/story_loop.md` steps 2 to 6, `docs/method/builder.md`).

See also: `.claude-swarm.toml` (the config a cascade's spec commit rewrites).

## Layout

- `.claude-swarm.toml` sits at the repo root; the skill walks up from the worktree and finds it. The cascade's spec commit sets `type_contract_path`, `umbrella_test_cmd` and `briefs_dir`; the rest is fixed. The landing commit resets them to the placeholders and restores anything the cascade loosened in `parent_owned`.
- `spec_dir` is this folder, `docs/northstar/plans/cascades/`.
- Each cascade has a folder `docs/northstar/plans/cascades/<slug>/` holding its spec, its contract, `briefs/` (the leaf briefs, the `briefs_dir`), `GATES.md`, sweeps and audits. The umbrella test lives under `tests/`.
- That folder is committed with the cascade's branch, so the record survives.
- `tests/**` is parent-owned: leaves never write tests. The shard-test-writer writes the cascade's tests in the wave base commit.

## Who does what

- The Architect (a Fable chat) writes the spec, the contract, the umbrella test and the cascade's `.claude-swarm.toml` in a worktree cut from `~/Projects/om-wt/`, on branch `s/<id>-<slug>`, and pushes it.
- Westley opens a Sonnet 5.5 chat in that worktree and runs `/manager-mode` on the spec path; it runs the shard tests, the leaves and the admission, then the verify step of the spec and reports once.

## Landing

- The cascade lands by `git merge --no-ff` on main in `~/Projects/ouroboros-manifold`, as `docs/method/story_loop.md` step 6 says: subject `Land <id> <slug>`, trailers `Story:` and `Tests:`, push. There is no Dispatcher, no gate queue and no `push/<slug>-cascade` branch.
- Parent-owned documents (ROADMAP, harness row, story file, SNAPSHOT.md) are written by the overlord in the landing commit, not by a leaf.
