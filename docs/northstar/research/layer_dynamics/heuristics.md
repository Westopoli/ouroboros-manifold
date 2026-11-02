# Where the lines cross: Westley's layout heuristics

Core documentation of the simulation lab (Westley, 2026-11-01). Each layout kind carries his expected win rate for the better-positioned side. These are not thresholds the lab enforces; they are blurry locations of where the lines cross between positioning and headcount, and the lab's purpose is to find strategic depth around them.

His words: "Those percentages I listed out are blurry locations of where the lines cross, if a configuration is producing more than a 5-10% difference higher or lower of the specific percentage I listed, that's an indication that the specific configuration being tested does not match where the 'lines cross'. ... the layout paired with the prediction should be a guiding heuristic for where the lines cross, and can be used in tandem with the rules we've already laid out for finding strategic depth (lab's whole purpose)."

How the lab uses them: a layout's measured win rate over its seeds is compared with the heuristic; a difference above DRAFT-rate-band 10 points (his "5-10%") flags the configuration under test (unit values, ranges, speeds, terrain rules) as off the line, never the heuristic. Today's fights are deterministic for a seed; as variables are added, variance appears and the rate becomes meaningful. No position jitter is added by the lab (his 2026-11-01 answer: the variables supply the variance).

| kind | better-positioned side and its shape | expected win rate | his words (2026-11-01) |
|---|---|---|---|
| chokepoint | holder in an arc flush at the exit, range covering the mouth | 98% | "Blue is expected to win 98% of the time." |
| vantage | holder in an arc near the edge of the hill, hill at twice the height on one travel band | 98% | "Blue is expected to win 98% of the time." |
| cover (as drawn in round two) | the side behind the boxes is worse off | attacker 75% | "red is expected to win 75% of the time depending on where units stop" |
| objective | both in arcs; attacker in two groups from two angles surrounding the holder | attacker 80% | "Red would be expected to win 80% of the time." |
| flank route (a subset of trap) | surrounder, two- or three-pronged, equal forces | 95% | "blue is expected to win 95% of the time" |
| slope | holder in an arc on the upper band | 60% | "blue expected to win 60% of the time" |
| city | holder inside the city with arcs on the entry streets, many buildings | 75% | "blue expected to win 75% of the time" |
| trap | the side that led the enemy in, mouth closed from high ground, several attack points | per layout | his definition, 2026-11-01 |
| any surround at half the centre force | surrounder | 75% | "the force doing the surround should still win 75% of the time" |
| open field, equal forces | neither | 50% | control |

General rules that go with the table: a side holding a position stands in an arc that maximises concurrent fire; an arc or a surround raises the holder's probability; every layout follows one of two order rules (both sides attack-move to one spot, or one side holds and the other attack-moves onto its centre of mass); a fight ends on a wipe or on ten seconds with no shot and no movement, a stall is flagged for him. Staging, transit and hazard anchor are not tactical situations and are out of the catalogue. Priority kinds: trap, city, flank, vantage, chokepoint, many ratios each.
