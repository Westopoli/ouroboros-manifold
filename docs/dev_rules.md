# Ouroboros Manifold — Development Rules

> **This document governs how the project is built.** The game bible (`game_bible.md`) says what to build. This document says how to build it, how to organize the work, and how to avoid the mistakes that killed the last iteration. Every Claude session — Code or chat — reads this file and follows these rules.
>
> **Last updated:** April 6, 2026

---

## Context

This is a solo developer project. Westley designs in Claude.ai (brainstorming, design decisions, documentation) and implements in Claude Code (writing and modifying code). The game bible is the single source of truth for design. This document is the single source of truth for process.

The project is well into implementation. Stages 1–4 (simulation foundation, event chains, faction agents, diplomacy/technology, civilizational lifecycle) are complete. Stage 5 (chronicle pipeline, coherence ledger, library builder, naming system) and Stage 6 (headless tactical simulation engine) are in progress or recently completed. The implementation stage roadmap is maintained in `game_bible.md` (see "Implementation Stage Roadmap" section). Dev rules does not duplicate the stage list — the bible is authoritative for what each stage contains and their ordering.

The previous iteration of this game suffered from:
- Code piling up without being proven, leading to 15+ orphaned files
- Systems growing tendrils into each other before they were validated, making removal surgical
- Design docs proliferating across many files with conflicting information
- Implementation racing ahead of design, requiring costly rework

These rules exist to prevent all of that.

---

## The Five Development Principles

### 1. Isolation First

Every new system starts as a standalone module with a clear API boundary. It reads inputs, produces outputs, and touches nothing else. If you delete the file, nothing breaks except the thing that calls it.

**In practice:**
- New systems live in their own file(s) with no imports from other in-progress systems
- Communication between systems happens through documented data structures (dicts, JSON schemas), not deep function calls into each other's internals
- A system should be testable in complete isolation — it should run with mock inputs and produce verifiable outputs without needing the rest of the project

### 2. Prove Before Integrating

Each system gets a "prove it" phase where it runs in isolation — a test script, console output, or minimal UI. Only after it's proven does it get wired into the larger system. Integration is a separate, deliberate step.

**In practice:**
- Every system has a standalone test or demo that proves it works before it touches anything else
- "Proven" means: Westley has seen it run, reviewed the output, and said "yes, this works"
- Integration happens in a dedicated step, not as a side effect of building the next thing
- If a system can't be proven in isolation, it's scoped wrong — break it down further

### 3. Thin Interfaces

Systems communicate through minimal, documented data structures. If System A needs something from System B, they share a data shape, not function calls deep into each other's internals.

**In practice:**
- Every system documents its input shape and output shape at the top of its primary file
- When two systems need to talk, define the interface contract first, then implement both sides
- If changing System A's internals would break System B, the interface is too thick — refactor
- Data structures should be plain dicts or simple dataclasses, not complex object graphs

### 4. Kill Switch Architecture

Every integrated system should be disableable with a single flag or config toggle. If you turn off the mission generator, the simulation still runs. If you turn off combat, missions still generate briefs. Nothing is load-bearing until Westley explicitly decides it is.

**In practice:**
- Every integration point has a bypass: `if config.ENABLE_MISSIONS: ...` else the system continues without it
- Default state for any new system is OFF until proven and explicitly enabled
- Disabling a system should never crash the project or produce errors — it should gracefully degrade to the behavior that existed before the system was added
- This means integration is always additive, never structural

### 5. Stage Gates

Each stage has a clear "done" condition. You don't move to the next stage until the current one is proven and Westley is happy with it. If he's NOT happy, the current stage's code can be killed cleanly because of principles 1–4.

**In practice:**
- Each stage spec defines a "Prove it" condition — a concrete, observable test that confirms the stage works
- Moving to the next stage requires explicit confirmation from Westley
- If a stage is abandoned, removing its code should take minutes, not hours
- No "partial stage" work that spans multiple stages — finish one, gate it, then start the next

