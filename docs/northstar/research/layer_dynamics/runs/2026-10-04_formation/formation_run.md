# Skill lab formation batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

Lab rule, provisional: mop-up order. A side whose units have stopped, none with an enemy in attack range, that sees an enemy, re-issues its attack-move at the centroid of the enemies it sees, at most once per mopup_interval_ticks. Setting: mopup=True, mopup_interval_ticks=200. Each fight's count is the mopup_orders column.

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

- line@16, default: 16 units beat 11, lose to 12; mean fight ticks 3344.1; mean firing unit-seconds 1088.96 side 0, 846.18 side 1; stalled fights 5 (quiet stalemates only); caps 11; draws 0 | pair spread 0.51 to 0.71
- blob@16, default: 16 units beat 10, lose to 11; mean fight ticks 3257.3; mean firing unit-seconds 955.63 side 0, 837.45 side 1; stalled fights 13 (quiet stalemates only); caps 29; draws 0 | pair spread 0.60 to 0.72
- concave@16 (unconfirmed draft), default: 16 units beat 12, lose to 13; mean fight ticks 3372.2; mean firing unit-seconds 1063.86 side 0, 870.44 side 1; stalled fights 1 (quiet stalemates only); caps 26; draws 0 | pair spread 0.50 to 0.64
- counter@16 (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 4136.0; mean firing unit-seconds 877.76 side 0, 880.50 side 1; stalled fights 11 (quiet stalemates only); caps 108; draws 0 | pair spread 0.44 to 0.64
- line@8, default: 8 units beat 5, lose to 6; mean fight ticks 2786.3; mean firing unit-seconds 504.20 side 0, 500.80 side 1; stalled fights 2 (quiet stalemates only); caps 0; draws 0 | pair spread 0.57 to 0.68
- blob@8, default: 8 units beat 5, lose to 6; mean fight ticks 2617.5; mean firing unit-seconds 466.13 side 0, 415.02 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread 0.52 to 0.70
- concave@8 (unconfirmed draft), default: 8 units beat 5, lose to 6; mean fight ticks 2874.2; mean firing unit-seconds 463.65 side 0, 408.31 side 1; stalled fights 4 (quiet stalemates only); caps 1; draws 0 | pair spread 0.50 to 0.71
- counter@8 (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 3095.8; mean firing unit-seconds 450.32 side 0, 506.40 side 1; stalled fights 2 (quiet stalemates only); caps 3; draws 0 | pair spread -0.09 to 0.31
- line@32, default: 32 units beat 30, lose to 31; mean fight ticks 3969.7; mean firing unit-seconds 2414.35 side 0, 1428.59 side 1; stalled fights 163 (quiet stalemates only); caps 11; draws 0 | pair spread 0.43 to 0.61
- blob@32, default: 32 units beat 22, lose to 23; mean fight ticks 3398.6; mean firing unit-seconds 1822.16 side 0, 1686.92 side 1; stalled fights 24 (quiet stalemates only); caps 31; draws 0 | pair spread 0.51 to 0.66
- concave@32 (unconfirmed draft), default: 32 units beat 25, lose to 26; mean fight ticks 3361.6; mean firing unit-seconds 2091.66 side 0, 1531.36 side 1; stalled fights 14 (quiet stalemates only); caps 18; draws 0 | pair spread 0.44 to 0.66
- counter@32 (unconfirmed draft), default: no break-even in range; mean fight ticks 5853.7; mean firing unit-seconds 1532.64 side 0, 1724.46 side 1; stalled fights 142 (quiet stalemates only); caps 187; draws 0
- line@16:Raider, default: 16 units beat 16, lose to 17; mean fight ticks 1083.1; mean firing unit-seconds 314.74 side 0, 274.90 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 2 | pair spread 0.09 to 0.33
- blob@16:Raider, default: 16 units beat 15, lose to 16; mean fight ticks 1266.4; mean firing unit-seconds 278.65 side 0, 274.09 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread -0.15 to 0.27
- concave@16:Raider (unconfirmed draft), default: 16 units beat 14, lose to 15; mean fight ticks 1113.9; mean firing unit-seconds 286.20 side 0, 253.16 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread 0.22 to 0.42
- counter@16:Raider (unconfirmed draft), default: 16 units beat 13, lose to 14; mean fight ticks 1420.0; mean firing unit-seconds 251.78 side 0, 277.17 side 1; stalled fights 2 (quiet stalemates only); caps 0; draws 0 | pair spread 0.10 to 0.46
- line@8:Raider, default: 8 units beat 8, lose to 9; mean fight ticks 878.9; mean firing unit-seconds 141.51 side 0, 136.47 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.03 to 0.30
- blob@8:Raider, default: 8 units beat 7, lose to 8; mean fight ticks 875.5; mean firing unit-seconds 131.48 side 0, 132.62 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread 0.06 to 0.40
- concave@8:Raider (unconfirmed draft), default: 8 units beat 4, lose to 5; mean fight ticks 822.2; mean firing unit-seconds 121.85 side 0, 105.93 side 1; stalled fights 1 (quiet stalemates only); caps 0; draws 0 | pair spread 0.69 to 0.80
- counter@8:Raider (unconfirmed draft), default: 8 units beat 7, lose to 8; mean fight ticks 980.3; mean firing unit-seconds 122.92 side 0, 138.10 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.16 to 0.37
- line@32:Raider, default: 32 units beat 22, lose to 23; mean fight ticks 1285.5; mean firing unit-seconds 496.59 side 0, 397.02 side 1; stalled fights 469 (quiet stalemates only); caps 0; draws 0 | pair spread 0.57 to 0.64
- blob@32:Raider, default: 32 units beat 18, lose to 19; mean fight ticks 1100.8; mean firing unit-seconds 485.24 side 0, 442.57 side 1; stalled fights 10 (quiet stalemates only); caps 0; draws 0 | pair spread 0.68 to 0.75
- concave@32:Raider (unconfirmed draft), default: 32 units beat 21, lose to 22; mean fight ticks 1148.4; mean firing unit-seconds 538.45 side 0, 429.45 side 1; stalled fights 12 (quiet stalemates only); caps 0; draws 0 | pair spread 0.63 to 0.69
- counter@32:Raider (unconfirmed draft), default: 32 units beat 22, lose to 23; mean fight ticks 2127.9; mean firing unit-seconds 453.92 side 0, 504.21 side 1; stalled fights 137 (quiet stalemates only); caps 0; draws 0 | pair spread 0.21 to 0.42

## Vanguard against Raider

- line@16: Vanguard 16 units beat 11; Raider 16 units beat 16; Raider larger
- blob@16: Vanguard 16 units beat 10; Raider 16 units beat 15; Raider larger
- concave@16: Vanguard 16 units beat 12; Raider 16 units beat 14; Raider larger
- counter@16: Vanguard 16 units beat 10; Raider 16 units beat 13; Raider larger
- line@8: Vanguard 8 units beat 5; Raider 8 units beat 8; Raider larger
- blob@8: Vanguard 8 units beat 5; Raider 8 units beat 7; Raider larger
- concave@8: Vanguard 8 units beat 5; Raider 8 units beat 4; Raider smaller
- counter@8: Vanguard 8 units beat 7; Raider 8 units beat 7; same
- line@32: Vanguard 32 units beat 30; Raider 32 units beat 22; Raider smaller
- blob@32: Vanguard 32 units beat 22; Raider 32 units beat 18; Raider smaller
- concave@32: Vanguard 32 units beat 25; Raider 32 units beat 21; Raider smaller
- counter@32: Vanguard 32 units: no break-even in range; Raider 32 units beat 22; Raider larger

## What the instrument could not express

- skills S1, S3, S4, S5 have no formation play
- concave curves around the middle of the enemy's front (the draft's default focus), not the enemy's first anchor or a tracked arrival point

## Files

- formation.csv
- formation_run.md
- formation_page.html
