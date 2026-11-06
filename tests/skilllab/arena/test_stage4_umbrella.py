# Rule pins: none (lab harness story H-088, cascade lab-stage4; spec docs/northstar/plans/cascades/lab-stage4/spec.md criteria 1, 2, 4, 5, 10, 11)
"""Umbrella test of the lab-stage4 cascade: the stage 4 pipeline end to end on the vantage fixture. RED on main 4fa618ce (`--control sight` is not a flag, the fight file
has no `sights`, `seen` or `first_seen`, the page has no sight caption); GREEN when leaves A and C are admitted.

One fight with `--sight on --control-dir D --control sight`: the main document names the sight rule set (ground era, per-unit `seen`, `sights`, `first_seen`, the holder
guarded) and the high ground sees first; the control document is the same fight with sight off and carries none of the sight keys; `page.build` on the directory prints
the stage header, the sight control caption and the first-seen line. Spec: criteria 1, 2, 4, 5 (leaf A) and 10, 11 (leaf C)."""
import math

import h063_fixtures as fx
from scripts.skilllab.arena import page, snapshot

VANTAGE_FEATURE = {"kind": "vantage", "x": 1100.0, "y": 2000.0, "radius": 700.0, "height_band": 1}


def vantage_layout(lid):
    """Eight Vanguards a side, A one band up at x 1400, B on the flat at x 2600, rows y 1860 to 2140, B walks to A (`hold:A`); spec criterion 5."""
    return {"id": lid, "situation": "vantage", "landscape": "small_tiered", "seed": 1, "predict": "A", "predict_why": "Test fixture.", "verdict": "", "feedback": "",
            "defender": "A", "orders": "hold:A", "side_a": {"headcount": 8, "units": fx.block(8, 1400.0, 2000.0, 0.0, layer=1, cols=8)},
            "side_b": {"headcount": 8, "units": fx.block(8, 2600.0, 2000.0, round(math.pi, 4), layer=0, cols=8)}, "features": [VANTAGE_FEATURE]}


def test_stage4_pipeline_end_to_end(tmp_path):
    control_dir = tmp_path / "control"
    proc, doc = fx.fight(vantage_layout("L-9401"), tmp_path, 1, "--sight", "on", "--cap-seconds", "60", "--control-dir", control_dir, "--control", "sight")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert doc["sight"] == "on"
    assert doc["movement_kind"] == 1, "sight on is a ground era: the units walk"
    assert doc["orders"]["guard"] is True, "the holder of hold:A is on order_guard"
    assert set(doc["sights"]) >= {"Vanguard"} and doc["sights"]["Vanguard"] > 0
    assert all("seen" in u for f in doc["frames"] for u in f["units"])
    first = doc["result"]["first_seen"]
    assert isinstance(first["A"], int) and isinstance(first["B"], int) and first["B"] >= first["A"], "the high ground sees red coming; red sees up only from the ramp's midline (R-005-09, stage 4 fix F1)"
    side = {u["id"]: u["side"] for u in doc["frames"][0]["units"]}
    assert any(u["seen"] for f in doc["frames"] for u in f["units"] if u["side"] == "A")
    assert not any(u["seen"] and u["layer"] == 0 for f in doc["frames"] for u in f["units"] if u["side"] == "B"), "no B unit on the low layer sees an A unit on the band above"
    assert all(side[e] == "B" for f in doc["frames"] for u in f["units"] if u["side"] == "A" for e in u["seen"])
    assert snapshot.validate(doc) == []

    control = snapshot.read(control_dir / "L-9401-control-s1.fight.json")
    assert control["sight"] == "off"
    assert control["layout_path"] == doc["layout_path"], "the sight control is the same layout, no twin"
    assert not any("seen" in u for f in control["frames"] for u in f["units"])
    assert control["movement_kind"] == 1 and control["orders"]["guard"] is True, "the control differs from the main fight by sight only (DEC-stage4-control-sight-off, amended)"
    assert "sights" not in control and "first_seen" not in control["result"]
    assert any(u["target"] for f in control["frames"] for u in f["units"] if u["side"] == "A"), "without sight targeting A fires down on the walkers"

    html = tmp_path / "index.html"
    assert page.build(str(tmp_path / "out"), str(html), control_dir=str(control_dir), stage=4) == 0
    text = html.read_text()
    assert "Stage 4, sight" in text
    assert "control: the same fight with everyone seeing everyone (sight off)" in text
    assert "first seen A %d  B %d" % (first["A"], first["B"]) in text
