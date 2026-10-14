# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-20 (reach control command)
"""main(["reach", ...]) scans plays.reach_play like controls scans its plays; siblings are replaced by recorders
on their own modules (main must reach them through module attributes)."""
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


def _fight(tag):
    return FightResult(outcome="side0", margin=0.1, strength_left=(0.5, 0.2), survivors=(8, 2),
                       heads=(16, 16), ticks=tag, first_contact_tick=1, firing=[(0, 1, 1)],
                       firing_unit_seconds=(0.25, 0.25))


def _scan_result():
    cells = [CellResult(enemy_heads=n, fights=[_fight(2 * n), _fight(2 * n + 1)], mean_margin=0.1, won=True)
             for n in range(8, 25)]
    return ScanResult(size=16, cells=cells, beats=None, loses_to=None)


class World:
    def __init__(self, monkeypatch):
        self.scan_calls, self.row_calls, self.write_calls, self.report_calls = [], [], [], []
        self.reach_args, self.blob_args, self.damage_args = [], [], []
        self.reach_build = lambda enemy_heads, swap: "reach-setup"
        self.result = _scan_result()

        def reach_play(*args, **kwargs):
            self.reach_args.append((args, kwargs))
            return self.reach_build

        def blob_play(*args, **kwargs):
            self.blob_args.append((args, kwargs))
            return lambda enemy_heads, swap: "blob-setup"

        def damage_play(*args, **kwargs):
            self.damage_args.append((args, kwargs))
            return lambda enemy_heads, swap: "damage-setup"

        def fake_scan(build, size, enemy_from, enemy_to, replicates=10, fight_fn=None, map_fn=None, full_scan=False, **kw):
            self.scan_calls.append(dict(build=build, size=size, enemy_from=enemy_from, enemy_to=enemy_to,
                                        replicates=replicates, full_scan=full_scan))
            return self.result

        def fake_fight_row(result, **labels):
            self.row_calls.append((result, labels))
            return dict(labels, ticks=result.ticks)

        def fake_write_rows(rows, path):
            self.write_calls.append((list(rows), path))

        def fake_report(batch, out_dir):
            self.report_calls.append((batch, out_dir))
            return str(Path(out_dir) / "report.html")

        monkeypatch.setattr(plays, "reach_play", reach_play)
        monkeypatch.setattr(plays, "blob_play", blob_play)
        monkeypatch.setattr(plays, "damage_play", damage_play, raising=False)
        monkeypatch.setattr(scan_mod, "scan", fake_scan)
        monkeypatch.setattr(rows_mod, "fight_row", fake_fight_row)
        monkeypatch.setattr(rows_mod, "write_rows", fake_write_rows)
        monkeypatch.setattr(report_mod, "report", fake_report)


@pytest.fixture
def world(monkeypatch):
    return World(monkeypatch)


def run_main(argv):
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code


def test_reach_default_factor_is_1_2_and_one_scan_with_the_spec_parameters(world, tmp_path):
    assert main(["reach", "--out", str(tmp_path)]) == 0
    assert world.reach_args == [((16,), {"factor": 1.2})]
    assert len(world.scan_calls) == 1
    call = world.scan_calls[0]
    assert (call["size"], call["enemy_from"], call["enemy_to"], call["replicates"]) == (16, 8, 24, 10)
    assert call["build"] is world.reach_build


def test_reach_factor_option_is_passed_through(world, tmp_path):
    assert main(["reach", "--factor", "1.5", "--out", str(tmp_path)]) == 0
    assert world.reach_args == [((16,), {"factor": 1.5})]


def test_reach_writes_reach_csv_with_play_reach_labels(world, tmp_path):
    main(["reach", "--out", str(tmp_path)])
    assert len(world.write_calls) == 1
    rows, path = world.write_calls[0]
    assert Path(path).resolve() == (tmp_path / "reach.csv").resolve()
    assert len(rows) == 17 * 2
    assert all(lab == {"play": "reach", "enemy_heads": lab["enemy_heads"]} for _, lab in world.row_calls)
    assert sorted({lab["enemy_heads"] for _, lab in world.row_calls}) == list(range(8, 25))


def test_reach_reports_once_with_the_titled_batch(world, tmp_path):
    main(["reach", "--out", str(tmp_path)])
    assert len(world.report_calls) == 1
    batch, out_dir = world.report_calls[0]
    assert Path(out_dir).resolve() == tmp_path.resolve()
    assert isinstance(batch, Batch)
    assert batch.title == "Skill lab reach control"
    assert list(batch.scans) == ["reach"] and batch.scans["reach"] is world.result
    cell16 = [c for c in world.result.cells if c.enemy_heads == 16][0]
    assert batch.firing_example["reach"] is cell16.fights[0]


def test_reach_prints_the_csv_path_and_the_page_path(world, tmp_path, capsys):
    assert main(["reach", "--out", str(tmp_path)]) == 0
    lines = capsys.readouterr().out.split()
    assert str(tmp_path / "reach.csv") in lines
    assert str(tmp_path / "report.html") in lines


@pytest.mark.parametrize("bad", ["0", "-1", "-0.5", "abc", "nan"])
def test_bad_factor_exits_non_zero_before_any_scan(world, tmp_path, bad):
    code = run_main(["reach", f"--factor={bad}", "--out", str(tmp_path)])
    assert code not in (0, None)
    assert world.scan_calls == [] and world.reach_args == [] and world.write_calls == []
    assert world.report_calls == []


def test_controls_still_never_calls_reach_play(world, tmp_path):
    main(["controls", "--out", str(tmp_path)])
    assert world.reach_args == []


def test_unknown_command_still_returns_two(world, tmp_path):
    code = run_main(["frobnicate", "--out", str(tmp_path)])
    assert code == 2
    assert world.scan_calls == []


def test_reach_command_scans_every_headcount_not_the_bisection(world, tmp_path):
    main(["reach", "--out", str(tmp_path)])
    assert [c["full_scan"] for c in world.scan_calls] == [True]
