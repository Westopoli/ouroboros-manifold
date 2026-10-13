# spec: skill lab memory - trim_series drops per-tick series, keeps row values; batches keep only the charted example whole
"""No engine: fake fights."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, pool, rows  # noqa: E402
from scripts.skilllab.contract import CellResult, ScanResult, trim_series  # noqa: E402
from tests.skilllab.fakes_batches import fight  # noqa: E402


def _full(**kw):
    f = fight(**kw)
    f.firing = [(t, 3, 3) for t in range(0, 500, 5)]
    f.trace, f.states, f.weighted = [(1,)], [(1,)], [(1, 2, 3)]
    f.weighted_unit_seconds = (1.0, 2.0)
    return f


def test_trim_series_keeps_every_row_value_and_empties_series():
    f = _full()
    t = trim_series(f)
    assert t.firing == [] and t.trace == [] and t.states == [] and t.weighted == []
    assert rows.fight_row(t, a=1) == rows.fight_row(f, a=1)
    assert f.firing  # the original is untouched


def test_trim_series_leaves_off_series_off():
    f = fight()
    t = trim_series(f)
    assert t.trace is None and t.states is None and t.weighted is None


def test_trimmed_keeps_only_the_example_whole():
    fs = [_full() for _ in range(4)]
    res = ScanResult(size=8, cells=[CellResult(8, fs, 0.0, False)], beats=None, loses_to=None, win_margin=0.0)
    batches._trimmed(res, fs[0])
    out = res.cells[0].fights
    assert out[0] is fs[0] and out[0].firing
    assert all(f.firing == [] for f in out[1:])


def test_worker_trims_all_but_seed_zero_unswapped(monkeypatch):
    monkeypatch.setattr(pool.fight_module, "fight", lambda s, seed, swap, e: _full())
    monkeypatch.setattr(pool, "_engine", pool.engine_module.Engine.__new__(pool.engine_module.Engine))
    monkeypatch.setattr(pool, "_lean", True)
    assert pool.run_job((None, 0, False)).firing
    assert pool.run_job((None, 1, False)).firing == []
    assert pool.run_job((None, 0, True)).firing == []
    monkeypatch.setattr(pool, "_lean", False)
    assert pool.run_job((None, 1, False)).firing
