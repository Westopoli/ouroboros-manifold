# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, ruling 8, "Contract / Engine", Pieces row E2.
# piece LAB-REV2-E2 (firing arc); rule R-100-04 DRAFT (E-13 S-100), register Q-100-01.
"""S-100 firing arc (R-100-04, DRAFT, Westley 2026-10-13 "add a firing-arc rule to the game"; Q-100-01).

The rule: a unit with a target does not fire while the target lies outside the arc of OM_TP_FIRING_ARC_DEG about
its facing (360 is no arc, today's behaviour); it keeps the target, turns toward it at the R-100-02 rate, and
fires once the target is inside. Acquisition, the hold and return fire are untouched; a unit kiting under
attack-target faces its target directly.

What is pinned here, and where the number comes from (nothing below is a threshold of mine):
  * Turn rate: R-100-02 / csrc/om_constants.h: Strike 6.0, Line 4.0, Siege 2.5 rad/s, at OM_TACTICAL_TICK_RATE 20
    ticks/s, so a Line unit turns 0.2 rad per tick. The constants are read from the header text, not retyped.
  * Tick count: the face pass (om_move_face_pass) turns a unit on the very tick it acquires (measured on the E0
    tree: facing already 0.2 rad off its start at the end of the acquisition tick), and a shot is decided on the
    state after the tick's movement (unit.c P2: "a shot is decided on the positions after this tick's movement").
    So if A is the acquisition tick and a unit must turn N face-pass steps to bring its target inside the arc,
    the first shot is on tick A + N - 1 (N = 1 or less: the acquisition tick itself). turn_steps() below is that
    arithmetic; every gated test asserts the shot on exactly that tick, and also asserts the observed facing at the
    end of the tick before is outside the arc and at the end of the shot tick inside it.
  * The arc width is the setting's own value (90, 120, 180, 270 are fixture values; 120 is DRAFT-firing-arc-deg).

Every scene: one subject (Vanguard unless named, faction 0, origin, facing set away with om_unit_set_facing) and
one Supply unit of faction 1 (never fires, so nothing else moves hp or the subject's state) 200 wu out along +x,
inside every subject's attack range and sensor. The return-fire scene replaces the Supply with a Vanguard.

The arc gates the FIRE PASS only. The baseline path with OM_TP_PURSUE_BY_STEERING = 0 is not gated by the arc and is not
tested here (a note, not a claim: nothing below reads that path).

Red on the E0 tree (the setting exists and is stored but unread): every gated scene fires on the acquisition tick
at arc 90; the trace of the fixed fight at arc 90 equals the arc-360 trace. Green on the E0 tree: every arc-360
control (fires on the acquisition tick), the kiting scene (the snap), the in-arc scenes, the byte-identity of the
fixed fight at 360 (unset and set), and the detector checks.

Baseline of step 1 (the spec's "csim trace hash of the arc scene at 360, recorded on main"): TRACE_HASH_360 below was
recorded by running fixed_fight_hash() with the setting UNSET and with it set to 360 on the E0 tree (branch
push/labrev2-e0, sha 4decde94); both runs printed the same digest. fixed_fight_hash() orders units one by one
(the lone attack-move, which LAB-REV2-E1 does not change) and uses no guard, so the E1/E3/E4 landings leave it
alone. A later mismatch is a finding or a ledger-row re-record, never a patch to this file."""
import ctypes
import hashlib
import math
import re
import struct

import pytest

from conftest import CSRC_DIR, OMFeature
from test_PP_unit_support import set_param, spawn, step

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION, SUPPLY = 0, 1, 2, 3, 4, 5, 6
ARC = "OM_TP_FIRING_ARC_DEG"
FRIEND, ENEMY = 0, 1
DIST = 200.0          # fixture: subject to enemy, inside the attack range of Raider (200 is the edge), Vanguard 300, Bombard 1200
RAIDER_DIST = 150.0   # a Raider's range is 200, so its scene stands closer
WINDOW = 60           # ticks watched; the slowest turn here (Bombard, 19 steps) fits with room

TICK_RATE = int(re.search(r"#define\s+OM_TACTICAL_TICK_RATE\s+(\d+)", (CSRC_DIR / "om_constants.h").read_text()).group(1))


