# Rule pins: R-082-01@7030c1, R-164-01@511d57
"""Phase C step G5, the reach calls (E-01 S-164, R-164-01; contract pp_contract.md section 6).

om_roster_set_reach(w, type, up, down): 0 ok, -1 for an unknown type. om_unit_profile_reach(w, type,
&up, &down): writes the type's reach, either pointer may be NULL, -1 for an unknown type. The
built-in roster defaults to 0 up, 0 down.

Today both are inert stubs in csrc/tactical_move.c: set_reach returns 0 for every type (unknown
included) and stores nothing; profile_reach returns 0 for every type and WRITES NOTHING (the 99
sentinel the helper presets stays 99). So the default, the round trip and the unknown-type returns
all fail today for those reasons.
"""
import ctypes

import pytest

from test_PP_C_g5_support import (
    BASTION, BOMBARD, BUILTIN_COMBAT, INTERCEPTOR, RAIDER, VANGUARD, WARDEN, read_reach, set_reach,
)

UNKNOWN_TYPES = (99, -1)

# TD-VG-T-1: the API test splits in two. This half is the bare world, no mission started; the other half
# (test_R_164_01_a_world_after_the_games_own_mission_start_...) reads a world after the game's own start.
# Rule pin text, R-164-01: "Line its own layer, Raider one layer either way, Interceptor two up and one down,
# Siege two down". Line = Vanguard, Warden; Siege = Bombard, Bastion (E-11 R-082-01 table). (rc, up, down).
BIBLE_REACH = {
    RAIDER: (0, 1, 1), INTERCEPTOR: (0, 2, 1), VANGUARD: (0, 0, 0), WARDEN: (0, 0, 0),
    BOMBARD: (0, 0, 2), BASTION: (0, 0, 2),
}
FEATURES = [1, 2, 3, 4, 5, 6, 7]
# Strict xfail until VG-T-REACH-WIRE lands (FINDING-reach-not-wired): the four types the table gives a non-zero reach.
# The wiring turns them into XPASS(strict) failures and removes the mark. Vanguard and Warden (0, 0) are green today.
XFAIL = pytest.mark.xfail(strict=True, reason="VG-T-REACH-WIRE: R-164-01 reach not wired, FINDING-reach-not-wired")
STARTED_WORLD_TYPES = [
    pytest.param(t, marks=XFAIL) if t in (RAIDER, INTERCEPTOR, BOMBARD, BASTION) else t for t in BUILTIN_COMBAT
]


@pytest.mark.parametrize("utype", BUILTIN_COMBAT)
def test_R_164_01_built_in_default_reach_is_zero_up_zero_down(lib, world_factory, utype):
    """R-164-01 / brief G5: 'The built-in roster's default reach is 0 up, 0 down.' Each of the six
    built-in combat types reads (0, 0) in a bare world: one made with om_world_new and no mission started
    (the half of the TD-VG-T-1 split that keeps the default; the bible table is read in a started world
    below). Green after the table is wired too: a bare world is not the game's start."""
    w = world_factory(n_regions=1)
    assert read_reach(lib, w, utype) == (0, 0, 0)


def _started_world(lib, world_factory):
    """PATH: csim, the same exported calls in the same order as the pipe's set_seed (new_campaign false),
    step 10, mission_start, mission_begin (csrc/pipe/om_pipe.c handle_set_seed, handle_mission_start,
    handle_mission_begin), then one tactical step. Same recipe as tests/transport/test_pipe_tactical_world.py,
    which checks it against the pipe's own world. The pipe variant of this claim is
    tests/transport/test_pipe_reach_cross_layer.py (the pipe has no reach readout, so that test reads the fight)."""
    w = world_factory(n_regions=80, seed=1)
    for f in FEATURES:
        lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)
    lib.om_events_load_launch(w)
    lib.om_mission_load_launch_library(w)
    for _ in range(10):
        lib.om_world_step(w)
    lib.om_mission_start(w, 0)
    for ri in range(lib.om_region_count(w)):
        lib.om_mission_refresh_context(w, ri)
    for _ in range(5):
        if lib.om_mission_generator_chosen_archetype(w) >= 0:
            break
        lib.om_time_jump_run(w, 20)
        for ri in range(lib.om_region_count(w)):
            lib.om_mission_refresh_context(w, ri)
    archetype = lib.om_mission_generator_chosen_archetype(w)
    region = lib.om_mission_generator_chosen_region(w)
    if archetype < 0:
        region, archetype = 0, 0
    lib.om_mission_setup(w, region, archetype, 0)
    lib.om_mission_build_objectives(w, archetype)
    lib.om_chapter_set_phase(w, 2)  # GEN_PHASE_MISSION (csrc/generational.c), not exported by the header
    lib.om_mission_begin(w)
    lib.om_tactical_step(w)
    return w


