# leaf-01 Assumptions

## A1 — symmetric test scope narrowed

Brief: forbid "symmetric blind" / "same polygon visible" polygon model in bible_combat.md.

"symmetric" appears at bible_combat.md line 521 in probe-steering paragraph ("two symmetric probe results") — legitimate use, unrelated to cover model.

Broad `assert "symmetric" not in combat_text` would be wrong forever. Narrowed test to check for "symmetric blind" and "observer-in-cover blind" — the exact polygon-cover phrases. Probe-steering "symmetric" untouched.

## A2 — cover_density field name kept in bible_world.md

Spec says rewrite cover_density definition. Field name `cover_density` retained as the gradient property tag (engine still uses it to drive cluster placement intensity). Only the definition text (what cover_density means at runtime) was replaced. No spec line contradicts this reading.
