"""S-018, S-020, plus the scale and behavior invariants -- the combined E-02
gating test.

Builds 60 inhabited regions (region 0 is the epic's "obviously working in 60
seconds" probe: tier HOME, military 42, economy 66, tension 18, population
60, phases 0,0) and asserts, in one test, every leg the epic and e2e demand
together:

- SCALE: 60 regions, and a 5,000-tick bulk run reaches its full count
  (docs/northstar/e2e/E-02.md "Scale gates").
- SPEED: that untraced bulk run finishes under the Westley-confirmed budget
  (< 0.5s total, < 50 us/tick average) -- never loosened by Agora.
- BEHAVIOR: every trace row holds the [0,100] clamps and the economy floor,
  composites are stored already rounded to 2dp, the probe region's economy
  climbs into the mid-50s, and the oscillator's net contribution over every
  15-tick window (k >= 2) is ~0 (R-018-04, ALG-01).
- DETERMINISM: a repeat run with the same seed and configuration produces
  the same final checksum (R-020-01), and enabling the trace does not
  perturb the math -- the traced run's checksum matches the untraced run's
  (R-020-03 invariant: recording is observation, not computation).
"""
import math
import random
import time

from conftest import OMTier, OmTraceRow, set_region

GATE_WORLD_SEED = 2026091460
FIELD_GEN_SEED = 20260914
N_REGIONS = 60
N_TICKS = 5000
PROBE_REGION = 0


def _build_60_region_world(lib, world_factory):
    w = world_factory(n_regions=N_REGIONS, seed=GATE_WORLD_SEED)
    set_region(lib, w, PROBE_REGION, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0, econ_phase=0.0, tension_phase=0.0)

    rng = random.Random(FIELD_GEN_SEED)
    for idx in range(1, N_REGIONS):
        tier = OMTier.HOME if rng.random() < 0.5 else OMTier.FRONTIER
        set_region(
            lib, w, idx, tier=tier,
            military=rng.uniform(5.0, 95.0),
            economy=rng.uniform(10.0, 95.0),
            tension=rng.uniform(0.0, 80.0),
            population=rng.uniform(5.0, 95.0),
            econ_phase=rng.uniform(0.0, 2 * math.pi),
            tension_phase=rng.uniform(0.0, 2 * math.pi),
        )
    return w


def test_gate_60_regions_scale_speed_behavior_determinism(lib, world_factory):
    # ---- SCALE ----
    w_speed = _build_60_region_world(lib, world_factory)
    assert lib.om_region_count(w_speed) == N_REGIONS

    # ---- SPEED (untraced bulk run) ----
    start = time.perf_counter()
    ran = lib.om_world_run(w_speed, N_TICKS)
    elapsed = time.perf_counter() - start
    assert ran == N_TICKS

    assert elapsed < 0.5, (
        f"5,000-tick bulk run for {N_REGIONS} regions took {elapsed:.3f}s, budget 0.5s"
    )
    per_tick_us = (elapsed * 1_000_000.0) / N_TICKS
    assert per_tick_us < 50.0, (
        f"{per_tick_us:.2f} us/tick average across {N_REGIONS} regions, budget 50 us/tick"
    )

    speed_checksum = lib.om_world_checksum(w_speed)

    # ---- BEHAVIOR (second run, trace on, same seed and configuration) ----
    w_trace = _build_60_region_world(lib, world_factory)
    lib.om_trace_enable(w_trace, 1)
    ran2 = lib.om_world_run(w_trace, N_TICKS)
    assert ran2 == N_TICKS

    n_rows = lib.om_trace_len(w_trace)
    assert n_rows == N_REGIONS * N_TICKS

    eps = 1e-6
    probe_economies = []
    region_osc_series = {idx: [] for idx in range(N_REGIONS)}

    chunk = 20000
    offset = 0
    while offset < n_rows:
        count = min(chunk, n_rows - offset)
        buf = (OmTraceRow * count)()
        got = lib.om_trace_read(w_trace, offset, count, buf)
        assert got == count

        for row in buf:
            assert 0.0 <= row.military <= 100.0, f"military out of [0,100] at tick {row.tick}"
            assert 0.0 <= row.economy <= 100.0, f"economy out of [0,100] at tick {row.tick}"
            assert 0.0 <= row.tension <= 100.0, f"tension out of [0,100] at tick {row.tick}"
            assert 0.0 <= row.population <= 100.0, f"population out of [0,100] at tick {row.tick}"
            assert row.economy >= 8.0, f"economy below floor 8.0 at tick {row.tick}"
            assert row.military < 90.0 + eps, f"military past recruitment ceiling at tick {row.tick}"

            assert abs(row.stability - round(row.stability, 2)) < 1e-9, (
                f"stability {row.stability} not stored rounded to 2dp at tick {row.tick}"
            )
            assert abs(row.capacity - round(row.capacity, 2)) < 1e-9, (
                f"capacity {row.capacity} not stored rounded to 2dp at tick {row.tick}"
            )

            if row.region_idx == PROBE_REGION and row.tick >= 100:
                probe_economies.append(row.economy)

            region_osc_series[row.region_idx].append((row.tick, row.drift.economy_osc_delta))

        offset += count

    assert probe_economies, "no probe-region rows read at tick >= 100"
    probe_max = max(probe_economies)
    assert 50.0 <= probe_max <= 60.0, (
        f"probe region economy peaked at {probe_max} for ticks >= 100, expected within [50, 60]"
    )

    for idx, series in region_osc_series.items():
        series.sort(key=lambda pair: pair[0])
        deltas = [d for _, d in series]
        for k in range(2, len(deltas) - 15 + 1):
            window_sum = sum(deltas[k:k + 15])
            assert abs(window_sum) < 1e-6, (
                f"region {idx}: 15-tick oscillator window at k={k} sums to {window_sum}, not ~0"
            )

    # ---- DETERMINISM ----
    w_repeat = _build_60_region_world(lib, world_factory)
    ran3 = lib.om_world_run(w_repeat, N_TICKS)
    assert ran3 == N_TICKS
    assert lib.om_world_checksum(w_repeat) == speed_checksum, (
        "a second seeded run's checksum does not match the first (R-020-01)"
    )

    trace_checksum = lib.om_world_checksum(w_trace)
    assert trace_checksum == speed_checksum, (
        "the traced run's checksum does not match the untraced run's -- "
        "trace recording perturbed the math"
    )
