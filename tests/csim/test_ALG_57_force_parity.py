"""ALG-57 Force parity (docs/bible/algorithms.md), rules R-074-01..R-074-05 (E-10, S-074).

Isolation: om_mission_compute_enemy_power, om_mission_compute_base_parity,
om_mission_compute_difficulty_parity, om_mission_fill_player_force and om_mission_apply_capacity_shortfall,
each on a hand-built input with the expected value computed here from the row. Constants from
csrc/om_constants.h by name (breakpoints PARITY_BREAKPOINTS_n_X/_Y, scales, thresholds).
Unstated: the rounding of the shortfall removal count (the row says "0.20 of the units"; the C removes
total - floor(total * 0.8)), Westley's.
Unstated: the order of unit types with equal profile ratio (the C's selection sort is not index-stable, so the
cases use distinct ratios), Westley's.
Unstated: the unit power values and archetype profile ratios the fill uses are not in the row; the test reads
unit power from om_unit_power and sets an explicit profile, Westley's.
"""
import math

import pytest

from alg_consts import const
from conftest import OMArchetype, force_draws, set_faction

B2P = const("BUDGET_TO_POWER_SCALE")
M2P = const("MILITARY_TO_POWER_SCALE")
LOW_POP = const("MISSION_INSURGENT_POP_LOW_THRESHOLD")
HIGH_POP = const("MISSION_INSURGENT_POP_HIGH_THRESHOLD")
LO_LO, LO_HI = const("INSURGENT_MIL_LOW_POP_RANGE_LO"), const("INSURGENT_MIL_LOW_POP_RANGE_HI")
HI_LO, HI_HI = const("INSURGENT_MIL_HIGH_POP_RANGE_LO"), const("INSURGENT_MIL_HIGH_POP_RANGE_HI")
BP = [(const("PARITY_BREAKPOINTS_%d_X" % i), const("PARITY_BREAKPOINTS_%d_Y" % i)) for i in range(const("PARITY_BREAKPOINTS_N"))]
EASY_FLOOR = const("MISSION_PARITY_EASY_FLOOR")
HARD_CEIL = const("MISSION_PARITY_HARD_CEILING")
FLOOR = const("PARITY_FLOOR")
OVERSHOOT = const("MISSION_FILL_OVERSHOOT_MULT")
SHORT_T = const("CAPACITY_SHORTFALL_THRESHOLD")
SHORT_R = const("CAPACITY_SHORTFALL_REDUCTION")
EASY, MEDIUM, HARD = 0, 1, 2
# attack-driven, insurgent, other (names as in the row; C indices)
ATTACK_DRIVEN = (0, 5, 6)   # defensive stand, multi-front defense, interception
INSURGENT = (4, 9)          # suppression, counterinsurgency
OTHER = (1, 2, 3, 7, 8)     # siege breaking, reconquest, assault, evacuation, containment
N_TYPES = 6


def base_parity(c):
    if c <= BP[0][0]:
        return BP[0][1]
    if c >= BP[-1][0]:
        return BP[-1][1]
    for (x0, y0), (x1, y1) in zip(BP, BP[1:]):
        if x0 <= c <= x1:
            return y0 + (c - x0) / (x1 - x0) * (y1 - y0)


def difficulty_parity(base, d):
    p = max(base, EASY_FLOOR) if d == EASY else min(base, HARD_CEIL) if d == HARD else base
    return max(p, FLOOR)


def insurgent_range(pop):
    t = min(1.0, max(0.0, (pop - LOW_POP) / (HIGH_POP - LOW_POP)))
    return LO_LO + t * (HI_LO - LO_LO), LO_HI + t * (HI_HI - LO_HI)


@pytest.mark.parametrize("arch", ATTACK_DRIVEN)
def test_ALG_57_enemy_power_attack_driven_is_committed_budget_times_300(lib, world_factory, arch):
    """ALG-57 / R-074-01: attack-driven archetypes: budget_committed * BUDGET_TO_POWER_SCALE."""
    w = world_factory(n_regions=2)
    assert lib.om_mission_compute_enemy_power(w, arch, 40.0, 99.0, 99.0) == pytest.approx(40.0 * B2P, abs=1e-9)


@pytest.mark.parametrize("arch", INSURGENT)
@pytest.mark.parametrize("pop", [0.0, 25.0, 40.0, 47.5, 70.0, 100.0])
@pytest.mark.parametrize("draw", [0.0, 0.5, 0.999999])
def test_ALG_57_enemy_power_insurgent_is_rolled_military_times_2000(lib, world_factory, arch, pop, draw):
    """ALG-57 / R-074-01: insurgent_m = U(lo, hi), lo/hi interpolated from (20,50) at pop <= 25 to (40,70) at pop >= 70;
    power = insurgent_m * MILITARY_TO_POWER_SCALE."""
    w = world_factory(n_regions=2)
    force_draws(lib, w, [draw])
    lo, hi = insurgent_range(pop)
    got = lib.om_mission_compute_enemy_power(w, arch, 0.0, 10.0, pop)
    assert got == pytest.approx((lo + draw * (hi - lo)) * M2P, abs=1e-6)


