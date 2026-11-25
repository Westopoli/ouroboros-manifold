# LI4-FW interface: `scripts/skilllab/arena/isolation_fw.py` (2026-11-24)

Arms F (one factor) and W (whole) of the lab isolation measurement, stage 3, and the comparison row of spec section 5. What LI5 (table and page) calls. Pinned by `tests/skilllab/integration/test_isolation_fw_*.py` (helpers: `isolation_fw_real.py`); the implementer builds to this and reports a test that looks wrong as a `test-defect`, never edits it. Spec: `docs/northstar/plans/lab-isolation-2026-11-24/spec.md` sections 3 to 5, 7. Runs every fight through LI1's lab-per-version (`isolation_runner.build_version`, `resolve_version`, the version's own `scripts.skilllab.arena.run`) and measures it with LI2 (`isolation_measures.measure_fight`). Nothing is gated: a flag is a signal.

## Names

```python
STAGE3_LAYOUTS = ("L-0055", "L-0073", "L-0084", "L-0039")   # chokepoint, city, slope, cover
DRAFT_SEEDS = (10, 1)                                        # DRAFT-seeds: 10 as approved plus 1 (seeds change nothing in lab fights); the first is the headline seed
DRAFT_SAME_OR_CHANGED_RULE = "identical winner over the seeds"   # DRAFT-same-or-changed-rule
ARM_ORDER = ("M", "V", "R", "F", "P", "W")

approved(repo=None) -> {layout: approved.toml stage 3 row}            # expected_winner, predict_rate (side A's), decision
ruling(layout, repo=None) -> {words, date, per_picture, stage_approval: {words, date}}   # ValueError for a layout he never ruled on
neutral_layout(layout: dict) -> dict                                   # arm F's layout, pure
run_arms(versions, scratch_root, rows_path, *, arms=("F","W"), layouts=STAGE3_LAYOUTS, seeds=DRAFT_SEEDS, refs=None, repo=None, out_dir=None) -> list[dict]
cell(rows) -> dict                                                     # rows of one (version, arm, layout, variant) over its seeds
same_or_changed(then: {seed: winner}, now: {seed: winner}) -> {verdict, seeds_flipped, rule}
first_differing_arm(readings: {arm: {version: reading}}) -> str
measured_rate(winners: list, predict_rate) -> {rate_a, predict_rate, band_gap}
comparison_rows(rows, repo=None) -> list[dict]                         # one per layout present, in STAGE3_LAYOUTS order
```

## Arms

