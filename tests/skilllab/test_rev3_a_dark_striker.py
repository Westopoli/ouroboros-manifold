# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T5; defect D5); ledger FINDING-lab-d5; piece LAB-REV3-A
"""LAB-REV3-A, T5 (R8, D5): `s3_dark_striker` is not a no-op. Its timeline is `Step.set_emission(0, False), Step.set_emission(1, False)`:
a group index is an index into `Setup.groups`, groups 0 and 1 are BOTH side 0 (the Raiders and the Vanguards), and silent is the engine
default, so nobody ever emits and the family `emitting` (sweep.PLAYS_BY_FAMILY["emitting"] == ("s3_dark_striker",)) has nothing to act on.
Fast half, no fight: the play's own Setup. The fight half is tests/skilllab/integration/test_rev3_a_dark_striker_real.py.

Architect ruling 2026-10-20 (plan T5): the play STAYS; the D5 fix makes the enemy emit at the emitting family's grid values (the family
sets the multipliers; the play turns the enemy's emission on). Deleting the play is no longer accepted, so a deleted play fails here.
The fast checks: the play is in `plays_space.PLAYS` and in `sweep.PLAYS_BY_FAMILY["emitting"]`; at least one `set_emission` step with on=True
addresses a group of side 1; no step turns side 0 on (the striker stays dark). `test_plays_space.py::test_dark_striker_side_0_goes_silent_at_tick_0_
and_the_naive_side_does_not` and `test_scenes_mix.py::test_placed_dark_striker_keeps_its_silent_steps_on_side_0` are the existing tests the
ruler retires or rewrites under TD rows; this file does not touch them.
BUILDER CONTRACT: nothing is named; the Setup's groups and timeline are read."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays_space, sweep  # noqa: E402

PLAY = "s3_dark_striker"


def emission_steps(setup):
    return [(s, setup.groups[s.group].side) for s in setup.timeline if s.order == "set_emission"]


def test_positive_control_the_ping_play_has_a_working_timeline_step_on_its_own_side():
    """Green on the lab tip: a play whose step addresses a group of side 0 on purpose reads as side 0 through the same helper."""
    setup = plays_space.PLAYS["s3_ping_then_commit"].setup_fn()
    ping = [s for s in setup.timeline if s.order == "ping"]
    assert ping and setup.groups[ping[0].group].side == 0


def test_t5_the_dark_striker_stays_in_the_registry_and_the_emitting_family():
    """T5 (ruling): the play is kept. Green on the lab tip, red if the builder deletes it."""
    assert PLAY in plays_space.PLAYS and PLAY in sweep.PLAYS_BY_FAMILY["emitting"]


def test_t5_the_dark_striker_makes_the_enemy_emit():
    """T5 (D5): some step turns emission ON for a side 1 group. Red today: both steps address side 0 groups and turn emission off."""
    steps = emission_steps(plays_space.PLAYS[PLAY].setup_fn())
    assert [(s.on, side) for s, side in steps if s.on and side == 1], "emission steps (on, side): %s" % [(s.on, side) for s, side in steps]


def test_t5_side_0_does_not_emit():
    """T5 (D5): the striker stays dark. Holds today, and must hold after the fix: no step turns emission on for side 0."""
    steps = emission_steps(plays_space.PLAYS[PLAY].setup_fn())
    assert not [1 for s, side in steps if s.on and side == 0]