@pytest.mark.parametrize("arch", OTHER)
def test_ALG_57_enemy_power_other_is_region_military_times_2000(lib, world_factory, arch):
    """ALG-57 / R-074-01: other archetypes: region military * MILITARY_TO_POWER_SCALE."""
    w = world_factory(n_regions=2)
    assert lib.om_mission_compute_enemy_power(w, arch, 99.0, 35.0, 50.0) == pytest.approx(35.0 * M2P, abs=1e-9)


def test_ALG_57_enemy_power_positive_control_wrong_scale_rejected(lib, world_factory):
    """Positive control: using the 2000 scale for an attack-driven archetype must be rejected."""
    w = world_factory(n_regions=2)
    got = lib.om_mission_compute_enemy_power(w, 0, 40.0, 50.0, 50.0)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(40.0 * M2P, abs=1e-9)


@pytest.mark.parametrize("c", [-0.1, 0.0, 0.1, 0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0, 1.4])
def test_ALG_57_base_parity_is_piecewise_linear_through_the_breakpoints(lib, c):
    """ALG-57 / R-074-02: base parity piecewise linear through PARITY_BREAKPOINTS on capacity/100, held flat beyond the ends."""
    assert lib.om_mission_compute_base_parity(c) == pytest.approx(base_parity(c), abs=1e-12)


@pytest.mark.parametrize("base", [0.60, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0])
@pytest.mark.parametrize("difficulty", [EASY, MEDIUM, HARD])
def test_ALG_57_difficulty_parity_easy_hard_and_floor(lib, base, difficulty):
    """ALG-57 / R-074-03: easy max(base, 0.95), hard min(base, 0.85), medium base; then max(parity, PARITY_FLOOR)."""
    assert lib.om_mission_compute_difficulty_parity(base, difficulty) == pytest.approx(difficulty_parity(base, difficulty), abs=1e-12)


def test_ALG_57_parity_positive_control_hard_ceiling_rejected(lib):
    """Positive control: hard at base 0.90 is capped at 0.85; asserting 0.90 must be rejected."""
    got = lib.om_mission_compute_difficulty_parity(0.90, HARD)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(0.90, abs=1e-12)


def _expected_fill(lib, ratios, budget):
    """Row Fill: for each unit type in descending profile ratio (ties keep index order), add units while
    allocated < budget * ratio and power <= OVERSHOOT * remaining."""
    order = sorted(range(N_TYPES), key=lambda t: (-ratios[t], t))
    counts = [0] * N_TYPES
    remaining = budget
    total = 0.0
    for t in order:
        pr = lib.om_unit_power(t)
        target = budget * ratios[t]
        allocated = 0.0
        while allocated < target and remaining > 0.0:
            if pr > remaining * OVERSHOOT:
                break
            counts[t] += 1
            allocated += pr
            remaining -= pr
            total += pr
    return counts, total


def _fill_world(lib, world_factory, ratios):
    import ctypes
    w = world_factory(n_regions=1)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    arr = (ctypes.c_double * N_TYPES)(*ratios)
    lib.om_mission_set_archetype_profile(w, 3, arr, N_TYPES)
    lib.om_mission_setup(w, 0, 3, 0)  # assault; sets the mission archetype whose profile the fill reads
    return w


@pytest.mark.parametrize("ratios,P,parity", [
    ([0.40, 0.25, 0.15, 0.10, 0.06, 0.04], 10000.0, 0.90),
    ([0.05, 0.10, 0.12, 0.08, 0.15, 0.50], 6000.0, 0.75),
    ([0.0, 0.0, 1.0, 0.0, 0.0, 0.0], 2500.0, 1.0),
    ([0.30, 0.22, 0.18, 0.14, 0.10, 0.06], 30000.0, 0.85),
])
def test_ALG_57_fill_player_force_per_type_in_descending_ratio(lib, world_factory, ratios, P, parity):
    """ALG-57 / R-074-04: budget = P * parity, filled per unit type in descending profile ratio while allocated < budget * ratio
    and unit power <= 1.15 * remaining; the returned total and the unit counts match the row's loop run in the test."""
    import ctypes
    w = _fill_world(lib, world_factory, ratios)
    got_total = lib.om_mission_fill_player_force(w, P, parity)
    counts = (ctypes.c_uint32 * N_TYPES)()
    lib.om_mission_get_player_units(w, 0, counts, N_TYPES)
    exp_counts, exp_total = _expected_fill(lib, ratios, P * parity)
    assert list(counts) == exp_counts
    assert got_total == pytest.approx(exp_total, abs=1e-9)


