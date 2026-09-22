# Adversarial review: The Factory + fast-track proposal

Read: PLAN.md §Factory (lines 96-188), B8 traces, DECISIONS.md (all rounds), SCORECARD + PX-16/17/18/08/06/19, A9, real harness (`agora/scripts/next.py`, `build.py`, `ollama_client.py`, `agy_client.py`, systemd unit), ouroboros `scripts/specfactory/*`, `csrc/`, `Makefile`, `tests/csim/conftest.py`. Measured: full `tests/csim` suite 33.65 s (563 failed / 108 passed), `make` 1.24 s, host 16 cores / 30 GB RAM / 12 GB VRAM, `clang` absent, dispatcher currently `active` and `driver: idle` since 205a escalated 2026-09-20 16:22.

---

## 1. Contradictions (PLAN vs PLAN, PLAN vs DECISIONS, design vs code)

**F-1-1: Three uncoordinated hint/plateau mechanisms; design's K=3 plateau layered on a K=2 break already in code.**
`build.py:1033-1034` breaks a rung on two consecutive identical failing sets (`if prev_ids is not None and ids_set == prev_ids: break`) then calls `_intervene` (up to `MAX_INTERVENTIONS=3`, `build.py:59`). `build.py:561-562` adds cross-run advisor on runs 3-9. PLAN:141 adds "plateau (three distinct candidates...) forces an escalator diagnosis call". PX-08 showed K=2 has 4 false stops; the live code is effectively K=2. Nothing says which survives, or how per-card call counts sum.
Severity: serious. Fix: one plateau policy, one hint budget per card, delete the other two.

**F-1-2: "Red stops the chain" vs "escalated card never idles the GPU".**
PLAN:112 gate result: "Red stops the chain". PLAN:153: "an escalated card never idles the GPU: the next independent card runs". `next.py:196-199` docstring: GATE-FAILED terminal "simply stops the chain there... resumes only once a human renames the card". DECISIONS Q7: gate red = escalation. Unspecified whether a red epic gate blocks dependents only or all.
Severity: serious. Fix: state "red gate blocks its story/epic subtree; siblings continue".

**F-1-3: CLAUDE.md test fence contradicts the escalator role; design breaks its own stale-doc tripwire.**
CLAUDE.md: "Tests live in fenced paths Agora cannot edit"; "Sub-agents... may not... edit any test threshold, or decide what is tested." PLAN:123: escalator (an Agora module per fast-track Wave 2) "may fix a test or a mission"; PX-06 consequence 2: survivor set → "test-defect, escalator-owned" i.e. escalator authors assertions. DECISIONS C6: "the test fence therefore excludes the worker, not the escalator". CLAUDE.md never rewritten.
Severity: serious. Fix: rewrite CLAUDE.md fence paragraph in the same PR as Wave 2.

**F-1-4: DECISIONS R10.3 stale against PX-18.**
R10.3 (DECISIONS:186): dead control → "the escalator redesigns the fixture (PX-13 already computes the distinguishing value... military 15.0 for R7l)". PX-18: R7l failed 3/3; consequence 2 routes R7l class to Claude. Both rows stand in the same file.
Severity: minor. Fix: delete R10.3 sentence, point to PX-18 split.

**F-1-5: Candidate fence in PLAN is function-level; in code it is file-level plus hoisting.**
PLAN:110 "Only the named function(s) in one file change". `build.py:961` fence = `changed != [snippet_file]`. `merge_reply_c:272-298` inserts any new `#include` (both `<>` and `""` forms, `_C_INCLUDE_LINE`) and hoists every new top-level definition in the block. Worker prompt says "do not add new headers beyond the C standard library" (`prompts/worker-build-c.md`) but nothing enforces it.
Severity: serious. Fix: reject `"..."` includes and any hoisted non-`static` symbol; diff the function span, not the file.

**F-1-6: "Cap doesn't stop" is false; humans reset it. PX-16's S1 gain rests on that error.**
`next.py:365` cap holds. `runs/` has 10 live `204b1-*` dirs + 20 `_archived-prefix-204b1-*` = three batches of 10; R7h/R7l text: "archived so the card gets a fair, uncapped attempt count", "fresh attempt budget given". A9 #3 and PLAN:159 call it "to be verified as a harness bug". PX-16:40 "S1's building drop (-215.4 min) is entirely the cap" — it is entirely human re-queues after upstream fixes, which under the factory return as repair cards with fresh budgets.
Severity: serious. Fix: strike the harness-bug claim; re-run S1 with re-queues modelled as repair cards.

