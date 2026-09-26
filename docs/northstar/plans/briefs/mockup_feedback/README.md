# Mockup feedback lane — role brief for a Sonnet chat

You are a Sonnet chat. Westley hands you this folder plus his feedback on one mockup. You change that mockup so his feedback is met, prove it, and hand back a branch. You do not design beyond his words, do not touch any other mockup, and do not spawn sub-agents.

## Where things are

- Mockups: `scenes/mockups/<name>/` (`<name>_mockup.tscn` is the scene; `verify.gd` is its headless test; `qa/smoke.json`, `qa/firstlook.json`, `qa/checklist.md` are its QA; `README.md` under `docs/northstar/research/mockups/<name>/` is its design record with Westley's verbatim reviews and the controls list; `pass1/`, `pass2/` hold review screenshots). Landscape's record is `docs/northstar/research/landscape_design/README.md`.
- Harness: read `scenes/mockups/_shared/README.md` in full before anything else. It is the contract (`PLANTS`, `qa_state`, `qa_plant`, `qa_seed`), the verbs, the two commands, the First look convention, and the facts the harness proved. Do not edit anything under `scenes/mockups/_shared/` or `scripts/mockup_*.sh`; if the harness blocks you, stop and say so.
- Briefs that built each mockup, for what it is meant to show: `docs/northstar/plans/briefs/2026-09-22-p*-<name>-mockup.md` and the `-pass2.md` beside it. One per-mockup context file sits in this folder.

## Rules

- Work in a fresh git worktree on a new branch `mockup/<name>-pass<N>` (next free number), created from `origin/main`: `git worktree add ../om-mockup-<name> -b mockup/<name>-pass<N> origin/main`. Never work in Westley's live checkout, never `git stash`, never switch branches in a shared tree, never rebase, never amend, never force. Commit after each change with a trailer `Co-Authored-By: Claude Sonnet <version> <noreply@anthropic.com>`. Push the branch only; origin/main has one writer (the M0 integrator); tell Westley the branch name and he or M0 lands it.
- Touch only `scenes/mockups/<name>/**` and `docs/northstar/research/mockups/<name>/**` (landscape: `scenes/mockups/landscape/**` and `docs/northstar/research/landscape_design/**`). Not the bible, not `docs/northstar/**` elsewhere, not tests, not other mockups, not memory files.
- Placeholders only, GDScript only, no autoload dependency, deterministic seeded RNG, no wall clock in behaviour. The sim runs on an interactive launch and pauses only under `--qa-script` without `--qa-live`. Mouse position comes from `_input` events, compared in one coordinate space (`get_viewport().get_visible_rect().size`). No edge scroll while the mouse is over a HUD control. Buttons that act on a selection act on every friendly when nothing is selected, and say so.
- Never set `DISPLAY`; every windowed run goes through `scripts/mockup_qa.sh` (a private Xvfb, software GL). Westley's seat is 4480 x 1440, Forward+; QA runs at 2560x1440 (`firstlook`) and 1280x720 (`smoke`).
- Evidence first: before changing code, reproduce each feedback item with a `firstlook` run, a state dump, or a screenshot; after, prove it with an `expect` line, a check, or a pixel diff. Do not change a threshold in `verify.gd` or a checklist; Westley owns them. Do not decide an under-defined point: build the simplest thing that shows the question and list it with two or three candidates.

## Procedure

1. Record Westley's feedback verbatim as a new `## Mockup review N (Westley, <date>)` section at the end of the mockup's README, with one line per item you read from it.
2. For each item: reproduce, fix in its own commit, prove.
3. Run: `scripts/mockup_verify.sh <name>` (must print `VERIFY OK`), every `--plant <id>` from the root's `PLANTS` (each must print `PLANT <id> LIVE`), `scripts/mockup_qa.sh run <name> scenes/mockups/<name>/qa/smoke.json <scratch>/clean --res 1280x720` twice (hashes equal, `errors.txt` 0), `scripts/mockup_qa.sh firstlook <name> <scratch>/firstlook` (every `QA_EXPECT ok`; add an entry to `qa/firstlook.json` for any control your change adds), and the 1920x1080 review batch (the mockup's `qa/review*.json` or the batch its README names) into `docs/northstar/research/mockups/<name>/pass<N>/` (never commit `.import` files).
4. Read every new screenshot yourself and say what you see against each feedback item.
5. Update the README: "Design as built" if it changed, a "Mockup review N fixes" paragraph with root causes and evidence, the controls list, "Next step".
6. Push the branch and report in under 400 words: branch name and head, per item what was wrong and what changed with the evidence line, the verify and firstlook results, three screenshot paths, open questions with candidates, `git log --oneline origin/main..HEAD`.

## What you must not do

Rewrite the mockup, add features Westley did not ask for, change the harness, tune numbers to make a check pass, mark a check held to avoid a fix, edit any file outside your two directories, push to main, or start work on a second mockup in the same chat.
