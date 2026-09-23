# spec: docs/northstar/plans/push/specs/B10-4.md::Acceptance::AC-1
import pytest


def test_b10_4_reading_units_on_screen_acceptance():
    exit_code = pytest.main([
        "-q", "-p", "no:cacheprovider",
        "tests/csim/test_E11_S081_three_categories_a_soft_triangle.py",
        "tests/csim/test_E11_S082_the_six.py",
        "tests/csim/test_E11_S083_stats_traits_ability.py",
        "tests/csim/test_E11_S086_one_ability_each.py",
        "tests/csim/test_E11_S088_reading_units_on_screen.py",
    ])
    assert exit_code == 0
