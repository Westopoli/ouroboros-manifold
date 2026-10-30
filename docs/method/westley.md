# Westley

What you see, where, and the words you give.

## Where you look

`scripts/method/status.sh` from the repo, or the commit list of main on GitHub. Every `Land S-###` subject is a story landed; its trailers say which tests, which scene, when it was played and how long the gate took. `Seen S-###` is your verdict. A subject ending `(stub)` landed a placeholder scene, and the status script says so beside it. `Sweep` lines are the full suite on main. There is no lane table, no pieces table, no ledger, no review queue, no README of shots. `decisions.md` and `stories.md` stay.

## Playing

- Today's main: `scripts/play.sh`. It builds the pipe, opens the game on your display and prints how long the window took.
- A story waiting for your verdict: `scripts/play.sh --story S-###` puts the game in that story's state, live, in your hands. The status script lists them oldest first with the story's words beside each run line.
- No screenshots are produced for you any more (2026-10-30).

## Your words

- On a scene: **approve** or **reject**, with any note. A clerk commits it. A reject goes to the Architect as a fix.
- On a decision row: **veto** by id. Otherwise it stands.
- On a flag batch: **approve defaults**, or `Q-###-##: c`.
- On a story that ends in a frame or changes a rule: **go** on its story file before it builds. Nothing else needs your go.
- **pause** and **go** for the whole loop. Answers are never a go.
- A threshold, tolerance or pass mark: yours, by number.

## What you lose and gain

Lost: the per-piece paper trail; "which landing changed this test and why" is now `git log --grep='^Test-defect:' -- <file>`. The method metrics drop from 24 to 4. The drift audit runs when you ask. Gained: status that cannot drift from reality, because it is computed from the commits that are the reality; a spec you read in one page; one number a week that says whether the compute went into the game.

## The four numbers

Printed by the status script, written nightly to `docs/method/metrics/<week>.csv`: build plus tests share of model spend (at least 50%), landings this week, stories Seen this week, Fable share (DRAFT 25%). Under 50% is a method defect the Architect reports to you with the cut it proposes.
