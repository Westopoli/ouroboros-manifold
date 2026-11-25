Fixtures for the look-rig fix tests (measured 2026-11-24). Copied from real renders and fights; nothing here is hand-edited except where noted.

- `slice_a/` L-0083 seed 1, ticks 495..512 (18 frames), full fight file (feeds the Godot test), `frame-<i>.id.png` + sidecar `frame-<i>.json` as the old sidecar wrote them (ground-point x, y).
- `slice_b/` L-0083 seed 1, a slice starting at tick 820, fight file with `seen` dropped; PNGs and sidecars for frames 5..22 only (frame index = index into `fight.json` frames).
- `slice_c/` L-0061 seed 1, ticks 600..640 (41 frames), `seen` dropped.
- `l0039_s1.fight.json.gz` L-0039 seed 1, all 2214 frames, `seen` dropped, x, y, facing rounded to 3 decimals.
