# Build ledger

Per-run performance and quality record for the real Agora game-development build,
the counterpart to `SCORECARD.md` (which covered the Stage-0 proving ground). The
table is regenerated from `~/Projects/agora/runs/*/report.md` and `costs.jsonl` by
`scripts/build_ledger.py`; run it after a card finishes. Findings below the table
are written by hand — the durable record of what each build taught us.

Columns: Cands = candidates the local ladder tried; Best = best passed/total tests
in any candidate; Models = worker models used; Wall s = summed worker seconds;
Intervs = DeepSeek resets/hints/aborts; DS calls / USD = DeepSeek calls and cost in
the run's hour window (approximate attribution).

<!-- AUTO:BEGIN -->
| Run | When | Outcome | Cands | Best | Models | Wall s | Intervs | DS calls | USD |
|---|---|---|---|---|---|---|---|---|---|
| 001-blob-two-20260906-0948 | 2026-09-06 09:48 | **DONE** | 4 | 65/65 | qwen3-coder:30b | 62.2 | 2 | 4 | 0.0033 |
| 002-api-put-20260906-0949 | 2026-09-06 09:49 | **DONE** | 4 | 15/15 | qwen3-coder:30b | 102.4 | 2 | 2 | 0.001 |
| 002-switchboard-mcp-skip-20260821-2151 | 2026-08-21 21:51 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 002-switchboard-mcp-skip-20260821-2154 | 2026-08-21 21:54 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 003-agora-spec-parser-tests-20260821-2148 | 2026-08-21 21:48 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 1 | 0.0015 |
| 003-agora-spec-parser-tests-20260821-2156 | 2026-08-21 21:56 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 004-digest-limit-flag-20260821-2200 | 2026-08-21 22:00 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 004-digest-limit-flag-20260821-2203 | 2026-08-21 22:03 | **DONE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 006-best-salesmen-test-skip-20260821-2207 | 2026-08-21 22:07 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 006-best-salesmen-test-skip-20260821-2208 | 2026-08-21 22:08 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 010-search-query-trigrams-once-20260902-1810 | 2026-09-02 18:10 | **DONE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 010-search-query-trigrams-once-20260911-0147 | 2026-09-11 01:47 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 011-search-trigram-memo-20260902-2040 | 2026-09-02 20:40 | **DONE** | 0 | - | - | 0 | 0 | 3 | 0.0287 |
| 011-search-trigram-memo-20260911-0148 | 2026-09-11 01:48 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 012-search-db-path-20260903-0948 | 2026-09-03 09:48 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 6 | 0.0395 |
| 012-search-db-path-20260903-0950 | 2026-09-03 09:50 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 5 | 0.0342 |
| 013-entries-update-no-refetch-20260903-0953 | 2026-09-03 09:53 | **DONE** | 0 | - | - | 0 | 0 | 4 | 0.0255 |
| 013-entries-update-no-refetch-20260911-0149 | 2026-09-11 01:49 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 014-sensitive-upsert-no-refetch-20260903-0954 | 2026-09-03 09:54 | **DONE** | 0 | - | - | 0 | 0 | 3 | 0.0237 |
| 014-sensitive-upsert-no-refetch-20260911-0151 | 2026-09-11 01:51 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 015-notes-list-single-query-20260903-0002 | 2026-09-03 00:02 | **DONE** | 0 | - | - | 0 | 0 | 1 | 0.001 |
| 015-notes-list-single-query-20260911-0152 | 2026-09-11 01:52 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 016-dashboard-stale-search-20260903-1830 | 2026-09-03 18:30 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 11 | 0.0514 |
| 016-dashboard-stale-search-20260903-1831 | 2026-09-03 18:31 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 11 | 0.0514 |
| 017-vendor-link-update-by-id-20260903-0959 | 2026-09-03 09:59 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 2 | 0.0177 |
| 017-vendor-link-update-by-id-20260903-1002 | 2026-09-03 10:02 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 1 | 0.01 |
| 019-auto-search-local-rank-rows-early-exit-20260903-0401 | 2026-09-03 04:01 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 13 | 0.0599 |
| 019-auto-search-local-rank-rows-early-exit-20260903-0423 | 2026-09-03 04:23 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 11 | 0.0479 |
| 020-auto-search-local-trigram-similarity-early-exit-20260903-0445 | 2026-09-03 04:45 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 9 | 0.0366 |
| 020-auto-search-local-trigram-similarity-early-exit-20260903-0447 | 2026-09-03 04:47 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 8 | 0.0351 |
| 021-auto-search-local-levenshtein-hit-early-exit-20260903-0511 | 2026-09-03 05:11 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 8 | 0.0379 |
| 021-auto-search-local-levenshtein-hit-early-exit-20260903-0536 | 2026-09-03 05:36 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 6 | 0.0263 |
| 022-search-narrow-projection-20260903-1838 | 2026-09-03 18:38 | **DONE** | 0 | - | - | 0 | 0 | 9 | 0.0375 |
| 022-search-narrow-projection-20260911-0153 | 2026-09-11 01:53 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 023-notes-insert-returning-20260903-1843 | 2026-09-03 18:43 | **DONE** | 0 | - | - | 0 | 0 | 8 | 0.0336 |
| 023-notes-insert-returning-20260911-0154 | 2026-09-11 01:54 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 024-entries-insert-returning-20260903-1902 | 2026-09-03 19:02 | **DONE** | 0 | - | - | 0 | 0 | 11 | 0.0501 |
| 024-entries-insert-returning-20260911-0155 | 2026-09-11 01:55 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 025-vendor-upsert-returning-20260903-1915 | 2026-09-03 19:15 | **DONE** | 0 | - | - | 0 | 0 | 10 | 0.0466 |
| 025-vendor-upsert-returning-20260911-0156 | 2026-09-11 01:56 | **SPEC-INVALID** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 026-auto-export-csv-batch-rows-20260903-1926 | 2026-09-03 19:26 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 8 | 0.0388 |
| 026-auto-export-csv-batch-rows-20260903-1935 | 2026-09-03 19:35 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 7 | 0.0361 |
| 027-auto-export-gather-single-pass-20260903-1939 | 2026-09-03 19:39 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 6 | 0.0328 |
| 027-auto-export-gather-single-pass-20260903-1958 | 2026-09-03 19:58 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 4 | 0.0192 |
| 028-entries-update-returning-20260905-0910 | 2026-09-05 09:10 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 2 | 0.004 |
| 028-entries-update-returning-20260905-0913 | 2026-09-05 09:13 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 1 | 0.0012 |
| 028-entries-update-returning-20260905-0952 | 2026-09-05 09:52 | **DONE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
| 101-probe-a-toy-drift-20260910-1521 | 2026-09-10 15:21 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 1 | 0.0004 |
| 101-probe-a-toy-drift-20260910-1606 | 2026-09-10 16:06 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 19 | 0.0144 |
| 103-probe-a-toy-drift-r2-20260910-1612 | 2026-09-10 16:12 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 19 | 0.0144 |
| 104-probe-a-toy-drift-r3-20260910-1635 | 2026-09-10 16:35 | **INCOMPLETE** | 0 | - | - | 0 | 0 | 19 | 0.0144 |
| 107-probe-a-build-20260910-1703 | 2026-09-10 17:03 | **DONE** | 1 | 17/17 | qwen3-coder:30b | 37.8 | 0 | 18 | 0.0141 |
| 108-probe-b-build-20260910-1705 | 2026-09-10 17:05 | **INCOMPLETE** | 12 | 4/11 | gpt-oss:20b, qwen3-coder:30b | 670.8 | 2 | 17 | 0.0118 |
| 108-probe-b-build.md-20260910-1717 | 2026-09-10 17:17 | **INCOMPLETE** | 12 | 10/11 | gpt-oss:20b, qwen3-coder:30b | 479.6 | 1 | 14 | 0.0089 |
| 108-probe-b-build.md-20260910-1726 | 2026-09-10 17:26 | **DONE** | 9 | 11/11 | gpt-oss:20b, qwen3-coder:30b | 275.7 | 1 | 12 | 0.0075 |
| 109-probe-e-build-20260910-1732 | 2026-09-10 17:32 | **INCOMPLETE** | 15 | 1/2 | gpt-oss:20b, qwen3-coder:30b | 355.8 | 3 | 11 | 0.0066 |
| 109-probe-e-build-20260910-1739 | 2026-09-10 17:39 | **INCOMPLETE** | 6 | 1/2 | gpt-oss:20b, qwen3-coder:30b | 113.2 | 0 | 7 | 0.0053 |
| 110-probe-f-build-20260910-1742 | 2026-09-10 17:42 | **DONE** | 1 | 18/18 | qwen3-coder:30b | 59.0 | 0 | 4 | 0.0043 |
| 111-probe-e-abort-20260910-1744 | 2026-09-10 17:44 | **UNSATISFIABLE** | 6 | 1/2 | gpt-oss:20b, qwen3-coder:30b | 81.5 | 1 | 3 | 0.0021 |
| 112-probe-h-gd-build-20260914-1942-2 |  | **DONE** | 1 | 1/1 | qwen3-coder:30b | 23.4 | 0 | 0 | 0.0 |
| 200-e02-region-state-20260914-1737 | 2026-09-14 17:37 | **INCOMPLETE** | 18 | 0/7 | gpt-oss:20b, qwen3-coder:30b | 1611.9 | 2 | 7 | 0.0164 |
| 200-e02-region-state-20260914-1806 | 2026-09-14 18:06 | **DONE** | 18 | 7/7 | gpt-oss:20b, qwen3-coder:30b | 1547.2 | 2 | 4 | 0.006 |
| 900-boot-smoke-20260907-1224 | 2026-09-07 12:24 | **DONE** | 0 | - | - | 0 | 0 | 0 | 0.0 |
<!-- AUTO:END -->

