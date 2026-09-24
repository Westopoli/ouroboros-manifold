"""E-12 (docs/bible/epics/E-12-fog-and-sensors.md), "## Scale requirements":
"Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is
escalated): visibility for 1,000 units in under 2 ms per tick (shared with
E-01); 10,000 in under 20 ms; must use spatial hashing, not all-pairs."

om_visibility_compute(w) (csrc/fog.c) is a deliberate no-op marker -- fog is
computed on demand, per query, by om_unit_can_see/om_player_can_see* (its own
docstring: "visibility is a pure function of current positions, computed
fresh ... on every call"). The measurable per-tick cost is therefore N
single-target om_unit_can_see queries -- one per unit, against its opposing-
faction counterpart -- not the no-op aggregate call.
"""
from ._scale_helpers import assert_budget, assert_control_violates_budget, median_ns, raw_world, spawn_grid

RAIDER = 0
N_SMALL = 1000
N_LARGE = 10000
BUDGET_SMALL_NS = 2_000_000  # 2 ms
BUDGET_LARGE_NS = 20_000_000  # 20 ms
SEED = 2026091412


def _build(lib, n, seed):
    w = raw_world(lib, 1, seed, features=[])
    half = n // 2
    a = spawn_grid(lib, w, half, 0, RAIDER)
    b = spawn_grid(lib, w, n - half, 1, RAIDER)
    pairs = list(zip(a, b))
    return w, pairs


def test_e12_1000_units_visibility_per_tick(lib):
    w, pairs = _build(lib, N_SMALL, SEED)
    med = median_ns(lambda: [lib.om_unit_can_see(w, o, t) for o, t in pairs])
    lib.om_world_free(w)
    assert_budget(med, BUDGET_SMALL_NS, f"E-12 {N_SMALL} units, {N_SMALL // 2} om_unit_can_see queries/tick")


def test_e12_10000_units_visibility_per_tick(lib):
    w, pairs = _build(lib, N_LARGE, SEED)
    med = median_ns(lambda: [lib.om_unit_can_see(w, o, t) for o, t in pairs])
    lib.om_world_free(w)
    assert_budget(med, BUDGET_LARGE_NS, f"E-12 {N_LARGE} units, {N_LARGE // 2} om_unit_can_see queries/tick")
    assert_control_violates_budget(med, BUDGET_LARGE_NS, f"E-12 control, {N_LARGE} units (budget/100)")
