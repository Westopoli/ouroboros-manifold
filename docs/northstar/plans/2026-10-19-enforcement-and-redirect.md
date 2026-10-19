# Making the method fail instead of drift, and redirecting the queue (Architect proposal, 2026-10-19)

Westley, 2026-10-19, on the three method changes in `drift_audits/2026-10-19-decision-to-spec.md`: "how can we construct it such that the spec 'fails' if the requirements aren't met, not just writing down a 'rule' but formalizing it into something immutable?" And: redirect the work in flight, the queued specs of both chats, and the finished prototypes for the gap the audits found. This page is the proposal. Westley picks; nothing here is in force until he does.

## 1. Where enforcement already lives, and what it cannot see

Main has one path in: the merge gate. `scripts/specfactory/pre_gate.sh` runs before every push and before the gate lock; `scripts/specfactory/spec_provenance.py` already fails a spec on seven reasons (untagged behaviour unit, a stand-in phrase, a `[P]` without file:line, a `[B R-id]` absent from the epics, a `[W Q-id]` not closed, a `[DRAFT-name]` without a row, two units clashing on one piece id); `status_check.py` fails a landing whose lane table, `pieces.toml` and review queue disagree with git. Builders cannot edit tests or `scripts/specfactory/` (owner rows), and `git-guard` blocks `--no-verify`.

What the audit found slips through all of it: a correct `[W]` quote followed by an Architect sentence whose number replaces the quote's meaning; a rule line rewritten in the epic while a spec paragraph and a test still encode the old text; a decision recorded in a side file the builder never reads; a workflow script and its gap rulings that exist only in a scratch folder. Each is a form defect, and form can be linted. Meaning cannot: a lint can force a re-read and force the test to name his words, it cannot prove the test's logic matches them. That last check stays with the audit.

## 2. Five checks, each a lint reason or a gate stage, each failing the piece

Each is written as: what the author must write, what the check computes, and what fails.

