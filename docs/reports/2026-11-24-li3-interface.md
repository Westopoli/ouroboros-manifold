# LI3 interface: `scripts/skilllab/arena/isolation_arms.py` (2026-11-24)

What LI4 (arms R, F, W, P) and LI5 (table, page) call. Pinned by `tests/skilllab/integration/test_isolation_arms_*.py` (helpers in `isolation_arms_fixtures.py`). The implementer builds to this and reports a test that looks wrong as a `test-defect`, never edits it. Spec: `docs/northstar/plans/lab-isolation-2026-11-24/spec.md` sections 3 (arms M, V), 4, 7, 8. New file only; it calls LI1's `isolation_runner` (resolve, build, `run_one`, `row_key`) and LI2's `isolation_measures` (`measure_fight`, `orders_ended_short`, `first_contact_tick`, `load_fight`) and the lab's `scan.read_cells`; it changes neither, imports no engine and issues no order (the lab's one click per side is the only one).

## How a run reaches the runner

The runner runs a catalogue id of the version's own tree. The arm writes its flat layout into that tree (`<scratch>/tree-<sha>/docs/northstar/research/layer_dynamics/catalogue/L-####.toml`; never the repository) and gives the id to `run_one`; ids are `L-####`, unique per cell, and none is a catalogue layout of any version. `dump_toml` drops the layout's `movement` key, so `layout_toml(layout)` is `dump_toml` plus `movement = "walk"` placed before the first table. The lab has no sight flag in LI1: arm V calls the version's lab itself (`build_version`, same `python -m scripts.skilllab.arena.run` call, cwd the scratch tree) with `--sight on --control-dir <out>/ctl --control sight`; it must still return a row when the lab exits 2 because the sight twin is INVALID (L-0080, L-0083 at `now`: R-097-05; the fight file is written). See also: LI1 `_fight` reads every exit 2 as a layout REJECT.

## Constants (each on a line with `DRAFT-` or `Westley`/`README`)

