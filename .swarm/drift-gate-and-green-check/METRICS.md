# Cascade metrics — `drift-gate-and-green-check`

- window: 2026-09-17T22:40:18+00:00 → 2026-09-17T22:50:12+00:00 (9.9 min)
- overlord session: `47d2bfa1-631d-41d9-a94a-8c198e61f4c9` model=claude-sonnet-5  variant=-  skill=?/b02ba568cca21831

| role | model | n | turns | fresh | cache_read | output | $ |
|---|---|---|---|---|---|---|---|
| overlord | claude-sonnet-5 | 1 | 52 | 52,348 | 20,170,457 | 32,048 | 4.5638 |
| leaf | claude-sonnet-5 | 2 | 38 | 147,669 | 2,766,162 | 29,804 | 1.2204 |
| test-fixer | claude-sonnet-5 | 1 | 6 | 54,735 | 243,940 | 4,466 | 0.2303 |
| **total** | | 4 | 96 | | | | **6.0145** |

overlord share of $: **75.9%**

- leaves 28 · log rows {'clean': 2} · gates FAIL 0 / ADVISORY 0 / PASS 28 over 2 files
- audit default: 2 round(s), 🔴4 🟡34 🟢0
- questions 0 / answers 0 · proposals 0 · sweep flagged 0
