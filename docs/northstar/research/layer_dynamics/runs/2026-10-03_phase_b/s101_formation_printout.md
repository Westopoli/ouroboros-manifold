Legend: `0-9a-j` = unit index 0..19 (index = 5 x column + row of the start block); `X` = unit 1 and `Y` = unit 4, the two that never end their order; `.` = an empty slot (the slot each unit was told to stand in). Left-right is x (the way they march), up-down is y. One character = 5 wu across, 10 wu down. Units are 30 wu across (collision), so two neighbours in a slot row sit 6 characters apart, 3.5 rows apart.

**Tick 0** (x window -40..180 wu; centre of the group x = 52; slots at x 947.5 to 1052.5); orders ended so far: 0 of 20.
```
    |                                            |
    |                                            |
    |                                            |
    |        0      5      a      f              |
    |                                            |
    |                                            |
    |        X      6      b      g              |
    |                                            |
    |                                            |
    |                                            |
    |        2      7      c      h              |
    |                                            |
    |                                            |
    |        3      8      d      i              |
    |                                            |
    |                                            |
    |                                            |
    |        Y      9      e      j              |
    |                                            |
    |                                            |
    |                                            |
    |                                            |
    |                                            |
```

**Tick 60** (x window 352..572 wu; centre of the group x = 452; slots at x 947.5 to 1052.5); orders ended so far: 0 of 20.
```
    |                           a                |
    |                                            |
    |                       b                    |
    |                                        f   |
    |                                            |
    |                                            |
    |                 6                      g   |
    |                                            |
    |                                            |
    |                                            |
    |                 7                      h   |
    | X                                          |
    |                                            |
    |                       c                i   |
    |2                                           |
    |                                            |
    |                                            |
    |                       d                j   |
    |   8                                        |
    |                                            |
    |       3                   e                |
    |                                            |
    |                                            |
```

**Tick 125** (x window 860..1100 wu; centre of the group x = 916; slots at x 947.5 to 1052.5); orders ended so far: 5 of 20.
```
    |                                                |
    |   5                                            |
    |                                                |
    |                 .    a .      .   f  .         |
    |6                                               |
    |                                                |
    |                b.      .      .   g  .         |
    |                                                |
    |                                                |
    |                                                |
    |                 . c    .      .   h  .         |
    |                                                |
    |                                                |
    |                 . d    .      .   i  .         |
    |   3                                            |
    |                                                |
    |                                                |
    |                 .   e  .      .   j  .         |
    |                                                |
    |                                                |
    |       9                                        |
    |                                                |
    |                                                |
```

**Tick 200** (x window 860..1100 wu; centre of the group x = 984; slots at x 947.5 to 1052.5); orders ended so far: 18 of 20.
```
    |                                                |
    |                     5                          |
    |         X                                      |
    |                 .      .      .   f  .         |
    |              0              a                  |
    |                                                |
    |                 .   6  .      .   g  .         |
    |                                                |
    |                             b                  |
    |             2       7                          |
    |                 .      .      .   h  .         |
    |                              c                 |
    |                                                |
    |             3   .  8   .      .   i  .         |
    |                                                |
    |                             d                  |
    |                                                |
    |                 .      .      .   j  .         |
    |                      9     e                   |
    |                                                |
    |                                                |
    |               Y                                |
    |                                                |
```

**Tick 300** (x window 860..1100 wu; centre of the group x = 984; slots at x 947.5 to 1052.5); orders ended so far: 18 of 20.
```
    |                                                |
    |                     5                          |
    |         X                                      |
    |                 .      .      .   f  .         |
    |              0              a                  |
    |                                                |
    |                 .   6  .      .   g  .         |
    |                                                |
    |                             b                  |
    |             2       7                          |
    |                 .      .      .   h  .         |
    |                              c                 |
    |                                                |
    |             3   .  8   .      .   i  .         |
    |                                                |
    |                             d                  |
    |                                                |
    |                 .      .      .   j  .         |
    |                      9     e                   |
    |                                                |
    |                                                |
    |               Y                                |
    |                                                |
```

**Tick 600** (x window 860..1100 wu; centre of the group x = 984; slots at x 947.5 to 1052.5); orders ended so far: 18 of 20.
```
    |                                                |
    |                     5                          |
    |         X                                      |
    |                 .      .      .   f  .         |
    |              0              a                  |
    |                                                |
    |                 .   6  .      .   g  .         |
    |                                                |
    |                             b                  |
    |             2       7                          |
    |                 .      .      .   h  .         |
    |                              c                 |
    |                                                |
    |             3   .  8   .      .   i  .         |
    |                                                |
    |                             d                  |
    |                                                |
    |                 .      .      .   j  .         |
    |                      9     e                   |
    |             Y                                  |
    |                                                |
    |                                                |
    |                                                |
```

### The two that never end their order, and their neighbours

Slot of unit i: x = 947.5 + 35 x (i div 5), y = 35 x (i mod 5). A unit's order ends when it is within 22.5 wu of its slot (1.5 collision radii), per `csrc/tactical_move.c`.

