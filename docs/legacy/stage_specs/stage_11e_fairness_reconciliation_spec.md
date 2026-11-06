# Stage 11e — Fairness Reconciliation: Layouts, Profiles, Metric Hygiene

## Pivot (2026-05-03)

**Scope reduction.** The original spec attempted to reconcile the fairness pipeline by authoring profile targets and rebalancing layout positions/edges. The Checkpoint D audit (`tuning_output/stage11e/layout_audit.md`) revealed that the four fairness metrics (proximity-based vantage/hazard balance, BFS-hop travel time, max-flow path balance) measure different things than the bible's two-layer architecture intends. Authored layout asymmetries (vantage overlooking enemy approach, defender starting near chokepoints) are **intentional design**, not authoring oversights — yet the evaluator flags them as failures.

Designing fairness targets without playtest data would either homogenize maps (bad for gameplay) or rubber-stamp existing layouts (bad for the evaluator's purpose). Instead: ship an interim simple-random picker, log fairness scores for every generated map, and defer the real fairness architecture to `stage_11f_fairness_redesign_spec.md` once a playtest corpus grounds the metrics.

**What shipped:**
- Checkpoint A (baseline diagnostic) — done, preserved in `tuning_output/stage11e/`.
- Checkpoint B (D1 zero-count metric skip) — done, landed in `fairness_evaluator.py`.
- Simple-random picker in `map_generator.py` — replaces retry/rejection loop.
- Structured fairness logging to `tuning_output/fairness_log/<date>.jsonl`.
- Bible updated (`docs/bible_history/bible_2_00_world.md` §"Generation Pipeline") to reflect interim state.

**Deferred to stage_11f:** Checkpoints C (profile operationalization), D/E/F (layout audit and edits), G/H (verification). The audit document is preserved as future-spec input.

---

## Goal (original, for reference)

Reconcile three independent gaps in the map-fairness pipeline that surfaced during Stage 11b's Checkpoint D diagnostic. Pre-spec evidence: every (layout, archetype) pair fails fairness 100% of the time across 20 seeds; the map generator never finds an "acceptable" map and always falls back to "best of N retries." The variety the player sees today is determined by which random layout happens to score least-bad during retries — not by the evaluator's stated purpose. This contradicts `docs/bible_history/bible_2_00_world.md:196`, which describes fairness as a two-layer system where hard constraints handle 90% of cases and the evaluator catches the remaining 10% as edge cases.

The three reconciled gaps:

1. **Zero-count metric degeneracy.** When a layout has zero of a fairness-relevant node type (e.g., zero `vantage` nodes), the current `_safe_ratio(0, 0) = 1.0` returns "balanced" silently. This is a measurement bug, not a design feature — the evaluator was never meant to grade absent node types as "balanced." Per CLAUDE.md ("you may narrow an invariant's scope without approval — skipping cases it was never meant to check"), this is a scope-narrowing fix.

2. **Six non-prototype archetype profile placeholders.** Stage 7 spec authored intentional `FairnessTargetProfile` values for 4 prototype archetypes (assault, defensive_stand, multi_front_defense, counterinsurgency). The other 6 (evacuation, raid, rear_guard, reconquest, siege_breaking, suppression) carry a `_SYMMETRIC_DEFAULT` of `1.0 ± 0.15` on every metric, with the explicit note *"until their 7.5 scripts pin their actual intent."* Stage 7.5 didn't pin them. This spec does.

3. **Layout authoring vs target profile mismatch.** Even with valid profiles and the zero-count fix, the existing 8 layouts have systemic asymmetries (vantage clustered on enemy side; staging vs spawn_point at unequal BFS distances from chokepoints; hazards clustered) that mean most layouts will still fail most archetypes' fairness checks. Layouts were authored for gameplay topology (chokepoints, flanks, staging) but not for the fairness evaluator's distance/proximity metrics. This spec audits and reauthors as needed.

When all three gaps close, the bible's stated fairness model becomes real: most (layout, archetype) pairs pass on first try, retries are occasional, and the original Stage 11b expectation of "0.8 layout diversity ratio over 30 random seeds" becomes meaningful again (re-tested at Checkpoint H).

**Not in scope:**
- New layouts. The existing 8 are reauthored in place; no new authored layouts ship in this spec. (If the audit reveals an archetype needs a layout it doesn't have, escalate to Westley — that's a separate authoring conversation.)
- Library hint system (bible §"What Makes Each Mission Unique" item 3 — still deferred per Stage 11b).
- Pre-mission map preview UI.
- Map variety wiring (`stage_11b_map_variety_spec.md` — already shipped).
- Layer visuals, fog of war, mid-mission HUD (`stage_11c_*`, `stage_11d_*` — orthogonal Godot work).
- Per-branch fairness parameterization (post-Stage 13 per `game_bible.md` v2.14).
- Fairness evaluator algorithm changes beyond the zero-count scope-narrowing fix. The four metrics (path balance, travel time, vantage, hazard) and their formulas remain as Stage 7 specified. We adjust *what counts as acceptable*, not *how it's measured*.

**Architecture.** Sim-side only. Three categories of change: (1) one targeted edit to `fairness_evaluator.py` for the zero-count scope-narrowing; (2) `archetype_filters.py` profile values for the 6 placeholder archetypes (or wherever the `_SYMMETRIC_DEFAULT` lives — confirm at implementation); (3) zone-position edits to JSON layout files in `simulation/layout_library/`. No new files. No tick delta shape changes. No Godot-side changes.

This is more design-and-content work than code work. Most of the line count is JSON layout edits.

## Bible References

- **`docs/bible_history/bible_2_00_world.md`** §"Generation Pipeline" (lines 174–211) — fairness evaluator design, hard-constraint vs evaluator division of labor.
- **`docs/bible_history/bible_2_00_world.md`** line 196 — *"the constraint rules handle 90% of fairness; the evaluator catches edge cases from canvas scaling and gradient interactions."* The current 0% pass rate violates this directly. Bible-authoritative target for this spec: most (layout, archetype) pairs pass first-try.
- **`docs/bible_history/bible_2_00_world.md`** line 196 — *"Map seeds are tiny... so regenerating a few times is cheap."* Confirms retries are exceptional, not routine. Current behavior (always retrying to exhaustion) violates this.
- **`docs/bible_history/bible_2_00_world.md`** §"Spine Node Types" — defines the role of each node type (objective, staging, transit, chokepoint, flank route, **vantage**, **hazard zone anchor**, spawn point, extraction, reinforcement structure). Vantage and hazard placement decisions live here.
- **`docs/bible_history/bible_2_00_missions.md`** (full file) — per-archetype mission character prose. The 6 non-prototype `FairnessTargetProfile` values (Design Decision D2 below) derive their *directional intent* from this spoke. Read fully before drafting profile values.
- **`docs/bible_history/bible_2_00_combat.md`** §"Vantage Points" / §"Hazard Zones" — tactical role of these node types in combat resolution. Helps inform what "balanced vantage access" means in practice.
- **Stage 7 spec** §"Archetype-Aware Fairness" + §"Files to create" `archetype_filters.py` description — the original `FairnessTargetProfile` design and the explicit placeholder note for the 6 non-prototype archetypes. This spec finishes what Stage 7 specified.

Do NOT read `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_antagonist.md`, `docs/bible_history/bible_2_00_ai_pipeline.md`, or `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) — not relevant.

## Cross-Stage References

- **Stage 7 (map generation)** — owns `fairness_evaluator.py`, `archetype_filters.py`, `layout_library/`, the `FairnessTargetProfile` dataclass. This spec edits all three but introduces no new structure. The Stage 7 contract is unchanged.
- **Stage 7.5 (enemy macro behavior + reinforcement ownership baselines)** — Stage 7.5 spec mentioned "prototype reinforcement ownership baselines author here alongside the scripts" but did not pin the 6 placeholder fairness profiles despite Stage 7's note that 7.5 would. This spec absorbs that orphaned work.
- **Stage 11b (map variety wiring)** — already shipped with a recalibrated Checkpoint D pass condition (per the 2026-04-30 escalation approval). When this spec lands, Stage 11b's *original* 0.8 layout-diversity expectation becomes achievable; Checkpoint H below verifies and effectively retroactively closes the original 11b condition.
- **Stage 11c / 11d** — orthogonal. Godot rendering work. No interaction.
- **Stage 12 / 12.5** — visual polish. No interaction.

## Pre-Spec Evidence

The diagnostic that motivated this spec lives at `tuning_output/stage11b/post_d_variety.txt` and was instrumented in the Stage 11b Checkpoint D escalation chat. Key findings preserved here so the implementer doesn't have to re-derive them:

- 0% pass rate across all (layout, archetype) pairs over 20 seeds.
- Three failing metrics dominate: travel_time (ratios 0.25–4.00 vs target ~1.0±0.15), vantage (ratio 0.00 — all vantage on enemy side, on layouts that have any), hazard (similar asymmetry).
- Layouts with zero vantage or zero hazard nodes silently "pass" those metrics via `_safe_ratio(0, 0) = 1.0`.
- The 6 non-prototype archetypes use `_SYMMETRIC_DEFAULT = 1.0 ± 0.15` placeholder.
- Per-archetype filter pool sizes: counterinsurgency=2, multi_front_defense=3, defensive_stand/assault=5, others=8.

The implementer should re-run the per-(layout, archetype) fairness instrumentation as Checkpoint A's baseline rather than trusting these notes — this captures the current state at implementation time, in case anything has shifted.

## Design Decisions

### D1 — Zero-count metric scope-narrowing

**Decision:** When a fairness metric's underlying counts are zero on **both sides** (player_value == 0 and enemy_value == 0), the metric is **skipped** (not counted toward aggregate pass/fail). The current code's `_safe_ratio(0, 0) = 1.0` is replaced with explicit skip semantics.

**Authority:** CLAUDE.md — *"You may narrow an invariant's scope without approval — skipping cases it was never meant to check (empty regions, factions with zero territory, runs shorter than the invariant's window)."* A layout with zero vantage nodes is a "case the invariant was never meant to check" — vantage *balance* is undefined when there's no vantage to balance.

**Why both-sides-zero only, not either-side-zero:** if only one side has zero of a node type (e.g., player has 0 vantage, enemy has 3), that's a real authoring imbalance — one side has access, the other doesn't. The metric correctly returns ratio=0.0 in that case, and that should fail. The bible's hard constraints already require certain features be reachable by both sides (`docs/bible_history/bible_2_00_world.md:196` — *"vantage points must be reachable by both sides"*). Asymmetric *presence* is the layout's problem to solve; the evaluator should surface it, not paper over it.

**Implementation shape:** `FairnessScore` gains a `metric_skipped` flag per metric. `is_acceptable()` excludes skipped metrics from the aggregate. Logging surfaces which metrics were skipped per evaluation, so we can spot the case where most metrics are getting skipped (which would itself be a layout-authoring red flag).

**Rejected alternatives:**
- *Treat zero-of-both as fail.* Too strict — the bible's hard-constraint layer handles "node type required" cases via the archetype filter. If `assault` requires ≥1 vantage and a layout has zero, the filter excludes it — fairness shouldn't double-fail it.
- *Treat zero-of-both as pass with ratio=1.0 (current behavior).* Misleading — silently grades absent features as "balanced," masking authoring oversights. The diagnostic that motivated this spec was muddied by exactly this behavior.

### D2 — Author the 6 non-prototype `FairnessTargetProfile`s, directionally per `docs/bible_history/bible_2_00_missions.md`

**Decision:** Each of the 6 non-prototype archetypes (evacuation, raid, rear_guard, reconquest, siege_breaking, suppression) gets a `FairnessTargetProfile` reflecting its tactical character per `docs/bible_history/bible_2_00_missions.md`. The spec pins **directional intent per metric per archetype** — not specific numerical values.

**Why directional, not numerical:** per CLAUDE.md (Stage 6 v2.07 precedent: *"Tier 2 numeric table removed (values live in config)"*), specific numbers are tuning parameters and live in code. The bible-grounded design decision is *which direction each metric leans* and *roughly how tight the tolerance is*. Implementation produces draft numerical values matching the directional intent and presents them for Westley's approval before code lands (see Checkpoint C — there is an explicit hold-for-approval gate).

**Directional framework:** for each metric, the profile is described as one of:
- `(symmetric, tight)` — target ~1.0, tolerance ±0.10–0.15. Mirror missions, balanced confrontations.
- `(symmetric, loose)` — target ~1.0, tolerance ±0.20–0.30. Tactical variety acceptable; absolute symmetry not required.
- `(player_advantage)` — target > 1.0 on metrics where higher = player benefit. Defenders, dug-in scenarios, prepared positions.
- `(enemy_advantage)` — target < 1.0 (or > 1.0 on inverse metrics). Player is the underdog; mission character is "you're under pressure."
- `(skip)` — metric not pinned for this archetype because it's not characteristic. (Rare; the four metrics are all generally relevant.)

**Per-archetype directional draft (subject to bible re-reading and Westley approval at Checkpoint C):**

These are first-pass directional reads. The implementer should re-read `docs/bible_history/bible_2_00_missions.md` for each archetype and refine these before Checkpoint C's approval gate.

- **evacuation** — player extracts something under pressure. Travel: `(enemy_advantage)` — enemy spawns close; player must move under threat. Vantage: `(symmetric, loose)` — extraction routes shouldn't be wholly enemy-dominated. Hazard: `(symmetric, loose)` — hazards are situational. Path: `(player_advantage)` — multiple extraction routes is the design intent; one route is a trap.
- **raid** — fast, asymmetric strike. Travel: `(player_advantage)` slight — strike force benefits from quick approach. Vantage: `(enemy_advantage)` — defender holds the high ground; raider exploits anyway. Hazard: `(symmetric, loose)`. Path: `(symmetric, loose)` — raids work with any path topology.
- **rear_guard** — player holds while something behind them retreats. Travel: `(symmetric, tight)` — even confrontation. Vantage: `(player_advantage)` — defender chooses ground. Hazard: `(player_advantage)` — defender prepared the field. Path: `(enemy_advantage)` — attacker has multiple approaches.
- **reconquest** — player takes back territory. Travel: `(symmetric, tight)`. Vantage: `(symmetric, tight)`. Hazard: `(enemy_advantage)` — entrenched defender has hazards in their favor. Path: `(symmetric, loose)`.
- **siege_breaking** — player breaks an enemy siege. Travel: `(enemy_advantage)` — siege has the geometric advantage; relief force fights uphill. Vantage: `(enemy_advantage)`. Hazard: `(enemy_advantage)` — siege has had time to fortify. Path: `(player_advantage)` — relief needs route options.
- **suppression** — player fixes/suppresses enemy force. Travel: `(symmetric, loose)`. Vantage: `(symmetric, tight)` — both sides need eyes. Hazard: `(symmetric, loose)`. Path: `(symmetric, loose)`.

**Important note on prototype archetypes:** the 4 prototypes (assault, defensive_stand, multi_front_defense, counterinsurgency) keep their existing Stage 7 profiles unchanged. **Do not edit prototype profiles in this spec.** If the audit (Checkpoint D) reveals a prototype profile is unattainable by any layout, that's a design escalation, not a profile recalibration.

### D3 — Layout authoring scope: edit-in-place, audit-driven

**Decision:** Existing 8 layouts are edited in place (zone position adjustments, possible node-type changes, possible adds/removes of vantage/hazard nodes) per the audit at Checkpoint D. No new layouts ship in this spec. No layout is removed from the library.

**Three classes of edits the audit may produce:**

- **Class A: rebalance node positions.** Move existing vantage / hazard / staging / spawn_point zones so BFS distances and proximity ratios fall within target tolerances. Cheapest class; preserves the layout's authored intent.
- **Class B: add or remove fairness-relevant nodes.** A layout with zero vantage that's in an archetype pool requiring vantage gets vantage nodes added. A layout with too many hazards (causing ratio >2.0) gets some demoted to other types. Riskier — changes the layout's gameplay shape.
- **Class C: narrow the archetype filter to exclude this (layout, archetype) pair.** Some layouts genuinely don't fit some archetypes — e.g., `layout_07_scattered_outposts` has no chokepoints and may simply not work for `siege_breaking`. Tightening the filter is the correct fix in those cases.

**Approval gate:** every Class B and Class C edit is presented to Westley before the change is made (Checkpoint E hold). Class A edits within tight numerical bounds may proceed without per-edit approval but are summarized in a single batch review at Checkpoint E. The implementer makes a recommendation per (layout, archetype) failing pair; Westley approves the class.

**Why audit-driven rather than blanket:** layout authoring is gameplay design. Repositioning a vantage node from "near enemy spawn" to "central, accessible to both" changes how players approach the map. That's not a mechanical fix — it's a design decision. Bulk-fixing 80+ failing pairs without per-pair thought produces flavorless layouts.

### D4 — Hard-constraint enforcement at layout authoring time

**Decision:** Reaffirm and strengthen the bible's two-layer fairness model. Hard constraints (per `docs/bible_history/bible_2_00_world.md:196` — *"vantage points must be reachable by both sides, all player approaches can't be blocked by hazards while enemy approaches are clear"*) are enforced at **layout load time**, not at fairness-evaluation time. The fairness evaluator handles edge cases from canvas scaling and gradient interactions; it does not handle layout-authoring oversights.

**Implementation shape:** `layout_library.py`'s `load_all_layouts()` validation (which already exists per Stage 7 spec) is extended with hard-constraint checks. Failed checks are loud — the layout fails to load with a clear error pointing to the violated rule. This means an invalid layout never enters the candidate pool, never gets selected, never confuses the fairness evaluator.

**Why this is in scope here, not deferred:** without hard-constraint enforcement, the fairness evaluator absorbs work it shouldn't — tolerances widen to accommodate authoring oversights, profiles drift away from real design intent, and we're back to the current 0% pass rate within a few sprints. Enforcing hard constraints at load time keeps the evaluator's job small and well-defined.

**Open question OQ1:** does Stage 7's existing layout validation include any hard-constraint checks beyond structural validity (zone references, position bounds)? Verify at Checkpoint B; if the validation is thinner than the bible's stated hard constraints, this spec adds the missing checks. If full hard-constraint enforcement is already there, this decision is documentary.

### D5 — Performance framing

This spec's runtime cost is sim-side only. The fairness evaluator is called once per mission start and once per fairness retry. With the zero-count fix in place and reauthored layouts, **expected retry count drops from `FAIRNESS_MAX_RETRIES` (current behavior, every mission) to ~0–2 (bible's intended behavior, occasional)**. Net effect on mission generation latency: faster, not slower.

The 16.7 ms Godot frame budget (`docs/bible_history/bible_2_00_combat.md:313`) is not relevant to this spec. The 50 ms sim tick budget is not affected — fairness evaluation is mission-start work, not per-tick work.

Checkpoint G measures end-to-end mission generation time as a sanity check.

## Open Questions

- **OQ1 — Existing hard-constraint validation.** D4 assumes Stage 7's `load_all_layouts()` already does structural validation but may not enforce all hard constraints from `docs/bible_history/bible_2_00_world.md:196`. Verify at Checkpoint B; if the validator is thinner than the bible specifies, the gap closes here. If full enforcement already exists, D4 is documentary only.
- **OQ2 — Positional jitter ordering.** Per `layout_instantiator.py`, positional jitter is applied during layout instantiation. Question: does the fairness evaluator score the layout *before* or *after* jitter? If after, jitter could push an authored-fair layout out of tolerance, contributing to the failure pattern. If before, the evaluator sees the authored map directly. Verify at Checkpoint B; if the order is wrong (jitter then evaluate, when it should be evaluate then jitter, or vice versa), escalate — that's a separate fix.
- **OQ3 — Counterinsurgency pool size.** Counterinsurgency only has 2 layouts in its compatible pool, and the diagnostic showed both fail fairness. Even with this spec's reconciliation, a 2-layout pool produces low diversity. **Out of scope for this spec to fix (no new layouts authored here).** Flagged for a future authoring conversation. The audit at Checkpoint D may surface that one of the 2 layouts genuinely doesn't fit counterinsurgency, in which case Class C narrows the filter and the pool drops to 1 — escalate then; Westley decides whether to ship with a 1-layout pool or author a new layout.
- **OQ4 — Profile value bounds.** D2 talks about tight (±0.10–0.15) vs loose (±0.20–0.30) tolerances. These ranges are first-pass; if the audit (Checkpoint D) shows a profile is unattainable by any layout no matter how reauthored, the tolerance widens further — but only with Westley's approval, since that's invariant-loosening per CLAUDE.md.

## What to Build

### Files to modify

**`simulation/fairness_evaluator.py`** — zero-count metric scope-narrowing per D1.
- Replace `_safe_ratio(0, 0) = 1.0` with explicit skip semantics. Specific shape: each metric returns either a `Ratio(value, both_sides_zero=False)` tuple or sets a `metric_skipped` flag on `FairnessScore`.
- Update `is_acceptable(score, archetype)` to exclude skipped metrics from the aggregate. Aggregate passes when all *non-skipped* metrics fall within their tolerances.
- Add logging: at evaluator entry, log per-metric skip status. This surfaces the case where most metrics are getting skipped (which means the layout is too feature-sparse and is itself a red flag).
- Add a `# See also: docs/legacy/stage_specs/stage_11e_fairness_reconciliation_spec.md` comment near the change.

**`simulation/archetype_filters.py`** (or wherever `FairnessTargetProfile`s live; verify at implementation) — pin the 6 placeholder profiles per D2.
- Replace each archetype's reference to `_SYMMETRIC_DEFAULT` with an authored profile. Specific numerical values produced at Checkpoint C and approved by Westley before this code lands.
- Keep the 4 prototype profiles unchanged.
- Optionally remove `_SYMMETRIC_DEFAULT` after all references are gone, OR keep it as a documented fallback for future archetypes added without explicit profiles. Implementer's call; document the choice.

**`simulation/layout_library.py`** — strengthen hard-constraint validation per D4 (only if OQ1 reveals gaps).
- Extend `load_all_layouts()`'s validation block with the bible's hard-constraint rules. Specific rules to enforce:
  - Vantage points (if present) must be reachable by both staging and spawn_point sides via the spine graph.
  - Hazard zone anchors must not block all player approaches while leaving enemy approaches clear (graph-distance check).
  - Every chokepoint must have at least one flank route per archetype filter requirements (Stage 7 already enforces this for some archetypes; generalize to layout-load time).
- Failed checks raise `LayoutValidationError` with a clear message naming the rule and the offending zone.
- This change is conditional on OQ1's answer. If full enforcement exists, skip this file.

**`simulation/layout_library/layout_*.json`** — reauthored zone positions, possible node-type changes, possible adds/removes per D3.
- Per the audit at Checkpoint D, each affected layout gets edited. Class A edits (rebalance positions) are within authoring tolerance; Class B edits (add/remove nodes) and Class C edits (filter narrowing, no JSON change but config change) are flagged for Westley's approval at Checkpoint E.
- Each edited file gets a top-level `"_meta": {"edited_for": "stage_11e", "edit_summary": "..."}` field documenting what changed and why. If layout JSONs already have a meta field, extend it; if not, add one.

**`simulation/archetype_filters.py`** (Class C edits) — narrow filters for genuinely-incompatible (layout, archetype) pairs.
- For each Class C decision approved at Checkpoint E, add an exclusion rule to the relevant archetype's filter, OR add a tag to the layout that the filter excludes.
- Specific mechanism: implementer's choice between filter-rule and layout-tag, document the choice.

**`docs/architecture.md`** — document the zero-count metric skip semantics.
- Brief subsection under the fairness evaluator description (if one exists) explaining the both-sides-zero skip behavior and pointing to this spec.
- Per CLAUDE.md, contract-shape changes go here; the `FairnessScore` shape gains a `metric_skipped` flag, which is a contract-shape change.

**`docs/legacy/stage_specs/stage_11b_map_variety_spec.md`** — note this spec's relationship.
- Add a short note at the top of Stage 11b's spec or in a forward-references section: *"Stage 11e (fairness reconciliation) closes the diagnostic gap surfaced at Stage 11b's Checkpoint D escalation. Once 11e ships, the original 0.8 layout-diversity expectation in this spec's earlier draft becomes achievable; Stage 11e Checkpoint H verifies."*
- Do not alter Stage 11b's recalibrated Checkpoint D pass condition — it's correct for what 11b alone is responsible for.

**`docs/bible_history/bible_2_00_world.md`** — bible reconciliation, only if Checkpoint H surfaces design ambiguity.
- Per CLAUDE.md, bible edits are first-class deliverables when behavior changes the bible's stated promises. If the audit surfaces (e.g.) that "fairness" needs more nuance than the current §"Generation Pipeline" prose conveys, capture that here. Default expectation: no bible edits needed; the bible's existing fairness model is correct, this spec just makes it real.

### Files NOT to modify

Listing explicitly because the temptation will be there:

- **`simulation/fairness_evaluator.py` algorithm beyond D1.** The four metrics' formulas are correct per `docs/bible_history/bible_2_00_world.md:196`. We change *what counts as acceptable* (skip semantics) and *what acceptable values are per archetype* (D2), not *how the metrics compute*.
- **The 4 prototype `FairnessTargetProfile`s.** If a prototype profile is unattainable, **STOP and escalate** per the rule below. Do not silently widen its tolerance.
- **`simulation/map_generator.py` retry logic.** Once fairness pass-rate is healthy (Checkpoint G expected: most layouts pass first try), the retry logic does what the bible promised — occasional regeneration. No changes needed.
- **`simulation/sim_flavoring.py`.** Sim-state-driven gradient modifiers are not in scope. They affect rendered terrain detail, not the fairness evaluator's inputs.
- **`simulation/layout_instantiator.py`.** Jitter logic is not in scope unless OQ2 reveals an ordering bug. If it does, escalate — that's a separate fix.

## Checkpoints

> **Escalation rule — read this before running any checkpoint.**
>
> When a checkpoint's after-state measurement does **not** match this spec's expected outcome — whether a test fails, a baseline doesn't reproduce, a perf number regresses outside the stated tolerance, a schema check rejects something it shouldn't, or any output is unexpected enough that the implementer would be guessing at the cause — **STOP**. Do not modify the implementation, the test, or the spec to make it pass. Do not iterate on a fix.
>
> **FLAG the discrepancy and bring it to Westley.** Include: which checkpoint, what was measured, what was expected, what was observed, and the implementer's hypothesis if any. Wait for guidance.
>
> The cost of a wrong silent fix is a debugging session three weeks from now without context; the cost of a five-minute escalation is five minutes. Default to escalation.
>
> This rule exists per CLAUDE.md ("No shotgun fixes" and "One confirmed diagnosis is worth ten guesses") and applies uniformly to every checkpoint below.

> **Approval gates.** Three checkpoints in this spec have **explicit hold-for-Westley-approval gates** (Checkpoints C, E). At those points the implementer presents draft work and waits for explicit approval before code changes land. Do not interpret silence as approval.

Each checkpoint follows the **measure → change → re-measure** pattern.

### Checkpoint A — Baseline confirmation: re-instrument the diagnostic

**Purpose:** Reproduce the Stage 11b Checkpoint D escalation diagnostic from a fresh run, capturing current state at implementation time. The pre-spec evidence section above summarizes what the original run found, but state may have shifted slightly; baseline measurement here is authoritative.

**Baseline measurement:**
1. Re-create the per-(layout, archetype) fairness instrumentation that produced the original diagnostic. The implementer doesn't need to recover the original Bash one-liner — author a short Python script under `tests/diag_fairness_pass_rate.py` that:
   - For each archetype, for each layout in its compatible pool, runs N=20 random seeds through `instantiate_layout` + `evaluate_fairness`.
   - Reports per (archetype, layout): pass count out of 20, which metrics failed and how often, sample ratio values vs target.
   - Saves output to `tuning_output/stage11e/baseline_pass_rates.txt`.
2. Confirm the diagnosis pattern matches what's documented in pre-spec evidence: ~0% pass rate, three dominant failing metrics, zero-count cases silently passing where applicable.

**Pass condition:** baseline diagnostic reproduces the documented failure pattern. **If pass rates are substantially different from the documented evidence (e.g., 50% pass rate now), STOP and escalate** — something has changed since the original diagnostic and the spec's premise needs re-examination.

**No code change in this checkpoint.** Just instrumentation.

### Checkpoint B — Zero-count metric scope-narrowing (D1) + OQ1 + OQ2

**Purpose:** Land the smallest authorized change first (CLAUDE.md authorizes scope-narrowing without approval), and resolve the two open questions about existing infrastructure.

**Resolve OQ1 first.** Read `simulation/layout_library.py` `load_all_layouts()` validation. List exactly which checks are currently enforced. Compare against `docs/bible_history/bible_2_00_world.md:196`'s hard constraints. Document the gap — if any — in a short note appended to this checkpoint's evidence file.

**Resolve OQ2.** Read `simulation/map_generator.py` and `simulation/layout_instantiator.py` to determine ordering: is fairness evaluated on the jittered map, or the pre-jitter map? Document the answer. **If the order is wrong (e.g., fairness scores the pre-jitter layout, then jitter changes the map after), STOP and escalate** — that's a separate bug.

**Baseline measurement (for D1):**
- Use the diag harness from Checkpoint A. Identify (layout, archetype) pairs where one or more metrics is currently passing via `_safe_ratio(0, 0) = 1.0`. List them. Expected: layouts without vantage (per pre-spec evidence: layout_04, layout_07) pass vantage; layouts without hazard (layout_02, layout_03) pass hazard.

**Change:**
- Implement D1 in `fairness_evaluator.py` per "Files to modify."
- Update `is_acceptable()` to skip-aware aggregation.
- Add the `architecture.md` note for the `metric_skipped` flag.

**After-state measurement:**
- Re-run the diag harness. Same (layout, archetype) pairs that previously "passed" via zero-count should now show their relevant metric as **skipped**, not passed.
- Aggregate pass-rate may shift slightly (some pairs that passed before due to zero-count now have one fewer metric being evaluated; depending on the other metrics, they may pass or fail).
- Confirm logging shows skip status correctly.

**Pass condition:**
- All previously-zero-count "passes" now register as skips.
- No (layout, archetype) pair that previously failed via a non-zero-count metric has flipped to passing — the change is intended to *not* improve pass rates by relaxation.
- `architecture.md` reflects the contract change.

**Important:** D1 alone is **not** expected to substantially improve overall pass rates. The dominant failures are travel_time, vantage (non-zero, asymmetric), and hazard (non-zero, asymmetric) — none of which are affected by zero-count handling. If D1 alone produces a large pass-rate jump, **STOP and escalate** — likely indicates the change went further than intended.

### Checkpoint C — Author the 6 non-prototype `FairnessTargetProfile`s (D2) — APPROVAL GATE

**Purpose:** Land the per-archetype directional intent for the 6 placeholder archetypes. This is design work; explicit Westley approval is required before code changes.

**Process:**

1. **Read `docs/bible_history/bible_2_00_missions.md` fully.** Capture per-archetype tactical character. The directional drafts in D2 are first-pass; refine them by reading the bible's mission-character prose for each of the 6 archetypes.

2. **Author draft profile values.** For each of the 6 archetypes, produce concrete numerical `FairnessTargetProfile` values matching the directional intent. Use the existing 4 prototype profiles as numerical reference points (e.g., if defensive_stand uses `vantage = 1.15 ± 0.15` for player-advantage, and reconquest's directional intent is `(symmetric, tight)` on vantage, draft `vantage = 1.0 ± 0.10`).

3. **Document the rationale.** For each profile, write a 1–3 sentence rationale citing the relevant `docs/bible_history/bible_2_00_missions.md` passage.

4. **Save the draft.** Write to `tuning_output/stage11e/draft_profiles.md`.

5. **STOP. Present to Westley.** Wait for explicit approval. Do not commit code yet. Acceptable formats for the approval handoff: a comment summarizing the 6 profiles inline, a markdown table, or simply asking Westley to read `draft_profiles.md`.

**On approval:**
- Implement the approved profiles in `archetype_filters.py`.
- Re-run the diag harness from Checkpoint A.
- Save updated pass-rate report to `tuning_output/stage11e/post_c_pass_rates.txt`.

**Expected outcome:** pass rates rise modestly for the 6 non-prototype archetypes (looser tolerances on some metrics will let some currently-failing pairs pass). Pass rates for the 4 prototype archetypes are unchanged (those profiles weren't edited).

**Pass condition:** profiles approved by Westley; implemented as approved; diagnostic shows no regression on prototype archetypes; some improvement on non-prototype archetypes. **If a prototype archetype's pass rate changes (it shouldn't — its profile wasn't touched), STOP and escalate** — likely indicates an unintended change leaked.

### Checkpoint D — Per-(layout, archetype) audit (analysis only, no code change)

**Purpose:** Diagnose every still-failing (layout, archetype) pair and classify the remediation. This is the design-heavy step. Output is an audit document, not code.

**Process:**

1. **Re-run the diag harness** with Checkpoints B and C in place. Save: `tuning_output/stage11e/post_c_failures.txt`. Identify every (layout, archetype) pair still failing, with the failing metrics and ratio values.

2. **Classify each failing pair** into one of the three classes from D3:
   - **Class A (rebalance):** the layout has the right node types in roughly the right places, but specific positions push BFS distances or proximity ratios out of tolerance. Solvable by moving zone positions.
   - **Class B (add/remove nodes):** the layout is missing fairness-relevant nodes that the archetype needs, or has too many of one type. Adds/removes change gameplay shape.
   - **Class C (narrow filter):** the layout is structurally incompatible with the archetype regardless of position fixes. Filter narrows to exclude the pair; pool size shrinks.

3. **For each pair, draft a specific remediation.** E.g., *"layout_05_coastal_wedge × defensive_stand: Class A — vantage zone Z3 currently at (0.85, 0.2) is enemy-side; move to (0.5, 0.2) to make accessible to both sides. Expected: vantage ratio shifts from 0.0 to ~1.1, within target ±0.15."*

4. **Save the audit document** to `tuning_output/stage11e/layout_audit.md`. Format: one section per failing pair, each with current state, classification, proposed remediation, expected post-fix metrics.

**No code change in this checkpoint.** Audit only.

**Pass condition:** every still-failing pair is classified and has a draft remediation. Audit document written. **If the audit reveals a pair where no remediation in any of the three classes is workable, STOP and escalate** — that's a design conversation about whether the archetype needs a new layout authored (out of this spec's scope).

**Counterinsurgency note:** counterinsurgency has only 2 layouts in its pool. If the audit recommends Class C on either of them, the pool drops to 1. Flag this loudly in the audit and escalate before applying the Class C — Westley may prefer a Class B or Class A even at higher complexity cost rather than ship a 1-layout pool.

### Checkpoint E — Layout authoring decisions — APPROVAL GATE

**Purpose:** Westley approves the audit's per-pair remediations before any layout JSON is edited or any filter is narrowed.

**Process:**

1. **Present the audit document** (`tuning_output/stage11e/layout_audit.md` from Checkpoint D) to Westley.
2. **Clearly summarize the scope:** total failing pairs, count per class (A/B/C), any pairs flagged for special attention (e.g., counterinsurgency), and the expected pass-rate delta if all remediations are applied as drafted.
3. **STOP. Wait for approval.** Westley may approve all, approve some, redirect specific decisions, or push back on the framing entirely. Default to no code change until each decision is explicitly approved.
4. **Class A edits within tight numerical bounds may be approved as a batch** (e.g., "all Class A edits approved, proceed"). Class B and Class C edits approved individually unless Westley explicitly batches them.

**No code change in this checkpoint.** Approval handoff only.

**On approval (per pair or per batch):** record the approval in `tuning_output/stage11e/layout_audit.md` (mark each pair "approved YYYY-MM-DD" with the resolution class confirmed) and proceed to Checkpoint F.

**If approval surfaces new design concerns** (e.g., Westley objects to a vantage placement on aesthetic grounds), iterate the audit document and re-present. Do not apply edits piecemeal as approvals trickle in — wait until the audit is closed in a clean state.

### Checkpoint F — Apply approved layout edits

**Purpose:** Execute the approved audit. This is the largest code-change checkpoint, but each individual change is small (zone position adjustment, node type change, filter rule add).

**Process:**

1. **For each approved Class A edit:** open the relevant layout JSON, adjust the zone position(s) per the audit. Update the `_meta.edit_summary` field documenting the change.
2. **For each approved Class B edit:** add or remove the relevant zones. Update edges if connectivity changes. Update `_meta.edit_summary`.
3. **For each approved Class C edit:** narrow the archetype filter (or add a layout exclusion tag) per the implementer's chosen mechanism. Document in `archetype_filters.py` with a `# See also` comment pointing to the audit.

**Per-edit verification:**
- After each layout JSON edit: run `load_all_layouts()` (with Checkpoint B's hard-constraint validation in place per OQ1). Layout must still load. If it fails validation, STOP and escalate — the edit broke a constraint.
- After each Class C filter edit: re-run the archetype's `matching_layouts()` and confirm the pool shrinks as expected.

**Batch verification (after all edits applied):**
- Re-run the diag harness from Checkpoint A. Save: `tuning_output/stage11e/post_f_pass_rates.txt`.

**Pass condition:**
- All approved edits applied.
- All layouts still load successfully.
- Diagnostic shows substantial improvement: most (layout, archetype) pairs now pass first try, matching the bible's "evaluator catches edge cases" model. Specific quantitative target: **aggregate pass rate ≥ 70% across all (layout, archetype) pairs in compatible pools.** This is the "most layouts pass most archetypes" expectation made concrete.
- **If aggregate pass rate is < 70%, STOP and escalate.** Likely cause is one of: (a) the audit's expected post-fix metrics were optimistic (re-audit), (b) a profile value (Checkpoint C) needs further tuning, (c) layout edits introduced unintended effects. None of these are implementer fixes — escalate.

### Checkpoint G — End-to-end mission generation: retry rate drops, generation time stays flat or improves

**Purpose:** Confirm the bible's "regenerating a few times is cheap" promise is now reality.

**Baseline measurement:**
- Pre-spec baseline: capture from Stage 11b's stage close report if available, or generate fresh: 100 missions across all archetypes via the existing `mission_generator.py` path. Log per-mission retry count and generation time.

**After-state measurement:**
- 100 missions across all archetypes with all of this spec's changes in place. Log per-mission retry count and generation time.
- Save report: `tuning_output/stage11e/post_g_retry_and_timing.txt`.

**Pass condition:**
- **Average retry count drops from `FAIRNESS_MAX_RETRIES` (current: every mission retries to exhaustion) to ≤ 2.** Bible's "regenerating a few times is cheap" implies single-digit retries as the norm.
- **Average mission generation time within ±15% of baseline.** Faster is fine and expected; slower would be a regression.
- **Zero missions hit `FAIRNESS_MAX_RETRIES` exhaustion.** If this fires, the layout for that (archetype, region_state) combo is genuinely unworkable — escalate the specific case.

**If retry rate doesn't drop, STOP and escalate.** Means fairness is still rejecting most maps; either Checkpoint F's improvements were illusory or a different mechanism (e.g., simulation flavoring pushing layouts out of tolerance) is at play. Diagnostic question, not implementer fix.

### Checkpoint H — Stage 11b's original 0.8 layout-diversity expectation, retroactively verified

**Purpose:** Stage 11b's Checkpoint D originally asked for 80% layout-diversity ratio over 30 random seeds. That target was recalibrated when fairness was found to be degenerate. With fairness now working, the original target should be achievable. This checkpoint is the retroactive verification that closes the loop on the Stage 11b → 11e escalation.

**Measurement:**
- Run `tests.diag_map_variety` (Stage 11b's harness) with `--n 30 --random` against the post-spec build.
- Save report: `tuning_output/stage11e/post_h_diversity.txt`.

**Pass condition:**
- **Layout diversity ratio ≥ 0.8 for every archetype with pool_size ≥ 5.**
- For archetypes with pool_size = 2 or 3 (counterinsurgency, multi_front_defense), expect ratio ≥ 0.5 minimum, with the target being "every layout in the pool gets selected at least once over 30 missions." Tighter pool sizes have inherently less variety; the test is "does the pool actually exercise" not "does it match the 0.8 ratio designed for larger pools."

**If diversity ratios fall short of these targets, the audit at Checkpoint D missed something.** STOP and escalate; likely a (layout, archetype) pair that should have been Class C narrowed is still consistently winning the retry tiebreaker.

### Checkpoint I — Stage close: bible reconciliation + closing report

**Purpose:** Final review. If anything from the audit and remediation surfaced design ambiguity in the bible, capture it. Otherwise, document what shipped.

**Process:**

1. **Bible reconciliation review.** Re-read `docs/bible_history/bible_2_00_world.md` §"Generation Pipeline" and `docs/bible_history/bible_2_00_missions.md` per-archetype prose. Are there any decisions made during this spec's audit (Checkpoint D) or profile authoring (Checkpoint C) that contradict or clarify the bible's prose? If yes, draft a short bible edit proposal and present to Westley for approval. If no, this step is a no-op confirmation.

2. **Stage close report.** Write `tuning_output/stage11e/stage_close_report.md` summarizing:
   - Initial state (0% pass rate; placeholder profiles; layout-authoring asymmetries).
   - What changed (D1 zero-count fix; 6 authored profiles; Class A/B/C remediations; hard-constraint validation if added).
   - Final state (pass-rate %, retry-rate average, layout-diversity ratios per archetype).
   - Any deferred items (e.g., counterinsurgency pool_size=2 if not addressed; new layouts if Westley wants them later).

3. **Update Stage 11b spec** with a closing note in its forward-references section: *"Stage 11e shipped YYYY-MM-DD; original 0.8 diversity expectation verified at Stage 11e Checkpoint H."*

**Pass condition:** stage close report written; bible reconciliation complete or no-op confirmed; Stage 11b cross-reference updated. Spec is shipped.

## Performance Notes

Sim-side only. The 16.7 ms Godot frame budget (`docs/bible_history/bible_2_00_combat.md:313`) is irrelevant. The sim 50 ms tick budget is unaffected — fairness evaluation is mission-start work.

Mission-start latency (the only relevant timing surface) is **expected to drop**, not rise:

- Current behavior: every mission retries fairness to exhaustion (`FAIRNESS_MAX_RETRIES`), then ships "best of N retries."
- Post-spec behavior: most missions pass fairness on first or second try.
- Net effect on mission-start time: faster.

Checkpoint G measures this directly. If average mission generation time regresses by > 15%, escalate — likely candidate is a fairness check made more expensive by D1's skip logic, but that's a diagnostic question.

## Forward References

- **New layout authoring** (post-this-spec). If Checkpoint D's audit recommends Class C on counterinsurgency layouts, the pool drops to 1 (or zero, in the worst case). Westley may then commission a new layout authored specifically for counterinsurgency. Out of scope here; flagged in OQ3 above and tracked in the Stage 11e stage close report.
- **Per-branch fairness parameterization** — post-Stage 13, when Branch 2 (modern) and Branch 3 (ancient) ship, the `FairnessTargetProfile` values become per-(branch, archetype). The structure built here is the consumer of those branch values; the bible's branch parameterization decision (deferred per `game_bible.md` v2.14) eventually fills in the per-branch axes.
- **Library hint system** (bible §"What Makes Each Mission Unique" item 3). Hints can bias layout selection via fairness profile adjustments (e.g., "this hint prefers high-vantage layouts" → temporarily tilts the vantage profile). Not in scope here; future content-pipeline spec.
- **Fairness evaluator algorithm changes**. The four metrics' formulas remain as Stage 7 specified. If future design work reveals a missing metric (e.g., "early-game proximity" — how close enemies are to the player's starting force), that's a separate spec; this one does not modify the metrics.
- **Learned fairness evaluator** (`docs/bible_history/bible_2_00_world.md:198` — *"A learned evaluator (neural network trained on playtested maps) can supplement or replace the algorithmic evaluator once sufficient playtest data exists. This is a post-launch evolution."*). Far-future. The algorithmic evaluator made real by this spec is the launch vehicle.

## Out of Scope (reaffirmed)

- **New layouts.** This spec edits the existing 8 in place.
- **Library hint system.**
- **Pre-mission map preview UI.**
- **Per-branch parameterization** (post-Stage 13).
- **Map seed wiring** (`stage_11b_map_variety_spec.md` — already shipped).
- **Layer visuals, fog of war, mid-mission HUD** (`stage_11c_*`, `stage_11d_*`).
- **Fairness algorithm changes beyond D1's zero-count scope-narrowing.**
- **Prototype `FairnessTargetProfile` edits.** If a prototype is unattainable, escalate.
- **`map_generator.py` retry logic.**
- **`sim_flavoring.py`** sim-state-driven gradient modifiers.
- **`layout_instantiator.py`** jitter logic, unless OQ2 reveals an ordering bug — escalate then.
- **Godot-side changes.** None. Pure sim.

## File Map (summary)

**Modify (sim):**
- `simulation/fairness_evaluator.py` — D1 zero-count scope-narrowing; add `metric_skipped` flag to `FairnessScore`.
- `simulation/archetype_filters.py` (or wherever `FairnessTargetProfile`s live) — pin the 6 non-prototype profiles per Westley's Checkpoint C approval; Class C filter narrowings per Checkpoint E approval.
- `simulation/layout_library.py` — strengthen hard-constraint validation per OQ1 outcome (conditional).
- `simulation/layout_library/layout_*.json` — per Checkpoint E-approved Class A and Class B edits. Each edited layout gets a `_meta.edit_summary` field.

**Modify (docs):**
- `docs/architecture.md` — `metric_skipped` flag and skip semantics in fairness evaluator.
- `docs/legacy/stage_specs/stage_11b_map_variety_spec.md` — closing forward-reference noting Stage 11e closure.
- `docs/bible_history/bible_2_00_world.md` — only if Checkpoint I surfaces design ambiguity.

**Create:**
- `tests/diag_fairness_pass_rate.py` — per-(layout, archetype) pass-rate harness used by Checkpoints A, B, C, F.
- `tuning_output/stage11e/` (gitignored) — checkpoint output directory:
  - `baseline_pass_rates.txt` (Checkpoint A)
  - `post_b_skip_audit.txt` (Checkpoint B)
  - `draft_profiles.md` (Checkpoint C, draft)
  - `post_c_pass_rates.txt` (Checkpoint C, after approval)
  - `layout_audit.md` (Checkpoint D)
  - `post_f_pass_rates.txt` (Checkpoint F)
  - `post_g_retry_and_timing.txt` (Checkpoint G)
  - `post_h_diversity.txt` (Checkpoint H)
  - `stage_close_report.md` (Checkpoint I)

**Bible:** likely no edits required; Checkpoint I confirms.

**Estimated size:** ~30 lines of Python (fairness evaluator skip logic + score shape change), ~50 lines of profile values (6 archetypes × 4 metrics with rationale comments), variable JSON edits across 8 layouts (audit-driven; could be 0 lines on layouts that don't need changes, could be ~20 zone-position fields per layout). The spec's largest deliverable by line count is the audit document and the per-archetype rationale write-ups, not code.

