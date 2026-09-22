# PX-10 — Content card: pack validator and the fenced content diff (proving the factory)

Run 2026-09-22 (`scripts/specfactory/pack_validate.py`, `tests/specfactory/test_pack_validate.py` — 15 tests, one new `card_lint.py` check with 3 tests, specfactory suite 316/317 green — the one red is a pre-existing, unrelated `alg_constants.py` lint finding against `csrc/sim.c` from concurrent work elsewhere in this checkout). Claim ("Content and multiplayer are not special cases", B.8 change 3): a content card is a gate over a pack directory whose acceptance is validators plus a fenced content diff; a broken pack fails, a clean pack passes, and the fence blocks the worker from editing the validator.

Result: **pass on every stated control**.

## Facts found before building

No pack validator existed anywhere in the tree (`scripts/`, `tools/`, `simulation/library/`, `autoload/era_theme_resolver.gd` all came back empty). `assets/eras/test_era/manifest.json` and `assets/eras/settled_reach/manifest.json` agree on eight top-level keys — `era_id, era_display_name, era_accent_color, units, structures, environment, materials, faction_colors` — so those became the required set. No banned-word list existed in code, only prose (E-09 `R-071-02`, E-21 `R-153-02`). `card_lint.py` had no check on `allowed_files` paths at all before this run — the brief asked whether it was absent, and it was.

## Build

`scripts/specfactory/pack_validate.py <pack_dir>` checks: all eight required manifest keys present (`R-146-03`, missing one named); every referenced `scene` path exists relative to the pack; `R-145-01` applied to content — no unit id may contain the pack's own `era_id`; `era_display_name` and any `naming_pools` entry against `docs/northstar/spec_factory/banned_words.txt` (ten terms: meta — `placeholder, prototype, sandbox, debug, todo`; IP — `jedi, klingon, wookiee, hobbit, tardis`). A top-level key outside the required eight (e.g. a future `weather` class) is optional and its absence is never a finding. `--diff-mechanical <pack> <reference>` compares two packs' gameplay-relevant shape (unit/structure/environment ids, categories, squad counts, tier counts, material treatments, faction-color count) and exits 1 with a unified diff on any mismatch — the `R-146-02` fence a content card's acceptance runs alongside `pack_validate.py` itself.

`card_lint.py` gained one check, `FORBIDDEN_ALLOWED_PATH`: any `allowed_files` entry starting with `scripts/specfactory/` or `tests/` is a FAIL, named. It runs for every card kind, not just `content` — a build card has the identical reason to never touch the gate it is measured against or the tests that are its own spec.

## Result table

| Control | Fixture | Outcome |
|---|---|---|
| Missing required key | `pack_broken` (`era_accent_color` absent) | `MISSING_REQUIRED_KEY era_accent_color` named |
| Banned word in display name | `pack_broken` (`era_display_name: "Prototype Frontier"`) | `BANNED_WORD 'prototype'` named |
| Unit id containing era id | `pack_broken` (`era_id: "brokenera"`, unit `brokenera_vanguard`) | `ERA_ID_IN_UNIT_ID` named |
| All three together | `pack_broken` (one pack, three defects, one run) | all three named, exit 1 |
| Clean pack | `pack_clean` (copy of `test_era`, `era_id`/`era_display_name` renamed) | `PACK OK`, exit 0 |
| Optional class absent | `pack_clean` (no `weather` key, same as every shipped pack today) | accepted silently, no finding |
| Real shipped packs, sanity | `assets/eras/test_era`, `assets/eras/settled_reach` | both `PACK OK` (not part of the fenced test suite, checked by hand) |
| Content card, real shape | `evidence/px10/px10-content-card.md` (`kind: content`, never queued) | `card_lint.py`: `LINT OK`, exit 0 |
| Validator-editing card | `evidence/px10/px10-validator-edit-card.md` (`allowed_files` includes `pack_validate.py`) | `card_lint.py`: `FORBIDDEN_ALLOWED_PATH`, exit 1 |

## Limits, stated plainly

1. `px10-content-card.md`'s content diff points `--diff-mechanical` at `pack_clean` against itself — this proving-ground card has no second, genuinely different pack to build, so the diff is a self-check proving the mechanism runs and holds, not a proof that two differently-dressed eras stay mechanically identical under drift. A real content card built from this template would point the second argument at the pack it must match.
2. The banned-word scan only reaches `era_display_name` and `naming_pools` entries, because those are the only free-text fields the current manifest schema defines; a pack format that later adds ability names, structure names, or chronicle fragment text needs the same scan wired to those fields explicitly, not inherited automatically.
3. `MISSING_SCENE` checks only that the referenced file exists on disk, not that it parses as a valid Godot scene or glTF asset.
4. A pack directory with no `manifest.json` at all surfaces as a named finding (`MISSING_MANIFEST`, exit 1), not a usage error (exit 2) — deliberate, so a malformed pack still gets an entry named rather than a bare crash; only a nonexistent pack directory itself is exit 2.
5. `FORBIDDEN_ALLOWED_PATH` is a plain path-prefix check on the `allowed_files` string; it does not resolve `..` or symlinks, so a card could still evade it with a relative path that reaches the same file by another route. Not exercised here.

## Design consequences
