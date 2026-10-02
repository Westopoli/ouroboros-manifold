# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S::first bullet (per-tick trace)
# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase B::first paragraph (position trace, wave A1)
"""The per-tick trace recorded through the production library (om_unit_get_pos, om_unit_get_target,
om_unit_get_facing; the last two already exist in csrc, no new C getter is needed).

Entry layout, ordering and the rule for units that die are fixed in tests/skilllab/test_trace.py.
Golden rows: the mirror and numbers controls of tests/skilllab/golden_hashes.json are re-hashed with the trace
on and with it explicitly off; both must equal the golden values, so recording cannot move a row byte.
"""
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays, rows, scan  # noqa: E402

GOLDEN = json.loads((ROOT / "tests" / "skilllab" / "golden_hashes.json").read_text())
REPLICATES = 10


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def traced(build, trace=True):
    def make(enemy_heads, swap):
        return dataclasses.replace(build(enemy_heads, swap), trace=trace)
    return make


def run(size, enemies, seed=0, swap=False, trace=True, max_ticks=1500):
    setup = dataclasses.replace(plays.blob_play(size)(enemies, swap), trace=trace, max_ticks=max_ticks)
    return fight.fight(setup, seed, swap)


def trace_bytes(result):
    return repr(result.trace).encode()


@pytest.fixture(scope="module")
def mirror_fight(library):
    return run(4, 4, seed=1, max_ticks=500)


@pytest.fixture(scope="module")
def lopsided_fight(library):
    return run(16, 8, seed=2)


def test_trace_has_one_entry_per_unit_per_tick_in_id_order(mirror_fight):
    r = mirror_fight
    ids = list(range(1, 9))
    assert len(r.trace) == (r.ticks + 1) * len(ids)
    assert [(e[0], e[1]) for e in r.trace] == [(t, u) for t in range(r.ticks + 1) for u in ids]


def test_trace_reads_the_library_position_target_and_facing(mirror_fight):
    """Real values: units move, a unit acquires a target on the other side, and facing changes."""
    t = mirror_fight.trace
    first = {e[1]: e for e in t if e[0] == 0}
    last = {e[1]: e for e in t if e[0] == mirror_fight.ticks}
    assert any(first[u][2:4] != last[u][2:4] for u in first), "no unit moved"
    side1 = set(range(5, 9))
    aimed = [(e[1], e[4]) for e in t if e[4] != 0]
    assert aimed, "no unit ever had a target"
    assert all((u in side1) != (tg in side1) for u, tg in aimed), "a target on the aimer's own side"
    assert len({e[5] for e in t}) > 8, "facing never changes"
    assert all(e[4] == 0 for e in t if e[0] == 0)


def test_trace_covers_units_that_die(lopsided_fight):
    r = lopsided_fight
    ids = sorted({e[1] for e in r.trace})
    assert len(ids) == 24 and len(r.trace) == (r.ticks + 1) * 24
    deaths = {}
    for u in ids:
        flags = [e[6] for e in r.trace if e[1] == u]
        assert flags == sorted(flags, reverse=True), "unit %d comes back to life" % u    # True... then False...
        if not flags[-1]:
            deaths[u] = flags.index(False)
    assert deaths, "nobody died, the control fight is vacuous"
    final = [e for e in r.trace if e[0] == r.ticks]
    assert sum(1 for e in final if e[6] and e[1] <= 16) == r.survivors[0]
    assert sum(1 for e in final if e[6] and e[1] > 16) == r.survivors[1]
    for u, d in deaths.items():
        mine = [e for e in r.trace if e[1] == u]
        assert all(e[2:4] == mine[d][2:4] and e[5] == mine[d][5] and e[4] == 0 for e in mine[d:])


def test_same_seed_gives_byte_identical_traces_and_other_seeds_differ(library):
    a, b = run(4, 4, seed=3, max_ticks=300), run(4, 4, seed=3, max_ticks=300)
    assert len(a.trace) > 0 and trace_bytes(a) == trace_bytes(b)
    assert trace_bytes(a) != trace_bytes(run(4, 4, seed=4, max_ticks=300))          # positive control
    assert trace_bytes(a) != trace_bytes(run(4, 4, seed=3, swap=True, max_ticks=300))


def test_trace_does_not_change_the_row(library):
    on, off = run(8, 8, seed=5, max_ticks=600), run(8, 8, seed=5, trace=False, max_ticks=600)
    assert off.trace is None
    assert rows.fight_row(on) == rows.fight_row(off)
    assert on.firing == off.firing


def _csv_hash(tmp_path, name, row_list):
    path = tmp_path / (name + ".csv")
    rows.write_rows(row_list, path)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _cell_rows(name, cell_result):
    return [rows.fight_row(f, play=name, enemy_heads=cell_result.enemy_heads) for f in cell_result.fights]


@pytest.mark.parametrize("trace", [False, True])
@pytest.mark.parametrize("key,size,enemies", [("mirror", 16, 16), ("numbers", 16, 8)])
def test_control_rows_equal_golden_with_trace_off_and_on(library, tmp_path, key, size, enemies, trace):
    """Trace off: the rows are byte-identical to the golden hashes. Trace on: the rows still are."""
    cell = scan.cell(traced(plays.blob_play(size), trace), enemies, REPLICATES)
    assert (cell.fights[0].trace is not None) == trace
    assert _csv_hash(tmp_path, key, _cell_rows(key, cell)) == GOLDEN[key]
