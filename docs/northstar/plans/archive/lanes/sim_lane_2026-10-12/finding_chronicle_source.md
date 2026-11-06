# Finding: the chronicle's source (sim lane step 2, E-09 against the delta stream)

Run 2026-10-15 on origin/main (fe5fe84e), debug pipe `pipe/ouroboros_pipe_dbg`, seeds 1 to 5, `n_regions` 0 (284 to 383 regions), features 0..7. Nothing edited; scratch scripts in `/tmp/chr/`. Engineer (Sonnet 5.5) report.

## Counts

| | |
|---|---|
| Chapters run | 25 (5 seeds x 5; 22 with a mission: 10 ended at once, 9 with the objective completed, 3 refused; 3 had none because `mission_start` answered `no viable mission`) |
| Chronicle entries checked | 243 (194 readable, 49 blank shells) |
| Events checked | 22,683 (25 jumps x about 900) |
| Attacks / collisions / admin-roll records | 12,327 (2,983 conquests) / 6,073 / 82,858 |
| Ownership changes (start vs end of jump) | 1,803 |
| Multi-event chains (2 or more events, same tag) | 1,749 |

## Method

`jump` streams no delta frames, so the jump's own ticks cannot be read from it. Per chapter: `mission_start`, then `mission_end` (after `objective_complete` on some) or `mission_refuse`; then `save`; `step` 50 (collect the 50 deltas); `snapshot`; `load` the save; `jump` 50 (collect `chronicle` and `snapshot`). `om_time_jump_run` is a plain loop of `om_world_step` (`csrc/generational.c:1948`), and the twin was verified: regions and world checksum after the 50 steps equal the post-jump snapshot in 25 of 25 chapters. Checks per jump: entry order and outcome against the band (band 0 or 5 failure, 1 or 2 mixed, 3 or 4 success); family entry; each chain entry needs a chain-tagged event in its region and tick window; each regional entry needs an event or an owner change in its region; category cap of 2 on chain and regional; significance recomputed from the tier table (`GEN_LAUNCH_EVENT_TIER`) plus min(D/50, 3); regions whose recomputed peak reaches the lowest delivered significance but have no entry, classed as explained (budget full at 10, or that category already at 2) or unexplained; ownership changes and faction-creating events without an entry; digits; 90-word base; 40 percent content-word overlap between entries; verbatim sentences (4 or more words) repeated within a campaign.

## Findings

