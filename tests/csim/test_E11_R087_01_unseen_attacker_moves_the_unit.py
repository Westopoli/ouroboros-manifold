# Rule pins: R-087-01, R-087-06, R-096-02, R-096-08, R-087-02, R-005-09, R-207-06, R-207-07
"""E-11 R-087-01 (engine rule fixes 2026-11-11, Round 2, F9): a unit with no target that is hit by an attacker it cannot see or cannot reach
leaves the line of fire; the attack-mover half of the rule is not built.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01):
  "Given an idle or attack-moving unit with no target that takes damage from an attacker it cannot see or cannot reach, When the loop runs, Then it
  leaves the line of fire instead of standing or walking on blindly: it moves 200 wu directly away from the damage direction and stops, and an
  attack-mover then resumes its attack-move toward its original point (R-096-02); once the attacker is visible and in range it stands and fights. A
  plain-moving unit and a guard (R-096-08, never walks off) ignore the hit; a repeat hit moves it again (Westley 2026-11-06, the SC2 movement model)."
The note under S-087 names the unbuilt half: "The attack-mover relocation of R-087-01 is not built either (engine item, csrc/unit.c:2169 and the flinch cancel
at :2142)." The code starts the flinch only for a unit with `order == OM_ORDER_NONE`.
Evidence: the L-0080 trap fight (12,000-tick cap, red attack-movers stand on the low ground shot from the hill by blue units they cannot see; trace in
engine-rules-baseline/r2d). The whole-fight twin is tests/skilllab/arena/test_engine_rules_f9_unseen_fire.py.

Scene H (the shipped configuration, as scripts/skilllab/arena/run.py `fight(.., "on")` builds it): a 4000 x 4000 canvas, ground era (om_set_era_kind 1),
generated terrain whose heights are replaced by a `vantage` disc as scripts/skilllab/arena/hills.py builds it (LOW_CM 7000, STEP_CM 6000, a 200 wu ramp,
radius 400, the corner cell raises the band step), walking kinds, abilities off (om_tactical_disable_abilities, as the lab's `fight`), targeting by sight on
(the default), reach 0 up 1 down for every type. The victim is the built-in Vanguard (hp 500, speed 80 wu/s = 4 wu per tick), faction 0, on the flat
(layer 0). The attacker is a custom type GUN (speed 0 so that it never follows, range 800 so that it still reaches the victim after a 200 wu move, one
shot of 10 every DRAFT-t5-interval 8 s = 160 ticks so that one hit falls in each measuring window), faction 1, on the hill (layer 1). Premises dumped from the
built tree (2026-11-11, Round 2 tip 1feed3c5), hill centre (2400, 2000), victim (1800, 2000), attacker (2000, 2000):
    layers                     victim 0, attacker 1                     the victim sits 600 wu from the hill centre, the attacker 400
    om_unit_can_see(v, g)      0    (low ground never sees up, E-01 R-005-09)     om_player_can_see(side 0, g) = 0
    om_unit_can_see(g, v)      1    om_combat_can_shoot(g, v) = 1    the first shot lands on tick 4 (hp 500 -> 492.5), then every 160 ticks
    victim with an attack-move 800 wu on: tgt -1 for ever, walks on at 4 wu per tick, ignores every hit (red today)
Each test asserts the premise it needs from the live world before it measures.

Measuring: the first tick on which the victim's hp falls is the hit; `away` is the unit vector from the attacker to the victim at that tick (the damage
direction); `along` is the displacement from the victim's position at the hit projected on `away`. The move is read as the PEAK of `along` over the window
(the unit moves, stops, and an attack-mover then walks on toward its point, so its last position is not the evidence).

Detector bounds (not rules; Westley's to change): FLEE_MIN 150 and FLEE_MAX 250 wu (the brief: 200 wu, at least 150 and at most 250), DRAFT-t5-slack-ticks 30
(the window is the walk of 200 wu at the unit's own speed plus this: the hit is found one tick after the shot, the cohort turn is up to 4 ticks, the stop and
the order's re-issue take a few), DRAFT-t5-lateral 75 wu (the move is "directly away": at its peak the unit is within this of the line, the walk snaps to the 100 wu
grid), DRAFT-t5-ignore 60 wu (a unit that ignores a hit moves less than this along the damage direction), DRAFT-t5-resume 40 wu (an attack-mover that resumes is
this much nearer its point 20 ticks after it stopped), DRAFT-t5-min-flee 50 wu (with a wall or the canvas edge 100 wu behind, the unit moves at least half of that room).
"""
import ctypes
import math

