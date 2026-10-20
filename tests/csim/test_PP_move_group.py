# Rule pins: R-087-04@edc84b, R-095-01@d24419, R-095-02@47ddf5, R-095-03@f360de, R-095-04@d31828, R-095-06@efed7d, R-095-07@9c81ee, R-096-02@dbc10f, R-096-03@915cb9
"""PP-move rule tests, groups (P5), the movement switches, and the settings contract.

Proves E-13 R-095-01, R-095-02, R-095-03, R-095-06, R-096-02 (S-095, S-096), as reworded by Addendum 45
(docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md, rows P5 and "Settings"), and the
OM_TP_PURSUE_BY_STEERING switch of P1 (the half of it that lives in the movement step: the pursuit goal is walked
by the ordinary step, with steering and collision).

Group orders go through `om_command_group_move` (a move) and `om_command_attack_move` with two or more units
(an attack-move: slots, as R-095-02 to R-095-04). A unit attack-moved alone is not a group and a group resumes after every fight just as the lone unit does (R-096-02,
Westley: "It should resume its prior goal after the fight is completed.", rewritten 2026-10-13).

Not written here: the leash (R-096-03, unit.c), pursuit target choice and the first-shot timing (P1, P2, P6; PP-unit).
Not written, needs the grid: R-095-04 (a blocked slot falls back to the click point), in test_PP_move_route.py.
"""
import ctypes
import math
import pathlib
import re

import pytest

from conftest import OMFeature

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = 0, 1, 2, 3, 4, 5
FRIEND, ENEMY = 0, 1
POS_TOL = 0.05
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _arr(ids):
    return (ctypes.c_uint32 * len(ids))(*ids)


def _step_len(lib, w, u):
    x0, y0 = lib.om_unit_get_pos(w, u)
    lib.om_tactical_step(w)
    x1, y1 = lib.om_unit_get_pos(w, u)
    return math.hypot(x1 - x0, y1 - y0)


def _step_lens(lib, w, ids):
    """One tactical tick; the distance each listed unit moved in it."""
    before = [lib.om_unit_get_pos(w, u) for u in ids]
    lib.om_tactical_step(w)
    return [math.hypot(lib.om_unit_get_pos(w, u)[0] - x, lib.om_unit_get_pos(w, u)[1] - y)
            for u, (x, y) in zip(ids, before)]


def _tp(name):
    """Value of an `om_tac_param` enum member, read from csrc/ouroboros_sim.h. The contract piece (PP-contract) has
    not landed, so today this fails with 'no enum om_tac_param': part of the red."""
    text = (REPO_ROOT / "csrc/ouroboros_sim.h").read_text()
    m = re.search(r"enum\s+(?:om_tac_param\s*)?\{([^{}]*?\bOM_TP_[A-Z0-9_]+[^{}]*?)\}\s*(?:om_tac_param)?\s*;", text, re.S)
    assert m, "csrc/ouroboros_sim.h has no enum om_tac_param (PP-contract has not landed)"
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    nxt = 0
    for item in body.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            key, val = [t.strip() for t in item.split("=", 1)]
            nxt = int(val, 0)
        else:
            key = item
        if key == name:
            return nxt
        nxt += 1
    raise AssertionError(f"{name} is not a member of om_tac_param")


def _set_param(lib, w, name, value):
    return lib.om_tactical_set_param(w, _tp(name), float(value))


def _get_param(lib, w, name):
    lib.om_tactical_get_param.restype = ctypes.c_double
    return lib.om_tactical_get_param(w, _tp(name))


# ---------------------------------------------------------------- settings contract

@pytest.mark.parametrize("name", ["OM_TP_PURSUE_BY_STEERING", "OM_TP_ROUTE_AROUND_TERRAIN"])
def test_PP_contract_movement_switches_default_to_1_and_refuse_out_of_range(lib, tw, name):
    """Plan Phase A row "Settings" and the appendix: both switches default to 1 (the new behaviour); 0 gives the
    old behaviour; a value out of range is refused (-1) and changes nothing. Red until PP-contract lands the call."""
    assert _get_param(lib, tw, name) == 1.0
    assert _set_param(lib, tw, name, 0) == 0
    assert _get_param(lib, tw, name) == 0.0
    assert _set_param(lib, tw, name, 7) == -1
    assert _get_param(lib, tw, name) == 0.0, "a refused value changed the setting"
    assert _set_param(lib, tw, name, 1) == 0
    assert _get_param(lib, tw, name) == 1.0


# ---------------------------------------------------------------- the speed cap and the detach (R-095-01, R-095-06)

