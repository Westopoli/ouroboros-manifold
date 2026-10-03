# Skill lab formation batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

## Scene

Open map, no terrain. Side 0 of Vanguards plays line, blob, a 120-degree concave or a column counter against a naive blob (the counter plays against a line). Sizes 16, then 8 and 32; the enemy runs from half to one and a half times the size. The units start just outside sensor range of each other.

## Cells

| cell | size | enemy range | replicates | fights per cell | status |
|---|---|---|---|---|---|
| line@16 | 16 | 8 to 24 | 10 | 20 | naive |
| blob@16 | 16 | 8 to 24 | 10 | 20 | naive |
| concave@16 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| counter@16 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| line@8 | 8 | 4 to 12 | 10 | 20 | naive |
| blob@8 | 8 | 4 to 12 | 10 | 20 | naive |
| concave@8 | 8 | 4 to 12 | 10 | 20 | unconfirmed draft |
| counter@8 | 8 | 4 to 12 | 10 | 20 | unconfirmed draft |
| line@32 | 32 | 16 to 48 | 10 | 20 | naive |
| blob@32 | 32 | 16 to 48 | 10 | 20 | naive |
| concave@32 | 32 | 16 to 48 | 10 | 20 | unconfirmed draft |
| counter@32 | 32 | 16 to 48 | 10 | 20 | unconfirmed draft |
| line@16:Raider | 16 | 8 to 24 | 10 | 20 | naive |
| blob@16:Raider | 16 | 8 to 24 | 10 | 20 | naive |
| concave@16:Raider | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| counter@16:Raider | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| line@8:Raider | 8 | 4 to 12 | 10 | 20 | naive |
| blob@8:Raider | 8 | 4 to 12 | 10 | 20 | naive |
| concave@8:Raider | 8 | 4 to 12 | 10 | 20 | unconfirmed draft |
| counter@8:Raider | 8 | 4 to 12 | 10 | 20 | unconfirmed draft |
| line@32:Raider | 32 | 16 to 48 | 10 | 20 | naive |
| blob@32:Raider | 32 | 16 to 48 | 10 | 20 | naive |
| concave@32:Raider | 32 | 16 to 48 | 10 | 20 | unconfirmed draft |
| counter@32:Raider | 32 | 16 to 48 | 10 | 20 | unconfirmed draft |

## Results

