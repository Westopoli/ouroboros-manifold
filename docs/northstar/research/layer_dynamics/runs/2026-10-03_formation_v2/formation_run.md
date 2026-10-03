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

Cells within 2 enemy units of a break-even run 3 times the fights.

## Results

- line@16, default: 16 units beat 15, lose to 16; mean fight ticks 2249.2; mean firing unit-seconds 972.38 side 0, 933.25 side 1; stalled fights 0 | pair spread 0.09 to 0.40
- blob@16, default: 16 units beat 15, lose to 16; mean fight ticks 2356.5; mean firing unit-seconds 958.99 side 0, 959.52 side 1; stalled fights 0 | pair spread -0.21 to 0.40
- concave@16 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 2221.3; mean firing unit-seconds 945.73 side 0, 960.79 side 1; stalled fights 0 | pair spread -0.06 to 0.43
- counter@16 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 2354.1; mean firing unit-seconds 892.34 side 0, 990.76 side 1; stalled fights 0 | pair spread -0.23 to 0.30
- line@8, default: 8 units beat 8, lose to 9; mean fight ticks 1814.0; mean firing unit-seconds 463.96 side 0, 490.16 side 1; stalled fights 0 | pair spread -0.22 to 0.29
- blob@8, default: 8 units beat 7, lose to 8; mean fight ticks 1812.2; mean firing unit-seconds 463.85 side 0, 463.14 side 1; stalled fights 0 | pair spread 0.10 to 0.45
- concave@8 (unconfirmed draft), default: 8 units beat 8, lose to 9; mean fight ticks 1800.7; mean firing unit-seconds 455.30 side 0, 486.94 side 1; stalled fights 0 | pair spread -0.23 to 0.26
- counter@8 (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 1790.1; mean firing unit-seconds 454.38 side 0, 450.32 side 1; stalled fights 1 | pair spread 0.11 to 0.49
- line@32, default: 32 units beat 34, lose to 35; mean fight ticks 2718.3; mean firing unit-seconds 2105.80 side 0, 1856.38 side 1; stalled fights 0 | pair spread -0.18 to 0.32
- blob@32, default: 32 units beat 30, lose to 31; mean fight ticks 2997.2; mean firing unit-seconds 1925.79 side 0, 1929.71 side 1; stalled fights 2 | pair spread -0.17 to 0.35
- concave@32 (unconfirmed draft), default: 32 units beat 30, lose to 31; mean fight ticks 2910.5; mean firing unit-seconds 1867.09 side 0, 1961.95 side 1; stalled fights 1 | pair spread -0.31 to 0.34
- counter@32 (unconfirmed draft), default: 32 units beat 28, lose to 29; mean fight ticks 3002.2; mean firing unit-seconds 1663.64 side 0, 2013.09 side 1; stalled fights 0 | pair spread -0.14 to 0.36
- line@16:Raider, default: 16 units beat 16, lose to 17; mean fight ticks 660.2; mean firing unit-seconds 262.14 side 0, 261.59 side 1; stalled fights 0 | pair spread -0.22 to 0.30
- blob@16:Raider, default: 16 units beat 15, lose to 16; mean fight ticks 697.5; mean firing unit-seconds 260.41 side 0, 259.20 side 1; stalled fights 0 | pair spread -0.11 to 0.33
- concave@16:Raider (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 650.5; mean firing unit-seconds 251.74 side 0, 262.73 side 1; stalled fights 0 | pair spread -0.25 to 0.36
- counter@16:Raider (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 685.5; mean firing unit-seconds 242.71 side 0, 260.63 side 1; stalled fights 0 | pair spread 0.01 to 0.34
- line@8:Raider, default: 8 units beat 8, lose to 9; mean fight ticks 541.1; mean firing unit-seconds 129.60 side 0, 131.96 side 1; stalled fights 0 | pair spread -0.21 to 0.27
- blob@8:Raider, default: 8 units beat 7, lose to 8; mean fight ticks 545.4; mean firing unit-seconds 128.11 side 0, 135.37 side 1; stalled fights 0 | pair spread 0.17 to 0.40
- concave@8:Raider (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 528.1; mean firing unit-seconds 122.36 side 0, 133.84 side 1; stalled fights 0 | pair spread 0.25 to 0.42
- counter@8:Raider (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 530.6; mean firing unit-seconds 120.22 side 0, 126.61 side 1; stalled fights 0 | pair spread 0.07 to 0.44
- line@32:Raider, default: 32 units beat 33, lose to 34; mean fight ticks 797.8; mean firing unit-seconds 556.21 side 0, 502.63 side 1; stalled fights 0 | pair spread -0.14 to 0.26
- blob@32:Raider, default: 32 units beat 31, lose to 32; mean fight ticks 893.8; mean firing unit-seconds 521.68 side 0, 535.75 side 1; stalled fights 0 | pair spread -0.18 to 0.29
- concave@32:Raider (unconfirmed draft), default: 32 units beat 30, lose to 31; mean fight ticks 859.7; mean firing unit-seconds 511.21 side 0, 532.85 side 1; stalled fights 0 | pair spread -0.27 to 0.32
- counter@32:Raider (unconfirmed draft), default: 32 units beat 29, lose to 30; mean fight ticks 931.7; mean firing unit-seconds 473.31 side 0, 536.62 side 1; stalled fights 0 | pair spread -0.09 to 0.23

## Vanguard against Raider

- line@16: Vanguard 16 units beat 15; Raider 16 units beat 16; Raider larger
- blob@16: Vanguard 16 units beat 15; Raider 16 units beat 15; same
- concave@16: Vanguard 16 units beat 15; Raider 16 units beat 15; same
- counter@16: Vanguard 16 units beat 15; Raider 16 units beat 15; same
- line@8: Vanguard 8 units beat 8; Raider 8 units beat 8; same
- blob@8: Vanguard 8 units beat 7; Raider 8 units beat 7; same
- concave@8: Vanguard 8 units beat 8; Raider 8 units beat 7; Raider smaller
- counter@8: Vanguard 8 units beat 7; Raider 8 units beat 7; same
- line@32: Vanguard 32 units beat 34; Raider 32 units beat 33; Raider smaller
- blob@32: Vanguard 32 units beat 30; Raider 32 units beat 31; Raider larger
- concave@32: Vanguard 32 units beat 30; Raider 32 units beat 30; same
- counter@32: Vanguard 32 units beat 28; Raider 32 units beat 29; Raider larger

## What the instrument could not express

- skills S1, S3, S4, S5 have no formation play
- concave curves around the middle of the enemy's front (the draft's default focus), not the enemy's first anchor or a tracked arrival point

## Files

- formation.csv
- formation_run.md
- formation_page.html
