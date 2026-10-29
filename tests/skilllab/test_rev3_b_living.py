# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R1 known cap, test T11/T1; defect D9); ledger FINDING-lab-d9; piece LAB-REV3-B
"""LAB-REV3-B, the `living` field of a fight result (Architect ruling 2026-10-20, ratified): `contract.FightResult` gains a defaulted field
`living` = ({side-0 unit name: count}, {side-1 unit name: count}), the units alive at the END of the fight, filled by fight.py at the end
of every fight (one field, one fill site; the B builder owns the contract.py and fight.py edit). The mirror pre-check reads it at a cap to
tell the Warden stall of FINDING-lab-d9 from any other cap (tests/skilllab/test_rev3_b_mirror.py). Fast half: the fake engine, no
compiler; the real M9 run is integration/test_rev3_b_mirror_real.py (OM_LAB_SLOW=1) and depends on this field.

Pinned here: the field exists with a default (every older FightResult constructor keeps working); a fight with known survivors reports
them per unit name (Group.unit) per side; a side with no survivor reads {} (a zero count is omitted, so "a side that still has a living
unit" is "a non-empty dict"); a CAPPED fight carries it; a draw carries ({}, {}); trim_series keeps it (row values stay).
Red today: FightResult has no `living` field."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes import FakeEngine  # noqa: E402
from scripts.skilllab import contract  # noqa: E402
from scripts.skilllab.contract import FightResult, Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402


@pytest.fixture(autouse=True)
def stub_place(monkeypatch, seam):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, unit, count):
    return Group(side=side, unit=unit, count=count, formation="line", x=-300.0 if side == 0 else 300.0, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None, params={"spacing": 30.0})


def setup(max_ticks=50):
    """Side 0: 3 Vanguards then 2 Raiders (spawn order); side 1: 2 Vanguards then 2 Wardens."""
    return Setup(groups=(G(0, "Vanguard", 3), G(0, "Raider", 2), G(1, "Vanguard", 2), G(1, "Warden", 2)), unit_types={},
                 max_ticks=max_ticks, sample_every=5)


def run(script, max_ticks=50):
    return fight(setup(max_ticks), 0, False, engine=FakeEngine(script=script))


def kill(fake, faction, indexes=None):
    units = fake.units_of(faction)
    for i, u in enumerate(units):
        if indexes is None or i in indexes:
            fake.set_hp(u, 0)


def test_the_field_exists_with_a_default_so_older_constructors_keep_working():
    f = {x.name: x for x in dataclasses.fields(FightResult)}
    assert "living" in f, "FightResult has no field `living`"
    assert f["living"].default is not dataclasses.MISSING or f["living"].default_factory is not dataclasses.MISSING
    FightResult(outcome="side0", margin=0.0, strength_left=(0.0, 0.0), survivors=(0, 0), heads=(1, 1), ticks=1, first_contact_tick=-1,
                firing=[], firing_unit_seconds=(0.0, 0.0))


def test_a_won_fight_reports_its_survivors_per_unit_name_and_side():
    """Positive: at tick 3 side 1 is wiped out and the first Vanguard and the first Raider of side 0 die; known survivors: 2 Vanguards
    and 1 Raider on side 0, none on side 1."""
    def script(t, fake):
        if t == 3:
            kill(fake, 1)
            kill(fake, 0, {0, 3})
    r = run(script)
    assert r.outcome == "side0"
    assert r.living == ({"Vanguard": 2, "Raider": 1}, {}), r.living


def test_a_lost_fight_reports_the_survivors_of_side_1():
    def script(t, fake):
        if t == 3:
            kill(fake, 0)
            kill(fake, 1, {1})              # one of the two Vanguards of side 1
    r = run(script)
    assert r.outcome == "side1" and r.living == ({}, {"Vanguard": 1, "Warden": 2}), r.living


def test_a_capped_fight_carries_the_living_roster_at_the_cap():
    """The point of the field: at the cap (max_ticks 30, nobody finishes) the roster is what is alive then, here two Wardens on side 1
    and the Raiders of side 0 after the Vanguards of both sides were killed at tick 2."""
    def script(t, fake):
        if t == 2:
            kill(fake, 0, {0, 1, 2})
            kill(fake, 1, {0, 1})
    r = run(script, max_ticks=30)
    assert r.outcome == "cap" and r.ticks == 30
    assert r.living == ({"Raider": 2}, {"Warden": 2}), r.living


def test_a_draw_carries_two_empty_dicts():
    r = run(lambda t, fake: (kill(fake, 0), kill(fake, 1)) if t == 3 else None)
    assert r.outcome == "draw" and r.living == ({}, {}), r.living


def test_trim_series_keeps_the_living_roster():
    r = run(lambda t, fake: kill(fake, 1) if t == 3 else None)
    assert contract.trim_series(r).living == r.living == ({"Vanguard": 3, "Raider": 2}, {})