def test_R_095_01_group_moves_at_the_slowest_members_pace(lib, tw):
    """R-095-01: a group of 2 or more is capped at the slowest member's base speed, fixed at order time. A Raider
    (7.5 wu/tick alone) group-moved with a Vanguard (4 wu/tick) steps 4 wu per tick. Green today."""
    r = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    v = lib.om_unit_spawn(tw, VANGUARD, FRIEND, 0.0, 100.0, 0)
    lib.om_command_group_move(tw, _arr([r, v]), 2, 3000.0, 50.0)
    for _ in range(3):
        assert _step_len(lib, tw, r) == pytest.approx(4.0, abs=0.01)


def test_R_095_01_a_unit_that_uses_a_movement_ability_leaves_the_group(lib, tw):
    """R-095-01 (Q-095-01, Westley's ruled difference from the Python): a unit that activates a movement ability
    leaves the group and moves at its boosted speed. The Raider's Surge multiplies speed by 2.5: 150 x 2.5 = 375
    wu/s = 18.75 wu per tick, where the group cap of 4 would hold it. The Vanguard keeps its 4 wu per tick.
    The C keeps the cap on a surging unit."""
    r = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    v = lib.om_unit_spawn(tw, VANGUARD, FRIEND, 0.0, 100.0, 0)
    lib.om_command_group_move(tw, _arr([r, v]), 2, 3000.0, 50.0)
    assert _step_len(lib, tw, r) == pytest.approx(4.0, abs=0.01), "scene error: group cap not applied before the ability"
    lib.om_command_activate_ability(tw, _arr([r]), 1)
    assert lib.om_unit_has_active_buff(tw, r, b"surge") == 1
    for _ in range(3):
        dr, dv = _step_lens(lib, tw, [r, v])
        assert dr == pytest.approx(18.75, abs=0.05), f"surging unit still capped at the group pace: {dr}"
        assert dv == pytest.approx(4.0, abs=0.01)


def test_R_095_06_a_subset_forms_its_own_group_and_the_old_group_continues(lib, tw):
    """R-095-06: the player selects a subset and issues a new move: the subset forms a new group at its own slowest
    pace, the old group continues without it. Group of Raider, Vanguard, Bastion (slowest 40 wu/s = 2 wu/tick);
    then Raider and Vanguard are re-ordered alone: they now step 4 wu per tick (the Vanguard's pace) and the
    Bastion keeps 2 wu per tick. Regression, expected green today."""
    r = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    v = lib.om_unit_spawn(tw, VANGUARD, FRIEND, 0.0, 100.0, 0)
    b = lib.om_unit_spawn(tw, BASTION, FRIEND, 0.0, 200.0, 0)
    lib.om_command_group_move(tw, _arr([r, v, b]), 3, 3000.0, 100.0)
    assert _step_len(lib, tw, r) == pytest.approx(2.0, abs=0.01), "scene error: the three-unit cap is the Bastion's"
    lib.om_command_group_move(tw, _arr([r, v]), 2, 3000.0, 50.0)
    dr, dv, db = _step_lens(lib, tw, [r, v, b])
    assert dr == pytest.approx(4.0, abs=0.01)
    assert dv == pytest.approx(4.0, abs=0.01)
    assert db == pytest.approx(2.0, abs=0.01)


# ---------------------------------------------------------------- attack-move takes slots (R-096-02, R-095-02, R-095-03)

def test_R_096_02_attack_move_group_takes_formation_slots(lib, tw):
    """R-096-02 / R-095-02: two or more units attack-moved together take formation slots as a move group does: each
    destination is the click point plus the unit's offset from the selection's centroid. A (0,0) and B (60,0) have
    centroid (30,0): attack-move to (1000,500) gives A (970,500) and B (1030,500). The C sends both to (1000,500)."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 60.0, 0.0, 0)
    lib.om_command_attack_move(tw, [a, b], 2, 1000.0, 500.0)
    assert lib.om_unit_get_destination(tw, a) == pytest.approx((970.0, 500.0), abs=POS_TOL)
    assert lib.om_unit_get_destination(tw, b) == pytest.approx((1030.0, 500.0), abs=POS_TOL)


def test_R_096_02_a_lone_attack_moved_unit_gets_the_click_point(lib, tw):
    """R-096-02 / R-095-07: a unit attack-moved alone is not a group: its destination is the click point. Positive
    control for the slot test (offsets belong only to groups of two or more). Green today."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    lib.om_command_attack_move(tw, a, 1000.0, 500.0)
    assert lib.om_unit_get_destination(tw, a) == pytest.approx((1000.0, 500.0), abs=POS_TOL)


