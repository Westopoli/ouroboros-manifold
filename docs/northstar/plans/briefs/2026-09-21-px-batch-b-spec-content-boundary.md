# HANDOFF BRIEF — PX batch B: PX-1, PX-10, PX-11 (expectation spec, content card, second project)

Self-contained. Program context: `2026-09-21-factory-program.md`; design under test: `docs/northstar/PLAN.md` section "The Factory" (artifact table, "Three homes", "Content and multiplayer are not special cases"). Results as `docs/northstar/proving_ground/PX-01-*.md`, `PX-10-*.md`, `PX-11-*.md` plus `SCORECARD.md` rows, in the style of the existing files, "Design consequences" left blank. Normal prose.

## Rules for the implementor

- Sub-agents are Sonnet; you plan and review, they build. Ask Westley about his Claude usage before a batch of more than two doers.
- Nobody writes game code or implements a card. PX-11 runs one real build card through Agora on a different project, which is the only model call in this batch; it needs the GPU, so it runs only when `systemctl --user is-active agora-dispatcher.service` says `inactive` or Westley pauses the chain for it. Ask him for the window; do everything else first.
- New files allowed: under ouroboros `scripts/specfactory/`, `tests/specfactory/`, `docs/northstar/proving_ground/`, and one toy pack pair under `docs/northstar/proving_ground/evidence/px10/`; under agora `projects/proving-ground/` and `projects/salesmen/` (data only); under `~/Projects/the-best-salesmen` one failing test and one stub for PX-11 (its own repo, its own commit). No edits to `~/Projects/agora/scripts/` unless the change is generic and you record it as the PX-11 count.
- Scratch under `/tmp/pxB/`; clean up worktrees.
- Commit and push per PX. Trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Never stage files you did not create.

## PX-1 — expectation spec to mission

**Claim (artifact table):** the expectation spec, generated from the story and never hand-edited, is enough to generate a director mission mechanically; no prose rules file is needed.

**Facts.** No spec schema exists yet; this PX writes the first one. The director's mission format is runtime JSON (`~/Projects/agora/runs/director-20260915-0101/mission.json`: `mission_id, feature, hypothesis, success_signal, checkpoint_every, steps`), matching `Mission` in `scripts/cascade_types.py:948-956`. A step's `expect` dict may only use `EXPECT_KEYS = ("url_path", "url_path_prefix", "role", "name_contains", "text_contains", "status", "max_actions")` (`cascade_types.py:380-381`; `qa_director_core.py:63-64` drops steps with other keys); `read_state` is in `ACTION_VERBS` (`:388`) for the desktop protocol. The toy scene is the probe-D Godot scene PX-02 ran (toy scene commit `b247fdf`; see `proving_ground/PX-02-*.md` for the path and the launch on a private Xvfb) with the eleven verbs and `pause`/`step`. Its prose rules file is `~/Projects/agora/projects/proving-ground/rules/toy-scene.md`.

**Schema to write** (`docs/northstar/spec_factory/expectation_spec.schema.json`, plus one instance `S-TOY.spec.yaml` beside it for the toy scene):

```yaml
story: S-TOY
rules:
  - id: R-TOY-01
    given: {fixture: toy_scene, seed: 1, switches: {}}
    when:
      - {verb: click, target: "Click me"}
      - {verb: step, n: 1}
    then:
      state: [{path: "label.count", op: "==", value: 1}]
      invariants: []
      visual: []            # declared empty on purpose
    scale: null
  - id: R-TOY-02
    given: {fixture: toy_scene, seed: 1, switches: {}}
    when: [{verb: press, key: "L"}, {verb: step, n: 1}]
    then:
      state: [{path: "layer_dot.layer", op: "==", value: 2}]
      invariants: []
      visual: [{claim: "the layer dot sits higher on screen than at layer 1", oracle: "held"}]
    scale: null
```

Nothing in the schema names a game; `fixture`, `path` and `verb` are strings the profile resolves.

