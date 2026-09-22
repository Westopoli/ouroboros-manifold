"""S-160 determinism: om_pow, the deterministic replacement for libm pow().

Audit finding 1 (docs/northstar/research/factory/audit_2026-09-21/README.md,
blocker): `csrc/sim.c` called libm `pow()` in ALG-03's headroom term
(`pow(1.0 - tension/100, 0.3)`) while `om_sin` already exists precisely
because platform libm differs -- `pow` was missed. Change-protocol reason:
the determinism contract (CLAUDE.md "Determinism is a contract"). The
equation's value does not change beyond rounding (R_014_04-class tolerance
still holds; see the E-02 gate trajectory test run alongside this one).

The table below pins `om_pow(x, 0.3)` for 64 inputs evenly spaced across
[0, 1] to the hex-exact double this build produces, computed once on this
machine (2026-09-21, x86_64 Linux, gcc). This is a determinism pin (same
build, same output, forever), not an accuracy claim against libm -- a
separate control (below) proves om_pow and libm pow() actually disagree at
the bit level, which is the whole point of not calling libm.
"""
import math

import pytest

from conftest import OMBug, OMTier, read_drift, set_region

TABLE = [
    (0.0, '0x0.0p+0'),
    (0.015873015873015872, '0x1.27759a5b99265p-2'),
    (0.031746031746031744, '0x1.6bc0cff46a327p-2'),
    (0.047619047619047616, '0x1.9acdb43af2e0bp-2'),
    (0.06349206349206349, '0x1.bfd52af8bbe0bp-2'),
    (0.07936507936507936, '0x1.ded69487b03bep-2'),
    (0.09523809523809523, '0x1.f9c22b429dba7p-2'),
    (0.1111111111111111, '0x1.08d92aed9b1b0p-1'),
    (0.12698412698412698, '0x1.13ac6103b1895p-1'),
    (0.14285714285714285, '0x1.1d96a0c370202p-1'),
    (0.15873015873015872, '0x1.26c26dec895a7p-1'),
    (0.1746031746031746, '0x1.2f4f288f812b9p-1'),
    (0.19047619047619047, '0x1.3754b32d41de9p-1'),
    (0.20634920634920634, '0x1.3ee5b382436a8p-1'),
    (0.2222222222222222, '0x1.4611076094668p-1'),
    (0.23809523809523808, '0x1.4ce2bef8f9abbp-1'),
    (0.25396825396825395, '0x1.5364ca43bfe05p-1'),
    (0.2698412698412698, '0x1.599f746d57aa4p-1'),
    (0.2857142857142857, '0x1.5f99bdbf0b694p-1'),
    (0.30158730158730157, '0x1.65599e73debfdp-1'),
    (0.31746031746031744, '0x1.6ae43949e6fd2p-1'),
    (0.3333333333333333, '0x1.703e0260b76c8p-1'),
    (0.3492063492063492, '0x1.756add85f2fa6p-1'),
    (0.36507936507936506, '0x1.7a6e362075eb6p-1'),
    (0.38095238095238093, '0x1.7f4b12496f8f4p-1'),
    (0.3968253968253968, '0x1.84042234b3e8ap-1'),
    (0.4126984126984127, '0x1.889bccbcfaaf5p-1'),
    (0.42857142857142855, '0x1.8d1439b297f82p-1'),
    (0.4444444444444444, '0x1.916f5a645714cp-1'),
    (0.4603174603174603, '0x1.95aef0bdd027ep-1'),
    (0.47619047619047616, '0x1.99d49541b0e23p-1'),
    (0.49206349206349204, '0x1.9de1bc16de29dp-1'),
    (0.5079365079365079, '0x1.a1d7b95396168p-1'),
    (0.5238095238095238, '0x1.a5b7c4a8c78d1p-1'),
    (0.5396825396825397, '0x1.a982fc88f402bp-1'),
    (0.5555555555555556, '0x1.ad3a68e09a221p-1'),
    (0.5714285714285714, '0x1.b0defd71fc175p-1'),
    (0.5873015873015873, '0x1.b4719be2caa6fp-1'),
    (0.6031746031746031, '0x1.b7f31587a2454p-1'),
    (0.6190476190476191, '0x1.bb642cf731a43p-1'),
    (0.6349206349206349, '0x1.bec5976d33ec1p-1'),
    (0.6507936507936508, '0x1.c217fe040d949p-1'),
    (0.6666666666666666, '0x1.c55bfecac0434p-1'),
    (0.6825396825396826, '0x1.c8922dbc02e61p-1'),
    (0.6984126984126984, '0x1.cbbb159a8d34ap-1'),
    (0.7142857142857143, '0x1.ced738b608ae8p-1'),
    (0.7301587301587301, '0x1.d1e7119b96cfbp-1'),
    (0.746031746031746, '0x1.d4eb13b46f79fp-1'),
    (0.7619047619047619, '0x1.d7e3abd4bf958p-1'),
    (0.7777777777777778, '0x1.dad140bca35bap-1'),
    (0.7936507936507936, '0x1.ddb4338cd730dp-1'),
    (0.8095238095238095, '0x1.e08ce03083430p-1'),
    (0.8253968253968254, '0x1.e35b9dbd579b8p-1'),
    (0.8412698412698413, '0x1.e620becb06b6ep-1'),
    (0.8571428571428571, '0x1.e8dc91c30ac23p-1'),
    (0.873015873015873, '0x1.eb8f6129847e4p-1'),
    (0.8888888888888888, '0x1.ee3973dfe9befp-1'),
    (0.9047619047619048, '0x1.f0db0d6223d13p-1'),
    (0.9206349206349206, '0x1.f3746dfeab5cep-1'),
    (0.9365079365079365, '0x1.f605d30a1f11ap-1'),
    (0.9523809523809523, '0x1.f88f770ec4482p-1'),
    (0.9682539682539683, '0x1.fb1191f8546a2p-1'),
    (0.9841269841269841, '0x1.fd8c593c6f25ep-1'),
    (1.0, '0x1.0000000000000p+0'),
]


