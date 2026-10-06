# spec: docs/northstar/plans/2026-10-05-ping-search-spec.md::Positive controls 1 to 7 - real library (R-162-01 to R-162-05)
"""The seven positive controls of the ping search scene, on the production C library. Placement and SearchSetting
are built by hand so no test depends on the sampler. Each test fails with a clear message while
scripts/skilllab/search.py (or search_batch.py for control 6) does not exist.

Sight: the real Vanguard sight is read through the wrapper, engine.type_stats(w, Vanguard)["sensor_radius"] (700 at
the time of writing); nothing here hard-codes it. Speed is read the same way (wu per second, 20 ticks a second).

Readings of the spec the builder must confirm (see the report):
- control 6 calls run_search_batch(..., out_dir=<dir>) and expects it to return a dict of written paths with a "csv"
  entry (the other batches' form: batches.run(defn, out_dir) -> {name: path});
- control 5 is checked on the engine directly, after the search module is required to exist, so it is red until then.
Control 4 is parameter-tuned by reading, not by running (no search code existed): see the report."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402

try:
    from scripts.skilllab import search as S
except Exception as e:  # noqa: BLE001
    S, S_ERR = None, e
try:
    from scripts.skilllab import search_batch as SB
except Exception as e:  # noqa: BLE001
    SB, SB_ERR = None, e

VANGUARD = 2
RADIUS, COOLDOWN, REVEAL, FORCE = 500.0, 100, 100, 16
SEEKER_LAYER = 2


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


@pytest.fixture(scope="module")
def stats(lib):
    w = lib.new_world(0)
    try:
        return lib.type_stats(w, VANGUARD)
    finally:
        lib.free_world(w)


def _need():
    assert S is not None, "scripts/skilllab/search.py is missing or fails to import: %r" % (S_ERR,)
    for n in ("SearchSetting", "Placement", "run_search"):
        assert hasattr(S, n), "scripts/skilllab/search.py has no %s" % n


def _sight(stats):
    assert stats["sensor_radius"] > 0, "could not read the Vanguard sight through engine.type_stats"
    return stats["sensor_radius"]


def _setting(stats, reach_x=2.0, **kw):
    d = dict(radius=RADIUS, reach=reach_x * _sight(stats), reveal_ticks=REVEAL, cooldown_ticks=COOLDOWN, force=FORCE)
    d.update(kw)
    return S.SearchSetting(**d)


def _place(dx, layer=SEEKER_LAYER, script="still", dy=0.0, heading=0.0):
    return S.Placement(dx=dx, dy=dy, layer=layer, heading_deg=heading, script=script)


def _run(setting, policy, placement, seed=1, cap=2400, **kw):
    return S.run_search(setting, policy, "none", placement, seed, cap_ticks=cap, **kw)


def test_control_1_ahead_finds_a_hider_ahead_inside_reach_on_its_layer_and_none_does_not(lib, stats):
    _need()
    st = _setting(stats)
    pl = _place(0.95 * st.reach)                          # beyond sight (0.7 x 2 reach... sight < 0.95 reach)
    assert 0.95 * st.reach > _sight(stats)
    a, n = _run(st, "ahead", pl, engine=lib), _run(st, "none", pl, engine=lib)
    assert a.side[0].found_before_contact, "ahead must reveal a hider 0.95 reach ahead on its own layer: %r" % (a,)
    assert a.side[0].first_reveal_tick is not None and a.side[0].pings_found >= 1
    assert not n.side[0].found_before_contact and n.side[0].pings_cast == 0, "none never pings: %r" % (n,)
    assert n.ended == "contact", "with no pings the seeker walks into true vision"


def test_control_2_ahead_misses_a_hider_on_another_layer_and_sweep_finds_it(lib, stats):
    _need()
    st = _setting(stats)
    pl = _place(0.95 * st.reach, layer=4)
    a, s = _run(st, "ahead", pl, engine=lib), _run(st, "sweep", pl, engine=lib)
    assert not a.side[0].found_before_contact, "ahead pings on its own layer only, hider on layer 4: %r" % (a,)
    assert s.side[0].found_before_contact, "sweep covers all five layers and must find the layer-4 hider: %r" % (s,)


def test_control_3_a_still_hider_beyond_reach_plus_radius_is_found_later_than_one_inside_reach(lib, stats):
    _need()
    st = _setting(stats)
    near = _run(st, "ahead", _place(0.95 * st.reach), engine=lib)
    far_dx = st.reach + st.radius + 1000.0
    far = _run(st, "ahead", _place(far_dx), engine=lib)
    assert near.side[0].first_reveal_tick is not None, "control 1 setup must find the near hider"
    assert far.side[0].found_before_contact, \
        "the seeker closes on a still hider; ahead pings every %d ticks and must catch it before true vision: %r" \
        % (COOLDOWN, far)
    t_far = far.side[0].first_reveal_tick
    assert t_far > near.side[0].first_reveal_tick, "far hider found at %r, near at %r" % (t_far, near.side[0].first_reveal_tick)
    speed_per_tick = stats["speed"] / 20.0
    assert t_far * speed_per_tick >= far_dx - st.reach - st.radius - 300.0, \
        "nothing may be found until the seeker is within reach + radius of the hider (tick %d)" % t_far


def test_control_4_reactive_keeps_a_fresher_picture_than_sweep_against_a_drifting_hider(lib, stats):
    _need()
    st = _setting(stats, reveal_ticks=20)
    # Staged where sweep is certain to find it early: same layer as the seeker, at a sweep target (bearing 0, ring 1.0 of
    # reach), 1200 wu below the line, drifting across the seeker's front (heading 90) so it leaves the disc; measured:
    # sweep finds it (picture age 155), reactive keeps it fresher (45).
    pl = _place(st.reach, dy=-1200.0, heading=90.0, script="drift")
    s, r = _run(st, "sweep", pl, engine=lib), _run(st, "reactive", pl, engine=lib)
    age_r, age_s = r.side[0].picture_age_ticks, s.side[0].picture_age_ticks
    assert age_r is not None, "reactive found nothing; the placement must be findable by sweep first: %r" % (r,)
    assert age_s is None or age_r < age_s, "picture age at contact: reactive %r, sweep %r" % (age_r, age_s)


def test_control_5_the_reveal_follows_the_units_it_caught(lib, stats):
    _need()
    sight = _sight(stats)
    radius, reveal = 250.0, 200
    w = lib.new_world(3)
    try:
        lib.set_ping_params(w, radius=radius, reach=2.0 * sight, reveal_ticks=reveal, cooldown_ticks=COOLDOWN)
        caster = lib.spawn(w, VANGUARD, 0, 0.0, 0.0, SEEKER_LAYER)
        hider = lib.spawn(w, VANGUARD, 1, 1.5 * sight, 0.0, SEEKER_LAYER)
        assert caster and hider
        lib.step(w)
        assert lib.seen_by_sight(w, 0, [hider]) == set(), "setup: the hider must start outside true vision"
        assert lib.ping(w, caster, SEEKER_LAYER, 1.5 * sight, 0.0) == 0, "ping refused"
        lib.step(w)
        assert hider in lib.visible_enemies(w, 0, [hider]), "setup: the ping must reveal the hider"
        lib.order_move(w, [hider], 1.5 * sight, 9000.0)
        for _ in range(100):
            lib.step(w)
        x, y = lib.unit_pos(w, hider)
        assert ((x - 1.5 * sight) ** 2 + y ** 2) ** 0.5 > radius + 50.0, "setup: the hider must have left the pinged disc"
        assert hider in lib.visible_enemies(w, 0, [hider]), "revealed units stay revealed after they leave the disc"
        for _ in range(reveal + 300):
            lib.step(w)
        assert hider not in lib.visible_enemies(w, 0, [hider]), "the reveal must end after reveal_ticks"
    finally:
        lib.free_world(w)


def test_control_6_same_inputs_same_result_and_workers_do_not_change_the_csv(lib, stats, tmp_path):
    _need()
    st = _setting(stats)
    pl = _place(0.95 * st.reach, layer=4, script="drift", heading=90.0)
    assert _run(st, "sweep", pl, seed=7, engine=lib) == _run(st, "sweep", pl, seed=7, engine=lib), \
        "same seed and inputs must give an identical SearchResult"
    assert SB is not None, "scripts/skilllab/search_batch.py is missing or fails to import: %r" % (SB_ERR,)
    assert hasattr(SB, "run_search_batch"), "scripts/skilllab/search_batch.py has no run_search_batch"
    outs = {}
    for workers in (1, 3):
        paths = SB.run_search_batch([st], ["ahead", "sweep"], 3, 11, workers, out_dir=tmp_path / ("w%d" % workers))
        outs[workers] = Path(paths["csv"] if isinstance(paths, dict) else paths).read_bytes()
    assert outs[1] and outs[1] == outs[3], "csv differs between 1 and 3 workers"


def test_control_7_a_larger_radius_never_lowers_sweeps_found_rate(lib, stats):
    _need()
    sight = _sight(stats)
    reach = 2.0 * sight
    scripts = ("still", "drift", "shift")
    places = [_place(dx=1.1 * sight + 0.15 * reach * (i % 7), dy=((i % 5) - 2) * 0.12 * reach, layer=i % 5,
                     script=scripts[i % 3], heading=(37.0 * i) % 360.0) for i in range(20)]
    assert len(places) == 20
    rates = []
    for radius in (250.0, 500.0, 1000.0):
        st = _setting(stats, radius=radius)
        found = sum(_run(st, "sweep", pl, seed=i, cap=1200, engine=lib).side[0].found_before_contact
                    for i, pl in enumerate(places))
        rates.append(found / 20.0)
    assert rates[0] <= rates[1] <= rates[2], "found rate must not fall as radius grows (250, 500, 1000): %r" % (rates,)
