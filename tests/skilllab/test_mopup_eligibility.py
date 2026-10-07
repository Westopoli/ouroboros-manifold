# spec: Architect ruling 2026-10-06 (residual stalemate), ruling 2: mop-up eligibility
"""A side mops up once, after its timeline steps have fired, every group of it is attack-move. A guard group that never
converts keeps the side out (the genuine standoff). Fake engine: everybody sees everybody and nobody can reach anybody."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fakes_guard import GuardFakeEngine  # noqa: E402
from scripts.skilllab import fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402

INTERVAL = 10


class Eng(GuardFakeEngine):
    def unit_destination(self, w, u):
        return None

    def can_see(self, w, a, b):
        return True


def G(side, x, order):
    return Group(side=side, unit="Vanguard", count=1, formation="line", x=x, y=0.0, facing_deg=0.0, layer=0,
                 order=order, goal=None if order == "guard" else (-x, 0.0), params={"spacing": 40.0})


def run(timeline, side0_order="guard"):
    setup = Setup(groups=(G(0, -2000.0, side0_order), G(1, 2000.0, "attack_move")), unit_types={}, mopup=True,
                  mopup_interval_ticks=INTERVAL, max_ticks=60, stalemate_ticks=1000, timeline=timeline)
    eng = Eng()
    fight.fight(setup, engine=eng)
    side0 = set(eng.units_of(0))
    return [o for o in eng.orders_of("attack_move") if o[0] > 0 and o[0] % INTERVAL == 0 and set(o[2]) <= side0]   # mop-ups only: the step fires off-interval


def test_guard_side_converted_by_a_step_mops_up_after_the_step_not_before():
    mops = run((Step(group=0, when=("tick", 25), order="attack_move", goal=(2000.0, 0.0)),))
    assert mops, "side 0 never mopped up after its guard became attack-move"
    assert min(t for t, *_ in mops) >= 25


def test_guard_group_that_never_converts_never_mops_up():
    assert run(()) == []


def test_positive_control_an_all_attack_move_side_mops_up_from_the_first_interval():
    mops = run((), side0_order="attack_move")
    assert mops and min(t for t, *_ in mops) <= INTERVAL
