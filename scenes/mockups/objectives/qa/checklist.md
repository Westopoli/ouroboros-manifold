# Objectives mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs, Godot 4.6.3, llvmpipe. Filled after the clean and planted Xvfb runs.

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | same seed/archetype/fixture hashes equal twice | TBD | seed-ignored | TBD |
| SEED-2 | seed 11 vs 12 differ in hash for >= 6/10 archetypes | TBD | seed-ignored | TBD |
| KIND-3 | objective kind equals table kind for all 10 | TBD | kind-mapping-random | TBD |
| PLACE-4 | placement matches kind's expected node type | TBD | objective-on-spawn | TBD |
| SAT-5 | all 10 archetypes satisfiable on all 3 fixtures, >=2000wu from spawn | TBD | objective-on-spawn | TBD |
| ROUTE-6 | blocked route exceeds straight line; walled objective unsatisfiable+skip | TBD | route-ignored | TBD |
| NAME-7 | 1 marker, Label3D text non-empty and matches objective name | TBD | marker-unnamed | TBD |
| PROG-8 | tick(600) progress in (0,1), monotone, pauses in enemy window, completes | TBD | progress-static | TBD |
| SHAPE-9 | objective dict has exactly id/type/progress/status/is_primary/location | TBD | none | TBD |
| JSON-10 | qa_state() round-trips JSON; qa_plant contract correct | TBD | none | TBD |
| TIME-11 | timing_ms.gen < 200ms headless | TBD | none | TBD |

## Xvfb oracles

| id | oracle | clean | plant | planted |
|---|---|---|---|---|
| MARKER-X | marker colour within 6px of marker.px at heights 3000/12000 | TBD | marker-unnamed | TBD |
| PROG-X | diff hud_p30 vs hud_p90 bar crop >= 0.002; progress 0.3 vs 0.9 | TBD | progress-static | TBD |
| SEED-X | diff seed11 vs seed12 >= 0.05 clean, < 0.01 planted | TBD | seed-ignored | TBD |
| KIND-X | the five kind screenshots pairwise diff >= 0.01 | TBD | none | TBD |
| ERR-0 | errors.txt count, exit.txt, no UNIFORM | TBD | none | TBD |
| GPU-0 | _qa.adapter contains llvmpipe | TBD | none | TBD |

## Visual questions

- **Q1** (objective is first thing the eye lands on at tactical zoom, name readable): TBD
- **Q2** (five kinds tellable apart from marker alone, no HUD line): TBD
- **Q3** (at map zoom, marker/ring read, escort route reads as a route): TBD
- **Q4** (HUD line shows done-looks-like in one glance): TBD
- **Q5** (map reads as places, not a blank plane with one marker): TBD
- **Q6** (any magenta/black/clipped/overlapping text at 720p): TBD

**HELD:** TBD

## Wall/frame time

TBD
