# Harness defect investigation (2026-09-17)

## Why this exists

Agora's local ladder (qwen3-coder:30b, then gpt-oss:20b at low and medium thinking) was failing ouroboros C cards, and a benchmark session on card `202b2-e05-faction-budget` concluded that the local models were not capable of the work. Westley asked for an investigation on the reasoning that comparing high-level harness configurations is pointless if a lower-level fault sinks all of them equally.

The reasoning was correct. The failures trace to spec and harness defects, not to model capability. Nothing in this document has been fixed; every item is a finding that awaits a decision. `agora-dispatcher.service` is stopped.

Method: Claude (main session) formed hypotheses and checked the decisive claims against source. Sonnet sub-agents gathered the evidence. Raw evidence sits in `evidence/` beside this file.

## Headline

1. Card 202b2 cannot pass. A correct implementation fails its acceptance test because `csrc/sim.c` ignores the `OM_FEAT_DRIFT` switch that the test fixtures rely on. Around 30 test files and most parked cards share the exposure.
2. The C-card protocol makes the worker re-emit the whole `.c` file inside a hardcoded 16,384-token context, of which the prompt takes about 14,400 to 15,000. The reply does not fit. gpt-oss is cut off every time on this card; a control run at 32,768 completes cleanly.
3. The gpt-oss rungs have produced one pass in 885 C-card attempts. The ladder was only ever validated on small Python function-splice cards.
4. The harness gives wrong feedback in several ways, and nothing in the spec factory proves that a card is passable before it is queued.

## Defects

Severity: **blocker** makes success impossible, **major** depresses every configuration, **minor** adds noise or waste.

### Spec and simulation defects (ouroboros repo)

**D1. Card 202b2 is impassable (blocker).**
A hand-written reference body for `om_faction_step_budget`, matching the brief exactly, fails `tests/csim/test_E05_S033_territory_pays_or_costs.py::test_R_033_01_budget_66_8_40_8` with `assert 2.4449064893841093 == 2.275`. The test sets region economies to 66, 40 and 9 and calls `isolate_agents()` (`tests/csim/conftest.py:597`), which switches `OM_FEAT_DRIFT` off. `csrc/sim.c::om_world_step` gates only `OM_FEAT_FACTIONS`, `OM_FEAT_FRICTION` and `OM_FEAT_ADMIN_REVOLTS` (lines 282 to 294). The drift loop (lines 111 to 279) runs unconditionally, so the economies become 65.9154, 43.4404 and 12.4404 before the budget step reads them. `sim.c` is outside the card's `allowed_files`. The card consumed 131 attempts across 15 runs. Of 47 candidate functions that could be extracted from the replies, 0 pass when spliced in at function level; 43 fail on the assertion (most on exactly the drifted value 2.4449, meaning the function was right), and 4 fail to compile (`fmax` without `<math.h>`).
Evidence: `evidence/splice/e1_reference_body.diff`, `evidence/splice/e4_results.json`, `evidence/splice/extract_and_test.py`.

**D2. Nobody owns drift gating (blocker, wide blast radius).**
The feature switches arrived in commit `94e5e9d` (2026-09-14) with a header contract that says switching a feature off skips its step entirely. The drift loop was hand-written in `9bc9b9e` (2026-09-16) with no gate. Commits `eccf6fa` and `4d16fc9` gated the three newer steps because `docs/northstar/plans/archive/specs/PLAN_CARD_DECOMPOSITION.md:115-117` told them to add hooks "after drift loop". `OM_FEAT_DRIFT` has never appeared in any revision of `sim.c`. No epic rule, card brief, Agora rules file or doc assigns drift gating to anyone, and no test would fail because of its absence. A scratch-build probe confirms the behavior directly: with DRIFT set to 0, one step moves military 50 to 50.955, economy 50 to 54.057, tension 50 to 50.768 and population 50 to 50.412. Thirty test files call `isolate_agents()` before stepping and then assert on drifting fields or values derived from them (E-03 S-023 and S-024, all of E-05 S-032 to S-041, all of E-06, all of E-07, eight E-05 controls). Fourteen more use `isolate_events()`. Nearly every parked card (203 to 206, 208 to 210, 211 to 215, 220 to 235) targets those files. Cards 202a1 to 202a4 and 202b1 passed only because their tests read getters and territory counts, which do not drift.
Evidence: `evidence/drift_trace/proxy_check.py`.

**D3. Feature defaults contradict the documents (major).**
The header comment and `docs/bible/algorithms.md:11` say the feature flags are all true at launch. `om_world_new` allocates with `calloc` and never writes `features[]`, so every feature defaults to off.

