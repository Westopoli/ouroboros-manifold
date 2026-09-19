# Factory research (2026-09-18)

Research memos behind the PLAN.md section "The Factory: how Agora builds and verifies autonomously". Each memo answers a named design question with sources, compares against what the repos already do, and ends with open questions for Westley. Written by Sonnet doers from briefs by the Fable session, reviewed before landing here. The design synthesis and Westley's decisions are recorded in `docs/northstar/PLAN.md` once approved; until then the working draft lives with the session.

| Memo | Question it closes |
|---|---|
| `A1-spec-to-task.md` | How stories become expectation specs, tests and cards mechanically, project-agnostic, and how a change propagates |
| `A2-verification-vs-reward-hacking.md` | Which gates keep a weak implementer honest, which hole remains (special-casing), how wide the regression net should be |
| `A3-long-horizon-coherence.md` | How a years-long card-built codebase stays coherent; the card-cut rule; what the run archive should keep |
| `A4-game-qa-plugin.md` | Oracle taxonomy, actor vocabulary, verifier and harness-error status, per-project profile, planted-bug controls |
| `A5-harness-self-improvement.md` | What the harness may change about itself, how proposals are gated, metrics that resist gaming |
| `A6-content-at-scale.md` | Era and landscape packs as factory artifacts; validators as acceptance; content-only controls |
| `A7-multiplayer-determinism-qa.md` | Determinism gates per card, sanitizer and banned-call checks, desync as a T1 detector, replay files as evidence |

Earlier surveys feeding these: the game-QA prior-art pass and the self-improving-agent pass summarized in `../harness_defects_2026-09-17/` (2026-09-17/18).
