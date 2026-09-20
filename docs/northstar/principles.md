# Core Principles

These persist beyond any chat. The Factory section of `PLAN.md` is the operating model that applies them after Stage 2. A feature, plan, or task that violates one of these is wrong and gets fixed at the plan level, not worked around.

1. **Autonomy is the product.** Agora (local models plus a dollar-capped DeepSeek driver) builds and QA-tests the game unattended. Anything a human must do mid-loop is a design defect in the plan, not a task for Westley.

2. **Claude does judgment, day-side only.** Claude designs the bible, the end-to-end behavior definitions, the roadmap, the tests, and the escalation rules. Claude never runs in an unattended path by default (Agora decision D16). The opt-in loop watcher is a documented exception Westley enables by hand.

3. **Tests are the spec.** Every story exists as failing tests before Agora touches code. Tests are fenced; Agora cannot edit them. A failing test always has a reason and the loop keeps iterating until green. Every detector ships with a positive control proving it can fail.

4. **Small bites, upward.** Sprints feed tiny stories in dependency order. One task is one story with one acceptance command set, bounded by Agora's `max_impl_lines`. QA runs on every task, not at the end.

5. **Scale is a test.** Tests induce high input (units, regions, ticks) with hard thresholds. Under threshold means the story is not done. Thresholds are set by Claude with Westley and are never loosened by Agora.

6. **C for speed, equations preserved.** The sim is rewritten in C. The stochastic equations (drift, world generation, faction scoring, attack resolution, border friction, technology) are retained verbatim as named formulas unless Stage 1 kills them. Determinism via seeded RNG is a contract.

7. **The model is the user.** QA drives the game the way a player does and watches for what a player hates: rubber-banding, stuck units, backwards walking, dropped orders, and the rest of the RTS bug catalog. Two tiers: T1 state traces, T2 visual.

8. **Escalation is a ladder with a top.** The local model stalls; the escalator (Gemini via `agy`) hints, resets, or declares the card unsatisfiable; a plateau (distinct candidates, identical failing set) stops the run early; an upstream defect named by the escalator becomes its own fix task; the cap parks the card and writes an English flag with evidence. Only design decisions reach Westley. "Start over" is a defined protocol, not a panic.

9. **The bible describes now.** Rewrite, never append. Machine-consumable structure (stable IDs, story catalog, per-epic rules) so Agora artifacts derive from it by script.

10. **Agile, not waterfall.** Requirements are epics, stories, and rules. They may change while building. A change runs the change protocol (story revised, bible rewritten, tests revised by Claude, Agora task respec'd) in one pass, never partially.

11. **Definition of Ready gates building.** Nothing enters a sprint until its inputs and outputs are fully mapped, its ambiguity register is empty, its look-and-behavior references are attached, and its tests exist. A story that fails the gate is a planning task, not a build task.

12. **Ambiguity is flagged, never guessed.** When Claude finds an under-defined behavior it raises a `[NEEDS WESTLEY]` flag in the ambiguity register with the concrete question and candidate answers. Local models never see an open flag; they only see resolved rules.

13. **Prove the tool before trusting it.** Before Agora touches the game it passes toy probes with planted defects: build to fenced tests, obey a scale gate, catch each RTS bug class, drive a real Godot window, escalate to a flag, absorb a requirement change. A capability that has not been shown to fail on a planted defect is not a capability the plan may rely on.

14. **The harness is a tenant of the project, never the reverse.** Everything that names the game lives in the project or its profile; Agora stays product-blind so a second project onboards with data, not a fork, and an undefined future feature needs no harness code.

15. **A QA pass that cannot fail is not a QA pass.** Every session proves its inputs land, every scenario has a planted variant where it must fail, a session whose actions never mutate state ends `harness-error` and never counts as clean, and a planted-build campaign with zero findings is a harness failure.
