# Ground rules for push managers M1, M2, M3 (two-day push, 2026-09-22)

Read with your own brief (`2026-09-22-manager-M1.md`, `-M2.md`, `-M3.md`) and the plan `2026-09-22-two-day-push.md` (Decisions, Waves table, Attach gates, Straggler rule, Managers table).

- You are a **Sonnet chat** running the updated `manager-mode` skill: overlord Sonnet, shard-test-writer Sonnet, leaves Sonnet. Do not switch models.
- Work only in your clean clone. Never open, pull into, or commit in `~/Projects/ouroboros-manifold` (Westley's live checkout) or any other clone. `origin` is GitHub; `origin/main` is the truth; your clone's `main` moves only by `git pull --ff-only origin main`.
- Every git operation the cascade needs goes through `python3 ~/.claude/skills/swarm-shared/scripts/worktree_ops.py` (preflight, base, add, commit). A repository guard denies any Bash command whose text contains history-rewriting verbs (the word rebase, `reset --hard`, `clean`, `checkout <sha> -- path`, `-D`, `stash`, `--amend`, force pushes); never type them, not even in a commit message. Pushing a leaf branch is `git push origin push/<piece>` from the leaf worktree; that is the only plain git command you run.
- Leaves never edit `tests/**`, `csrc/*.h`, `csrc/sim.c`, `csrc/region.c`, `Makefile`, `project.godot`, `docs/**`, `scripts/**` (all `parent_owned`). A leaf that needs a header change files it in `.swarm/<slug>/NEEDS-HEADER.md`; M0 batches those into `freeze/F2b`.
- Tests are the spec and pre-exist, fenced. The shard-test-writer authors no new assertions; it writes one **adapter test file per leaf**, `tests/push/test_leaf_<piece>.py`, carrying the Spec Link header (`# spec: docs/northstar/plans/push/specs/<piece>.md::Acceptance::AC-1`) and a single test that runs the piece's acceptance node ids from `docs/northstar/plans/push/pieces.toml` through `pytest.main([...])` and asserts exit 0. That satisfies the skill's invariants without touching a fenced test; record the deviation in your Phase 7 report.
- Per-piece spec: `docs/northstar/plans/push/specs/<piece>.md`, written by you (lite-discovery is fine) from the piece's regenerated cards in `docs/northstar/proving_ground/evidence/card_regen/<E>/` (their briefs quote the bible rules verbatim), the module's declaration block in `csrc/ouroboros_sim.h` (between the `generated from signatures.toml: <module>` markers) or `scripts/specfactory/card_slice.py <card> --print`, `csrc/om_constants.h` (constants come from there, never typed as literals; `scripts/specfactory/alg_constants.py --lint csrc` must pass), and the module's control in `tests/csim/controls/` naming the fault the leaf plants under `#ifdef OM_DEBUG_INJECT`. The spec's Acceptance section lists the node ids from pieces.toml verbatim.
- Per-clone `.claude-swarm.toml` (overwrite the tracked one in your clone only; never commit it):

```
spec_dir           = "docs/northstar/plans/push/specs/"
type_contract_path = "csrc/ouroboros_sim.h"
umbrella_test_cmd  = "~/Projects/agora/.venv/bin/python -m pytest tests/push -q -p no:cacheprovider"
parent_owned = ["csrc/*.h", "csrc/sim.c", "csrc/region.c", "csrc/om_constants.h", "Makefile", "project.godot", "tests/csim/**", "tests/qa/**", "tests/transport/**", "docs/**", "scripts/**", "autoload/**", "scenes/**"]
worktree_link    = [".venv"]
footprint_ignore = [".git/**", ".swarm/**", ".claude/**", "logs/**", "__pycache__/**", "*.pyc", ".pytest_cache/**", "build/**", "*.so", "*.gd.uid"]
[invariants]
max_impl_lines = 2500
max_test_assertions = 20
```

  M3 removes `autoload/**` and `scenes/**` from `parent_owned` for its client pieces and adds `csrc/**` (except `csrc/pipe/**`) instead.
- One cascade slug per piece (`<piece>` lower-case). Phases 0 to 3 as the skill says; Phase 4 spawns the leaf on its worktree; Phase 5 commits through `worktree_ops.py commit`; then **stop before admit**: push the leaf branch as `push/<piece>`, message M0 (session `parallel-backend-client-mvp`, ref `adf873`) with the piece id, branch and the leaf's green and red ids, and take the next piece. M0 merges; you never merge, never run `admit`, `sync`, `finish` or `cleanup --purge`.
- `build/` at the repo root is a tracked PyInstaller tree that also holds the `O0`/`O2` library output dirs; never `rm -rf build` or `make clean` it (two M0 agents already deleted it by accident and had to restore it). Godot tests for client pieces run through `scripts/run_godot_tests.sh <test>.gd` under Xvfb.
- Leaves run only the piece's acceptance ids locally plus `make -s OPT=-O2 WERROR=1 libouroboros.so libouroboros_dbg.so`, never the whole suite. At most 6 leaves in flight in your clone at once.
- Straggler rule: when M0 pushes tag `attach/<piece>` (poll `git fetch --tags` every 5 minutes), `git pull --ff-only origin main`, then `base --wave N+1 --commit-artifacts --yes`, then spawn the next piece in your queue whose `depends_on` are all tagged; running leaves keep going untouched. A leaf green on a subset submits an increment `push/<piece>-1` (you commit `git add <owns> && git commit` in its worktree) and continues. At 2× the size estimate ask the leaf for a checkpoint; at 3×, or three distinct candidates failing the same ids, wait for its current increment to merge, stop it, spawn a split leaf for the remaining stories, and write `.swarm/<slug>/NEEDS-DIAGNOSIS.md` for M0 with the failing ids and first assertion lines.
- Report to M0 after each piece, five lines: piece, branch, green count, red ids, anything the brief could not do. Report-back caveman mode; code normal prose.