**F-1-7: Whole-suite cost stated as "seconds", scope ambiguous (per candidate vs per DONE).**
PLAN:152 "per candidate, the whole headless suite (seconds)"; PLAN:141 "whole-suite regression after every DONE". Measured 33.65 s with 563 tests failing fast; passing tests run 5,000-tick scenarios. Per-candidate ×10-30 candidates/card = 6-17 min CPU per card, not seconds.
Severity: minor. Fix: say "per passing candidate before merge", quote the measured number.

**F-1-8: Verifier and vision judge are single-route agy; only the escalator became a seat.**
PLAN:124 "Verifier and refiner: Gemini via agy"; PLAN:147 "judged by Gemini vision via agy". PX-17 §Model note: every agy group empty ~45 h, shared across two accounts. Seat/fallback added for escalator only (PLAN:123).
Severity: serious. Fix: same seat abstraction for verifier and judge, or QA declares itself dark.

**F-1-9: Test bodies are written by agy (Gemini), contradicting "Claude designs and tests".**
PLAN:108 "Skeletons by script, bodies by agy, Claude owns". CLAUDE.md north star: Claude writes "the fenced test suite". DECISIONS B2: "Tests stay unaudited". So Gemini writes spec-tests, Gemini/DeepSeek escalator edits them, nobody audits.
Severity: serious. Fix: state the real author; if agy, require the red-check plus a Claude review row per file.

**F-1-10: "52 min per shipped card is the expectation" contradicts A9's own conclusion and hides that every shipped card needed a human fix.**
A9:60 "52.4 min/card"; A9:99-101 "~110 min/card average — still 2-4x Westley's expectation". A9 table col "Recut or upstream fix needed?" = Yes for all five DONE cards. PLAN:153 quotes 52 as expectation and uses it for the runway.
Severity: serious. Fix: baseline = 110 min and "0 of 5 without human intervention".

---

## 2. Claims resting on prototypes that did not test them

**F-2-1: Escalator "proven" on `deepseek-v4-flash`, one shot each, no fallback; PLAN names Gemini first.**
PX-17 Limits: "One model... one run each (not the plan's 3-attempts-per-case-per-model with a second model on failure)". R8 (the multi-function case) "unknown, not confirmed-impossible". Canned positive control is R7a (`#include <math.h>`) — `merge_reply_c:272-280` already hoists includes, so the control exercises no function-body fix.
Severity: serious. Fix: canned control = R7d (byte-identical body fix); re-run PX-17 on Gemini when quota returns.

**F-2-2: PX-16's 4-6 h number needs autonomous fixes of a class the escalator is defined not to do.**
PX-16:42-49: S1/S2 residual idle = "204a1 recut" and "206b recut for 204b2"; S3 removes them assuming a fix lands in 15-60 min. Re-cuts are card authoring (who owns which symbol), and PX-17 consequence 3 routes anything beyond one function to a repair card (transcriber/Claude). S2 "inherits PX-08's false stops... not re-measured... an upper bound" (PX-16:40).
Severity: blocker for the throughput claim. Fix: quote S1 (11h30) as the evidenced number; S3 is a hypothesis.

**F-2-3: PX-16 S0 "validation" is tautological.**
PX-16:38: S0 matches A9 "exactly — the simulator is reading the same real data A9 mined". Same input, same sum.
Severity: minor. Fix: validate on a held-out window.

**F-2-4: Shadow fixture listed as a gate, never proven, and needs an oracle the rules forbid.**
PLAN:141 lists "shadow fixture". PX-06 E3/E4 "inconclusive... not tested". Perturbing a fixture needs recomputed expected values = a reference implementation, which Q4 forbids Sonnet from writing.
Severity: serious. Fix: drop from gate list until a card is green at HEAD and a perturbation oracle exists.

**F-2-5: Cross-compiler determinism gate untested and impossible today.**
D10 "gcc vs clang... on every C card". `which clang` → nothing. PX-05 ran one binary twice in one process (same compiler, same libm). No PX covers compiler or platform variance.
Severity: serious. Fix: install clang, add a PX with a planted `-ffp-contract` difference, before D10 goes in Wave 3.