**D4. Tick order contradicts the retained sequence, and four steps are missing (major).**
`docs/bible/algorithms.md` lists factions as step 3, friction and admin revolts as step 4, and passive drift as step 5. `sim.c` runs drift first and the gated faction block after it. Even with a drift gate added, non-isolated play would feed post-drift economy into the budget step, the reverse of `tick.py`, which bears on the bit-for-bit determinism contract. Events (steps 1 and 2), diplomacy, technology and lifecycle are not called from `om_world_step` at all, so the E-04 tests fail for that reason as well.

**D5. The spec factory has no satisfiability check, and the test audit cannot replace one (major, process).**
The factory's `red_check` proves that a test fails on the stub. Nothing proves that a reference implementation passes. The worker-model experiments of 2026-09-05 had a `--verify` step that proved every reference body green and every skeleton red; it was not carried into the factory. The Sonnet audit marked the S-033 test file "clean" (`docs/northstar/spec_factory.md:80`), and the file is in fact correct: the defect lies between a shared fixture and `sim.c`, which a static review of the test file cannot see. The audited-versus-unaudited experiment cannot be read while harness faults dominate the outcome metrics: 16 of 22 C cards have zero passes in either arm.

### Harness defects (Agora repo)

**D6. The whole-file reply does not fit in the context window (blocker for gpt-oss on this card, major in general).**
`prompts/worker-build-c.md` requires the complete rewritten `.c` file in one block. `scripts/build.py:732` hardcodes `num_ctx=16384, num_predict=8192`. The reconstructed 202b2 worker prompt is 52,193 characters: header 38,091 (73 percent, included whole), whole file 6,361, extra context 2,771, scope line 2,403 for 128 symbols, system 1,414, instruction 994. Measured prompt size is 14,984 tokens for qwen3-coder and 14,403 for gpt-oss. The prompt itself is not truncated (the count is identical at 16,384 and 32,768, and the Ollama log has no truncation warning for this card). What is left for output is 1,400 to 1,981 tokens, while the finished file needs about 2,141.

| Test | think | num_ctx | done_reason | prompt + output tokens | fence closed |
|---|---|---|---|---|---|
| T1 | low | 16384 | length | 14403 + 1981 = 16384 | no |
| T2 | medium | 16384 | length | 14403 + 1981 = 16384 | no |
| T3 | low | 16384 | length | 14403 + 1981 = 16384 | no |
| T4 | low | 32768 | stop | 14403 + 2141 = 16544 | yes |

In T1 and T3 the reply is a correct-looking file cut off inside `om_faction_step_budget`, which sits last in the file, so truncation always removes the part that matters. In T2 the thinking text consumed part of the same budget and the content never reached the target function. Generation is capped by `num_ctx` minus the prompt, not by `num_predict`. For qwen3-coder the server runs with `--context-shift` and `--keep 4`: when the window fills it discards 8,189 tokens and keeps 4, which removes the system prompt, header, scope and instruction in the middle of generation. The log shows 259 such shifts at this context size over seven days, and two hard prompt truncations on 2026-09-15 (`limit=8194 prompt=16440`). The available room shrinks as `faction.c` grows card by card, which matches 202a1 to 202a4 passing on the first attempt at smaller file sizes. The 30B sizing contract in `PLAN.md` bounds the size of the change, but the harness cost scales with the size of the file and the header.
Context size is a setting, not a memory limit on this machine. The KV cache for qwen3-coder costs about 96 KB per token, so 32k adds about 3 GB and 64k about 6 GB.
Evidence: `evidence/tokens/` (component report, raw responses T1 to T4 and both qwen measurements, log excerpts).

**D7. Reading the prompt dominates attempt time (major).**
qwen3-coder evaluates the prompt at about 34 tokens per second in production logs, so 15,000 tokens cost about seven and a half minutes before the first output token. That accounts for the 540 to 980 second attempts that returned about 730 bytes. gpt-oss reads the same prompt in 18 seconds. Build plus acceptance test takes 0.2 to 1.1 seconds. Three quarters of what is being read is the full header, of which the card needs a few lines.

