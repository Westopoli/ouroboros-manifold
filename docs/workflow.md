# Workflow — TDD + Graphify + Caveman

How a session runs. Single source of truth for "what should Claude be doing right now."

This is the longer-form version of the **Workflow (active mode)** section in `CLAUDE.md`. Read CLAUDE.md first; this file fills in the how.

---

## The shape of a session

One terminal. One queue. One item at a time. Each item ends with a test deliverable Westley can run in Godot (or in pytest) and confirm.

```
read top of priority_queue.md
  → restate caveman-style + confirm with Westley
  → git checkout -b wn/<type>-<slug>
  → TDD (red → green → refactor)
  → implement minimal diff
  → git push + gh pr create (PR body has Godot test steps)
  → hand Westley the test deliverable
  → Westley confirms in Godot
  → merge
  → update ai_status.md + priority_queue.md
  → next item
```

If an item feels like two items, split it. Small tasks only.

---

## Pre-scope audit (do this before writing any spec)

Before scoping a BLOCKER or queue item — and absolutely before dispatching sub-agents — verify what already exists. The gate description in `priority_queue.md` is a player-facing problem statement, not a code inventory. Past stages often shipped partial infrastructure that the gate row doesn't mention.

For each item, sweep these surfaces:

1. `Grep` the keyword across `simulation/`, `autoload/`, `scenes/`, `build/`, `tests/`.
2. Check `docs/stage_specs/stage_*_spec*.md` for any mention of the feature as "complete" or "shipped".
3. **For anything a spec calls "complete": verify the production callsite exists**, not just the storage-layer function and not just test fixtures. A `write_*` that's only called by `test_*` is unwired infrastructure, not a working feature.
4. Read `MEMORY.md` pointers — prior chats may have noted partial state.

Produce a 5-line "what's built / what's wired / what's genuinely missing" before writing the spec. Re-scope the queue item to only the genuinely-missing piece. Past lesson (2026-05-16): nearly dispatched 2 sub-agents to build save infra that already existed in 6 files across Stages 10 + 12; only the converter + sim-side command handler were actually missing.

---

## Test deliverable format

Every PR includes — in the PR body — exactly this shape:

```
## Test deliverable

Scene: scenes/<path>/<scene>.tscn        (or: pytest path::test_name)

Steps:
1. <step>
2. <step>
3. <step>
4. <step>
5. <step>

Expected: <one sentence describing what you should see>

Fail-look-fors: <what would indicate the change is broken>
```

Constraints:
- ≤ 5 numbered steps
- testable in ≤ 5 minutes
- expected outcome is observable (visible on screen, printed by test, written to log)
- if a step requires Westley to "look closely" or "feel out" something, rewrite it so the pass/fail criteria is objective

---

## TDD discipline

**Sim code (Python):** pytest first.
1. Write a failing test that captures the bug or the new behavior.
2. Run it. Confirm it fails for the right reason (not import error, not fixture issue).
3. Implement the minimum to make it green.
4. Refactor only if needed; no opportunistic cleanup.
5. Re-run the full file (not just the new test) to catch regressions.

**Godot code (GDScript):** scene-level `test_*.gd` where practical.
- Model: `tests/test_input_router_selection.gd` + `tests/test_input_router_selection.tscn`.
- If a scene-level test isn't practical (e.g. camera feel, animation timing), document the manual checklist *as* the test in the PR body. The manual checklist is the test deliverable.

**Both:** the Testing Rigor Directive (below) is non-negotiable.

---

## Testing Rigor Directive

Sourced from the 2026-05-14 feedback. Pillar of the new workflow.

Every system needs **both** levels of coverage:

- **Isolation tests** — system under test alone, every other variable hard-fixtured or disabled. Proves the core mechanic works.
- **Integration tests** — same system in a realistic scene with pathing, AI, fog, vision, scale, other actors. Proves it survives contact with the rest of the game.

A bug in one doesn't imply a bug in the other. Both reveal different failure modes.

**Before asserting on any system's behavior:**

1. **List every actor + variable in the test scene** — movement, pathing, obstacle props, spawn timing, fog, vision, AI behavior.
2. **Verify the fixture works before asserting on the system.** Testing concavity? Prove the obstacle is actually blocking line-of-sight in a baseline shot first.
3. **An assertion that fails is only a system bug if the fixture is proven clean.** Otherwise it's a test bug — fix the test first.
4. **More tests can't hurt.** If a system has only one level of coverage, add the other.

Real failures this directive came from:
- Combat-balance test had two unit groups "in open space," but extra units with broken pathing wandered into the engagement zone. Claude flagged a balance bug. Wasn't a balance bug — was uncontrolled pathing contamination.
- Concavity test depended on obstacle props blocking line-of-sight. Props were broken (not blocking). Claude asserted concavity logic was buggy. Logic was fine — fixture was broken.

This wastes Westley's time, corrupts the priority queue with false bugs, and erodes trust in the test suite.

