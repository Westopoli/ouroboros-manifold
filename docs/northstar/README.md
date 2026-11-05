# Northstar

The records behind the game's development: what is planned, what was decided, what was researched, what Westley has judged. **How the repo is run is `docs/method/README.md`**; where it disagrees with anything here, `docs/method/` wins. What the game is lives in `docs/bible/`.

The first method (Agora-driven development, September 2026: an unattended local-model loop builds against fenced tests, Claude designs and tests) is retired. Its stage pages, backlog and Track L plan are in `docs/legacy/agora_era/` and `docs/legacy/mvp/`.

| Path | What it is |
|---|---|
| `ROADMAP.md` | The order of plans: what is being built now and next, one row per plan |
| `ambiguity_register.md` | Open and answered design questions (`Q-` rows); an epic with an open flag is not built |
| `agile.md` | Epics, stories, rules, the ID scheme, the change protocol and the Definition of Ready |
| `PLAN.md` | The Agora-era plan. Only its "The Factory" section (the failure modes the harness guards against) is still cited; the stages are history |
| `regression.md`, `baselines/` | The three regression tiers and the captured baselines `scripts/integration_check.py` compares against |
| `spec_factory.md`, `spec_factory/` | The spec-factory pipeline and its prompts, schemas, transport schemas and allowlists, which scripts and tests read |
| `e2e/` | End-to-end definitions for epics E-02 to E-05, cited by the sim header and sources |
| `plans/` | Specs, the programme file and its lane table, the push ledger, `push/pieces.toml` file ownership, cascades, briefs, retros and workflow scripts. `plans/archive/` holds what the programme no longer points at |
| `research/` | Research briefs and results (lab, layout engine, landscape, economy, options, mockups, determinism) |
| `proving_ground/` | The probe README, scorecard and build ledger from before building began, with the evidence scripts and tests cite |
| `story_reviews/` | One picture per player-facing piece, the lane review tables, and `westley/`, the one folder of everything waiting on Westley |

Retired material is moved, not deleted: `docs/legacy/README.md` is the index, and `git log --follow` on a moved file shows its earlier life.
