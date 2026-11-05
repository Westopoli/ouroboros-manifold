# spec: docs/northstar/plans/cascades/lab-stage4/spec.md::Acceptance criteria::AC-7
# Rule pins: none (lab harness story H-088)
"""lab-stage4 leaf-02, criteria 7 to 9 (spec lines 29 to 31): the replay shows sight (scenes/proto/fight_replay/fight_replay.gd).

7: sight discs: with `sights` in the fight file, one disc per role per side on the same tick-0 unit the role ring uses, radius `sights[role]`, key V toggles the disc to every
   living unit (as R does for rings); a file without `sights` draws none. `qa_state()` gains `sight_rings` ({side, role, radius, centre}, as `rings`) and `sight_mode`.
8: hollow marks: a living unit that no living unit of the other side lists in `seen` is drawn hollow; a frame without `seen` keys draws nobody hollow. `qa_state()` gains
   `hollow_units` (sorted ids).
9: the tick line is `tick %d  A %d  B %d  blocked %d  A sees %d  B sees %d  frame %d/%d` (a frame without `seen` keys prints the stage 3 line unchanged); the last frame's
   end line gains `first seen A <tick|never>  B <tick|never>` from `result.first_seen`. `qa_state()` gains `hud_sight` and `seen_counts` ([a, b]).

Launcher and helpers are those of tests/qa/test_fight_replay.py (xvfb, software GL, qa-port); the fight files are hand-written JSON (not run through the arena, and written
raw so the checker's keys do not matter here), staged from the 24-unit file of test_fight_replay_readability.py (ids 1 to 12 side A, 13 to 24 side B, three frames, winner A).
The disc alpha (DRAFT-sight-alpha 0.25) and the hollow alpha (DRAFT-hollow-alpha 0.35) are not in qa_state, so how a disc and a hollow body look is a look for Westley
(BOUNDARIES.md); what is tested is which discs and which units, and the HUD text."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_fight_replay import _hud_lines, _key, _open, _state, _write_fight  # noqa: E402
from test_fight_replay_readability import RANGES, ROLES, _fight  # noqa: E402

SIGHTS = {"Raider": 800.0, "Interceptor": 1000.0, "Vanguard": 700.0, "Warden": 800.0, "Bombard": 300.0, "Bastion": 300.0}
ALL = list(range(1, 25))
TICK = "tick %d  A %d  B %d  blocked 0  A sees %d  B sees %d  frame %d/3"
STAGE3_TICK = "tick %d  A %d  B %d  blocked %d  frame %d/%d"


def sight_fight(tmp_path, sights=True, seen=True, first_seen=None, drop_range=None, drop_sight=None):
    """(path, doc): the 24-unit fight with `sights` (the six radii), per-unit `seen` and `result.first_seen`, as asked (`drop_range` takes that role out of the file's `ranges`, `drop_sight` out of its `sights`). `seen`: frame 0 unit 1 lists enemies 13 and 14,
    unit 2 lists 14, unit 13 lists 1, nobody else lists any (so A sees 2 units, B sees 1); frame 1 nobody lists any; frame 2 (B all dead) nobody lists any except the dead
    unit 13, which lists 1 (a stale list of a dead unit: a dead unit is not an observer)."""
    path, doc = _fight(tmp_path)
    if sights:
        doc["sights"] = dict(SIGHTS)
    if drop_range:
        del doc["ranges"][drop_range]
    if drop_sight:
        del doc["sights"][drop_sight]
    if seen:
        for f in doc["frames"]:
            for u in f["units"]:
                u["seen"] = []
        lists = {0: {1: [13, 14], 2: [14], 13: [1]}, 2: {13: [1]}}
        for n, ids in lists.items():
            for u in doc["frames"][n]["units"]:
                u["seen"] = ids.get(u["id"], [])
    if first_seen is not None:
        doc["result"]["first_seen"] = first_seen
    return _write_fight(path, doc), doc


def frames_at(g, wanted):
    """{frame index: full state} for the frames in `wanted` (ascending), stepping with Space."""
    out = {}
    for i in range(max(wanted) + 1):
        st = _state(g, lambda q, i=i: q.get("frame") == i, timeout=15.0, label="frame %d" % i)
        if i in wanted:
            out[i] = st
        if i < max(wanted):
            _key(g, "Space")
    return out


def launched(monkeypatch, path):
    g = _open(monkeypatch, path)
    g.wait_for_port(timeout=90.0)
    return g


# ---------------------------------------------------------------- criterion 7: sight discs

def test_sight_discs_are_one_per_role_per_side_on_the_role_ring_anchor_and_v_toggles(tmp_path, monkeypatch):
    """Criterion 7, spec line 29: with `sights` in the file `qa_state().sight_rings` has one entry per role per side (12), each with the file's radius for the role, on
    the same centre as the role ring of that side and role (`rings`); `sight_mode` is "role" at the start, "unit" after key V, "role" after V again."""
    path, _ = sight_fight(tmp_path)
    g = launched(monkeypatch, path)
    try:
        qa = _state(g)["qa"]
        discs = sorted((r["side"], r["role"], r["radius"], tuple(r["centre"])) for r in qa.get("sight_rings", []))
        rings = sorted((r["side"], r["role"], SIGHTS[r["role"]], tuple(r["centre"])) for r in qa["rings"])
        modes = [qa.get("sight_mode")]
        for _ in range(2):
            _key(g, "V")
            modes.append(_state(g)["qa"].get("sight_mode"))
        assert (len(discs), discs == rings, modes) == (12, True, ["role", "unit", "role"])
    finally:
        g.stop()


def test_a_role_in_sights_but_not_in_ranges_draws_no_disc(tmp_path, monkeypatch):
    """Criterion 9, last sentence (spec line 31): a role present in `sights` but absent from `ranges` has no anchor unit (no role ring) and draws no disc: `sight_rings` lists
    the other five roles on each side (10 entries, none for Bombard), on the centres of the 10 role rings."""
    path, _ = sight_fight(tmp_path, drop_range="Bombard")
    g = launched(monkeypatch, path)
    try:
        qa = _state(g)["qa"]
        discs = sorted((r["side"], r["role"], r["radius"], tuple(r["centre"])) for r in qa.get("sight_rings", []))
        rings = sorted((r["side"], r["role"], SIGHTS[r["role"]], tuple(r["centre"])) for r in qa["rings"])
        assert (len(discs), discs == rings, [d for d in discs if d[1] == "Bombard"]) == (10, True, [])
    finally:
        g.stop()


def test_key_v_draws_a_sight_disc_under_every_living_unit_and_v_again_returns_to_the_role_discs(tmp_path, monkeypatch):
    """Criterion 9, spec line 31 (ruling Y7): key V sets `sight_mode` "unit" and `sight_rings` then holds one {side, role, radius, centre} per living unit, the centre the unit's
    position and the radius `sights[role]` (frame 0: all 24 units; frame 2, side B dead: the 12 units of A); V again returns `sight_mode` "role" and the 12 role discs."""
    path, doc = sight_fight(tmp_path)
    g = launched(monkeypatch, path)
    try:
        discs = lambda qa: sorted((r["side"], r["role"], r["radius"], tuple(round(v, 1) for v in r["centre"])) for r in qa.get("sight_rings", []))
        living = lambda n: sorted((u["side"], u["role"], SIGHTS[u["role"]], (round(u["x"], 1), round(u["y"], 1))) for u in doc["frames"][n]["units"] if u["alive"])
        _key(g, "V")
        qa0 = _state(g)["qa"]
        _key(g, "Space")
        _key(g, "Space")
        qa2 = _state(g, lambda q: q.get("frame") == 2, timeout=15.0, label="frame 2")["qa"]
        _key(g, "V")
        back = _state(g)["qa"]
        assert (qa0.get("sight_mode"), discs(qa0) == living(0), len(discs(qa0))) == ("unit", True, 24)
        assert (discs(qa2) == living(2), len(discs(qa2))) == (True, 12)
        assert (back.get("sight_mode"), len(back.get("sight_rings", []))) == ("role", 12)
    finally:
        g.stop()


def test_a_role_in_ranges_but_not_in_sights_draws_no_sight_disc(tmp_path, monkeypatch):
    """Criterion 9, spec line 31 (ruling Y7): a role present in `ranges` but absent from `sights` draws no sight disc: with Bombard taken out of `sights` the role rings are still
    12 (the role is in `ranges`) and `sight_rings` lists the other five roles on each side (10 entries), none for Bombard."""
    path, _ = sight_fight(tmp_path, drop_sight="Bombard")
    g = launched(monkeypatch, path)
    try:
        qa = _state(g)["qa"]
        discs = sorted((r["side"], r["role"]) for r in qa.get("sight_rings", []))
        assert (len(qa["rings"]), len(discs), [d for d in discs if d[1] == "Bombard"]) == (12, 10, [])
    finally:
        g.stop()


def test_a_file_with_sights_but_no_seen_draws_the_discs_and_no_hollow_unit(tmp_path, monkeypatch):
    """Criterion 7 and 8: a fight file with `sights` and no `seen` key anywhere still lists its 12 discs, "a frame without `seen` keys draws nobody hollow", and `hud_sight` is `""` there."""
    path, _ = sight_fight(tmp_path, seen=False)
    g = launched(monkeypatch, path)
    try:
        qa = _state(g)["qa"]
        assert (len(qa.get("sight_rings", [])), qa.get("hollow_units"), qa.get("hud_sight")) == (12, [], "")
    finally:
        g.stop()


def test_a_file_without_sights_draws_no_disc(tmp_path, monkeypatch):
    """Criterion 7, spec line 29: "a file without `sights` draws none": `sight_rings` is `[]` (the file has `seen`, so the units are judged for hollow marks all the same)."""
    path, _ = sight_fight(tmp_path, sights=False)
    g = launched(monkeypatch, path)
    try:
        qa = _state(g)["qa"]
        assert (qa.get("sight_rings"), qa.get("sight_mode"), qa.get("hollow_units")) == ([], "role", sorted(set(ALL) - {1, 13, 14}))
    finally:
        g.stop()


# ---------------------------------------------------------------- criterion 8 and 9: hollow marks, counts, HUD

def test_hollow_units_are_the_living_units_no_living_enemy_lists(tmp_path, monkeypatch):
    """Criterion 8, spec line 30, and the `seen_counts` of criterion 9: frame 0, the units seen are 13 and 14 (listed by unit 1, 2) and 1 (listed by 13), so every other
    living unit is hollow and the counts are [2, 1] (a union: 14 is listed twice); frame 1, nobody lists anyone: all 24 hollow, [0, 0]; frame 2, side B is dead: a dead
    unit is not hollow, and unit 1 stays hollow although the dead unit 13 lists it (a dead unit is not an observer)."""
    path, _ = sight_fight(tmp_path)
    g = launched(monkeypatch, path)
    try:
        qa = {i: st["qa"] for i, st in frames_at(g, (0, 1, 2)).items()}
        assert ([qa[i].get("hollow_units") for i in (0, 1, 2)], [qa[i].get("seen_counts") for i in (0, 1)]) == (
            [sorted(set(ALL) - {1, 13, 14}), ALL, list(range(1, 13))], [[2, 1], [0, 0]])
    finally:
        g.stop()


def test_hud_tick_line_gains_the_sees_counts_and_hud_sight_says_them(tmp_path, monkeypatch):
    """Criterion 9, spec line 31 (ruling Q2): with `seen` keys the tick line of a Label, and `hud_tick`, read `tick %d  A %d  B %d  blocked %d  A sees %d  B sees %d  frame %d/%d`
    (frame 0: A sees 2, B sees 1; frame 1: 0 and 0; the last frame's B count is not pinned, see BOUNDARIES.md); `hud_sight` is the sight part alone, `A sees %d  B sees %d`
    (on the last frame too, with no `first seen` in it); the `first seen` words are on no frame but the last."""
    path, doc = sight_fight(tmp_path, first_seen={"A": 40, "B": None})
    g = launched(monkeypatch, path)
    try:
        st = frames_at(g, (0, 1, 2))
        lines = {i: _hud_lines(s) for i, s in st.items()}
        f = doc["frames"]
        want = {i: TICK % (f[i]["tick"], f[i]["alive"][0], f[i]["alive"][1], a, b, i) for i, (a, b) in ((0, (2, 1)), (1, (0, 0)))}
        last = re.compile(r"^tick 200  A 12  B 0  blocked 0  A sees 0  B sees \d+  frame 2/3$")
        sight = [st[i]["qa"].get("hud_sight") for i in (0, 1, 2)]
        assert ([want[i] in lines[i] for i in (0, 1)], [st[i]["qa"].get("hud_tick") for i in (0, 1)], any(last.match(t) for t in lines[2]), sight[:2],
                bool(re.fullmatch(r"A sees 0  B sees \d+", sight[2] or ""))) == ([True, True], [want[0], want[1]], True, ["A sees 2  B sees 1", "A sees 0  B sees 0"], True)
        assert [any("first seen" in t for t in lines[i]) for i in (0, 1)] == [False, False]
    finally:
        g.stop()


@pytest.mark.parametrize("first_seen,words", [({"A": 40, "B": None}, "first seen A 40  B never"), ({"A": None, "B": 0}, "first seen A never  B 0")],
                         ids=["a-saw-b-never", "tick-zero-is-not-never"])
def test_the_last_frames_end_line_names_the_first_seen_ticks(first_seen, words, tmp_path, monkeypatch):
    """Criterion 9, spec line 31: the last frame's HUD gains `first seen A <tick|never>  B <tick|never>` from `result.first_seen` (null is `never`; a tick of 0 is the
    number 0, not `never`)."""
    path, _ = sight_fight(tmp_path, first_seen=first_seen)
    g = launched(monkeypatch, path)
    try:
        st = frames_at(g, (2,))[2]
        assert any(words in t for t in _hud_lines(st)), "no HUD Label holds %r among %s" % (words, _hud_lines(st))
    finally:
        g.stop()


def test_control_a_file_without_sight_keys_keeps_the_stage_3_line(tmp_path, monkeypatch):
    """CONTROL (green today, must stay green), criterion 9: a fight file with neither `sights` nor `seen` prints the stage 3 tick line
    `tick %d  A %d  B %d  blocked %d  frame %d/%d` on every frame, with no `sees` and no `first seen` words in any HUD Label."""
    path, doc = sight_fight(tmp_path, sights=False, seen=False)
    g = launched(monkeypatch, path)
    try:
        st = frames_at(g, (0, 1, 2))
        f = doc["frames"]
        got = [(STAGE3_TICK % (f[i]["tick"], f[i]["alive"][0], f[i]["alive"][1], 0, i, 3) in _hud_lines(st[i]), any("sees" in t or "first seen" in t for t in _hud_lines(st[i])))
               for i in (0, 1, 2)]
        assert got == [(True, False)] * 3
    finally:
        g.stop()


def test_a_file_without_first_seen_adds_no_first_seen_text_to_the_end_line(tmp_path, monkeypatch):
    """Criterion 9, last sentence (spec line 31, ruling Y7): a fight file with `seen` and `sights` but no `result.first_seen` prints the sight part of the tick line on the last
    frame (`A sees 0  B sees <n>`, premise) and no HUD Label, and not `hud_sight`, holds the words `first seen`."""
    path, doc = sight_fight(tmp_path)
    assert "first_seen" not in doc["result"]
    g = launched(monkeypatch, path)
    try:
        st = frames_at(g, (2,))[2]
        lines = _hud_lines(st)
        assert (any("A sees" in t for t in lines), any("first seen" in t for t in lines), "first seen" in (st["qa"].get("hud_sight") or "")) == (True, False, False)
    finally:
        g.stop()
