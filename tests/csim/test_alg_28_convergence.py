"""ALG-28 Convergence (docs/bible/algorithms.md; E-06 R-047-01..04, S-047).

Rule: among factions this faction holds a cooperative stance toward, take the one
with the highest tech above its own; bonus = TECH_CONVERGENCE_RATE *
max(0, partner_tech - tech) / 100, rate 0.1; tech = min(100, tech + bonus).

Growth (ALG-27) is made zero by giving every region economy 0 and population 0,
and the world is stepped at tick 1 where the Knowledge Lost cooldown (ALG-27b)
cannot fire, so the only tech change is the convergence bonus. The expected
bonuses are computed here. The stance is read from the converging faction's side
("this faction holds a cooperative stance toward"). Positive control: a wrong
partner choice or rate fails the same assertions.
"""
import pytest

from conftest import (
    OMArchetype,
    OMFeature,
    OMStance,
    OMTier,
    isolate_agents,
    set_faction,
    set_owner,
    set_region,
    set_stance,
)

RATE = 0.1


def bonus(own, partner):
    return RATE * max(0.0, partner - own) / 100.0


def _world(lib, world_factory, techs):
    w = world_factory(n_regions=len(techs))
    isolate_agents(lib, w)
    lib.om_world_set_feature(w, OMFeature.TECHNOLOGY, 1)
    for i, t in enumerate(techs):
        set_faction(lib, w, i, OMArchetype.DEFAULT, budget=0.0, tech=t)
        set_region(lib, w, i, tier=OMTier.HOME, military=50.0, economy=0.0, tension=10.0, population=0.0)
        set_owner(lib, w, i, i)
    return w


def test_ALG_28_bonus_comes_from_the_highest_cooperative_partner_above_own(lib, world_factory):
    """A=30 cooperative with B=70, C=50 and E=20; D=90 is hostile and F=95 neutral. Only B counts: bonus 0.1*(70-30)/100 = 0.04; nothing is summed over partners."""
    w = _world(lib, world_factory, [30.0, 70.0, 50.0, 90.0, 20.0, 95.0])
    set_stance(lib, w, 0, 1, OMStance.COOPERATIVE, both_ways=False)
    set_stance(lib, w, 0, 2, OMStance.COOPERATIVE, both_ways=False)
    set_stance(lib, w, 0, 4, OMStance.COOPERATIVE, both_ways=False)
    set_stance(lib, w, 0, 3, OMStance.HOSTILE, both_ways=False)
    set_stance(lib, w, 0, 5, OMStance.NEUTRAL, both_ways=False)
    lib.om_world_step(w)
    assert lib.om_faction_tech(w, 0) == pytest.approx(30.0 + bonus(30.0, 70.0), abs=1e-9)


def test_ALG_28_the_stance_is_read_from_the_converging_factions_side(lib, world_factory):
    """A (30) is cooperative toward B (70) but B is neutral toward A: A gains 0.04, B gains nothing. C (30) is only the target of B-like cooperation (D=70 cooperative toward C, C neutral): C gains nothing."""
    w = _world(lib, world_factory, [30.0, 70.0, 30.0, 70.0])
    set_stance(lib, w, 0, 1, OMStance.COOPERATIVE, both_ways=False)
    set_stance(lib, w, 1, 0, OMStance.NEUTRAL, both_ways=False)
    set_stance(lib, w, 3, 2, OMStance.COOPERATIVE, both_ways=False)
    set_stance(lib, w, 2, 3, OMStance.NEUTRAL, both_ways=False)
    lib.om_world_step(w)
    assert lib.om_faction_tech(w, 0) == pytest.approx(30.0 + bonus(30.0, 70.0), abs=1e-9)
    assert lib.om_faction_tech(w, 1) == pytest.approx(70.0, abs=1e-9)
    assert lib.om_faction_tech(w, 2) == pytest.approx(30.0, abs=1e-9)
    assert lib.om_faction_tech(w, 3) == pytest.approx(70.0, abs=1e-9)


def test_ALG_28_no_bonus_at_equal_or_higher_own_tech(lib, world_factory):
    w = _world(lib, world_factory, [60.0, 60.0, 40.0])
    set_stance(lib, w, 0, 1, OMStance.COOPERATIVE, both_ways=False)   # equal
    set_stance(lib, w, 0, 2, OMStance.COOPERATIVE, both_ways=False)   # lower
    lib.om_world_step(w)
    assert lib.om_faction_tech(w, 0) == pytest.approx(60.0, abs=1e-9)


def test_control_ALG_28_detector_fires(lib, world_factory):
    """Positive control: the summed-over-partners result (0.04 + 0.02) and a rate of 0.2 are both rejected by the main assertion, and removing the cooperative stance removes the bonus."""
    w = _world(lib, world_factory, [30.0, 70.0, 50.0])
    set_stance(lib, w, 0, 1, OMStance.COOPERATIVE, both_ways=False)
    set_stance(lib, w, 0, 2, OMStance.COOPERATIVE, both_ways=False)
    lib.om_world_step(w)
    got = lib.om_faction_tech(w, 0)
    assert got == pytest.approx(30.0 + bonus(30.0, 70.0), abs=1e-9)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(30.0 + bonus(30.0, 70.0) + bonus(30.0, 50.0), abs=1e-9)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(30.0 + 0.2 * 40.0 / 100.0, abs=1e-9)
    w2 = _world(lib, world_factory, [30.0, 70.0])
    lib.om_world_step(w2)
    assert lib.om_faction_tech(w2, 0) == pytest.approx(30.0, abs=1e-9)
