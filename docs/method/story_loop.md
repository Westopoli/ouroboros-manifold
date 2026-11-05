# The story loop

One story (or one cascade of stories), one branch, one `--no-ff` merge on main. Git is the record. Westley's plan prompt names this file and says what the plan must do beyond it; nothing below is repeated in a card.

1. **Requirement.** The story row and its rules exist in the bible (`requirements.md`: Epic, Story, Rule, Flag; Definition of Ready); no open `Q-` row.
2. **Spec.** The Architect (a Fable chat) writes the cascade inputs in `docs/northstar/plans/cascades/<slug>/` (spec, contract, umbrella test) or one story page `docs/stories/<id>.md`. The pre-flight is one paragraph: every precondition checked by reading `git show origin/main:<path>` or by running, with the sha. Rules quoted by id; every file named; every shared interface in full; every number given or a named `DRAFT-`; the scene as one line `Scene: res://<path> [launch arguments]`.
3. **Tests first.** Failing tests exist before any code, each naming the `S-###`/`R-###-##` it proves. The `/manager-mode` shard-test-writer writes them for a cascade; one test writer for a single-builder story. Builders never edit tests. A test the builder believes wrong is fixed by the skill's test-fixer or by the Architect, in a commit with the trailer `Test-defect: <why>`; thresholds, windows and tolerances are Westley's.
4. **Build.** The cascade (a Sonnet 5.5 chat running `/manager-mode` on the spec path; leaves on Sonnet 5.5 in the skill's worktrees), or one Sonnet builder on a worktree cut from `~/Projects/ouroboros-manifold`, until the tests are green. `builder.md` holds the build lines.
5. **Verify.** `make`, the story's tests, `godot.real --headless --import`, and the console clean of `SCRIPT ERROR`, `ERROR:`, `Parser Error`. A red test outside the story, a lint or a moved golden is a line in the landing report, not a block; the known-red lists `scripts/specfactory/gd_tests_known_red.txt` and `lane_plays_known_red.txt` carry ruled reds with the ruling commit.
6. **Land.** Open the merged game with `scripts/play.sh` (`--story <id>` puts it in the story's state) and play it end to end: menu, the story's scene, on to the end of a match. Anything that breaks is fixed forward, by `/investigate` first (hypothesis, evidence, fix), never a guess. Then `git merge --no-ff` on main in `~/Projects/ouroboros-manifold`, subject `Land <id> <slug>`, trailers `Story:` and `Tests:`, push. Westley plays main when he likes and writes his verdict in `docs/northstar/story_reviews/westley/ruled.md`; a reject becomes the next plan's first item.

## Scenes, not screenshots

The review artifact of a player-facing story is a scene Westley runs, never a picture: the story names its scene path and launch arguments, and `scripts/play.sh --story <id>` opens it (the `OS.get_cmdline_user_args()` readers in `autoload/c_bridge.gd`, `autoload/era_config.gd` and `autoload/qa_daemon.gd` are the pattern). The 30B plays main nightly with the same script and files what it finds as `H-` rows.

## Trailers

`Story:` and `Tests:` on a `Land` merge; `Test-defect: <why>` on a commit that changes a test; `Decision: DEC-<slug>-<date>` on a commit that adds a row to `decisions.md`. The nightly sweep (`scripts/specfactory/sweep.sh`, the full suite on main) records `Sweep <date> <pass|red n>` as an empty commit; a red sweep is a report, never an automatic revert.
