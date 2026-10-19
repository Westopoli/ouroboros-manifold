# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-28; docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Rulings in force::13 and Pieces::S
"""Speed guards: AC 28 (30 s) and the scale marks of ruling 13, each with a planted-slowdown control (LAB-REV2-S).

Wall-clock is the point of this file; it runs alone. The library build is excluded (the Engine is built before the clock starts, and a
pool is warmed by one tiny map before the scan is timed).

INTERFACE (S builds nothing; "tests only". Everything below exists on push/labrev2-lab at 4c638fc0):
  engine.Engine(); fight.fight(setup, seed, swap, engine) -> FightResult; plays.blob_play(16)(enemy_heads, swap) -> Setup;
  scan.scan(build, size, enemy_from, enemy_to, replicates, fight_fn=None, map_fn=None, full_scan=False) -> ScanResult
    (default = coarse pass every 8 headcounts then bisection; full_scan=True fights every headcount);
  pool.FightPool(workers).map(jobs); tests/skilllab/fakes_scans.py (ScriptedFight, fake_builds, _fr) for the fakes.

MARKS (spec ruling 13, all DRAFT, Westley's; pinned here only because the spec gives them, never loosened here):
  FIGHT_MARK_SECONDS = 1.5   one 16 v 48 fight on one worker, engine already built
  SCAN_MARK_SECONDS  = 90    one play scan 8 to 48 at 3 replicates at 12 workers (the default scan, which bisects; the mark rests on L4)
  LIMIT_SECONDS      = 30    AC 28: a scan of 16 against 12 to 24, 10 replicates, both orders, every headcount (full_scan=True), one process
Ruling 13 also names "the first coarse knob batch under 4 h wall at 12 workers": that is a run of the batch, not a unit guard; it is
checked by the overseer at batch time and has no test here (reported as a stop).

HOW A GUARD IS PROVEN (planted-slowdown controls): the detector is `within_mark(seconds, mark, what)`, the only place a mark is
compared, and the measure_* functions are the only places a time is read. Each guard measures with the real clock. Each control
runs the same measure with a planted slowdown on a VirtualClock (time.perf_counter plus the seconds a fake slept, so no control
waits) and requires `within_mark` to fail; a complement runs the same measure with the slowdown set to zero and requires it to
pass, so the detector is not simply always failing (the fight's complement checks that the proxy is transparent instead, because
the real engine's speed is the guard's own question and depends on the machine). The fight control plants a per-tick sleep in a proxy around the real engine
(the spec's "fake engine that sleeps per tick"); the scan controls plant a per-fight sleep in a fake 12-worker pool.
"""
import math
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
HERE = str(Path(__file__).resolve().parents[1])
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from fakes_scans import ScriptedFight, fake_builds  # noqa: E402
from scripts.skilllab import engine, fight, plays, scan  # noqa: E402

LIMIT_SECONDS = 30.0            # AC 28 (existing, Westley's)
FIGHT_MARK_SECONDS = 1.5        # ruling 13, DRAFT
SCAN_MARK_SECONDS = 90.0        # ruling 13, DRAFT
SCAN_WORKERS = 12
SCAN_REPLICATES = 3
SCAN_FROM, SCAN_TO = 8, 48      # the spec's "8 to 48"
FIGHT_SIZE, FIGHT_ENEMY = 16, 48

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="12 workers, a real scan 8 to 48; set OM_LAB_SLOW=1")


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


# ---- the detector and the measures -------------------------------------------------------------------------------------------------

class VirtualClock:
    """time.perf_counter plus the seconds a planted fake 'slept'; a fake calls .sleep(dt) instead of waiting."""

    def __init__(self):
        self.slept = 0.0

    def __call__(self):
        return time.perf_counter() + self.slept

    def sleep(self, seconds):
        self.slept += seconds


def within_mark(seconds, mark, what):
    """THE detector: strictly under the mark, as the AC 28 guard always read it."""
    assert seconds < mark, "%s took %.1f s, the mark is %.1f s" % (what, seconds, mark)


def measure_fight(eng, clock=time.perf_counter):
    """Seconds for one 16 v 48 fight (seed 0, unswapped) on `eng`; returns (seconds, FightResult)."""
    setup = plays.blob_play(FIGHT_SIZE)(FIGHT_ENEMY, False)
    start = clock()
    result = fight.fight(setup, 0, False, eng)
    return clock() - start, result


def measure_scan(build, map_fn=None, fight_fn=None, clock=time.perf_counter, full_scan=False):
    """Seconds for one play scan 8 to 48 at 3 replicates; returns (seconds, ScanResult)."""
    start = clock()
    result = scan.scan(build, FIGHT_SIZE, SCAN_FROM, SCAN_TO, replicates=SCAN_REPLICATES, map_fn=map_fn, fight_fn=fight_fn,
                       full_scan=full_scan)
    return clock() - start, result


