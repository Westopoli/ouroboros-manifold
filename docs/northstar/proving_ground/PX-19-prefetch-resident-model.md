# PX-19 — Prefetch and resident model

Run 2026-09-21 (ouroboros `8967fb0`: `scripts/specfactory/prefetch_measure.py`, `tests/specfactory/test_prefetch_measure.py`, 14 new tests; full `tests/specfactory/` suite 155 passed). Claim (Factory, "Pipelining"): the CPU slot prepares the next card while the GPU builds, so the next attempt starts within one tick of the previous outcome; the worker stays resident (`OLLAMA_KEEP_ALIVE=-1`).

Result: **partial pass**. CPU prep is real but tiny (2.23 s), so there is almost nothing for prefetch to hide. Model load is real and substantial (median ~25-47 s depending on model) and is not currently amortized (`keep_alive` is never sent, confirmed absent from every payload `chat_full` builds). But most of the measured "gap" distribution's tail is neither prep nor load: it is the dispatcher's queue sitting empty, which prefetching and a resident model do nothing to close. The two numbers the brief's own "Facts" section quotes (63 s, 131 s, 62 s) are real and reproduced exactly, but they are the *best case* (a card that resolves in one dispatcher tick), not representative of the median.

## 1. Gap distribution (whole `cron.log`)

Tool: `scripts/specfactory/prefetch_measure.py gaps ~/Projects/agora/runs/cron.log` (evidence: `docs/northstar/proving_ground/evidence/px19/gaps.json`).