import pytest

from conftest import OMFeature, OMWorldP
from test_PP_unit_support import VANGUARD, attack_move, dest, hp, pos, spawn, step, target

CANVAS = 4000.0
LOW_CM, STEP_CM, RAMP_WU, HILL_R = 7000, 6000, 200.0, 400.0     # scripts/skilllab/arena/hills.py
CELL = 100.0
GUN, SPOT = 40, 41                  # SPOT: sees 900 wu, shoots 1 wu, never moves: the side's eyes for the out-of-reach scene
GUN_HP, GUN_DMG, GUN_RANGE, GUN_SENSOR = 5000.0, 10.0, 800.0, 900.0   # DRAFT-t5-gun
INTERVAL_S = 8.0                    # DRAFT-t5-interval: 160 ticks between shots
WALKING = 1
FLEE = 200.0                        # R-087-01
FLEE_MIN, FLEE_MAX = 150.0, 250.0   # the brief
SLACK_TICKS = 30                    # DRAFT-t5-slack-ticks
LATERAL = 75.0                      # DRAFT-t5-lateral
IGNORE = 60.0                       # DRAFT-t5-ignore
RESUME = 40.0                       # DRAFT-t5-resume
MIN_FLEE = 50.0                     # DRAFT-t5-min-flee
HILL = (2400.0, 2000.0)
V0 = (1800.0, 2000.0)               # victim on the flat
G0 = (2000.0, 2000.0)               # attacker on the hill
POINT = (1800.0, 1100.0)            # the original ordered point: 900 wu from the victim, at right angles to the line of fire


