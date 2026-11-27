"""LAB stage 5, piece E1 (story H-091): the firing arc, E-13 R-100-04 (R-091-01 to R-091-06).

Rule words (docs/stories/H-091.md, "E1 the firing arc"):
  R-091-01  Given OM_TP_FIRING_ARC_DEG 90 and a unit holding a living target in range whose direction is more than 45 degrees from the
            unit's facing, When the tick runs, Then the unit does not fire that tick, keeps the same target, and its facing moves toward
            the target by no more than its category's turn rate (R-100-02: Line 4.0 rad/s, 0.2 rad a tick at 20 ticks a second); on the
            first tick the target is within 45 degrees it may fire. Checked every tick.
  R-091-02  Given the arc at 360 (the default), Then every existing golden, hash and fight file is unchanged: the csim goldens,
            tests/skilllab/golden_hashes.json and the stage 3 and 4 pinned fight files pass untouched.
  R-091-03  Given a unit with its target dead ahead (0 degrees) and the arc at 90, Then its first shot comes on the same tick as with the
            arc at 360; given the target at 180 degrees (directly behind), its first shot comes later by at least the ticks its turn rate
            needs to bring the target inside the arc (135 degrees at 0.2 rad a tick: 12 ticks) and by no more than that plus 2.
  R-091-04  The arc changes nothing but the shot: with the arc at 90, acquisition (who targets whom and when), the lock, return-fire
            targeting and every unit's orders and destinations are the same, tick for tick, as with 360 until the first tick a shot is
            withheld.
  R-091-05  A save taken mid-fight with the arc at 90 and loaded gives the same later frames as the run that was not saved; two runs with
            the same seed give byte-identical traces.
  R-091-06  The arc is the full angle centred on the facing: a target at exactly half the arc is inside; values are taken as the
            parameter is set (10 to 360).

Scene facts (dumped on this tree, 2026-11-26, before the tests were written): a Vanguard (type 2, Line, attack range 300, walking kind 1)
at (500, 500) with a Supply (type 6, faction 1) 80 wu east of it and the sim's defaults otherwise: om_unit_target is -1 for ticks 1 to 3,
the Supply's id on tick 4, and the first shot is fired on tick 4 (tactical event kind 0, attacker in `a`), whatever the facing and whatever
the arc (today nothing reads the arc). The unit starts turning on tick 4, 0.2 rad a tick, and ends turned toward the Supply: facing after
tick 4 from pi is 2.942 (pi - 0.2). The tests use the facing the unit had at the START of the tick (read after the previous tick) as "the
unit's facing" of the rule words; with that reading the story's 12-tick minimum of R-091-03 is exact (tick 4 + 12 = tick 16, the first
tick that starts with the target inside 45 degrees).

Harness notes. The scene is the shipped configuration: the walking movement kind for Vanguards, the default parameters, no
obstacles on the open canvas, sight at its default. The Supply never fires, so the single-unit scenes have one shooter. The "exactly half
the arc" cases use math.radians(half) as the facing and expect the engine to accept it to better than 1e-9 rad.

Today the arc is read by nothing (csrc/unit.c om_tac_fire_pass and om_tac_fire never read facing): every red test below fails because a
unit fires with its target outside the arc. The controls at arc 360 and the R-091-02 trace-equality test are green today and must stay so.
"""
import ctypes
import hashlib
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import SUPPLY, VANGUARD, attack_move, dest, get_param, set_param, spawn, step

TICK_RATE = 20
LINE_TURN_PER_TICK = 4.0 / TICK_RATE          # R-100-02: Line 4.0 rad/s
EPS = 1e-9                                     # angle tolerance of the "exactly half" cases and of the per-tick checks
FIRST_SHOT_TICK = 4                            # dumped: target held on tick 4, first shot on tick 4 (arc 360, any facing)
SAVE_SERIAL_AT = 40                            # the 8-byte world serial in the save header (csrc/save.c): zeroed before comparing saves


# ---------------------------------------------------------------------------------------------------- helpers

def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, 1) == 0   # walkers, the shipped configuration
    return w


def _fired(lib, w):
    """Attacker ids of this tick's fire events (tactical event kind 0)."""
    k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
    out = set()
    for i in range(lib.om_tactical_event_count(w)):
        if lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and k.value == 0:
            out.add(a.value)
    return out


