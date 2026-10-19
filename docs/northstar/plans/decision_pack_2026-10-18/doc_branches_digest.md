# Doc branches digest (ROADMAP 3b T5, T6, T7, T9), 2026-10-18

**Form. Per branch: a / b / c, plus answers to its numbered asks.**
(a) land as is; (b) land after the named edits; (c) retire, superseded.

| Branch | Verdict | Your answers |
|---|---|---|
| `docs/method` (T5) | b | ask 1: ___ ; ask 2: ___ |
| `docs/military-doctrine` (T7) | b | ask 1: ___ ; ask 2: ___ ; ask 3: ___ |
| `docs/era-pack-form` (T9) | b | ask 1: ___ ; ask 2: ___ |
| `docs/map-design-pillars` (T6) | already on main; only the Q-MAP rows remain | ask 1: ___ to ask 5: ___ |
| `docs/map-design-research` (T6) | already on main; nothing to land | none |

Checked after `git fetch origin`. Each verdict below is mine, offered as a candidate; the choice is yours.

---

## 1. `origin/docs/method` (T5): `docs/northstar/method.md`, 122 lines, new file

**What it is.** An outsider-readable page on how the game is built, written from the project's own documents and saying where they are silent. Sections: the goal sentence (small force that understands positioning beats a larger one); tests are the spec (epic/story/rule/question ids, the Ready gate, positive controls, Westley owns thresholds, determinism, wired-not-tested); the prototype gate (mockup vs instrument, a pass is a page, three unapproved passes force an options page); the skill lab (five skills, margin in whole soldiers, break-even, space lab vs ground lab, ten pass conditions with draft marks, the ping measured in two stages); workflows and the pre-flight; the merge gate and three regression tiers; the bible and how a ruling is recorded. It claims no new rule. It states the pass marks are drafts.

**Asks of you.** The page asks for nothing explicitly. The two decisions it implies:
1. Is this page the right public face of the method, as a reader-facing description? Candidates: (a) yes, it stays an outsider page; (b) it becomes an internal page; (c) not wanted.
2. Does it land in `docs/northstar/`, where "the method directory wins" over other docs (its own precedence rule, last line)? Candidates: (a) yes, there; (b) elsewhere, so that it does not outrank `README.md`/`PLAN.md`.

**Stale against main.**
- ROADMAP T5 says it plainly: method rev 2 and the retro supersede parts of it.
- Section 5 describes the workflow script but not the roles. Main now splits Architect, Dispatcher and Engineer/Doer with a one-chat status table, clerk landings, and a 400k-token restart (`plans/workflows_2026-10-07/dispatcher.md`; evidence in `plans/retro_2026-10-10/README.md`).
- Section 5 lacks `pre_gate.sh`, "at most two build workflows and one landing in flight", the ruler agent, and the status/drift checks (`status_check.py`, `method_check.py`, journal).
- Section 3 lacks the skeleton-first rule and the visible-game guards (a player-facing piece needs a screenshot a human sees; stories "Seen" only on your approval).
- Section 6 says the individual merge-gate stages are undescribed and that the play check "is run by hand, no command". Re-check both against `regression.md` and the gate script before landing.
- Section 3 describes mockup and instrument as the two prototype kinds and the three-pass stop; check against `agile.md` as it stands.

**Recommendation.** (b) land after edits, or (c) if you want one clean rewrite. Named edits: add the rev 2 role split and guards (a short new section citing the retro and dispatcher.md); fix sections 5 and 6 as above. ROADMAP already names the alternative: a Sonnet re-draft against `retro_2026-10-10/`. Not (a): it would publish the pre-rev-2 method as current.

---

## 2. `origin/docs/military-doctrine` (T7): three files under `docs/research/topics/`

Files: `terrain_in_military_doctrine.md` (126 lines, the synthesis), `terrain_in_military_doctrine_deep_research_2026-10-06.md` (243 lines, the Gemini report), `terrain_in_military_doctrine_gemini_prompt.md` (27 lines). The folder exists on main with other topic notes; these are not on main.

