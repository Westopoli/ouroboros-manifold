# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L5; decision 29 "Wiring": L5 owns __main__.py and adds the `artifact` command
"""LAB-REV2-L5: `python -m scripts.skilllab artifact <dir>` reads the sweep CSVs in <dir> and writes artifact.html and diagrams/*.svg there.

THE INTERFACE BELOW IS FIXED BY THIS FILE (the builder reads it as the spec):

    main(["artifact", "<dir>"]) -> 0
        <dir> holds sweep_summary.json (sweep.run's file: {"order": [...], "replicates": n, "families": {family: entry}}) and the CSVs the
        entries name (entry["csv"], relative to <dir>; a skipped family has csv None and is not read) and, if present, smoke.csv.
        rows = diagram.read_rows of each family CSV in summary["order"] order, then smoke.csv, concatenated (the row index of a
        both_wrong notable is its index in that list).
        setup_for(notable) = the real scene code reached through MODULE ATTRIBUTES of scripts.skilllab.sweep (as the other main tests
        expect their siblings): features = sweep.smoke_layouts()[notable.layout]; build = sweep.default_builds(notable.play, "play",
        features); return build(notable.heads, False). Asked for every notable (how many times is free).
        Calls report.artifact(summary, rows, setup_for, <dir>) (title default, verdicts None: the conditions are computed where the
        thresholds are, which is not here), so the page is <dir>/artifact.html and the svgs <dir>/diagrams/<id>.svg.
        Prints the artifact path on stdout (one line) and returns 0.
    main(["artifact"]) -> 2 and a message naming the missing directory; main(["artifact", "<dir without sweep_summary.json>"]) -> 2 and a
        message naming sweep_summary.json; nothing is written in either case.
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import __main__ as cli, rows as rows_mod, sweep  # noqa: E402
from scripts.skilllab.__main__ import main  # noqa: E402

LAYOUTS = {"81": {"id": 81}, "78": {"id": 78}, "192": {"id": 192}}


def _td():
    import test_diagram
    return test_diagram


def _write_run(d, td):
    """A sweep directory: two family CSVs, a skipped arc family, a smoke.csv, and the summary."""
    d.mkdir(parents=True, exist_ok=True)
    range_up = td.crossing_rows() + td.ceiling_rows(play="s3_types_by_reach")
    vision = [td.both_wrong_row()]
    smoke = [td.both_wrong_row(ticks=301, kind="control_smoke")]
    rows_mod.write_rows(range_up, d / "sweep_range_up.csv")
    rows_mod.write_rows(vision, d / "sweep_vision.csv")
    rows_mod.write_rows(smoke, d / "smoke.csv")
    summary = {"order": ["range_up", "arc", "vision"], "replicates": 3, "families": {
        "range_up": {"family": "range_up", "skipped": None, "csv": "sweep_range_up.csv", "refined": [], "refined_vs": {"naive_attacker": []}},
        "arc": {"family": "arc", "skipped": "the library has no OM_TP_FIRING_ARC_DEG (LAB-REV2-E0 not built)", "csv": None, "refined": [], "refined_vs": {}},
        "vision": {"family": "vision", "skipped": None, "csv": "sweep_vision.csv", "refined": [], "refined_vs": {"naive_attacker": []}}}}
    (d / "sweep_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return range_up + vision + smoke


class Recorder:
    """sweep.smoke_layouts and sweep.default_builds replaced on their own module; records what main asked for."""

    def __init__(self, monkeypatch, td):
        self.default_calls, self.build_calls = [], []
        monkeypatch.setattr(sweep, "smoke_layouts", lambda: dict(LAYOUTS))

        def default_builds(play, role, features):
            self.default_calls.append((play, role, features))

            def build(enemy_heads, swap):
                self.build_calls.append((enemy_heads, swap))
                return td.fake_setup()
            build.labels = {"prefight": "ok"}
            return build
        monkeypatch.setattr(sweep, "default_builds", default_builds)


def test_artifact_command_writes_the_page_and_one_svg_per_notable_from_the_csvs(tmp_path, monkeypatch, capsys):
    from scripts.skilllab import diagram
    td = _td()
    rows = _write_run(tmp_path, td)
    rec = Recorder(monkeypatch, td)
    assert main(["artifact", str(tmp_path)]) == 0
    typed = (diagram.read_rows(tmp_path / "sweep_range_up.csv") + diagram.read_rows(tmp_path / "sweep_vision.csv") + diagram.read_rows(tmp_path / "smoke.csv"))
    assert len(typed) == len(rows)
    ns = diagram.notables(typed)
    assert [n.kind for n in ns].count(diagram.BOTH_WRONG) == 2 and len(ns) == 4                # the smoke row is read too
    assert (tmp_path / "artifact.html").is_file()
    assert sorted(p.name for p in (tmp_path / "diagrams").glob("*.svg")) == sorted(n.id + ".svg" for n in ns)
    html = (tmp_path / "artifact.html").read_text(encoding="utf-8")
    listed = [int(i) for i in re.findall(r"<li[^>]*data-row=[\"']?(\d+)", html)]
    assert listed == [n.row for n in ns if n.kind == diagram.BOTH_WRONG] == [len(typed) - 2, len(typed) - 1]
    assert capsys.readouterr().out.strip().splitlines()[-1] == str(tmp_path / "artifact.html")
    # setup_for is the real scene seam: for every notable, with the notable's play, the "play" role, its layout's features and its own
    # headcount (Notable.heads), swap False (repeated asks are free)
    first = lambda calls: [c for i, c in enumerate(calls) if c not in calls[:i]]
    assert first(rec.default_calls) == [(n.play, "play", LAYOUTS[n.layout]) for n in ns][:len(first(rec.default_calls))]
    assert all(call in rec.default_calls for call in [(n.play, "play", LAYOUTS[n.layout]) for n in ns])
    assert all(call in rec.build_calls for call in [(n.heads, False) for n in ns])
    assert all(c[2] in LAYOUTS.values() and c[1] == "play" and b[1] is False for c, b in zip(rec.default_calls, rec.build_calls))


def test_artifact_command_skipped_family_is_not_read_and_the_run_is_deterministic(tmp_path, monkeypatch):
    td = _td()
    _write_run(tmp_path / "a", td)
    _write_run(tmp_path / "b", td)
    (tmp_path / "a" / "sweep_arc.csv").write_text("this is not a csv the command may read\n", encoding="utf-8")    # arc is skipped: csv None
    Recorder(monkeypatch, td)
    assert main(["artifact", str(tmp_path / "a")]) == 0 and main(["artifact", str(tmp_path / "b")]) == 0
    assert (tmp_path / "a" / "artifact.html").read_bytes() == (tmp_path / "b" / "artifact.html").read_bytes()
    for p in (tmp_path / "a" / "diagrams").glob("*.svg"):
        assert p.read_bytes() == (tmp_path / "b" / "diagrams" / p.name).read_bytes()


def test_artifact_command_without_a_directory_is_a_usage_error_and_writes_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["artifact"]) == 2
    out = capsys.readouterr()
    assert "artifact" in (out.out + out.err).lower() and not list(tmp_path.iterdir())


def test_artifact_command_without_the_summary_file_is_an_error_naming_it_and_writes_nothing(tmp_path, capsys):
    (tmp_path / "sweep_range_up.csv").write_text("family\n", encoding="utf-8")
    assert main(["artifact", str(tmp_path)]) == 2
    out = capsys.readouterr()
    assert "sweep_summary.json" in out.out + out.err
    assert not (tmp_path / "artifact.html").exists() and not (tmp_path / "diagrams").exists()


def test_the_other_commands_are_still_dispatched_negative_control(tmp_path, capsys):
    """Adding the command must not make unknown commands succeed or the usage of `batch` change."""
    assert main(["no_such_command"]) == 2
    assert main(["batch"]) == 2 and "batch needs one of" in capsys.readouterr().out


# ---- SLOW: the real scene code behind setup_for -----------------------------------------------------------------------------

import os  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="the real placed scenes (no engine, but the real map code); set OM_LAB_SLOW=1")


@SLOW
def test_artifact_command_with_the_real_placed_scene_draws_every_real_unit(tmp_path):
    """SLOW: no monkeypatching. A crossing on s3_layer_above at layout 81 (smoke layout) is drawn from sweep.default_builds(...)(heads, False):
    the svg holds exactly the units of that Setup."""
    import xml.etree.ElementTree as ET
    from scripts.skilllab import diagram
    td = _td()
    d = tmp_path
    rows_mod.write_rows(td.crossing_rows(), d / "sweep_range_up.csv")
    (d / "sweep_summary.json").write_text(json.dumps({"order": ["range_up"], "replicates": 3, "families": {
        "range_up": {"family": "range_up", "skipped": None, "csv": "sweep_range_up.csv", "refined": [], "refined_vs": {"naive_attacker": []}}}}),
        encoding="utf-8")
    assert main(["artifact", str(d)]) == 0
    n = diagram.notables(diagram.read_rows(d / "sweep_range_up.csv"))[0]
    setup = sweep.default_builds(n.play, "play", sweep.smoke_layouts()[n.layout])(n.heads, False)
    svg = ET.fromstring((d / "diagrams" / (n.id + ".svg")).read_text(encoding="utf-8"))
    units = [e for e in svg.iter() if e.tag.split("}")[-1] == "circle" and "unit" in (e.get("class") or "").split()]
    assert len(units) == sum(g.count for g in setup.groups) > 0
