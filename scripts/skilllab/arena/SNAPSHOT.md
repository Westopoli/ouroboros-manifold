# Fight file additions in the arena package (H-063, H-088)

The format is `docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md`; schema name `om-fight-2` unchanged.

- Optional per-frame key `blocked`: a list of unit ids (the `id` of the unit rows) that were blocked at that frame, meaning alive, still (moved no more than 2 wu) for more than 2 s of sim time, with a destination and no target. The runner (`run.py`) writes it on every frame of a fight whose layout has features it gave the engine (`features.py`), and omits it otherwise; a reader treats absent as `[]`. `snapshot.validate` accepts it present or absent.
- The control twin of such a fight (the same layout with `features` emptied) is `<id>-control-s<n>.fight.json` in the runner's `--control-dir`; it carries no `blocked`.
- Optional top-level keys on `om-fight-2` (`snapshot.validate` rejects both on `om-fight-1`): `landscape`, a string, the layout's landscape preset name (the runner writes it on every fight; a reader that lacks it builds `small_flat`); `movement_kind`, the int 1, written when the fight's units walk (a layout with features it gave the engine, and the control twin) and omitted when they fly.
- The control twin's layout is written beside its fight as `<id>-control.toml` and `<id>-control.json` in `--control-dir` (the layout with `features` emptied and `movement` "walk"); the control fight's `layout_path` is the TOML, so a replay draws no walls the control walks through.
- `results.md` rows end with the column `blocked`: the count of (frame, unit) pairs in the fight's frames' `blocked` lists, 0 when the fight has none.

## Stage 4, sight (H-088)

`run.py --sight on` runs the stage 4 rule set: targeting by sight on, ground era, every role walking on a canvas, reach 0 up 1 down for every role, the holder of a `hold:A` / `hold:B` layout on guard (R-096-08). It writes four more optional keys on `om-fight-2` (`snapshot.validate` rejects each on `om-fight-1`, accepts each absent or present); a fight run with `--sight off`, and every sight-off control, carries none of them. A reader treats absent as "not recorded".

- Per-unit key `seen` (on every unit row of every frame): a sorted list of the unit ids of the living enemies this unit sees (`engine.can_see`); `[]` for a dead unit.
- Top-level `sights`: `{role: sensor radius}` in wu, one key per role in the fight, non-negative numbers (as `ranges` does for weapon range).
- `result.first_seen`: `{"A": tick | null, "B": tick | null}`, the first sampled tick at which that side's living units see any living enemy (`engine.seen_by_sight`), sampled every `CHECK_EVERY` ticks (one sim second) from tick 0; `null` when the side never sees one. It is a sample tick, not a frame tick.
- `orders.guard`: a bool, `true` when the holder of the `hold:` layout was ordered to guard, `false` for `both_same_point`. The control of a sight-on fight carries it as applied.
- `movement_kind` is 1 on every `--sight on` fight, since every role walks.
- The sight-off control: `--sight on --control sight --control-dir D` writes `D/<id>-control-s<n>.fight.json` for every layout, whether or not it has features: the same layout and seed under the stage 4 rule set with targeting by sight switched off, so it differs from the main fight by sight only. Its document has `sight` `"off"`, `movement_kind` 1, `orders.guard` as applied, and none of `seen`, `sights`, `first_seen`; its `layout_path` is the original layout, and no twin layout files are written. `--control sight` with `--sight off` is a usage error (exit 2); `--control ground` (the default, the H-063 twin) is allowed with either sight.
- `results.md` with `--sight on` ends with two more columns, `first seen A` and `first seen B` (a tick, or `-`); with `--sight off` the columns are the stage 3 ones.
