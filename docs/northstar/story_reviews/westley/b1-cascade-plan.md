# B1 cascade: the approved screens, in the project, on both machines

Architect, rewritten 2026-11-05 at landing. The earlier version of this file planned a rebuild of H-060; the cascade instead reused the finished H-060 build (DEC-b1-reuse-the-built-branch-2026-11-05) and built only the new Mac story H-087. Landing: `Land H-060 H-087 beta-b1-approved-screens`.

## What was delivered

- H-060 (rules R-060-01 to R-060-08 in `docs/stories/H-060.md`): the approved screens chained to an empty field in the beta, a `variant` picker on mission preparation, `BetaMode.active()`, `[editor] run/main_run_args="-- --om-beta"` so an editor F5 is the beta. Built 2026-11-02 (branch `s/H-060-beta-b1-approved-screens`, 1948fb5e), merged into the cascade branch, its 17 tests re-run green on 2026-11-05.
- H-087 (rules R-087-01 to R-087-05 in `docs/stories/H-087.md`): `scripts/setup_editor.sh` builds the pipe with `scripts/build_pipe_macos.sh` on a Mac, finds Godot in `/Applications`, and `--check` names the Godot and `clang`; `scripts/fetch_godotsteam.sh` uses `shasum -a 256` where `sha256sum` is absent; the README says what a Mac needs. One cascade leaf; its spec, contract and records are in `docs/northstar/plans/cascades/b1-approved-screens/`.
- Harness: `parent_owned` no longer lists `autoload/**` and `scenes/**`; `apex_test_cmd` is the story's verify line (DEC-client-cascade-parent-owned-2026-11-05).

## How it was proved here

The Darwin cases run on the Linux box with stubs (`uname`, `clang`, `shasum`, a stub Godot app). The saboteur confirmed every spec-pinned target fails a test when broken. Nothing was run on a Mac; the BSD `find` and bash 3.2 rules are carried by constraints in the spec and a `find` that rejects `-quit` in the test rig. The play check reached `res://scenes/beta/stage_field.tscn`; its proof capture was rejected only because a virtual display draws nothing (no real display in the session).

## Verdict

Seen 2026-11-05 on both machines ("B1 approved", `ruled.md`). His Mac walk found no pan or zoom in the galaxy view and on the field: bug W8 in `ROADMAP.md`, investigated and fixed before B2 is judged. Decisions he may veto: `decisions.md`, rows dated 2026-11-05 (reuse, clone, parent-owned, Seen by F5, Mac is editor F5, ruling 8, the `OM_GODOT_APP` seam, the boundary rulings).
