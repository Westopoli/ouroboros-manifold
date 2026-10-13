"""ALG-46 Rotation decision (docs/bible/algorithms.md), proving R-057-01 .. R-057-05 and R-057-08 (S-057, E-08).

Order: (1) forced rotation if the lineage has no living member, or none within 2 hops of the mission
region; (2) stay below SELECTOR_MIN_CHAPTERS = 2; (3) the hard cap is gone, replaced by the decay of
Q-057-01 (closed: any curve that decays and never reaches 0 or a cap; the test reads the curve the
register proposed and the repo implements); (4) p_rotate = 0.8 + min(1, delta/200) * (0.1 - 0.8),
one draw, rotate (reason normal) if draw < p_rotate unless the home region's stability < 20.0 (veto).
Expectations are computed here from those lines; the SL-C2 wiring test reads the delta the rule names.
"""
import ctypes

from conftest import OMField, OMTier, OmSelectionRecord, force_draws, set_edge, set_region

MAX_P, MIN_P, DELTA_SAFE = 0.8, 0.1, 200.0
MIN_CHAPTERS = 2
CRISIS = 20.0
DECAY_BASE = 0.75
REASON_FORCED, REASON_NORMAL = 0, 1
RANK_LINEAGE_MEMBER = 3


def _ref_base_p(delta, max_p=MAX_P, min_p=MIN_P, safe=DELTA_SAFE):
    t = min(1.0, delta / safe)
    return max_p + t * (min_p - max_p)


def _ref_decayed_p(base, chapters):
    if chapters <= MIN_CHAPTERS:
        return base
    return base + (1.0 - base) * (1.0 - DECAY_BASE ** (chapters - MIN_CHAPTERS))


def _lineage(lib, w, lineage=1, chapters=2, home=0, members=((10, 0),)):
    lib.om_lineage_create(w, lineage_id=lineage, home_region=home)
    lib.om_lineage_set_chapter_count(w, lineage_id=lineage, chapters=chapters)
    for cid, region in members:
        lib.om_character_create(w, character_id=cid, lineage_id=lineage, region_idx=region,
                                rank=RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)


def _select(lib, w, mission_region=0, lineage=1, draws=()):
    if draws:
        force_draws(lib, w, list(draws))
    rec = OmSelectionRecord()
    lib.om_character_selector_run_for_lineage(w, lineage_id=lineage, mission_region=mission_region,
                                              out_record=ctypes.byref(rec))
    return rec


def _calm_home(lib, w, idx=0):
    """A home region whose ALG-09 stability is far above 20 (low tension, solid military and population)."""
    set_region(lib, w, idx, tier=OMTier.HOME, military=60.0, economy=50.0, tension=10.0, population=60.0, faction_id=0)


def _crisis_home(lib, w, idx=0):
    set_region(lib, w, idx, tier=OMTier.HOME, military=5.0, economy=10.0, tension=90.0, population=15.0, faction_id=0)


def test_control_ALG_46_wrong_curves_are_detected(lib, world_factory):
    """Positive control: a reference with max 0.9, safe 100 or decay base 0.5 disagrees with the C probability, so the sweeps below can fail; and the draw really flips the outcome (0.5 rotates, 0.95 stays) in the same fixture."""
    w = world_factory(n_regions=2)
    got = lib.om_selector_base_rotation_prob(w, delta=50.0)
    assert abs(got - _ref_base_p(50.0, max_p=0.9)) > 1e-3
    assert abs(got - _ref_base_p(50.0, safe=100.0)) > 1e-3
    assert abs(lib.om_selector_decayed_rotation_prob(w, base_p=0.5, chapters=5) - (0.5 + 0.5 * (1 - 0.5 ** 3))) > 1e-3
    w1 = world_factory(n_regions=2)
    _calm_home(lib, w1)
    _lineage(lib, w1)
    assert _select(lib, w1, draws=[0.5, 0.95]).rotated == 1
    w2 = world_factory(n_regions=2)
    _calm_home(lib, w2)
    _lineage(lib, w2)
    assert _select(lib, w2, draws=[0.95, 0.95]).rotated == 0