Stage 6 Checkpoint J (RPS) is governed by this directive when resumed — re-audit every L1–L4 fixture for uncontrolled variables AND add integration-level coverage if missing, before re-running balance assertions.

---

## Graphify first for code navigation

Before falling back to cold Grep/Read sweeps, try the graph:

```
/graphify query "where does tick resolution start"
/graphify path "TacticalEngine" "Region"
/graphify explain "InspectionState"
```

The graph lives in `graphify-out/`:
- `graph.json` — GraphRAG-ready, what `query` reads
- `graph.html` — interactive viz (open in browser)
- `GRAPH_REPORT.md` — plain-language summary, god nodes, surprising connections

**When to rebuild:**
- After a structural change: new module, big rename, file moves
- When queries start returning stale or wrong answers
- After completing a stage (the graph should reflect current truth)

Rebuild: invoke `/graphify` skill. AST extraction (deterministic) reruns immediately; semantic extraction reuses cache for unchanged files. Full rebuild takes ~5 min wall time via ~30 parallel sub-agents.

**God nodes are cosmetic.** Top-degree nodes (currently `main()`, `config`) reflect import-graph topology, not architectural centrality. They don't affect `query`/`path`/`explain` results — those are concept-driven BFS.

---

## Branching + PR conventions

**Branch names:** `wn/<type>-<slug>` where `type ∈ {bug, feat, refactor, chore, docs}`.

Examples:
- `wn/bug-unit-rotation`
- `wn/feat-camera-pan`
- `wn/refactor-region-tier`
- `wn/chore-graphify-rebuild`
- `wn/docs-stage12-spec`

**Plain git + gh CLI.** No Graphite. No stacked PRs.

**Always PR against `main`.** Solo merge OK after Westley confirms in Godot. Never commit directly to `main` — the git-guard hook will reject it.

**One PR per item.** If you find an unrelated fix mid-task, note it in the PR description as a follow-up; don't bundle.

---

## Caveman mode (default)

Caveman is on by default — terse, fragments OK, drop articles + filler. Switch back to normal for:
- Security warnings
- Destructive op confirmations
- Multi-step sequences where ordering matters and fragments risk misread
- Commit messages and PR text (write those normally)

Toggle: `/caveman lite | full | ultra | wenyan-full` or `stop caveman` / `normal mode`.

---

## Git guardrails

Enforced by `.claude/settings.json` (deny/ask/allow rules) and `.claude/hooks/git-guard.sh` (PreToolUse hook).

**Denied at the harness layer:**
- `git reset --hard`, `git clean -f/-d`, `git checkout -- <path>`, `git restore .`
- `git branch -D`, `git push --force`, `git push origin main`
- `git commit --amend`, `git commit --no-verify`
- `git rebase`
- Commits or pushes while HEAD is on `main` or `master`

**If a legit op gets blocked:** ask Westley before working around it. Don't bypass the hook.

---

## Escalation rules

An item that won't close cleanly:
- **One targeted iteration after a failed confirm.** If Westley reports the test deliverable failed, Claude diagnoses, makes one focused change, and asks for a re-test.
- **If the second iteration still fails:** stop. Write up findings, mark the item BLOCKED in `priority_queue.md`, and ask Westley what to do.
- **Two-session limit per item.** Anything that has burned >2 sessions gets a fresh look from Westley — usually de-prioritized or split.

Never silently expand scope. Never refactor code that wasn't part of the task. Never decide "this needs a bigger redesign" without Westley's sign-off.

---

## Sub-agents implement, never design

Sub-agents (Explore, general-purpose, Plan, claude-code-guide) execute against a spec the main agent (this terminal) has decided on. They cannot:
- Make architectural decisions
- Change API shapes
- Edit `docs/bible/**`, `docs/stage_specs/**`, `docs/launch_*`, `CLAUDE.md`
- Modify test thresholds
- Decide what should be tested

When a sub-agent hits ambiguity, it returns findings + a proposed change. The main agent decides.

---

## Updating state at end of each item

1. **`docs/ai_status.md`** — move the just-finished item from "Current Item" → "Completed log" with a one-line outcome.
2. **`docs/priority_queue.md`** — flip status of the finished item to `done`; promote the next item to `in-progress`.
3. **Memory** — if the session surfaced something durable (a new preference, a non-obvious decision, a stable reference), update the relevant memory file. Don't journal session details — only durable signal.

---

## Reference files

- `CLAUDE.md` — the rules of the road; read on every session start
- `docs/priority_queue.md` — what's next
- `docs/ai_status.md` — what's now (Current Item + Queue summary + Completed log + Escalations)
- `docs/bible/game_bible.md` — hub for design truth; spokes are `bible_*.md`
- `docs/stage_specs/` — implementation specs per stage; each lists which bible spokes to read
- `graphify-out/` — the knowledge graph (artifacts committed; intermediates gitignored)