def _world(lib, wf, hill=HILL, hill_r=HILL_R, gun_reach=(0, 1), victim_reach=(0, 1)):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, 7, CANVAS, CANVAS) == 0
    lib.om_set_era_kind(w, 1)
    n = int(CANVAS // CELL)
    cm = []
    for cy in range(n):
        for cx in range(n):
            d = math.hypot((cx + 0.5) * CELL - hill[0], (cy + 0.5) * CELL - hill[1])
            t = min(1.0, max(0.0, (hill_r + RAMP_WU - d) / RAMP_WU))
            cm.append(LOW_CM + int(t * (2 * STEP_CM - 1)))
    assert cm[0] == LOW_CM
    cm[0] = LOW_CM + 5 * STEP_CM
    assert lib.om_terrain_set_heights(w, (ctypes.c_int32 * len(cm))(*cm), n, n) == 1
    assert lib.om_roster_register_custom_unit(w, GUN, 0, b"t5_gun", GUN_HP, GUN_DMG, INTERVAL_S, GUN_RANGE, 0.0, GUN_SENSOR, 1.0, 0.0, 0) == 0
    assert lib.om_roster_register_custom_unit(w, SPOT, 0, b"t5_spot", GUN_HP, 0.0, INTERVAL_S, 1.0, 0.0, GUN_SENSOR, 1.0, 0.0, 0) == 0
    for t in (GUN, SPOT, VANGUARD):
        assert lib.om_roster_set_movement_kind(w, t, WALKING) == 0
    assert lib.om_roster_set_reach(w, GUN, *gun_reach) == 0
    assert lib.om_roster_set_reach(w, VANGUARD, *victim_reach) == 0
    lib.om_tactical_disable_abilities(w)
    return w


def _scene(lib, wf, order="attack_move", v_xy=V0, g_xy=G0, g_layer=1, v_layer=0, **world):
    """(world, victim, attacker). `order`: attack_move, move, guard or None, given at the victim's spawn."""
    w = _world(lib, wf, **world)
    v = spawn(lib, w, VANGUARD, 0, *v_xy, v_layer)
    g = spawn(lib, w, GUN, 1, *g_xy, g_layer)
    _order(lib, w, v, order)
    return w, v, g


def _order(lib, w, v, order, point=POINT):
    if order == "attack_move":
        attack_move(lib, w, [v], *point)
    elif order == "move":
        lib.om_command_move.raw(w, (ctypes.c_uint32 * 1)(v), 1, float(point[0]), float(point[1]))
    elif order == "guard":
        fn = getattr(lib.om_command_guard, "raw", lib.om_command_guard)
        fn.argtypes = [OMWorldP, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        fn.restype = ctypes.c_int
        assert fn(w, (ctypes.c_uint32 * 1)(v), 1) == 0
    else:
        assert order is None


def _window(lib, w, v):
    """Ticks to walk FLEE wu at the unit's own speed, plus DRAFT-t5-slack-ticks."""
    per_tick = lib.om_unit_effective_speed(w, v) / 20.0
    assert per_tick > 0.0, "scene broken: the victim cannot move"
    return int(math.ceil(FLEE / per_tick)) + SLACK_TICKS


def _unit(a, b):
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _wait_hit(lib, w, v, limit=400):
    """Step until the victim's hp falls; returns (ticks stepped, victim position at that tick)."""
    h0 = hp(lib, w, v)
    for n in range(1, limit + 1):
        step(lib, w)
        if hp(lib, w, v) < h0:
            return n, pos(lib, w, v)
    pytest.fail("scene broken: the victim was not hit in %d ticks (at %s, hp %.1f)" % (limit, pos(lib, w, v), hp(lib, w, v)))


class Hit:
    """One measured hit: the position at the hit, the damage direction, then `ticks` of the world with the victim's state per tick."""

    def __init__(self, lib, w, v, g, ticks=None, away=None):
        self.lib, self.w, self.v, self.g = lib, w, v, g
        self.start = pos(lib, w, v)
        self.away = away or _unit(pos(lib, w, g), self.start)
        self.ticks = ticks if ticks is not None else _window(lib, w, v)
        self.rows = []
        for k in range(1, self.ticks + 1):
            step(lib, w)
            p = pos(lib, w, v)
            self.rows.append((k, p, dest(lib, w, v), target(lib, w, v), self.along(p), self.lateral(p)))

    def along(self, p):
        return (p[0] - self.start[0]) * self.away[0] + (p[1] - self.start[1]) * self.away[1]

    def lateral(self, p):
        return (p[0] - self.start[0]) * -self.away[1] + (p[1] - self.start[1]) * self.away[0]

    def peak(self):
        return max(self.rows, key=lambda r: r[4])

    def text(self):
        k, p, d, t, a, lat = self.peak()
        return "peak %.1f wu along the damage direction %s (tick +%d at %s, lateral %.1f); last position %s, destination %s" % (
            a, tuple(round(c, 3) for c in self.away), k, tuple(round(c, 1) for c in p), lat, tuple(round(c, 1) for c in self.rows[-1][1]), self.rows[-1][2])


def _dump(lib, w, v, g):
    return {"layers": (lib.om_unit_get_layer(w, v), lib.om_unit_get_layer(w, g)), "v_sees_g": lib.om_unit_can_see(w, v, g), "side0_sees_g": lib.om_player_can_see(w, 0, g),
            "g_sees_v": lib.om_unit_can_see(w, g, v), "side1_sees_v": lib.om_player_can_see(w, 1, v), "g_can_shoot_v": lib.om_combat_can_shoot(w, g, v), "v_can_shoot_g": lib.om_combat_can_shoot(w, v, g)}


def _unseen_premise(lib, w, v, g):
    d = _dump(lib, w, v, g)
    assert d["layers"] == (0, 1), "premise: layers (victim, attacker) %s" % (d["layers"],)
    assert d["v_sees_g"] == 0 and d["side0_sees_g"] == 0, "premise: the victim's side must not see the hill attacker: %s" % d
    assert d["g_sees_v"] == 1 and d["g_can_shoot_v"] == 1, "premise: the attacker must see and shoot the victim: %s" % d
    return d


def _assert_flees(h, what):
    k, p, d, t, a, lat = h.peak()
    assert FLEE_MIN <= a <= FLEE_MAX, "%s: %s; wanted %.0f to %.0f wu" % (what, h.text(), FLEE_MIN, FLEE_MAX)
    assert abs(lat) <= LATERAL, "%s: not directly away, %s" % (what, h.text())


# ------------------------------------------------------------------ controls: green today and after

def test_R_087_01_control_a_unit_with_no_order_hit_from_the_hill_moves_200_wu_away_and_stops(lib, world_factory):
    """R-087-01 control (green today, must stay): 'an idle ... unit with no target that takes damage from an attacker it cannot see ... moves 200 wu directly
    away from the damage direction and stops'. The victim with no order, hit from the hill by the attacker it cannot see: its peak is 150 to 250 wu along
    the damage direction, and 40 ticks after the move it still stands where it stopped. Proves the scene (the hill, the unseen attacker, the hit, the
    measure), so the attack-moving tests below are red for the order's sake."""
    w, v, g = _scene(lib, world_factory, order=None)
    d = _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    h = Hit(lib, w, v, g)
    _assert_flees(h, "idle unit, hit from the hill (%s)" % d)
    k, p, _, _, a, _ = h.peak()
    last = h.rows[-1][1]
    assert math.hypot(last[0] - p[0], last[1] - p[1]) <= 5.0, "idle unit did not stop where the move ended: peak at %s, last %s" % (p, last)


def test_R_087_01_control_a_plain_moving_unit_ignores_the_hit(lib, world_factory):
    """R-087-01 'A plain-moving unit ... ignore[s] the hit' (green today, must stay): a move order to (1800, 1100), hit from the hill by the attacker it cannot
    see. It is hit, never moves 60 wu along the damage direction, keeps its destination, and is nearer its point by at least 0.75 of its pace over the window."""
    w, v, g = _scene(lib, world_factory, order="move")
    _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    before = math.hypot(pos(lib, w, v)[0] - POINT[0], pos(lib, w, v)[1] - POINT[1])
    h = Hit(lib, w, v, g)
    assert h.peak()[4] < IGNORE, "plain-moving unit moved away from the hit: %s" % h.text()
    has, dx, dy = dest(lib, w, v)
    assert has == 1 and (dx, dy) == pytest.approx(POINT, abs=1.0), "plain-moving unit lost its destination: %s" % ((has, dx, dy),)
    last = h.rows[-1][1]
    gained = before - math.hypot(last[0] - POINT[0], last[1] - POINT[1])
    pace = lib.om_unit_effective_speed(w, v) / 20.0 * h.ticks
    assert gained >= 0.75 * pace, "plain-moving unit is only %.1f wu nearer its point after %d ticks (pace %.1f)" % (gained, h.ticks, pace)


def test_R_087_01_control_a_guard_ignores_the_hit_and_never_walks_off(lib, world_factory):
    """R-087-01 'a guard (R-096-08, never walks off) ignore[s] the hit' (green today, must stay): a guard at its post is hit three times by the attacker on the
    hill it cannot see (every 160 ticks) and never ends a tick more than 5 wu from the post."""
    w, v, g = _scene(lib, world_factory, order="guard")
    _unseen_premise(lib, w, v, g)
    post = pos(lib, w, v)
    h0 = hp(lib, w, v)
    worst, hits = 0.0, 0
    prev = h0
    for _ in range(3 * 160 + 20):
        step(lib, w)
        p = pos(lib, w, v)
        worst = max(worst, math.hypot(p[0] - post[0], p[1] - post[1]))
        now = hp(lib, w, v)
        hits += now < prev
        prev = now
    assert hits >= 3, "scene broken: the guard was hit %d times" % hits
    assert worst <= 5.0, "the guard walked %.1f wu from its post" % worst


def test_R_087_01_control_a_visible_attacker_in_range_is_fought_not_fled(lib, world_factory):
    """R-087-01 'once the attacker is visible and in range it stands and fights' / R-087-06 return fire (green today, must stay): the attack-moving victim
    on the hill (layer 1, 200 wu from the attacker, also layer 1, which it sees and reaches, range 300) takes the target, fires back, and never moves 60 wu away
    along the damage direction in the window after the hit."""
    w, v, g = _scene(lib, world_factory, order="attack_move", v_xy=(2200.0, 2000.0), g_xy=G0, g_layer=1, v_layer=1)
    d = _dump(lib, w, v, g)
    assert d["layers"] == (1, 1) and d["v_sees_g"] == 1 and d["v_can_shoot_g"] == 1, "premise: a visible attacker in range on one layer: %s" % d
    _wait_hit(lib, w, v)
    gun_hp = hp(lib, w, g)
    h = Hit(lib, w, v, g)
    assert any(r[3] == g for r in h.rows), "the victim never took the visible attacker as its target"
    assert hp(lib, w, g) < gun_hp, "the victim never fired back"
    assert h.peak()[4] < IGNORE, "the unit fled an attacker it sees and reaches: %s" % h.text()


UC, UR = (2400.0, 2000.0), 1300.0       # the out-of-reach scene's hill: radius 1300, plateau out to 1400 wu from the centre
UV, UG, US = (2400.0, 3300.0), (2400.0, 3550.0), (3195.0, 3000.0)
UPOINT = (1500.0, 3300.0)


def _unreachable_scene(lib, wf, order):
    """The victim on the plateau's south rim (layer 1, reach 0 up 0 down), the attacker on the flat just below it (layer 0, 250 wu south, reach 1 up), and a
    SPOTTER of the attacker's side on the plateau 850 wu from the victim: beyond the victim's sensor (700), inside the spotter's (900), and farther than 700 from where
    the victim will stand after a 200 wu move north. A unit on the low ground never sees up (E-01 R-005-09), so the attacker can shoot the victim only because its SIDE
    sees it through the spotter; the victim sees down onto the attacker (inside half its sensor radius, 350 wu) and cannot reach it (layer 0 is one down, its reach
    down is 0). The damage direction is north. The order point is 900 wu west."""
    w = _world(lib, wf, hill=UC, hill_r=UR, gun_reach=(1, 0), victim_reach=(0, 0))
    v = spawn(lib, w, VANGUARD, 0, *UV, 1)
    g = spawn(lib, w, GUN, 1, *UG, 0)
    spawn(lib, w, SPOT, 1, *US, 1)
    _order(lib, w, v, order, UPOINT)
    return w, v, g


# ------------------------------------------------------------------ red today: the attack-mover

def test_R_087_01_an_attack_mover_hit_from_the_hill_by_an_attacker_it_cannot_see_moves_200_wu_away(lib, world_factory):
    """R-087-01: an attack-moving unit with no target (order (1800,1100), 900 wu to go), hit from the hill by the attacker it cannot see, within DRAFT-t5 window
    reaches 150 to 250 wu farther from the attacker along the damage direction, directly away. Red today: the code starts the flinch only for a unit with
    no order (unit.c, `order == OM_ORDER_NONE`); the attack-mover walks on at 4 wu per tick and never moves along the damage direction."""
    w, v, g = _scene(lib, world_factory)
    d = _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    assert target(lib, w, v) <= 0, "premise: the victim holds a target"
    _assert_flees(Hit(lib, w, v, g), "attack-mover, hit from the hill (%s)" % d)


def test_R_087_01_an_attack_mover_that_has_arrived_and_stands_moves_200_wu_away(lib, world_factory):
    """R-087-01: an attack-mover that has arrived at its point (destination cleared, the order still an attack-move, P1 chase) and stands is hit by the attacker
    it cannot see (teleported onto the hill once the victim has arrived: it starts 1200 wu away, out of sensor range): the same move, 150 to 250 wu along the damage
    direction. Red today."""
    w, v, g = _scene(lib, world_factory, g_xy=(3000.0, 2000.0), g_layer=0)
    attack_move(lib, w, [v], V0[0], V0[1] - 40.0)
    for _ in range(40):
        step(lib, w)
    assert dest(lib, w, v)[0] == 0 and math.hypot(pos(lib, w, v)[0] - V0[0], pos(lib, w, v)[1] - (V0[1] - 40.0)) <= 5.0, \
        "premise: the victim has arrived and stands (destination %s, at %s)" % (dest(lib, w, v), pos(lib, w, v))
    assert hp(lib, w, v) == 500.0, "premise: the victim was hit before it arrived"
    lib.om_unit_teleport(w, g, G0[0], G0[1], 1)
    step(lib, w)    # the layer of a teleported unit is set by the next tick
    d = _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    assert target(lib, w, v) <= 0, "premise: the victim holds a target"
    _assert_flees(Hit(lib, w, v, g), "arrived attack-mover, hit from the hill (%s)" % d)


def test_R_087_01_the_attack_mover_then_resumes_toward_its_original_point(lib, world_factory):
    """R-087-01 'an attack-mover then resumes its attack-move toward its original point (R-096-02)': after the move the unit that had not arrived has the
    original point (1800, 1100) as its destination again within the window plus 20 ticks, and 20 ticks later it is at least 40 wu nearer that point than where
    it stopped (it walks on, it does not stand). Red today: it never moved, so the first assertion (the move) fails; the destination is the point throughout."""
    w, v, g = _scene(lib, world_factory)
    _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    h = Hit(lib, w, v, g)
    _assert_flees(h, "attack-mover, hit from the hill")
    k, stop, _, _, _, _ = h.peak()
    after = [r for r in h.rows if r[0] > k]
    back = next((r for r in after if r[2][0] == 1 and (r[2][1], r[2][2]) == pytest.approx(POINT, abs=1.0)), None)
    assert back is not None, "after the move the destination was never the original point again: destinations %s" % sorted({(r[2][1], r[2][2]) for r in after})[:5]
    here = back[1]
    for _ in range(20):
        step(lib, w)
    now = pos(lib, w, v)
    d0, d1 = math.hypot(here[0] - POINT[0], here[1] - POINT[1]), math.hypot(now[0] - POINT[0], now[1] - POINT[1])
    assert d0 - d1 >= RESUME, "the attack-mover did not walk on toward its point: %.1f wu from it at the resume, %.1f wu 20 ticks later" % (d0, d1)


def test_R_087_01_a_repeat_hit_moves_the_attack_mover_again(lib, world_factory):
    """R-087-01 'a repeat hit moves it again': the same attack-mover is hit again 160 ticks after the first shot (from where it stands then, which is
    not where it was first hit) and again reaches 150 to 250 wu along the new damage direction. Red today at the first move."""
    w, v, g = _scene(lib, world_factory)
    _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    first = Hit(lib, w, v, g)
    _assert_flees(first, "first hit")
    _wait_hit(lib, w, v)
    assert not lib.om_unit_can_see(w, v, g) and target(lib, w, v) <= 0, "premise: the second hit finds the victim still blind and without a target"
    second = Hit(lib, w, v, g)
    assert second.start != first.start, "premise: the second hit is at the first hit's position"
    _assert_flees(second, "repeat hit")


def test_R_087_01_an_attack_mover_hit_by_an_attacker_it_sees_but_cannot_reach_moves_200_wu_away(lib, world_factory):
    """R-087-01 'an attacker it cannot see or cannot reach': the victim stands on the hill (layer 1, reach 0 up 0 down), the attacker on the flat below (layer 0,
    reach 1 up): the victim SEES it (high ground sees down) and cannot reach it by layer (reach down 0; om_combat_can_shoot is a line-of-sight test and says 1, so
    the evidence of 'cannot reach' is that the victim never takes it as a target, and the idle control below flinches). Attack-moving, hit by it: the same move,
    150 to 250 wu along the damage direction. Red today."""
    w, v, g = _unreachable_scene(lib, world_factory, "attack_move")
    d = _dump(lib, w, v, g)
    assert d["layers"] == (1, 0), "premise: layers %s" % (d["layers"],)
    assert d["v_sees_g"] == 1 and d["side0_sees_g"] == 1, "premise: the victim and its side see the attacker: %s" % d
    assert d["side1_sees_v"] == 1 and d["g_can_shoot_v"] == 1, "premise: the attacker's side sees the victim and the attacker can shoot it: %s" % d
    _wait_hit(lib, w, v)
    assert target(lib, w, v) <= 0, "premise: the victim holds a target"
    _assert_flees(Hit(lib, w, v, g), "attack-mover, visible but out of reach (%s)" % d)


def test_R_087_01_control_an_idle_unit_hit_by_an_attacker_it_sees_but_cannot_reach_moves_away(lib, world_factory):
    """R-087-01 control (green today, must stay): the visible-but-out-of-reach scene above with no order: the code flinches (the `!om_tac_in_reach` branch), 150 to
    250 wu along the damage direction. Proves the scene's out-of-reach hit starts the move for a unit with no order, so the attack-moving twin is red for the order."""
    w, v, g = _unreachable_scene(lib, world_factory, None)
    _wait_hit(lib, w, v)
    _assert_flees(Hit(lib, w, v, g), "idle unit, visible but out of reach")


# ------------------------------------------------------------------ the move stays inside the map (R-207-06, R-207-07)

def _blocked(lib, w, v):
    p = pos(lib, w, v)
    return bool(lib.om_navmesh_is_cell_blocked(w, int(p[0] // CELL), int(p[1] // CELL), lib.om_unit_get_layer(w, v)))


def _walled_scene(lib, wf, order):
    """Scene H with a wall 100 wu behind the victim (west of it): cells x 1600..1700, y 1800..2200, every layer. The damage direction is west."""
    w, v, g = _scene(lib, wf, order=order)
    assert lib.om_map_block_rect(w, 1600.0, 1800.0, 1700.0, 2200.0, 0, 4) == 0    # after om_terrain_set_heights, which rewrites the blocked bits
    return w, v, g


def test_R_207_06_the_move_away_never_ends_a_tick_in_a_blocked_cell(lib, world_factory):
    """R-207-06 / E-13 Invariants ('A unit never enters a blocked cell') with R-087-01: the attack-mover is hit with a wall 100 wu behind it on the line away
    from the attacker. It still moves away (peak at least 50 wu: half the room it has) and ends no tick of 200 in a blocked cell. Red today: the attack-mover
    does not move away at all (the first assertion)."""
    w, v, g = _walled_scene(lib, world_factory, "attack_move")
    _unseen_premise(lib, w, v, g)
    assert not _blocked(lib, w, v)
    _wait_hit(lib, w, v)
    inside, best = [], 0.0
    start = pos(lib, w, v)
    for n in range(1, 201):
        step(lib, w)
        p = pos(lib, w, v)
        best = max(best, start[0] - p[0])
        if _blocked(lib, w, v):
            inside.append((n, tuple(round(c, 1) for c in p)))
    assert best >= MIN_FLEE, "the attack-mover did not move away from the hit toward the wall: peak %.1f wu west (room: 100 wu)" % best
    assert not inside, "%d ticks inside a blocked cell, first %s" % (len(inside), inside[:3])


def test_R_207_06_control_a_unit_with_no_order_fleeing_toward_a_wall_does_not_enter_it(lib, world_factory):
    """R-207-06 control (green today, must stay): the same wall, the victim with no order: it flees west, ends no tick of 200 in a blocked cell. Proves the wall, the
    cell oracle and the unseen hit."""
    w, v, g = _walled_scene(lib, world_factory, None)
    _wait_hit(lib, w, v)
    start = pos(lib, w, v)
    best, inside = 0.0, 0
    for _ in range(200):
        step(lib, w)
        best = max(best, start[0] - pos(lib, w, v)[0])
        inside += _blocked(lib, w, v)
    assert best >= MIN_FLEE, "scene broken: the idle unit did not flee toward the wall (%.1f wu)" % best
    assert inside == 0, "%d ticks inside a blocked cell" % inside


def _edge_scene(lib, wf, order):
    """Scene H moved to the west edge: hill centre (700, 2000), attacker (300, 2000) on it, victim (100, 2000) on the flat, the canvas edge 100 wu behind it."""
    w, v, g = _scene(lib, wf, order=order, hill=(700.0, 2000.0), v_xy=(100.0, 2000.0), g_xy=(300.0, 2000.0))
    return w, v, g


def test_R_207_07_the_move_away_never_leaves_the_canvas(lib, world_factory):
    """R-207-07 ('a unit's position is always inside the canvas') with R-087-01: the attack-mover is hit with the canvas edge 100 wu behind it. It still moves
    away (peak at least 50 wu) and every tick of 200 ends inside the canvas. Red today: it does not move away."""
    w, v, g = _edge_scene(lib, world_factory, "attack_move")
    d = _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    start = pos(lib, w, v)
    best, outside = 0.0, []
    for n in range(1, 201):
        step(lib, w)
        p = pos(lib, w, v)
        best = max(best, start[0] - p[0])
        if not (0.0 <= p[0] <= CANVAS and 0.0 <= p[1] <= CANVAS):
            outside.append((n, tuple(round(c, 1) for c in p)))
    assert best >= MIN_FLEE, "the attack-mover did not move away from the hit toward the edge: peak %.1f wu west (room: 100 wu), premise %s" % (best, d)
    assert not outside, "%d ticks outside the canvas, first %s" % (len(outside), outside[:3])


def test_R_207_07_control_a_unit_with_no_order_fleeing_toward_the_edge_stays_inside_the_canvas(lib, world_factory):
    """R-207-07 control (green today, must stay): the same edge scene, the victim with no order: it flees west and every tick of 200 ends inside the canvas."""
    w, v, g = _edge_scene(lib, world_factory, None)
    _wait_hit(lib, w, v)
    start = pos(lib, w, v)
    best, outside = 0.0, 0
    for _ in range(200):
        step(lib, w)
        p = pos(lib, w, v)
        best = max(best, start[0] - p[0])
        outside += not (0.0 <= p[0] <= CANVAS and 0.0 <= p[1] <= CANVAS)
    assert best >= MIN_FLEE, "scene broken: the idle unit did not flee toward the edge (%.1f wu)" % best
    assert outside == 0, "%d ticks outside the canvas" % outside