cron.log carries no date on any line, only `[HH:MM:SS]`. There are no per-candidate `candidate`/`rung` lines in cron.log at all (grep found zero; the brief's alternative, "the run dir's `state.json` first timestamp", also does not exist — `state.json` has no timestamp field of any kind, confirmed by inspecting `~/Projects/agora/runs/204b3-e05-damage-history-20260919-1440/state.json`). So the proxy used is: every `[HH:MM:SS] dispatch -> build` / `dispatch -> burn` line marks the start of a queue-task attempt, and the gap is the wall time from one such tick to the next — this is exactly how the brief's own two worked examples were computed (verified: reproducing DONE-at-21:50:30 -> next dispatch at 21:51:33 gives 63 s; 14:40:31 -> 14:42:42 gives 131 s, then -> 14:43:44 gives 62 s, all three exact). To get real dates across the log's many days without a per-line date, the parser anchors on the `YYYYMMDD` embedded in each outcome line's own run-directory name (`report at .../<task>-YYYYMMDD-HHMM.../report.md`) and falls back to same-day rollover only where no anchor is available (`prefetch_measure.py:75-113`).

**Numbers (n=468 gaps, 469 ticks):**

| stat | value |
|---|---|
| median | 134.0 s |
| p90 | 2205.0 s (36.75 min) |
| max | 1,433,794 s (~16.6 days) |
| gaps > 300 s | 212 / 468 (45.3%) |

The max is not a parser bug: it is the real elapsed time between the last `108-probe-b-build` tick (line 7144, 2026-08-19) and the first `200-e02-region-state` tick (line 80669, 2026-09-10+) — a historical stretch before the continuous-dispatcher systemd unit existed. The distribution is not unimodal. Splitting each gap by whether any other dispatcher tick (of any kind — `qa`, `driver`, `digest`, ...) was logged between the two build/burn ticks (evidence: `evidence/px19/gaps_backtoback.json`):

| subset | n | median | p90 | max | >300 s |
|---|---|---|---|---|---|
| back-to-back (no intervening tick) | 431 | 62 s | 2032 s | 86,640 s | 177 (41%) |
| loose (something else ran, or the dispatcher was idle/down between) | 37 | 5627 s | 58,003 s | 1,433,794 s | 35 (95%) |

The "loose" 37 pairs account for nearly all of the extreme tail and are queue-idle or dispatcher-downtime, not GPU-busy time — pipelining a next card's CPU prep cannot start a card that has not been released yet, and it cannot restart a stopped systemd unit. Even within the "back-to-back" 431 pairs, 41% still exceed 300 s. That is *not* explained by CPU prep or model load either: cron.log's dispatch-tick timestamp is written when the tick *starts*, before `build.py` runs, and `build.py`'s own run for a card needing more than one candidate (multiple worker calls, possibly a DeepSeek hint/reset) can itself run for several minutes before the next tick's line appears. `candidates.jsonl` records each attempt's `wall_s` but no absolute timestamp, so this cannot be separated from the tick-to-tick gap with the data cron.log and candidates.jsonl currently keep — flagged here as a measurement limit, not resolved. Concretely: the brief's two worked examples are gate cards or a card resolving on one baseline check, i.e. the fast case; the median and the back-to-back-but-still-slow 41% are cards where the *current* card's own multi-candidate build, not idle waiting, fills most of the gap.

## 2. CPU prep time (one real parked card, scratch worktree)

Card: `queue/parked/208a1-e04-launch-templates.md.hold` (`csrc/events.c`, `om_event_template_count`/`om_event_template_get`/`om_event_template_by_name`, story S-030). Chosen over the brief's implicit assumption that any `.hold` file is still open: `203a-e05-candidate-scoring.md.hold` was checked first and found stale — `om_faction_candidates` already has a full 400+-line implementation on `main` (`csrc/agent.c:47`), so its baseline would pass trivially and not exercise a real "still open" prep sequence. `208a1`'s target (`om_event_template_count` etc. in `csrc/events.c`) is still a genuine `/* STUB */` on `main`, confirmed by reading the file before running anything.

Tool: `scripts/specfactory/prefetch_measure.py prep queue/parked/208a1-e04-launch-templates.md.hold --repo <ouroboros-manifold> --worktree /tmp/pxA/px19 --commit HEAD` (evidence: `evidence/px19/prep_208a1.json`). Worktree created with `git worktree add --detach`, removed with `git worktree remove --force` + `git worktree prune` in a `finally` block; `git worktree list` confirmed empty of `/tmp/pxA` entries after the run and after full cleanup.

| step | seconds | note |
|---|---|---|
| `git worktree add --detach` | 0.509 | |
| `make -s libouroboros.so` | 0.640 | matches `Makefile` target (`Makefile:24-25`) |
| baseline pytest of `acceptance[0]` | 0.909 | exit 1 (red, as expected — real stub) |
| `scripts/specfactory/card_lint.py --project <worktree> --json` | 0.093 | exit 0, LINT OK; this tool lives in *this* repo, not agora — the brief's "if present in agora" did not find it there because it isn't there |
| `scripts/specfactory/card_slice.py --project <worktree> --write` | 0.077 | exit 0; run against a scratch copy of the card file under `/tmp/pxA`, never against agora's own `queue/parked/208a1-...md.hold` |
| prompt assembly (string build only) | 0.0003 | 47,681 chars, ~11,920 estimated tokens (chars/4) |
| **total** | **2.227 s** | |

`card_lint.py` and `card_slice.py` are real, existing tools in this repo (`scripts/specfactory/card_lint.py`, `scripts/specfactory/card_slice.py` — not brief-hypothesized, not written for this probe), from an earlier design-lane session. Neither exists in `~/Projects/agora/scripts/`.

Prompt assembly reproduces (not imports, to avoid pulling in `agy_client`/`deepseek_client` module-level code) `build.py`'s `_worker_user_c` (`~/Projects/agora/scripts/build.py:316-332`) for the first-candidate case: no previous attempt, no advisor hint, brief taken straight from the card's own `## Brief for DeepSeek` section (`build.py:833`, since `lang == "c" and card_brief` skips the DeepSeek driver call entirely for this card). Header text and extra context come from `header_file`/`extra_context_files` per `build.py:786-817`. The token count is a plain `len(text)//4` heuristic, explicitly not a reproduction of anything in `build.py`, because there is nothing to reproduce: `OllamaReply` (`~/Projects/agora/scripts/cascade_types.py:982-990`) carries only `content`, `thinking`, `done_reason`, `prompt_eval_count`, `eval_count` — the token count is read back from Ollama's response *after* the call, never estimated before it.

2.227 s total prep is small next to even the fastest observed gap (62 s median, back-to-back subset) — CPU prep was never the bottleneck for this card.

## 3. Model load time

`grep -rl load_duration ~/Projects/agora/runs` finds 672 files, but `scripts/specfactory/prefetch_measure.py loads ~/Projects/agora/runs` (evidence: `evidence/px19/loads.json`) shows these are 672 copies of exactly **6 distinct files** (deduped by sha256), all `resp_t1..t4.json` / `resp_qwen_16384.json` / `resp_qwen_32768.json` under `docs/northstar/research/harness_defects_2026-09-17/evidence/tokens/` — a single evidence set from a one-off 2026-09-17 investigation, checked into this repo's own docs tree, and copied once into every subsequent Agora worktree snapshot simply because each worktree is a full checkout of `main` at that point. This is **not per-card telemetry**: `state.json` never carries `load_duration` (0 hits across every `state.json` under `~/Projects/agora/runs`), and `OllamaReply` (§2) drops the field entirely — Agora currently has zero real per-card visibility into model load time.

The 6 distinct values found (brief's own citation, `resp_t2.json`, load_duration=14.16 s, reproduced exactly):

| model | load_duration (s) |
|---|---|
| gpt-oss:20b | 0.49 |
| gpt-oss:20b | 14.16 |
| gpt-oss:20b | 15.54 |
| gpt-oss:20b | 35.91 |
| qwen3-coder:30b | 44.55 |
| qwen3-coder:30b | 49.66 |

All 6 (n=6): median 25.72 s. `build.py`'s actual `WORKER_MODEL` default is `qwen3-coder:30b` (`~/Projects/agora/scripts/ollama_client.py:18`); the two qwen-specific samples (n=2, thin) give median 47.11 s. Both are one-off measurements from a token-budget investigation (different `num_ctx`, not a production sampling), not a live distribution — flagged as a limit on this number's confidence, not hidden.

Per-card cost: with the default 5-minute `OLLAMA_KEEP_ALIVE` (never overridden anywhere — `/etc/systemd/system/ollama.service` sets only `PATH`; `~/Projects/agora/scripts/ollama_client.py`'s `chat_full` payload (`ollama_client.py:26-39`) never sends a `keep_alive` key), a card whose worker calls are spaced more than 5 minutes apart (multi-candidate builds crossing a DeepSeek hint/reset, or any card following an idle/QA stretch) pays this load cost again on its first call. A card resolving in one fast candidate right after the previous one, inside the keep-alive window, pays it zero times — Ollama would already have the model warm.

## Projected gap with prefetch + resident model

Pass criteria formula: `max(poll_interval, gap − prep − load)`. Poll interval: `~/.config/systemd/user/agora-dispatcher.service:12` — `while true; do flock -n /tmp/agora.lock ... next.py ...; sleep 60; done` — **60 s**, not found in `next.py` itself (the dispatcher loop lives in the systemd unit, not the script).

Using prep = 2.227 s (§2) and load = 47.11 s (qwen3-coder:30b median, n=2; the all-model n=6 median of 25.72 s is given alongside as the broader, less model-specific bound):

| gap basis | raw gap | − prep − load (qwen) | floored at 60 s | − prep − load (all n=6) | floored |
|---|---|---|---|---|---|
| whole-log median | 134 s | 84.7 s | 84.7 s | 106.1 s | 106.1 s |
| whole-log p90 | 2205 s | 2155.7 s | 2155.7 s | 2177.1 s | 2177.1 s |
| back-to-back median | 62 s | 12.7 s | **60 s** | 34.1 s | 60 s |

Reading these together with §1: for the fast/back-to-back cards (the case the brief's own worked examples describe), prefetch + resident model would save at most ~2 s off an already-near-floor 62 s gap — there's nothing left to hide. For the whole-log median (134 s, a mix of fast and multi-candidate cards), the model-load term is the one doing real work (roughly a third of the gap), and CPU prep is negligible either way. For p90, subtracting prep and load barely moves the number at all, because p90 is dominated by queue-empty/dispatcher-idle time (§1's "loose" pairs), which prefetching a next card cannot help if there is no next card yet, and a resident model cannot help if nothing is calling it.

**Proposal (not implemented or verified live in this probe — no Ollama call was made):** send `"keep_alive": -1` in the `chat_full` payload (`~/Projects/agora/scripts/ollama_client.py:26`, alongside the existing `payload` dict fields), or equivalently `Environment=OLLAMA_KEEP_ALIVE=-1` on `ollama.service`. This is a one-line change for the executor to make and verify; this probe only measured the gap it would close.

## Deviations from the brief worth flagging

- No `candidate`/`rung` lines exist in cron.log, and `state.json` has no timestamp field — the brief's two named alternatives for "first model call" are both unavailable; the dispatch-tick proxy was used instead (§1), which the brief's own two worked examples already implicitly rely on.
- `resp_*.json`/`state.json` `load_duration` data under `~/Projects/agora/runs` is 672 duplicate copies of 6 files from this repo's own `docs/northstar/research/harness_defects_2026-09-17/` evidence, not live telemetry — there is currently no way to get a real per-card load-time sample from Agora's own artifacts.
- `card_lint.py`/`card_slice.py` exist in *this* repo (`scripts/specfactory/`), not in agora as the brief hedged ("if present"). Used directly.
- `203a-e05-candidate-scoring.md.hold`, the first card checked for §2, is stale (its target function is already fully implemented on `main`); `208a1-e04-launch-templates.md.hold` was substituted as a card whose target is still a genuine stub.
- `build.py` has no pre-call token counter to "reuse" for prompt assembly (§2); `OllamaReply` only carries post-call `prompt_eval_count`/`eval_count`. The chars/4 estimate in this probe's own tool is a labelled approximation, not a reproduction.
- File line numbers the brief cited in `build.py` (691-693 worktree, 747-756 baseline, 870-877 prompt, 886-888 first model call) were checked against the current file and match exactly — no drift.

Design consequences are left for the design lane review.
