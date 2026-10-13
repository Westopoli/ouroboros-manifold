"""ALG-74 Behavior runner (docs/bible/algorithms.md; E-14 R-120..R-125, S-121).

ALG-74: "Per force at mission start: ... one uniform draw in +-noise_pct (default SCRIPT_NOISE_DEFAULT_PCT = 0.15,
timers SCRIPT_TIMER_NOISE_DEFAULT_PCT = 0.20). Every SCRIPT_EVAL_INTERVAL_TICKS = 40 ticks, for each force with living
units: context = force HP fraction (x (1 + noise) for threshold checks), unit count, elapsed seconds since mission start
(x (1 + noise) for timers), timer expired, bus flags."

What is testable through the ABI: the 40-tick evaluation interval (om_macro_tick), the noise draw (range, held for
the mission, one per force), and the timer rule elapsed x (1 + noise) >= duration (om_macro_eval_timer_transition).
What is not: the live runner never reads either noise value (SL-C3-08 in
docs/northstar/plans/sim_lane_2026-10-12/findings/alg_c3.md). The ALG text draws "for every transition and hook"; the C
draws one threshold noise and one timer noise per force (SL-C3-09).

Positive control: the noise bound check is run against a deliberately too-tight bound and must fail it (a draw really
spans the range), so the bound assertion can fire.
"""
import pytest

NOISE_PCT = 0.15
TIMER_NOISE_PCT = 0.20
EVAL_INTERVAL = 40
SEEDS = range(1, 201)


def _force_world(lib, seed, force=0, faction=1):
    w = lib.om_world_new(1, seed)
    assert w
    lib.om_macro_init_force(w, force, faction)
    return w


def test_ALG_74_evaluation_interval_is_40_ticks(lib, world_factory):
    assert lib.om_macro_evaluation_interval_ticks() == EVAL_INTERVAL
    w = world_factory(n_regions=1)
    lib.om_macro_init_force(w, 0, 1)
    lib.om_macro_tick(w, EVAL_INTERVAL - 1)
    assert lib.om_macro_has_evaluated(w) == 0
    lib.om_macro_tick(w, EVAL_INTERVAL)
    assert lib.om_macro_has_evaluated(w) == 1
    lib.om_macro_tick(w, EVAL_INTERVAL + 1)
    assert lib.om_macro_has_evaluated(w) == 0
    lib.om_macro_tick(w, 2 * EVAL_INTERVAL)
    assert lib.om_macro_has_evaluated(w) == 1


def test_ALG_74_noise_is_one_uniform_draw_within_the_default_percent(lib):
    thr, tim = [], []
    for seed in SEEDS:
        w = _force_world(lib, seed)
        thr.append(lib.om_macro_get_threshold_noise(w, 0))
        tim.append(lib.om_macro_get_timer_noise(w, 0))
        lib.om_world_free(w)
    assert all(-NOISE_PCT <= v <= NOISE_PCT for v in thr)
    assert all(-TIMER_NOISE_PCT <= v <= TIMER_NOISE_PCT for v in tim)
    # uniform over the range, not a constant and not clustered at zero: 200 seeds reach the outer fifth of each side
    assert max(thr) > 0.8 * NOISE_PCT and min(thr) < -0.8 * NOISE_PCT
    assert max(tim) > 0.8 * TIMER_NOISE_PCT and min(tim) < -0.8 * TIMER_NOISE_PCT


def test_control_ALG_74_a_too_tight_bound_is_violated_by_the_draws(lib):
    thr = []
    for seed in SEEDS:
        w = _force_world(lib, seed)
        thr.append(lib.om_macro_get_threshold_noise(w, 0))
        lib.om_world_free(w)
    assert not all(-0.5 * NOISE_PCT <= v <= 0.5 * NOISE_PCT for v in thr)


def test_ALG_74_noise_is_held_for_the_mission_and_drawn_per_force(lib):
    w = _force_world(lib, 5)
    lib.om_macro_init_force(w, 1, 2)
    first = (lib.om_macro_get_threshold_noise(w, 0), lib.om_macro_get_timer_noise(w, 0))
    other = (lib.om_macro_get_threshold_noise(w, 1), lib.om_macro_get_timer_noise(w, 1))
    for tick in range(1, 6 * EVAL_INTERVAL):
        lib.om_macro_tick(w, tick)
    assert (lib.om_macro_get_threshold_noise(w, 0), lib.om_macro_get_timer_noise(w, 0)) == first  # never re-rolled
    assert first != other  # a separate draw for the second force
    lib.om_world_free(w)


@pytest.mark.parametrize("duration,elapsed,noise,fires", [
    (100, 90, 0.10, False),   # 90 * 1.10 = 99.0 < 100
    (100, 91, 0.10, True),    # 91 * 1.10 = 100.1 >= 100
    (100, 100, -0.20, False), # 80 < 100
    (100, 100, 0.20, True),   # 120 >= 100
    (100, 100, 0.0, True),    # exactly the duration
    (100, 99, 0.0, False),
])
def test_ALG_74_timer_fires_when_elapsed_times_one_plus_noise_reaches_the_duration(lib, duration, elapsed, noise, fires):
    assert (elapsed * (1.0 + noise) >= duration) == fires  # the table agrees with the rule
    assert bool(lib.om_macro_eval_timer_transition(duration, elapsed, noise)) == fires


def test_control_ALG_74_the_timer_rule_discriminates_on_noise_alone(lib):
    assert lib.om_macro_eval_timer_transition(100, 90, 0.10) == 0  # 99.0 < 100
    assert lib.om_macro_eval_timer_transition(100, 91, 0.10) == 1  # 100.1 >= 100
