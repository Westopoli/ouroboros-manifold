"""E-14 (docs/bible/epics/E-14-enemy-macro-behavior.md), "## Scale
requirements": "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a
miss is escalated): macro evaluation for 10 forces over 1,000 units in under
1 ms per evaluation tick."

om_macro_tick(w, tick) only does its per-force work on ticks that are a
multiple of om_macro_evaluation_interval_ticks() (csrc/enemy_macro.c); the
timed tick is always called at such a tick.
"""
import pytest

from ._scale_helpers import assert_budget, median_ns, raw_world, spawn_grid

RAIDER = 0
N_FORCES = 10
N_UNITS = 1000
BUDGET_NS = 1_000_000  # 1 ms
SEED = 2026091414


def _build(lib, n_forces, n_units, seed):
    w = raw_world(lib, 1, seed, features=[])
    spawn_grid(lib, w, n_units, 1, RAIDER)  # player-adjacent units the forces react to
    for fid in range(n_forces):
        lib.om_macro_init_force(w, fid, 1)
    return w


def test_e14_10_forces_1000_units_macro_eval_per_tick(lib):
    w = _build(lib, N_FORCES, N_UNITS, SEED)
    interval = lib.om_macro_evaluation_interval_ticks()
    med = median_ns(lambda: lib.om_macro_tick(w, interval))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_NS, f"E-14 {N_FORCES} forces / {N_UNITS} units, om_macro_tick")


def test_e14_control_note_force_count_bound_not_unit_count(lib):
    """Not a pass/fail control: om_macro_tick's per-evaluation loop is
    `for i in 0..n_forces` (csrc/enemy_macro.c) -- its cost is bound by force
    count, not unit count, so scaling unit count 10x cannot make it trip a
    budget/100 control. Recorded per the brief's "skip with stated reason"
    allowance."""
    w = _build(lib, N_FORCES, N_UNITS * 10, SEED)
    interval = lib.om_macro_evaluation_interval_ticks()
    med = median_ns(lambda: lib.om_macro_tick(w, interval))
    lib.om_world_free(w)
    print(f"[scale-control-skip] E-14: {N_UNITS * 10} units (10x), om_macro_tick raw_median={med / 1000.0:.3f}us")
    pytest.skip(
        "om_macro_tick's cost is bound by force count (10), not unit count -- "
        f"measured {med / 1000.0:.3f}us at 10x units, no scaling to trip a budget/100 control"
    )
