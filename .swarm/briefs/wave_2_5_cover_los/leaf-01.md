---
leaf_id: leaf-01
spec_file: docs/test_specs/cover_los_rework_spec.md
spec_lines: 60-65
test_file: simulation/test_cover_umbrella.py
impl_file: docs/bible/bible_world.md
impl_files:
  - docs/bible/bible_combat.md
contract_imports:
do_not_edit:
  - docs/test_specs/cover_los_rework_spec.md
  - docs/phase1_ship_plan.md
  - docs/priority_queue.md
  - simulation/test_cover_umbrella.py
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
  - simulation/map_generator.py
  - simulation/fog_of_war.py
  - simulation/damage.py
  - simulation/tactical_engine.py
  - simulation/cover_integration_fixture.py
  - simulation/test_cover_polygon.py
  - simulation/test_cover_polygon_placement.py
  - simulation/test_cover_visibility.py
  - simulation/test_cover_damage_gate.py
  - simulation/test_cover_ai_peek.py
  - simulation/test_cover_integration.py
  - docs/bible/game_bible.md
  - docs/bible/bible_simulation.md
  - docs/bible/bible_missions.md
  - docs/bible/bible_chronicle.md
  - docs/bible/bible_antagonist.md
  - docs/bible/bible_monetization.md
  - docs/bible/bible_ai_pipeline.md
impl_line_budget: 200
test_assertion_budget: 20
test_owned_by: parent
wave: 1
---

## Task

Rewrite bible cover semantics from gradient damage-multiplier to SC2-style polygon LOS-blocker per spec lines 60-65.

In `docs/bible/bible_world.md` lines 142-150: rewrite the `cover_density` paragraph. New language must state: cover is a polygon LOS-blocker; hides units inside from outside observers; same-polygon units see each other; cover does NOT reduce incoming damage; cover does NOT block movement. The phrase "reduces incoming damage" must be removed from the cover paragraph. The phrase "line of sight" (or "LOS" or "blocks sight" or "blocks vision" or "line-of-sight") must appear in the cover paragraph.

In `docs/bible/bible_combat.md` lines 419-425: strip `(1.0 - cover_density)` from the damage formula. New formula reads `damage × category_multiplier` with no cover term. Any executable expression form `(1.0 - cover...)` must not remain in non-comment text.

In `docs/bible/bible_combat.md` lines 439-441: replace the Cover paragraph with a new "Cover & Vision" subsection stating symmetric blind (defender in cover hidden from outside observers; observer in cover blind to outside; same-polygon units mutually visible), no proximity reveal, no fire-reveal (defender firing OUT stays hidden).

In `docs/bible/bible_combat.md` line 529: extend the obstacle LOS line to mention cover polygons as additional LOS-blockers, keeping cover-distinct-from-obstacles per `bible_world.md:142`.

No bible edits outside the two named files. No spec edits.

## Acceptance

Run `cd simulation && python3 -m pytest test_cover_umbrella.py::test_umbrella_e_bible_combat_no_damage_mult_in_formula test_cover_umbrella.py::test_umbrella_e_bible_world_cover_describes_los_block -v`. Confirm both tests pass GREEN. Commit the two bible files. Stop.

## Escalation triggers

Stop and report to the parent if:
- Bible line numbers shifted from the ranges given and the target paragraphs cannot be unambiguously located.
- Rewriting a paragraph requires editing a sibling bible file not listed in `impl_files`.
- The umbrella E-tests still fail after a faithful rewrite — surface the failing assertion text and the rewritten paragraph.
- A paragraph contains downstream cross-references to gradient-cover language elsewhere in the bible.

## Assumption log

If at any point during your run you had to infer something the brief did not specify (paragraph boundaries, formula notation, subsection heading style, anything), write it to `.swarm/briefs/wave_2_5_cover_los/leaf-01.ASSUMPTIONS.md` before you commit. Format:

```markdown
## Assumptions made during leaf-01

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```
