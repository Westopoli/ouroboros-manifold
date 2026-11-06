# Handoff briefs

Each brief is a self-contained task handed to an implementor chat, copied here on the day it was handed off so the progression survives outside `~/.claude/plans/`. A brief is history once its finishing report lands; the report and the resulting design changes are recorded in `docs/northstar/proving_ground/` and `docs/northstar/research/`.

| Date | Brief | Handed to | Result |
|---|---|---|---|
| 2026-09-21 | `2026-09-21-factory-program.md` | design lane (this program's own plan) | in progress; Phase B.9 prototypes running |
| 2026-09-21 | `2026-09-21-px17-px18-escalator-fixes.md` | implementor chat | done 2026-09-21; `proving_ground/PX-17-PX-18-finishing-report.md` |
| 2026-09-21 | `2026-09-21-p2-landscape-mockup.md` | implementor chat | done; concept approved after review 2 |
| 2026-09-21 | `2026-09-21-p2-landscape-mockup-pass3.md` (terrain first, camera floor) | not yet handed | |
| 2026-09-21 | `2026-09-21-px-batch-a-sim-replays.md` (PX-4, PX-7, PX-14, PX-19) | implementor chat | done 2026-09-21; `proving_ground/PX-batch-A-finishing-report.md` |
| 2026-09-21 | `2026-09-21-px-batch-b-spec-content-boundary.md` (PX-1, PX-10, PX-11) | not yet handed | |
| 2026-09-21 | `2026-09-21-px-batch-c-vision-archive.md` (PX-12, PX-9) | not yet handed | |
| 2026-09-21 | `2026-09-21-executor-audit-fixes.md` (S-039 wiring and re-cut, E-04 re-cut, om_pow, fuel lint, DAG emitter, stale docs) | Sonnet sub-agent in the design chat | done 2026-09-21 night; DECISIONS.md Tenth round R13-R18; R13 became Q-039-01, R14/R17 resolved by the design lane and handed to a follow-up sub-agent |
| 2026-09-21 | `2026-09-21-agora-cascade-safety-seat-scheduler.md` (three waves, gated on the executor brief) | Sonnet sub-agent in the design chat, overnight | done 2026-09-22; DECISIONS.md Eleventh round; two follow-ups open (intervene out of the GPU process, runway row) |
| 2026-09-22 | `2026-09-22-mockup-qa-harness.md` (shared Xvfb self-QA harness for `scenes/mockups/*`, landscape retrofit as its positive control) | Sonnet sub-agent in the design chat, own worktree on branch `mockup/harness` (parallel doers cannot share one checkout; the design chat merges into `main`) | done 2026-09-22, merged `432ddba`; boot fixes `1797d68` and `b65afa8` (QA runs boot via `--script` and free every autoload: the SimBridge error route faded and freed mockups mid-run) |
| 2026-09-22 | `2026-09-22-p1-galaxy-mockup.md` | Sonnet sub-agent, worktree branch `mockup/galaxy` | done, merged, reviewed 2026-09-22; ready for Westley; pass-2 items: Local band framing, flash proof shot |
| 2026-09-22 | `2026-09-22-p3-objectives-mockup.md` | Sonnet sub-agent, worktree branch `mockup/objectives` | done, merged, reviewed, fixes merged `0709851`; ready for Westley |
| 2026-09-22 | `2026-09-22-p4-units-mockup.md` | Sonnet sub-agent, worktree branch `mockup/units` | done, merged, reviewed, fixes merged; ready for Westley; rule question: Bombards beat flanking Raiders under R-082-01 |
| 2026-09-22 | `2026-09-22-p5-fog-mockup.md` | Sonnet sub-agent, worktree branch `mockup/fog` | done 2026-09-22, merged `3ae4978`; reviewed; fixes merged `b50c548`; ready for Westley |
| 2026-09-22 | `2026-09-22-p6-layers-mockup.md` (two-layer prototype S-P10) | Sonnet sub-agent, worktree branch `mockup/layers` | done, merged, reviewed, fixes merged `e01725d`; ready for Westley |
| 2026-09-22 | `2026-09-22-p7-chronicle-mockup.md` | Sonnet sub-agent, worktree branch `mockup/chronicle` | done, merged, reviewed, fixes merged `65ccda5`; ready for Westley |
| 2026-09-22 | `2026-09-22-p8-hud-mockup.md` (camera, HUD, selection, S-P12) | Sonnet sub-agent, worktree branch `mockup/hud` | done, merged, reviewed, fixes merged `0d82c21`; ready for Westley |
| 2026-09-22 | `2026-09-22-p9-menus-mockup.md` (menu, setup, briefing, debrief, S-P01 card) | Sonnet sub-agent, worktree branch `mockup/menus` | done 2026-09-22, merged `532eb9f`; reviewed, notes in its README; ready for Westley |
| 2026-09-22 | `2026-09-22-two-day-push.md` (the approved plan: freeze, waves, attach gates, straggler rule, managers M0-M3) | M0 this session; M1-M3 chats Westley opens | running |
| 2026-09-22 | `2026-09-22-manager-M1.md` (push manager M1; rules in `2026-09-22-manager-common.md`) | Sonnet chat Westley opens in `~/Projects/om-push/m1` | ready to hand |
| 2026-09-22 | `2026-09-22-manager-M2.md` (push manager M2; rules in `2026-09-22-manager-common.md`) | Sonnet chat Westley opens in `~/Projects/om-push/m2` | ready to hand |
| 2026-09-22 | `2026-09-22-manager-M3.md` (push manager M3; rules in `2026-09-22-manager-common.md`) | Sonnet chat Westley opens in `~/Projects/om-push/m3` | ready to hand |
| 2026-09-22 | `2026-09-22-p1-galaxy-mockup-pass2.md` (legacy look on the new generator, shells, Play restart) | Sonnet sub-agent, worktree branch `mockup/galaxy-pass2` | done, merged 2026-09-22; shells use a flat stand-in under the QA renderer (raymarch too slow on llvmpipe), Q-106-shell-speed flagged |
| 2026-09-22 | `2026-09-22-p3-objectives-mockup-pass2.md` (edge scroll on large screens, regenerate advances the seed) | Sonnet sub-agent, worktree branch `mockup/objectives-pass2` | done, merged 2026-09-22; fog and hud share the window-size defect |
| 2026-09-22 | `2026-09-22-p4-units-mockup-pass2.md` (sim runs by default, drag box, edge scroll, HUD hover) | Sonnet sub-agent, worktree branch `mockup/units-pass2` | done, merged 2026-09-22 |
| 2026-09-22 | `2026-09-22-p5-fog-mockup-pass2.md` (edge scroll, seed perturbs the map) | Sonnet sub-agent, worktree branch `mockup/fog-pass2` | done, merged 2026-09-22 |
| 2026-09-22 | `2026-09-22-p6-layers-mockup-pass2.md` (runs on launch, pick and edges in one space, seed perturbs the map, self-demo) | Sonnet sub-agent, worktree branch `mockup/layers-pass2` | done, merged by the M0 gate 2026-09-22; real cause of dead buttons was no default selection, not coordinates |
| 2026-09-22 | `2026-09-22-p7-chronicle-mockup-pass2.md` (scroll over the galaxy mockup's view; same doer as galaxy pass 2) | Sonnet sub-agent (the galaxy doer), branch `mockup/chronicle-pass2` | done, merged by the M0 gate 2026-09-22; orbit camera's unseeded RNG costs screenshot determinism (galaxy pass-3 item) |
| 2026-09-22 | `2026-09-22-mockup-qa-harness-pass2.md` (first-look runs: real input, live clock, Westley's resolution, `expect` verb) | Sonnet sub-agent, worktree branch `mockup/harness-pass2` | done 2026-09-22, pushed, in the M0 gate; `firstlook` command, `expect` verb, cursor warp so polled mouse tracks synthetic moves, landscape positive control |

From 2026-09-22 evening every mockup branch and this ledger land through the M0 integrator's gate (origin/main has one writer during the push); ledger rows are batched on `docs/mockup-ledger`.

## Default shape of a workflow brief (2026-10-03)

For a brief the Architect writes and a Sonnet chat runs as a workflow. First used after `plans/archive/specs/2026-10-03-loop-fix-workflow-brief.md`, whose serial steps and one-at-a-time landings made it slow.

- Lanes run in parallel, one lane per file or file group, new code in new files.
- Inside a lane, the diagnoser and the test-writer start at the same time. The builder starts when both have reported. The test-writer works from the rule and the evidence in the brief, never from the diagnosis.
- Landings are batched: all lane branches merge into one landing branch, and the merge gate and the playthrough run once, at the end. Lanes whose files overlap are still queued one at a time.
- If the batched gate is red, the clerk bisects by lane: drop one lane's branch, rerun, and report the lane that caused it. A lane that fails is left out and reported; the others land.
- Agents stay small: one step, a brief under a page, one report under 30 lines, Sonnet only.
- The report gives agents spawned, tokens per agent and in total, wall-clock time, and lines changed per lane.
