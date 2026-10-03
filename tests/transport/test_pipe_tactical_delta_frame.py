"""A7: the delta tactical frame (architect rulings 2026-10-01 round 1 A7, round 2 section 3;
docs/architecture.md "tactical frame"). E-13 pipe budget: one tactical_step round trip stays
under 50 ms at 5,000 units; that measurement is a re-measure step (scripts/bench_tactical_pipe.py),
not asserted here.

Contract under test:
- every tactical frame carries `full` (bool); a full frame has `map` and the complete `units[]`;
  a delta frame has `units_changed[]` and `units_removed[]` and neither `map` nor `units`;
- full frames: `mission_begin`, `snapshot` (tactical map loaded), every 20th sim step counted
  from mission_begin (an n>1 call that reaches or crosses a multiple of 20 writes a full frame),
  and `"full":true` on tactical_step; `n:0` writes a full frame with no step;
- `tactical_step` with n>1 writes only the last frame, the delta taken against the last frame
  written;
- `visible` rides every frame and holds only the player's faction;
- `objectives:[{i,progress}]` rides every frame, full and delta;
- a client keeps id -> unit: full replaces, delta deletes `units_removed` then overwrites
  `units_changed`; after any frame the dict equals the full state at that tick.

Fixture: seed 76 with the eight launch features draws a DEFENSIVE_STAND (archetype 0) at
region 68, a small mission (118 units on the pre-A81 world, 145 on the A81 build, 80 regions);
player units that attack_target their nearest enemy see deaths before tick 2400, and the
objective's live completion creeps up every tick. Seed, tick and unit counts are fixtures,
not thresholds. The earlier seed 8 (81 units, deaths near tick 2300) became a 363-unit world
once events reached regions 64+ (A81), where no death arrived by tick 2400 (TD-A89-5); 76 was
chosen by scanning seeds 1 to 400 on both builds for the same drawn mission, deaths and
progress; seeds 26, 127, 158, 175 and 287 also pass the whole file on both.
"""
import json
import math
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SEED = 76
DRAWN = (0, 68)  # (archetype, region) the fixture seed draws on both builds
FULL_PERIOD = 20
UNIT_KEYS = {"id", "faction", "type", "tier", "x", "y", "hp", "layer", "facing", "target", "state"}

SET_SEED = {"type": "cmd", "name": "set_seed", "seed": SEED, "n_regions": 80, "features": FEATURES}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
SNAPSHOT = {"type": "cmd", "name": "snapshot"}
QUIT = {"type": "cmd", "name": "quit"}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=120)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _step(n=1, full=None):
    cmd = {"type": "cmd", "name": "tactical_step", "n": n}
    if full is not None:
        cmd["full"] = full
    return cmd


def _tacticals(frames):
    return [f for f in frames if f["type"] == "tactical"]


def _begin_frames(extra):
    """set_seed, mission_start, mission_begin, then extra; returns (mission, tactical frames in order)."""
    frames = _run([SET_SEED, START, BEGIN] + extra)
    errors = [f for f in frames if f["type"] == "error"]
    assert not errors, errors
    mission = next(f for f in frames if f["type"] == "mission")
    return mission, _tacticals(frames)


def _assert_drawn(frames):
    mission = next(f for f in frames if f["type"] == "mission")
    assert (mission["archetype"], mission["region"]) == DRAWN, (
        "fixture drift: seed %d drew archetype %r region %r, expected %r" % (
            SEED, mission["archetype"], mission["region"], DRAWN))


def _assert_full(f):
    assert "full" in f, "tactical frame carries no `full` key (A7): %r" % sorted(f)
    assert f["full"] is True, f["tick"]
    assert "map" in f and isinstance(f["units"], list), sorted(f)
    assert "units_changed" not in f and "units_removed" not in f, sorted(f)


def _assert_delta(f):
    assert "full" in f, "tactical frame carries no `full` key (A7): %r" % sorted(f)
    assert f["full"] is False, f["tick"]
    assert isinstance(f["units_changed"], list) and isinstance(f["units_removed"], list), sorted(f)
    assert "map" not in f and "units" not in f, sorted(f)


def _apply(state, f):
    """The client's reconstruction rule from docs/architecture.md."""
    if f["full"]:
        return {u["id"]: u for u in f["units"]}
    out = dict(state)
    for uid in f["units_removed"]:
        out.pop(uid, None)
    for u in f["units_changed"]:
        out[u["id"]] = u
    return out


def _player_ids(frame):
    return [u["id"] for u in frame["units"] if u["faction"] == 0]


