"""E-06 (docs/bible/epics/E-06-diplomacy-and-technology.md), "## Scale
requirements": "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a
miss is escalated): stance updates for 105 pairs (15 factions) in under 50 us
per tick; betrayal and peace checks O(pairs x border regions)."
"""
from ._scale_helpers import (
    OMArchetype,
    OMEdge,
    OMFeature,
    OMStance,
    OMTier,
    assert_budget,
    assert_control_violates_budget,
    median_ns,
    raw_world,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
)

N_FACTIONS = 15  # C(15,2) = 105 pairs
CONTROL_N_FACTIONS = 60  # OM_MAX_FACTIONS is 64; ~10x pair count (C(60,2)=1770 vs 105)
N_REGIONS = 60
BUDGET_NS = 50_000  # 50 us/tick
SEED = 2026091406


def _build(lib, n_factions, seed):
    w = raw_world(lib, N_REGIONS, seed, features=[OMFeature.DIPLOMACY, OMFeature.TECHNOLOGY])
    for idx in range(N_REGIONS):
        set_region(lib, w, idx, tier=OMTier.HOME, military=40.0, economy=50.0,
                    tension=20.0, population=50.0)
        set_owner(lib, w, idx, idx % n_factions)
        if idx > 0:
            set_edge(lib, w, idx - 1, idx, edge=OMEdge.BORDER)
    for fid in range(n_factions):
        set_faction(lib, w, fid, OMArchetype.DEFAULT, budget=50.0, tech=1.0, confidence=5.0)
        for other in range(fid):
            set_stance(lib, w, fid, other, OMStance.NEUTRAL)
    return w


def test_e06_15_factions_105_pairs_stance_update_per_tick(lib):
    w = _build(lib, N_FACTIONS, SEED)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_NS, f"E-06 {N_FACTIONS} factions (105 pairs), om_world_step")


def test_control_e06_60_factions_violates_tightened_budget(lib):
    w = _build(lib, CONTROL_N_FACTIONS, SEED)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_control_violates_budget(med, BUDGET_NS, f"E-06 control, {CONTROL_N_FACTIONS} factions")
