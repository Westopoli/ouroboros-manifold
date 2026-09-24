"""E-07 (docs/bible/epics/E-07-civilizational-lifecycle.md), "## Scale
requirements": "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a
miss is escalated): cleanup over 60 factions in under 50 us per tick."

OM_MAX_FACTIONS is 64 (csrc/ouroboros_sim.h #define), so a 10x-N (600)
control cannot be built; the positive control is skipped with that reason
per the brief ("skip the control with a stated reason if 10x N cannot be
built").
"""
import pytest

from ._scale_helpers import OMArchetype, OMFeature, assert_budget, median_ns, raw_world, set_faction

N_FACTIONS = 60
BUDGET_NS = 50_000  # 50 us/tick
SEED = 2026091407


def _build(lib, n_factions, seed):
    w = raw_world(lib, 1, seed, features=[OMFeature.LIFECYCLE])
    for fid in range(n_factions):
        set_faction(lib, w, fid, OMArchetype.DEFAULT, budget=10.0, tech=1.0, confidence=5.0)
    return w


def test_e07_60_factions_cleanup_per_tick(lib):
    w = _build(lib, N_FACTIONS, SEED)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_NS, f"E-07 {N_FACTIONS}-faction cleanup, om_world_step")


@pytest.mark.skip(reason="OM_MAX_FACTIONS is 64 (csrc/ouroboros_sim.h): a 10x-N (600 faction) "
                          "control world cannot be built for this epic")
def test_control_e07_10x_factions_violates_tightened_budget():
    pass
