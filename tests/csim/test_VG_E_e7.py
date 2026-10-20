"""VG-CONTRACT-E7 (lane E1 part e, spec docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12c, "E7, the starting
force"): the player starts with a fraction of F set by their share of the contested strongpoints; the structures produce the
rest, up to a cap; the enemy's production is unchanged. Fenced: builders never edit this file.

Rules proven (word for word):
  R-218-06 as the spec rewrites it: "until S-211 the player starts with at least half of F, sliding down to a fifth only when
    the player holds almost none of the contested strongpoints at the start and up to four fifths when they hold them all,
    and the structures can produce the rest" (Westley 2026-10-11: "players start with at least half-force when a match begins,
    if not as far down as 20% (specific number depends on the range of possible values for what the simulation currently is
    at for the specific mission being played, scaled)"; Architect reading 2026-10-19, Westley to confirm, register row Q-218-07).
  R-126-04: "a player who holds every structure the whole mission fields at least F" (start + production up to the cap = F).
  R-218-03: "production is paid by the holder's economy, not free" (payment stays E2; row FU-E7-production-paid: nothing here
    asserts a charge).
  Naming: START_KNEE 0.25 is the named draft DRAFT-e7-floor-knee (Westley owns the number); the five pins at F 1000 are
  600 (share 0.5), 400 capacity, 200 (share 0), 500 (share 0.25), 800 (share 1) and live in test_VG_E_ke2.py.

Each case names the E7 sentence it proves in its docstring. Rulings taken as written: gap 4 (reinforce_cap and
reinforce_spawned are uint32 in om_mission_state, saved in the mission slot AND hashed in om_mis_net_hash, integer arithmetic
in mission.c only, start_units = floor(start + 0.5), reinforce_cap = F_units - start_units), gap 5 (EVERY era moves),
gap 6 (reinforce_cap is UINT32_MAX on a bare world with no mission set up), gap 9 (the cut: per type
n_t = floor(count_t * start_units / F_units + 0.5), the remainder, positive or negative, on the type with the largest
count_t, lowest type index on ties).

Scene: tests/csim/test_VG_E_e1h.py scene(): greek placeholder era (om_set_era_kind 1; era 0 is the space era), a player home
region, om_mission_begin called. Fixtures below are small (F 16 and 845 for production-free cases) so that production to the
cap runs in a few thousand ticks with the tactical period at 1. Counts are rows of om_unit_get_faction: unit rows are never
freed within a battle (csrc/mission.c), so "spawned" is robust to units dying in the fight; alive counts are used only at
tick 0, where nothing has died.

Premises are dumped by premise() (printed as PREMISE ... with -s, and inside every assertion message): archetype, seed, era,
F, p, e, n, share, start, start_units, cap, tick, count. See the writer's report for the values on the built tree.
Red today for the stated reason: E7 is absent (the player spawns all of F, production is uncapped, the hash and the save
do not carry reinforce_cap and reinforce_spawned, the accessor symbol does not exist).
"""
import ctypes
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import (OMArchetype, OMEdge, OMFeature, OMTier, set_edge, set_faction, set_owner, set_region)
from test_E16_S111_saving import _load, _save
from test_net_section_hashes import N_SECTIONS, _secs
from test_VG_E_e1h import ENEMY, PLAYER, bind as e1h_bind, scene as e1h_scene

REPO = Path(__file__).resolve().parents[2]
V = ctypes.c_void_p
U32, I32, U64, D = ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint64, ctypes.c_double
MISSION_SECTION = 5  # csrc/mission.c OM_MIS_NET_SECTION
N_ROSTER = 16  # om_mission_get_player_units writes OM_MISSION_N_UNIT_TYPES (6) entries; the rest stay 0
START_KNEE = 0.25  # DRAFT-e7-floor-knee (Architect 2026-10-19, Westley to confirm; register row Q-218-07)
UINT32_MAX = 0xFFFFFFFF

