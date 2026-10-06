# How Ouroboros Manifold is built

This page describes the method behind the game: what is decided first, what is tested before anything is built, and how a design question gets an answer. It is written for readers outside the project. Every claim comes from the project's own documents, and where those documents are silent the page says so.

## 1. The goal, in one sentence

The game's own statement of what it is for (the hub of the design bible):

> "Missions are won or lost on positional skill. A smaller force that understands surrounds, high ground, and the 2.5D layer and vision system beats a larger force that does not."

Westley, the game's designer, put the same goal as the target of the whole method (2026-10-01): "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force". And: "We get to this goal by tuning all the variables we laid out such that that sentence becomes a reality."

Everything below exists to make that sentence testable.

## 2. Tests are the spec

The project is long-term, with no ship deadline, and works on one story at a time. Claude designs and tests; agents build. The simulation is written in C, and its stochastic equations are kept verbatim from a named list. Godot 4 is the client, talking to the simulation over a JSON pipe.

Requirements form a hierarchy with stable ids:

| Level | Id | What it is |
|---|---|---|
| Epic | `E-##` | a feature area, one file |
| Story | `S-###` | one behaviour the player sees, in the player's words |
| Rule | `R-###-##` | one acceptance criterion in Given/When/Then form; each maps to at least one test |
| Question | `Q-###-##` | an open question with two or three candidate answers; it blocks building |

The rules the project holds itself to:

- **A story is built only after it is Ready.** Ready means: its epic's end-state is written (what is true in the traces and what the player sees on screen); every input and output is mapped; the register has no open question for it; its scale numbers are confirmed; a visible story has a reference; and, where the plan marks the feature as needing a prototype, the prototype is approved.
- **Every story exists as failing tests before any code.** The tests live in paths builders cannot edit, and each names the story or rule it proves.
- **Builders never edit tests.** A test is fixed only when it is classed as a test defect, with a row in a ledger saying why.
- **Every detector ships with a positive control**, a case built to make it fail. Every system has an isolation test and an integration test. In the project's words, "a QA pass that cannot fail is not a QA pass".
- **Westley owns every threshold and tolerance.** An invariant's scope may be narrowed. Widening a threshold, extending a window or loosening a tolerance needs him, and a real finding is never reclassified as a skip.
- **The game is deterministic by contract.** The same seed and command stream give a byte-identical trace on every platform: no fast-math, no platform transcendentals, no hash-order or wall-clock input.
- **Behaviour must be wired, not just tested.** Something a rule says happens in play must be reachable from the tick, the time jump or a pipe handler, not only from a test. The project records why: a fast parallel push left 480 of 682 tested symbols unreachable from play because nobody owned the wiring.

The origin of the Ready gate is a cautionary example the project keeps on record. An earlier version of the game had a vertical layer system meant to be its defining mechanic. It existed in code, but units never changed elevation by layer, and in testing no different layer vision was observable: the feature was never defined clearly enough to be implemented. The gate is the fix.

## 3. The prototype gate: seen before planned

Anything judged by eye or by feel (how a thing looks, moves, lays out or plays) gets a rough prototype that Westley approves before any plan, story test or workflow is written for it. The prototype is disposable. What it produces is his decisions.

There are two kinds, kept apart:

| Kind | What it is | Used for |
|---|---|---|
| Mockup | a Godot scene with placeholder art | things he must see |
| Instrument | a harness that runs a rule and prints a page of charts | things he must read |

A pass is one spec of under a page, one build, screenshots or a page committed, then Westley's review. His words are recorded verbatim, with the architect's reading beside them, and the next pass follows from those. Only Westley approves a pass. If three passes go by without approval, building stops and an options page is written with two or three different directions to choose from; the count restarts on the direction he picks.

A prototype may skip determinism, budgets, tests and polish, and the game never loads it. After approval the game code is built fresh, tests first; the prototype's code is "a reference, not a source".

## 4. The skill lab

The goal in section 1 is a claim about skill, so the project measures skill directly, in a lab that runs the real simulation.

**What decides a fight.** The principle the lab rests on, in Westley's words: "the differentiator is **can your unit get shots off**." What matters is how many units on each side can fire, and for how long. With everything identical, the larger force wins; that is a control, not a scenario, since real matches have five layers, different vision and uneven ground.

**Five skills.** Each is a kind of understanding the game should reward:

| Skill | The skilled player |
|---|---|
| Landscape | fights where terrain limits how many enemies can fire |
| Formation | arranges units so more of them fire at once |
| Layers | uses the layer actions on purpose: the ping, going dark, reach by unit type |
| Enemy position | finds the enemy first and fires first |
| Unit-type matchup | puts each type against the type it beats |

A skill has no fixed worth. A play is worth what it does to the firing count in that situation.

**How a play is scored.** A skill is represented by a scripted skilled play and a scripted naive play (the naive play is measured two ways, as a blob and as a line abreast). Each skilled play has a counter, because "a skilled player only takes a battle that they can win". The score is the margin, one signed number per fight: the share of one side's strength left, minus the other's. A win rate would be a probability, and the simulation has no dice.

