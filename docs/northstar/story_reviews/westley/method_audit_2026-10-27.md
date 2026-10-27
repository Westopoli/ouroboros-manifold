# The method tests, audited

Two fresh reviewers tried to break the weekly method tests. I re-ran everything they claimed. Here is what matters, in plain words, and what I need from you.

## What they found, and whether it is true

**Serious, and true.** Five things mean the tests cannot do their job yet.

1. **The gate log and the tests disagree on a column name.** The gate writes `candidate_sha`; the tests look for `candidate`. The first real week crashes before printing a single line. Both reviewers' test worlds used the wrong name, so the suite never noticed.
2. **A landing of several pieces breaks its own log line.** The piece list has commas in it and is not quoted, so every column after it slides over. Eight of the forty-two gate rows so far are unreadable.
3. **The "bad week" safety check does not run the program.** It reads a saved answer and checks the saved answer says FAIL. If the program went blind, the check would stay green. Two of its five FAILs were typed in, not measured.
4. **Half the tests cannot fail.** Any test whose threshold you have not approved yet prints DRAFT whether the number is good or bad, and does not count toward the exit code. The other half fails correctly. Two copies of the same compare step disagreed.
5. **The chat counts include your other project.** The transcript folder covers every project, so Jarvis sessions were counted. About half the 2,599 oversized calls were Jarvis.

**Real, medium.** The coordinator-chat count treats every chat as a coordinator (66 in one hour, target 2). Spend on the subscription is counted as $0, so Fable's share reads blank. Spawns that do not follow the new naming vanish instead of being flagged. The lab's own code counts as "not product" in the lab phase. Several baselines in the settings file were measured in a different sense from the test that reads them. The test file writes a junk row into the real run log every time it runs.

**Small, true.** A dozen edge cases: files in a nested fixtures folder count as tests, some data extensions slip through, a touch of an old retro file counts as a retro, one test has no failing case, one crashes on an empty repo.

**Refuted.** One reviewer said the 18.4 docs-to-code baseline appears nowhere; it does (332 over 18 in the retro table). Another wanted the bible counted as method prose; it is game content, not method.

**My own.** Your README table no longer has a verdict column, so the "pictures waiting on you" count reads zero while three wait. Two FAIL lines are thousands of characters long.

Full table with evidence for both sides: `docs/northstar/plans/method_rev3_2026-10-26/audit_findings.md`.

## What I need from you

A word on each, or "as recommended" for all.

| Question | Recommended |
|---|---|
| A week with only docs commits and no code: FAIL or "no answer"? | No answer, with the count shown |
| A commit touching only scripts or tests: is that code? | Yes |
| The 16 page-asset files under the workflows folder: data to move, or leave? | Move with the lab data |
| Lab phase test-to-code ratio: keep 1.5, or a looser lab number? | Keep 1.5, show both sums, revisit after four lab weeks |
| Compaction drift lines: 2 per compaction (not the week sum)? | Yes |
| CLAUDE.md size bound: 18,000 bytes beside the 120 lines? | Yes |
| The 24 draft thresholds in the table at the end of the findings file | Approve as drafted; change any you want |
| Go for the five fix pieces (four code, one records)? | Yes, one Workflow each, Sonnet builders, same clerks |

Approve means: the five fixes are built and the thresholds get your date. Reject means: say which row, and it stays open.
