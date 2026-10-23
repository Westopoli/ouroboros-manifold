# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-20
"""Leaf-07: main(["controls", ...]) wires scan, rows and report; siblings are replaced by recorders.

The siblings are replaced on their own modules (scan.scan, rows.fight_row, rows.write_rows,
report.report, plays.blob_play, plays.damage_play, plays.reach_play); main must reach them through module attributes.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.skilllab.plays as plays  # noqa: E402
import scripts.skilllab.report as report_mod  # noqa: E402
import scripts.skilllab.rows as rows_mod  # noqa: E402
import scripts.skilllab.scan as scan_mod  # noqa: E402
from scripts.skilllab.__main__ import main  # noqa: E402
from scripts.skilllab.contract import Batch, CellResult, FightResult, ScanResult  # noqa: E402

ENEMY_FROM, ENEMY_TO = 8, 24


def _fight(tag):
    return FightResult(outcome="side0", margin=0.1, strength_left=(0.5, 0.2), survivors=(8, 2),
                       heads=(16, 16), ticks=tag, first_contact_tick=1, firing=[(0, 1, 1)],
                       firing_unit_seconds=(0.25, 0.25))


def _scan_result(base):
    cells = [CellResult(enemy_heads=n, fights=[_fight(base + 2 * n), _fight(base + 2 * n + 1)],
                        mean_margin=0.1, won=True) for n in range(ENEMY_FROM, ENEMY_TO + 1)]
    return ScanResult(size=16, cells=cells, beats=None, loses_to=None)


class World:
    """Recorders for every sibling main talks to."""

    def __init__(self, monkeypatch):
        self.scan_calls, self.row_calls, self.write_calls, self.report_calls = [], [], [], []
        self.blob_args, self.damage_args, self.reach_args = [], [], []
        self.blob_build = lambda enemy_heads, swap: "blob-setup"
        self.damage_build = lambda enemy_heads, swap: "damage-setup"
        self.reach_build = lambda enemy_heads, swap: "reach-setup"
        self.results = {"identical": _scan_result(1000), "damage": _scan_result(5000)}
        self.dicts = []

        def blob_play(*args, **kwargs):
            self.blob_args.append((args, kwargs))        # recorded exactly as main called it
            return self.blob_build

        def damage_play(*args, **kwargs):
            self.damage_args.append((args, kwargs))
            return self.damage_build

        def reach_play(*args, **kwargs):          # the study knob: controls must never reach for it
            self.reach_args.append((args, kwargs))
            return self.reach_build

        def fake_scan(build, size, enemy_from, enemy_to, replicates=10, fight_fn=None, map_fn=None, full_scan=False, **kw):
            self.scan_calls.append(dict(build=build, size=size, enemy_from=enemy_from, enemy_to=enemy_to,
                                        replicates=replicates, full_scan=full_scan))
            return self.results["identical"] if build is self.blob_build else self.results["damage"]

        def fake_fight_row(result, **labels):
            self.row_calls.append((result, labels))
            row = dict(labels)
            row["ticks"] = result.ticks
            self.dicts.append(row)
            return row

        def fake_write_rows(rows, path):
            self.write_calls.append((list(rows), path))

        def fake_report(batch, out_dir):
            self.report_calls.append((batch, out_dir))
            return str(Path(out_dir) / "report.html")

        monkeypatch.setattr(plays, "blob_play", blob_play)
        monkeypatch.setattr(plays, "damage_play", damage_play, raising=False)  # plays shard owns it; isolate main from it
        monkeypatch.setattr(plays, "reach_play", reach_play)
        monkeypatch.setattr(scan_mod, "scan", fake_scan)
        monkeypatch.setattr(rows_mod, "fight_row", fake_fight_row)
        monkeypatch.setattr(rows_mod, "write_rows", fake_write_rows)
        monkeypatch.setattr(report_mod, "report", fake_report)


@pytest.fixture
def world(monkeypatch):
    return World(monkeypatch)


def test_controls_returns_zero_and_runs_two_scans_with_the_spec_parameters(world, tmp_path):
    """AC-20: two scans of size 16, enemy 8..24, 10 replicates, one per play (blob and damage)."""
    assert main(["controls", "--out", str(tmp_path)]) == 0
    assert len(world.scan_calls) == 2
    for call in world.scan_calls:
        assert (call["size"], call["enemy_from"], call["enemy_to"], call["replicates"]) == (16, 8, 24, 10)
    builds = [c["build"] for c in world.scan_calls]
    assert world.blob_build in builds and world.damage_build in builds
    assert builds == [world.blob_build, world.damage_build]          # identical first, then damage

def test_controls_calls_the_plays_with_size_16_and_the_default_damage_factor(world, tmp_path):
    """AC-20/AC-12/AC-23: blob_play(16) and damage_play(16) exactly; no factor override (default 1.2 stays)."""
    main(["controls", "--out", str(tmp_path)])
    assert world.blob_args == [((16,), {})]
    assert len(world.damage_args) == 1
    args, kwargs = world.damage_args[0]
    assert args == (16,)
    assert kwargs in ({}, {"factor": 1.2})


def test_controls_never_calls_reach_play(world, tmp_path):
    """AC-20/AC-23 (mutant catcher): reach is a study knob, not the planted control; controls must not build it."""
    main(["controls", "--out", str(tmp_path)])
    assert world.reach_args == []
    assert world.reach_build not in [c["build"] for c in world.scan_calls]


def test_controls_builds_one_row_per_fight_with_play_and_enemy_heads_labels(world, tmp_path):
    """AC-20: fight_row over every fight of every cell of both scans, labelled play (identical or damage) and enemy_heads."""
    main(["controls", "--out", str(tmp_path)])
    expected = set()
    for label, res in world.results.items():
        for c in res.cells:
            for f in c.fights:
                expected.add((id(f), label, c.enemy_heads))
    got = [(id(r), lab["play"], lab["enemy_heads"]) for r, lab in world.row_calls]
    assert len(got) == 2 * 17 * 2 == len(expected)
    assert set(got) == expected
    assert all(set(lab) == {"play", "enemy_heads"} for _, lab in world.row_calls)


def test_controls_writes_controls_csv_once_with_the_built_rows(world, tmp_path):
    """AC-20: write_rows once, path controls.csv in the out dir, rows are the fight_row dicts."""
    main(["controls", "--out", str(tmp_path)])
    assert len(world.write_calls) == 1
    rows, path = world.write_calls[0]
    assert Path(path).resolve() == (tmp_path / "controls.csv").resolve()
    assert len(rows) == 68
    assert sorted(id(r) for r in rows) == sorted(id(r) for r in world.dicts)
    assert [id(r) for r in rows] == [id(r) for r in world.dicts]     # file order is fight_row order
    assert [lab["play"] for _, lab in world.row_calls] == ["identical"] * 34 + ["damage"] * 34


def test_controls_reports_once_with_a_batch_of_both_scans(world, tmp_path):
    """AC-20: report called once with the out dir and a Batch whose scans are identical and damage."""
    main(["controls", "--out", str(tmp_path)])
    assert len(world.report_calls) == 1
    batch, out_dir = world.report_calls[0]
    assert Path(out_dir).resolve() == tmp_path.resolve()
    assert isinstance(batch, Batch)
    assert set(batch.scans) == {"identical", "damage"}
    assert list(batch.scans) == ["identical", "damage"]               # page section order
    assert batch.scans["identical"] is world.results["identical"]
    assert batch.scans["damage"] is world.results["damage"]
    assert sorted(id(r) for r in batch.rows) == sorted(id(r) for r in world.dicts)
    assert [id(r) for r in batch.rows] == [id(r) for r in world.dicts]


def test_controls_firing_example_is_first_fight_of_the_cell_at_16_enemies(world, tmp_path):
    """AC-20 Reading: firing_example[label] is the first fight of the cell with enemy_heads == 16."""
    main(["controls", "--out", str(tmp_path)])
    batch, _ = world.report_calls[0]
    assert set(batch.firing_example) == {"identical", "damage"}
    for label in ("identical", "damage"):
        cell16 = [c for c in world.results[label].cells if c.enemy_heads == 16]
        assert len(cell16) == 1
        assert batch.firing_example[label] is cell16[0].fights[0]
        assert batch.firing_example[label] is not cell16[0].fights[1]


def test_main_creates_the_out_dir_with_parents(world, tmp_path):
    """AC-20 Reading: main creates --out (parents included); the recorders create nothing themselves."""
    out = tmp_path / "x" / "y" / "out"
    assert main(["controls", "--out", str(out)]) == 0
    assert out.is_dir()
    assert Path(world.write_calls[0][1]).resolve() == (out / "controls.csv").resolve()


def test_default_out_dir_is_skilllab_out_under_the_working_directory(world, tmp_path, monkeypatch):
    """AC-20: without --out both outputs go to ./skilllab_out."""
    monkeypatch.chdir(tmp_path)
    assert main(["controls"]) == 0
    want = (tmp_path / "skilllab_out").resolve()
    assert Path(world.write_calls[0][1]).resolve() == want / "controls.csv"
    assert Path(world.report_calls[0][1]).resolve() == want
    assert want.is_dir()


def test_argv_none_reads_the_process_arguments(world, tmp_path, monkeypatch):
    """AC-20 (contract main(argv=None)): argv None means sys.argv[1:]."""
    monkeypatch.setattr(sys, "argv", ["skilllab", "controls", "--out", str(tmp_path)])
    assert main() == 0
    assert len(world.scan_calls) == 2


def test_unknown_command_returns_two_and_runs_nothing(world, tmp_path):
    """AC-20: an unknown command gives exit status 2 (returned, or SystemExit(2) from the parser)."""
    try:
        code = main(["frobnicate", "--out", str(tmp_path)])
    except SystemExit as exc:
        code = exc.code
    assert code == 2
    assert world.scan_calls == [] and world.write_calls == [] and world.report_calls == []


def test_controls_scan_every_headcount_not_the_bisection(world, tmp_path):
    """LAB-REV2-L4: scan() now bisects by default. The controls chart a dot per fight at every headcount 8 to 24 and the golden
    planted hash covers every fight of both scans, so the `controls` command asks for the linear sweep."""
    main(["controls", "--out", str(tmp_path)])
    assert [c["full_scan"] for c in world.scan_calls] == [True, True]
