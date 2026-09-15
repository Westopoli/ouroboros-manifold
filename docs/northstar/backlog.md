# Product backlog (Stage 4 — story status tracker)

The single place that says where every story is in the pipeline. Sprints pull only from **Tested**. Claude's planning job each cycle is to move stories toward Tested faster than Agora drains Tested; if Tested runs dry, Agora idles and the escalation flag notes it.

**Status vocabulary** (from `agile.md`): Spec'd (written, gate not passed) → Ready (Definition of Ready met) → Tested (failing tests authored) → Queued (Agora task exists) → Building (Agora worktree active) → Built (merged, tests green) → Revised (built then the story changed; back to Spec'd for the changed rules) → Killed.

Story text and rules live in the epic files and `docs/bible/stories.md`; flag answers in `docs/northstar/ambiguity_register.md`; e2e definitions in `docs/northstar/e2e/`. This file tracks status only.

## Build order (dependency ladders)

Sprint 0 (toolchain) precedes all game epics. Then:

- **Strategic sim:** E-02 region fields/composites/drift → E-03 world gen → E-04 events → E-05 faction agents → E-06 diplomacy/tech → E-07 lifecycle → E-08 generational → E-09 chronicle.
- **Tactical sim:** E-11 units → E-13 movement → E-12 fog → E-01 layer system (deferred behind a single-layer prototype) → E-14 enemy macro → E-15 reinforcement/hazards → E-18 visual style.
- **Map/gen:** E-17 map generation, E-10 missions (feed tactical).
- **Integration:** C pipe (Phase 1) → GDExtension (Phase 2).
- **Client:** E-16 camera/HUD/world view — only after the sim ladders are green. E-19 multiplayer, E-20 multi-era/monetization, E-21 offline AI pipeline: later.

## Epic status

| Epic | Stage | Status | Blocker before tests |
|---|---|---|---|
| Sprint 0 toolchain | 4 | Building | Contract + tests landing; C impl + installs + Agora project remain |
| E-02 region fields & drift | 5 | Ready → Tested (in progress) | none — tests being authored |
| E-03 world generation | 3 | Register-clean | Stage-3 pass (fold 2026-09-14 answers, author e2e, confirm scale) |
| E-04 events & chains | 5 | Tested (2026-09-14), S-031 Spec'd | S-026..S-030: 31 rules, 44 tests red; S-031 waits on the Python pacing measurement |
| E-06 diplomacy & technology | 3 | Register-clean | Stage-3 pass; confirm deferrals safe |
| E-17 map generation | 3 | Register-clean | Stage-3 pass |
| E-08 generational structure | 3 | Register-clean (mixed) | Stage-3 pass; setup UI TBD-design (non-blocking for sim) |
| E-09 chronicle | 3 | Register-clean (mixed) | Stage-3 pass; galaxy-view reference pending build fix |
| E-10 missions | 3 | Register-clean (mixed) | Stage-3 pass; briefing/debrief UI TBD-design |
| E-11 units & combat | 3 | Register-clean (mixed) | Stage-3 pass; references derive from E-18/E-13 |
| E-12 fog & sensors | 3 | Register-clean (mixed) | Stage-3 pass; fold fog-memory-toggle into a story |
| E-01 layer system | — | TBD | Single-layer prototype + layer-options design phase; Q-E01-08 |
| E-05 faction agents | 5 | Tested (2026-09-14) | none — 58 rules, 67 tests red in `tests/csim/`, cards 202–207 queued behind 201 |
| E-07 civilizational lifecycle | — | TBD | Q-054-01 (terminal conditions, deferred) |
| E-13 movement & command | — | TBD | 5 flags |
| E-14 enemy macro behavior | — | TBD | 2 flags |
| E-15 reinforcement/supply/hazards | — | TBD | 6 flags + references |
| E-16 client camera/HUD/world view | — | TBD | 5 flags + UI design phase |
| E-18 visual style | — | TBD | 4 flags + define the T2 "matches register" check |
| E-19 multiplayer | — | TBD | 8 flags (largest gap) |
| E-20 multi-era & monetization | — | TBD | 8 flags (era-feel pinned for later) |
| E-21 offline AI pipeline | — | TBD | 5 flags |

## E-02 stories (the active epic)

| Story | Status |
|---|---|
| S-012 four fields and two composites | Ready |
| S-013 armies cost money and grow in peace | Ready |
| S-014 people make money, unrest and overreach cost it | Ready |
| S-015 friendly neighbors make you richer | Ready |
| S-016 hardship breeds unrest, unrest burns itself out | Ready |
| S-017 population grows slowly and starves slowly | Ready |
| S-018 boom and bust | Ready |
| S-019 the floor is not safe | Ready |
| S-020 same seed, same galaxy | Ready |

These move to Tested when the `tests/csim/` suite lands (red), then to Built when Agora's `csrc/*.c` makes them green. Other epics get per-story rows as they pass Stage 3.