**What it is.** A synthesis of ten military principles (chokes, high ground and reverse slope, concave envelopment, line against column, depth and reserves, recon/ambush/bait, combined arms, vertical terrain, force ratio, counter-cases). Each is marked solid / contested / weak by the author (not by the source), with cases, the condition under which it holds, and the lab play that tests it, in game terms. It then maps principles to map pillars P1-P8 and skills S1-S5. It claims the history supports the hub's promise, adds no new lab play, and that the source report has errors: the Kursk loss figures read backwards, "2.4x" is not Dupuy's number as stated, several battle figures are the weak end of wide ranges, and the report's "game translation" paragraphs assert behaviour the bible does not record. Nothing in it is a decision; every number is prior art, not a game number.

**Asks of you** (section 4, candidates not recommendations):
1. Are Dupuy's terrain and posture multipliers (terrain about 1.3 to 1.5; hasty defence about 1.5 to 1.6; surprise up to 2.0) a published scale you want to read when you answer Q-MAP-01 (what height does beyond vision) and Q-MAP-02 (directional cover)? Candidates: (a) yes, as prior art only; (b) no, ignore.
2. Does line-against-column need a lab run, since group movement at the slowest member's pace may change it? Candidates: (a) queue a lab run; (b) no.
3. The ranking in section 5 (1 chokes and frontage; 2 formation; 3 matchup; 4 height; 5 recon; 6 vertical; 7 counter-cases; 8 force ratio) is the author's, not the source's. Accept, amend, or leave unranked.

**Stale against main.**
- Principle 2 and its testable line use the ground vision rule (R-005-09, ping space-only R-005-12). Still consistent with E-01; vantage nodes are retired for ground eras (E-01 R-005-06, your "retire them yes", 2026-10-05).
- Section 3's table points to `docs/northstar/research/map_design/README.md` and Q-MAP-01/02. Those exist on main, but no `Q-MAP` row is in `ambiguity_register.md` (see section 4 below).
- Lab references (condition C6, C7, "about 2x" target) cite `layer_dynamics/README.md`; I did not re-check that those numbers are unchanged. Re-check before landing.
- Nothing is superseded.

**Recommendation.** (a) land as is, as research under `docs/research/topics/`; or (b) with one edit, the C6/C7 and plays-table references re-checked against `layer_dynamics/README.md`. The raw report and prompt are provenance; keep or drop them as you prefer. Not (c).

---

## 3. `origin/docs/era-pack-form` (T9): `docs/northstar/era_pack_form.md`, 64 lines, new file

**What it is.** A form for whoever designs era 3 of 20+. Sections: what an era does not write (the whole engine: no `if era ==`, R-145-01/02/04); era kind (space or ground) as the choice that shapes vision, movement and landscape; a table of every field an era supplies, with where it lives, who decides, the Settled Reach example, and a status of exists / rule only; three fields the record had no place for (vision model per kind, layout kit, roster by role); and the open questions Q-133-01, Q-146-02, Q-082-05. It claims most of the form is rule only: only the manifest keys are validated today.

**Asks of you.** None stated as such. The implied ones:
1. Accept the form as the shape of an era pack? Candidates: (a) yes; (b) amend the field list.
2. Who owns the open fields the table marks "Westley" (names of the three resources, per-era config constants, strategic view definition)? These stay yours; the page assigns them to you without proposing values.

