"""The parity tolerance: the ONE place the side-by-side harness reads it from.

Confirmed by Westley, 2026-10-02 (Architect A149): position 0.05 wu, facing 2e-3 rad. The measured
proposal discussed below was 1e-6 wu; 0.05 is his number (a threshold is his: narrowing needs no one,
widening needs him). Plan: docs/northstar/plans/
2026-10-02-movement-layers-and-search-plan.md, Phase A "Verification" 1 ("Tolerance measured
first, proposed to Westley, then fixed"). Every number below is reproduced by
`python -m parity.measure --tolerance` (from tests/csim/) and `--sensitivity` (agora venv python).

PARITY_TOLERANCE (position, world units): the largest difference any unit may show against the
Python on any tick. Measured by running every scene through the Python twice, once with its trig
steering sweep and once with the fixed direction vectors the plan puts in the C (P8: +-30, +-60,
+-90 degrees as constants rotated onto the seek vector), constants rounded to n decimals; largest
position difference over all nine scenes and every tick:

    constants          largest position difference     largest facing difference
    full double                     0 wu                          0 rad
    12 decimals               1.0e-10 wu                    1.8e-12 rad
    10 decimals               3.5e-9  wu                    6.7e-11 rad   (what csrc's present sweep constant carries)
    8 decimals                8.5e-7  wu                    1.6e-8  rad
    6 decimals                9.1e-5  wu                    1.7e-6  rad
    4 decimals                5.7e-3  wu                    1.1e-4  rad

The proposal, 1e-6 wu, passes constants of 8 decimals or more and fails 6 or fewer, so it asks of
algorithms.md / alg_constants.py that the six sweep constants carry at least 8 decimals. It also asks
that the straight-line step use the Python's own direction vector (dx / dist, a sqrt, allowed), not
om_cos(om_atan2(...)): today's C trig alone leaves 4.7e-3 wu after a 450 wu diagonal march
(scene control_diagonal_march) and 2.5e-5 wu after a 450 wu march along x.
Westley's 0.05 wu (A149) passes constants of 3 decimals or more (3 and 4 decimals both measure
5.7e-3 wu over all nine scenes) and fails 2 decimals (3.98 wu) and 1 decimal (118 wu).

What it does NOT absorb: collision pair order. The Python takes pairs by grid cell, the C by id.
In the six scenes reversing the Python's own pair order changes nothing (0 wu), but in a pile-up
(scene crowd_converges, eight units sent to one point) it moves units by 124 wu and turns one
through pi. Exact parity through a dense pile-up needs the C to take pairs in the Python's order;
the six scenes avoid pile-ups on purpose and test_parity_harness.py pins both facts.

PARITY_FACING_TOLERANCE (radians, shortest arc): facing is an angle, so it cannot share the
position number; it sits beside it with the same status (the brief asked for one constant; this is
the second, and Westley may fold or move it). The fixed vectors barely move facing (1.6e-8 rad at
8 decimals), but the C turns toward an om_atan2 target, and the C's om_atan2 (csrc/tactical_move.c
267-285, coefficients 0.2447 and 0.0663; libm atan2 is banned for determinism) is off by up to
1.51e-3 rad (largest error over a full circle, replicated and scanned at 0.01 degree). 2e-3 rad is
that error rounded up; a tighter facing tolerance needs a better om_atan2 first.
"""

# Largest position difference, in wu, any unit may show against the Python on any tick.
PARITY_TOLERANCE = 0.05  # Westley, 2026-10-02 (A149): position, world units; was proposed as 1e-6

# Largest facing difference, in radians (shortest arc), any unit may show on any tick.
PARITY_FACING_TOLERANCE = 2e-3  # confirmed unchanged by Westley, 2026-10-02 (A149)
