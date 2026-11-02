"""PP-unit: the leash anchor is where the target was ACQUIRED (E-11 R-087-05, E-13 R-096-03;
ALG-68 "Attack-move leash 200 wu from the acquisition anchor"; rulings-2 A167, A168; contract call
`om_unit_get_leash_anchor`, docs/northstar/plans/push/pp_contract.md item 16).

A167 suspects the anchor is the spot where the ORDER started, so a unit more than 200 wu into a march
drops every target. Phase B trace: front pair in range at 268 wu with no target for ticks 55 to 65.

Scenes (Vanguard: range 300, sensor 700, 4 wu per tick, march goal (0, -3000), Supply target: 100 hp,
never fires). Each test runs with OM_TP_LEASH_BEFORE_DAMAGE 0 (today's order, default) and 1.

RE-RUN THE LEASH TABLE AFTER THE FIX (not run here; A168 says the table is re-run after A167 lands):
    cd <repo>; for L in 0 1: build the plays with settings {"OM_TP_LEASH_BEFORE_DAMAGE": L}
    python3 -m scripts.skilllab controls --out <dir>_leash0     (settings 0)
    python3 -m scripts.skilllab controls --out <dir>_leash1     (settings 1)
The `controls` command has no settings flag today (scripts/skilllab/plays.py builds Setups with an empty
`settings`; contract.Setup.settings is applied before tick 1 by fight.py). So set it per run by wrapping
the play, e.g. `dataclasses.replace(setup, settings={"OM_TP_LEASH_BEFORE_DAMAGE": L})` around
plays.blob_play / plays.damage_play in scripts/skilllab/__main__.py `_controls` (harness owner's edit, not
this fence), then compare the two out dirs' controls.csv: fight length, stalled fights, and the break-even
headcount. Pass the same seeds both ways.
"""
import ctypes

import pytest

from conftest import OMWorldP
from test_PP_unit_support import (SUPPLY, VANGUARD, attack_move, hp, pos, set_param, spawn, step,
                                  target, watch_target)

LEASH = "OM_TP_LEASH_BEFORE_DAMAGE"
SWITCHES = pytest.mark.parametrize("switch", [0, 1], ids=["leash_after_damage_0", "leash_before_damage_1"])


def _anchor(lib, w, uid):
    """(returned, x, y) from om_unit_get_leash_anchor; a missing symbol fails naming it."""
    if not hasattr(lib, "om_unit_get_leash_anchor"):
        pytest.fail("contract missing: om_unit_get_leash_anchor is not exported by libouroboros.so")
    fn = lib.om_unit_get_leash_anchor.raw if hasattr(lib.om_unit_get_leash_anchor, "raw") else lib.om_unit_get_leash_anchor
    fn.argtypes = [OMWorldP, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
    fn.restype = ctypes.c_int
    x, y = ctypes.c_double(), ctypes.c_double()
    return fn(w, uid, ctypes.byref(x), ctypes.byref(y)), x.value, y.value


def _marched_unit(lib, w, switch, march_ticks=75):
    """Vanguard attack-moving to (0, -3000), with nothing in sight (enemy 5000 wu away), 75 ticks = 300 wu in."""
    assert set_param(lib, w, LEASH, switch) == 0
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 5000.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, march_ticks)
    assert pos(lib, w, u)[1] < -250.0, "fixture: the unit should be 300 wu into the march"
    return u, enemy


def _acquire_ahead(lib, w, u, enemy, ahead):
    """Put the enemy `ahead` wu in front of the marching unit (inside its 300 wu range) and run until the
    unit holds it (a cohort cycle is 20 ticks)."""
    ux, uy = pos(lib, w, u)
    lib.om_unit_teleport(w, enemy, ux, uy - ahead, 0)
    for _ in range(25):
        step(lib, w)
        if target(lib, w, u) == enemy:
            return pos(lib, w, u)
    pytest.fail("fixture: the unit never acquired a target %s wu ahead, in range" % ahead)


@SWITCHES
def test_R_087_05_target_taken_300_wu_into_a_march_is_kept_and_shot(lib, world_factory, switch):
    """R-087-05 / R-096-03, A167: the unit is 300 wu into its march (268+ wu from the order start) when a
    target comes into range 150 wu ahead (inside the 200 wu leash of the spot where it is acquired). It keeps
    that target on every tick for 30 ticks and its hp falls. Red today means the drop measured from the order
    start (or from a sensor sighting) and not from the acquisition spot."""
    w = world_factory(n_regions=1)
    u, enemy = _marched_unit(lib, w, switch)
    _acquire_ahead(lib, w, u, enemy, 150.0)
    before = hp(lib, w, enemy)

    seen = watch_target(lib, w, u, 30)

    assert seen == [enemy] * 30, f"a target inside 200 wu of its acquisition spot was dropped: {seen}"
    assert hp(lib, w, enemy) < before, "the held target in range was never fired at"


