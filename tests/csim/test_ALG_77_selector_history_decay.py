"""ALG-77 Selector history decay (docs/bible/algorithms.md), rule R-057-04 / Q-060-02 (E-08).

The row states: a lineage's history weight in the commander pools decays by
SELECTOR_DECAY_BASE = 0.75 per generation (Westley 2026-09-26). Asserted here: the constant
named by the row, and the arithmetic at the one C site that uses it,
om_selector_decayed_rotation_prob (generational.c:1795), as Q-057-01 option (a):
p_rotate = base + (1 - base) * (1 - 0.75^(c - 2)) for c above SELECTOR_MIN_CHAPTERS, base below.
unstated: the weight the decay multiplies in the commander pools (the row names no formula for
the pool weight and no generation index), Westley's. The C applies the base to the chapter
counter of the rotation probability, not to a pool weight or a generation; see the sim-lane
report finding.
"""
import pytest

from alg_consts import const

DECAY = const("SELECTOR_DECAY_BASE")
MIN_CH = const("SELECTOR_MIN_CHAPTERS")


def expected(base, c):
    if c <= MIN_CH:
        return base
    return base + (1.0 - base) * (1.0 - DECAY ** (c - MIN_CH))


def test_ALG_77_decay_base_is_the_rows_value():
    """ALG-77: SELECTOR_DECAY_BASE = 0.75."""
    assert DECAY == 0.75


@pytest.mark.parametrize("base", [0.1, 0.45, 0.8])
@pytest.mark.parametrize("chapters", [0, 1, 2, 3, 4, 6, 10, 40])
def test_ALG_77_decayed_rotation_probability(lib, world_factory, base, chapters):
    """ALG-77 / Q-057-01 (a): the decayed rotation probability from the row's constant."""
    w = world_factory(n_regions=2)
    got = lib.om_selector_decayed_rotation_prob(w, base_p=base, chapters=chapters)
    assert got == pytest.approx(expected(base, chapters), abs=1e-12)


def test_ALG_77_never_reaches_one_and_rises_monotonically(lib, world_factory):
    """ALG-77: the stay probability decays geometrically and never hits zero (no hard cap)."""
    w = world_factory(n_regions=2)
    prev = 0.0
    for c in range(MIN_CH, 30):
        p = lib.om_selector_decayed_rotation_prob(w, base_p=0.1, chapters=c)
        assert p >= prev and p < 1.0
        prev = p


def test_ALG_77_positive_control_other_base_rejected(lib, world_factory):
    """Positive control: an expectation built with decay base 0.5 must be rejected."""
    w = world_factory(n_regions=2)
    got = lib.om_selector_decayed_rotation_prob(w, base_p=0.5, chapters=MIN_CH + 2)
    wrong = 0.5 + 0.5 * (1.0 - 0.5 ** 2)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(wrong, abs=1e-9)
