"""Visible-game VG-CONTRACT-E7: the starting force (spec docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12c,
"Lane E1 part e", paragraph "E7, the starting force", and section 2). Fenced: builders never edit this file.

Rules proved (quoted word for word):
  R-218-06 (bible E-15, rewritten by E7's docs piece): "until S-211 the starting force is between a fifth and four fifths of F by the
    player's share of contested strongpoints at the start, and the structures can produce the rest". Westley, 2026-10-11:
    "players start with at least half-force when a match begins, if not as far down as 20% (specific number depends on the range of
    possible values for what the simulation currently is at for the specific mission being played, scaled)".
  R-126-04: "a player who holds every structure the whole mission fields at least F".
  R-218-03: "production is paid by the holder's economy, not free" (payment stays E2, ledger row FU-E7-production-paid: nothing here
    asserts a price).
Drafts: START_MIN 0.2 and START_SPAN 0.6 are the named draft DRAFT-start-fraction (register row Q-218-07): start = F * clamp(START_MIN +
START_SPAN * share, START_MIN, START_MIN + START_SPAN), capacity = F - start. Rulings that bind this file (gaps 4, 5, 6, 8, 9, 10 of the
E7 Architect rulings): start_units = floor(start + 0.5); reinforce_cap = F_units - start_units, integer arithmetic in mission.c;
om_mission_state holds uint32_t reinforce_cap, reinforce_spawned, both saved in the mission slot AND hashed in om_mis_net_hash (section 5
of om_world_checksum_full, mission.c OM_MIS_NET_SECTION); reinforce_cap is UINT32_MAX on a bare world with no mission set up; EVERY era
moves (structures are placed in every era, mission.c:2765); the cut order is per unit type n_t = floor(count_t * start_units / F_units
+ 0.5), the remainder (positive or negative) on the type with the largest count_t, lowest type index on ties.

Fixture: tests/csim/test_VG_E_e1h.py scene(): ground era (om_set_era_kind 1, the greek placeholder era), a 2-region world, region 0 the
enemy's HOME, region 1 the player's, om_mission_setup then om_mission_begin. e1h's own default military 0 fields NO player force
(F = 0, dumped), so these fixtures raise the region's military (premise dumped below: F, p, e, n, share, start, count).

POSITIVE CONTROLS (green today, and they stay green after E7): the row counter partitions the rows, F > 0, the structures' owners are
readable, and a player structure spawns a unit when its timer elapses. Everything else is red until E7 (the one-argument functions, the
full-force spawn, no cap, no hash of the counters, symbols absent).
"""
import ctypes
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from conftest import OMFeature
from test_VG_E_e1h import PLAYER, ENEMY, scene as e1h_scene

W = ctypes.c_void_p
P = ctypes.POINTER
D = ctypes.c_double
U32 = ctypes.c_uint32
U64 = ctypes.c_uint64

REPO = Path(__file__).resolve().parents[2]
SIEGE_BREAKING, ASSAULT = 1, 3
SPACE_ERA, GROUND_ERA = 0, 1
MISSION_SECTION = 5  # OM_MIS_NET_SECTION, csrc/mission.c: the mission slot's index in om_world_checksum_full's sections
N_SECTIONS = 9      # OM_NET_SECTION_COUNT

# DRAFT-start-fraction (ledger row DRAFT-start-fraction, register row Q-218-07): Westley owns these.
START_MIN = 0.2
START_SPAN = 0.6