---

## File and Project Organization

### Project Structure Philosophy

- **Flat over nested.** Don't create deep directory hierarchies speculatively. Start flat, add structure only when the number of files in a directory makes it unreadable.
- **One system, one file (to start).** A new system is one Python file or one GDScript file. Only split into multiple files when the single file becomes genuinely unmanageable (300+ lines with clearly separable concerns).
- **Tests live next to code.** Test files sit alongside the files they test, prefixed with `test_`. Not in a separate test directory.
- **Dead code gets deleted, not commented.** If something is no longer used, remove it. Git history preserves it if you ever need it back. Commented-out blocks are clutter that confuses future Claude sessions.

### Documentation Structure

```
docs/
├── game_bible.md          ← THE design document. Single source of truth.
├── bible_*.md             ← Spoke files for major systems (simulation, combat, etc.)
├── dev_rules.md            ← THIS file. How the project is built.
├── stage_specs/            ← One spec per stage, created when that stage begins.
│   ├── stage_1_spec.md
│   ├── stage_2_spec.md
│   └── ...
└── continuation_context.md ← Temporary. For bridging brainstorming sessions.
```

- **game_bible.md + bible_*.md** — what to build. Hub-and-spoke architecture. Conceptual only. No code, no file paths, no implementation details.
- **dev_rules.md** — how to build it. Process, principles, organizational rules.
- **stage_specs/** — implementation details for each stage. Created one at a time, as each stage begins. Each spec is self-contained: what to build, input/output shapes, done condition, files to create.
- **continuation_context.md** — ephemeral. Exists only to bridge a brainstorming session across Claude.ai conversations. Gets deleted once its decisions are merged into the bible.

### Rules for Documentation

1. **Three docs maximum govern the project at any time:** the bible (hub + relevant spokes), this file, and the current stage spec. That's it.
2. **No other design docs.** If it's a design decision, it goes in the bible. If it's an implementation detail, it goes in the stage spec. If it's a process rule, it goes here. There is no fourth category.
3. **Stage specs are disposable.** Once a stage is complete and integrated, its spec is historical reference only. It should not be consulted for how the system works — the code is the source of truth for implementation, the bible is the source of truth for design.
4. **Never duplicate bible content in stage specs.** Stage specs reference the bible ("See bible_combat.md, Unit Roster section") rather than restating design decisions. This prevents conflicting information.

---

## Stage Spec Format

Every stage spec follows this structure:

```markdown
# Stage [N] — [Name]

## Goal
One sentence: what this stage proves.

## Bible References
Which spoke files and sections to read before implementing.

## Context
What previous stages this builds on.

## What to Build
Concrete list of files to create, with purpose and scope for each.

## Input/Output Shapes
The data structures this stage's systems consume and produce.
Written as example dicts/JSON — not abstract descriptions.

## Integration Points
How this stage connects to previous stages (if at all).
What config flags enable/disable it.

## Done Condition
A concrete, observable test. "Run X, see Y, confirm Z."
Westley signs off on this before the next stage begins.

## Files Created
Filled in after implementation. Lists every file this stage produced.
Used for auditing — if a file isn't on this list, it shouldn't exist.
```

---
### Performance regression discipline

Algorithm replacements must include a performance budget check at the
checkpoint where they land. A test that verifies correctness without
verifying cost is incomplete.

When a checkpoint replaces a subsystem's algorithm (movement, targeting,
pathfinding, damage resolution, agent decision, etc.), the checkpoint's
test set must include at least one scenario that:

1. Exercises the replaced subsystem at representative load (not a toy case).
2. Asserts a hard millisecond ceiling on that subsystem's per-tick cost.
3. Fails the checkpoint if the ceiling is exceeded.

The ceiling is set from the pre-replacement baseline measured on the same
scenario, with a documented margin. A 2x regression is a budget failure
even if all correctness tests pass. Performance is a correctness property
of this simulation — the deterministic replay system, batch sim, and
chronicle distillation all assume real-time-or-faster execution, and a
subsystem that silently runs 10x slower breaks downstream pipelines as
surely as a subsystem that returns wrong values.

This rule exists because Stage 6J replaced steering with ORCA/RVO under
a correctness-only test and the resulting ~100x regression lived in the
codebase across multiple subsequent checkpoints before being detected.

### Do not run profiling tools inside the timing hot path

`tracemalloc`, `cProfile`, `memory_profiler`, and similar instrumentation
tools intercept every allocation or call. Running them across the timed
tick loop inflates measurements by 3–10× and makes performance tests
meaningless. This was discovered in Stage 6K: `tracemalloc.start()` before
the 3000-tick loop caused the benchmark to report 55ms/tick when the real
cost was 11ms/tick — a 5× overcount that appeared as a budget failure.

**Rule:** memory or call profiling snapshots must be taken *outside* the
timed section (before the loop begins or after it ends). Never wrap the
hot path in a profiler to get a single number — run the timed loop clean,
then run a separate profiling pass if needed.
---

## Rules for Claude Code Sessions

### Starting a Session

1. **Read the game bible hub first.** Every Claude Code session begins by reading `game_bible.md` to understand what the game is.
2. **Read this file second.** Understand the development principles.
3. **Read the current stage spec third.** This tells you what to build right now.
4. **Read the spoke files listed in the stage spec's Bible References.** Only the spokes specified — not all of them.
5. **Don't read old stage specs or old design docs.** They're historical. The bible and current spec are all you need.

### During a Session

1. **Build only what the current stage spec asks for.** Do not anticipate future stages. Do not add "hooks" for systems that don't exist yet. Do not build infrastructure "we'll need later." Build what's specified, prove it works, stop.
2. **One system at a time.** Implement, test, confirm. Don't start the next system until the current one is proven.
3. **Ask before integrating.** If a system needs to touch another system's code, stop and confirm with Westley. Integration is a deliberate decision, not a side effect.
4. **No dead code.** If you write something and it turns out not to be needed, delete it. Don't leave it commented out. Don't leave "utility functions" that nothing calls.
5. **Document interfaces, not internals.** Put docstrings on public functions describing what they take and return. Don't over-comment internal logic — the code should be readable on its own.
6. **Config values in one place.** All tuning parameters live in `config.py` (or equivalent). Never hardcode a value that Westley might want to adjust.
7. **Checkpoint output must be self-verifying.** Every data structure tested in a checkpoint must have its key properties printed in the output — not just asserted silently. If a checkpoint tests edge types, print edge types. If it tests field ranges, print the ranges alongside the values. Westley reviews checkpoints by reading terminal output, not by reading test code. If he can't verify a property from the printed output alone, the checkpoint is incomplete.
8. **Baby steps.** Each change should be small enough to verify independently. If a task feels like it needs 200+ lines of changes across multiple files, break it into smaller steps and confirm between each one.

### Mandatory Checkpoints — STOP AND WAIT

> **THIS IS THE MOST IMPORTANT RULE IN THIS DOCUMENT.** The entire development methodology depends on Westley seeing and approving output at every step. Claude Code cannot self-verify. Claude Code's judgment about whether output "looks right" is not reliable enough — it has been wrong. Only Westley's eyes count.

**After completing each step in the stage spec:**

1. **Run the prove-it test.** Execute the test script and capture the output.
2. **Show the output to Westley.** Print it, display it, make it visible. Do not summarize it — show the actual numbers.
3. **STOP. Do not continue to the next step.** Wait for Westley to review the output and say "yes, this works" or "no, this is wrong."
4. **Do not evaluate the output yourself and decide to proceed.** You are not the judge of whether the simulation's behavior is correct. Westley is. Your job is to build, test, and present. His job is to evaluate and approve.
5. **Do not batch multiple steps.** Each step gets its own checkpoint. Do not implement steps 2 and 3 and then show output for both — implement step 2, show output, wait for approval, then implement step 3.

**What counts as a step:** Every numbered step in the stage spec (A1, A2, B1, etc.) is a checkpoint. Every substep that produces testable output is a checkpoint. If you're unsure whether something needs a checkpoint, it does.

**What "STOP" means:** Stop generating code. Stop running tests. Stop planning the next step. Present the output and wait for input. The next message from Westley determines what happens next — proceed, adjust, or redo.

**Why this exists:** This is a solo developer project. The developer cannot review code and output if Claude Code has already moved three steps past the problem. The incremental build methodology only works if every increment is verified before the next one begins. Skipping checkpoints turns "small provable steps" into "a big pile of unverified changes" — which is exactly what the dev rules exist to prevent.

### When Something Doesn't Work

1. **Don't pile fixes on top of broken code.** If a system isn't working, understand why before adding more code. Adding code to work around a bug creates the exact tangle this process is designed to prevent.
2. **It's okay to delete and restart a system.** The isolation principles mean this is cheap. If a module isn't working after reasonable effort, delete it and rebuild with a clearer understanding. This is faster than debugging a tangled mess.
3. **Escalate design questions.** If implementation reveals a design problem — something the bible didn't account for, or two design decisions that conflict — stop implementing and flag it. Westley will take it to a Claude.ai brainstorming session. Don't make design decisions in implementation sessions.

---

## Rules for Claude.ai Brainstorming Sessions

### Purpose
Claude.ai sessions are for design exploration, decision-making, and documentation. They are NOT for writing code.

### Starting a Session
1. Upload `game_bible.md` and relevant spoke files for the topic being discussed.
2. Upload `continuation_context.md` if continuing a prior session.
3. Upload this file if the session might touch process/organization questions.

### During a Session
1. **Decisions get captured in the bible.** At the end of a session (or when a major decision is made), update the bible. Don't leave decisions only in the conversation.
2. **Produce a continuation context if the session will span multiple conversations.** This is a temporary file that captures where the discussion is, what's been decided, and what's still open. It gets deleted once its contents are merged into the bible.
3. **Don't produce implementation docs.** Stage specs are produced by the session that begins a stage, not speculatively.

### Ending a Session
1. Update the bible with any decisions made.
2. If more brainstorming is needed, produce a continuation context.
3. If a stage is ready to begin, produce the stage spec for that stage.

---

## Communication Patterns

### Westley → Claude Code
- "Here's the stage spec, implement it"
- "This system doesn't feel right, let's debug"
- "Delete this, it's not working"
- "I want to adjust [specific thing], here's what I want instead"

### Westley → Claude.ai
- "I want to brainstorm [design area]"
- "This didn't work in practice, let's redesign"
- "Write up what we decided into the bible"
- "Produce a continuation context / stage spec"

### Claude Code → Westley
- "Here's what I built, here's how to test it"
- "This design decision doesn't work in implementation because [specific reason] — flag for brainstorming?"
- "Stage done. Here's the prove-it test. Ready for your sign-off."

### Claude.ai → Westley
- "Here's what I recommend and why"
- "Here are the tradeoffs between options"
- "Updated the bible with our decisions"
- "Here's the continuation context for next session"

---

## Summary: The One-Page Version

1. **Bible says what. Dev rules say how. Stage specs say what right now.**
2. **Isolate, prove, then integrate. Never the reverse.**
3. **If you can't delete it cleanly, it's wired in wrong.**
4. **Build only what the current stage asks for. No speculation.**
5. **Three docs govern the project. No more.**
6. **Dead code gets deleted, not commented.**
7. **Design questions go to brainstorming. Implementation questions go to Code. Never cross the streams.**
8. **Every stage has a gate. Westley opens it.**
9. **STOP after every step. Show output. Wait for Westley. Do not self-verify and continue.**