class SleepyEngine:
    """Proxy around a real Engine: every step() also 'sleeps' `per_tick` seconds on the virtual clock."""

    def __init__(self, inner, clock, per_tick):
        self._inner, self._clock, self._per_tick = inner, clock, per_tick

    def step(self, *args, **kw):
        self._clock.sleep(self._per_tick)
        return self._inner.step(*args, **kw)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class SleepyPool:
    """A fake pool of `workers` workers: each fight costs `per_fight` virtual seconds, a map of n jobs takes ceil(n / workers)
    rounds of that. Results come from a ScriptedFight, in job order (the order the real pool guarantees)."""

    def __init__(self, clock, per_fight, workers=SCAN_WORKERS):
        self.clock, self.per_fight, self.workers = clock, per_fight, workers
        self.fights = 0
        self._fight_fn = ScriptedFight(be_of=lambda setup: 16)

    def map(self, jobs):
        jobs = list(jobs)
        self.clock.sleep(math.ceil(len(jobs) / self.workers) * self.per_fight)
        self.fights += len(jobs)
        return [self._fight_fn(*job) for job in jobs]


def fake_build():
    """A BuildFn the fakes read: the scan is fought by ScriptedFight, side 0 winning up to 16 enemies."""
    return fake_builds()("p", "play", {})


# ---- AC 28 (existing mark) ---------------------------------------------------------------------------------------------------------

def _ac28(fight_fn=None, clock=time.perf_counter):
    start = clock()
    result = scan.scan(plays.blob_play(16) if fight_fn is None else fake_build(), 16, 12, 24, replicates=10, fight_fn=fight_fn,
                       full_scan=True)
    return clock() - start, result


def test_scan_16_against_12_to_24_finishes_under_30_seconds(library):
    """AC 28: perf_counter around scan only; the result must hold all the work, so a stub cannot pass.

    TD-LAB-REV2-S-fullscan: the default scan now bisects (L4), so the 13-headcount scan this guard has always timed asks for
    full_scan=True; with the default the 13 cells and the 260 fights below would not exist."""
    elapsed, result = _ac28()
    assert [c.enemy_heads for c in result.cells] == list(range(12, 25))
    assert all(len(c.fights) == 20 for c in result.cells)
    # the fights really ran: a stub returning canned FightResult objects has no ticks, no firing series
    for c in result.cells:
        for f in c.fights:
            assert f.ticks > 0, (c.enemy_heads, f.ticks)
            assert f.heads == (16, c.enemy_heads), (c.enemy_heads, f.heads)
            assert len(f.firing) > 0, c.enemy_heads
    within_mark(elapsed, LIMIT_SECONDS, "scan")


def test_ac28_planted_slowdown_control_a_fake_that_sleeps_per_fight_fails_the_30_second_mark():
    """260 fights at 0.2 virtual seconds each is 52 s: over the 30 s mark. The same scan with a zero sleep passes."""
    clock = VirtualClock()
    inner = ScriptedFight(be_of=lambda setup: 16)

    def slow(setup, seed, swap):
        clock.sleep(0.2)
        return inner(setup, seed, swap)
    elapsed, result = _ac28(slow, clock)
    assert sum(len(c.fights) for c in result.cells) == 260          # the plant sits in all the work the guard counts
    with pytest.raises(AssertionError, match="took .* s, the mark is 30.0 s"):
        within_mark(elapsed, LIMIT_SECONDS, "scan")


def test_ac28_planted_slowdown_control_complement_the_same_fake_with_no_sleep_passes():
    clock = VirtualClock()
    inner = ScriptedFight(be_of=lambda setup: 16)
    elapsed, result = _ac28(lambda setup, seed, swap: inner(setup, seed, swap), clock)
    assert sum(len(c.fights) for c in result.cells) == 260
    within_mark(elapsed, LIMIT_SECONDS, "scan")


# ---- ruling 13: one 16 v 48 fight under 1.5 s on one worker -----------------------------------------------------------------------------

def test_one_16_v_48_fight_finishes_under_1_5_seconds_on_one_worker(library):
    seconds, result = measure_fight(library)
    assert result.heads == (16, 48) and result.ticks > 0 and len(result.firing) > 0       # the fight really ran
    within_mark(seconds, FIGHT_MARK_SECONDS, "one 16 v 48 fight")


