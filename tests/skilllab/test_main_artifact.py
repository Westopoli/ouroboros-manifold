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
        Calls report.artifact(summary, rows, setup_for, <dir>, thresholds=<None or evidence.Thresholds>) (title default), so the page is
        <dir>/artifact.html and the svgs <dir>/diagrams/<id>.svg.
        Prints the artifact path on stdout (one line) and returns 0.
    main(["artifact", "<dir>", "--thresholds", "<file.json>"]) -> 0       (decision 34 item 2, corrected; ruled 2026-10-19)
        An OPTIONAL flag. <file.json> is a JSON object holding Westley's pass marks: its keys are the field names of
        evidence.Thresholds (scripts/skilllab/evidence.py; all fifteen, because Thresholds has no defaults; c7_ceiling_targets and
        c9_length_bounds_ticks are JSON lists, read as tuples). The command builds the Thresholds from it and passes it to
        report.artifact, which shows the verdicts the CSV rows alone support, each with its Thresholds field name and the value used
        (test_report.py header, section "conditions"). The thresholds are an input: nothing in the lab supplies a default.
        Without the flag the page's conditions section reads `no condition verdicts: thresholds not supplied` and lists the raw
        agreement counts and C1 advantages as numbers, with no pass or fail words.
    main(["artifact", "<dir>", "--thresholds", "<file with a key missing>"]) -> 2 and a message (stdout or stderr) naming the missing
        key; nothing is written (no artifact.html, no diagrams/). Tested with keys the verdicts use; whether an UNUSED key may be
        missing is not pinned (the file holds every Thresholds field).
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
import fixtures_conditions as fx  # noqa: E402

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


def _write_conditions_run(d, rows):
    """A one-family sweep directory whose CSV holds `rows` (fixtures_conditions), and the file name of a thresholds json is the caller's."""
    d.mkdir(parents=True, exist_ok=True)
    rows_mod.write_rows(rows, d / "sweep_range_up.csv")
    (d / "sweep_summary.json").write_text(json.dumps({"order": ["range_up"], "replicates": 3, "families": {
        "range_up": {"family": "range_up", "skipped": None, "csv": "sweep_range_up.csv", "refined": [], "refined_vs": {"naive_attacker": []}}}}),
        encoding="utf-8")


def _conditions(d):
    import test_report
    return test_report._sec(test_report._tree((d / "artifact.html").read_text(encoding="utf-8")), "conditions")


def _thresholds_file(path, **over):
    path.write_text(json.dumps(fx.thresholds_dict(**over)), encoding="utf-8")
    return str(path)


def test_artifact_command_with_a_thresholds_file_shows_the_verdicts_with_the_names_and_values_from_the_file(tmp_path, monkeypatch):
    """Plumbing only: the file's c1_min_firing_advantage (0.0625) decides the strict comparison and is the value shown. Window attacker
    line 0.375 > 0.25 + 0.0625 holds; with 0.125 in the file it does not (0.375 > 0.375 is false)."""
    import test_report
    td = _td()
    Recorder(monkeypatch, td)
    for sub, mn, holds in (("a", 0.0625, "true"), ("b", 0.125, "false")):
        d = tmp_path / sub
        _write_conditions_run(d, fx.c1_rows())              # c1_rows alone: the C2 lines are computed from its fights too
        assert main(["artifact", str(d), "--thresholds", _thresholds_file(tmp_path / (sub + ".json"), c1_min_firing_advantage=mn)]) == 0
        sec = _conditions(d)
        assert "no condition verdicts" not in sec.text()
        line = [tr for tr in test_report._cls(sec, "tr", "c1") if (tr.attrs["data-basis"], tr.attrs["data-baseline"]) == ("window", "naive_attacker")]
        assert len(line) == 1 and line[0].attrs["data-holds"] == holds
        spans = test_report._cls(line[0], "span", "threshold")
        assert [(s.attrs["data-name"], float(s.attrs["data-value"])) for s in spans] == [("c1_min_firing_advantage", mn)]
        c2 = test_report._cls(sec, "tr", "c2-verdict")
        assert {s.attrs["data-name"] for tr in c2 for s in test_report._cls(tr, "span", "threshold")} == {
            "c2_rank_agreement", "c2_off_trend_margin", "c2_off_trend_share"}


def test_artifact_command_without_the_flag_says_thresholds_not_supplied_and_lists_the_numbers(tmp_path, monkeypatch):
    """The exact sentence, the raw agreement counts and the C1 advantages as numbers, no pass or fail words (the same page the thresholds
    file would have given, minus the verdicts)."""
    import test_report
    Recorder(monkeypatch, _td())
    d = tmp_path / "run"
    _write_conditions_run(d, fx.c2_rows())
    assert main(["artifact", str(d)]) == 0
    test_report.check_no_verdicts_with_raw_numbers(_conditions(d), counts=fx.C2_COUNTS)
    d2 = tmp_path / "run2"
    _write_conditions_run(d2, fx.c1_rows())
    assert main(["artifact", str(d2)]) == 0
    test_report.check_no_verdicts_with_raw_numbers(_conditions(d2), c1=fx.C1_NUMBERS)


def test_artifact_command_with_a_thresholds_file_missing_a_key_is_an_error_naming_the_key_and_writes_nothing(tmp_path, monkeypatch, capsys):
    Recorder(monkeypatch, _td())
    for key in ("c1_min_firing_advantage", "c2_rank_agreement", "c2_off_trend_share"):
        d = tmp_path / key
        _write_conditions_run(d, fx.c1_rows() + fx.c2_rows())
        bad = fx.thresholds_dict()
        del bad[key]
        f = tmp_path / (key + ".json")
        f.write_text(json.dumps(bad), encoding="utf-8")
        assert main(["artifact", str(d), "--thresholds", str(f)]) == 2
        out = capsys.readouterr()
        assert key in out.out + out.err, key
        assert not (d / "artifact.html").exists() and not (d / "diagrams").exists(), key
    d = tmp_path / "positive_control"                                                 # the same file with the key present succeeds
    _write_conditions_run(d, fx.c1_rows() + fx.c2_rows())
    assert main(["artifact", str(d), "--thresholds", _thresholds_file(tmp_path / "ok.json")]) == 0 and (d / "artifact.html").is_file()


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