def _wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _off(facing, bearing):
    """The angle between a facing and a bearing, 0 to pi."""
    return abs(_wrap(bearing - facing))


def _lone(lib, wf, arc, off_deg):
    """One Vanguard at (500, 500) with a Supply 80 wu east (bearing 0) and the Supply's id; facing set so the target is off_deg degrees
    off it (off_deg 180: facing pi). arc None: the parameter is never set."""
    w = _world(lib, wf)
    if arc is not None:
        assert set_param(lib, w, "OM_TP_FIRING_ARC_DEG", arc) == 0
    a = spawn(lib, w, VANGUARD, 0, 500, 500)
    s = spawn(lib, w, SUPPLY, 1, 580, 500)
    lib.om_unit_set_hp(w, s, 1.0e6)
    lib.om_unit_set_facing(w, a, -math.radians(off_deg) if off_deg != 180 else math.pi)
    return w, a, s


def _lone_trace(lib, w, a, ticks):
    """Per tick n (1-based): the target after the tick, the facing before and after it, whether `a` fired."""
    rows = []
    for n in range(1, ticks + 1):
        f0 = lib.om_unit_get_facing(w, a)
        step(lib, w)
        rows.append(dict(n=n, target=lib.om_unit_target(w, a), f0=f0, f1=lib.om_unit_get_facing(w, a), fired=a in _fired(lib, w)))
    return rows


def _first_shot(rows):
    return next((r["n"] for r in rows if r["fired"]), None)


def _lone_first_shot(lib, wf, arc, off_deg, ticks=40):
    w, a, _ = _lone(lib, wf, arc, off_deg)
    return _first_shot(_lone_trace(lib, w, a, ticks))


# ---------------------------------------------------------------------------------------------------- R-091-01

def test_R_091_01_control_the_scene_shoots_on_tick_4_at_arc_360(lib, world_factory):
    """R-091-01 control (green today and after): at arc 360 the Vanguard facing away from its Supply holds it from tick 4 and fires on tick 4,
    so a red below means the arc is missing, not that the scene is broken."""
    w, a, s = _lone(lib, world_factory, 360, 180)
    rows = _lone_trace(lib, w, a, 6)
    assert [r["target"] for r in rows[:3]] == [-1, -1, -1] and rows[3]["target"] == s, "scene broken: %s" % [r["target"] for r in rows]
    assert _first_shot(rows) == FIRST_SHOT_TICK, "scene broken: first shot on tick %s" % _first_shot(rows)


@pytest.mark.parametrize("off_deg", [60, 90, 120, 135, 180, -135])
def test_R_091_01_a_unit_does_not_fire_that_tick_with_its_target_outside_the_arc(lib, world_factory, off_deg):
    """R-091-01, every tick, arc 90: on every tick that STARTS with the held target more than 45 degrees from the unit's facing the unit
    does not fire; it keeps the same target once it holds it; its facing moves toward the target by at most 0.2 rad a tick (and moves,
    while it is off); and it does fire once the target is within 45 degrees. Red today: it fires on tick 4 with the target off_deg off."""
    w, a, s = _lone(lib, world_factory, 90, off_deg)
    rows = _lone_trace(lib, w, a, 40)
    held = [r for r in rows if r["target"] == s]
    assert held and held[0]["n"] == FIRST_SHOT_TICK, "scene broken: target first held on tick %s" % (held[0]["n"] if held else None)
    assert all(r["target"] == s for r in rows[held[0]["n"] - 1:]), "the unit changed or lost its target: %s" % [r["target"] for r in rows]
    bearing = 0.0
    for r in rows:
        before, after = _off(r["f0"], bearing), _off(r["f1"], bearing)
        assert not (r["fired"] and before > math.radians(45.0) + EPS), \
            "tick %d: fired with its target %.1f degrees off its facing (arc 90 allows 45)" % (r["n"], math.degrees(before))
        assert abs(_wrap(r["f1"] - r["f0"])) <= LINE_TURN_PER_TICK + EPS, "tick %d: turned %.4f rad, more than the Line rate" % (r["n"], abs(_wrap(r["f1"] - r["f0"])))
        assert after <= before + EPS, "tick %d: facing moved away from the target (%.4f to %.4f rad off)" % (r["n"], before, after)
        if r["n"] >= FIRST_SHOT_TICK and before > EPS:
            assert after < before - EPS, "tick %d: the unit holding its target did not turn toward it (%.4f rad off)" % (r["n"], before)
    assert _first_shot(rows) is not None, "the unit never fired once its target was inside the arc"


