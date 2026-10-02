# Flag drift report, epics E-01 to E-22

Register read: `docs/northstar/ambiguity_register.md` (424 rows; 190 closed, 234 open counting by row). Status of a flag id is the Status column of its row or rows; an id counts as closed only if every row says closed. The register was not edited.

Counting rule used below. "Listed" means an id named in a story's `Open flags:` line or in the epic's `## Open ambiguity flags` section. "Before" counts every listed id of any status (the epics treated them all as open); "after" counts listed ids that the register marks open. Ids that an epic only cites from another epic (for example E-22 flags cited in E-11) are included in these counts. The gate tables count only the epic's own open flags.

Method: all ids were pulled from each epic by script and looked up in the register. Ranges written as "Q-215-01 to Q-215-04" were expanded and each id checked (all open, except E-03's Q-021-01 to Q-021-06, all closed). The citation check for each bracketed rule was `grep -rlE "R[-_]###[-_]##" tests/ csrc/ scripts/`.

## Register facts

- Duplicate ids in the register (9): Q-002-01 (closed, open), Q-065-01 (closed, closed), Q-085-01 (open, open), Q-085-02 (open, open), Q-111-01 (closed, open), Q-118-02 (open, open), Q-120-02 (open, closed), Q-124-02 (closed, closed), Q-130-01 (open, open). Of these only four are mentioned in epics: Q-065-01 in E-09, treated closed because both rows are closed; Q-120-02 in E-14 (inside R-120-02 text only), treated open; Q-111-01 in E-16 (gate row only), treated open; Q-118-02 in E-17, open.
- Q-111-01 drift the other way: the register has an open row for Q-111-01 (save buffer layout, E-16 S-111) but S-111 prints `Open flags: none`. Left as is; I did not add flags.
- Two register rows have no Answer cell (Q-021-07, Q-086-02); parsed from the 4-cell form. Both open.
- Flags the epics mention that the register does not contain: Q-139-01 (E-19, gate row, the start of the range "Q-139-01 through Q-144-02") and Q-145-01 (E-20, gate row, the start of the range "Q-145-01 through Q-150-01"). They appeared nowhere else. Changing nothing was not possible for these two mentions because the rows they sit in had to be recounted and closed flags removed; both gate rows were rewritten as explicit lists of open ids, so the two ranges are gone. No other missing ids exist after range expansion.

## Counts before and after (ids listed in open-flag lines and footers)

| Epic | Stories / rules (gate row before -> after) | Listed before | Listed open after | Gate verdict now |
|---|---|---|---|---|
| E-01 | 15 / 82 (unchanged, were correct) | 19 | 12 | not passed (S-008, S-009, S-010, S-200, parts of S-007, S-162, S-163) |
| E-02 | 10 / 47 -> 13 / 60 | 12 | 9 | not passed, S-220 to S-222 blocked on Q-220-01, Q-220-02, Q-159-13, Q-221-01, Q-221-02, Q-222-01 |
| E-03 | 5 / 28 -> 7 / 31 | 10 | 3 | not passed, S-224 blocked on Q-224-01 |
| E-04 | 6 / 31 -> 7 / 33 | 7 | 2 | not passed, S-225 blocked on Q-225-01, Q-225-02 |
| E-05 | 10 / 58 -> 11 / 62 | 9 | 3 | not passed, S-226 blocked on Q-226-01, Q-226-02 |
| E-06 | 7 / 30 -> 8 / 46 | 9 | 5 | not passed, S-227 blocked on Q-227-01 to Q-227-03 and Q-159-12 |
| E-07 | 6 / 27 -> 6 / 28 | 6 | 2 (both cited, held by E-02) | no open flags; gate to be rerun |
| E-08 | 10 / 45 -> 11 / 54 | 11 | 4 | not passed, S-228 blocked on Q-228-01, Q-228-02, plus the missing S-063 reference |
| E-09 | 7 / 36 -> 7 / 40 | 8 | 3 | not passed, Q-068-03, Q-070-02, plus the missing S-069 reference |
| E-10 | 14 / 70 (were correct) | 31 | 21 | not passed, Q-080-03, S-210 to S-214 flags, plus the missing S-079 reference |
| E-11 | 12 / 61 (were correct) | 21 | 15 | not passed, flags at the foot plus the missing S-088 reference |
| E-12 | 8 / 31 (were correct) | 15 | 9 | not passed, flags at the foot plus the missing S-094 reference |
| E-13 | 11 / 49 (were correct) | 10 | 9 | not passed (Q-096-01, Q-097-02, Q-101-02, S-207 flags, missing S-101 reference) |
| E-14 | 9 / 39 (were correct) | 16 | 10 | not passed, Q-125-03 and S-215 to S-217 flags |
| E-15 | 8 / 41 (were correct) | 12 | 10 | not passed, S-218 and S-219 flags plus the missing S-131 reference |
| E-16 | 16 / 91 (were correct) | 21 | 16 (17 counting open duplicate Q-111-01) | not passed |
| E-17 | 22 / 107 (rules added to row) | 40 | 33 | not passed, 33 open flags |
| E-18 | 12 / 49 (were correct) | 10 | 8 | not passed |
| E-19 | 9 / 33 (were correct) | 15 | 15 (13 own, 2 cited) | not passed, 13 own flags |
| E-20 | 8 / 28 (were correct) | 16 | 13 (12 own) | not passed |
| E-21 | 8 / 30 (were correct) | 11 | 10 (9 own) | not passed |
| E-22 | 16 / 83 (were correct) | 48 | 48 | not passed (nothing closed) |

Open-flag figures in the gate tables: E-01 12, E-02 9, E-03 1 (plus 2 cited), E-04 2, E-05 2 (plus 1 cited), E-06 4, E-07 0 (plus 2 cited), E-08 2 (plus 2 cited), E-09 2 (plus 1 cited), E-10 18 (plus 2 carried), E-11 15, E-12 9, E-13 9, E-14 10, E-15 10, E-16 17, E-17 33, E-18 8, E-19 13, E-20 12, E-21 9, E-22 46.

## Flags removed from open lists, rules rewritten, pending lines, brackets left

"Pending line" means the line `Flag closed, rule text pending: <flag>, <answer>. The rule below is what the tests read today.` placed under the story heading.

### E-01
- Removed: Q-001-05 (S-001 to S-003, verdict), Q-005-02 (S-005), Q-005-03 and Q-005-04 (S-005, S-006, S-162 to S-164, verdict), Q-008-01 (S-008), Q-009-01 and Q-E01-08 (S-009). Also the bracket-form mentions in the Inputs and Outputs tables for Q-001-01, Q-004-01 and Q-005-04.
- Rules rewritten with the register answer: R-001-05 and R-003-03 and R-002-02 (Q-001-05), R-004-01 (Q-004-01), R-162-02 and R-162-04 (Q-005-04). Partly rewritten: R-162-01 (numbers radius 500, reveal 2 s, reach 2,000 put in; "which units" left), R-163-01 (emitting doubles cross-layer sight and being seen put in), R-164-01 (the reach table put in; Q-008-03 range and damage left).
- Judgment: the grep for R-001-05 hit `tests/specfactory/test_card_lint.py` (`test_R_001_05_stub`) and for R-004-01 hit `tests/specfactory/test_chain_graph.py` (`test_R_004_01`). Both are harness fixtures with made-up ids, not tests of the game rule, so I treated both rules as uncited and rewrote them. If you read the instruction literally these two get pending lines instead.
- Brackets left, answer insufficient: R-162-01 ("which units", with open Q-162-01), R-163-02, R-163-03 and R-164-03 (Q-005-04: the register answer gives no number for silent, nothing on per unit or per group, and no weaknesses). R-163-01 and R-164-01 keep only their open-flag parts.
- The numbers that sat in the `Open flags:` lines of S-162 to S-164 (cooldown 20 s per unit, "silent is the default", "the reach table is provisional") were kept as plain sentences below the line, without the flag id.
- Gate row: verdict text no longer names Q-001-05 and Q-005-04; row 4 now says 12 flags open.

### E-02
- Removed: Q-013-01, Q-015-01, Q-019-01 (gate row, verdict, S-013, S-015, S-019, footer). Gate rows recounted to 13 stories and 60 rules. Verdict was "passed" with 9 open flags on S-220 to S-222; now "not passed", blockers named, S-012 to S-020 and S-160 stated as having no open flags.
- No brackets. No pending lines.

### E-03
- Removed: Q-021-01 to Q-021-06 (including 02 to 05), Q-021-08, Q-022-01, Q-022-02, Q-024-01, Q-025-01 (gate heading, rows 1 and 4, verdict, five story lines, footer). Rows recounted to 7 stories and 31 rules; verdict "S-021 to S-025 passed, zero open flags" now "not passed", S-224 blocked on Q-224-01. The audit narrative in row 4 was dropped with the closed ids.
- No brackets. No pending lines.

### E-04
- Removed: Q-026-01, Q-027-01, Q-027-02, Q-028-01, Q-031-01. Rows recounted to 7 stories and 33 rules. Verdict now "not passed", S-225 blocked on Q-225-01 and Q-225-02. R-031-01 keeps its parenthetical "(Q-031-01: measure first)", which already states the answer.

### E-05
- Removed: Q-035-01, Q-036-01, Q-036-02, Q-037-01, Q-040-01, Q-041-01. Rows recounted to 11 stories and 62 rules.
- Pending line: S-036, Q-036-02 (no bracket in the rules, but the answer, no reservation and attacks may stack, is not in the cited rule text, and the epic footer said the tests assume the other candidate).

### E-06
- Removed: Q-042-01, Q-043-01, Q-045-01, Q-048-01. Rows recounted to 8 stories and 46 rules. Verdict now "not passed", S-227 blocked on Q-227-01 to Q-227-03 and Q-159-12; S-042 to S-048 "no open flags; gate to be rerun".
- Pending lines: S-044 (Q-045-01, R-044-07), S-046 (Q-048-01, R-046-05).
- Needs a new story, not written: Q-043-01's answer adds a story (a decisive player victory in a mission against a hostile faction shifts its stance toward the player to neutral with probability 0.50). E-06 has no such story. Only the flag was dropped.

### E-07
- Removed: Q-049-01, Q-050-01, Q-052-01, Q-054-01. Verdict now "no open flags; gate to be rerun".
- Pending lines: S-049 (Q-049-01, no bracket), S-051 (Q-052-01, no bracket), S-054 (Q-054-01, R-054-01's text "No rule until Q-054-01 is answered" is cited by a test and left).
- Needs a new story, not written: Q-052-01's answer attaches an idea (fallen great powers live on as legend or myth in the chronicle); no E-07 or E-09 story carries it.

### E-08
- Removed: Q-056-01, Q-057-01, Q-058-01, Q-060-01, Q-062-01, Q-063-01, Q-063-02. Rows recounted to 11 stories and 54 rules. Verdict now names S-228's two flags and the missing S-063 reference.
- Pending lines: S-056 (Q-056-01, R-056-01), S-057 (Q-057-01, R-057-04), S-060 (Q-060-01, R-060-04), S-063 (Q-063-01 for R-063-01 and Q-063-02 for R-063-03). All five rules are cited by `tests/csim/test_E08_*`.
- Conflict noticed, not fixed: R-056-05 and R-060-04 say natural deaths run once at the end of the jump; Q-060-01's answer says per tick.

### E-09
- Removed: Q-065-01 (two rows, both closed), Q-065-02, Q-067-01, Q-068-01, Q-070-01. Rows recounted to 7 stories and 40 rules. Verdict now names Q-068-03, Q-070-02 and the missing S-069 reference.
- Pending lines: S-067 (Q-067-01, R-067-06), S-068 (Q-068-01, R-068-02), S-070 (Q-070-01, no bracket; R-065-03 still reads one lineage cluster per region).

### E-10
- Removed: Q-072-01, Q-074-01, Q-076-01, Q-076-02, Q-077-01, Q-077-02, Q-078-01, Q-079-01, Q-080-01, Q-080-02. Gate rows already had the right story and rule counts (9 / 48 and 5 / 22); row 4 now says 1 open flag on S-072 to S-080 (Q-080-03).
- Pending lines: S-074 (Q-074-01, R-074-06), S-078 (Q-078-01, no bracket).
- Sentences about closed flags in the S-077 and S-080 `Open flags:` lines were removed; the design content they carried (full ramp ships, Crossed Signals via the options pass, host owns difficulty) stayed as plain sentences.

### E-11
- Removed: Q-081-01, Q-083-01, Q-083-02, Q-084-01, Q-086-01, Q-088-01. The brief's lead that E-11's Purpose lists these as open did not hold at the time of the run: the Purpose names only open flags (Q-082-03 to Q-082-05 and the like).
- Pending line: S-081 (Q-081-01, R-081-01). Q-086-01's answer confirms the code values the rules already state, so no pending line.
- Gate row 4 now says 15 flags open; verdict names the missing reference and the stories with no open flags.

### E-12
- Removed: Q-089-01, Q-090-01, Q-092-01, Q-094-01, Q-E12-01 (and Q-005-04 mention in S-089).
- Pending lines: S-089 (Q-089-01, R-089-04), S-090 (Q-090-01, R-090-02 and R-090-03), S-091 (Q-092-01, R-091-02), S-094 (Q-094-01, no bracket; the answer says no sensor circles and two fog states, while R-094-02 still has a sensor circle).
- S-089's `Open flags:` line now lists Q-176-02 and Q-007-01, which it previously only described.

### E-13
- Removed: Q-101-01 (S-101). Q-095-01 stays as the parenthetical in R-095-01 (states the answer). Row 4 now says 9 flags open. Q-098-02 is not in E-13's text.

### E-14
- Removed: Q-120-01, Q-121-01, Q-122-01, Q-124-01, Q-125-01, Q-125-02. The line "Q-120-01 closed: ..." under S-120 is not in an open-flag list and was left.
- Pending lines: S-121 (Q-121-01, R-121-05; R-121-01 lists the same two conditions), S-122 (Q-122-01, R-122-04), S-124 (Q-124-01, R-124-01). All cited by tests.
- Gate rows were already correct (9 stories; 22 + 17 rules). Verdict now names Q-125-03 and S-215 to S-217.

### E-15
- Removed: Q-129-01, Q-131-01, and from the gate row Q-126-02, Q-127-01, Q-128-01 and from the verdict Q-126-01. The invariant "(pending Q-126-02)" was rewritten to cite R-126-02's world-stream draws.
- Pending line: S-129 (Q-129-01, R-129-04). S-131's `Open flags:` line now states Settlement as the engine-wide name; no pending line (no bracket, no conflict).
- Bracket left: R-218-08 (open Q-218-06; it names Q-131-01 only as context).

### E-16
- Removed: Q-103-03, Q-104-01, Q-105-02, Q-106-01, Q-108-01 from open lists; from the gate row Q-103-01, Q-105-01, Q-110-01 (rule counts were already right).
- Pending line: S-104 (Q-104-01, R-104-03; replaces the old sentence "the bracket stays until that rule is rewritten"). S-107's line now states that the panel shows stats as bands (R-107-04 is not cited by any test, so no pending line).
- Gate row 4 now lists 17 open flags including the open duplicate row of Q-111-01.

### E-17
- Removed: Q-112-01, Q-113-01, Q-115-01, Q-117-01, Q-118-01, Q-119-01, Q-119-02. Gate row 4 now says 33 open flags; the footer sentence that the new flags sat in the audit sidecars "until the register takes them" was removed (every one of the 33 is in the register).
- Pending lines (all seven rules are cited by `tests/csim/test_E17_*`): S-112 (Q-113-01 for R-112-02; Q-112-01 for R-112-05), S-114 (Q-115-01), S-115 (Q-117-01), S-116 (Q-118-01), S-117 (Q-113-01 for R-117-02), S-119 (Q-119-01).
- Partial answer: R-112-02's bracket also asked whether library hints bias layout selection; the Q-113-01 answer covers only the fairness gate.

### E-18
- Removed: Q-134-01, Q-136-01, and from the gate row Q-132-01, Q-138-01.
- Rules rewritten with the register answer (both uncited): R-134-05 (the six per-type attack categories), R-136-03 (wrecks fade after 30 s, cap 150).
- Footer: Q-132-02 was open and listed on S-132 but missing from the footer; added. Gate row 4 now says 8 open flags.

### E-19
- Removed: Q-144-02 (gate row). Gate row 4 now lists the 13 open flags; verdict names them.
- Bracket left: R-141-02 (open Q-141-02; it cites Q-079-01, closed, only as a relation). R-144-02 and R-159-01 cite closed Q-079-01 and Q-159-05 inside prose and were left.

### E-20
- Removed: Q-146-01, Q-148-01, Q-148-02, and from the verdict Q-151-01. R-151-01 keeps the closed-flag citation in its text.
- Pending line: S-146 (Q-146-01, R-146-02; cited by `tests/specfactory/test_pack_validate.py` and `scripts/specfactory/pack_validate.py`).
- Gate row 4 now lists 12 open flags (the range "Q-145-01 through Q-150-01" is gone).

### E-21
- Removed: Q-158-01, and from the gate row Q-152-01. Gate row 4 lists 9 open flags. The sentence on the S-156 line stays as plain text without the id.

### E-22
- Nothing closed. 40 new plus 6 carried flags, all open. Only change: removed the footer note that Q-177-05 lived in `sidecar_answers2.md` (the register has it).

## stories.md

Three Status cells changed: S-054 `Deferred (Q-054-01)` -> `Deferred`; S-148 `blocked on Q-148-01` -> `blocked on Q-148-04, Q-148-05` (the open flags of S-148 in E-20); S-156 `blocked on Q-158-01` -> `blocked on Q-156-02`. No other row listed a closed flag (checked by script, ranges expanded).

## Left alone, for you

- Closed-flag parentheticals that state the answer in rule text: E-04 R-031-01, E-08 R-062-02, E-09 R-065-02, R-065-06, R-069-03, R-069-07, E-13 R-095-01, E-14 R-123-02, E-16 R-110-02, R-110-07, E-17 R-188-02, R-188-05, R-190-04, R-197-04, E-19 R-144-02, E-20 R-151-01.
- The register's open flags that the epics do not list on the right story: Q-111-01 (S-111, open duplicate row), Q-120-02 (open duplicate row, E-14 S-120).
- E-08 Scale requirements and E-03 generation budget items from sidecar section 6 are not flag drift and were not touched.
- I ran `git diff --stat` once, read-only, before noticing the no-git-commands rule. No other git command was run and nothing was staged or committed.
