# Editor debug chat: get the game running from the project folder

Written 2026-11-02 by the Architect chat (`beta-staircase-gate-channel`, ref 845ad1) for a Sonnet chat that Westley opens himself. Westley's order: "I'd rather fix it with a chat myself ... we're going to edit the main ouroboros project files to get the game working, the fixes should persist forwards and be integrated into the beta dispatcher's work once we're done." He ran it under Godot 4.6.3 and the errors came from there, so these are project bugs, not version differences.

## Your job

The repo root is a Godot project. Opening it in the editor and pressing F5, or running `godot.real --path .`, prints many errors and the game does not run. The first one Westley saw: `Invalid access to property or key 'done' on a base object of type 'Dictionary'.` Find every error in the console output, fix its cause in the project files, and re-run until this chain runs with zero `ERROR` and `SCRIPT ERROR` lines: privacy modal, loading screen, main menu, NEW CAMPAIGN to the galaxy view, a mission to mission preparation, Deploy to the tactical view (`scenes/tactical_c/tactical_view.tscn`). This is the failure Westley named at the start of the beta staircase: "the work being done passes tests, but doesn't actually run". For every fix, write down why no test caught it.

## Where you work (rules that keep the other lanes safe)

- Your folder is the git worktree `/home/westopoli/Projects/om-push/wt/ed-run` on branch `push/editor-debug` (made from main by the Architect's doer, with the C pipe built into `pipe/` and the Steam libraries copied into `addons/godotsteam/`). Launch your chat there. Westley opens that same folder in his Godot editor.
- Never touch `/home/westopoli/Projects/ouroboros-manifold` (Westley's own checkout, dirty). Never push to main. Push only your branch: `git push origin HEAD:refs/heads/push/editor-debug`. No force, no rebase (the git guard denies them); to stay current run `git fetch -q origin && git merge --no-edit origin/main` every so often, since two Dispatcher lanes are landing work.
- One fix per commit. The message quotes the console line it removes and names the file and line. Stage only files you changed on purpose (`git status` first; Godot may rewrite `.uid` or `.import` files or `project.godot` on open: do not commit those unless the fix needs it).
- A game window on Westley's real display takes `flock -w 1800 /home/westopoli/Projects/om-push/play.lock <command>` for the length of that run only (proof captures use the same screen). Headless or `xvfb-run -a` runs need no lock.
- Do not run `tests/qa` pytest or anything that starts the QA daemon on a port while a sweep or a gate is running; run at most one game at a time. A known race (a socket connecting to itself on ports 47500-47599) can falsely report a game as up until story H-066 lands; if a scripted run fails with a refused connection, retry once before suspecting your change.
- Contracts are frozen: `csrc/ouroboros_sim.h`, `signatures.toml`, the pipe frames in `docs/architecture.md`. If a fix seems to need one, stop and tell Westley. Tests under `tests/` are fenced: you do not edit them; a test that looks wrong goes in your log. Determinism is a contract (no wall clock, no platform maths in the sim). The game never calls a model API. No names, places or plot from existing fiction.
- Code quality (CLAUDE.md): minimal diffs, no unasked layers or wrappers, no cosmetic refactors, a `# See also:` comment where B exists because A fails, and a doc claim your fix makes wrong is rewritten in the same commit. Read CLAUDE.md first.
- Keep reports to Westley short. If you are stuck for more than three attempts on one error, say so, with the console lines, and ask. The Architect chat (`beta-staircase-gate-channel`) can be asked through Westley; do not message the Dispatcher chats yourself.

## What is known (read from main by an engineer on 2026-11-02; verify before relying)

- Godot: the gate, `play.sh` and the beta export all use `~/.local/bin/godot.real` (4.6.3); Westley's editor is `~/Apps/Godot_v4.7.2-stable_linux.x86_64`; `project.godot` says 4.7 since 2026-09-16. The `godot` wrapper on PATH forces `--headless` unless `OM_GODOT_GUI=1`; for a window run `godot.real` directly.
- The chain uses only the C sim pipe: `autoload/sim_session.gd` `bridge()` to `CBridge.open_session` to `OS.execute_with_pipe(_pipe_path())` (`autoload/c_bridge.gd` about lines 204-237). `_pipe_path()` takes env `OM_PIPE` first; with the `editor` feature tag (true in the editor and under `godot --path`) it uses `res://pipe/ouroboros_pipe`; otherwise the file beside the executable. `autoload/sim_bridge.gd` (the legacy Python sim) is inert (`USE_LIVE_SIM := false`). If the pipe is missing the galaxy view shows "pipe binary missing" (`scenes/galaxy/galaxy_view.gd` about line 164). Rebuild after a pull that changes `csrc/`: `scripts/build_pipe_linux.sh && mkdir -p pipe && cp dist/linux/ouroboros_pipe pipe/`.
- Steam: every use is guarded by `Engine.has_singleton("Steam")`; the beta chain never touches Steam; with the libraries copied there should be no Steam errors (without them: two harmless ERROR lines per run).
- The gate's plays drive the real game through a TCP daemon: `tests/qa/desktop/daemon_client.py` (`GodotGame`, `DaemonClient` verbs `state`, `tree`, `click`, `input`, `screenshot`; launched with `-- --qa-port N --seed 1`). You may script a chain walk with it under `xvfb-run -a` to check a fix headlessly; Westley's own GUI run is the final check.
- The tests pass on main today. That means these errors are in code no test reaches, or in the real-client path the harness avoids. That is useful information for the story that follows: note it.

## Your log (the hand-over to the story that follows)

Keep `docs/northstar/plans/editor_debug/log.md` in your branch, one row per distinct error: number, the console line verbatim, file and line, cause in one sentence, the fix commit, why no test caught it, and what would pin it (one sentence). Commit it with the fixes. Add a final section "Still red" for anything you could not fix, with the console line.

## End state and hand-back

Done means: a cold start from this folder runs the chain above with zero `ERROR` and `SCRIPT ERROR` lines in the console, Westley has walked it in his editor and says so, and `godot.real --headless --import --path .` prints no errors. Then: update the log, push the branch, tell Westley the head sha.

What happens next, so you know what your branch is for: the Architect turns the log into a story (client, beta channel) whose failing tests are written first from your rows by a different Sonnet; the beta Dispatcher's builder takes your branch's fixes (merge, then make the tests green) and lands them through the gate; the beta stage stories (B1 onward) then build on a game that runs. Your branch is the reference until that landing; nothing in it lands by itself.
