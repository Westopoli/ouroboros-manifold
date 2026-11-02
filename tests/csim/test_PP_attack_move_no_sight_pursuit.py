"""PP-move (the A199 "no pursuit on sight" tests that pinned the old rule are retired: H-057 replaced it with R-087-04 rev
2026-11-01, engage on sight; the replacing tests are tests/csim/test_E11_S087_engage_on_sight.py. See also there.): an attack-moving unit holds its slot and route until it can SHOOT, not until it sees (E-11 R-087-04,
R-087-05; E-13 R-096-02, R-096-03; ruling A199, docs/northstar/plans/2026-10-01-architect-rulings-2.md Addendum).
Rule marked for playtest review, A199 (Westley: "something we might change when it comes to play testing").

Old rule (P1, csrc/unit.c om_tac_pursue_goal, called from om_tac_unit_ai when OM_TP_PURSUE_BY_STEERING != 0, the
default): an attack-mover with no enemy in attack range, on its cohort turn, makes the nearest enemy it SEES in
sensor range its move goal and drops its slot and route. New rule: it keeps slot and route, halts and fires when an
enemy is in attack range, and pursues an ACQUIRED target under the leash (R-087-05, unchanged).
Gate: OM_TP_PURSUE_BY_STEERING (om_tac_pursue). At 0 the PP baseline branch (the `else if (u->order ==
OM_ORDER_ATTACK_MOVE)` arm of om_tac_unit_ai: hold on the seen unit and om_tac_step_toward it) keeps the old
walk; the baseline tests below must not move.

Scenes (Vanguard: range 300, sensor 700, speed 80, collision radius 15; Raider: range 200, sensor 800, hp 250,
idle faction 1). Slot arrival radius is OM_ARRIVAL_TOLERANCE_MULT x OM_UNIT_COLLISION_RADIUS = 1.5 x 15, read
from csrc/om_constants.h, not a free tolerance.
"""
import re

import pytest

from conftest import CSRC_DIR
from test_PP_unit_support import (RAIDER, VANGUARD, attack_move, dest, hp, pos, set_param, spawn, step, target)

PURSUE = "OM_TP_PURSUE_BY_STEERING"
_H = (CSRC_DIR / "om_constants.h").read_text()
ARRIVAL = (float(re.search(r"#define\s+OM_ARRIVAL_TOLERANCE_MULT\s+([\d.]+)", _H).group(1))
           * float(re.search(r"#define\s+OM_UNIT_COLLISION_RADIUS\s+([\d.]+)", _H).group(1)))
CENTROID_ARRIVAL = 2.0 * 15.0   # 2 x collision radius, the looser of the engines' centroid radii (open flag, R-095-05)
VAN_RANGE = 300.0   # Vanguard attack range (config.py / unit table)
LINE_N, SPACING = 32, 40.0   # 40 wu = collision diameter 30 + a gap, so the line spawns un-overlapped
LINE_X0, LINE_Y = 1000.0, 1000.0
CLICK = (1620.0, 3000.0)     # the line's centroid (x0 + 31*20) goes here: its slots keep the line's shape
TICKS = 700                  # 2000 wu at 80 wu/s is 500 ticks; the rest is slack, not a rule number


def _d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _centroid(ps):
    return (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))


def _shape_error(at, slots, clicks):
    """TD-PP-A199-shape-measure: the largest gap between a unit's offset from its chunk's centroid and its assigned
    slot's offset from the chunk's click (zero when the chunk's shape is intact)."""
    err = 0.0
    for chunk, click in clicks:
        c = _centroid([at(u) for u in chunk])
        for u in chunk:
            p = at(u)
            err = max(err, _d((p[0] - c[0], p[1] - c[1]), (slots[u][0] - click[0], slots[u][1] - click[1])))
    return err


def _line(lib, w, enemy_xy):
    ids = [spawn(lib, w, VANGUARD, 0, LINE_X0 + i * SPACING, LINE_Y) for i in range(LINE_N)]
    enemy = spawn(lib, w, RAIDER, 1, *enemy_xy)
    # TD-PP-A199-line-fixture: 32 units 40 wu apart sit 620 wu from their centroid, past R-095-03's 450 wu, so one
    # group order drops every slot to the raw click. Issue it as two chunks of 16 (300 wu from their own centroid), each
    # to the click plus its chunk's offset from the line's centroid, as scripts/skilllab/fight.py _chunks does.
    half = LINE_N // 2
    clicks = []
    for chunk in (ids[:half], ids[half:]):
        cx = LINE_X0 + (LINE_X0 + (LINE_N - 1) * SPACING - LINE_X0) / 2.0
        cc = sum(pos(lib, w, u)[0] for u in chunk) / len(chunk)
        attack_move(lib, w, chunk, CLICK[0] + cc - cx, CLICK[1])
        clicks.append((chunk, (CLICK[0] + cc - cx, CLICK[1])))
    slots = {}
    for u in ids:
        has, x, y = dest(lib, w, u)
        assert has == 1, "fixture: a line unit has no slot after the group attack-move"
        slots[u] = (x, y)
    assert len({(round(x), round(y)) for x, y in slots.values()}) == LINE_N, "fixture: slots collapsed to the click (R-095-03)"
    return ids, enemy, slots, clicks


