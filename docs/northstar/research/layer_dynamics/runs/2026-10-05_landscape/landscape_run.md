# Skill lab landscape batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

Lab rule, provisional (v2): a side re-orders when none of its units has an enemy in attack range and it sees at least one enemy; a unit with a destination blocks the re-order only if it moved at least 30 wu in the last 200 ticks; the order sends every unit of the side at the position of the nearest seen enemy to the side's centroid, with no chunk offsets (one group if the side fits inside the 450 wu scatter limit of E-13 R-095-03, otherwise chunks all aimed at that point); considered every mopup_interval_ticks, counted per fight, same for both sides. Setting: mopup=True, mopup_interval_ticks=200. Each fight's count is the mopup_orders column.

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

- open:blob_v_defenders, guard: 16 units beat 17, lose to 18; mean fight ticks 2504.6; mean firing unit-seconds 1307.65 side 0, 349.83 side 1; stalled fights 1 (quiet stalemates only); caps 4; draws 0 | pair spread 0.66 to 0.73
- naive against naive on this map: 16 units beat 14, lose to 15
- open:line_v_defenders, guard: 16 units beat 14, lose to 15; mean fight ticks 3710.2; mean firing unit-seconds 1174.63 side 0, 335.49 side 1; stalled fights 0 (quiet stalemates only); caps 54; draws 0 | pair spread 0.70 to 0.81
- naive against naive on this map: 16 units beat 14, lose to 15
- block:blob_v_defenders, guard: 16 units beat 17, lose to 18; mean fight ticks 2504.6; mean firing unit-seconds 1307.65 side 0, 349.83 side 1; stalled fights 1 (quiet stalemates only); caps 4; draws 0 | pair spread 0.66 to 0.73
- naive against naive on this map: 16 units beat 14, lose to 15
- block:line_v_defenders, guard: 16 units beat 14, lose to 15; mean fight ticks 3710.2; mean firing unit-seconds 1174.63 side 0, 335.49 side 1; stalled fights 0 (quiet stalemates only); caps 54; draws 0 | pair spread 0.70 to 0.81
- naive against naive on this map: 16 units beat 14, lose to 15
- wall:blob_v_defenders, guard: 16 units beat 17, lose to 18; mean fight ticks 2504.6; mean firing unit-seconds 1307.65 side 0, 349.83 side 1; stalled fights 1 (quiet stalemates only); caps 4; draws 0 | pair spread 0.66 to 0.73
- naive against naive on this map: 16 units beat 14, lose to 15
- wall:line_v_defenders, guard: 16 units beat 14, lose to 15; mean fight ticks 3710.2; mean firing unit-seconds 1174.63 side 0, 335.49 side 1; stalled fights 0 (quiet stalemates only); caps 54; draws 0 | pair spread 0.70 to 0.81
- naive against naive on this map: 16 units beat 14, lose to 15
- lane:blob_v_defenders, guard: 16 units beat 17, lose to 18; mean fight ticks 2504.6; mean firing unit-seconds 1307.65 side 0, 349.83 side 1; stalled fights 1 (quiet stalemates only); caps 4; draws 0 | pair spread 0.66 to 0.73
- naive against naive on this map: 16 units beat 14, lose to 15
- lane:line_v_defenders, guard: 16 units beat 14, lose to 15; mean fight ticks 3710.2; mean firing unit-seconds 1174.63 side 0, 335.49 side 1; stalled fights 0 (quiet stalemates only); caps 54; draws 0 | pair spread 0.70 to 0.81
- naive against naive on this map: 16 units beat 14, lose to 15
- cover_field:blob_v_defenders, guard: 16 units beat 17, lose to 18; mean fight ticks 2504.6; mean firing unit-seconds 1307.65 side 0, 349.83 side 1; stalled fights 1 (quiet stalemates only); caps 4; draws 0 | pair spread 0.66 to 0.73
- naive against naive on this map: 16 units beat 14, lose to 15
- cover_field:line_v_defenders, guard: 16 units beat 14, lose to 15; mean fight ticks 3710.2; mean firing unit-seconds 1174.63 side 0, 335.49 side 1; stalled fights 0 (quiet stalemates only); caps 54; draws 0 | pair spread 0.70 to 0.81
- naive against naive on this map: 16 units beat 14, lose to 15
- tall_cover (unconfirmed draft), guard: 16 units beat 17, lose to 18; mean fight ticks 2504.6; mean firing unit-seconds 1307.65 side 0, 349.83 side 1; stalled fights 1 (quiet stalemates only); caps 4; draws 0 | pair spread 0.66 to 0.73
- naive against naive on this map: 16 units beat 8, lose to 9
- tall_cover_counter (unconfirmed draft), guard: no break-even in range; mean fight ticks 2193.2; mean firing unit-seconds 0.00 side 0, 0.00 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0
- naive against naive on this map: 16 units beat 8, lose to 9

## What the instrument could not express


## Files

- landscape.csv
- landscape_run.md
- landscape_page.html
- summary.json
