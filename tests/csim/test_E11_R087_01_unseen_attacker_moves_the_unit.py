# Rule pins: R-087-01, R-087-06, R-096-02, R-096-08, R-087-02, R-005-09, R-207-06, R-207-07
"""E-11 R-087-01 (engine rule fixes 2026-11-11, Round 2, F9; rewritten for Round 5, G4): a unit with no target that is hit by an attacker it cannot see or cannot reach leaves the line of fire and holds
where the move ends; an attack-mover still on its way to its point is neither moved nor stopped by such a hit.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01, as it reads on the Round 5 branch):
  "Given an idle unit, or an attack-moving unit that has arrived at its point, with no target, that takes damage from an attacker it cannot see or cannot reach, When the loop runs, Then it leaves the line
  of fire instead of standing in it: it moves 200 wu directly away from the damage direction and stops, and it holds where the move away ends; it does not walk back into the fire (Westley, 2026-11-17,
  asked whether a unit that moved away walks back in, after one unit in a lab fight moved away 57 times: "All the rest go with recommended", the recommendation being that it holds where it stops). While
  it holds it acquires and returns fire as any idle unit does (R-087-04, R-087-06), and a repeat hit it still cannot answer moves it again. An attack-moving unit still on its way to its point is neither
  moved nor stopped by such a hit: it keeps walking its attack-move (Westley, 2026-11-17: "them starting to be shot at does not stop their attack move"; StarCraft 2 does the same, an attack-moving unit
  ignores what it cannot attack; this replaces, for that unit, the move away he ruled on 2026-11-06). A plain-moving unit and a guard (R-096-08, never walks off) ignore the hit (Westley 2026-11-06, the SC2
  movement model). Hit from several sides it moves away from the latest hit; a unit that holds a target is not moved (DEC-engine-rules-round2-2026-11-11)."
This file proves the first half (the idle unit and the arrived attack-mover move away, a repeat hit moves them again, the move stays inside the map R-207-06, R-207-07) and the on-its-way clause; the hold
after the move, the acquire while holding and the unchanged units are tests/csim/test_E11_R087_01_attack_mover_not_stopped_by_unseen_fire.py. Rewritten from the Round 2 file (the Test-defect commit that
carries this text names the ruling): its attack-mover tests asserted the move away of an attack-mover that has not arrived, which Westley's ruling of 2026-11-17 replaced.
Evidence: the L-0080 trap fight (12,000-tick cap, red attack-movers stand on the low ground shot from the hill by blue units they cannot see; trace in
engine-rules-baseline/r2d). The whole-fight twins are tests/skilllab/arena/test_engine_rules_f9_unseen_fire.py and test_engine_rules_r5_unseen_fire.py.

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
    victim with an attack-move 900 wu on (to (1850, 1150), a cell centre: from (1800, 2000), a cell edge, the first steps of any walk lean 45 degrees off the line): tgt -1 for ever
Each test asserts the premise it needs from the live world before it measures.

Measuring: the first tick on which the victim's hp falls is the hit; `away` is the unit vector from the attacker to the victim at that tick (the damage
direction); `along` is the displacement from the victim's position at the hit projected on `away`. The move is read as the PEAK of `along` over the window
(the unit moves and stops, so its last position is the stop and the peak is the evidence of how far it went).

Detector bounds (not rules; Westley's to change): FLEE_MIN 150 and FLEE_MAX 250 wu (the brief: 200 wu, at least 150 and at most 250), DRAFT-t5-slack-ticks 30
(the window is the walk of 200 wu at the unit's own speed plus this: the hit is found one tick after the shot, the cohort turn is up to 4 ticks, the stop and
the order's re-issue take a few), DRAFT-t5-lateral 75 wu (the move is "directly away": at its peak the unit is within this of the line, the walk snaps to the 100 wu
grid), DRAFT-t5-ignore 60 wu (a unit that ignores a hit moves less than this along the damage direction), DRAFT-t5-min-flee 50 wu (with a wall or the canvas edge 100 wu behind, the unit moves at least half of that room).
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
MIN_FLEE = 50.0                     # DRAFT-t5-min-flee
HILL = (2400.0, 2000.0)
V0 = (1800.0, 2000.0)               # victim on the flat
G0 = (2000.0, 2000.0)               # attacker on the hill
POINT = (1850.0, 1150.0)            # the original ordered point: 900 wu from the victim, at right angles to the line of fire


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
        self.flinch = []        # per tick: the engine's own flag for "in a move away" (om_unit_in_flinch), read at the end of the tick
        for k in range(1, self.ticks + 1):
            step(lib, w)
            p = pos(lib, w, v)
            self.rows.append((k, p, dest(lib, w, v), target(lib, w, v), self.along(p), self.lateral(p)))
            self.flinch.append(lib.om_unit_in_flinch(w, v))

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
    """R-087-01 'A plain-moving unit ... ignore[s] the hit' (green today, must stay): a move order to (1850, 1150), hit from the hill by the attacker it cannot
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