**Stale against main.**
- **Era kind row is wrong.** It says "no manifest key yet (Q-146-04 open)". Q-146-04 closed (a), 2026-10-06 ("#5 a": a new pack field `kind`), and `assets/eras/settled_reach/manifest.json` now has `"kind": "space"`, validated in `scripts/specfactory/pack_validate.py` (terrain stage 2). Section 4's first bullet (no place to declare kind) is also settled; its vision-units half is not.
- **Lane E manifest lists.** ROADMAP T9 says the form gains the building and doctrine lists (E1f, E1g). The manifest now has `"doctrines": ["boom","fortify","press","balanced"]` and a `"buildings"` list (id, role, footprint, hp). The rows "Doctrines" (Q-243-01, still open) and "Building pieces" need updating from "not in the manifest".
- E-20 changes of 2026-10-15: S-147 (two launch eras, one space and one land) and S-151 (Climate of War values come from the lab's crossings, not invented per era). The form says nothing of either; the "Per-era config: fog, reinforcement constants" row should point to S-151. R-146-02 says "three" eras (the epic says rewrite pending); the form is not wrong on that.
- Still open and correctly listed: Q-133-01, Q-146-02, Q-082-05, Q-243-01. The page cites Q-146-03 (elevation flag) too; that row is open.

**Recommendation.** (b) land after the named edits: kind row to "exists, validated"; add doctrines and buildings rows; add an S-151/S-147 line; drop the first bullet of section 4. ROADMAP T9 already plans this.

---

## 4. `origin/docs/map-design-pillars` and `origin/docs/map-design-research` (T6)

**Both are already on main.** `git merge-base --is-ancestor` succeeds for each against `origin/main`, and `git diff --stat origin/main...origin/<b>` is empty. `docs/northstar/research/map_design/` on main holds `README.md` (the pillars page, identical to the pillars branch's file), `prior_art_strategic_depth.md`, and the Gemini report. ROADMAP T6 still lists them as branches waiting; that row is stale on its own words ("`research/map_design/` on main"). What awaits you is the acceptance of the page, not a merge.

**What it is.** Eight pillars for map design, from the Gemini report and a Sonnet draft, each with principle, evidence, a measurable check, skills touched, and the failure it prevents. P1 equal numbers, free shapes (topological fairness); P2 paced distance; P3 chokes that bind and can be paid for; P4 several routes of unequal cost with loops; P5 height with a rule and a readable reference; P6 alternating open and sheltered ground; P7 escalating exposure; P8 every strong position has a counter. Every number is prior art, not a game number. It notes the space era kind (layers plus ping) has no prior art. Claims resting on search summaries are marked.

**Asks of you** (section 4; candidate Q rows, not yet in `ambiguity_register.md`; the only mention of Q-MAP on main is this page):
1. **Q-MAP-01.** What does high ground do on the ground, beyond vision (R-005-09)? (a) nothing, vision only, as SC2; (b) a miss chance for ground attackers from low ground, as Brood War (120/256); (c) damage scaled by slope, as Total War (up to +30 percent downhill); (d) an aim bonus for the high side with no defence, as XCOM (+20).
2. **Q-MAP-02.** Does ground cover protect by direction? (a) height-only cover: cover is whatever blocks sight (R-005-10), no direction; (b) directional cover, cut only from the front arc, void when flanked or at close range, as Company of Heroes (minus 50 percent, void under 10 m); (c) directional only for chosen strongpoints.
3. **Q-MAP-03.** Does the layout kit get pacing tools? (a) no, distance only; (b) slow and speed zones; (c) destructible blockers on route openings; (d) both (b) and (c).
4. **Q-MAP-04.** Are rush-distance bands set per mission archetype, and who sets them? (a) one band for all; (b) a band per archetype, the lab proposes numbers from group pace and you confirm; (c) bands only for archetypes with a rush play.
5. **Q-MAP-05.** Is prospect-refuge alternation a layout check? (a) no, left to the landscape engine's judgement; (b) a check on routes; (c) a check on key sites only.
Also implied: do you accept the eight pillars as the reading list for E-17 S-112/S-191/S-192 and both labs, or amend.

**Stale against main.**
- Pillar 5 and Q-MAP-01 are partly overtaken: E-01 R-005-06 retired vantage nodes and the elevation bonus for ground eras (commit 0818f230, "retire them yes"). Candidate (a), vision only, is consistent with that; (b) to (d) re-open it, so ask 1 is a real reopening, not a clean-slate question.
- Q-191-03 and the switch of Q-191-13 (P1) are cited as matching; I did not re-check they are unchanged.
- The pillars page predates the layout-engine and landscape work (terrain stages 1 to 3, mockup `PROTO-terrain-obeys`, `research/layout_engine/`, `research/landscape_design/`). The checks in each pillar (path-time difference, choke firing count) were not re-read against those; a pass against them is needed before treating any pillar as the engine's contract.

**Recommendation.**
- `docs/map-design-research`: (c) retire the branch; its content is on main. Mark T6 done for it.
- `docs/map-design-pillars`: (a) accept the page as research as is, and have a clerk enter Q-MAP-01 to 05 in the register after your answers; or (b) with the edit that Q-MAP-01 is narrowed to say R-005-06 already retired the elevation bonus. Retire the branch either way.

---

## Order to read, ten minutes each
1. Pillars page (already on main), then asks 1 to 5. These are the only items that block anything: Q-MAP rows feed E-17 and the layout work.
2. Era pack form: confirm the form; the edits are mechanical.
3. Method: decide land-after-edits or re-draft.
4. Military doctrine: skim sections 1 and 4 only.
