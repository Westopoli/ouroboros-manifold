# spec: parallel batches - batches.run(workers=N) opens one FightPool per run and threads map_fn into every scan
"""batches.run with a recording FightPool fake and the FakeScan; no engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, pool  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, faked  # noqa: E402


class RecPool:
    created = []

    def __init__(self, workers, *a, **k):
        self.workers, self.closed = workers, False
        RecPool.created.append(self)

    def map(self, jobs):
        return [j for j in jobs]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def rec(monkeypatch):
    RecPool.created = []
    monkeypatch.setattr(pool, "FightPool", RecPool)
    return RecPool


def _defn(name="formation"):
    return faked(batches.get(name))


def _bytes(paths):
    return {k: Path(p).read_bytes() for k, p in paths.items()}


def test_one_worker_creates_no_pool_and_passes_no_map_fn(tmp_path, rec):
    fake = FakeScan()
    batches.run(_defn(), tmp_path, scan_fn=fake, workers=1)
    assert rec.created == []
    assert fake.calls and all("map_fn" not in c["kw"] for c in fake.calls)


def test_default_is_one_worker(tmp_path, rec):
    fake = FakeScan()
    batches.run(_defn(), tmp_path, scan_fn=fake)
    assert rec.created == [] and all("map_fn" not in c["kw"] for c in fake.calls)


def test_three_workers_one_pool_map_fn_on_every_scan_and_closed(tmp_path, rec):
    fake = FakeScan()
    batches.run(_defn("landscape"), tmp_path, scan_fn=fake, workers=3)
    (fp,) = rec.created
    assert fp.workers == 3 and fp.closed
    assert len(fake.calls) > 1
    assert all(c["kw"].get("map_fn") == fp.map for c in fake.calls)


def test_reference_scans_get_map_fn_too(tmp_path, rec):
    defn = _defn("landscape")
    assert any(getattr(c, "reference", None) is not None for c in defn.cells)
    fake = FakeScan()
    batches.run(defn, tmp_path, scan_fn=fake, workers=3)
    assert any(c["label"].endswith("#ref") for c in fake.calls)
    assert all(c["kw"].get("map_fn") == rec.created[0].map for c in fake.calls)


def test_pool_closed_when_a_scan_raises(tmp_path, rec):
    class Boom(FakeScan):
        def __call__(self, *a, **k):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        batches.run(_defn(), tmp_path, scan_fn=Boom(), workers=3)
    (fp,) = rec.created
    assert fp.closed


def test_outputs_byte_identical_between_one_and_three_workers(tmp_path, rec):
    serial = batches.run(_defn(), tmp_path / "a", scan_fn=FakeScan(), workers=1)
    par = batches.run(_defn(), tmp_path / "b", scan_fn=FakeScan(), workers=3)
    assert len(rec.created) == 1
    assert _bytes(serial).keys() == _bytes(par).keys() and len(serial) == 4
    for k in serial:
        assert Path(serial[k]).name == Path(par[k]).name
        assert Path(serial[k]).read_bytes() == Path(par[k]).read_bytes()


@pytest.mark.parametrize("bad", [0, -1])
def test_non_positive_workers_raise_before_anything_is_created(tmp_path, rec, bad):
    fake = FakeScan()
    with pytest.raises(ValueError):
        batches.run(_defn(), tmp_path / "o", scan_fn=fake, workers=bad)
    assert rec.created == [] and fake.calls == []
