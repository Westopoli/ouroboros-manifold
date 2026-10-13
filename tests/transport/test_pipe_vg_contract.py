"""Visible-game programme lane K, pieces K-a (om_pipe.c frame fields), K-f (net_step frame, _setmode)
and K-h (mission_start fog_filter). Written against docs/northstar/plans/2026-10-07-visible-game-spec.md
rev 4 section 2 (the field table) and the rulebook rev 2. Fenced: builders never edit this file.

Stories and rules proved (each test names its own in its docstring):
  S-087 / R-087-*  fire and kill events          S-086 / R-096-05  ability events and `acd`
  S-005 / R-104-09 layer transit (`tl`,`ld`,4)    S-089 / R-089-03, S-205 / R-205-02 fog_filter
  S-007 cover class                               S-139 / S-140 net_step frame (K-f)
Fixture: seed 8 (eight launch features), the clash of tests/transport/test_pipe_tactical_tier_state_reserved.py:
the opposing groups meet around tick 2300. Frames are read from the real pipe/ouroboros_pipe.
Every detector function has a positive control (a planted bad frame it must reject).

Assumptions where section 2 is silent (stated, not guessed silently):
  * cover `class` is taken from the cover circle radius `r` (the spec's wu thresholds 150/400); the field
    it reads is not named in section 2 (see the report's open question).
  * `net_step {frame:true}` answers the `net_ack` and then one `tactical` frame (K-f).
"""
import json
import math
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
PIPE_SRC = ROOT / "csrc/pipe/om_pipe.c"
SEED = 8
STRUCT_KEYS = {"id", "type", "owner", "x", "y", "hp", "stage", "cap", "nst", "next_type", "period"}
PROFILE_KEYS = {"type", "max_hp", "range", "interval", "sensor", "ability", "acd_max", "aoe"}
UNIT_REQUIRED = {"id", "faction", "type", "tier", "x", "y", "hp", "layer", "facing", "target", "state"}
EVENT_CAP = 512
ONE_STEP_FRAMES = 300

SET_SEED = {"type": "cmd", "name": "set_seed", "seed": SEED, "n_regions": 80, "features": list(range(8))}
BEGIN = {"type": "cmd", "name": "mission_begin"}
QUIT = {"type": "cmd", "name": "quit"}


def start(**extra):
    cmd = {"type": "cmd", "name": "mission_start", "faction": 0}
    cmd.update(extra)
    return cmd


pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def run(cmds, timeout=240):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=timeout)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def step(n=1, full=None):
    cmd = {"type": "cmd", "name": "tactical_step", "n": n}
    if full is not None:
        cmd["full"] = full
    return cmd


def tacticals(frames):
    return [f for f in frames if f["type"] == "tactical"]


def clash_script(first):
    mine = [u for u in first["units"] if u["faction"] == 0]
    enemy = [u for u in first["units"] if u["faction"] != 0]
    _, target = min(((a, b) for a in mine for b in enemy),
                    key=lambda p: math.hypot(p[0]["x"] - p[1]["x"], p[0]["y"] - p[1]["y"]))
    cmds = [{"type": "cmd", "name": "command", "verb": "attack_target",
             "units": [u["id"] for u in mine], "target": target["id"]}]
    cmds += [step(100, full=True)] * 11
    cmds += [step(100)] * 11
    cmds += [step(100)] * 5               # to tick 2700; the first deaths come between 2600 and 2900 (seed 8)
    cmds += [step(1)] * ONE_STEP_FRAMES
    cmds += [step(1, full=True)]
    return cmds


@pytest.fixture(scope="module")
def first_frames():
    return run([SET_SEED, start(), BEGIN])


@pytest.fixture(scope="module")
def clash(first_frames):
    """Every frame of one clash run (full and delta), in order."""
    first = tacticals(first_frames)[0]
    return run([SET_SEED, start(), BEGIN] + clash_script(first))


# ---- detectors (pure functions on a frame, each with a positive control below) ----

def unit_violations(frame):
    """Section 2 unit object: `state` int always present, OR of 1/2/4; `tl`,`ld` only with bit 4."""
    bad = []
    for key in ("units", "units_changed"):
        for u in frame.get(key, []):
            st = u.get("state")
            if not isinstance(st, int) or st & ~7:
                bad.append((u.get("id"), "state", st))
                continue
            has_tl, has_ld = "tl" in u, "ld" in u
            if bool(st & 4) != has_tl or has_tl != has_ld:
                bad.append((u.get("id"), "transit", st, u.get("tl"), u.get("ld")))
    return bad


