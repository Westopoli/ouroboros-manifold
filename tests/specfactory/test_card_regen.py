# spec: docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md R22
"""Tests for scripts/specfactory/card_regen.py.

Builds a throwaway synthetic project (csrc/, tests/csim/, docs/bible/epics/,
a queue with one epic-wide placeholder card per story) per test, exactly
like test_skeleton_gen.py and test_card_lint.py, so this suite never
depends on the real ouroboros-manifold repo's own state. The fixture has
two stories (S-901, S-902) so story-boundary and cross-story symbol reuse
are both exercised.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CARD_REGEN = REPO / "scripts" / "specfactory" / "card_regen.py"

HEADER = '''#ifndef OUROBOROS_SIM_H
#define OUROBOROS_SIM_H
typedef struct om_world om_world;
void om_world_free(om_world *w);
#endif
'''

# om_world_new is "built" (non-STUB, real body) -- every test calls it, and
# it must never be assigned to a new card or counted against any story's
# symbol budget.
OTHER_C = '''#include "ouroboros_sim.h"
om_world *om_world_new(unsigned n, unsigned long long seed) { (void)n; (void)seed; return 0; }
'''

CONFTEST = '''def make_world(lib):
    return lib.om_world_new(0, 1)


def set_thing(lib, w, idx):
    lib.om_widget_set(w, idx)
'''

BIBLE = '''# E-90 -- Synthetic Test Epic

## Stories

### S-901 -- First synthetic story
Rules
- R-901-01  Given a fixture, When alpha runs, Then alpha holds.
- R-901-02  Given a fixture, When beta runs, Then beta holds.
- R-901-03  Given a fixture, When gamma runs, Then gamma holds.
- R-901-04  Given a fixture, When delta runs, Then delta holds.
- R-901-05  Given a fixture, When epsilon runs, Then epsilon holds.
- R-901-06  Given a fixture, When zeta runs, Then zeta holds.

### S-902 -- Second synthetic story
Rules
- R-902-01  Given a fixture, When eta runs, Then eta holds.
- R-902-02  Given a fixture, When theta runs, Then theta holds.
'''

TEST_S901 = '''from conftest import make_world, set_thing


def test_R_901_01_alpha(lib, world_factory):
    w = make_world(lib)
    lib.om_alpha_step(w)


def test_R_901_02_beta(lib, world_factory):
    w = make_world(lib)
    lib.om_alpha_step(w)
    lib.om_beta_read(w)


def test_R_901_03_gamma(lib, world_factory):
    w = make_world(lib)
    set_thing(lib, w, 0)
    lib.om_gamma_calc(w)


def test_R_901_04_delta(lib, world_factory):
    w = make_world(lib)
    lib.om_delta_apply(w)


def test_R_901_05_epsilon(lib, world_factory):
    w = make_world(lib)
    lib.om_epsilon_finish(w)


def test_R_901_06_zeta_already_built(lib, world_factory):
    # calls only the already-built om_world_new (via make_world) -- no
    # unbuilt symbol of its own, so this test needs no new card.
    w = make_world(lib)
    assert w == 0
'''

TEST_S902 = '''from conftest import make_world


def test_R_902_01_eta(lib, world_factory):
    w = make_world(lib)
    lib.om_alpha_step(w)  # shared with S-901 -- cross-story reuse within one epic
    lib.om_eta_only(w)


def test_R_902_02_theta_already_built(lib, world_factory):
    w = make_world(lib)
    assert w == 0
'''


def _card_text(*, snippet_symbol: str, test_file: str, card_goal: str,
                epic: str = "E-90", snippet_file: str = "csrc/synth.c") -> str:
    return (
        "---\n"
        f"project: {{PROJECT}}\n"
        f'goal: "{card_goal}"\n'
        "acceptance:\n"
        f'  - "{{VENV}}/bin/python -m pytest -q -p no:cacheprovider {test_file}"\n'
        f'allowed_files: "{snippet_file}"\n'
        f"snippet_file: {snippet_file}\n"
        f'snippet_symbol: "{snippet_symbol}"\n'
        "header_file: csrc/ouroboros_sim.h\n"
        "extra_context_files: csrc/om_internal.h\n"
        f"rules_file: projects/ouroboros/rules/{epic}.md\n"
        f"test_file: {test_file}\n"
        "expected_lines: 40\n"
        "max_wall_minutes: 30\n"
        "---\n\n## Brief for DeepSeek\nOld placeholder, not real.\n"
    )


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "docs" / "bible" / "epics").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(HEADER)
    (project / "csrc" / "other.c").write_text(OTHER_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "tests" / "csim" / "test_E90_S901_first_synthetic_story.py").write_text(TEST_S901)
    (project / "tests" / "csim" / "test_E90_S902_second_synthetic_story.py").write_text(TEST_S902)
    (project / "docs" / "bible" / "epics" / "E-90-synthetic.md").write_text(BIBLE)
    return project


def _init_queue(tmp_path: Path, project: Path) -> Path:
    queue = tmp_path / "queue"
    parked = queue / "parked"
    parked.mkdir(parents=True)
    venv = str(tmp_path / "venv")
    fields = {
        "PROJECT": str(project),
        "VENV": venv,
    }

    def card(**kw):
        text = _card_text(**kw)
        for k, v in fields.items():
            text = text.replace("{" + k + "}", v)
        return text

    (parked / "500a-e90-synth-first_synthetic_story.md.hold").write_text(card(
        snippet_symbol="om_synth_step",
        test_file="tests/csim/test_E90_S901_first_synthetic_story.py",
        card_goal="csrc/synth.c implements E90 S-901",
    ))
    (parked / "501a-e90-synth-second_synthetic_story.md.hold").write_text(card(
        snippet_symbol="om_synth_step",
        test_file="tests/csim/test_E90_S902_second_synthetic_story.py",
        card_goal="csrc/synth.c implements E90 S-902",
    ))
    return queue


def _run(project: Path, queue: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CARD_REGEN), "E-90", "--project", str(project), "--queue", str(queue), *extra],
        capture_output=True, text=True,
    )


def _json_result(project: Path, queue: Path, *extra) -> dict:
    proc = _run(project, queue, "--json", *extra)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)["results"]["E-90"]


def _story(result: dict, story_id: str) -> dict:
    return next(s for s in result["stories"] if s["story_id"] == story_id)


def test_writes_nothing_under_report(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    out = tmp_path / "out"
    proc = _run(project, queue, "--out", str(out), "--report")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not out.exists()


def test_splits_story_into_cards_of_at_most_five_symbols(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    result = _json_result(project, queue)
    s901 = _story(result, "S-901")
    # 5 unbuilt symbols this story needs (om_world_new is built, excluded):
    # om_alpha_step, om_beta_read, om_widget_set, om_gamma_calc,
    # om_delta_apply, om_epsilon_finish = 6 symbols -> two cards (5 + 1).
    all_syms = [sym for c in s901["cards"] for sym in c["symbols"]]
    assert len(all_syms) == len(set(all_syms)) == 6
    assert "om_world_new" not in all_syms
    assert len(s901["cards"]) == 2
    for c in s901["cards"]:
        assert len(c["symbols"]) <= 5


def test_first_appearance_order_and_helper_symbol_included(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    result = _json_result(project, queue)
    s901 = _story(result, "S-901")
    all_syms = [sym for c in s901["cards"] for sym in c["symbols"]]
    # source order across tests: alpha (test 01), beta (test 02, alpha
    # already seen), widget_set + gamma_calc (test 03), delta (test 04),
    # epsilon (test 05).
    assert all_syms == [
        "om_alpha_step", "om_beta_read", "om_widget_set",
        "om_gamma_calc", "om_delta_apply", "om_epsilon_finish",
    ]


def test_card_acceptance_never_spans_a_symbol_outside_the_card(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    result = _json_result(project, queue)
    s901 = _story(result, "S-901")
    card1, card2 = s901["cards"]
    assert card1["symbols"] == ["om_alpha_step", "om_beta_read", "om_widget_set", "om_gamma_calc", "om_delta_apply"]
    assert card2["symbols"] == ["om_epsilon_finish"]
    # test_R_901_02_beta needs alpha_step + beta_read -- both in card 1.
    assert "test_R_901_02_beta" in card1["tests"]
    # test_R_901_05_epsilon needs epsilon_finish -- only in card 2, not card 1.
    assert "test_R_901_05_epsilon" in card2["tests"]
    assert "test_R_901_05_epsilon" not in card1["tests"]


def test_already_satisfiable_test_gets_no_card(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    result = _json_result(project, queue)
    s901 = _story(result, "S-901")
    assert "test_R_901_06_zeta_already_built" in s901["already_satisfiable"]
    for c in s901["cards"]:
        assert "test_R_901_06_zeta_already_built" not in c["tests"]


def test_card_ids_reuse_old_numeric_prefix_and_tail(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    result = _json_result(project, queue)
    s901 = _story(result, "S-901")
    s902 = _story(result, "S-902")
    assert s901["cards"][0]["card_id"] == "500a1-e90-synth-first_synthetic_story"
    assert s901["cards"][1]["card_id"] == "500a2-e90-synth-first_synthetic_story"
    # S-902 needs only om_eta_only of its own: om_alpha_step was already
    # claimed by S-901's card 500a1 earlier in this same epic run (stories
    # share one module file, so a symbol is built once -- sequential
    # ownership across stories, R21) -- no digit suffix when the story needs
    # exactly one card.
    assert len(s902["cards"]) == 1
    assert s902["cards"][0]["card_id"] == "501a-e90-synth-second_synthetic_story"
    assert s902["cards"][0]["symbols"] == ["om_eta_only"]


def test_brief_quotes_only_the_rule_lines_named_by_the_cards_own_tests(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    out = tmp_path / "out"
    proc = _run(project, queue, "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    card1_text = (out / "E-90" / "500a1-e90-synth-first_synthetic_story.md").read_text()
    assert "R-901-01  Given a fixture, When alpha runs, Then alpha holds." in card1_text
    assert "R-901-02  Given a fixture, When beta runs, Then beta holds." in card1_text
    assert "R-901-03  Given a fixture, When gamma runs, Then gamma holds." in card1_text
    assert "R-901-04  Given a fixture, When delta runs, Then delta holds." in card1_text
    # card 1's tests do not reach epsilon (R-901-05) or zeta (R-901-06)
    assert "R-901-05" not in card1_text
    assert "R-901-06" not in card1_text
    card2_text = (out / "E-90" / "500a2-e90-synth-first_synthetic_story.md").read_text()
    assert "R-901-05  Given a fixture, When epsilon runs, Then epsilon holds." in card2_text


def test_header_slice_is_the_literal_placeholder_line(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    out = tmp_path / "out"
    proc = _run(project, queue, "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (out / "E-90" / "500a1-e90-synth-first_synthetic_story.md").read_text()
    assert "## Header slice" in text
    assert "(run card_slice.py --write after the skeleton lands)" in text


def test_card_frontmatter_reuses_shared_fields_from_old_card(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    out = tmp_path / "out"
    proc = _run(project, queue, "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (out / "E-90" / "500a1-e90-synth-first_synthetic_story.md").read_text()
    assert "rules_file: projects/ouroboros/rules/E-90.md" in text
    assert "header_file: csrc/ouroboros_sim.h" in text
    assert "extra_context_files: csrc/om_internal.h" in text
    assert "max_wall_minutes: 30" in text
    assert "snippet_file: csrc/synth.c" in text
    assert 'snippet_symbol: "om_alpha_step,om_beta_read,om_widget_set,om_gamma_calc,om_delta_apply"' in text


def test_card_lint_passes_on_a_generated_card_modulo_missing_snippet_file(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    out = tmp_path / "out"
    proc = _run(project, queue, "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    card_lint = REPO / "scripts" / "specfactory" / "card_lint.py"
    lint_proc = subprocess.run(
        [sys.executable, str(card_lint), str(out / "E-90" / "500a1-e90-synth-first_synthetic_story.md"),
         "--project", str(project), "--queue", str(out / "E-90")],
        capture_output=True, text=True,
    )
    assert "MISSING_SNIPPET_FILE" in lint_proc.stdout
    assert lint_proc.returncode == 1


def test_report_md_lists_cards_and_already_satisfiable_and_no_test_placeholder(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    out = tmp_path / "out"
    proc = _run(project, queue, "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = (out / "E-90" / "report.md").read_text()
    assert "500a1-e90-synth-first_synthetic_story" in report
    assert "500a2-e90-synth-first_synthetic_story" in report
    assert "test_R_901_06_zeta_already_built" in report
    assert "om_synth_step" in report  # old placeholder, no test calls it


def test_cross_epic_overlap_detected_across_two_epics(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path, project)
    # a sibling epic E-91 whose own test also calls om_alpha_step (S-901's
    # first symbol) -- a real cross-epic ownership conflict.
    (project / "tests" / "csim" / "test_E91_S950_sibling.py").write_text(
        "def test_R_950_01_shared(lib, world_factory):\n"
        "    lib.om_alpha_step(0)\n"
    )
    (project / "docs" / "bible" / "epics" / "E-91-sibling.md").write_text(
        "# E-91 -- Sibling\n\n## Stories\n\n### S-950 -- Sibling story\nRules\n"
        "- R-950-01  Given a fixture, When shared runs, Then shared holds.\n"
    )
    (queue / "parked" / "600a-e91-sib-sibling_story.md.hold").write_text(
        _card_text(
            snippet_symbol="om_sib_step",
            test_file="tests/csim/test_E91_S950_sibling.py",
            card_goal="csrc/sib.c implements E91 S-950",
            epic="E-91",
            snippet_file="csrc/sib.c",
        ).replace("{PROJECT}", str(project)).replace("{VENV}", str(tmp_path / "venv"))
    )
    proc = subprocess.run(
        [sys.executable, str(CARD_REGEN), "E-90", "E-91", "--project", str(project), "--queue", str(queue), "--json"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["cross_epic"]["om_alpha_step"] == ["E-90", "E-91"]

    out = tmp_path / "out"
    proc2 = subprocess.run(
        [sys.executable, str(CARD_REGEN), "E-90", "E-91", "--project", str(project), "--queue", str(queue),
         "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    cross_text = (out / "cross_epic.md").read_text()
    assert "om_alpha_step" in cross_text
    assert "E-90" in cross_text and "E-91" in cross_text


def test_report_flags_a_card_with_no_acceptance_test_of_its_own(tmp_path):
    """Found in the real E-12/E-15 runs (S-092, S-129): when a single test's
    own closure needs more than 5 unbuilt symbols, it is assigned entirely
    to the last card that covers it, and an earlier card in the same story
    can end up with symbols but zero acceptance tests -- a real card_lint
    defect (empty acceptance), not silently patched around here."""
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "docs" / "bible" / "epics").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(HEADER)
    (project / "tests" / "csim" / "conftest.py").write_text("")
    (project / "tests" / "csim" / "test_E92_S903_wide_test.py").write_text(
        "def test_R_903_01_wide(lib, world_factory):\n"
        "    lib.om_one(0)\n"
        "    lib.om_two(0)\n"
        "    lib.om_three(0)\n"
        "    lib.om_four(0)\n"
        "    lib.om_five(0)\n"
        "    lib.om_six(0)\n"
    )
    (project / "docs" / "bible" / "epics" / "E-92-wide.md").write_text(
        "# E-92 -- Wide\n\n## Stories\n\n### S-903 -- Wide story\nRules\n"
        "- R-903-01  Given a fixture, When wide runs, Then wide holds.\n"
    )
    queue = tmp_path / "queue"
    (queue / "parked").mkdir(parents=True)
    (queue / "parked" / "700a-e92-wide-wide_test.md.hold").write_text(
        _card_text(
            snippet_symbol="om_wide_step",
            test_file="tests/csim/test_E92_S903_wide_test.py",
            card_goal="csrc/wide.c implements E92 S-903",
            epic="E-92",
            snippet_file="csrc/wide.c",
        ).replace("{PROJECT}", str(project)).replace("{VENV}", str(tmp_path / "venv"))
    )
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(CARD_REGEN), "E-92", "--project", str(project), "--queue", str(queue),
         "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads(subprocess.run(
        [sys.executable, str(CARD_REGEN), "E-92", "--project", str(project), "--queue", str(queue), "--json"],
        capture_output=True, text=True,
    ).stdout)["results"]["E-92"]
    s903 = _story(result, "S-903")
    assert len(s903["cards"]) == 2
    assert s903["cards"][0]["tests"] == []
    assert s903["cards"][1]["tests"] == ["test_R_903_01_wide"]

    report = (out / "E-92" / "report.md").read_text()
    assert "Cards with no acceptance test of their own" in report
    assert "700a1-e92-wide-wide_test" in report
