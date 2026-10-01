## 2026-09-30: entry

- Command: `sweep var=groups[0].count values=[5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16] metric=win_rate expect=A seeds=0..19`
- Transfer class: T2
- PNG: /Users/westley/ouroboros/toys/layerlab/results/sweep_20260930-205508_groups_0__count_win_rate.png

Scenario diff against base.toml:

```
groups[0].side: None -> 'A'
groups[0].type: None -> 'raider'
groups[0].count: None -> 10
groups[0].formation: None -> 'line'
groups[0].x: None -> 1000.0
groups[0].y: None -> 1000.0
groups[0].facing: None -> 0.0
groups[0].layer: None -> 3
groups[0].order: None -> 'attack_move'
groups[0].goal[0]: None -> 3000.0
groups[0].goal[1]: None -> 1000.0
groups[1].side: None -> 'B'
groups[1].type: None -> 'raider'
groups[1].count: None -> 10
groups[1].formation: None -> 'line'
groups[1].x: None -> 3000.0
groups[1].y: None -> 1000.0
groups[1].facing: None -> 180.0
groups[1].layer: None -> 3
groups[1].order: None -> 'attack_move'
groups[1].goal[0]: None -> 1000.0
groups[1].goal[1]: None -> 1000.0
```

```
sweep groups[0].count  metric=win_rate  expect=A  seeds=0..19 (20)
value               win_rate  stalemates  caps
5                      0.000           0     0
6                      0.000           0     0
7                      0.000           0     0
8                      0.000           0     0
9                      0.000           0     0
10                     0.400           0     0
11                     1.000           0     0
12                     1.000           0     0
13                     1.000           0     0
14                     1.000           0     0
15                     1.000           0     0
16                     1.000           0     0
crossings of 0.5: 10.167
```

## 2026-09-30: entry

- Command: `sweep var=groups[0].count values=[10] metric=win_rate expect=A seeds=0..199`
- Transfer class: T2
- PNG: /Users/westley/ouroboros/toys/layerlab/results/sweep_20260930-205517_groups_0__count_win_rate.png

Scenario diff against base.toml:

```
groups[0].side: None -> 'A'
groups[0].type: None -> 'raider'
groups[0].count: None -> 10
groups[0].formation: None -> 'line'
groups[0].x: None -> 1000.0
groups[0].y: None -> 1000.0
groups[0].facing: None -> 0.0
groups[0].layer: None -> 3
groups[0].order: None -> 'attack_move'
groups[0].goal[0]: None -> 3000.0
groups[0].goal[1]: None -> 1000.0
groups[1].side: None -> 'B'
groups[1].type: None -> 'raider'
groups[1].count: None -> 10
groups[1].formation: None -> 'line'
groups[1].x: None -> 3000.0
groups[1].y: None -> 1000.0
groups[1].facing: None -> 180.0
groups[1].layer: None -> 3
groups[1].order: None -> 'attack_move'
groups[1].goal[0]: None -> 1000.0
groups[1].goal[1]: None -> 1000.0
```

```
sweep groups[0].count  metric=win_rate  expect=A  seeds=0..199 (200)
value               win_rate  stalemates  caps
10                     0.485           0     0
```

## 2026-09-30: entry

- Command: `sweep var=groups[1].count values=[3, 4, 5, 6, 7] metric=win_rate expect=A seeds=0..19`
- Transfer class: T2
- PNG: /Users/westley/ouroboros/toys/layerlab/results/sweep_20260930-205518_groups_1__count_win_rate.png

Scenario diff against base.toml:

```
groups[0].side: None -> 'A'
groups[0].type: None -> 'raider'
groups[0].count: None -> 10
groups[0].formation: None -> 'line'
groups[0].x: None -> 1000.0
groups[0].y: None -> 1000.0
groups[0].facing: None -> 0.0
groups[0].layer: None -> 3
groups[0].order: None -> 'attack_move'
groups[0].goal[0]: None -> 3000.0
groups[0].goal[1]: None -> 1000.0
groups[1].side: None -> 'B'
groups[1].type: None -> 'raider'
groups[1].count: None -> 5
groups[1].formation: None -> 'line'
groups[1].x: None -> 3000.0
groups[1].y: None -> 1000.0
groups[1].facing: None -> 180.0
groups[1].layer: None -> 3
groups[1].order: None -> 'attack_move'
groups[1].goal[0]: None -> 1000.0
groups[1].goal[1]: None -> 1000.0
```

```
sweep groups[1].count  metric=win_rate  expect=A  seeds=0..19 (20)
value               win_rate  stalemates  caps
3                      1.000           0     0
4                      1.000           0     0
5                      1.000           0     0
6                      1.000           0     0
7                      1.000           0     0
```

## 2026-09-30: entry

- Command: `sweep var=rules.vis_factor[5] values=[0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5] metric=win_rate expect=A seeds=0..59`
- Transfer class: T2
- PNG: /tmp/ll_out/sweep_20260930-205943_rules_vis_factor_5_win_rate.png

Scenario diff against base.toml:

