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
- block:blob_v_defenders, guard: 16 units beat 14, lose to 15; mean fight ticks 2501.7; mean firing unit-seconds 1050.26 side 0, 1068.65 side 1; stalled fights 151 (quiet stalemates only); caps 15; draws 0 | pair spread 0.29 to 0.72
- naive against naive on this map: no break-even in range
- block:line_v_defenders, guard: 16 units beat 14, lose to 15; mean fight ticks 3049.1; mean firing unit-seconds 1141.58 side 0, 1115.17 side 1; stalled fights 23 (quiet stalemates only); caps 22; draws 0 | pair spread 0.34 to 0.77
- naive against naive on this map: no break-even in range
- wall:blob_v_defenders, guard: 16 units beat 12, lose to 13; mean fight ticks 3318.6; mean firing unit-seconds 1043.10 side 0, 540.99 side 1; stalled fights 10 (quiet stalemates only); caps 70; draws 0 | pair spread 0.55 to 0.69
- naive against naive on this map: 16 units beat 9, lose to 10
- wall:line_v_defenders, guard: 16 units beat 13, lose to 14; mean fight ticks 4335.8; mean firing unit-seconds 1093.44 side 0, 683.57 side 1; stalled fights 1 (quiet stalemates only); caps 159; draws 0 | pair spread 0.47 to 0.60
- naive against naive on this map: 16 units beat 9, lose to 10
- lane:blob_v_defenders, guard: 16 units beat 17, lose to 18; mean fight ticks 4488.6; mean firing unit-seconds 1345.69 side 0, 844.18 side 1; stalled fights 0 (quiet stalemates only); caps 132; draws 0 | pair spread 0.27 to 0.41
- naive against naive on this map: 16 units beat 14, lose to 15
- lane:line_v_defenders, guard: 16 units beat 10, lose to 11; mean fight ticks 3659.9; mean firing unit-seconds 842.28 side 0, 833.54 side 1; stalled fights 164 (quiet stalemates only); caps 43; draws 0 | pair spread 0.27 to 0.66
- naive against naive on this map: 16 units beat 14, lose to 15
- cover_field:blob_v_defenders, guard: 16 units beat 17, lose to 18; mean fight ticks 2802.5; mean firing unit-seconds 1303.22 side 0, 436.72 side 1; stalled fights 2 (quiet stalemates only); caps 17; draws 0 | pair spread 0.58 to 0.68
- naive against naive on this map: 16 units beat 9, lose to 10
- cover_field:line_v_defenders, guard: 16 units beat 12, lose to 13; mean fight ticks 4072.3; mean firing unit-seconds 1074.34 side 0, 446.76 side 1; stalled fights 0 (quiet stalemates only); caps 118; draws 0 | pair spread 0.61 to 0.81
- naive against naive on this map: 16 units beat 9, lose to 10
- tall_cover, guard: 16 units beat 17, lose to 18; mean fight ticks 2504.6; mean firing unit-seconds 1307.65 side 0, 349.83 side 1; stalled fights 1 (quiet stalemates only); caps 4; draws 0 | pair spread 0.66 to 0.73
- naive against naive on this map: 16 units beat 9, lose to 10
- tall_cover_counter, guard: no break-even in range; mean fight ticks 2193.2; mean firing unit-seconds 0.00 side 0, 0.00 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0
- naive against naive on this map: 16 units beat 9, lose to 10

## What the instrument could not express


## Files

- landscape.csv
- landscape_run.md
- landscape_page.html
- summary.json
