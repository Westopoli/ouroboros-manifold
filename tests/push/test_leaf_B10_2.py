# spec: docs/northstar/plans/push/specs/B10-2.md::Acceptance::AC-1
import pytest


def test_b10_2_traits_ability_warden_aura_acceptance():
    exit_code = pytest.main([
        "-q", "-p", "no:cacheprovider",
        "tests/csim/test_E11_S081_three_categories_a_soft_triangle.py",
        "tests/csim/test_E11_S082_the_six.py",
        "tests/csim/test_E11_S083_stats_traits_ability.py",
    ])
    assert exit_code == 0
