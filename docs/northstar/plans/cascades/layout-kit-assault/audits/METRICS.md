# Cascade metrics — `layout-kit-assault`

- window: 2026-11-06T00:16:01+00:00 → 2026-11-06T02:03:05+00:00 (107.1 min)
- overlord session: `db98320a-0522-401b-91ae-f1f3583f73a5` model=claude-sonnet-5-5  variant=-  skill=?/49420fd3758c2498

| role | model | n | turns | fresh | cache_read | output | $ |
|---|---|---|---|---|---|---|---|
| overlord | claude-sonnet-5-5 | 1 | 86 | 172,745 | 21,794,613 | 74,879 | 8.6975 |
| leaf | claude-sonnet-5-5 | 3 | 40 | 351,177 | 3,312,279 | 152,056 | 4.5913 |
| other | claude-sonnet-5-5 | 1 | 70 | 872,051 | 11,984,620 | 136,343 | 8.9106 |
| saboteur | claude-sonnet-5-5 | 1 | 20 | 90,425 | 1,143,349 | 37,309 | 1.2417 |
| shard-test-writer | claude-sonnet-5-5 | 2 | 79 | 374,844 | 10,424,415 | 202,827 | 7.5753 |
| test-auditor | claude-sonnet-5-5 | 3 | 51 | 397,937 | 3,801,221 | 132,190 | 4.6154 |
| **total** | | 11 | 346 | | | | **35.6318** |

overlord share of $: **24.4%**

- leaves 13 · log rows {'clean': 3} · gates FAIL 0 / ADVISORY 4 / PASS 56 over 4 files
- audit default: 4 round(s), 🔴0 🟡0 🟢0
- questions 13 / answers 1 · proposals 0 · sweep flagged 3
