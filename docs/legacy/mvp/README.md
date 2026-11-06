# Track L — Lean MVP loop: method

Status: approved as a track on 2026-09-14 (`PLAN.md` Track L, `README.md` decisions table). Round 1's cut is decided (`Q-MVP-01`: every major feature at its most minimal; `Q-MVP-02`: auto-resolved mission card while the tactical slice is unbuilt). The Round 2 and 3 cuts and the thresholds are proposals for Westley to review. The backlog's Round column is the next follow-up. Open questions for this track are `Q-MVP-##` rows in `../ambiguity_register.md`.

## Why this track exists

The stage pipeline builds the game epic by epic and has no way to learn from a player until the game is done. That is the waterfall failure in agile clothing: every story could be Ready, Tested, and Built and still be something nobody wants to play. Track L puts a player in the loop as early as the C/Agora path allows, in rounds, and uses what they say and do to decide what gets built next. Its two questions are: which of the bible's ideas are actually good, and what does player satisfaction mean for this specific game, as opposed to what the bible assumes it means.

## Lean vocabulary, mapped to this project

| Lean term | Here |
|---|---|
| Hypothesis | A bible claim about what players value, rewritten as a falsifiable statement with a metric and a threshold. Listed in `experiments.md`. |
| Experiment | A round: a cut shipped to a defined tester group with defined instruments. |
| Build | The cut: a subset of stories, chosen by omission, plus marked stand-ins for epics the round needs but does not build. `feature_mvps.md`. |
| Measure | Telemetry file, structured feedback form, scripted interview, and (Round 3) Steam's own numbers. |
| Learn | The gap review: assumed value versus observed, one row per hypothesis. |
| Pivot or persevere | A change-protocol PR, a new `Q-` flag, a kill, or a keep. Never a silent edit. |

## Rounds

| Round | Testers | Delivery | Instruments | Gate to open the round |
|---|---|---|---|---|
| 0 | none | none | Hypotheses written, metrics defined, feedback instruments drafted, and a two-week Agora velocity baseline recorded in `../proving_ground/BUILD_LEDGER.md`. | This track merged. |
| 1 | 10 to 20 friends over the round, at most 4 active at once, Windows assumed, in a small Discord server | ZIP posted to Discord; `README.txt` with hotkeys and where logs go; structured feedback form; bug-report capture hotkey; a bug channel. | Scripted 30-minute interview per tester; feedback form; local session telemetry file with opt-in upload. | Every Round 1 story Built; probes H and I passed; one cold-machine smoke test by a friend with no dev tools. |
| 2 | 10 to 30 people, the Round 1 Discord widened | ZIP posted to Discord; bug channel; a pinned survey. | Same as Round 1 plus aggregated telemetry and a weekly digest written offline from the files. | Round 1 gap review done and its actions landed; every Round 2 story Built. |
| 3 | Steam Playtest | Steam build: store page, export presets, store copy worded in Round 2 testers' own words (`Q-MVP-06`). | Steam retention and wishlist numbers, in-game survey, Discord. | Round 2 gap review done; the layer-system option chosen in its design phase; onboarding passes the 30-minute personality-load check (below). |

Rounds open on evidence. No round has a date, because Agora's throughput on this project is unmeasured: at the time of writing it has completed zero cards for Ouroboros. `build_path.md` defines the velocity measurement that must exist before any forecast is shown to Westley.

## What player satisfaction means here

Each metric ties to a hypothesis in `distinctiveness.md`. Everything below is measurable without a model API, in keeping with the no-runtime-API rule.

**Engagement**
- Chapters completed per session, sessions per tester, and return within seven days. The research band for the tribe's paid titles (D7 of 40 to 75 percent) is a comparison point, not a target for a friends build.
- Time from first screen to first order; whether the first mission was abandoned; whether the tutorial was skipped. These are the UI-bounce signals the research names as the tribe's number one complaint.

**The world moves without me** (H1)
- Free answer after the first time jump: "What changed in the galaxy while you were away?" Scored yes/no on whether the tester names a change they did not cause, and whether they call it interesting or random.

**Carry-forward** (H2)
- Free answer after chapter three: "Name something that happened because of a mission you played earlier." Scored yes/no.

