"""A93 (docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 32):
the E-13 scale figures on the Siege Breaking case at 1,000 and 10,000 units.

E-13 (docs/bible/epics/E-13-movement-and-command.md), "## Scale requirements",
quoted exactly:

  "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is
  escalated): movement and collision for 1,000 units in under 3 ms per tick,
  10,000 in under 30 ms; route queries under 1,000 per second at 60 wu cells.
  The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to
  above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure
  at 20 ticks/s."

Ids: R-099-03 (tick rate drops from 20 to 10 ticks/s above 1,000 live units),
S-099 (Speed is position). The Scale requirements section carries no rule id
of its own; the ledger row for this file names it "E-13 Scale requirements".
The same section's 100 ms pipe round trip at 5,000 units is a different
figure (tests/csim/scale/test_scale_pipe_budget.py), not tested here.

Case: Siege Breaking (archetype 1) at region 0 of an 80-region seed-121
world, built as in docs/northstar/proving_ground/evidence/
a91_tactical_tick_time_2026-10-02.md (harness a91_tactical_tick_harness.c on
push/A91-tactical-measure). Unit count is set through region 0's military
(about 56.5 live units per military point in this binding; the A91 harness measured 58.5). 990 units is the "1,000 units"
point: 1,002 live units already switches the period to 2 (R-099-03), and the
1,000-unit figure is the 20 ticks/s one. 10,000 units runs at period 2.

What is timed. The budget names movement and collision. In this sim those
are om_move_sync (csrc/tactical_move.c, static), replayed from inside
om_tactical_step's position refresh, interleaved with targeting, damage,
abilities and the enemy macro tick. No exported entry point runs movement and
collision alone (om_collision_pass replays pending ticks through the same
sync, but a tick cannot be advanced without running the whole step). So the
asserted tests time the WHOLE om_tactical_step and are upper-bound tests:
the budgeted subset is at most that figure. They fail today (3.33 ms at 990
units; far over 30 ms at 10,000) and stay failing until the step is fast
enough. Each prints the whole-step figure; a per-phase figure needs the test
seam named in the report for A93, not present in csrc.

Noise: median of many timed steps after a warm-up (the spike every 20th step
is the enemy macro evaluation and does not move a median). Thresholds: the E-13
figures, 3 ms and 30 ms, passed unchanged to the suite's assert_budget, which
divides by OM_SCALE_CPU_FACTOR like every other test in this directory
(Architect ruling A97). Whole-step time is the test; there is no debug timing
seam, and the asserted figure is an upper bound of movement+collision.

Gated behind OM_SCALE=1 like the rest of this directory.
"""
import time

from ._scale_helpers import assert_budget, median_ns

SEED = 121
N_REGIONS = 80
SIEGE_BREAKING = 1
BUDGET_1000_NS = 3_000_000     # E-13: 1,000 units, 3 ms, 20 ticks/s
BUDGET_10000_NS = 30_000_000   # E-13: 10,000 units, 30 ms, 10 ticks/s (100 ms tick)


def _live(lib, w):
    return sum(1 for u in range(1, lib.om_unit_count(w) + 1) if lib.om_unit_alive(w, u))


def _siege_world(lib, military):
    w = lib.om_world_new(N_REGIONS, SEED)
    assert w
    for f in range(8):
        lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)
    lib.om_events_load_launch(w)
    lib.om_mission_load_launch_library(w)
    lib.om_campaign_start(w, 1)
    for _ in range(10):
        lib.om_world_step(w)
    for r in range(lib.om_region_count(w)):
        lib.om_mission_refresh_context(w, r)
    lib.om_region_set(w, 0, lib.om_region_tier(w, 0), military,
                      lib.om_region_field(w, 0, 0), lib.om_region_field(w, 0, 1),
                      lib.om_region_field(w, 0, 2), 0.0, 0.0, lib.om_region_owner(w, 0))
    lib.om_mission_setup(w, 0, SIEGE_BREAKING, 0)
    lib.om_mission_begin(w)
    return w


def _measure(lib, military, n, warmup):
    w = _siege_world(lib, military)
    live = _live(lib, w)
    med = median_ns(lambda: lib.om_tactical_step(w), n=n, warmup=warmup)
    period = lib.om_tactical_tick_period(w)  # set by the first step, so read after the warm-up
    lib.om_world_free(w)
    return med, live, period


def test_e13_siege_1000_units_whole_step_upper_bound_under_3ms(lib):
    """R-099-03 / E-13 Scale requirements: 1,000 units, movement+collision
    under 3 ms per tick at 20 ticks/s. Upper bound: whole om_tactical_step."""
    med, live, period = _measure(lib, 17.6, n=200, warmup=5)  # about 990 units
    print(f"[a93] siege {live} units period={period}: whole om_tactical_step median "
          f"{med / 1e6:.3f} ms (upper bound of movement+collision), budget 3.000 ms")
    assert 950 <= live <= 1000 and period == 1, f"fixture drifted: {live} units, period {period}"
    assert_budget(med, BUDGET_1000_NS, f"E-13 siege {live} units whole step (upper bound of movement+collision)")


def test_e13_siege_10000_units_whole_step_upper_bound_under_30ms(lib):
    """R-099-03 / E-13 Scale requirements: 10,000 units, movement+collision
    under 30 ms per tick at 10 ticks/s. Upper bound: whole om_tactical_step."""
    med, live, period = _measure(lib, 178.0, n=41, warmup=3)
    print(f"[a93] siege {live} units period={period}: whole om_tactical_step median "
          f"{med / 1e6:.3f} ms (upper bound of movement+collision), budget 30.000 ms")
    assert 10000 <= live <= 10400 and period == 2, f"fixture drifted: {live} units, period {period}"
    assert_budget(med, BUDGET_10000_NS, f"E-13 siege {live} units whole step (upper bound of movement+collision)")


def test_control_e13_timer_separates_known_slow_from_known_fast(lib):
    """Positive control for the two tests above: the same measurement path
    must read a ~250-unit Siege case as far cheaper than a 990-unit one, and
    the clock must read a known 5 ms sleep above a no-op. A timer that cannot
    tell these apart could not detect the budget misses either."""
    fast, live_fast, _ = _measure(lib, 4.3, n=100, warmup=5)
    slow, live_slow, _ = _measure(lib, 17.6, n=100, warmup=5)
    print(f"[a93-control] {live_fast} units {fast / 1e6:.3f} ms vs {live_slow} units {slow / 1e6:.3f} ms")
    assert live_slow > 3 * live_fast
    assert slow > 4 * fast, f"slow case {slow / 1e6:.3f} ms is not over 4x fast case {fast / 1e6:.3f} ms"
    assert fast < BUDGET_1000_NS, "known-fast case must clear the 3 ms budget the detector enforces"
    assert median_ns(lambda: time.sleep(0.005), n=5, warmup=1) > 4_900_000
    assert median_ns(lambda: None, n=50, warmup=2) < 1_000_000
