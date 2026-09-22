# spec: docs/northstar/plans/push/specs/b1-events.md::Acceptance criteria::AC-1
"""Adapter test, common brief 2026-09-22 line 9 (pieces.toml not yet written by
M0 at F6; acceptance ids taken from the spec's Acceptance criteria section,
collected 2026-09-22 and unchanged since). Runs the piece's real acceptance
node ids through pytest.main and asserts exit 0. No new assertions of its
own — the fenced tests it invokes are the spec."""
import pytest

ACCEPTANCE = [
    "tests/csim/test_E04_S026_crises_start_when_a_line_is_crossed.py",
    "tests/csim/test_E04_S027_one_thing_leads_to_another.py",
    "tests/csim/test_E04_S028_disasters_stack_contradictions_do_not.py",
    "tests/csim/test_E04_S029_some_pressures_never_stop.py",
    "tests/csim/test_E04_S030_the_launch_event_library.py",
    "tests/csim/test_E04_wiring.py",
]


def test_leaf_b1_events_acceptance_green():
    assert pytest.main(["-q", "-p", "no:cacheprovider", *ACCEPTANCE]) == 0
