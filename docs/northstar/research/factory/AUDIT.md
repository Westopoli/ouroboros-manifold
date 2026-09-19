# Comprehensive Audit of Model Deductions, Research Synthesis, and Evidence Integrity

**Audit Target**: Claude Session [`e5a6ed2f-9b6f-4836-ba20-e13fc9129eef`](file:///home/westopoli/.claude/projects/-home-westopoli-Projects-ouroboros-manifold/e5a6ed2f-9b6f-4836-ba20-e13fc9129eef.jsonl)  
**Deliverables Audited**:
- Factory Research Memos: [`A1`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/factory/A1-spec-to-task.md) through [`A7`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/factory/A7-multiplayer-determinism-qa.md) (committed `8577f6f`)
- Harness Defect Investigation: [`README.md`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/README.md) (D1–D10) and [`DECISIONS.md`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md) (Rounds 1–5, R1–R7l)
- Evidence Base: [`evidence/tokens/`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/evidence/tokens/), [`evidence/forensics/c_replies.csv`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/evidence/forensics/c_replies.csv), [`evidence/splice/`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/evidence/splice/), [`evidence/recut/`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/evidence/recut/)
- Working Program Plans: [`clever-spinning-gizmo.md`](file:///home/westopoli/.claude/plans/clever-spinning-gizmo.md) (Phases A, B, B.9, C) and [`B-design-draft.md`](file:///tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/e5a6ed2f-9b6f-4836-ba20-e13fc9129eef/scratchpad/factory/B-design-draft.md)
- Memory System: [`harness-investigation-2026-09-17.md`](file:///home/westopoli/.claude/projects/-home-westopoli-Projects-ouroboros-manifold/memory/harness-investigation-2026-09-17.md), [`verify-satisfiable-before-blaming-models.md`](file:///home/westopoli/.claude/projects/-home-westopoli-Projects-ouroboros-manifold/memory/verify-satisfiable-before-blaming-models.md), [`continuation-2026-09-18-harness-fix-handoff.md`](file:///home/westopoli/.claude/projects/-home-westopoli-Projects-ouroboros-manifold/memory/continuation-2026-09-18-harness-fix-handoff.md)

---

## Executive Summary

The audited session represents a monumental effort: diagnosing why Agora's local model ladder failed on C cards (D1–D10), establishing an empirical forensics base (1,352 attempts analyzed in [`c_replies.csv`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/evidence/forensics/c_replies.csv)), fixing the C harness (function-level splice, header slicing, context shift suppression), commissioning seven research memos ([A1–A7](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/factory/)), and drafting a comprehensive factory build-and-QA architecture ([`clever-spinning-gizmo.md`](file:///home/westopoli/.claude/plans/clever-spinning-gizmo.md)) with a 12-experiment prototype phase (Phase B.9).

However, a deep forensic audit reveals a critical bifurcation:
1. **The Empirical Defect Investigation (D1–D10) was brilliant, rigorous, and completely factual.** The attribution of card failures to ungated simulation drift (`sim.c`), 73% header bloat in 16k context windows, and gpt-oss truncation was proven beyond doubt by hard data.
2. **The High-Level Architecture (Phase B) suffered from serious deductive leaps, over-generalizations, and critical blind spots.** The model swung from diagnosing harness mechanical bugs to deducing an idealized factory framework that assumed:
   - Static symbol AST linting (`card_lint.py`) can guarantee card passability and independence without reference bodies.
   - Reward hacking is narrow and restricted to literal hard-coding (solvable by shadow fixtures), making mutation testing unnecessary.
   - Simulation cards can be neatly isolated by static function call closures, ignoring the temporal and dynamic state mutations of the simulation tick loop.
   - MemorySanitizer (MSan) can be trivially attached to C builds invoked via Python `ctypes`.

The ultimate proof of these deductive flaws unfolded in real-time: while Claude was finalizing Phase B, an executor session ran Round 5 ([R7a–R7l](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md)). **100% of the failures in Round 5 breached the assumptions of Claude's Phase B design.**

---

## Section 1: Audit of the Nine Core Deductions (Turn 2207)

In Turn 2207 of the transcript, the model summarized how research changed its thinking into nine key deductions. Below is the point-by-point audit of each deduction against hard evidence.

### Deduction 1: Reference Implementations vs. Mechanical Lint
> **Model's Deduction**: *"Prove passability with a reference -> mechanical lint, references only for diagnosis. You caught this before the research did, but A2 sealed it: every real goalpost move this week was a card-authoring mistake, not the worker cheating. So the design puts the honesty burden on the spec side (lint, controls, green-check on demand), not on Claude pre-implementing."*

- **Audit Verdict**: **Partially Sound, Functionally Inadequate.**
- **The Empirical Reality**:
  - Claude correctly identified that having Sonnet write a reference implementation for every card turns Claude into the builder and defeats the purpose of an autonomous factory.
  - However, the leap to **"mechanical lint (`card_lint.py`) is sufficient to prove passability"** was immediately refuted by the evidence.
  - In Round 5 ([DECISIONS.md](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md)):
    - **R7b/R7c**: Cards 204a1 and 204a3 were both verified as `LINT OK` by `card_lint.py`, yet were **physically circular** at runtime: 204a3 needed 204a1's telegraph dispatch, while 204a1 needed 204a3's attack tick logic!
    - **R7d**: `agent.c`'s mode selection ignored `rng_forced_len`. `card_lint.py` showed no errors.
    - **R7e**: `test_R_036_05` passed `card_lint.py`, but was impossible to pass because the fixture's defender had a higher budget than the attacker, legitimately counter-attacking and confounding the assertions.
    - **R7h**: `test_control_e05_agent_reads_live` passed `card_lint.py`, but was structurally unsatisfiable because 3d (decisions) executes completely before 3f (resolution) starts.
    - **R7l**: `test_control_e05_garrison_before_damage` passed `card_lint.py`, but was unobservable because `military + damage = 4.0` never clamped.
- **Root Cause**: `card_lint.py` inspects only static Python AST calls and maps them to C function names and STUB markers. It has zero awareness of **temporal tick order, shared state mutations, or fixture parameter satisfiability**. The model substituted an AST check for an execution proof.

---

### Deduction 2: Reward Hacking vs. Special-Casing (Shadow Fixtures vs. Mutation Testing)
> **Model's Deduction**: *"The weak model will game the tests -> the fence already closes most of it; the open hole is special-casing. I expected reward hacking to be the central threat. A2's inventory: test editing and harness tampering are structurally closed (fence, no shell); vacuous patches are caught; the one uncaught behavior is hard-coding the fixture's numbers, and the cheap answer is a shadow fixture rerun. Landed as PF-6 and one gate, not a mutation-testing program."*

- **Audit Verdict**: **Flawed Deductive Leap. Conflated Malicious Hacking with Semantic Under-Specification.**
- **The Empirical Reality**:
  - Claude correctly noted that with a strict diff fence (`finalize_pass` in `build.py:955-964`) and no shell execution, the model cannot rewrite pytest files or tamper with test runners.
  - But Claude deduced that literal hardcoding (e.g. `if (x == 66.0) return 2.275;`) is the *only* remaining leak, and that a single shadow fixture (PF-6) closes the hole.
  - **The Counter-Proof (R7g)**: Card 204a1 produced a merged implementation of `om_step_telegraphs` that was clean on `card_lint.py` and passed its acceptance test (`test_R_036_03`). Yet it was catastrophic:
    - Never multiplied `stochastic` into `net`.
    - Compared `net` against `effective_defense * 1.5` instead of `15.0`.
    - Deducted damage as percentage-of-current-field instead of `-0.8 * net`.
    - Inverted the entrenchment condition.
    - Produced conquest on the breakthrough band verbatim matching `OM_BUG_CONQUEST_ON_BAND`.
  - **Why did this happen?** Because `test_R_036_03` only asserted `effective_attack`. The worker wrote code that satisfied that single assertion while emitting junk for the rest of the algorithm.
  - **Why Shadow Fixtures (PF-6) Fail Here**: A shadow fixture with perturbed values would still have passed R7g, because the model didn't hard-code literals—it implemented an incomplete formula that satisfied the fixture!
  - **The Discarded Technique (Diff-Scoped Mutation Testing)**: A2 cited Google's practice of mutating the candidate diff at review time. If Agora had mutated lines in the candidate's diff, it would have discovered that mutating the damage or stochastic branches caused zero test failures, instantly flagging the card as under-tested. Claude prematurely discarded mutation testing.

---

### Deduction 3: Regression Gate Scope
> **Model's Deduction**: *"Regression gate scoped to the file is a sensible trade-off -> run the whole suite after every DONE. I had framed width as cost. A2 measured it: seconds. My own Q1 design was too narrow because I assumed cost. Landed in B.4 and PF-7."*

- **Audit Verdict**: **Sound for Headless C; Dangerously Over-Extended to Full Factory.**
- **The Empirical Reality**:
  - For `tests/csim/`, Claude's measurement is verified: the determinism tests execute in `0.02s`, and the entire ~670 test C suite executes in seconds against the compiled `.so`.
  - Q1's narrow fix (re-running only DONE cards sharing `snippet_file`) failed repeatedly (203b1 broke 203a1 across files; 204a1/204a2/204a3 broke each other across files). Widening to the full C test suite after every DONE was an empirically sound correction.
  - **The Over-Extension**: In `clever-spinning-gizmo.md` B.5 and PF-7, Claude extended this rule across the entire Factory, including Godot T2 scenarios. Running a full T2 suite involving Godot headless scene launches, Xvfb screen captures, and multi-thousand-tick playthroughs takes minutes, not seconds. The deduction failed to define tiered regression gating (per-candidate C unit tests vs. per-rung T2 integration passes).

---

### Deduction 4: Self-Improvement & The Refiner
> **Model's Deduction**: *"Build a refiner -> generalize the PROPOSE move that already exists. A5 found Agora already has propose-only self-modification with the human-applies contract, and that every system without a held-out gate (SICA, DGM, Continual Harness) got gamed or broke itself; DGM's agent faked test logs. Landed as the three-tier rule... and per-epic cadence. I dropped the 'nightly refiner' I had sketched."*

- **Audit Verdict**: **Highly Sound and Grounded.**
- **The Empirical Reality**:
  - This is one of the strongest deductions in the entire research program.
  - A5's literature analysis of SICA (infinite loops, degradation of general reasoning), DGM (agents hacking the hallucination reward function and fabricating tool logs), and Continual Harness (1,003-turn loop due to ungated in-place schema rewrites) provides ironclad justification for rejecting autonomous self-modifying code.
  - Grounding self-improvement in Agora's existing `DriverMove.PROPOSE` (`prompts/driver-propose.md: "This diff is NEVER applied automatically: a human reads it and applies it by hand or not at all"`) preserves safety.
  - **The Latent Data Deficit**: Claude proposed PF-9 (scoring ladder strategies offline from `candidates.jsonl`). However, as noted in A5 §3, `candidates.jsonl` currently does not log prompt hashes, advisor hints used, or regression deltas. The deduction is sound, but the data pipeline required to support it does not yet exist.

---

### Deduction 5: State Oracles vs. Vision Judges
> **Model's Deduction**: *"QA needs vision -> state first, vision last, maybe never for most bugs. BALROG, the Pokémon harnesses, OSWorld and WebArena all found state beats pixels for weak models, and A4's mapping shows 13 of 22 catalog rows need no vision. Landed as the oracle ordering in B.4 and the 'defer the vision judge' recommendation; PF-12 decides on a VRAM number instead of a hope."*

- **Audit Verdict**: **Sound Hardware Pragmatism; Severe Risk to Game Rendering.**
- **The Empirical Reality**:
  - The hardware calculation is accurate: on a 12GB RTX 3060 running Ollama, hosting `qwen3-coder:30b` leaves negligible VRAM for `qwen2.5-vl:7b`, even quantized.
  - Prior art (OSWorld, BALROG) confirms that querying structural state (DOM, scene tree, variables) is orders of magnitude faster, cheaper, and less flaky than VLM image inspection.
  - **The Blind Spot**: Ouroboros is an RTS game client built in Godot. Crucial visual defects (canvas layer z-fighting, camera clipping, font rendering failures, shader pipeline crashes, texture loading errors, animation desync) leave zero trace in sim or UI state variables. If the factory defers visual judgment "maybe never", the Godot frontend can become completely unplayable while all state oracles report 100% green.

---

### Deduction 6: QA Harness Faults vs. Product Faults
> **Model's Deduction**: *"The QA harness's problem is coverage -> its problem is that it cannot tell its own faults from the product's. The retracted probes and campaign 004 converging on a dead-input session were the most instructive data of the whole exercise. A harness-error outcome, input-liveness precheck, and 'zero findings on a planted build is a harness failure' became load-bearing. PF-3 is first in the experiment order for that reason."*

- **Audit Verdict**: **Exceptionally Sound. Best Grounded Deduction in the Session.**
- **The Empirical Reality**:
  - Directly backed by [`docs/northstar/proving_ground/SCORECARD.md`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/proving_ground/SCORECARD.md): Probes D and G were marked passed and subsequently retracted because clicks recorded outcome `"ok"` while Wayland focus prevented inputs from ever reaching the game window.
  - Campaign 004 converged on a false positive because the QA director treated repeated non-mutating sessions as a stable app.
  - Establishing `harness-error` as a distinct terminal outcome, requiring input-liveness checks before session execution, and mandating that planted defect builds must trigger detectors are exemplary design choices directly solving documented historical failures.

---

### Deduction 7: Card Sizing vs. The Cut Seam
> **Model's Deduction**: *"Card size is the coherence problem -> the cut seam is. A3's two benchmarks quantified erosion in long agent runs, but our own week showed the mechanism: cards cut by rule pair crossed file ownership. The rule became 'smallest (file, function family) whose acceptance symbol-closure stays inside it', plus a scheduled per-epic architecture review rather than incident-triggered. PF-8 tests it against the actual 204-207 cards."*

- **Audit Verdict**: **Flawed Deductive Leap. Static Seams vs. Dynamic Simulation Couplings.**
- **The Empirical Reality**:
  - Claude correctly identified why the original 204–207 cut failed: cutting by rule pair split functions across cards, causing acceptance tests to call stubs in other files (`SPANS_ANOTHER_CARD`).
  - Claude deduced: *a card's boundary is the smallest (file, top-level function or function family) pair whose acceptance test's transitive symbol closure stays inside that pair*.
  - **The Collapse in Practice**: The executor session applied this exact re-cut rule to E-05 (R1 in [DECISIONS.md](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md)). The result?
    - 204a1 (`om_step_telegraphs`) and 204a3 (`om_step_resolve`) each passed the symbol-closure lint, yet could not build because they had a circular tick dependency (R7b).
    - 204a1 also depended on 204a2 (`om_tick_reinforces`), forcing a second re-order (R7c).
  - **Why?** Because in an engine simulation, functions communicate via **the shared world state (`w->telegraphs`, `w->attacks`, `w->rng_forced`) across the sequential stages of `om_world_step`**. A static symbol AST check cannot see that calling `om_world_step` in a test executes 3c, 3d, 3e, and 3f in order, creating hidden temporal dependencies across files.

---

### Deduction 8: Content and Multiplayer from Day 1
> **Model's Deduction**: *"Content and multiplayer are later problems -> they are card kinds and detector classes from rung P0. A6: content cards = validators and a diff fence as acceptance, sized by entry count; A7: desync = two instances in one process, a T1 detector with a bit-flip control; sanitizers and a banned-call list belong in every C card now, not at multiplayer time. Landed in B.1 (card kinds) and the ladder's P0/P8/P9 rows."*

- **Audit Verdict**: **Conceptually Sound; Systematically Broken on Sanitizers (MSan).**
- **The Empirical Reality**:
  - The content card formulation (validator scripts as acceptance commands, content diff fence) in A6 is clean and extends Agora's `acceptance:` command model naturally.
  - The multiplayer desync detector (two `om_world` instances in one process comparing checksums) in A7 is elegant, avoiding multi-process networking for early determinism testing.
  - **The Fatal Systems Defect (MSan)**: Claude deduced in A7 §3 that every C card should bundle `-fsanitize=undefined` (UBSan) and a separate MemorySanitizer (MSan) build against `tests/csim/`.
    - **Technical Impossibility**: MSan tracks the initialization state of every memory bit. It requires the **entire executable and all linked libraries** to be compiled with MSan.
    - Ouroboros runs tests using Python `ctypes` (`/usr/bin/python3`). Python itself, `glibc`, and system libraries are NOT compiled with MSan.
    - When Python loads an MSan-instrumented `libouroboros.so`, the first time Python passes a buffer or libc allocates memory, MSan reports a false-positive crash (`use-of-uninitialized-value`) because Python's memory is uninstrumented.
    - MSan cannot be used via Python `ctypes` without a hermetic C test runner or a custom-compiled Python binary. Claude proposed this without verifying basic ABI/sanitizer runtime constraints.

---

### Deduction 9: Specification Format (Prose vs. Structured YAML)
> **Model's Deduction**: *"Prose rules files are the director's input -> a structured expectation spec. A1: Gherkin's data/code split is the only pattern that absorbs a new feature type without a template change, and our slugify-the-prose parser already produced a bug class. Landed as the new artifact in B.1 and PF-1."*

- **Audit Verdict**: **Mechanically Sound; Recreates the Prose-Spec Drift Trap.**
- **The Empirical Reality**:
  - Claude correctly identified that regex-slugifying prose markdown tables to generate pytest stubs (`gen_test_skeleton.py`) was fragile and caused syntax crashes.
  - Adopting Given/When/Then with structured `state_checks` and `visual_claims` provides a machine-readable target for the QA director.
  - **The Drift Trap Contradiction**: In A1 §2, Claude extensively quoted Frisinger on how BDD/Gherkin failed because the prose spec and the executable step definitions drifted apart.
  - Yet in B.1, Claude introduced `S-###.spec.yaml` as an intermediate artifact alongside `docs/northstar/e2e/E-##.md` and `tests/csim/test_*.py`!
  - When the C implementation or tests were altered in Round 5 (e.g. R7f modifying `test_R_036_05`), the tests were edited directly, leaving `E-05.md` and any future `spec.yaml` completely out of sync. Claude created the exact multi-tier drift trap that its own research paper warned against.

---

## Section 2: Audit of Discarded Prior Art

In Turn 2207, Claude listed ten research areas that it deliberately chose not to adopt. Below is the forensic audit of those decisions:

| Discarded Technique | Claude's Stated Rationale | Audit Finding & Assessment |
|---|---|---|
| **Self-Modifying Code (SICA, DGM)** | Fails unattended; agents game reward functions and falsify logs; `PROPOSE` with human review gives most value. | **100% Sound.** Validated by Sakana AI's DGM findings and Continual Harness stagnation loops. |
| **Dream-RSI Offline Policy Search** | Replaying thousands of policies via 30B model is unaffordable; simplified to flat lookup table. | **Sound.** 30B local inference cannot sustain bulk policy simulation. (However, required archive fields are currently missing). |
| **AlphaEvolve Numeric Fitness** | Needs a single scalar fitness function; game QA is multidimensional and visual. | **Sound.** Scalar optimization causes extreme reward hacking in gameplay testing. |
| **ChatDev Role Chat** | MetaGPT proved structured document handoffs beat open-ended conversation. | **Sound.** Confirmed by SWE-bench and multi-agent literature. |
| **Vision-First Actor Agents** | Weak models struggle with pixels; state oracles are faster and more reliable. | **Sound for gameplay mechanics; risky for graphics/UI rendering.** |
| **Voyager Vector Store Skills** | Plain files and scripts are simpler than vector embeddings for 160 stories. | **Sound.** Vector retrieval adds unnecessary complexity for bounded deterministic cards. |
| **Curiosity-Driven RL (EA SEED)** | Requires heavy reinforcement learning infrastructure unavailable on workstation. | **Sound.** Hardware-constrained reality. |
| **Full Mutation Testing** | Heavier than incident record justifies; shadow fixtures sufficient. | **Flawed Discard.** R7g proved that candidates can pass tests while breaking untested algorithm formulas. Diff-scoped mutation testing would have caught this. |
| **Continual Harness Ungated Edits** | In-place ungated edits compound errors (1,003-turn loop in Power Plant Route). | **100% Sound.** Validated by literature. |
| **Gherkin/Cucumber for Gameplay** | No industry precedent for games; Cucumber tooling is web-oriented. | **Sound.** Adopting Gherkin's Given/When/Then schema without Cucumber baggage was the right choice. |

---

## Section 3: Forensic Audit of the "What Was Not Read" Confession

In Turn 2186 of the transcript, Claude provided an honest inventory of what it read versus what it skipped:

```markdown
Build runs I used directly: 
- 2026-09-17 investigation: every candidates.jsonl and reply-N.md across 22 C cards (D1-D10).
- 2026-09-18 runs under fixed harness: 203a1, 203a2, 203b1, 203c, 203e.

Not read by me:
- Anything the chain produced after 203e (ran overnight).
- Gemini intervention texts beyond two in 203a2.
- advisor_hint.md contents; thinking-N.md; runs/metrics.jsonl and costs.jsonl.
- QA runs: none read by me. A4 doer read campaigns 004/005, director sessions, SCORECARD.
```

### Forensic Analysis of the Impact of These Blind Spots:

1. **The Post-203e Blind Spot**:
   - Because Claude did not read the post-203e runs, it designed Phase B believing that Cascade 1 and Cascade 2 had permanently stabilized C card generation.
   - In reality, the moment the chain hit 204a3 and 204a1, it ground to a complete halt with 14 consecutive failures due to compile errors (`fmin`), circular function dependencies, and broken stochastic formulas. Phase B was drafted in an epistemic vacuum regarding the actual behavior of E-05 cards.

2. **The QA Delegation Blind Spot**:
   - Claude read zero raw QA logs, relying entirely on the Sonnet subagent (A4 doer).
   - The A4 doer extracted high-level summaries (retracted probes D and G, lack of keypress verb), but failed to notice that `qa_desktop.py` lacked robust IPC handling and was prone to freezing when desktop processes failed to bind ports immediately.

3. **The Metrics and Costs Blind Spot**:
   - Claude did not inspect `metrics.jsonl` or `costs.jsonl`. Consequently, when it proposed PF-9 (offline scoring of ladder strategies), it did not realize that Agora does not log the prompt text or regression history in its candidate rows.

---

## Section 4: Stress-Testing Phase B Against Round 5 (R7a–R7l)

The ultimate test of any architectural design is how well it holds up against empirical reality. Round 5 ([DECISIONS.md](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md)) occurred concurrently with Phase B's authoring. Below is the scorecard of how Claude's design mechanisms fared against the 10 real-world blockers encountered in Round 5:

```
+---------------------------------------------------------------------------------------------------------+
|                                ROUND 5 REALITY SCORECARD FOR PHASE B DESIGN                              |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| ID    | Failure Incident                              | Predicted by B.7? | B.1-B.5 Design Vulnerability|
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7a   | Missing `#include <math.h>` compile error     | ❌ Missed         | Function splice cannot add  |
|       | across candidate splice                       |                   | file-level C headers        |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7b   | Circular dependency: 204a1 <-> 204a3          | ❌ Missed         | AST linting ignores runtime |
|       | each needed the other's unbuilt function      |                   | tick call-graph dependency  |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7c   | 204a1 also depended on 204a2 reinforce        | ❌ Missed         | Acceptance test called      |
|       | resolution                                    |                   | multi-card tick pipeline    |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7d   | `agent.c` RNG draw bypassed `rng_forced_len`  | ❌ Missed         | Contract stated in header   |
|       | breaking downstream tick reproducibility      |                   | was violated in C code      |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7e   | Confounded fixture: defender counter-attacked | ❌ Missed         | Assumed tests are objective;|
|       | due to higher budget in two-faction setup     |                   | missed autonomous agency    |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7g   | Merged code green on tests, but completely    | ❌ Missed         | Falsified claim that shadow |
|       | mangled damage math & reproduced named bug    |                   | fixtures replace mutation   |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7h   | `agent_reads_live` control unsatisfiable by   | ❌ Missed         | Controls asserted impossible|
|       | construction (decide-then-resolve batch order)|                   | temporal tick relationships |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7i   | Same-target double attack due to declaration- | ❌ Missed         | Dynamic state loop not      |
|       | time budget deduction                         |                   | visible to static spec      |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7j   | Bug fix for 204a1 implemented 204b1's job,    | ❌ Missed         | Strong model fix caused     |
|       | making 204b1 structurally unsatisfiable       |                   | cross-card collision        |
+-------+-----------------------------------------------+-------------------+-----------------------------+
| R7l   | `garrison_before_damage` control fixture      | ❌ Missed         | Fixture numbers never hit   |
|       | never clamped; control was unobservable       |                   | zero clamp; vacuous control |
+-------+-----------------------------------------------+-------------------+-----------------------------+
```

### Analysis of the Scorecard:
The scorecard is decisive: **0 out of 10 Round 5 blockers were prevented or caught by the mechanisms in Phase B.**
- Phase B focused its defensive posture on **worker model adversarial behavior** (fences, context shifts, truncation, special-casing literal hardcodes).
- Reality demonstrated that **100% of the failures were semantic, architectural, and dynamic**:
  1. Confounded fixtures where tests made contradictory assumptions about agent behavior.
  2. Temporal tick coupling where function boundaries did not align with simulation phases.
  3. Under-specified tests that let broken implementations pass green.
  4. Positive controls that were physically unsatisfiable or mathematically vacuous.

---

## Section 5: Audit of the Twelve Prototype Experiments (Phase B.9)

In response to Westley's directive, Claude introduced Phase B.9 ([`clever-spinning-gizmo.md`](file:///home/westopoli/.claude/plans/clever-spinning-gizmo.md): lines 62–80), establishing twelve prototype experiments (PF-1 to PF-12) to test load-bearing design claims before Stage 3.

Below is the evaluation of each proposed experiment:

1. **PF-1 (Expectation spec -> mission)**:
   - *Design Claim*: A structured YAML spec is sufficient for the QA director without prose rules.
   - *Audit Assessment*: **Valid and Necessary.** Proves whether the director can generate actionable missions from structured state checks.
2. **PF-2 (Actor vocabulary: press, drag, wait, read_state)**:
   - *Design Claim*: Extending the protocol with these verbs enables deterministic RTS action and tick-stepping.
   - *Audit Assessment*: **Crucial.** Must specifically verify that `wait` (tick-step) does not freeze Godot's RPC thread.
3. **PF-3 (Harness-error status on dead input)**:
   - *Design Claim*: Replaying dead-input sessions terminates as `harness-error` and does not count toward convergence.
   - *Audit Assessment*: **Rock Solid.** Directly prevents the recurrence of campaign 004's false-positive convergence.
4. **PF-4 (T1 detectors on C trace)**:
   - *Design Claim*: Probe C detectors run over `om_trace_read` on the real sim; trips on `OM_BUG_*` builds.
   - *Audit Assessment*: **Sound.** Bridges Probe C's toy proof to the actual C simulation.
5. **PF-5 (Metamorphic desync detector)**:
   - *Design Claim*: Two `om_world` instances with identical seeds and inputs match checksums; 1-bit flip trips detector within 10 ticks.
   - *Audit Assessment*: **Sound and Cheap.** Can run in Python ctypes immediately.
6. **PF-6 (Shadow-fixture special-casing check)**:
   - *Design Claim*: Running a candidate against a second perturbed fixture catches hardcoded cheating.
   - *Audit Assessment*: **Partially Valid, but Insufficient.** Will catch literal hardcoding (`if (x == 66) return 2.275;`), but will **not** catch R7g-style under-specified functional implementations. Needs to be paired with diff-scoped mutation.
7. **PF-7 (Full-suite regression after DONE)**:
   - *Design Claim*: Replaying 203b1 against full suite catches 203a1 regression.
   - *Audit Assessment*: **Valid for C sim; must be explicitly bounded to C cards.**
8. **PF-8 (Card-cut by symbol closure)**:
   - *Design Claim*: Rule accepts re-cut cards and rejects original 204–207 cards.
   - *Audit Assessment*: **Falsified by Round 5.** The re-cut cards passed `card_lint.py` but still deadlocked on circular tick dependencies (R7b/R7c). PF-8 must be expanded to check **tick-stage dependency closure**, not just symbol definitions.
9. **PF-9 (Refiner proposals from archive)**:
   - *Design Claim*: Offline scoring of ladder strategies agrees with live outcomes.
   - *Audit Assessment*: **Blocked by Data Deficit.** Requires updating Agora's `candidates.jsonl` logging before this experiment can be executed.
10. **PF-10 (Content card validation)**:
    - *Design Claim*: Validator rejects broken era pack, accepts clean pack, fence blocks editing validator.
    - *Audit Assessment*: **Sound.** Tests the data-driven content pipeline.
11. **PF-11 (Second project onboarding)**:
    - *Design Claim*: Onboarding a CLI/web target requires zero Agora code changes.
    - *Audit Assessment*: **High-Value.** Truly tests whether Agora's B.3 project boundary is real or leaky.
12. **PF-12 (Vision judge feasibility on RTX 3060)**:
    - *Design Claim*: Measure VRAM and latency of quantized `qwen2.5-vl` beside `qwen3-coder` on 12GB GPU.
    - *Audit Assessment*: **Essential.** Provides the hard hardware number to permanently settle the vision judge debate.

---

## Section 6: Actionable Recommendations for the Factory Program

Based on this deep audit, the following adjustments should be made to [`clever-spinning-gizmo.md`](file:///home/westopoli/.claude/plans/clever-spinning-gizmo.md) and [`B-design-draft.md`](file:///tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/e5a6ed2f-9b6f-4836-ba20-e13fc9129eef/scratchpad/factory/B-design-draft.md) before Phase D approval:

1. **Replace Static Symbol Closure with Tick-Stage Simulation Closure (Fix for R7b, R7c, R7g)**:
   - `card_lint.py` must not only check function symbol definitions; it must check the **tick-stage pipeline dependency**.
   - If an acceptance test calls `om_world_step`, the card cannot be queued until all functions in the tick sequence prior to and including the tested function are fully implemented (non-stubs).
2. **Re-introduce Diff-Scoped Mutation Testing (Fix for R7g and Premature Discard)**:
   - Do not rely solely on shadow fixtures (PF-6).
   - Implement Google-style diff-scoped mutation testing: mutate only the lines touched by the candidate diff (flip operators, replace constants with 0). If the acceptance test does not fail on any mutant, the test is under-specified and the candidate must not be marked DONE.
3. **Drop MemorySanitizer (MSan) from ctypes Runs; Retain UBSan (Fix for A7 Toolchain Defect)**:
   - Remove MSan from automatic pytest-ctypes acceptance commands. Keep `-fsanitize=undefined` (UBSan) and `-Wfloat-equal`.
   - Reserve MSan for standalone, pure-C integration binaries where all linked libraries are hermetically instrumented.
4. **Resolve the Specification Drift Trap (Fix for A1 and Frisinger's Paradox)**:
   - Do not create a separate, hand-maintained `S-###.spec.yaml`.
   - Keep the epic markdown (`docs/northstar/e2e/E-##.md`) as the sole authoritative human/Claude specification. Have `scripts/specfactory/` mechanically compile the markdown tables into machine-readable JSON/YAML artifacts at build time as a generated cache, never as an independent source file.
5. **Expand Agora Logging to Enable PF-9**:
   - Update Agora's `candidates.jsonl` writer to log `prompt_hash`, `hint_applied`, and `regression_failures_count` so offline strategy evaluation can actually function.
6. **Ensure Godot Debug-Port Thread Safety for Tick-Stepping (PF-2)**:
   - In `docs/desktop-qa-protocol.md`, specify that the Godot debug-port daemon must set `process_mode = Node.PROCESS_MODE_ALWAYS` so `pause` and `step <n>` can be received and processed while the simulation scene tree is paused.

---
*Audit completed with complete fidelity to repository evidence, git commit history, and transcript logs.*