**Chronicle** (H3, H8)
- Telemetry: read time per jump, expand-clicks per jump.
- Interview: one entry recalled unprompted; one line quoted.
- Any tester describing the text as filler or placeholder is a fail on its own.

**Tragedy of understanding** (H4)
- After a loss: "Why did you lose?" Scored on whether the answer names a positional or force cause, versus "the game cheated" or "no idea."

**Commander, not king** (H5)
- Interview count of testers who ask for base building or economy, and whether "freeing" or "missing" wins when they describe the absence.

**Intent to continue**
- Would you play another chapter? Would you pay $12 for this? Both yes/no, asked last.

The thresholds attached to these in `distinctiveness.md` are live kill criteria from Round 1 for every hypothesis, prototypes included (`Q-MVP-04`, answered 2026-09-14). A threshold miss on a prototype surface is still a finding; the gap review decides whether the idea or the stand-in failed.

## Feedback instruments

- **Feedback form.** A rewrite of the existing `legacy/build/feedback.txt` template so that every question maps to one metric above. Free text where the metric is a scored free answer; yes/no where it is a count. Delivered inside the ZIP as a text file for Round 1, as a pinned form for Round 2, in-game for Round 3.
- **Interview script.** Ten questions in fixed order, thirty minutes, after the tester's second session. Recorded with consent. The scored questions are asked verbatim so answers are comparable across testers.
- **Telemetry file.** Local, plain JSON, written by the client: session start and end, chapter index, mission outcome band, orders issued per mission, chronicle read time and expand-clicks, screens visited, first-order latency. Stored locally; the tester may send it back with the form or opt in, from the first-launch notice, to an upload to the project's R2 bucket (`Q-MVP-03`, answered 2026-09-14). Consent follows the pattern the legacy client's privacy modal used; nothing uploads without the opt-in.
- **Bug capture.** A hotkey that zips logs, the telemetry file, and a screenshot, and copies the path to the clipboard. The legacy client's F12 flow is the reference for behavior, not for code.
- **Discord (from Round 1).** Opens with the friends round and widens for Round 2 (`Q-MVP-05`, answered 2026-09-14). One bug channel, one feedback channel, one pinned survey, a weekly digest written by Claude from the files. The research names this "support-shaped" Discord as the norm for small strategy teams.

All of the above are stories in the proposed epic E-22 (`feature_mvps.md`), built by Agora like anything else.

## Gap review

Run after every round, before any Round N+1 story enters Stage 3. One table, one row per hypothesis:

| Hypothesis | Bible source | Assumed value | Observed | Gap | Action | Owner |
|---|---|---|---|---|---|---|

Action is exactly one of: **change protocol** (story and rules rewritten, tests revised, card respec'd, one PR); **flag** (a new `Q-` row when the result raises a question only Westley can answer); **kill** (story status Killed, recorded in `experiments.md` under "Killed by evidence"); **keep** (recorded under "Confirmed by evidence" with the number that confirmed it). A gap with no action is not allowed; "watch it next round" is a keep with a note.

The review also produces the next round's cut: the ranking in `distinctiveness.md` is re-scored with the new evidence, and `feature_mvps.md` is rewritten (not annotated) to match.

## What Track L may not do

- Weaken a rule or test to fit a round. Cuts are by story omission only.
- Loosen a scale gate or a speed budget.
- Build on the legacy Python slice, or use it for a playtest.
- Call a model at runtime, including for feedback digests inside the game.
- Put a human in the build loop. Client and packaging cards wait for probes H and I like any other capability.
- Claim Ready for a story outside a round's scope because its epic's e2e file exists. A round-scoped e2e file lists the stories it does not cover.

## Relationship to the stages

Stages 3, 4, and 5 are unchanged in content. Track L decides their order: the next epic into Stage 3 is the one whose Round N stories are not yet Ready, in dependency order within the round. Stage 4's backlog gains a Round column (`build_path.md`). Stage 5 writes tests only for stories in the current or next round. The proving ground gains probes H and I. The layer-system design phase (README decision of 2026-09-13) is unchanged and sits between Round 2 and Round 3.