## Findings

### 2026-09-14 — Card 200 (E-02 region.c, S-012): first real build, INCOMPLETE, root cause found

The first real game-dev build. The **infrastructure worked end to end**: the loop
dispatched the card, `build.py` ran the escalation ladder (18 candidates across
qwen3-coder:30b and gpt-oss:20b at three rungs), DeepSeek issued 3 resets, the run
hit its limit, the escalation flag was written, and the report captured every
attempt with timings. Cost was $0.0129.

But every candidate scored **0/7** — because the **brief itself had the wrong
equations**. DeepSeek drafted the brief by reverse-engineering the header and the
test file instead of reading the derived rules (`projects/ouroboros/rules/E-02.md`),
so it invented:
- a wrong stability formula (`100 - 0.5*military - 0.5*economy - 0.5*tension`)
  instead of the real `military*0.40 + (100-tension)*0.35 + population*0.25` (+penalties);
- a wrong capacity formula (`100 - 0.5*population`);
- a nonexistent enum, `OM_TIER_SETTLED` (the header defines EMPTY/FRONTIER/HOME).

The workers faithfully implemented the wrong spec, so no candidate could ever pass
tests that assert the real values (stability = 59.00, etc.). This is not a model
capability failure; it is a **brief-source gap**: the correct rules existed in the
derived rules file and in the card's own `## Brief`, but `build.py`'s brief
generation did not use them.

**Fix (proposed, Agora side):** wire the derived rules file into `build.py`'s
DeepSeek brief so it reproduces the equations verbatim (Agora D17 already says
DeepSeek reads the rules files) — or make `build.py` use the card's own `## Brief`
section rather than reverse-engineering one from the header and tests. Until then,
a card must carry the exact formulas and the exact enum names in a form the brief
generator cannot override.

**Also:** the card hit the 2-run cap partly because a pre-skeleton race produced a
SPEC-INVALID run. `csrc/region.c` must exist as a compiling skeleton before the card
is activated (now committed).
