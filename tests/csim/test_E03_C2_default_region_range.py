"""C2 / R-021-01 (docs/bible/epics/E-03-world-generation.md): "Given a seed, When the world is generated,
Then the region count is an integer drawn uniformly from [250, 400] and the faction count is 15."
Default range, no gen_set_region_range call. No count other than the two bounds is asserted: the
rule gives only the range.
"""
from conftest import generate

SEEDS = list(range(1, 13))


def _count(lib, seed):
    w = lib.om_world_new(0, seed)
    assert w
    ok = generate(lib, w)
    n = lib.om_region_count(w)
    lib.om_world_free(w)
    return ok, n


def test_R_021_01_default_generation_lands_in_250_to_400(lib):
    """Given twelve seeds at the default range, When each world is generated, Then each succeeds with 250 <= count <= 400."""
    for seed in SEEDS:
        ok, n = _count(lib, seed)
        assert ok == 1, f"seed {seed}: generation failed"
        assert 250 <= n <= 400, f"seed {seed}: region count {n} not in [250, 400]"


def test_R_021_01_the_count_is_drawn_not_fixed(lib):
    """Given the same twelve seeds, When the counts are compared, Then they are not all equal (a draw, not a constant)."""
    counts = {_count(lib, s)[1] for s in SEEDS}
    assert len(counts) > 1, f"every seed gave {counts}: the range is not being drawn from"


def test_control_R_021_01_the_old_range_would_fail_the_check(lib):
    """Control: the counting helper reports a real count, so the 250 lower bound above is a live check (a 60..110 world is below it)."""
    w = lib.om_world_new(0, 1)
    lib.om_gen_set_region_range(w, 60, 110)
    generate(lib, w)
    assert lib.om_region_count(w) < 250
    lib.om_world_free(w)
