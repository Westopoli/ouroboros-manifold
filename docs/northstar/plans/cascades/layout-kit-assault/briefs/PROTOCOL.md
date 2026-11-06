# Leaf protocols (shared by every brief of this cascade)

Replace `leaf-NN` with your leaf id. `<cascade-slug>` is `layout-kit-assault`; `<briefs_dir>` is this directory.

## Assumption log

If at any point during your run you had to **infer** something the brief did not specify (a default value, an error code, a representation choice, anything), write it to `docs/northstar/plans/cascades/layout-kit-assault/briefs/leaf-NN.ASSUMPTIONS.md` before you finish. Format:

```markdown
## Assumptions made during leaf-NN

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```

Do not bury inferences inside impl comments. The parent runs an assumption-sweep across all leaves before any admission — that sweep only sees the .ASSUMPTIONS.md files. An undocumented inference cannot be swept.

## Sibling-assumption read (do this before logging)

Before you append a new entry to your own `leaf-NN.ASSUMPTIONS.md`, check whether a sibling already published a related inference:

1. List `docs/northstar/plans/cascades/layout-kit-assault/briefs/leaf-??.ASSUMPTIONS.md` (every leaf's file other than your own).
2. Grep for terms related to the thing you are about to infer (the type name, the field name, the behavior).
3. If a sibling already declared a value:
   - **Compatible** (your inference would match): adopt the sibling's value verbatim and add `— matches sibling leaf-XX` to your log line. Cascade stays coherent.
   - **Contradictory** (your inference would clash): do **not** log your value as a quiet assumption. Instead, write a question (see next section) or escalate to the parent. Two contradictory assumptions across siblings is exactly the drift the cascade exists to prevent.
4. If no sibling published anything related: continue as normal.

You may only **read** sibling ASSUMPTIONS files. You may never edit one. Cross-leaf writes break the file-ownership invariant.

## Question ledger (when you would otherwise infer silently)

If the brief is ambiguous on a point that materially shapes your impl (an API shape, a default value, a precedence rule), publish a question instead of guessing:

1. Write the question to `.swarm/layout-kit-assault/questions/leaf-NN-Q<n>.md` with this shape:

   ```markdown
   ---
   leaf_id: leaf-NN
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
   - **<thing>**: <inferred value> — source: best-guess, question leaf-NN-Q<n>, unanswered: true
   ```

3. The parent may answer mid-run by writing `.swarm/layout-kit-assault/answers/leaf-NN-Q<n>.md`:

   ```markdown
   ---
   leaf_id: leaf-NN
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

1. Write `.swarm/layout-kit-assault/proposals/leaf-NN.md`:

   ```markdown
   ---
   leaf_id: leaf-NN
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
