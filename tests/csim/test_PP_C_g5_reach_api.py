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

from test_PP_C_g5_support import BUILTIN_COMBAT, RAIDER, VANGUARD, read_reach, set_reach

UNKNOWN_TYPES = (99, -1)


@pytest.mark.parametrize("utype", BUILTIN_COMBAT)
def test_R_164_01_built_in_default_reach_is_zero_up_zero_down(lib, world_factory, utype):
    """R-164-01 / brief G5: 'The built-in roster's default reach is 0 up, 0 down.' Each of the six
    built-in combat types reads (0, 0) in a fresh world. Fails today: the stub writes nothing."""
    w = world_factory(n_regions=1)
    assert read_reach(lib, w, utype) == (0, 0, 0)


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
