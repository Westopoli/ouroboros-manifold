# The method

Where another document disagrees with this directory, this directory wins. Each role reads its own card and the story it is given, nothing else unless the card sends it there. Written 2026-10-30 from the plan "The method, rewritten" (Westley approved); the sixteen documents it replaces are listed in `history.md`.

## Roles

| Role | Model | Card |
|---|---|---|
| Architect | Fable, a chat | `architect.md` |
| Builder | Sonnet, `subagent_type: doer` | `builder.md` |
| Test writer | Sonnet, `subagent_type: engineer` | `test_writer.md` |
| Clerk (lands, rules test defects) | Sonnet, `subagent_type: engineer` | `clerk.md`, `rulebook.md` |
| Runner (the main chat while stories build) | Sonnet | `runner.md` |
| Westley | human | `westley.md` |

Every spawn names its model. A task that mixes roles is split, one brief per role. Sub-agents never spawn sub-agents. Nothing is spawned in plan mode. Engineers and doers are never Fable.

## The six steps

The unit of work is one story: `S-###` from `docs/bible/stories.md`, or `H-###` from `harness.md` for work on the harness itself. One story, one branch `s/<id>-<slug>`, one landing, one `--no-ff` merge commit on main. Full text with the git conventions: `story_loop.md`.

1. **Requirement.** The story row exists, its epic rules are written, no open `Q-` row. The Architect moves it to Ready (`requirements.md`).
2. **Spec.** The Architect writes one page, `docs/stories/<id>.md`, and commits it on the branch: `<id> spec: <what>`.
3. **Verification.** A test writer, never the builder, commits red tests with the failing line pasted and one green positive control: `<id> tests: <n> red, <m> control`.
4. **Build.** One builder on one worktree builds until the story's tests are green, runs `pre_gate.sh`, pushes, stops. A round is one build and its gate; after the third reject the Architect hears of it.
5. **Verify.** A clerk merges main, runs the layered gate under the story's channel lock, `gate-lab.lock` or `gate-beta.lock` (`gate.md`), under ten minutes.
6. **Land.** The clerk opens the merged game with `scripts/play.sh` and reaches the story's scene; a game that does not open is a REJECT whatever the tests said. The merge commit carries the trailers. Westley's verdict is a `Seen <id>` commit.

## Numbers

| Name | Value | Owner |
|---|---|---|
| DRAFT-build-slots | 8 builds in flight (four per channel), 1 landing per channel | Westley, 2026-11-03 |
| DRAFT-mail-linger | 20 min before an unread `info` raises the flag | Architect, DEC-mail-station-2026-11-03 |
| DRAFT-mail-batch | 5 unread lines raise the flag before the linger | Architect, DEC-mail-station-2026-11-03 |
| DRAFT-mail-max | 1,500 characters per mail; longer is a file | Architect, DEC-mail-station-2026-11-03 |
| DRAFT-mail-stale | 30 min unread `block` or `ask` is `STATUS mail DRIFT` | Architect, DEC-mail-station-2026-11-03 |
| DRAFT-wakeups-per-landing | 10 chat turns per Land commit per week; over is a method defect | Westley, 2026-11-03 |
| DRAFT-proc-ttl | 14,400 s default before a recorded process may be reaped on time alone | Architect, DEC-proc-reaper-2026-11-03 |
| DRAFT-queue-lookahead | 1 candidate prepared ahead per channel in the gate queue | Architect, DEC-gate-queue-2026-11-03 |
| DRAFT-wt-slots-per-channel | 10 worktree slots per channel (`lab`, `beta`) | Architect, H-059 |
| Locks (`~/Projects/om-push/`) | `gate-lab.lock`, `gate-beta.lock` (stages 0 to 3, one per channel); `push.lock` (land_push.sh); `play.lock` (real-display runs); `records.lock` (records pushes) | Architect, H-059 |
| Build plus tests share of weekly model spend | at least 50% | Westley, 2026-10-29 |
| Fable share of weekly model spend | DRAFT 25% | method rev 3 G04 |
| Story size cap | 1,000 implementation lines | Westley, 2026-10-30 |
| Builder rounds before escalation | 3 | Architect |
| DRAFT-play-window-s | 60 s for the window to appear | Architect |
| DRAFT-play-settle-s | 10 s after the window before `qa_state()` is read | Architect |
| DRAFT-play-resolution | 1919x1080, the launch always passes `--windowed --resolution`; not 1920x1080, which equals the project viewport and presents only the splash (DEC-display-fault-measured-2026-10-31) | Architect, H-031 |
| DRAFT-play-min-fps | 30 fps on the Wayland window check | Architect, H-031 |
| DRAFT-play-fps-s | 3 consecutive seconds at DRAFT-play-min-fps | Architect, H-031 |
| DRAFT-pregate-pins-timeout-s | 600 s for the pre-gate csrc pins step (build plus pinned csim files) | Westley, 2026-10-29 layered-gate spec section 9 |
| DRAFT-token-report-tolerance | 3 points on shares, 5% on calls and tokens, for the 2026-10-29 fixture | Architect, DEC-token-report-day-2026-10-30 |
| Agent context stop | 120k per builder, test writer or clerk; 60k for the on-call architect agent | method rev 2 |
| Architect context | compaction at 400k is the only context rule; a turn past 400k without a compaction (more than one lone turn before it) is drift in `method_check.py`; the guard hook is removed (DEC-context-guard-off-2026-11-01) | Westley, 2026-11-01 |

## Status

This table is the register for every `DRAFT-` named in this directory. Status is computed, never written: `scripts/method/status.sh` reads `git log` and prints stories in flight, landed this week, waiting on Westley, test defects, sweeps and the four weekly numbers (build plus tests share, landings, stories Seen, Fable share). `scripts/method/token_report.py` writes the numbers nightly to `~/Projects/om-push/metrics/<week>.csv`. Under 50% build plus tests for a week is a method defect: the Architect names the class that grew and proposes the cut before specifying the next story. Over DRAFT-wakeups-per-landing is a method defect the same way: the Architect names the wake source that grew and proposes the cut.

## Files

- `requirements.md`: epics, stories, rules, flags, Ready, the prototype gate, change protocol.
- `story_loop.md`: the six steps and the git conventions.
- `architect.md`, `builder.md`, `test_writer.md`, `clerk.md`, `runner.md`, `westley.md`: role cards.
- `rulebook.md`: the test-defect procedure.
- `gate.md`: the layered gate in brief; spec of record `docs/northstar/plans/2026-10-29-layered-gate-spec.md`.
- `communication.md`: mail, station, wake rule, gate queue, process register (H-077 to H-081); registry `agents.toml`.
- `harness.md`: the `H-` stories.
- `history.md`: what was retired and where it is.
- Decisions: `docs/northstar/story_reviews/westley/decisions.md`, unchanged.
