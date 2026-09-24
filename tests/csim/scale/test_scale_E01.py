"""E-01 (docs/bible/epics/E-01-layer-system.md), "## Scale requirements":
"Numbers to be confirmed by Westley in Stage 3. Proposed: 1,000 units
computing cross-layer visibility against 1,000 units in under 2 ms per tick;
10,000 units in under 20 ms per tick; accessibility queries at 10,000 per
tick in under 1 ms."

These budgets are PROPOSED, not confirmed (Stage 3 has not run) -- every test
here is `xfail(strict=False)`: a fail is expected/allowed, a pass is also
allowed and reported, neither blocks the suite. Confirmed once Westley signs
off a number here, at which point this file drops the xfail markers.

Cross-layer visibility, like E-12's same-layer case, has no single aggregate
call: om_visibility_compute is a no-op marker (csrc/fog.c); the real per-tick
cost is N om_unit_can_see queries, one per unit against a same-index
counterpart on the OTHER layer, exercising om_unit_get_cross_layer_factor's
path inside om_unit_can_see.
"""
import pytest

from ._scale_helpers import assert_budget, assert_control_violates_budget, median_ns, raw_world, spawn_grid

RAIDER = 0
N_SMALL = 1000
N_LARGE = 10000
BUDGET_SMALL_NS = 2_000_000  # 2 ms
BUDGET_LARGE_NS = 20_000_000  # 20 ms
N_ACCESS_QUERIES = 10000
ACCESS_BUDGET_NS = 1_000_000  # 1 ms total for 10,000 queries
SEED = 2026091401


def _build_cross_layer(lib, n, seed):
    w = raw_world(lib, 1, seed, features=[])
    half = n // 2
    a = spawn_grid(lib, w, half, 0, RAIDER, layer=0)
    b = spawn_grid(lib, w, n - half, 1, RAIDER, layer=1)
    pairs = list(zip(a, b))
    return w, pairs


@pytest.mark.xfail(strict=False, reason="E-01 budget proposed, not confirmed (Stage 3)")
def test_e01_1000_units_cross_layer_visibility_per_tick(lib):
    w, pairs = _build_cross_layer(lib, N_SMALL, SEED)
    med = median_ns(lambda: [lib.om_unit_can_see(w, o, t) for o, t in pairs])
    lib.om_world_free(w)
    assert_budget(med, BUDGET_SMALL_NS, f"E-01 {N_SMALL} units, {N_SMALL // 2} cross-layer om_unit_can_see/tick")


@pytest.mark.xfail(strict=False, reason="E-01 budget proposed, not confirmed (Stage 3)")
def test_e01_10000_units_cross_layer_visibility_per_tick(lib):
    w, pairs = _build_cross_layer(lib, N_LARGE, SEED)
    med = median_ns(lambda: [lib.om_unit_can_see(w, o, t) for o, t in pairs])
    lib.om_world_free(w)
    assert_budget(med, BUDGET_LARGE_NS, f"E-01 {N_LARGE} units, {N_LARGE // 2} cross-layer om_unit_can_see/tick")
    assert_control_violates_budget(med, BUDGET_LARGE_NS, f"E-01 control, {N_LARGE} units (budget/100)")


@pytest.mark.xfail(strict=False, reason="E-01 budget proposed, not confirmed (Stage 3)")
def test_e01_10000_accessibility_queries_per_tick(lib):
    w = raw_world(lib, 1, SEED, features=[])
    xs = [(i * 37.0) % 24000.0 for i in range(N_ACCESS_QUERIES)]
    ys = [(i * 53.0) % 24000.0 for i in range(N_ACCESS_QUERIES)]
    layers = [i % 2 for i in range(N_ACCESS_QUERIES)]

    def _batch():
        for x, y, layer in zip(xs, ys, layers):
            lib.om_map_sample_layer_accessibility(w, x, y, layer)

    med = median_ns(_batch, n=100, warmup=5)
    lib.om_world_free(w)
    assert_budget(med, ACCESS_BUDGET_NS, f"E-01 {N_ACCESS_QUERIES} om_map_sample_layer_accessibility queries/tick")
