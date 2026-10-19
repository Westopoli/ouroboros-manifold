# E-09 — Chronicle

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 7 stories, 40 rules, numbers from `algorithms.md` ALG-50 through ALG-53. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 2 open flags, Q-068-03 (S-068) and Q-070-02 (S-070); Q-159-07 is cited and held by E-22 S-182. |
| Every visible-surface story has a reference | **No.** S-069 (the scroll presentation) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on Q-068-03 (S-068), Q-070-02 (S-070) and one missing reference (S-069).

## Purpose

The chronicle is how decades of simulation become a story the player can read. After every mission the galaxy runs on for a lifetime, and the player watches it as a split screen: the map animates borders shifting on the left, and on the right five to ten entries print word by word like a history being written as it happens. The first entry is always what the player's last mission did. The player's family always gets an entry, even if all it says is that life went on. The rest are the biggest chains and the most changed regions, each written from authored fragments so no two campaigns read the same.

Every entry is grounded: named people from the ledger, named regions with their owners on first mention, causes traced through chain tags. No numbers, no game-speak. The chronicle is the long memory too: a new commander's briefing draws from it.

## Obviously working in 60 seconds

Run a 50-tick jump after a successful mission in region R where a famine chain ran and two regions changed hands. The scroll shows: entry 1 in the consequence-success register naming R and the outcome; one lineage entry; a chain entry for the famine with its full chain in one paragraph; regional entries for the changed regions. Between 5 and 10 entries, none sharing 40 percent of their content words, none over 90 words in base form. Click a printed entry: everything pauses, the expanded form adds a closing sentence and names. Same seed, same events, same scroll text.

## Stories

### S-065 — Five to ten entries, in the right order
As a player, I want the scroll to open with what my mission did, always tell me about my family, and then show the biggest stories of the age, so that I read it as my history and not as a log.

Rules
- R-065-01  Given a time jump with any events, When the scroll is built, Then it has at most 10 entries, and at least 5 whenever the per-category cap of R-065-05 allows it.
- R-065-02  Given events flagged as consequences of the last mission, When clusters are ranked, Then they form one consequence cluster that is entry 1, categorized by the mission's band: total_success and strong_success give success; partial_success and partial_failure give mixed; total_failure and refusal give failure (Westley 2026-10-01). Flagged events in regions adjacent to the mission region form the `consequence_ripple` cluster (Q-067-01). The consequence cluster appears only in the jump that directly follows the mission; a jump with no mission since the last one has none.
- R-065-03  Given the player's lineage, When clusters are ranked, Then every lineage cluster is included regardless of score, one per region the lineage touched.
- R-065-04  Given no event touched the lineage, When clusters are ranked, Then one `lineage_quiet` cluster is included, placed in the lineage's most recent region.
- R-065-05  Given the remaining clusters, When the budget is filled, Then they are taken in descending peak score, skipping any category that already has 2 entries, until 10 entries.
- R-065-06  Given fewer than 5 entries after ranking, When the budget is filled, Then skipped clusters are added in score order only from categories that still have fewer than 2 entries; the cap wins over the minimum, so a quiet jump may show 4 entries (Q-065-03, Westley 2026-10-01).
- R-065-07  Given the opening jump of a campaign, When the scroll is built, Then it has 3 to 5 entries and no consequence or lineage cluster.

Inputs: time jump event log; mission outcome; ledger.
Outputs: ordered cluster list; scroll entries.
Open flags: none. R-065-02's mapping already covers the economy's rule that once a side has lost its original main base the best result is partial failure, which gives a mixed consequence entry (E-22 S-178, E-10 S-077).

### S-066 — What counts as notable
As a player, I want a first contact to make the chronicle even if nothing much changed, and a small event to make it only if it snowballed, so that the scroll reads like history and not like a stat feed.

