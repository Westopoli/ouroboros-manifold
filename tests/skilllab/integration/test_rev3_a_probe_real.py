# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R6, test T2; defects D1, D10); ledger FINDING-lab-d1, FINDING-lab-d10; piece LAB-REV3-A
"""LAB-REV3-A, T2 (R6, D1, D10) against the real engine (OM_LAB_SLOW=1; seconds a test): the inert-knob probe on the real plays, built as
the sweep builds them (`sweep.default_builds(play, "play", sweep.smoke_layouts()["192"])`, the one smoke layout the layer plays fit).
The contract is in the docstring of tests/skilllab/test_rev3_a_probe.py (`probe.inert` / `probe.survey` over the sweep's coarse
headcounts 8, 16, 24, 32, 40, 48 (read from scan.COARSE_STEP) and seeds 0 and 1, 24 fights of about 0.4 s: Architect ruling
2026-10-20, a family is inert only when EVERY row is identical to base; the survey returns {(heads, seed): {"differed", "base_cached"}}).

The two knob sets are the band's low extreme (0.25 of base, from sweep.BASES) of the TWO-LAYER knobs and of the ONE-LAYER knobs.
Measured on the lab tip (2026-10-20, this file's author, 16 enemies, seed 0, both plays): the two-layer set leaves the row byte-identical on
s3_layer_above and on s3_types_by_reach (no unit is ever two layers from an enemy there: FINDING-lab-d1) and the one-layer set moves it;
on s3_over_the_choke (Bombards two layers above) OM_TP_RANGE_DOWN_2 alone moves it. The first two are this file's controls (green on the lab
tip, no probe module needed); the probe tests are red on the one-point probe (16 heads, seed 0).

Measured on the lab tip fb0874cc + this branch 2026-10-20 (this file's author, extreme point of the family vs the same point with the
family's own keys at BASES, layout 192, headcounts 8, 16, 24, 32, 40, 48, seeds 0 and 1, rows differing from base):
  range_up   s3_layer_above   none at 8 and 16 heads; both seeds at 24, 32, 40, 48     -> inert at 16 heads, bites from 24
  vision     s3_layer_above   seed 1 only at 8 heads; both seeds from 16 on           -> not inert, bites from 8 (seed 1)
  range_up   s3_types_by_reach none at 8; both seeds from 16 on                       -> bites from 16
  emitting   s3_dark_striker  both seeds at every headcount                           -> bites at every point
  range_up   s2_concave       none at any of the 12 points (layout 192 and 81; damage_up and vision at 81 too: no unit is a layer from an enemy) -> inert
(the sweep measured caps at 32, 40 and 48 heads on s3_layer_above; the probe's rows differ one step earlier, at 24.)"""
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight as fight_mod, rows as rows_mod, scan, sweep  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")
LAYOUT = "192"
HEADS, SEEDS = tuple(sorted(set(range(sweep.ENEMY_FROM, sweep.ENEMY_TO + 1, scan.COARSE_STEP)) | {sweep.ENEMY_TO})), (0, 1)   # the sweep's coarse list: 8, 16, 24, 32, 40, 48
TWO_LAYER = {"OM_TP_VISION_UP_2": 0.05, "OM_TP_VISION_DOWN_2": 0.05, "OM_TP_RANGE_UP_2": 0.25, "OM_TP_RANGE_DOWN_2": 0.25,
             "OM_TP_DAMAGE_UP_2": 0.25}     # 0.25 of BASES (0.2 for vision)
ONE_LAYER = {"OM_TP_VISION_UP_1": 0.125, "OM_TP_VISION_DOWN_1": 0.125, "OM_TP_RANGE_UP_1": 0.25, "OM_TP_RANGE_DOWN_1": 0.25,
             "OM_TP_DAMAGE_UP_1": 0.25}     # 0.25 of BASES (0.5 for vision)


def build(play):
    return sweep.default_builds(play, "play", sweep.smoke_layouts()[LAYOUT])


def row(play, settings):
    setup = build(play)(sweep.SIZE, False)
    return rows_mod.fight_row(fight_mod.fight(dataclasses.replace(setup, settings={**setup.settings, **settings}), 0, False))


def test_the_knob_sets_are_a_quarter_of_the_bases():
    """Green on the lab tip, no engine: the extremes are 0.25 of sweep.BASES, not numbers of this file's own."""
    for k, v in {**TWO_LAYER, **ONE_LAYER}.items():
        assert v == pytest.approx(0.25 * sweep.BASES[k])


@SLOW
@pytest.mark.parametrize("play", ["s3_layer_above", "s3_types_by_reach"])
def test_positive_control_the_two_layer_knobs_do_not_move_the_row_and_the_one_layer_knobs_do(play):
    """Green on the lab tip (the D1 measurement): the premise the probe is checked against."""
    base = row(play, {})
    assert row(play, TWO_LAYER) == base
    assert row(play, ONE_LAYER) != base


ALL = {(h, s) for h in HEADS for s in SEEDS}


def pair(family):
    """(settings, base_settings) of the family's extreme point: the base is the same point with the family's own keys at BASES."""
    point = extreme(family).settings
    return point, {**point, **{k: sweep.BASES[k] for k in point}}


@SLOW
@pytest.mark.parametrize("play", ["s3_layer_above", "s3_types_by_reach"])
def test_t2_the_probe_calls_the_two_layer_knobs_inert_on_the_layer_plays(play):
    """T2 (R6, D1): inert on s3_layer_above and s3_types_by_reach across every sweep headcount and seed (24 fights)."""
    from scripts.skilllab import probe
    assert probe.inert(build(play), TWO_LAYER) is True


