"""Pinned regression for R-055-02 (docs/bible/epics/E-08-generational-play.md,
S-055): "Given a mission is running, When any tactical tick passes, Then no
strategic tick runs; the strategic sim is stopped for the mission's
duration." Implemented in om_world_step (csrc/sim.c): while
om_chapter_current_phase(w) reports the mission phase, om_world_step runs
only the tactical step (when OM_FEAT_TACTICAL is on) and returns without
advancing w->tick, without any strategic step, and without touching any
checksum-relevant strategic state. Every other phase is unaffected.
"""
from conftest import OMField, OMFeature, OMTier, set_owner, set_region


class OMChapterPhase:
    BRIEFING = 0
    RECON = 1
    MISSION = 2
    OUTCOME_RESOLUTION = 3
    TIME_JUMP = 4
    CHARACTER_SELECTION = 5
    NEXT_BRIEFING = 6


def _setup_region(lib, w):
    set_region(lib, w, 0, tier=OMTier.HOME, military=30.0, economy=40.0,
               tension=20.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)


def test_R_055_02_no_strategic_tick_runs_with_tactical_map_loaded(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup_region(lib, w)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    # A tactical map is "loaded": at least one unit exists so om_tactical_step
    # is not itself a no-op (csrc/unit.c om_tactical_step: n_units == 0 is a
    # no-op that never advances the tactical tick).
    lib.om_unit_spawn(w, 0, 0, 0.0, 0.0, 0)

    lib.om_chapter_start(w, 1)
    lib.om_chapter_set_phase(w, OMChapterPhase.MISSION)

    strat_before = lib.om_world_strategic_tick(w)
    tac_before = lib.om_tactical_tick(w)
    military_before = lib.om_region_field(w, 0, OMField.MILITARY)
    economy_before = lib.om_region_field(w, 0, OMField.ECONOMY)
    tension_before = lib.om_region_field(w, 0, OMField.TENSION)
    population_before = lib.om_region_field(w, 0, OMField.POPULATION)

    for _ in range(3):
        lib.om_world_step(w)

    assert lib.om_chapter_current_phase(w) == OMChapterPhase.MISSION

    # No strategic tick ran: the strategic counter did not move.
    assert lib.om_world_strategic_tick(w) == strat_before

    # No strategic state changed either -- the region this test's DRIFT/
    # FACTIONS/FRICTION/ADMIN_REVOLTS features would otherwise touch is
    # untouched while the mission holds the strategic sim stopped.
    assert lib.om_region_field(w, 0, OMField.MILITARY) == military_before
    assert lib.om_region_field(w, 0, OMField.ECONOMY) == economy_before
    assert lib.om_region_field(w, 0, OMField.TENSION) == tension_before
    assert lib.om_region_field(w, 0, OMField.POPULATION) == population_before

    # The tactical tick did advance -- three om_world_step calls, three
    # tactical steps, since a tactical map (a spawned unit) exists.
    assert lib.om_tactical_tick(w) == tac_before + 3


def test_R_055_02_no_strategic_tick_is_clean_noop_without_tactical_map(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup_region(lib, w)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    # No unit spawned: no tactical map, so om_tactical_step's own no-op path
    # applies (csrc/unit.c). The mission-phase gate must still be a clean
    # no-op: the strategic tick holds, and the (never-advancing) tactical
    # tick holds too.

    lib.om_chapter_start(w, 1)
    lib.om_chapter_set_phase(w, OMChapterPhase.MISSION)

    strat_before = lib.om_world_strategic_tick(w)
    tac_before = lib.om_tactical_tick(w)
    military_before = lib.om_region_field(w, 0, OMField.MILITARY)

    for _ in range(3):
        returned = lib.om_world_step(w)
        assert returned == strat_before

    assert lib.om_world_strategic_tick(w) == strat_before
    assert lib.om_tactical_tick(w) == tac_before
    assert lib.om_region_field(w, 0, OMField.MILITARY) == military_before


def test_control_strategic_tick_advances_outside_mission_phase(lib, world_factory):
    """Positive control: outside the mission phase, om_world_step behaves as
    today -- the strategic tick advances and the strategic sim runs. Proves
    the gate above is not a global no-op / dead branch."""
    w = world_factory(n_regions=1)
    _setup_region(lib, w)

    lib.om_chapter_start(w, 1)
    assert lib.om_chapter_current_phase(w) == OMChapterPhase.BRIEFING

    strat_before = lib.om_world_strategic_tick(w)
    military_before = lib.om_region_field(w, 0, OMField.MILITARY)
    economy_before = lib.om_region_field(w, 0, OMField.ECONOMY)
    tension_before = lib.om_region_field(w, 0, OMField.TENSION)
    population_before = lib.om_region_field(w, 0, OMField.POPULATION)

    for _ in range(3):
        lib.om_world_step(w)

    assert lib.om_world_strategic_tick(w) == strat_before + 3

    after = (
        lib.om_region_field(w, 0, OMField.MILITARY),
        lib.om_region_field(w, 0, OMField.ECONOMY),
        lib.om_region_field(w, 0, OMField.TENSION),
        lib.om_region_field(w, 0, OMField.POPULATION),
    )
    before = (military_before, economy_before, tension_before, population_before)
    assert after != before, "strategic drift must actually run outside the mission phase"
