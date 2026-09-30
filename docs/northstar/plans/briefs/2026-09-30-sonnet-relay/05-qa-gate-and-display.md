# Spec 05: the QA plays whole matches at 1080p (Agora harness)

You are a Claude Sonnet 4.6 worker chat. You execute this spec directly. You do not spawn agents, redesign, or widen scope. This spec is in the **Agora** repo (`~/Projects/agora`), the harness that drives the local 30B model through the game as a QA player.

## Why

Missions are now 30 to 60 minutes of battle (E-10 R-076-02). The QA ends every mission after about one second, because its End Mission gate opens at 20 mission ticks or 8 orders, and the tick side of the gate never counts (every session log shows `0/20 mission ticks played` even after several orders), so 8 orders is the real gate. Westley's decisions (2026-09-29): the QA may press End Mission only after **10 minutes** of battle; a session may play a whole match; the QA runs at **1920x1080**, his screen. Playing the full match is a real player experience and is wanted.

## Where

`~/Projects/agora` is a git repo with a running dispatcher (`agora-dispatcher.service`) that starts a QA session every few minutes from the working tree. Work on a branch in a separate worktree so the dispatcher keeps running from `main`:
```
cd ~/Projects/agora && git fetch origin && git worktree add ~/Projects/relay-05 -b relay/05-qa-gate origin/main
cd ~/Projects/relay-05
```
Python: `~/Projects/agora/.venv/bin/python` and `.venv/bin/pytest`. Do not restart or stop the dispatcher. Do not stage `campaigns/`, `runs/`, `digest/` or `.claude/` files; they are the dispatcher's.

## Files you may edit

- `scripts/qa_tactical.py` (the gate)
- `scripts/next.py` (the per-session action budget, two call sites)
- `scripts/qa_desktop.py` (the Xvfb screen size)
- `projects/ouroboros/qa.toml` (the Godot launch resolution)
- `tests/test_qa_tactical.py` (the gate's tests; you may change them because this spec changes the rule they encode, and Westley set the new numbers)

Nothing else. The game repo (`~/Projects/om-push/qa`, `~/Projects/ouroboros-manifold`) is read-only for you.

## Part A: the gate

In `scripts/qa_tactical.py`:
- `END_MISSION_TURN_THRESHOLD = 20` becomes `12000` base ticks (10 minutes at 20 ticks per second). Rename nothing; update its comment to say "10 minutes of battle at 20 base ticks/s (Westley 2026-09-29)".
- Remove the order-count alternative: `end_mission_banned` lifts only on ticks. Delete `END_MISSION_ORDER_THRESHOLD` if nothing else reads it (grep). The gate may keep counting orders for the message, but orders no longer unlock End Mission.
- `end_mission_ban_reason` message becomes: `EndMission withheld: {minutes_played:.1f}/10.0 minutes of battle played -- keep playing; the mission ends on its own by the clock, the objective, or your force being destroyed.`
- Update `tests/test_qa_tactical.py`: `test_end_mission_banned_until_20_ticks_or_8_orders` and `test_end_mission_lifts_early_on_8_orders` become tests of the new rule (banned below 12000 ticks regardless of orders; lifts at 12000). Rename them to say what they prove.

## Part B: the session budget

`scripts/next.py` passes `"--actions", "60"` at two call sites (around lines 978 and 1179). A session turn takes about 4 seconds of wall time, so 60 actions is about 4 minutes. Change both to `"900"` (about an hour, enough for a 60-minute mission plus the menus). Nothing else in `next.py` changes.

## Part C: the display

- `scripts/qa_desktop.py` around line 105: `"1024x768x24"` becomes `"1920x1080x24"`.
- `projects/ouroboros/qa.toml`: `"--resolution", "1280x720"` becomes `"--resolution", "1920x1080"`. The game's `project.godot` already sets a 1920x1080 viewport.
- Grep both repos' harness side (`scripts/`, `projects/ouroboros/`) for `1024`, `768`, `1280`, `720`, and for hard-coded click coordinates that assumed the old size (the profile text mentions "Accept & Continue at approximately (640, 410)"). Report every hit; fix only those in files you may edit, and only when the value is clearly the window size. The privacy modal's coordinates are found live from the control tree, so the prose hint may be left as is.

## Part D: why the tick count never moves (investigate, then fix if it is harness-side)

Method: hypothesis first, then evidence, then one fix.

Evidence to start from: `~/Projects/agora/runs/qa-20260929-2143/session.jsonl` shows attack-moves on tactical turns 6 to 8 and then `EndMission ... ok` at turn 9, with the gate having read `0/20` ticks at turn 5. The game's tactical scene reports its tick in `qa_state()["tick"]` (`~/Projects/om-push/qa/scenes/tactical_c/tactical_view.gd`, function `qa_state`, key `tick` from `_frame`). The gate reads `qa.get("tick", 0)` in `update_tactical_gate` (`scripts/qa_tactical.py` around line 229), where `qa` is built by `scripts/qa_explore.py` (search for `update_tactical_gate` there).

Two hypotheses, test them in order:
1. `qa_explore.py` passes the daemon's top-level `state()` dict, whose `tick` comes from a dead `TacticalBridge` autoload, instead of `state()["qa"]` from the scene. Check what dict reaches `update_tactical_gate` and what key holds the scene's tick.
2. The scene's `_frame` has the tick under another key (`base_tick`, `step`, or similar), so `_frame.get("tick", 0)` is always 0. Check the tactical frame the C pipe writes (`~/Projects/om-push/qa/csrc/pipe/om_pipe.c`, search `"tick"` near the tactical frame writer) against `tactical_view.gd`.

Confirm with a short live probe rather than reasoning alone: `~/Projects/agora/.venv/bin/python scripts/qa_explore.py --profile projects/ouroboros/qa.toml --actions 12` from your worktree (check `qa_explore.py --help` for the exact flags; the run directory it prints holds `session.jsonl`), and read what the gate message says after a few orders. If the fix is in a file you may edit, make it, with one regression test in `tests/test_qa_tactical.py` that feeds the real shape of the state dict. If the fix is in the game (`tactical_view.gd` or the pipe), do not make it: describe it under Open in the report, with the file and line.

## Checks

- `.venv/bin/pytest tests/test_qa_tactical.py tests/test_qa_desktop.py tests/test_next_qa_desktop_dispatch.py -q` all pass.
- `.venv/bin/pytest tests/ -q` summary line (pre-existing failures, if any, listed by name).
- The live probe's run directory: `shot-1.png` is 1920x1080 (`python -c "from PIL import Image; print(Image.open('<run>/shot-1.png').size)"`), and the gate message shows minutes counting up once the mission is running, or Part D's finding explains why not.

## Steps to finish

`git add` the edited files by name, commit in plain prose ending `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`, `git push origin relay/05-qa-gate`. Stop.

## Report (your last message, nothing after it)

```
Branch: relay/05-qa-gate (commit <hash>)
Files: <list>
Tests: <the two pytest summary lines>
Probe: <screenshot size; gate message text after the probe's last tactical turn>
Part D: <hypothesis confirmed (1 or 2 or other), evidence in one or two lines, fixed or not>
Display grep: <hits and what you did with each>
Open: <anything, or "none">
```
