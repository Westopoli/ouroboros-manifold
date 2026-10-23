# spec: docs/northstar/research/layer_dynamics/README.md::9 (process-pool runner, skill lab harness item 4)
"""Real engine, spawned workers, tiny fights. Red until scripts/skilllab/pool.py exists.

No speedup or time is asserted; the speed gate stays test_speed.py.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays  # noqa: E402
from scripts.skilllab.pool import FightPool  # noqa: E402
from scripts.skilllab.scan import scan  # noqa: E402


def _jobs():
    build = plays.blob_play(4)
    return [(build(enemy, swap), seed, swap)
            for enemy in (4, 5, 6) for swap in (False, True) for seed in (0,)]


def test_map_results_equal_for_one_two_and_four_workers():
    """Same jobs, same FightResults in the same order whatever the worker count."""
    jobs = _jobs()
    results = {}
    for workers in (1, 2, 4):
        with FightPool(workers) as fp:
            results[workers] = fp.map(jobs)
        assert len(results[workers]) == len(jobs)
    assert results[2] == results[1]
    assert results[4] == results[1]


def test_pooled_scan_equals_serial_scan_field_by_field():
    """Blob 4 against 3..5, 2 replicates: workers 2 scan equals the serial scan."""
    build = plays.blob_play(4)
    serial = scan(build, 4, 3, 5, replicates=2)
    with FightPool(2) as fp:
        pooled = scan(build, 4, 3, 5, replicates=2, map_fn=fp.map)
    assert pooled.size == serial.size and (pooled.ceiling_hit, pooled.multi_flip) == (serial.ceiling_hit, serial.multi_flip)
    assert (pooled.beats, pooled.loses_to) == (serial.beats, serial.loses_to)
    assert len(pooled.cells) == len(serial.cells)
    for a, b in zip(pooled.cells, serial.cells):
        assert (a.enemy_heads, a.mean_margin, a.won) == (b.enemy_heads, b.mean_margin, b.won)
        assert a.fights == b.fights
    assert pooled == serial


def test_pooled_find_break_even_equals_serial():
    """Blob 4 against 3..5, replicates 2, near 3, one round: workers 2 equals the serial result."""
    from scripts.skilllab.breakeven import find_break_even
    build = plays.blob_play(4)
    kw = dict(replicates=2, near_replicates=3, max_rounds=1)
    serial = find_break_even(build, 4, 3, 5, **kw)
    with FightPool(2) as fp:
        pooled = find_break_even(build, 4, 3, 5, map_fn=fp.map, **kw)
    assert pooled == serial


def test_pooled_bisection_scan_equals_serial_and_the_full_scan_agrees_on_the_break_even():
    """LAB-REV2-L4: the default scan bisects; through the pool it must still equal the serial run, and the linear sweep (which
    fights every headcount) reads the same break-even on the same engine."""
    build = plays.blob_play(4)
    serial = scan(build, 4, 2, 8, replicates=2)
    with FightPool(2) as fp:
        assert scan(build, 4, 2, 8, replicates=2, map_fn=fp.map) == serial
        full = scan(build, 4, 2, 8, replicates=2, map_fn=fp.map, full_scan=True)
    assert [c.enemy_heads for c in full.cells] == list(range(2, 9))
    assert (full.beats, full.loses_to, full.ceiling_hit) == (serial.beats, serial.loses_to, serial.ceiling_hit)