def _arrived_scene(lib, wf, v_xy=V0, g_xy=(3000.0, 2000.0), **world):
    """The scene H victim as an attack-mover that has ARRIVED: attack-moved to a point 40 wu away, 40 ticks later it stands there (destination cleared, the order still an attack-move), unhit; the attacker
    (which starts 1200 wu away on the flat, out of sensor and gun range) is then teleported onto the hill and fires at once: the world is returned on the tick of that FIRST hit (hp below 500), so a
    caller measures the move away from it with `Hit`, without waiting for a second shot. Returns (world, victim, attacker)."""
    w, v, g = _scene(lib, wf, order=None, v_xy=v_xy, g_xy=g_xy, g_layer=0, **world)
    attack_move(lib, w, [v], v_xy[0], v_xy[1] - 40.0)
    for _ in range(40):
        step(lib, w)
    assert dest(lib, w, v)[0] == 0 and math.hypot(pos(lib, w, v)[0] - v_xy[0], pos(lib, w, v)[1] - (v_xy[1] - 40.0)) <= 5.0, \
        "premise: the victim has arrived and stands (destination %s, at %s)" % (dest(lib, w, v), pos(lib, w, v))
    assert hp(lib, w, v) == 500.0, "premise: the victim was hit before it arrived"
    lib.om_unit_teleport(w, g, G0[0] + (v_xy[0] - V0[0]), G0[1], 1)
    step(lib, w)    # the layer of a teleported unit is set by the next tick; its gun is ready, so this tick is the first hit
    assert hp(lib, w, v) < 500.0, "premise: the first shot did not land on the tick after the teleport (hp %.1f)" % hp(lib, w, v)
    return w, v, g


def _closing_every_tick(lib, w, v, h, point, floor_fraction=0.25):
    """The per-tick facts of an attack-mover that keeps walking its order through a hit: [(tick, what was wrong)] over the window `h` (a Hit): the unit is in a move away (engine flag), holds a target, has no
    destination or one other than `point`, or ends the tick no nearer `point` than it began by `floor_fraction` of its pace (a quarter: the first ticks of a walk from a cell edge lean 45 degrees off the line, a halt or a step back gains nothing)."""
    bad, prev = [], h.start
    pace = lib.om_unit_effective_speed(w, v) / 20.0
    for (k, p, d, t, a, lat), fl in zip(h.rows, h.flinch):
        if fl:
            bad.append((k, "in a move away"))
        if t > 0:
            bad.append((k, "holds target %d" % t))
        if not (d[0] == 1 and (d[1], d[2]) == pytest.approx(point, abs=1.0)):
            bad.append((k, "destination %s, wanted %s" % (d, point)))
        gained = math.hypot(prev[0] - point[0], prev[1] - point[1]) - math.hypot(p[0] - point[0], p[1] - point[1])
        if gained < floor_fraction * pace:
            bad.append((k, "gained %.2f wu toward the point, pace %.2f" % (gained, pace)))
        prev = p
    return bad


# ------------------------------------------------------------------ the attack-mover still on its way (the Round 5 half)