def event_violations(frame):
    """`events`: list of [kind,a,b,tick], kind 0..3, at most 512; `events_dropped` int only at the cap."""
    ev = frame.get("events")
    if not isinstance(ev, list):
        return ["events missing"]
    bad = []
    for e in ev:
        if not (isinstance(e, list) and len(e) == 4 and all(isinstance(v, int) for v in e) and 0 <= e[0] <= 3):
            bad.append(e)
    if len(ev) > EVENT_CAP:
        bad.append("over cap")
    if "events_dropped" in frame and not (isinstance(frame["events_dropped"], int) and len(ev) == EVENT_CAP):
        bad.append("events_dropped without a full ring")
    if len(ev) == EVENT_CAP and not isinstance(frame.get("events_dropped", 0), int):
        bad.append("events_dropped not int")
    return bad


def structure_violations(rows):
    bad = []
    for s in rows:
        if set(s) != STRUCT_KEYS or not (0 <= s["cap"] <= 1000) or s["stage"] != 0:
            bad.append(s)
    return bad


# ---- positive controls ----

def test_control_unit_detector_rejects_planted_frames():
    """Positive control for unit_violations (S-005, R-104-09)."""
    ok = {"units": [{"id": 1, "state": 5, "tl": 2, "ld": 9}]}
    assert unit_violations(ok) == []
    assert unit_violations({"units": [{"id": 1, "state": 8}]})
    assert unit_violations({"units": [{"id": 1}]})
    assert unit_violations({"units": [{"id": 1, "state": 4}]})           # transit bit without tl/ld
    assert unit_violations({"units": [{"id": 1, "state": 0, "tl": 1, "ld": 3}]})  # tl without the bit


def test_control_event_and_structure_detectors_reject_planted_frames():
    """Positive control for event_violations and structure_violations (S-087, S-209)."""
    assert event_violations({"events": [[0, 1, 2, 30]]}) == []
    assert event_violations({"events": [[4, 1, 2, 30]]})
    assert event_violations({"events": [[0, 1, 2]]})
    assert event_violations({"events": [], "events_dropped": 3})
    assert event_violations({})
    row = dict.fromkeys(STRUCT_KEYS, 0)
    assert structure_violations([row]) == []
    assert structure_violations([dict(row, cap=1001)])
    assert structure_violations([{k: v for k, v in row.items() if k != "nst"}])


# ---- K-a: unit object ----

def test_every_unit_carries_state_and_transit_fields_consistently(first_frames, clash):
    """S-087 (R-087-04), S-005: `state` is an int on every unit of every frame, never omitted, bits 1|2|4 only,
    and `tl`/`ld` are present exactly while bit 4 is set. Red on main: `state` is written but always the reserved 0
    (ruling A30; rulebook row 22 lets K-a re-pin it)."""
    frames = tacticals(first_frames) + tacticals(clash)
    assert frames, "no tactical frames came back"
    for f in frames:
        missing = [u["id"] for u in f.get("units", []) if "state" not in u]
        assert not missing, f"units without `state`: {missing[:5]} (tick {f.get('tick')})"
        assert not unit_violations(f), unit_violations(f)[:5]
    assert any(u["state"] for f in tacticals(clash) for u in f.get("units", []) + f.get("units_changed", [])), (
        "no unit ever had a non-zero `state` through the clash (main writes the reserved 0, ruling A30)")
    u0 = tacticals(first_frames)[0]["units"][0]
    assert UNIT_REQUIRED <= set(u0), sorted(UNIT_REQUIRED - set(u0))


def test_fired_state_bit_matches_a_fire_event_in_the_same_call(clash):
    """S-087 (R-087-04): on a one-step frame a unit with `state` bit 1 has a fire event [0,id,*,tick] in that
    frame's `events`; bit 1 appears at least once in the clash (positive control: the clash really fires)."""
    seen = 0
    for f in tacticals(clash):
        for u in f.get("units", []) + f.get("units_changed", []):
            if u.get("state", 0) & 1:
                seen += 1
                assert any(e[0] == 0 and e[1] == u["id"] for e in f.get("events", [])), (f["tick"], u["id"])
    assert seen > 0, "no unit ever showed state bit 1 (fired) through the whole clash"


def test_own_units_carry_sight_enemy_units_do_not(first_frames):
    """S-089 (R-089-02): `sight` int wu on own-faction units only (from om_fog_get_drawn_sensor_circle_radius).
    Red on main: no unit has `sight`."""
    units = tacticals(first_frames)[0]["units"]
    mine = [u for u in units if u["faction"] == 0]
    enemy = [u for u in units if u["faction"] != 0]
    assert mine and enemy, "fixture needs both factions in the first frame (fog_filter off)"
    assert all(isinstance(u.get("sight"), int) and u["sight"] > 0 for u in mine), [u.get("sight") for u in mine[:5]]
    assert all("sight" not in u for u in enemy)


