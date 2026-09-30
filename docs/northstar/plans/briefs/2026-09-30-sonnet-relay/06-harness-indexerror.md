# Spec 06: the QA harness's `stuck: IndexError` (Agora harness)

You are a Claude Sonnet 4.6 worker chat. You execute this spec directly. You do not spawn agents, redesign, or widen scope. This is a bug investigation followed by one targeted fix, in the **Agora** repo (`~/Projects/agora`).

## Why

Between 17:00 and 21:45 on 2026-09-29, 44 QA sessions logged `stuck: IndexError` on 347 of 2,640 turns (13%), in every session. The hits are `click` actions on buttons in the galaxy, debrief, briefing and chronicle screens, plus `fill` actions on text boxes and combo boxes. Each hit wastes a turn and bans the target for five turns, so the QA spends part of every session unable to act. The harness swallows the exception and logs only its type, so nobody knows where it comes from.

## Where

```
cd ~/Projects/agora && git fetch origin && git worktree add ~/Projects/relay-06 -b relay/06-indexerror origin/main
cd ~/Projects/relay-06
```
Python: `~/Projects/agora/.venv/bin/python`, `.venv/bin/pytest`. The dispatcher keeps running from `main`; do not stop it. Do not stage `campaigns/`, `runs/`, `digest/` or `.claude/` files.

## Files you may edit

- `scripts/qa_explore.py`
- `scripts/qa_desktop.py`
- `scripts/qa_tactical.py`
- one new or existing test file under `tests/`

If the root cause is elsewhere, stop at diagnosis and report it.

## Method

Hypothesis, then evidence, then one fix. Do not fix by wrapping more code in `try`.

1. **Make the error visible.** In `scripts/qa_explore.py`, the two `except Exception as e:` sites that produce `outcome = f"stuck: {type(e).__name__}"` (around lines 471 and 518) discard the traceback. Add the last traceback frame to the outcome string, e.g. `stuck: IndexError at qa_desktop.py:412 in _target` (use `traceback.extract_tb(e.__traceback__)[-1]`), and keep that change: it is diagnostic and stays. Check `tests/` for a test that asserts the exact `stuck: <Type>` string and update its expectation only if it asserts the full string (prefer `startswith` in the assertion).
2. **Reproduce.** Run one short session from your worktree: `.venv/bin/python scripts/qa_explore.py --profile projects/ouroboros/qa.toml --actions 25` (see `--help`; add `--project` if the profile requires it). Read its `session.jsonl`. You will likely see the new outcome string within the first galaxy or briefing turns. If a live run is impractical, reproduce offline: the actions that failed are in `~/Projects/agora/runs/qa-20260929-2143/session.jsonl` (turns 12, 13, 15 for example); feed the same `(action, role, name)` through the desktop backend's target resolution against the daemon's `tree` output, which the backend caches per turn.
3. **Localise.** With the frame in hand, read that function. Likely candidates, in no order: `_target()` or the control lookup in `scripts/qa_desktop.py` indexing an empty list when a control name matches nothing or matches twice; `rect_px[...]` on a control whose rect is missing; a list index on the `Battlefield` targets in `scripts/qa_tactical.py` when the tactical state is empty. State the root cause in one paragraph with the file and line.
4. **Fix once.** The fix must make the action either succeed or produce a meaningful outcome (`stuck: no control named X` rather than an exception). Write one regression test under `tests/` that reproduces the failing input shape (the same tree/state that made the index fail) and passes after the fix.
5. `.venv/bin/pytest tests/ -q`. Record the summary line and any pre-existing failures by name.
6. `git add` the edited files by name, commit in plain prose ending `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`, `git push origin relay/06-indexerror`. Stop.

## Report (your last message, nothing after it)

```
Branch: relay/06-indexerror (commit <hash>)
Root cause: <one paragraph, file:line>
Fix: <one or two lines>
Regression test: <test name>
Tests: <pytest summary line>
Open: <anything, or "none">
```