def _rate(name):
    return float(re.search(rf"#define\s+{name}\s+([0-9.]+)", (CSRC_DIR / "om_constants.h").read_text()).group(1))


RATE_STRIKE, RATE_LINE, RATE_SIEGE = _rate("OM_FACING_ROTATION_SPEED_STRIKE"), _rate("OM_LINE"), _rate("OM_SIEGE")
RATE_OF = {RAIDER: RATE_STRIKE, VANGUARD: RATE_LINE, BOMBARD: RATE_SIEGE}  # by category of the type (R-100-02)


def turn_steps(offset_rad, arc_deg, rate_rad_s):
    """Face-pass steps needed to bring a target `offset_rad` off the facing inside an arc of `arc_deg`
    (inside means within half the arc of the facing): 0 when already inside, else the whole steps of
    rate/TICK_RATE radians. The 1e-9 only keeps an exact multiple from rounding up."""
    need = abs(offset_rad) - math.radians(arc_deg) / 2.0
    if need <= 0.0:
        return 0
    return math.ceil(need / (rate_rad_s / TICK_RATE) - 1e-9)


def shot_tick(acquired_tick, steps):
    """First shot tick (see the module docstring): the acquisition tick already contains the first turn step."""
    return acquired_tick + max(steps, 1) - 1


def _events(lib, w):
    out = []
    for i in range(lib.om_tactical_event_count(w)):
        k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
        assert lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0
        out.append((k.value, a.value, b.value, t.value))
    return out


def _fires(lib, w):
    return [(a, b) for (k, a, b, _t) in _events(lib, w) if k == 0]


def _guard(lib, w, ids):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return getattr(lib.om_command_guard, "raw", lib.om_command_guard)(w, arr, len(ids))


def _attack_move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return getattr(lib.om_command_attack_move, "raw", lib.om_command_attack_move)(w, arr, len(ids), float(x), float(y))


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def scene(lib, w, *, arc, order="idle", subject=VANGUARD, facing=math.pi, dist=DIST, enemy_combat=False, query=False):
    """Build one subject-and-enemy scene and watch WINDOW ticks. Returns a dict:
    ids, per-tick log [(tick, subject_target, subject_facing, subject_fired, subject_pos)], acquired (first tick the
    subject holds the enemy), shot (first tick the subject fires), enemy_shot (first tick the enemy fires).
    With query=True each log row also carries om_combat_can_engage(subject, enemy) read after the tick (index 5); it is
    off by default so the other scenes run exactly as they did."""
    if arc is not None:
        assert set_param(lib, w, ARC, arc) == 0, f"setting {ARC} refused {arc}"
    s = spawn(lib, w, subject, FRIEND, 0.0, 0.0)
    e = spawn(lib, w, VANGUARD if enemy_combat else SUPPLY, ENEMY, dist, 0.0)
    lib.om_unit_set_facing(w, s, facing)
    if enemy_combat:
        lib.om_unit_set_facing(w, e, math.pi)  # looking at the subject, so it shoots at once at any arc
    if order == "attack_move":
        _attack_move(lib, w, [s], -3000.0, 0.0)  # walking away from the enemy, as the subject already faces
    elif order == "guard":
        assert _guard(lib, w, [s]) == 0
    elif order == "attack_target":
        lib.om_command_attack_target(w, s, e)
    log, acquired, shot, enemy_shot = [], None, None, None
    for k in range(1, WINDOW + 1):
        step(lib, w)
        fires = _fires(lib, w)
        fired = any(a == s for a, _b in fires)
        tgt = lib.om_unit_target(w, s)
        row = (k, tgt, lib.om_unit_get_facing(w, s), fired, (lib.om_unit_position_x(w, s), lib.om_unit_position_y(w, s)))
        log.append(row + (lib.om_combat_can_engage(w, s, e),) if query else row)
        if acquired is None and tgt == e:
            acquired = k
        if shot is None and fired:
            shot = k
        if enemy_shot is None and any(a == e for a, _b in fires):
            enemy_shot = k
        if shot is not None and k >= shot + 2:
            break
    return {"s": s, "e": e, "log": log, "acquired": acquired, "shot": shot, "enemy_shot": enemy_shot}


