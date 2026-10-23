# What the game offers, ranked for validation

Status: proposal, 2026-09-14. Scores are Claude's first pass; Westley re-scores on review. Re-scored after every gap review with the evidence from `experiments.md`.

## How the ranking works

Every offer is one of the hub's "What's Unique" items or a sacred principle, restated as something a player would notice. Three scores, 1 to 5 each:

- **Distinctiveness.** How much of the reason to buy this game rather than another rests on this. From the hub, `vision_v2.md`, and the audience research in `docs/legacy/topics/`.
- **Risk.** How likely it is that the idea is wrong or that players will not value it, given the research, the code reality, and how many open flags the epics carry.
- **Cost.** How much C, client, and Stage 3 to 5 work stands between today and a testable cut on the C/Agora path. 5 is "needs a full tactical slice and an unproven Agora capability."

Priority is distinctiveness times risk, divided by cost. High-distinctiveness, high-risk, low-cost items are validated first: they are the ones most likely to change the plan if wrong, and cheapest to find out about. Each row becomes a hypothesis in `experiments.md`.

## The ranking

| # | Offer | Epics | Dist | Risk | Cost | Priority | Hypothesis | Earliest round |
|---|---|---|---|---|---|---|---|---|
| 1 | A living galaxy that moves without the player | E-02, E-03, E-04, E-05, E-07, E-16 | 5 | 3 | 2 | 7.5 | H1: after the first time jump, at least 70 percent of testers name a galaxy change they did not cause, and call it interesting rather than random. | 1 |
| 2 | Generational carry-forward: return as someone new, consequences persist | E-08, E-10 (outcome), E-09 | 5 | 5 | 3 | 8.3 | H2: after three chapters, at least 60 percent name a consequence of a mission they played earlier. | 1 |
| 3 | A chronicle that reads as real history, different every campaign | E-09, E-21 | 4 | 4 | 2 | 8.0 | H3: median read time per jump at least 60 seconds; at least half recall one entry unprompted; nobody calls the text filler. | 1 |
| 4 | Elegiac tone with dry, earned humor | E-09, E-21 | 3 | 2 | 1 | 6.0 | H8: at least one line quoted per tester in interview; no tester describes the writing as trying too hard. | 1 |
| 5 | The tragedy of understanding: mastery is knowing why you lost | E-10, E-11, E-14 | 4 | 4 | 4 | 4.0 | H4: after a loss, at least 60 percent name a positional or force cause; no more than 20 percent say the game was unfair. | 1 |
| 6 | Commander, not king: a task force, no base, no economy | E-10, E-15 | 4 | 4 | 3 | 5.3 | H5: no more than 30 percent of testers ask for base building; "freeing" outnumbers "missing" when they describe its absence. | 1 |
| 7 | Missions generated from real trouble in the galaxy | E-10 | 3 | 3 | 3 | 3.0 | H9: at least 60 percent can say why this mission exists from the briefing alone. | 1 |
| 8 | Single-layer positional skill ceiling: surrounds, terrain, soft rock-paper-scissors | E-11, E-13, E-12, E-17, E-14 | 4 | 3 | 5 | 2.4 | H6: in a fixed scripted scenario where the tester's force is smaller, at least half of testers who attempt a surround win, and they describe positioning as the reason. | 1 |
| 9 | Art of Rally low-poly look, one readable silhouette per unit type | E-18 | 2 | 2 | 3 | 1.3 | H12: in a screenshot preference survey, the game's look is preferred over two reference styles by a majority; every tester can name the six unit types from silhouettes. | 1 |
| 10 | The 2.5D layer and vision system | E-01 | 5 | 5 | 5 | 5.0 | H7: with the option chosen in the layer design phase, at least half of losses are attributed by the tester to layer reading; cross-layer vision is described as a rule they used, not a surprise. | 1 (two-layer prototype) |
| 11 | Multi-era on one skeleton; $3 era packs, some earnable | E-20 | 4 | 4 | 5 | 3.2 | H10: survey only until two eras exist; after Round 3, at least 40 percent say they would buy a second era. | 3 (survey) |
| 12 | Multiplayer lockstep and cross-era matches | E-19 | 3 | 3 | 5 | 1.8 | Not testable before Round 3. The determinism contract is built regardless (E-02 S-020). The research says the tribe has no unified multiplayer demand and single-player-first is fine. | later |

Westley answered `Q-MVP-01` on 2026-09-14: Round 1 is every major feature at its most minimal, so every row except 11 and 12 is present in Round 1. The ranking still matters in two ways. It sets the order inside Round 1 (rows 1 to 4 are built and T1-tested first, as the macro loop; the tactical rows follow; client last), and every hypothesis present in Round 1 carries its threshold as a live kill criterion (`Q-MVP-04`); when a prototype surface misses, the gap review decides whether the idea or the stand-in failed. Row 10's two-layer prototype is the first option of the layer design phase, shown to friends rather than only to Westley.

## What the research says players hate, and how each round watches for it

From `docs/legacy/topics/` (audience profile, retention curves, tag research) and `../research/rts_bug_catalog.md`. Some briefs still name the killed Lieutenant system; those lines are ignored.

| Complaint | Where it would show | Instrument | Round |
|---|---|---|---|
| UI and tutorial bounce, the tribe's universal complaint | First session: long time to first order, abandoned first mission, tutorial skipped then lost | Telemetry (first-order latency, abandonment), interview question 1 | 1 |
| "Nothing I do matters" in a systemic game | H2 fails; interview says the jump felt like a reset | Chapter-three question | 1 |
| Filler prose, repeated sentences | H3 fails; telemetry shows near-zero read time | Read time, recall, S-071 test (no repeats) | 1 |
| Unclear objectives | Mission abandoned; "what was I supposed to do" in interview | Interview, telemetry | 2 |
| Dropped orders, stuck units, rubber-banding | R4 catalog signatures in T1 traces before any tester sees them; tester bug reports after | T1 detectors with positive controls, bug capture | 2 |
| Unfair loss | H4 fails | Loss question | 2 |
| "RTS" framing on the store page | Wishlist velocity below the festival band | Steam numbers; wording taken from Round 2 testers' own words (`Q-MVP-06`) | 3 |

## What no round can test yet

Listed so they are not mistaken for validated claims.

- Era-to-era feel. Pinned for later by the Stage 1 audit (A-321); one era ships in every round here.
- The monetization mix (earnable versus purchase-only packs). Survey only, and only once a second era exists.
- Multiplayer session shape, matchmaking, and cross-era matches. Every open flag on E-19 stays open through Round 3.
- Whether "commander, not king" survives contact with a long campaign (tens of chapters). Round 3's Steam retention numbers are the first real signal.
- The layer system's skill ceiling at scale. Round 3 tests one chosen option with a small cohort; the ceiling claim needs ranked play that does not exist yet.
