# MVP Scope Decisions & Single-Chat Capability Assessment

**Date**: 2026-09-16  
**Context**: Following the completion of the test authoring pass (411 red tests across 12 epics; PLAN.md calls this Stage 5) and the card generation pass (136 Agora micro-cards queued; part of PLAN.md's Stage 4). This file's earlier "Stage 4 / Stage 5" labels were swapped relative to PLAN.md and are corrected here. Following the completion of Stage 5 tests and Stage 4 cards in `~/Projects/agora/queue/parked/`), this document records:
1. What remains to be decided for the Round 1 Lean MVP scope.
2. An empirical assessment of a single chat's capabilities, throughput, and boundaries.

---

## Part 1: What Still Needs to Be Decided for MVP Scope (Round 1)

Per [`docs/northstar/mvp/build_path.md`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/mvp/build_path.md) and [`docs/northstar/mvp/README.md`](file:///home/westopoli/Projects/ouroboros-manifold/docs/northstar/mvp/README.md), Round 1 is **"every major feature at its most minimal"** delivered as a standalone Windows ZIP to 10–20 friends on Discord.

The simulation core (`E-02` through `E-15`, `E-17`) is **100% specified, tested, and queued** (166 total micro-cards). Only **~15 stories** remain across the client, presentation, and packaging layers.

The following specific decisions must be finalized before those remaining stories can be queued:

### 1. E-01: Two-Layer Movement Prototype (`S-P10`) Visual Reference
- **Current State**: The full 5-layer system is deferred behind a playable prototype. Round 1 uses a minimal 2-layer prototype (`S-P10`) to test tactical height transitions.
- **Decision Needed (`Q-E01-08`)**:
  - Provide visual/feel direction for the 2-layer transition: How should a unit transitioning between Layer 1 and Layer 2 appear in Godot? (e.g. Simple vertical tweening, alpha fade, ring indicator).
  - Confirm elevation separation distance (e.g. 50 world units).

### 2. E-16: Minimal Client UI & Galaxy Viewer
- **Current State**: Godot client currently has mock main menu and privacy modal. Needs the minimal in-game UI shell to connect to the C sim.
- **Decisions Needed**:
  - **Galaxy View (`S-103`)**: Confirm whether galaxy navigation in Round 1 uses Godot 3D particle nodes (existing `scenes/shared/galaxy/galaxy_structure.tscn`) or a 2D node map view.
  - **Tactical Camera (`S-105`)**: Confirm camera controls (RTS edge-pan, middle-mouse drag, WASD, fixed 45° isometric tilt).
  - **Selection & Orders (`S-106`, `S-107`)**: Drag-box selection + right-click move/attack. Confirm whether formation movement uses group centroid arrival (Halo Wars model) or individual unit arrival.

### 3. E-18: C-to-Godot Sim Bridge & Save Format
- **Current State**: Sim runs in C (`libouroboros.so`).
- **Decisions Needed**:
  - Confirm integration bridge for Round 1: Shared library C ABI (`GDExtension` / ctypes C API bridge) vs. legacy pipe JSON IPC. (*Recommendation: Direct GDExtension / ctypes C ABI call to avoid IPC serialization overhead*).
  - Save format: Plain binary struct dump of `om_world` or lightweight JSON snapshot for chapter saves.

### 4. E-22: Friends Playtest Packaging & Telemetry
- **Current State**: Specification written in Track L.
- **Decisions Needed**:
  - **Distribution**: Confirm ZIP structure: Godot executable + `libouroboros.so` (or `.dll`) + `README.txt` with default keybindings.
  - **Telemetry Opt-In**: Confirm local JSON telemetry logging path (`user://telemetry.json`) and opt-in upload behavior (R2 bucket upload vs. manual Discord attachment).
  - **Bug Capture Hotkey**: Confirm `F12` hotkey behavior (packages screenshot + log + current seed into a timestamped zip).

---

## Part 2: Assessment of a Single Chat's Capability

### 1. Demonstrated Velocity in a Single Session
In this single session, operating within the Antigravity coordinator + sub-agent pattern, we achieved:
- **Planning & Verification**: Authored `PLAN_MULTIAGENT_TEST_AUTHORING.md` verbatim, unblocked 19 ambiguity flags across 12 epics, and validated Definition of Ready.
- **Test Generation & TDD Suite**: Generated skeletons, dispatched 4 parallel sub-agents on the everyday model (`flash`), and authored **86 test files / 411 tests** (14,986 lines of code).
- **Quality & Red Verification**: Resolved false-green edge cases and proved **100% RED failures (411/411)** via `red_check.py`.
- **Card Decomposition**: Authored `gen_all_cards.py`, generated **136 Agora micro-cards**, dispatched a card auditor sub-agent to rebalance partitions, and enriched 68 cards with algorithm math (`ALG-30`..`ALG-75`).
- **Pipeline Integration**: Extended `RELEASE_CHAIN` in `agora/scripts/next.py` and committed all repositories cleanly.

### 2. The High-Leverage Zone (What a Single Chat Excels At)
1. **Architectural Coordination & TDD Gating**:
   - The coordinator agent acts as a strict compiler/auditor rather than typing repetitive code.
   - Enforcing strict gates (`red_check.py`, 30B contract validation, DoR audits) prevents downstream hallucination.
2. **Sub-Agent Fan-Out on the Everyday Model (`flash`)**:
   - Offloading high-volume transcription work (e.g. test writing, card generation) to 1–4 sub-agents running on `flash` achieves massive parallel throughput with zero degradation in reasoning quality.
   - Cost and token efficiency is maximized; the primary chat context stays lean and responsive.
3. **Automated Generator Tooling**:
   - Writing small, deterministic Python scripts (`gen_all_cards.py`, `red_check.py`, `derive_agora_rules.py`) to handle mechanical bulk operations (rather than making hundreds of LLM tool calls) cuts execution time from hours to seconds.

### 3. Structural Limits & Boundaries (What Requires Handoff)
1. **Human Design Judgment**:
   - The agent cannot and must not invent game feel, visual aesthetics, or business decisions (e.g. naming eras, choosing visual references, deciding monetization). These require brief user input gates.
2. **Long-Horizon Worker Execution**:
   - Actually building the C code and running candidate loops across 136 cards takes **~22 hours of GPU execution**. This belongs in the background Agora burner daemon (`next.py`), not inside an active conversation session.
3. **Context Saturation Guards**:
   - A single chat should never attempt to write 100+ files sequentially in the main conversation. Sub-agent delegation and generator scripts are mandatory to avoid context exhaustion.

### 4. Conclusion
A single well-orchestrated chat is capable of defining, testing, and queueing **an entire game subsystem (80–100 stories / 130+ micro-cards)** in 2–3 hours. The entire remaining MVP backlog (~15 client and packaging stories) can easily be brought to 100% Ready, Tested, and Queued in **one additional session**.
