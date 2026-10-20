# spec: docs/northstar/plans/skilllab-harness-spec.md clause 24 (cross-layer 16 v 16 fixture, side 0 one layer up); ledger FINDING-lab-vision-poscontrol (Architect ruling 2026-10-20, option (a)); piece LAB-VISION-CONTROL
"""LAB-VISION-CONTROL against the real engine (OM_LAB_SLOW=1; a few seconds a test): the vision family's positive control, run on the
designated play `sweep.VISION_CONTROL_PLAY`, built exactly as the sweep builds it (`sweep.default_builds`, `sweep.Applied`, the three
`sweep.smoke_layouts()`, REPLICATES = 3 seeds both orders = 6 fights a layout, CONTROL_MAX_TICKS = 600).

The builder contract is in the docstring of tests/skilllab/test_vision_control.py.

Red on the lab tip 126add1f: `sweep.VISION_CONTROL_PLAY` does not exist and the control (Control.play None) runs on the mixed sweep
plays (side 0 has 8 Vanguards on layer 0, the same layer as all of side 1), where the same-layer Vanguards see and fire at vision 0
(FINDING-lab-vision-poscontrol: all 12 control_positive rows of the vision sweep show shots).

Why this is not a pass by construction (option (b), counting only the cross-layer pair in a mixed scene, was rejected): the check is
unchanged and reads the whole fight. The same designated scene at vision 1.0 fires on both sides in every fight (the control's own
positive control), a single vision knob left at 1.0 fires (the detector discriminates), and the real mixed plays at vision 0 still FAIL
the check (so a scene that cannot be blinded is caught, not excused)."""
import csv
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import scan as scan_mod, sweep  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")
KNOBS = ("OM_TP_VISION_UP_1", "OM_TP_VISION_DOWN_1", "OM_TP_VISION_UP_2", "OM_TP_VISION_DOWN_2")
FIRST = "81"        # the first smoke layout: the discrimination cases run on it alone
MIXED_LAYOUT = "192"    # the only smoke layout the mixed sweep plays are not refused on (81 and 78 read no_fit), so the finding's 12 rows are all here


def fights(play, settings, layout):
    """The six fights (3 seeds, both orders) of `play` at `settings` on a smoke layout, as the control fights them."""
    point = sweep.Point("vision", KNOBS[0], settings[KNOBS[0]], settings, {}, "control_positive", "vision test")
    build = sweep.default_builds(play, "play", sweep.smoke_layouts()[layout])
    assert sweep._refusal({"play": build}) is None
    return scan_mod.cell(sweep.Applied(build, point, sweep.CONTROL_MAX_TICKS), sweep.SIZE, sweep.REPLICATES).fights


def at(**knobs):
    return {k: knobs.get(k, 0.0) for k in KNOBS}


@pytest.fixture(scope="module")
def control_run(tmp_path_factory):
    """The vision family run with no sweep plays: only the designated-play controls run (as the sweep runs the damage control)."""
    out = tmp_path_factory.mktemp("vision_control")
    entry = sweep.run_family("vision", out, plays=())
    with open(out / "sweep_vision.csv", newline="") as fh:
        return entry, list(csv.DictReader(fh))


# ---- (1) the control on the real scene at vision 0.0 is ok --------------------------------------------------------------------

@SLOW
def test_the_vision_control_on_the_real_cross_layer_scene_at_vision_zero_is_ok(control_run):
    """FINDING-lab-vision-poscontrol, clause 24 (test 1): sweep.controls("vision")["positive"] is fought on VISION_CONTROL_PLAY and its
    verdict is True (not None: it ran; not False: it saw no shot and no loss)."""
    entry, _rows = control_run
    assert sweep.controls("vision")["positive"].play == sweep.VISION_CONTROL_PLAY
    assert entry["controls"]["positive"]["play"] == sweep.VISION_CONTROL_PLAY
    assert entry["controls"]["positive"]["ok"] is True


