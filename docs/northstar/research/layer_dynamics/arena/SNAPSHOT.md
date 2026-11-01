# Arena fight file (`om-fight-1`)

What the Godot replay scene, the page and any other reader open. They read the JSON; they never import `scripts/skilllab/arena/snapshot.py`. Contract story: `docs/stories/H-039.md`. Every number is an Architect draft dated 2026-10-31 that Westley rules.

## The file

One fight, one file, JSON, UTF-8, keys sorted, two-space indent (so two runs of the same fight diff to nothing). Written by the arena runner (H-040 part 2) beside the layout it ran, name `<layout id>-s<seed>.fight.json`.

Top-level keys:
- `schema`: the string `om-fight-1`.
- `layout_id`: the layout file's `id` (H-025 schema, `L-NNNN`).
- `layout_path`: repository-relative path of the layout TOML.
- `seed`: int, the sim seed.
- `tick_rate`: int ticks per second of sim time (20 today, `scripts/skilllab/contract.py:161`).
- `snapshot_every`: int ticks between frames (DRAFT-snapshot-seconds 5 s, so 100 ticks).
- `sight`: `"off"` or `"on"` (stage 1 writes `"off"`: `OM_TP_TARGET_BY_SIGHT` set to 0, `csrc/unit.c:1175`; stages 4 and after write `"on"`).
- `frames`: list, in tick order. Always includes tick 0 and the last tick simulated; between them one frame every `snapshot_every` ticks. DRAFT-snapshot-count: a runner that would write more than 20 frames doubles `snapshot_every` until it does not (Westley 2026-10-30: 10 to 20 snapshots); fewer than 10 is allowed when the fight is short.
- `result`: table, below.

A frame:
- `tick`: int.
- `alive`: `[a, b]` ints.
- `units`: list, one row per unit spawned (dead units stay in every frame), sorted by `id`: `id` (int, engine unit id), `side` (`"A"` or `"B"`), `role` (roster name, `scripts/skilllab/engine.py:16`), `x`, `y` (float, world units, 2 decimals), `layer` (int), `facing` (float radians, 3 decimals), `hp` (float, 1 decimal, 0.0 once dead), `alive` (bool), `target` (int unit id or `null`; from `engine.unit_target`).

Stage 4 adds `seen` (list of enemy ids the unit's side sees) per unit; stage 5 adds `climbing` (float 0 to 1, `transition_progress`). Those keys are absent until their stage; a reader ignores keys it does not know; the checker rejects keys it does not know (so a stage cannot grow the file silently).

`result`:
- `winner`: `"A"`, `"B"` or `"draw"`. DRAFT-winner: the side with survivors when the other has none; both alive at the cap, or both dead, is `"draw"`.
- `survivors`: `[a, b]`.
- `ticks`: int, last tick simulated.
- `capped`: bool, true when the DRAFT-fight-cap 600 s (12,000 ticks) stopped the fight.
- `predict`: the layout's `predict` (`"A"`, `"B"`, `"draw"`), copied.
- `agree`: bool, `winner == predict`.

## Worked example

Two frames, one unit per side. Side A's unit stands still; side B's unit is dead by tick 100, so A wins as the layout predicted. This is exactly what `snapshot.example(frames=2, units_per_side=1)` returns, written by `snapshot.write`.

```json
{
  "frames": [
    {
      "alive": [
        1,
        1
      ],
      "tick": 0,
      "units": [
        {
          "alive": true,
          "facing": 0.0,
          "hp": 100.0,
          "id": 1,
          "layer": 0,
          "role": "Raider",
          "side": "A",
          "target": null,
          "x": 100.0,
          "y": 50.0
        },
        {
          "alive": true,
          "facing": 3.142,
          "hp": 100.0,
          "id": 2,
          "layer": 0,
          "role": "Raider",
          "side": "B",
          "target": null,
          "x": 140.0,
          "y": 50.0
        }
      ]
    },
    {
      "alive": [
        1,
        0
      ],
      "tick": 100,
      "units": [
        {
          "alive": true,
          "facing": 0.0,
          "hp": 100.0,
          "id": 1,
          "layer": 0,
          "role": "Raider",
          "side": "A",
          "target": null,
          "x": 100.0,
          "y": 50.0
        },
        {
          "alive": false,
          "facing": 3.142,
          "hp": 0.0,
          "id": 2,
          "layer": 0,
          "role": "Raider",
          "side": "B",
          "target": null,
          "x": 140.0,
          "y": 50.0
        }
      ]
    }
  ],
  "layout_id": "L-0001",
  "layout_path": "docs/northstar/research/layer_dynamics/layouts/L-0001.toml",
  "result": {
    "agree": true,
    "capped": false,
    "predict": "A",
    "survivors": [
      1,
      0
    ],
    "ticks": 100,
    "winner": "A"
  },
  "schema": "om-fight-1",
  "seed": 1,
  "sight": "off",
  "snapshot_every": 100,
  "tick_rate": 20
}
```

## The reader rule

Ignore keys you do not know: a later stage may add `seen` or `climbing` to a unit row, and a reader written before that stage must keep working. The checker (`snapshot.validate`) is the opposite: it rejects keys it does not know, so a stage cannot grow the file without its own contract change. Units are never removed from later frames, so a unit id found in frame 0 is in every frame.
