"""E-05 (docs/bible/epics/E-05-faction-agents-and-conflict.md), "## Scale
requirements": "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a
miss is escalated): 15 factions deciding over 60 regions in under 200 us per
tick; 5,000 ticks with full agents in under 5 s."
"""
import time

from ._scale_helpers import (
    OMArchetype,
    OMFeature,
    OMTier,
    assert_budget,
    assert_control_violates_budget,
    median_ns,
    raw_world,
    set_faction,
    set_owner,
    set_region,
)

N_REGIONS = 60
N_FACTIONS = 15
CONTROL_N_REGIONS = 512
PER_TICK_BUDGET_NS = 200_000  # 200 us/tick
BULK_BUDGET_NS = 5_000_000_000  # 5 s for 5,000 ticks, full agents
SEED = 2026091405


def _build(lib, n_regions, n_factions, seed, *, full_agents):
    features = [OMFeature.FACTIONS]
    if full_agents:
        features += [OMFeature.FRICTION, OMFeature.ADMIN_REVOLTS]
    w = raw_world(lib, n_regions, seed, features=features)
    for idx in range(n_regions):
        set_region(lib, w, idx, tier=OMTier.HOME, military=40.0, economy=50.0,
                    tension=20.0, population=50.0)
        set_owner(lib, w, idx, idx % n_factions)
    for fid in range(n_factions):
        arch = OMArchetype.CONQUEROR if fid % 2 == 0 else OMArchetype.FORTIFIER
        set_faction(lib, w, fid, arch, budget=50.0, tech=1.0, confidence=5.0)
    return w


def test_e05_15_factions_60_regions_decide_per_tick(lib):
    w = _build(lib, N_REGIONS, N_FACTIONS, SEED, full_agents=False)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_budget(med, PER_TICK_BUDGET_NS, f"E-05 {N_FACTIONS} factions x {N_REGIONS} regions, om_world_step")


def test_e05_5000_ticks_full_agents_under_5s(lib):
    w = _build(lib, N_REGIONS, N_FACTIONS, SEED, full_agents=True)
    t0 = time.perf_counter_ns()
    ran = lib.om_world_run(w, 5000)
    t1 = time.perf_counter_ns()
    lib.om_world_free(w)
    assert ran == 5000
    assert_budget(t1 - t0, BULK_BUDGET_NS, "E-05 5,000-tick bulk, full agents")


def test_control_e05_10x_regions_violates_tightened_budget(lib):
    w = _build(lib, CONTROL_N_REGIONS, N_FACTIONS, SEED, full_agents=False)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_control_violates_budget(med, PER_TICK_BUDGET_NS, f"E-05 control, {CONTROL_N_REGIONS} regions")