def test_R_087_01_an_attack_mover_on_its_way_hit_from_the_hill_is_not_moved_away(lib, world_factory):
    """R-087-01: "An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit: it keeps walking its attack-move": the victim attack-moving to (1850,1150), 900 wu to go,
    hit from the hill by the attacker it cannot see. On every tick of the window it is not in a move away (the engine's flag), holds no target, and its peak along the damage direction stays under
    DRAFT-t5-ignore 60 wu (the point is at right angles to the line of fire, so its own walk does not carry it along it). Red until Round 5: the engine moves it 200 wu away first."""
    w, v, g = _scene(lib, world_factory)
    d = _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    assert target(lib, w, v) <= 0, "premise: the victim holds a target"
    h = Hit(lib, w, v, g)
    moved = [(r[0], round(r[4], 1)) for r, fl in zip(h.rows, h.flinch) if fl]
    assert not moved, "the attack-mover was in a move away on %d ticks (tick, along), first %s; %s (premise %s)" % (len(moved), moved[:3], h.text(), d)
    assert h.peak()[4] < IGNORE, "the attack-mover moved %.1f wu along the damage direction: %s" % (h.peak()[4], h.text())


def test_R_087_01_an_attack_mover_on_its_way_hit_from_the_hill_is_not_stopped_and_keeps_its_destination(lib, world_factory):
    """R-087-01: "neither moved nor stopped by such a hit: it keeps walking its attack-move": the same victim and hit; on every tick of the window its destination is still the ordered point (1850,1150),
    it has no target, and it ends the tick nearer that point by at least a quarter of its pace (4 wu a tick; the first steps from a cell edge lean off the line): it neither halts nor loses the order. Red until Round 5: the move away clears the destination and
    the unit walks the other way for 200 wu."""
    w, v, g = _scene(lib, world_factory)
    _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    h = Hit(lib, w, v, g)
    bad = _closing_every_tick(lib, w, v, h, POINT)
    assert not bad, "%d ticks on which the attack-mover was stopped, moved or lost its point (tick, what), first %s; %s" % (len(bad), bad[:4], h.text())


def test_R_087_01_control_the_same_attack_mover_not_hit_passes_the_per_tick_measure(lib, world_factory):
    """R-087-01 control (green today and after): the scene above with the attacker out of range (teleported to the far corner before the first shot): the per-tick measure of the two tests above reads no
    stop, no move away and no change of destination on 80 ticks of an unhit attack-move, so the measure can be passed and its failure above is the hit's doing."""
    w, v, g = _scene(lib, world_factory)
    lib.om_unit_teleport(w, g, 3900.0, 3900.0, 0)
    step(lib, w)
    h = Hit(lib, w, v, g, ticks=80, away=(-1.0, 0.0))
    assert hp(lib, w, v) == 500.0, "premise: the victim was hit"
    assert not _closing_every_tick(lib, w, v, h, POINT), _closing_every_tick(lib, w, v, h, POINT)[:4]
    assert not any(h.flinch), "premise: an unhit unit is in a move away"


def test_R_087_01_control_the_same_attack_mover_that_has_arrived_is_moved_away_and_the_measure_sees_it(lib, world_factory):
    """R-087-01 control (green today and after): the arrived attack-mover (the setup one step outside the on-its-way clause) hit from the hill: the engine's move-away flag is up on some tick of the window and
    the per-tick measure of the tests above reports it (a destination that is not the point, no gain toward it). Proves those tests can fail."""
    w, v, g = _arrived_scene(lib, world_factory)
    _unseen_premise(lib, w, v, g)
    h = Hit(lib, w, v, g)
    assert any(h.flinch), "the arrived attack-mover never entered a move away: %s" % h.text()
    assert _closing_every_tick(lib, w, v, h, POINT), "the measure read nothing on a unit that moved away"


