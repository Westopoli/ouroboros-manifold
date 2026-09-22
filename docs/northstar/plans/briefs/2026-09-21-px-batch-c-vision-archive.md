# HANDOFF BRIEF — PX batch C: PX-12, PX-9 (vision judge, refiner archive)

Self-contained. Program context: `2026-09-21-factory-program.md`; design under test: `docs/northstar/PLAN.md` section "The Factory" ("Oracles": vision judge; "Self-improvement, bounded": the refiner). Results as `docs/northstar/proving_ground/PX-12-*.md`, `PX-09-*.md` plus `SCORECARD.md` rows, "Design consequences" left blank. Normal prose.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- PX-12(b) pulls and runs a local vision model on the GPU; it runs only in a window Westley grants with the chain paused. PX-12(a) and PX-9 need no GPU.
- Cloud vision calls are capped: at most 40 judged screenshots per model, and every call's cost is logged to `~/Projects/agora/runs/costs.jsonl` under `campaign: px12-vision-probe`. Stop and report if a route costs more than $2 total.
- No game code. New files under ouroboros `scripts/specfactory/`, `tests/specfactory/`, `docs/northstar/proving_ground/` and evidence dirs; under agora only data under `projects/proving-ground/`. Scratch under `/tmp/pxC/`.
- Commit and push per PX. Trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Never stage files you did not create.

## PX-12 — vision judge

**Claim ("Oracles"):** visual claims are judged by Gemini vision via agy by default, capped; a local model only if it measurably fits beside the worker; state first, vision never alone, never absent.

**Facts that already argue against the default.** `~/Projects/agora/scripts/agy_client.py` has no image input (zero hits for image, `--image`, vision), so "Gemini vision via agy" does not exist as a route today; every agy quota group was empty for 45 hours during PX-17. `ollama list` has no vision model (`gpt-oss:20b`, `qwen3:8b`, `qwen3-coder:30b` only); `qwen3-coder:30b` is 18 GB against a 12 GB card, so a local VLM is a swap with the worker, not co-resident. Screenshots from QA runs sit in the run dir root (`runs/director-20260912-0259/shot-1.png`).

**Fixture.** Twenty screenshots of the probe-D toy scene (PX-02's scene, on the private Xvfb): ten clean at varied states (label counts, layer 1 and 2) and ten with one planted rendering defect each, at least three defect classes with three or more instances: wrong layer height (dot drawn at layer 1 height while state says 2), missing element (label absent), stale label (text one behind the state). Plant by editing the toy scene in a scratch worktree, never the committed scene. Beside each PNG, the state JSON the daemon reported, and a one-line claim in the spec's form (`the layer dot sits higher on screen than at layer 1`).

**(a) Cloud routes, in order, stopping at the first that works.**
1. `agy`: check `agy --help` and `agy models` for any image or file input; if there is one, use it with `gemini-3.7-flash-high`. If not, record that the design's named route does not exist.
2. The Anthropic API through the library builder's existing client (offline use is allowed by the "no runtime API calls during play" rule; QA is not play): `claude-sonnet-4-20250514` or newer with image input.
3. DeepSeek through Agora's driver only if the model accepts images (check; `deepseek-v4-flash` may not).
Judge prompt: the claim, the state JSON, the screenshot; answer JSON `{"claim_holds": bool, "defect": "<class or none>", "confidence": 0-1}`. Score precision and recall per defect class and overall, cost and wall per call.

**(b) Local.** In the granted window: `ollama pull qwen2.5-vl:7b` (or the smallest `qwen3-vl` if listed), record VRAM (`nvidia-smi`) with the worker unloaded and note that co-residence is impossible at 18 GB plus 6 GB on 12 GB; judge the same twenty; same scores; wall per call. Then `ollama rm` it unless Westley says keep.

**Pass.** Per route: precision and recall per class; the claim "vision catches planted rendering defects" needs recall ≥ 0.8 and precision ≥ 0.8 on at least one route. Report which route is viable, its cost per call, and whether local matches cloud.

## PX-9 — refiner proposals from the archive

**Claim ("Self-improvement, bounded"):** the refiner scores strategy choices offline from the run archive, and the offline score agrees with the live outcome on a held-out card.

**Facts.** The archive is `~/Projects/agora/runs/<run>/candidates.jsonl` (fields per line: `n, rung, model, think, passed, failed, failing_ids, body_lines, reason, diff_sha, wall_s`) and `runs/metrics.jsonl` (`ts, kind, task, outcome, candidates, interventions, resets, best_failed, rung_done, wall_minutes, usd` for build rows). Missing today: per-candidate `prompt_hash` (exists only on the QA side as `ConfigStamp`, `cascade_types.py:222-244`) and any `hint_used` marker; the escalator's hints are visible only in each run's `report.md` interventions table and `state.json` log. The program listed PX-9 as blocked on archive fields; this PX measures how far the existing fields go and names the missing ones exactly.

**Do.**
1. `scripts/specfactory/archive_score.py`: load every run's `candidates.jsonl` with its `report.md` and `state.json`; reconstruct per candidate whether a hint preceded it (from the intervention timestamps in `state.json`; state the rule you used). Output one table: run, card, candidate n, rung, model, hint before (yes/no/unknown), passed, failed, wall.
2. Score two strategies offline over the 2026-09-17 to 2026-09-20 runs: "hint after 3 unassisted failures" versus "hint after 2": for each card, the candidate index at which it first went green (or never), and the wall to that point, under each policy, by replaying the archive (a card's candidates are what they were; the policy only decides when the hint would have been available; a candidate after the hint under the real run is usable only if the policy also has a hint by then). Same method as PX-16's replay.
3. Hold out the last card that went DONE with a hint (find it in `metrics.jsonl`); the offline score must predict which policy finishes it sooner; compare with what actually happened.

**Pass.** The table exists for every run with the `unknown` count reported; the two policies scored with wall and candidates-to-green per card; the held-out card's live outcome matches the offline prediction, or the mismatch is explained. The list of archive fields the refiner needs and does not have (at least `prompt_hash` and `hint_used` per candidate, `intervention_n` per hint) with the one-line `build.py` change per field written as a proposal, not applied.

## Verification

- `pytest tests/specfactory/` green including new tests.
- `costs.jsonl` rows under `px12-vision-probe` sum to the reported cost.
- No vision model left in `ollama list` unless Westley kept it; `nvidia-smi` shows the worker's usual footprint after the window.
- Finishing report for Westley: per PX the pass/fail against the numbers, the viable vision route or that none exists, the archive fields missing, no recommendations.
