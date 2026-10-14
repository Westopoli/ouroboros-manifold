# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, "Contract / Engine" (om_combat_can_engage), ruling 5, Pieces row E2.
# piece LAB-REV2-E2 (om_combat_can_engage body). Draft rule for the arc gate: R-100-04 (E-13 S-100).
"""om_combat_can_engage(w, attacker, target) -> int (spec Contract / Engine).

  -1  an unknown id, a dead attacker or target, the same or a neutral faction, attacker equal to target, or a
      non-combat attacker (Supply, Evacuation);
  else the FIRST failing reason in this ABSOLUTE diagnostic order (the engine's gates are a conjunction; the order is
  for reading):
   1 out of reach (the type's reach at the layer offset)
   2 not seen by the side (the target is stealthed, or OM_TP_TARGET_BY_SIGHT is on and the side's set, which includes
     live ping reveals, does not hold it)
   3 out of range at this offset (attack range times the offset multiplier)
   4 outside the arc (only when OM_TP_FIRING_ARC_DEG is below 360)
   5 line blocked (om_combat_can_shoot)
   0 every gate passes.
  It ignores cooldown, backswing, the cohort slot and the order kind: it answers "could fire this tick if ready".
  Parity is one-way: after tick t every fire event of tick t has can_engage 0, or -1 (Architect 2026-10-14, accepted
  wording: "-1 is allowed when either unit of the pair is dead after the tick"); 0 never implies a shot.
  Reason 5 needs a spotter in every scene that reaches it: a cover disc across the line blocks SIGHT before it blocks
  fire, so a lone attacker reads 2 (not seen), not 5; a friendly with a clear line to the target keeps the side's set
  holding it. Arc parity (the fire pass and can_engage agree on reason 4) is pinned in
  tests/csim/test_E13_S100_firing_arc.py (can_engage reads 4 on every turning tick and 0 on the shot tick of each flank
  scene); the fight-wide parity below is insensitive to the fire-pass arc gate, because a unit that shot anyway still reads 0.

Red on the E0 tree: the stub answers -1 for everything, so every test that expects a value other than -1 fails with
that value in the message (the pairs that expect -1 are written so that a base pair expecting 0 comes first, which is
red on the stub too). Green on the E0 tree: the detector checks at the bottom.

Fixture numbers (named): scenes use the roster's own ranges and sensors (Vanguard range 300, sensor 700; Bombard range
1200, sensor 300; Raider sensor 800), read as constants below from csrc/om_constants.h, and positions in whole wu.
Nothing here is a threshold. Every query is made before the first tick unless the test says otherwise (positions and
the side's sight are pure functions of the units' places, R-089-04)."""
import ctypes
import itertools
import math
import re

import pytest

from conftest import CSRC_DIR, OMFeature
from test_PP_unit_support import set_param, spawn, step

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION, SUPPLY, EVACUATION = range(8)
FRIEND, ENEMY, NEUTRAL = 0, 1, -1
ARC = "OM_TP_FIRING_ARC_DEG"
GATE_NAMES = {0: "ok", 1: "out of reach", 2: "not seen", 3: "out of range", 4: "outside the arc", 5: "line blocked"}


def _c(name):
    return float(re.search(rf"#define\s+{name}\s+([0-9.]+)", (CSRC_DIR / "om_constants.h").read_text()).group(1))


V_RANGE, V_SENSOR = _c("OM_ROSTER_VANGUARD_RANGE"), _c("OM_ROSTER_VANGUARD_SENSOR")
B_RANGE, B_SENSOR = _c("OM_ROSTER_BOMBARD_RANGE"), _c("OM_ROSTER_BOMBARD_SENSOR")


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def can(lib, w, a, t):
    return lib.om_combat_can_engage(w, a, t)


def pair(lib, w, a_type=VANGUARD, t_type=SUPPLY, dist=200.0, a_layer=0, t_layer=0, a_faction=FRIEND, t_faction=ENEMY, facing=0.0):
    """Attacker at the origin facing `facing`, target `dist` wu along +x. Returns (attacker, target)."""
    a = spawn(lib, w, a_type, a_faction, 0.0, 0.0, layer=a_layer)
    t = spawn(lib, w, t_type, t_faction, float(dist), 0.0, layer=t_layer)
    lib.om_unit_set_facing(w, a, facing)
    return a, t


