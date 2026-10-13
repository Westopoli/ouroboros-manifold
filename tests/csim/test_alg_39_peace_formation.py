"""ALG-39 Peace formation (docs/bible/algorithms.md; E-06 S-043, R-043-*, ALG-38 counter).

Rule: for each neutral pair with counter >= PEACE_FORMATION_THRESHOLD = 80: stab = min(avg
stability of A's regions bordering B, avg of B's regions bordering A); if stab <
PEACE_STABILITY_THRESHOLD = 35.0, counter = 0 and no draw. Else p = clamp(PEACE_BASE_PROBABILITY
(0.5) * (1 - |avg_e_A - avg_e_B|/100) * (stab/100) * disp_A * disp_B, 0, 1) with dispositions
conqueror 0.1, fortifier 2.0, warlord 0.2, opportunist 1.0, schism 0.3, player 1.5, breakaway 0.8.
One draw; success if draw < p: stance cooperative both ways, cooperative-since = tick, shared
edges `both`. Failure: counter = 0.

Only the diplomacy step is enabled. Expected probabilities are computed in this file from the
rule (stability by ALG-09). Positive control: a draw at p exactly (strict <) and the below-35
case both fail the success expectation, and a wrong disposition fails the probability check.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMFeature,
    OMStance,
    OMTier,
    force_draws,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
)

BASE = 0.5
THRESHOLD = 80
STAB_MIN = 35.0
DISP = {
    OMArchetype.CONQUEROR: 0.1,
    OMArchetype.FORTIFIER: 2.0,
    OMArchetype.WARLORD: 0.2,
    OMArchetype.OPPORTUNIST: 1.0,
    OMArchetype.SCHISM: 0.3,
    OMArchetype.PLAYER: 1.5,
    OMArchetype.BREAKAWAY: 0.8,
}


def stability(m, t, p):
    """ALG-09 with the penalties (m < 10 x0.70, p < 20 x0.75), rounded to 2 decimals."""
    s = m * 0.40 + (100.0 - t) * 0.35 + p * 0.25
    if m < 10.0:
        s *= 0.70
    if p < 20.0:
        s *= 0.75
    return round(s, 2)


def peace_p(arch_a, arch_b, ea, eb, stab):
    return min(1.0, max(0.0, BASE * (1.0 - abs(ea - eb) / 100.0) * (stab / 100.0) * DISP[arch_a] * DISP[arch_b]))


def _world(handle, factory, arch_a, arch_b, *, counter=THRESHOLD - 1, tension_b=0.0, stance=OMStance.NEUTRAL):
    """Faction 0 owns r0 (borders B, e 80, t 0) and r1 (no border, e 40): avg_e_A = 60. Faction 1 owns r2
    (borders A, e 50, tension `tension_b`)."""
    w = factory(n_regions=3)
    for f in range(8):
        handle.om_world_set_feature(w, f, 0)
    handle.om_world_set_feature(w, OMFeature.DIPLOMACY, 1)
    set_faction(handle, w, 0, arch_a, budget=0.0, tech=0.0)
    set_faction(handle, w, 1, arch_b, budget=0.0, tech=0.0)
    set_stance(handle, w, 0, 1, stance)
    set_region(handle, w, 0, tier=OMTier.HOME, military=50.0, economy=80.0, tension=0.0, population=50.0, faction_id=0)
    set_region(handle, w, 1, tier=OMTier.HOME, military=50.0, economy=40.0, tension=0.0, population=50.0, faction_id=0)
    set_region(handle, w, 2, tier=OMTier.HOME, military=50.0, economy=50.0, tension=tension_b, population=50.0, faction_id=1)
    for idx, f in ((0, 0), (1, 0), (2, 1)):
        set_owner(handle, w, idx, f, held_since=-1)
    set_edge(handle, w, 0, 2, OMEdge.BORDER)
    handle.om_faction_set_stance_counter(w, 0, 1, counter)
    return w


def _step(handle, w, draw):
    force_draws(handle, w, [draw])
    handle.om_world_step(w)


def _assert_peace(handle, w):
    assert handle.om_faction_stance(w, 0, 1) == OMStance.COOPERATIVE
    assert handle.om_faction_stance(w, 1, 0) == OMStance.COOPERATIVE
    assert handle.om_faction_cooperative_since(w, 0, 1) == 1
    edge = ctypes.c_int(-1)
    assert handle.om_region_edge(w, 0, 2, ctypes.byref(edge)) == 1
    assert edge.value == OMEdge.BOTH


STAB = min(stability(50.0, 0.0, 50.0), stability(50.0, 0.0, 50.0))  # 67.5 at tension 0 on both sides


@pytest.mark.parametrize("arch", sorted(DISP))
def test_ALG_39_probability_uses_the_archetype_disposition_strict_less_than(lib, world_factory, arch):
    """A of archetype `arch` against an opportunist (1.0); avg_e_A = (80+40)/2 = 60 over all A's regions, avg_e_B = 50."""
    p = peace_p(arch, OMArchetype.OPPORTUNIST, 60.0, 50.0, STAB)
    assert 0.0 < p < 1.0
    w = _world(lib, world_factory, arch, OMArchetype.OPPORTUNIST)
    _step(lib, w, p - 1e-6)
    _assert_peace(lib, w)
    w2 = _world(lib, world_factory, arch, OMArchetype.OPPORTUNIST)
    _step(lib, w2, p)                      # draw == p is not < p
    assert lib.om_faction_stance(w2, 0, 1) == OMStance.NEUTRAL
    assert lib.om_faction_stance_counter(w2, 0, 1) == 0