def test_R_091_01_a_withheld_shot_is_not_a_lost_target_the_unit_fires_again_after_turning(lib, world_factory):
    """R-091-01, the first-tick clause: with the target directly behind, the shots begin on the first tick that starts inside 45 degrees
    (not later than two ticks after) and then repeat at the unit's attack interval, with the target kept throughout. Red today: the
    first shot is on tick 4."""
    w, a, s = _lone(lib, world_factory, 90, 180)
    rows = _lone_trace(lib, w, a, 60)
    first_inside = next(r["n"] for r in rows if _off(r["f0"], 0.0) <= math.radians(45.0) + EPS)
    shots = [r["n"] for r in rows if r["fired"]]
    assert shots and first_inside <= shots[0] <= first_inside + 2, "first tick starting inside the arc %d, shots %s" % (first_inside, shots)
    assert len(shots) >= 2 and all(r["target"] == s for r in rows[FIRST_SHOT_TICK - 1:]), "shots %s" % shots


# ---------------------------------------------------------------------------------------------------- R-091-03

def test_R_091_03_a_target_dead_ahead_is_shot_on_the_same_tick_as_at_arc_360(lib, world_factory):
    """R-091-03: target at 0 degrees, arc 90: the first shot is on the same tick as with the arc at 360 (control: green today and after)."""
    base = _lone_first_shot(lib, world_factory, 360, 0)
    assert base == FIRST_SHOT_TICK, "scene broken: arc 360 first shot on tick %s" % base
    assert _lone_first_shot(lib, world_factory, 90, 0) == base


def test_R_091_03_a_target_directly_behind_is_shot_12_to_14_ticks_later(lib, world_factory):
    """R-091-03: target at 180 degrees, arc 90: the first shot is later than the arc-360 shot by at least 12 ticks (135 degrees at 0.2 rad
    a tick) and by no more than 14. Red today: the delay is 0."""
    base = _lone_first_shot(lib, world_factory, 360, 180)
    shot = _lone_first_shot(lib, world_factory, 90, 180)
    assert shot is not None, "the unit never fired at arc 90 in 40 ticks"
    assert 12 <= shot - base <= 14, "first shot on tick %d against %d at arc 360: %d ticks later, not 12 to 14" % (shot, base, shot - base)


def test_R_091_03_a_narrower_arc_waits_longer(lib, world_factory):
    """R-091-03 (the turn the arc needs): from directly behind, arc 60 (half 30) needs 150 degrees of turn = 2.62 rad = 14 ticks at 0.2 rad
    (13.1 rounded up to 14), arc 180 (half 90) needs 90 degrees = 8 ticks (7.85 up): the delays are the ticks the turn needs, to within 2.
    Red today: both 0."""
    base = _lone_first_shot(lib, world_factory, 360, 180)
    for arc, need in ((180, 8), (60, 14)):
        shot = _lone_first_shot(lib, world_factory, arc, 180)
        assert shot is not None and need <= shot - base <= need + 2, "arc %d: first shot on tick %s, %s ticks after the arc-360 shot, expected %d to %d" % (arc, shot, None if shot is None else shot - base, need, need + 2)


# ---------------------------------------------------------------------------------------------------- R-091-06

@pytest.mark.parametrize("arc,half", [(90, 45), (180, 90), (60, 30), (120, 60), (10, 5)])
def test_R_091_06_a_target_at_exactly_half_the_arc_is_inside(lib, world_factory, arc, half):
    """R-091-06: 'the arc is the full angle centred on the facing: a target at exactly half the arc is inside': with the target exactly `half`
    degrees off the facing and the arc at `arc`, the first shot is on the same tick as at arc 360, whatever the arc value (values taken as
    set, 10 to 360). Green today (nothing is withheld); it must stay green when the arc is built, which is what an off-by-an-ulp edge breaks."""
    assert _lone_first_shot(lib, world_factory, arc, half) == _lone_first_shot(lib, world_factory, 360, half) == FIRST_SHOT_TICK