def _row(r, tick):
    return r["log"][tick - 1]


# ---------------------------------------------------------------- arithmetic and detector controls (green today)

def test_control_turn_arithmetic_matches_the_constants():
    """The constants read from csrc/om_constants.h are the R-100-02 numbers (6.0, 4.0, 2.5) and the tick rate is 20,
    so a Line unit turns 0.2 rad a tick. Positive control of turn_steps: a half turn at arc 90 is 12 steps
    (2.356 rad / 0.2), already-inside is 0, and one more arc degree range moves nothing across an exact multiple."""
    assert (RATE_STRIKE, RATE_LINE, RATE_SIEGE, TICK_RATE) == (6.0, 4.0, 2.5, 20)
    assert turn_steps(math.pi, 90, RATE_LINE) == 12
    assert turn_steps(math.pi, 360, RATE_LINE) == 0
    assert turn_steps(math.radians(40), 90, RATE_LINE) == 0
    assert turn_steps(math.radians(45) + 0.2, 90, RATE_LINE) == 1
    assert shot_tick(4, 0) == 4 and shot_tick(4, 1) == 4 and shot_tick(4, 12) == 15


def test_control_scene_reader_sees_a_shot_and_the_acquisition_tick(lib, tw):
    """Detector control: at arc 360 with the enemy 200 wu out the scene reader reports an acquisition tick and a
    shot (a reader that never saw a shot would make every 'later' assertion below meaningless)."""
    r = scene(lib, tw, arc=360)
    assert r["acquired"] is not None and r["shot"] is not None


# ---------------------------------------------------------------- the arc delays the shot, nothing else

ORDERS = ["idle", "attack_move", "guard", "return_fire"]


def _make(lib, world_factory, arc, order, **kw):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return scene(lib, w, arc=arc, order="idle" if order == "return_fire" else order,
                 enemy_combat=order == "return_fire", **kw)


@pytest.mark.parametrize("order", ORDERS)
def test_control_arc_360_fires_on_the_acquisition_tick(lib, world_factory, order):
    """R-100-04 control (green on the E0 tree): at 360 a unit facing away from its target still fires on the tick it
    acquires it (idle, attack-move, guard; and by return fire, the tick after the enemy's first shot). Without this
    the delay measured below could be something else."""
    r = _make(lib, world_factory, 360, order)
    assert r["acquired"] is not None, "the subject never took the enemy as its target"
    assert r["shot"] == r["acquired"], f"{order}: arc 360 shot on tick {r['shot']}, acquired on {r['acquired']}"
    if order == "return_fire":
        assert r["enemy_shot"] == 1 and r["acquired"] == 2, "return fire scene: the enemy shoots first (tick 1), the subject answers"


# (order, arc, facing). The attack-move subject walks away along -x, so only the straight-behind facing keeps the
# enemy collinear with its heading (a sideways facing would be turned toward the heading while it walks, and the
# measured offset at acquisition would no longer be the fixture's).
FLANK_CASES = [(o, arc, math.pi) for o in ORDERS for arc in (90, 120, 180, 270)] + \
              [(o, 90, side) for o in ORDERS if o != "attack_move" for side in (math.pi / 2, -math.pi / 2)]


@pytest.mark.parametrize("order,arc,facing", FLANK_CASES,
                         ids=[f"{o}-a{a}-f{round(math.degrees(f))}" for o, a, f in FLANK_CASES])
