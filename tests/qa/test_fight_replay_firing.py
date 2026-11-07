# spec: bug H-088 replay-firing-lines (Westley's replay recording, 2026-11-07): the replay drew a target line from every unit with a `target`, even one still walking toward it
# Rule pins: none (lab harness story H-088)
"""H-088 replay-firing-lines, part B: `scenes/proto/fight_replay/fight_replay.gd` draws a unit's target line only when the unit's row has `fired` true.

FL-1 a unit row with `fired` true and a target (alive in the frame) is drawn with its line; `fired` false: no line.
FL-2 a row with no `fired` key (a file from before the key) draws the line as before: every living unit with a target.
FL-3 `qa_state()` gains `firing_lines`: [[unit id, target id]] of the lines actually drawn on the current frame; the existing `targets` (all living units with a target) is unchanged.
FL-4 a unit that fired and has no target draws no line (nothing to draw to), so it is not in `firing_lines`.

The drawn lines are scene nodes the harness cannot count, so `firing_lines` is the seam (as `targets`, `rings` and `hollow_units` are for the other marks). Launcher and helpers are
those of tests/qa/test_fight_replay.py (xvfb, software GL, qa-port). The fight is `snapshot.example(frames=3)` (ids 1, 2 side A, 3, 4 side B) written raw, with targets and `fired`
set per frame as FRAMES says; `fired` is stripped for the older-file case. Whether a line to a target that died in the same window is drawn is not pinned (the fixture avoids it).
Positive control (green today): the fixture's `targets` per frame are those of FRAMES and extra `fired` keys do not stop the scene opening."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_fight_replay import _key, _open, _state, _write_fight  # noqa: E402
from scripts.skilllab.arena import snapshot  # noqa: E402

# per frame: {unit id: (target id or None, fired)} for the living units; frame 2 has side B dead (the example's last frame)
FRAMES = [
    {1: (3, False), 2: (4, True), 3: (1, False), 4: (2, True)},    # 1 and 3 are walking toward a target; 2 and 4 fired
    {1: (3, True), 2: (None, False), 3: (1, False), 4: (2, False)},
    {1: (None, False), 2: (None, True)},                            # unit 2 fired and has no target: no line
]
TARGETS = [[[1, 3], [2, 4], [3, 1], [4, 2]], [[1, 3], [3, 1], [4, 2]], []]
FIRING = [[[2, 4], [4, 2]], [[1, 3]], []]


def fight(tmp_path, keep_fired=True):
    """(path, doc): the three-frame example with `target` and `fired` per FRAMES; `keep_fired` False leaves `fired` out of every row (an older file)."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    for f, spec in zip(doc["frames"], FRAMES):
        for u in f["units"]:
            target, fired = spec.get(u["id"], (None, False))
            u["target"] = target
            if keep_fired:
                u["fired"] = fired
    path = _write_fight(tmp_path / ("L-0001-s1%s.fight.json" % ("" if keep_fired else "-old")), doc)
    return path, doc


def lines_per_frame(monkeypatch, path):
    """[(targets, firing_lines)] of qa_state for frames 0 to 2, stepping with Space; each list sorted. A missing `firing_lines` key reads as None."""
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        out = []
        for i in range(3):
            qa = _state(g, lambda q, i=i: q.get("frame") == i, timeout=15.0, label="frame %d" % i)["qa"]
            fl = qa.get("firing_lines")
            out.append((sorted(qa["targets"]), None if fl is None else sorted(fl)))
            if i < 2:
                _key(g, "Space")
        return out
    finally:
        g.stop()


def test_control_the_fixture_opens_and_targets_are_all_living_units_with_a_target(tmp_path, monkeypatch):
    """CONTROL (green today, must stay green), FL-3 "`targets` stays unchanged": the file with `fired` keys opens and `targets` on frames 0 to 2 are every living unit with a target,
    whether or not it fired."""
    path, _ = fight(tmp_path)
    assert [t for t, _ in lines_per_frame(monkeypatch, path)] == TARGETS


def test_fl1_fl3_firing_lines_are_the_units_that_fired_with_a_target(tmp_path, monkeypatch):
    """FL-1 / FL-3 / FL-4 ("a unit's target line is drawn only when its row has `fired` true"; "qa_state gains `firing_lines`: [[unit id, target id]] of the lines actually drawn"):
    on frames 0 to 2 `firing_lines` is FIRING: frame 0 only units 2 and 4 (1 and 3 have targets and did not fire), frame 1 only unit 1, frame 2 none (unit 2 fired with no target)."""
    path, _ = fight(tmp_path)
    assert [fl for _, fl in lines_per_frame(monkeypatch, path)] == FIRING


def test_fl2_a_file_without_fired_draws_every_target_line(tmp_path, monkeypatch):
    """FL-2 ("A row with no `fired` key (older file) draws the line as before"): the same file with `fired` removed from every row has `firing_lines` equal to `targets` on every
    frame (and not missing: the key is reported all the same)."""
    path, doc = fight(tmp_path, keep_fired=False)
    assert all("fired" not in u for f in doc["frames"] for u in f["units"])
    got = lines_per_frame(monkeypatch, path)
    assert [fl for _, fl in got] == TARGETS and [t for t, _ in got] == TARGETS


def test_fl2_rows_without_fired_among_rows_with_it_still_draw(tmp_path, monkeypatch):
    """FL-2 per row (a row with no key draws as before, the rule is per row): on frame 0 units 1 and 3 lose their `fired` key (they had it false); the lines are those of
    units 2 and 4 (fired true) and of 1 and 3 (no key), i.e. all four, while on frame 1 the rows that keep `fired` false stay undrawn."""
    path, doc = fight(tmp_path)
    for u in doc["frames"][0]["units"]:
        if u["id"] in (1, 3):
            del u["fired"]
    path = _write_fight(tmp_path / "L-0001-s1-mixed.fight.json", doc)
    got = lines_per_frame(monkeypatch, path)
    assert [fl for _, fl in got] == [TARGETS[0], FIRING[1], FIRING[2]]
