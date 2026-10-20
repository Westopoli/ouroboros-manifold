# spec: docs/northstar/plans/skilllab-harness-spec.md clause 24 (cross-layer 16 v 16 fixture, side 0 one layer up); ledger FINDING-lab-vision-poscontrol (Architect ruling 2026-10-20, option (a)); piece LAB-VISION-CONTROL
"""LAB-VISION-CONTROL, the fast half (no engine): the vision family's positive control is ONE designated fight on a designated play,
`sweep.VISION_CONTROL_PLAY`, run the way `sweep.DAMAGE_CONTROL_PLAY` is run (Control.play set, whatever plays the run covers).

BUILDER CONTRACT these tests require (nothing else is pinned):
  - `scripts/skilllab/sweep.py` defines the module constant `VISION_CONTROL_PLAY`, a play name string (the tests' suggestion:
    "s3_vision_control"), next to `DAMAGE_CONTROL_PLAY`.
  - `scripts/skilllab/plays_space.py` registers that name in `PLAYS` (a PlayDraft with `anchors`, so `scenes.placed_scene` and
    `sweep.default_builds(VISION_CONTROL_PLAY, "play", features)` build it like any play).
  - Composition (clause 24: 16 v 16, side 0 one layer up): 16 units of side 0, all on layer 1; 16 units of side 1, all on layer 0, at
    the headcount 16 of the control; side 1 follows the sweep's enemy headcount and stays on layer 0. No same-layer pair exists.
    Every unit must be able to fire across one layer in both directions (reach one up and one down): measured 2026-10-20 on a scratch
    play of 16 Raiders a side (`plays_space._types("Raider")`, reach (1, 1)) behind `Anchors("defender", "behind_cover", "blob")`
    with the two sides one blob each: vision 0 reads 16 v 16 alive and (0.0, 0.0) firing unit-seconds in all 18 fights of the
    three smoke layouts; vision 1.0 fires on both sides in all 18. A Vanguard given reach (1, 1) did NOT shoot within the control's
    600 ticks on those layouts at vision 1.0, so it cannot be the control's unit (the integration file's vision-1.0 test goes red).
  - `sweep.controls("vision")["positive"]` keeps its one point (vision 0.0 on all four knobs), `check` = `_vision_zero_ok` (unchanged),
    `max_ticks` = CONTROL_MAX_TICKS, `reach` None, and gains `play = VISION_CONTROL_PLAY`.
  - The vision NULL control keeps `play = None` (it still runs on every play of the run).
The real-engine half is tests/skilllab/integration/test_vision_control_real.py (OM_LAB_SLOW=1)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays_space, sweep  # noqa: E402

V1, V2 = "OM_TP_VISION_UP_1", "OM_TP_VISION_UP_2"


def pairs(groups):
    """(cross-layer pair count, same-layer pair count) of unit pairs (one of side 0, one of side 1)."""
    cross = same = 0
    for a in (g for g in groups if g.side == 0):
        for b in (g for g in groups if g.side == 1):
            if a.layer == b.layer:
                same += a.count * b.count
            else:
                cross += a.count * b.count
    return cross, same


def sides(groups):
    return {s: (sum(g.count for g in groups if g.side == s), sorted({g.layer for g in groups if g.side == s})) for s in (0, 1)}


# ---- the control is designated -----------------------------------------------------------------------------------------------

def test_the_vision_positive_control_is_one_designated_fight_on_vision_control_play():
    """FINDING-lab-vision-poscontrol, spec clause 24: the control is a designated fight (Control.play), like the damage control."""
    name = sweep.VISION_CONTROL_PLAY
    assert isinstance(name, str) and name and name in plays_space.PLAYS
    c = sweep.controls("vision")["positive"]
    assert c.play == name


def test_the_vision_control_keeps_its_point_its_check_and_its_stop_tick():
    """Option (a) changes WHERE the control is fought, not what it asks: `_vision_zero_ok` unchanged, vision 0.0 on all four knobs,
    stops at CONTROL_MAX_TICKS (FINDING-lab-vision-poscontrol, clause 24)."""
    c = sweep.controls("vision")["positive"]
    assert c.check is sweep._vision_zero_ok and c.max_ticks == sweep.CONTROL_MAX_TICKS and c.reach is None
    assert len(c.points) == 1 and c.points[0].kind == "control_positive" and c.points[0].value == 0.0
    assert set(c.points[0].settings.values()) == {0.0} and len(c.points[0].settings) == 4


def test_the_vision_null_control_still_runs_on_every_play():
    """The designation is for the POSITIVE control only; the null control keeps play None (FINDING-lab-vision-poscontrol)."""
    assert sweep.controls("vision")["null"].play is None


# ---- the designated play is all cross-layer ----------------------------------------------------------------------------------

def test_vision_control_play_is_16_v_16_with_side_0_on_layer_1_and_side_1_on_layer_0():
    """Clause 24: 16 v 16, side 0 one layer up; no same-layer pair exists (FINDING-lab-vision-poscontrol: a same-layer pair sees and
    fires at vision 0, fog.c:719 blinds cross-layer pairs only)."""
    groups = plays_space.PLAYS[sweep.VISION_CONTROL_PLAY].setup_fn().groups
    assert sides(groups) == {0: (16, [1]), 1: (16, [0])}
    cross, same = pairs(groups)
    assert same == 0 and cross == 16 * 16


@pytest.mark.parametrize("heads", [8, 16, 48])
def test_vision_control_play_as_the_sweep_builds_it_is_all_cross_layer_on_every_smoke_layout(heads):
    """FINDING-lab-vision-poscontrol, spec clause 24. The built scene (sweep.default_builds, the one the control is fought on) keeps
    side 0 on layer 1 and side 1 on layer 0, and the build is not refused (prefight ok) at the headcounts the sweep's refusal check
    builds (8 and 48) nor at the control's 16. No swap case: scenes._groups_and_timeline always passes swap False to scan_build, so the
    swap flag never changes the groups."""
    for layout, features in sweep.smoke_layouts().items():
        build = sweep.default_builds(sweep.VISION_CONTROL_PLAY, "play", features)
        setup = build(heads, False)
        assert build.labels.get("prefight") in (None, "ok"), (layout, heads, build.labels.get("prefight"))
        got = sides(setup.groups)
        assert got[0] == (16, [1]) and got[1] == (heads, [0]), (layout, heads, got)
        assert pairs(setup.groups)[1] == 0, (layout, heads)


@pytest.mark.parametrize("heads", [16, 48])
def test_vision_control_play_units_are_all_raiders_with_reach_one_up_and_one_down(heads):
    """FINDING-lab-vision-poscontrol, spec clause 24 as ruled by the Architect 2026-10-20: the fixture is 16 Raiders a side (Raider
    reach (1, 1), R-164-01). Read from the built scene, not the play's name: every group's unit type, on both sides, resolves to base
    Raider (the Setup.unit_types entry's "base", else the unit's own name) with reach (1, 1) (the entry's "reach", else
    plays_space._REACH). Fast tier trap for the unit-type choice: a Vanguard given reach (1, 1) does not fire within the control's 600
    ticks at vision 1.0 (the slow vision-1.0 test also catches it)."""
    for layout, features in sweep.smoke_layouts().items():
        setup = sweep.default_builds(sweep.VISION_CONTROL_PLAY, "play", features)(heads, False)
        assert setup.groups, layout
        for g in setup.groups:
            entry = setup.unit_types.get(g.unit, {})
            base = entry.get("base", g.unit)
            assert base == "Raider", (layout, g.side, g.unit, base)
            assert tuple(entry.get("reach", plays_space._REACH.get(base))) == (1, 1), (layout, g.side, g.unit, entry)


@pytest.mark.parametrize("play", sweep.PLAYS_BY_FAMILY["vision"])
def test_positive_control_the_structural_check_flags_the_mixed_sweep_plays(play):
    """Positive control of the two structural tests above: the pair counter finds same-layer pairs in the real mixed sweep plays
    (side 1 all on layer 0 and 8 side-0 Vanguards on layer 0), which is exactly why the control cannot run on them."""
    groups = plays_space.PLAYS[play].setup_fn().groups
    cross, same = pairs(groups)
    assert same > 0 and cross > 0, (play, cross, same)