- **W**: the layout as authored (`variant` `layout`) and its control twin (`variant` `control`, the lab's `control_twin`: same positions, `features` emptied, walk). Approved expected winner and `predict_rate` from `approved()`.
- **F**: the same two variants of `neutral_layout(authored)`: every unit of both sides `role` Vanguard, `range` 300.0 (Vanguard's), nothing else changed (positions, facing, layer, arc, headcounts, features, orders). The isolation is control versus layout: the feature is the only difference. The neutral layout's `id` differs from the authored one; a row's `layout` field is always the authored id.
- `arms` outside ("F", "W") raise `ValueError` before any run. Fights run at the stage 3 rule set (`--sight off`, the lab's default), one order a side (precondition 7); the twin is made by the version's own `run.control_twin` and written under the built tree so `layout_path` in the fight file is tree-relative (no scratch path in a fight file). The control fight file is named `<layout>-control-s<seed>.fight.json` (the lab's `--control-dir` name).

## Row (one JSON object per line, `json.dumps(sort_keys=True)`; read back equal to the returned rows)

The LI1 row keys (`version, lab_sha, arm, layout, seed, result, margin, units_firing, fight_path, fight_sha256, error`) plus:

| key | value |
|---|---|
| variant | `layout` or `control` |
| invalid | list of distinct rule ids of the fight file's `violations` (`[]` when valid); `not measured at <version>` when that version's tree has no rule checker (`scripts/skilllab/invariants.py` absent: `then`); a valid fight at `now` writes neither `invalid` nor `violations`, so the tree decides, not the file; `null` on error |
| measures | `json.loads(json.dumps(measure_fight(load_fight(fight_path))))`; `null` on error |

Order: versions, then arms, then layouts, then `layout` before `control`, then seeds. `rows_path` is rewritten, one line appended and flushed per run. A run that cannot run (ref that is no commit, layout the lab does not have, build failure) is an error row (LI1's stages), never an exception; its `variant`, `invalid`, `measures` as above.

**An invalid fight is a row.** The lab exits 2 on `INVALID ... R-097-05` and still writes the fight file; LI1's `run_one` turns exit 2 into an error row of stage `layout`, so at `now` L-0055 and L-0084 are error rows through `run_one` today (found writing these tests). The module must not do that: the exit-2-with-a-file case is a result with `invalid` listing the rule; exit 2 with no fight file is still the layout error (REJECT). Where the fix lives (a change in `_fight` of LI1 or a local run) is the implementer's call; LI1's tests bind either way. The lab also rejects (R6) a featureless layout run alone, so the twin is run the way the lab runs it (`--control-dir`, or `control_twin` and `fight` in the tree), not as a layout file.

## Cell (`cell(rows)`; the headline seed is `DRAFT_SEEDS[0]` when present)

Keys: `version, lab_sha, seed, winner, survivors, last_tick, end, defect, winners, winner_counts, invalid, units_firing, predictions, error`. `winner/survivors/last_tick/end/defect` are LI2's `result_of` of the headline seed (so a `cap` is winner `cap`, a stall is `draw`, both `defect` True); `winners` = `[[seed, winner], ...]` in seed order; `winner_counts` = `{winner: n}`; `invalid` as the row's; `units_firing` as LI2's `units_firing` of the measures (`not measured: the fight file has no per-unit fired flag` at `then`; the row's own `units_firing` stays LI1's `not measured at then`); `predictions` = `{count, type, agreement}` of LI2's `predictions` (`not measured: ...` at `then`). An error row gives `not measured: <stage>: <first line of the message>` in `winner` and in every measured cell, `error` the row's, `winners` the same string per seed.

## Comparison row (`comparison_rows`)

| key | value |
|---|---|
| layout, kind | authored id; `situation` of the catalogue file |
| ruling | `ruling(layout)`: `words` verbatim (heuristics.md table; for L-0039 the verdicts.md line), `date` 2026-11-01, `per_picture` (`no per-picture verdict` for L-0055, L-0073, L-0084, which were redrawn and approved only with the stage; his words again for L-0039, which he denied by id), `stage_approval` (`I rule approval on stage 3, we are go to move to stage 4`, 2026-11-05) |
| expected_winner, predict_rate | `approved()` (side A's rate) |
| then, now, fix | W layout cell; `"not run"` for a version with no rows (fix until it lands) |
| control | `{then, now, fix}` W control-twin cells |
| f | `{then, now, fix}`: `{layout: cell, control: cell, same_winner: bool}` (arm F, neutral roles) |
| matches_expected | per version: True / False, `n/a` for a defect cell, `not run` |
| rate | per version: `measured_rate(winners over seeds, predict_rate)`, shown not scored (`not run`) |
| same_or_changed, seeds_flipped, rule | `same_or_changed(then winners, now winners)` (then against now only) |
| arm_readings | `{"W": {version: [winner per seed]}, "F": {version: {"layout": [..], "control": [..]}}}` for the versions run |
| first_differing_arm | `first_differing_arm(arm_readings)` |

`same_or_changed`: `same` when every seed's winner is equal, else `changed` with the number of seeds that differ; seed sets unequal is `ValueError`; a winner that starts `not measured` on either side gives a `verdict` starting `not measured` (two failures are not `same`). `first_differing_arm`: first of M, V, R, F, P, W (any order given) with unequal `then` and `now` readings; `none, the whole differs only at W` when only W differs; `none` when none; `ValueError` for an arm outside ARM_ORDER; the fix column is not read. `measured_rate`: `rate_a` = wins of A over the seeds, `band_gap` = |rate_a - predict_rate| x 100 (the lab's `rate.py`); a cap or draw is not a win.

No scratch path appears in a comparison row; two runs of the same fights from two scratch roots give equal rows.

## Known facts pinned (real runs, 2026-11-24; seed 10 equals seed 1)

`then` 4fa618ce7 / `now` 893a5af7f. Layouts: L-0055 A 21:0 t3394 / A 19:0 t1963; L-0073 A 17:0 t6175 / A 19:0 t2516; L-0084 B 0:6 t2268 / A 18:0 t2097; L-0039 cap 8:8 t12000 / A 2:0 t3081. Twins: L-0055 A 23:0 t2196 / A 19:0 t2188; L-0073 A 22:0 t2156 / A 13:0 t4395; L-0084 **stall 40:56 t820 (silence)** / B 0:27 t1361; L-0039 A 3:0 t2606 / B 0:5 t2352. Same-or-changed by the named rule: L-0055 same, L-0073 same, L-0084 changed (2 seeds), L-0039 changed (2 seeds). The one difference from the walker survey is the then twin of L-0084 (survey B 0:36 t1159): the survey ran the then engine under today's lab, whose twin builder has the L6 layer fix; the then lab does not, so its slope twin stalls (a defect cell). The spec says each version runs its own lab.

## Open for the chat (nobody decided; not tested)

- Same-or-changed: the spec (section 5) says identical winner **count** over the seeds, the brief says identical winner **over the seeds**; tests pin only cases where both agree (lab seeds give one fight).
- A `then` or `now` fight whose twin is a stall or cap is a defect cell by spec 4; the row carries it, nothing is dropped.
- Seed 1 repeats seed 10 in every lab fight, so 2 seeds cost double and add nothing today; the constant stays DRAFT.
- `rate_a` over two seeds is 0, 0.5 or 1; `rate.py`'s 20 seeds are not run (DRAFT-seeds-20).
- The `fix` column and arms R, M, V, P are other pieces.