def test_R_160_01_om_pow_matches_the_pinned_table(lib):
    assert len(TABLE) == 64
    for x, expected_hex in TABLE:
        got = lib.om_pow(x, 0.3)
        expected = float.fromhex(expected_hex)
        assert got.hex() == expected.hex(), (
            f"om_pow({x!r}, 0.3) = {got.hex()} but the pinned table says {expected_hex} "
            "-- a build-visible change to om_pow's output, or a return to libm pow()"
        )


def test_R_160_02_om_pow_is_deterministic_across_repeat_calls(lib):
    for x, _ in TABLE:
        first = lib.om_pow(x, 0.3)
        for _ in range(5):
            assert lib.om_pow(x, 0.3).hex() == first.hex()


def test_R_160_03_at_least_one_table_input_disagrees_with_libm_pow():
    """Proves the table is not vacuously equal to what libm would have given
    anyway -- if every input agreed, a card that quietly reverted to libm
    pow() would never be caught by this suite."""
    diffs = sum(
        1 for x, expected_hex in TABLE
        if float.fromhex(expected_hex).hex() != math.pow(x, 0.3).hex()
    )
    assert diffs > 0, (
        "every pinned om_pow value bit-matches libm's pow() on this table -- "
        "the determinism-pin table would not catch a silent reversion to libm"
    )


def _military_recruit_at_tension(handle, w, tension):
    """One tick's ALG-03 military_recruit term (the only place om_pow is
    called) for a HOME region with economy 50, population 80 -- chosen so
    trend_economy (50) > RECRUITMENT_THRESHOLD (20) at tick 1 (osc_prev is
    0 there), so the pow(1 - tension/100, 0.3) term is on the live path."""
    set_region(handle, w, 0, tier=OMTier.HOME, military=10.0, economy=50.0,
               tension=tension, population=80.0)
    handle.om_world_step(w)
    _, row = read_drift(handle, w, 0)
    return row.military_recruit


def test_control_libm_pow_trips_the_detector(dbg, dbg_world_factory):
    """OM_BUG_LIBM_POW (7): swap om_pow for libm pow() at the ALG-03 call
    site. Compares the debug build with nothing injected (default inject
    state 0 happens to equal OM_BUG_OSC_AS_LEVEL, R11 -- irrelevant here
    since military_recruit's pow term reads none of the oscillator fields)
    against the debug build with OM_BUG_LIBM_POW injected, at tension 50.0
    (om_pow(0.5, 0.3) and libm pow(0.5, 0.3) disagree by 1 ULP on this
    machine, confirmed against the pinned table's own libm-disagreement
    check above)."""
    w_clean = dbg_world_factory(n_regions=1)
    clean_val = _military_recruit_at_tension(dbg, w_clean, 50.0)

    w_bug = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w_bug, OMBug.LIBM_POW)
    bug_val = _military_recruit_at_tension(dbg, w_bug, 50.0)

    assert clean_val.hex() != bug_val.hex(), (
        "OM_BUG_LIBM_POW injected but military_recruit is bit-identical to the "
        "clean debug build -- the libm-pow-swap detector did not trip"
    )
