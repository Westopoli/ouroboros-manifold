# PX-02 — Actor vocabulary and pause/step (proving the factory)

Run 2026-09-19 against the probe-D toy scene on a private Xvfb with the real Godot 4.6.3 binary (agora `c0ffc46`, toy scene `b247fdf`).

Claim (A4 §2): the actor vocabulary must include `press`, `drag`, `wait` (tick-step, not wall-clock), `read_state`, `screenshot`; the desktop protocol must support `pause` / `step <n>` so a real-time game never waits on a slow model; a directive needing a verb the mission does not allow must fail as a harness condition, never be silently downgraded to a click.

Result: **pass**.

- Vocabulary: `ACTION_VERBS` grew from six web verbs to eleven; schema fields added; dispatch wired. RED first: nine of ten vocabulary tests failed by falling through to click, the exact "silent downgrade" that produced the 2026-09-14/15 "L key never toggles" false positives.
- Protocol: `pause`, `resume`, `step <n>`, `drag x1 y1 x2 y2`, and an `unsupported` reply documented in `docs/desktop-qa-protocol.md`.
- Live run: `press l` → `layer: 2`; `pause` → `paused: true`; `step 3` → `tick: 3` while still paused (state polled before `resume`); `drag` across the dot → `last_drag_start`/`last_drag_end` populated from real xdotool coordinates.
- Control: with `press` removed from `allowed_actions`, `guard_action` rejected the directive ("action 'press' not allowed"); the layer stayed 1 and no finding was recorded. No new exception class was needed: the existing membership check covers every new verb once it is in the vocabulary.
- Suite: agora 883 passed, the 13 pre-existing failures, plus PX-03's in-flight test file; zero regressions from this change.

Found along the way, worth carrying into the game-side hook: Godot's default `mouse_filter = STOP` on the root Control and on the Dot swallowed every synthetic mouse-button event before `_unhandled_input` saw it; drag reported nothing until both were `MOUSE_FILTER_IGNORE`. The debug daemon node runs with `PROCESS_MODE_ALWAYS` so `step` is answered during pause.

Design consequence: none beyond confirming; the `unsupported` reply is the mechanism by which a non-game target implements only the subset it has.