**F-2-6: Control liveness gate has no controls to gate for E-06+.**
PX-15: 119 controls, 92 placeholder skeletons. "Story's own controls must flip" (PLAN:141) means 92 authoring tasks before those stories' cards can reach DoD; PENDING covers unbuilt features, not unwritten controls.
Severity: serious. Fix: count placeholder controls as day-side backlog in the runway.

**F-2-7: QA architecture cites PX-02/PX-03 as proof; real Godot input delivery never passed.**
SCORECARD row D (2026-09-11): "this row's 'pass' verdict is retracted"; row G: "Still needs a G probe run on the GPU virtual screen to reach pass". PX-02/03 ran on the toy scene under Xvfb (software GL). Forward+ needs Vulkan; no run on the RTX display.
Severity: serious (deferred to P1 by fast-track, but PLAN:150 states precheck as proven guard). Fix: mark QA claims "toy-scene only".

**F-2-8: Prefetch "gate" solves a 2-second problem.**
PX-19 §2: CPU prep 2.227 s; §1: median back-to-back gap 62 s; `agora-dispatcher.service` `sleep 60` floor; `keep_alive` "never sent". Wave 3's prefetch item saves ~2 s per card.
Severity: minor. Fix: drop prefetch; ship `keep_alive` and cut the 60 s sleep to event-driven.

---

## 3. Hardware and scheduling

**F-3-1: CPU-slot cost per C card is 4-6 min without memcheck, unbounded with it, and contends with CPU-offloaded inference.**
Sum per card: mutation 50-95 s (PX-06), whole suite 34 s now (measured; grows as tests go green), UBSan build+suite ≥35 s, ASan build+suite ≥70 s (2× slowdown), gcc -O0 + clang -O2 builds + checksum sweeps ~10 s, "sampled memcheck" = valgrind on CPython+ctypes at 20-50× → 11-28 min if it runs the suite. Model is 18 GB on 12 GB VRAM (`ollama show`: 30.5B Q4_K_M) so ~6-7 GB of layers run on the same 16 cores the CPU slot uses. No PX measured contention.
Severity: serious. Fix: define memcheck sampling (n tests, nightly only); measure tok/s with and without a concurrent pytest.

**F-3-2: RAM budget on Tue/Thu does not close.**
`free -g`: 30 GB total. Resident model (`keep_alive -1`, PLAN:153) pins ~7 GB RAM + 11 GB VRAM. `win11edu` VM 16.6 GB. Plus pytest/valgrind. 7+16.6+OS > 30 on Windows-gate days.
Severity: serious. Fix: unload the model for the VM window; or gate Windows on a separate box.

**F-3-3: Dispatcher priority starves builds once any QA campaign is active.**
`next.py:617-641`: director → QA → build. `QA_INTERVAL_MIN = 1` (`next.py:34`). PLAN:151 activates a per-epic QA campaign when an epic gate is DONE; from then on every tick is a QA session until BUDGET-HALT or convergence (`next.py:296-346`). Also Godot Forward+ needs VRAM the resident model holds.
Severity: serious. Fix: explicit slot arbitration (QA off-peak, builds otherwise; unload model before a Godot session).

**F-3-4: Windows gate per epic closes only Tue/Thu, and the first Windows build fails on GCC-isms.**
D2: "an epic gate cannot close without a passing Windows run". PLAN:151 per-epic QA triggers on gate DONE → up to 5-day latency. `csrc/region.c:158` `__attribute__((weak))`; `Makefile:17-18` `-fexcess-precision=standard -msse2 -mfpmath=sse` (GCC/x86 only). No VM toolchain, build script, or ctypes-on-Windows conftest exists.
Severity: serious. Fix: separate "epic gate (Linux)" from "platform gate (weekly)"; write the MSVC/clang-cl build first.

**F-3-5: Prompt size exceeds `num_ctx` on larger files; overflow is a "crash" candidate that burns budget.**
`build.py:887` `num_ctx=16384`; `ollama_client.py:35-36` `shift/truncate False` → HTTP 400 → `build.py:889-893` reason `crash` (not HARNESS-ERROR). Prompt = whole skeleton + header/slice + `om_internal.h` + brief + previous[:1200] + hint. `resolve.c` 23,981 B, `ouroboros_sim.h` 38,734 B; 166/169 parked cards have no `## Header slice` → full header (`build.py:790-794`) → ~18k tokens for a resolve.c card. Grows with every merge into the file. "Measured prompts" (PLAN:184) has no tokenizer (PX-19 §2: chars/4).
Severity: serious. Fix: slice every card at prep (0.077 s per PX-19); pre-flight token count via `/api/tokenize`; classify overflow as HARNESS-ERROR.