# name -> kwargs of scene(). Chosen from a sweep of archetype x military x seed on the built tree (see the report):
# every one of them spawns the whole roster at tick 0 today (count == F), so a lower count is E7 and nothing else.
FIXTURES = {
    "ground_third": dict(archetype=2, military=0.5, seed=1, era=1),          # F 16, p 1, e 2, n 0: share 1/3
    "ground_two_thirds": dict(archetype=7, military=0.5, seed=1, era=1),     # F 16, p 2, e 1, n 0: share 2/3
    "ground_half": dict(archetype=1, military=30.0, seed=1, era=1),          # F 845, p 1, e 1, n 2: share 1/2
    # The next three carry a cut remainder (gap 9): the per-type rounded parts miss start_units by +1, -1 and -2.
    "ground_rem_pos": dict(archetype=1, military=0.7, seed=1, era=1),        # F 20, p 1, e 1: start_units 12, remainder +1
    "ground_rem_neg": dict(archetype=2, military=1.0, seed=1, era=1),        # F 28, p 1, e 2: start_units 15, remainder -1
    "ground_rem_neg2": dict(archetype=1, military=0.3, seed=1, era=1),       # F 9, p 1, e 1: start_units 5, remainder -2
    "ground_no_strongpoint": dict(archetype=4, military=0.0, seed=1, era=1),  # F 602, p 0, e 0: slope cap leaves none
    "space_half": dict(archetype=4, military=0.0, seed=1, era=0),            # F 602, p 1, e 1: era 0 moves too (gap 5)
}


# ------------------------------------------------------------------------------------------------ the oracle (spec text)

def frac(share):
    """Spec: frac(share) = 0.2 + 1.2 * share for share <= START_KNEE, 0.5 + 0.4 * (share - START_KNEE) above it; share
    clamped to [0, 1]. Plain double arithmetic in this order, as the C does."""
    share = min(max(share, 0.0), 1.0)
    return 0.2 + 1.2 * share if share <= START_KNEE else 0.5 + 0.4 * (share - START_KNEE)


def oracle_units(F, p, e):
    """(start_units, reinforce_cap): start = F * frac(p / (p + e)); start_units = floor(start + 0.5); cap = F - start_units;
    when p + e == 0 the whole F spawns and the cap is 0 (Architect 2026-10-19, under 5 percent)."""
    if p + e == 0:
        return F, 0
    start = F * frac(p / (p + e))
    start_units = math.floor(start + 0.5)
    return start_units, F - start_units