def test_ALG_46_step4_rotation_probability_curve(lib, world_factory):
    """ALG-46 step 4 / R-057-03: p = 0.8 + min(1, D/200)(0.1 - 0.8) for D in [0, 400], clamped past 200; ALG-46 step 3 / R-057-04: the decay never reaches 1 or a cap for c up to 20."""
    w = world_factory(n_regions=2)
    for d in [x * 5.0 for x in range(0, 81)]:
        assert abs(lib.om_selector_base_rotation_prob(w, delta=d) - _ref_base_p(d)) <= 1e-12, d
    for base in (0.1, 0.45, 0.8):
        previous = None
        for c in range(2, 21):
            got = lib.om_selector_decayed_rotation_prob(w, base_p=base, chapters=c)
            assert abs(got - _ref_decayed_p(base, c)) <= 1e-12, (base, c)
            assert got < 1.0
            if previous is not None:
                assert got >= previous  # stay probability only falls as c grows
            previous = got


def test_ALG_46_step1_forced_when_no_living_member_within_two_hops(lib, world_factory):
    """ALG-46 step 1 / R-057-01: the commander (character 10, region 0) is dead and the only living member is 3 hops from the mission region: forced rotation, reason forced. The same member at 2 hops: not forced. A lineage with no living member at all: forced."""
    def build(member_region, members):
        w = world_factory(n_regions=5)
        for a, b in ((0, 1), (1, 2), (2, 3)):
            set_edge(lib, w, a, b)
        _calm_home(lib, w)
        _lineage(lib, w, chapters=1, members=members)
        return w

    w = build(3, ((10, 0), (11, 3)))
    lib.om_character_kill(w, 10, tick=5)
    rec = _select(lib, w, mission_region=0)
    assert rec.rotated == 1 and rec.reason == REASON_FORCED
    w2 = build(2, ((10, 0), (11, 2)))
    lib.om_character_kill(w2, 10, tick=5)
    assert _select(lib, w2, mission_region=0).rotated == 0
    w3 = build(0, ())
    rec3 = _select(lib, w3, mission_region=0)
    assert rec3.rotated == 1 and rec3.reason == REASON_FORCED


def test_ALG_46_step2_stay_below_two_chapters_whatever_the_draw(lib, world_factory):
    """ALG-46 step 2 / R-057-02: with a chapter counter of 0 or 1 the selection stays even when the draw would have rotated; at 2 it rotates on the same draw."""
    for chapters, rotates in ((0, 0), (1, 0), (2, 1)):
        w = world_factory(n_regions=2)
        _calm_home(lib, w)
        _lineage(lib, w, chapters=chapters)
        assert _select(lib, w, draws=[0.0, 0.95]).rotated == rotates, chapters


def test_ALG_46_step4_draw_below_p_rotates_normal_otherwise_stays(lib, world_factory):
    """ALG-46 step 4 / R-057-03, R-057-08: at counter 2 and D = 0, p_rotate = 0.8: draw 0.79 rotates with reason normal and a new lineage whose counter is 1; draw 0.81 stays."""
    w = world_factory(n_regions=2)
    _calm_home(lib, w)
    _lineage(lib, w, chapters=2)
    rec = _select(lib, w, draws=[0.79, 0.95])
    assert rec.rotated == 1 and rec.reason == REASON_NORMAL
    assert rec.chapters_in_lineage == 1 and rec.new_lineage_id != 1
    w2 = world_factory(n_regions=2)
    _calm_home(lib, w2)
    _lineage(lib, w2, chapters=2)
    assert _select(lib, w2, draws=[0.81, 0.95]).rotated == 0


def test_ALG_46_decay_raises_the_rotation_chance_with_chapters(lib, world_factory):
    """ALG-46 step 3 replacement / R-057-04: at counter 6 and D = 0, p_rotate = 0.8 + 0.2(1 - 0.75^4) = 0.936..., so draw 0.9 rotates at counter 6 but, at counter 2 (p = 0.8), stays."""
    p6 = _ref_decayed_p(0.8, 6)
    assert 0.9 < p6 < 0.95
    w = world_factory(n_regions=2)
    _calm_home(lib, w)
    _lineage(lib, w, chapters=6)
    assert _select(lib, w, draws=[0.9, 0.95]).rotated == 1
    w2 = world_factory(n_regions=2)
    _calm_home(lib, w2)
    _lineage(lib, w2, chapters=2)
    assert _select(lib, w2, draws=[0.9, 0.95]).rotated == 0


