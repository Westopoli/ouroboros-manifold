"""W-1b pipe test: structure production adds player-faction unit within timer.

HELD: the pipe binary has no command that places a structure in a live mission.
om_structure_init / om_structure_set_owner are ctypes-only entry points; the
pipe session command set (set_seed, step, mission_start, mission_begin,
tactical_step, ...) has no analogue. Adding a pipe command for structure
placement requires a docs/architecture.md update (session command v1.1 shape)
before implementation. Until then this test is xfail(strict=True).

Verified: pipe/om_pipe.c command dispatch (and pipe/ouroboros_pipe_dbg with
-DOM_DEBUG_INJECT) expose no 'place_structure' or equivalent command; the debug
injection flag adds om_debug_inject for unit-count manipulation only, not
structure placement.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


@pytest.mark.xfail(
    reason=(
        "HELD: pipe has no structure-placement command. om_structure_init / "
        "om_structure_set_owner are ctypes-only; the JSON wire protocol has no "
        "analogue. A new pipe command requires a docs/architecture.md session "
        "command shape update before implementation."
    ),
    strict=True,
)
def test_player_structure_adds_unit_within_timer():
    """A player-owned production structure adds a player-faction unit within
    its production interval, visible as a new unit in the tactical frame.

    HELD: pipe/om_pipe.c has no 'place_structure' or equivalent command.
    Enable once a pipe command is documented in docs/architecture.md and wired.
    """
    pytest.xfail("pipe cannot place a structure -- no pipe command exists")