def oracle_cut(roster, start_units):
    """Gap 9: n_t = floor(count_t * start_units / F + 0.5) per type (exact: (2 count S + F) // 2F); the remainder, positive
    or negative, lands on the type with the largest count, lowest type index on ties."""
    F = sum(roster)
    n = [(2 * c * start_units + F) // (2 * F) for c in roster]
    n[max(range(len(roster)), key=lambda t: (roster[t], -t))] += start_units - sum(n)
    return n


# ------------------------------------------------------------------------------------------------ world helpers

def _bind(lib):
    e1h_bind(lib)
    lib.om_tactical_tick_to.argtypes, lib.om_tactical_tick_to.restype = [V, U64], U64
    lib.om_tactical_base_tick.argtypes, lib.om_tactical_base_tick.restype = [V], U64
    lib.om_tactical_tick_period.argtypes, lib.om_tactical_tick_period.restype = [V], U32
    lib.om_era_kind.argtypes, lib.om_era_kind.restype = [V], ctypes.c_int
    lib.om_unit_count.argtypes, lib.om_unit_count.restype = [V], U32
    lib.om_unit_alive.argtypes, lib.om_unit_alive.restype = [V, U32], ctypes.c_int
    lib.om_unit_get_faction.argtypes, lib.om_unit_get_faction.restype = [V, U32], I32
    lib.om_unit_get_unit_type.argtypes, lib.om_unit_get_unit_type.restype = [V, U32], I32
    lib.om_structure_count.argtypes, lib.om_structure_count.restype = [V], U32
    lib.om_structure_get_owner.argtypes, lib.om_structure_get_owner.restype = [V, U32], I32
    lib.om_structure_get_unit_type.argtypes, lib.om_structure_get_unit_type.restype = [V, U32], U32
    lib.om_structure_set_owner.argtypes, lib.om_structure_set_owner.restype = [V, U32, I32], None
    lib.om_unit_power.argtypes, lib.om_unit_power.restype = [U32], D
    lib.om_structure_production_interval_ticks.argtypes, lib.om_structure_production_interval_ticks.restype = [D], U32
    lib.om_mission_get_player_units.argtypes, lib.om_mission_get_player_units.restype = [V, I32, ctypes.POINTER(U32), U32], None


def build(lib, world_factory, name):
    _bind(lib)
    return e1h_scene(lib, world_factory, **FIXTURES[name])


def rows(lib, w, faction):
    """Ids of every unit row of the faction, alive or not (rows are never freed within a battle)."""
    return [u for u in range(1, lib.om_unit_count(w) + 1) if lib.om_unit_get_faction(w, u) == faction]


def roster_of(lib, w):
    buf = (U32 * N_ROSTER)()
    lib.om_mission_get_player_units(w, PLAYER, buf, N_ROSTER)
    return list(buf)


def owners_of(lib, w):
    return [lib.om_structure_get_owner(w, i) for i in range(lib.om_structure_count(w))]


def premise(lib, w, name):
    """The dumped premise: everything the expectations rest on, printed (PREMISE ...) and returned."""
    roster = roster_of(lib, w)
    owners = owners_of(lib, w)
    p, e, n = owners.count(PLAYER), owners.count(ENEMY), owners.count(-1)
    F = sum(roster)
    start_units, cap = oracle_units(F, p, e)
    share = p / (p + e) if p + e else None
    start = F * frac(share) if share is not None else float(F)
    d = dict(fixture=name, **FIXTURES[name], era_kind=lib.om_era_kind(w), roster=roster, F=F, p=p, e=e, n=n, share=share,
             start=start, start_units=start_units, cap=cap, tick=lib.om_tactical_base_tick(w),
             period=lib.om_tactical_tick_period(w), count=len(rows(lib, w, PLAYER)),
             alive=sum(1 for u in rows(lib, w, PLAYER) if lib.om_unit_alive(w, u)))
    print("PREMISE", json.dumps(d, sort_keys=True))
    return d


def first_interval(lib, w, faction):
    """Base ticks between spawns of a structure of the faction (all fixture structures share the anchor unit type)."""
    slot = owners_of(lib, w).index(faction)
    return lib.om_structure_production_interval_ticks(lib.om_unit_power(lib.om_structure_get_unit_type(w, slot)))


def spawn_series(lib, w, faction, intervals, interval):
    """Rows spawned for the faction since the call, sampled after each production interval (tick_to is the driver)."""
    base = len(rows(lib, w, faction))
    out = []
    for k in range(1, intervals + 1):
        lib.om_tactical_tick_to(w, k * interval)
        out.append(len(rows(lib, w, faction)) - base)
    return out


# ------------------------------------------------------------------------------------------------ POSITIVE CONTROL (green today)

def test_control_tick0_count_is_the_roster_sum_and_a_player_structure_spawns(lib, world_factory):
    """POSITIVE CONTROL, green on the built tree: on the ground fixture the player's unit count at tick 0 is the sum of
    om_mission_get_player_units, and a player-owned structure spawns one unit when its timer elapses through
    om_tactical_tick_to. A red below therefore means E7 is missing, not that the harness is broken. (After E7 the first half
    of this control is replaced by (b); the second half stays: the structure must still spawn while under the cap.)"""
    w = build(lib, world_factory, "ground_third")
    d = premise(lib, w, "ground_third")
    assert d["era_kind"] == 1 and d["tick"] == 0 and d["period"] == 1 and d["F"] > 0 and d["p"] >= 1, d
    # Control for the tick-0 half: it can only be asserted as "the count is a roster-derived number"; before E7 that
    # number is F, after E7 it is start_units (<= F). Either way it is never above F and never zero here.
    assert 0 < d["alive"] <= d["F"], d
    interval = first_interval(lib, w, PLAYER)
    before = len(rows(lib, w, PLAYER))
    lib.om_tactical_tick_to(w, interval - 1)
    assert len(rows(lib, w, PLAYER)) == before, f"a unit spawned before the production interval {interval} elapsed: {d}"
    lib.om_tactical_tick_to(w, interval)
    assert len(rows(lib, w, PLAYER)) == before + d["p"], f"the player structure did not spawn at tick {interval}: {d}"


def test_control_enemy_structure_spawns_and_oracle_pins(lib, world_factory):
    """POSITIVE CONTROL (green today): an enemy-owned structure spawns a unit at its interval (the control for (d)), and the
    Python oracle gives the five spec pins: frac(0.5) = 0.6, frac(0) = 0.2, frac(0.25) = 0.5, frac(1) = 0.8 of F 1000, and a
    cut whose parts sum to start_units, so a red in the cases below is the build and not the oracle."""
    w = build(lib, world_factory, "ground_third")
    d = premise(lib, w, "ground_third")
    interval = first_interval(lib, w, ENEMY)
    before = len(rows(lib, w, ENEMY))
    lib.om_tactical_tick_to(w, interval)
    assert len(rows(lib, w, ENEMY)) == before + d["e"], d
    assert [round(1000 * frac(s)) for s in (0.5, 0.0, 0.25, 1.0)] == [600, 200, 500, 800]
    assert oracle_units(1000, 1, 1) == (600, 400)
    for roster, s in (([5, 3, 2], 7), ([5, 5, 0], 3), ([1, 1, 1], 2)):
        assert sum(oracle_cut(roster, s)) == s


# ------------------------------------------------------------------------------------------------ (a0) the accessor stub

def test_a0_force_group_accessor_exists_and_the_stub_returns_zero(lib, world_factory):
    """E7 (a0): "the accessor int32_t om_mission_get_force_group(const om_world *w, uint32_t i) ... returns 1..3, 0 for none
    is declared as a stub in E7's header piece, riding the ABI 7 to 8 bump ... the stub body returns 0 and the real body lands
    in VG-E-startforce". Module mission.c; i is the i-th player unit in spawn order. E7 asserts only that the symbol exists
    and answers 0 for i = 0 and for i past the roster (DRAFT, GAP 13). Stub until VG-E-startforce implements it, See also the
    spec E7 paragraph. Red today: the symbol is absent from the library."""
    w = build(lib, world_factory, "ground_third")
    assert hasattr(lib, "om_mission_get_force_group"), "om_mission_get_force_group is absent from the library (ABI 7; E7 adds it at ABI 8)"
    fn = lib.om_mission_get_force_group
    fn.argtypes, fn.restype = [V, U32], I32
    assert fn(w, 0) == 0, "stub: i = 0 answers 0 until VG-E-startforce"
    assert fn(w, 1_000_000) == 0, "past the roster answers 0"


# ------------------------------------------------------------------------------------------------ (a) the two-argument functions

@pytest.mark.parametrize("share", [-0.5, -1e-9, 1.0 + 1e-9, 1.5, 7.0])
def test_a_share_outside_zero_one_is_clamped_inside_a_fifth_to_four_fifths(lib, share):
    """E7 (a): "`share` clamped to [0, 1]" so "start = F * frac(share)" stays inside 0.2..0.8 of F, and "capacity = F - start"
    stays inside 0.2..0.8 too. The in-range pins (600/400/200/500/800) are in test_VG_E_ke2.py. Red today: the functions take
    one argument (or (F, ticks)) and answer F and 0."""
    lib.om_mission_compute_starting_force.argtypes, lib.om_mission_compute_starting_force.restype = [D, D], D
    lib.om_mission_compute_reinforcement_capacity.argtypes, lib.om_mission_compute_reinforcement_capacity.restype = [D, D], D
    start = lib.om_mission_compute_starting_force(1000.0, share)
    cap = lib.om_mission_compute_reinforcement_capacity(1000.0, share)
    expect = 200.0 if share < 0.0 else 800.0
    assert start == pytest.approx(expect, abs=1e-5), f"share {share}: start {start}, clamped expectation {expect}"
    assert 200.0 - 1e-5 <= start <= 800.0 + 1e-5 and 200.0 - 1e-5 <= cap <= 800.0 + 1e-5, (start, cap)
    assert start + cap == pytest.approx(1000.0, abs=1e-5), "capacity = F - start"


# ------------------------------------------------------------------------------------------------ (b) tick-0 count, (f) era

def test_b_premise_is_not_on_a_rounding_half(lib, world_factory):
    """Premise guard (green): for every fixture start = F * frac(share) is at least 1e-6 away from an .5 boundary, so
    floor(start + 0.5) is not an accident of the last bit and the cases below fail only for E7."""
    for name in FIXTURES:
        d = premise(lib, build(lib, world_factory, name), name)
        if d["share"] is None:
            continue
        assert abs((d["start"] % 1.0) - 0.5) > 1e-6, d


@pytest.mark.parametrize("name", ["ground_third", "ground_two_thirds", "ground_half", "space_half", "ground_rem_pos", "ground_rem_neg", "ground_rem_neg2"])
def test_b_player_count_at_tick_0_is_start_units(lib, world_factory, name):
    """E7 (b), gap 5 (EVERY era moves): "`om_mission_instantiate_map` spawns the player's force after
    `om_mission_place_structures` (so `p` and `e` are known), spawning `start_units` units ... `start_units = floor(start +
    0.5)`" for the fixture's share, p and e read from om_structure_get_owner over om_structure_count (n excluded), F the sum of
    om_mission_get_player_units. The 'space_half' fixture is era 0: the space era moves too. Red today: the count is F."""
    w = build(lib, world_factory, name)
    d = premise(lib, w, name)
    assert d["tick"] == 0 and d["F"] > 0 and d["p"] + d["e"] > 0 and 0.0 <= d["share"] <= 1.0, d
    assert d["start_units"] < d["F"], f"fixture does not exercise the cut: {d}"
    assert d["count"] == d["start_units"], (
        f"the player has {d['count']} units at tick 0 of {name}, E7 wants floor(start + 0.5) = {d['start_units']} of F {d['F']} "
        f"(share {d['share']}); PREMISE {d}")


def test_b_no_contested_strongpoint_spawns_the_whole_force(lib, world_factory):
    """E7 (b): "when `p + e == 0` the whole F spawns and the capacity is 0, nothing could produce it; Architect 2026-10-19,
    under 5 percent" (start = F, capacity 0). The ground fixture whose slope cap leaves no strongpoint. Green today and after
    E7 (the whole force is also today's behaviour); it pins the clause so E7 cannot cut a force nothing could refill."""
    w = build(lib, world_factory, "ground_no_strongpoint")
    d = premise(lib, w, "ground_no_strongpoint")
    assert d["p"] + d["e"] == 0 and d["F"] > 0 and d["start_units"] == d["F"] and d["cap"] == 0, d
    assert d["count"] == d["F"], d


# ------------------------------------------------------------------------------------------------ (f) the cut

@pytest.mark.parametrize("name", ["ground_third", "ground_two_thirds", "ground_half", "space_half", "ground_rem_pos", "ground_rem_neg", "ground_rem_neg2"])
def test_f_the_cut_keeps_the_rosters_mix(lib, world_factory, name):
    """E7 (f), gap 9, spec text exactly: "per unit type `n_t = floor(count_t * start_units / F_units + 0.5)`; the remainder
    (positive or negative) lands on the type with the largest `count_t`, lowest type index on ties, so the sum is `start_units`
    and the mix stays the roster's". Compared per type with the player's alive units at tick 0. Red today: every type is whole."""
    w = build(lib, world_factory, name)
    d = premise(lib, w, name)
    by_type = [0] * len(d["roster"])
    for u in rows(lib, w, PLAYER):
        by_type[lib.om_unit_get_unit_type(w, u)] += 1
    expect = oracle_cut(d["roster"], d["start_units"])
    print("CUT", name, "roster", d["roster"], "start_units", d["start_units"], "expected", expect, "got", by_type)
    assert by_type == expect, f"per-type player units {by_type} != the gap-9 cut {expect} of roster {d['roster']}; PREMISE {d}"


def test_f_the_cut_exercises_a_remainder_of_each_sign(lib, world_factory):
    """Detector control (green): the fixtures include a positive and a negative cut remainder (the per-type rounded parts miss
    start_units), so the 'remainder, positive or negative, lands on the largest type' clause is proven by (f), not vacuous;
    and in each of them the largest type is the one that absorbed it (the oracle's choice differs from the rounded part)."""
    rems = {}
    for name in ("ground_third", "ground_two_thirds", "ground_half", "space_half", "ground_rem_pos", "ground_rem_neg", "ground_rem_neg2"):
        d = premise(lib, build(lib, world_factory, name), name)
        parts = [(2 * c * d["start_units"] + d["F"]) // (2 * d["F"]) for c in d["roster"]]
        rems[name] = d["start_units"] - sum(parts)
    assert rems["ground_rem_pos"] == 1 and rems["ground_rem_neg"] == -1 and rems["ground_rem_neg2"] == -2, rems


# ------------------------------------------------------------------------------------------------ (c) cap, (d) enemy

@pytest.mark.parametrize("name", ["ground_third", "ground_two_thirds"])
def test_c_player_production_stops_at_reinforce_cap(lib, world_factory, name):
    """E7 (c): "`om_sup_structure_tick_production_driver` spawns a unit for the player's faction only while
    `reinforce_spawned < reinforce_cap`, incrementing it". Step until the structure timer would have spawned one more than the
    cap allows: the player's rows are unchanged from then on, and the total spawned equals the cap, which is read behaviourally
    (no public getter) and equals F minus the spawned-at-start count (gap-4 rounding). Red today: production never stops."""
    w = build(lib, world_factory, name)
    d = premise(lib, w, name)
    interval = first_interval(lib, w, PLAYER)
    intervals = math.ceil(d["cap"] / d["p"]) + 3  # the cap is reached after ceil(cap / p) rounds, then three more
    series = spawn_series(lib, w, PLAYER, intervals, interval)
    print("CAP", name, "interval", interval, "cap", d["cap"], "player spawned after each interval", series)
    assert owners_of(lib, w).count(PLAYER) == d["p"], f"premise broke: a player structure was lost: {owners_of(lib, w)}; {d}"
    assert max(series) <= d["cap"], f"player production passed reinforce_cap {d['cap']} (F {d['F']} - start_units {d['start_units']}): {series}"
    assert series[-1] == d["cap"], f"player production total {series[-1]} != reinforce_cap {d['cap']}: {series}"
    assert series[-2] == series[-1] == series[-3], f"production did not stop once the cap was reached: {series}"
    assert all(a <= b for a, b in zip(series, series[1:])), series


def test_d_enemy_keeps_producing_while_the_player_is_capped(lib, world_factory):
    """E7 (d): "the enemy's production is unchanged (its force is sized by `enemy_total`, R-074)". Over the same run as (c)
    every enemy structure keeps spawning one unit per interval, past the player's cap. Control: green today and after E7."""
    w = build(lib, world_factory, "ground_third")
    d = premise(lib, w, "ground_third")
    interval = first_interval(lib, w, ENEMY)
    intervals = math.ceil(d["cap"] / d["p"]) + 3
    series = spawn_series(lib, w, ENEMY, intervals, interval)
    print("ENEMY", "interval", interval, "enemy spawned after each interval", series)
    assert owners_of(lib, w).count(ENEMY) == d["e"], f"premise broke: an enemy structure changed hands: {owners_of(lib, w)}; {d}"
    assert series == [d["e"] * k for k in range(1, intervals + 1)], series
    assert series[-1] > d["cap"], "the control must run the enemy past the player's cap"


def test_f_a_bare_world_without_a_mission_is_uncapped(lib, world_factory):
    """E7 (f), gap 6: "`reinforce_cap` is `UINT32_MAX` on a bare world with no mission set up" so production there is uncapped
    (tests/csim/test_core_support_driver.py and test_core_B14N_support_tick_materialise.py stay green unchanged). A bare world,
    a hand-built player structure, eleven intervals: eleven spawns, well past any cap a mission would set. Green today and
    after E7."""
    _bind(lib)
    w = world_factory(n_regions=1, seed=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_structure_init(w, 0, 2, D(100.0))
    lib.om_structure_set_owner(w, 0, PLAYER)
    lib.om_structure_set_position(w, 0, 3000.0, 3000.0)
    lib.om_unit_spawn(w, 0, ENEMY, 100_000.0, 100_000.0, 0)  # om_tactical_step is a no-op with no units: a far filler
    interval = lib.om_structure_production_interval_ticks(D(100.0))
    series = spawn_series(lib, w, PLAYER, 11, interval)
    assert series == list(range(1, 12)), f"an uncapped bare world must keep producing: {series}"


# ------------------------------------------------------------------------------------------------ (e) save, determinism

def bare_target(lib, world_factory):
    """The load target with no om_mission_setup (cap UINT32_MAX by gap 6): everything it ends up with came from the save."""
    _bind(lib)
    w = world_factory(n_regions=2, seed=FIXTURES["ground_third"]["seed"])
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_set_era_kind(w, 1)
    set_faction(lib, w, PLAYER, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY, held_since=-1)
    set_owner(lib, w, 1, PLAYER, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=FIXTURES["ground_third"]["military"], faction_id=ENEMY)
    return w


@pytest.mark.parametrize("target", ["setup_target", "bare_target"])
def test_e_save_round_trip_keeps_reinforce_cap_and_reinforce_spawned(lib, world_factory, target):
    """E7 (e): "a save round trip keeps `reinforce_cap` and `reinforce_spawned`". Save after three production intervals, load
    into a fresh world, step on: the production total over the whole run equals the cap, never the cap plus the units spawned
    before the save. 'setup_target' is a fresh scene (its own cap, spawned = 0 before the load), so only a saved
    `reinforce_spawned` makes the total come out at the cap; 'bare_target' has no mission set up (cap UINT32_MAX), so only a
    saved `reinforce_cap` does. Red today: production is uncapped in both."""
    a = build(lib, world_factory, "ground_third")
    d = premise(lib, a, "ground_third")
    interval = first_interval(lib, a, PLAYER)
    start_rows = len(rows(lib, a, PLAYER))
    lib.om_tactical_tick_to(a, 3 * interval)
    spawned_before_save = len(rows(lib, a, PLAYER)) - start_rows
    assert spawned_before_save == 3 and d["cap"] > 3, f"the save must fall mid-way through the production: {d}"
    buf, size = _save(lib, a)
    b = build(lib, world_factory, "ground_third") if target == "setup_target" else bare_target(lib, world_factory)
    assert _load(lib, b, buf, size) == 0
    assert len(rows(lib, b, PLAYER)) == len(rows(lib, a, PLAYER)), "the loaded world lost units"
    intervals = math.ceil(d["cap"] / d["p"]) + 3
    for w in (a, b):
        lib.om_tactical_tick_to(w, intervals * interval)
    total_a = len(rows(lib, a, PLAYER)) - start_rows
    total_b = len(rows(lib, b, PLAYER)) - start_rows
    print("SAVE", target, "cap", d["cap"], "spawned before save", spawned_before_save, "total a", total_a, "total b", total_b)
    assert total_a == d["cap"], f"the original world produced {total_a}, cap {d['cap']}; PREMISE {d}"
    assert total_b == d["cap"], (
        f"{target}: production total over the whole run {total_b} != cap {d['cap']} (cap + spawned before the save = "
        f"{d['cap'] + spawned_before_save}): reinforce_cap and reinforce_spawned must both be saved; PREMISE {d}")


_CHILD = """
import json, sys
sys.path.insert(0, sys.argv[1])
import conftest, test_VG_E_e7 as m
lib = conftest.load_lib()
make, _ = conftest._world_factory_for(lib, None)
print(json.dumps(m.determinism_probe(lib, make, int(sys.argv[2]))))
"""


def determinism_probe(lib, make, seed):
    """Child-process body: the ground_third fixture at the given seed, three production intervals, then the save bytes and
    the full checksum."""
    _bind(lib)
    kw = dict(FIXTURES["ground_third"], seed=seed)
    w = e1h_scene(lib, make, **kw)
    lib.om_tactical_tick_to(w, 3 * first_interval(lib, w, PLAYER))
    buf, size = _save(lib, w)
    secs = (U64 * N_SECTIONS)()
    lib.om_world_checksum_full.argtypes, lib.om_world_checksum_full.restype = [V, ctypes.POINTER(U64), U32], U64
    whole = lib.om_world_checksum_full(w, secs, N_SECTIONS)
    return dict(sha=hashlib.sha256(bytes(buf)).hexdigest(), size=size, whole=whole, sections=list(secs),
                rows=len(rows(lib, w, PLAYER)))


def _child(seed):
    res = subprocess.run([sys.executable, "-c", _CHILD, str(REPO / "tests" / "csim"), str(seed)], capture_output=True,
                         text=True, timeout=300, cwd=str(REPO))
    assert res.returncode == 0, res.stderr[-2000:]
    return json.loads(res.stdout.strip().splitlines()[-1])


def test_e_two_processes_same_seed_byte_identical_save_and_checksum(lib):
    """E7 (e): "two processes, same seed and command stream, byte-identical save bytes and `om_world_checksum_full`"
    ([B determinism]). Control: a different seed gives a different save. Green today (determinism holds without E7); it
    is the guard that the new counters and the cut add no order or platform input."""
    first, second, other = _child(1), _child(1), _child(2)
    assert first["size"] > 0 and first["whole"] != 0 and any(first["sections"])
    assert first == second, f"two processes disagree: {first} vs {second}"
    assert first["sha"] != other["sha"], "control: the save does not depend on the seed"


# ------------------------------------------------------------------------------------------------ (g) hash coverage

def test_g_mission_hash_covers_reinforce_spawned(lib, world_factory):
    """E7 (g), HASH COVERAGE: "`reinforce_cap` and `reinforce_spawned` are saved AND hashed in `om_mis_net_hash` (after
    `player_units`): `reinforce_spawned` gates future spawns, so an unhashed divergence would be a silent desync". Two worlds
    from the same seed and mission that differ ONLY in reinforce_spawned give different mission-section hashes
    (om_world_checksum_full section 5). The only handle is behavioural: in `a` the player's structure is neutral, so after
    one interval it has spawned nothing; in `b` it has spawned one. Both worlds step the same number of ticks, so no other
    mission field differs. Controls: two identical worlds hash equal and nonzero; the section moves when the mission itself
    changes (an objective completion). Red today: the section does not see the counter."""
    a, b, c = (build(lib, world_factory, "ground_third") for _ in range(3))
    d = premise(lib, b, "ground_third")
    interval = first_interval(lib, b, PLAYER)
    slot = owners_of(lib, a).index(PLAYER)
    lib.om_structure_set_owner(a, slot, -1)
    start_rows = len(rows(lib, b, PLAYER))
    for w in (a, b, c):
        lib.om_tactical_tick_to(w, interval)
    assert len(rows(lib, b, PLAYER)) == start_rows + d["p"] and len(rows(lib, a, PLAYER)) == start_rows, "premise: b spawned, a did not"
    sa, sb, sc = (_secs(lib, w)[MISSION_SECTION] for w in (a, b, c))
    print("HASH section 5: a (no spawn)", sa, "b (one spawn)", sb, "c (identical to b)", sc)
    assert sb == sc != 0, "control: identical worlds must hash equal (and the section must be nonzero)"
    x, y = build(lib, world_factory, "ground_third"), build(lib, world_factory, "ground_third")
    for w in (x, y):
        lib.om_mission_build_objectives(w, 2)
    lib.om_mission_set_objective_completion(y, 0, 0.37)
    assert _secs(lib, x)[MISSION_SECTION] != _secs(lib, y)[MISSION_SECTION], "control: the section does not move on a mission change"
    assert sa != sb, "worlds differing only in reinforce_spawned (0 vs 1) hash equal: reinforce_spawned is not in om_mis_net_hash"