**F-3-6: "Next attempt within one tick" = 60 s sleep + 47 s reload.**
`agora-dispatcher.service` `sleep 60`; PX-19 §3 median load 47.1 s (n=2); `keep_alive` absent from every payload. One dispatcher unit per tick.
Severity: minor. Fix: send `keep_alive: -1`; event-driven loop.

---

## 4. Reward hacking and gate holes (30B implementer)

**F-4-1: Fence admits arbitrary `#include "path"` and hoisted globals; reference solutions sit in-repo.**
`_C_INCLUDE_LINE` (`build.py:222`) matches `"..."`; `merge_reply_c:274-280` inserts them; file-level fence (`build.py:961`) sees only `csrc/x.c`. `tests/csim/references/203a1-...c` etc. exist (DECISIONS:9). A hoisted `static` helper with `__attribute__((constructor))` can mutate world state before any test. Mutation on the include line "kills" (build breaks) → passes.
Severity: serious. Fix: reject non-`<std>` includes and attributes; span-diff fence.

**F-4-2: Worker owns the correct branch and the `OM_BUG_*` injection branch in the same function; liveness is satisfiable by any flip.**
203f (DECISIONS R6) "adds the two inject branches"; 208+ "spawn fault branches"; control liveness (PLAN:141, R10) = outcome differs clean vs injected. Nothing checks the injected branch models the named bug. `if (w->inject == X) return 0;` makes every control LIVE.
Severity: serious. Fix: injection branches authored with the control (Claude), never by the card that implements the rule; or liveness requires the injected failure to match a declared expected wrong value.

**F-4-3: Escalator test-fix gate cannot see a test made vacuous by a fixture number.**
PLAN:123 gate = assertions preserved, red at stub, PX-13 detectors clear. R7l shows both clamp orders give 31.3 while every assertion survives; PX-13 detectors are convention-bound (PX-13 Limits, PX-18 Limits). Mutation runs on the candidate's code diff (PLAN:141), never on a test edit. `red_at_stub` undefined for a test over merged code (no stub; PX-18 consequence 6).
Severity: serious. Fix: after any test edit, re-run diff-scoped mutation of the function under test against the edited test; require kill.

**F-4-4: Sizing cap is on a self-declared number.**
`cascade_types.py:205-212` checks `expected_lines` from the card; `mess()` (`build.py:204-205`) trips at 3×. R6 set `expected_lines: 60` for a 150-line function. 203b1 (170 lines) merged.
Severity: minor. Fix: cap on measured body lines of the accepted candidate.

**F-4-5: Stub detection is `\bSTUB\b` in the body.**
`card_lint.py:85-86`. Merged body that keeps the word in a comment stays "stub" → dependents never release, no alarm (head is not parked, it is DONE). Removing the word with a wrong body releases them (R7g shape).
Severity: serious. Fix: stub = explicit marker macro removed by the splice; DONE flips ownership in the graph, not text.

**F-4-6: Mutation gate blocks on equivalent mutants and hands assertion-writing to the escalator.**
PX-06 E2: 38/40 survivors after the fix, mostly comment/no-op mutants; equivalence undecidable. PX-06 consequence 2: survivor set → test-defect for escalator (= deciding what is tested). No positive control for an "equivalent" verdict.
Severity: serious. Fix: survivor → Claude's ledger; per-card allowlist of equivalent lines signed by Claude.

**F-4-7: "Whole suite no worse" over 563 failing tests is blind to how failing tests fail.**
Measured HEAD: 563 failed / 108 passed. A parent patch or candidate that changes a red test's failure mode is invisible; R7g's wrong `om_step_telegraphs` passed "no regression" (DECISIONS R7g).
Severity: serious. Fix: regression compares failing-id sets and first assertion line per test, not counts.

**F-4-8: Merge race: candidate tested at `base_sha`, cherry-picked onto a main that moved.**
`build.py:691-699` worktree at run start; `build.py:630-641` cherry-pick + `git push` at finish. PLAN:153 runs escalator diagnosis/patches concurrently in a scratch worktree. The merged combination is never tested before push.
Severity: serious. Fix: rebase worktree onto main and re-run suite before cherry-pick; serialize merges.

---

## 5. Escalator seat