# (label, archetype, military, seed, era). The dumped premise of each is asserted in test_control_premises_dump.
FIX_THIRD = ("assault_third", ASSAULT, 0.5, 1, GROUND_ERA)         # F 16 [2,2,1,11,0,0], p1 e2 n1, share 1/3, start 6.4 -> 6, cap 10
FIX_HALF = ("siege_half", SIEGE_BREAKING, 0.5, 1, GROUND_ERA)      # F 16, p1 e1 n2, share 1/2, start 8, cap 8
FIX_HALF_ROUND = ("siege_half_round", SIEGE_BREAKING, 0.3, 1, GROUND_ERA)  # F 9 [1,1,1,5,1,0], share 1/2, start 4.5 -> 5 (half rounds up), cap 4
FIX_TIE = ("assault_tie", ASSAULT, 0.05, 1, GROUND_ERA)            # F 2 [0,1,0,1,0,0], share 1/3, start 1.3 -> 1, tie on the largest count -> the lowest type index
FIX_NOSTRUCT = ("suppression_no_strongpoints", 4, 0.5, 1, GROUND_ERA)  # F 602, ground era places 0 structures: p + e == 0, share 0.5, start 301
FIX_SPACE = ("assault_third_space", ASSAULT, 0.5, 1, SPACE_ERA)    # the same mission in the space era: every era moves (gap 5)
STARTS = [FIX_THIRD, FIX_HALF, FIX_HALF_ROUND, FIX_TIE, FIX_NOSTRUCT, FIX_SPACE]
IDS = [f[0] for f in STARTS]

PRODUCER_POWER_TYPE = 0   # OM_MISSION_POWER_ANCHOR_UNIT_TYPE: the unit type the placed structures produce
NO_CAP = 0xFFFFFFFF       # UINT32_MAX


def bind(lib):
    lib.om_mission_compute_starting_force.argtypes, lib.om_mission_compute_starting_force.restype = [D, D], D
    lib.om_mission_compute_reinforcement_capacity.argtypes, lib.om_mission_compute_reinforcement_capacity.restype = [D, D], D
    lib.om_mission_get_player_units.argtypes, lib.om_mission_get_player_units.restype = [W, ctypes.c_int32, P(U32), U32], None
    lib.om_mission_get_enemy_faction.argtypes, lib.om_mission_get_enemy_faction.restype = [W], ctypes.c_int32
    lib.om_structure_count.argtypes, lib.om_structure_count.restype = [W], U32
    lib.om_structure_get_owner.argtypes, lib.om_structure_get_owner.restype = [W, U32], ctypes.c_int32
    lib.om_structure_set_owner.argtypes, lib.om_structure_set_owner.restype = [W, U32, ctypes.c_int32], None
    lib.om_structure_production_interval_ticks.argtypes, lib.om_structure_production_interval_ticks.restype = [D], U32
    lib.om_unit_power.argtypes, lib.om_unit_power.restype = [U32], D
    lib.om_unit_count.argtypes, lib.om_unit_count.restype = [W], U32
    lib.om_unit_get_faction.argtypes, lib.om_unit_get_faction.restype = [W, U32], ctypes.c_int32
    lib.om_unit_get_unit_type.argtypes, lib.om_unit_get_unit_type.restype = [W, U32], ctypes.c_int32
    lib.om_tactical_tick_to.argtypes, lib.om_tactical_tick_to.restype = [W, U64], U64
    lib.om_tactical_step.argtypes, lib.om_tactical_step.restype = [W], None
    lib.om_tactical_base_tick.argtypes, lib.om_tactical_base_tick.restype = [W], U64
    lib.om_save_state_size.argtypes, lib.om_save_state_size.restype = [W], U32
    lib.om_save_state_write.argtypes, lib.om_save_state_write.restype = [W, P(ctypes.c_uint8), U32], None
    lib.om_load_state_read.argtypes, lib.om_load_state_read.restype = [W, P(ctypes.c_uint8), U32], ctypes.c_int
    lib.om_world_checksum_full.argtypes, lib.om_world_checksum_full.restype = [W, P(U64), U32], U64


def bind_internal(lib):
    """The two gap-4 accessors (csrc/om_internal.h, not public, exported by the shared object like the economy entries).
    Absent today: the case that calls this is red for that reason."""
    missing = [n for n in ("om_mission_reinforce_cap", "om_mission_reinforce_note_spawn") if not hasattr(lib, n)]
    assert not missing, f"E7 internal accessors missing from the library: {missing}"
    lib.om_mission_reinforce_cap.argtypes, lib.om_mission_reinforce_cap.restype = [W], U32
    lib.om_mission_reinforce_note_spawn.argtypes, lib.om_mission_reinforce_note_spawn.restype = [W], None