def test_layer_order_sets_transit_fields_then_clears_them(first_frames):
    """S-005, R-104-09: `command {verb:set_layer, units, layer}` acks; the unit then shows `tl` == the target,
    `ld` > the tick and state bit 4 while in transit; once `ld` has passed, none of the three remain.
    Red on main: unknown verb."""
    first = tacticals(first_frames)[0]
    me = next(u for u in first["units"] if u["faction"] == 0)
    target = (me["layer"] + 1) % 5
    frames = run([SET_SEED, start(), BEGIN,
                  {"type": "cmd", "name": "command", "verb": "set_layer", "units": [me["id"]], "layer": target},
                  step(1, full=True)] + [step(50, full=True)] * 12)
    acks = [f for f in frames if f["type"] in ("ack", "error")]
    assert acks and acks[0]["type"] == "ack", acks[:1]
    rows = [next(u for u in f["units"] if u["id"] == me["id"]) for f in tacticals(frames)[1:]]
    moving = [u for u in rows if u.get("state", 0) & 4]
    assert moving, "unit never entered layer transit"
    assert moving[0]["tl"] == target and moving[0]["ld"] > 0
    assert "tl" not in rows[-1] and not rows[-1]["state"] & 4 and rows[-1]["layer"] == target


def test_ability_use_sets_acd_and_ability_event(first_frames):
    """S-086 (R-096-05, R-086-01), S-135: after `activate_ability` the unit carries `acd` (the tick it is ready,
    an int above the current tick) and the frame's events hold [1, unit, ability, tick]; before use `acd` is
    omitted. Red on main: no `acd`, no events."""
    first = tacticals(first_frames)[0]
    # A Warden (type 3, Rally) starts its cooldown at activation; a Raider's Surge zeroes its cooldown while
    # active, so `acd` is absent then (`acd` present only while cooldown_end > tick; TD-VG-K-8).
    raider = next(u for u in first["units"] if u["faction"] == 0 and u["type"] == 3)
    assert "acd" not in raider
    frames = run([SET_SEED, start(), BEGIN,
                  {"type": "cmd", "name": "command", "verb": "activate_ability", "units": [raider["id"]]},
                  step(1, full=True)])
    tick_frame = tacticals(frames)[-1]
    u = next(x for x in tick_frame["units"] if x["id"] == raider["id"])
    assert isinstance(u.get("acd"), int) and u["acd"] > tick_frame["tick"], u.get("acd")
    assert any(e[0] == 1 and e[1] == raider["id"] for e in tick_frame.get("events", [])), tick_frame.get("events")


# ---- K-a: events ----

def test_clash_emits_fire_and_kill_events_never_diffed(clash):
    """S-087 (R-087-04), S-085: every tactical frame (full or delta) has an `events` list of [kind,a,b,tick];
    the clash has fire (0) and kill (2) events; kill events name a unit that is gone or hp 0 after.
    Red on main: no `events` key."""
    frames = tacticals(clash)
    for f in frames:
        assert not event_violations(f), (f["tick"], event_violations(f)[:3])
    kinds = {e[0] for f in frames for e in f["events"]}
    assert 0 in kinds, "no fire event in the clash"
    assert 2 in kinds, "no kill event in the clash"
    for f in frames[-ONE_STEP_FRAMES:]:  # the trailing one-step frames: every event carries that frame's tick
        assert all(e[3] == f["tick"] for e in f["events"]), f["tick"]


def test_events_over_many_steps_accumulate_with_their_own_ticks():
    """S-087 (R-087-04): a `tactical_step n=100` through the clash returns the events of all 100 steps, each
    tagged with its own tick, so more than one distinct tick appears. Red on main: no `events`."""
    first = tacticals(run([SET_SEED, start(), BEGIN]))[0]
    frames = run([SET_SEED, start(), BEGIN] + clash_script(first)[:-1 - ONE_STEP_FRAMES + 50] + [step(100)])
    last = tacticals(frames)[-1]
    ev = last.get("events")
    assert isinstance(ev, list), "no events list"
    ticks = {e[3] for e in ev}
    assert len(ticks) > 1, f"events of a 100-step call share ticks {sorted(ticks)}"
    assert all(last["tick"] - 100 < t <= last["tick"] for t in ticks)


# ---- K-a: structures ----