def _run_line(lib, w, enemy_xy):
    """Returns (max slot miss at the end, closest approach of any unit to the enemy, enemy hp, max slot miss on the
    tick the enemy first lost hp or None)."""
    ids, enemy, slots, clicks = _line(lib, w, enemy_xy)
    closest, at_hit, held = 1e9, None, 0.0
    for _ in range(TICKS):
        step(lib, w)
        closest = min(closest, min(_d(pos(lib, w, u), pos(lib, w, enemy)) for u in ids))
        held = max(held, _shape_error(lambda u: pos(lib, w, u), slots, clicks))   # the shape, every tick of the run
        if at_hit is None and hp(lib, w, enemy) < 250.0:
            at_hit = max(_d(pos(lib, w, u), slots[u]) for u in ids)
    miss = held
    arrive = max(_d(_centroid([pos(lib, w, u) for u in ch]), ck) for ch, ck in clicks)
    return (miss, arrive), closest, hp(lib, w, enemy), at_hit




def test_control_R_087_04_A199_the_slot_miss_detector_trips_when_the_route_leads_to_the_enemy(lib, world_factory):
    """Positive control (green now and after): the enemy stands ON the route, between the line and its slots,
    in attack range of the units passing it. The units halt and fire short of their slots, so the same slot-miss
    measurement, taken on the tick the enemy first loses hp (it dies before the end and the line resumes, so the end
    reading is not the control's), is over the arrival radius: the detector above can trip."""
    w = world_factory(n_regions=1)
    _, closest, ehp, at_hit = _run_line(lib, w, (LINE_X0 + 15.5 * SPACING, 2000.0))
    assert closest <= VAN_RANGE and ehp < 250.0, "fixture: the line never engaged the enemy on its route"
    assert at_hit is not None and at_hit > ARRIVAL, "control: units were firing but still read as at their slots (miss %s)" % at_hit

def test_control_R_087_04_A199_the_shape_measure_trips_when_one_unit_leaves_its_slot_offset():
    """Positive control (TD-PP-A199-shape-measure): the shape reading is zero when every unit sits on its slot and over the
    slot radius when one unit is 40 wu off its slot offset, so assertion (1) above can trip."""
    ids = list(range(4))
    slots = {0: (0.0, 0.0), 1: (40.0, 0.0), 2: (80.0, 0.0), 3: (120.0, 0.0)}
    clicks = [(ids, (60.0, 0.0))]
    assert _shape_error(lambda u: slots[u], slots, clicks) < 1e-9
    assert _shape_error(lambda u: (slots[u][0], slots[u][1] + (40.0 if u == 3 else 0.0)), slots, clicks) > ARRIVAL



def _lone(lib, w, enemy_xy, switch=None):
    if switch is not None:
        assert set_param(lib, w, PURSUE, switch) == 0
    u = spawn(lib, w, VANGUARD, 0, 2000.0, 500.0)
    enemy = spawn(lib, w, RAIDER, 1, *enemy_xy)
    attack_move(lib, w, [u], 2000.0, 3000.0)
    return u, enemy






def test_R_087_04_A199_halt_and_fire_when_an_enemy_is_in_attack_range(lib, world_factory):
    """R-087-04 / A199 guard (green now and after): an idle Raider 250 wu ahead is inside attack range 300. The
    unit halts (same place at tick 40 and 60) and the enemy loses hp."""
    w = world_factory(n_regions=1)
    u, enemy = _lone(lib, w, (2000.0, 750.0))
    step(lib, w, 40)
    p40 = pos(lib, w, u)
    step(lib, w, 20)
    assert _d(p40, pos(lib, w, u)) <= 0.5, "the unit kept walking with an enemy in attack range"
    assert hp(lib, w, enemy) < 250.0, "it halted but never fired"
    assert target(lib, w, u) == enemy


