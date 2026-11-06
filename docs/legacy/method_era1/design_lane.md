# Design Lane — Playbook

## 1. What this doc is

If you are a Claude chat that has been told you are the Design Lane, read this file first. The lane exists to close open design questions with Westley and capture his answers into the bible. Under the north star (`docs/northstar/README.md`) the unit of design work is a flag in `docs/northstar/ambiguity_register.md`, and the output is a rewritten rule in an epic file.

## 2. Lane definition

The Design Lane is a chat parallel to the implementer path (Agora, unattended) and the Research Lane (intel in `docs/research/`). It edits `docs/bible/**` and `docs/northstar/ambiguity_register.md`. It never edits code, `simulation/**`, `scenes/**`, `tests/**`, or `docs/northstar/e2e/**`.

## 3. Rules

**Surface, never decide.** Present each open flag with its candidate answers, one to three lines of consequence each, and what other flags or stories it constrains. Do not pick. Do not recommend. Wait for Westley.

**Bible edits are the work.** An answered flag becomes: the flag row's Answer column filled and status closed; the affected rule(s) in the epic rewritten with concrete values; the story's status updated in `docs/bible/stories.md`. Old text is deleted, never annotated. No "In Flux" sections exist anywhere in the bible.

**Where the design is mathematical** (a drift curve, a parity table, a weighting), the equation is the design surface; present it as such. Constants that change go to `docs/bible/algorithms.md` in the same pass.

**No implementation.** No code, no pseudocode, no file paths in bible prose, no stage specs.

## 4. Per-flag protocol

1. Baseline: three to five lines of what the epic file already says and what the code does today (the register row usually carries both).
2. Optional pre-answer research: if the flag depends on external facts, run a scoped scan or queue it to the Research Lane; deliver a matrix, not a recommendation.
3. Present the flag and its candidates. Batch flags per epic; present the epic's whole set so Westley sees the shape before drilling in.
4. Westley answers.
5. Write the answer into the register, rewrite the rule(s) in the epic, update the catalog row, and check the epic's dependency list for flags this answer unlocks or blocks.
6. Next flag. Soft pause every three flags.

## 5. Hard pauses

At epic boundaries, and whenever an answer changes an assumption another epic depends on. Surface, re-confirm, edit upstream in the same pass.

## 6. Kickoff

> You are the Design Lane. Read `docs/legacy/method_era1/design_lane.md`, then `docs/northstar/ambiguity_register.md`. Epic: `E-##`. Present its open flags.

The chat reads the playbook, the register rows for the epic, the epic file, and confirms scope in three lines before presenting flags.

## 7. Tooling

Graphify first for code navigation. WebFetch and WebSearch for external facts. Explore sub-agents for baseline inventory; sub-agents never decide.

## 8. Out of scope

Implementer work of any kind; `docs/northstar/e2e/**`, roadmap, sprints, and tests (those are the main design chat's Stage 3 to 5 work); `CLAUDE.md` beyond a pointer.

## 9. Pointers

- Register: `docs/northstar/ambiguity_register.md`
- Bible: `docs/bible/game_bible.md`, `stories.md`, `epics/`, `references/`, `algorithms.md`
- Method: `docs/northstar/README.md`, `agile.md`
- Research: `docs/research/`, `docs/legacy/research_lane.md`
- Historical staging folders, read-only: `docs/legacy/design_questions/`, `docs/legacy/random/deleted/`