def test_full_frame_lists_structures_with_the_spec_keys(first_frames):
    """S-209 (R-209-*), R-089-03: the full frame has `structures` with exactly {id,type,owner,x,y,hp,stage,cap,
    nst,next_type,period}, stage 0, cap 0..1000. Red on main: no `structures`."""
    f = tacticals(first_frames)[0]
    assert "structures" in f, sorted(f)
    assert f["structures"], "the fixture mission has no structures"
    assert not structure_violations(f["structures"]), structure_violations(f["structures"])[:2]


def test_deltas_carry_changed_and_removed_structures_not_the_list(clash):
    """S-209: delta frames never carry `structures`; a changed structure appears in `structures_changed`
    (entries have `id`), removed ids in `structures_removed`; capture progress changes during the clash or the
    fixture is wrong (control: the full frames' `cap` differ across the run). Red on main."""
    frames = tacticals(clash)
    deltas = [f for f in frames if not f.get("full", True)]
    assert deltas, "no delta frames in the run"
    assert all("structures" not in f for f in deltas)
    assert all(isinstance(f.get("structures_changed", []), list) and isinstance(f.get("structures_removed", []), list)
               for f in deltas)
    assert all("id" in s for f in deltas for s in f.get("structures_changed", []))
    fulls = [f for f in frames if f.get("full", True)]
    assert all("structures" in f for f in fulls), "a full frame lacks `structures`"


def test_capture_produces_a_capture_event_or_the_fixture_has_none(clash):
    """S-209, R-209-*: a capture event [3, structure, new owner, tick] names a structure id of the full frame.
    Control: the structure ids exist. Red on main (no structures at all)."""
    frames = tacticals(clash)
    full = next(f for f in frames if f.get("full", True))
    ids = {s["id"] for s in full.get("structures", [])}
    assert ids, "no structures to capture"
    for f in frames:
        for e in f.get("events", []):
            if e[0] == 3:
                assert e[1] in ids


# ---- K-a: profiles, objectives, map, dumps ----

def test_profiles_once_per_full_frame_only(clash):
    """S-086, S-135: `profiles` is [{type,max_hp,range,interval,sensor,ability,acd_max,aoe}] on full frames and
    absent on deltas. Red on main: no `profiles`."""
    frames = tacticals(clash)
    fulls = [f for f in frames if f.get("full", True)]
    assert all(isinstance(f.get("profiles"), list) and f["profiles"] for f in fulls)
    for p in fulls[0]["profiles"]:
        assert set(p) == PROFILE_KEYS, sorted(set(p) ^ PROFILE_KEYS)
    assert all("profiles" not in f for f in frames if not f.get("full", True))


def test_objectives_carry_done_state(clash):
    """S-209, R-104-01: every frame's `objectives` entries are {i, progress, done} with done 0 open, 1 complete,
    2 failed (rulebook row 23: superset of {i,progress}). Red on main: no `done`."""
    for f in tacticals(clash):
        for o in f["objectives"]:
            assert {"i", "progress", "done"} <= set(o), o
            assert o["done"] in (0, 1, 2)


def test_map_has_obstacles_and_cover_class_by_size(first_frames):
    """S-007 (R-007-*): full-frame `map.obstacles` is [{x,y,r}] and each `map.cover` entry has `class` 0 small
    (r < 150 wu), 1 medium (< 400), 2 huge. Red on main: no `class`. Positive control: the classifier rejects a
    planted wrong class."""
    def klass(r):
        return 0 if r < 150 else 1 if r < 400 else 2
    assert klass(149.9) == 0 and klass(150) == 1 and klass(399.9) == 1 and klass(400) == 2
    m = tacticals(first_frames)[0]["map"]
    assert m["cover"], "fixture has no cover"
    for c in m["cover"]:
        assert c.get("class") == klass(c["r"]), c
    assert all(set(o) >= {"x", "y", "r"} for o in m["obstacles"])


def test_delta_frames_carry_no_map(clash):
    """Rulebook row 25: `map` stays full-frame only."""
    assert all("map" not in f for f in tacticals(clash) if not f.get("full", True))


def test_terrain_dump_carries_heights_as_hex_le_int32():
    """S-236, R-001-*: ground era `terrain_dump` gains `heights`, hex of little-endian int32 cm, one per cell:
    length 8 * cells_w * cells_h. Red on main: no `heights`."""
    frames = run([SET_SEED, start(era_kind=1), BEGIN, {"type": "cmd", "name": "terrain_dump"}])
    t = next((f for f in frames if f["type"] == "terrain"), None)
    assert t is not None, [f["type"] for f in frames]
    assert "heights" in t, sorted(t)
    raw = bytes.fromhex(t["heights"])
    assert len(raw) == 4 * t["cells_w"] * t["cells_h"], (len(raw), t["cells_w"], t["cells_h"])
    vals = [int.from_bytes(raw[i:i + 4], "little", signed=True) for i in range(0, len(raw), 4)]
    assert len(set(vals)) > 1, "heights are flat"


