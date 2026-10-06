# Skill lab enemy position batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

Lab rule, provisional (v2): a side re-orders when none of its units has an enemy in attack range and it sees at least one enemy; a unit with a destination blocks the re-order only if it moved at least 30 wu in the last 200 ticks; the order sends every unit of the side at the position of the nearest seen enemy to the side's centroid, with no chunk offsets (one group if the side fits inside the 450 wu scatter limit of E-13 R-095-03, otherwise chunks all aimed at that point); considered every mopup_interval_ticks, counted per fight, same for both sides. Setting: mopup=True, mopup_interval_ticks=200. Each fight's count is the mopup_orders column.

## Scene

Open map, no terrain. 16 Vanguards on side 0 play a position play (bait, ambush or fall back) against a naive blob of 8 to 24; a blob against a blob is the control. The plays are drafts: the turn or spring tick is 100 and the bait share is 0.25, neither confirmed.

## Cells

| cell | size | enemy range | replicates | fights per cell | status |
|---|---|---|---|---|---|
| blob | 16 | 8 to 24 | 10 | 20 | naive |
| bait | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| ambush | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| fall_back | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| bait_hold_fire | 16 | 8 to 24 | 10 | 20 | not expressed |
| ambush_hold_fire | 16 | 8 to 24 | 10 | 20 | not expressed |
| dark_approach | 16 | 8 to 24 | 10 | 20 | not expressed |
| dark_ambush | 16 | 8 to 24 | 10 | 20 | not expressed |

Cells within 2 enemy units of a break-even run 3 times the fights.

## Results

- blob, default: 16 units beat 14, lose to 15; mean fight ticks 3643.9; mean firing unit-seconds 998.82 side 0, 939.50 side 1; stalled fights 0 (quiet stalemates only); caps 49; draws 0 | pair spread 0.08 to 0.43
- bait (unconfirmed draft), default: 16 units beat 9, lose to 10; mean fight ticks 4374.0; mean firing unit-seconds 887.74 side 0, 766.69 side 1; stalled fights 6 (quiet stalemates only); caps 103; draws 0 | pair spread 0.59 to 0.76
- ambush (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 3328.0; mean firing unit-seconds 910.25 side 0, 825.85 side 1; stalled fights 0 (quiet stalemates only); caps 56; draws 0 | pair spread 0.54 to 0.72
- fall_back (unconfirmed draft), default: 16 units beat 12, lose to 13; mean fight ticks 3377.6; mean firing unit-seconds 895.80 side 0, 969.09 side 1; stalled fights 0 (quiet stalemates only); caps 24; draws 0 | pair spread 0.28 to 0.55

## What the instrument could not express

- bait_hold_fire
- ambush_hold_fire
- dark_approach
- dark_ambush
- draft numbers: turn or spring tick 100, bait share 0.25, none confirmed
- bait: the bait is a second group, so the play is not a single group order
- fall_back: the retreat is a later move, so the play is not a single group order
- bait_hold_fire: needs hold-fire, not built
- ambush_hold_fire: needs hold-fire, not built
- dark_approach: going dark, emission per unit, needs Phase C G6
- dark_ambush: going dark, emission per unit, needs Phase C G6

## Files

- enemy_position.csv
- enemy_position_run.md
- enemy_position_page.html
- summary.json
