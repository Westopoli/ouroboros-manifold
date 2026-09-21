# PX-17 — Escalator fixes an upstream code defect alone (proving the factory)

Run 2026-09-21 (ouroboros `5f98cef`/`de26615`/`b3be0d2`, `scripts/specfactory/escalator_fix_probe.py`, `tests/specfactory/` 142 tests). Claim (Factory section, C4/C6, `docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md`): when a finding is that already-merged code violates a documented contract, the escalator can fix it alone, unattended, under a parent-patch fence, without Westley.

**Model note.** The plan named `gemini-3.7-flash-high` (rerun on `gemini-3.1-pro-high` for failures). At run time every `agy` quota group was exhausted -- confirmed on two genuinely different Google accounts (`westleyyarlott@gmail.com` and a second account, `agy2`), both reporting the same reset countdown to the minute, which means one shared backend quota behind Antigravity, not a per-account limit; Gemini's group resets in ~45h, the Claude/GPT group in ~4h, both empty at run time. Westley: swap to DeepSeek. The harness gained a second escalator path (`call_deepseek`/`call_escalator`, same `(payload, wall_seconds)` contract as the agy path) and this run used **`deepseek-v4-flash`** through Agora's own driver API (not agy), at a real, if small, dollar cost (`campaign: px17-px18-escalator-probe` in `~/Projects/agora/runs/costs.jsonl`). This is a real deviation from the plan's named model, authorized by Westley in the moment; it changes which model the claim is evidenced for, not the claim itself.

Result: **2 of 3 cases fixed on the first real attempt; 1 fence-violation** (a two-function sequential case that never got a clean shot at the actual logic bug because the model invented C symbol names in attempt 1 and over-scoped its reply in attempt 2).

| Case | Verdict | Attempts | Escalator calls (wall) | Equivalence to human fix |
|---|---|---|---|---|
| R7a (missing `#include <math.h>`) | **fixed-first-try** | 1 | 1 (1.1s) | Same fix, different position in the include block (appended at the end instead of inserted after `om_internal.h`) -- functionally identical, no behavioral difference. |
| R7d (3d ignores the forced-RNG queue) | **fixed-first-try** | 1 | 1 (6.5s) | **Byte-identical** to the human fix (`ecfcffe`) except one comment line the human fix added and DeepSeek didn't. Same forced-queue-first branch, same corrected two-draw PCG32 algorithm in the fallback branch. |
| R8 (`om_intent_inject` contract violation, two sequential fenced edits) | **fence-violation** | 2 | 3 (8.0s, 2.1s, 8.8s) | N/A -- never reached a gate on the real logic. |

## R8 in detail (the one that didn't land)

Attempt 1 built both functions (`om_step_decisions` then `om_intent_inject`, agent.c first per the fence) but failed the **build** gate: `om_intent_inject`'s reply invented symbol names that don't exist in this codebase -- `OM_ACTION_ATTACK` (real: `OM_ACT_ATTACK`), `OM_ATTACK_TELEGRAPH` (real: `OM_MODE_TELEGRAPH`), and `om_telegraph` fields `->tick`/`->faction_id` (the real struct has `declared_tick`/`attacker`, and the reply never set `target_idx`, `source_idx`, or `commit` at all). None of these names were given anywhere in the prompt -- the diagnosis and contract quote describe the *behavior* the fix needs, not the enum/struct definitions `om_intent_inject`'s body must reference, because the case fence is one function's body text plus the header's prose contract, not the full header. This is a real, structural gap in the "no repository access, everything is in the prompt" design (`om_intent_inject`'s own existing signature and the neighboring `om_step_telegraphs` code that already uses these exact names correctly were both *not* shown to the model, only the two fenced functions' own current bodies) -- plausible-sounding invented names are exactly the failure mode a fence that omits referenced types invites.

The build-error output (real compiler diagnostics naming the bad symbols) was fed back per the retry design. Attempt 2's `om_step_decisions` reply then violated the fence outright: it returned **both** `om_step_decisions` and `om_intent_inject` in a call fenced to `om_step_decisions` alone -- the model tried to fix everything at once in response to feedback that named a problem in the *other* function, rather than confining itself to its own turn. Scored `fence-violation` per the plan ("Reject any reply that names a function outside the fence"), terminal, no third attempt.

**Diagnosis completeness caveat, found by inspecting the reply, not assumed:** the real R8 fix (`30e86bb`) needed a *third* sub-fix beyond the two scope items this case's diagnosis gave -- `om_intent_inject` stamping the decision with `w->tick` instead of `w->tick + 1` (a bug the executor found empirically while implementing, not known at diagnosis time; DECISIONS.md's own text frames it as "found along the way"). This case's diagnosis faithfully reproduces what was known *before* implementation, matching how a real escalator would be briefed, but it means even a syntactically clean reply from DeepSeek would not have fully matched the header's contract without the model separately noticing the off-by-one during its own testing -- R8 is a harder case than R7a/R7d for a reason outside the fence-violation finding.

## Limits

- One model (`deepseek-v4-flash`), one run each (not the plan's 3-attempts-per-case-per-model with a second model on failure) -- quota exhaustion cut the comparison short; R8's real fix quality against this model is unknown, not confirmed-impossible.
- Wall time is dominated by harness overhead (git worktree checkout, `make`, the whole-suite regression gate), not the model call: the three model calls that succeeded ranged 1.1-12.5s; per-case wall time (build+test+regression) ran 40-90s.
- `assertions_preserved`/`red_at_stub`/`two_agent_confound` gates (PX-18's stricter checks) don't apply to PX-17; R7a and R7d were graded on build+target-tests+whole-suite-no-worse only, per the plan.
- R7a's target-tests mode is "compiles and collects", not "passes" -- the fix is a build prerequisite, not new logic, so a green R-036/R-037 test suite was never the bar there.

## Design consequences

(left for the design lane)
