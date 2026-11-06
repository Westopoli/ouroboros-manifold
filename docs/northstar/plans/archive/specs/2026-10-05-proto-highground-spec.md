# Prototype spec: what high ground is worth (instrument, pass 1)

Under the Prototype gate (`docs/northstar/agile.md`). An instrument: it runs fights and prints a chart, for what Westley must read. Disposable. Nothing here changes the game until he decides.

## Why

No rule says what a force gains by holding the top of a slope. The bible gives a sight bonus per elevation tier (E-12 R-091-02, read by nothing) and the rules for a unit on a slope (E-01 R-004-06, R-004-07: it changes layer at the midline; the crossing takes the slope's length over the unit's speed). The goal names landscape first, and the lab has never measured height. This chart shows what each candidate rule is worth in whole units, so he can pick one or say none.

## What is measured

The real engine, through the skill lab, on open ground. A slope is stood in for by a timed layer change at a fixed place, which is how the engine already treats a unit crossing between layers (R-004-02: until halfway, only the layer it is leaving can hit it and it fights as that layer; from halfway, only the layer it is entering). This is an approximation: there is no ground, so nothing blocks sight or movement, and every climber crosses at the same spot. The page says so at the top.

- **Defenders:** 16 Vanguards holding (guard) on layer 3, at the "top".
- **Attackers:** 8 to 32 Vanguards starting 1,500 wu away on layer 2, attack-moving to the foot of the slope (300 wu short of the defenders), then ordered to layer 3.
- **Result per cell:** the break-even, in whole units: the largest attacking force the 16 defenders beat, with units firing per side, as in every other lab batch.
- **Control:** the same fight with both sides on one layer (no climb).

## The sweep (every number is a lab draft, provisional)

| Axis | Points |
|---|---|
| Climb time (slope length over speed; a Vanguard at 80 wu/s) | 2 s (160 wu), 4 s (320 wu), 8 s (640 wu), 15 s (1,200 wu) |
| Height rule | H0: no fire between layers (reach 0), so the climb alone decides. H1: both sides may fire one layer up or down at equal range and damage. H2: as H1, firing down has 1.25 times the range and firing up 0.75. H3: as H1, firing down does 1.25 times the damage and firing up 0.75. H4: H2 and H3 together. H5: as H1, and the defenders see 15 percent further per layer of height (R-091-02), if the engine setting can be reached from the lab; otherwise listed as not expressed |

20 cells and the control (24 with H5).

## What Westley reads

1. One chart: break-even (y) against climb time (x), one line per height rule, the flat control as a dashed line.
2. A table of the same numbers, with units firing per side.
3. A line per rule in words: "holding the top of a 640 wu slope is worth N units under this rule".
4. "What the instrument could not express": real ground (sight and movement are not blocked by the hill), walking units, more than one way up, a slope wider than one crossing place, the defender standing back from the edge.

## Questions for Westley after reading

1. Should height give anything beyond the climb itself (H0), and if so which: range, damage, sight, or a mix?
2. Is the size of the advantage about right, too small to matter, or large enough that nobody would ever attack uphill?
3. Should firing up be worse, or only firing down better?
4. Does the long slope (15 s) feel like it should be this much harder than the short one?

## Build notes

- New files only: `scripts/skilllab/highground.py`, `tests/skilllab/test_highground.py`, `tests/skilllab/integration/test_highground_real.py`. Branch `push/proto-highground`, from `push/lab-run-4`. No C code; no edit to another lab file.
- The climb time is the attackers' layer-change time. If the lab cannot set it for a unit type (a clone type with its own value, as the ping search does for attack range), stop and report; do not fake it with waits.
- Reach, and range and damage by layer offset, are existing engine settings (`om_roster_set_reach`, `OM_TP_RANGE_UP_n`, `OM_TP_RANGE_DOWN_n`, `OM_TP_DAMAGE_UP_n`, `OM_TP_DAMAGE_DOWN_n`).
- Positive controls (real engine): with H0 and a climb, no unit takes damage before a climber passes halfway; under H2 the defenders fire first; a longer climb never raises the break-even under H0; the control equals the lab's open-ground guard result for the same forces; same seed, same result.
- Outputs in the other batches' form: csv, run file, page (one chart, plain HTML and inline SVG, light and dark), under `docs/northstar/research/layer_dynamics/runs/<date>_highground/`.