def mission(lib, wf, fix):
    bind(lib)
    _, arch, mil, seed, era = fix
    return e1h_scene(lib, wf, archetype=arch, military=mil, seed=seed, era=era)


def roster(lib, w):
    arr = (U32 * 6)()
    lib.om_mission_get_player_units(w, PLAYER, arr, 6)
    return list(arr)


def split(lib, w):
    """(p, e, n) from om_structure_get_owner over om_structure_count; n (neutral, owner -1) is excluded from the share."""
    enemy = lib.om_mission_get_enemy_faction(w)
    owners = [lib.om_structure_get_owner(w, i) for i in range(lib.om_structure_count(w))]
    return sum(o == PLAYER for o in owners), sum(o == enemy for o in owners), sum(o < 0 for o in owners)


def share_of(p, e):
    return 0.5 if p + e == 0 else p / (p + e)


def start_units_of(f_units, share):
    frac = min(max(START_MIN + START_SPAN * share, START_MIN), START_MIN + START_SPAN)
    return int(math.floor(f_units * frac + 0.5))


def cut_of(counts, start_units):
    """Spec cut: n_t = floor(count_t * start_units / F + 0.5); the remainder to the largest count, lowest type index on ties."""
    f = sum(counts)
    n = [int(math.floor(c * start_units / f + 0.5)) for c in counts]
    big = max(range(len(counts)), key=lambda t: (counts[t], -t))
    n[big] += start_units - sum(n)
    return n


def rows(lib, w):
    """Counter {(faction, type): rows}. Rows are never freed within a battle, so a death does not lower a count: the count is
    'units ever on the field for that faction' and only production or the start spawn raises it."""
    c = Counter()
    for u in range(1, lib.om_unit_count(w) + 1):
        c[(lib.om_unit_get_faction(w, u), lib.om_unit_get_unit_type(w, u))] += 1
    return c


def n_rows(c, faction):
    return sum(v for (f, _), v in c.items() if f == faction)


def per_type(c, faction):
    return [c.get((faction, t), 0) for t in range(6)]


def premise(lib, w, fix):
    ros = roster(lib, w)
    f_units = sum(ros)
    p, e, n = split(lib, w)
    share = share_of(p, e)
    frac = min(max(START_MIN + START_SPAN * share, START_MIN), START_MIN + START_SPAN)
    start = f_units * frac
    su = int(math.floor(start + 0.5))
    count = n_rows(rows(lib, w), PLAYER)
    return {"fixture": fix[0], "archetype": fix[1], "military": fix[2], "seed": fix[3], "era": fix[4], "roster": ros, "F": f_units,
            "p": p, "e": e, "n": n, "share": share, "start": start, "start_units": su, "cap": f_units - su, "count_at_tick0": count,
            "tick": lib.om_tactical_base_tick(w)}


def interval_ticks(lib):
    return lib.om_structure_production_interval_ticks(D(lib.om_unit_power(PRODUCER_POWER_TYPE)))


def secs(lib, w):
    buf = (U64 * N_SECTIONS)()
    lib.om_world_checksum_full(w, buf, N_SECTIONS)
    return list(buf)


def save_bytes(lib, w):
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    return buf, n


# ---- POSITIVE CONTROLS (green today, first) ----

def test_control_row_counter_partitions_and_a_player_structure_spawns(lib, world_factory):
    """Control, E7 sentence 'spawning start_units units of the composed roster' read through a counter that works: on a ground mission
    (greek placeholder era, om_set_era_kind 1) F = sum(om_mission_get_player_units) > 0, the player fields at most F units at tick 0
    (today exactly F; after E7 start_units), every row is the player's or the enemy's (the counter partitions), and a player-owned
    structure spawns a unit when its timer elapses through om_tactical_tick_to. A red below means E7 is missing, not that the harness
    is broken. (The brief's 'count at tick 0 equals sum(get_player_units)' holds today but is exactly what E7 changes, so it is not
    kept as a control: it would go red when E7 lands.)"""
    w = mission(lib, world_factory, FIX_THIRD)
    f_units = sum(roster(lib, w))
    c0 = rows(lib, w)
    assert f_units > 0, "control setup: the fixture must field a force"
    assert 0 < n_rows(c0, PLAYER) <= f_units
    assert n_rows(c0, PLAYER) + n_rows(c0, ENEMY) == sum(c0.values()), "control: a row belongs to neither faction"
    p, e, n = split(lib, w)
    assert p >= 1 and e >= 1 and p + e + n == lib.om_structure_count(w), "control: structure owners unreadable"
    interval = interval_ticks(lib)
    assert interval > 0
    lib.om_tactical_tick_to(w, 3 * interval)
    assert n_rows(rows(lib, w), PLAYER) > n_rows(c0, PLAYER), "control: a player-owned structure spawned nothing in three intervals"