@SWITCHES
def test_R_087_05_mutual_approach_target_is_held_every_tick_once_in_range(lib, world_factory, switch):
    """The Phase B scene in two units (R-087-05, R-096-03, A167): Vanguards 682 wu apart attack-move at each
    other (each sees the other at 700 wu, sensor). Once the pair is inside range (300 wu) and a cohort cycle
    (24 ticks) has passed, each must hold the other on every tick while the target is within 200 wu of its anchor (see the test-defect note below). Red before the fix: the sighting at about 700 wu sets the anchor there (`om_tac_pursue_goal`, unit.c),
    so the target is always more than 200 wu from its anchor and is dropped on the next tick, then
    re-sighted on the next cohort turn; the target flickers 1 tick in 4 and the units walk on to about 190 wu.
    Positive control: the same measure reads 'dropped' in the control test below."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, LEASH, switch) == 0
    a = spawn(lib, w, VANGUARD, 0, -341.0, 0.0)
    b = spawn(lib, w, VANGUARD, 1, 341.0, 0.0)
    attack_move(lib, w, [a], 3000.0, 0.0)
    attack_move(lib, w, [b], -3000.0, 0.0)
    for _ in range(120):
        step(lib, w)
        if pos(lib, w, b)[0] - pos(lib, w, a)[0] <= 300.0:
            break
    else:
        pytest.fail("fixture: the pair never closed to 300 wu in 120 ticks")
    step(lib, w, 24)    # two 12-tick cohort cycles to take a target in range

    # Test-defect, A172: a Vanguard's range (300 wu) is longer than the leash (200 wu, ALG-68 "from the
    # acquisition anchor"). The Python reference does the same: simulation/movement.py
    # `_update_attack_move_state` (lines 279-296) drops the target when its distance from the anchor
    # (where the unit stood when it took the target) is over 200 wu. So "held every tick once in range"
    # holds only while the target is within the leash of the anchor. A drop is allowed only when the target
    # is beyond the leash (slack 8 wu: both units walk 4 wu in the tick). Before the fix it flickered
    # 1 tick in 4 with the target well inside 200 wu of the anchor.
    drops_inside_leash, held, dropped_outside = [], 0, 0
    for _ in range(30):
        was_held = target(lib, w, a) == b
        got, ax, ay = _anchor(lib, w, a)
        step(lib, w)
        now_held = target(lib, w, a) == b
        held += now_held
        if was_held and got == 1 and not now_held:
            bx, by = pos(lib, w, b)
            d = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
            if d <= 192.0:
                drops_inside_leash.append(round(d, 1))
            else:
                dropped_outside += 1

    assert not drops_inside_leash, f"a target within the leash of its anchor was dropped (distances): {drops_inside_leash}"
    assert held >= 1, "the pair never held each other in range"


@SWITCHES
def test_R_087_05_target_sighted_by_sensor_is_held_when_it_comes_into_range(lib, world_factory, switch):
    """Guard (green today; a still target is re-acquired in range on a cohort turn): a Supply 1000 wu ahead is sighted at 700 wu (sensor), the unit walks
    on and gets it in range at 300 wu (y -700) after about 175 ticks. It must hold it and fire by tick 260.
    Ruling needed if this is judged a different rule (a sighting is not an acquisition): the unit then should
    re-acquire in range and anchor there, which this test also accepts, since it asserts only the hit."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, LEASH, switch) == 0
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 0.0, -1000.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 260)

    assert pos(lib, w, u)[1] <= -690.0, "fixture: the unit should have reached the target's range"
    assert hp(lib, w, enemy) < 100.0, "the unit walked into range of the target and never fired at it"


@SWITCHES
def test_control_R_087_05_target_leaving_200_of_the_acquisition_spot_is_dropped(lib, world_factory, switch):
    """Positive control (the leash still works), re-pinned to A188 (the leash tests the unit's OWN distance
    from its anchor): the same 300 wu in scene; the target is held 150 wu ahead, then the UNIT is moved to 250
    wu from the acquisition spot (the target stays in range 300). It is dropped within a cohort cycle.
    Measured from the acquisition spot, so it distinguishes a leash that works from one that never drops."""
    w = world_factory(n_regions=1)
    u, enemy = _marched_unit(lib, w, switch)
    ax, ay = _acquire_ahead(lib, w, u, enemy, 150.0)
    lib.om_unit_teleport(w, u, ax + 750.0, ay, 0)

    seen = watch_target(lib, w, u, 25)

    assert -1 in seen, f"a unit 250 wu from the acquisition spot never dropped its target: {seen}"


@SWITCHES
def test_R_087_05_leash_anchor_getter_reads_the_acquisition_point_not_the_order_start(lib, world_factory, switch):
    """Contract item 16: om_unit_get_leash_anchor returns 1 and the unit's position at acquisition (about
    300 wu down the march, y about -300 to -320), and not the order start (0, 0). Returns 0 before any target
    is held, and 0 for an unknown unit."""
    w = world_factory(n_regions=1)
    u, enemy = _marched_unit(lib, w, switch)
    assert _anchor(lib, w, u)[0] == 0, "no target held yet: there is no anchor"
    assert _anchor(lib, w, 0xFFFFFF)[0] == 0

    ax, ay = _acquire_ahead(lib, w, u, enemy, 150.0)
    got, x, y = _anchor(lib, w, u)

    assert got == 1, "a unit holding a target under an attack-move has an anchor"
    assert (x, y) == pytest.approx((ax, ay), abs=1e-6) or abs(y - ay) <= 20.0, \
        f"anchor {(x, y)} is not the acquisition spot near {(ax, ay)}"
    assert y < -250.0, f"anchor y {y} is the order start (0, 0), not the acquisition spot"
