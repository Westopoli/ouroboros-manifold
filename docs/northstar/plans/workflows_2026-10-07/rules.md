# Shared RULES blocks for lane briefs and wave scripts

Cited by briefs, not pasted. Source wording: vg-wave5-laneE1.js line 12, vg-resume-laneC-land2.js line 8, plus the 2026-10-09 lessons. Three roles: Builder, Landing clerk, Scout or auditor.

## (a) Builder (Doer)

- Model Sonnet 5.5; never spawn sub-agents; think tersely; the last message is the report, no interim notices.
- Worktree ONLY by absolute path: `git -C ~/Projects/ouroboros-manifold fetch -q && git -C ~/Projects/ouroboros-manifold worktree add -b <branch> ~/Projects/om-push/wt/<suffix> origin/main`. Every command names its absolute path; never cd into, or touch, `~/Projects/ouroboros-manifold`.
- No stash, rebase, amend, force, `make clean`; never push to main; never kill another process's gate.
- Build: `make && make pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg`; run `godot.real --headless --import` once first. Python `~/Projects/ouroboros-manifold/.venv/bin/python`; Godot `~/.local/bin/godot.real` (4.6.3).
- Godot tests: `timeout 1800 scripts/run_godot_tests.sh <file>`. Display-needing files: `xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s <file>`. Wrap every Godot or xvfb run in `timeout 1800` (two wave-1 runs hung 8 h).
- Long runs: `systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 -- nice -n 10 <cmd>`. Gates run detached, polled every 5 min.
- Renderer split (2026-10-09): Godot tests and desktop tests run under the DEFAULT renderer. `OM_QA_RENDERER=vulkan` is for story plays only (Xvfb vulkan washes colours out). The galaxy pixel tests and the plays are pinned to that split. Desktop plays run one at a time: `xvfb-run -a timeout 900 .venv/bin/python -m pytest <play> -q`.
- Determinism: integer or plain double arithmetic, no libm transcendentals (libm_lint), no wall clock, no hash-order iteration; new world state is hashed (checksum_full) and saved.
- Builders never edit tests. A test that looks wrong is ruled by the rulebook (ledger row TD-<lane>-<n>) or the piece stops. A Westley threshold lives in a `*_park_*` file.
- Liberties named in the spec are taken as written and marked in a code comment; anything else undecided stops the piece.
- Stop and report (ok=false, stop_reason) on a file outside your list, a number nobody gave (named mockup drafts allowed: cite), or a new public C symbol not in the frozen header.
- Never stage `*.import` or `*.uid` noise. `godot --import` leaves untracked `*.uid`: delete them before any checkout or merge. (Exception: a `.uid` beside a new script you wrote is committed per NOTE-uid-files.)
- Push your branch, write `.wt-done` (date, branch, pushed sha). Stop past 120k context.

## (b) Landing clerk (Engineer)

- Gate, run from the worktree, detached into `<TMPDIR>/gate.log`: `flock -w 14400 ~/Projects/om-push/gate.lock env TMPDIR=<dir> MERGE_GATE_SUITE_TIMEOUT=2400 MERGE_GATE_PLAYTHROUGH_TIMEOUT=2400 MERGE_GATE_PLAY_TIMEOUT=900 MERGE_GATE_PIECES=<worktree>/docs/northstar/plans/push/pieces.toml scripts/specfactory/merge_gate.sh <worktree> origin/main <comma piece list>`. Three positional arguments.
- Wait: poll `gate.log` for the `^GATE look ` line, one foreground command under 10 minutes at a time. Then `pgrep -f '^bash scripts/specfactory/merge_gate.sh'` to confirm no gate for the worktree still runs; never pgrep your own command line. There is no VERDICT line: the verdict is the set of `GATE <stage> REJECT` lines.
- Flake rule: a lone playthrough or lane_plays red that passes twice alone gets one re-run.
- Known-red: `scripts/specfactory/lane_plays_known_red.txt` holds exact ids with reasons; `scripts/specfactory/playthrough_known_red.txt` stays empty (a gate test enforces it).
- Ownership: every file in the diff is owned by a listed piece (`owns` or `owns_glob`; acceptance does not count). Two in-flight pieces sharing a file need `depends_on`. Park files (`*_park_*`) stay off the candidate and are listed.
- Push: branch first. `git push origin HEAD:main` only on a clean gate and only when the brief authorises it; merge origin/main first if it moved and say so (ledger appends keep both sides).
- Snapshot cleanup: delete only the `merge_gate_before_*` directories under your own TMPDIR, never a glob over /tmp.
- Test-defect rule: a test changes only under a rulebook or ledger row. Thresholds, windows and tolerances are Westley's. A determinism golden moves once, with a ledger row naming old and new values.
- Report schema: ok, branch, sha, summary (stage lines verbatim), red_ids, stop_reason. Write `.wt-done` after the push.

## (c) Read-only scout or auditor

- Detached worktree (`git worktree add --detach <abs path> origin/main`); remove it after, even if removal is slow. Change nothing; no commits, no pushes, no ledger edits.
- Evidence as file:line plus the sha read. Mark what was not run (Godot, pytest) as unverified.
- Report once, at the end, findings numbered, with a blocking yes or no.
