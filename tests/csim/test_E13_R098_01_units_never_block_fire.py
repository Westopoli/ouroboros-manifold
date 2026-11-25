"""E-13 R-098-01 (S-098): units never block fire. Cover, walls and ground do.

Rule, word for word as it stands on main (docs/bible/epics/E-13-movement-and-command.md, R-098-01):
  "Given a ranged unit with an ally between it and its target, When it fires, Then the shot lands; friendly units never block fire."
Extended by Westley, 2026-11-25 (DEC-units-never-block-fire-2026-11-25, recorded by the story fire-blocking-docs):
  "The rule is units never block fire; only cover, walls and ground do."
so the rule covers friendly and enemy units, alive or dead, on the shooter's layer or another. The friendly-ally case on its own is
tests/csim/test_E13_S098_firing_through_friends.py; this file pins the rest, so the rule cannot change without a red test.
Engine side: csrc/tactical_move.c om_combat_can_shoot_from (consults no unit between the endpoints), csrc/unit.c (the firing-spot walk, F5, R-087-09,
starts only when the line is blocked).

Configuration: the shipped one for a csim scene (as test_E11_R087_09 sets it): tactical feature on, a 2000 x 2000 canvas, walking units (the kind is
set per scene and named below), planar obstacles by om_map_block_rect, routing around terrain on (OM_TP_ROUTE_AROUND_TERRAIN 1, its default), targeting
by sight on (its default). Scene (a flyer is the one exception, test_flyer_shooter): shooter A (faction 0) at (470, 395), target T (a Supply with 1e6 hp
that never fires, faction 1) at (630, 395), 160 wu away, inside the Vanguard's attack range 300. Blockers stand at about (550, 395). A is ordered to
attack T (om_command_attack_target), so a nearer enemy on the line does not become its target; the idle scenes (no order) use no enemy blocker, because an
idle unit takes the nearest enemy and a nearer one on the line would be its target.

What is asserted (a never-rule, so per tick, qualification 4): every tick of a 200-tick run, om_combat_can_shoot(A, T) reads 1; A fires its first shot on
the same tick as in the open control scene (same shooter, no blocker) and its shot ticks are the open scene's; T's hit points fall by the open scene's
amount; a blocker takes none of the shots; A never walks. Positive controls (they go red if cover or walls stop blocking): a cover disc on the line gives
can_shoot 0 on every tick and no shot from the ordered shooter (the idle shooter walks to a spot and fires later, test_R_098_01_idle...); a wall on the
shooter's layer does the same as the disc. A break that makes units block turns the
unit scenes red; a break that makes cover not block turns the controls red.
Shown red against a break of om_combat_can_shoot_from (named in the report of the story fire-blocking-docs, not here).
"""
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import BOMBARD, INTERCEPTOR, RAIDER, SUPPLY, VANGUARD, hp, pos, set_param, spawn, step

CANVAS = 2000.0
FLYING, WALKING = 0, 1              # om_movement_kind
A_XY, T_XY, MID, SPOT_XY = (470.0, 395.0), (630.0, 395.0), (550.0, 395.0), (630.0, 1100.0)
TICKS = 200                         # run length; the open scene fires its first shot on run tick 1
BIG_HP = 1.0e6                      # T and the enemy blockers never die
NEAR = 15.0                         # a unit within this of the segment is "on the line" (premise, not a rule number)
MOVED = 5.0                         # detector bound: "A walked" (Westley's to change)
LAYER_ALL = 4                       # om_map_block_rect upper layer, as test_E11_R087_09 uses


def _world(lib, wf, kind_of=None):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    set_param(lib, w, "OM_TP_ROUTE_AROUND_TERRAIN", 1.0)
    for utype, kind in (kind_of or {}).items():
        assert lib.om_roster_set_movement_kind(w, utype, kind) == 0
    return w