def test_control_premises_dump(lib, world_factory, capsys):
    """Premises dumped (run with -s to read them) and asserted, so a drifting generator turns THIS test red, not E7's. Dumped on the
    built tree origin/push/vg-e7-base: (archetype, military, seed, era) -> F, roster, p, e, n, share, start, start_units, cap, count."""
    got = {}
    for fix in STARTS:
        w = mission(lib, world_factory, fix)
        got[fix[0]] = premise(lib, w, fix)
        print("PREMISE " + json.dumps(got[fix[0]], sort_keys=True))
    assert got["assault_third"]["roster"] == [2, 2, 1, 11, 0, 0] and (got["assault_third"]["p"], got["assault_third"]["e"]) == (1, 2)
    assert got["siege_half"]["F"] == 16 and (got["siege_half"]["p"], got["siege_half"]["e"]) == (1, 1)
    assert got["siege_half_round"]["F"] == 9 and got["siege_half_round"]["start"] == pytest.approx(4.5)
    assert got["assault_tie"]["roster"] == [0, 1, 0, 1, 0, 0]
    assert got["suppression_no_strongpoints"]["p"] + got["suppression_no_strongpoints"]["e"] == 0
    assert got["assault_third_space"]["roster"] == got["assault_third"]["roster"]
    assert (got["assault_third"]["start_units"], got["assault_third"]["cap"]) == (6, 10)
    assert (got["siege_half_round"]["start_units"], got["siege_half_round"]["cap"]) == (5, 4)


# ---- (a0) the force-group accessor stub ----

def test_a0_force_group_accessor_stub_returns_zero(lib, world_factory):
    """E7 sentence 'int32_t om_mission_get_force_group(const om_world *w, uint32_t i) ... is declared as a stub in E7's header piece,
    riding the ABI 7 to 8 bump ... the stub body returns 0' (DRAFT, GAP 13). Stub until VG-E-startforce implements it, See also the
    spec E7 paragraph. This is the only thing E7 asserts about the accessor: 0 for i = 0 and for i past the roster. Red today: the
    symbol is absent from the library."""
    assert hasattr(lib, "om_mission_get_force_group"), "om_mission_get_force_group is absent from the library (declared by E7's header piece)"
    lib.om_mission_get_force_group.argtypes, lib.om_mission_get_force_group.restype = [W, U32], ctypes.c_int32
    w = mission(lib, world_factory, FIX_THIRD)
    assert lib.om_mission_get_force_group(w, 0) == 0
    assert lib.om_mission_get_force_group(w, sum(roster(lib, w)) + 5) == 0


# ---- (a) the two-argument functions ----

