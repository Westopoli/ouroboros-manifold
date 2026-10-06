# Skill lab combinations batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

Lab rule, provisional (v2): a side re-orders when none of its units has an enemy in attack range and it sees at least one enemy; a unit with a destination blocks the re-order only if it moved at least 30 wu in the last 200 ticks; the order sends every unit of the side at the position of the nearest seen enemy to the side's centroid, with no chunk offsets (one group if the side fits inside the 450 wu scatter limit of E-13 R-095-03, otherwise chunks all aimed at that point); considered every mopup_interval_ticks, counted per fight, same for both sides. Setting: mopup=True, mopup_interval_ticks=200. Each fight's count is the mopup_orders column.

## Scene

Open map, no terrain. 16 Vanguards on side 0 apply a subset of the five skills (S1 to S5) against a naive blob of 8 to 24; 32 subsets, then S2's counter play against a line. A subset is played only if every skill in it has a registered skilled play and it holds at most one skill: the slot plays that would merge several skills' plays do not exist yet.

## Cells

| cell | size | enemy range | replicates | fights per cell | status |
|---|---|---|---|---|---|
| combo:none | 16 | 8 to 24 | 10 | 20 | naive |
| combo:S1 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| combo:S3 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S3 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2+S3 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2+S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S3+S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S3+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2+S3 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2+S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S3+S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S3+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2+S3+S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2+S3+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2+S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S3+S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2+S3+S4 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2+S3+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2+S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S3+S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S2+S3+S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| combo:S1+S2+S3+S4+S5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| counter:S2 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |

Cells within 2 enemy units of a break-even run 3 times the fights.

## Results

- combo:none, default: 16 units beat 14, lose to 15; mean fight ticks 3643.9; mean firing unit-seconds 998.82 side 0, 939.50 side 1; stalled fights 0 (quiet stalemates only); caps 49; draws 0 | pair spread 0.08 to 0.43
- combo:S2 (unconfirmed draft), default: 16 units beat 14, lose to 15; mean fight ticks 3368.6; mean firing unit-seconds 1061.53 side 0, 871.45 side 1; stalled fights 0 (quiet stalemates only); caps 22; draws 0 | pair spread 0.27 to 0.46
- counter:S2 (unconfirmed draft), default: 16 units beat 11, lose to 12; mean fight ticks 4250.7; mean firing unit-seconds 893.20 side 0, 922.57 side 1; stalled fights 0 (quiet stalemates only); caps 128; draws 0 | pair spread 0.35 to 0.60

## Profile

One row per subset of the five skills; break-even and advantage in whole units (unconfirmed definition).

| skills | status | break-even | advantage over combo:none |
|---|---|---|---|
| none | naive | 14 | 0 |
| S1 | not expressed | not expressed | not expressed |
| S2 | unconfirmed draft | 14 | 0 |
| S3 | not expressed | not expressed | not expressed |
| S4 | not expressed | not expressed | not expressed |
| S5 | not expressed | not expressed | not expressed |
| S1+S2 | not expressed | not expressed | not expressed |
| S1+S3 | not expressed | not expressed | not expressed |
| S1+S4 | not expressed | not expressed | not expressed |
| S1+S5 | not expressed | not expressed | not expressed |
| S2+S3 | not expressed | not expressed | not expressed |
| S2+S4 | not expressed | not expressed | not expressed |
| S2+S5 | not expressed | not expressed | not expressed |
| S3+S4 | not expressed | not expressed | not expressed |
| S3+S5 | not expressed | not expressed | not expressed |
| S4+S5 | not expressed | not expressed | not expressed |
| S1+S2+S3 | not expressed | not expressed | not expressed |
| S1+S2+S4 | not expressed | not expressed | not expressed |
| S1+S2+S5 | not expressed | not expressed | not expressed |
| S1+S3+S4 | not expressed | not expressed | not expressed |
| S1+S3+S5 | not expressed | not expressed | not expressed |
| S1+S4+S5 | not expressed | not expressed | not expressed |
| S2+S3+S4 | not expressed | not expressed | not expressed |
| S2+S3+S5 | not expressed | not expressed | not expressed |
| S2+S4+S5 | not expressed | not expressed | not expressed |
| S3+S4+S5 | not expressed | not expressed | not expressed |
| S1+S2+S3+S4 | not expressed | not expressed | not expressed |
| S1+S2+S3+S5 | not expressed | not expressed | not expressed |
| S1+S2+S4+S5 | not expressed | not expressed | not expressed |
| S1+S3+S4+S5 | not expressed | not expressed | not expressed |
| S2+S3+S4+S5 | not expressed | not expressed | not expressed |
| S1+S2+S3+S4+S5 | not expressed | not expressed | not expressed |

## What the instrument could not express

- subsets of two or more skills: slot plays that merge several skills' plays do not exist yet
- skills with no registered skilled play (defined with Westley later)
- combo:S1: no skilled play for S1
- combo:S3: no skilled play for S3
- combo:S4: no skilled play for S4
- combo:S5: no skilled play for S5
- combo:S1+S2: no skilled play for S1
- combo:S1+S3: no skilled play for S1, S3
- combo:S1+S4: no skilled play for S1, S4
- combo:S1+S5: no skilled play for S1, S5
- combo:S2+S3: no skilled play for S3
- combo:S2+S4: no skilled play for S4
- combo:S2+S5: no skilled play for S5
- combo:S3+S4: no skilled play for S3, S4
- combo:S3+S5: no skilled play for S3, S5
- combo:S4+S5: no skilled play for S4, S5
- combo:S1+S2+S3: no skilled play for S1, S3
- combo:S1+S2+S4: no skilled play for S1, S4
- combo:S1+S2+S5: no skilled play for S1, S5
- combo:S1+S3+S4: no skilled play for S1, S3, S4
- combo:S1+S3+S5: no skilled play for S1, S3, S5
- combo:S1+S4+S5: no skilled play for S1, S4, S5
- combo:S2+S3+S4: no skilled play for S3, S4
- combo:S2+S3+S5: no skilled play for S3, S5
- combo:S2+S4+S5: no skilled play for S4, S5
- combo:S3+S4+S5: no skilled play for S3, S4, S5
- combo:S1+S2+S3+S4: no skilled play for S1, S3, S4
- combo:S1+S2+S3+S5: no skilled play for S1, S3, S5
- combo:S1+S2+S4+S5: no skilled play for S1, S4, S5
- combo:S1+S3+S4+S5: no skilled play for S1, S3, S4, S5
- combo:S2+S3+S4+S5: no skilled play for S3, S4, S5
- combo:S1+S2+S3+S4+S5: no skilled play for S1, S3, S4, S5

## Files

- combinations.csv
- combinations_run.md
- combinations_page.html
- summary.json