**C1. Rule pins carry a hash of the rule text.** A `[B R-193-01]` tag becomes `[B R-193-01@7f3a2c]`, the first six hex digits of the sha256 of that rule's line in its epic, whitespace-normalised. Test headers carry the same pin (`# Rules proved: R-193-01@7f3a2c`). `spec_provenance.py` reason (8): a `[B]` tag without a pin, or with a pin that does not match the epic on the tree being gated, fails. A new `test_pins.py` in `pre_gate.sh` does the same for every test under `tests/` that names an `R-` id. Effect: when Westley's ruling rewrites a rule line (the clerk's verdict commit), every spec paragraph and every test that encoded the old text fails the gate until someone re-reads it and re-pins. Re-pinning is a diff a reviewer sees; it is the "superseded by" banner, computed instead of remembered. Audit rows closed by it: decision-to-spec 2, 9 (E-15 still says "whole force"), 11; consistency 8, 14.

**C2. A quantified quote must be asserted in its own words.** A `[W ...]` quote whose text contains a quantifier (at least, at most, never, always, every, all, only, no more than, any age, within) must sit in a unit that also carries `[ASSERT tests/<path>::<test_name>]`. Reason (9): the tag is missing, the test does not exist, or the test's source does not contain the quote's key phrase inside an assertion message (`assert ..., "W: never a square or an octagon at any age"`). The test writer pastes his words into the assertion; the builder's code must satisfy that assertion, not the draft number beside it. Rows: decision-to-spec 8, 9, 11.

**C3. A number after a quote is a draft with a row that says "reading".** Reason (10): any number in the sentences that follow a `[W]` quote inside the same unit is either inside the quote or tagged `[DRAFT-name]`. The register gains one status value, `reading (Westley to confirm)`, for a row whose answer is the Architect's reading of his words; `status_check.py` fails if a row's answer text contains "until Westley", "Westley to confirm" or "default" while its status says `closed` (row 29's exact shape), and the register extract for his batches lists every `reading` row first. A `reading` row never blocks a landing (he vetoes on the shot) and is never shown as closed.

**C4. Nothing launches from an uncommitted script.** Every workflow script's first phase is a check that needs no agent: it hashes its own source and its args file and fails with `STOP script-not-on-main` unless `origin/main` holds the same bytes at `docs/northstar/plans/workflows_2026-10-07/<name>.js` and `<name>.args.json`. The `pieces.toml` row of every launched piece gains `script = "<path>"` and `args = "<path>"`; `status_check.py` fails a landing whose row lacks them or names a path not in git. Every gap ruling in the args (`gaps.<id>`) carries `spec = "<file>:<line>"`, and the check phase greps that line on `origin/main` for the gap id; a ruling that is not in the spec on main fails the launch. Rows: decision-to-spec 1, the whole brief hop.

**C5. A spec may not set a rule aside without an open flag.** Reason (11): a unit that mentions an `R-` id together with "not in scope", "out of scope", "set aside", "not this piece", "deferred", "later" must also carry a `[W Q-id]` whose row is open and names the piece that waits. Row: decision-to-spec 2 (A16 set Alt+N aside "not A16 scope" with no row), 6 (VG-D-DEFAULT with "no pieces.toml row yet").

Also carried from the consistency audit, one gate stage rather than a lint: **a review row is not written without a legend, the unit of every number, the run id and the camera band**; the clerk's row template has the four fields and `status_check.py` fails a queue row that lacks one (consistency rows 4, 11, 12, 20).

Where they run: `pre_gate.sh` runs `spec_provenance.py` unconditionally (today only with `PRE_GATE_SPEC` set) plus `test_pins.py`; `status_check.py` runs after every landing as now; the workflow check phase runs at launch. Owner: a HARNESS piece per check, tests first by a different agent, positive controls (a spec with a stale pin, a quote without an assert, a closed row saying "until Westley") red before the lint and green after. Estimated size: C1 and C5 about 120 lines in `spec_provenance.py` plus `test_pins.py` about 80; C2 and C3 about 100; C4 about 60 in the script template and 30 in `status_check.py`. One week of Doer work beside the lanes, not instead of them.

**What it costs.** Every existing `[B]` tag (several hundred across the specs and tests) gets a pin in one records piece, and every quantified `[W]` quote (about a dozen in the visible-game spec) needs an `[ASSERT]` or is re-tagged as a `reading` row. That pass is itself the audit's fix list, done once.

## 3. Redirecting the work in flight and the queue

Verdict per item, against the audit rows. "Proceed" means the piece is untouched by the findings.

| Item | Where | Verdict | Why (audit row) |
|---|---|---|---|
| W-6 timing twin, HARNESS-userdir (land2), records 7+8, VG-A-edgescroll | Dispatcher, landing now | proceed | untouched |
| VG-P1 layout engine | Dispatcher, landing now | proceed | pure function, new files; the direction reversal did not touch it (dts 10) |
| VG-P2 lot-order noise | built green on `push/vg-p2-fin`, parked | **hold the landing; respec** | the bible puts the noise on the field's spread ("ragged from its first ring, never a square or an octagon at any age"); the spec moved it to lot order and pinned a draft 0.5 (dts 11, cons 28). The rule text already rules this; the respec is implementation: noise on the field spread per R-193-01, the shape test asserting his words under C2, built as P2n on P2's files, tests rewritten by a different agent. P2 lands with P2n as one landing |
| VG-CONTRACT-E7 starting force | relaunch after records 8 | **hold the relaunch until Westley gives the floor** | "at least half-force, if not as far down as 20%" became 20 to 80 percent; at seed 1 the player starts at 40 (dts 9, cons 29). The ABI and save parts are fine; the formula is one constant and its test. Ask him now: is the floor half, with 20 only at the far end of the scale? |
| VG-B24b quality control | relaunch after records 8 | proceed | untouched |
| VG-D-VIEW | branch green, not on a clerk | proceed, with two records | opt-in behind `OM_SPACE_VIEW=1`; the play orders layers through To-layer buttons that VG-A-layerkeys will delete (cons 23): the layerkeys piece lists that play among the tests it rewrites. Register row Q-S3-01 contradicts itself (cons 25): strike the first sentence. The dimming 0.4 in the layers mockup against 0.55 in the spec (dts 12) is checked by the D-VIEW look reviewer against the mockup frame |
| VG-B26 chronicle one entry at a time | not on a clerk | **hold until Q-069-03 is answered** (pack B9) | it would build the register default (map runs on) while he leans the other way (cons 27) |
| VG-A-layerkeys, VG-A-routeline | queued | proceed, with one addition each | layerkeys retires the A16 paragraph (SPEC:101) and `tests/test_vg_a_a16.gd`'s Q/E and "To layer" pins in the same piece, listed as superseded tests with the ruling (dts 2; C1 would force this). Routeline: the S-140 net story re-shot is a ground shot or the spec says why a straight line is right (cons 24) |
| A18 3D fit (FU-A18-3d) | a follow-up with no owner | **becomes a piece now**, after his point-5 answer on pitch | the launch view has no home base in frame (cons 13 to 15, dts 1); needs the pitch and the spawn marker answers; the home base itself waits on lane P |
| VG-A-startforce, VG-E-prodslot, VG-E1R, VG-E1K | queued behind E7 | proceed | consistent (cons 34); prodslot is the real cause of stacked units (dts 7), so it moves ahead of any further unit-size change |
| E lane fan-out (E1l, E1o, E1p-b) | depends_on VG-P3 | proceed as recorded | already waits on P3; the lane table cell that says "on the S-237 verdict" is the stale copy (cons 18, point 8) |
| VG-B25 vast space | queued, tests-first missing | proceed; tests first | the decision is now in the spec (dts 4); write the tests before the script |
| SIM-LOGS, then CH-1 to CH-3, CHRON-CONTEXT, SEL-ORDER, CONTROLS-IDS-1 | sim lane, after its depends_on | proceed after one confirmation | W1 ("this window" = since the last mission ended) is rule meaning and the spec's go line still says it waits on him (cons 30). One line from Westley: W1, W2, W4 confirmed as his, or taken by the Architect as implementation. The "implementation decisions are yours" quote is in the pack README section C, not only in the spec |
| CONST-2, ALG coverage | Mac branches, gate | proceed | consistent |
| Lab rev 2 (overseer chat) | its own landing | proceed, plus one game-side piece | rows 33 and 34 consistent. "Ground fire should go cross-layer, that's a bug" (10-13) became lab scope only (dts 14): a FINDING row and a csim test on the game's fire path, owner TBD after the lab landing |
| Transition mockup (S-108) | prototype, not approved | **pass 2 waits on point 2's answer** | the battlefield-to-star ratio is two draft numbers with no rule (cons 1); his answer gives the rule, then pass 2 |
| Terrain-obeys mockup (S-191, S-189) | prototype, not approved | **pass 3 does not start before P1 and P2 land** (his point 4: layout engine first); before any pass 3: the vantage check per R-192-03, the legend and unit on the shot, a route colour that is not water blue (cons 3 to 7, point 3) | |
| Landscape pass 6b (approved 10-04) | prototype | one run of 6b alone to see whether the terrace stripes are in the approved look (cons 5, point 3) | |
| Layout prototype pass 1 (10-04), layers mockup, settlement banding, space density, galaxy bubble, sand table | prototypes | each gets a `parity.toml` (constants with file:line) when it is consumed, the B23 pattern; Q-S3-02 (which layers prototype is the one he meant) is confirmed by him from the mockup frame, not guessed (dts 12) | |

The batch verdicts already given (7, 9, 10 approved; 8 rejected 2026-10-13) and the two stale S-237 lane-table cells plus the pack index are one records clerk piece, on his word.

## 4. What this asks of Westley today

1. Pick among C1 to C5 (all five is the recommendation; C1 and C4 close the most rows).
2. The starting-force floor (E7 is held on it).
3. Q-069-03, map waits or runs on (B26 is held on it).
4. W1, W2, W4 of SIM-LOGS: his, or the Architect's.
5. The point 2, 3, 4, 5, 11 answers already listed in the chat, which unblock the two mockups and the A18 fit.