def _fired(lib, w):
    """{(attacker, target)} of the fire events (kind 0) of the last tick."""
    k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
    out = set()
    for i in range(lib.om_tactical_event_count(w)):
        if lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and k.value == 0:
            out.add((a.value, b.value))
    return out


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _run(lib, wf, shooter, kind, blockers=(), cover=None, wall=None, order=True, kill_first=(), spotter=False):
    """Build the scene, step once (the same pre-step in every scene, so the dead blockers are dead before the order), then run TICKS ticks.
    spotter: a friendly Interceptor far away that sees T, so an idle A acquires T behind cover or a wall (as test_E11_R087_09 does).
    blockers: [(unit type, faction, (x, y), layer)]. Returns a dict of what the run showed."""
    w = _world(lib, wf, {shooter: kind})
    a = spawn(lib, w, shooter, 0, *A_XY)
    t = spawn(lib, w, SUPPLY, 1, *T_XY)
    lib.om_unit_set_hp(w, t, BIG_HP)
    bl = [spawn(lib, w, ut, fac, xy[0], xy[1], lay) for ut, fac, xy, lay in blockers]
    for u, (ut, fac, xy, lay) in zip(bl, blockers):
        if fac == 1:
            lib.om_unit_set_hp(w, u, BIG_HP)
    for i in kill_first:
        lib.om_unit_set_hp(w, bl[i], 0.0)
    if cover:
        assert lib.om_map_add_cover(w, *cover) != 0
    if wall:
        assert lib.om_map_block_rect(w, *wall, 0, LAYER_ALL) == 0
    if spotter:
        spawn(lib, w, INTERCEPTOR, 0, *SPOT_XY)
    placed = sum(1 for u in bl if _seg_dist(pos(lib, w, u), A_XY, T_XY) <= NEAR)
    step(lib, w)    # the same pre-step in every scene: the killed blockers die before A is ordered or fires
    if order:
        arr = (ctypes.c_uint32 * 1)(a)
        assert lib.om_command_attack_target(w, arr, 1, t) == 0
    on_line = [u for u in bl if lib.om_unit_alive(w, u) and _seg_dist(pos(lib, w, u), pos(lib, w, a), pos(lib, w, t)) <= NEAR]
    dead = [u for u in bl if not lib.om_unit_alive(w, u)]
    out = dict(w=w, a=a, t=t, bl=bl, placed=placed, on_line=on_line, dead=dead, p0=pos(lib, w, a), hp0=hp(lib, w, t),
               bl_hp0={u: hp(lib, w, u) for u in bl}, shots=[], can=[], layer=lib.om_unit_get_layer(w, a))
    for n in range(1, TICKS + 1):
        step(lib, w)
        if (a, t) in _fired(lib, w):
            out["shots"].append(n)
        out["can"].append(bool(lib.om_combat_can_shoot(w, a, t)))
    out["moved"] = math.dist(out["p0"], pos(lib, w, a))
    out["damage"] = out["hp0"] - hp(lib, w, t)
    out["bl_hp1"] = {u: hp(lib, w, u) for u in bl}
    out["dist0"] = math.dist(out["p0"], pos(lib, w, t))
    return out


def _dump(name, r):
    print("premises %s: A->T %.0f wu, blockers %d (placed on the line %d, still on it %d, dead %d), first shot tick %s, shots %d, damage %.3f, moved %.1f, can_shoot all ticks %s"
          % (name, r["dist0"], len(r["bl"]), r["placed"], len(r["on_line"]), len(r["dead"]), r["shots"][:1], len(r["shots"]), r["damage"], r["moved"], all(r["can"])))


def _same_as_open(open_run, r, n_on_line, n_dead=0):
    """The R-098-01 Then: the line never read blocked, and the shooter fired exactly as with nothing between."""
    # packed units push each other apart in the pre-step, so "on the line" is counted twice: as placed, and as still standing there after it
    assert r["placed"] == n_on_line and len(r["dead"]) == n_dead, "scene broken: blockers not placed on the line / not dead as planned"
    assert len(r["on_line"]) >= (1 if n_on_line > n_dead else 0), "scene broken: no living unit is left on the line after the pre-step"
    assert r["dist0"] <= 300.0, "scene broken: T is out of A's attack range"
    assert all(r["can"]), "R-098-01: om_combat_can_shoot read 0 on a tick with only units on the line (a unit blocked fire)"
    assert r["shots"], "R-098-01: A never fired with only units on the line"
    assert r["shots"][0] == open_run["shots"][0], "R-098-01: A's first shot came on tick %s, not on its ready tick %s" % (r["shots"][0], open_run["shots"][0])
    assert r["shots"] == open_run["shots"], "R-098-01: A's shot ticks differ from the open scene's"
    assert r["damage"] == pytest.approx(open_run["damage"], abs=1e-6), "R-098-01: T took %.3f, the open scene's %.3f" % (r["damage"], open_run["damage"])
    assert r["moved"] < 1e-6, "R-098-01: A walked (a spot walk) with only units on the line"
    for u in r["bl"]:
        assert r["bl_hp1"][u] == r["bl_hp0"][u], "R-098-01: the shot landed on a unit on the line, not on T"