Rules
- R-066-01  Given an event whose template has significance tier T and whose field deltas sum in absolute value to D, When scored, Then base = T + min(D/50, 3.0).
- R-066-02  Given the event is in the last mission's region, When scored, Then the context multiplier gains +0.5; given it has an attached character, +0.3; given it has chain length L > 1, +0.1 · min(L, 5); given a lineage member lives in its region, +0.8; the multiplier starts at 1.0 and the score is base · multiplier.
- R-066-03  Given a tier-5 event with deltas summing to 2 in a quiet region, When scored, Then score = (5 + 0.04) · 1.0 = 5.04.
- R-066-04  Given a tier-2 event with deltas summing to 200, chain length 6, in the mission region with a character attached, When scored, Then score = (2 + 3.0) · (1 + 0.5 + 0.3 + 0.5) = 11.5.
- R-066-05  Given any event, When scored, Then the score is never below its tier.

Inputs: event records with template tier, deltas, region, chain length, character attachment; ledger lineage locations.
Outputs: per-event score (T1 trace).
Open flags: none.

### S-067 — Stories, not events
Flag closed, rule text pending: Q-067-01, the list has 21 categories with `consequence_ripple` built, and the fragment count is 399. The rule below is what the tests read today.
As a player, I want a famine, the revolt it caused, and the compromise that ended it to be one entry, so that the scroll tells causes and not incidents.

Rules
- R-067-01  Given scored events not in the consequence cluster, When clustered, Then an event is a lineage event if a lineage member lives in its region, or its attached character is a lineage member, or it is in the last mission's region; lineage events cluster by region.
- R-067-02  Given a lineage cluster, When categorized, Then: any template with "succession" or "death" gives `lineage_succession`; else any "military" or "revolt" gives `lineage_military_action`; else net economy > 2 or net military > 2 gives `lineage_thrived`; else net economy < −3 or net tension > 5 gives `lineage_suffered`; else `lineage_quiet`.
- R-067-03  Given the remaining events, When clustered, Then events sharing a chain tag form one chain cluster spanning every region the chain touched, and chain clusters with the same primary region and category merge into one.
- R-067-04  Given a chain cluster, When categorized, Then: any "revolt" template gives `chain_revolt_spawned`; else any "expansion" or "coloniz" gives `chain_expansion`; else 4 or more events gives `chain_cascade`; else net military > 2 and net tension < 3 gives `chain_conflict_victory`; else net military < −2 and net tension > 3 gives `chain_conflict_defeat`; else |net military| ≤ 2 and net tension > 2 gives `chain_conflict_stalemate`; else net economy > 0 and net tension ≤ 0 gives `chain_crisis_resolved_well`; else `chain_crisis_resolved_badly`.
- R-067-05  Given events with no chain tag and no lineage link, When clustered, Then they group by region into a regional cluster categorized `regional_faction_shift` if any conquest, revolt, or faction-creating event is present, else `regional_growth` if net economy + population > 3, else `regional_decline` if < −3, else `regional_stable`.
- R-067-06  Given the category list, When read, Then it is exactly: 5 lineage, 8 chain, 4 regional, and the consequence categories [Q-067-01: 3 in code, 4 in the bible].

Inputs: scored events; ledger.
Outputs: clusters with type, category, region, peak score, chain tag, tick range.
Open flags: none.

### S-068 — Written from fragments, never the same twice
Flag closed, rule text pending: Q-068-01, openings, details and closings ship at 30, 35 and 35 words, and the chronicle writing system gets an overhaul pass before launch. The rule below is what the tests read today.
As a player, I want each entry to read like a passage from a real history, different every campaign, so that the chronicle feels authored and alive.

