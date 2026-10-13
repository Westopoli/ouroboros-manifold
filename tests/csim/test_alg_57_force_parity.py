"""ALG-57 Force parity (docs/bible/algorithms.md), proving R-074-01 .. R-074-05 (S-074, E-10).

Enemy power, base parity (piecewise linear), difficulty parity with the 0.75 floor, the descending-
ratio fill with the 1.15 overshoot rule, and the 20 percent capacity shortfall. Every expectation
is computed here from the algorithms.md text; unit power is an input (om_unit_power), not an output
under test.
"""
import ctypes

from conftest import force_draws

# ---- ALG-57 constants as written in algorithms.md ----
BUDGET_TO_POWER_SCALE = 300
MILITARY_TO_POWER_SCALE = 2000
POP_LOW, POP_HIGH = 25.0, 70.0  # Q-057-02: 25, not the header duplicate 20
LOW_POP_RANGE = (20.0, 50.0)
HIGH_POP_RANGE = (40.0, 70.0)
PARITY_BREAKPOINTS = [(0.0, 0.80), (0.3, 0.85), (0.5, 0.90), (0.7, 0.95), (1.0, 1.00)]
PARITY_FLOOR = 0.75
EASY_FLOOR, HARD_CEILING = 0.95, 0.85
OVERSHOOT = 1.15
SHORTFALL_THRESHOLD = 0.4
SHORTFALL_REDUCTION = 0.20

ATTACK_DRIVEN = (0, 5, 6)  # defensive_stand, multi_front_defense, interception
INSURGENT = (4, 9)  # suppression, counterinsurgency
OTHERS = (1, 2, 3, 7, 8)
EASY, MEDIUM, HARD = 0, 1, 2


def _ref_enemy_power(archetype, budget, military, population, r):
    if archetype in ATTACK_DRIVEN:
        return budget * BUDGET_TO_POWER_SCALE
    if archetype in INSURGENT:
        t = min(1.0, max(0.0, (population - POP_LOW) / (POP_HIGH - POP_LOW)))
        lo = LOW_POP_RANGE[0] + t * (HIGH_POP_RANGE[0] - LOW_POP_RANGE[0])
        hi = LOW_POP_RANGE[1] + t * (HIGH_POP_RANGE[1] - LOW_POP_RANGE[1])
        return (lo + r * (hi - lo)) * MILITARY_TO_POWER_SCALE
    return military * MILITARY_TO_POWER_SCALE


def _ref_base_parity(c, points=PARITY_BREAKPOINTS):
    if c <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if c <= x1:
            return y0 + (c - x0) / (x1 - x0) * (y1 - y0)
    return points[-1][1]


def _ref_difficulty_parity(base, difficulty, easy_floor=EASY_FLOOR):
    p = base
    if difficulty == EASY:
        p = max(base, easy_floor)
    elif difficulty == HARD:
        p = min(base, HARD_CEILING)
    return max(p, PARITY_FLOOR)


def _ref_fill(lib, ratios, budget):
    """The ALG-57 Fill: types by descending ratio, add units while allocated < budget*ratio and power <= 1.15 * remaining."""
    order = sorted(range(6), key=lambda t: -ratios[t])
    counts = [0] * 6
    remaining = budget
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
    return counts


def _ref_shortfall(counts, capacity):
    if capacity >= SHORTFALL_THRESHOLD:
        return list(counts)
    total = sum(counts)
    target = max(1, int(total * (1.0 - SHORTFALL_REDUCTION)))
    if total == 0 or target >= total:
        return list(counts)
    left = list(counts)
    order = sorted(range(6), key=lambda t: -counts[t])  # snapshot, distinct counts in these tests
    removed, i = 0, 0
    while removed < total - target:
        t = order[i % 6]
        if left[t] > 0:
            left[t] -= 1
            removed += 1
        i += 1
    return left


def _setup(lib, w, archetype, profile):
    arr = (ctypes.c_double * 6)(*profile)
    lib.om_mission_set_archetype_profile(w, archetype, arr, 6)
    lib.om_mission_setup(w, 0, archetype, 0)


def _player_units(lib, w):
    out = (ctypes.c_uint32 * 6)()
    lib.om_mission_get_player_units(w, 0, out, 6)
    return list(out)


# ---- positive controls: each detector fires on a deliberately wrong reference ----

def test_control_ALG_57_wrong_expectations_are_detected(lib, world_factory):
    """Positive control: a wrong breakpoint, floor, scale or shortfall rule disagrees with the C sim, so the real tests below can fail."""
    w = world_factory(n_regions=1)
    wrong = [(0.0, 0.80), (0.3, 0.85), (0.5, 0.92), (0.7, 0.95), (1.0, 1.00)]
    assert abs(lib.om_mission_compute_base_parity(0.4) - _ref_base_parity(0.4, wrong)) > 1e-3
    assert abs(lib.om_mission_compute_difficulty_parity(0.85, EASY) - _ref_difficulty_parity(0.85, EASY, easy_floor=0.90)) > 1e-3
    assert lib.om_mission_compute_enemy_power(w, 0, 10.0, 0.0, 0.0) != 10.0 * 3000
    counts = (ctypes.c_uint32 * 6)(7, 4, 2, 0, 1, 0)
    lib.om_mission_set_player_units(w, 0, counts, 6)
    lib.om_mission_apply_capacity_shortfall(w, 0.39)
    assert _player_units(lib, w) != [7, 4, 2, 0, 1, 0]  # shortfall fires, so "unchanged" would be a defect