def test_R_087_05_A199_an_acquired_target_that_walks_out_of_range_stays_held_under_the_leash(lib, world_factory):
    """R-087-05 / A199 guard (green now and after): the Vanguard acquires a Raider 250 ahead, the Raider is moved to
    350 ahead (out of range 300, inside sensor). While the unit is inside 200 wu of its anchor it keeps that
    target on every tick of the next 10 and the anchor stays where it was taken."""
    import ctypes
    from conftest import OMWorldP
    w = world_factory(n_regions=1)
    u, enemy = _lone(lib, w, (2000.0, 750.0))
    for _ in range(40):
        step(lib, w)
        if target(lib, w, u) == enemy:
            break
    assert target(lib, w, u) == enemy, "fixture: no acquisition"
    ax, ay = pos(lib, w, u)
    lib.om_unit_teleport(w, enemy, ax, ay + 350.0, 0)
    for _ in range(10):
        step(lib, w)
        assert _d(pos(lib, w, u), (ax, ay)) < 200.0
        assert target(lib, w, u) == enemy, "the acquired target was dropped while the unit was inside its leash"
    # R-087-04: "pursues an acquired target that leaves that range under the leash": it walks back into range.
    for _ in range(40):
        step(lib, w)
    assert _d(pos(lib, w, u), pos(lib, w, enemy)) <= VAN_RANGE, "it held its place and never pursued the target that left its range"
    assert _d(pos(lib, w, u), (ax, ay)) < 200.0 and target(lib, w, u) == enemy


def test_R_087_04_A199_a_lone_attack_mover_resumes_its_route_after_the_fight(lib, world_factory):
    """R-087-04 / A199: a Vanguard kills a weak Raider (hp 20) in range on its way, then continues and ends
    within the arrival radius of its destination (the target is dead: the attack-move goes on)."""
    w = world_factory(n_regions=1)
    u, enemy = _lone(lib, w, (2000.0, 750.0))
    lib.om_unit_set_hp(w, enemy, 20.0)
    for _ in range(TICKS + 200):
        step(lib, w)
    assert hp(lib, w, enemy) <= 0.0, "fixture: the enemy never died"
    assert _d(pos(lib, w, u), (2000.0, 3000.0)) <= ARRIVAL, "it did not resume its route: ended %s" % (pos(lib, w, u),)


def test_PP_baseline_switch_0_keeps_the_old_walk_toward_a_seen_enemy(lib, world_factory):
    """A140 baseline (green now and after A199): with OM_TP_PURSUE_BY_STEERING 0 the old behaviour is kept: the
    Vanguard steps sideways toward the Raider it sees (om_tac_step_toward; no target is exposed)."""
    w = world_factory(n_regions=1)
    u, enemy = _lone(lib, w, (2450.0, 800.0), switch=0)
    step(lib, w, 40)
    assert pos(lib, w, u)[0] > 2000.0 + ARRIVAL, "baseline no longer steps toward the seen enemy"




def test_R_087_04_A199_a_blocked_cell_between_it_and_an_enemy_in_range_does_not_stop_the_march(lib, world_factory):
    """R-087-04: "a target behind cover, a wall or a blocked cell does not stop the march: it keeps walking its route
    and fires when the line clears". A Vanguard marches north along x=1950; a Raider at (2200, 1500) is in attack range
    from y=1334 to y=1666, and a one-cell wall (cell column 20, row 14) hides it while the Vanguard is at y 1334 to
    1500 (the line crosses the wall at x=2050; hand-placed terrain as in test_PP_move_route.py). The unit keeps
    walking through that stretch with the enemy untouched, then fires once the line clears."""
    from conftest import OMFeature
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 4000.0, 4000.0) == 0
    assert lib.om_map_block_rect(w, 2010.0, 1410.0, 2090.0, 1490.0, 0, 4) == 0
    u = spawn(lib, w, VANGUARD, 0, 1950.0, 500.0)
    enemy = spawn(lib, w, RAIDER, 1, 2200.0, 1500.0)
    attack_move(lib, w, [u], 1950.0, 3000.0)
    walked, last_y = 0, pos(lib, w, u)[1]
    for _ in range(400):
        step(lib, w)
        y = pos(lib, w, u)[1]
        if 1340.0 <= y <= 1490.0:
            assert hp(lib, w, enemy) == 250.0, "it fired through the blocked cell"
            assert y > last_y, "it stopped in the blocked stretch (y %.1f)" % y
            walked += 1
        last_y = y
    assert walked >= 20, "fixture: the unit was not in the blocked stretch long enough (%d ticks)" % walked
    assert hp(lib, w, enemy) < 250.0, "it never fired once the line cleared"