Rules
- R-068-01  Given a cluster with category C, When its entry is assembled, Then an opening, a detail, and a closing are each drawn uniformly from C's pools among fragments whose required slots resolve from the cluster; base form = opening + detail, expanded form = opening + detail + closing.
- R-068-02  Given fragment length limits, When the library is validated, Then openings are at most 30 words and details and closings at most 35 [Q-068-01]; base form under 90 words, expanded under 140.
- R-068-03  Given a slot, When resolved, Then it comes only from the vocabulary: identity (character name, rank, faction, lineage name, faction name, region name, adjacent region), event (event description as a lowercase noun phrase, chain length, duration prose), state (field delta summary, stability, capacity, tension as qualitative words), consequence (mission outcome phrase, archetype, mission region), relational (previous event reference, lineage history note); no raw numbers ever appear.
- R-068-04  Given a region's first mention in a scroll, When rendered, Then it reads "<region>, held by <faction display name>", and later mentions use the bare name; an unowned region gets no qualifier.
- R-068-05  Given an assembled entry, When two adjacent fragments resolve the same slot value of 6 or more words, Then the second becomes an anaphoric form ("what followed", "the outcome").
- R-068-06  Given an assembled entry, When a significant word (4+ letters, not a stop word) appears twice, Then the second occurrence is replaced by a synonym from the curated map if one exists.
- R-068-07  Given the finished entries in order, When two entries share 40 percent or more of their content words (relative to the shorter), Then the later one is dropped; the first always survives.
- R-068-08  Given the assembler seed equals the jump's start tick, When run twice on the same clusters, Then the text is identical.

Inputs: clusters; fragment library (E-21); ledger; world snapshot; registry names.
Outputs: entries with base and expanded text, category, region, tick range; warnings.
Open flags: Q-068-03 (whether events inside a mission, such as a base occupied, retaken or fallen back from, or an expansion made, reach the time-jump log and so the consequence slots and the `chain_expansion` category of R-067-04; it depends on what the pair carries forward between missions, Q-159-07 held by E-22 S-182).

### S-069 — Watching history happen
As a player, I want to watch the map change on the left while the scroll writes itself on the right, and to be able to stop and read, so that the time jump is the game's signature moment and not a loading screen.

Rules
- R-069-01  Given the narration phase begins, When the panel appears, Then it slides in from the right over 0.40 s and the map view resizes to 62 percent of the width; it stays until the player presses Proceed (E-16 R-108-05, R-108-06), then slides out over 0.40 s and the map returns to full width.
- R-069-02  Given an entry prints, When words appear, Then each word arrives every 0.08 s and fades from 0 to full opacity over 0.20 s.
- R-069-03  Given the map animation is the master clock, When an entry's tick range is reached and no other entry is printing, Then that entry begins printing; entries print one after another, never two at once, so the scroll reads like a book (Westley, 2026-10-13, on the S-108 frame: "in the python version they were printed out one at a time so the user would read it like a book"); an entry whose tick is reached while another prints waits its turn; a printed entry holds for at least 3.0 s. Whether the map holds at that entry's keyframe until it has printed is open (Q-069-03). The map replays the jump at 2 ticks per second (Q-069-01), so a 20-tick jump lasts 10 s and a 100-tick jump 50 s.
- R-069-04  Given an entry is printing, When the player clicks it, Then nothing happens; Given it is printed (blinking cursor shown), When clicked, Then the expanded form overlays the scroll and the map, clock, and any printing entry pause; dismissing resumes from the exact word and frame.
- R-069-05  Given every chronicle entry, When keyframes are chosen, Then the map has a keyframe within the entry's tick range; and every ownership change has a keyframe whether or not it has an entry.
- R-069-06  Given a T2 screenshot at the end of the narration phase, When compared, Then the number of entries on screen equals the number the distiller produced.
- R-069-07  Given a printed entry, When the player clicks a faction name or a system name in it, Then the galaxy centres on that faction's territory or that system; the sim sends the entry's text and each name's position in it, the client shows that text as sent, and no other words are clickable (Q-069-02).

Inputs: scroll entries with tick ranges; ownership timeline (every 2 ticks); player clicks.
Outputs: on-screen scroll; map animation; pause state.
Open flags: none beyond the missing reference. In R-069-01 "the map view" means the galaxy map during narration, not the battlefield's map view of E-16 S-161. Reference required: `references/E-09/notes.md`, missing.

### S-070 — My family is always in the story
Flag closed, rule text pending: Q-070-01, lineage clusters are capped at 2, merging the rest into the highest-scoring one (R-065-03 still reads one per region). The rule below is what the tests read today.
As a player, I want the events near my family to bubble up into the scroll, framed as the deeds of a military family, so that the lineage is the spine of the history.

