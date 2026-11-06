# BOUNDARIES, wave 2 (S-247 layout kit: leaf-02, the `layout_dump` CLI)

Spec = `docs/northstar/plans/cascades/layout-kit-assault/spec.md` (criteria 5 to 7, "JSON", "Checks"); header = `csrc/layout_kit.h`. Axes: CORRECT (test-design.md). Test files: `tests/csim/test_layout_kit_{cli,connected,fairness,bypass,approaches,chokes,bounds,determinism}.py`, helper `tests/csim/layout_kit_cli_helpers.py` (37 `assert` statements in all, budget 40). Every module honours `LAYOUT_DUMP_SRC` (default `csrc/tools/layout_dump.c`).

| symbol | axis | boundary | spec says | disposition |
|---|---|---|---|---|
| CLI source | Existence | `csrc/tools/layout_dump.c` absent | criterion 5 | every module fixture asserts the file; all 675 tests are red for that reason (lint test: `src.is_file()`) |
| `--canvas` | Range | 7999 / 8000 / 64000 / 64001 | header -3 outside `DRAFT_CANVAS_MIN`..`_MAX`; criterion 5: exit 1, stderr prints the return code | test written (`a_failed_generation_exits_1`): 7999 and 64001 exit 1 with "-3" on stderr and no JSON, 8000 and 64000 exit 0 |
| `--canvas` | Existence | absent | criterion 5: default `DRAFT_CANVAS_ASSAULT` | test written (`defaults_and_echo`: 24000) |
| `--canvas` | Conformance | non-numeric ("wide") | "usage error" 2 | test written |
| `--canvas` | Range | 0 / negative | passes to `om_lk_generate` (-3) | not tested separately (7999 covers -3); Q5(g) |
| `--sides` | Existence / Conformance | absent / each of mirror, rotate, separate / "sideways" | default separate; usage 2 | test written (default; all three in the sweeps; bad name exits 2) |
| `--seed` | Range | uint64 (2^32+1, 2^63, 2^64-1) | header: `uint64_t seed`; JSON "seed (integer)" | test written (`seed_is_a_full_uint64`), the largest seed must print whole (a signed print fails it) |
| `--seed` | Conformance | non-numeric | usage 2 | test written |
| `--seed` | Existence / Range | absent; negative | silent | question Q5 (a)(h), untested |
| `--archetype` | Conformance | "banana" | unknown name exits 2 | test written |
| `--archetype` | Range | the nine other archetypes | exits 2 with "not built" | test written, names assumed from `csrc/mission.c:161-170` snake_case; question Q2 |
| `--archetype` | Existence | absent | silent | question Q5(b), untested (tests always pass it) |
| unknown option; flag missing its value | Conformance | `--bogus`; `--archetype` last | usage 2, stderr names it | test written (8 usage cases incl. `--check` without file and bad `--break` name) |
| `--out` | Cardinality | one file | file gets the JSON, stdout empty | test written (`out_writes_the_file_and_leaves_stdout_empty`) |
| `--seeds A..B --out-dir` | Cardinality | 1..12, 3..5, 7..7 (A = B) | one file and one line per seed | test written; files exactly the named set, each equal to the single-seed run, lines `seed N sides S checks 6/6` |
| `--seeds` | Range / Existence | A > B; no `--out-dir`; dir missing; non-numeric | silent | question Q5(c)(d), untested |
| `--break` | Conformance | unknown name | silent beyond "<check>" | test written (exit 2 as a usage error: the only sensible reading of "usage error"; flagged here as derived) |
| `--break connected` | Reference | objective lanes all removed | criterion 6 | test written: lanes gone, objective unreachable, distances print `-1.00`, false vs true without, edit equal to the spec's words, Python oracle agrees |
| `--break fairness` | Reference | resource 0 moved 40 percent toward A | criterion 6 (positive control: check false) | edit test written (literal); positive control written and RED against a literal implementation: the check cannot fall on this engine (question Q1, blocking) |
| `--break bypass` | Existence | way-round lane of choke 0 removed | criterion 6 | test written; "no path avoiding the lane" counts as failing (spec check 3 is silent on an infinite avoiding path; the positive control forces it) |
| `--break approaches` | Cardinality | lowest-index objective lane removed, one left | criterion 6 (parenthesis) | test written: exactly one lane left, `connected` stays true, check false |
| `--break chokes` | Range | width 800 (`DRAFT_CHOKE_W_MAX` + 100) | criterion 6 | test written; unbroken widths 300..700 inclusive (R-113-03) and `800.00` printed |
| `--break bounds` | Range | place x = canvas + 100 at canvas 8,000 / 16,000 / 64,000 | criterion 6 | test written, edge follows the asked canvas |
| `--break` | Reference | what else the edit leaves alone (lane renumbering, requests, lane endpoints at the moved node) | silent | question Q3; tests are neutral on lane-index fields, strict (literal) on everything else |
| JSON | Ordering | keys of the object, of every element, `fairness`, `checks`; elements in array order | "JSON": exact order | test written (3 sides modes) |
| JSON | Conformance | two-space indent, one element per line, district rows one line, single final newline | "JSON" | test written (3 sides modes); array formatting inside a line (`[0, 1]` vs `[0,1]`) not pinned |
| JSON | Conformance | quantised text `[-]int.dd`, no exponent, no `%g`, no `-0.00`; bare integers for counts | "Numbers" | test written; per-field table in the helper, canvas / frac / request height_bands / drafts accept either form (Q4) |
| JSON | Range | `-1.00` for an unreachable distance | "JSON" | test written (connected break) |
| JSON | Conformance | `kind` `piece` `landform` `mode` strings, side letters A / B / none, `archetype` "assault", `sides` | "JSON" name lists | test written (3 sides modes) and cross-checked against the engine for all 36 layouts |
| JSON | Reference | equals the engine's own dump | criterion 5, "Tests" | test written (36 layouts, probe as reference, +-1 hundredth); rounding mode unstated (Q4) |
| `drafts` | Ordering / Existence | every `om_lk_draft_*` entry, table order | criterion 5, JSON | test written: names and order equal the header's X-macro order and the probe's, values within a hundredth; `DRAFT_INF` (1e30) and `DRAFT_EPS` (1e-9) cannot print as integer hundredths: Q4 |
| `--check` | Conformance | six lines `connected true` ... in order, exit 0 / 1 | criterion 7 | test written: 36 default layouts plus canvas 8,000 and 64,000 x 3 modes, output equal to the file's own `checks`; also for each broken file |
| `--check` | Reference | judges the file, not the seed | criterion 7 | test written: a lane deleted (text edit), a choke widened to 800, a place moved past the 8,000 canvas edge in the file, each false vs true unedited |
| `--check` | Existence | missing / malformed file; with other flags | silent | question Q5(e), untested |
| determinism | Time / Ordering | two runs; -O0 vs -O2 over 12 seeds x 3 modes; -O0 vs -O2 for each break | R-112-01, criterion 2 | test written, byte equality of stdout, fresh processes (no cache) |
| libm ban | Reference | `libm_lint.py` over `csrc/` with the CLI in place | criterion 4 | test written (lint exit 0 and the file exists); lints the file's own directory when `LAYOUT_DUMP_SRC` is set |
| scale | Cardinality | 1 layout per call, 12 per `--seeds` | Scale profile: nothing above 12 | no scale test (no growth claim for the CLI; the quadratic work is in the engine, wave 1) |

Throwaway-CLI proof (scratchpad, not in the repo): a CLI written by me against the header passes 638 of 675 tests, the 37 failing being the `fairness` positive control (36 cases) and the `--check` on the broken fairness file (1 case) (Q1); with an extra direct lane added to the fairness edit (not the spec) the positive control passes too. 28 deliberate bugs were each caught: `%g` numbers, key order swapped, drafts out of order, no final newline, multi-line place, usage exit 1, generate failure exit 2, `--check` ignoring the canvas, `--check` regenerating from the seed, `--check` exit always 0, `--out` also writing stdout, summary line without `/6`, `--seeds` hi exclusive, `-1` printed as `-1`, `DRAFT_INF` wrapped, "not built" missing, a `rand()` call (lint), a wrong word in the lane names, signed seed, break chokes at 750, break bypass not applied, break approaches removing all, break connected removing one, break bounds not moving the node, break fairness at 50 percent, edits not re-running the checks, a pid-dependent byte, an -O2-only byte.
