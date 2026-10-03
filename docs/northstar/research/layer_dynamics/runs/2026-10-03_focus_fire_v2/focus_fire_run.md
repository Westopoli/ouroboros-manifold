# Skill lab focus fire batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

## Scene

Open map, no terrain. 16 Vanguards on side 0 against 8 to 24 on side 1. Each cell is fought twice: enemy units pick the nearest target, then the most damaged one in reach.

## Cells

| cell | size | enemy range | replicates | fights per cell | status |
|---|---|---|---|---|---|
| identical | 16 | 8 to 24 | 10 | 20 | naive |
| damage | 16 | 8 to 24 | 10 | 20 | naive |
| reach | 16 | 8 to 24 | 10 | 20 | naive |
| S2_skilled | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| S2_counter | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| S1_skilled | 16 | 8 to 24 | 10 | 20 | not expressed |
| S3_skilled | 16 | 8 to 24 | 10 | 20 | not expressed |
| S4_skilled | 16 | 8 to 24 | 10 | 20 | not expressed |
| S5_skilled | 16 | 8 to 24 | 10 | 20 | not expressed |

Cells within 2 enemy units of a break-even run 3 times the fights.

## Results

- identical, nearest: 16 units beat 15, lose to 16; mean fight ticks 2371.4; mean firing unit-seconds 959.06 side 0, 959.32 side 1; stalled fights 0 | pair spread -0.07 to 0.39
- identical, most_damaged: 16 units beat 15, lose to 16; mean fight ticks 2379.7; mean firing unit-seconds 957.14 side 0, 958.88 side 1; stalled fights 0 | pair spread -0.16 to 0.40
- damage, nearest: 16 units beat 17, lose to 18; mean fight ticks 2233.2; mean firing unit-seconds 902.48 side 0, 919.07 side 1; stalled fights 0 | pair spread -0.17 to 0.38
- damage, most_damaged: 16 units beat 17, lose to 18; mean fight ticks 2235.7; mean firing unit-seconds 900.87 side 0, 916.08 side 1; stalled fights 0 | pair spread -0.18 to 0.35
- reach, nearest: 16 units beat 16, lose to 17; mean fight ticks 2237.1; mean firing unit-seconds 1022.91 side 0, 915.25 side 1; stalled fights 0 | pair spread 0.01 to 0.39
- reach, most_damaged: 16 units beat 17, lose to 18; mean fight ticks 2359.6; mean firing unit-seconds 1058.40 side 0, 911.89 side 1; stalled fights 0 | pair spread -0.07 to 0.31
- S2_skilled (unconfirmed draft), nearest: 16 units beat 15, lose to 16; mean fight ticks 2221.3; mean firing unit-seconds 945.73 side 0, 960.79 side 1; stalled fights 0 | pair spread -0.06 to 0.43
- S2_skilled (unconfirmed draft), most_damaged: 16 units beat 15, lose to 16; mean fight ticks 2225.8; mean firing unit-seconds 942.98 side 0, 959.37 side 1; stalled fights 0 | pair spread 0.02 to 0.43
- S2_counter (unconfirmed draft), nearest: 16 units beat 15, lose to 16; mean fight ticks 2354.1; mean firing unit-seconds 892.34 side 0, 990.76 side 1; stalled fights 0 | pair spread -0.23 to 0.30
- S2_counter (unconfirmed draft), most_damaged: 16 units beat 15, lose to 16; mean fight ticks 2361.8; mean firing unit-seconds 894.66 side 0, 989.51 side 1; stalled fights 0 | pair spread -0.25 to 0.29

## What changes

- identical: break-even nearest 15, most_damaged 15, no change
- damage: break-even nearest 17, most_damaged 17, no change
- reach: break-even nearest 16, most_damaged 17, gains
- S2_skilled: break-even nearest 15, most_damaged 15, no change
- S2_counter: break-even nearest 15, most_damaged 15, no change

## What the instrument could not express

- S1
- S3
- S4
- S5
- S1_skilled: no skilled play until defined with Westley (A145)
- S3_skilled: no skilled play until defined with Westley (A145)
- S4_skilled: no skilled play until defined with Westley (A145)
- S5_skilled: no skilled play until defined with Westley (A145)

## Files

- focus_fire.csv
- focus_fire_run.md
- focus_fire_page.html