**Why break-even in whole units.** The headline figure is a break-even in soldiers, not a ratio: for example, 16 units beat 17 enemies and lose to 18. Beating means ending ahead by a margin, not a wipe-out. On why not a ratio, Westley (2026-10-01): "it depends on the number of units that can get shots ... not a basic ratio". Beside every result the lab reports the number of units firing on each side through the fight, which is the explanation for it.

**Two labs.** Every era is space or ground, a formal property of the era (the game keeps the two kinds cleanly separate). The space lab, where every unit flies and the five layers are free, is the one being built and run. The ground lab waits for the simulation to have ground. Land maps are reported, and do not block, until walking units exist.

**What passes.** The lab judges a rule set against ten conditions, among them: a mirrored fight is won by the larger force; skill wins the firing count on most maps that offer the play; the result follows the firing count; skills stack; no skill dominates and none is dead; counters exist; and the result holds across most space maps. The pass marks are drafts. Westley has not confirmed them, so this page does not state them as final.

**One action that cannot be scored by a fight.** The ping reveals a layer and place for a moment and deals no damage. Two forces that ping and then walk into each other fight exactly as if nobody had pinged. So it is measured in two stages: a search with no fight, run thousands of times against hidden placements, then a few fights that compare a defender who knew the enemy's route with one who guessed. The value of a ping policy is the share of placements found with enough warning, times what knowing is worth in whole units.

Results are read in small batches. Each batch is one page of charts whose heading states the finding in soldiers. Westley's reaction to the first, harder-to-read draft was "I had to stare at it to figure out what it meant", and to the redesign, "looks much better".

## 5. Workflows and the pre-flight

Parallel agent work runs through scripted workflows. The project's rule is that a workflow enforces nothing by itself; "the spec and the script do". Before any workflow launches, in this order (quoted from the project's working rules):

- **Pre-flight:** "list every precondition each lane rests on (an API and its exact shape, a setting the harness can set, a base that builds and its red tests, owner rows for every file, free slots in shared enums or tables) and check each by reading or running, never from memory. 'Quick' shrinks the pre-flight, never skips it."
- **The spec** is written from the pre-flight: every file and function named, every shared interface fixed in full, every number given or marked as a named draft, a positive control per mechanism, and lanes on disjoint files.
- **Audit:** "a fresh Sonnet auditor that has not seen the author's reasoning reads the spec against the bible and the code and tries to refute it". A contract-level spec gets a second review. Westley approves after the audit.
- **The script:** tests first, by a different agent than the builder, red for the stated reason; a gate agent per lane returning pass or fail with the decisive line; stop rules in every brief; a kill rule; a baseline recorded before the first build.

Three structural rules keep this cheap and safe. Every file has one owner at a time. New systems go in new files behind a frozen header, with the wiring as its own small piece, landed one at a time with a playthrough after each. And the project prefers many short-lived agents with small contexts to a few long ones, because the cost is context size times the number of calls.

## 6. The merge gate and the regression tiers

"Nothing broke" is checked at three levels.

| Tier | When | What |
|---|---|---|
| 1. Landing | every merge | the merge gate script; passing means no stage rejects |
| 2. Integration check | after each prototype is integrated, after multiplayer is wired, and before a plan is marked finished | one script runs eleven suites in turn, each under a memory cap and a timeout, and compares the result with the newest earlier baseline |
| 3. Play check | the same moments as tier 2 | three QA sessions on the new main, each playing at least one mission to its end, with no new error fingerprint in the campaign ledger |

The integration suites are the C simulation tests, the scale tests, the pipe transport tests, the state-level QA tests, the harness tests, the desktop client tests, the long seeded runs, the Godot scripts, the mockup checks, the multiplayer tests and a trace comparison between two builds of the simulation.

A regression is any of: a test that passed in the previous baseline and fails or aborts now; fewer tests in a suite; a long-run seed whose end or length changed; or a multiplayer or trace check that passed and now fails or is absent. Timings, scale-budget failures and mockup time-budget failures are reported and not counted. Each plan declares up front what it expects to change; anything else that moves is a regression.

The play check is run by hand today; there is no command for it. The project's sources do not describe the individual stages inside the tier-1 merge gate, so this page does not either.

## 7. The bible, and how a ruling is recorded

The design bible is the source of truth for what the game is: a short hub, a story catalog, one file per epic with its rules, reference screenshots and notes from games the designer points at, and a file of named equations that is the contract for the C rewrite.

- **Rewrite, never append.** When direction changes, the old text is deleted. The bible always describes what the game is now; history lives in snapshots and in version control.
- **Ambiguity is flagged, never guessed.** When something is under-defined, a question row is added with two or three candidate answers and a recommended one. An epic with an open question is not built. Local builders never see an open question, only resolved rules.
- **A ruling is recorded where it applies.** Westley answers a batch of questions by approving the recommended candidates or overriding by id. The epic's rule is rewritten to match, often quoting him with the date, and the question is closed. A prototype's approval is recorded verbatim in that topic's research record, and the plan then cites it.
- **Small decisions are delegated.** Trivial design choices, ones nothing a player would notice and nothing else depends on, are decided without a flag and written into the rule text.
- **Documents must not drift.** A change in behaviour rewrites every document claim it makes wrong, in the same change.

The method documents themselves have a precedence rule: where another document disagrees with the method directory, the method directory wins; where anything disagrees with the hub of the bible, the hub wins.