**Generator.** `scripts/specfactory/spec_to_mission.py <spec.yaml> --profile <qa.toml> --out mission.json`: one mission per rule, `steps` from `when` verbatim plus a final `read_state` step whose `expect` is the `then.state` checks. `EXPECT_KEYS` has no state-path key; add nothing to Agora for this PX: encode the state check as `text_contains` over the `read_state` JSON if that works with the desktop backend, and if it does not, report that as the design finding (the design says state checks are the first oracle; the director's expect vocabulary cannot express one today). Visual claims with `oracle: held` become a `held` note in the mission, never a step.

**Run.** On the toy scene with the scripted runner from PX-02 (no model; the scripted actor executes the steps), on the clean build and on the planted build (PX-02/PX-03 used a planted variant; reuse it or plant "label does not increment"). Expected: R-TOY-01 passes clean, fails planted; the planted run's finding names the rule id.

**Pass.** Mission generated from the spec alone with `rules/toy-scene.md` deleted from the profile for the run; the same clean/planted outcome as with the prose rules; the diff between the generated mission and the director's last hand-planned `toy-scene-plan-01` mission stated.

## PX-10 — content card

**Claim ("Content and multiplayer are not special cases", B.8 change 3):** a content card is a gate over a pack directory whose acceptance is validators plus a fenced content diff; a broken pack fails, a clean pack passes, and the fence blocks the worker from editing the validator.

**Facts.** No pack validator exists (grep of `scripts/`, `tools/`, `simulation/library/`, `autoload/era_theme_resolver.gd`); `assets/eras/test_era/` has `manifest.json` and three `.tscn` units; manifest keys `era_id, era_display_name, era_accent_color, units, structures, environment, materials, faction_colors`. No banned-word list exists in code; E-09 R-071-02 and E-21 R-153-02 name one as prose. R-146-01 is the full pack checklist; R-146-03 says a missing required entry fails with the entry named and a missing optional asset uses the placeholder; R-145-01 says no engine identifier names an era.

**Build.** `scripts/specfactory/pack_validate.py <pack dir>`: checks the manifest keys above, that every referenced scene path exists, that unit ids do not contain the era id (R-145-01 applied to content), that `era_display_name` and any naming pool contain no word from `docs/northstar/spec_factory/banned_words.txt` (write it: ten obvious meta or IP terms), and that a new optional class (`weather`, absent from every pack today) is accepted as missing. Exit 1 with the entry named.

**Fixture.** `evidence/px10/pack_clean/` (copy of `test_era` with the ids renamed) and `evidence/px10/pack_broken/` with three defects: a missing required key, a banned word in the display name, a unit id containing the era id.

**Card.** A `kind: content` card file (write it as data under `evidence/px10/`, do not queue it) whose acceptance is `pack_validate.py` over the pack path and a content diff (`diff` of the mechanical keys against `pack_clean`). Run `card_lint.py` on it: it must lint; then a second card whose `allowed_files` includes `scripts/specfactory/pack_validate.py` must fail lint (add that check to `card_lint.py` if absent: a card may not allow a path under `scripts/specfactory/` or `tests/`; report whether it was absent).

**Pass.** Broken pack rejected with all three defects named; clean pack accepted; missing optional class accepted; the validator-editing card blocked by lint.

## PX-11 — second project through the profile alone

**Claim ("Three homes"):** onboarding a second project needs zero Agora code changes; anything needed goes into Agora generically.

**Facts.** `~/Projects/the-best-salesmen` already has a QA profile (`~/Projects/agora/projects/salesmen/qa.toml`: `[target]`, `[browser]`, `[seed]`) and a converged QA campaign (`campaigns/todo/001-salesmen-qa.md`). Its tests: `uv run pytest` (fast) and `uv run pytest tests/e2e -m e2e`. The build side has never run on it. Agora's build loop has a Python mode (`build.py:876-877` `_worker_user`). The profile schema is `agora/specs/cascade-qa-profile.md:24-31`; ouroboros's `projects/ouroboros/qa.toml` adds `[backend]` and `[desktop]` sections the schema does not list. The design says the profile also carries the gate set (`orchestrators` may be empty), the language table and the chain; none of that exists in code yet, so this PX measures the distance.

**Do.**
1. Write one story for salesmen as Given/When/Then (a trivial pure function in its backend: a rule with two numbers), one failing test in its repo, one stub, one card in `agora/queue/parked/` for project salesmen (py mode). Lint it with `card_lint.py` from the salesmen repo root; record every place lint assumes ouroboros (paths, `om_` prefixes, C-only closure).
2. Run the card through `build.py` once in the agreed GPU window (one attempt is enough; if the worker fails, that is not the finding; the finding is what the harness needed). Record every edit required anywhere in `~/Projects/agora/scripts/` and classify each: generic (a language table entry, a profile key) or project-specific (anything naming salesmen or ouroboros).
3. Run one QA session with the existing salesmen profile to confirm the QA side still works after any edit.
4. Write the profile the design describes (`projects/salesmen/profile.toml`: language table, test command, gate set with `orchestrators = []`, `determinism = false`, chain order) as data, even though nothing reads it yet, and list which of the edits in step 2 that file would have made unnecessary.

**Pass.** The count of project-specific Agora code changes is zero. Report the count of generic changes and the list, and the lint assumptions from step 1. If the number is not zero, the write-up says which change and why it could not be generic.

## Order

PX-10 first (no dependencies), PX-1 second (needs the toy scene on Xvfb, no model), PX-11 last (needs the GPU window).

## Verification

- `pytest tests/specfactory/` green including new tests.
- Ouroboros E-02 baseline untouched (52 passed / 4 skipped on the E-02 set).
- Agora's own suite no worse than its 13 known failures plus 15 strict xfails (`~/Projects/agora/.venv/bin/python -m pytest -q tests/`).
- `git worktree list` clean of `/tmp/pxB`; each repo's `git status --short` shows only deliverables before commit.
- Finishing report for Westley: per PX the pass/fail against the number, every place the design's vocabulary could not express what was needed (PX-1's state check, PX-11's gate switches), no recommendations.
