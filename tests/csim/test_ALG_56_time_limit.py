"""ALG-56 Time limit (docs/bible/algorithms.md), rules R-076-01, R-076-02 (E-10, S-076).

Isolation: om_archetype_base_time_ticks against the row's minutes table, om_mission_compute_time_limit
against max(B * (1 - TIME_PRESSURE_SCALING * u), B * TIME_LIMIT_FLOOR_PCT), and om_mission_get_time_limit
end to end on a set-up mission. Constants from csrc/om_constants.h by name.
Unstated: the rounding of a fractional limit to whole ticks (the C rounds half up); the cases here use
integer-valued results, and the one fractional case is asserted to within one tick, Westley's.
"""
import pytest

from alg_consts import const
from conftest import OMArchetype, OMEdge, OMStance, OMTier, set_edge, set_faction, set_owner, set_region, set_stance

SCALING = const("TIME_PRESSURE_SCALING")
FLOOR = const("TIME_LIMIT_FLOOR_PCT")
RATE = const("TACTICAL_TICK_RATE")

# The row's table, in minutes, keyed by the C archetype index (names from the row).
MINUTES = {
    "defensive_stand": (0, 37.5), "siege_breaking": (1, 60.0), "reconquest": (2, 45.0), "assault": (3, 52.5),
    "suppression": (4, 30.0), "multi_front_defense": (5, 60.0), "interception": (6, 37.5),
    "evacuation": (7, 30.0), "containment": (8, 52.5), "counterinsurgency": (9, 37.5),
}


def expected_limit(B, u):
    return max(B * (1.0 - SCALING * u), B * FLOOR)


@pytest.mark.parametrize("name", sorted(MINUTES))
def test_ALG_56_base_time_is_minutes_times_60_times_tick_rate(lib, name):
    """ALG-56 / R-076-02: B = minutes * 60 * TACTICAL_TICK_RATE ticks."""
    idx, minutes = MINUTES[name]
    assert lib.om_archetype_base_time_ticks(idx) == int(minutes * 60 * RATE)


@pytest.mark.parametrize("B,u", [
    (45000, 0.0), (45000, 1.0), (45000, 1.5), (45000, 2.0), (45000, 2.5), (72000, 0.5), (36000, 10.0),
])
def test_ALG_56_limit_formula(lib, B, u):
    """ALG-56 / R-076-01: limit = max(B (1 - 0.2 u), 0.6 B); the floor binds from u = 2.0 upward."""
    assert lib.om_mission_compute_time_limit(B, u) == pytest.approx(expected_limit(B, u), abs=0.5)


def test_ALG_56_floor_binds_where_the_row_says(lib):
    """ALG-56: at u = 1 (the normal ceiling) 0.8 B is above the floor; at u = 2.5 it is not, so the floor 0.6 B is returned."""
    B = 40000
    assert lib.om_mission_compute_time_limit(B, 1.0) == int(B * (1 - SCALING))
    assert lib.om_mission_compute_time_limit(B, 2.5) == int(B * FLOOR)


def test_ALG_56_positive_control_unfloored_value_rejected(lib):
    """Positive control: B (1 - 0.2 u) at u = 2.5 is 0.5 B, below the floor; asserting it must be rejected."""
    B = 40000
    got = lib.om_mission_compute_time_limit(B, 2.5)
    with pytest.raises(AssertionError):
        assert got == int(B * (1 - SCALING * 2.5))


def test_ALG_56_mission_limit_uses_the_archetype_base_and_the_candidate_urgency(lib, world_factory):
    """ALG-56 end to end: om_mission_get_time_limit = compute_time_limit(B of the mission archetype, urgency of the mission region)."""
    for idx, minutes in ((0, 37.5), (3, 52.5), (4, 30.0)):
        w = world_factory(n_regions=2)
        set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
        set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=100.0)
        set_stance(lib, w, 0, 1, OMStance.HOSTILE)
        set_region(lib, w, 0, tier=OMTier.HOME, military=30.0, economy=30.0, tension=60.0, population=50.0)
        set_region(lib, w, 1, tier=OMTier.HOME, military=70.0, economy=50.0, tension=10.0, population=50.0)
        set_owner(lib, w, 0, 0, held_since=-1)
        set_owner(lib, w, 1, 1, held_since=-1)
        set_edge(lib, w, 0, 1, OMEdge.BORDER)
        lib.om_mission_setup(w, 0, idx, 0)
        u = lib.om_mission_compute_urgency(w, 0, idx)
        assert 0.0 < u <= 1.0
        B = int(minutes * 60 * RATE)
        assert lib.om_mission_get_time_limit(w) == pytest.approx(expected_limit(B, u), abs=0.5)
