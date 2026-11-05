# Context for the simulation lane (start here; written 2026-10-12 by the Architect chat)

You continue work on the simulation engine: the C world model in `csrc/` (regions, factions, events, missions, the time jump, the chronicle) that the game client drives over the JSON pipe. Westley opened this lane because the visible-game programme has built screens since 2026-10-07 and nobody has checked that the world behind them still behaves as the bible says. ROADMAP section 2b, step 1, is the mandate: verify the simulation follows the stochastic rules, find regressions in mission choice and in the source of the chronicle. Read from `origin/main`, never the live checkout as a working tree; push from a worktree under `~/Projects/om-push/wt/`.

## Read first, in this order (the original plan for the simulation)

1. `docs/northstar/README.md` and `docs/northstar/PLAN.md` "Stage 1" and "Track R": the method and the decision that the C sim keeps the Python equations verbatim.
2. `docs/northstar/research/c_rewrite.md` (R2): how the Python sim became a C library, the determinism contract, the open questions it listed.
3. `docs/bible/algorithms.md`: the retained equations, constants and draw order per tick (the Stage 1 algorithm pass, 2026-09-10). This is the contract the C code must reproduce bit for bit.
4. `docs/bible/game_bible.md` hub, then the simulation epics E-02 to E-08 under `docs/bible/epics/` (fields and drift, world generation, events, factions, diplomacy, time jump, generations) and E-10 (missions) and E-09 (chronicle). Read only the epic you touch after the first pass.
5. `docs/northstar/e2e/E-02.md` to `E-05.md`: the end-to-end behaviour definitions written when those epics passed the Definition of Ready.

## The first synthesis (findings and diagrams already produced; present these to Westley as links before new work)

- `docs/architecture.md` "Strategic tick" (the `om_world_step` diagram, `csrc/sim.c:194-552`) and "Tactical tick" (`om_tactical_step`): the two mermaid diagrams of what runs in what order each tick, with the function names.
- `docs/legacy/research/epics_audit_2026-10-02/REPORT.md`, then `group_3_simulation.md` (the strategic simulation audit, E-02 to E-08: findings table, decisions with no home, things the auditor could not judge) and `sidecar_simulation.md` (stories S-220 to S-228 proposed for the simulation epics). `DECISIONS.md` and `DIRECTION_CHANGES.md` beside them hold what Westley ruled on that audit.
- The code-versus-bible discrepancies found on 2026-09-10 while the epics were written, each a `Q-` row in `docs/northstar/ambiguity_register.md`: dead `border_friction.py` (Q-041-01), diplomacy never initialised (Q-042-01), fixed 50-tick jump (Q-056-01), the duplicate time-limit table (Q-076-01), the opportunist boost never fed (Q-035-01), the 5-tick revolt chain (Q-040-01), the 6-chapter cap (Q-057-01), the chronicle category count (Q-067-01). Check each row's status: an answered row is the rule the C sim must follow; an open one is still a question.
- `docs/northstar/plans/archive/specs/2026-10-03-finish-loop-rulings.md` and ROADMAP section 3 "Finishing the MVP loop": F1 to F13, the scouts' questions about the live loop (event-threshold noise never rolled, collapse successor, campaign end, jump length unclamped, regional commander never created, four objective archetypes that cannot score, retention scope). Most are simulation questions still waiting on Westley; list them with your findings.
- `docs/northstar/plans/2026-10-01-a7-sim-profile.md`: the sim and serialise cost profile at 5,000 units (performance baseline, not behaviour).
- Tests that encode the equations today: `tests/csim/` (per-rule pytest over ctypes, `conftest.py` generated from `docs/northstar/spec_factory/signatures.toml`), `tests/transport/` (pipe frames), `tests/long/` (scale and determinism gates). Read `tests/csim/README.md` if present, else the test names: each names the `S-`/`R-` it proves.

## The tool this lane builds first

`docs/northstar/plans/archive/specs/2026-10-12-simviewer-plan.md`: Westley's 2026-10-12 order and the approved plan. A 2D simulation viewer (port of the legacy pygame `simulation/strategic_viewer.py`) that drives the real C sim over the pipe: every civilization and its regions in its colour, per-region graphs of the six values, sparklines over time, the events per region; tick mode at a chosen rate and mission mode that shows the region the sim chose, lets Westley pick one of the five outcomes, applies it, and jumps. Piece order in that plan: SV-0 (the one-field pipe contract change, `mission_end` optional `retention`, second Fable audit before anything builds on it), SV-1 session, SV-2 history, SV-3 viewer. Tests first by a different agent than the builder; `scripts/specfactory/pre_gate.sh` before every push; owner rows in `docs/northstar/plans/push/pieces.toml`; one landing clerk through the merge gate. The viewer is tooling, never in the game loop.

## Then: plan execution

With the viewer running, the lane does step 1 of ROADMAP 2b as a measured programme, one finding at a time:
1. Mission choice: run ten campaigns at ten seeds through mission mode; for each mission record the chosen region, archetype, urgency and relevance inputs (E-10 S-072 to S-074) and check the choice against the rule; a wrong choice is a finding with the seed and tick.
2. The chronicle's source: after each jump compare the chronicle entries with the delta stream's events, attacks, collisions and revolts (E-09 rules); an entry with no event behind it, or an event of the recorded significance with no entry, is a finding.
3. The equations: for each `ALG-` row in `algorithms.md` that has no `tests/csim/` test naming it, write the test (Westley's thresholds, never widened).
Findings go to a ledger table in this lane's report file (`docs/northstar/plans/archive/lanes/sim_lane_2026-10-12/README.md`, create it), one row each: what the rule says, what the sim did, seed and tick, the proposed fix as a piece. Fixes are built as pieces only after Westley reads the row; a rule question is a `Q-` row with candidates, never a guess.

## Rules that bind this lane

CLAUDE.md whole, then `docs/northstar/plans/workflows_2026-10-07/rules.md`. In particular: the stochastic equations stay verbatim; determinism is a contract (no fast-math, no platform transcendentals, no hash-order or wall-clock input); contracts (`csrc/ouroboros_sim.h`, `signatures.toml`, pipe frames) change only as their own documented piece; every file has one owner in `pieces.toml`; new code in new files; builders never edit tests; Westley owns every threshold; read `origin/main`; every spawn names its model and sub-agents never spawn; report once, at the end, in a schema. Westley's standing word on tuning (2026-10-12): find and show first, change only what he has seen.