def test_a_share_outside_zero_one_stays_inside_a_fifth_to_four_fifths(lib):
    """E7 sentence 'start = F * clamp(START_MIN + START_SPAN * share, START_MIN, START_MIN + START_SPAN)' (DRAFT-start-fraction): a share
    outside 0..1 stays inside 0.2..0.8 of F. (The values (1000, 0.5) -> 500, (1000, 0) -> 200, (1000, 1) -> 800 live in the moved ke2
    tests, TD-VG-E-28.) Red today: the function takes one argument and returns F."""
    bind(lib)
    for share in (-5.0, -1.0, -0.01):
        assert lib.om_mission_compute_starting_force(1000.0, share) == 200.0, f"share {share}"
        assert lib.om_mission_compute_reinforcement_capacity(1000.0, share) == 800.0, f"share {share}"
    for share in (1.01, 2.0, 7.5):
        assert lib.om_mission_compute_starting_force(1000.0, share) == 800.0, f"share {share}"
        assert lib.om_mission_compute_reinforcement_capacity(1000.0, share) == 200.0, f"share {share}"
    seen = [lib.om_mission_compute_starting_force(1000.0, s / 10.0) for s in range(0, 11)]
    assert seen == sorted(seen) and len(set(seen)) == len(seen), "the starting force must rise with the share"
    for s in range(-3, 14):
        f = lib.om_mission_compute_starting_force(1000.0, s / 10.0)
        assert 200.0 <= f <= 800.0
        # float rounding only, not a game tolerance: start + capacity gives F back
        assert f + lib.om_mission_compute_reinforcement_capacity(1000.0, s / 10.0) == pytest.approx(1000.0, abs=1e-9)


# ---- (b) the starting count, with the premise dumped ----

@pytest.mark.parametrize("fix", STARTS, ids=IDS)
def test_b_player_count_at_tick_0_is_floor_start_plus_half(lib, world_factory, fix):
    """E7 sentence 'spawning start_units units ... start_units = floor(start + 0.5)': the player's unit count at tick 0 equals
    floor(start + 0.5) for the fixture's share, p / (p + e) from om_structure_get_owner over om_structure_count (n excluded; share 0.5
    when p + e == 0). R-218-06 / R-126-04. Every era (gap 5): FIX_SPACE is the space era. PREMISE DUMPED in the message: archetype, seed, F,
    p, e, n, share, start, count. Red today: the player fields the whole force F."""
    w = mission(lib, world_factory, fix)
    pr = premise(lib, w, fix)
    msg = "premise " + json.dumps(pr, sort_keys=True)
    assert pr["F"] > 0, msg
    assert pr["count_at_tick0"] == pr["start_units"], f"the player fields {pr['count_at_tick0']} units at tick 0, expected {pr['start_units']}; {msg}"
    assert pr["start_units"] < pr["F"], msg


@pytest.mark.parametrize("fix", [FIX_THIRD, FIX_HALF_ROUND, FIX_SPACE], ids=["assault_third", "siege_half_round", "assault_third_space"])
def test_b_the_roster_is_unchanged_the_cut_is_in_the_spawn(lib, world_factory, fix):
    """E7 sentence 'the mix stays the roster's': om_mission_get_player_units still reports the whole composed force F (the cap is
    F - start_units), only the spawn is cut. Red today: the cut is absent (count == F is caught by the case above; here the roster sum must
    exceed the spawned count, which today it does not)."""
    w = mission(lib, world_factory, fix)
    f_units = sum(roster(lib, w))
    assert n_rows(rows(lib, w), PLAYER) < f_units, f"nothing was cut: {n_rows(rows(lib, w), PLAYER)} spawned of F {f_units}"


# ---- (f) the cut order, the era scope, the no-mission case ----

@pytest.mark.parametrize("fix", [FIX_THIRD, FIX_HALF_ROUND, FIX_TIE, FIX_SPACE], ids=["assault_third", "siege_half_round", "assault_tie", "assault_third_space"])
def test_f_cut_order_per_type_with_the_remainder_on_the_largest(lib, world_factory, fix):
    """Gap 9: per unit type n_t = floor(count_t * start_units / F_units + 0.5); the remainder (positive or negative) lands on the type
    with the largest count_t, lowest type index on ties, so the sum is start_units and the mix stays the roster's. FIX_HALF_ROUND has
    remainder -2 on type 3; FIX_TIE has the tie between types 1 and 3 (remainder -1, so type 1 gives its unit up: [0,0,0,1,0,0]).
    Red today: the whole roster spawns."""
    w = mission(lib, world_factory, fix)
    ros = roster(lib, w)
    su = start_units_of(sum(ros), share_of(*split(lib, w)[:2]))
    want = cut_of(ros, su)
    got = per_type(rows(lib, w), PLAYER)
    assert sum(want) == su and min(want) >= 0
    assert got == want, f"per-type player units at tick 0 {got}, expected {want} (roster {ros}, start_units {su})"


