# Rulebook: when a test may change

Builders never edit tests. A test changes only under this procedure, by a clerk, in a commit carrying the trailer `Test-defect: <why> (<ruler>)`. Thresholds, windows, tolerances and pass marks are Westley's: narrowing an invariant's scope is allowed; widening a threshold, extending a window or loosening a tolerance needs his word. A real finding is never reclassified as a skip.

## Decision procedure

A test is a defect only if all five hold:

1. The failing assertion pins a literal, a key list or a scene parameter that the story file or the bible has since changed (a renamed key, a moved scene path, a constant the spec now gives a new value), or matches the same pattern as a row below.
2. The story file or the bible names the replacing line, and the clerk quotes it with file:line.
3. The edit changes only the pinned literal, key list or scene parameter.
4. No threshold, window or tolerance moves, and no positive control is weakened.
5. The file is not a fenced invariant: the `qa_state()` key contract, the blank-frame detector, the determinism traces, the save-format pins.

Then: edit the one file, run the touched test alone and its control, commit with the trailer on the story branch, report `ruled: true` with the sha. Otherwise `ruled: false` and a brief under a page for the Architect: the test id and failing line, the builder's claim, the story and bible lines that bear on it, two or three options with what each changes.

## Patterns

| Pattern | Rule |
|---|---|
| A frozen fixture or golden trace moves because a `contract` story changed the format | re-pin once, old and new values in the trailer |
| A determinism golden moves for a `sim` story | never a defect: the story changed the sim; the story file must say so or the builder is wrong |
| A key renamed or a scene moved by the story | re-pin the name or path only |
| A count pinned to the sim (system count, region count) | keep; a change is the Architect's |
| A regex pinned to a HUD text the story renames | re-pin to the story's example only |
| A test asserting a feature the story removes | only with a parity test green on the replacement first (no deletion without parity) |
| A pixel or frame threshold | Westley's; park in a `*_park_*` file, never edit |
| A play red because a premise changed (economy zero, no units, clock stopped) | fix the premise in the play, say so |

## Known red

A test red for a ruled reason is listed in `scripts/specfactory/gd_tests_known_red.txt` or `lane_plays_known_red.txt` with the commit that ruled it (`<test id> :: <sha>`), so unrelated landings are not rejected on it; the entry leaves when the fix lands. A test is never listed without a ruling commit.
