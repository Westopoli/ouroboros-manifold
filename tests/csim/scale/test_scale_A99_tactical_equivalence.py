"""A99 equivalence guard, large runs (2,501 and 4,996 units). Same recorded hashes and
helpers as tests/csim/test_E13_A99_tactical_equivalence.py (see its docstring for the
generator); gated behind OM_SCALE=1 by this directory's conftest because the runs take
minutes. The 4,996-unit fight has both sides above the 2,048 contact cap
(OM_MACRO_ORDER_CAP in csrc/enemy_macro.c), so the cap-reproducing contact check is exercised.
"""
import pytest

import a99_tactical_runs as A

SCALE = [r for r in A.RUNS if r[4] == "scale"]


@pytest.mark.parametrize("run", SCALE, ids=[r[0] for r in SCALE])
def test_A99_tactical_trace_equals_recorded_hashes_large(lib, run):
    name, units, gap, steps, _tier = run
    rec = A.load_recorded()[name]["hashes"]
    got = A.run_hashes(lib, units, gap, steps)
    bad = A.first_mismatch(rec, got)
    assert bad is None, f"{name}: step {bad} hash {got[bad:bad+1]} != recorded {rec[bad:bad+1]}"


def test_A99_largest_fight_has_both_sides_over_the_contact_cap(lib):
    player, enemy = A.side_counts(lib, 4996)
    assert player > 2048 and enemy > 2048, (player, enemy)
