# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7, piece LI1 (the version runner); preconditions 5 and 7 of section 1
"""LI1 controls: the lab commands `isolation_runner.py` must wrap, exercised as they are today. They are green before the runner exists and must stay green;
if one goes red, the runner's premise moved (not the runner). Each names the runner behaviour that stands on it.

C1 `git archive <then>` holds what the runner copies (csrc, Makefile, scripts, layout catalogue, situations) and the `libouroboros.so` make target exists.  (build from `git archive`)
C2 the lab's own CLI, `python -m scripts.skilllab.arena.run`, runs a catalogue layout at a seed and writes `<id>-s<seed>.fight.json` with the `result` the row copies.  (a layout run with that version's lab)
C3 the lab's situation converter turns a situation id into a layout file at `now`, and the lab at `then` refuses the same file.  (a situation id as a layout; error rows)
C4 the lab at `then` writes no per-unit `fired`; the lab at `now` does.  (`not measured at <version>`)"""
import json
import subprocess
import tarfile
import io

import pytest

import isolation_fixtures as fx

LD = "docs/northstar/research/layer_dynamics"
WRAPPED = ("csrc", "Makefile", "scripts", LD + "/catalogue", LD + "/situations")


def _run(args, cwd, timeout=1800):
    """A lab job under the memory cap, as every build and fight of this work is run."""
    cmd = ["timeout", str(timeout), "systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=3G", "-p", "MemorySwapMax=0", "--", "nice", "-n", "10", *args]
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


@pytest.fixture(scope="module")
def then_tree(tmp_path_factory):
    """`git archive` of the `then` commit, the paths the runner is to copy, extracted by hand (the way `reopen_command` in approved_scenes.toml does)."""
    dest = tmp_path_factory.mktemp("then-tree")
    data = subprocess.run(["git", "-C", str(fx.ROOT), "archive", fx.THEN_SHA, *WRAPPED], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")
    return dest


def test_c1_archive_holds_the_wrapped_paths_and_the_make_target(then_tree):
    """C1: LI1 builds a version from `git archive`: the paths are all there, and `make -n libouroboros.so` (the target the runner runs) plans a compile."""
    for rel in WRAPPED:
        assert (then_tree / rel).exists(), rel
    assert list((then_tree / "csrc").glob("*.c"))
    assert not (then_tree / ".git").exists()
    plan = _run(["make", "-n", "libouroboros.so"], then_tree)
    assert plan.returncode == 0 and "-shared" in plan.stdout and "libouroboros.so" in plan.stdout, plan.stderr


def test_c2_lab_cli_runs_a_layout_and_writes_the_fight_file(tmp_path):
    """C2 (current main's lab, run from this worktree; one real fight, about 14 s): the file name and the `result` keys the row copies. One order a side is the lab's own (precondition 7)."""
    done = _run([fx.PY, "-m", "scripts.skilllab.arena.run", "--layout", "%s/catalogue/%s.toml" % (fx.ROOT / LD, fx.LAYOUT), "--seed", str(fx.SEED), "--out", str(tmp_path)], fx.ROOT)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "FIGHT %s seed %d" % (fx.LAYOUT, fx.SEED) in done.stdout
    doc = json.loads((tmp_path / ("%s-s%d.fight.json" % (fx.LAYOUT, fx.SEED))).read_text())
    assert {"winner", "survivors", "ticks", "end"} <= set(doc["result"])
    assert doc["result"]["end"] in fx.ENDS and len(doc["result"]["survivors"]) == 2
    assert doc["seed"] == fx.SEED and doc["layout_id"] == fx.LAYOUT
    assert doc["layout_path"].startswith("docs/"), "the file names the layout relative to the tree that ran it, which is what lets two scratch trees write equal files"
    assert any("fired" in u for u in doc["frames"][1]["units"]), "the lab at now offers the per-unit `fired` flag"


def test_c3_situation_converts_at_now_and_the_lab_at_then_refuses_it(then_tree, tmp_path):
    """C3: a situation id is converted by that version's own converter into a layout file; the `then` lab rejects SIT-0106 (an error row, not a skip)."""
    cmd = ["-m", "scripts.skilllab.arena.situations", "--next-id", "L-0106"]
    src = tmp_path / "src"
    src.mkdir()
    (src / "SIT-0106-open_field.md").write_text((fx.ROOT / LD / "situations" / "SIT-0106-open_field.md").read_text())
    now = _run([fx.PY, *cmd, "--dir", str(src), "--out", str(tmp_path / "now")], fx.ROOT)
    assert now.returncode == 0 and "CONVERTED SIT-0106-open_field L-0106" in now.stdout, now.stdout + now.stderr
    assert (tmp_path / "now" / "L-0106.toml").exists()
    src_then = tmp_path / "src-then"
    src_then.mkdir()
    (src_then / "SIT-0106-open_field.md").write_text((then_tree / LD / "situations" / "SIT-0106-open_field.md").read_text())
    then = _run([fx.PY, *cmd, "--dir", str(src_then), "--out", str(tmp_path / "then")], then_tree)
    assert then.returncode == 2 and "REJECT SIT-0106-open_field arc too small" in then.stdout, then.stdout + then.stderr


def test_c4_then_lab_has_no_fired_flag_in_its_source(then_tree):
    """C4: the `then` lab's `run._frame` writes no `fired` key (added 2026-11-07, replay-firing-lines), so a units-firing summary is `not measured at then`."""
    assert '"fired"' not in (then_tree / "scripts/skilllab/arena/run.py").read_text()
    assert '"fired"' in (fx.ROOT / "scripts/skilllab/arena/run.py").read_text()