| Rule says | Sim did | Seed / tick | Class | Proposed piece |
|---|---|---|---|---|
| R-065-03, R-065-04, invariant "every lineage cluster is in the scroll": a family entry always (quiet if nothing happened) | 1 of 25 jumps has a `cluster_type` 1 entry (seed 1 chapter 1, the jump with the fewest active regions, 173). 24 of 25 missing, including quiet jumps. Not even a blank shell | all seeds, every jump but s1 c1 | sim defect. Cause is a hypothesis, not proven: `chron_push_candidate` drops silently at `CHRON_MAX_CANDIDATES` 256 (`chronicle.c:134,1590`) and the lineage candidate is pushed after about 150 to 270 regional ones plus growth/decline extras and chain clusters (`generational.c:2043-2087`) | CH-1: log `n_candidates` and drops per jump first (debugging rule), then fix by order or capacity |
| R-067-03, "biggest stories": chain clusters (famine, revolt, relief as one entry) reach the scroll | 0 chain entries in 25 jumps, against 1,749 multi-event chains (longest 4). Chain clusters are pushed with peak score 0.0 (`chronicle.c:1641`) and the selector sorts by peak score, so they sort last, after the 5 to 10 regional entries; same candidate buffer overflow may also drop them | all | sim defect | CH-2: chain cluster peak = max event score in the chain; include in CH-1 diagnosis |
| R-068-07: a dropped later entry is dropped | The sim drops the text but still sends the cluster: 49 of 243 entries (24 of 25 jumps had at least 1) arrive as `text ""`, `fragment_ids [-1,-1,-1]`, `refs.factions []`. Cause: `n_entries = n_clusters` with `entry_valid` 0 (`chronicle.c:1869-1896`) and `write_chronicle` emits invalid ones from the cluster (pipe comment lines 33-35). 29 of the 50 ripple entries are blank | s1 c1 ids 2,3,4,7; all seeds | contract bug (frame carries entries the sim says do not exist) | CH-3: contract piece, frame lists only kept entries; R-069-06 count test follows |
| R-065-02: entry 1 is the mission result, categorised by band; only the jump after the mission | 22 of 22 mission jumps: entry id 0 is consequence, category matches the band (9 success, 9 mixed, 4 failure incl. 3 refusals). 3 no-mission jumps: no consequence cluster | all | pass | none |
| R-065-02, Q-067-01: ripple cluster for flagged events in adjacent regions; R-065-05 cap 2 per category | 50 ripple entries (2.3 per mission jump); 9 jumps have 3 or 4 (cap 2 broken). They are selected before scored clusters and uncapped (`chronicle.c:1729-1733`), so they use up to 4 of 10 slots. The code ripples for any event in an adjacent region (about 65 percent of regions are active, so nearly every neighbour); flagged consequence events are not what it tests (`generational.c:2068-2073`) | s1 c1 (4), s1 c2 (3), s2 c1 (4) and 6 more | rule ambiguity plus defect | Q-row: is ripple one cluster or one per region, capped or not; CH-4 follows the answer |
| R-066-02: context multiplier (mission region +0.5, character +0.3, chain length +0.1 x min(L,5)) | Jump scoring calls `chron_score_event` with those terms fixed at 0 (`chronicle.c:1669-1672`, comment admits it). Entry significance equals tier + delta term in 125 of 143 checkable regional entries (the other 18 differ, lineage +0.8 or owner-change scoring); 124 of 243 entries carry exactly 5.20 (a lone `REVOLT_ENTRENCHED`), so score barely ranks | all | sim gap (known by the code comment) | CH-5: feed per-event context to the scorer (needs the event record fields, see below) |
| R-067-05: regional_faction_shift when a conquest, revolt or faction-creating event is present | The classifier is called with `has_conquest_or_revolt` 0 (`generational.c:2065`); faction shift comes only from a net owner change. 761 faction-creating events (all `REVOLT_ENTRENCHED`), 636 in regions with no entry; 1 owner-change region (s2 c1, region 271) labelled `regional_stable` | s2 c1 | sim gap | CH-6, small |
| R-065-05/R-066 significance threshold: events at or above the recorded significance have an entry | Regions whose recomputed peak is at or above the lowest delivered significance but have no entry: 2,265 region-jumps, all explained (1,710 budget full at 10, 555 category at 2); 0 unexplained. Faction-flips: 1,736 of 1,803 ownership changes have no entry (1,534 budget, 202 cap, 0 unexplained). 1,764 of 1,953 `REGIONAL_REVOLT` events have no entry | all | pass on the rule as coded; the threshold itself is not a number in E-09 | none; Q-row if Westley wants a floor |
| R-071: no sentence repeated word for word in a campaign | 147 verbatim repeats of sentences of 4 or more words in the 5 campaigns (4 inside one scroll, 143 across chapters). Mostly regional boilerplate: "Disputes were resolved at the local level; appeals to higher authority were rare..." 10 times in one campaign. 126 of 332 distinct fragment ids used were reused inside their campaign | all seeds | fragment library (E-21), not the sim | Q-row: R-071 is stated per fragment count (6/8/5) but the player rule is per sentence; a bigger library or a no-repeat memory |
| R-065-01 (10 max, 5 min), invariants (no digit, base under 90 words, overlap under 40 percent), grounding (every regional entry has an event or owner change, every ripple has a neighbour event) | 10 entries max always (21 jumps send 10, 3 send 8, 1 sends 9; readable per jump min 6, mean 7.8, shells excluded); 0 digits, 0 over 90 words, 0 surviving pairs at 40 percent; 0 ungrounded regional or ripple entries; 0 chain entries to check | all | pass | none |
| R-065-07: opening jump has 3 to 5 entries | Not checkable: `set_seed` is silent, so the opening chronicle frame never reaches the pipe | all | pipe gap | CH-7 if wanted |

## Observed beside the chronicle (not rules of this step)

- `mission_start` answered `no viable mission` in 3 of 25 chapters (s2 c3, s3 c3, s4 c2), where the architecture text promises the A3 fallback mission with `quiet_world`. For the mission step.
- About 72 owner changes per 50-tick jump (a quarter of the regions), 959 of 2,983 conquests reverted within the jump; FAMINE is 5,550 of 22,683 events. For the equations step; no threshold is judged here.

## Fields the pipe does not expose

- Per-tick events during `jump` (worked around by the twin run above; no verb needed to change C).
- Opening-jump chronicle frame (`set_seed` is silent).
- Per event: the mission-consequence flag, attached character, lineage membership, chain length, its score. Per entry: lineage ref (`om_chronicle_entry.lineage_ref`), chain tag, the event ids behind it, the "dropped by dedup" state. Lineage locations (family region).
- `revolts[]` is every admin roll (82,858 records, roll 2e-6 to 0.97), not the revolts that fired; outcome and probability are absent. Names and tiers of event templates are not in the frame (tier table copied from `generational.c:1923`).
- Chain tags stop at the event frame; the entry frame carries `cluster_type` and `category` only, so a chain entry is matched by region and tick window.