def test_R_087_01_an_attack_mover_hit_by_an_attacker_it_sees_but_cannot_reach_keeps_walking(lib, world_factory):
    """R-087-01 'an attacker it cannot see or cannot reach': the victim stands on the hill (layer 1, reach 0 up 0 down), the attacker on the flat below (layer 0, reach 1 up): the victim SEES it (high ground
    sees down) and cannot reach it by layer (om_combat_can_shoot is a line-of-sight test and says 1, so the evidence of 'cannot reach' is that the victim never takes it as a target, and the idle control
    below moves away). Attack-moving to (1500,3300), 900 wu on, and hit by it: on every tick of the window it is not in a move away, has no target, keeps that destination and gains on it. Red until Round 5."""
    w, v, g = _unreachable_scene(lib, world_factory, "attack_move")
    d = _dump(lib, w, v, g)
    assert d["layers"] == (1, 0), "premise: layers %s" % (d["layers"],)
    assert d["v_sees_g"] == 1 and d["side0_sees_g"] == 1, "premise: the victim and its side see the attacker: %s" % d
    assert d["side1_sees_v"] == 1 and d["g_can_shoot_v"] == 1, "premise: the attacker's side sees the victim and the attacker can shoot it: %s" % d
    _wait_hit(lib, w, v)
    assert target(lib, w, v) <= 0, "premise: the victim holds a target"
    h = Hit(lib, w, v, g)
    bad = _closing_every_tick(lib, w, v, h, UPOINT)
    assert not bad, "attack-mover, visible but out of reach: %d ticks stopped, moved or off its point (tick, what), first %s; %s (%s)" % (len(bad), bad[:4], h.text(), d)


def test_R_087_01_control_an_idle_unit_hit_by_an_attacker_it_sees_but_cannot_reach_moves_away(lib, world_factory):
    """R-087-01 control (green today and after): the visible-but-out-of-reach scene above with no order: the code flinches (the `!om_tac_in_reach` branch), 150 to 250 wu along the damage direction. Proves
    the scene's out-of-reach hit starts the move away for a unit with no order, so the attack-moving twin above is red for the order."""
    w, v, g = _unreachable_scene(lib, world_factory, None)
    _wait_hit(lib, w, v)
    _assert_flees(Hit(lib, w, v, g), "idle unit, visible but out of reach")


# ------------------------------------------------------------------ the idle unit and the arrived attack-mover: the move away, again on a repeat hit

def test_R_087_01_an_attack_mover_that_has_arrived_and_stands_moves_200_wu_away(lib, world_factory):
    """R-087-01: "an attack-moving unit that has arrived at its point, with no target, that takes damage from an attacker it cannot see ... moves 200 wu directly away from the damage direction and stops": the
    arrived attack-mover (destination cleared, the order still an attack-move) hit by the attacker it cannot see (teleported onto the hill once the victim has arrived): 150 to 250 wu along the damage
    direction, directly away. Green today (built in Round 2) and after."""
    w, v, g = _arrived_scene(lib, world_factory)
    d = _unseen_premise(lib, w, v, g)
    assert target(lib, w, v) <= 0, "premise: the victim holds a target"
    _assert_flees(Hit(lib, w, v, g), "arrived attack-mover, hit from the hill (%s)" % d)


def test_R_087_01_a_repeat_hit_moves_the_idle_unit_again(lib, world_factory):
    """R-087-01 'a repeat hit it still cannot answer moves it again': the idle victim (no order), hit from the hill, moves 150 to 250 wu away; 160 ticks after the first shot it is hit again (from where it
    stands then, which is not where it was first hit; the attacker's range is 800 wu) and again reaches 150 to 250 wu along the new damage direction."""
    w, v, g = _scene(lib, world_factory, order=None)
    _unseen_premise(lib, w, v, g)
    _wait_hit(lib, w, v)
    first = Hit(lib, w, v, g)
    _assert_flees(first, "first hit")
    _wait_hit(lib, w, v)
    assert not lib.om_unit_can_see(w, v, g) and target(lib, w, v) <= 0, "premise: the second hit finds the victim still blind and without a target"
    second = Hit(lib, w, v, g)
    assert second.start != first.start, "premise: the second hit is at the first hit's position"
    _assert_flees(second, "repeat hit")


# ------------------------------------------------------------------ the move stays inside the map (R-207-06, R-207-07)