def test_ALG_46_crisis_veto_when_home_stability_below_20(lib, world_factory):
    """ALG-46 step 4 / R-057-05: the same rotating draw 0.5 stays when the lineage's home region (first history region) is in crisis, and rotates when it is calm; a calm mission region does not rescue a crisis home."""
    w = world_factory(n_regions=3)
    _calm_home(lib, w, 1)
    _crisis_home(lib, w, 0)  # lineage home = region 0
    _lineage(lib, w, chapters=3, home=0, members=((10, 1),))
    set_edge(lib, w, 0, 1)
    assert _select(lib, w, mission_region=1, draws=[0.5, 0.95]).rotated == 0
    w2 = world_factory(n_regions=3)
    _calm_home(lib, w2, 0)
    _crisis_home(lib, w2, 1)  # crisis elsewhere does not veto
    _lineage(lib, w2, chapters=3, home=0, members=((10, 1),))
    set_edge(lib, w2, 0, 1)
    assert _select(lib, w2, mission_region=1, draws=[0.5, 0.95]).rotated == 1


def test_ALG_46_stay_picks_first_living_member_within_two_hops_else_the_commander(lib, world_factory):
    """ALG-46 closing sentence / R-057-06: on a stay with members at 0 and 1 hops and a dead first member, the pick is a living member within 2 hops (lowest hop first)."""
    w = world_factory(n_regions=4)
    set_edge(lib, w, 0, 1)
    set_edge(lib, w, 1, 2)
    _calm_home(lib, w)
    _lineage(lib, w, chapters=1, members=((10, 0), (12, 2)))
    lib.om_character_kill(w, 10, tick=5)
    rec = _select(lib, w, mission_region=0)
    assert rec.rotated == 0 and rec.commander_id == 12


def test_ALG_46_the_delta_the_rule_names_reaches_the_live_selector(lib, world_factory):
    """ALG-46 step 4 / R-057-03: 'delta' is the home region's total field delta over the jump. After a real 50-tick jump in which the home region's four fields moved by D > 0, p_rotate is 0.8 + min(1, D/200)(-0.7) < 0.8, so a draw halfway between p and 0.8 must STAY. The live selector passes D = 0 (csrc/generational.c, om_character_selector_run_for_lineage: 'double delta = 0.0'), so it rotates."""
    w = world_factory(n_regions=3)
    set_edge(lib, w, 0, 1)
    set_edge(lib, w, 1, 2)
    # A region that is far from equilibrium moves a lot over 50 ticks; stability stays above the crisis line.
    set_region(lib, w, 0, tier=OMTier.HOME, military=95.0, economy=15.0, tension=5.0, population=95.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.FRONTIER, military=20.0, economy=40.0, tension=40.0, population=40.0, faction_id=0)
    set_region(lib, w, 2, tier=OMTier.FRONTIER, military=20.0, economy=40.0, tension=40.0, population=40.0, faction_id=0)
    _lineage(lib, w, chapters=2, home=0, members=((10, 0),))
    before = [lib.om_region_field(w, 0, f) for f in range(OMField.COUNT)]
    assert lib.om_time_jump_run(w, 50) in (0, 1)
    after = [lib.om_region_field(w, 0, f) for f in range(OMField.COUNT)]
    d = sum(abs(a - b) for a, b in zip(after, before))
    assert d > 20.0, f"fixture control: the home region must move over the jump (D={d})"
    p = _ref_base_p(d)
    draw = (p + MAX_P) / 2.0
    assert p < draw < MAX_P
    rec = _select(lib, w, mission_region=0, draws=[draw, 0.95])
    assert rec.rotated == 0, f"D={d:.1f} -> p_rotate={p:.3f}; draw {draw:.3f} must stay but the selector used p=0.8 and rotated"