@pytest.fixture
def open_run(lib, world_factory):
    r = _run(lib, world_factory, VANGUARD, WALKING)
    _dump("open", r)
    assert all(r["can"]), "control broken: can_shoot reads 0 in the open scene"
    assert r["shots"][:1] == [1], "control broken: the open scene's first shot is not run tick 1"
    return r


def test_control_cover_and_wall_block_fire(lib, world_factory, open_run):
    """Positive control for the whole file (R-098-01, with R-098-02): a cover disc on the line, and a wall on the shooter's layer, each make
    om_combat_can_shoot read 0 on every tick and the ordered shooter, in range, never fires (the open scene fires 9 shots). If this goes red, cover or walls stopped blocking
    and the unit tests below prove nothing; if the unit tests go red and this is green, units began to block."""
    cover = _run(lib, world_factory, VANGUARD, WALKING, cover=(MID[0], MID[1], 20.0, 1.0))
    wall = _run(lib, world_factory, VANGUARD, WALKING, wall=(530.0, 380.0, 570.0, 410.0))
    _dump("cover", cover)
    _dump("wall", wall)
    for name, r in (("cover disc", cover), ("wall", wall)):
        assert not any(r["can"]), "control: a %s on the line did not block (can_shoot read 1 on some tick)" % name
        assert not r["shots"], "control: A fired through a %s on the line (%d shots; the open scene fires %d)" % (name, len(r["shots"]), len(open_run["shots"]))
        assert r["damage"] == 0.0, "control: T took damage through a %s" % name


def test_R_098_01_enemy_unit_between_does_not_block(lib, world_factory, open_run):
    """R-098-01 "units never block fire" (Westley, 2026-11-25): Given an enemy unit between the shooter and its target, When the shooter fires, Then
    can_shoot reads 1 on every tick, the shooter fires on its ready tick and the target takes the damage (the enemy between takes none)."""
    r = _run(lib, world_factory, VANGUARD, WALKING, blockers=[(SUPPLY, 1, MID, 0)])
    _dump("enemy between", r)
    _same_as_open(open_run, r, 1)


def test_R_098_01_dead_unit_on_the_line_does_not_block(lib, world_factory, open_run):
    """R-098-01 "units never block fire", dead units too: Given a unit killed first that lies on the line, When the shooter fires, Then the shot
    lands on its ready tick (A ordered to attack, and idle: the first shot of the idle run is the idle open scene's)."""
    r = _run(lib, world_factory, VANGUARD, WALKING, blockers=[(SUPPLY, 1, MID, 0), (SUPPLY, 0, (540.0, 395.0), 0)], kill_first=(0, 1))
    _dump("dead on the line", r)
    assert len(r["bl"]) == 2 and len(r["dead"]) == 2, "scene broken: the blockers are not dead"
    _same_as_open(open_run, r, 2, n_dead=2)