def _blocked(lib, w, v):
    p = pos(lib, w, v)
    return bool(lib.om_navmesh_is_cell_blocked(w, int(p[0] // CELL), int(p[1] // CELL), lib.om_unit_get_layer(w, v)))


def _walled_scene(lib, wf, order):
    """Scene H with a wall 100 wu behind the victim (west of it): cells x 1600..1700, y 1800..2200, every layer. The damage direction is west. `order` is None (idle) or "arrived"."""
    if order == "arrived":
        w, v, g = _arrived_scene(lib, wf)
    else:
        w, v, g = _scene(lib, wf, order=order)
    assert lib.om_map_block_rect(w, 1600.0, 1800.0, 1700.0, 2200.0, 0, 4) == 0    # after om_terrain_set_heights, which rewrites the blocked bits
    return w, v, g


def test_R_207_06_the_move_away_never_ends_a_tick_in_a_blocked_cell(lib, world_factory):
    """R-207-06 / E-13 Invariants ('A unit never enters a blocked cell') with R-087-01: the arrived attack-mover is hit with a wall 100 wu behind it on the line away from the attacker. It still moves away
    (peak at least 50 wu: half the room it has) and ends no tick of 200 in a blocked cell. Green today and after (the unit that moves away is the arrived one)."""
    w, v, g = _walled_scene(lib, world_factory, "arrived")
    _unseen_premise(lib, w, v, g)
    assert not _blocked(lib, w, v)
    inside, best = [], 0.0
    start = pos(lib, w, v)
    for n in range(1, 201):
        step(lib, w)
        p = pos(lib, w, v)
        best = max(best, start[0] - p[0])
        if _blocked(lib, w, v):
            inside.append((n, tuple(round(c, 1) for c in p)))
    assert best >= MIN_FLEE, "the arrived attack-mover did not move away from the hit toward the wall: peak %.1f wu west (room: 100 wu)" % best
    assert not inside, "%d ticks inside a blocked cell, first %s" % (len(inside), inside[:3])


def test_R_207_06_control_a_unit_with_no_order_fleeing_toward_a_wall_does_not_enter_it(lib, world_factory):
    """R-207-06 control (green today and after): the same wall, the victim with no order: it flees west, ends no tick of 200 in a blocked cell. Proves the wall, the cell oracle and the unseen hit."""
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
    """Scene H moved to the west edge: hill centre (700, 2000), attacker (300, 2000) on it, victim (100, 2000) on the flat, the canvas edge 100 wu behind it. `order` is None (idle) or "arrived"."""
    if order == "arrived":
        return _arrived_scene(lib, wf, v_xy=(100.0, 2000.0), g_xy=(2000.0, 2000.0), hill=(700.0, 2000.0))
    return _scene(lib, wf, order=order, hill=(700.0, 2000.0), v_xy=(100.0, 2000.0), g_xy=(300.0, 2000.0))


def test_R_207_07_the_move_away_never_leaves_the_canvas(lib, world_factory):
    """R-207-07 ('a unit's position is always inside the canvas') with R-087-01: the arrived attack-mover is hit with the canvas edge 100 wu behind it. It still moves away (peak at least 50 wu) and every
    tick of 200 ends inside the canvas. Green today and after."""
    w, v, g = _edge_scene(lib, world_factory, "arrived")
    d = _unseen_premise(lib, w, v, g)
    start = pos(lib, w, v)
    best, outside = 0.0, []
    for n in range(1, 201):
        step(lib, w)
        p = pos(lib, w, v)
        best = max(best, start[0] - p[0])
        if not (0.0 <= p[0] <= CANVAS and 0.0 <= p[1] <= CANVAS):
            outside.append((n, tuple(round(c, 1) for c in p)))
    assert best >= MIN_FLEE, "the arrived attack-mover did not move away from the hit toward the edge: peak %.1f wu west (room: 100 wu), premise %s" % (best, d)
    assert not outside, "%d ticks outside the canvas, first %s" % (len(outside), outside[:3])


def test_R_207_07_control_a_unit_with_no_order_fleeing_toward_the_edge_stays_inside_the_canvas(lib, world_factory):
    """R-207-07 control (green today and after): the same edge scene, the victim with no order: it flees west and every tick of 200 ends inside the canvas."""
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