# ---------------------------------------------------------------- the base pair: every gate passes

def test_R_can_engage_zero_when_every_gate_passes(lib, tw):
    """A Vanguard and an enemy Supply 200 wu apart on one layer, in range (300), in sight (700), facing it, nothing
    between: 0. Red on the E0 tree (the stub answers -1)."""
    a, t = pair(lib, tw)
    assert can(lib, tw, a, t) == 0


# ---------------------------------------------------------------- -1

def _base_then(lib, tw, bad):
    """The base pair must read 0 (so the -1 below is the change and the test is red on the stub), then `bad(a, t)`."""
    a, t = pair(lib, tw)
    assert can(lib, tw, a, t) == 0, "the base pair must be able to engage before the -1 case is made"
    return bad(a, t)


def test_R_can_engage_minus_one_unknown_ids(lib, tw):
    """-1 for an attacker id or a target id that names no unit (0, one past the last, a large one)."""
    def bad(a, t):
        return [can(lib, tw, 0, t), can(lib, tw, a, 0), can(lib, tw, 9999, t), can(lib, tw, a, 9999), can(lib, tw, 0, 0)]
    assert _base_then(lib, tw, bad) == [-1] * 5


def test_R_can_engage_minus_one_dead_attacker_or_target(lib, tw):
    """-1 once the attacker is dead, and once the target is dead (hit points set to 0)."""
    a, t = pair(lib, tw)
    a2, t2 = pair(lib, tw)       # a second pair on the same spot (nothing has ticked, so nothing has moved)
    assert can(lib, tw, a, t) == 0 and can(lib, tw, a2, t2) == 0
    lib.om_unit_set_hp(tw, t, 0.0)
    assert can(lib, tw, a, t) == -1, "dead target"
    lib.om_unit_set_hp(tw, a2, 0.0)
    assert can(lib, tw, a2, t2) == -1, "dead attacker"


def test_R_can_engage_minus_one_same_faction_and_neutral(lib, tw):
    """-1 for two units of the same faction, for a neutral (faction -1) target and for a neutral attacker."""
    base_a, base_t = pair(lib, tw)
    assert can(lib, tw, base_a, base_t) == 0
    friend = spawn(lib, tw, SUPPLY, FRIEND, 100.0, 0.0)
    neutral_t = spawn(lib, tw, SUPPLY, NEUTRAL, 100.0, 50.0)
    neutral_a = spawn(lib, tw, VANGUARD, NEUTRAL, 0.0, 100.0)
    assert can(lib, tw, base_a, friend) == -1, "same faction"
    assert can(lib, tw, base_a, neutral_t) == -1, "neutral target"
    assert can(lib, tw, neutral_a, base_t) == -1, "neutral attacker"


def test_R_can_engage_minus_one_attacker_equal_to_target(lib, tw):
    """-1 for a unit asked against itself."""
    a, t = pair(lib, tw)
    assert can(lib, tw, a, t) == 0
    assert can(lib, tw, a, a) == -1 and can(lib, tw, t, t) == -1


@pytest.mark.parametrize("kind", [SUPPLY, EVACUATION], ids=["supply", "evacuation"])
def test_R_can_engage_minus_one_non_combat_attacker(lib, tw, kind):
    """-1 for a Supply or Evacuation attacker, even against an enemy it could 'reach' (they never fire)."""
    a, t = pair(lib, tw)
    assert can(lib, tw, a, t) == 0
    nc = spawn(lib, tw, kind, FRIEND, 0.0, 60.0)
    assert can(lib, tw, nc, t) == -1


# ---------------------------------------------------------------- each reason, alone

