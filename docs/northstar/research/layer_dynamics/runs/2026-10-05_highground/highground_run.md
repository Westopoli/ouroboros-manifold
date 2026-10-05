# High-ground instrument: highground

The slope is stood in for by a timed layer change at one place: the climbers walk to the foot and are ordered up, and the engine treats them as crossing for the climb time. There is no ground: nothing blocks sight or movement, and every climber crosses at the same spot. Every number on this page is a provisional lab draft.

| rule | climb (s) | slope (wu) | break-even (units) | attackers firing (unit-s) | defenders firing (unit-s) |
|---|---|---|---|---|---|
| H0 | 2 | 160 | 11 | 647.4 | 875.4 |
| H0 | 4 | 320 | 15 | 964.0 | 1198.7 |
| H0 | 8 | 640 | 16 | 1102.3 | 1277.8 |
| H0 | 15 | 1200 | 16 | 1104.0 | 1279.3 |
| H1 | 2 | 160 | 5 | 536.1 | 394.1 |
| H1 | 4 | 320 | 6 | 676.2 | 458.9 |
| H1 | 8 | 640 | 6 | 702.5 | 460.2 |
| H1 | 15 | 1200 | 7 | 842.1 | 516.0 |
| H2 | 2 | 160 | 6 | 711.0 | 457.6 |
| H2 | 4 | 320 | 9 | 726.9 | 708.6 |
| H2 | 8 | 640 | 10 | 832.5 | 767.3 |
| H2 | 15 | 1200 | 10 | 826.5 | 794.6 |
| H3 | 2 | 160 | 5 | 537.0 | 393.9 |
| H3 | 4 | 320 | 6 | 679.4 | 458.1 |
| H3 | 8 | 640 | 6 | 704.7 | 457.9 |
| H3 | 15 | 1200 | 6 | 763.5 | 455.9 |
| H4 | 2 | 160 | 6 | 708.0 | 457.4 |
| H4 | 4 | 320 | 9 | 721.0 | 702.4 |
| H4 | 8 | 640 | 9 | 562.6 | 699.1 |
| H4 | 15 | 1200 | 11 | 1035.7 | 839.5 |
| control | - | - | 7 | 879.8 | 527.5 |

* the search hit its bound (0 or 48).

- Holding the top of a 160 wu slope is worth 4 units under H0 (no fire between layers).
- Holding the top of a 320 wu slope is worth 8 units under H0 (no fire between layers).
- Holding the top of a 640 wu slope is worth 9 units under H0 (no fire between layers).
- Holding the top of a 1200 wu slope is worth 9 units under H0 (no fire between layers).
- Holding the top of a 160 wu slope is worth -2 units under H1 (fire one layer up or down, equal).
- Holding the top of a 320 wu slope is worth -1 units under H1 (fire one layer up or down, equal).
- Holding the top of a 640 wu slope is worth -1 units under H1 (fire one layer up or down, equal).
- Holding the top of a 1200 wu slope is worth 0 units under H1 (fire one layer up or down, equal).
- Holding the top of a 160 wu slope is worth -1 units under H2 (H1, range down 1.25, up 0.75).
- Holding the top of a 320 wu slope is worth 2 units under H2 (H1, range down 1.25, up 0.75).
- Holding the top of a 640 wu slope is worth 3 units under H2 (H1, range down 1.25, up 0.75).
- Holding the top of a 1200 wu slope is worth 3 units under H2 (H1, range down 1.25, up 0.75).
- Holding the top of a 160 wu slope is worth -2 units under H3 (H1, damage down 1.25, up 0.75).
- Holding the top of a 320 wu slope is worth -1 units under H3 (H1, damage down 1.25, up 0.75).
- Holding the top of a 640 wu slope is worth -1 units under H3 (H1, damage down 1.25, up 0.75).
- Holding the top of a 1200 wu slope is worth -1 units under H3 (H1, damage down 1.25, up 0.75).
- Holding the top of a 160 wu slope is worth -1 units under H4 (H2 and H3 together).
- Holding the top of a 320 wu slope is worth 2 units under H4 (H2 and H3 together).
- Holding the top of a 640 wu slope is worth 2 units under H4 (H2 and H3 together).
- Holding the top of a 1200 wu slope is worth 4 units under H4 (H2 and H3 together).

## What the instrument could not express

- Real ground: sight and movement are not blocked by the hill; there is no ground.
- Walking units: every climber changes layer at one spot; nobody walks up.
- More than one way up: there is one crossing place.
- A slope wider than one crossing place: all climbers cross at the same spot.
- The defender standing back from the edge: the defenders hold at the top, 300 wu past the foot.
- H5 (sight bonus per layer of height, R-091-02): the engine's cross-layer vision settings (OM_TP_VISION_UP_n and DOWN_n) are a fraction of the sensor radius, capped at 1.0, so they cannot give +15 percent; not expressed.

## Questions for Westley

1. Should height give anything beyond the climb itself (H0), and if so which: range, damage, sight, or a mix?
2. Is the size of the advantage about right, too small to matter, or large enough that nobody would ever attack uphill?
3. Should firing up be worse, or only firing down better?
4. Does the long slope (15 s) feel like it should be this much harder than the short one?