def test_R_100_04_flanked_unit_turns_then_fires_on_the_derived_tick(lib, world_factory, order, arc, facing):
    """R-100-04: the enemy is behind (or 90 degrees off) the facing and outside the arc. The unit acquires on the same
    tick it does at arc 360 (acquisition is untouched), keeps the enemy as its target through the turn, fires
    nothing before the derived tick, and fires on it: acquired + steps - 1 with steps = ceil((offset - arc/2) / 0.2 rad).
    The facing read after the tick before the shot is outside the arc and after the shot tick inside it.
    Red on the E0 tree: the shot lands on the acquisition tick whatever the arc."""
    gated = _make(lib, world_factory, arc, order, facing=facing)
    free = _make(lib, world_factory, 360, order, facing=facing)
    assert gated["acquired"] == free["acquired"] is not None, "the arc moved the acquisition tick (it must not)"
    steps = turn_steps(facing, arc, RATE_LINE)
    expect = shot_tick(gated["acquired"], steps)
    assert gated["shot"] == expect, (
        f"{order} arc {arc} facing {facing:.3f}: first shot on tick {gated['shot']}, expected {expect} "
        f"(acquired {gated['acquired']}, {steps} turn steps at {RATE_LINE} rad/s)")
    for k in range(gated["acquired"], expect + 1):
        assert _row(gated, k)[1] == gated["e"], f"target dropped on tick {k} while turning"
    for k in range(gated["acquired"], expect):
        assert not _row(gated, k)[3], f"fired on tick {k}, before the target was inside the arc"
    half = math.radians(arc) / 2.0
    assert abs(_row(gated, expect)[2]) <= half + 1e-9, "fired with the target outside the arc"
    if expect > gated["acquired"]:
        assert abs(_row(gated, expect - 1)[2]) > half, "the tick before the shot already had the target inside the arc"


@pytest.mark.parametrize("order,arc,facing", FLANK_CASES,
                         ids=[f"{o}-a{a}-f{round(math.degrees(f))}" for o, a, f in FLANK_CASES])
def test_R_100_04_can_engage_reads_4_while_turning_and_0_on_the_shot_tick(lib, world_factory, order, arc, facing):
    """R-100-04 with the can_engage gate order (arc is reason 4): in each flank scene om_combat_can_engage(subject,
    enemy), read after every tick, is 4 on every tick from the acquisition tick to the tick before the first shot (the
    target is in reach, seen and in range, only the arc fails) and 0 on the shot tick. This ties can_engage's arc test to
    the fire pass's: a can_engage without the arc gate reads 0 while turning, a fire pass without it shoots on the
    acquisition tick (the test above). Control: at arc 360 the same scene reads 0 on the acquisition tick. Red on the E0
    tree: the stub answers -1."""
    def go(a):
        w = world_factory(n_regions=1)
        lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
        return scene(lib, w, arc=a, order="idle" if order == "return_fire" else order,
                     enemy_combat=order == "return_fire", facing=facing, query=True)
    free, gated = go(360), go(arc)
    assert _row(free, free["acquired"])[5] == 0, "arc 360: the target is engageable on the acquisition tick"
    shot, acq = gated["shot"], gated["acquired"]
    assert _row(gated, shot)[5] == 0, f"can_engage on the shot tick {shot} reads {_row(gated, shot)[5]}, not 0"
    assert shot > acq, "setup: a flanked unit must spend at least one tick turning"
    for k in range(acq, shot):
        assert _row(gated, k)[5] == 4, f"tick {k} (before the shot on {shot}): can_engage reads {_row(gated, k)[5]}, not 4"


def test_R_100_04_attack_move_unit_stops_and_turns_in_place(lib, world_factory):
    """R-100-04: the arc gates the shot only, never the hold. An attack-moving unit with the enemy behind it acquires,
    stops where it stands, turns, and fires: from the tick after acquisition to the shot its position does not
    change (and equals the position at arc 360 on the same tick, where it also holds)."""
    gated = _make(lib, world_factory, 90, "attack_move")
    free = _make(lib, world_factory, 360, "attack_move")
    a, f = gated["acquired"], gated["shot"]
    assert f is not None and f > a + 3, "setup: the shot was not delayed (red until the gate exists)"
    held_at = _row(gated, a + 1)[4]
    for k in range(a + 1, f + 1):
        assert _row(gated, k)[4] == held_at, f"the unit moved on tick {k} while turning (the hold must not consult the arc)"
    assert _row(free, a + 1)[4] == held_at, "the held position differs from the arc-360 run"


@pytest.mark.parametrize("arc,facing_off_deg,delayed", [(90, 40.0, False), (90, 70.0, True), (120, 55.0, False)],
                         ids=["inside_40_of_45", "outside_70_of_45", "inside_55_of_60"])
