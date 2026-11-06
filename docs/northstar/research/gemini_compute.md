# Gemini compute via Antigravity CLI — findings (2026-09-14)

Question: can Westley's spare Google AI Pro capacity do transcription-class work in the spec factory (Deliverable 2) and, later, in Agora's `spec` tool at night? Answer: yes, subscription-only, no API key, via the Antigravity CLI (`agy`). Spike below is complete and green; the wrapper contract in `scripts/agy_task.sh` is the thing both day-side Claude and night-side Agora call.

## What changed

Gemini CLI stopped serving Google AI Pro/Ultra requests on 2026-06-18 (Google Developers Blog, 2026-05-19). Replacement is Antigravity CLI, binary `agy`. Agent Skills, Hooks, Subagents, and Extensions carry over from Gemini CLI's model.

## Division of labor

- `agy` = text worker for transcription-class steps: draft e2e, fill test bodies, card brief prose, first-pass findings. Called by Claude in day sessions and by Agora's `spec` tool at night, same prompt/schema contract either way.
- Gemini web app (gemini.google.com) = Westley's manual tool only, for Deep Research reports (20/day on AI Pro, no export API) and Nano Banana Pro concept art (~100 generations/day, up to 14 reference images). Never automated; scripting the official CLI is Google's sanctioned use, browser-automating the web app is the risk zone this plan stays out of.
- No API key anywhere. The API paths for Deep Research ($1–$7/task) and image generation exist but are excluded by decision.

## Install

`curl -fsSL https://antigravity.google/cli/install.sh | bash` → `~/.local/bin/agy`. Installed 2026-09-14, version 1.2.2. Appends `~/.local/bin` to `PATH` in `.bashrc`/`.profile`.

## Sign-in

Westley signed in once via the interactive `agy` REPL (Google account, browser OAuth). Confirmed working: interactive session shows the author's account (Google AI Pro), model `Gemini 3.8 Flash`.

## Bug found and fixed: headless calls never saw the sign-in

Every headless call (`agy -p ... --output-format json`) from Claude's own shell failed with `authentication failed or timed out`, re-triggering a fresh OAuth URL each time — even after the interactive sign-in above completed.

**Isolation.** `agy`'s log printed the deciding line on every run: `composite_token_storage.go:123: Using file-based token storage because SSH session detected`. Claude's shell tool inherits `SSH_CONNECTION` (Claude Code's own remote-access session), which flips `agy` onto a file-based token store that was never written — the real sign-in used keyring storage in Westley's own terminal, which has no `SSH_CONNECTION` set. Confirmed by a single-variable test: unsetting `SSH_CONNECTION`, `SSH_CLIENT`, `SSH_TTY` before the same headless call made it find the keyring token immediately and return `{"status":"SUCCESS","response":"ok\n"}` in 2.7 s.

**Fix.** `scripts/agy_task.sh` unsets those three variables before invoking `agy`. Any other unattended caller (a plain cron job, a script run over SSH) needs the same line if it hits the same symptom.

**Residual risk.** This machine's real login used the OS keyring (Secret Service/dbus). Agora's night-side service environment must be able to unlock that same keyring headlessly, or `agy` falls back to a file-based store that has never been populated. The systemd-run test below only proves a *foreground-equivalent* headless call works when the keyring is already unlocked in the calling user's session — it does not prove a boot-time or fully detached service session can unlock it cold. If Agora's service runs as the same logged-in user session (not a fresh login), this is moot; if not, the fallback is a long-lived login file if `agy` offers one (not found in this spike — no such flag surfaced in `agy --help`), else day-side-only use, per the plan's original contingency.

## Spike checklist — results

1. **Plain-shell round trip.** `agy -p "say ok" --output-format json` → `SUCCESS`, real response, 2.7 s, once `SSH_*` vars are unset. Pass.
2. **Unattended test.** `systemd-run --user --collect --wait --pipe agy -p "say ok" --output-format json` (no controlling terminal, `DISPLAY` unset) → `SUCCESS` in 1.7 s. Pass, with the keyring-unlock caveat above.
3. **Quota probe.** 20 one-line prompts (~4 s each) plus 3 large real-repo prompts (read two epic files and list every rule id; read the full bible and summarize sacred principles in 5 bullets; read `PLAN.md` and summarize Stage 3/5). All 23 succeeded; the 3 large calls used 27k–133k input tokens each (prompt-cache hits on repeats: 471,808 cached tokens on the biggest one) and produced correct, on-target output — rule ids matched the epics' actual `R-###-##` ids, the bible summary and the Stage 3/5 summary were accurate. Westley checked the Gemini site session-usage indicator after the run: **0% of session limit consumed.** Plan quota comfortably absorbs the spec-factory's per-epic drafting load; no G1-credit spend needed for this workload size. Exact numeric AI Pro quota (requests/tokens per period) is still unpublished by Google — only the 0% reading is known.
4. **Rules-file check.** `agy`'s own bundled `agy-customizations` skill doc confirms it discovers `AGENTS.md` (or `GEMINI.md`) hierarchically from the working directory up to the repo root, workspace rules taking precedence over global (`~/.gemini/config/`) and built-in defaults. Pass — an `AGENTS.md` at the repo root carries the sub-agent constraints from `CLAUDE.md`.

## Permissions

Headless mode cannot prompt for tool permission, so any read/write/command tool call is auto-denied by default (`denied_actions` in the JSON, response empty). `--dangerously-skip-permissions` is required for every real headless call; without it the 3 large probes above returned empty responses with `denied_actions: [read_file]` / `[command]`. `scripts/agy_task.sh` always passes it, matching the plan's original design (`agy` is treated as an implementer sub-agent under `CLAUDE.md`'s rules regardless of what permissions it holds at the tool layer).

## Fences (unchanged from the plan)

`agy` never designs, never edits `docs/bible/**`, `docs/northstar/**`, or tests it did not draft, and returns findings plus a proposed change on ambiguity. This is now written into `AGENTS.md` at the repo root, which `agy` loads automatically (see rules-file check above); `CLAUDE.md` names `agy` as an implementer sub-agent for Claude's own reading.

## Image prompt kit

Not built this session — depends on the site repo's three.js page existing first (to render the six unit GLBs for reference images), which is Deliverable 3. Tracked as follow-up, `docs/legacy/mvp/site/prompt_kit.md`, once the site scaffold lands.