@pytest.mark.parametrize("arc,half", [(90, 46), (180, 91), (60, 31), (120, 61), (10, 6)])
def test_R_091_06_a_target_one_degree_beyond_half_the_arc_is_outside(lib, world_factory, arc, half):
    """R-091-06: one degree past half the arc is outside: the shot is withheld that tick (the target is off its facing at the start of tick 4),
    and comes after the unit has turned into the arc. Pairs with the 'exactly half' test above so an engine that withholds everything
    cannot pass both. Red today: the shot is on tick 4."""
    shot = _lone_first_shot(lib, world_factory, arc, half)
    assert shot is not None and shot > FIRST_SHOT_TICK, "first shot on tick %s with the target %d degrees off at arc %d (half %d)" % (shot, half, arc, arc // 2)


def test_R_091_06_the_arc_value_is_taken_as_set(lib, world_factory):
    """R-091-06 'values are taken as the parameter is set (10 to 360)': what was set is what the sim holds (10, 90, 360 read back), and the
    same scene (target 60 degrees off) is withheld at 90 and 10 and shot on tick 4 at 120, 180 and 360. Red today: 90 and 10 are shot on tick 4."""
    w = _world(lib, world_factory)
    for v in (10, 60, 90, 180, 360):
        assert set_param(lib, w, "OM_TP_FIRING_ARC_DEG", v) == 0
        assert get_param(lib, w, "OM_TP_FIRING_ARC_DEG") == v
    shots = {arc: _lone_first_shot(lib, world_factory, arc, 60) for arc in (10, 90, 120, 180, 360)}
    assert all(shots[arc] == FIRST_SHOT_TICK for arc in (120, 180, 360)), "scene broken: %s" % shots
    assert all(shots[arc] is not None and shots[arc] > FIRST_SHOT_TICK for arc in (10, 90)), "arc 10 and 90 did not withhold a shot at 60 degrees off: %s" % shots


# ---------------------------------------------------------------------------------------------------- a small fight (R-091-02, -04, -05)

def _fight(lib, wf, arc, ticks=160, save_at=None, load_into=None):
    """Three Vanguards attack-move east from x=100 toward three Vanguards standing at x=700 that face east, away from them (facing 0),
    so every defender must turn through 180 degrees before it may answer. Returns (world, ids, per-tick rows). Row: tick, the units'
    (target, order kind, has_dest, dest x, dest y, x, y, facing, hp), the fire set, the world checksum."""
    w = _world(lib, wf) if load_into is None else load_into
    if arc is not None:
        assert set_param(lib, w, "OM_TP_FIRING_ARC_DEG", arc) == 0
    ids = [spawn(lib, w, VANGUARD, 0, 100, 400 + 60 * i) for i in range(3)] + [spawn(lib, w, VANGUARD, 1, 700, 400 + 60 * i) for i in range(3)]
    for u in ids[3:]:
        lib.om_unit_set_facing(w, u, 0.0)
    attack_move(lib, w, ids[:3], 1500, 460)
    return w, ids


def _fight_rows(lib, w, ids, ticks, first_tick=1):
    rows = []
    for n in range(first_tick, first_tick + ticks):
        step(lib, w)
        units = []
        for u in ids:
            has, dx, dy = dest(lib, w, u)
            x, y = lib.om_unit_get_pos(w, u)
            units.append((lib.om_unit_target(w, u), lib.om_unit_get_order_kind(w, u), has, dx, dy, x, y, lib.om_unit_get_facing(w, u), lib.om_unit_get_hp(w, u)))
        rows.append(dict(n=n, units=units, fired=_fired(lib, w), checksum=lib.om_world_checksum(w)))
    return rows


def _save(lib, w):
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _comparable(buf, size):
    b = bytes(buf[:size])
    return b[:SAVE_SERIAL_AT] + bytes(8) + b[SAVE_SERIAL_AT + 8:]


def test_R_091_02_control_the_fight_shoots_both_ways_at_arc_360(lib, world_factory):
    """R-091-02 / R-091-04 / R-091-05 control (green today and after): the small fight at arc 360 has shots from both sides and the three
    attackers reach the defenders, so the arc-90 comparisons below are made on a fight that fights."""
    w, ids = _fight(lib, world_factory, 360)
    rows = _fight_rows(lib, w, ids, 160)
    shooters = set().union(*(r["fired"] for r in rows))
    assert shooters & set(ids[:3]) and shooters & set(ids[3:]), "scene broken: shooters %s of %s" % (sorted(shooters), ids)


def test_R_091_02_the_default_arc_and_an_explicit_360_give_byte_identical_traces(lib, world_factory):
    """R-091-02: with the arc never set and with it set to 360 the same small fight gives the same per-tick trace (checksum, positions,
    facing, targets, orders, destinations, hp, fire events) for 160 ticks. Green today and after; the existing goldens are left alone
    (tests/csim goldens, tests/skilllab/golden_hashes.json and the stage 3 and 4 fight files are not edited by this change)."""
    w1, ids1 = _fight(lib, world_factory, None)
    r1 = _fight_rows(lib, w1, ids1, 160)
    w2, ids2 = _fight(lib, world_factory, 360)
    r2 = _fight_rows(lib, w2, ids2, 160)
    assert ids1 == ids2
    bad = [(a["n"]) for a, b in zip(r1, r2) if a != b]
    assert not bad, "arc 360 differs from the unset default first on tick %d" % bad[0]


def test_R_091_02_control_the_fight_is_sensitive_to_the_arc(lib, world_factory):
    """R-091-02 positive control for the trace-equality test above: the same fight at arc 90 does not give the arc-360 trace (the defenders
    face away from the attackers, so the arc must withhold shots), so equality at 360 is not equality of a scene the arc cannot touch.
    Red today: the arc is read by nothing and the two traces are identical."""
    w1, ids1 = _fight(lib, world_factory, 360)
    r1 = _fight_rows(lib, w1, ids1, 160)
    w2, ids2 = _fight(lib, world_factory, 90)
    r2 = _fight_rows(lib, w2, ids2, 160)
    assert [r["fired"] for r in r1] != [r["fired"] for r in r2], "arc 90 and arc 360 give the same shots on all 160 ticks: the arc changed nothing"


# ---------------------------------------------------------------------------------------------------- R-091-04

def test_R_091_04_the_arc_changes_nothing_but_the_shot(lib, world_factory):
    """R-091-04: the same small fight at arc 90 and at arc 360, tick for tick: every unit's target (acquisition, the lock, return-fire
    targeting), order kind and destination are equal on every tick before the first tick on which the two runs' shots differ (a shot is
    withheld), and the targets are still equal on that tick. The first differing tick must exist and must not be tick 1 (else nothing was compared). Red today: the arc withholds
    nothing, the shots never differ."""
    w1, ids1 = _fight(lib, world_factory, 360)
    r360 = _fight_rows(lib, w1, ids1, 160)
    w2, ids2 = _fight(lib, world_factory, 90)
    r90 = _fight_rows(lib, w2, ids2, 160)
    first = next((a["n"] for a, b in zip(r360, r90) if a["fired"] != b["fired"]), None)
    assert first is not None, "no shot was withheld in 160 ticks at arc 90: the arc is not read"
    assert first > 1, "a shot was withheld on tick 1: nothing to compare before it"
    key = lambda row: [(t, order, has, dx, dy) for (t, order, has, dx, dy, *_rest) in row["units"]]
    for a, b in zip(r360, r90):
        if a["n"] > first:
            break
        if a["n"] < first:
            assert key(a) == key(b), "tick %d (first withheld shot on tick %d): targets, orders or destinations differ: %s against %s" % (a["n"], first, key(a), key(b))
        else:   # the tick of the withheld shot itself: R-091-01 'keeps the same target'; the lock is not the arc's to change
            assert [k[0] for k in key(a)] == [k[0] for k in key(b)], "tick %d (the first withheld shot): a target changed: %s against %s" % (first, key(a), key(b))


# ---------------------------------------------------------------------------------------------------- R-091-05

SAVE_TICK = 8


def test_R_091_05_control_a_save_at_arc_360_loads_and_continues_the_same_trace(lib, world_factory):
    """R-091-05 control (green today and after): the save/load path of this harness (as test_collision_radius.py
    test_H_041_control_a_save_without_radii_round_trips) continues the small fight's run tick for tick at arc 360."""
    w, ids = _fight(lib, world_factory, 360)
    _fight_rows(lib, w, ids, 30)
    buf, size = _save(lib, w)
    want = _fight_rows(lib, w, ids, 40, first_tick=31)
    b = _world(lib, world_factory)
    assert lib.om_load_state_read(b, buf, size) == 0
    assert _fight_rows(lib, b, ids, 40, first_tick=31) == want


def test_R_091_05_a_save_taken_mid_turn_at_arc_90_gives_the_same_later_frames(lib, world_factory):
    """R-091-05, one unit: a Vanguard facing away from its Supply, arc 90, saved on tick 8 (target held, mid-turn, first shot still withheld
    until tick 16), loaded into a fresh world; the loaded world reads the arc as 90 and gives, for 30 ticks, the same targets, facings and
    shots as the run that was not saved, including the shot on tick 16 and not one before it. Red today: with the arc ignored the
    first shot is on tick 4, before the save, so the precondition fails."""
    w, a, s = _lone(lib, world_factory, 90, 180)
    before = _lone_trace(lib, w, a, SAVE_TICK)
    buf, size = _save(lib, w)
    want = _lone_trace(lib, w, a, 30)
    assert _first_shot(before) is None and _first_shot(want) is not None and 12 + FIRST_SHOT_TICK <= SAVE_TICK + _first_shot(want) <= 14 + FIRST_SHOT_TICK, \
        "precondition: no shot before the save and the first one on tick 16 to 18 (arc 90, target behind); shots before %s, after (ticks past the save) %s" % (_first_shot(before), _first_shot(want))
    b = _world(lib, world_factory)
    assert lib.om_load_state_read(b, buf, size) == 0
    assert get_param(lib, b, "OM_TP_FIRING_ARC_DEG") == 90
    got = _lone_trace(lib, b, a, 30)
    key = lambda rows: [(r["target"], r["f0"], r["f1"], r["fired"]) for r in rows]
    assert key(got) == key(want), "the loaded run differs from the unsaved run (first shots: %s against %s)" % (_first_shot(got), _first_shot(want))


def test_R_091_05_a_fight_saved_mid_way_at_arc_90_gives_the_same_later_frames(lib, world_factory):
    """R-091-05, the small fight: saved on tick 30 with the arc at 90 and loaded into a fresh world, the next 60 ticks (checksum, positions,
    facing, targets, orders, hp, fire events) equal the unsaved run's; the arc-90 fight differs from the arc-360 fight after the save
    (precondition, so the saved arc matters). Red today: the precondition fails."""
    w, ids = _fight(lib, world_factory, 90)
    _fight_rows(lib, w, ids, 30)
    buf, size = _save(lib, w)
    want = _fight_rows(lib, w, ids, 60, first_tick=31)
    w3, ids3 = _fight(lib, world_factory, 360)
    _fight_rows(lib, w3, ids3, 30)
    other = _fight_rows(lib, w3, ids3, 60, first_tick=31)
    assert [r["fired"] for r in want] != [r["fired"] for r in other], "precondition: arc 90 and 360 shoot differently after tick 30"
    b = _world(lib, world_factory)
    assert lib.om_load_state_read(b, buf, size) == 0
    assert get_param(lib, b, "OM_TP_FIRING_ARC_DEG") == 90
    got = _fight_rows(lib, b, ids, 60, first_tick=31)
    bad = [x["n"] for x, y in zip(got, want) if x != y]
    assert not bad, "the loaded fight differs from the unsaved one from tick %d" % bad[0]


def test_R_091_05_two_runs_with_the_same_seed_give_byte_identical_traces(lib, world_factory):
    """R-091-05: two fresh worlds, same seed and commands, arc 90, the small fight for 160 ticks: every tick's row is equal and the final
    saves are byte for byte equal (the 8-byte world serial excluded, as test_collision_radius.py does). Needs the arc to bite to say anything
    about it: the arc-90 trace differs from arc 360 (red today)."""
    runs = []
    for _ in range(2):
        w, ids = _fight(lib, world_factory, 90)
        rows = _fight_rows(lib, w, ids, 160)
        buf, size = _save(lib, w)
        runs.append((rows, hashlib.sha256(_comparable(buf, size)).hexdigest()))
    assert runs[0][0] == runs[1][0], "the two runs' traces differ"
    assert runs[0][1] == runs[1][1], "the two runs' final saves differ"
    w, ids = _fight(lib, world_factory, 360)
    assert [r["fired"] for r in _fight_rows(lib, w, ids, 160)] != [r["fired"] for r in runs[0][0]], "the arc-90 trace equals the arc-360 trace: the arc is not read"