def test_R_095_03_attack_move_scatter_fallback_beyond_450(lib, tw):
    """R-095-03 applied to attack-move (R-096-02): any unit farther than 450 wu from the centroid at command time
    sends every unit to the raw click point. A (0,0) and B (1000,0): each is 500 from the centroid. Control: at
    800 apart (400 each) slots apply, A (600,500) and B (1400,500) for a click at (1000,500)."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 1000.0, 0.0, 0)
    lib.om_command_attack_move(tw, [a, b], 2, 1000.0, 500.0)
    assert lib.om_unit_get_destination(tw, a) == pytest.approx((1000.0, 500.0), abs=POS_TOL)
    assert lib.om_unit_get_destination(tw, b) == pytest.approx((1000.0, 500.0), abs=POS_TOL)

    c = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 2000.0, 0)
    d = lib.om_unit_spawn(tw, RAIDER, FRIEND, 800.0, 2000.0, 0)
    lib.om_command_attack_move(tw, [c, d], 2, 1000.0, 500.0)
    assert lib.om_unit_get_destination(tw, c) == pytest.approx((600.0, 500.0), abs=POS_TOL)
    assert lib.om_unit_get_destination(tw, d) == pytest.approx((1400.0, 500.0), abs=POS_TOL)


# ---------------------------------------------------------------- the group and the lone unit both resume (R-096-02)

def _fight_scene(lib, w, friend_positions, enemy_positions, unit_type=VANGUARD):
    friends = [lib.om_unit_spawn(w, unit_type, FRIEND, x, y, 0) for (x, y) in friend_positions]
    enemies = [lib.om_unit_spawn(w, RAIDER, ENEMY, x, y, 0) for (x, y) in enemy_positions]
    return friends, enemies


def _run_until(lib, w, cond, limit=40):
    for _ in range(limit):
        if cond():
            return True
        lib.om_tactical_step(w)
    return cond()


def _kill(lib, w, ids):
    for e in ids:
        lib.om_unit_set_hp(w, e, 0.0)


def test_R_096_02_group_resumes_after_every_member_has_engaged(lib, tw):
    """R-096-02 (rewritten 2026-10-13, option (a); TD-LAB-REV2-E1-1 replaces the old group-ends test): once every member
    of an attack-move group has engaged, the group still resumes toward its point after the fight, as a unit attack-moved
    alone does. Vanguards A (0,0) and B (0,60), attack-moved together to (1000,0); enemy Raiders 150 wu ahead of each,
    inside the Vanguard's 300 wu range. Both engage; the enemies are then removed; within 10 ticks both Vanguards march
    on toward the point (+x)."""
    (a, b), (e1, e2) = _fight_scene(lib, tw, [(0.0, 0.0), (0.0, 60.0)], [(150.0, 0.0), (150.0, 60.0)])
    lib.om_command_attack_move(tw, [a, b], 2, 1000.0, 0.0)
    assert _run_until(lib, tw, lambda: lib.om_unit_get_target(tw, a) != 0 and lib.om_unit_get_target(tw, b) != 0), \
        "scene error: both Vanguards did not engage"
    _kill(lib, tw, [e1, e2])
    lib.om_tactical_step(tw)
    lib.om_tactical_step(tw)
    xa, xb = lib.om_unit_get_pos(tw, a)[0], lib.om_unit_get_pos(tw, b)[0]
    for _ in range(10):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, a)[0] > xa + 10.0, "member A did not resume the march after the fight"
    assert lib.om_unit_get_pos(tw, b)[0] > xb + 10.0, "member B did not resume the march after the fight"


def test_R_096_02_group_has_not_ended_while_a_member_has_not_engaged(lib, tw):
    """R-096-02 (control for the group-resume test): while one member has never engaged, the group marches on, and an
    engaged member resumes toward its slot when its target dies. Vanguards A (0,0) and B (0,-800) (centroid (0,-400),
    each 400 from it, so slots apply); one enemy Raider at (200,0): in A's range, 824 from B (beyond its sensor 700),
    so only A engages. After the enemy is removed A marches on (+x)."""
    (a, b), (e,) = _fight_scene(lib, tw, [(0.0, 0.0), (0.0, -800.0)], [(200.0, 0.0)])
    lib.om_command_attack_move(tw, [a, b], 2, 3000.0, 0.0)
    assert _run_until(lib, tw, lambda: lib.om_unit_get_target(tw, a) != 0), "scene error: A did not engage"
    assert lib.om_unit_get_target(tw, b) == 0, "scene error: B engaged as well"
    _kill(lib, tw, [e])
    lib.om_tactical_step(tw)
    lib.om_tactical_step(tw)
    x0 = lib.om_unit_get_pos(tw, a)[0]
    for _ in range(10):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, a)[0] > x0 + 10.0, "A did not resume while the group was still alive"


def test_R_096_02_lone_attack_moved_unit_resumes_after_the_fight(lib, tw):
    """R-096-02, Westley 2026-10-02: "It should resume its prior goal after the fight is completed." A unit
    attack-moved alone resumes toward its point after every fight, and since 2026-10-13 a group does too. Vanguard A
    (0,0) to (3000,0); an enemy Raider at (150,0) is engaged then removed; within 10 ticks A is marching again. The
    lone-unit twin of the group-resume test."""
    (a,), (e,) = _fight_scene(lib, tw, [(0.0, 0.0)], [(150.0, 0.0)])
    lib.om_command_attack_move(tw, a, 3000.0, 0.0)
    assert _run_until(lib, tw, lambda: lib.om_unit_get_target(tw, a) != 0), "scene error: A did not engage"
    _kill(lib, tw, [e])
    lib.om_tactical_step(tw)
    lib.om_tactical_step(tw)
    x0 = lib.om_unit_get_pos(tw, a)[0]
    for _ in range(10):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, a)[0] > x0 + 10.0, "the lone unit did not resume its march"


# ---------------------------------------------------------------- OM_TP_PURSUE_BY_STEERING (P1, movement half)

def _pursuit_trace(lib, w, ticks=12):
    """P (id 1, Raider, sensor 800) attack-moves along +x; an idle friendly blocker stands 40 wu along the line to a
    visible enemy at (400,300) (bearing 36.87 deg). Returns [(angle, distance moved, distance to the blocker)]."""
    p = lib.om_unit_spawn(w, RAIDER, FRIEND, 0.0, 0.0, 0)
    blocker = lib.om_unit_spawn(w, RAIDER, FRIEND, 32.0, 24.0, 0)
    lib.om_unit_spawn(w, RAIDER, ENEMY, 400.0, 300.0, 0)
    lib.om_command_attack_move(w, p, 3000.0, 0.0)
    out = []
    x0, y0 = lib.om_unit_get_pos(w, p)
    for _ in range(ticks):
        lib.om_tactical_step(w)
        x1, y1 = lib.om_unit_get_pos(w, p)
        bx, by = lib.om_unit_get_pos(w, blocker)
        out.append((math.atan2(y1 - y0, x1 - x0), math.hypot(x1 - x0, y1 - y0), math.hypot(x1 - bx, y1 - by)))
        x0, y0 = x1, y1
    return out


BEARING_TO_ENEMY = math.atan2(300.0, 400.0)


def test_P1_pursue_by_steering_on_walks_the_goal_with_steering_and_collision(lib, tw):
    """P1 / R-087-04 (movement half), OM_TP_PURSUE_BY_STEERING = 1 (the default, the new behaviour): the pursuit goal
    is walked by the ordinary movement step. The blocker 40 wu along the line to the enemy therefore makes the
    pursuer deflect (some tick's displacement leaves the bearing to the enemy by at least 0.3 rad) and collision
    keeps the pair at least 30 wu apart on every tick."""
    assert _get_param(lib, tw, "OM_TP_PURSUE_BY_STEERING") == 1.0
    trace = _pursuit_trace(lib, tw)
    assert max(abs((a - BEARING_TO_ENEMY + math.pi) % (2 * math.pi) - math.pi) for a, d, _ in trace if d > 0.5) >= 0.3, \
        "the pursuer never steered around the blocker"
    assert min(c for _, _, c in trace) >= 30.0 - POS_TOL, "the pursuer walked through its ally"


def test_P1_pursue_by_steering_off_is_the_old_straight_line_control(lib, tw):
    """OM_TP_PURSUE_BY_STEERING = 0 gives the old behaviour (the hash baseline): the pursuit step is a straight-line
    position write toward the enemy that ignores the blocker, tick after tick along the 36.87 degree bearing,
    passing within 30 wu of the blocker. Positive control for the 'on' test: the same scene, the opposite verdict.
    Red today only because the setting does not exist; the scene itself is how the C behaves now (verified)."""
    assert _set_param(lib, tw, "OM_TP_PURSUE_BY_STEERING", 0) == 0
    trace = _pursuit_trace(lib, tw)
    for k, (a, d, _) in enumerate(trace):
        assert d == pytest.approx(7.5, abs=0.01), f"tick {k + 1}: old straight-line pursuit moves its full step"
        assert abs((a - BEARING_TO_ENEMY + math.pi) % (2 * math.pi) - math.pi) < 0.01, f"tick {k + 1}: not along the bearing"
    assert min(c for _, _, c in trace) < 30.0 - 1.0, "the old pursuit was expected to pass through the blocker"
