# Proposal: task matching, agent instruction files, the 30B test writer, and what the C4 model is for

Status: draft for Westley's decision, 2026-09-28. Nothing here is in force until he approves it; approved parts move into `CLAUDE.md`, `AGENTS.md`, `.claude/agents/` and `.claude/settings.json`, and this file is then deleted (rewrite, never append).

## 1. The task-matching rule

Tiers are named by role, not by model, so the model behind a tier can change without rewriting every rule that mentions it.

| Tier | Model today | Model after the subscription change | Work that belongs here |
|---|---|---|---|
| Architect | Fable (the main chat) | Fable | Architecture, planning, rulings and arbitration, decomposing work into briefs, diagnosing abstract or cross-cutting problems, anything where a wrong call is expensive to unwind. |
| Engineer | Sonnet 5 (`model: sonnet`) | Sonnet 5, or the 30B for test writing once it passes the pilot in section 4 | Test generation and test-defect fixes, git maintenance (merge clerks, rebuild-by-copy, worktree cleanup, ledger rows), audits and reviews, doc drafting against a spec (the C4 draft), inventories. |
| Doer | Sonnet 4.6 (`sonnet46-doer`) | Local 30B through Agora | Coding against a written spec, single-file or mechanical edits, landing a prepared branch, copying files. |

Rules that go with it:
- A task that mixes tiers is split: the judgement part goes up a tier, the mechanical part stays down.
- The Architect never spawns an Architect-tier subagent unless Westley asks for one.
- Two changes from today's habits follow from the table: merge clerks and test-fix doers move from Sonnet 4.6 to Sonnet 5 (they are git maintenance and test work), and pure coding leaves stay on Sonnet 4.6.

### The swap to the local 30B

Claude Code subagents can only run Anthropic models; a local model cannot back an Agent call. So "the Doer tier runs on the 30B" means Doer work stops being an Agent call and becomes an Agora card (`~/Projects/agora/queue/`), built by the 30B under Agora's existing gates, with the result landing through the same merge queue. The switch is one line in `CLAUDE.md`:

```
DOER_BACKEND = sonnet46      # or: agora-30b
TEST_WRITER  = sonnet5       # or: agora-30b (only after the section 4 pilot passes)
```

When `DOER_BACKEND = agora-30b`, the Architect writes Doer briefs as Agora cards instead of Agent prompts. The brief shape stays the same (one deliverable, exact files, verification commands, report shape), which is also what the card format already asks for.

## 2. How it is documented and enforced

Documented in three places, each with one job:
- `CLAUDE.md` gets a short "Task matching" section: the table above, the two switches, and the split rule. About fifteen lines.
- `.claude/agents/` gets one definition per spawnable tier: `engineer.md` (`model: sonnet`) and `doer.md` (`model: claude-sonnet-4-6`). `sonnet46-doer.md` stays as an alias during the transition so running chats do not break. Architect has no file: it is the main chat.
- The two switches are read by the hook below, so the rule and the enforcement cannot drift apart.

Enforced by a PreToolUse hook on the `Agent` tool (`.claude/hooks/tier-guard.sh`, beside `git-guard.sh`):
- Deny a spawn whose model resolves to the main chat's model (no `model`, no tier definition), because that silently bills Architect rates. The denial reason names the tiers.
- Deny `model: fable` or `opus` unless the prompt carries `TIER-OVERRIDE: <reason>` (for the cases Westley asks for).
- Allow the read-only built-ins (`Explore`, `claude-code-guide`, `statusline-setup`) and forks.
- Append every allowed spawn (time, tier, model, description) to `~/.claude/tier-log.jsonl`, so a weekly Engineer-tier clerk can report how tokens split across tiers.

A cheaper safety net alongside the hook: set `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6` in the project settings, so any spawn that slips past the hook falls to the Doer tier instead of Fable.

## 3. AGENTS.md

What is true today:
- `AGENTS.md` exists in the repo but is written only for Antigravity (agy).
- Per the Claude Code docs (checked 2026-09-28; worth a one-line confirmation on this machine), Claude Code reads `CLAUDE.md` and skips `AGENTS.md` when a `CLAUDE.md` exists, unless configured to read both; nested `CLAUDE.md` files in subdirectories load on demand, when a file in that directory is read.
- Agora's local models read neither file. `scripts/build.py` feeds them a per-card rules file, `extra_context_files`, and the `prompts/worker-build-*.md` system prompts.

