# spec: Architect speed brief, change 1 (firing takes the living set); AC-10 numbers unchanged
"""count_able, count_able_weighted and unit_states take an optional `alive` set instead of calling unit_alive."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_weighted import WeightedFakeEngine  # noqa: E402
from scripts.skilllab.firing import count_able, count_able_weighted, unit_states  # noqa: E402


class Fake(WeightedFakeEngine):
    def unit_destination(self, w, u):
        self.calls.append(("unit_destination", w, u))
        return None


def situation():
    """Side 0: a1 a2 a3 (a3 dead); side 1: e1 e2 e3 (e3 dead); all within reach 100 on layer 0."""
    fake = Fake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    s0 = [fake.spawn(w, vg, 0, 10.0 * i, 0.0, 0) for i in range(3)]
    s1 = [fake.spawn(w, vg, 1, 60.0 + 10.0 * i, 0.0, 0) for i in range(3)]
    fake.set_hp(s0[2], 0)
    fake.set_hp(s1[2], 0)
    ranges = {u: 100.0 for u in s0 + s1}
    weights = {u: 1.0 + u for u in s0 + s1}
    return fake, w, s0, s1, ranges, weights, {s0[0], s0[1], s1[0], s1[1]}


def unit_alive_calls(fake):
    return fake.calls_named("unit_alive")


def test_count_able_same_result_and_no_unit_alive_with_alive():
    fake, w, s0, s1, ranges, _, alive = situation()
    plain = count_able(fake, w, s0, s1, ranges)
    assert plain == (2, 2) and unit_alive_calls(fake)       # contract kept without the set
    fake, w, s0, s1, ranges, _, alive = situation()
    assert count_able(fake, w, s0, s1, ranges, alive=alive) == plain
    assert unit_alive_calls(fake) == []


def test_count_able_weighted_same_result_and_no_unit_alive_with_alive():
    fake, w, s0, s1, ranges, weights, alive = situation()
    plain = count_able_weighted(fake, w, s0, s1, ranges, weights)
    assert plain == (sum(weights[u] for u in s0[:2]), sum(weights[u] for u in s1[:2]))
    assert unit_alive_calls(fake)
    fake, w, s0, s1, ranges, weights, alive = situation()
    assert count_able_weighted(fake, w, s0, s1, ranges, weights, alive=alive) == plain
    assert unit_alive_calls(fake) == []


def test_unit_states_same_result_and_no_unit_alive_with_alive():
    fake, w, s0, s1, ranges, _, alive = situation()
    plain = unit_states(fake, w, s0, s1, ranges)
    assert set(plain) == alive and unit_alive_calls(fake)
    fake, w, s0, s1, ranges, _, alive = situation()
    assert unit_states(fake, w, s0, s1, ranges, alive=alive) == plain
    assert unit_alive_calls(fake) == []


def test_the_set_is_what_is_read_a_unit_missing_from_it_is_dead_even_if_the_fake_says_alive():
    fake, w, s0, s1, ranges, weights, alive = situation()
    alive = alive - {s1[1]}                                  # fake still has s1[1] at full hp
    assert count_able(fake, w, s0, s1, ranges, alive=alive) == (2, 1)
    assert count_able_weighted(fake, w, s0, s1, ranges, weights, alive=alive) == (
        weights[s0[0]] + weights[s0[1]], weights[s1[0]])
    assert set(unit_states(fake, w, s0, s1, ranges, alive=alive)) == alive


def test_a_unit_in_the_set_is_alive_even_if_the_fake_says_dead():
    fake, w, s0, s1, ranges, _, alive = situation()
    assert count_able(fake, w, s0, s1, ranges, alive=alive | {s0[2]}) == (3, 2)


def test_empty_alive_gives_zero():
    fake, w, s0, s1, ranges, weights, _ = situation()
    assert count_able(fake, w, s0, s1, ranges, alive=set()) == (0, 0)
    assert count_able_weighted(fake, w, s0, s1, ranges, weights, alive=set()) == (0.0, 0.0)
    assert unit_states(fake, w, s0, s1, ranges, alive=set()) == {}
    assert unit_alive_calls(fake) == []
