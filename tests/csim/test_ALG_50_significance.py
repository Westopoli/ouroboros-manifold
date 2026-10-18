"""ALG-50 Significance (docs/bible/algorithms.md), rules R-066-01..R-066-05 (E-09, S-066).

Isolation: om_chronicle_score_base, om_chronicle_context_multiplier and om_chronicle_calculate_score
on hand-built inputs, expected values computed here from the row's formula with the constants read
from csrc/om_constants.h by the names the row gives. The lineage-region term is also driven through
om_chronicle_score_event with a real lineage member in the region.
Unstated: how the live game obtains the template tier "default 2" (the ctypes entry takes the tier
as an argument, so the default is not reachable here), Westley's.
"""
import itertools

import pytest

from alg_consts import const

SCALE = const("SIGNIFICANCE_DELTA_SCALE")
CAP = const("SIGNIFICANCE_DELTA_CAP")
MISSION = const("SIGNIFICANCE_MISSION_REGION_BONUS")
CHAR = const("SIGNIFICANCE_CHARACTER_BONUS")
CHAIN_B = const("SIGNIFICANCE_CHAIN_LENGTH_BONUS")
LINEAGE = const("SIGNIFICANCE_LINEAGE_REGION_BONUS")
CHAIN_CAP = const("CHAIN_LENGTH_CAP")


def base(tier, d):
    return tier + min(d / SCALE, CAP)


def context(mission, char, chain, lineage):
    m = 1.0 + MISSION * mission + CHAR * char + LINEAGE * lineage
    if chain > 1:
        m += CHAIN_B * min(chain, CHAIN_CAP)
    return m


@pytest.mark.parametrize("tier,d", [(1, 0.0), (2, 25.0), (3, 149.99), (3, 150.0), (3, 151.0), (5, 2.0), (4, 1e6)])
def test_ALG_50_base_formula(lib, world_factory, tier, d):
    """ALG-50: base = tier + min(|delta|_sum / 50, 3.0)."""
    w = world_factory(n_regions=2)
    assert lib.om_chronicle_score_base(w, tier=tier, delta_sum=d) == pytest.approx(base(tier, d), abs=1e-9)


@pytest.mark.parametrize("chain", [0, 1, 2, 3, 5, 6, 40])
@pytest.mark.parametrize("flags", list(itertools.product((0, 1), repeat=3)))
def test_ALG_50_context_multiplier_formula(lib, world_factory, chain, flags):
    """ALG-50: context = 1 + 0.5[mission] + 0.3[character] + 0.1*min(chain, 5)[chain > 1] + 0.8[lineage]."""
    mission, char, lineage = flags
    w = world_factory(n_regions=2)
    got = lib.om_chronicle_context_multiplier(w, in_mission_region=mission, has_character=char,
                                              chain_length=chain, has_lineage_member=lineage)
    assert got == pytest.approx(context(mission, char, chain, lineage), abs=1e-9)


@pytest.mark.parametrize("tier,d,flags,chain", [
    (2, 50.0, (1, 1, 1), 3),
    (5, 2.0, (0, 0, 0), 1),
    (2, 200.0, (1, 1, 0), 6),
    (1, 0.0, (0, 1, 1), 2),
])
def test_ALG_50_score_is_base_times_context(lib, world_factory, tier, d, flags, chain):
    """ALG-50: score = base * context."""
    mission, char, lineage = flags
    w = world_factory(n_regions=2)
    got = lib.om_chronicle_calculate_score(w, tier=tier, delta_sum=d, in_mission_region=mission, has_character=char,
                                           chain_length=chain, has_lineage_member=lineage)
    assert got == pytest.approx(base(tier, d) * context(mission, char, chain, lineage), abs=1e-9)


def test_ALG_50_positive_control_uncapped_delta_rejected(lib, world_factory):
    """Positive control: a base that skips the DELTA_CAP clamp (delta 400 -> 8.0, not 3.0) must be rejected."""
    w = world_factory(n_regions=2)
    got = lib.om_chronicle_score_base(w, tier=2, delta_sum=400.0)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(2 + 400.0 / SCALE, abs=1e-9)


def test_ALG_50_positive_control_chain_cap_rejected(lib, world_factory):
    """Positive control: a chain term that is not capped at CHAIN_LENGTH_CAP must be rejected."""
    w = world_factory(n_regions=2)
    got = lib.om_chronicle_context_multiplier(w, in_mission_region=0, has_character=0, chain_length=9, has_lineage_member=0)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(1.0 + CHAIN_B * 9, abs=1e-9)


def test_ALG_50_score_event_adds_lineage_bonus_when_a_member_lives_in_the_region(lib, world_factory):
    """ALG-50: the lineage-region term is applied by om_chronicle_score_event when a lineage member lives in the region."""
    w = world_factory(n_regions=3)
    lib.om_lineage_create(w, lineage_id=1, home_region=1)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=1, rank=3, birth_tick=0, lifespan=1000)
    with_member = lib.om_chronicle_score_event(w, region_idx=1, tier=3, delta_sum=50.0)
    without = lib.om_chronicle_score_event(w, region_idx=2, tier=3, delta_sum=50.0)
    assert with_member == pytest.approx(base(3, 50.0) * context(0, 0, 0, 1), abs=1e-9)
    assert without == pytest.approx(base(3, 50.0) * context(0, 0, 0, 0), abs=1e-9)
