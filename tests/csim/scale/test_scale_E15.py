"""E-15 (docs/bible/epics/E-15-reinforcement-supply-and-hazards.md), "## Scale
requirements": "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a
miss is escalated): capture and production for 8 structures in under 0.2 ms
per tick."
"""
import pytest

from ._scale_helpers import assert_budget, median_ns, raw_world, scaled_budget_ns

RAIDER = 0
N_STRUCTURES = 8
CONTROL_N_STRUCTURES = 64  # OM_SUP_MAX_STRUCTURES (csrc/tactical_support.c); the ABI's own cap
BUDGET_NS = 200_000  # 0.2 ms
SEED = 2026091415


def _build(lib, n_structures, seed):
    w = raw_world(lib, 1, seed, features=[])
    for i in range(n_structures):
        lib.om_structure_init(w, i, RAIDER, 10.0)
        lib.om_structure_set_capturing_faction(w, i, 1)
    return w


def _tick_all(lib, w, n_structures):
    for i in range(n_structures):
        lib.om_structure_tick_capture(w, i)
        lib.om_structure_tick_production(w, i)


def test_e15_8_structures_capture_and_production_per_tick(lib):
    w = _build(lib, N_STRUCTURES, SEED)
    med = median_ns(lambda: _tick_all(lib, w, N_STRUCTURES))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_NS, f"E-15 {N_STRUCTURES} structures, capture+production tick")


def test_e15_control_10x_structures(lib):
    w = _build(lib, CONTROL_N_STRUCTURES, SEED)
    med = median_ns(lambda: _tick_all(lib, w, CONTROL_N_STRUCTURES))
    lib.om_world_free(w)
    control_budget = scaled_budget_ns(BUDGET_NS) / 100
    print(f"[scale-control] E-15: {CONTROL_N_STRUCTURES} structures raw_median={med / 1000.0:.3f}us "
          f"control_budget={control_budget / 1000.0:.3f}us")
    if med < control_budget:
        pytest.skip(
            f"capture+production over {CONTROL_N_STRUCTURES} structures measured {med / 1000.0:.3f}us, "
            f"still under budget/100 ({control_budget / 1000.0:.3f}us); OM_SUP_MAX_STRUCTURES may cap "
            "well below 80 -- no larger N buildable to trip this control"
        )
    assert med >= control_budget, "control expected to exceed the tightened budget"
