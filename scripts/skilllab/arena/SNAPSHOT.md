# Fight file additions in the arena package (H-063)

The format is `docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md`; schema name `om-fight-2` unchanged.

- Optional per-frame key `blocked`: a list of unit ids (the `id` of the unit rows) that were blocked at that frame, meaning alive, still (moved no more than 2 wu) for more than 2 s of sim time, with a destination and no target. The runner (`run.py`) writes it on every frame of a fight whose layout has features it gave the engine (`features.py`), and omits it otherwise; a reader treats absent as `[]`. `snapshot.validate` accepts it present or absent.
- The control twin of such a fight (the same layout with `features` emptied) is `<id>-control-s<n>.fight.json` in the runner's `--control-dir`; it carries no `blocked`.
