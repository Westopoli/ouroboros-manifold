# Batch A follow-up 9: a sim-viewer run contrasted with the bible's rules

Written 2026-10-21 for Westley. It answers point 9 of Batch A (2026-10-18): "I'd like to see it in action, hand me the command to run it myself, I'd also like an analysis of the simulation that I see that plays out, the analysis will contrast what actually happens against the rules written for the simulation engine in the bible, and flag any instances of rules not being followed."

Short version. The command is in section 1. I drove the viewer's own state machine headlessly for the length of its 10-minute view in both modes and checked the stream against the bible. Twelve findings are rules not followed (section 3), three smaller ones sit beside them, and the rest of what a run can check holds (section 4). The two that change what you see most: after a conquest nothing seethes (Conquest Unrest never fires) and an overgrown empire never fractures on its own (the admin revolt chain never starts); from the 20th jump the chronicle prints 11 to 16 entries, nearly all about the family, where the bible says at most 10 and that the first is your mission. "Supply" in your list is the faction budget (E-05 S-033); E-15's supply is a mission mechanic the strategic viewer never shows.

## 1. Run it

From your main checkout, once to build the debug pipe (about 20 seconds, pygame is already in that `.venv`), then either mode:

```
cd ~/Projects/ouroboros-manifold
make pipe/ouroboros_pipe_dbg
.venv/bin/python -m scripts.simviewer --seed 1 --n-regions 80 --rate 10
.venv/bin/python -m scripts.simviewer --seed 1 --n-regions 80 --rate 10 --mode mission
```

What I verified: the pipe builds from a fresh worktree of main, and the same launch path (`--shot DIR`) renders both modes headlessly in 1.2 seconds. What I did not exercise: the live window and its key handling (no display here).

Things to know when you press keys (from `scripts/simviewer/README.md` and `viewer.py`):

- It starts PAUSED. SPACE runs; RIGHT is one tick; `[` and `]` change the rate.
- Tick mode never takes a time jump; it only steps one tick at a time. Jumps, chronicles, commanders and chapters appear only in mission mode (M toggles).
- Mission mode needs a key per mission: press 1 to 5 (band 0 to 4, total failure to total success) or 0 (refuse), then RETURN three times: start the mission, resolve it, jump 50 ticks. Pick 1 (total failure) shows a red MISMATCH, a documented gap (SV-0).
- The sidebar's faction list and the stance rows are affected by finding J below until that is fixed.

## 2. What the run showed, in player terms

Seed 1, 80 regions, 15 factions, the viewer's feature set. The world you meet is already 20 ticks old (the hidden opening jump); you are faction 0 with six regions and seven empty regions sit between the factions.

Tick mode, 6,000 ticks (10 minutes at rate 10). All seven empty regions are colonised by tick 40. From then on it is a permanent brawl: 53,187 attacks (8.9 per tick), 9,132 of them conquests, so the average region changes hands every 53 ticks. Faction 11 swells to 24 regions at tick 3,909 and holds 19 at the end; you hold between 4 and 6. Revolts keep birthing small nations (54 breakaway factions over the run) and they are absorbed again. By tick 770 all 15 factions are at the technology cap of 100; Knowledge Lost then knocks a faction down five points 296 times (about 2.5 per 50 ticks across the galaxy). Budgets sit at about 10 to 27, except three hoarders (63, 78 and 145 at tick 3,020).

Mission mode, 66 missions with their 50-tick jumps (10 minutes at one advance per second). The campaign runs from tick 20 to tick 3,320 and from chapter 1 to chapter 67. Missions came from six of the ten archetypes (Siege Breaking 16, Assault 13, Evacuation 12, Containment 12, Defensive Stand 9, Multi-Front 4), always in or next to your territory: 52 of the 66 in your own rim regions 57, 66 and 74, five at home (region 0), nine in neighbouring enemy regions (76, 71). All five winning Assaults handed you the region. The scroll printed 10 entries per jump for the first 19 jumps and then 11 to 16 (16 in 44 of the last 47; 934 entries over 66 jumps), nearly all of them lineage entries; the commander stopped changing at chapter 17.

Determinism held: two runs of the same session, tick and mission, are byte-identical, and interleaving a snapshot request after every tick does not change the 300 checksums on cadence ticks.

## 3. Rules not followed (flagged first)

Dump references: `T` is `tick_a.jsonl` (tick mode, 6,000 ticks; 1-based line = tick - 17), `S` is `tick_snap.jsonl` (3,000 ticks with a snapshot after each tick; step line = 2 x tick - 38), `M` is `mission_a.jsonl` (66 missions). Paths are in section 6.