def _move_cmd(ids, dx=500.0):
    return {"type": "cmd", "name": "command", "verb": "move", "units": ids, "x": dx, "y": 5000.0}


def _begin_units():
    _, tac = _begin_frames([])
    return tac[0]


def test_every_tactical_frame_carries_full_flag():
    _, tac = _begin_frames([_step(1), _step(1), _step(3), _step(1, full=True), _step(0)])
    assert len(tac) == 6, [f["tick"] for f in tac]
    for f in tac:
        assert "full" in f, "tactical frame at tick %d carries no `full` key (A7)" % f["tick"]
        assert isinstance(f["full"], bool)


def test_mission_begin_frame_is_full():
    _, tac = _begin_frames([])
    assert len(tac) == 1
    _assert_full(tac[0])
    assert tac[0]["tick"] == 0 and tac[0]["units"]


def test_snapshot_during_a_mission_answers_a_full_tactical_frame():
    # Ambiguity: the docs do not say whether `snapshot` still also writes the strategic
    # snapshot frame in a mission; only the presence of the full tactical frame is asserted.
    _, tac = _begin_frames([_step(1), _step(1), _step(1), SNAPSHOT])
    assert len(tac) == 5, [f["tick"] for f in tac]
    snap_frame = tac[-1]
    _assert_full(snap_frame)
    assert snap_frame["tick"] == 3
    expected = {u["id"]: u for u in tac[0]["units"]}
    assert {u["id"] for u in snap_frame["units"]} >= set(expected)


def test_delta_frame_has_the_delta_shape_and_only_changed_units():
    """Positive control: one move order makes exactly that unit change; an unchanged unit
    never rides units_changed."""
    first = _begin_units()
    mover = _player_ids(first)[0]
    _, tac = _begin_frames([_move_cmd([mover]), _step(1)])
    delta = tac[-1]
    _assert_delta(delta)
    assert delta["tick"] == 1
    assert [u["id"] for u in delta["units_changed"]] == [mover], [u["id"] for u in delta["units_changed"]][:10]
    assert set(delta["units_changed"][0]) == UNIT_KEYS
    assert delta["units_removed"] == []
    before = next(u for u in first["units"] if u["id"] == mover)
    assert (delta["units_changed"][0]["x"], delta["units_changed"][0]["y"]) != (before["x"], before["y"])


def test_idle_step_writes_an_empty_delta():
    _, tac = _begin_frames([_step(1)])
    _assert_delta(tac[-1])
    assert tac[-1]["units_changed"] == [] and tac[-1]["units_removed"] == []


def test_full_frame_on_every_20th_step_counted_from_mission_begin():
    steps = 45
    _, tac = _begin_frames([_step(1)] * steps)
    frames = tac[1:]
    assert len(frames) == steps
    got = [f["full"] if "full" in f else None for f in frames]
    want = [(i % FULL_PERIOD == 0) for i in range(1, steps + 1)]
    assert got == want, "full flags by step 1..%d: %r, expected %r" % (steps, got, want)
    for i, f in enumerate(frames, 1):
        assert f["tick"] == i
        (_assert_full if want[i - 1] else _assert_delta)(f)


def test_n_greater_than_one_writes_only_the_last_frame_against_the_last_frame_written():
    first = _begin_units()
    mover = _player_ids(first)[0]
    _, tac = _begin_frames([_move_cmd([mover]), _step(5), _step(0)])
    assert len(tac) == 3, "n=5 must write one frame, got ticks %r" % [f["tick"] for f in tac]
    delta, probe = tac[1], tac[2]
    _assert_delta(delta)
    assert delta["tick"] == 5
    assert [u["id"] for u in delta["units_changed"]] == [mover]
    state = _apply(_apply({}, tac[0]), delta)
    assert state == {u["id"]: u for u in probe["units"]}, "reconstruction after an n=5 call differs from the full state"


def test_n_greater_than_one_crossing_a_multiple_of_20_writes_a_full_frame():
    _, tac = _begin_frames([_step(15), _step(3), _step(4), _step(20), _step(1)])
    frames = tac[1:]
    assert [f["tick"] for f in frames] == [15, 18, 22, 42, 43]
    assert [f.get("full") for f in frames] == [False, False, True, True, False], (
        "full flags for calls reaching ticks 15, 18, 22 (crosses 20), 42 (crosses 40), 43")
    _assert_delta(frames[0])
    _assert_full(frames[2])
    _assert_full(frames[3])