def test_R_100_04_target_inside_the_arc_fires_at_once(lib, world_factory, arc, facing_off_deg, delayed):
    """R-100-04 boundary pair: a target 40 degrees off the facing with a 90 degree arc (half 45) is inside, so the
    unit fires on the acquisition tick as at 360; 70 degrees off is outside and costs turn steps; 55 off with a
    120 arc (half 60) is inside. The inside cases are green on the E0 tree, the outside case is red."""
    off = math.radians(facing_off_deg)
    r = _make(lib, world_factory, arc, "idle", facing=off)
    expect = shot_tick(r["acquired"], turn_steps(off, arc, RATE_LINE))
    assert r["shot"] == expect
    assert (r["shot"] > r["acquired"]) == delayed


@pytest.mark.parametrize("subject,dist", [(RAIDER, RAIDER_DIST), (BOMBARD, DIST)], ids=["strike_raider", "siege_bombard"])
def test_R_100_04_the_turn_uses_the_category_rate(lib, world_factory, subject, dist):
    """R-100-02 under R-100-04: Strike turns at 6.0 rad/s (0.3 a tick) and Siege at 2.5 (0.125), so the same
    half turn at arc 90 costs 8 and 19 steps. The Bombard's shot is its area attack; the arc gates it as any shot.
    Red on the E0 tree (the shot lands on the acquisition tick)."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    r = scene(lib, w, arc=90, subject=subject, dist=dist)
    steps = turn_steps(math.pi, 90, RATE_OF[subject])
    assert steps in (8, 19)
    assert r["shot"] == shot_tick(r["acquired"], steps), f"first shot on tick {r['shot']}, acquired {r['acquired']}, {steps} steps"


def test_R_100_04_kiting_attack_target_faces_its_target_directly(lib, world_factory):
    """R-100-04: 'a unit kiting under attack-target faces its target directly'. A unit ordered to attack the enemy
    with its facing set away snaps to the target (no turn delay), so at arc 90 it fires on the very tick it does at
    arc 360 and its facing at that tick points at the enemy. Green on the E0 tree (nothing gates yet), and must stay
    green after E2: the gate must not make a kiting unit wait for a turn it does not make."""
    gated = _make(lib, world_factory, 90, "attack_target")
    free = _make(lib, world_factory, 360, "attack_target")
    assert free["shot"] is not None and gated["shot"] == free["shot"]
    assert abs(_row(gated, gated["shot"])[2]) < 1e-6, "the kiting unit does not face its target on the shot tick"


# ---------------------------------------------------------------- byte identity at 360

# Recorded on the E0 tree (push/labrev2-e0 @ 4decde94, ABI as there): fixed_fight_hash(arc=None) == fixed_fight_hash(arc=360).
TRACE_HASH_360 = "3a40902e950681c7b6e6d6ecc9595dd277e55f7f1a656f38231a6b0f44560770"
FIGHT_TICKS = 500


def _pack(*vals):
    return struct.pack("<%dd" % len(vals), *[float(v) for v in vals])


def hash_rows(rows):
    """sha256 over the byte image of the rows, each a tuple of numbers (doubles, little endian)."""
    h = hashlib.sha256()
    for row in rows:
        h.update(_pack(*row))
    return h.hexdigest()


def fixed_fight_rows(lib, world_factory, arc):
    """The fixed scene: 11 against 11 on layer 0 (6 Vanguard, 3 Raider, 1 Bombard, 1 Warden a side) in two blocks 700 wu
    apart, a Raider a side on layer 1 with reach (1, 1), every unit given its own attack-move to the middle, side 0
    facing +x and side 1 facing -x, world seed 1. After each of FIGHT_TICKS ticks the rows are, per unit in id order:
    (id, x, y, hp, facing, target) and then the fire events (shooter, target)."""
    w = world_factory(n_regions=1, seed=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    if arc is not None:
        assert set_param(lib, w, ARC, arc) == 0
    assert lib.om_roster_set_reach(w, RAIDER, 1, 1) == 0
    kinds = [VANGUARD] * 6 + [RAIDER] * 3 + [BOMBARD, WARDEN]
    ids = []
    for side, sx in ((0, -350.0), (1, 350.0)):
        sign = 1.0 if side == 0 else -1.0
        for i, kind in enumerate(kinds):
            col, row = divmod(i, 4)
            u = spawn(lib, w, kind, side, sx - sign * 40.0 * col, 40.0 * (row - 1.5))
            lib.om_unit_set_facing(w, u, 0.0 if side == 0 else math.pi)
            ids.append(u)
        extra = spawn(lib, w, RAIDER, side, sx + sign * 60.0, 0.0, layer=1)
        lib.om_unit_set_facing(w, extra, 0.0 if side == 0 else math.pi)
        ids.append(extra)
    for u in ids:
        _attack_move(lib, w, [u], 0.0, 0.0)  # one call per unit: the lone attack-move
    rows = []
    for tick in range(1, FIGHT_TICKS + 1):
        step(lib, w)
        for u in ids:
            rows.append((tick, u, lib.om_unit_position_x(w, u), lib.om_unit_position_y(w, u), lib.om_unit_get_hp(w, u),
                         lib.om_unit_get_facing(w, u), lib.om_unit_target(w, u)))
        for a, b in _fires(lib, w):
            rows.append((tick, -1, a, b, 0.0, 0.0, 0))
    return rows


def fixed_fight_hash(lib, world_factory, arc):
    return hash_rows(fixed_fight_rows(lib, world_factory, arc))


def test_control_hash_detector_sees_a_one_ulp_change():
    """Detector control: hash_rows differs when a single value moves by one unit in the last place and when a row
    is dropped, and is stable for equal input."""
    rows = [(1, 2, 3.0, 4.0, 5.0, 6.0, 7), (2, 2, 3.5, 4.5, 5.5, 6.5, 7)]
    bumped = [rows[0], (2, 2, math.nextafter(3.5, 4.0), 4.5, 5.5, 6.5, 7)]
    assert hash_rows(rows) == hash_rows(list(rows))
    assert hash_rows(rows) != hash_rows(bumped)
    assert hash_rows(rows) != hash_rows(rows[:1])


def test_control_fixed_fight_has_a_real_fight_in_it(lib, world_factory):
    """Control (green on the E0 tree): the fixed scene contains fire events, hp loss and movement, so the recorded
    digest covers a fight and not an empty hash of stationary units."""
    rows = fixed_fight_rows(lib, world_factory, None)
    fires = [r for r in rows if r[1] == -1]
    assert len(fires) > 50, f"only {len(fires)} fire events in {FIGHT_TICKS} ticks"
    first, last = {r[1]: r for r in rows if r[0] == 1 and r[1] != -1}, {r[1]: r for r in rows if r[0] == FIGHT_TICKS and r[1] != -1}
    assert any(last[u][4] < first[u][4] for u in first), "no unit lost hit points"
    assert any((last[u][2], last[u][3]) != (first[u][2], first[u][3]) for u in first), "nothing moved"


@pytest.mark.parametrize("arc", [None, 360], ids=["unset", "set_360"])
def test_R_100_04_arc_360_trace_is_byte_identical_to_the_recorded_baseline(lib, world_factory, arc):
    """R-100-04 / spec E2 row: at 360 the gate is bypassed entirely (no new float op), so the fixed fight's trace hash
    equals the one recorded on the E0 tree, with the setting left at its default and with it set to 360. Green on the
    E0 tree by construction; it goes red if the gate perturbs anything at 360."""
    assert fixed_fight_hash(lib, world_factory, arc) == TRACE_HASH_360


def test_R_100_04_a_narrow_arc_changes_the_fixed_fight(lib, world_factory):
    """R-100-04: the same fight at the narrowest arc the setting allows (10 degrees, OM_TP_FIRING_ARC_DEG's lower
    bound) is not the arc-360 fight (units that keep turning toward a moving enemy wait for the turn), so the
    byte-identity above is a statement about 360 and not about a setting that is never read. (Arc 90 and wider
    leave this particular fight unchanged: its units already face the enemy; the flank scenes above cover 90.)
    Red on the E0 tree: the setting is stored and never read, the two traces are the same."""
    assert fixed_fight_hash(lib, world_factory, 10) != TRACE_HASH_360, "arc 10 left the trace unchanged: the gate is not in the fire pass"
