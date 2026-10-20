# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T5; defect D5); ledger FINDING-lab-d5; piece LAB-REV3-A
"""LAB-REV3-A, T5 (R8, D5) against the real engine (OM_LAB_SLOW=1; seconds a test): the dark-striker fight changes under the emitting knob.
The fights are the sweep's: `sweep.default_builds("s3_dark_striker", "play", sweep.smoke_layouts()["192"])`, `sweep.Applied` with the
`emitting` family's grid points at vision 0.125 and sight/seen (1.0, 1.5), (2.0, 3.0), (4.0, 6.0) (the three settings of the finding),
16 enemies, seeds 0 and 1, rows through `rows.fight_row`.

Measured on the lab tip (2026-10-20, this file's author, layout 192): the three settings give the same row at vision 0.125 (1633 ticks,
15:0) and at vision 0.25 (1669 ticks, 14:0), the finding's line. With the enemy groups (2 and 3) set to emit, the vision 0.125 rows
differ (1571, 1669, 1669 ticks): the control below builds that scene by hand.
If the play is deleted (the plan's other fix) the defect test passes as soon as the play is gone; see the fast half's docstring."""
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight as fight_mod, plays_space, rows as rows_mod, sweep  # noqa: E402
from scripts.skilllab.contract import Step  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")
PLAY, LAYOUT, SEEDS = "s3_dark_striker", "192", (0, 1)


def trio():
    pts = [p for p in sweep.grid("emitting") if p.settings["OM_TP_VISION_UP_1"] == 0.125]
    assert len(pts) == 3
    return pts


def rows(build, points):
    """{seed: [row of each point]}: the settings are compared at the same seed, never across seeds."""
    return {seed: [tuple(sorted(rows_mod.fight_row(fight_mod.fight(sweep.Applied(build, p)(sweep.SIZE, False), seed, False)).items()))
                   for p in points] for seed in SEEDS}


def moves(by_seed):
    """True when, at some seed, the rows of the three settings are not all the same."""
    return any(len(set(r)) > 1 for r in by_seed.values())


def enemy_emits(build):
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        side1 = [i for i, g in enumerate(setup.groups) if g.side == 1]
        return dataclasses.replace(setup, timeline=(Step.set_emission(0, False),) + tuple(Step.set_emission(i, True) for i in side1))
    wrapped.labels = build.labels
    return wrapped


@SLOW
def test_positive_control_when_the_enemy_emits_the_emitting_knob_changes_the_fight():
    """Green on the lab tip: the same scene with the enemy groups set to emit gives rows that are not all identical across the trio."""
    build = enemy_emits(sweep.default_builds(PLAY, "play", sweep.smoke_layouts()[LAYOUT]))
    assert moves(rows(build, trio()))


@SLOW
def test_t5_the_dark_striker_fight_changes_under_the_emitting_knob():
    """T5 (D5): the play as the registry builds it gives rows that are not all identical across the three emitting settings. Red today:
    one row per seed. Passes when the play is deleted."""
    if PLAY not in plays_space.PLAYS:
        return
    got = rows(sweep.default_builds(PLAY, "play", sweep.smoke_layouts()[LAYOUT]), trio())
    assert moves(got), "identical rows under sight 1.0, 2.0 and 4.0 at every seed: %s" % {s: len(set(r)) for s, r in got.items()}
