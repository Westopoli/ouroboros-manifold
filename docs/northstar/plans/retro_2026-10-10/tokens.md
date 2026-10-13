# Token usage, visible game programme window

Window: 2026-10-07 00:00 to 2026-10-10 10:00 America/New_York (-0400); = 2026-10-07T04:00Z .. 2026-10-10T14:00Z. Script: tokens.py (not committed) (python3 -I). Run at 2026-10-10 09:25 EDT, so the window end is not yet reached: data runs to the run time.
JSONL files scanned: 2332. Assistant entries with usage, deduped by (file, message.id) keeping the last line (only output_tokens varies across lines of one id, and the last is always the max): 8627.
Scope "manifold" = project dirs starting -home-westopoli-Projects-ouroboros-manifold (main + -m3). No om-push project dir exists. This accounting session itself (7e9d8393) is inside the window and included.

Price assumptions ($ per million tokens: input / cache write / cache read / output): Sonnet 5.5 3 / 3.75 / 0.30 / 15; Opus 5.5 15 / 18.75 / 1.50 / 75; Fable 5.1 20 / 25 / 2.00 / 100. Model strings matched: claude-sonnet-5-5, claude-opus-5-5, claude-fable-5-1; anything else (e.g. "<synthetic>") is bucket "other" at Sonnet prices.

## Scope: manifold project dirs (headline)

Overall:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| ALL | 8,623 | 30,074 | 57,601,201 | 784,631,572 | 4,993,223 | 847,256,070 |

Cache-read share of total tokens: 92.61%

By project dir:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| -home-westopoli-Projects-ouroboros-manifold | 8,623 | 30,074 | 57,601,201 | 784,631,572 | 4,993,223 | 847,256,070 |

By project dir x kind (session = top-level file, subagent = under subagents/):
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| -home-westopoli-Projects-ouroboros-manifold / session | 1,233 | 15,214 | 10,135,807 | 524,551,707 | 1,173,914 | 535,876,642 |
| -home-westopoli-Projects-ouroboros-manifold / subagent | 7,390 | 14,860 | 47,465,394 | 260,079,865 | 3,819,309 | 311,379,428 |

By kind x model:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| session / <synthetic> | 2 | 0 | 0 | 0 | 0 | 0 |
| session / claude-fable-5-1 | 1,045 | 14,842 | 7,370,661 | 425,472,619 | 947,264 | 433,805,386 |
| session / claude-sonnet-5-5 | 186 | 372 | 2,765,146 | 99,079,088 | 226,650 | 102,071,256 |
| subagent / claude-sonnet-5-5 | 7,390 | 14,860 | 47,465,394 | 260,079,865 | 3,819,309 | 311,379,428 |

By model:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| <synthetic> | 2 | 0 | 0 | 0 | 0 | 0 |
| claude-fable-5-1 | 1,045 | 14,842 | 7,370,661 | 425,472,619 | 947,264 | 433,805,386 |
| claude-sonnet-5-5 | 7,576 | 15,232 | 50,230,540 | 359,158,953 | 4,045,959 | 413,450,684 |

By local day (America/New_York; 10-10 is partial, to 10:00 or to now if earlier):
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| 10-07 | 1,604 | 3,212 | 14,806,854 | 230,219,910 | 1,250,409 | 246,280,385 |
| 10-08 | 3,783 | 8,818 | 22,338,688 | 260,635,623 | 1,873,329 | 284,856,458 |
| 10-09 | 2,090 | 12,106 | 14,114,455 | 227,078,097 | 1,230,430 | 242,435,088 |
| 10-10 | 1,146 | 5,938 | 6,341,204 | 66,697,942 | 639,055 | 73,684,139 |

Distinct top-level session files with in-window turns: 5
Distinct subagent transcript files with in-window turns: 430 (of which under workflows/: 288); parent sessions spawning them: 3

Top 12 top-level session files by total tokens:
| dir | file | turns | total |
|---|---|---|---|
| -home-westopoli-Projects-ouroboros-manifold | 1e828a6f-17d9-426d-af2c-1266f6b1c9af.jsonl | 610 | 223,815,919 |
| -home-westopoli-Projects-ouroboros-manifold | cb87e7a3-1ce3-4046-b25c-8e237293a96c.jsonl | 422 | 208,200,161 |
| -home-westopoli-Projects-ouroboros-manifold | 71834282-7abc-4b12-97d6-38cad03f27c6.jsonl | 137 | 96,451,156 |
| -home-westopoli-Projects-ouroboros-manifold | 841c3942-97d9-4e87-846d-89e2097d2851.jsonl | 49 | 5,620,100 |
| -home-westopoli-Projects-ouroboros-manifold | 7e9d8393-6f9a-44e1-a26b-66264f334079.jsonl | 15 | 1,789,306 |

Cost estimate (list prices below):
| family | turns | tokens | USD |
|---|---|---|---|
| sonnet | 7,576 | 413,450,684 | $356.85 |
| fable | 1,045 | 433,805,386 | $1,130.24 |
| other | 2 | 0 | $0.00 |
| TOTAL | 8,623 | 847,256,070 | $1,487.08 |

Cache-write tokens: 57,601,201, of which tagged ephemeral_1h: 10,135,807 (17.6%; by family {'fable': 7370661, 'sonnet': 2765146, 'other': 0}). The 1h tag appears only on top-level session entries; subagent entries are all 5m writes. All writes are priced at the 5m rate per the brief; if 1h writes bill at 2x input (Sonnet 6, Fable 40 per M) the estimate rises by roughly 1h_sonnet*2.25 + 1h_fable*15 per M (about $6 + $110 here), so cache-write dollars are a floor.

