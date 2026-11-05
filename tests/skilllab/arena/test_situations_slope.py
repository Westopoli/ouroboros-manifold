# spec: docs/northstar/plans/cascades/lab-stage3/spec.md::Acceptance criteria::AC-14
# Rule pins: none (lab harness story H-063)
"""lab-stage3 leaf-05, criteria 14 and 15 (spec lines 46 and 47): a `slope` row of a situation file converts to the H-025 round-two feature, and the converted
SIT-0109 fights as a climb (scripts/skilllab/arena/situations.py).

14: for `kind = slope` the converter emits `{kind: slope, x, y, length, width, heading: 0.0, from_band: 0, to_band: 1}` from the table row (`size` is
    `<length> x <width>`), landscape `small_tiered`; any other kind keeps today's `{kind, x, y, size, notes}` row. SIT-0109 converts to a layout that binds,
    passes `check_layout`, is not REJECTed by the route check, and fights with side A on layer 1 in every frame.
15: seed 1, `--cap-seconds 120`: no side B unit's recorded position lies in the cliff cells (x within 1700 to 2300 and y outside 1900 to 2100) in any frame.

Brief of leaf-05 (not a spec line): a slope `size` that is not `<number> x <number>` is a `Reject` of the converter."""
import json
import tomllib
from pathlib import Path

import pytest

import h063_fixtures as fx
from scripts.skilllab.arena import features, run as arena_run, situations, snapshot
from scripts.skilllab.catalogue import produce

SIT = fx.ROOT / "docs/northstar/research/layer_dynamics/situations/SIT-0109-slope.md"
SLOPE_ROW = "| slope | 2000 | 2000 | 600 x 200 | rises toward +x from band 0 to band 1; the ribbon is the only way up |"
COVER_ROW = "| cover | 1500 | 1900 | 300 x 100 | a box beside the foot |"
WANT = {"kind": "slope", "x": 2000, "y": 2000, "length": 600, "width": 200, "heading": 0.0, "from_band": 0, "to_band": 1}


def convert(tmp_path, text=None, lid="L-9701"):
    """(printed lines, rejected, the converted layout dict or None) for SIT-0109 (or `text`) alone in a scratch situations directory."""
    src = tmp_path / "sit"
    src.mkdir(exist_ok=True)
    (src / "SIT-0109-slope.md").write_text(SIT.read_text() if text is None else text)
    out = tmp_path / "catalogue"
    lines, rejected = situations.convert(src, out, lid)
    path = out / (lid + ".json")
    return lines, rejected, json.loads(path.read_text()) if path.exists() else None


def with_rows(rows):
    text = SIT.read_text()
    assert SLOPE_ROW in text, "fixture premise: SIT-0109 carries its slope row"
    return text.replace(SLOPE_ROW, rows)


# ---------------------------------------------------------------- criterion 14: the converter

def test_sit_0109_converts_with_the_h025_slope_feature(tmp_path):
    """Criterion 14, spec line 46: SIT-0109 converts (`CONVERTED`), landscape `small_tiered`, and its one feature is exactly the round-two slope (numbers, no `size`,
    no `notes`), in the JSON and in the TOML."""
    lines, rejected, lay = convert(tmp_path)
    assert not rejected and lines == ["CONVERTED SIT-0109-slope L-9701"], lines
    assert lay["landscape"] == "small_tiered"
    assert lay["features"] == [WANT]
    assert all(isinstance(lay["features"][0][k], (int, float)) and not isinstance(lay["features"][0][k], bool) for k in ("x", "y", "length", "width", "heading"))
    parsed = tomllib.loads((tmp_path / "catalogue" / "L-9701.toml").read_text())
    assert parsed["features"] == [WANT]


def test_converted_sit_0109_binds_passes_the_rules_and_the_route_check(tmp_path):
    """Criterion 14: `features.bound(layout)` is true, `check_layout` returns no rule, `run.unreachable(layout)` is None (the real engine's walk mask)."""
    _, _, lay = convert(tmp_path)
    assert lay["features"] == [WANT]
    assert features.bound(lay)
    assert produce.check_layout(lay, produce.presets(), produce.rules()) == []
    assert arena_run.unreachable(lay) is None


