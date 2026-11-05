# Fight file additions in the arena package (H-063)

The format is `docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md`; schema name `om-fight-2` unchanged.

- Optional per-frame key `blocked`: a list of unit ids (the `id` of the unit rows) that were blocked at that frame, meaning alive, still (moved no more than 2 wu) for more than 2 s of sim time, with a destination and no target. The runner (`run.py`) writes it on every frame of a fight whose layout has features it gave the engine (`features.py`), and omits it otherwise; a reader treats absent as `[]`. `snapshot.validate` accepts it present or absent.
- The control twin of such a fight (the same layout with `features` emptied) is `<id>-control-s<n>.fight.json` in the runner's `--control-dir`; it carries no `blocked`.
- Optional top-level keys on `om-fight-2` (`snapshot.validate` rejects both on `om-fight-1`): `landscape`, a string, the layout's landscape preset name (the runner writes it on every fight; a reader that lacks it builds `small_flat`); `movement_kind`, the int 1, written when the fight's units walk (a layout with features it gave the engine, and the control twin) and omitted when they fly.
- The control twin's layout is written beside its fight as `<id>-control.toml` and `<id>-control.json` in `--control-dir` (the layout with `features` emptied and `movement` "walk"); the control fight's `layout_path` is the TOML, so a replay draws no walls the control walks through.
- `results.md` rows end with the column `blocked`: the count of (frame, unit) pairs in the fight's frames' `blocked` lists, 0 when the fight has none.