def test_R_098_01_thirty_packed_units_on_the_line_do_not_block(lib, world_factory, open_run):
    """R-098-01 "units never block fire": Given 30 units packed on the line, friends and enemies mixed, When the shooter fires, Then can_shoot reads 1
    on every tick and the shooter fires on its ready tick, the shots landing on T."""
    crowd = [(SUPPLY, i % 2, (500.0 + (i % 10) * 6.0, 395.0 + (i // 10 - 1) * 5.0), 0) for i in range(30)]
    r = _run(lib, world_factory, VANGUARD, WALKING, blockers=crowd)
    _dump("30 packed", r)
    _same_as_open(open_run, r, 30)
    assert sum(1 for u in r["bl"] if lib.om_unit_get_faction(r["w"], u) == 0) == 15, "scene broken: not 15 friends and 15 enemies"


def test_R_098_01_unit_on_another_layer_does_not_block(lib, world_factory, open_run):
    """R-098-01 "units never block fire": Given a unit on another layer standing on the line, When the shooter fires, Then the line reads clear and the
    shot lands on its ready tick."""
    r = _run(lib, world_factory, VANGUARD, WALKING, blockers=[(SUPPLY, 1, MID, 1), (SUPPLY, 0, (545.0, 395.0), 2)])
    _dump("other layers", r)
    _same_as_open(open_run, r, 2)


def test_R_098_01_walker_shooter_with_a_unit_on_the_line(lib, world_factory):
    """R-098-01 "units never block fire", walking shooter: Given a walking Raider (movement kind set to walking) with an enemy and a friend on the
    line, When it fires, Then it fires on its ready tick, as with nothing between."""
    base = _run(lib, world_factory, RAIDER, WALKING)
    r = _run(lib, world_factory, RAIDER, WALKING, blockers=[(SUPPLY, 1, MID, 0), (SUPPLY, 0, (520.0, 395.0), 0)])
    _dump("walker open", base)
    _dump("walker blocked by units", r)
    assert lib.om_unit_profile_movement_kind(r["w"], RAIDER) == WALKING, "scene broken: the Raider is not walking"
    _same_as_open(base, r, 2)


def test_R_098_01_flyer_shooter_with_a_unit_on_the_line(lib, world_factory):
    """R-098-01 "units never block fire", flying shooter: Given a flying Interceptor (movement kind flying; the switch that differs from the walking
    scenes, since fire must not depend on the kind) with an enemy and a friend on the line, When it fires, Then it fires on its ready tick."""
    base = _run(lib, world_factory, INTERCEPTOR, FLYING)
    r = _run(lib, world_factory, INTERCEPTOR, FLYING, blockers=[(SUPPLY, 1, MID, 0), (SUPPLY, 0, (520.0, 395.0), 0)])
    _dump("flyer open", base)
    _dump("flyer blocked by units", r)
    assert lib.om_unit_profile_movement_kind(r["w"], INTERCEPTOR) == FLYING, "scene broken: the Interceptor is not flying"
    _same_as_open(base, r, 2)


def test_R_098_01_idle_unit_with_a_unit_on_its_line_does_not_start_a_spot_walk(lib, world_factory):
    """R-098-01 "units never block fire", and the firing-spot walk (E-11 R-087-09, csrc/unit.c: an idle unit looks for a spot only when the line is
    blocked): Given an idle shooter (no order) whose target is in range and a friend, and a dead unit, on the line, When it acts, Then it does not
    walk, and fires on the same tick as the idle shooter with nothing between. Control in the same test: with a cover disc on the line the idle
    shooter does walk and fires later."""
    base = _run(lib, world_factory, VANGUARD, WALKING, order=False)
    r = _run(lib, world_factory, VANGUARD, WALKING, order=False,
             blockers=[(SUPPLY, 0, MID, 0), (SUPPLY, 1, (540.0, 395.0), 0), (SUPPLY, 0, (560.0, 395.0), 0)], kill_first=(1,))
    cov = _run(lib, world_factory, VANGUARD, WALKING, order=False, cover=(MID[0], MID[1], 20.0, 1.0), spotter=True)
    _dump("idle open", base)
    _dump("idle with friends and a dead unit on the line", r)
    _dump("idle with cover on the line", cov)
    assert base["shots"], "control broken: the idle open scene does not fire"
    assert r["placed"] == 3 and len(r["on_line"]) == 2 and len(r["dead"]) == 1, "scene broken: two living friends on the line and one dead unit expected"
    assert all(r["can"]), "R-098-01: can_shoot read 0 for an idle shooter with only units on the line"
    assert r["moved"] < 1e-6, "R-098-01: the idle shooter started a firing-spot walk because of units on the line"
    assert r["shots"][0] == base["shots"][0], "R-098-01: the idle shooter's first shot came on tick %s, not %s" % (r["shots"][0], base["shots"][0])
    assert r["damage"] == pytest.approx(base["damage"], abs=1e-6)
    assert cov["moved"] > MOVED and cov["shots"][0] > base["shots"][0], "control: cover on the line did not start the idle shooter's spot walk"


def test_R_098_01_unit_blocks_neither_direction_of_can_shoot(lib, world_factory):
    """R-098-01 "units never block fire": Given one enemy on the line between two units that face each other, When can_shoot is asked in both
    directions (no tick run), Then both read 1; the same line with a cover disc reads 0 both ways (control)."""
    for cover, want in ((None, 1), ((MID[0], MID[1] + 0.0, 20.0, 1.0), 0)):
        w = _world(lib, world_factory)
        a = spawn(lib, w, VANGUARD, 0, *A_XY)
        t = spawn(lib, w, VANGUARD, 1, *T_XY)
        spawn(lib, w, SUPPLY, 1, *MID)
        spawn(lib, w, SUPPLY, 0, MID[0] + 3.0, MID[1])
        if cover:
            assert lib.om_map_add_cover(w, *cover) != 0
        print("premises both ways: cover=%s can_shoot a->t %d t->a %d" % (cover, lib.om_combat_can_shoot(w, a, t), lib.om_combat_can_shoot(w, t, a)))
        assert lib.om_combat_can_shoot(w, a, t) == want and lib.om_combat_can_shoot(w, t, a) == want