Rules
- R-070-01  Given an event fires in a region where a lineage member lives, When scored, Then it receives the +0.8 lineage term (R-066-02), no other special handling.
- R-070-02  Given an event of significance tier 3 or higher in a lineage region, When logged, Then the lineage member is attached to the event record (E-08 R-060-05).
- R-070-03  Given a lineage member appears in a fragment, When their rank is rendered, Then it is a military rank; no lineage member is ever framed as a governor, trader, or political leader.

Inputs: ledger lineage locations; event tiers.
Outputs: scores; attachments; fragment slot values.
Open flags: Q-070-02 (in a pair a second player runs the economy, and in a team of up to 6 there are more players; whether the economy player or any teammate has a place in the lineage and the chronicle, and how R-070-03's military framing and R-065-03's "the player's lineage" apply, E-19 S-159, S-241).

### S-071 — The fragment library contract
As a player, I want the scroll to draw on enough authored fragments that I do not see the same sentence twice in a campaign, so that history never repeats itself word for word.

Rules
- R-071-01  Given the launch library, When loaded, Then every category has at least 6 openings, 8 details, and 5 closings (240 assemblies per category).
- R-071-02  Given the library, When validated, Then every fragment uses only vocabulary slots, uses all of its category's required slots (lineage categories require lineage name; consequence categories require mission outcome; chain categories require region name), is within its word limit, contains no banned mechanical or meta phrase, and has a unique id.
- R-071-03  Given two fragments in the same pool, When their edit distance is below the threshold, Then the later is rejected; a batch losing more than 35 percent to rejection is flagged, not shipped.
- R-071-04  Given every event template, When the library is validated, Then it has a chronicle prose phrase (lowercase noun phrase), else validation fails.

Inputs: fragment library file; event template table.
Outputs: validation report (E-21).
Open flags: none. Generation and validation run offline in E-21; this story is the consumer's contract.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Time jump event log | E-08 | list of event records with tick, template, region, deltas, chain tag, chain length, character, mission-consequence flag | missing template id scores at tier 2 |
| Mission outcome | E-10 | success, failure, or other | other reads as mixed |
| Ledger | E-08 | | |
| Fragment library | E-21 | validated | invalid library fails to load |
| Ownership timeline | E-08 | snapshot every 2 ticks | |
| Player clicks | Client | | |

## Outputs

| Output | Observable where |
|---|---|
| Clusters and scores | T1 trace |
| Entries (base, expanded, category, region, tick range) | Scroll panel; save file; briefing input |
| Warnings | T1 trace; library validation report |
| Scroll presentation state | Screen; T2 screenshots |

## Invariants

- Entry 1 is the consequence cluster whenever one exists.
- Every lineage cluster is in the scroll.
- 5 ≤ entries ≤ 10 for any jump with events (3 to 5 for the opening jump).
- No entry contains a digit.
- Same seed, same scroll.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): distill and assemble 2,000 events in under 200 ms; the scroll panel renders 10 entries at 60 fps while the map animates.

## Look and behavior references

`references/E-09/notes.md`, missing: the split-screen scroll (2 to 5 screenshots or clips of streaming-text and animated-map presentations that read the way Westley wants, and what in them he does not want).

## Ways this could be wrong

- Consequence cluster ranked by score and dropped.
- Lineage cluster omitted when the family had no events (no `lineage_quiet` fallback).
- Chain clusters split by region, breaking the one-story-per-chain promise.
- Category cap applied to lineage clusters.
- A digit leaks through a slot.
- First-mention qualifier applied on every mention.
- Cross-entry dedup keeps the later entry instead of the first.
- Map waits for the scroll, or expand does not pause the map.
- Assembler seeded from wall clock, breaking determinism.

## Open ambiguity flags

Q-068-03, Q-070-02, and Q-159-07 as cited in S-068. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-04 Events (chain tags, significance tiers, chronicle prose).
- E-08 Generational structure (time jump log, ledger, lineage).
- E-10 Missions (outcome and consequence flags).
- E-16 Client (world view animation, panel, click handling).
- E-21 Offline AI pipeline (fragment library generation and validation).
