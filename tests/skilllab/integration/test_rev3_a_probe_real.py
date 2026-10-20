# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R6, test T2; defects D1, D10); ledger FINDING-lab-d1, FINDING-lab-d10; piece LAB-REV3-A
"""LAB-REV3-A, T2 (R6, D1, D10) against the real engine (OM_LAB_SLOW=1; seconds a test): the inert-knob probe on the real plays, built as
the sweep builds them (`sweep.default_builds(play, "play", sweep.smoke_layouts()["192"])`, the one smoke layout the layer plays fit).
The contract is in the docstring of tests/skilllab/test_rev3_a_probe.py (`probe.inert(build, settings)`).

The two knob sets are the band's low extreme (0.25 of base, from sweep.BASES) of the TWO-LAYER knobs and of the ONE-LAYER knobs.
Measured on the lab tip (2026-10-20, this file's author, 16 enemies, seed 0, both plays): the two-layer set leaves the row byte-identical on
s3_layer_above and on s3_types_by_reach (no unit is ever two layers from an enemy there: FINDING-lab-d1) and the one-layer set moves it;
on s3_over_the_choke (Bombards two layers above) OM_TP_RANGE_DOWN_2 alone moves it. The first two are this file's controls (green on the lab
tip, no probe module needed); the probe tests are red today only because the module does not exist."""
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight as fight_mod, rows as rows_mod, sweep  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")
LAYOUT = "192"
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


@SLOW
@pytest.mark.parametrize("play", ["s3_layer_above", "s3_types_by_reach"])
def test_t2_the_probe_calls_the_two_layer_knobs_inert_on_the_layer_plays(play):
    """T2 (R6, D1): inert on s3_layer_above and s3_types_by_reach. Red today: no probe module."""
    from scripts.skilllab import probe
    assert probe.inert(build(play), TWO_LAYER) is True


@SLOW
@pytest.mark.parametrize("play", ["s3_layer_above", "s3_types_by_reach"])
def test_t2_the_probe_does_not_call_the_one_layer_knobs_inert(play):
    """T2 positive control (R6): the one-layer family bites on the same plays. Red today only for the missing module."""
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
def test_t2_range_up_bites_on_s3_layer_above_because_real_families_set_the_one_layer_knob_too():
    """T2 positive control through a family (W3): the real range_up family sets OM_TP_RANGE_UP_1 and OM_TP_RANGE_UP_2 together
    (sweep._range_up; vision likewise in _vision_settings), so its extreme point moves the row on s3_layer_above although the two-layer
    knobs alone do not. Red today only for the missing module."""
    from scripts.skilllab import probe
    assert probe.inert(build("s3_layer_above"), extreme("range_up").settings) is False


@SLOW
def test_t2_the_emitting_family_is_not_inert_on_the_dark_striker():
    """T2 through a family (W3): the emitting extreme (sight 1.0, seen 1.5 at vision 0.125) against the same vision with the emit
    multipliers at their bases (2.0, 3.0). Today the three sight values give ONE row on s3_dark_striker (nobody emits: FINDING-lab-d5),
    so the probe reads inert and the family would be refused there; after the D5 fix the enemy emits and it must not be. Red today
    (module missing); red after the module and before D5 (inert)."""
    from scripts.skilllab import probe
    point = min((p for p in sweep.grid("emitting") if p.settings["OM_TP_VISION_UP_1"] == 0.125), key=lambda p: p.value)
    base = {**point.settings, "OM_TP_EMIT_SIGHT_MULT": sweep.BASES["OM_TP_EMIT_SIGHT_MULT"],
            "OM_TP_EMIT_SEEN_MULT": sweep.BASES["OM_TP_EMIT_SEEN_MULT"]}
    assert (point.settings["OM_TP_EMIT_SIGHT_MULT"], point.settings["OM_TP_EMIT_SEEN_MULT"]) == (1.0, 1.5)
    assert probe.inert(build("s3_dark_striker"), point.settings, base_settings=base) is False


@SLOW
def test_t2_run_family_with_the_probe_does_not_refuse_the_emitting_family_on_the_dark_striker(tmp_path):
    """T2 through run_family (W3): probe=True on the real emitting family, the real dark striker, the first smoke layout it fits (192),
    one replicate (about two minutes once the play emits; before the D5 fix it is refused after the two probe fights). Red today: no
    `probe` keyword. After D5: refused == []."""
    entry = sweep.run_family("emitting", tmp_path, plays=("s3_dark_striker",), layouts={LAYOUT: sweep.smoke_layouts()[LAYOUT]},
                             replicates=1, probe=True)
    assert entry["refused"] == [], entry["refused"]