def test_fight_planted_slowdown_control_an_engine_that_sleeps_per_tick_fails_the_1_5_second_mark(library):
    """10 ms of virtual sleep per tick. The fight is at least 150 ticks, so the plant alone is over the mark."""
    clock = VirtualClock()
    seconds, result = measure_fight(SleepyEngine(library, clock, 0.01), clock)
    assert result.heads == (16, 48) and result.ticks >= 150        # a shorter fight would let the plant hide under the mark
    assert clock.slept >= 0.01 * result.ticks
    with pytest.raises(AssertionError, match="the mark is 1.5 s"):
        within_mark(seconds, FIGHT_MARK_SECONDS, "one 16 v 48 fight")


def test_fight_planted_slowdown_control_complement_the_proxy_with_no_sleep_is_transparent(library):
    """Proves the proxy and the virtual clock add nothing by themselves: with a zero sleep the same fight gives the same result and
    the clock gains no virtual time, so the only thing that can trip the detector in the planted run is the sleep. (That the unplanted
    fight passes the mark is the guard above; this complement does not depend on how fast the machine is.)"""
    clock = VirtualClock()
    seconds, result = measure_fight(SleepyEngine(library, clock, 0.0), clock)
    _plain_seconds, plain = measure_fight(library)
    assert clock.slept == 0.0 and result == plain


# ---- ruling 13: one play scan 8 to 48 at 3 replicates under 90 s at 12 workers (the default scan; rests on L4's bisection) ----------------

@SLOW
def test_play_scan_8_to_48_at_3_replicates_finishes_under_90_seconds_at_12_workers(library):
    from scripts.skilllab.pool import FightPool
    build = plays.blob_play(16)
    with FightPool(SCAN_WORKERS) as fp:
        fp.map([(build(16, False), 0, False)])        # spawn the 12 workers and load their library before the clock starts
        seconds, result = measure_scan(build, map_fn=fp.map)
    cells = [c.enemy_heads for c in result.cells]
    assert cells[0] == SCAN_FROM and cells[-1] == SCAN_TO and cells == sorted(cells)
    assert all(len(c.fights) == 2 * SCAN_REPLICATES for c in result.cells)
    assert all(f.ticks > 0 for c in result.cells for f in c.fights)
    assert len(cells) < SCAN_TO - SCAN_FROM + 1, cells          # bisection ran: the mark is not met by fighting all 41 headcounts
    within_mark(seconds, SCAN_MARK_SECONDS, "play scan 8 to 48")


def test_scan_planted_slowdown_control_a_pool_that_sleeps_per_fight_fails_the_90_second_mark():
    """30 virtual seconds per fight on a 12-worker fake pool: a bisecting scan is 36 coarse fights (3 rounds of 12) plus a few
    bisection rounds, every one at least 30 s, over the mark."""
    clock = VirtualClock()
    pool = SleepyPool(clock, 30.0)
    seconds, result = measure_scan(fake_build(), map_fn=pool.map, clock=clock)
    assert pool.fights >= 6 * 6 and result.cells[0].enemy_heads == SCAN_FROM and result.cells[-1].enemy_heads == SCAN_TO
    with pytest.raises(AssertionError, match="the mark is 90.0 s"):
        within_mark(seconds, SCAN_MARK_SECONDS, "play scan 8 to 48")


def test_scan_planted_slowdown_control_complement_the_same_pool_with_no_sleep_passes():
    clock = VirtualClock()
    pool = SleepyPool(clock, 0.0)
    seconds, result = measure_scan(fake_build(), map_fn=pool.map, clock=clock)
    assert pool.fights >= 6 * 6 and clock.slept == 0.0
    within_mark(seconds, SCAN_MARK_SECONDS, "play scan 8 to 48")


def test_the_90_second_mark_rests_on_bisection_the_same_slow_pool_passes_by_bisecting_and_fails_fighting_every_headcount():
    """5 virtual seconds per fight: the bisecting scan stays under 90 s, the full scan (41 headcounts, 246 fights, 21 rounds of 12)
    is over it. This is why L4's bisection is a precondition of the mark."""
    bis_clock, full_clock = VirtualClock(), VirtualClock()
    bis_pool, full_pool = SleepyPool(bis_clock, 5.0), SleepyPool(full_clock, 5.0)
    bis_seconds, bis = measure_scan(fake_build(), map_fn=bis_pool.map, clock=bis_clock)
    full_seconds, full = measure_scan(fake_build(), map_fn=full_pool.map, clock=full_clock, full_scan=True)
    assert len(full.cells) == SCAN_TO - SCAN_FROM + 1 and len(bis.cells) < len(full.cells)
    within_mark(bis_seconds, SCAN_MARK_SECONDS, "bisecting scan")
    with pytest.raises(AssertionError):
        within_mark(full_seconds, SCAN_MARK_SECONDS, "full scan")