@SLOW
def test_the_control_rows_are_on_the_designated_play_on_every_smoke_layout_and_show_no_shot(control_run):
    """FINDING-lab-vision-poscontrol (test 1, the rows): kind control_positive, play VISION_CONTROL_PLAY, the three smoke layouts,
    6 fights each, 16 v 16 alive, firing unit-seconds exactly 0 on both sides (the 12 rows of the finding all showed shots)."""
    _entry, rows = control_run
    ctl = [r for r in rows if r["kind"] == "control_positive"]
    assert {r["play"] for r in ctl} == {sweep.VISION_CONTROL_PLAY}
    assert sorted({r["layout"] for r in ctl}) == sorted(sweep.SMOKE_LAYOUTS) and len(ctl) == 3 * 2 * sweep.REPLICATES
    assert {(r["survivors_0"], r["survivors_1"], r["heads_0"], r["heads_1"]) for r in ctl} == {("16", "16", "16", "16")}
    assert {(float(r["firing_unit_seconds_0"]), float(r["firing_unit_seconds_1"])) for r in ctl} == {(0.0, 0.0)}


# ---- (2) the same scene at vision 1.0 fires ------------------------------------------------------------------------------------

@SLOW
@pytest.mark.parametrize("layout", sorted(sweep.SMOKE_LAYOUTS))
def test_the_same_scene_at_vision_one_fires_on_both_sides_in_every_fight(layout):
    """Test 2, the control's own positive control (clause 24: vision 0.5 reads (16, 16) on the cross-layer fixture): all four vision
    knobs at 1.0 on VISION_CONTROL_PLAY, every fight has firing unit-seconds above 0 on BOTH sides (measured 2026-10-20: 8 to 138 a
    side on the three layouts, 16 Raiders a side), and `_vision_zero_ok` reads False."""
    got = fights(sweep.VISION_CONTROL_PLAY, at(**{k: 1.0 for k in KNOBS}), layout)
    assert len(got) == 2 * sweep.REPLICATES
    assert all(f.firing_unit_seconds[0] > 0 and f.firing_unit_seconds[1] > 0 for f in got), [f.firing_unit_seconds for f in got]
    assert sweep._vision_zero_ok([got]) is False


# ---- the detector discriminates; it does not pass by construction -------------------------------------------------------------

@SLOW
@pytest.mark.parametrize("knob,firing_side", [("OM_TP_VISION_UP_1", 1), ("OM_TP_VISION_DOWN_1", 0)])
def test_a_vision_knob_left_at_one_on_the_cross_layer_scene_fails_the_check(knob, firing_side):
    """Negative control: vision 0 on three knobs and 1.0 on `knob` (UP_1: the side below sees up; DOWN_1: the side above sees down).
    The side that sees fires, so `_vision_zero_ok` reads False. A control that read True here would pass whatever the knobs do."""
    got = fights(sweep.VISION_CONTROL_PLAY, at(**{knob: 1.0}), FIRST)
    assert any(f.firing_unit_seconds[firing_side] > 0 for f in got), [f.firing_unit_seconds for f in got]
    assert sweep._vision_zero_ok([got]) is False


@SLOW
@pytest.mark.parametrize("play", sweep.PLAYS_BY_FAMILY["vision"])
def test_the_check_still_fails_on_the_mixed_sweep_plays_at_vision_zero(play):
    """FINDING-lab-vision-poscontrol: the real mixed plays (same-layer Vanguards) shoot at vision 0, so `_vision_zero_ok` is False on
    them (layout 192, where the finding's 12 rows come from). Pins that the check is not loosened to pass a mixed scene (option (b) rejected) and that the finding is a scene problem."""
    got = fights(play, at(), MIXED_LAYOUT)
    assert any(f.firing_unit_seconds[0] > 0 or f.firing_unit_seconds[1] > 0 for f in got), [f.firing_unit_seconds for f in got]
    assert sweep._vision_zero_ok([got]) is False


@SLOW
def test_the_check_rejects_a_unit_lost_or_a_head_missing_or_a_shot_on_a_real_quiet_result():
    """The cases of the retired hand-fed test (TD-LAB-VISION-CONTROL-handfed), made from a REAL quiet result of the control scene
    (dataclasses.replace on one real FightResult): a fallen unit, a missing head and a counted shot each turn the verdict False."""
    quiet = fights(sweep.VISION_CONTROL_PLAY, at(), FIRST)
    assert sweep._vision_zero_ok([quiet]) is True                                          # the real result is quiet: the base case
    one = quiet[0]
    assert sweep._vision_zero_ok([[one, dataclasses.replace(one, survivors=(15, 16))]]) is False         # a unit fell
    assert sweep._vision_zero_ok([[one, dataclasses.replace(one, heads=(16, 15), survivors=(16, 15))]]) is False     # not 16 v 16
    assert sweep._vision_zero_ok([[one, dataclasses.replace(one, firing_unit_seconds=(1.0, 0.0))]]) is False        # a shot