Subagent files by dominant model (tokens per file; p90 = nearest-rank):
| model | files | median tokens | p90 tokens | sum tokens |
|---|---|---|---|---|
| claude-sonnet-5-5 | 430 | 373,098 | 1,591,080 | 311,379,428 |
| ALL | 430 | 373,098 | 1,591,080 | 311,379,428 |

## Scope: all project dirs on the machine

Overall:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| ALL | 8,627 | 30,082 | 57,655,262 | 784,788,544 | 4,993,447 | 847,467,335 |

Cache-read share of total tokens: 92.60%

By project dir:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| -home-westopoli-Projects-agora | 4 | 8 | 54,061 | 156,972 | 224 | 211,265 |
| -home-westopoli-Projects-ouroboros-manifold | 8,623 | 30,074 | 57,601,201 | 784,631,572 | 4,993,223 | 847,256,070 |

By project dir x kind (session = top-level file, subagent = under subagents/):
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| -home-westopoli-Projects-agora / session | 4 | 8 | 54,061 | 156,972 | 224 | 211,265 |
| -home-westopoli-Projects-ouroboros-manifold / session | 1,233 | 15,214 | 10,135,807 | 524,551,707 | 1,173,914 | 535,876,642 |
| -home-westopoli-Projects-ouroboros-manifold / subagent | 7,390 | 14,860 | 47,465,394 | 260,079,865 | 3,819,309 | 311,379,428 |

By kind x model:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| session / <synthetic> | 2 | 0 | 0 | 0 | 0 | 0 |
| session / claude-fable-5-1 | 1,045 | 14,842 | 7,370,661 | 425,472,619 | 947,264 | 433,805,386 |
| session / claude-sonnet-5-5 | 190 | 380 | 2,819,207 | 99,236,060 | 226,874 | 102,282,521 |
| subagent / claude-sonnet-5-5 | 7,390 | 14,860 | 47,465,394 | 260,079,865 | 3,819,309 | 311,379,428 |

By model:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| <synthetic> | 2 | 0 | 0 | 0 | 0 | 0 |
| claude-fable-5-1 | 1,045 | 14,842 | 7,370,661 | 425,472,619 | 947,264 | 433,805,386 |
| claude-sonnet-5-5 | 7,580 | 15,240 | 50,284,601 | 359,315,925 | 4,046,183 | 413,661,949 |

By local day (America/New_York; 10-10 is partial, to 10:00 or to now if earlier):
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| 10-07 | 1,604 | 3,212 | 14,806,854 | 230,219,910 | 1,250,409 | 246,280,385 |
| 10-08 | 3,787 | 8,826 | 22,392,749 | 260,792,595 | 1,873,553 | 285,067,723 |
| 10-09 | 2,090 | 12,106 | 14,114,455 | 227,078,097 | 1,230,430 | 242,435,088 |
| 10-10 | 1,146 | 5,938 | 6,341,204 | 66,697,942 | 639,055 | 73,684,139 |

Distinct top-level session files with in-window turns: 6
Distinct subagent transcript files with in-window turns: 430 (of which under workflows/: 288); parent sessions spawning them: 3

Top 12 top-level session files by total tokens:
| dir | file | turns | total |
|---|---|---|---|
| -home-westopoli-Projects-ouroboros-manifold | 1e828a6f-17d9-426d-af2c-1266f6b1c9af.jsonl | 610 | 223,815,919 |
| -home-westopoli-Projects-ouroboros-manifold | cb87e7a3-1ce3-4046-b25c-8e237293a96c.jsonl | 422 | 208,200,161 |
| -home-westopoli-Projects-ouroboros-manifold | 71834282-7abc-4b12-97d6-38cad03f27c6.jsonl | 137 | 96,451,156 |
| -home-westopoli-Projects-ouroboros-manifold | 841c3942-97d9-4e87-846d-89e2097d2851.jsonl | 49 | 5,620,100 |
| -home-westopoli-Projects-ouroboros-manifold | 7e9d8393-6f9a-44e1-a26b-66264f334079.jsonl | 15 | 1,789,306 |
| -home-westopoli-Projects-agora | c33688df-78da-419e-a840-370d5af9621d.jsonl | 4 | 211,265 |

Cost estimate (list prices below):
| family | turns | tokens | USD |
|---|---|---|---|
| sonnet | 7,580 | 413,661,949 | $357.10 |
| fable | 1,045 | 433,805,386 | $1,130.24 |
| other | 2 | 0 | $0.00 |
| TOTAL | 8,627 | 847,467,335 | $1,487.34 |

Cache-write tokens: 57,655,262, of which tagged ephemeral_1h: 10,189,868 (17.7%; by family {'fable': 7370661, 'sonnet': 2819207, 'other': 0}). The 1h tag appears only on top-level session entries; subagent entries are all 5m writes. All writes are priced at the 5m rate per the brief; if 1h writes bill at 2x input (Sonnet 6, Fable 40 per M) the estimate rises by roughly 1h_sonnet*2.25 + 1h_fable*15 per M (about $6 + $110 here), so cache-write dollars are a floor.

Subagent files by dominant model (tokens per file; p90 = nearest-rank):
| model | files | median tokens | p90 tokens | sum tokens |
|---|---|---|---|---|
| claude-sonnet-5-5 | 430 | 373,098 | 1,591,080 | 311,379,428 |
| ALL | 430 | 373,098 | 1,591,080 | 311,379,428 |

Non-manifold project dirs in window, for reference:
| key | turns | input | cache write | cache read | output | total |
|---|---|---|---|---|---|---|
| -home-westopoli-Projects-agora | 4 | 8 | 54,061 | 156,972 | 224 | 211,265 |

Cross-file duplicate message ids in manifold scope: 0 ids, 0 tokens counted twice (spec dedupes per file only; left as is).