def test_converted_sit_0109_fights_with_side_a_on_layer_1_in_every_frame(tmp_path):
    """Criterion 14: `run.py` on the converted layout writes a fight whose side A units' `layer` is 1 in every frame (the high ground is held, not left)."""
    _, _, lay = convert(tmp_path)
    proc, doc = fx.fight(lay, tmp_path / "fight", 1, "--cap-seconds", "5")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    layers = {u["layer"] for f in doc["frames"] for u in f["units"] if u["side"] == "A"}
    assert layers == {1}, layers
    assert len(doc["frames"]) >= 2


def test_other_kinds_keep_todays_row_beside_a_slope(tmp_path):
    """Criterion 14, "any other kind keeps today's `{kind, x, y, size, notes}` row": a cover row beside the slope row keeps its size string and notes, the slope row is
    converted (Cardinality: two feature rows, in table order)."""
    _, rejected, lay = convert(tmp_path, with_rows(SLOPE_ROW + "\n" + COVER_ROW))
    assert not rejected
    assert lay["features"] == [WANT, {"kind": "cover", "x": 1500, "y": 1900, "size": "300 x 100", "notes": "a box beside the foot"}]


def test_a_fractional_slope_size_converts_to_numbers(tmp_path):
    """Criterion 14: `<length> x <width>` are numbers; 600.5 x 200 gives length 600.5 and width 200."""
    _, rejected, lay = convert(tmp_path, with_rows(SLOPE_ROW.replace("600 x 200", "600.5 x 200")))
    assert not rejected and lay["features"][0]["length"] == 600.5 and lay["features"][0]["width"] == 200


@pytest.mark.parametrize("size", ["600", "600 x", "x 200", "wide x 200", "600 x deep", "600 by 200", "600 x 200 x 5", ""],
                         ids=["one-number", "no-width", "no-length", "length-word", "width-word", "by", "three-numbers", "empty"])
def test_a_slope_size_that_is_not_length_x_width_is_rejected(size, tmp_path):
    """Leaf-05 brief: "Reject a slope `size` that is not `<number> x <number>` with the converter's `Reject`": the line is `REJECT SIT-0109-slope ...`, the run is
    rejected and no layout is written."""
    lines, rejected, lay = convert(tmp_path, with_rows(SLOPE_ROW.replace("600 x 200", size)))
    assert rejected and len(lines) == 1 and lines[0].startswith("REJECT SIT-0109-slope "), lines
    assert lay is None and not list((tmp_path / "catalogue").glob("L-9701.*"))


# ---------------------------------------------------------------- criterion 15: the climb

def test_the_converted_slope_fight_never_puts_a_side_b_unit_on_the_cliff(tmp_path):
    """Criterion 15, spec line 47: seed 1, `--cap-seconds 120`: no side B unit's recorded position (dead units included, every frame) is in the cliff cells, x within
    1700 to 2300 and y outside 1900 to 2100; the ribbon is the only way up. The fight has more than the opening frame, and side B did leave the foot (some B unit
    reached x 1700 or more), so an empty field would not pass."""
    _, _, lay = convert(tmp_path)
    proc, doc = fx.fight(lay, tmp_path / "fight", 1, "--cap-seconds", "120")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    b = [(f["tick"], u["id"], u["x"], u["y"]) for f in doc["frames"] for u in f["units"] if u["side"] == "B"]
    cliff = [row for row in b if 1700 <= row[2] <= 2300 and (row[3] < 1900 or row[3] > 2100)]
    assert cliff == [], "side B units on the cliff (tick, id, x, y): %s" % cliff[:5]
    assert len(doc["frames"]) > 2 and max(x for _, _, x, _ in b) >= 1700, "side B never advanced to the slope"
