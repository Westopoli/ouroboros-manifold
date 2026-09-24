"""E-11 (docs/bible/epics/E-11-units-and-combat.md), "## Scale requirements":
"Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is
escalated): targeting and damage for 1,000 units in under 2 ms per tick,
10,000 in under 25 ms."

Per the leaf brief's measurement recipe: om_tactical_step is the tactical
tick driver for E-11/E-13 (targeting, damage, movement, and collision all run
inside one tactical tick; the public ABI has no finer per-concern entry
point), spawned on a 24000 wu canvas in a grid, half faction 0 / half
faction 1 (hostile) so targeting has real work to do.
"""
from ._scale_helpers import assert_budget, assert_control_violates_budget, median_ns, raw_world, spawn_grid

RAIDER = 0
N_SMALL = 1000
N_LARGE = 10000
BUDGET_SMALL_NS = 2_000_000  # 2 ms
BUDGET_LARGE_NS = 25_000_000  # 25 ms
SEED = 2026091411


def _build(lib, n, seed):
    w = raw_world(lib, 1, seed, features=[])
    half = n // 2
    spawn_grid(lib, w, half, 0, RAIDER)
    spawn_grid(lib, w, n - half, 1, RAIDER)
    return w


def test_e11_1000_units_targeting_and_damage_per_tick(lib):
    w = _build(lib, N_SMALL, SEED)
    med = median_ns(lambda: lib.om_tactical_step(w))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_SMALL_NS, f"E-11 {N_SMALL} units, om_tactical_step")


def test_e11_10000_units_targeting_and_damage_per_tick(lib):
    w = _build(lib, N_LARGE, SEED)
    med = median_ns(lambda: lib.om_tactical_step(w))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_LARGE_NS, f"E-11 {N_LARGE} units, om_tactical_step")
    # positive control: same 10,000-unit measurement, tightened budget
    assert_control_violates_budget(med, BUDGET_LARGE_NS, f"E-11 control, {N_LARGE} units (budget/100)")