def test_ALG_39_probability_is_clamped_to_1(lib, world_factory):
    p_raw = BASE * 0.9 * (STAB / 100.0) * 2.0 * 2.0
    assert p_raw > 1.0
    w = _world(lib, world_factory, OMArchetype.FORTIFIER, OMArchetype.FORTIFIER)
    _step(lib, w, 0.999999)
    _assert_peace(lib, w)


def test_ALG_39_below_the_counter_threshold_nothing_is_drawn(lib, world_factory):
    w = _world(lib, world_factory, OMArchetype.OPPORTUNIST, OMArchetype.OPPORTUNIST, counter=THRESHOLD - 2)
    _step(lib, w, 0.0)
    assert lib.om_rng_forced_remaining(w) == 1
    assert lib.om_faction_stance(w, 0, 1) == OMStance.NEUTRAL
    assert lib.om_faction_stance_counter(w, 0, 1) == THRESHOLD - 1


def test_ALG_39_low_stability_resets_the_counter_with_no_draw(lib, world_factory):
    """Tension 95 on B gives border stability 32.5 + 5*0.35 = 34.25 < 35.0; tension 90 gives 36.0 and the draw is taken."""
    assert stability(50.0, 95.0, 50.0) < STAB_MIN <= stability(50.0, 90.0, 50.0)
    w = _world(lib, world_factory, OMArchetype.OPPORTUNIST, OMArchetype.OPPORTUNIST, tension_b=95.0)
    _step(lib, w, 0.0)
    assert lib.om_rng_forced_remaining(w) == 1, "below the stability threshold no draw is made"
    assert lib.om_faction_stance(w, 0, 1) == OMStance.NEUTRAL
    assert lib.om_faction_stance_counter(w, 0, 1) == 0
    w2 = _world(lib, world_factory, OMArchetype.OPPORTUNIST, OMArchetype.OPPORTUNIST, tension_b=90.0)
    _step(lib, w2, 0.0)
    assert lib.om_rng_forced_remaining(w2) == 0
    assert lib.om_faction_stance(w2, 0, 1) == OMStance.COOPERATIVE


def test_ALG_39_stability_is_the_minimum_of_the_two_border_averages(lib, world_factory):
    """B at tension 90 (36.0) is the minimum against A at 67.5: p uses 36.0, not 67.5 or the mean."""
    stab_b = stability(50.0, 90.0, 50.0)
    p = peace_p(OMArchetype.OPPORTUNIST, OMArchetype.OPPORTUNIST, 60.0, 50.0, stab_b)
    w = _world(lib, world_factory, OMArchetype.OPPORTUNIST, OMArchetype.OPPORTUNIST, tension_b=90.0)
    _step(lib, w, p - 1e-6)
    _assert_peace(lib, w)
    w2 = _world(lib, world_factory, OMArchetype.OPPORTUNIST, OMArchetype.OPPORTUNIST, tension_b=90.0)
    _step(lib, w2, p + 1e-6)
    assert lib.om_faction_stance(w2, 0, 1) == OMStance.NEUTRAL
    assert lib.om_faction_stance_counter(w2, 0, 1) == 0


def test_control_ALG_39_detector_fires(lib, world_factory):
    """Positive control: wrong expectations are rejected -- a draw of exactly p succeeding, and the conqueror pair using the opportunist disposition."""
    p_wrong = peace_p(OMArchetype.OPPORTUNIST, OMArchetype.OPPORTUNIST, 60.0, 50.0, STAB)
    p_right = peace_p(OMArchetype.CONQUEROR, OMArchetype.OPPORTUNIST, 60.0, 50.0, STAB)
    assert p_wrong > p_right * 5
    w = _world(lib, world_factory, OMArchetype.CONQUEROR, OMArchetype.OPPORTUNIST)
    _step(lib, w, p_right + 1e-4)           # inside the wrong (opportunist x opportunist) probability
    with pytest.raises(AssertionError):
        _assert_peace(lib, w)
