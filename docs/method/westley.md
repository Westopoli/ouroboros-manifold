# Westley

What you see, where, and the words you give.

## Where you look

`scripts/method/status.sh` from the repo, or the commit list of main on GitHub. Every `Land <id>` subject is a story landed; its trailers say which tests. `Sweep` lines are the full suite on main, nightly. Your verdicts are in `story_reviews/westley/ruled.md`; what waits on you is the table in `story_reviews/westley/README.md`; the two staircase plans sit beside it.

## Playing

- Today's main: `scripts/play.sh`. It builds the pipe, opens the game on your display and prints how long the window took.
- A story waiting for your verdict: `scripts/play.sh --story S-###` puts the game in that story's state, live, in your hands.
- No screenshots are produced for you any more (2026-10-30).

## Your words

- On a scene: **approve** or **reject**, with any note. The Architect writes it into `ruled.md`. A reject is the first item of the next plan.
- On a decision row: **veto** by id. Otherwise it stands.
- On a flag batch: **approve defaults**, or `Q-###-##: c`.
- A plan: you write the prompt, point a Fable chat at the stage, hand the plan to a Sonnet chat. Answers are never a go.
- A threshold, tolerance or pass mark: yours, by number.

## What you lose and gain

Lost (2026-11-05): the clerk, the gate per landing, the mail station, the play proof pictures; you relay between chats and judge the game by playing it. Kept: "which landing changed this test and why" is `git log --grep='^Test-defect:' -- <file>`; status computed from commits; one number a week that says whether the compute went into the game.

## The four numbers

Printed by the status script, written nightly to `~/Projects/om-push/metrics/<week>.csv`: build plus tests share of model spend (at least 50%), landings this week, stories Seen this week, Fable share (DRAFT 25%). Under 50% is a method defect the Architect reports to you with the cut it proposes.