**F-5-1: All-routes-down is not a harness condition; it burns the card's budget and pages Westley. Happened 2026-09-20.**
`runs/205a-*-1514..1622`: 10 runs in 68 min, 1-2 candidates each, log "HARNESS-ERROR: intervene failed (network)" yet outcome INCOMPLETE (`build.py:1059-1061` breaks, falls to INCOMPLETE at :1111). `next.py:365-367` counts them → `escalate.escalate` → ntfy. `escalations/205a-e05-collision-lottery.md` exists. Under escalate-and-continue every buildable card repeats this: chain fully parked in ~N hours. PLAN:123 says "falls through on quota or timeout", nothing for "all fell through".
Severity: blocker. Fix: seat-empty → HARNESS-ERROR class that pauses the GPU slot, retries hourly, alarms once.

**F-5-2: Wrong parent patch merges; nothing bounds patches per function.**
Gate = named test green + "whole suite no worse" (C4, PLAN:141). No mutation, no control on parent patches. R7g→R7j is the human precedent: a "fix" implemented another card's scope and was partly reverted. Two escalator diagnoses can oscillate on one function forever.
Severity: serious. Fix: max one parent patch per function per epic; second diagnosis → repair card with Claude review.

**F-5-3: Repair-card loop writes machine-authored spec.**
PLAN:109 repair card: "the finding becomes a fenced regression test... generated by the transcriber". Contradicts PLAN:108 "Claude owns". Verifier is Gemini reading spec, not bible (PLAN:113); a `bug` that is really `false_positive` becomes a fenced test asserting wrong behavior → worker implements it → story test conflicts → `contradiction` → Q- → Westley. Fingerprint dedupe after repair unspecified.
Severity: serious. Fix: generated regression test lands as `proposed` until Claude's red-check signs it.

**F-5-4: Cost model absent for the Claude fallback.**
Per card: up to 10 runs × (3 intervene + 1 advisor) + plateau + parent-patch retries. ~12k-token prompts (PX-19 §2) on Sonnet ≈ $0.05-0.20/call → $2-8/card when agy and DeepSeek are both down. Caps exist per model (PLAN:123); "all caps hit" = F-5-1.
Severity: minor. Fix: daily seat cap + the F-5-1 pause.

**F-5-5: "A Claude model" via agy is not an independent route.**
`agy_client.py:31` `AGY_MODEL` default `claude-sonnet-4-6` via agy; PX-17: Claude/GPT group empty on the same shared clock. Only direct Anthropic API is independent.
Severity: minor. Fix: name the transport per seat entry.

---

## 6. Routing rule: what reaches Westley anyway / gets misrouted

**F-6-1: Eleven non-design paths reach Westley today or under the design.**
(a) `MAX_HARNESS_RUNS=4` → `escalate` + ntfy (`next.py:364-368`): Ollama down, missing skeleton (142 cards, F-10-1), worktree add failure; (b) seat empty (F-5-1); (c) idle-with-parked-head alarm "then to Westley" (PLAN:153); (d) runway <24 h — true at restart (F-9-4); (e) `held` vision claims (PLAN:147); (f) GATE-FAILED "a human decides which one" (`build.py:734-735`); (g) auto-merge conflict "cherry-pick by hand" (`build.py:645-652`); (h) SPEC-INVALID terminal; (i) every escalator test edit at epic review (PLAN:123); (j) hand-implement sign-off (PLAN:141); (k) refiner proposals (PLAN:114).
Severity: serious. Fix: publish the real routing table; give (a),(b),(f),(g) machine owners.

**F-6-2: Misrouted away: real bugs filed as `bug` loop in the escalator; false positives delete missions.**
`contradiction` needs both cited entries green (PLAN:113), so a shared-code bug where both fail → `bug` → parent patch loop (F-5-2). `false_positive` → escalator "fixes the harness or mission" (C6) with no second oracle — a real defect's mission gets edited away. R7e/C3 precedent: what was ruled "test-authoring" (R7f) later became a design ruling (C3).
Severity: serious. Fix: `false_positive` requires a replay bundle where the deterministic oracle disagrees with the verdict; else `held`.

---

## 7. Open-endedness and the second project

