"""ALG-46 Rotation decision (docs/bible/algorithms.md), rules R-057-01..R-057-07 (E-08, S-057).

Isolation: the base rotation probability from a hand-built delta, then the ordered
decision steps through om_character_selector_run_for_lineage on hand-built lineages.
Constants are read from csrc/om_constants.h by the names the row uses.
Unstated: the delta the live selector passes is not in the row (the C passes 0.0, see
the finding in the sim-lane report), Westley's.
unstated: whether a living commander out of range (rather than a dead one) forces rotation; the C forces on
"no living member within the hops" without looking at the commander's state, Westley's.
"""
import ctypes

import pytest

from alg_consts import const
from conftest import OMComposite, OMTier, force_draws, set_edge, set_region
from test_E08_S057_stay_with_the_family_or_move_on import OmSelectionRecord

MAXP = const("SELECTOR_MAX_ROTATION_PROB")
MINP = const("SELECTOR_MIN_ROTATION_PROB")
SAFE = const("SELECTOR_DELTA_SAFE")
CRISIS = const("SELECTOR_CRISIS_THRESHOLD")
DECAY = const("SELECTOR_DECAY_BASE")
MIN_CH = const("SELECTOR_MIN_CHAPTERS")
FORCED, NORMAL = 0, 1


def expected_base(delta):
    t = min(1.0, delta / SAFE)
    return MAXP + t * (MINP - MAXP)


@pytest.mark.parametrize("delta", [0.0, 50.0, 100.0, 199.0, 200.0, 500.0])
def test_ALG_46_step4_base_probability_formula(lib, world_factory, delta):
    """ALG-46 step 4 / R-057-03: p = MAX + min(1, delta/SAFE) * (MIN - MAX)."""
    w = world_factory(n_regions=2)
    assert lib.om_selector_base_rotation_prob(w, delta=delta) == pytest.approx(expected_base(delta), abs=1e-9)


def test_ALG_46_positive_control_wrong_value_rejected(lib, world_factory):
    """Positive control: an expectation that ignores the clamp at SAFE must fail against the C."""
    w = world_factory(n_regions=2)
    got = lib.om_selector_base_rotation_prob(w, delta=2 * SAFE)
    unclamped = MAXP + (2 * SAFE / SAFE) * (MINP - MAXP)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(unclamped, abs=1e-9)


def _run(lib, w, mission_region=0):
    rec = OmSelectionRecord()
    lib.om_character_selector_run_for_lineage(w, lineage_id=1, mission_region=mission_region, out_record=ctypes.byref(rec))
    return rec


def test_ALG_46_step1_forced_when_no_living_member(lib, world_factory):
    """ALG-46 step 1 / R-057-01: no living member in the lineage -> rotation, reason forced."""
    w = world_factory(n_regions=4)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=3)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=0, rank=3, birth_tick=0, lifespan=50)
    lib.om_character_kill(w, character_id=10, tick=50)
    rec = _run(lib, w)
    assert (rec.rotated, rec.reason) == (1, FORCED)


def test_ALG_46_step1_forced_when_no_member_within_hops(lib, world_factory):
    """ALG-46 step 1: a living member 3 hops out is outside SELECTOR_PROXIMITY_HOPS = 2 -> forced."""
    hops = const("SELECTOR_PROXIMITY_HOPS")
    w = world_factory(n_regions=6)
    for a in range(hops + 1):
        set_edge(lib, w, a, a + 1)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=3)
    lib.om_character_create(w, character_id=11, lineage_id=1, region_idx=hops + 1, rank=3, birth_tick=0, lifespan=80)
    rec = _run(lib, w)
    assert (rec.rotated, rec.reason) == (1, FORCED)


def test_ALG_46_step1_member_exactly_at_hop_limit_is_not_forced(lib, world_factory):
    """ALG-46 step 1 boundary: a living member exactly SELECTOR_PROXIMITY_HOPS away does not force rotation."""
    hops = const("SELECTOR_PROXIMITY_HOPS")
    w = world_factory(n_regions=6)
    for a in range(hops):
        set_edge(lib, w, a, a + 1)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=MIN_CH - 1)
    lib.om_character_create(w, character_id=11, lineage_id=1, region_idx=hops, rank=3, birth_tick=0, lifespan=80)
    rec = _run(lib, w)
    assert rec.rotated == 0 and rec.commander_id == 11