| unit | slot (x, y) | distance to its slot at tick 125 | 200 | 300 | 600 | position at tick 600 |
|---|---|---|---|---|---|---|
| 1 (X) | (947.5, 35) | 122.6 | 54.3 | 54.1 | 54.1 | (909.8, -3.7) |
| 4 (Y) | (947.5, 140) | 133.9 | 50.2 | 45.1 | 34.9 | (925.6, 167.2) |

Who stands near slot of unit 1 (947.5, 35) at tick 600 (within 30 wu of the slot centre):
- unit 6: 19.5 wu from that slot (its own slot is 15.8 wu from it; order ended tick 140)
- unit 0: 22.8 wu from that slot (its own slot is 21.8 wu from it; order ended tick 147)
- unit 7: 35.2 wu from that slot (its own slot is 16.7 wu from it; order ended tick 147)
- unit 2: 36.5 wu from that slot (its own slot is 22.1 wu from it; order ended tick 199)

Who stands near slot of unit 4 (947.5, 140) at tick 600 (within 30 wu of the slot centre):
- unit 9: 32.2 wu from that slot (its own slot is 20.7 wu from it; order ended tick 137)
- unit 8: 35.4 wu from that slot (its own slot is 19.1 wu from it; order ended tick 178)
- unit 3: 38.1 wu from that slot (its own slot is 20.4 wu from it; order ended tick 133)
- unit 14: 58.3 wu from that slot (its own slot is 21.4 wu from it; order ended tick 140)

Does a straggler move at all after tick 200? Path walked in ticks 200 to 600, and how far apart its tick-200 and tick-600 positions are:

| unit | path walked 200..600 (wu) | net move 200 to 600 (wu) | distance to slot at 200 / 400 / 600 |
|---|---|---|---|
| 1 | 3000 | 0.2 | 54.3 / 54.1 / 54.1 |
| 4 | 3000 | 25.9 | 50.2 / 40.6 / 34.9 |

### Per unit: order-end tick and where it stands

| unit | slot | order ended at tick | distance to slot at its end | distance to slot at tick 600 |
|---|---|---|---|---|
| 0 | (947.5, 0) | 147 | 21.8 | 21.8 |
| 1 | (947.5, 35) | never (700 ticks watched) | - | 54.1 |
| 2 | (947.5, 70) | 199 | 22.1 | 22.1 |
| 3 | (947.5, 105) | 133 | 20.4 | 20.4 |
| 4 | (947.5, 140) | never (700 ticks watched) | - | 34.9 |
| 5 | (982.5, 0) | 138 | 19.8 | 19.8 |
| 6 | (982.5, 35) | 140 | 15.8 | 15.8 |
| 7 | (982.5, 70) | 147 | 16.7 | 16.7 |
| 8 | (982.5, 105) | 178 | 19.1 | 19.1 |
| 9 | (982.5, 140) | 137 | 20.7 | 20.7 |
| 10 | (1017.5, 0) | 135 | 17.2 | 17.2 |
| 11 | (1017.5, 35) | 138 | 20.0 | 20.0 |
| 12 | (1017.5, 70) | 152 | 18.2 | 18.2 |
| 13 | (1017.5, 105) | 134 | 22.4 | 22.4 |
| 14 | (1017.5, 140) | 140 | 21.4 | 21.4 |
| 15 | (1052.5, 0) | 125 | 17.5 | 17.5 |
| 16 | (1052.5, 35) | 125 | 17.5 | 17.5 |
| 17 | (1052.5, 70) | 125 | 17.5 | 17.5 |
| 18 | (1052.5, 105) | 125 | 17.5 | 17.5 |
| 19 | (1052.5, 140) | 125 | 17.5 | 17.5 |

Orders ended: 18 of 20; first at tick 125, last at tick 199 (spread 74 ticks = 3.7 s; the test's window is 40 ticks = 2 s). Five units (15 to 19) end together at tick 125.
Closest any two units ever got over the 700 ticks: 29.1 wu at tick 173. Largest one-tick step of any unit: 9.4 wu.

### What the two stragglers do, step by step (ticks 300 to 311)

Unit 1 (slot at y 35), position then step length: tick 300 (909.8, -3.7), 301 (906.1, 2.8), 302 (902.3, 9.3), 303 (898.6, 15.8), 304 (894.9, 22.3), 305 (891.2, 28.8), 306 (887.5, 35.4), then 307 (891.2, 28.8), 308 (894.9, 22.3) ... back the way it came. Every step is 7.5 wu, the Raider's full speed, in every one of the 400 ticks 200 to 600 (min and max step both 7.50), yet its tick-200 and tick-600 positions differ by 0.2 wu. It paces a line about 30 wu by 50 wu, to the left of its slot, at full speed, without stopping.
Unit 4 (slot at y 140) does the same over a patch of x 918..964, y 154..208, 25.9 wu net drift in 400 ticks of 3000 wu walked.
