# spec: batch runner spec (batch_spec.md) - `batch <name> --out <dir>` command
"""main(["batch", name, ...]) reaches batches.get and batches.run through module attributes."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from scripts.skilllab.__main__ import main  # noqa: E402

SENTINEL = object()


class World:
    def __init__(self, monkeypatch, tmp_path):
        self.run_calls, self.get_calls = [], []
        self.paths = {"csv": tmp_path / "x.csv", "run": tmp_path / "x_run.md", "page": tmp_path / "x_page.html"}

        def fake_run(defn, out_dir, scan_fn=None, workers=1):
            self.run_calls.append((defn, out_dir))
            return self.paths

        self.real_get = batches.get

        def get(name):
            self.get_calls.append(name)
            self.real_get(name)           # unknown names still raise ValueError
            return SENTINEL

        monkeypatch.setattr(batches, "get", get)
        monkeypatch.setattr(batches, "run", fake_run)


@pytest.fixture
def world(monkeypatch, tmp_path):
    return World(monkeypatch, tmp_path)


def run_main(argv):
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code


@pytest.mark.parametrize("name", ["formation", "focus_fire", "matchup", "landscape", "enemy_position", "combinations"])
def test_valid_name_runs_once_and_prints_three_paths(world, tmp_path, capsys, name):
    assert main(["batch", name, "--out", str(tmp_path / "o")]) == 0
    assert world.get_calls == [name]
    assert len(world.run_calls) == 1
    defn, out = world.run_calls[0]
    assert defn is SENTINEL and Path(out).resolve() == (tmp_path / "o").resolve()
    printed = capsys.readouterr().out.split()
    for p in world.paths.values():
        assert str(p) in printed


@pytest.mark.parametrize("argv", [["batch", "nonsense"], ["batch"]])
def test_unknown_or_missing_name_returns_two_and_prints_names(world, capsys, argv):
    assert run_main(argv) == 2
    assert world.run_calls == []
    out = capsys.readouterr().out
    assert all(n in out for n in ("formation", "focus_fire", "matchup", "landscape", "enemy_position", "combinations"))


def test_other_commands_do_not_reach_batches(world, tmp_path):
    assert run_main(["frobnicate", "--out", str(tmp_path)]) == 2
    assert world.run_calls == [] and world.get_calls == []
