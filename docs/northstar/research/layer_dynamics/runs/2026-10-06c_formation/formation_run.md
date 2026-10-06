# Skill lab formation batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

Lab rule, provisional (v2): a side re-orders when none of its units has an enemy in attack range and it sees at least one enemy; a unit with a destination blocks the re-order only if it moved at least 30 wu in the last 200 ticks; the order sends every unit of the side at the position of the nearest seen enemy to the side's centroid, with no chunk offsets (one group if the side fits inside the 450 wu scatter limit of E-13 R-095-03, otherwise chunks all aimed at that point); considered every mopup_interval_ticks, counted per fight, same for both sides. Setting: mopup=True, mopup_interval_ticks=200. Each fight's count is the mopup_orders column.

## Scene

Open map, no terrain. Side 0 of Vanguards plays line, blob, a 120-degree concave or a column counter against a naive blob (the counter plays against a line). Sizes 16, then 8 and 32; the enemy runs from half to one and a half times the size. The units start just outside sensor range of each other.

## Cells

| cell | size | enemy range | replicates | fights per cell | status |
|---|---|---|---|---|---|
| line@16 | 16 | 8 to 24 | 10 | 20 | naive |
| blob@16 | 16 | 8 to 24 | 10 | 20 | naive |
| concave@16 | 16 | 8 to 24 | 10 | 20 | draft |
| counter@16 | 16 | 8 to 24 | 10 | 20 | draft |
| line@8 | 8 | 4 to 12 | 10 | 20 | naive |
| blob@8 | 8 | 4 to 12 | 10 | 20 | naive |
| concave@8 | 8 | 4 to 12 | 10 | 20 | draft |
| counter@8 | 8 | 4 to 12 | 10 | 20 | draft |
| line@32 | 32 | 16 to 48 | 10 | 20 | naive |
| blob@32 | 32 | 16 to 48 | 10 | 20 | naive |
| concave@32 | 32 | 16 to 48 | 10 | 20 | draft |
| counter@32 | 32 | 16 to 48 | 10 | 20 | draft |
| line@16:Raider | 16 | 8 to 24 | 10 | 20 | naive |
| blob@16:Raider | 16 | 8 to 24 | 10 | 20 | naive |
| concave@16:Raider | 16 | 8 to 24 | 10 | 20 | draft |
| counter@16:Raider | 16 | 8 to 24 | 10 | 20 | draft |
| line@8:Raider | 8 | 4 to 12 | 10 | 20 | naive |
| blob@8:Raider | 8 | 4 to 12 | 10 | 20 | naive |
| concave@8:Raider | 8 | 4 to 12 | 10 | 20 | draft |
| counter@8:Raider | 8 | 4 to 12 | 10 | 20 | draft |
| line@32:Raider | 32 | 16 to 48 | 10 | 20 | naive |
| blob@32:Raider | 32 | 16 to 48 | 10 | 20 | naive |
| concave@32:Raider | 32 | 16 to 48 | 10 | 20 | draft |
| counter@32:Raider | 32 | 16 to 48 | 10 | 20 | draft |

Cells within 2 enemy units of a break-even run 3 times the fights.

## Results

