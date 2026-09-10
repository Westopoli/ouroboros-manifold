# Stage 1 Audit — Ledger

Verdict key: keep, kill, rewrite, defer, unsure. `unsure` is not allowed to survive — every row must resolve before Stage 1 is done.

## Progress

- Files done: none complete.
- Files in progress: `game_bible.md` (hub) — batch 1 of ~4-5 estimated, covering lines 34-76 (Vision and Identity, start of Game Shape at a Glance).
- Files not started: `bible_design_vision.md`, `bible_simulation.md`, `bible_combat.md`, `bible_world.md`, `bible_missions.md`, `bible_chronicle.md`, `bible_antagonist.md`, `bible_ai_pipeline.md`, `bible_animation_strategy.md`, `priority_queue.md` research-only list, known-stale-claims sweep.
- Total rows so far: 20 (A-001 through A-020), all pending verdict.
- Cross-check pass: not started (will run after every file is walked).
- Algorithm pass: not started.

## Batch 1 — `game_bible.md`, Vision and Identity + Game Shape (lines 34-76)

| id | source | type | built | verdict | note |
|---|---|---|---|---|---|
| A-001 | game_bible.md:38 | story | built | | "single-player sci-fi strategy game" — directly conflicts with vision_v2.md Q1/Q3 (multiplayer confirmed). Pre-flagged rewrite target. |
| A-002 | game_bible.md:38 | rule | built | | Player is commander, not king/god — given impossible task by civ with own plans, politics, momentum. Matches vision_v2.md Q3. |
| A-003 | game_bible.md:38 | rule | built | | World doesn't revolve around player, moves on its own, player is "a piece of the puzzle." Matches Q3. |
| A-004 | game_bible.md:40 | mechanic | built | | Generational chain of missions, each mission a chapter, time jumps forward decades/centuries between chapters, world evolves via simulation. Matches Q5. |
| A-005 | game_bible.md:40 | mechanic | built | | Player returns each chapter as new character (descendant/successor/shaped by consequences); career across generations IS the story. Matches Q5. |
| A-006 | game_bible.md:42 | story | unknown | | Core Fantasy frames each mission as having "a deadline." Unclear if this is enforced mechanically or just narrative framing — flag for confirmation during item walk of bible_missions.md, not resolving here. |
| A-007 | game_bible.md:44 | story | built | | Mission difficulty "perhaps impossible," world keeps turning during mission (factions rise/fall, threats emerge, history happens around player). Matches vision generally. |
| A-008 | game_bible.md:46 | story | built | | Mission outcome shapes but doesn't control time-jump world changes; player returns as someone new in a world that "remembers what happened even if your new character doesn't fully understand it." Matches Q5's "story and simulation both affected" answer. |
| A-009 | game_bible.md:48 | story | built | | Over many chapters, player experiences civilization's rise/crisis/potential-extinction from inside, not above; always one person with limited tools in a genuinely uncertain universe. Matches vision. |
| A-010 | game_bible.md:52 | story | unknown | | **IP FLAG, not a design call.** "The Foundation feeling. You're not Hari Seldon. You're Hober Mallow." Both are literal Asimov character names — violates CLAUDE.md "No IP exposure" rule directly. This line is a mandatory kill/rewrite regardless of your design verdict on the underlying feeling it's describing (the "tragedy of understanding" concept itself can stay; the character names cannot). |
| A-011 | game_bible.md:56 | rule | unknown | | "Not Stellaris" — don't manage a whole empire's economy/diplomacy/military, you command a task force. Matches Q3. |
| A-012 | game_bible.md:57 | rule | unknown | | "Not Total War" — no separate campaign map / battle map split, one continuous world. |
| A-013 | game_bible.md:58 | rule | unknown | | "Not a god-game" — don't hover above pressing buttons, you're in it. Matches Q3. |
| A-014 | game_bible.md:59 | aspiration | unknown | | Closest-comparisons list: FTL (limited resources/hard choices), Crusader Kings (emergent narrative), Homeworld (spatial command), Dwarf Fortress (living world doesn't care), Halo Wars (unit control: heavy individual/light squads), Immortal: Gates of Pyre (RPS-with-exceptions, accessible depth). Vision_v2.md Q1/Q8 names a different comp set (SC2, AoE3, Halo Wars, Art of Rally, Halo CE). Overlap on Halo Wars only — this list likely needs reconciling/rewriting against the confirmed vision comps, not necessarily wrong, but stale relative to the new interview answers. |
| A-015 | game_bible.md:63 | story | built | | Asimov's Foundation series is primary narrative/thematic inspiration — vast civilizational arcs, individual action vs. historical momentum, reading currents in a world too large to control. No character names in this line (unlike A-010) — IP-safe as written. |
| A-016 | game_bible.md:63 | story | built | | Game "set thousands of years in the future, in a world of humans," player experiences rise/fall from inside. **Contradicts Q10** (MVP = 3 eras, past/present/future) — this line frames the whole game as one far-future sci-fi setting only. |
| A-017 | game_bible.md:65 | aspiration | partial | | Immortal: Gates of Pyre is key source for combat/accessibility philosophy — low skill floor, high skill ceiling, RPS-with-exceptions unit design. Compatible with Q6 (skill ceiling vision) but Q6 names SC2 as the explicit heavy comp for positional mastery — worth confirming both stand together, not a straight contradiction. |
| A-018 | game_bible.md:71 | rule | partial | KILL (pre-resolved) | "Pause-and-command tactical... not turn-based... not an RTS in the marketing sense — pacing is deliberate, player encouraged to pause and read the field, engine never measures player against the clock." Directly contradicted by vision_v2.md Q4 correction: full real-time, no pause, SC2-style, confirmed by you mid-session. Marking pre-resolved kill; say so explicitly or override if you want a different call. |
| A-019 | game_bible.md:75 | mechanic | built | | Tactical layer — missions: force groups on procedurally laid-out map, one engagement per mission, 30-60 min of continuous gameplay, simulation stopped during missions. Split from the "pause-and-command" wording in the same line (that half is A-018's kill target) — this half (engagement structure/duration/sim-paused-during-mission) is a separate claim, still live. |
| A-020 | game_bible.md:76 | mechanic | built | | Macro layer — batch-tick simulation of factions/regions/history, not real-time, runs forward in deterministic ticks between missions, produces state snapshot + chronicle. Matches built code reality (sim runs as child process, tick-based). |

Reply with verdicts (terse is fine, e.g. "1-9 keep, 10 kill per IP rule, 14 rewrite, 16 rewrite to multi-era, rest keep"). I'll record and move to batch 2 (rest of Game Shape at a Glance: the cycle, tempo controls, rewind).
