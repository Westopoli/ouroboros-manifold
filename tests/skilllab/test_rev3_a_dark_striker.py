# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T5; defect D5); ledger FINDING-lab-d5; piece LAB-REV3-A
"""LAB-REV3-A, T5 (R8, D5): `s3_dark_striker` is not a no-op. Its timeline is `Step.set_emission(0, False), Step.set_emission(1, False)`:
a group index is an index into `Setup.groups`, groups 0 and 1 are BOTH side 0 (the Raiders and the Vanguards), and silent is the engine
default, so nobody ever emits and the family `emitting` (sweep.PLAYS_BY_FAMILY["emitting"] == ("s3_dark_striker",)) has nothing to act on.
Fast half, no fight: the play's own Setup. The fight half is tests/skilllab/integration/test_rev3_a_dark_striker_real.py.

The plan allows two fixes (R8): "the dark-striker play makes the enemy emit at the knob's values, or is deleted with its row". Both are
accepted here:
  - the play stays: at least one `set_emission` step with on=True addresses a group of side 1 (the enemy), and side 0 is not set to emit
    by any step; or
  - the play is deleted: "s3_dark_striker" is in neither plays_space.PLAYS nor any value of sweep.PLAYS_BY_FAMILY, and the emitting family
    names no play that cannot respond (it is then the Architect's/B's to give the family another play; the family list may be empty).
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


def test_t5_the_dark_striker_makes_the_enemy_emit_or_the_play_is_gone():
    """T5 (D5): some step turns emission ON for a side 1 group. Red today: both steps address side 0 groups and turn emission off."""
    if PLAY not in plays_space.PLAYS:
        assert not any(PLAY in plays for plays in sweep.PLAYS_BY_FAMILY.values())
        return
    steps = emission_steps(plays_space.PLAYS[PLAY].setup_fn())
    assert [(s.on, side) for s, side in steps if s.on and side == 1], "emission steps (on, side): %s" % [(s.on, side) for s, side in steps]


def test_t5_side_0_does_not_emit():
    """T5 (D5): the striker stays dark. Holds today, and must hold after the fix: no step turns emission on for side 0."""
    if PLAY not in plays_space.PLAYS:
        return
    steps = emission_steps(plays_space.PLAYS[PLAY].setup_fn())
    assert not [1 for s, side in steps if s.on and side == 0]
