"""E-04 (docs/bible/epics/E-04-events-and-chains.md), "## Scale requirements":
"Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is
escalated): trigger evaluation for 60 regions x 26 templates in under 20 us
per tick; queue resolution O(due entries)."
"""
from ._scale_helpers import OMFeature, assert_budget, assert_control_violates_budget, median_ns, raw_world

N_REGIONS = 60
CONTROL_N_REGIONS = 600
BUDGET_NS = 20_000  # 20 us/tick
SEED = 2026091402


def _build(lib, n_regions, seed):
    w = raw_world(lib, n_regions, seed, features=[OMFeature.EVENTS])
    lib.om_events_load_launch(w)  # the 26-template launch library
    return w


def test_e04_60_regions_26_templates_trigger_eval_per_tick(lib):
    w = _build(lib, N_REGIONS, SEED)
    assert lib.om_event_template_count(w) == 26, (
        f"launch library loaded {lib.om_event_template_count(w)} templates, expected 26"
    )
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_NS, f"E-04 {N_REGIONS} regions x 26 templates, om_world_step")


def test_control_e04_10x_regions_violates_tightened_budget(lib):
    w = _build(lib, CONTROL_N_REGIONS, SEED)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_control_violates_budget(med, BUDGET_NS, f"E-04 control, {CONTROL_N_REGIONS} regions")