**A. R-038-04, Conquest Unrest (E-05 S-038, ALG-22). NOT FOLLOWED.**
Expected: each conquest queues Conquest Unrest with probability 0.60, due 4 to 8 ticks later, tension +6 on the region.
Observed: 9,132 conquests, 0 Conquest Unrest events (template 10); about 5,480 expected.
Evidence: T line 4 (tick 21): faction 6 conquers region 60 (`conquest:1`). Region 60's events over ticks 21 to 31: tick 23 Famine (chain 201), tick 27 Regional Revolt, tick 31 Revolt Entrenched; nothing in the 25 to 29 window.
Cause: `csrc/resolve.c:516` queues template id 100 straight into the event queue; `csrc/events.c:691` drops any due entry whose id is not below the loaded library size ("unknown template: drop defensively"), so it vanishes silently.

**B. R-040-03, R-040-05, R-027-05, the admin revolt chain (E-05 S-040, E-07 S-049). NOT FOLLOWED.**
Expected: a triggered admin roll queues Admin Separatist for the next tick and the chain ends in a Breakaway at tick + L (L 3 to 8), which creates a faction.
Observed: 8,420 triggered rolls (the roll itself is right, see section 4) and 0 events of templates 21 to 25.
Evidence: T line 13 (tick 30): `revolts:[{region:76, faction:0, roll:0.00169}]`. Region 76's events at ticks 31 to 39: tick 33 Revolt Entrenched (spawned), tick 34 Famine, tick 39 Regional Revolt; no Admin Separatist at 31, no Breakaway at 33 to 38.
Cause: same drop as A, template id 101 written at `csrc/friction.c:166`.
Effect: E-05's "empires fracture" works only through Regional Revolt, not through size. The invariant "no faction above 20 regions for more than 500 ticks" still held (longest 55 ticks, faction 11), carried by conquest churn.

**C. R-065-01, R-065-05, Q-070-01, entry count and caps (E-09 S-065). NOT FOLLOWED.**
Expected: at most 10 entries, at most 2 per category, lineage clusters capped at 2 (Q-070-01, closed).
Observed (M): entries per jump 10 (19 jumps), 11, 15, 14, then 16 in 44 jumps; 47 of 66 jumps exceed 10. Lineage entries per jump run from 3 to 16 (more than 2 in all 66); 51 jumps use a category more than twice. M cycle 22 (ticks 1120 to 1170): 16 entries, 6 lineage_thrived and 10 lineage_quiet.
Cause: `csrc/chronicle.c:1729-1747`: all consequence and lineage clusters are taken first, up to `CHRON_MAX_FINAL 16` (`:135`), with no category cap and no Q-070-01 cap; the 10-entry limit and the category cap apply only to the remaining clusters. The family grows 2.5 times per 50-tick jump under R-059-01, so the page fills with it.

**D. R-065-02, the scroll opens with what your mission did (E-09 Purpose). NOT FOLLOWED.**
Expected: entry 1 is the consequence cluster of the mission just played (success, mixed or failure register).
Observed (M): 0 entries of categories 30 to 33 in 934 entries; entry 1 is a lineage entry in all 66 jumps (lineage_succession 28, lineage_thrived 27, lineage_military_action 11). Missions did change the region (section 4, R-078-01), so either the consequence flag of R-078-06 is not set on the jump's events or no consequence cluster is built from it.

**E. R-069-05, a keyframe at every ownership change (E-09 S-069). NOT FOLLOWED (half).**
Expected: a keyframe inside every entry's range and one at every ownership change.
Observed (M): every entry holds a keyframe (0 misses of 934), but the 66 jumps hold 1,573 two-tick intervals in which an owner changed and only 601 contain a keyframe; a jump carries 4 to 14 keyframes.

**F. R-039-05, R-039-06, Q-039-01 (a), same-tick attackers on one region (E-05 S-039). NOT FOLLOWED (ruled, not built).**
Expected: several factions striking one region on the same tick collide; Q-039-01 was closed on 2026-10-18 as option (a), matured telegraphs and immediate attacks grouped in one resolution list.
Observed: 0 collision records and `collision:0` on all 53,187 attacks. In S, 5,712 (tick, region) pairs took two or more attacks and 1,941 took two or more immediate attacks from different factions. Example T line 4 (tick 21): factions 6 and 8 both attack region 60; two separate attack records, 6 conquers.
Cause: `csrc/collision.c:216` skips every owned target ("R-039-05 out of scope (Q-039-01)"); only colonise races can collide and the empties are gone by tick 40.