```
rules.range_mult[3]: 0.0 -> 1.0
rules.range_mult[5]: 0.0 -> 1.0
rules.dmg_mult[3]: 0.0 -> 1.0
rules.dmg_mult[5]: 0.0 -> 1.0
rules.aoe_layer_mult[3]: 0.0 -> 1.0
rules.aoe_layer_mult[5]: 0.0 -> 1.0
groups[0].side: None -> 'A'
groups[0].type: None -> 'raider'
groups[0].count: None -> 10
groups[0].formation: None -> 'line'
groups[0].x: None -> 1000.0
groups[0].y: None -> 1000.0
groups[0].facing: None -> 0.0
groups[0].layer: None -> 4
groups[0].order: None -> 'attack_move'
groups[0].goal[0]: None -> 3000.0
groups[0].goal[1]: None -> 1000.0
groups[1].side: None -> 'B'
groups[1].type: None -> 'raider'
groups[1].count: None -> 10
groups[1].formation: None -> 'line'
groups[1].x: None -> 3000.0
groups[1].y: None -> 1000.0
groups[1].facing: None -> 180.0
groups[1].layer: None -> 3
groups[1].order: None -> 'attack_move'
groups[1].goal[0]: None -> 1000.0
groups[1].goal[1]: None -> 1000.0
```

```
sweep rules.vis_factor[5]  metric=win_rate  expect=A  seeds=0..59 (60)
value                   win_rate  stalemates  caps
0                          1.000           0     0
0.05                       0.917           0     0
0.1                        0.733           0     0
0.15                       0.767           0     0
0.2                        0.683           0     0
0.25                       0.633           0     0
0.3                        0.417           0     0
0.35                       0.517           0     0
0.4                        0.450           0     0
0.5                        0.467           0     0
crossings of 0.5: 0.281, 0.342, 0.363
```

## 2026-09-30: entry

- Command: `sweep var=rules.vis_factor[5] values=[0, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5] metric=unanswered_A expect=A seeds=0..39`
- Transfer class: T2
- PNG: /tmp/ll_out/sweep_20260930-205944_rules_vis_factor_5_unanswered_A.png

Scenario diff against base.toml:

```
rules.range_mult[3]: 0.0 -> 1.0
rules.range_mult[5]: 0.0 -> 1.0
rules.dmg_mult[3]: 0.0 -> 1.0
rules.dmg_mult[5]: 0.0 -> 1.0
rules.aoe_layer_mult[3]: 0.0 -> 1.0
rules.aoe_layer_mult[5]: 0.0 -> 1.0
groups[0].side: None -> 'A'
groups[0].type: None -> 'raider'
groups[0].count: None -> 10
groups[0].formation: None -> 'line'
groups[0].x: None -> 1000.0
groups[0].y: None -> 1000.0
groups[0].facing: None -> 0.0
groups[0].layer: None -> 4
groups[0].order: None -> 'attack_move'
groups[0].goal[0]: None -> 3000.0
groups[0].goal[1]: None -> 1000.0
groups[1].side: None -> 'B'
groups[1].type: None -> 'raider'
groups[1].count: None -> 10
groups[1].formation: None -> 'line'
groups[1].x: None -> 3000.0
groups[1].y: None -> 1000.0
groups[1].facing: None -> 180.0
groups[1].layer: None -> 3
groups[1].order: None -> 'attack_move'
groups[1].goal[0]: None -> 1000.0
groups[1].goal[1]: None -> 1000.0
```

```
sweep rules.vis_factor[5]  metric=unanswered_A  expect=A  seeds=0..39 (40)
value               unanswered_A  stalemates  caps
0                        197.250           0     0
0.1                      127.675           0     0
0.2                      118.800           0     0
0.25                      53.450           0     0
0.3                       50.000           0     0
0.4                       47.700           0     0
0.5                       41.700           0     0
```

## 2026-09-30: entry

- Command: `sweep var=rules.vis_factor[5] values=[0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5] var2=groups[1].count values2=[10, 12, 14, 16, 18, 20, 24, 28] metric=win_rate expect=A seeds=0..19`
- Transfer class: T2
- PNG: /tmp/ll_out/sweep_20260930-205956_rules_vis_factor_5__x_groups_1__count_win_rate.png

Scenario diff against base.toml:

```
rules.range_mult[3]: 0.0 -> 1.0
rules.range_mult[5]: 0.0 -> 1.0
rules.dmg_mult[3]: 0.0 -> 1.0
rules.dmg_mult[5]: 0.0 -> 1.0
rules.aoe_layer_mult[3]: 0.0 -> 1.0
rules.aoe_layer_mult[5]: 0.0 -> 1.0
groups[0].side: None -> 'A'
groups[0].type: None -> 'raider'
groups[0].count: None -> 10
groups[0].formation: None -> 'line'
groups[0].x: None -> 1000.0
groups[0].y: None -> 1000.0
groups[0].facing: None -> 0.0
groups[0].layer: None -> 4
groups[0].order: None -> 'attack_move'
groups[0].goal[0]: None -> 3000.0
groups[0].goal[1]: None -> 1000.0
groups[1].side: None -> 'B'
groups[1].type: None -> 'raider'
groups[1].count: None -> 10
groups[1].formation: None -> 'line'
groups[1].x: None -> 3000.0
groups[1].y: None -> 1000.0
groups[1].facing: None -> 180.0
groups[1].layer: None -> 3
groups[1].order: None -> 'attack_move'
groups[1].goal[0]: None -> 1000.0
groups[1].goal[1]: None -> 1000.0
```