def test_R_can_engage_1_out_of_reach_layer_offset(lib, tw):
    """Reason 1: reach (0, 0), an enemy one layer up inside range and sight: 1. Control (same scene): the type given
    reach (1, 0) reads 0 for the up-one enemy, still 1 for an enemy two layers up, and 1 for one layer DOWN (the
    reach is signed)."""
    a, t_up = pair(lib, tw, t_layer=1)
    assert lib.om_roster_set_reach(tw, VANGUARD, 0, 0) == 0
    assert can(lib, tw, a, t_up) == 1
    assert lib.om_roster_set_reach(tw, VANGUARD, 1, 0) == 0
    assert can(lib, tw, a, t_up) == 0, "reach (1, 0): the up-one enemy is within reach, in range (multiplier 1.0) and in sight"
    t_up2 = spawn(lib, tw, SUPPLY, ENEMY, 150.0, 0.0, layer=2)
    t_down = spawn(lib, tw, SUPPLY, ENEMY, 150.0, 40.0, layer=0)
    a2 = spawn(lib, tw, VANGUARD, FRIEND, 0.0, 40.0, layer=1)
    assert can(lib, tw, a, t_up2) == 1, "two layers up with reach 1"
    assert can(lib, tw, a2, t_down) == 1, "one layer down with reach down 0"


def test_R_can_engage_2_not_seen_bombard_without_and_with_a_spotter(lib, tw):
    """Reason 2: a Bombard (range 1200, sensor 300) and an enemy 600 wu away, in range: 2 while no friendly sees it.
    A friendly Raider spotter (sensor 800) 150 wu from the enemy puts it in the side's set: 0."""
    a, t = pair(lib, tw, a_type=BOMBARD, dist=600.0)
    assert 600.0 > B_SENSOR and 600.0 < B_RANGE
    assert can(lib, tw, a, t) == 2
    spotter = spawn(lib, tw, RAIDER, FRIEND, 450.0, 0.0)
    assert can(lib, tw, a, t) == 0, f"spotter {spotter} 150 wu from the target did not put it in the side's set"


def test_R_can_engage_2_a_ping_reveal_counts_as_seen(lib, tw):
    """Reason 2 and the ping: the side's set 'includes live ping reveals'. A Bombard at the origin, a friendly Raider
    at (0, 200) as the caster, an enemy 1000 wu east that neither sees: 2. After the Raider pings the enemy's point
    (and one tick passes, as the ping tests read it): 0."""
    a, t = pair(lib, tw, a_type=BOMBARD, dist=1000.0)
    spotter = spawn(lib, tw, RAIDER, FRIEND, 0.0, 200.0)
    assert set_param(lib, tw, "OM_TP_PING_REVEAL_TICKS", 300) == 0
    assert can(lib, tw, a, t) == 2
    assert lib.om_command_ping(tw, spotter, 0, 1000.0, 0.0) == 0
    step(lib, tw)
    assert can(lib, tw, a, t) == 0, "a live ping reveal did not put the target in the side's set"


def test_R_can_engage_2_stealth(lib, tw):
    """Reason 2: a stealthed target reads 2 even at 200 wu in plain sight; unstealthed again it reads 0."""
    a, t = pair(lib, tw)
    assert can(lib, tw, a, t) == 0
    lib.om_unit_set_stealth(tw, t, 1)
    assert can(lib, tw, a, t) == 2
    lib.om_unit_set_stealth(tw, t, 0)
    assert can(lib, tw, a, t) == 0