Proposal:
1. Make `AGENTS.md` the tool-neutral rulebook: the rules every agent needs regardless of vendor (determinism contract, no runtime API calls, no IP, tests are fenced and name their R-id, never edit the bible, ambiguity becomes a question, scope discipline, no stink). `CLAUDE.md` imports it with `@AGENTS.md` and keeps only Claude-specific material (tiers, memory, cross-chat messaging, orchestration, output style). One source, no duplicated rules to drift.
2. Add nested rule files per area, loaded only when an agent works there: `csrc/`, `csrc/pipe/`, `tests/`, `scenes/`. Each carries the local rules that today sit in `CLAUDE.md` or in briefs (for `csrc/`: constants lint, libm lint, OM_BUG ranges, header changes go to M0; for `tests/`: R-id naming, positive controls, fixture rules; for `scenes/`: the qa_state contract). For Claude, each area gets a `CLAUDE.md` that imports its sibling `AGENTS.md`, so it loads on demand.
3. Have Agora include the target directory's `AGENTS.md` in the card context (a small change in `build.py` beside `rules_file`). This is the biggest win for the 30B: the same local rules Claude sees, instead of values it invents.
4. Trim `CLAUDE.md`. It is about 150 lines and is loaded into every turn and every subagent. The simulation file map, the Python-era protected-files list and the long testing sections move into the nested files or into `docs/`. A reasonable target is under 70 lines at the root.

## 4. The 30B test writer (optional, swappable)

The aim is a harness strict enough that the 30B can write tests in the manager-mode fashion, with Sonnet 5 as the fallback, switched by `TEST_WRITER`.

Input is a test card generated from the epic: the story's rules (Given/When/Then), its inputs and invariants, the epic's scale section, the component's slice of the C4 registry (section 5), the existing fixtures, and a template.

Every rule must be covered in these categories, each marked on the test (`@pytest.mark.category("boundary")` or the equivalent naming):
- the plain case, and every Given or When branch the rule states;
- boundaries: zero, one, the stated limits, one past each;
- rejected input, where the rule defines one;
- determinism: the same seed gives the same trace;
- scale and volume, using the epic's stated numbers exactly;
- an isolation test and an integration test;
- a positive control: red against a stub, for the right reason.

Gates, mostly existing tools:
- collection;
- `red_check.py` (red at stub, on an assertion, never on a TypeError);
- `control_liveness.py`;
- `fixture_defects.py`;
- `undertest_check.py` (mutation kill rate);
- a new `test_coverage_lint.py` (every R-id has a test in every required category, and scale tests cite the epic's number).

A Sonnet 5 reviewer samples a share of accepted files, and every miss it finds becomes a new lint rule, so the gates get stricter over time instead of the review getting bigger.

Before trusting it: run both writers on three stories that already have good tests, and compare gate pass rate, mutation kill rate and reviewer findings. The switch flips only if the 30B clears a bar Westley sets.

## 5. Is the C4 model worth it

Diagrams for people have little value here: there is one developer and nothing is being shared. The value is for agents, and only if the model is a compact, checkable registry rather than prose.

What agents would get from a registry:
- **Scope fences.** A card names its component; the component row gives its files, owning piece, allowed dependencies and entry points. That is the context a Doer or the 30B needs, and the fence it must stay inside.
- **Context packs.** The 30B receives its component's slice instead of the whole header, which is the failure class Agora already hit (invented member names).
- **Wiring checks.** A status column with "tested but unwired", backed by a reachability lint (every public symbol that has tests is reached from a tick step or a pipe handler, or is marked test-only), would have caught the reinforcement and structure-production gap days before a person found it.
- **Change impact.** When a boundary moves, the registry row changes in the same branch, and the merge gate can check that.

Recommendation: keep C4, but make it data first. A `docs/legacy/architecture_c4/mvp/components.toml` (or new columns on `pieces.toml` and `symbol_modules.toml`, which already hold half of it) is the source; the Markdown pages and Mermaid diagrams are generated from it. Two lints go in the merge gate: every `csrc` module and pipe command appears in the registry, and the reachability lint above. If the audit of the current draft shows it mostly restates `pieces.toml`, fold it into that file and drop the separate pages.

## 6. Decisions for Westley

1. The tier table, including moving clerks and test doers to Sonnet 5 (a small cost increase for better judgement on git and tests).
2. The hook: deny (as proposed) or warn only.
3. The `AGENTS.md` split and the `CLAUDE.md` trim (both edit `CLAUDE.md`, which is yours to approve).
4. C4 as a registry with generated pages, decided after the audit of the current draft.
5. When to run the 30B test-writer pilot: before the subscription change, so there is data when it happens.

Suggested order once approved: tiers, agent files and hook first (small, immediate savings); then the `AGENTS.md` split; then the C4 registry and its two lints, after the audit; then the test-writer pilot.