@SLOW
@pytest.mark.parametrize("play", ["s3_layer_above", "s3_types_by_reach"])
def test_t2_the_probe_does_not_call_the_one_layer_knobs_inert(play):
    """T2 positive control (R6): the one-layer family bites on the same plays."""
    from scripts.skilllab import probe
    assert probe.inert(build(play), ONE_LAYER) is False


@SLOW
def test_t2_the_probe_does_not_call_the_two_layer_knobs_inert_where_a_unit_is_two_layers_away():
    """T2 positive control (R6): s3_over_the_choke has Bombards two layers above the enemy, so the two-layer set bites there."""
    from scripts.skilllab import probe
    assert probe.inert(build("s3_over_the_choke"), TWO_LAYER) is False


# ---- through the families (W3 of the audit) ---------------------------------------------------------------------------------------------

def extreme(family):
    """The family's extreme grid point: the smallest value (contract in tests/skilllab/test_rev3_a_probe.py)."""
    return min((p for p in sweep.grid(family) if p.kind == "grid"), key=lambda p: p.value)


@SLOW
def test_t2_range_up_is_not_inert_on_s3_layer_above():
    """T2 (R6, the Architect's ruling 2026-10-20, R4): range_up at the 0.25 point on s3_layer_above, layout 192, is NOT inert, and the
    rows differ at the three headcounts where the sweep measured caps (32, 40, 48) on both seeds and are equal at the smallest (8) on
    both seeds. Red on the one-point probe: it reads 16 heads, seed 0, and says inert.

    The pin is deliberately only those facts: the real-engine rows move with the engine (decisions 50, pieces B and C). The full
    measurement the artifact line is built from (2026-10-20, fb0874cc + this branch, extreme vs the same point with the family's own keys
    at BASES, both seeds alike): equal at 8 and 16 heads, differing at 24, 32, 40 and 48, so the first differing headcount is 24 and the
    record's line reads 'bites from 24 heads seed 0; silent at [(8, 0), (8, 1), (16, 0), (16, 1)]' (also reported in the A landing)."""
    from scripts.skilllab import probe
    settings, base = pair("range_up")
    assert probe.inert(build("s3_layer_above"), settings, base_settings=base) is False
    got = probe.survey(build("s3_layer_above"), settings, base_settings=base)
    differed = {k: v["differed"] for k, v in got.items()}
    assert not any(differed[(HEADS[0], s)] for s in SEEDS), differed
    assert all(differed[(h, s)] for h in (32, 40, 48) for s in SEEDS), differed


@SLOW
def test_t2_vision_and_range_up_are_not_inert_on_the_layer_plays_they_are_swept_on():
    """T2 (R6, R4 of the audit's open item): the families the sweep runs on the layer plays are not refused there. Documented measurement
    only (not asserted): vision on s3_layer_above differs on seed 1 only at 8 heads and on both seeds from 16; range_up on
    s3_types_by_reach is equal at 8 and differs from 16."""
    from scripts.skilllab import probe
    for family, play in (("vision", "s3_layer_above"), ("range_up", "s3_types_by_reach")):
        settings, base = pair(family)
        assert probe.inert(build(play), settings, base_settings=base) is False, (family, play)


@SLOW
@pytest.mark.parametrize("family, layout", [("range_up", "81"), ("damage_up", "81"), ("vision", "81"), ("range_up", "192")])
def test_t2_a_family_is_inert_where_no_unit_is_ever_a_layer_from_an_enemy(family, layout):
    """T2 positive control (R6), the truly inert case: s2_concave puts every unit on one layer, so no layer knob has anything to act
    on; all 12 points of the survey (6 headcounts x 2 seeds) have a row identical to base (measured 2026-10-20 on the four cases)."""
    from scripts.skilllab import probe
    settings, base = pair(family)
    b = sweep.default_builds("s2_concave", "play", sweep.smoke_layouts()[layout])
    assert {k: v["differed"] for k, v in probe.survey(b, settings, base_settings=base).items()} == {k: False for k in ALL}
    assert probe.inert(b, settings, base_settings=base) is True


@SLOW
def test_t2_the_emitting_family_is_not_inert_on_the_dark_striker():
    """T2 through a family (W3): the emitting extreme (sight 1.0, seen 1.5 at vision 0.125) against the same vision with the emit
    multipliers at their bases (2.0, 3.0): the enemy emits (FINDING-lab-d5), so the rows differ at every sweep point."""
    from scripts.skilllab import probe
    point = min((p for p in sweep.grid("emitting") if p.settings["OM_TP_VISION_UP_1"] == 0.125), key=lambda p: p.value)
    base = {**point.settings, "OM_TP_EMIT_SIGHT_MULT": sweep.BASES["OM_TP_EMIT_SIGHT_MULT"],
            "OM_TP_EMIT_SEEN_MULT": sweep.BASES["OM_TP_EMIT_SEEN_MULT"]}
    assert (point.settings["OM_TP_EMIT_SIGHT_MULT"], point.settings["OM_TP_EMIT_SEEN_MULT"]) == (1.0, 1.5)
    assert probe.inert(build("s3_dark_striker"), point.settings, base_settings=base) is False


@SLOW
def test_t2_run_family_with_the_probe_does_not_refuse_the_emitting_family_on_the_dark_striker(tmp_path):
    """T2 through run_family (W3): probe=True on the real emitting family, the real dark striker, the first smoke layout it fits (192),
    one replicate (about two minutes): not refused."""
    entry = sweep.run_family("emitting", tmp_path, plays=("s3_dark_striker",), layouts={LAYOUT: sweep.smoke_layouts()[LAYOUT]},
                             replicates=1, probe=True)
    assert entry["refused"] == [], entry["refused"]