- line@16, default: 16 units beat 16, lose to 17; mean fight ticks 1611.5; mean firing unit-seconds 880.96 side 0, 879.73 side 1; stalled fights 0
- blob@16, default: 16 units beat 15, lose to 16; mean fight ticks 1656.9; mean firing unit-seconds 852.29 side 0, 900.21 side 1; stalled fights 0
- concave@16 (unconfirmed draft), default: 16 units beat 16, lose to 17; mean fight ticks 1613.5; mean firing unit-seconds 862.04 side 0, 898.38 side 1; stalled fights 0
- counter@16 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1694.4; mean firing unit-seconds 812.19 side 0, 929.30 side 1; stalled fights 0
- line@8, default: 8 units beat 8, lose to 9; mean fight ticks 1510.8; mean firing unit-seconds 442.37 side 0, 442.77 side 1; stalled fights 0
- blob@8, default: 8 units beat 7, lose to 8; mean fight ticks 1537.5; mean firing unit-seconds 434.00 side 0, 453.85 side 1; stalled fights 0
- concave@8 (unconfirmed draft), default: 8 units beat 8, lose to 9; mean fight ticks 1538.1; mean firing unit-seconds 429.47 side 0, 448.69 side 1; stalled fights 0
- counter@8 (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 1532.5; mean firing unit-seconds 410.30 side 0, 462.76 side 1; stalled fights 0
- line@32, default: 32 units beat 32, lose to 33; mean fight ticks 1698.3; mean firing unit-seconds 1777.52 side 0, 1757.70 side 1; stalled fights 0
- blob@32, default: 32 units beat 31, lose to 32; mean fight ticks 1774.6; mean firing unit-seconds 1687.57 side 0, 1809.13 side 1; stalled fights 0
- concave@32 (unconfirmed draft), default: 32 units beat 32, lose to 33; mean fight ticks 1729.6; mean firing unit-seconds 1709.25 side 0, 1792.03 side 1; stalled fights 0
- counter@32 (unconfirmed draft), default: 32 units beat 31, lose to 32; mean fight ticks 1860.3; mean firing unit-seconds 1678.22 side 0, 1822.53 side 1; stalled fights 0
- line@16:Raider, default: 16 units beat 16, lose to 17; mean fight ticks 588.7; mean firing unit-seconds 243.33 side 0, 240.81 side 1; stalled fights 0
- blob@16:Raider, default: 16 units beat 15, lose to 16; mean fight ticks 632.2; mean firing unit-seconds 240.76 side 0, 248.62 side 1; stalled fights 0
- concave@16:Raider (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 591.7; mean firing unit-seconds 232.90 side 0, 251.39 side 1; stalled fights 0
- counter@16:Raider (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 614.1; mean firing unit-seconds 222.65 side 0, 247.56 side 1; stalled fights 0
- line@8:Raider, default: 8 units beat 8, lose to 9; mean fight ticks 505.3; mean firing unit-seconds 122.43 side 0, 120.44 side 1; stalled fights 0
- blob@8:Raider, default: 8 units beat 8, lose to 9; mean fight ticks 511.6; mean firing unit-seconds 121.74 side 0, 124.76 side 1; stalled fights 0
- concave@8:Raider (unconfirmed draft), default: 8 units beat 8, lose to 9; mean fight ticks 488.3; mean firing unit-seconds 116.55 side 0, 122.08 side 1; stalled fights 0
- counter@8:Raider (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 503.9; mean firing unit-seconds 113.04 side 0, 125.34 side 1; stalled fights 0
- line@32:Raider, default: 32 units beat 33, lose to 34; mean fight ticks 724.5; mean firing unit-seconds 512.04 side 0, 477.33 side 1; stalled fights 0
- blob@32:Raider, default: 32 units beat 32, lose to 33; mean fight ticks 822.7; mean firing unit-seconds 493.99 side 0, 507.49 side 1; stalled fights 0
- concave@32:Raider (unconfirmed draft), default: 32 units beat 30, lose to 31; mean fight ticks 789.9; mean firing unit-seconds 484.19 side 0, 515.25 side 1; stalled fights 0
- counter@32:Raider (unconfirmed draft), default: 32 units beat 28, lose to 29; mean fight ticks 848.2; mean firing unit-seconds 444.22 side 0, 517.14 side 1; stalled fights 0

## Vanguard against Raider

- line@16: Vanguard 16 units beat 16; Raider 16 units beat 16; same
- blob@16: Vanguard 16 units beat 15; Raider 16 units beat 15; same
- concave@16: Vanguard 16 units beat 16; Raider 16 units beat 15; Raider smaller
- counter@16: Vanguard 16 units beat 15; Raider 16 units beat 15; same
- line@8: Vanguard 8 units beat 8; Raider 8 units beat 8; same
- blob@8: Vanguard 8 units beat 7; Raider 8 units beat 8; Raider larger
- concave@8: Vanguard 8 units beat 8; Raider 8 units beat 8; same
- counter@8: Vanguard 8 units beat 7; Raider 8 units beat 7; same
- line@32: Vanguard 32 units beat 32; Raider 32 units beat 33; Raider larger
- blob@32: Vanguard 32 units beat 31; Raider 32 units beat 32; Raider larger
- concave@32: Vanguard 32 units beat 32; Raider 32 units beat 30; Raider smaller
- counter@32: Vanguard 32 units beat 31; Raider 32 units beat 28; Raider smaller

## What the instrument could not express

- skills S1, S3, S4, S5 have no formation play
- concave curves around the middle of the enemy's front (the draft's default focus), not the enemy's first anchor or a tracked arrival point

## Files

- formation.csv
- formation_run.md
- formation_page.html
