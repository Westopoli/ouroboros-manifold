# spec: parallel batches - `batch <name> --out <dir> [--workers N]`
"""main(["batch", ...]) passes --workers to batches.run; bad values exit non-zero before any batch runs."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from scripts.skilllab.__main__ import main  # noqa: E402


@pytest.fixture
def calls(monkeypatch, tmp_path):
    got = []

    def fake_run(defn, out_dir, scan_fn=None, workers=1):
        got.append((defn, Path(out_dir), workers))
        return {"csv": tmp_path / "x.csv"}

    monkeypatch.setattr(batches, "run", fake_run)
    return got


def run_main(argv):
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code


def test_default_workers_is_one(calls, tmp_path):
    assert main(["batch", "formation", "--out", str(tmp_path / "o")]) == 0
    assert len(calls) == 1 and calls[0][2] == 1


def test_workers_flag_is_passed_through(calls, tmp_path):
    assert main(["batch", "formation", "--out", str(tmp_path / "o"), "--workers", "6"]) == 0
    assert calls[0][2] == 6 and calls[0][1].resolve() == (tmp_path / "o").resolve()


def test_workers_flag_before_positional(calls, tmp_path):
    assert main(["batch", "--workers", "2", "formation", "--out", str(tmp_path / "o")]) == 0
    assert calls[0][2] == 2


@pytest.mark.parametrize("bad", ["0", "-2", "x", "1.5"])
def test_bad_workers_exit_nonzero_and_run_nothing(calls, tmp_path, bad):
    code = run_main(["batch", "formation", "--out", str(tmp_path / "o"), "--workers", bad])
    assert code not in (0, None)
    assert calls == []


def test_unknown_name_still_returns_two_and_lists_names(calls, tmp_path, capsys):
    assert main(["batch", "nonsense", "--out", str(tmp_path / "o"), "--workers", "4"]) == 2
    out = capsys.readouterr().out
    for n in batches.NAMES:
        assert n in out
    assert calls == []


def test_missing_name_returns_two(calls, tmp_path):
    assert main(["batch", "--out", str(tmp_path / "o")]) == 2 and calls == []
