"""ALG-72 Fairness (docs/bible/algorithms.md; E-17 R-117-01..03, Q-113-01 closed (b) logger only).

ALG-72: "evaluate_fairness scores path balance (max-flow staging->objective vs spawn->objective), travel-time balance
(BFS hops), vantage proximity balance, and hazard proximity balance; is_acceptable compares to thresholds; the live
pipeline logs the score and does not regenerate (FAIRNESS_MAX_RETRIES = 5 exists, unused; see Q-113-01)."

Both red tests are the fairness functions being STUBs (SL-C3-05).

ALG-72 gives no formula for the four balances and no threshold, so the test asserts only what the text states: the four
scores and the composite are produced in [0, 1], the score is logged, and a low score never regenerates the map (the
active seed is unchanged). The numbers themselves are a gap: SL-C3-06 proposes a Q- row.

Positive control: the main test pre-fills the score struct with -1.0; test_control_* shows that sentinel fails the range
check, so a stub that writes nothing cannot pass.
"""
import ctypes

import pytest


class _Score(ctypes.Structure):
    _fields_ = [("route_count_balance", ctypes.c_double), ("travel_time_balance", ctypes.c_double),
                ("vantage_accessibility_balance", ctypes.c_double), ("hazard_symmetry", ctypes.c_double),
                ("composite_score", ctypes.c_double)]


def test_ALG_72_evaluate_scores_the_four_balances_and_the_composite_in_unit_range_and_logs(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_map_generate(w, 0, 42)
    s = _Score(-1.0, -1.0, -1.0, -1.0, -1.0)  # sentinel: a stub that writes nothing leaves it out of range
    lib.om_fairness_evaluate(w, ctypes.byref(s))
    for name in ("route_count_balance", "travel_time_balance", "vantage_accessibility_balance", "hazard_symmetry", "composite_score"):
        assert 0.0 <= getattr(s, name) <= 1.0, name
    assert lib.om_fairness_is_score_logged(w) == 1


def test_ALG_72_a_low_score_is_logged_and_does_not_regenerate(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_map_generate(w, 0, 42)
    seed_before = lib.om_map_get_active_seed(w)
    lib.om_fairness_force_score(w, 0.10)
    lib.om_fairness_run_post_generation_check(w)
    assert lib.om_map_get_active_seed(w) == seed_before
    assert lib.om_fairness_is_score_logged(w) == 1


def test_control_ALG_72_an_unwritten_score_struct_fails_the_range_check(lib):
    s = _Score(-1.0, -1.0, -1.0, -1.0, -1.0)  # the sentinel the main test pre-fills
    assert not all(0.0 <= getattr(s, f[0]) <= 1.0 for f in _Score._fields_)
