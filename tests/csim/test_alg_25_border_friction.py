"""ALG-25 Border friction (docs/bible/algorithms.md; E-05 R-041-01..05, S-041, Q-041-01).

Rule: for each inhabited owned region, over every neighbor across a `border` or
`both` edge (trade-only contributes nothing) owned by a different faction where
either side's stance toward the other is hostile: tension +0.15 and economy
-0.05 per such neighbor, flat (not scaled by the neighbor's military). Summed:
t = min(100, t + sum), e = max(8.0, e - sum); composites recompute (ALG-09/10).

One hub region is surrounded by neighbors that each hit exactly one clause of the
rule; the expected sum is computed here. Positive control: the debug build with
OM_BUG_FRICTION_COUNTS_TRADE injected must make the same assertions fail.
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMComposite,
    OMEdge,
    OMField,
    OMStance,
    OMTier,
    isolate_agents,
    read_friction,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)

BORDER_FRICTION_TENSION = 0.15
BORDER_FRICTION_ECONOMY = 0.05
ECONOMY_FLOOR = 8.0
FIELD_MAX = 100.0


def _hub_world(handle, factory, *, inject=None, hub_econ=50.0, hub_tension=20.0):
    """Hub 0 (faction 0) and seven neighbors. Counting neighbors: 1 (hostile only from the
    neighbor's side, border edge) and 2 (hostile both ways, both edge). Not counting: 3 (hostile,
    trade-only edge), 4 (neutral), 5 (same faction), 6 (unowned), 7 (cooperative)."""
    w = factory(n_regions=8)
    isolate_agents(handle, w, friction=True)
    for f in range(6):
        set_faction(handle, w, f, OMArchetype.DEFAULT, budget=0.0, tech=0.0, confidence=5.0)
        set_tech_multipliers(handle, w, f, 1.0, 1.0, 1.0)
    set_stance(handle, w, 1, 0, OMStance.HOSTILE, both_ways=False)   # only faction 1 is hostile
    set_stance(handle, w, 0, 2, OMStance.HOSTILE)
    set_stance(handle, w, 0, 3, OMStance.HOSTILE)
    set_stance(handle, w, 0, 4, OMStance.NEUTRAL)
    set_stance(handle, w, 0, 5, OMStance.COOPERATIVE)
    if inject is not None:
        handle.om_debug_inject(w, inject)
    owners = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 0, 6: -1, 7: 5}
    militaries = {0: 50.0, 1: 5.0, 2: 95.0, 3: 50.0, 4: 50.0, 5: 50.0, 6: 0.0, 7: 50.0}
    for idx, f in owners.items():
        tier = OMTier.EMPTY if f < 0 else OMTier.HOME
        eco = hub_econ if idx == 0 else 50.0
        ten = hub_tension if idx == 0 else 20.0
        set_region(handle, w, idx, tier=tier, military=militaries[idx], economy=eco if f >= 0 else 0.0,
                   tension=ten if f >= 0 else 0.0, population=50.0 if f >= 0 else 0.0, faction_id=f)
        if f >= 0:
            set_owner(handle, w, idx, f, held_since=-1)
    set_edge(handle, w, 0, 1, OMEdge.BORDER)
    set_edge(handle, w, 0, 2, OMEdge.BOTH)
    set_edge(handle, w, 0, 3, OMEdge.TRADE)
    set_edge(handle, w, 0, 4, OMEdge.BORDER)
    set_edge(handle, w, 0, 5, OMEdge.BORDER)
    set_edge(handle, w, 0, 6, OMEdge.BORDER)
    set_edge(handle, w, 0, 7, OMEdge.BORDER)
    handle.om_world_step(w)
    return w


def _assert_hub_friction(handle, w, hostile=2, hub_econ=50.0, hub_tension=20.0):
    sum_t = hostile * BORDER_FRICTION_TENSION
    sum_e = hostile * BORDER_FRICTION_ECONOMY
    exp_t = min(FIELD_MAX, hub_tension + sum_t)
    exp_e = max(ECONOMY_FLOOR, hub_econ - sum_e)
    rec = next(r for r in read_friction(handle, w) if r.region_idx == 0)
    assert rec.hostile_neighbors == hostile
    # the friction record carries the applied (clamped) delta; unclamped it equals the sum
    assert rec.d_tension == pytest.approx(exp_t - hub_tension, abs=1e-9)
    assert rec.d_economy == pytest.approx(exp_e - hub_econ, abs=1e-9)
    assert handle.om_region_field(w, 0, OMField.TENSION) == pytest.approx(exp_t, abs=1e-9)
    assert handle.om_region_field(w, 0, OMField.ECONOMY) == pytest.approx(exp_e, abs=1e-9)
    # composites recompute from the post-friction fields (ALG-09 / ALG-10, m=50, p=50)
    m, p = 50.0, 50.0
    stab = m * 0.40 + (100.0 - exp_t) * 0.35 + p * 0.25
    cap = exp_e * 0.50 + p * 0.35 + m * 0.15
    if exp_e < 20.0:   # CAP_ECONOMY_PENALTY 0.65 below CAP_ECONOMY_THRESHOLD 20.0 (m, p are above their thresholds)
        cap *= 0.65
    assert handle.om_region_composite(w, 0, OMComposite.STABILITY) == pytest.approx(stab, abs=0.0051)
    assert handle.om_region_composite(w, 0, OMComposite.CAPACITY) == pytest.approx(cap, abs=0.0051)


def test_ALG_25_flat_per_hostile_border_or_both_neighbor_only(lib, world_factory):
    """Two counting neighbors (one hostile from the neighbor's side only, one both ways) of military 5 and 95 give exactly +0.30 / -0.10; trade-only, neutral, same-faction, unowned and cooperative neighbors give nothing."""
    w = _hub_world(lib, world_factory)
    _assert_hub_friction(lib, w)


def test_ALG_25_economy_floor_and_tension_cap(lib, world_factory):
    """economy bottoms at ECONOMY_FLOOR 8.0 (8.05 - 0.10 -> 8.0) and tension tops at 100 (99.9 + 0.30 -> 100)."""
    w = _hub_world(lib, world_factory, hub_econ=8.05, hub_tension=99.9)
    _assert_hub_friction(lib, w, hub_econ=8.05, hub_tension=99.9)
    assert lib.om_region_field(w, 0, OMField.ECONOMY) == 8.0
    assert lib.om_region_field(w, 0, OMField.TENSION) == 100.0


def test_control_ALG_25_trade_edge_injection_trips_the_detector(dbg, dbg_world_factory):
    """Positive control: with OM_BUG_FRICTION_COUNTS_TRADE the trade-only hostile neighbor is counted, so the ALG-25 assertions above must fail."""
    w = _hub_world(dbg, dbg_world_factory, inject=OMBugE05.FRICTION_COUNTS_TRADE)
    with pytest.raises(AssertionError):
        _assert_hub_friction(dbg, w)
