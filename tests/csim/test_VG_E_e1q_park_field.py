"""PARKED (rules.md (d): a value or meaning nobody gave goes in a *_park_* file; this file stays off the landing candidate).
Two cases of the spec's E1q-field Tests paragraph that the spec's own growth formulas cannot satisfy as worded. Written on the
K-e5 tree; the Architect rules each, the case is then moved into test_VG_E_e1q_field.py (or dropped) under a ledger row.
Register rows: none exist yet; proposed Q-E1Q-sea-density and Q-E1Q-symmetry-tolerance (Architect to add).

1. Q-E1Q-symmetry-tolerance. Spec Tests: "on a flat synthetic terrain with no sea ... the field is 8-fold symmetric about the
   core". The growth runs in place in the order NW N NE W E SW S SE (E1q-field), and the Q16 truncation at the end of each step
   meets float products formed along different paths, so the mirrors and quarter turns differ from the centre by 1 to 3 Q16
   units (1.5e-5 to 4.6e-5) while the transposition is exact (a Python model of the spec's formulas: 6, 12 and 30 growth steps, econ
   0.4 and 1.0: transposition 0 differing cells, every other symmetry 4 to 1896 cells differing by at most 3 Q16 units). The
   field file asserts the transposition exactly. A tolerance is Westley's: DRAFT-symmetry-ulps below is the test writer's draft
   (4 Q16 units, one above the model's maximum of 3), not a ruling.
2. Q-E1Q-sea-density. Spec Tests: "a sea strip has D == 0 in the sea". The E1q-field formulas give a water cell a reach
   (factor 0.85, WATER_CROSS) and then ease D toward min(1, P * maturity * econ) for every cell with P > 0, so D > 0 in the sea
   (the mockup does the same, settlement_sim.gd:184-185, 232-235; the model gives 0.21, 0.18, 0.15 on a three-cell strip). Either
   the port zeroes D on water cells (a rule the E1q-field paragraph does not state) or the test line is dropped; lots are
   kept out of the sea by the buildable rule alone (E1q-lots), which the lots file proves.
Both NEEDS E1q-field: yes. Red on the K-e5 tree: the legacy field is centred on the canvas centre and has no water.
"""

from test_VG_E_e1q_field import SEA_CM, SIDE, d_at, flat, heights, objective_cell, scene, sea_strip, steps

DRAFT_SYMMETRY_ULPS = 4          # DRAFT-symmetry-ulps: Q16 units of 1/65536; not Westley's number yet
Q16 = 65536.0
RADIUS = 10


def test_flat_land_field_is_eight_fold_symmetric_within_the_draft_tolerance(lib, world_factory):
    """Spec Tests (E1q-field), 8-fold symmetry about the core with DRAFT-symmetry-ulps. Control: at least 100 nonzero cells."""
    w = scene(lib, world_factory, terrain=flat)
    cx, cy = objective_cell(lib, w)
    steps(lib, w, 60 * 10 + 1)
    nonzero = sum(1 for dx in range(-RADIUS, RADIUS + 1) for dy in range(-RADIUS, RADIUS + 1) if d_at(lib, w, cx + dx, cy + dy) > 0.0)
    assert nonzero >= 100, f"control: only {nonzero} nonzero cells in the box"
    worst, where = 0.0, None
    for dy in range(-RADIUS, RADIUS + 1):
        for dx in range(-RADIUS, RADIUS + 1):
            here = d_at(lib, w, cx + dx, cy + dy)
            for ox, oy in ((dx, -dy), (-dx, dy), (-dx, -dy), (dy, dx), (dy, -dx), (-dy, dx), (-dy, -dx)):
                gap = abs(here - d_at(lib, w, cx + ox, cy + oy))
                if gap > worst:
                    worst, where = gap, (dx, dy, ox, oy)
    assert worst * Q16 <= DRAFT_SYMMETRY_ULPS, f"widest asymmetry {worst * Q16:.2f} Q16 units at {where} (draft {DRAFT_SYMMETRY_ULPS})"


def test_sea_cells_hold_no_density(lib, world_factory):
    """Spec Tests (E1q-field), "D == 0 in the sea" on the three-cell sea strip, after 25 growth steps. Control: the land cells
    beside the strip have density, so the zero is not an empty field."""
    w = scene(lib, world_factory, terrain=sea_strip)
    cx, cy = objective_cell(lib, w)
    _, h = heights(lib, w)
    steps(lib, w, 60 * 25 + 1)
    assert d_at(lib, w, cx + 5, cy) > 0.0 and d_at(lib, w, cx + 9, cy) > 0.0, "control: no density beside the strip"
    wet = [(gx, gy) for gy in range(cy - 10, cy + 11) for gx in range(cx + 6, cx + 9) if h[gy * SIDE + gx] == SEA_CM
           and d_at(lib, w, gx, gy) != 0.0]
    assert wet == [], f"{len(wet)} sea cells hold density, first {wet[:3]} = {d_at(lib, w, *wet[0]) if wet else 0}"
