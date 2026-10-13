"""ALG-19 Reinforce (docs/bible/algorithms.md; E-05 R-036-06, S-036).

Rule: tier_cap = REINFORCE_MIL_CAP[tier] (home 100, frontier 60);
headroom = max(0, (tier_cap - m) / tier_cap); base = commit * 0.5 * headroom;
variance uniform in [0.85 - (t/100)*0.20, 1.15 + (t/100)*0.20]; delta_m =
base * variance; budget spent = commit.

The only reinforce the sim produces is the reactive 3e one, so it is driven by an
injected telegraph against the defender (see test_alg_18). A forced draw u in
[0,1] stands for the uniform draw: variance = lo + (hi - lo) * u, with lo, hi
computed here. Positive control: a different tension moves the variance bounds,
and a wrong expectation fails.
"""
import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMField,
    OMMode,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_reinforces,
    set_faction,
    set_owner,
    set_region,
    set_tech_multipliers,
)

CAP = {OMTier.HOME: 100.0, OMTier.FRONTIER: 60.0}
EFFICIENCY = 0.5
VAR_BASE = (0.85, 1.15)
VAR_TENSION_SCALE = 0.20
DEFENDER_BUDGET = 100.0
TELEGRAPH_COMMIT = 40.0  # -> commit = min(100*0.30, 40*0.5) = 20.0
COMMIT = min(DEFENDER_BUDGET * 0.30, TELEGRAPH_COMMIT * 0.5)


def _expected(tier, m, t, u):
    cap = CAP[tier]
    headroom = max(0.0, (cap - m) / cap)
    base = COMMIT * EFFICIENCY * headroom
    lo = VAR_BASE[0] - (t / 100.0) * VAR_TENSION_SCALE
    hi = VAR_BASE[1] + (t / 100.0) * VAR_TENSION_SCALE
    variance = lo + (hi - lo) * u
    return headroom, base, variance, base * variance


def _run(lib, world_factory, tier, m, t, u):
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=1000.0, confidence=2.0)
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget=DEFENDER_BUDGET)
    for f in (0, 1):
        set_tech_multipliers(lib, w, f, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=tier, military=m, economy=8.0, tension=t, population=50.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    inject_intent(lib, w, 1, OMAction.ACCUMULATE, 1, 1, 0.0)
    inject_intent(lib, w, 0, OMAction.ATTACK, 1, 0, TELEGRAPH_COMMIT, OMMode.TELEGRAPH)
    force_draws(lib, w, [0.0, u])  # 3e: probability draw (act), then the variance draw
    lib.om_world_step(w)
    recs = [r for r in read_reinforces(lib, w) if r.faction_id == 1]
    return w, recs


CASES = [
    (OMTier.HOME, 20.0, 0.0),
    (OMTier.HOME, 80.0, 50.0),
    (OMTier.HOME, 100.0, 100.0),
    (OMTier.FRONTIER, 30.0, 50.0),
    (OMTier.FRONTIER, 59.0, 0.0),
    (OMTier.FRONTIER, 80.0, 100.0),  # above the frontier cap: headroom floors at 0
]


@pytest.mark.parametrize("tier,m,t", CASES)
@pytest.mark.parametrize("u", [0.0, 0.25, 1.0])
def test_ALG_19_headroom_base_variance_and_delta(lib, world_factory, tier, m, t, u):
    headroom, base, variance, d_m = _expected(tier, m, t, u)
    w, recs = _run(lib, world_factory, tier, m, t, u)
    assert len(recs) == 1
    r = recs[0]
    assert r.commit == pytest.approx(COMMIT, abs=1e-9)
    assert r.headroom == pytest.approx(headroom, abs=1e-9)
    assert r.base == pytest.approx(base, abs=1e-9)
    assert r.variance == pytest.approx(variance, abs=1e-9)
    assert r.d_military == pytest.approx(d_m, abs=1e-9)
    assert lib.om_region_field(w, 1, OMField.MILITARY) == pytest.approx(m + d_m, abs=1e-9)


def test_ALG_19_budget_spent_equals_commit(lib, world_factory):
    w, recs = _run(lib, world_factory, OMTier.HOME, 20.0, 0.0, 0.5)
    assert len(recs) == 1
    assert lib.om_faction_budget(w, 1) == pytest.approx(DEFENDER_BUDGET - COMMIT, abs=1e-9)


def test_control_ALG_19_detector_fires(lib, world_factory):
    """Positive control: tension moves the variance interval at the same draw, and a wrong (tension-blind) expectation fails."""
    _, recs0 = _run(lib, world_factory, OMTier.HOME, 20.0, 0.0, 1.0)
    _, recs100 = _run(lib, world_factory, OMTier.HOME, 20.0, 100.0, 1.0)
    assert recs100[0].variance > recs0[0].variance
    with pytest.raises(AssertionError):
        assert recs100[0].variance == pytest.approx(_expected(OMTier.HOME, 20.0, 0.0, 1.0)[2], abs=1e-9)