```
sweep rules.vis_factor[5] x groups[1].count  metric=win_rate  expect=A  seeds=0..19 (20)
rows: rules.vis_factor[5]   columns: groups[1].count   cells: mean win_rate
             10        12        14        16        18        20        24        28
0         1.000     1.000     1.000     1.000     1.000     1.000     1.000     1.000
0.05      0.950     0.100     0.050     0.000     0.000     0.000     0.000     0.000
0.1       0.600     0.000     0.000     0.000     0.000     0.000     0.000     0.000
0.15      0.850     0.000     0.000     0.000     0.000     0.000     0.000     0.000
0.2       0.750     0.000     0.000     0.000     0.000     0.000     0.000     0.000
0.25      0.600     0.000     0.000     0.000     0.000     0.000     0.000     0.000
0.3       0.550     0.000     0.000     0.000     0.000     0.000     0.000     0.000
0.4       0.450     0.000     0.000     0.000     0.000     0.000     0.000     0.000
0.5       0.350     0.000     0.000     0.000     0.000     0.000     0.000     0.000
stalemates 0  caps 0 (all cells)
crossings of 0.5 at groups[1].count=10: 0.350
crossings of 0.5 at groups[1].count=12: 0.028
crossings of 0.5 at groups[1].count=14: 0.026
crossings of 0.5 at groups[1].count=16: 0.025
crossings of 0.5 at groups[1].count=18: 0.025
crossings of 0.5 at groups[1].count=20: 0.025
crossings of 0.5 at groups[1].count=24: 0.025
crossings of 0.5 at groups[1].count=28: 0.025
```

## 2026-09-30: entry

- Command: `sweep var=rules.dmg_mult[5] values=[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] var2=groups[1].count values2=[10, 12, 14, 16, 18, 20, 24, 28] metric=win_rate expect=A seeds=0..19`
- Transfer class: T2
- PNG: /tmp/ll_out/sweep_20260930-210015_rules_dmg_mult_5__x_groups_1__count_win_rate.png

Scenario diff against base.toml:

```
rules.range_mult[3]: 0.0 -> 1.0
rules.range_mult[5]: 0.0 -> 1.0
rules.dmg_mult[3]: 0.0 -> 1.0
rules.dmg_mult[5]: 0.0 -> 1.0
rules.aoe_layer_mult[3]: 0.0 -> 1.0
rules.aoe_layer_mult[5]: 0.0 -> 1.0
groups[0].side: None -> 'A'
groups[0].type: None -> 'raider'
groups[0].count: None -> 10
groups[0].formation: None -> 'line'
groups[0].x: None -> 1000.0
groups[0].y: None -> 1000.0
groups[0].facing: None -> 0.0
groups[0].layer: None -> 4
groups[0].order: None -> 'attack_move'
groups[0].goal[0]: None -> 3000.0
groups[0].goal[1]: None -> 1000.0
groups[1].side: None -> 'B'
groups[1].type: None -> 'raider'
groups[1].count: None -> 10
groups[1].formation: None -> 'line'
groups[1].x: None -> 3000.0
groups[1].y: None -> 1000.0
groups[1].facing: None -> 180.0
groups[1].layer: None -> 3
groups[1].order: None -> 'attack_move'
groups[1].goal[0]: None -> 1000.0
groups[1].goal[1]: None -> 1000.0
```

```
sweep rules.dmg_mult[5] x groups[1].count  metric=win_rate  expect=A  seeds=0..19 (20)
rows: rules.dmg_mult[5]   columns: groups[1].count   cells: mean win_rate
             10        12        14        16        18        20        24        28
0.2       1.000     1.000     1.000     1.000     1.000     1.000     0.250     0.000
0.3       1.000     1.000     1.000     1.000     1.000     0.000     0.000     0.000
0.4       1.000     1.000     1.000     0.900     0.000     0.000     0.000     0.000
0.5       1.000     1.000     1.000     0.000     0.000     0.000     0.000     0.000
0.6       1.000     1.000     0.000     0.000     0.000     0.000     0.000     0.000
0.7       1.000     0.950     0.000     0.000     0.000     0.000     0.000     0.000
0.8       1.000     0.000     0.000     0.000     0.000     0.000     0.000     0.000
0.9       1.000     0.000     0.000     0.000     0.000     0.000     0.000     0.000
1         0.350     0.000     0.000     0.000     0.000     0.000     0.000     0.000
stalemates 0  caps 0 (all cells)
crossings of 0.5 at groups[1].count=10: 0.977
crossings of 0.5 at groups[1].count=12: 0.747
crossings of 0.5 at groups[1].count=14: 0.550
crossings of 0.5 at groups[1].count=16: 0.444
crossings of 0.5 at groups[1].count=18: 0.350
crossings of 0.5 at groups[1].count=20: 0.250
```