def test_ALG_57_fill_positive_control_ignoring_the_overshoot_limit_rejected(lib, world_factory):
    """Positive control: a budget that cannot afford one unit of the only profiled type stays empty; asserting one unit was added must fail."""
    import ctypes
    ratios = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    w = _fill_world(lib, world_factory, ratios)
    budget = lib.om_unit_power(2) / OVERSHOOT / 2.0   # pr > OVERSHOOT * remaining
    lib.om_mission_fill_player_force(w, budget, 1.0)
    counts = (ctypes.c_uint32 * N_TYPES)()
    lib.om_mission_get_player_units(w, 0, counts, N_TYPES)
    assert counts[2] == 0
    with pytest.raises(AssertionError):
        assert counts[2] == 1


@pytest.mark.parametrize("capacity,expect_shortfall", [(SHORT_T - 0.01, True), (SHORT_T, False), (0.9, False)])
def test_ALG_57_shortfall_threshold(lib, world_factory, capacity, expect_shortfall):
    """ALG-57 / R-074-05: shortfall applies when capacity < CAPACITY_SHORTFALL_THRESHOLD (0.4), not at it."""
    import ctypes
    w = world_factory(n_regions=1)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    counts = (ctypes.c_uint32 * N_TYPES)(10, 0, 0, 0, 0, 0)
    lib.om_mission_set_player_units(w, 0, counts, N_TYPES)
    lib.om_mission_apply_capacity_shortfall(w, capacity)
    out = (ctypes.c_uint32 * N_TYPES)()
    lib.om_mission_get_player_units(w, 0, out, N_TYPES)
    assert (sum(out) < 10) == expect_shortfall


@pytest.mark.parametrize("start", [
    [5, 3, 2, 0, 0, 0], [10, 0, 0, 0, 0, 0], [4, 4, 4, 4, 4, 4], [1, 0, 0, 0, 0, 0], [2, 2, 0, 0, 0, 0], [7, 1, 0, 3, 0, 0],
])
def test_ALG_57_shortfall_removes_twenty_percent_round_robin_from_the_most_numerous(lib, world_factory, start):
    """ALG-57 / R-074-05: remove CAPACITY_SHORTFALL_REDUCTION of the units, round-robin over types ordered by starting count
    (fixed snapshot), keeping at least 1. Removal count = total - max(1, floor(total * 0.8)) (rounding unstated)."""
    import ctypes
    w = world_factory(n_regions=1)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    lib.om_mission_set_player_units(w, 0, (ctypes.c_uint32 * N_TYPES)(*start), N_TYPES)
    lib.om_mission_apply_capacity_shortfall(w, SHORT_T - 0.05)
    out = (ctypes.c_uint32 * N_TYPES)()
    lib.om_mission_get_player_units(w, 0, out, N_TYPES)
    total = sum(start)
    keep = max(1, math.floor(total * (1.0 - SHORT_R)))
    to_remove = max(0, total - keep)
    counts = list(start)
    order = sorted(range(N_TYPES), key=lambda t: (-start[t], t))
    removed = idx = 0
    while removed < to_remove and any(counts):
        t = order[idx % N_TYPES]
        if counts[t] > 0:
            counts[t] -= 1
            removed += 1
        idx += 1
    assert list(out) == counts
    assert sum(out) >= 1


@pytest.mark.parametrize("m,e,t,p", [(100, 100, 0, 100), (50, 50, 30, 50), (10, 20, 70, 30)])
def test_ALG_57_mission_parity_is_base_parity_of_region_capacity_over_100(lib, world_factory, m, e, t, p):
    """ALG-57 / R-074-02: base parity is taken on region capacity / 100 (ALG-10 composite); the world carries no
    difficulty setting, so the mission's parity is the medium-difficulty value (base, floored at PARITY_FLOOR)."""
    from conftest import OMComposite, OMTier, set_owner, set_region
    w = world_factory(n_regions=1)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=m, economy=e, tension=t, population=p)
    set_owner(lib, w, 0, 0, held_since=-1)
    cap = lib.om_region_composite(w, 0, OMComposite.CAPACITY)
    lib.om_mission_setup(w, 0, 3, 0)
    assert lib.om_mission_get_player_parity(w, 0) == pytest.approx(difficulty_parity(base_parity(cap / 100.0), MEDIUM), abs=1e-12)
