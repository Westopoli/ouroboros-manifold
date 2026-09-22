# Galaxy mockup QA checklist

TEMPLATE — filled with real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs once the feature is built. Thresholds are candidates; Westley owns the final number.

| id | oracle | threshold (candidate) | measured clean | measured planted | plant |
|---|---|---|---|---|---|
| DET-1 | `qa_seed(11)` twice, `hash` equal | exact | TBD | — | none |
| SEED-2 | `hash` differs 11 vs 12; `diff seed11_regional.png seed12_regional.png` | >= 0.15 clean; < 0.02 planted | TBD | TBD | `seed-ignored` |
| CONN-3 | every faction's systems form one connected component over border edges | exact | TBD | — | none (self-test) |
| KIND-4 | no border edge crosses owners; no trade edge shares an owner | exact | TBD | — | none (self-test) |
| COLOUR-5 | every point colour matches its owner's palette | exact | TBD | TBD | `owner-colour-flat` |
| BAND-6 | `get_band()` at 80/50/20 is Overview/Regional/Local | exact | TBD | TBD | `bands-frozen` |
| PICK-7 | `project` then `pick_at` round-trips; 40px away misses | exact | TBD | TBD | `pick-radius-zero` |
| EDGES-8 | filament parent is Node3D under World; no 2D fault overlay | exact | TBD | TBD | `edges-2d-overlay` |
| REPLAY-9 | fixture ids valid; conquest recolours `to` to `from`'s owner | exact | TBD | TBD | `conquest-no-recolour` |
| JSON-10 | `qa_state()` round-trips JSON; every plant id returns true, `nope` false | exact | TBD | — | none |
| TIME-11 | `timing_ms.gen + timing_ms.build` | < 500ms | TBD | — | none |
| FOCUS-X | click system 5's pixel, `focused == 5`, `band == "Local"` | exact | TBD | TBD | `pick-radius-zero` |
| HOVER-X | `diff regional.png hover_f1.png` | >= 0.03 | TBD | TBD | `owner-colour-flat` |
| BAND-X | `diff overview.png local.png` | >= 0.30 | TBD | — | none |
| FLASH-X | `diff before_replay.png mid_replay.png`; owners changed after conquest | >= 0.01; owners differ | TBD | TBD | `conquest-no-recolour` |
| ERR-0 | `errors.txt` count, `exit.txt`, no `UNIFORM` | count 0; exit 0 | TBD | — | none |
| GPU-0 | `_qa.adapter` contains `llvmpipe` | exact | TBD | — | none |

## Visual questions

TBD once screenshots exist.

## HELD

TBD.

## Timings

TBD.
