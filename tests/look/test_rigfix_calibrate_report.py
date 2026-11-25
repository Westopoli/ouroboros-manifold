"""look-judge-rig fixes, defect 4 (measurement 2026-11-24): `calibrate.py` reported no UNSURE count and no per-row verdicts, so "0 false passes" could not be told from "every
call failed". Spec piece 2: "Run a back end over a control set; report false passes and agreement"; UNSURE counts as FAIL for the gate but must be visible.

Report shape pinned: `unsure` = {check: number of rows whose back-end verdict was UNSURE}, every check present (like `false_pass`); `rows` = one entry per control, in
controls.json order: {"id", "verdict" (the back end's own PASS|FAIL|UNSURE, not collapsed), "truth", "label"}.
"""
import base64

import pytest

from test_backends_calibrate import build_set, run  # same control-set layout and runner as the existing calibrate tests


@pytest.fixture
def mixed(ollama):
    def reply(req):
        img = base64.b64decode(req["images"][0])
        if b"VAGUE" in img:
            return "yes"
        return "count: 2" if b"BREAK" in img else "count: 0"
    ollama.reply = reply
    return ollama


def test_control_report_has_false_pass_and_agreement(mixed, tmp_path, capsys):
    """Positive control (spec piece 2), green today: the report already carries false_pass, agreement and controls."""
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK"), ("overlap", "clean", b"CLEAN")])
    code, rep = run(root, capsys)
    assert code == 0 and rep["agreement"] == 1.0 and rep["controls"] == 2 and rep["false_pass"] == {"overlap": 0}


def test_report_counts_unsure_per_check(mixed, tmp_path, capsys):
    """Spec piece 2: the report says how many rows were UNSURE, per check, with zero for a check that had none."""
    root = build_set(tmp_path / "set", [("overlap", "break", b"VAGUE"), ("overlap", "clean", b"CLEAN"),
                                        ("overlap", "break", b"VAGUE"), ("wall", "clean", b"CLEAN")])
    code, rep = run(root, capsys)
    assert rep["unsure"] == {"overlap": 2, "wall": 0}
    assert code == 0 and sum(rep["false_pass"].values()) == 0  # UNSURE is still not a false pass


def test_report_lists_every_row_with_its_verdict(mixed, tmp_path, capsys):
    """Spec piece 2: one row per control, in order, with id, the back end's verdict (UNSURE kept as UNSURE), the truth and the label."""
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK"), ("overlap", "clean", b"CLEAN"), ("overlap", "break", b"VAGUE")])
    _, rep = run(root, capsys)
    rows = rep["rows"]
    assert [r["id"] for r in rows] == ["c0", "c1", "c2"]
    assert [r["verdict"] for r in rows] == ["FAIL", "PASS", "UNSURE"]
    assert [r["label"] for r in rows] == ["FAIL", "PASS", "FAIL"]
    assert all(r["truth"] == {"count": 0} for r in rows)
