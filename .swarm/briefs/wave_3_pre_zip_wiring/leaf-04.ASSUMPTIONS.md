# leaf-04 assumptions

## A1: beats.json structure = dict keyed by TUT_NNN, not list

Brief acceptance text says "loads as JSON list of length 5" but existing `simulation/library/tutorial/beats.json` is JSON object keyed by `TUT_001`..`TUT_005`. Brief also instructs preserve all other fields verbatim + no add/remove beats. Inferring: keep dict shape, assert dict-of-length-5 instead of list-of-length-5. Ordering assertion (TUT_001 → mission_load etc.) interpreted as key→trigger_event mapping check via sorted dict keys.

Impact: assertion (1) reads dict-of-length-5; assertion (6) iterates sorted keys to verify TUT_NNN → trigger mapping. No impact on impl beyond field rename + value swap.

Escalate if reviewer wants list shape — that requires breaking change to existing readers (none in scope per leaf-04 contract).
