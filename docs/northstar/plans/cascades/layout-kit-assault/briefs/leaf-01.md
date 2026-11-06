---
leaf_id: leaf-01
spec_file: docs/northstar/plans/cascades/layout-kit-assault/spec.md
spec_lines: 27-98
test_files:
  - tests/csim/test_layout_kit_engine.py
  - tests/csim/test_layout_kit_header.py
impl_files:
  - csrc/layout_drafts.h
  - csrc/layout_kit.c
  - csrc/layout_kit_pieces.c
  - csrc/layout_kit_graph.c
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
  - scripts/layout/render.py
  - csrc/tools/layout_dump.c
impl_line_budget: 1500
test_assertion_budget: 40
test_owned_by: parent
wave: 1
growth_claim: quadratic-ok
---

## Task

Implement the layout kit engine in the four files in `impl_files`, behind the frozen header `csrc/layout_kit.h` (read it in full first; never edit it). `csrc/layout_kit.c` already exists as a sentinel (every entry point returns -1, NULL or 0): replace its body. Read the spec at the lines in `spec_lines` and follow its algorithm section, checks section, determinism section and the engine acceptance criteria 1 to 4 exactly. Entry points to implement, all declared in `csrc/layout_kit.h`: `om_lk_generate`, `om_lk_run_checks`, `om_lk_name`, `om_lk_draft_count`, `om_lk_draft_name`, `om_lk_draft_value`. Put every figure in `csrc/layout_drafts.h` as a `DRAFT_` macro and list the macros in one X-macro table named `LK_DRAFT_TABLE(X)`; the spec names the required drafts and their values; add the further drafts you need with a one-line reason each in your ASSUMPTIONS file. Put the splitmix64 constants as `LK_RNG_` macros beside the table. Assign the code to the files by responsibility: `layout_kit.c` holds the splitmix64 stream, the district grid and the driver (`om_lk_generate`, candidates, sides modes, `om_lk_name`, the draft accessors); `layout_kit_pieces.c` holds the six kit pieces and the request list; `layout_kit_graph.c` holds the route graph, Dijkstra, the fairness numbers and `om_lk_run_checks`. Share helpers between the files through declarations at the top of `layout_drafts.h` or through static-free internal functions prefixed `lk_`; keep every name prefixed `om_lk_` or `lk_` so nothing collides with `csrc/layout_engine.c`. Determinism rules (spec determinism paragraph) are mandatory: no `qsort`, no `atan2`, no `sin`/`cos`/`pow`/`exp`/`log`, only `sqrt fabs floor fmin fmax`; angles from `om_tn_sin_q16`/`om_tn_cos_q16` (declare them with a local prototype); no heap; the struct is zeroed first. Include `<stdint.h>` and `layout_kit.h` only; do not include `layout_internal.h`. The tests build `csrc/layout_kit*.c` and `csrc/terrain_noise.c` together with a parent-owned probe driver `tests/csim/layout_kit_probe.c`; do not edit the probe.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/layout-kit-assault/worktrees/leaf-01/`, which is your working directory
and which the parent manages. Never run git. Nothing you do there is visible
to a sibling leaf or to the user's checkout.

Your working directory is the absolute worktree path the parent gives you; run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/csim/test_layout_kit_engine.py tests/csim/test_layout_kit_header.py -q -p no:cacheprovider` for your test files. Confirm RED. Edit `impl_file` in
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

If at any point during your run you had to **infer** something the brief did not specify (a default value, an error code, a representation choice, anything), write it to `docs/northstar/plans/cascades/layout-kit-assault/briefs/leaf-01.ASSUMPTIONS.md` before you finish. Format:

```markdown
## Assumptions made during leaf-01

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```

Do not bury inferences inside impl comments. The parent runs an assumption-sweep across all leaves before any admission — that sweep only sees the .ASSUMPTIONS.md files. An undocumented inference cannot be swept.

## Sibling-assumption read (do this before logging)

Before you append a new entry to your own `leaf-01.ASSUMPTIONS.md`, check whether a sibling already published a related inference:

1. List `docs/northstar/plans/cascades/layout-kit-assault/briefs/leaf-??.ASSUMPTIONS.md` (every leaf's file other than your own).
2. Grep for terms related to the thing you are about to infer (the type name, the field name, the behavior).
3. If a sibling already declared a value:
   - **Compatible** (your inference would match): adopt the sibling's value verbatim and add `— matches sibling leaf-XX` to your log line. Cascade stays coherent.
   - **Contradictory** (your inference would clash): do **not** log your value as a quiet assumption. Instead, write a question (see next section) or escalate to the parent. Two contradictory assumptions across siblings is exactly the drift the cascade exists to prevent.
4. If no sibling published anything related: continue as normal.

You may only **read** sibling ASSUMPTIONS files. You may never edit one. Cross-leaf writes break the file-ownership invariant.

## Question ledger (when you would otherwise infer silently)

If the brief is ambiguous on a point that materially shapes your impl (an API shape, a default value, a precedence rule), publish a question instead of guessing:

1. Write the question to `.swarm/layout-kit-assault/questions/leaf-01-Q<n>.md` with this shape:

   ```markdown
   ---
   leaf_id: leaf-01
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
   - **<thing>**: <inferred value> — source: best-guess, question leaf-01-Q<n>, unanswered: true
   ```

3. The parent may answer mid-run by writing `.swarm/layout-kit-assault/answers/leaf-01-Q<n>.md`:

   ```markdown
   ---
   leaf_id: leaf-01
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

1. Write `.swarm/layout-kit-assault/proposals/leaf-01.md`:

   ```markdown
   ---
   leaf_id: leaf-01
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
