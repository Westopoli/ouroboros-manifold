# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 arm M ("break-even near equal ... not as a verdict on where equal sits"), section 1 precondition 3 ("Thresholds are Westley's"); README section 4 C0 ("tolerance to be set by Westley")
"""PARKED, not red and not green: numbers nobody has given. Register row: Q-156-02 (open; the mirror break-even tolerance of C0 is one of the pass marks Westley has not confirmed, ledger DEC-Q-156-02-2026-10-21).

A scan reports the cell map with its flips; whether the first flip is "near equal" needs a tolerance (how many soldiers either side of 16 is near) and a rule for the cells in between. Until Westley rules the tolerance, `scan_m` reports where the flip is and `part_word_m` reads only the
direction (the larger force wins in the cells where numbers differ). When he gives the number, this file becomes a test: the first flip's `before` and `after` lie within it of `OWN_HEADS`.
Nothing here is invented: no number appears below."""
import pytest


@pytest.mark.skip(reason="parked: the near-equal tolerance of C0 is Westley's (register Q-156-02, open)")
def test_the_first_flip_lies_within_his_tolerance_of_equal_numbers():
    raise AssertionError("parked until the tolerance is ruled")