**F-7-1: The scheduler's graph derivation is C/Ouroboros-specific and cross-repo-wired.**
`tick_closure.py:54` `ORCHESTRATORS = {"om_world_step"}`, `:155` `"sim.c"`; `chain_sim.py:57` `AGORA = Path("/home/westopoli/Projects/agora")`, `:396` loads `next.py` by file path; `card_lint.py:37` hard `DEFAULT_QUEUE`; `control_liveness.py:88-89` reads `OM_BUG_*/OMBug.*`. Wave 1 makes `chain_sim` the release rule inside `next.py` → circular. Web app: no stubs, no orchestrator → empty edge set → every card eligible at once = the "overnight false-DONE incident" `next.py:54-61` was written to prevent.
Severity: serious. Fix: profile declares `dependency_source` (closure | explicit list); closure lives in a language-table entry.

**F-7-2: Escalator (agora) needs `card_slice.py` (ouroboros).**
PX-19 §2: "Neither exists in `~/Projects/agora/scripts/`". PLAN:123 puts the slice in the parent-patch prompt. Two-homes rule (PLAN:131-137).
Severity: minor. Fix: profile field `slice_command`.

**F-7-3: One dispatcher, no per-project arbitration, wrong cost attribution.**
`next.py:655-656` build campaign = `_first_active_campaign()` by filename regardless of project; QA of `salesmen` preempts ouroboros builds (F-3-3).
Severity: serious. Fix: per-project slot budget in the profile.

**F-7-4: Profile schema will be designed against Ouroboros before PX-11 runs.**
`projects/ouroboros/` = `README.md`, `qa.toml`, `rules/`. None of gate set, orchestrators, empty-chain list, detectors, personas, planted-bug catalog exists. Fast-track runs PX-11 "in parallel".
Severity: serious. Fix: PX-11 before Wave 1 freezes the schema.

**F-7-5: Gate switch-off covers absence, not presence.**
PLAN:134 "every gate on by default... switched off is named". A web project needs gates the list lacks (flake retry, migration reversibility). Vocabulary "tick-stage", "seed", "era pack", "pack entry count" in the generic gate list (PLAN:141,176).
Severity: minor. Fix: gates as pluggable classes listed by the profile, not a fixed set with off-switches.

---

## 8. Determinism

**F-8-1: `pow()` from libm at `csrc/sim.c:206` breaks the cross-platform contract on the first non-zero tension.**
`pow(1.0 - r->tension / 100.0, 0.3)`. `om_sin` polynomial exists (`sim.c:35-41`) precisely because libm differs; `pow` missed. glibc vs UCRT vs Apple libm are not bit-identical. Checksum hashes raw double bytes (`sim.c:376-384`) → one ulp flips it. Every Linux gate (gcc/clang, -O0/-O2) links the same glibc and cannot see it.
Severity: blocker for the contract. Fix: deterministic `om_pow` (exp/log polynomials) with a fenced bit-exact table test.

**F-8-2: Windows/macOS builds fail before any checksum runs.**
`region.c:158` `__attribute__((weak))` (no MSVC); `Makefile:17-18` GCC/x86 flags (`-msse2 -mfpmath=sse -fexcess-precision=standard`); arm64 macOS rejects `-msse2`. No second build system, not in any wave.
Severity: serious. Fix: CMake or a `build_msvc.bat` with `/fp:strict /arch:SSE2`, `#define OM_WEAK` per compiler.

**F-8-3: Alt-compiler / -O0 / sanitizer variants need fenced project files, not build.py.**
`conftest.py:36` hardcodes `make -s libouroboros.so libouroboros_dbg.so`; `Makefile:19` `CFLAGS :=` (environment does not override without `-e`); Makefile header: "Fenced (parent-owned)". Wave 3 puts these gates in `build.py`; Wave 4 does not touch Makefile/conftest.
Severity: serious. Fix: profile `build_variants = {det_o0, det_clang, ubsan, asan}` mapping to Makefile targets Claude adds in Wave 4.

**F-8-4: ASan/memcheck through CPython need suppressions and a definition of "sampled".**
LD_PRELOAD libasan into python: needs `ASAN_OPTIONS=detect_leaks=0`, link-order check; valgrind on CPython needs the python suppressions file and is 20-50×. "sampled memcheck" (PLAN:141) undefined.
Severity: minor. Fix: nightly memcheck on N named tests; ASan with a fixed `ASAN_OPTIONS` in the profile.

**F-8-5: ctypes struct mirrors are the second platform contract nobody gates.**
`conftest.py` "mirrors every struct and enum in csrc/ouroboros_sim.h exactly"; no `#pragma pack`; MSVC layout/alignment can differ. The Windows gate as designed (D2) compares checksums only; a mirror mismatch reads garbage and reports as a determinism "bug" with no owner card.
Severity: serious. Fix: `om_abi_layout_check()` exporting `sizeof/offsetof` table; Windows gate asserts it first.