def test_ALG_46_step2_stay_below_min_chapters_even_on_a_rotating_draw(lib, world_factory):
    """ALG-46 step 2 / R-057-02: counter < SELECTOR_MIN_CHAPTERS stays, whatever the draw."""
    w = world_factory(n_regions=4)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=MIN_CH - 1)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=0, rank=3, birth_tick=0, lifespan=100)
    force_draws(lib, w, [0.0, 0.0, 0.0])
    assert _run(lib, w).rotated == 0


def test_ALG_46_step3_hard_cap_not_applied(lib, world_factory):
    """ALG-46 step 3 (struck by A-050): at chapters >= SELECTOR_HARD_CAP a draw above p_rotate still stays."""
    cap = const("SELECTOR_HARD_CAP")
    w = world_factory(n_regions=4)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=cap)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=0, rank=3, birth_tick=0, lifespan=100)
    set_region(lib, w, 0, tier=OMTier.HOME, military=60.0, economy=60.0, tension=5.0, population=60.0, faction_id=0)
    force_draws(lib, w, [0.999999])
    assert _run(lib, w).rotated == 0


def test_ALG_46_step4_draw_below_p_rotate_rotates_with_reason_normal(lib, world_factory):
    """ALG-46 step 4 / R-057-03: draw < p_rotate and calm home -> rotate, reason normal.
    p_rotate here = decayed(base(delta = 0), chapters) per ALG-77; draw 0.01 is below any of them."""
    w = world_factory(n_regions=4)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=MIN_CH + 1)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=0, rank=3, birth_tick=0, lifespan=100)
    set_region(lib, w, 0, tier=OMTier.HOME, military=60.0, economy=60.0, tension=5.0, population=60.0, faction_id=0)
    assert lib.om_region_composite(w, 0, OMComposite.STABILITY) >= CRISIS
    force_draws(lib, w, [0.01, 0.99])
    rec = _run(lib, w)
    assert (rec.rotated, rec.reason) == (1, NORMAL)


def test_ALG_46_step4_draw_at_or_above_p_rotate_stays(lib, world_factory):
    """ALG-46 step 4: draw >= p_rotate stays. p_rotate for delta 0, chapters = MIN+1."""
    p = expected_base(0.0)
    p_rotate = p + (1.0 - p) * (1.0 - DECAY ** 1)
    w = world_factory(n_regions=4)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=MIN_CH + 1)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=0, rank=3, birth_tick=0, lifespan=100)
    set_region(lib, w, 0, tier=OMTier.HOME, military=60.0, economy=60.0, tension=5.0, population=60.0, faction_id=0)
    force_draws(lib, w, [min(0.999999, p_rotate + 1e-6)])
    assert _run(lib, w).rotated == 0


def test_ALG_46_step4_crisis_veto_when_home_stability_below_threshold(lib, world_factory):
    """ALG-46 step 4 / R-057-05: draw says rotate but home stability < SELECTOR_CRISIS_THRESHOLD -> stay."""
    w = world_factory(n_regions=4)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=MIN_CH + 1)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=0, rank=3, birth_tick=0, lifespan=100)
    set_region(lib, w, 0, tier=OMTier.HOME, military=5.0, economy=10.0, tension=85.0, population=15.0, faction_id=0)
    assert lib.om_region_composite(w, 0, OMComposite.STABILITY) < CRISIS
    force_draws(lib, w, [0.01, 0.99])
    assert _run(lib, w).rotated == 0


def test_ALG_46_stay_picks_first_living_member_by_hop_distance(lib, world_factory):
    """ALG-46 stay rule / R-057-06: the nearest living member (own region first, then 1 hop, then 2) is picked."""
    w = world_factory(n_regions=4)
    set_edge(lib, w, 0, 1)
    set_edge(lib, w, 1, 2)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=1, chapters=MIN_CH - 1)
    lib.om_character_create(w, character_id=20, lineage_id=1, region_idx=2, rank=3, birth_tick=0, lifespan=100)
    lib.om_character_create(w, character_id=21, lineage_id=1, region_idx=1, rank=3, birth_tick=0, lifespan=100)
    assert _run(lib, w).commander_id == 21


def test_ALG_46_home_region_is_first_history_region(lib, world_factory):
    """ALG-46 home region / R-057-07: the first region recorded in the lineage history."""
    w = world_factory(n_regions=4)
    lib.om_lineage_create(w, lineage_id=1, home_region=2)
    lib.om_lineage_record_history_region(w, lineage_id=1, region_idx=3)
    assert lib.om_lineage_home_region(w, lineage_id=1) == 2
