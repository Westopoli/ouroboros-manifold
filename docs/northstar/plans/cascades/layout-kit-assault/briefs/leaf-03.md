---
leaf_id: leaf-03
spec_file: docs/northstar/plans/cascades/layout-kit-assault/spec.md
spec_lines: 31-91
test_files:
  - tests/layout/test_render.py
impl_files:
  - scripts/layout/render.py
contract_imports: []
do_not_edit:
  - csrc/ouroboros_sim.h
  - csrc/layout_kit.h
  - csrc/layout_internal.h
  - csrc/layout_engine.c
  - csrc/mission.c
  - Makefile
  - docs/**
  - tests/**
  - scenes/**
  - autoload/**
  - scripts/specfactory/**
  - simulation/**
  - csrc/layout_drafts.h
  - csrc/layout_kit.c
  - csrc/layout_kit_pieces.c
  - csrc/layout_kit_graph.c
  - csrc/tools/layout_dump.c
impl_line_budget: 600
test_assertion_budget: 40
test_owned_by: parent
wave: 1
---

## Task

Write the renderer `scripts/layout/render.py`: `render.py map <layout.json> <out.png>` and `render.py sheet <dir> <out.png>`, as acceptance criteria 8 to 10 in the spec lines in `spec_lines` say, reading the JSON schema `om-layout-1` given in the spec's JSON section (key names, `side` as "A"/"B"/"none", numbers as plain JSON numbers). Imports allowed: the Python standard library and Pillow only (`PIL`, version 12.3.0 is in the interpreter named in the Acceptance section). The tests use a hand-written fixture `tests/layout/fixtures/layout_hand.json` (already present, do not edit it); the renderer needs no C binary and never opens a window. Draw at 2x the output size and reduce with `Image.LANCZOS`; the scale is `DRAFT_PX_WU` (20 wu per pixel, read it as a module constant named `DRAFT_PX_WU`). Print a usage line to stderr and exit 2 on bad arguments; exit 1 from `sheet` when a seed file is missing, after writing the image with a labelled empty tile. Mirror the argument-handling shape of `scripts/skilllab/arena/page.py`.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/layout-kit-assault/worktrees/leaf-03/`, which is your working directory
and which the parent manages. Never run git. Nothing you do there is visible
to a sibling leaf or to the user's checkout.

Your working directory is the absolute worktree path the parent gives you; run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/layout/test_render.py -q -p no:cacheprovider` for your test files. Confirm RED. Edit `impl_file` in
place, at its normal path inside the worktree. Confirm GREEN. Stop.

Do not stage, copy, commit, or move anything. `/manager-mode` Phase 5 commits
your declared files from the worktree onto your branch, and Phase 6 merges
that commit into the integration branch only after every gate passes.

Earlier versions of this template asked the leaf to confirm GREEN *and* write
only to a staging directory. Those two instructions could not both be
satisfied: the test imports impl at its real path, so a leaf that never wrote
there was running its test against the unmodified file and could not reach
GREEN. The worktree removes the conflict rather than picking a side — inside
it, the real path IS yours.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a file not listed in `impl_files`. (Creating a
  file that IS listed is ordinary — a declared impl file often does not exist
  yet.)
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

If at any point during your run you had to **infer** something the brief did not specify (a default value, an error code, a representation choice, anything), write it to `docs/northstar/plans/cascades/layout-kit-assault/briefs/leaf-03.ASSUMPTIONS.md` before you finish. Format:

```markdown
## Assumptions made during leaf-03

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```

Do not bury inferences inside impl comments. The parent runs an assumption-sweep across all leaves before any admission — that sweep only sees the .ASSUMPTIONS.md files. An undocumented inference cannot be swept.

## Sibling-assumption read (do this before logging)

Before you append a new entry to your own `leaf-03.ASSUMPTIONS.md`, check whether a sibling already published a related inference:

1. List `docs/northstar/plans/cascades/layout-kit-assault/briefs/leaf-??.ASSUMPTIONS.md` (every leaf's file other than your own).
2. Grep for terms related to the thing you are about to infer (the type name, the field name, the behavior).
3. If a sibling already declared a value:
   - **Compatible** (your inference would match): adopt the sibling's value verbatim and add `— matches sibling leaf-XX` to your log line. Cascade stays coherent.
   - **Contradictory** (your inference would clash): do **not** log your value as a quiet assumption. Instead, write a question (see next section) or escalate to the parent. Two contradictory assumptions across siblings is exactly the drift the cascade exists to prevent.
4. If no sibling published anything related: continue as normal.

You may only **read** sibling ASSUMPTIONS files. You may never edit one. Cross-leaf writes break the file-ownership invariant.

## Question ledger (when you would otherwise infer silently)

If the brief is ambiguous on a point that materially shapes your impl (an API shape, a default value, a precedence rule), publish a question instead of guessing:

1. Write the question to `.swarm/layout-kit-assault/questions/leaf-03-Q<n>.md` with this shape:

   ```markdown
   ---
   leaf_id: leaf-03
   question_id: Q<n>
   status: open
   ---

   ## Question

   <one paragraph stating what is unspecified and why it matters for your impl>

   ## Best-guess inference (if parent does not answer)

   <the value you will proceed with if no answer arrives>
   ```

2. Proceed with your best-guess inference and record it in your ASSUMPTIONS file with the line:

   ```
   - **<thing>**: <inferred value> — source: best-guess, question leaf-03-Q<n>, unanswered: true
   ```

3. The parent may answer mid-run by writing `.swarm/layout-kit-assault/answers/leaf-03-Q<n>.md`:

   ```markdown
   ---
   leaf_id: leaf-03
   question_id: Q<n>
   ---

   decision: <value>

   ## Rationale

   <one paragraph>
   ```

   If the answer arrives **before** you finalize, replace your assumption entry's `unanswered: true` with `unanswered: false` and adjust your impl to match the decision.

4. **You may not delete a question file you wrote** — it is part of the audit trail. Status flips happen by the parent writing an answer.

If the question is not resolved by admission time, `/manager-mode` Phase 6.5 gate G3 blocks: either parent must answer or you must keep the `unanswered: true` tag (which makes the inference explicit and reviewable).

## Contract-proposal protocol (when a parent-owned file must change)

If satisfying your brief requires a change to a parent-owned file (a type contract field, a fixture, a config), do **not** edit it. G1 will reject your admission. Instead:

1. Write `.swarm/layout-kit-assault/proposals/leaf-03.md`:

   ```markdown
   ---
   leaf_id: leaf-03
   target_file: <path to parent-owned file>
   status: pending
   ---

   ## Proposed change

   <unified diff or precise description of the addition/edit>

   ## Why this is required

   <one paragraph citing brief spec_lines + what fails without the change>

   ## Fallback if rejected

   <how you will proceed — usually "re-spawn with revised brief">
   ```

2. Continue working on the parts of your impl that do not depend on the proposed change. The dependent parts stay incomplete; this is intentional — the test referencing the missing piece will stay RED and the parent will see that on admission attempt.

3. The parent will set status to `accepted` (after applying the diff to the target file), `rejected` (you re-plan), or `superseded` (a related leaf already covered it).

4. `/manager-mode` Phase 6.5 gate G4 blocks any leaf whose proposal is still `pending` at admission time, or whose proposal is marked `accepted` but the target file does not actually contain the change.

Never copy the parent-owned file into your impl as a workaround. Duplication is silent drift; the proposal protocol is how you make the need visible.
