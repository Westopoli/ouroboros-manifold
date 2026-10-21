# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md ruling 13; docs/northstar/plans/2026-10-01-architect-rulings-2.md A98 Addendum 34
"""Tests for pieces row HARNESS-lab-slow-tier: the merge gate's scale-gated mechanism gains a
second tier. A skipped test whose node id is under tests/skilllab/ and whose skip reason contains
"OM_LAB_SLOW" (the lab's SLOW marker, ruling 13 of the skill-lab rev 2 spec) is counted on the
"scale-gated: N" line, not as a skip, provided its id is listed in
docs/northstar/plans/push/scale_gated_tests.txt (mgs.SCALE_LIST_REL, read from the candidate tree).
An unlisted id, a lab skip with another reason, and an OM_LAB_SLOW reason outside tests/skilllab/
still count as skips. The csim tier (tests/csim/scale/, OM_SCALE; A98 Addendum 34) is unchanged.

See also: tests/specfactory/test_merge_gate_support.py (the csim-tier tests this file mirrors;
that file is not edited here), scripts/specfactory/suite_regression.py is_scale_gated.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402
import suite_regression as sr  # noqa: E402

PYTHON = sr.DEFAULT_PYTHON
GOOD_TEST = "def test_a():\n    assert 1 == 1\n"

# All 19 SLOW (OM_LAB_SLOW) ids under tests/skilllab of the lab landing tree (origin/push/labrev2-landLab 46fb4e17),
# read by a collection-only pass with OM_LAB_SLOW unset: the 15 of tests/skilllab/integration (the only ones the gate's lab
# stage collects), then 4 in the tests/skilllab top-level files. Architect 2026-10-20: the list is the inventory of the slow tier.
LAB_SLOW_IDS = (
    "tests/skilllab/integration/test_attackmove_idle_cap_real.py::test_E1b_layout_192_lone_attacker_scene_ends_by_elimination_not_by_the_cap",
    "tests/skilllab/integration/test_attackmove_idle_cap_real.py::test_control_the_same_scene_with_the_attacker_killed_before_it_fires_ends_by_elimination",
    "tests/skilllab/integration/test_attackmove_idle_cap_real.py::test_the_traced_scene_is_the_one_that_capped",
    "tests/skilllab/integration/test_baselines_real.py::test_e_the_sweep_over_the_real_builds_on_layout_192_reaches_48_with_nothing_refused_or_cut",
    "tests/skilllab/integration/test_blind_post_real.py::test_the_real_shift_and_the_real_refusal",
    "tests/skilllab/integration/test_reengage_real.py::test_per_unit_orders_on_the_same_scene_are_untouched_by_the_counts_field",
    "tests/skilllab/integration/test_reengage_real.py::test_the_capped_group_order_fights_end_by_elimination[mirror control, swapped (caps with 1 v 1 alive today)-_group_orders_mirror-True]",
    "tests/skilllab/integration/test_reengage_real.py::test_the_capped_group_order_fights_end_by_elimination[objective scene, unswapped (caps with 1 v 2 alive today)-_group_orders_objective-False]",
    "tests/skilllab/integration/test_reengage_real.py::test_the_elimination_came_through_a_reengage[_group_orders_mirror-True]",
    "tests/skilllab/integration/test_reengage_real.py::test_the_elimination_came_through_a_reengage[_group_orders_objective-False]",
    "tests/skilllab/integration/test_speed.py::test_play_scan_8_to_48_at_3_replicates_finishes_under_90_seconds_at_12_workers",
    "tests/skilllab/integration/test_sweep_real.py::test_smoke_rows_are_the_same_bytes_at_1_and_12_workers_and_every_fight_ends_clean",
    "tests/skilllab/integration/test_sweep_real.py::test_the_sweep_command_writes_the_family_csv_and_the_summary",
    "tests/skilllab/integration/test_workers_hash.py::test_real_smoke_rows_hash_identically_at_1_and_12_workers",
    "tests/skilllab/integration/test_workers_hash.py::test_real_sweep_family_rows_are_the_same_bytes_at_1_and_12_workers",
    "tests/skilllab/test_depth.py::test_real_smoke_two_layouts_one_replicate_four_workers",
    "tests/skilllab/test_diagram.py::test_real_agreement_values_are_all_known_and_a_real_both_wrong_would_be_listed",
    "tests/skilllab/test_diagram.py::test_real_fight_rows_and_a_real_placed_scene_make_a_consistent_both_wrong_diagram",
    "tests/skilllab/test_main_artifact.py::test_artifact_command_with_the_real_placed_scene_draws_every_real_unit",
)


def _read_list(text: str) -> set[str]:
    return {ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


# ------------------------------------------------ gate fixtures (pattern of test_merge_gate_support) --

def _skip_test(reason: str) -> str:
    return ("import os\nimport pytest\n"
            f"SLOW = pytest.mark.skipif(os.environ.get('OM_LAB_SLOW') != '1', reason={reason!r})\n"
            "@SLOW\ndef test_real():\n    assert 1 == 2\n")


LAB_SLOW_REASON = "real fights; set OM_LAB_SLOW=1"
LAB_ID = "tests/skilllab/test_slow_synth.py::test_real"
CSIM_SCALE_REASON = "scale suite gated behind OM_SCALE=1"
CSIM_ID = "tests/csim/scale/test_scale_synth.py::test_real"


def _candidate(tmp_path, monkeypatch, *, files, list_text=None):
    """Base = one passing test; the candidate adds `files` {relpath: text} and optionally the list
    file. Returns (ok, detail, report) of mgs.regression_check."""
    monkeypatch.delenv("OM_LAB_SLOW", raising=False)
    monkeypatch.delenv("OM_SCALE", raising=False)
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "test_base.py").write_text(GOOD_TEST)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    allfiles = dict(files)
    if list_text is not None:
        allfiles[mgs.SCALE_LIST_REL] = list_text
    for rel, text in allfiles.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")
    return mgs.regression_check(repo, base_sha, ["."], python_exe=PYTHON, worktree_root=tmp_path)


def test_lab_slow_skip_listed_is_counted_scale_gated_not_a_skip(tmp_path, monkeypatch):
    """Fixture A. HARNESS-lab-slow-tier, ruling 13: a tests/skilllab skip naming OM_LAB_SLOW and
    listed is counted on the "scale-gated: N" line, not in skipped."""
    ok, detail, report = _candidate(
        tmp_path, monkeypatch, files={"tests/skilllab/test_slow_synth.py": _skip_test(LAB_SLOW_REASON)},
        list_text=f"# lab slow tier\n{LAB_ID}\n")
    assert ok is True, detail
    assert report.skipped_increase == 0
    assert list(report.after.scale_gated) == [LAB_ID]
    assert "scale-gated: 1" in detail


def test_lab_slow_skip_listed_and_a_csim_scale_skip_make_one_count_of_two(tmp_path, monkeypatch):
    """HARNESS-lab-slow-tier: both tiers share the one "scale-gated: N" line."""
    ok, detail, report = _candidate(
        tmp_path, monkeypatch,
        files={"tests/skilllab/test_slow_synth.py": _skip_test(LAB_SLOW_REASON),
               "tests/csim/scale/test_scale_synth.py": _skip_test(CSIM_SCALE_REASON)},
        list_text=f"{LAB_ID}\n{CSIM_ID}\n")
    assert ok is True, detail
    assert report.skipped_increase == 0
    assert list(report.after.scale_gated) == sorted([LAB_ID, CSIM_ID])
    assert "scale-gated: 2" in detail


@pytest.mark.parametrize("reason", ["needs the pipe binary", "gated behind OM_SCALE=1"])
def test_positive_control_lab_skip_with_another_reason_is_still_a_skip(tmp_path, monkeypatch, reason):
    """Fixture B (control). A tests/skilllab skip whose reason does not name OM_LAB_SLOW is an
    ordinary skip even when its id is listed."""
    ok, detail, report = _candidate(
        tmp_path, monkeypatch, files={"tests/skilllab/test_slow_synth.py": _skip_test(reason)},
        list_text=f"{LAB_ID}\n")
    assert ok is False
    assert report.skipped_increase == 1
    assert "skipped +1" in detail
    assert list(report.after.scale_gated) == []


def test_positive_control_lab_slow_skip_not_in_the_list_is_rejected_like_the_csim_tier(tmp_path, monkeypatch):
    """Fixture C. HARNESS-lab-slow-tier mirrors the csim tier exactly: is_scale_gated and the junit
    parsers do not see the list, so an unlisted OM_LAB_SLOW lab skip is still counted as scale-gated
    (skipped_increase == 0, its id in scale_gated) and regression_check rejects it through the
    "scale-gated tests missing from <list>" branch (merge_gate_support.py:732,755). Assertions copied
    from the csim pin tests/specfactory/test_merge_gate_support.py:918-922
    (test_positive_control_scale_test_missing_from_list_rejected)."""
    ok, detail, report = _candidate(
        tmp_path, monkeypatch, files={"tests/skilllab/test_slow_synth.py": _skip_test(LAB_SLOW_REASON)},
        list_text="# nothing listed\n")
    assert ok is False
    assert LAB_ID in detail and "scale" in detail
    assert "scale-gated tests missing from" in detail
    assert report.skipped_increase == 0  # counted on its own line, not as a skip
    assert list(report.after.scale_gated) == [LAB_ID]


@pytest.mark.parametrize("dirname", ["skilllabx", "skilllab_other"])
def test_positive_control_lab_slow_reason_under_a_prefix_lookalike_dir_is_an_ordinary_skip(tmp_path, monkeypatch, dirname):
    """Prefix control. Only the directory tests/skilllab/ is the lab tier: a skip under tests/skilllabx/
    or tests/skilllab_other/ with an OM_LAB_SLOW reason, even listed, still counts as a skip."""
    rel = f"tests/{dirname}/test_slow_synth.py"
    ok, detail, report = _candidate(
        tmp_path, monkeypatch, files={rel: _skip_test(LAB_SLOW_REASON)}, list_text=f"{rel}::test_real\n")
    assert ok is False
    assert report.skipped_increase == 1
    assert "skipped +1" in detail
    assert list(report.after.scale_gated) == []


def test_positive_control_csim_scale_tier_unchanged(tmp_path, monkeypatch):
    """Fixture D (control, green before and after). The csim tier: a tests/csim/scale skip naming
    OM_SCALE and listed is scale-gated, as before the piece."""
    ok, detail, report = _candidate(
        tmp_path, monkeypatch, files={"tests/csim/scale/test_scale_synth.py": _skip_test(CSIM_SCALE_REASON)},
        list_text=f"{CSIM_ID}\n")
    assert ok is True, detail
    assert report.skipped_increase == 0
    assert list(report.after.scale_gated) == [CSIM_ID]
    assert "scale-gated: 1" in detail


def test_positive_control_lab_slow_reason_outside_skilllab_is_an_ordinary_skip(tmp_path, monkeypatch):
    """Fixture E (control). Naming OM_LAB_SLOW in a skip reason outside tests/skilllab/ (here
    tests/csim/ and tests/csim/scale/, where only OM_SCALE counts) is not a way around the skip
    count, listed or not."""
    elsewhere = "tests/csim/test_elsewhere.py::test_real"
    scale_dir = "tests/csim/scale/test_scale_synth.py::test_real"
    ok, detail, report = _candidate(
        tmp_path, monkeypatch,
        files={"tests/csim/test_elsewhere.py": _skip_test(LAB_SLOW_REASON),
               "tests/csim/scale/test_scale_synth.py": _skip_test(LAB_SLOW_REASON)},
        list_text=f"{elsewhere}\n{scale_dir}\n")
    assert ok is False
    assert report.skipped_increase == 2
    assert list(report.after.scale_gated) == []


# ----------------------------------------------- the lab tier's ids against the list file --

SLOW_PLUGIN = '''\
import os


def pytest_collection_modifyitems(config, items):
    """Print SLOWID <nodeid> for every item a skip/skipif marker whose condition is true and whose
    reason names OM_LAB_SLOW would skip (the SLOW marker of tests/skilllab)."""
    for item in items:
        for m in item.iter_markers():
            if m.name not in ("skip", "skipif"):
                continue
            cond = True
            if m.name == "skipif":
                cond = m.args[0] if m.args else m.kwargs.get("condition", True)
                if isinstance(cond, str):
                    cond = bool(eval(cond, {"os": os}))
            reason = m.kwargs.get("reason") or (m.args[0] if m.name == "skip" and m.args else "")
            if cond and "OM_LAB_SLOW" in reason:
                print("SLOWID " + item.nodeid)
                break
'''


def collect_lab_slow_ids(root: Path, scratch: Path) -> set[str]:
    """Node ids under <root>/tests/skilllab that a skip marker naming OM_LAB_SLOW skips with
    OM_LAB_SLOW unset. Collection only: no test body runs."""
    plug = scratch / "plug"
    plug.mkdir(parents=True, exist_ok=True)
    (plug / "slowcollect_plugin.py").write_text(SLOW_PLUGIN)
    env = {k: v for k, v in os.environ.items() if k != "OM_LAB_SLOW"}
    env["PYTHONPATH"] = str(plug)
    try:
        proc = subprocess.run([PYTHON, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
                               "-p", "slowcollect_plugin", "tests/skilllab"],
                              cwd=root, env=env, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"collection of {root}/tests/skilllab timed out after {exc.timeout}s")
    if proc.returncode != 0 or proc.stderr.strip():
        pytest.fail(f"collection of {root}/tests/skilllab failed (rc {proc.returncode}):\n"
                    f"{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")
    return {ln[len("SLOWID "):].strip() for ln in proc.stdout.splitlines() if ln.startswith("SLOWID ")}


def unlisted(found: set[str], list_text: str) -> set[str]:
    return found - _read_list(list_text)


SYNTH_SLOW = ("import os\nimport pytest\n"
              "SLOW = pytest.mark.skipif(os.environ.get('OM_LAB_SLOW') != '1', reason='real fights; set OM_LAB_SLOW=1')\n"
              "@SLOW\ndef test_real():\n    assert 1 == 2\n"
              "@pytest.mark.skip(reason='needs the pipe binary')\ndef test_other():\n    pass\n"
              "def test_fast():\n    assert 1 == 1\n")


def test_positive_control_collector_finds_a_slow_marked_test_and_the_list_check_detects_it(tmp_path):
    """HARNESS-lab-slow-tier detector control: a synthetic tests/skilllab tree with one SLOW test, one
    other-reason skip and one plain test. The collector names only the SLOW one; listed -> nothing
    missing, unlisted -> detected."""
    sk = tmp_path / "tree" / "tests" / "skilllab"
    sk.mkdir(parents=True)
    (sk / "test_x.py").write_text(SYNTH_SLOW)
    found = collect_lab_slow_ids(tmp_path / "tree", tmp_path)
    sid = "tests/skilllab/test_x.py::test_real"
    assert found == {sid}
    assert unlisted(found, f"# header\n{sid}\n") == set()
    assert unlisted(found, "# header\n") == {sid}


def test_real_repo_lab_list_names_every_lab_slow_test_present_today(tmp_path):
    """HARNESS-lab-slow-tier, mirror of test_real_repo_scale_list_names_every_scale_gated_test_present_today
    for the lab tier: every test under tests/skilllab skipped for OM_LAB_SLOW (OM_LAB_SLOW unset) is
    named in scale_gated_tests.txt. Vacuous on a tree without SLOW tests; the lab landing carries them."""
    found = collect_lab_slow_ids(REPO, tmp_path)
    assert unlisted(found, (REPO / mgs.SCALE_LIST_REL).read_text()) == set()


def test_list_names_all_19_lab_slow_ids():
    """HARNESS-lab-slow-tier, Architect 2026-10-20 option (a): ALL SLOW (OM_LAB_SLOW) ids under tests/skilllab
    are listed in scale_gated_tests.txt. The gate's lab stage collects tests/skilllab/integration and
    ground only, so 15 of the 19 are the skips a landing shows; the list is the inventory of the slow
    tier. Red until the builder adds them (ids missing from the list)."""
    assert len(LAB_SLOW_IDS) == 19 and len(set(LAB_SLOW_IDS)) == 19
    assert sum("/integration/" in i for i in LAB_SLOW_IDS) == 15
    listed = _read_list((REPO / mgs.SCALE_LIST_REL).read_text())
    missing = sorted(set(LAB_SLOW_IDS) - listed)
    assert missing == [], f"ids missing from scale_gated_tests.txt: {len(missing)} of 19"


def test_positive_control_csim_ids_are_still_listed():
    """Control (green): adding the lab tier removes no csim scale id from the list."""
    listed = _read_list((REPO / mgs.SCALE_LIST_REL).read_text())
    assert len([i for i in listed if i.startswith("tests/csim/scale/")]) >= 50


def test_list_header_comment_names_both_tiers():
    """HARNESS-lab-slow-tier: the header comment of scale_gated_tests.txt (the whole leading block of
    # lines, blank lines allowed between them, up to the first other line) names the csim tier
    (tests/csim/scale, OM_SCALE) and the lab tier (tests/skilllab, OM_LAB_SLOW) and says the list is
    the inventory of every SLOW test."""
    header = []
    for ln in (REPO / mgs.SCALE_LIST_REL).read_text().splitlines():
        if ln.strip() == "":
            continue
        if not ln.lstrip().startswith("#"):
            break
        header.append(ln.lstrip().lstrip("#").strip())
    text = " ".join(" ".join(header).split())  # a sentence may wrap across comment lines
    sentence = "every tests/skilllab test marked SLOW (OM_LAB_SLOW), whether or not the gate's lab stage collects it today"
    missing = [x for x in ("tests/csim/scale", "OM_SCALE", "tests/skilllab", "OM_LAB_SLOW", sentence) if x not in text]
    assert missing == [], f"header comment does not name: {missing}"
