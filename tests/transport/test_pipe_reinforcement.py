"""Pipe-level reinforcement wiring tests (W-1).

Stage A (enemy wave unit count): HELD. Wave spawn is not implemented; wave size
is pending Q-124-02 (open in the ambiguity register). The pipe has no command to
inject forced RNG draws, so arrival cannot be deterministically triggered without
a seed-stable scenario that lands a wave within N steps -- not feasible until the
wave size is closed and unit spawn is wired.

Stage B (structure production): HELD. The pipe binary has no command that places
a structure in a live mission. om_structure_init / om_structure_set_owner are
ctypes-only entry points; the pipe session command set (set_seed, step,
mission_start, mission_begin, tactical_step, ...) has no analogue. Until a pipe
command is added for structure placement, this test cannot be exercised through
the transport layer without bypassing the pipe entirely.

Both tests are marked xfail-with-strict=False so the suite stays green and the
merge gate sees them as held rather than skipped.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


@pytest.mark.xfail(reason="HELD: wave unit spawn pending Q-124-02 (wave size open)", strict=False)
def test_enemy_unit_count_rises_after_wave_arrival():
    """After N tactical_step frames past a wave arrival tick the enemy unit
    count in the snapshot must have risen.

    HELD: wave size not defined (Q-124-02 open in ambiguity register). Wire
    om_unit_spawn in om_mission_check_external_reinforcements (or a post-check
    hook in om_macro_tick) once Q-124-02 closes and size is numbered in the
    header.
    """
    pytest.xfail("wave unit spawn not wired -- Q-124-02 open")


@pytest.mark.xfail(reason="HELD: pipe has no structure-placement command", strict=False)
def test_player_structure_adds_unit_within_timer():
    """A player-owned production structure adds a player unit within its
    production interval, visible as a new unit in the tactical frame.

    HELD: pipe/om_pipe.c has no 'place_structure' or equivalent command; the
    ctypes entry point om_structure_init / om_structure_set_owner is not exposed
    through the JSON wire protocol. Add a pipe command for structure placement
    before enabling this test.
    """
    pytest.xfail("pipe cannot place a structure -- no pipe command exists")
