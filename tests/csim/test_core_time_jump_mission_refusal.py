"""Pinned regression for R-055-02 (docs/bible/epics/E-08-generational-structure.md,
S-055): "Given a mission is running, When any tactical tick passes, Then no
strategic tick runs; the strategic sim is stopped for the mission's
duration." A time jump is the only entry point that advances the strategic
tick outside om_world_step's own per-tick call, so om_time_jump_run
(csrc/generational.c) must itself refuse to run while the chapter is in the
mission phase: no tick advances, and the refusal uses this function's
existing error convention (it returns 1 on the !w / !gs guard above; a
mission-phase refusal returns the same 1, never partially running).
"""
class OMChapterPhase:
    BRIEFING = 0
    RECON = 1
    MISSION = 2
    OUTCOME_RESOLUTION = 3
    TIME_JUMP = 4
    CHARACTER_SELECTION = 5
    NEXT_BRIEFING = 6


def test_R_055_02_time_jump_refused_during_mission_phase(lib, world_factory):
    w = world_factory(n_regions=2)
    lib.om_chapter_start(w, 1)
    lib.om_chapter_set_phase(w, OMChapterPhase.MISSION)

    strat_before = lib.om_world_strategic_tick(w)
    start_tick_before = lib.om_time_jump_start_tick(w)

    ret = lib.om_time_jump_run(w, 10)

    assert ret == 1
    assert lib.om_chapter_current_phase(w) == OMChapterPhase.MISSION
    assert lib.om_world_strategic_tick(w) == strat_before
    assert lib.om_time_jump_start_tick(w) == start_tick_before


def test_control_time_jump_runs_outside_mission_phase(lib, world_factory):
    """Positive control: outside the mission phase, the same jump call runs
    and the tick advances by exactly n_ticks. Proves the refusal above is
    not a global no-op / dead branch."""
    w = world_factory(n_regions=2)
    lib.om_chapter_start(w, 1)
    assert lib.om_chapter_current_phase(w) == OMChapterPhase.BRIEFING

    strat_before = lib.om_world_strategic_tick(w)

    ret = lib.om_time_jump_run(w, 10)

    assert ret == 0
    assert lib.om_world_strategic_tick(w) == strat_before + 10