def test_f_share_is_half_when_no_strongpoint_exists(lib, world_factory):
    """E7 sentence 'share 0.5 when p + e == 0': the ground era of a Suppression mission places no structure here (dumped), so the
    start is half of F. Red today: the player fields F."""
    w = mission(lib, world_factory, FIX_NOSTRUCT)
    assert lib.om_structure_count(w) == 0, "premise: this fixture places no structures"
    f_units = sum(roster(lib, w))
    assert n_rows(rows(lib, w), PLAYER) == int(math.floor(f_units * 0.5 + 0.5)), f"F {f_units}"


def test_f_reinforce_cap_accessor_values_and_the_bare_world(lib, world_factory):
    """Gap 4 and gap 6: om_mission_reinforce_cap (internal, om_internal.h) is F - start_units on a mission world and UINT32_MAX on a
    bare world with no mission set up. Red today: the symbol is absent."""
    bind_internal(lib)
    w = mission(lib, world_factory, FIX_THIRD)
    pr = premise(lib, w, FIX_THIRD)
    assert lib.om_mission_reinforce_cap(w) == pr["F"] - pr["start_units"]
    bare = world_factory(n_regions=1, seed=3)
    assert lib.om_mission_reinforce_cap(bare) == NO_CAP, "the cap on a bare world with no mission set up must be UINT32_MAX"


def test_f_bare_world_production_is_uncapped(lib, world_factory):
    """Gap 6: on a bare world (no om_mission_setup) production is uncapped, so tests/csim/test_core_support_driver.py and
    test_core_B14N_support_tick_materialise.py stay green unchanged. Control and regression pin, green today and after E7: a hand-built
    player structure spawns one unit per interval for ten intervals."""
    bind(lib)
    w = world_factory(n_regions=1, seed=11)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_structure_init(w, 0, 0, D(100.0))
    lib.om_structure_set_owner(w, 0, PLAYER)
    lib.om_structure_set_position(w, 0, 3000.0, 3000.0)
    lib.om_unit_spawn(w, 0, ENEMY, 100_000.0, 100_000.0, 0)  # om_tactical_step is a no-op with no units
    interval = lib.om_structure_production_interval_ticks(D(100.0))
    assert interval > 0
    for _ in range(10 * interval + 1):
        lib.om_tactical_step(w)
    assert n_rows(rows(lib, w), PLAYER) >= 10, "a bare world's player structure must keep producing past any mission cap"


# ---- (c) and (d) production stops at the cap, the enemy keeps producing ----

def run_to_cap(lib, w, pr, extra_intervals):
    """Step interval by interval to (cap + 6) intervals, then extra_intervals more. Returns (production counts when the run first
    covers (cap + 6) intervals, the same after the extra intervals, the peak production ever seen); a production count is a
    Counter of the rows added since tick 0, so it is independent of how many units the start spawned."""
    interval = interval_ticks(lib)
    base = rows(lib, w)
    horizon = (pr["cap"] + 6) * interval
    peak = 0
    t = 0
    while t < horizon:
        t += interval
        lib.om_tactical_tick_to(w, t)
        peak = max(peak, n_rows(rows(lib, w), PLAYER) - n_rows(base, PLAYER))
    at_cap = rows(lib, w)
    for _ in range(extra_intervals):
        t += interval
        lib.om_tactical_tick_to(w, t)
        peak = max(peak, n_rows(rows(lib, w), PLAYER) - n_rows(base, PLAYER))
    return base, at_cap, rows(lib, w), peak


