# Spec 07: two visual checks on the QA's screenshots (Agora harness)

You are a Claude Sonnet 4.6 worker chat. You execute this spec directly. You do not spawn agents, redesign, or widen scope. This is in the **Agora** repo (`~/Projects/agora`).

## Why

The QA takes a screenshot after every action and never looks at it. Of the 2,326 screenshots from 2026-09-29 17:00 to 21:45, 582 are one flat colour, and session `qa-20260929-2143` has 36 identical frames in a row (shots 22 to 57) while the QA clicked Deploy behind a modal that said "Chronicle review will be available after backend integration"; every one of those clicks was logged `ok`. Two deterministic checks catch both: a blank frame, and a frozen screen. Each is a finding about the game, because the game really showed nothing, or really stopped responding. Every detector ships with a positive control, and thresholds below are Westley's to change, not yours.

## Where

```
cd ~/Projects/agora && git fetch origin && git worktree add ~/Projects/relay-07 -b relay/07-visual-checks origin/main
cd ~/Projects/relay-07
```
Python: `~/Projects/agora/.venv/bin/python`, `.venv/bin/pytest`. Pillow is installed in that venv. The dispatcher keeps running from `main`. Do not stage `campaigns/`, `runs/`, `digest/` or `.claude/` files.

Control images (read-only, copy the ones you need into `tests/fixtures/visual/`):
- Blank positive: `~/Projects/agora/runs/qa-20260929-2143/shot-1.png` (1,022 bytes, flat dark grey).
- Blank negative: `~/Projects/agora/runs/qa-20260929-2143/shot-2.png` (the main menu).
- Frozen positive: `~/Projects/agora/runs/qa-20260929-2143/shot-22.png` through `shot-57.png` (identical).
- Frozen negative: `shot-2.png` through `shot-11.png` of the same run (they vary).

## Files you may edit

- `scripts/qa_visual.py` (new: the two pure checks, no I/O beyond opening an image path)
- `scripts/qa_desktop.py` (only `_after_action`, to call the checks and emit events)
- `scripts/qa_oracle.py` (only `classify`, to turn the two new event kinds into findings)
- `tests/test_qa_visual.py` (new) and `tests/fixtures/visual/` (new, the control images)

Nothing else. Read `scripts/qa_liveness.py` and `scripts/qa_oracle.py` first: `classify(event)` already maps event kinds (`console-error`, `pageerror`, `http-5xx`, `json-not-page`) to `Finding` objects with `detector`, `url`, `evidence`, `role`; `fingerprint()` normalises the evidence. The desktop backend already has `_emit(kind, payload)` and `on(kind, handler)`; the session registers `classify` on the event kinds it knows. Find where that registration happens (grep `page.on(` in `scripts/qa_explore.py` or `scripts/qa_session.py`) and add the two new kinds there.

## The checks (`scripts/qa_visual.py`)

```python
BLANK_RANGE_MAX = 8        # grayscale max minus min; below this the frame is one colour (Westley's threshold)
FROZEN_RUN = 10            # identical consecutive frames before "frozen" fires (Westley's threshold)

def is_blank(path: str) -> bool
    # Open with Pillow, convert("L"), getextrema(); blank when hi - lo < BLANK_RANGE_MAX.
    # An unreadable file returns False (never raises): a capture failure is the liveness guard's business.

def frame_hash(path: str) -> str
    # sha1 of the PNG bytes. Unreadable file: "<unreadable>".

class FrozenTracker:
    # observe(hash, outcome_ok: bool) -> bool
    # Keeps the current run length of identical hashes seen while outcome_ok is True.
    # Returns True exactly once per run, when the length first reaches FROZEN_RUN; a
    # different hash or a non-ok outcome resets the run. A run that continues past
    # FROZEN_RUN does not fire again (one finding per freeze).
```

## Wiring

- `qa_desktop.py` `_after_action`: after the `import` capture, if the file exists: `if qa_visual.is_blank(path): self._emit("blank-frame", {"url": <current scene url as other events use>, "text": f"blank frame shot-{self._turn}.png"})`. Then `if self._frozen.observe(qa_visual.frame_hash(path), self._last_outcome_ok): self._emit("frozen-screen", {"url": ..., "text": f"screen unchanged for {FROZEN_RUN} actions ending shot-{self._turn}.png"})`. You will need to know whether the last action's outcome was `ok`; find where the backend learns the outcome (or default `True` and note it under Open if the backend never sees outcomes).
- `qa_oracle.classify`: map `blank-frame` to `Finding(detector="blank-frame", ...)` and `frozen-screen` to `Finding(detector="frozen-screen", ...)`, evidence = the `text` payload. Fingerprints must not include the shot number (the normaliser already strips digits; confirm with a test that two blank frames on the same scene share a fingerprint).
- A blank frame on the privacy modal happens on every boot today (shot-1 of every session). That is still a finding; do not special-case it. It will converge to one fingerprint.

## Tests (`tests/test_qa_visual.py`)

1. `is_blank` is True for the blank positive control, False for the negative.
2. `FrozenTracker` fires once on the 10th identical hash with ok outcomes, not on the 9th, not again on the 11th, and resets on a different hash or a non-ok outcome.
3. Replay: hashing the frozen positive control sequence (shots 22 to 57, or the 12 copies you put in fixtures; keep fixtures small, 12 files is enough) fires exactly once; the negative sequence never fires.
4. `classify({"kind": "blank-frame", ...})` returns a Finding with `detector == "blank-frame"`, and two such events on the same scene fingerprint identically.

## Checks

- `.venv/bin/pytest tests/test_qa_visual.py -q` all pass.
- `.venv/bin/pytest tests/ -q` summary line, pre-existing failures by name.
- Optional if cheap: one live session (`.venv/bin/python scripts/qa_explore.py --profile projects/ouroboros/qa.toml --actions 15`) whose `session.jsonl` shows a `blank-frame` finding on turn 1.

## Steps to finish

`git add` the edited and new files by name (fixtures included), commit in plain prose ending `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`, `git push origin relay/07-visual-checks`. Stop.

## Report (your last message, nothing after it)

```
Branch: relay/07-visual-checks (commit <hash>)
Files: <list>
Tests: <the two pytest summary lines>
Outcome source: <how _after_action learns the last outcome, or "defaulted to True">
Live: <finding seen on turn 1, or "not run">
Open: <anything, or "none">
```