def test_full_true_request_writes_a_full_frame_and_does_not_move_the_cadence():
    _, tac = _begin_frames([_step(1)] * 2 + [_step(1, full=True)] + [_step(1)] * 17)
    frames = tac[1:]
    assert [f["tick"] for f in frames] == list(range(1, 21))
    assert frames[2]["tick"] == 3
    _assert_full(frames[2])
    assert frames[2]["tick"] == 3 and len(frames[2]["units"]) == len(tac[0]["units"])
    _assert_delta(frames[3])
    _assert_delta(frames[18])
    _assert_full(frames[19])  # step 20 is still the 20th step from mission_begin


def test_n_zero_writes_a_full_frame_without_stepping():
    _, tac = _begin_frames([_step(1), _step(0), _step(0)])
    assert len(tac) == 4
    for f in tac[2:]:
        _assert_full(f)
        assert f["tick"] == 1
    assert tac[2]["units"] == tac[3]["units"]


def test_visible_only_for_the_player_faction_on_every_frame():
    frames = _run([SET_SEED, SNAPSHOT, START, BEGIN, _step(1), _step(1, full=True), _step(2), _step(0)])
    player = next(f for f in frames if f["type"] == "snapshot")["player_faction"]
    tac = _tacticals(frames)
    assert len(tac) == 5
    saw_delta = False
    for f in tac:
        assert set(f["visible"]) == {str(player)}, "tick %d visible keys %r, expected only %r" % (
            f["tick"], sorted(f["visible"]), str(player))
        ids = f["visible"][str(player)]
        assert isinstance(ids, list) and ids, "player sees nothing at tick %d" % f["tick"]
        if f["full"]:
            assert set(ids) <= {u["id"] for u in f["units"]}
        else:
            saw_delta = True
    assert saw_delta, "fixture drift: no delta frame in the script"


def test_objectives_ride_every_frame_full_and_delta():
    frames = _run([SET_SEED, START, BEGIN, _step(1), _step(1, full=True), _step(0)])
    mission = next(f for f in frames if f["type"] == "mission")
    tac = _tacticals(frames)
    assert len(tac) == 4
    want = [o["i"] for o in mission["objectives"]]
    assert want
    for f in tac:
        assert "objectives" in f, "tactical frame at tick %d has no objectives (A6/A7)" % f["tick"]
        assert [o["i"] for o in f["objectives"]] == want
        for o in f["objectives"]:
            assert set(o) == {"i", "progress"}
            assert 0.0 <= o["progress"] <= 1.0
    assert tac[1]["full"] is False and "objectives" in tac[1]


def test_objective_progress_is_live_and_never_diffed_across_delta_frames():
    """Positive control for `progress`: on seed 76 the objective's live completion creeps up
    every tick, so consecutive delta frames carry different values; a diffed or cached array
    would repeat or omit them."""
    frames = _run([SET_SEED, START, BEGIN, _step(1), _step(1), _step(1)])
    _assert_drawn(frames)
    tac = _tacticals(frames)
    assert all("objectives" in f for f in tac), "tactical frame has no objectives (A6/A7)"
    progress = [f["objectives"][0]["progress"] for f in tac[1:]]
    for f in tac[1:]:
        _assert_delta(f)
    assert progress[0] < progress[1] < progress[2], progress


def test_delta_reconstruction_equals_the_full_frame_at_the_same_tick():
    """Run through mid-cadence ticks, a wave spawn (units appear at tick ~600) and moving
    units; at each checkpoint a `n:0` full frame (same tick, no step) must equal the dict the
    client built from deltas alone. Ticks 37, 213 and 605 are off the 20-step cadence."""
    first = _begin_units()
    movers = _player_ids(first)[:20]
    cmds, checkpoints, tick = [_move_cmd(movers, 9000.0)], [], 0
    for target in (37, 213, 605):
        while tick < target:
            cmds.append(_step(1))
            tick += 1
        cmds.append(_step(0))
        checkpoints.append(len(cmds) - 1)
    frames = _run([SET_SEED, START, BEGIN] + cmds)
    tac = _tacticals(frames)
    assert len(tac) == 1 + sum(1 for c in cmds if c.get("name") == "tactical_step")
    by_cmd = {}
    k = 1
    for idx, c in enumerate(cmds):
        if c.get("name") == "tactical_step":
            by_cmd[idx] = tac[k]
            k += 1
    state = _apply({}, tac[0])
    ticks_checked = []
    for idx in sorted(by_cmd):
        f = by_cmd[idx]
        assert "full" in f, "tactical frame carries no `full` key (A7)"
        if idx in checkpoints:
            assert f["full"] is True
            assert state == {u["id"]: u for u in f["units"]}, "client dict differs from the full state at tick %d" % f["tick"]
            ticks_checked.append(f["tick"])
        state = _apply(state, f)
    assert ticks_checked == [37, 213, 605]
    assert len({u for u in state}) > len(first["units"]), "fixture drift: no wave spawn reached by tick 605"