@pytest.mark.parametrize("fix", [FIX_THIRD, FIX_TIE], ids=["assault_third", "assault_tie"])
def test_c_player_production_stops_at_reinforce_cap_and_d_the_enemy_keeps_producing(lib, world_factory, fix):
    """E7 sentence 'om_sup_structure_tick_production_driver spawns a unit for the player's faction only while reinforce_spawned <
    reinforce_cap, incrementing it; the enemy's production is unchanged'. (c) step past (cap + 6) intervals so the player's
    structure would have spawned well beyond the cap: the units produced since tick 0 are exactly F minus the units spawned at the
    start (the cap, read behaviourally, per the gap-4 rounding: start_units + cap = F), never more at any interval, and two intervals
    later still the same. (d) control: over those two intervals the enemy, whose structures keep their owners, still spawns.
    Red today: no cap, the player starts at F and keeps producing."""
    w = mission(lib, world_factory, fix)
    pr = premise(lib, w, fix)
    msg = "premise " + json.dumps(pr, sort_keys=True)
    assert pr["cap"] == pr["F"] - pr["start_units"] > 0, msg
    base, at_cap, after, peak = run_to_cap(lib, w, pr, extra_intervals=2)
    allowed = pr["F"] - n_rows(base, PLAYER)  # = reinforce_cap when the start spawned start_units (case b)
    assert peak <= allowed, f"the player produced {peak} units since tick 0, above F - spawned-at-start = {allowed}; {msg}"
    assert n_rows(at_cap, PLAYER) - n_rows(base, PLAYER) == allowed, f"the cap was never reached ({n_rows(at_cap, PLAYER) - n_rows(base, PLAYER)} produced, expected {allowed}); {msg}"
    assert n_rows(after, PLAYER) == n_rows(at_cap, PLAYER), f"the player's count moved after the cap; {msg}"
    # (d) enemy control: its production is unchanged by the player's cap
    assert n_rows(after, ENEMY) > n_rows(at_cap, ENEMY), f"the enemy stopped producing; {msg}"


# ---- (e) save round trip and determinism ----

def test_e_save_round_trip_keeps_reinforce_cap_and_reinforce_spawned(lib, world_factory):
    """E7 sentence 'a save round trip keeps reinforce_cap and reinforce_spawned' (saved in the mission slot). Save mid-way (some units
    already produced, the cap not yet reached), load into a fresh world, step both on: the production total over the whole run equals
    the cap F - spawned-at-start, never the cap plus the units spawned before the save. If reinforce_spawned were not saved the loaded
    world would produce a full cap more; if reinforce_cap were not saved it would produce without limit. Red today: no cap at all."""
    w = mission(lib, world_factory, FIX_THIRD)
    pr = premise(lib, w, FIX_THIRD)
    base = n_rows(rows(lib, w), PLAYER)
    allowed = pr["F"] - base
    interval = interval_ticks(lib)
    mid = 3 * interval
    lib.om_tactical_tick_to(w, mid)
    spawned_before = n_rows(rows(lib, w), PLAYER) - base
    assert 0 < spawned_before < pr["cap"], f"premise: save mid-way, spawned {spawned_before} of cap {pr['cap']}; premise " + json.dumps(pr, sort_keys=True)
    buf, size = save_bytes(lib, w)
    other = world_factory(n_regions=2, seed=999)
    lib.om_world_set_feature(other, OMFeature.TACTICAL, 1)
    assert lib.om_load_state_read(other, buf, size) == 0
    assert lib.om_tactical_base_tick(other) == mid, "premise: the loaded world resumes at the saved tick"
    horizon = (pr["cap"] + 6) * interval
    t = mid
    while t < horizon:
        t += interval
        lib.om_tactical_tick_to(w, t)
        lib.om_tactical_tick_to(other, t)
    total_a = n_rows(rows(lib, w), PLAYER) - base
    total_b = n_rows(rows(lib, other), PLAYER) - base
    assert total_a == allowed, f"the original produced {total_a} over the run, expected the cap {allowed}"
    assert total_b == allowed, f"the loaded world produced {total_b} over the whole run, expected the cap {allowed} (spawned before the save: {spawned_before})"


_WORKER = r"""
import sys, ctypes, hashlib, json
sys.path.insert(0, %(csim)r)
import conftest as C
lib = C.load_lib()
import test_VG_E_e7 as T
mk, created = C._world_factory_for(lib, None)
w = T.mission(lib, mk, T.FIX_THIRD)
lib.om_tactical_tick_to(w, 3 * T.interval_ticks(lib))
buf, size = T.save_bytes(lib, w)
print(json.dumps({"save": hashlib.sha256(bytes(buf)).hexdigest(), "size": size, "checksum_full": lib.om_world_checksum_full(w, None, 0)}))
"""


