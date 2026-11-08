"""E-11 S-087 / R-087-04 / R-096-02 / R-084-04 (engine rule fixes 2026-11-08, F2): a unit that moves under its own power does not fire
that tick, and the 0.5 s pause after a shot holds for group members too.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F2"; evidence docs/reports/2026-11-07-rule-enforcement.md and appendix A 2.3
(unit.c decides at P_c, tactical_move.c moves, the fire pass shoots at P_c+1 without asking whether the unit moved; group members use a
frozen speed_cap and ignore the backswing). Bug fix, not a story. The whole-fight twin is
tests/skilllab/arena/test_engine_rules_f2_move_or_fire.py.

Rule words (docs/bible/epics/E-11-*.md, E-13-*.md; ALG-60 docs/bible/algorithms.md):
  R-087-04  "walks toward it until the enemy is within attack range, then halts and fires"
  R-096-02  an attack-moving unit halts to fire and resumes the walk
  R-084-04  the 0.5 s pause after a shot: the unit does not move for it
Rule pins: R-087-04, R-096-02, R-084-04, ALG-60.

Observables per tick: om_unit_get_position before and after om_tactical_step, and the tactical fire events of that step
(om_tactical_event_get_at, kind 0, attacker in `a`). "Moved under its own power" is a displacement above OWN_MOVE with no unit within
the push radius; the scenes keep every neighbour farther than that, except in the one pushed-unit control, which makes the push on purpose.

Measured on the unfixed tree (2026-11-08): a lone Raider attack-moving toward a Supply 500 wu away fires its first shot on the tick it
moved (tick 40 flier, tick 42 walker, 7.5 wu that tick), then fires every 16 ticks halted. Two Bombards attack-moved together: the
shooter walks 2.5 wu a tick on the tick after its shot (a lone Bombard waits 10 ticks, then walks). Controls green today: a halted
unit fires, a plain mover never fires, a halted unit pushed by a neighbour on the tick it would fire still fires.

Detector bounds (not rules; DRAFT-inv-* in the spec, Westley's): OWN_MOVE 0.5 wu, BACKSWING 10 ticks (the pause is ticks 1 to 9 after the
shot; tick 10 is the first free one), FIRE_GAP_MAX 2 ticks between the last moving tick and the first shot.
"""
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, pos, set_param, spawn, step

BOMBARD = 4
OWN_MOVE = 0.5
BACKSWING = 10
FIRE_GAP_MAX = 2


def _world(lib, wf, walk):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    set_param(lib, w, "OM_TP_ROUTE_AROUND_TERRAIN", 1.0)
    if walk:
        for t in (RAIDER, VANGUARD, BOMBARD):
            assert lib.om_roster_set_movement_kind(w, t, 1) == 0
    return w


def _fired(lib, w):
    k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
    out = set()
    for i in range(lib.om_tactical_event_count(w)):
        if lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and k.value == 0:
            out.add(a.value)
    return out


def _trace(lib, w, ids, ticks):
    """[(tick, unit, displacement, fired)] for every unit and tick."""
    rows = []
    for n in range(1, ticks + 1):
        before = {u: pos(lib, w, u) for u in ids}
        step(lib, w)
        fired = _fired(lib, w)
        rows += [(n, u, math.dist(before[u], pos(lib, w, u)), u in fired) for u in ids]
    return rows


def _approach(lib, wf, walk, ticks=120):
    w = _world(lib, wf, walk)
    a = spawn(lib, w, RAIDER, 0, 100, 400)
    spawn(lib, w, SUPPLY, 1, 600, 400)
    attack_move(lib, w, [a], 1500, 400)
    return _trace(lib, w, [a], ticks)


# ------------------------------------------------------------------ red today

@pytest.mark.parametrize("walk", [False, True], ids=["flier", "walker"])
def test_R_087_04_a_unit_walking_into_range_does_not_fire_on_a_tick_it_moved(lib, world_factory, walk):
    """R-087-04 'walks toward it until the enemy is within attack range, then halts and fires': per tick, a shot is never fired on a tick on
    which the unit moved under its own power. Red today: the first shot is fired on the tick of the last step (7.5 wu moved)."""
    rows = _approach(lib, world_factory, walk)
    shots = [r for r in rows if r[3]]
    assert len(shots) >= 3, "scene broken: only %d shots in 120 ticks" % len(shots)
    moved = [(r[0], round(r[2], 2)) for r in shots if r[2] > OWN_MOVE]
    assert not moved, "fired on tick(s) on which it moved: %s" % moved[:3]


@pytest.mark.parametrize("walk", [False, True], ids=["flier", "walker"])
def test_R_087_04_the_first_shot_comes_on_the_tick_after_the_last_step(lib, world_factory, walk):
    """R-087-04: the unit halts, and fires on the next tick (spec F2: 'it fires on the next tick, when halted'; detector bound: within
    FIRE_GAP_MAX ticks). Red today: it fires on the last moving tick itself (gap 0)."""
    rows = _approach(lib, world_factory, walk)
    last_move = max(r[0] for r in rows if r[2] > OWN_MOVE and r[0] < min(x[0] for x in rows if x[3]) + 1)
    first_shot = min(r[0] for r in rows if r[3])
    assert 1 <= first_shot - last_move <= FIRE_GAP_MAX, "last step on tick %d, first shot on tick %d" % (last_move, first_shot)


