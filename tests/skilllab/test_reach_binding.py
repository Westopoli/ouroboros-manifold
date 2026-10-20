# Rule pins: R-096-04@1876c2
# spec: R-096-04 layer reach by unit type - Engine.set_reach and the "reach" key of Setup.unit_types
"""fight() calls engine.set_reach for a custom type that carries "reach": (up, down); stub-library wrapper test."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes_reach import ReachFakeEngine  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam), not the fake's engine

FULL = {"category": 1, "role": "x", "max_hp": 55.0, "base_damage": 3.0, "attack_interval": 10.0,
        "attack_range": 77.0, "speed": 2.0, "sensor_radius": 100.0, "layer_transition_time": 0.0,
        "aoe_radius": 0.0, "ability_id": 0}
BASED = {"base": "Vanguard", "scale": {"attack_range": 2.0}, "set": {"speed": 3.0}}


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]
    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, unit="Vanguard", x=None):
    x = (-300.0 if side == 0 else 300.0) if x is None else x
    return Group(side=side, unit=unit, count=1, formation="line", x=x, y=0.0, facing_deg=0.0, layer=0,
                 order="attack_move", params={"spacing": 30.0})


def run(groups, types):
    fake = ReachFakeEngine()
    fight(Setup(groups=tuple(groups), unit_types=types, max_ticks=2), 0, False, engine=fake)
    return fake


def test_full_stats_entry_with_reach_calls_set_reach_once_after_register():
    fake = run([G(0, "Tall"), G(1)], {"Tall": dict(FULL, reach=(0, 2))})
    regs, sets = fake.calls_named("register_unit_type"), fake.calls_named("set_reach")
    assert len(regs) == 1 and sets == [("set_reach", fake.world, regs[0][2], 0, 2)]
    names = [c[0] for c in fake.calls]
    assert names.index("register_unit_type") < names.index("set_reach") < names.index("spawn")


def test_base_entry_with_reach_calls_set_reach_once_after_register():
    fake = run([G(0, "Tall"), G(1)], {"Tall": dict(BASED, reach=(1, 3))})
    regs, sets = fake.calls_named("register_unit_type"), fake.calls_named("set_reach")
    assert len(regs) == 1 and sets == [("set_reach", fake.world, regs[0][2], 1, 3)]
    assert [c[0] for c in fake.calls].index("register_unit_type") < [c[0] for c in fake.calls].index("set_reach")


def test_reach_is_not_passed_to_register_unit_type_for_either_form():
    for entry in (dict(FULL, reach=(0, 2)), dict(BASED, reach=(0, 2))):
        fake = run([G(0, "Tall"), G(1)], {"Tall": entry})
        stats = fake.calls_named("register_unit_type")[0][3]
        assert "reach" not in stats and len(stats) == 11, sorted(stats)


def test_base_entry_reach_is_not_read_as_a_stat():
    fake = run([G(0, "Tall"), G(1)], {"Tall": dict(BASED, reach=(0, 2))})   # a stat named reach would raise ValueError
    stats = fake.calls_named("register_unit_type")[0][3]
    assert stats["attack_range"] == 2.0 * fake.type_stats(fake.world, 2)["attack_range"] and stats["speed"] == 3.0


def test_no_reach_key_means_no_set_reach_call():
    assert not run([G(0, "Tall"), G(1)], {"Tall": dict(FULL)}).calls_named("set_reach")
    assert not run([G(0, "Tall"), G(1)], {"Tall": dict(BASED)}).calls_named("set_reach")
    assert not run([G(0), G(1)], {}).calls_named("set_reach")


def test_one_call_per_custom_type_with_its_own_tuple():
    types = {"A": dict(BASED, reach=(0, 1)), "B": dict(FULL, reach=(2, 0)), "C": dict(BASED)}
    fake = run([G(0, "A"), G(0, "B", x=-200.0), G(1, "C")], types)
    assert [c[3:] for c in fake.calls_named("set_reach")] == [(0, 1), (2, 0)]
    assert len({c[2] for c in fake.calls_named("set_reach")}) == 2


def test_reach_is_set_once_per_type_even_with_several_groups():
    fake = run([G(0, "A"), G(0, "A", x=-200.0), G(1)], {"A": dict(BASED, reach=(0, 1))})
    assert len(fake.calls_named("set_reach")) == 1


@pytest.mark.parametrize("bad", [(1,), (1, 2, 3), (), 2, "ab"])
def test_bad_reach_raises_value_error_before_any_engine_call(bad):
    fake = ReachFakeEngine()
    setup = Setup(groups=(G(0, "Tall"), G(1)), unit_types={"Tall": dict(BASED, reach=bad)}, max_ticks=2)
    with pytest.raises(ValueError):
        fight(setup, 0, False, engine=fake)
    assert fake.calls == []


# ---- Engine.set_reach (stub library) ----

class _Lib:
    def __init__(self, ret=0):
        self.ret, self.seen = ret, None
        self.om_roster_set_reach = self._call

    def _call(self, w, t, up, down):
        self.seen = (w, t, up, down)
        return self.ret


def _engine(lib):
    from scripts.skilllab.engine import Engine
    e = Engine.__new__(Engine)
    e._lib = lib
    return e


def test_engine_set_reach_passes_the_arguments():
    lib = _Lib()
    _engine(lib).set_reach("W", 100, 1, 2)
    assert lib.seen == ("W", 100, 1, 2)


def test_engine_set_reach_nonzero_raises_value_error():
    with pytest.raises(ValueError):
        _engine(_Lib(ret=-1)).set_reach("W", 999, 1, 2)