**D8. `merge_reply_c` accepts a partial file and the model is told the wrong thing (major).**
The merge checks only that the target symbol is defined. When a model returns the includes plus the one function (37 cases, among them qwen's first attempt in five consecutive 202b2 runs), the harness overwrites the whole file with it. The library still links, then fails at `dlopen` with `undefined symbol: om_world_feature`, and the attempt is recorded as `tests`. The model's next prompt carries test output rather than the real cause.

**D9. The gpt-oss rungs do not function in C whole-file mode (major).**
Across 1,352 attempts on 22 C cards, gpt-oss made 885 attempts and passed once. 668 (75 percent) produced no usable block: 269 were cut off with an unclosed fence (explained by D6) and 398 contained no code fence at all, only narration. gpt-oss also labels its block ```` ```c ```` rather than ```` ```snippet ````; the fallback parser only counts a block when it sees the closing fence, so every truncated reply is a guaranteed `snippet-format` reject. `ollama_client.chat` returns `message.content` only and discards `message.thinking` without logging it. The ladder was validated on 2026-09-05 (`~/Projects/agora/experiments/2026-09-05-worker-model/`) for Python cards with function-level splicing and a small module as context, where gpt-oss was green nearly everywhere. C whole-file mode was added between 2026-09-10 and 2026-09-14 and never re-benchmarked. qwen3-coder by contrast returns a correctly fenced whole file 86 percent of the time, and all six of its passes came on attempt 1.
Evidence: `evidence/forensics/c_replies.csv` (one row per attempt), `evidence/forensics/analyze_c_replies.py`.

**D10. Unstable briefs and unenforced goal text (minor to major).**
DeepSeek regenerates the brief on every run. Across 19 runs of 202b2, `expected_lines` took the values 12, 20, 24, 260, 300, 320 and 340 for the same twelve-line function, and the phrases "from 0 to OM_MAX_FACTIONS - 1" and "all other functions" each appeared in about half the runs. The first phrase led models to write `f < OM_MAX_FACTIONS - 1`, an off-by-one that this test happens not to detect. "Keep all other functions unchanged" sits awkwardly beside a protocol that demands the whole file and may be what prompts function-only replies (D8). The harness runs only `checks[0]`; the "earlier suites stay green" clause in card goals is never executed. `mess()` never fired on any C card.

### Environment findings

**E1.** The `win11edu` libvirt VM holds 16.6 GB and keeps running after its viewer window is closed; `virsh -c qemu:///session shutdown win11edu` stops it. It ran alongside every Agora run on 2026-09-17, filling RAM to 25 of 30 GB and swap to 8 of 8 GB. Treat that day's wall times with suspicion, though the qwen prompt-reading speed measured that day (30 to 34 tokens per second) matches production logs from other days.
**E2.** `agora-dispatcher.service` is a systemd user unit with `Restart=always`. Killing its process restarts it within 30 seconds; only `systemctl --user stop` holds.
**E3.** The uncommitted change to `csrc/faction.c` on ouroboros `main` is a hand-written, correct budget body from another session. It fails the acceptance test for the reason in D1. It was left untouched.

## Hypotheses that were tested and rejected

- The prompt is truncated at 16k and the format rules are lost before generation. Rejected for 202b2: the token count is identical at both context sizes and there are no warnings. It does occur rarely on larger prompts (two events in seven days).
- gpt-oss writes its code into the thinking channel and the client throws it away. Rejected for 202b2: the thinking text was 19 to 96 characters at low and 2,087 at medium, and the code was in `content`. What is true is that thinking shares the output budget (T2).
- Slow attempts are test or build time. Rejected: 0.2 to 1.1 seconds.
- A sub-agent reported prompt-injection text inside the 202b2 card file. Checked and false; the card is clean.

## Open questions

- O1. What explains the 398 gpt-oss replies with narration and no code, mostly on cards other than 202b2? Candidates are loss of the instructions after a context shift, or code drafted in the thinking channel on cards with more room. Thinking text has never been logged, so existing data cannot settle it.
- O2. How many of the 30 exposed test files are impassable today? A sweep with reference bodies would answer it; none has been run.
- O3. Were 201a and 201b (0 passes in 654 attempts) also impassable, or victims of D6 to D9? Not examined.
- O4. qwen3-coder's prompt reading speed free of any VM pressure has not been measured in isolation.

## Decisions this hands to Westley

1. The ouroboros side: who owns the drift gate (an E-02 rule with a test and a positive control seems the natural home), the tick order in D4, and the defaults in D3. `sim.c` equations and order bear on the determinism contract.
2. Whether Stage 5 gains a green check (reference body passes) beside `red_check`, and what happens to the audit experiment.
3. The reply protocol for C cards: whole file against function-level splice (which the Python path already uses), and how much of the header a worker sees.
4. `num_ctx`, and whether the gpt-oss rungs stay, change or go, decided by a re-benchmark in C mode once items 1 and 3 are settled.
5. Only after those: the high-level harness comparison that started this.
