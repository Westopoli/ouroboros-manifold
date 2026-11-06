# Wave 1 assumption-sweep

## Summary
- Total assumptions logged: 22 (leaf-01 13, leaf-03 9).
- Flagged: 3 yellow, none red. No question or proposal files from the leaves; test-writer Q1-Q8 answered in answers/test-writer-answers.md.

## Flagged entries

### [leaf-01 / category 2-ish: simplification of the reference]
- Assumption: "Division pattern ... reference layout_gen.gd not available to me; pure guess" and "the builder builds exactly one of each" (single-instance pieces; one crossing, one height, one prize pair).
- Conflicts with: spec Design step 3 ("division pattern per seed (band, ring, two patches)"): the pattern only weights the district fill; the rest of the layout is one fixed graph shape.
- Damage assessment: low for round A1 (Assault budget is exactly 1/1/1); it limits how different seeds look, which Westley judges on the sheet.
- Patch suggestion: none now; if the sheet reads samey, the next round extends the pieces.

### [leaf-01 / objective offset fixed]
- Assumption: objective distance from the defender's base is a fixed draft, so `dist_b_objective` is identical across seeds.
- Conflicts with: nothing pinned; "different maps" tests pass (10 of 12 differ).
- Patch suggestion: a jitter draft in round A2 if he asks.

### [leaf-03 / label words]
- Assumption: base_home labelled "keep", objective labelled "objective".
- Conflicts with: spec Design ("objective keep beside home B"): the spec's word list reads as the objective being the keep.
- Patch suggestion: label swap in round A1 feedback (home base "town"? objective "keep"); labels are for his eye.

No cross-leaf contradictions (leaf-03 reads JSON only, leaf-01 owns the engine). No fabricated symbols.
