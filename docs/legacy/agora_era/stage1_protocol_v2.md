# Stage 1 Protocol v2 — from batch 20 onward

Decided by Westley 2026-09-10 after 19 batches (322 rows, 83% straight KEEP, every catch already flagged by Claude). Replaces the batch protocol in `stage1_brief.md` §Method Step 2. Everything else in the brief stands: no bible edits, ledger schema, done criteria, vision_v2 as the check.

## What changes

1. **Claude verdicts every row itself.** Fill `verdict` for all rows using vision_v2, the code-reality summary, the pivot commit `b0a545b`, and prior verdicts.
2. **Batch = one whole spoke file.** Remaining order: `bible_combat.md` (from line 244), `bible_world.md`, `bible_missions.md`, `bible_chronicle.md`, `bible_antagonist.md`, `bible_ai_pipeline.md`, `bible_animation_strategy.md`, then `priority_queue.md` research-only list and the known-stale-claims sweep.
3. **Westley sees only flagged rows.** Present each batch as: (a) a table of flagged rows with the recommended verdict and a one-line reason; (b) one line listing the silent KEEP row ids (spot-checkable); (c) counts. Westley replies "approve" or overrides by row id. On approve, write every verdict to the ledger.
4. **Flag threshold is lowered.** A row is flagged when ANY of these holds:
   - conflicts with `vision_v2.md` or with an earlier verdict;
   - is post-pivot content (commit `b0a545b`, 2026-05-18) or describes pause-and-command, Lieutenant, single-player-only, or multi-era-as-research framing;
   - is implementation detail (file paths, tick rates, engine types, driver bugs, dataclasses);
   - code reality says absent or partial for a claim written as built;
   - can be read two ways;
   - names a number, cap, cadence, range, or percentage;
   - proposes era-specific mechanical behavior at launch (A-321 standing constraint);
   - Claude's confidence in KEEP is below near-certain.
   When in doubt, flag. A flagged row that Westley approves costs one word; a silent wrong KEEP costs a Stage 2 bug.
5. **Ambiguity flags go to the register.** Any flagged row where the verdict depends on a reading Westley must give becomes a `Q-` entry in `ambiguity_register.md` with candidate answers, and the row is marked `unsure` until answered.

## Blanket policies (record each once as a ledger row, then apply silently)

- **A-323 — Version-tag callouts.** Every "RESOLVED (vX.XX)", "RE-OPEN FLAG", "NEW SECTION", "as of", "previously" callout in any bible file: KILL the tag. The substantive text under it is audited as a normal claim. No per-tag rows.
- **A-324 — Implementation documentation in the bible.** Sections that document engine mechanics (sim/renderer split with tick rates, attack event protocol, MultiMesh batching, platform driver bugs, `tactical_bridge.gd` internals, config values, JSON shapes): REWRITE to the behavior-level design intent (e.g. "sim and renderer are strictly separated so a replay reproduces bit for bit"), and Stage 2 moves the mechanics to `docs/architecture.md`. Applies to every `impl-claim` row from here on. The C rewrite will need those mechanics documented; `docs/architecture.md` is where they live.

## Batch report template

```
## Batch N — <file> (lines a–b), rows A-xxx..A-yyy

Flagged (recommended verdict in bold):
| id | line | type | built | **verdict** | why flagged / note |
|---|---|---|---|---|---|

Silent KEEP: A-…, A-…, …  (n rows)
Counts: keep n · rewrite n · defer n · kill n · unsure n
Register: Q-… added (or none)
```