def test_R_can_engage_2_the_by_sight_switch(lib, world_factory):
    """Reason 2 follows OM_TP_TARGET_BY_SIGHT: with it on (the default) a Bombard's enemy 600 wu out, which no friendly
    sees, reads 2; with it off the side's set is no longer required and it reads 0, while a stealthed target (own
    clause) reads 2 either way. Two worlds, because a Vanguard's sensor in the same world would see the 600 wu target."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    b, u = pair(lib, w, a_type=BOMBARD, dist=600.0)
    assert can(lib, w, b, u) == 2
    assert set_param(lib, w, "OM_TP_TARGET_BY_SIGHT", 0) == 0
    assert can(lib, w, b, u) == 0
    lib.om_unit_set_stealth(w, u, 1)
    assert can(lib, w, b, u) == 2, "the stealthed target stayed hidden with the by-sight switch off"


def test_R_can_engage_3_out_of_range_and_the_offset_multiplier(lib, tw):
    """Reason 3: a Vanguard (range 300, sensor 700) and an enemy 350 wu out: seen, in reach, facing it: 3; at 250: 0.
    One layer up with reach (1, 0): range is 300 times OM_TP_RANGE_UP_1, so at multiplier 0.5 an enemy 200 wu out is
    out of range (3) and at 1.0 it is in range (0). Vision of the up-one layer is opened (1.0) so sight is not the
    reason."""
    a, t = pair(lib, tw, dist=V_RANGE + 50.0)
    assert V_RANGE + 50.0 < V_SENSOR
    assert can(lib, tw, a, t) == 3
    near = spawn(lib, tw, SUPPLY, ENEMY, V_RANGE - 50.0, 30.0)
    assert can(lib, tw, a, near) == 0
    assert lib.om_roster_set_reach(tw, VANGUARD, 1, 0) == 0
    assert set_param(lib, tw, "OM_TP_VISION_UP_1", 1.0) == 0
    up = spawn(lib, tw, SUPPLY, ENEMY, 200.0, 60.0, layer=1)
    assert set_param(lib, tw, "OM_TP_RANGE_UP_1", 1.0) == 0
    assert can(lib, tw, a, up) == 0
    assert set_param(lib, tw, "OM_TP_RANGE_UP_1", 0.5) == 0
    assert can(lib, tw, a, up) == 3


def test_R_can_engage_4_outside_the_arc_only_below_360(lib, tw):
    """Reason 4: a Vanguard facing away from an enemy 200 wu out, in range, in sight, clear line. At arc 360 (the
    default) the arc is not consulted: 0. At arc 90: 4. Facing 0.5 rad off the enemy is inside a 90 degree arc
    (half 0.785 rad): 0; 1.0 rad off is outside: 4."""
    a, t = pair(lib, tw, facing=math.pi)
    assert can(lib, tw, a, t) == 0, "arc 360: the arc is not a gate"
    assert set_param(lib, tw, ARC, 90) == 0
    assert can(lib, tw, a, t) == 4
    lib.om_unit_set_facing(tw, a, 0.5)
    assert can(lib, tw, a, t) == 0
    lib.om_unit_set_facing(tw, a, 1.0)
    assert can(lib, tw, a, t) == 4


def test_R_can_engage_5_line_blocked_by_a_cover_disc(lib, tw):
    """Reason 5: a cover disc (radius 40, height 5) between a Vanguard and an enemy 250 wu out, neither inside it: 5,
    when the side still sees the target. (A cover disc blocks SIGHT as well as fire, so the lone Vanguard would read
    2, not seen; a friendly Raider beside the target, with a clear line to it, keeps it in the side's set: the same
    reason the matrix scene carries that spotter.) Control: the enemy short of the disc (60 wu) and one off the line
    (125, 120) read 0."""
    a, t = pair(lib, tw, dist=250.0)
    assert can(lib, tw, a, t) == 0
    assert lib.om_map_add_cover(tw, 125.0, 0.0, 40.0, 5.0) != 0xFFFFFFFF
    assert can(lib, tw, a, t) == 2, "alone, the blocked line is also a lost sight line (setup)"
    spawn(lib, tw, RAIDER, FRIEND, 250.0, 150.0)
    assert can(lib, tw, a, t) == 5
    short = spawn(lib, tw, SUPPLY, ENEMY, 60.0, 0.0)
    off = spawn(lib, tw, SUPPLY, ENEMY, 125.0, 120.0)
    assert can(lib, tw, a, short) == 0
    assert can(lib, tw, a, off) == 0


# ---------------------------------------------------------------- the absolute order

BREAKERS = [1, 2, 3, 4, 5]


def _order_scene(lib, w, on):
    """The base pair (Vanguard at the origin facing +x, enemy Supply at 200, arc 90) with the gates in `on` broken:
    1 the target is one layer up (reach 0, 0), 2 the target is stealthed, 3 the target is 350 wu out (past 300, inside
    sight 700; one layer up it is still 350), 4 the attacker faces away (pi), 5 a cover disc stands across the line.
    A friendly Raider spotter stands beside the target in every scene (see below). Returns (attacker, target)."""
    assert set_param(lib, w, ARC, 90) == 0
    dist = V_RANGE + 50.0 if 3 in on else 200.0
    a, t = pair(lib, w, dist=dist, t_layer=1 if 1 in on else 0, facing=math.pi if 4 in on else 0.0)
    if 2 in on:
        lib.om_unit_set_stealth(w, t, 1)
    # The spotter: a friendly Raider (sensor 800) beside the target with a clear line to it, so the side still sees the
    # target when the cover disc (which blocks sight too) stands across the attacker's own line.
    spawn(lib, w, RAIDER, FRIEND, dist, 150.0)
    if 5 in on:
        lib.om_map_add_cover(w, 100.0, 0.0, 40.0, 5.0)
    return a, t


def test_R_can_engage_order_none_broken_is_zero(lib, tw):
    """The order matrix's positive control: no gate broken reads 0 on the matrix scene."""
    a, t = _order_scene(lib, tw, set())
    assert can(lib, tw, a, t) == 0


