# Stage 11f — Fairness Redesign (Post-Playtest)

## Status

**Deferred.** Original deferral: 2026-05-03 (Stage 11e pivot). Most recent status check: 2026-06-02. Time elapsed since deferral: ~30 days.

**Blocked on:** playtest data accumulation. The structured fairness log corpus (`tuning_output/fairness_log/*.jsonl`) must contain enough real gameplay sessions to ground metric targets in observed player outcomes rather than theory. As of 2026-06-02, the corpus is small (a handful of dev-run JSONL files) — not enough signal to redesign metrics against.

**Unblock condition:** at least one full playtest cohort generating fairness logs across the full archetype × layout matrix, plus subjective "did this feel fair?" feedback from those players. Without both, the redesign would just be re-theorizing.

**Reopen-when:** Steam playtest cohort is running (see `docs/legacy/method_era1/priority_queue.md` Pre-Steam-submission group). Until then, the interim Stage 11e implementation (simple-random picker + JSONL logging) is the live behavior.

## Goal

Redesign the map fairness evaluation system using real playtest data. The bible's two-layer architecture (hard constraints at layout authoring time + an evaluator catching canvas-scaling edge cases) is the target. The current four metrics (path balance via max-flow, travel time via BFS hops, vantage proximity, hazard proximity) measure proxies that don't align with the bible's stated intent — they flag intentional authored asymmetries as failures. This spec will determine what fairness *actually means* in terms of player experience and design new metrics (or redesign targets) accordingly.

## Expected scope on unblock

When the playtest corpus is large enough, this stage will:

1. **Mine the JSONL corpus** — cluster real games by archetype × layout. Identify which generated maps produced fair-feeling games vs unfair-feeling games per player feedback.
2. **Build correlation matrix** — which current metrics (path balance, BFS travel time, vantage proximity, hazard proximity) actually correlate with player-perceived fairness? Which are noise? Which flag intentional design as failure?
3. **Redesign metrics** — drop noise metrics. Add new metrics for whatever the corpus shows actually matters. Re-tune target profiles per archetype.
4. **Re-implement evaluator** — `simulation/fairness_evaluator.py` rewrite against the new metric set. Preserve the bible's two-layer architecture.
5. **Re-tune `FairnessTargetProfile`** — replace intent placeholders in `simulation/archetype_filters.py` with corpus-grounded values.

## Cross-References

- `tuning_output/stage11e/layout_audit.md` — per-(layout, archetype) failure analysis from the Stage 11e audit. Documents why the current metrics fail and classifies root causes.
- `tuning_output/fairness_log/` — structured JSONL corpus written by `map_generator.py` for every generated map. Schema: `{"archetype", "layout_id", "seed", "fairness_score": {...}}`.
- `docs/bible_history/bible_2_00_world.md` §"Generation Pipeline" — the bible's two-layer fairness architecture passage and the interim-pivot note.
- `simulation/fairness_evaluator.py` — current metric implementations (preserved intact by Stage 11e).
- `simulation/archetype_filters.py` — current FairnessTargetProfile values (intent placeholders pending this spec).
- `docs/legacy/stage_specs/stage_11e_fairness_reconciliation_spec.md` §"Pivot" — rationale for original 2026-05-03 deferral.
- `docs/legacy/method_era1/priority_queue.md` Pre-Steam-submission group — Steam playtest cohort is the unblock event.
