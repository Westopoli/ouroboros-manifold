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

Every spawn names its model. Sub-agents never spawn sub-agents. Nothing is spawned in plan mode. Engineers and doers are never Fable.

## The six steps

The unit of work is one story: `S-###` from `docs/bible/stories.md`, or `H-###` from `harness.md` for work on the harness itself. One story, one branch `s/<id>-<slug>`, one landing, one `--no-ff` merge commit on main. Full text with the git conventions: `story_loop.md`.

1. **Requirement.** The story row exists, its epic rules are written, no open `Q-` row. The Architect moves it to Ready (`requirements.md`).
2. **Spec.** The Architect writes one page, `docs/stories/<id>.md`, and commits it on the branch: `<id> spec: <what>`.
3. **Verification.** A test writer, never the builder, commits red tests with the failing line pasted and one green positive control: `<id> tests: <n> red, <m> control`.
4. **Build.** One builder on one worktree builds until the story's tests are green, runs `pre_gate.sh`, pushes, stops. Up to three rounds with the same builder before the Architect hears of it.
5. **Verify.** A clerk merges main, runs the layered gate under `gate.lock` (`gate.md`), under ten minutes.
6. **Land.** The clerk opens the merged game with `scripts/play.sh` and reaches the story's scene; a game that does not open is a REJECT whatever the tests said. The merge commit carries the trailers. Westley's verdict is a `Seen <id>` commit.

## Numbers

| Name | Value | Owner |
|---|---|---|
| DRAFT-build-slots | 3 builds in flight, 1 landing | Westley |
| Build plus tests share of weekly model spend | at least 50% | Westley, 2026-10-29 |
| Fable share of weekly model spend | DRAFT 25% | method rev 3 G04 |
| Story size cap | 1,000 implementation lines | Westley, 2026-10-30 |
| Builder rounds before escalation | 3 | Architect |
| DRAFT-play-window-s | 60 s for the window to appear | Architect |
| Architect context | restart past 400k; compaction at 400k | Westley, 2026-10-30 |

## Status

Status is computed, never written: `scripts/method/status.sh` reads `git log` and prints stories in flight, landed this week, waiting on Westley, test defects, sweeps and the four weekly numbers (build plus tests share, landings, stories Seen, Fable share). `scripts/method/token_report.py` writes the numbers nightly to `docs/method/metrics/<week>.csv`. Under 50% build plus tests for a week is a method defect: the Architect names the class that grew and proposes the cut before specifying the next story.

## Files

- `requirements.md`: epics, stories, rules, flags, Ready, the prototype gate, change protocol.
- `story_loop.md`: the six steps and the git conventions.
- `architect.md`, `builder.md`, `test_writer.md`, `clerk.md`, `runner.md`, `westley.md`: role cards.
- `rulebook.md`: the test-defect procedure.
- `gate.md`: the layered gate in brief; spec of record `docs/northstar/plans/2026-10-29-layered-gate-spec.md`.
- `harness.md`: the `H-` stories.
- `history.md`: what was retired and where it is.
- Decisions: `docs/northstar/story_reviews/westley/decisions.md`, unchanged.
