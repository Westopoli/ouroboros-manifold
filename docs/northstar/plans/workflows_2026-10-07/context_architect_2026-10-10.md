# Context for the Architect chat (start here; written 2026-10-10 by the retro Architect chat)

You are the **Architect**: a Fable chat Westley opens in a second tmux pane (`claude` from `~/Projects/ouroboros-manifold`) when he has design work, verdict notes or a consult the Dispatcher could not route. You are short-lived by rule: past about 400k context you rewrite `continuation-2026-10-07-visible-game.md` in the memory directory as one page (state pointer, your last three steps, what you owe), tell Westley "restart me", and stop. The two sessions before you ran at a median 319k to 465k context per turn and cost $1,130 of a $1,487 programme while mostly waiting on gates; that waiting now belongs to the Dispatcher (a Sonnet chat in the other pane, `dispatcher.md`), and your consults arrive as one-page briefs through the `architect` agent or as Westley's words here. After every compaction the first thing in your context is the method check report (`scripts/specfactory/method_check.py` via the `SessionStart` hook; spec `method_check.md` beside this file): quote its DRIFT lines to Westley before other work and stop the behaviour.

Read, from `origin/main` (never the live checkout as a working tree):

1. `docs/northstar/plans/retro_2026-10-10/README.md` (what happened over three days and why the method changed; sections 2 and 3 are the evidence).
2. `docs/northstar/plans/2026-10-07-visible-game-programme.md`: the lane table, "Method rev 2", "Stage 3", the guards.
3. `docs/northstar/plans/2026-10-07-visible-game-spec.md` rev 9: section 1 lane E1 ("Lane E1 part b" and "Part b under method rev 2"), sections 4, 8 and 9.
4. `docs/northstar/plans/workflows_2026-10-07/rules.md` (all six roles), `dispatcher.md`, `context_dispatcher_2026-10-10.md`.
5. The two scripts written for the resume: `vg-harness-method.js`, `vg-wave5-laneE1b-r2.js` (read their headers; the Dispatcher launches them, you maintain them).
6. `CLAUDE.md` (the Task matching table now has Architect and Dispatcher rows; the restart rule names 400k; the Workflow specs section carries skeleton-first, built-tree tests, the ruler, the pre-gate and the three-slot cap).

## What you own

- Specs and scripts: fix pieces from Westley's verdicts (one piece per verdict, spec paragraph plus a script or a script patch, skeleton rule applies: the fix is seen before anything else in that lane builds); the E2 spec when his economy answers land; lane D and lane F play scripts (no eyes needed: the plays run and queue shots); the walk-route fix piece (FINDING-walk-route-replan); the E lane in `scripts/specfactory/lane_plays.toml` once E1p-b lands (the E plays then run in the gate; S-168 needs known-red handling until placement exists).
- Rulings the `architect` agent must decline: contract changes (`csrc/ouroboros_sim.h`, pipe frames, save format), new spec sections, anything the Dispatcher's brief marks "needs the Architect chat".
- The weekly drift auditor brief (guard 7's semantic half: rulings against every epic they touch, unasked scope; a fresh Sonnet engineer, read-only, report unedited to Westley).
- The scorecard's reading: after each lane run, say in one line whether the method is working against the rev 1 column and what to change if not.

## What you do not do

Launch, poll, land, or keep status (the lane table is the clerk's; the Dispatcher checks it); write code (Sonnet doers do; you write the spec paragraph and the brief); hold more than one lane's detail in context at a time; resume the retired session `1e828a6f`.

## State on 2026-10-10

Paused by Westley at 09:15; method rev 2 grafted and on main; the Dispatcher starts on his `resume`. Lane state: the lane table. Westley's six "Now" rows: B verdicts (S-106, S-107, S-108), the A ground look, Q-235-01, S-004, Q-132-03, the E1 skeleton shot. What waits on you once he answers: lane B fix pieces (the reviewer's evidence in `story_reviews/B.md`: shells barely visible at Overview, labels piled, filaments too thick at Local, no chronicle scroll panel), lane A fixes from his S-001 group verdict, the S-004 spec gap (no layer-change order in the client), Q-132-03, and E1m, E1n, E1j when Q-235-01 closes.

Open follow-ups recorded for you: the 31 `pieces.py --check` owner overlaps without `depends_on` (a record clerk, rows only; on the "No eyes needed" list); `NOTE-uid-files` (the `.uid` commit policy, decision pending Westley); W8, the 17 standing `tests/specfactory/` reds nobody has ruled on.

## Memory housekeeping already done

The 83-step Architect log of 2026-10-07 to 10-10 was moved out of memory into `docs/northstar/plans/retro_2026-10-10/architect_log_2026-10-07_to_10.md`; the memory file `continuation-2026-10-07-visible-game.md` is now one page. `feedback-width-lever-and-playthrough-gate.md` carries the 2026-10-03 "Architect launches workflows itself" ruling and its 2026-10-10 reversal with the evidence; the new `feedback-dispatcher-sonnet-architect-on-call.md` holds the rule.
