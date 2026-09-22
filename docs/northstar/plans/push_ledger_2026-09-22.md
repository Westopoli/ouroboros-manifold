# Push ledger, 2026-09-22 window

One row per event: freeze steps, attaches, reverts, parks, rung gates, harness errors. Times local (EDT).

| Time | Event | Detail |
|---|---|---|
| day1 09:xx | window opens | plan approved; dispatcher disabled (`systemctl --user disable --now agora-dispatcher.service`); `logs/` untracked; VM `win11edu` shut off (23 GB available) |
| day1 | F0 done | `logs/` untracked (`git rm --cached`); dispatcher `disabled`+`inactive`; VM already shut off, 23 GB available; clones `~/Projects/om-push/{m0,m1,m2,m3}` and `~/Projects/agora-push` (wn/qa-director) from GitHub, `.venv` symlinked; plan, Thirteenth round, panel journals committed (`0484ca8`) |
| day1 | F1 running | signature transcription workflow: eleven epic transcribers plus one struct track (Sonnet); F3 constants agent running alongside; further workflows wait for Westley's go-ahead (session limit) |
| day1 | F1 done | `signatures.toml`: 618 symbols, 38 structs, ABI 2; 251 rows resolved by rule (positional names cosmetic, doubtful status returns int), 14 canonical forms set for cross-epic conflicts (command functions take a group and a conftest wrapper adapts single-unit calls; `om_unit_get_pos` out-params with a tuple wrapper; `om_time_jump_run` optional report; tactical orchestrators return uint64_t); 6 wrappers to generate; 0 ambiguous rows left; per-epic ambiguity bullets in `f1_ambiguity_report.md` |
