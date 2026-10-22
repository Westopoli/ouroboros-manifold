# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::S (speed); Architect ruling 2026-10-22 for LAB-REV2-SPEED-1B (Westley may veto)
"""LAB-REV2-SPEED-1B (stage 1B): the CPU-time acceptance of the three firing.py levers on top of the stage-one epoch cache.

The builder owns scripts/skilllab/firing.py and engine.py; this file only pins the mark they must reach. The lever tests are in
test_speed1b_levers.py. The stage-one tests (test_speed_equal.py) keep running and keep proving equality at the old mark 0.75.

  ratio = time.process_time spent by the live firing / by the frozen reference tests/skilllab/ref_firing_rev2.py (firing.py at 30f827b3),
  the two interleaved fight by fight in one process, 26 fights (blob_play(16) against 12 to 24 enemies, both orders), the whole
  FightResult of every fight compared too. Wall time is printed beside it and never judged.

RED today (stage one built): measured ratio 0.714 (limit 0.55). POSITIVE CONTROLS: a planted CPU slowdown, and a candidate exactly as slow
as stage one (ratio 0.72), fail the check; a fast candidate passes; a sleep does not move a CPU measure; the constant is pinned.
"""
import contextlib
import dataclasses
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HERE = str(Path(__file__).resolve().parents[1])
for _p in (str(ROOT), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ref_firing_rev2 as ref  # noqa: E402
from scripts.skilllab import engine as engine_mod, fight, firing, plays  # noqa: E402

# DRAFT, Westley's number. Stage one (epoch cache only) measured 0.714 and was held to the stage-one limit 0.75 in test_speed_equal.py; stage
# 1B (the levers a to d in firing.py) must reach 0.55 (the estimate is 0.5, with margin). The combined 0.5 mark (DRAFT-lab-speed-ratio) is SPEED-2's.
DRAFT_LAB_SPEED_RATIO_1B = 0.55  # DRAFT: process_time(live firing) / process_time(frozen reference) must not exceed it. The mark is Westley's.
STAGE_ONE_MEASURED = 0.714
STAGE_ONE_LIMIT = 0.75
RATIO_ENEMIES = range(12, 25)
RATIO_SWAPS = (False, True)
FIRING_FUNCTIONS = ("count_able", "count_weighted", "states")


@pytest.fixture(scope="module")
def library():
    return engine_mod.Engine()


@contextlib.contextmanager
def firing_of(module):
    """fight.py calls the three names it imported from firing; point them at `module` for the duration (fight.py itself is untouched)."""
    saved = {n: getattr(fight, n) for n in FIRING_FUNCTIONS}
    try:
        for n in FIRING_FUNCTIONS:
            setattr(fight, n, getattr(module, n))
        yield module
    finally:
        for n, f in saved.items():
            setattr(fight, n, f)


def fight_with(module, setup, seed, swap, eng):
    with firing_of(module):
        return fight.fight(setup, seed, swap, eng)


def assert_results_equal(a, b, what="fight"):
    """The whole FightResult, field by field first so a failure names the field, then as a dataclass."""
    for f in dataclasses.fields(a):
        assert getattr(a, f.name) == getattr(b, f.name), "%s: FightResult.%s differs" % (what, f.name)
    assert a == b, what


def burn(seconds):
    """Spend CPU (not sleep) for `seconds` of process time."""
    end = time.process_time() + seconds
    while time.process_time() < end:
        pass


def measure_ratio(new_fn, ref_fn, items):
    """Run new_fn(item) and ref_fn(item) for every item, alternating which goes first. Returns (ratio, cpu_new, cpu_ref, wall_new, wall_ref):
    the ratio is time.process_time of the live side over the reference side (wall time is for the report only)."""
    cpu = {"new": 0.0, "ref": 0.0}
    wall = {"new": 0.0, "ref": 0.0}
    for i, item in enumerate(items):
        order = (("new", new_fn), ("ref", ref_fn)) if i % 2 == 0 else (("ref", ref_fn), ("new", new_fn))
        for label, fn in order:
            c0, w0 = time.process_time(), time.perf_counter()
            fn(item)
            cpu[label] += time.process_time() - c0
            wall[label] += time.perf_counter() - w0
    return cpu["new"] / cpu["ref"], cpu["new"], cpu["ref"], wall["new"], wall["ref"]


def within_ratio(measured, limit=None):
    """THE detector: the CPU ratio must not exceed the (DRAFT) stage-1B limit."""
    limit = DRAFT_LAB_SPEED_RATIO_1B if limit is None else limit
    ratio, cpu_new, cpu_ref, wall_new, wall_ref = measured
    assert ratio <= limit, ("CPU ratio %.3f (live %.2f s / reference %.2f s) is over the DRAFT limit %.2f; wall %.2f s / %.2f s = %.3f"
                            % (ratio, cpu_new, cpu_ref, limit, wall_new, wall_ref, wall_new / wall_ref))


def test_stage_1b_speed_ratio_of_the_live_firing_against_the_frozen_reference(library):
    """Acceptance (stage 1B): 26 fights, blob_play(16) against 12 to 24, both orders, live and reference interleaved in this process.
    RED on the stage-one tree (ratio about 0.71 over the limit 0.55). Results are compared too, so a faster-but-different firing cannot pass."""
    items = [(enemies, swap) for enemies in RATIO_ENEMIES for swap in RATIO_SWAPS]
    seen = {}

    def run(label, module):
        def go(item):
            enemies, swap = item
            seen[(label, item)] = fight_with(module, plays.blob_play(16)(enemies, swap), 0, swap, library)
        return go

    measured = measure_ratio(run("new", firing), run("ref", ref), items)
    print("\nLAB-REV2-SPEED-1B ratio %.3f  cpu live %.2f s ref %.2f s  wall live %.2f s ref %.2f s (limit DRAFT %.2f, stage one %.3f, %d fights each)"
          % (measured[0], measured[1], measured[2], measured[3], measured[4], DRAFT_LAB_SPEED_RATIO_1B, STAGE_ONE_MEASURED, len(items)))
    for item in items:
        assert_results_equal(seen[("new", item)], seen[("ref", item)], "enemies %d swap %s" % item)
    within_ratio(measured)


def _spin_items(n=8):
    return list(range(n))


def test_control_a_planted_cpu_slowdown_fails_the_1b_ratio_check():
    """Positive control: a candidate as slow as the reference (ratio 1.0), and one slower, fail the 0.55 check."""
    for planted in (0.012, 0.02):
        measured = measure_ratio(lambda _: burn(planted), lambda _: burn(0.012), _spin_items())
        with pytest.raises(AssertionError):
            within_ratio(measured)


def test_control_a_candidate_as_slow_as_stage_one_fails_the_1b_check_but_passes_the_stage_one_check():
    """Positive control: a candidate at ratio about 0.72 (stage one's speed) fails the 1B limit 0.55 and passes the stage-one limit 0.75,
    so the new mark is stricter than the old one and the check can tell them apart."""
    measured = measure_ratio(lambda _: burn(0.0086), lambda _: burn(0.012), _spin_items())
    assert 0.6 < measured[0] < 0.8
    within_ratio(measured, STAGE_ONE_LIMIT)
    with pytest.raises(AssertionError):
        within_ratio(measured)


def test_control_a_wrapper_planted_around_a_fast_candidate_fails_the_1b_check():
    """Positive control, wrapper form: a fast candidate (ratio 0.25) passes; wrapped to burn extra CPU per call (ratio 0.67), it fails."""
    def fast(_):
        burn(0.003)

    within_ratio(measure_ratio(fast, lambda _: burn(0.012), _spin_items()))

    def slowed(item):
        fast(item)
        burn(0.005)

    with pytest.raises(AssertionError):
        within_ratio(measure_ratio(slowed, lambda _: burn(0.012), _spin_items()))


def test_control_the_1b_ratio_is_cpu_time_not_wall_time():
    """A candidate that only sleeps spends no CPU: the ratio ignores it (the wall time is printed beside, never judged)."""
    measured = measure_ratio(lambda _: time.sleep(0.02), lambda _: burn(0.012), _spin_items(4))
    assert measured[0] < 0.1 and measured[3] > 0.07
    within_ratio(measured)


def test_the_1b_ratio_constant_is_the_ruled_draft():
    """Pins the ruled DRAFT (Westley's number); it changes only with his word. The stage-one limit stays 0.75 in test_speed_equal.py."""
    assert DRAFT_LAB_SPEED_RATIO_1B == 0.55
    assert DRAFT_LAB_SPEED_RATIO_1B < STAGE_ONE_MEASURED < STAGE_ONE_LIMIT == 0.75
