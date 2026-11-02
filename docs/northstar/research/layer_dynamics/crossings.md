# Lines-crossing log: why each fight goes the way it does (Westley's reasoning, per picture)

Purpose (Westley 2026-11-02): for every fight picture he looks at he says what he thinks happened and why the winner is the winner, and whether the lines should be crossing in that situation. Those words are the measurable insight that (a) tells us whether the engine behaves as intended and (b) defines, picture by picture, where positioning, headcount and matchup cross, on top of the measures already hashed out (`heuristics.md`: his percentages per kind; `docs/northstar/plans/2026-10-27-lab-plan-of-record.md` section 1: where the skilled smaller force wins; the stage 6 scan). This file is where they are kept; a records clerk adds the row the day he speaks, in his words, never paraphrased.

Where the other crossing measures live:
- `docs/northstar/research/layer_dynamics/heuristics.md`: his expected win rate per layout kind (98% chokepoint and vantage, 95% flank, 80% objective, 75% cover as drawn, city and half-strength surround, 60% slope, 50% control). Read as blurry locations of the crossing, not results, and not scored per fight.
- `docs/northstar/research/layer_dynamics/heuristics_source_2026-11-01.md`: the verbatim prompts they came from and the 2026-11-02 correction.
- `docs/northstar/research/layer_dynamics/catalogue/verdicts.md`: his verdict per catalogue layout, in his words (rows L-0037 and after carry the percentages).
- `docs/stories/H-025.md` "Round three": the same rules as build instructions.
- `docs/northstar/story_reviews/westley/decisions.md`: DEC-lab-arcs-and-win-rates-2026-11-01, DEC-lab-heuristics-2026-11-01 (and DEC-stage1-seen, DEC-stage2-replay-readability for the staircase).
- `docs/northstar/plans/2026-10-31-lab-staircase.md` stage 6 "where positioning stops deciding (the scan)": the stage that measures the crossing.

Columns: **fight** the layout and seed; **what happened** the engine's result (measured, from the rate file); **his reason** why that side wins, in his words; **crossing here?** his yes/no/not-yet on whether the lines should cross in this situation; **measure** the number or rule that follows (filled with him, DRAFT until he rules).

| fight | what happened | his reason | crossing here? | measure |
|---|---|---|---|---|
| L-0101 (SIT-0101): 12 Bombard in an arc vs 32 Raider rush | B wins, 32 of 32 left, tick 499 | "it's obvious that the 32 raiders would win, strike is meant to fight against siege, and there are more of them, they'll win every time" (2026-11-02) | no: a plain win, not a crossing | Strike versus Siege 1.5 per hit, headcount 2.7 to 1 |
| L-0102 (SIT-0102): 16 Bastion wall vs 32 Vanguard | B wins, 7 left, tick 6080 | (his) | (his) | (his) |
| L-0103 (SIT-0103): mirrored mixed sides, 4 of each role | B wins, 8 left, tick 2740; flagged: an exact mirror should not favour a side | (his) | (his) | (his) |
| L-0104 (SIT-0104): 16 Warden + 16 Interceptor vs 16 Vanguard + 16 Raider | A wins, 24 left, tick 2954 | (his) | (his) | (his) |
| L-0105 (SIT-0105): 3-ring arc (24) vs 24 Vanguard | A wins, 23 left, tick 1060 | (his) | (his) | (his) |
| L-0106 (SIT-0106): the same arc vs 48 Vanguard | A wins, 11 left, tick 2315 | (his) | (his) | (his) |
| L-0107 (SIT-0107): 12 Vanguard arc vs 24 Vanguard | B wins, 22 left, tick 1502 | (his) | (his) | (his) |
| L-0108 (SIT-0108): 16 vs 16 Vanguard control | mutual wipe in all 20 seeds, tick 4658 | (his) | (his) | (his) |

Engine: H-057 at 3d371e7a, not landed, pre-scale-lock, no jitter (every seed of a layout ends the same).
