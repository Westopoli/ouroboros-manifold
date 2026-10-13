"""ALG-56 Time limit (docs/bible/algorithms.md), proving R-076-01 and R-076-02 (S-076, E-10).

limit = max(B * (1 - urgency * 0.2), B * 0.6), B = base minutes * 60 * TACTICAL_TICK_RATE (20),
the base minutes per archetype from the ALG-56 table (Q-076-01, Q-076-02). The reference below is
written from the algorithms.md text; no number is read back from the C output.
"""
import ctypes
import math

# ALG-56 table, minutes of battle time. Archetype ids are the ouroboros_sim.h order
# (DEFENSIVE_STAND 0 .. COUNTERINSURGENCY 9, the same ids test_E10_S076 uses).
MINUTES = {
    "defensive_stand": (0, 37.5),
    "siege_breaking": (1, 60.0),
    "reconquest": (2, 45.0),
    "assault": (3, 52.5),
    "suppression": (4, 30.0),
    "multi_front_defense": (5, 60.0),
    "interception": (6, 37.5),
    "evacuation": (7, 30.0),
    "containment": (8, 52.5),
    "counterinsurgency": (9, 37.5),
}
TACTICAL_TICK_RATE = 20
TIME_PRESSURE_SCALING = 0.2
TIME_LIMIT_FLOOR_PCT = 0.6
URGENCIES = [i * 0.05 for i in range(0, 61)]  # 0.0 .. 3.0, covers the floor crossing at u = 2.0


def _ref_limit(base_ticks, urgency, scaling=TIME_PRESSURE_SCALING, floor=TIME_LIMIT_FLOOR_PCT):
    return max(base_ticks * (1.0 - urgency * scaling), base_ticks * floor)


def _worst_error(lib, **ref_kwargs):
    """Largest |C - reference| over every archetype and urgency; the C value is an integer tick count."""
    worst = 0.0
    for _name, (aid, minutes) in MINUTES.items():
        base = int(minutes * 60 * TACTICAL_TICK_RATE)
        for u in URGENCIES:
            got = lib.om_mission_compute_time_limit(base, ctypes.c_double(u))
            worst = max(worst, abs(got - _ref_limit(base, u, **ref_kwargs)))
    return worst


def test_control_ALG_56_a_wrong_scaling_or_floor_is_detected(lib):
    """Positive control: a reference with scaling 0.25 or floor 0.5 disagrees with the C limit somewhere on the grid, so the sweep below can fail."""
    assert _worst_error(lib, scaling=0.25) > 1.0
    assert _worst_error(lib, floor=0.5) > 1.0


def test_ALG_56_base_time_is_minutes_times_60_times_tick_rate(lib):
    """ALG-56 / R-076-02: each archetype's base time B in ticks is the table minutes * 60 * 20."""
    for name, (aid, minutes) in MINUTES.items():
        assert lib.om_archetype_base_time_ticks(aid) == minutes * 60 * TACTICAL_TICK_RATE, name


def test_ALG_56_limit_is_max_of_pressured_and_floor(lib):
    """ALG-56 / R-076-01: limit = max(B(1 - 0.2u), 0.6B) for every archetype across u in [0, 3]; the C value is a whole tick, so it may differ from the real-valued equation by at most half a tick."""
    assert _worst_error(lib) <= 0.5
    # The floor is reached exactly where 1 - 0.2u = 0.6, u = 2: above it the limit stays at 0.6 B.
    base = int(MINUTES["siege_breaking"][1] * 60 * TACTICAL_TICK_RATE)
    assert lib.om_mission_compute_time_limit(base, ctypes.c_double(3.0)) == math.floor(0.6 * base + 0.5)
    assert lib.om_mission_compute_time_limit(base, ctypes.c_double(0.0)) == base