**G. R-012-06, ALG-10, capacity penalty threshold (E-02 S-012). NOT FOLLOWED.**
Expected: the capacity penalty of 0.70 applies below population 15.
Observed (T): 32 region-ticks with population 15.02 to 19.85 carry the penalty anyway. T line 3 (tick 20 snapshot), region 60: economy 18.96, population 17.11, military 5.32, sent capacity 7.40; the formula gives 10.58.
Cause: `csrc/region.c:326` tests `< 20.0`; `om_constants.h` already defines `OM_CAP_POPULATION_THRESHOLD 15.0`. The rule's own example (population 10) passes either way.

**H. R-012-01, the invariant that fields stay in [0, 100] (E-02, E-04). NOT FOLLOWED.**
Observed (T): 34 region-ticks with population 100.02 to 100.04, all 34 on the tick a breakaway is born (a faction-creating event in that region). T line 387 (tick 404): region 48, Revolt Entrenched creates faction 16, population 99.983 before, 100.0204 after.
Cause: `csrc/lifecycle.c:160` rebuilds the pre-event population as `population - delta` without clamping.

**I. R-033-01, ALG-17 (E-05 S-033), with R-046-05 (E-06 S-046). NOT FOLLOWED as written.**
Expected: budget gain = sum of (economy - 8) x 0.025 over owned regions; R-046-05 says nothing consumes the economy multiplier.
Observed (S): in 8,559 of 8,559 clean faction-ticks the gain is that sum times the ALG-26 economy multiplier (1 + tech/100 x 0.02 to 0.08 by archetype), exact to 1e-9; the plain formula matches 3. At tech 100 a fortifier earns 8 percent more than R-033-01's example says.
Cause: `csrc/faction.c:260`. Q-048-01 (closed) says the multiplier is wired into economy growth (ALG-05); it also scales the budget, which the rule text does not say. A decision for you or the Architect: rewrite R-033-01 or drop the multiplier here.

**J. E-05 and E-07 Outputs, faction entries in the strategic snapshot. NOT FOLLOWED (wire).**
Expected: the snapshot's `factions` is one entry per living faction (R-032-01); removals and births are observable there (E-07 Outputs).
Observed (S): in 699 of 3,000 snapshots a faction that owns regions is missing from the list, 68 attacks come from unlisted factions, and 21,698 stance cells read 4294967295 (an invalid slot). S line 869 (snapshot 453): the list ends at id 16 with id 15 listed (budget 8.2, no region) while region owners include 17.
Cause: `csrc/pipe/om_pipe.c:417` (snapshot) and `:731` (delta) loop `0 .. om_faction_count`, which is the number of used slots (`csrc/lifecycle.c:374` decrements it on removal), but a removed breakaway frees a low slot while higher ids live on. The sim itself keeps acting (the unlisted faction attacks); the viewer's faction sidebar is what shows it wrong.

**K. R-026-01, R-026-02, R-026-05, trigger state of a new colony (E-04 S-026). NOT FOLLOWED (minor).**
Observed (T): 21 firings, three per colonised region, on the first tick of each of the seven colonies: Garrison Collapse, Labor Shortage and Infrastructure Decay, with no field crossing anything. T line 7 (tick 24): region 73, owner -1 two ticks earlier, events at templates 0, 11 and 13. The region was empty (fields 0) the tick before, so the stored "was past the line" flag was never primed.

**L. R-057-01, R-060-03 and the E-08 invariant "the commander is a living ledger character". NOT FOLLOWED (inferred).**
Observed (M): from jump 16 on the commander id is 100003304 through the last jump (51 jumps, about 2,550 ticks) while the lineage id changes at every jump (by exactly 3 in 49 of the 50 steps). Lifespans are 150 to 350 ticks and natural deaths run at each jump end, so that commander cannot be alive. The ledger is not on the wire, so this is an inference from the ids.
Possible cause: the ledger is full: `GEN_MAX_CHARACTERS` is 4096 (`csrc/generational.c:180`, creation returns NULL at line 698), below the 5,000 characters E-08's scale line names, and R-059-01 multiplies the family by 2.5 per 50-tick jump. Once full no new commander could be seated, and the same growth feeds C.