---

## 9. The fast-track itself

**F-9-1: The dispatcher executes `next.py`/`build.py` straight from the working tree; a live merge of Wave 1 crash-loops.**
`agora-dispatcher.service`: `ExecStart ... /home/westopoli/Projects/agora/scripts/next.py`, `Restart=always`, loop every 60 s. Proposal pauses only "during the build.py wave". Wave 1 (`next.py`) reading profile chain data Wave 4 has not produced → exception every tick.
Severity: serious. Fix: stop the unit for all four waves; add a `DEPLOY_SHA` file the loop checks before running.

**F-9-2: Wave order inverts dependencies.**
Wave 1 scheduler = closure over stubs from `tick_closure`/`card_lint` (ouroboros, Wave 4) and a non-cyclic E-04 cut (Wave 4 re-cut; PX-16: 208a1/208a2/208b1/209c cyclic, `om_step_resolve` and `om_tick_collisions` double-owned). Cycle = lint FAIL at chain-build → nothing past E-05 schedules until Wave 4 lands.
Severity: serious. Fix: Wave 4 (re-cut, lint) first; Wave 1 second.

**F-9-3: Verification controls are weak or unrunnable on the real chain.**
R7a as canned escalator case = include hoist (F-2-1). "Parked head does not idle the GPU" needs two independent eligible cards; after 205a/205b/206a/206b the next independent set is cyclic E-04 → control passes on a scratch chain and the real chain re-idles immediately. "Known-bad merge reverted" replays 203b1 (Q1) — already covered by predecessor checks (`build.py:968-995`); does not exercise the whole-suite path unless the planted break is outside the shared file.
Severity: serious. Fix: R7d as canned; plant the bad merge in a different file than its victim test's card.

**F-9-4: A 24-hour watch cannot see what the design claims; runway is ≤22 cards.**
142/164 parked build cards name a `snippet_file` absent from `csrc/` (12 of 18 target files missing; header has no `om_fog*`, `om_unit*`, `om_chronicle*`...). Buildable now: 205b, 206a, 206b + 9 E-04 (after re-cut) + 10 E-03 (`worldgen.c` missing) → ~13-22. At 52-110 min/card = 11-40 h. Watch observes the runway alarm and the empty-chain list, not the graph under load. Plateau false-stop rate needs ~70 runs (PX-08: 3 at K=3 over 74). Windows gate only Tue/Thu.
Severity: serious. Fix: watch = one full epic (E-04) + one Windows window; state pass criteria per gate.

**F-9-5: "Tests first" for the scheduler is possible but will miss the live-state shapes that actually broke it.**
100 test files in `agora/tests/`; `chain_sim` has synthetic fixtures. Real failures were state shapes: stale terminal markers re-escalating (R7g), `_archived-prefix-*` dirs, `.satisfied-by-*` tags (`build.py:540`), `204b1-...md-20260916-2027` stray dir, `git show` at another repo's HEAD (`chain_sim.py:600-604`).
Severity: minor. Fix: fixture corpus snapshotted from `runs/` and `queue/parked/` as-is.

**F-9-6: Running PX-10/PX-11/PX-12 in parallel breaks Principle 13 for the shapes Wave 1/3 freeze.**
PLAN:188 "A claim that fails its experiment changes the design, not the experiment." Wave 3 adds `kind: content` (PX-10 unrun); Wave 1 freezes profile chain/gate schema (PX-11 unrun); Wave 3 archive fields feed the refiner (PX-12 unrun).
Severity: serious. Fix: PX-10/11 before Waves 1/3; PX-12 may stay parallel.

**F-9-7: Wave 3 = seven features in one 1,286-line file with Sonnet leaves in worktrees.**
All land in `build.py:589-1113` (`_run`), one closure. Worktree isolation defers every conflict to the final fast-forward.
Severity: minor. Fix: split `_run` into gate modules first (safe-refactor leaf), then features.

**F-9-8: D1 (explicit feature set) in Wave 4 shifts the E-02 baseline the same cascade uses as fixture.**
`ouroboros_sim.h:103` signature change, every caller, conftest; R11: E-02 controls "may have been set against the faulted default"; R12 shows repairs silently kill mirrored controls. Wave 3's planted-control verification runs against a moving E-02.
Severity: serious. Fix: D1 as its own cascade with a full liveness re-sweep, before or after, not inside.

