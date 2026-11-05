# Rule pins: none (lab harness story H-063, cascade lab-stage3; spec docs/northstar/plans/cascades/lab-stage3/spec.md criteria 3, 4, 5, 10, 11)
"""Umbrella test of the lab-stage3 cascade: the finished stage 3 pipeline end to end on the chokepoint fixture. RED on main 634c4eb5 (the fight file has no
`landscape`, the control fight flies and names no twin, the page prints no control strip for an unrated layout); GREEN when leaves B and D are admitted.

One fight with `--control-dir`: the main document names its landscape and walks; the control document walks too (only the features differ), its `layout_path`
names a twin whose `features` is empty; `page.build` on the unrated directory prints the stage header, the control caption and the three sentences from a
sentences file. Spec: criteria 3, 4, 5 (leaf B) and 10, 11 (leaf D)."""
import json
from pathlib import Path

import h063_fixtures as fx
from scripts.skilllab.arena import page, snapshot

SENTENCES = ("| id | What to expect | Approve means | Deny means |\n|---|---|---|---|\n"
             "| L-9301 | Red queues at the gap. | Units respect the walls. | A unit stands inside a wall. |\n")


def test_stage3_pipeline_end_to_end(tmp_path):
    lay, _rects = fx.planar("chokepoint", "L-9301")
    control_dir = tmp_path / "control"
    proc, doc = fx.fight(lay, tmp_path, 1, "--cap-seconds", "5", "--control-dir", control_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert doc["landscape"] == "small_flat"
    assert doc["movement_kind"] == 1

    control = snapshot.read(control_dir / "L-9301-control-s1.fight.json")
    assert control["movement_kind"] == 1, "the control fight's units must walk like the main fight's; only the features differ"
    assert control["layout_path"].endswith("L-9301-control.toml")
    twin = json.loads((control_dir / "L-9301-control.json").read_text())
    assert twin["features"] == []
    assert Path(control_dir / "L-9301-control.toml").exists()

    sentences = tmp_path / "sentences.md"
    sentences.write_text(SENTENCES)
    html = tmp_path / "index.html"
    assert page.build(str(tmp_path / "out"), str(html), control_dir=str(control_dir), stage=3, sentences=str(sentences)) == 0
    text = html.read_text()
    assert "Stage 3, the ground pushes back" in text
    assert "control: the same fight without the ground" in text
    assert "Red queues at the gap." in text and "Units respect the walls." in text and "A unit stands inside a wall." in text