Smaller items. (1) R-045-07: each Knowledge Lost event record is stamped one tick after the tech drop (150 of 150). (2) `docs/architecture.md` says the six region numbers are "two decimals"; the pipe sends the four fields at full precision and rounds only stability and capacity, which is what R-012-01 asks, so the doc is the one that is wrong. (3) R-021-01 asks for 250 to 400 regions; the viewer and `autoload/c_bridge.gd:23` pin 80. With `n_regions` 0 the seed-1 draw is 284, so the generator follows the rule and the launch default does not.

## 4. Rules checked and consistent

| Rule | Expected | Observed |
|---|---|---|
| R-012-02, -03, -04, -05, R-012-07 | stability and capacity formulas; empty regions all zero | 480,020 region-ticks: stability 0 mismatches; capacity 0 other than G; 0 empty regions with numbers |
| R-019-01, R-014-04 | economy never below 8.0 under drift, friction, events | 0 inhabited region-ticks below 8.0. R-019-02's below-8 conquest state never shows at a tick end (the same tick's drift re-floors it) |
| R-030-01, R-030-03 | the 26 templates' effects, integers in [-4, 6]; faction creation only for two templates | 4,692 table events (plus 296 Knowledge Lost, outside the table), every delta equals the S-030 table, `creates_faction` only for templates 5 and 25 |
| R-037-01, -02, -03, -04 | breakthrough, contested, repelled shapes; tension capped +30 | all 53,187 attacks fit (1,135 / 37,304 / 14,748); largest breakthrough tension 30.0 |
| R-038-01, R-038-03 | conquest only when post-damage military < 5, never on repelled | 28,508 single-attack targets: 0 conquests at 5 or more; all 9,132 conquest flags show the owner change to the attacker; 332 start-of-tick predictions of a conquest that did not happen (1.2 percent) need the unreported same-tick reinforce records to settle |
| R-036-03 | a telegraph declared at t resolves at t + 3, sits pending at t + 1 and t + 2 | 11,893 telegraphs: declared tick right, pending right, resolved right; the 6 exceptions had a breakaway attacker with no regions left (dropped, as the invariant allows) |
| R-040-01, R-040-02 | admin roll chance 0.001 + 0.0005 x (regions - 4)^2 | 8,420 triggers against 8,422.3 expected; every roll below its chance |
| R-027-01, R-027-06 | spawn delay inside [a, b]; chain tag unique per start | 1,654 spawned events: 1,648 trace to a legal parent in the window, the other 6 are ticks 21 to 27 (parents fired in the hidden opening jump); 3,038 root tags, unique and increasing |
| R-026-01, R-026-02 | threshold events fire on a crossing only | 2,046 threshold firings, 0 with the field on the wrong side of the line beyond the 10-point noise; only K's 21 stand out |
| R-029-03 | revolt cooldown 12 ticks | 922 repeat revolts in one region, 0 inside 12 ticks |
| R-049-01, R-049-02 | an Entrenched revolt forms a nation with probability about 0.725 and only at population 25 or more | 824 events, 750 below population 25 (no nation); about 51 formations expected from the 74 eligible, 54 observed |
| R-051-02 | a lone breakaway of 50 or more ticks is absorbed by its strongest bordering faction | 31 hand-overs away from a breakaway without a conquest: 24 are that absorption (counting the breakaway's regions at cleanup time, after a same-tick conquest or revolt), 7 are a revolt in a breakaway region birthing a new nation; 0 unexplained |
| R-045-01, R-045-03, R-045-07, R-045-08 | tech grows 0.35 x avg economy x max(0.3, avg population); cap 100; falls only by Knowledge Lost, 100-tick cooldown | 4,518 uncapped clean ticks within 0.002 (68 more are the cap); max tech 100.0; in S all 150 falls of the 15 starting factions are Knowledge Lost (about -5), at least 102 ticks apart per faction; 142 of 152 events show the stated eligibility in the dump, 10 need the sim's population history |
| R-042-05, R-032-04, R-032-01 | all starting stances hostile, budget starts at 0 | tick 0: all hostile, all budgets 0 (and no cell but 4294967295 ever differs, J) |
| R-021-01, -02, -05, -08, -09, R-022-01, -02, -05, R-023-01, R-025-01, -02, R-045-05 (tick-0 read, same `set_seed` without the opening jump) | archetype cycle, template shapes, 0.12 x N extra edges, connected, population and field ranges, edge types, no player-NPC adjacency, starting tech | 15 factions, 51 inhabited regions in 9 isolated and 6 archipelago shapes; 88 edges = 79 + 9 = floor(0.12 x 80); 0 range violations; 0 edge-type violations; 0 player-NPC adjacent pairs; tech error 2e-15; seed 1 with `n_regions` 0 draws 284 |
| R-020-01, R-068-08 | same seed and commands give the same bytes | tick and mission runs each repeated: byte-identical |
| R-056-02, R-056-04, R-055-06, R-057-09 | exactly the asked ticks; opening jump 20 to 50; chapter +1 per jump; first commander seated after the opening jump | 66 of 66 jumps took 50 ticks and chapter +1; first snapshot at tick 20 with commander 100000001, lineage 100000000 |
| R-056-03 | ownership snapshot every 2 ticks, first = before, last = after | 66 of 66: 26 snapshots of 80 owners, stride 2, both ends equal the surrounding snapshots |
| R-057-02 | a lineage with fewer than 2 chapters played stays | jump 1 kept lineage 100000000; the first change came at jump 2 |
| R-068-02, R-068-03, R-065-04 | no digit in any entry; base under 90 words, expanded under 140; a lineage entry always | 934 entries: 0 digits, 0 over the word limits, a lineage entry in 66 of 66 jumps |
| R-077-02 | the picked band is the band the pipe reports | 66 of 66 (bands 1 to 4 and refuse; band 0, key 1, not used because of the known gap) |
| R-078-01, R-078-05, R-078-04 | consequence rows applied to the mission region; refusal tension +8 percent of the deficit; transfer bands hand the region over | 55 of 55 mission-region consequence rows equal the ALG-59 table (neighbour rows not checked); 11 of 11 refusals exact; 5 of 5 transfers |
| R-074-02, R-074-03, R-076-01, R-076-02, R-072-01 | parity from capacity, floor 0.75; deadline between 0.6 B and B; mission region in or next to the player's land | 66 of 66 each (parity 0.804 on the weak rim, 0.997 at home) |

## 5. Not checkable from this run

- E-06 diplomacy (S-043 peace, S-044 betrayal, S-047 convergence): every pair starts hostile (R-042-05) and nothing ever makes a pair neutral, so no overture, betrayal or convergence can occur at the launch settings. Not exercised, not a violation.
- E-05 friction (S-041) and drift terms (S-013 to S-018): they land in the same tick delta as everything else; the pipe has no per-term log and the oscillator phases are hidden.
- Lifecycle phases (S-053), unit tiers (S-048), lineage births and lifespans (S-059, S-060), the commander's chance of death (S-077): not on the wire.
- Mission trigger detail (R-073-01 windows such as "lost this window"), Reconquest, Suppression, Interception and Counterinsurgency: none was drawn in 66 missions.
- R-062 collapse: the player's faction never fell below 3 regions, so `chapter_end_reason` stayed 0 throughout.
- R-026-05 grace period and the opening jump's 3 to 5 world entries (R-065-07): the opening jump happens inside `set_seed` and sends nothing.

## 6. How the run was recorded, and its limits

The recorder drives the viewer's own `ViewerState.advance()` (so the command sequence is the viewer's) over its `PipeSession`, with a shim that writes every command and every frame returned as one JSON line. Mission mode cycles bands 3, 2, 4, 1, 3, 5, 2, 4, 3, 1, 2, 5 (5 is refuse). Wall time: 7 seconds for 6,000 ticks, 5.5 seconds for 66 missions.