SUBSETS = [s for r in range(1, 6) for s in itertools.combinations(BREAKERS, r)]


@pytest.mark.parametrize("broken", SUBSETS, ids=["".join(map(str, s)) for s in SUBSETS])
def test_R_can_engage_reports_the_first_failing_gate_in_the_absolute_order(lib, world_factory, broken):
    """Every one of the 31 non-empty combinations of the five broken gates reads the SMALLEST broken gate's number:
    1 before 2 before 3 before 4 before 5, whatever else is also broken. (E.g. {1,5}: out of reach, not line blocked;
    {2,4}: not seen, not outside the arc; {3,4,5}: out of range.) The first failing reason is the answer."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    a, t = _order_scene(lib, w, set(broken))
    got = can(lib, w, a, t)
    assert got == min(broken), f"broken {broken}: can_engage {got} ({GATE_NAMES.get(got)}), expected {min(broken)} ({GATE_NAMES[min(broken)]})"


# ---------------------------------------------------------------- what it ignores

def test_R_can_engage_ignores_cooldown_and_backswing(lib, tw):
    """It answers 'could fire this tick if ready': a Bombard that has just fired is in backswing and its next shot is
    60 ticks off, and can_engage on a living enemy in range still reads 0 on that tick and for the 5 ticks after. (The
    target has 1000 hit points so it lives through the volley.)"""
    a, t = pair(lib, tw, a_type=BOMBARD, dist=250.0)
    lib.om_unit_set_hp(tw, t, 1000.0)
    fired_at = None
    for tick in range(1, 40):
        step(lib, tw)
        for i in range(lib.om_tactical_event_count(tw)):
            k, sh, tg, tk = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
            lib.om_tactical_event_get_at(tw, i, ctypes.byref(k), ctypes.byref(sh), ctypes.byref(tg), ctypes.byref(tk))
            if k.value == 0 and sh.value == a:
                fired_at = tick
        if fired_at:
            break
    assert fired_at, "the Bombard never fired"
    assert lib.om_unit_in_backswing(tw, a) == 1, "setup: the shooter should be in backswing on its shot tick"
    for _ in range(6):
        assert can(lib, tw, a, t) == 0
        step(lib, tw)


def test_R_can_engage_ignores_the_cohort_slot(lib, tw):
    """Four units spawned in a row have four different targeting-cohort slots (id mod 4); the same geometry reads 0 for
    all of them, at tick 0 and after each of the next 4 ticks."""
    a0, t = pair(lib, tw, a_type=BOMBARD, dist=250.0)
    shooters = [a0] + [spawn(lib, tw, BOMBARD, FRIEND, 0.0, 30.0 * i) for i in range(1, 4)]
    lib.om_unit_set_hp(tw, t, 1000.0)
    for tick in range(5):
        assert [can(lib, tw, s, t) for s in shooters] == [0, 0, 0, 0], f"tick {tick}"
        step(lib, tw)


def test_R_can_engage_ignores_the_order_kind(lib, tw):
    """The same geometry reads 0 whatever the attacker was told to do: idle, a plain move away, an attack-move away, a
    guard order."""
    reads = []
    a, t = pair(lib, tw)
    reads.append(can(lib, tw, a, t))
    a2, t2 = pair(lib, tw)       # more pairs on the same spot; stacking is harmless before any tick
    lib.om_command_move(tw, a2, -2000.0, 0.0)
    reads.append(can(lib, tw, a2, t2))
    a3, t3 = pair(lib, tw)
    arr = (ctypes.c_uint32 * 1)(a3)
    getattr(lib.om_command_attack_move, "raw", lib.om_command_attack_move)(tw, arr, 1, -2000.0, 0.0)
    reads.append(can(lib, tw, a3, t3))
    a4, t4 = pair(lib, tw)
    arr4 = (ctypes.c_uint32 * 1)(a4)
    getattr(lib.om_command_guard, "raw", lib.om_command_guard)(tw, arr4, 1)
    reads.append(can(lib, tw, a4, t4))
    assert reads == [0, 0, 0, 0], f"idle, move, attack-move, guard read {reads}"


# ---------------------------------------------------------------- one-way parity over the lab controls

def _lab_blob(lib, w, faction, kinds, cx, sign, damage_type=None):
    """A blob of `kinds` around (cx, 0): rows of 4, 40 wu apart, each unit with its own attack-move to the middle."""
    ids = []
    for i, kind in enumerate(kinds):
        col, row = divmod(i, 4)
        u = spawn(lib, w, kind, faction, cx - sign * 40.0 * col, 40.0 * (row - 1.5))
        lib.om_unit_set_facing(w, u, 0.0 if sign > 0 else math.pi)
        ids.append(u)
    for u in ids:
        arr = (ctypes.c_uint32 * 1)(u)
        getattr(lib.om_command_attack_move, "raw", lib.om_command_attack_move)(w, arr, 1, 0.0, 0.0)
    return ids


PLANTED = 100   # a registered type: the Vanguard with 20 percent more damage (the lab's planted-damage control)


def _register_planted(lib, w):
    rc = lib.om_roster_register_custom_unit(
        w, PLANTED, 1, b"planted", _c("OM_ROSTER_VANGUARD_HP"), 1.2 * _c("OM_ROSTER_VANGUARD_DAMAGE"),
        _c("OM_ROSTER_VANGUARD_INTERVAL"), V_RANGE, _c("OM_ROSTER_VANGUARD_SPEED"), V_SENSOR, 1.0, 0.0, 0)
    assert rc == 0


def _control_world(lib, world_factory, name):
    """The lab's three controls on the engine: 'mirror' 16 against 16 Vanguard blobs, 'numbers' 24 against 16, 'planted'
    16 of a type with 20 percent more damage against 16 Vanguards; one attack-move per unit; blobs 900 wu apart."""
    w = world_factory(n_regions=1, seed=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    n0, n1, t0 = {"mirror": (16, 16, VANGUARD), "numbers": (24, 16, VANGUARD), "planted": (16, 16, PLANTED)}[name]
    if name == "planted":
        _register_planted(lib, w)
    s0 = _lab_blob(lib, w, 0, [t0] * n0, -450.0, 1.0)
    s1 = _lab_blob(lib, w, 1, [VANGUARD] * n1, 450.0, -1.0)
    return w, s0 + s1


def _fires(lib, w):
    out = []
    for i in range(lib.om_tactical_event_count(w)):
        k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
        assert lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0
        if k.value == 0:
            out.append((a.value, b.value))
    return out


def parity_run(lib, w, ids, max_ticks, query=True):
    """Step the fight; after each tick check every fire event of the tick: can_engage must be 0, or -1 with the target
    dead (or the shooter dead: fire events of one tick are simultaneous and a shooter killed by another's hit in the
    same tick reads -1 for its own dead attacker, which is the same documented -1). Returns (fire events checked,
    violations, final hit points)."""
    checked, bad = 0, []
    for tick in range(1, max_ticks + 1):
        step(lib, w)
        if query:
            for (a, b) in _fires(lib, w):
                rc = can(lib, w, a, b)
                checked += 1
                dead = lib.om_unit_get_hp(w, b) <= 0.0 or lib.om_unit_get_hp(w, a) <= 0.0
                if not (rc == 0 or (rc == -1 and dead)):
                    bad.append((tick, a, b, rc))
        alive = {lib.om_unit_get_faction(w, u) for u in ids if lib.om_unit_get_hp(w, u) > 0.0}
        if len(alive) < 2:
            break
    return checked, bad, tuple(lib.om_unit_get_hp(w, u) for u in ids)


@pytest.mark.parametrize("name", ["mirror", "numbers", "planted"])
@pytest.mark.parametrize("arc", [360, 120], ids=["arc360", "arc120"])
def test_R_can_engage_parity_one_way_over_the_lab_controls(lib, world_factory, name, arc):
    """After every tick of each lab control (mirror, numbers, planted damage), every fire event of the tick has
    can_engage 0, or -1 because a unit of the pair is dead ("-1 is allowed when either unit of the pair is dead after
    the tick", Architect 2026-10-14; that 0 does not imply a shot is the spec's one-way parity, so nothing asserts the
    converse). Run at the default arc (360) and at the DRAFT arc 120, so the arc gate of the fire pass and of can_engage agree.
    Control inside: events were checked (a fight with no shots would pass vacuously). Querying does not change the
    fight: the final hit points equal a run with no queries. Red on the E0 tree (the stub answers -1 with both
    units alive)."""
    w, ids = _control_world(lib, world_factory, name)
    assert set_param(lib, w, ARC, arc) == 0
    checked, bad, final = parity_run(lib, w, ids, 1500)
    assert checked > 50, f"only {checked} fire events were checked"
    assert not bad, f"{len(bad)} fire events without can_engage 0; first (tick, shooter, target, rc): {bad[:3]}"
    w2, ids2 = _control_world(lib, world_factory, name)
    assert set_param(lib, w2, ARC, arc) == 0
    _c2, _b2, final2 = parity_run(lib, w2, ids2, 1500, query=False)
    assert final == final2, "calling om_combat_can_engage changed the fight"


def test_R_can_engage_parity_over_mixed_roster_layers_and_a_spotter_need(lib, world_factory):
    """Beyond the three controls: 6 Vanguards, 3 Raiders, a Bombard and a Warden a side plus a layer-1 Raider each with
    reach (1, 1), on the way to each other from 700 wu: the cross-layer, the sight and the area paths agree with the
    fire pass too."""
    w = world_factory(n_regions=1, seed=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_roster_set_reach(w, RAIDER, 1, 1) == 0
    kinds = [VANGUARD] * 6 + [RAIDER] * 3 + [BOMBARD, WARDEN]
    ids = []
    for side, sx in ((0, -350.0), (1, 350.0)):
        sign = 1.0 if side == 0 else -1.0
        block = _lab_blob(lib, w, side, kinds, sx, sign)
        extra = spawn(lib, w, RAIDER, side, sx + sign * 60.0, 0.0, layer=1)
        lib.om_unit_set_facing(w, extra, 0.0 if side == 0 else math.pi)
        arr = (ctypes.c_uint32 * 1)(extra)
        getattr(lib.om_command_attack_move, "raw", lib.om_command_attack_move)(w, arr, 1, 0.0, 0.0)
        ids += block + [extra]
    checked, bad, _final = parity_run(lib, w, ids, 800)
    assert checked > 50
    assert not bad, f"{len(bad)} fire events without can_engage 0; first (tick, shooter, target, rc): {bad[:3]}"


# ---------------------------------------------------------------- detector checks (green on the E0 tree)

def test_control_parity_detector_flags_a_wrong_answer():
    """The parity rule used above, extracted: 0 passes, -1 with a dead unit passes, -1 with both alive and any positive
    reason fail. (The detector can fire.)"""
    def ok(rc, dead):
        return rc == 0 or (rc == -1 and dead)
    assert ok(0, False) and ok(-1, True)
    assert not ok(-1, False) and not ok(3, False) and not ok(3, True)


def test_control_order_matrix_covers_every_combination_once():
    """31 non-empty subsets of five gates, each distinct, each with a defined minimum."""
    assert len(SUBSETS) == 31 and len(set(SUBSETS)) == 31 and all(min(s) in GATE_NAMES for s in SUBSETS)
