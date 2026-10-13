"""ALG-77 Selector history decay (docs/bible/algorithms.md; E-08 R-057-04, Q-057-01, Q-060-02 closed (a), Westley
2026-09-26): "A lineage's history weight in the commander pools decays by SELECTOR_DECAY_BASE = 0.75 per generation."

The only place the C applies 0.75 is the rotation chance: om_selector_decayed_rotation_prob(base_p, chapters) =
base_p + (1 - base_p) * (1 - 0.75^(chapters - 2)) for chapters > 2 (Q-057-01), base_p for chapters <= 2. That is what
this file asserts, with the factor typed from the ALG-77 text. The commander pools (ALG-47) weight a previous lineage
by gap and density only (om_selector_score_previous_lineage), with no 0.75 factor and no generation input: the
"history weight in the commander pools" half of ALG-77 has no mechanism to test (SL-C3-10 in
docs/northstar/plans/sim_lane_2026-10-12/findings/alg_c3.md, with a proposed Q- row).

Positive control: the 0.75 factor is distinguished from 0.5 and from 1.0 (no decay) by the values at 4 and 6 chapters.
"""
import pytest

DECAY = 0.75
MIN_CHAPTERS = 2  # ALG-46 SELECTOR_MIN_CHAPTERS


def _expected(base_p, chapters):
    if chapters <= MIN_CHAPTERS:
        return base_p
    return base_p + (1.0 - base_p) * (1.0 - DECAY ** (chapters - MIN_CHAPTERS))


@pytest.mark.parametrize("base_p", [0.1, 0.45, 0.8])
@pytest.mark.parametrize("chapters", [0, 1, 2, 3, 4, 6, 10, 30])
def test_ALG_77_rotation_chance_decays_by_0_75_per_chapter_past_the_minimum(lib, world_factory, base_p, chapters):
    w = world_factory(n_regions=2)
    assert lib.om_selector_decayed_rotation_prob(w, base_p=base_p, chapters=chapters) == pytest.approx(_expected(base_p, chapters))


def test_control_ALG_77_the_factor_is_neither_one_half_nor_one(lib, world_factory):
    w = world_factory(n_regions=2)
    got = lib.om_selector_decayed_rotation_prob(w, base_p=0.5, chapters=4)
    assert got == pytest.approx(0.5 + 0.5 * (1.0 - 0.75 ** 2))
    assert got != pytest.approx(0.5 + 0.5 * (1.0 - 0.5 ** 2))   # base 0.5 would be a half-life per generation
    assert got != pytest.approx(0.5)                              # base 1.0 (no decay) would stay at base_p