def test_e_two_processes_give_byte_identical_save_and_checksum(lib):
    """Determinism contract: two processes, same seed and command stream, byte-identical save bytes (sha256) and om_world_checksum_full.
    Green today (a control for the saved mission slot) and it must stay green after the counters join the save."""
    code = _WORKER % {"csim": str(REPO / "tests" / "csim")}
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=600, cwd=str(REPO / "tests" / "csim"))
        assert r.returncode == 0, r.stderr[-2000:]
        outs.append(json.loads(r.stdout.strip().splitlines()[-1]))
    assert outs[0] == outs[1], f"two processes diverged: {outs}"
    assert outs[0]["size"] > 0


# ---- (g) hash coverage ----

def test_g_identical_worlds_hash_equal_positive_control(lib, world_factory):
    """Positive control for (g): two worlds built from the same seed and mission hash equal in the mission section, and neutralising
    every structure owner alone does not move that section (so a later difference can only come from what production changed)."""
    a, a2, b = (mission(lib, world_factory, FIX_THIRD) for _ in range(3))
    for i in range(lib.om_structure_count(b)):
        lib.om_structure_set_owner(b, i, -1)
    assert secs(lib, a)[MISSION_SECTION] == secs(lib, a2)[MISSION_SECTION], "control: identical worlds hash differently"
    assert secs(lib, a)[MISSION_SECTION] == secs(lib, b)[MISSION_SECTION], "control: structure ownership alone moved the mission section"
    assert secs(lib, a)[MISSION_SECTION] != 0


def test_g_reinforce_spawned_changes_the_mission_hash(lib, world_factory):
    """E7 sentence 'two worlds differing only in reinforce_spawned give different om_mis_net_hash values (positive control)':
    reinforce_cap and reinforce_spawned are both hashed in om_mis_net_hash after player_units, as well as saved, because
    reinforce_spawned gates future spawns (an unhashed divergence is a silent desync). The handle is behavioural: in world A the player's
    structure spawns a unit (reinforce_spawned 1 or more), in world B every structure is neutral so nothing spawns (0); the two start
    with equal mission sections (the control above), and step to the same tick. Red today: the sections stay equal."""
    a, b = (mission(lib, world_factory, FIX_THIRD) for _ in range(2))
    for i in range(lib.om_structure_count(b)):
        lib.om_structure_set_owner(b, i, -1)
    assert secs(lib, a)[MISSION_SECTION] == secs(lib, b)[MISSION_SECTION], "control: the worlds must start equal"
    t = 2 * interval_ticks(lib)
    lib.om_tactical_tick_to(a, t)
    lib.om_tactical_tick_to(b, t)
    assert n_rows(rows(lib, a), PLAYER) > n_rows(rows(lib, b), PLAYER), "control: A produced nothing, so reinforce_spawned did not differ"
    assert secs(lib, a)[MISSION_SECTION] != secs(lib, b)[MISSION_SECTION], \
        "the mission section ignores reinforce_spawned (one world spawned a reinforcement, the other none)"


def test_g_note_spawn_changes_the_mission_hash_directly(lib, world_factory):
    """Same sentence through the internal setter om_mission_reinforce_note_spawn (om_internal.h, gap 4): two otherwise identical worlds,
    one notes a spawn, the other not: the mission section differs; two worlds that each note one spawn hash equal (control).
    Red today: the symbol is absent."""
    bind_internal(lib)
    a, a2, b = (mission(lib, world_factory, FIX_THIRD) for _ in range(3))
    assert secs(lib, a)[MISSION_SECTION] == secs(lib, a2)[MISSION_SECTION]
    lib.om_mission_reinforce_note_spawn(a)
    lib.om_mission_reinforce_note_spawn(a2)
    assert secs(lib, a)[MISSION_SECTION] == secs(lib, a2)[MISSION_SECTION], "control: equal histories hash differently"
    assert secs(lib, a)[MISSION_SECTION] != secs(lib, b)[MISSION_SECTION], "reinforce_spawned is not hashed in the mission section"
