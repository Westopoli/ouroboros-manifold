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