Dumps and scripts are in scratch (each over 2 MB or not worth committing), so nothing is stored under `story_reviews/shots/`:

- `/home/westopoli/Projects/om-push/tmp-arch-simviewer/run/tick_a.jsonl` (85 MiB, tick mode, 6,000 ticks) and `tick_b.jsonl` (the repeat)
- `.../run/tick_snap.jsonl` (94 MiB, 3,000 ticks with a snapshot after every tick: stances, telegraphs, budgets)
- `.../run/mission_a.jsonl` (3.5 MiB, 66 missions) and `mission_b.jsonl` (the repeat)
- `.../run/control0.jsonl` and `control0_n0.jsonl` (the world at tick 0 for 80 regions and for a drawn count)
- recorder `.../record_run.py`, checks `.../an/*.py`

What the dump cannot see: the 50 ticks inside a jump (only the before and after snapshots, the chronicle and the ownership timeline every 2 ticks); the hidden opening jump; colonisations, reinforcements, decisions, attack mode and commit, pruned and delayed events, revolt success draws, the ledger; and tactical play, because the viewer resolves missions with `objective_complete` and `mission_end` instead of playing them. One seed, one world size (80, not the bible's 250 to 400), a fixed 50-tick jump. Stochastic rules (A to B of section 4, R-049) were checked as counts against their expectation, not as proofs; deterministic ones were checked on every instance.
