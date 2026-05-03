# Stage 11f — Fairness Redesign (Post-Playtest)

## Status

**Blocked on:** playtest data accumulation. The structured fairness log corpus (`tuning_output/fairness_log/*.jsonl`) must contain enough real gameplay sessions to ground metric targets in observed player outcomes rather than theory.

## Goal

Redesign the map fairness evaluation system using real playtest data. The bible's two-layer architecture (hard constraints at layout authoring time + an evaluator catching canvas-scaling edge cases) is the target. The current four metrics (path balance via max-flow, travel time via BFS hops, vantage proximity, hazard proximity) measure proxies that don't align with the bible's stated intent — they flag intentional authored asymmetries as failures. This spec will determine what fairness *actually means* in terms of player experience and design new metrics (or redesign targets) accordingly.

## Cross-References

- `tuning_output/stage11e/layout_audit.md` — per-(layout, archetype) failure analysis from the Stage 11e audit. Documents why the current metrics fail and classifies root causes.
- `tuning_output/fairness_log/` — structured JSONL corpus written by `map_generator.py` for every generated map. Schema: `{"archetype", "layout_id", "seed", "fairness_score": {...}}`.
- `docs/bible/bible_world.md` §"Generation Pipeline" — the bible's two-layer fairness architecture passage and the interim-pivot note.
- `simulation/fairness_evaluator.py` — current metric implementations (preserved intact by Stage 11e).
- `simulation/archetype_filters.py` — current FairnessTargetProfile values (intent placeholders pending this spec).
- `docs/stage_specs/stage_11e_fairness_reconciliation_spec.md` §"Pivot" — rationale for deferral.
