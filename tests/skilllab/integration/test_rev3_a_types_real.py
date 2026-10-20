# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T3; defect D3); ledger FINDING-lab-d3; piece LAB-REV3-A
"""LAB-REV3-A, T3 (R8, D3) against the real engine (OM_LAB_SLOW=1; a few seconds a test): a lab Warden is a mirror of a built-in
Warden, and a lab Bastion takes at most 1.0x from a Strike attacker (R-081-03's Siege exception, csrc/unit.c om_resolve_hit_multiplier).

How the two kinds meet in one fight (no builder contract beyond tests/skilllab/test_rev3_a_types.py): `AliasEngine.type_id("<Name>B")`
answers the built-in id of `<Name>`, so a group named "WardenB" is a BUILT-IN Warden that `fight._register_types` leaves alone (no
unit_types entry), while a group named "Warden" with the entry `{"base": "Warden", "reach": (0, 0)}` is the lab-registered one,
exactly what `plays_space._types` writes. The reach (0, 0) is the library default, so after the fix the two are the same type.

The mirror is 12 Vanguards + 4 Wardens a side (the M9 shape, the most Wardens D9 allows per 16), not the plan's 8 Wardens against 8:
two built-in Wardens a side cap at 12,000 ticks (D9's stall; measured 8 of 8 caps), which would make the check answer nothing.

Measured on the lab tip (2026-10-20, this file's author): eight fights, seeds 0 to 7, the lab Wardens on side 0 and the built-in ones
on side 1: side 1 wins 8 of 8 (the finding says "8 of 8"); the other way round side 0 wins 8 of 8; built-in on both sides: side 0 wins 3,
side 1 wins 5. Four Raiders against one Bastion for 200 ticks: the lab Bastion
is left at 0.383 of its hit points, the built-in one at 0.589 (the 1.5x of ALG-60's Strike to Siege applies to the copy)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights; set OM_LAB_SLOW=1")
SEEDS = range(8)


class AliasEngine(Engine):
    """A name ending in B is the built-in type of the name without it."""
    def type_id(self, name):
        return super().type_id(name[:-1] if name.endswith("B") else name)


def blob(side, unit, n, x):
    return Group(side=side, unit=unit, count=n, formation="blob", x=x, y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=0,
                 order="attack_move", params={"radius": 80 + 12 * n ** 0.5})


def winners(side0, side1, types):
    """Outcomes of eight fights of 12 Vanguards + 4 `side0` Wardens against 12 Vanguards + 4 `side1` Wardens."""
    out = []
    for seed in SEEDS:
        setup = Setup(groups=(blob(0, "Vanguard", 12, -350.0), blob(0, side0, 4, -350.0),
                              blob(1, "Vanguard", 12, 350.0), blob(1, side1, 4, 350.0)), unit_types=types)
        out.append(fight(setup, seed, False, engine=AliasEngine()).outcome)
    return out


@SLOW
def test_positive_control_two_builtin_wardens_split_the_wins():
    """Green on the lab tip: with no copy on either side the same eight fights are not one-sided, so the mirror check below can tell."""
    got = winners("Warden", "WardenB", {})
    assert {"side0", "side1"} <= set(got), got


@SLOW
def test_t3_a_lab_registered_warden_is_a_mirror_of_a_builtin_one():
    """T3 (D3): the lab Warden against the built-in Warden, eight seeds: both sides win at least once. Red today: side 1 (the built-in
    Wardens, whose aura heals) wins 8 of 8, the lab copy has no aura."""
    got = winners("Warden", "WardenB", {"Warden": {"base": "Warden", "reach": (0, 0)}})
    assert {"side0", "side1"} <= set(got), "outcomes by seed: %s" % got


@SLOW
def test_t3_the_mirror_does_not_depend_on_the_side():
    """T3 (D3): the built-in Warden on side 0 and the lab one on side 1 splits too. Red today: side 0 (built-in) wins 8 of 8."""
    got = winners("WardenB", "Warden", {"Warden": {"base": "Warden", "reach": (0, 0)}})
    assert {"side0", "side1"} <= set(got), "outcomes by seed: %s" % got


def bastion_left(target):
    setup = Setup(groups=(blob(0, "Raider", 4, -150.0), blob(1, target, 1, 150.0)),
                  unit_types={"Bastion": {"base": "Bastion", "reach": (0, 2)}}, max_ticks=200)
    return fight(setup, 0, False, engine=AliasEngine()).strength_left[1]


@SLOW
def test_positive_control_the_builtin_bastion_is_capped_at_one_times():
    """Green on the lab tip: four Raiders (Strike, 1.5x against Siege uncapped) leave the built-in Bastion more hit points than the
    uncapped multiplier would; measured 0.589 against 0.383 uncapped. The bound is the copy's own number from the same fight, not a
    new threshold: the capped target keeps strictly more than the uncapped copy."""
    assert bastion_left("BastionB") > bastion_left("Bastion")


@SLOW
def test_t3_a_lab_bastion_takes_the_same_damage_as_the_builtin_one_from_a_strike_attacker():
    """T3 (D3): the lab Bastion (entry `{"base": "Bastion", "reach": (0, 2)}`) is capped at 1.0x like the built-in one. Red today:
    the copy keeps 0.383 of its hit points, the built-in 0.589."""
    assert bastion_left("Bastion") == pytest.approx(bastion_left("BastionB"), abs=1e-9)