`OWN_HEADS = 16`, `SCAN_FROM, SCAN_TO = 8, 48` (README 4, his); `SCAN_HEADS = tuple(range(8, 49))` (every headcount, the default; a bisecting default is the implementer's option, not tested); `MIRROR_HEADS = 16`; `V_HEADS` (DRAFT-v-heads, any int >= 8); `DRAFT_SCAN_SEEDS_10` (default seeds); `DRAFT_SPREAD_TICKS` (tuple of ints starting 0, sorted); `DRAFT_HOLDER_STEP_WU` (a holder further than this from its tick-0 place has stepped; must be under 40); `STAGE4_LAYOUTS = ("L-0061", "L-0080", "L-0083", "L-0039")`; `FLAGS = ("defect", "invalid", "orders_ended_short")`.

## Functions

```python
m_layout(own, enemy, swap=False, movement="walk") -> dict   # open_field, small_flat, Vanguard both sides, blocks of 4 columns at pitch 40, A west spawned first, B east; side A has `own` units unless swap (swap == exchanging the arguments); orders both_same_point; no features; movement "walk" (walkers: the stage 3/4 ground, spec 8 ruling 5) or "fly"
v_layout(heads, holder="A") -> dict                          # same ground, equal numbers, orders "hold:A" or "hold:B"; same positions for both holders
layout_toml(layout) -> str;  layout_id_m(own, enemy, swap) -> "L-####";  layout_id_v(heads, holder) -> "L-####"
run_m(name, enemy, scratch_root, *, own=16, swap=False, seed=10, movement="walk", ref=None, repo=None, out_dir=None) -> row
scan_m(name, scratch_root, *, heads=SCAN_HEADS, own=16, seeds=DRAFT_SCAN_SEEDS_10, movement="walk", ref=None, repo=None, out_dir=None, rows_path=None) -> summary   # rows_path: JSONL, a line flushed per fight
run_v_flat(name, scratch_root, *, heads=V_HEADS, holder="A", seed=10, ref=None, repo=None, out_dir=None) -> row
run_v_stage4(name, layout, scratch_root, *, seed=10, ref=None, repo=None, out_dir=None) -> row   # layout in STAGE4_LAYOUTS
stopping_check(doc) -> {orders_ended_short: int | "not measured: ...", units: [LI2 rows], died_short: [LI2 rows], blocks: bool | None}
blocks_of(doc, arm) -> bool        # True only for arm "M" with orders_ended_short > 0
flags_of(doc) -> sorted list of names from FLAGS   # defect (draw/cap/stall), invalid (the lab's flag), orders_ended_short
vision_report(doc, version_name) -> {sensor, notice, first_seen, holder, standoff_count, first_shot_tick}
part_word_m(points) -> "pass" | "fail" | "no stated direction"; part_word_v(winner, expected) -> same words
```
CLI: `python -m scripts.skilllab.arena.isolation_arms --arm M --version then|now|fix [--ref R] [--heads 8,16] [--seeds 10] --scratch DIR --rows FILE [--repo P] [--out DIR]`; writes the fight rows of the scan; exit 1 when any row is an error row.

A cell is both spawn orders (swap False then True) over the seeds, in that order. `swap` exchanges which force is side A (always west, spawned first); `own_side` is "A" or "B". Won only when every fight of the cell is `side0` (own); a draw or cap marks the cell `defect`. Seeds do not change these fights (seed 10 and 11 gave identical files at `now` and `then`).

## Rows (JSON; `json.loads(json.dumps(x, sort_keys=True)) == x`; spread keys are strings)

M fight row = runner row (LI1 keys) + `own, enemy, swap, own_side, outcome (side0 | side1 | draw | cap, own's view), own_margin (own survivors minus enemy's), movement, measures (= `measure_fight(doc, spread_ticks=DRAFT_SPREAD_TICKS)`), stopping, flags, blocks`.
M point = `own_heads, enemy_heads, won, defect, outcomes, mean_margin, fights, layouts, orders_ended_short (sum), idle_behind, idle_front (sums), max_overlap_pairs (max), first_contact_ticks`.
M summary = `arm "M", version, lab_sha, own, heads, seeds, movement, spread_ticks, points (increasing enemy_heads), beats, loses_to, ceiling_hit, multi_flip (= `scan.read_cells` over the points), flips [{before, after, direction}], part_word (C0 direction read in every non-defect cell where numbers differ: the larger force wins both orders), blocks (any row), mirror (the point at enemy == own, or None), rows`.
V row = runner row + `kind ("flat" | "stage4"), heads, holder (A | B | None), sight (the file's), expected_winner (approved.toml stage 4 row; None on flat ground), part_word, measures, vision, twin, flags, blocks (always False)`. `twin` = `{sight "off", result (runner form), fight_path, fight_sha256, invalid}` from the lab's `--control sight`, or `"not measured at <version>"` where the lab has none (`then`).
`vision`: `sensor` {role: sights}, `notice` {role: range x (1 + `invariants.NOTICE_MARGIN`)}, `first_seen` (`result.first_seen`) as in the file, each `"not measured at <version>"` when the file has no `sights`; `holder` {side, stepped, fired, returned} when orders are hold_and_attack, else `"not measured: ..."`; `standoff_count` (alive-at-end ordered units short of the point with both sides alive, else 0); `first_shot_tick` (LI2).
A flag is a name, never a pass mark; no key is `pass`, `verdict`, `ok`, `threshold`. Only `blocks` of arm M (the stopping check) blocks a landing.

## Open for the chat (nobody decided; the tests do not pin these)

- Spec 3 M also names "the control twin of each stage 3 layout with its features emptied" as M's ground. Not in the LI3 brief and its roles are not Vanguard: not built, not tested.
- Walkers are the default (spec 8 ruling 5: the fix steers flyers; walkers are what the stage 3/4 layouts use). The flyer variant is `movement="fly"`: its place in the page is LI5's.
- "L-0039 sight twin" read as the stage 4 row L-0039 with its `--control sight` twin, like the other three.
- A defect cell (draw, cap, stall) gives V `part_word` "fail" or "no stated direction": not pinned; `reading` has no word for it.
- `then` on L-0061 with sight on is a STALL (24 v 24 alive at tick 460): a found defect, flagged, not blocking.
- Real fights at `now` carry orders ended short (24 v 16 walkers: 3 and 1 units in the probe of 2026-11-24): that is the finding that blocks; the tests assert the check, not its count.
- Mirror break-even tolerance is Westley's (Q-156-02, open): `test_isolation_arms_park_c0_tolerance.py` is skipped.
- LI1's `_fight` maps every lab exit 2 to a layout REJECT, including an INVALID fight (see above): a test-defect or an LI1 follow-up, the chat's call.