@pytest.mark.parametrize("utype", STARTED_WORLD_TYPES)
def test_R_164_01_a_world_after_the_games_own_mission_start_reads_the_bible_reach_table(lib, world_factory, utype):
    """R-164-01: 'Given a unit type, When its reach is read, Then it names the layer offsets it can fire at: its own
    layer, and how many layers up and how many down: Line its own layer, Raider one layer either way, Interceptor two up
    and one down, Siege two down.' PATH: csim, a world after the game's own start (see `_started_world`); no setter is
    called by the test. Positive control inside the test: the started world really holds a mission (units exist), so
    a (0, 0) read cannot come from a world that never started. RED today: every type reads (0, 0), because no game path
    sets reach (D1 of docs/northstar/plans/drift_audits/2026-10-19-positioning-green-tests.md)."""
    w = _started_world(lib, world_factory)
    assert lib.om_unit_count(w) > 0, "control: the mission has units, so the world did start"
    assert read_reach(lib, w, utype) == BIBLE_REACH[utype]


@pytest.mark.parametrize("up,down", [(1, 0), (0, 1), (2, 1), (0, 2), (4, 4), (3, 0)])
def test_R_164_01_reach_reads_back_what_was_set(lib, world_factory, up, down):
    """R-164-01: the reach a type was given is the reach read. Fails today: nothing is stored."""
    w = world_factory(n_regions=1)
    assert set_reach(lib, w, RAIDER, up, down) == 0
    assert read_reach(lib, w, RAIDER) == (0, up, down)


def test_R_164_01_a_second_call_replaces_the_first_and_other_types_are_untouched(lib, world_factory):
    """Setting is by type and replaces: Raider (2, 1) then (0, 3) reads (0, 3); the Vanguard, never set,
    still reads (0, 0). Positive control for the isolation half: the Vanguard read is the default
    read of the first test, so a store that wrote every type would show here."""
    w = world_factory(n_regions=1)
    assert set_reach(lib, w, RAIDER, 2, 1) == 0
    assert read_reach(lib, w, RAIDER) == (0, 2, 1)
    assert set_reach(lib, w, RAIDER, 0, 3) == 0
    assert read_reach(lib, w, RAIDER) == (0, 0, 3)
    assert read_reach(lib, w, VANGUARD) == (0, 0, 0)


@pytest.mark.parametrize("utype", UNKNOWN_TYPES)
def test_R_164_01_unknown_type_is_refused_and_changes_nothing(lib, world_factory, utype):
    """Contract: -1 for an unknown type, from both calls. A refused set changes nothing: a built-in
    type set first (positive control) keeps its reach. Fails today: both stubs return 0."""
    w = world_factory(n_regions=1)
    assert set_reach(lib, w, RAIDER, 1, 1) == 0
    assert read_reach(lib, w, RAIDER) == (0, 1, 1), "control: a known type is stored"
    assert set_reach(lib, w, utype, 2, 2) == -1
    rc, up, down = read_reach(lib, w, utype)
    assert (rc, up, down) == (-1, 99, 99), "an unknown type reads -1 and writes nothing"
    assert read_reach(lib, w, RAIDER) == (0, 1, 1)


def test_R_164_01_either_output_pointer_may_be_null(lib, world_factory):
    """Contract: 'either may be NULL'. A NULL down still writes up, a NULL up still writes down, both
    NULL is a valid 0. Fails today: the stub writes nothing."""
    w = world_factory(n_regions=1)
    assert set_reach(lib, w, VANGUARD, 3, 2) == 0
    up = ctypes.c_uint32(99)
    down = ctypes.c_uint32(99)
    assert lib.om_unit_profile_reach(w, VANGUARD, ctypes.byref(up), None) == 0 and up.value == 3
    assert lib.om_unit_profile_reach(w, VANGUARD, None, ctypes.byref(down)) == 0 and down.value == 2
    assert lib.om_unit_profile_reach(w, VANGUARD, None, None) == 0


def test_R_164_01_a_registered_custom_type_takes_a_reach_and_an_unregistered_one_does_not(lib, world_factory):
    """Contract: -1 only for an unknown type, so a custom type registered with
    om_roster_register_custom_unit is known. Type 50 registered: set (1, 2) reads back; type 51 never
    registered: refused. Fails today: the stub accepts 51 and stores nothing for 50."""
    w = world_factory(n_regions=1)
    assert lib.om_roster_register_custom_unit(w, 50, 0, b"seer", 100.0, 5.0, 1.0, 200.0, 50.0, 500.0, 1.0, 0.0, 0) == 0
    assert set_reach(lib, w, 50, 1, 2) == 0
    assert read_reach(lib, w, 50) == (0, 1, 2)
    assert set_reach(lib, w, 51, 1, 2) == -1


def test_R_164_01_reach_belongs_to_the_world_it_was_set_in(lib, world_factory):
    """The calls take a world, as every setting does (A133 Q-C4: 'a new world starts at the defaults').
    Raider (2, 2) in world A leaves world B at (0, 0). READING of the signature, not a quoted rule:
    the report asks whether reach may live in a process-wide table. Fails today: nothing is stored."""
    a = world_factory(n_regions=1)
    b = world_factory(n_regions=1)
    assert set_reach(lib, a, RAIDER, 2, 2) == 0
    assert read_reach(lib, a, RAIDER) == (0, 2, 2), "control: world A holds it"
    assert read_reach(lib, b, RAIDER) == (0, 0, 0)
