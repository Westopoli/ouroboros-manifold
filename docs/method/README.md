# The method

Where another document disagrees with this directory, this directory wins. Westley drives: he points a Fable chat at one stage, it writes the cascade plan, he hands the plan to a Sonnet chat that runs `/manager-mode`, and he relays between chats by hand. His plan prompt names `story_loop.md` and says everything the plan must do; the cards here hold only what every plan shares. Written 2026-10-30; cut to eight files 2026-11-05 (`history.md` lists what left and where it is); `requirement_audit.md` added 2026-11-09.

## Roles

| Role | Model | Card |
|---|---|---|
| Architect (plans, specs, decides) | Fable, a chat | `architect.md` |
| Overlord (runs one cascade) | Sonnet 5.5, a chat running `/manager-mode` | the skill |
| Builder | Sonnet 5.5, `subagent_type: doer` or a cascade leaf | `builder.md` |
| Test writer | Sonnet 5.5, `subagent_type: engineer` or the skill's shard-test-writer | `test_writer.md` |
| Auditor (weekly, read-only) | Sonnet 5.5, `subagent_type: engineer` | `requirement_audit.md` |
| Westley | human | `westley.md` |

Every spawn names its model. Sub-agents never spawn sub-agents. Nothing is spawned in plan mode. Engineers and doers are never Fable.

## The six steps

The unit of work is one story: `S-###` from `docs/bible/stories.md`, or `H-###` from `harness.md` for the harness itself; a cascade lands several at once. Requirement, Spec, Tests first, Build, Verify, Land: `story_loop.md`, the file Westley quotes in every plan prompt.

## Numbers

| Name | Value | Owner |
|---|---|---|
| Story and leaf size cap | 1,500 implementation lines (`.claude-swarm.toml` `max_impl_lines`) | Westley, 2026-11-05 |
| Build plus tests share of weekly model spend | at least 50% | Westley, 2026-10-29 |
| Fable share of weekly model spend | DRAFT 25% | method rev 3 G04 |
| DRAFT-play-window-s | 60 s for the window to appear | Architect |
| DRAFT-play-settle-s | 10 s after the window before `qa_state()` is read | Architect |
| DRAFT-play-resolution | 1919x1080, the launch always passes `--windowed --resolution`; not 1920x1080, which equals the project viewport and presents only the splash (DEC-display-fault-measured-2026-10-31) | Architect, H-031 |
| DRAFT-play-min-fps, DRAFT-play-fps-s | 30 fps for 3 consecutive seconds on the window check | Architect, H-031 |
| DRAFT-pregate-pins-timeout-s | 600 s for the pre-gate csrc pins step | Westley, 2026-10-29 |
| DRAFT-token-report-tolerance | 3 points on shares, 5% on calls and tokens | Architect, DEC-token-report-day-2026-10-30 |
| DRAFT-proc-ttl | 14,400 s before a recorded process may be reaped on time alone (`scripts/method/proc.py`) | Architect, DEC-proc-reaper-2026-11-03 |
| Agent context stop | 120k per builder or test writer | method rev 2 |
| Architect context | compaction at 400k is the only context rule (DEC-context-guard-off-2026-11-01) | Westley, 2026-11-01 |

## Status

`scripts/method/status.sh` reads `git log` and prints stories in flight, landed this week, and the weekly numbers; `scripts/method/token_report.py` writes them nightly to `~/Projects/om-push/metrics/<week>.csv`. Under 50% build plus tests for a week is a method defect: the Architect names the class that grew and proposes the cut. The nightly sweep and nightly play (`om-sweep.timer`, `om-nightly-play.timer`) run the full suite and the scripted playthrough on main and report; they block nothing. Once a week, on Westley's word, the requirement audit checks each rule against the bible and each rule's Proof line against the current lab and beta (`requirement_audit.md`); an unproven rule blocks the sign-off of the stage that depends on it.

## Files

- `story_loop.md`: the six steps and the git conventions.
- `requirements.md`: epics, stories, rules, the Proof line, flags, Ready, the prototype gate, change protocol.
- `requirement_audit.md`: the weekly audit of rules and their proofs; the auditor's card.
- `architect.md`, `builder.md`, `test_writer.md`, `westley.md`: role cards.
- `harness.md`: the `H-` stories.
- `history.md`: what was retired and where it is.
- Decisions: `docs/northstar/story_reviews/westley/decisions.md`. The two staircase plans: `docs/northstar/story_reviews/westley/beta-staircase.md`, `lab-staircase.md`.
