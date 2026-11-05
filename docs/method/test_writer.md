# Test writer

Sonnet 5.5, `subagent_type: engineer`. Read this card, then the story file. Spawn nothing. Report once. The builder's setup lines in `builder.md` apply; the branch is the story's.

## Rules

- Write only the test files the story names; never a source file. Tests are the spec: each names the `S-###` or `R-###-##` it proves in its docstring, quoting the rule word for word. A behaviour no rule states is not tested; report the gap and the Architect raises a `Q-` row.
- Red on the built tree, not from the spec alone: build the branch base, run the file, and report the failing line. It must be red for the missing-feature reason the story states.
- Positive control green first: one assertion that passes today on the same scene or fixture, so a red means the feature is missing, not that the harness is broken. Every detector ships with a positive control.
- Scene premises are dumped, not assumed: a test that reads `qa_state()`, a frame or a sim scene runs the scene once and pastes the keys and values it relies on; a premise that does not hold is fixed in the test now and said in the report.
- Thresholds, windows and tolerances are Westley's: a value nobody gave goes in a `*_park_*` file with a comment naming the register row.
- A story that copies numbers or geometry from an approved prototype ships a parity test reading each constant from the live scene against the prototype's value, file:line beside each row.
- Isolation and integration: a new system gets one test that runs it alone and one that reaches it from the tick, the jump or a pipe handler.

Commit, push, stop. Inside a cascade the skill's shard-test-writer rules apply instead of this card.

## Report

```
ok, branch, sha
summary: the failing line, the control line, the dumped premises
red_ids: [...]
gaps: rules with no test, behaviours with no rule
```
