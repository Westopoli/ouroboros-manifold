#### open ground, defenders attack-move: 8 defenders (o) against 9 attackers (x), seed 0. Result: side1, margin -0.281, survivors (0, 4) (defenders, attackers), 2137 ticks

Each row is one tick (20 ticks = 1 second). `fire` = has a target in range and the engine says the shot is open. `blocked` = target in range by distance but the engine says a wall is in the way. `walk` = target further than range. `none` = no target yet. Strength = sum of hp left / starting hp, divided by the side's starting head count (1.00 = untouched).

| tick | def fire | def blocked | def walk | def none | def strength | att fire | att blocked | att walk | att none | att strength | defenders west of x=1500 (the wall's west face; in open ground the same line) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 67 | 1 | 0 | 1 | 6 | 1.00 | 1 | 0 | 2 | 6 | 1.00 | 8 |
| 77 | 2 | 0 | 0 | 6 | 0.99 | 1 | 0 | 2 | 6 | 0.99 | 8 |
| 87 | 2 | 0 | 0 | 6 | 0.99 | 1 | 0 | 1 | 7 | 0.99 | 8 |
| 97 | 2 | 0 | 0 | 6 | 0.98 | 3 | 0 | 0 | 6 | 0.98 | 8 |
| 107 | 5 | 0 | 0 | 3 | 0.97 | 5 | 0 | 0 | 4 | 0.97 | 8 |
| 117 | 7 | 0 | 0 | 1 | 0.96 | 5 | 0 | 0 | 4 | 0.97 | 8 |
| 127 | 7 | 0 | 0 | 1 | 0.96 | 6 | 0 | 0 | 3 | 0.96 | 8 |
| 137 | 7 | 0 | 0 | 1 | 0.95 | 8 | 0 | 0 | 1 | 0.96 | 8 |
| 147 | 7 | 0 | 0 | 1 | 0.94 | 6 | 0 | 0 | 3 | 0.95 | 8 |
| 157 | 7 | 0 | 0 | 1 | 0.94 | 9 | 0 | 0 | 0 | 0.95 | 8 |
| 217 | 7 | 0 | 0 | 1 | 0.89 | 9 | 0 | 0 | 0 | 0.91 | 8 |
| 367 | 7 | 0 | 0 | 1 | 0.79 | 7 | 0 | 0 | 2 | 0.83 | 8 |

Picture at tick 127 (`#` wall where there is one, the gap is the blank stretch in the wall column; one character = 12 wu across, 94 wu down; `o` defender, `x` attacker):
```
    |                                                                           |
    |                                                                           |
    |                                                                           |
    |                                                                           |
    |                                                                           |
    |                                                                           |
    |                                                                           |
    | x    x               o                                                    |
    |    xx                o                                                    |
    |  x   x               o  o                                                 |
    |  x                                                                        |
    |                                                                           |
    |                                                                           |
    |                                                                           |
    |                                                                           |
    |                                                                           |
    |                                                                           |
```

#### choke, defenders attack-move: 8 defenders (o) against 9 attackers (x), seed 0. Result: side1, margin -0.283, survivors (0, 6) (defenders, attackers), 1858 ticks

Each row is one tick (20 ticks = 1 second). `fire` = has a target in range and the engine says the shot is open. `blocked` = target in range by distance but the engine says a wall is in the way. `walk` = target further than range. `none` = no target yet. Strength = sum of hp left / starting hp, divided by the side's starting head count (1.00 = untouched).

| tick | def fire | def blocked | def walk | def none | def strength | att fire | att blocked | att walk | att none | att strength | defenders west of x=1500 (the wall's west face; in open ground the same line) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 67 | 1 | 0 | 1 | 6 | 1.00 | 1 | 0 | 2 | 6 | 1.00 | 8 |
| 77 | 1 | 0 | 1 | 6 | 0.99 | 1 | 0 | 2 | 6 | 0.99 | 8 |
| 87 | 2 | 0 | 0 | 6 | 0.99 | 1 | 0 | 1 | 7 | 0.99 | 8 |
| 97 | 2 | 0 | 0 | 6 | 0.98 | 3 | 0 | 0 | 6 | 0.98 | 8 |
| 107 | 4 | 0 | 0 | 4 | 0.97 | 6 | 0 | 0 | 3 | 0.98 | 8 |
| 117 | 7 | 0 | 0 | 1 | 0.96 | 6 | 0 | 0 | 3 | 0.97 | 8 |
| 127 | 7 | 0 | 0 | 1 | 0.96 | 6 | 0 | 0 | 3 | 0.96 | 8 |
| 137 | 7 | 0 | 0 | 1 | 0.95 | 8 | 0 | 0 | 1 | 0.96 | 8 |
| 147 | 7 | 0 | 0 | 1 | 0.94 | 6 | 0 | 0 | 3 | 0.95 | 8 |
| 157 | 7 | 0 | 0 | 1 | 0.94 | 9 | 0 | 0 | 0 | 0.95 | 8 |
| 217 | 7 | 0 | 0 | 1 | 0.89 | 9 | 0 | 0 | 0 | 0.91 | 8 |
| 367 | 7 | 0 | 0 | 1 | 0.79 | 8 | 0 | 0 | 1 | 0.83 | 8 |

Picture at tick 127 (`#` wall where there is one, the gap is the blank stretch in the wall column; one character = 12 wu across, 94 wu down; `o` defender, `x` attacker):
```
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |  x  x                o                                                    |
    |    xx                o                                                    |
    |  x  xx              ooo                                                   |
    |  x                              #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
```

#### choke, defenders idle: 8 defenders (o) against 9 attackers (x), seed 0. Result: side1, margin -0.229, survivors (0, 4) (defenders, attackers), 2500 ticks

Each row is one tick (20 ticks = 1 second). `fire` = has a target in range and the engine says the shot is open. `blocked` = target in range by distance but the engine says a wall is in the way. `walk` = target further than range. `none` = no target yet. Strength = sum of hp left / starting hp, divided by the side's starting head count (1.00 = untouched).

| tick | def fire | def blocked | def walk | def none | def strength | att fire | att blocked | att walk | att none | att strength | defenders west of x=1500 (the wall's west face; in open ground the same line) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 135 | 1 | 0 | 0 | 7 | 1.00 | 1 | 0 | 2 | 6 | 1.00 | 0 |
| 145 | 4 | 0 | 0 | 4 | 0.99 | 1 | 0 | 2 | 6 | 0.99 | 0 |
| 155 | 8 | 0 | 0 | 0 | 0.99 | 0 | 1 | 1 | 7 | 0.99 | 0 |
| 165 | 8 | 0 | 0 | 0 | 0.99 | 2 | 0 | 2 | 5 | 0.98 | 0 |
| 175 | 8 | 0 | 0 | 0 | 0.98 | 1 | 1 | 0 | 7 | 0.98 | 0 |
| 185 | 8 | 0 | 0 | 0 | 0.98 | 3 | 0 | 0 | 6 | 0.97 | 0 |
| 195 | 8 | 0 | 0 | 0 | 0.97 | 1 | 1 | 0 | 7 | 0.97 | 0 |
| 205 | 8 | 0 | 0 | 0 | 0.97 | 5 | 1 | 0 | 3 | 0.96 | 0 |
| 215 | 8 | 0 | 0 | 0 | 0.96 | 4 | 1 | 0 | 4 | 0.95 | 0 |
| 225 | 8 | 0 | 0 | 0 | 0.96 | 5 | 1 | 0 | 3 | 0.95 | 0 |
| 285 | 8 | 0 | 0 | 0 | 0.92 | 7 | 1 | 0 | 1 | 0.91 | 0 |
| 435 | 8 | 0 | 0 | 0 | 0.83 | 6 | 1 | 0 | 2 | 0.83 | 0 |

Picture at tick 195 (`#` wall where there is one, the gap is the blank stretch in the wall column; one character = 12 wu across, 94 wu down; `o` defender, `x` attacker):
```
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                          x    x                 oo                        |
    |                             x  x                oo                        |
    |                           x x x x               oo                        |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
    |                                 #########                                 |
```

