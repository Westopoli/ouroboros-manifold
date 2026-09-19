# A1 — Spec-to-Task Mechanization: Prior Art vs. the Factory

## 1. Representing one feature so tasks/tests/acceptance derive mechanically

**GitHub Spec Kit** (`specify → plan → tasks → implement`) is the closest public analog to Stage 3→5. Each phase is a Markdown artifact an AI agent generates from the prior one ([github/spec-kit](https://github.com/github/spec-kit), [spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)). `spec.md`: numbered feature (001…), header metadata, per-story blocks (priority tag, journey, "Why this priority," "Independent Test," Given/When/Then "Acceptance Scenarios," Edge Cases), "Requirements" (numbered FR-001… with inline `NEEDS CLARIFICATION: [gap]` markers, "Key Entities"), "Success Criteria" (numbered SC-001…, tech-agnostic), "Assumptions." Forbids implementation detail ("WHAT/WHY, not HOW"). `plan.md`: tech choices with rationale, architecture traced to requirements, "constitutional compliance gates." `tasks.md`: one line each, `[ID] [P?] [Story] Description`, e.g. `T012 [P] [US1] Create Entity1 model in src/models/entity1.py` — sequential ID, optional parallel-safe marker, story tag, exact file path; grouped by phase, tests-before-code within a story. `constitution.md`: nine fixed principles (library-first, test-first, simplicity gate) plans are checked against.

**MetaGPT's SOP/structured-document bus** encodes a software company's SOP as a fixed sequence of typed document handoffs instead of open dialogue (Hong et al., ICLR 2024 oral, [arXiv:2308.00352](https://arxiv.org/abs/2308.00352)). Each role publishes one schema-typed document to a shared message pool; other roles subscribe only to what they need. Schemas, per independent summaries ([IBM](https://www.ibm.com/think/topics/metagpt), [agent-research-book](https://github.com/ndqkhanh/agent-research-book/blob/main/docs/91-metagpt-deep.md)): **PRD** (user stories, requirement pool, "Anything UNCLEAR" field); **System Design** (File List, Data Structures, API/interface signatures, Mermaid sequence diagrams); **Task List** (per-task description mapped to a file from the Architect's File List). Implemented as Pydantic-typed `ActionOutput` objects, so downstream agents parse mechanically, not by re-reading prose.

**BDD/Gherkin** collapses spec and test into one artifact. A `.feature` file: `Feature:` (title + narrative), optional `Background:`, one or more `Scenario:`/`Scenario Outline:` (+`Examples:` table) built from `Given`/`When`/`Then`/`And`/`But` steps ([Cucumber docs](https://cucumber.io/docs/gherkin/); [CRAN reference](https://cran.r-project.org/web/packages/cucumber/vignettes/reference-gherkin.html)). A step-definition layer binds each line to executable code, so one file is requirement, acceptance criteria, and test at once. I found no documented game-industry case study using Gherkin/Cucumber for gameplay QA — its literature is overwhelmingly web/API testing ([BrowserStack](https://www.browserstack.com/guide/learn-about-cucumber-testing-tool)); a real gap, not an oversight.

All three land on the same shape we use: a behavior statement that is both requirement and test seed. Spec Kit and MetaGPT seam it across three-to-four typed documents; Gherkin seams it inside one file. Our epic → e2e → tests → card chain is closer to the former — R-###-## sits in the same slot as Spec Kit's FR-### and MetaGPT's PRD stories.

## 2. Versioning and change propagation

None of the three has a mechanized "spec revised → tests revised → task respec'd" protocol.

**Spec Kit** states the aspiration — "change a core requirement in the PRD, and affected implementation plans update automatically" ([GitHub blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)) — but no template or doc shows how to detect which plan/task sections a spec change invalidates, or what happens to an in-flight task. In practice this means regenerate-and-re-review the whole downstream chain.

**MetaGPT** treats the message pool as append-only publish/subscribe; there is no documented re-publish or rollback protocol for an already-consumed PRD (inference from the design, not a stated claim in the paper).

**BDD/Gherkin** has the sharpest documented failure: "the spec drifted between the natural-language layer (which the business owned) and the step-definition layer (which the engineers owned) at exactly the rate the two roles diverged," and feature files "rotted" and were "quietly shelved" once step-definitions no longer matched the prose above them ([Frisinger, "Spec-Driven Development Is the Prose-Spec Drift Trap, Reborn"](https://dev.to/tmfrisinger/spec-driven-development-is-the-prose-spec-drift-trap-reborn-4p99)). The same piece generalizes across five historical attempts (requirements docs, Gherkin, wiki design docs, OpenAPI, now SDD): any artifact a machine doesn't fail loudly on when wrong will drift; only the executable layer is safe, because "a change to one that does not match a change to the other produces a failing build."

**What breaks in practice:** free-text layers are unfalsifiable and drift first, silently; regeneration cost scales with chain length; mid-flight work has no documented resolution in any of the three — this is exactly our own `203c-e05-candidate-regression-repair` pattern (`agora/queue/203c-e05-candidate-regression-repair.md`), a later card silently regressing an earlier one, caught by red/green checks, not spec diffing. Our `red_check.py`/`green_check.py` already do the job Frisinger says only executable tests can.

## 3. Handling a never-seen feature type

**Spec Kit**: four fixed Markdown templates; a new artifact kind (e.g. content/data output, not code) has no separate template — it's forced into the same Requirements sections written for code. The templates are code (checked-in structure); generated spec/plan/tasks content is data. A new artifact *kind* needs a new template — a manual, human-authored change, exactly analogous to our own scripts being fixed code over data-shaped epics/rules/tests.

**MetaGPT**: fixed role sequence; a new artifact kind has no home unless a new role/schema is coded in. The PRD's "Anything UNCLEAR" field is its only seam for the model to flag a schema mismatch — structurally like our `Q-###-##` flags, but with no register tracking it across runs the way `docs/northstar/ambiguity_register.md` does.

**Gherkin/BDD** generalizes better, because of its data/code split: Given/When/Then steps are data (plain text, regex-matched); step-definition functions are code. A new feature type needs new step vocabulary (data) plus, only if nothing matches, one new step function (code) — no new document kind. This is the strongest argument for keeping our expectation-spec schema generic: if the vocabulary is project-agnostic ("state check," "invariant," "visual claim"), the same generator absorbs a new content type without a code change.

Applied to us: a new **test kind** (e.g. a first T2 visual claim) is data under all three's logic only if the schema already has a slot for it (a `visual_claims` field, empty by default). A new **target type** (a data/content deliverable rather than code behavior) is the harder case none of the three solves publicly — both MetaGPT's Task List and Spec Kit's tasks.md assume a task maps to a source file. Our card schema already generalizes past this by keying off `acceptance:` (a runnable command) rather than file type — a command that runs a data-validator instead of a unit test costs nothing extra.

## 4. Proposed project-agnostic artifact chain

**story → expectation spec → tests → cards**, free of any Ouroboros noun in the schema itself.

```
story: {id, title, actor, narrative}

expectation_spec (one per story, one block per rule):
  id                 # RULE-###-##
  given              # setup: preconditions, fixture state, seed
  when               # directive(s): action/command/event under test
  then:
    state_checks:    # T1, required — field/operator/expected_value
    invariant_ids:   # T1, optional — refs into a project invariant catalog
    visual_claims:   # T2 — [] if none; else {description, judge_prompt, capture_spec}
  edge_case: bool
  scale_gate: {metric, threshold, units}   # optional

tests: {test_id, rule_ref, fixture_refs, body, is_control}

card: {id, target:{files, allowed_files}, acceptance, brief, symbol_hints, size_budget}
```

**Required for T1:** `given`, `when`, `then.state_checks` (≥1), `edge_case`. **Required additionally for T2:** `then.visual_claims` non-empty, each with `description`, `judge_prompt`, `capture_spec`; a story with no visible surface declares `visual_claims: []` explicitly, mirroring the Definition of Ready's "no empty section" rule (`docs/northstar/PLAN.md:178`) and E-05's own "visual: none direct" line.

**Against our current cards** (`agora/queue/204a3-e05-core-attack.md`, `scripts/specfactory/gen_card.py`): our frontmatter (`project, goal, acceptance, allowed_files, snippet_file/symbol, header_file, rules_file, test_file, expected_lines, max_wall_minutes`) is already richer than Spec Kit's one-line task and does inline what MetaGPT splits into a separate System Design document (`header_file`/`snippet_symbol` = API definitions). Two gaps: (1) no `visual_claims`/`judge_prompt` slot anywhere — E-05's e2e file just asserts T1-only; a T2 epic would need this field added. (2) the `expectation_spec` layer doesn't exist as a structured record — `docs/northstar/e2e/E-05.md`'s "Rules" section is prose tables that `gen_test_skeleton.py` parses by slugifying the "Then" clause of free text (`rule_slug()`), which is exactly the brittleness that produced the quoted-term `SyntaxError` bug documented in `docs/northstar/spec_factory.md`. Structuring `given`/`when`/`then` per rule would remove that parsing risk.

## 5. Pitfalls and mitigations

1. **Spec drift.** A free-text layer with no automated check drifts from the executable layer at the rate its two owners diverge ([Frisinger](https://dev.to/tmfrisinger/spec-driven-development-is-the-prose-spec-drift-trap-reborn-4p99)); mitigation is collapsing spec into test, or making every claim mechanically checkable. We already exceed this: the Definition of Ready requires zero empty e2e sections and zero open flags before tests are written, and CLAUDE.md's stale-doc tripwire forces the doc rewritten in the same PR as any behavior change — a process rule, not just a file-format fix.
2. **Over-specification / overly technical scenarios.** BDD guides warn engineer-written scenarios drift into implementation detail, unreadable to the non-technical owner they serve ([TestQuality](https://testquality.com/how-to-write-effective-gherkin-acceptance-criteria/)). Our analog is the card *brief*, not the rule, and `docs/northstar/spec_factory.md` already names and fixes it: "the card brief names the rules file and cites no equation directly," and a brief drafted from tests "leaks implementation instead of intent" (the E-02 finding, also in `gen_card.py`'s docstring) — the same lesson, arrived at independently.
3. **Task granularity.** Spec Kit's only sizing signal is "different files, no dependency" for `[P]`; MetaGPT states no size cap at all. Our "30B Sizing Contract" (`docs/northstar/PLAN.md:213-217`: 3–5 symbols, one algorithm family, 40–80 lines, 5–15 assertions) is more prescriptive than either, because we size for a weaker implementer (a local 30B model) than either precedent assumes — a constraint we had to invent.
4. **Tests written from implementation, not intent.** Not named explicitly in the retrieved Spec Kit/MetaGPT material, but it's pitfall 2's mirror and matches our own E-02 finding; the pipeline's fix (brief from rules only, never tests) is documented, though nothing independently confirms the `agy` test-fill step itself never peeks at a reference implementation.
5. **Regeneration cost.** "Cheaper spec generation doesn't solve maintenance … more artifacts simply mean more things drifting out of sync faster" (Frisinger). Our mitigation is machine-checked gates at every seam (`red_check`, `green_check`, `card_lint`) rather than trusting regeneration to stay consistent — and Westley's own audit experiment (`docs/northstar/spec_factory.md`, closed 2026-09-17) found the extra Sonnet-per-file audit step added cost without catching what `green_check` already catches (card 202b2), independent evidence for this pitfall's core claim.

## Open questions for Westley

1. **Should the expectation spec be a new structured file per story, or stay embedded in e2e Markdown tables?** (a) New sidecar file (e.g. `E-##.spec.yaml`) parsed directly — removes the rule-text-parsing fragility in §4, adds a second file to keep synced. (b) Keep tables in the epic Markdown, tighten columns so `gen_test_skeleton.py` reads structured cells instead of slugifying prose — smaller diff, doesn't fully remove the class of bug. (c) Epic Markdown stays the authored source; Stage 3 also emits a machine-readable sidecar regenerated from it, never hand-maintained.
2. **Should `visual_claims`/`judge_prompt` fix a judge-model contract in the schema, or leave it per-project?** (a) Schema carries a `judge_model` field with a project-set default — more portable, risks under-specifying what the judge sees. (b) Schema carries only prompt text and capture spec; judge wiring lives entirely in per-project harness config — simplest schema, but a new project reinvents judge wiring each time, which cuts against "absorb undefined future features without harness code changes."
3. **Should the 30B sizing contract travel with the schema as a fixed default, or be per-project-configurable?** (a) Fixed numbers, since they were tuned for `qwen3-coder:30b` specifically. (b) A `sizing_profile` field on the card schema, defaulting to today's numbers. (c) No default — every new project must set it explicitly before its first card, forcing the choice instead of silently inheriting Ouroboros's numbers.