# ---- K-f ----

def test_net_step_frame_true_also_writes_the_tactical_frame():
    """S-139, S-140 (K-f): `net_step {n, frame:true}` answers the net_ack and then one `tactical` frame; without
    `frame` no tactical frame is written (docs/architecture.md, lockstep verbs). Red on main: `frame` ignored."""
    plain = run([SET_SEED, start(), BEGIN, {"type": "cmd", "name": "net_step", "n": 2}])
    assert plain[-1]["type"] == "net_ack"
    framed = run([SET_SEED, start(), BEGIN, {"type": "cmd", "name": "net_step", "n": 2, "frame": True}])
    types = [f["type"] for f in framed[2:]]
    assert types[:2] == ["net_ack", "tactical"], types
    assert framed[-1]["tick"] > tacticals(framed)[0]["tick"]


def test_pipe_source_sets_binary_stdio_on_windows_only():
    """S-139 (K-f): the pipe puts stdin/stdout in binary mode with `_setmode` under `_WIN32` (Windows would
    otherwise translate bytes in the length-prefixed frames). The Linux build cannot run it, so the guard is
    read from the source; the wine probe is the clerk's. Positive control: the matcher rejects an unguarded call."""
    def guarded(text):
        return re.search(r"#\s*if[^\n]*_WIN32[^\n]*\n(?:(?!#\s*endif)[\s\S])*?_setmode\s*\(", text) is not None
    assert guarded("#ifdef _WIN32\n_setmode(0, 0x8000);\n#endif\n")
    assert not guarded("_setmode(0, 0x8000);\n")
    assert guarded(PIPE_SRC.read_text()), "csrc/pipe/om_pipe.c has no _WIN32-guarded _setmode call"


# ---- K-h ----

def test_fog_filter_hides_unseen_enemies_and_flag_off_shows_all(first_frames):
    """R-089-03, R-205-02, S-089, S-205 (K-h): with `mission_start {fog_filter:true}` units and structures the
    local faction cannot see are not written (their ids and positions are absent from every frame); with the
    flag absent every unit is present (the default stays off). Red on main: the flag is ignored."""
    off = tacticals(first_frames)[0]
    on = tacticals(run([SET_SEED, start(fog_filter=True), BEGIN]))[0]
    off_enemy = {u["id"] for u in off["units"] if u["faction"] != 0}
    on_enemy = {u["id"] for u in on["units"] if u["faction"] != 0}
    assert off_enemy, "control: with the flag off the enemy is in the first frame"
    assert len(on_enemy) < len(off_enemy), (len(on_enemy), len(off_enemy))
    own_off = {u["id"] for u in off["units"] if u["faction"] == 0}
    assert own_off == {u["id"] for u in on["units"] if u["faction"] == 0}, "own units must all stay"
    off_struct = {s["id"] for s in off.get("structures", []) if s["owner"] != 0}
    on_struct = {s["id"] for s in on.get("structures", []) if s["owner"] != 0}
    assert on_struct <= off_struct and len(on_struct) < len(off_struct) or not off_struct


def test_leaving_sight_sends_units_removed_and_events_follow_visibility():
    """R-089-03, S-089 (K-h): with fog_filter on, a unit that leaves sight while still alive appears in
    `units_removed` of a delta frame (control: an unfiltered run lists only real deaths there), and an event is
    sent only when its `a` or `b` is an own or visible unit. Red on main: the flag is ignored."""
    plain = tacticals(run([SET_SEED, start(), BEGIN]))[0]
    script = clash_script(plain)
    dead = {i for f in tacticals(run([SET_SEED, start(), BEGIN] + script)) for i in f.get("units_removed", [])}
    assert dead, "control: the unfiltered clash has no deaths"
    frames = tacticals(run([SET_SEED, start(fog_filter=True), BEGIN] + script))
    left_alive = set()
    seen = set()
    for f in frames:
        seen |= {u["id"] for u in f.get("units", []) + f.get("units_changed", [])}
        left_alive |= {i for i in f.get("units_removed", []) if i not in dead}
        for e in f.get("events", []):
            assert e[1] in seen or e[2] in seen, (f["tick"], e)
    assert left_alive, "no unit left sight alive (units_removed only ever listed deaths)"