---

## 10. Everything else

**F-10-1: 142 of 164 parked build cards cannot run; escalate-and-continue turns that into 568 wasted units and 142 pages.**
Counted from `queue/parked/*.hold` vs `csrc/`. Each hits `build.py:776-782` "cannot read card file" → HARNESS-ERROR ×4 (`next.py:41`) → `escalate` + ntfy. Q9e already flagged "no client cards"; nobody flagged that the sim cards themselves have no skeletons.
Severity: blocker. Fix: card lint FAIL on missing `snippet_file`/undeclared symbol at chain-build; those cards are not "Tested stories".

**F-10-2: Day-side is the bottleneck; the GPU is not.**
92/119 placeholder controls (PX-15); E-06..E-17 tests exist, skeletons/headers do not; test bodies "by agy" (PLAN:108) on a quota that was empty 45 h; every shipped card needed a Claude fix (A9). PLAN:153's runway alarm will be permanently on.
Severity: serious. Fix: runway counts skeleton+header+slice+live-control readiness, not "Tested" status.

**F-10-3: Runway = Tested × 52 min overstates by ≥2×.**
F-1-10. Alarm arrives a day late by construction.
Severity: serious. Fix: use rolling measured wall per DONE including human-fix stretches.

**F-10-4: Empty-chain work list becomes the steady state and spends cloud budget nightly.**
With F-10-2, "empty graph" is normal. Explorer campaign + vision judge (agy) + refiner scoring run every night; only per-campaign BUDGET-HALT guards (`next.py:310`). Judge cap is "per campaign" (PLAN:147), not per day.
Severity: minor. Fix: daily cloud cap across the work list; explorer only when a new rung merged since last run.

**F-10-5: Stale docs the design still leans on.**
CLAUDE.md fence (F-1-3); DECISIONS "Still open" Stage 4/5 numbering unresolved; A9 "cap harness bug" (F-1-6); C5 open `project.godot` 4.7 vs 4.6.3; `qa.toml` references the old Python pipe (Q9d-2); R10.3 (F-1-4).
Severity: minor. Fix: one doc-tripwire PR before the cascade.

**F-10-6: Auto-merge pushes to origin, then design adds post-merge revert.**
`build.py:640` `git push` on every DONE. "Revert on any new failure" (PLAN:141) after push = red commit + revert visible on GitHub main. Cherry-pick runs in the project checkout that has 8 modified files right now (git status); it proceeds unless conflicting.
Severity: minor. Fix: whole-suite before cherry-pick; never push a commit the suite has not passed on main.

**F-10-7: Epic gates as specified go red for retired cards, not regressions.**
Q9a: epic gate = whole `tests/csim/test_E##_*.py`. E-05 has retired 204b1/207 and two confirmed-blocked tests (R8e: `R_038_01`, `garrison_before_damage`) → E-05 gate GATE-FAILED terminal → "a human decides" (`build.py:734`). Same for every epic with an open R8e/R8f decision.
Severity: serious. Fix: gate = union of DONE cards' acceptance + explicit xfail list owned by Claude.

---

## Ranked top ten

1. **F-5-1** seat-empty burns budgets and pages Westley; already happened (205a, 10 runs / 68 min).
2. **F-10-1** 142/164 chain cards have no skeleton; the "169-card runway" is ~20 cards.
3. **F-8-1** `pow()` at `sim.c:206` breaks byte-identity; no Linux gate can see it.
4. **F-2-2** the 4-6 h throughput number assumes autonomous re-cuts the escalator is defined not to do.
5. **F-1-6 / F-10-3** "cap doesn't stop" is false; 52 min/card is cherry-picked; PX-16 S1 and the runway metric inherit both.
6. **F-4-2** worker writes its own bug-injection branch; liveness proves nothing.
7. **F-4-3** escalator can vacuate a test while passing all three gate checks.
8. **F-9-2 / F-9-1** wave order inverted; live dispatcher executes half-landed code.
9. **F-3-5** prompts exceed `num_ctx` on big files; overflow burns attempts as "crash".
10. **F-7-1** graph derivation is C-only and cross-repo hardwired; second project degenerates to batch release.

## Counts

- Blocker: 4 (F-2-2, F-5-1, F-8-1, F-10-1)
- Serious: 43
- Minor: 17
- Total: 64