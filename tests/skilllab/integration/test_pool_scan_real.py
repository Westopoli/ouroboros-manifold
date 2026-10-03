# spec: parallel batches - a scan through FightPool equals the serial scan, with and without a shared library path
"""Real library, spawned workers. Red until FightPool takes library_path and workers load a shared build."""
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, plays  # noqa: E402
from scripts.skilllab.pool import FightPool  # noqa: E402
from scripts.skilllab.scan import scan  # noqa: E402


def _fights(result):
    return [[dataclasses.asdict(f) for f in c.fights] for c in result.cells]


def _scan(**kw):
    return scan(plays.blob_play(8), 8, 6, 8, replicates=3, **kw)


def test_pooled_scan_equals_serial_and_with_explicit_library_path():
    serial = _fights(_scan())
    with FightPool(3) as fp:
        assert _fights(_scan(map_fn=fp.map)) == serial
    path = engine._cached_library()
    with FightPool(2, library_path=path) as fp:
        assert _fights(_scan(map_fn=fp.map)) == serial