- line@16, default: 16 units beat 16, lose to 17; mean fight ticks 3545.0; mean firing unit-seconds 1138.13 side 0, 928.14 side 1; stalled fights 0 (quiet stalemates only); caps 12; draws 0 | pair spread 0.15 to 0.36
- blob@16, default: 16 units beat 14, lose to 15; mean fight ticks 3643.9; mean firing unit-seconds 998.82 side 0, 939.50 side 1; stalled fights 0 (quiet stalemates only); caps 49; draws 0 | pair spread 0.08 to 0.43
- concave@16 (unconfirmed draft), default: 16 units beat 14, lose to 15; mean fight ticks 3368.6; mean firing unit-seconds 1061.53 side 0, 871.45 side 1; stalled fights 0 (quiet stalemates only); caps 22; draws 0 | pair spread 0.27 to 0.46
- counter@16 (unconfirmed draft), default: 16 units beat 11, lose to 12; mean fight ticks 4250.7; mean firing unit-seconds 893.20 side 0, 922.57 side 1; stalled fights 0 (quiet stalemates only); caps 128; draws 0 | pair spread 0.35 to 0.60
- line@8, default: 8 units beat 8, lose to 9; mean fight ticks 2791.9; mean firing unit-seconds 504.61 side 0, 501.56 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.00 to 0.26
- blob@8, default: 8 units beat 7, lose to 8; mean fight ticks 2828.6; mean firing unit-seconds 490.59 side 0, 480.35 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread 0.07 to 0.41
- concave@8 (unconfirmed draft), default: 8 units beat 8, lose to 9; mean fight ticks 2979.3; mean firing unit-seconds 488.24 side 0, 510.06 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.23 to 0.29
- counter@8 (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 3053.4; mean firing unit-seconds 448.90 side 0, 505.79 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.10 to 0.31
- line@32, default: 32 units beat 37, lose to 38; mean fight ticks 4488.2; mean firing unit-seconds 2555.87 side 0, 1615.18 side 1; stalled fights 0 (quiet stalemates only); caps 32; draws 0 | pair spread 0.16 to 0.40
- blob@32, default: 32 units beat 28, lose to 29; mean fight ticks 3840.4; mean firing unit-seconds 1942.99 side 0, 1859.89 side 1; stalled fights 0 (quiet stalemates only); caps 33; draws 0 | pair spread 0.24 to 0.44
- concave@32 (unconfirmed draft), default: 32 units beat 31, lose to 32; mean fight ticks 3924.7; mean firing unit-seconds 2226.49 side 0, 1750.23 side 1; stalled fights 0 (quiet stalemates only); caps 26; draws 0 | pair spread 0.24 to 0.45
- counter@32 (unconfirmed draft), default: 32 units beat 20, lose to 21; mean fight ticks 5769.9; mean firing unit-seconds 1678.08 side 0, 1896.46 side 1; stalled fights 0 (quiet stalemates only); caps 141; draws 0 | pair spread 0.53 to 0.64
- line@16:Raider, default: 16 units beat 17, lose to 18; mean fight ticks 1089.2; mean firing unit-seconds 314.61 side 0, 275.21 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.03 to 0.31
- blob@16:Raider, default: 16 units beat 15, lose to 16; mean fight ticks 1273.3; mean firing unit-seconds 278.06 side 0, 274.04 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.09 to 0.26
- concave@16:Raider (unconfirmed draft), default: 16 units beat 16, lose to 17; mean fight ticks 1143.6; mean firing unit-seconds 291.37 side 0, 275.53 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.14 to 0.28
- counter@16:Raider (unconfirmed draft), default: 16 units beat 14, lose to 15; mean fight ticks 1431.1; mean firing unit-seconds 251.97 side 0, 275.03 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.02 to 0.39
- line@8:Raider, default: 8 units beat 8, lose to 9; mean fight ticks 878.9; mean firing unit-seconds 141.28 side 0, 136.38 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.03 to 0.30
- blob@8:Raider, default: 8 units beat 7, lose to 8; mean fight ticks 881.5; mean firing unit-seconds 131.37 side 0, 132.78 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread 0.08 to 0.41
- concave@8:Raider (unconfirmed draft), default: 8 units beat 8, lose to 9; mean fight ticks 899.0; mean firing unit-seconds 134.67 side 0, 138.56 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.09 to 0.31
- counter@8:Raider (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 980.6; mean firing unit-seconds 122.70 side 0, 138.18 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.13 to 0.40
- line@32:Raider, default: 32 units beat 28, lose to 29; mean fight ticks 1480.8; mean firing unit-seconds 560.69 side 0, 491.71 side 1; stalled fights 144 (quiet stalemates only); caps 0; draws 0 | pair spread 0.24 to 0.40
- blob@32:Raider, default: 32 units beat 31, lose to 32; mean fight ticks 1378.0; mean firing unit-seconds 545.17 side 0, 548.35 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.04 to 0.22
- concave@32:Raider (unconfirmed draft), default: 32 units beat 33, lose to 34; mean fight ticks 1323.0; mean firing unit-seconds 595.76 side 0, 525.35 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.06 to 0.28
- counter@32:Raider (unconfirmed draft), default: 32 units beat 24, lose to 25; mean fight ticks 2075.6; mean firing unit-seconds 542.79 side 0, 551.01 side 1; stalled fights 15 (quiet stalemates only); caps 0; draws 0 | pair spread 0.17 to 0.49

## Vanguard against Raider

- line@16: Vanguard 16 units beat 16; Raider 16 units beat 17; Raider larger
- blob@16: Vanguard 16 units beat 14; Raider 16 units beat 15; Raider larger
- concave@16: Vanguard 16 units beat 14; Raider 16 units beat 16; Raider larger
- counter@16: Vanguard 16 units beat 11; Raider 16 units beat 14; Raider larger
- line@8: Vanguard 8 units beat 8; Raider 8 units beat 8; same
- blob@8: Vanguard 8 units beat 7; Raider 8 units beat 7; same
- concave@8: Vanguard 8 units beat 8; Raider 8 units beat 8; same
- counter@8: Vanguard 8 units beat 7; Raider 8 units beat 7; same
- line@32: Vanguard 32 units beat 37; Raider 32 units beat 28; Raider smaller
- blob@32: Vanguard 32 units beat 28; Raider 32 units beat 31; Raider larger
- concave@32: Vanguard 32 units beat 31; Raider 32 units beat 33; Raider larger
- counter@32: Vanguard 32 units beat 20; Raider 32 units beat 24; Raider larger

## What the instrument could not express

- skills S1, S3, S4, S5 have no formation play
- concave curves around the middle of the enemy's front (the draft's default focus), not the enemy's first anchor or a tracked arrival point

## Files

- formation.csv
- formation_run.md
- formation_page.html
- summary.json
