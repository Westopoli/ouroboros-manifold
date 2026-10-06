# Skill lab landscape batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

Lab rule, provisional: mop-up order. A side whose units have stopped, none with an enemy in attack range, that sees an enemy, re-issues its attack-move at the centroid of the enemies it sees, at most once per mopup_interval_ticks. Setting: mopup=True, mopup_interval_ticks=200. Each fight's count is the mopup_orders column.

## Scene

Five sampled maps (open, block, wall, lane, cover field). 16 attackers playing blob or line against 8 to 24 defenders in a blob. The defenders hold the guard order. Each cell also scans naive blob against naive blob on the same map as a reference.

## Cells

| cell | size | enemy range | replicates | fights per cell | status |
|---|---|---|---|---|---|
| open:blob_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| open:line_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| block:blob_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| block:line_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| wall:blob_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| wall:line_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| lane:blob_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| lane:line_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| cover_field:blob_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| cover_field:line_v_defenders | 16 | 8 to 24 | 10 | 20 | naive |
| tall_cover | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| tall_cover_counter | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |

Cells within 2 enemy units of a break-even run 3 times the fights.

## Results

- open:blob_v_defenders, guard: 16 units beat 9, lose to 10; mean fight ticks 2061.2; mean firing unit-seconds 1056.88 side 0, 265.28 side 1; stalled fights 43 (quiet stalemates only); caps 0; draws 0 | pair spread 0.86 to 0.88
- naive against naive on this map: 16 units beat 10, lose to 11
- open:line_v_defenders, guard: no break-even in range; mean fight ticks 3698.1; mean firing unit-seconds 1058.03 side 0, 319.88 side 1; stalled fights 74 (quiet stalemates only); caps 50; draws 0
- naive against naive on this map: 16 units beat 10, lose to 11
- block:blob_v_defenders, guard: 16 units beat 9, lose to 10; mean fight ticks 2061.2; mean firing unit-seconds 1056.88 side 0, 265.28 side 1; stalled fights 43 (quiet stalemates only); caps 0; draws 0 | pair spread 0.86 to 0.88
- naive against naive on this map: 16 units beat 10, lose to 11
- block:line_v_defenders, guard: no break-even in range; mean fight ticks 3698.1; mean firing unit-seconds 1058.03 side 0, 319.88 side 1; stalled fights 74 (quiet stalemates only); caps 50; draws 0
- naive against naive on this map: 16 units beat 10, lose to 11
- wall:blob_v_defenders, guard: 16 units beat 9, lose to 10; mean fight ticks 2061.2; mean firing unit-seconds 1056.88 side 0, 265.28 side 1; stalled fights 43 (quiet stalemates only); caps 0; draws 0 | pair spread 0.86 to 0.88
- naive against naive on this map: 16 units beat 10, lose to 11
- wall:line_v_defenders, guard: no break-even in range; mean fight ticks 3698.1; mean firing unit-seconds 1058.03 side 0, 319.88 side 1; stalled fights 74 (quiet stalemates only); caps 50; draws 0
- naive against naive on this map: 16 units beat 10, lose to 11
- lane:blob_v_defenders, guard: 16 units beat 9, lose to 10; mean fight ticks 2061.2; mean firing unit-seconds 1056.88 side 0, 265.28 side 1; stalled fights 43 (quiet stalemates only); caps 0; draws 0 | pair spread 0.86 to 0.88
- naive against naive on this map: 16 units beat 10, lose to 11
- lane:line_v_defenders, guard: no break-even in range; mean fight ticks 3698.1; mean firing unit-seconds 1058.03 side 0, 319.88 side 1; stalled fights 74 (quiet stalemates only); caps 50; draws 0
- naive against naive on this map: 16 units beat 10, lose to 11
- cover_field:blob_v_defenders, guard: 16 units beat 9, lose to 10; mean fight ticks 2061.2; mean firing unit-seconds 1056.88 side 0, 265.28 side 1; stalled fights 43 (quiet stalemates only); caps 0; draws 0 | pair spread 0.86 to 0.88
- naive against naive on this map: 16 units beat 10, lose to 11
- cover_field:line_v_defenders, guard: no break-even in range; mean fight ticks 3698.1; mean firing unit-seconds 1058.03 side 0, 319.88 side 1; stalled fights 74 (quiet stalemates only); caps 50; draws 0
- naive against naive on this map: 16 units beat 10, lose to 11
- tall_cover (unconfirmed draft), guard: 16 units beat 9, lose to 10; mean fight ticks 2061.2; mean firing unit-seconds 1056.88 side 0, 265.28 side 1; stalled fights 43 (quiet stalemates only); caps 0; draws 0 | pair spread 0.86 to 0.88
- naive against naive on this map: 16 units beat 8, lose to 9
- tall_cover_counter (unconfirmed draft), guard: 16 units beat 9, lose to 10; mean fight ticks 2011.4; mean firing unit-seconds 0.00 side 0, 0.00 side 1; stalled fights 35 (quiet stalemates only); caps 1; draws 0 | pair spread 1.00 to 1.00
- naive against naive on this map: 16 units beat 8, lose to 9

## What the instrument could not express


## Files

- landscape.csv
- landscape_run.md
- landscape_page.html