def test_reconstruction_check_detects_a_dropped_change():
    """Positive control for the reconstruction detector: dropping one changed unit from a
    delta breaks the equality the tests above assert."""
    first = _begin_units()
    movers = _player_ids(first)[:3]
    frames = _run([SET_SEED, START, BEGIN, _move_cmd(movers), _step(1), _step(0)])
    tac = _tacticals(frames)
    base, delta, probe = _apply({}, tac[0]), tac[1], tac[2]
    assert "full" in delta, "tactical frame carries no `full` key (A7)"
    honest = _apply(base, delta)
    assert honest == {u["id"]: u for u in probe["units"]}
    broken = dict(delta, units_changed=delta["units_changed"][1:])
    assert len(delta["units_changed"]) == 3
    assert _apply(base, broken) != {u["id"]: u for u in probe["units"]}


def _death_script(first):
    mine = [u for u in first["units"] if u["faction"] == 0]
    enemy = [u for u in first["units"] if u["faction"] != 0]
    _, target = min(((a, b) for a in mine for b in enemy),
                    key=lambda p: math.hypot(p[0]["x"] - p[1]["x"], p[0]["y"] - p[1]["y"]))
    cmds = [{"type": "cmd", "name": "command", "verb": "attack_target",
             "units": [u["id"] for u in mine], "target": target["id"]}]
    # Test-defect, A150: 22 x 100 + 200 x 1 (ticks 2200-2400) -> 16 x 100 + 200 x 1 (ticks 1600-1800); cause: slowest-member pacing of attack-move groups (R-095-01) / pursuit by steering (R-087-04); assertions unchanged.
    # First death now lands at tick 1690: 90 ticks inside the window start, 110 before its end.
    cmds += [_step(100)] * 16  # to tick 1600
    cmds += [_step(1)] * 200   # one frame per tick through the first deaths (tick ~1690)
    return cmds


def test_a_death_shows_in_units_removed_and_the_full_frame_agrees():
    first = _begin_units()
    cmds = _death_script(first)
    cmds.append(_step(0))
    frames = _run([SET_SEED, START, BEGIN] + cmds)
    _assert_drawn(frames)
    tac = _tacticals(frames)
    assert "full" in tac[1], "tactical frame carries no `full` key (A7)"
    state, removed_at = _apply({}, tac[0]), None
    for f in tac[1:-1]:
        if not f["full"] and f["units_removed"] and removed_at is None:
            removed_at = f
            gone = f["units_removed"]
            assert all(uid in state for uid in gone), "removed id was not in the previous frame state"
            assert not ({u["id"] for u in f["units_changed"]} & set(gone))
        state = _apply(state, f)
    assert removed_at is not None, "no unit death reached units_removed by tick %d" % tac[-2]["tick"]
    final = tac[-1]
    _assert_full(final)
    assert not (set(removed_at["units_removed"]) & {u["id"] for u in final["units"]}), (
        "a unit reported in units_removed is still listed in the full frame (dead units must leave both)")
    assert state == {u["id"]: u for u in final["units"]}


def test_death_positive_control_every_removed_id_belonged_to_the_previous_state():
    first = _begin_units()
    cmds = _death_script(first)
    frames = _run([SET_SEED, START, BEGIN] + cmds)
    _assert_drawn(frames)
    tac = _tacticals(frames)
    assert "full" in tac[1], "tactical frame carries no `full` key (A7)"
    state = _apply({}, tac[0])
    n_removed = 0
    for f in tac[1:]:
        if not f["full"]:
            for uid in f["units_removed"]:
                assert uid in state, "units_removed id %d was not in the last written frame" % uid
                n_removed += 1
        state = _apply(state, f)
    assert n_removed > 0, "fixture drift: no death in the first %d ticks" % tac[-1]["tick"]


def test_same_seed_and_commands_give_byte_identical_frames():
    first = _begin_units()
    movers = _player_ids(first)[:10]
    cmds = [_move_cmd(movers), _step(7), _step(1, full=True), _step(30), _step(0), _step(2)]
    run1 = _run([SET_SEED, START, BEGIN] + cmds)
    run2 = _run([SET_SEED, START, BEGIN] + cmds)
    assert "full" in _tacticals(run1)[1], "tactical frame carries no `full` key (A7)"
    assert json.dumps(run1, sort_keys=False) == json.dumps(run2, sort_keys=False)
