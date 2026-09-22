# Push ledger, 2026-09-22 window

One row per event: freeze steps, attaches, reverts, parks, rung gates, harness errors. Times local (EDT).

| Time | Event | Detail |
|---|---|---|
| day1 09:xx | window opens | plan approved; dispatcher disabled (`systemctl --user disable --now agora-dispatcher.service`); `logs/` untracked; VM `win11edu` shut off (23 GB available) |
| day1 | F0 done | `logs/` untracked (`git rm --cached`); dispatcher `disabled`+`inactive`; VM already shut off, 23 GB available; clones `~/Projects/om-push/{m0,m1,m2,m3}` and `~/Projects/agora-push` (wn/qa-director) from GitHub, `.venv` symlinked; plan, Thirteenth round, panel journals committed (`0484ca8`) |
| day1 | F1 running | signature transcription workflow: eleven epic transcribers plus one struct track (Sonnet); F3 constants agent running alongside; further workflows wait for Westley's go-ahead (session limit) |
| day1 | F1 done | `signatures.toml`: 618 symbols, 38 structs, ABI 2; 251 rows resolved by rule (positional names cosmetic, doubtful status returns int), 14 canonical forms set for cross-epic conflicts (command functions take a group and a conftest wrapper adapts single-unit calls; `om_unit_get_pos` out-params with a tuple wrapper; `om_time_jump_run` optional report; tactical orchestrators return uint64_t); 6 wrappers to generate; 0 ambiguous rows left; per-epic ambiguity bullets in `f1_ambiguity_report.md` |
| day1 | F3 done | `alg_constants.py --emit/--lint`, `csrc/om_constants.h` 363 defines (ALG-01..75), allowlist 336 grandfathered literals, 25 constants unparsed and listed (categorical tables, boolean flags, `REFUSAL_TENSION_PENALTY_PCT = 8 / 100` ambiguous); `libm_lint.py` recursive with rand/srand/time/clock/qsort/bsearch banned; both lints OK on csrc; commits `c8806c4`, `29d3cf3` |
| day1 | F4 done | `docs/architecture.md` "C transport v1" (hello, snapshot, delta, command, tactical, chronicle, mission, debrief frames; big-endian length prefix both ways; no names, positions or prose), three JSON schemas, `tests/transport/test_pipe_shapes.py` red until T1; commit `71b65e4` |
| day1 | F2 running | one Sonnet agent: tick wiring (diplomacy, technology, lifecycle, tactical orchestrator) with order-fault controls, core symbols, ABI 2, weak `om_world_generate`, D1 conftest-only, Makefile `OPT`/`WERROR`/build dirs/pipe target, `specfactory.toml`; workflow #2 (F1b generator) fires when F2 lands |
