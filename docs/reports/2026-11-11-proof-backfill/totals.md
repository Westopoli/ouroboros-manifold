# Backfill totals (assemble.py)

Counted after the qualification-1 normalisation; `proven` = a test is the proof line. Rows = rules + Invariant bullets.

| epic | rules | invariants | rows | proven | MISSING | MISSING? | unbuilt |
|---|---|---|---|---|---|---|---|
| E-01 | 87 | 7 | 94 | 1 | 67 | 6 | 20 |
| E-02 | 60 | 6 | 66 | 0 | 57 | 0 | 9 |
| E-03 | 31 | 5 | 36 | 0 | 34 | 0 | 2 |
| E-04 | 33 | 6 | 39 | 5 | 30 | 0 | 4 |
| E-05 | 62 | 6 | 68 | 7 | 57 | 0 | 4 |
| E-06 | 46 | 5 | 51 | 0 | 47 | 0 | 4 |
| E-07 | 28 | 5 | 33 | 0 | 32 | 0 | 1 |
| E-08 | 54 | 5 | 59 | 0 | 57 | 0 | 2 |
| E-09 | 40 | 5 | 45 | 0 | 45 | 0 | 0 |
| E-10 | 70 | 8 | 78 | 1 | 52 | 1 | 24 |
| E-11 | 64 | 6 | 70 | 0 | 51 | 2 | 17 |
| E-12 | 31 | 4 | 35 | 1 | 28 | 0 | 6 |
| E-13 | 53 | 5 | 58 | 0 | 46 | 0 | 12 |
| E-14 | 39 | 5 | 44 | 0 | 26 | 0 | 18 |
| E-15 | 41 | 6 | 47 | 0 | 36 | 0 | 11 |
| E-16 | 100 | 6 | 106 | 0 | 59 | 11 | 36 |
| E-17 | 122 | 9 | 131 | 0 | 55 | 11 | 65 |
| E-18 | 50 | 4 | 54 | 0 | 30 | 4 | 20 |
| E-19 | 35 | 5 | 40 | 0 | 24 | 2 | 14 |
| E-20 | 30 | 3 | 33 | 0 | 16 | 2 | 15 |
| E-21 | 30 | 3 | 33 | 0 | 14 | 0 | 19 |
| E-22 | 86 | 8 | 94 | 0 | 17 | 1 | 76 |
| **all** | 1192 | 122 | **1314** | **15** | **880** | **40** | **379** |

Overall: rows 1314, proven 15, MISSING 880, MISSING? 40, unbuilt 379.
Before normalisation 1: proven 28, MISSING 867 (13 proven rows dropped to MISSING).

## MISSING rows by failing set

Population: the 880 rows whose proof is `MISSING` (not `MISSING?`; `MISSING?` rows are counted apart below). A `fails` cell is read as a set of qualification numbers; `5?` is kept apart from `5`; the word `all` is read as {1,2,3,4,5,6}. Rows with an empty candidate cell go to `no candidate at all` and to no other bucket (their fails cell, if any, is not read). The first block below uses the buckets as named in the brief and they overlap on purpose (`only 5?` is inside `only 5 or 5?`; a row failing 3 and 4 is in both involves lines).

| bucket | rows |
|---|---|
| only 5? | 3 |
| only 5 or 5? | 221 |
| only 1 | 27 |
| only 1 and 5/5? | 38 |
| involves 3 | 126 |
| involves 4 | 80 |
| no candidate at all | 158 |
| candidate present but no fails recorded | 0 |

Disjoint partition of the same rows (first match wins, in this order), sums to the population:

| bucket | rows |
|---|---|
| no candidate at all | 158 |
| candidate but no fails recorded | 0 |
| involves 3 or 4 | 183 |
| only 5? | 3 |
| only 5 | 218 |
| only 5 and 5? | 0 |
| only 1 | 27 |
| only 1 and 5/5? | 38 |
| other (no 3, no 4) | 253 |
| sum | 880 (population 880) |

Rows involving both 3 and 4: 23.
`MISSING?` rows: 40; of them with a candidate: 1.

## Sensitivity: does the candidate quote the rule?

99 MISSING rows have a candidate `file::name` that the rule table (quotes_rule) says does NOT quote the rule, yet their fails cell omits `1`. These are not changed; they would also fail qualification 1. By bucket of the fails cell as written: has 3 or 4 38, only 5 or 5? 37, only 5? 2, other 22.
Of them 5 name a .gd test (client form; the table's quotes_rule is a text match on the first 40 characters of the rule, which a .gd header paraphrase can miss). (Detail: assemble_report.md.)