# ---- enemy power ----

def test_ALG_57_enemy_power_attack_insurgent_other(lib, world_factory):
    """ALG-57 / R-074-01: attack-driven archetypes give budget*300; insurgent ones give U(lo,hi)*2000 with lo,hi interpolated 25..70 population; the rest give military*2000."""
    w = world_factory(n_regions=1)
    for a in ATTACK_DRIVEN:
        for budget in (0.0, 12.5, 40.0, 99.0):
            got = lib.om_mission_compute_enemy_power(w, a, budget, 77.0, 55.0)
            assert abs(got - _ref_enemy_power(a, budget, 77.0, 55.0, 0.0)) <= 1e-6
    for a in OTHERS:
        for mil in (0.0, 17.0, 35.5, 100.0):
            got = lib.om_mission_compute_enemy_power(w, a, 33.0, mil, 55.0)
            assert abs(got - _ref_enemy_power(a, 33.0, mil, 55.0, 0.0)) <= 1e-6
    for a in INSURGENT:
        for pop in (0.0, 25.0, 30.0, 47.5, 69.0, 70.0, 100.0):
            for r in (0.0, 0.25, 0.5, 0.9, 1.0):
                force_draws(lib, w, [r])
                got = lib.om_mission_compute_enemy_power(w, a, 33.0, 50.0, pop)
                want = _ref_enemy_power(a, 33.0, 50.0, pop, r)
                assert abs(got - want) <= 1e-6, (a, pop, r, got, want)


# ---- parity ----

def test_ALG_57_base_parity_is_piecewise_linear_through_the_breakpoints(lib):
    """ALG-57 / R-074-02: base parity through (0,0.80) (0.3,0.85) (0.5,0.90) (0.7,0.95) (1,1.00) on capacity/100 in [0,1], flat outside."""
    for i in range(-5, 106):
        c = i / 100.0
        got = lib.om_mission_compute_base_parity(ctypes.c_double(c))
        assert abs(got - _ref_base_parity(c)) <= 1e-9, (c, got)


def test_ALG_57_difficulty_parity_easy_hard_medium_and_floor(lib):
    """ALG-57 / R-074-03: easy max(base,0.95), hard min(base,0.85), medium base, then never below 0.75."""
    for i in range(40, 111):
        base = i / 100.0
        for d in (EASY, MEDIUM, HARD):
            got = lib.om_mission_compute_difficulty_parity(ctypes.c_double(base), d)
            assert abs(got - _ref_difficulty_parity(base, d)) <= 1e-12, (base, d, got)
    # The floor is reachable only from a base below 0.75: it wins over medium and hard (easy lifts to 0.95 first).
    assert lib.om_mission_compute_difficulty_parity(ctypes.c_double(0.5), EASY) == 0.95
    assert lib.om_mission_compute_difficulty_parity(ctypes.c_double(0.5), MEDIUM) == 0.75
    assert lib.om_mission_compute_difficulty_parity(ctypes.c_double(0.5), HARD) == 0.75


# ---- fill ----

def test_ALG_57_fill_follows_descending_ratio_with_the_115_overshoot_rule(lib, world_factory):
    """ALG-57 / R-074-04: budget = P*parity, spent per unit type in descending profile ratio while allocated < budget*ratio and unit power <= 1.15*remaining; the returned total is the summed power."""
    profiles = [
        (0.30, 0.25, 0.20, 0.12, 0.08, 0.05),
        (0.05, 0.08, 0.12, 0.20, 0.25, 0.30),
        (0.40, 0.00, 0.35, 0.00, 0.25, 0.00),
        (0.10, 0.50, 0.15, 0.05, 0.12, 0.08),
    ]
    for pi, profile in enumerate(profiles):
        for P, parity in ((10000.0, 0.90), (3333.0, 0.80), (50.0, 1.00), (120000.0, 0.75)):
            w = world_factory(n_regions=1)
            _setup(lib, w, 0, profile)
            total = lib.om_mission_fill_player_force(w, ctypes.c_double(P), ctypes.c_double(parity))
            want = _ref_fill(lib, profile, P * parity)
            got = _player_units(lib, w)
            assert got == want, (pi, P, parity, got, want)
            assert abs(total - sum(c * lib.om_unit_power(t) for t, c in enumerate(want))) <= 1e-6


# ---- shortfall ----

def test_ALG_57_shortfall_removes_20_percent_round_robin_from_the_most_numerous(lib, world_factory):
    """ALG-57 / R-074-05: capacity < 0.4 removes int(n*0.8)-complement units round-robin from the most numerous types, never below 1 unit; capacity >= 0.4 changes nothing."""
    start_sets = [
        (7, 4, 2, 0, 1, 0),
        (5, 3, 2, 0, 0, 0),
        (1, 0, 0, 0, 0, 0),
        (2, 0, 0, 0, 0, 0),
        (9, 6, 4, 3, 2, 1),
        (0, 0, 0, 0, 0, 0),
    ]
    for start in start_sets:
        for capacity in (0.0, 0.2, 0.3999, 0.4, 0.55):
            w = world_factory(n_regions=1)
            lib.om_mission_set_player_units(w, 0, (ctypes.c_uint32 * 6)(*start), 6)
            lib.om_mission_apply_capacity_shortfall(w, ctypes.c_double(capacity))
            got = _player_units(lib, w)
            want = _ref_shortfall(start, capacity)
            assert got == want, (start, capacity, got, want)
            if sum(start) > 0:
                assert sum(got) >= 1