def _bombards(lib, wf, walk, n):
    """n Bombards attack-moved together (one group) toward a Supply with 1 hp that the first shot kills; the shooter then has its target
    gone and resumes the walk, so any step it takes inside the pause is the pause being ignored."""
    w = _world(lib, wf, walk)
    us = [spawn(lib, w, BOMBARD, 0, 100, 400 + 40 * i) for i in range(n)]
    t = spawn(lib, w, SUPPLY, 1, 560, 400)
    lib.om_unit_set_hp(w, t, 1.0)
    attack_move(lib, w, us, 1500, 400)
    return _trace(lib, w, us, 150)


def _backswing_steps(rows):
    """Every (tick, unit, wu) that moved 1 to BACKSWING-1 ticks after a shot of its own."""
    shot, out = {}, []
    for n, u, d, f in rows:
        if f:
            shot[u] = n
        elif u in shot and 1 <= n - shot[u] <= BACKSWING - 1 and d > OWN_MOVE:
            out.append((n, u, round(d, 2)))
    return out


@pytest.mark.parametrize("walk", [False, True], ids=["flier", "walker"])
def test_R_084_04_two_units_attack_moved_together_do_not_move_in_the_pause_after_a_shot(lib, world_factory, walk):
    """R-084-04: no own-power displacement in ticks 1 to 9 after a shot, for group members as for lone units (spec F2: backswing applies to
    group members; tactical_move.c:2168 and :2491 use a frozen speed_cap). Red today (flier): the shooter walks 2.5 wu a tick from the
    tick after its shot."""
    rows = _bombards(lib, world_factory, walk, 2)
    assert any(r[3] for r in rows), "scene broken: nobody fired"
    bad = _backswing_steps(rows)
    assert not bad, "moved inside the pause after a shot: %s" % bad[:4]


# ------------------------------------------------------------------ green today: the controls that must stay

@pytest.mark.parametrize("walk", [False, True], ids=["flier", "walker"])
def test_R_084_04_control_a_lone_unit_keeps_the_pause_after_a_shot(lib, world_factory, walk):
    """Control (green today, the same scene with one Bombard): the lone unit does not move for 9 ticks after its shot and then walks on.
    Proves the scene and the detector, so the group test above is red for the group's sake."""
    rows = _bombards(lib, world_factory, walk, 1)
    shots = [r[0] for r in rows if r[3]]
    assert shots, "scene broken: the lone Bombard never fired"
    assert not _backswing_steps(rows)
    assert any(r[2] > OWN_MOVE and r[0] > shots[0] + BACKSWING for r in rows), "scene broken: the lone unit never walked on after the pause"


@pytest.mark.parametrize("walk", [False, True], ids=["flier", "walker"])
def test_R_087_04_control_a_halted_unit_with_an_enemy_in_range_fires_every_interval(lib, world_factory, walk):
    """Control (green today and after): an idle Raider with a Supply 160 wu away fires, halted, at least 3 times in 60 ticks, 16 ticks
    apart (attack interval 0.8 s). The skip of a moving unit must not touch a unit that stands still."""
    w = _world(lib, world_factory, walk)
    s = spawn(lib, w, RAIDER, 0, 400, 400)
    spawn(lib, w, SUPPLY, 1, 560, 400)
    rows = _trace(lib, w, [s], 60)
    shots = [r[0] for r in rows if r[3]]
    assert len(shots) >= 3 and all(r[2] <= OWN_MOVE for r in rows), "shots on ticks %s" % shots
    assert all(b - a == 16 for a, b in zip(shots, shots[1:])), "fire gaps %s" % [b - a for a, b in zip(shots, shots[1:])]


@pytest.mark.parametrize("walk", [False, True], ids=["flier", "walker"])
def test_R_097_10_control_a_plain_mover_never_fires(lib, world_factory, walk):
    """Control (green today and after): a unit on a plain move order walks past a Supply in range and never fires."""
    w = _world(lib, world_factory, walk)
    a = spawn(lib, w, RAIDER, 0, 100, 400)
    spawn(lib, w, SUPPLY, 1, 600, 380)
    lib.om_command_move(w, [a], 1, 1500.0, 400.0)
    rows = _trace(lib, w, [a], 150)
    assert sum(1 for r in rows if r[2] > OWN_MOVE) > 100, "scene broken: the mover did not walk"
    assert not [r for r in rows if r[3]], "a plain mover fired"


@pytest.mark.parametrize("walk", [False, True], ids=["flier", "walker"])
def test_R_087_04_control_a_halted_unit_pushed_by_a_neighbour_still_fires(lib, world_factory, walk):
    """Control (green today, must stay): 'a unit pushed by collision while halted still fires' (spec F2). A friendly Vanguard is spawned
    8 wu from the halted shooter at tick `when`; the overlap pushes the shooter 11 wu on the next step. Over every `when` from 0 to 19
    (so the fix's one-tick shift of the first shot cannot hide the scene) some run has the shooter pushed more than OWN_MOVE and firing
    on the same tick."""
    both = []
    for when in range(20):
        w = _world(lib, world_factory, walk)
        s = spawn(lib, w, RAIDER, 0, 400, 400)
        spawn(lib, w, SUPPLY, 1, 560, 400)
        step(lib, w, when)
        spawn(lib, w, VANGUARD, 0, 408, 400)
        first = _trace(lib, w, [s], 1)[0]
        if first[2] > OWN_MOVE and first[3]:
            both.append(when)
    assert both, "a halted unit that is pushed on the tick it would fire did not fire on any run of 20"
