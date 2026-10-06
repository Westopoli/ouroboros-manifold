# spec: docs/northstar/plans/2026-10-05-ping-search-spec.md::Interfaces (placements, coverage_rate, SideResult)
"""search.placements, search.coverage_rate and search.summarise_side. No engine, no compiler.
summarise_side(reveal_log, contact_tick, cap_ticks, enemy_headcount, pings) -> SideResult is an interface ADDED by
this test file (the spec fixes SideResult but not the function that fills it). reveal_log is a list of
(tick, set of enemy ids revealed by ping and not by sight); pings is a list of (tick, found_count).
The numbers are the spec's lab drafts (2026-10-05), provisional."""
import math
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.skilllab import search as S
except Exception as e:  # noqa: BLE001
    S, S_ERR = None, e
try:
    from scripts.skilllab import search_policies as P
except Exception as e:  # noqa: BLE001
    P, P_ERR = None, e

SIGHT, REACH_MAX = 700.0, 3 * 700.0


def _s():
    assert S is not None, "scripts/skilllab/search.py is missing or fails to import: %r" % (S_ERR,)
    return S


def _has(name):
    assert hasattr(_s(), name), "scripts/skilllab/search.py has no %s" % name
    return getattr(S, name)


def _setting(**kw):
    d = dict(radius=500.0, reach=2000.0, reveal_ticks=100, cooldown_ticks=200, force=16)
    d.update(kw)
    return _s().SearchSetting(**d)


# ---- placements

def test_placements_deterministic_per_seed_and_differ_across_seeds():
    f = _has("placements")
    assert f(5, 30, SIGHT, REACH_MAX) == f(5, 30, SIGHT, REACH_MAX)
    assert f(5, 30, SIGHT, REACH_MAX) != f(6, 30, SIGHT, REACH_MAX)


def test_placements_count_and_type():
    f = _has("placements")
    for n in (1, 7, 60):
        out = f(1, n, SIGHT, REACH_MAX)
        assert len(out) == n and all(isinstance(p, S.Placement) for p in out)


def test_placements_ahead_within_75_degrees_and_outside_sight_and_inside_range():
    f = _has("placements")
    for seed in range(5):
        for p in f(seed, 200, SIGHT, REACH_MAX):
            d = math.hypot(p.dx, p.dy)
            assert d > SIGHT, "placement starts inside true vision: %r" % (p,)
            assert d <= REACH_MAX + 2000.0 + 1e-6, "placement beyond reach_max + 2000: %r" % (p,)
            assert p.dx > 0 and abs(math.degrees(math.atan2(p.dy, p.dx))) <= 75.0 + 1e-6, "not ahead: %r" % (p,)


def test_placements_cover_all_five_layers_and_are_valid():
    f = _has("placements")
    out = f(3, 100, SIGHT, REACH_MAX)
    assert {p.layer for p in out} == {0, 1, 2, 3, 4}
    assert all(isinstance(p.layer, int) and 0 <= p.layer <= 4 for p in out)


def test_placements_scripts_appear_equally_often():
    f = _has("placements")
    assert P is not None, "scripts/skilllab/search_policies.py is missing or fails to import: %r" % (P_ERR,)
    keys = list(P.HIDER_SCRIPTS)
    out = f(2, len(keys) * 20, SIGHT, REACH_MAX)
    counts = Counter(p.script for p in out)
    assert set(counts) == set(keys) and set(counts.values()) == {20}, counts


# ---- coverage_rate = force * pi r^2 / (cooldown s * pi reach^2 * layers)

def test_coverage_rate_hand_computed_default_layers():
    f = _has("coverage_rate")
    # 16 * 500^2 / (10 s * 2000^2 * 5) = 4e6 / 2e8
    assert f(_setting()) == pytest.approx(0.02, rel=1e-9)
    # 8 * 1000^2 / (20 s * 3000^2 * 5) = 8e6 / 9e8
    assert f(_setting(force=8, radius=1000.0, reach=3000.0, cooldown_ticks=400)) == pytest.approx(8e6 / 9e8, rel=1e-9)


def test_coverage_rate_layers_argument():
    f = _has("coverage_rate")
    assert f(_setting(), layers=1) == pytest.approx(0.1, rel=1e-9)


def test_coverage_rate_monotone():
    f = _has("coverage_rate")
    base = f(_setting())
    assert f(_setting(force=32)) > base and f(_setting(radius=1000.0)) > base
    assert f(_setting(cooldown_ticks=400)) < base and f(_setting(reach=3000.0)) < base


# ---- summarise_side(reveal_log, contact_tick, cap_ticks, enemy_headcount, pings)

CAP, HEAD = 2400, 16


def _sum(log, contact, pings=(), cap=CAP, head=HEAD):
    return _has("summarise_side")(list(log), contact, cap, head, list(pings))


def test_summarise_never_revealed():
    r = _sum([], 500, [(100, 0), (200, 0)])
    assert (r.found_before_contact, r.first_reveal_tick, r.warning_ticks) == (False, None, None)
    assert r.share_revealed == 0.0 and r.layer_learned is False and r.picture_age_ticks is None
    assert (r.pings_cast, r.pings_found) == (2, 0)


def test_summarise_revealed_once_then_contact():
    r = _sum([(100, {1, 2, 3, 4})], 300, [(100, 4), (150, 0)])
    assert r.found_before_contact is True and r.first_reveal_tick == 100
    assert r.warning_ticks == 200, "contact tick minus first reveal tick"
    assert r.share_revealed == pytest.approx(4 / 16)
    assert r.layer_learned is True
    assert r.picture_age_ticks == 200, "contact 300, last tick any enemy was revealed 100"
    assert (r.pings_cast, r.pings_found) == (2, 1)


def test_summarise_share_counts_each_unit_once_and_picture_age_uses_last_nonempty_tick():
    log = [(100, {1, 2}), (110, {1, 2}), (120, set()), (130, set())]
    r = _sum(log, 300, [(100, 2)])
    assert r.share_revealed == pytest.approx(2 / 16)
    assert r.warning_ticks == 200 and r.picture_age_ticks == 190


def test_summarise_union_over_ticks_for_share():
    r = _sum([(100, {1, 2}), (200, {2, 3, 4})], 300)
    assert r.share_revealed == pytest.approx(4 / 16)
    assert r.picture_age_ticks == 100


def test_summarise_reveal_after_contact_does_not_count_as_found_before_contact():
    r = _sum([(350, {1, 2})], 300, [(340, 2)])
    assert r.found_before_contact is False and r.warning_ticks is None
    assert r.share_revealed == 0.0 and r.layer_learned is False and r.picture_age_ticks is None


def test_summarise_reveals_after_contact_are_dropped_from_the_share():
    r = _sum([(100, {1}), (350, {2, 3})], 300)
    assert r.found_before_contact is True and r.first_reveal_tick == 100
    assert r.share_revealed == pytest.approx(1 / 16)


def test_summarise_cap_with_a_reveal_measures_warning_to_the_cap():
    r = _sum([(1000, {1, 2})], None, [(1000, 2)])
    assert r.found_before_contact is True and r.first_reveal_tick == 1000
    assert r.warning_ticks == CAP - 1000
    assert r.layer_learned is True


def test_summarise_cap_without_a_reveal():
    r = _sum([], None, [(100, 0)])
    assert r.found_before_contact is False and r.warning_ticks is None and r.pings_cast == 1
