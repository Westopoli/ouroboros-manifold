"""PP-unit: the target-choice setting (E-11 R-087-03; plan Phase A "Decisions": "Target choice:
Nearest stays the game's rule. A lab-only setting for focus fire is added").

`OM_TP_TARGET_POLICY` (om_tactical_set_param; 0 = nearest, the default and the game's rule;
1 = most damaged, lab only). The contract call and enum are new (PP-contract): until they land the
tests that need them fail naming the missing symbol.

"Most damaged" is read as the most hit points missing; every candidate here is the same unit type
(Supply, 100 hp) so hit points missing and fraction missing rank the candidates the same way and no
tie exists. Only enemies inside the unit's attack range are candidates (R-087-03).

Scene: a Raider (range 200) at the origin with four enemies on one line:
  near     (100, 0)  100 hp  full
  damaged  (150, 0)   40 hp  most damaged inside range
  other    (190, 0)   90 hp
  far      (350, 0)   10 hp  the most damaged of all, but out of range
"""
import pytest

from test_PP_unit_support import RAIDER, SUPPLY, attack_move, get_param, set_param, spawn, step, target

POLICY = "OM_TP_TARGET_POLICY"


def _scene(lib, w, attack_moving):
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    near = spawn(lib, w, SUPPLY, 1, 100.0, 0.0)
    damaged = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    other = spawn(lib, w, SUPPLY, 1, 190.0, 0.0)
    far = spawn(lib, w, SUPPLY, 1, 350.0, 0.0)
    lib.om_unit_set_hp(w, damaged, 40.0)
    lib.om_unit_set_hp(w, other, 90.0)
    lib.om_unit_set_hp(w, far, 10.0)
    if attack_moving:
        attack_move(lib, w, [u], -3000.0, 0.0)
    return u, near, damaged, other, far


@pytest.mark.parametrize("attack_moving", [False, True])
def test_R_087_03_default_policy_picks_the_nearest(lib, world_factory, attack_moving):
    """Default (no setting touched): the unit attacks the nearest enemy in range, whatever their
    health. Green today; the control for the policy-1 test below, which has the same scene."""
    w = world_factory(n_regions=1)
    u, near, *_ = _scene(lib, w, attack_moving)

    step(lib, w, 4)

    assert target(lib, w, u) == near


@pytest.mark.parametrize("attack_moving", [False, True])
def test_R_087_03_policy_1_picks_the_most_damaged_in_range(lib, world_factory, attack_moving):
    """OM_TP_TARGET_POLICY = 1: the same scene, the same unit: it takes the most damaged enemy in
    range ('damaged'), not the nearest, and not the more damaged one that is out of range."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, POLICY, 1) == 0
    u, near, damaged, other, far = _scene(lib, w, attack_moving)

    step(lib, w, 4)

    assert target(lib, w, u) == damaged, (
        f"policy 1 should pick the most damaged in range ({damaged}); got {target(lib, w, u)} "
        f"(nearest is {near}, out-of-range most damaged is {far})")


def test_R_087_03_policy_back_to_0_picks_the_nearest_again(lib, world_factory):
    """Both ways: 1 then 0 restores nearest."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, POLICY, 1) == 0
    assert set_param(lib, w, POLICY, 0) == 0
    u, near, *_ = _scene(lib, w, False)

    step(lib, w, 4)

    assert target(lib, w, u) == near


def test_R_087_03_policy_setting_default_and_range(lib, world_factory):
    """Default 0; 1 reads back; any other value is refused and changes nothing (PP-contract)."""
    w = world_factory(n_regions=1)
    assert get_param(lib, w, POLICY) == 0.0
    assert set_param(lib, w, POLICY, 1) == 0
    assert get_param(lib, w, POLICY) == 1.0
    assert set_param(lib, w, POLICY, 2) == -1
    assert set_param(lib, w, POLICY, -1) == -1
    assert get_param(lib, w, POLICY) == 1.0
