# spec: piece HARNESS-gdreach -- scripts/specfactory/gd_reach_lint.py and the merge_gate.sh stage "gd_reach".
"""Tests for the Godot reachability lint. RED today because scripts/specfactory/gd_reach_lint.py does not exist.

CLI contract (the builder implements it): gd_reach_lint.py --ref R --base-ref B --project DIR [--stubs FILE]
(stubs default scripts/specfactory/gd_reach_stubs.txt). Exit 1 = REJECT, 0 = ok or warn. Output lines:
'NEW UNREACHABLE <path>' (reject: unreachable at ref and not at base, or added in the diff),
'UNREACHABLE <path>' (warn: full list of the rest), 'GD REACH LINT OK ...' / 'GD REACH LINT FAILED ...'.
Paths are res-relative (scenes/x/y.gd). Roots: project.godot run/main_scene plus every [autoload] entry."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LINT = REPO / "scripts" / "specfactory" / "gd_reach_lint.py"


def _git(d, *a):
    return subprocess.run(["git", "-C", str(d), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                          capture_output=True, text=True, check=True).stdout.strip()


def _w(d, rel, text):
    p = Path(d) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _project(d):
    """All-reached project: main scene -> script, autoload, preload chain, class_name use, tscn ext_resource."""
    _w(d, "project.godot", 'config_version=5\n[application]\nrun/main_scene="res://scenes/main/main.tscn"\n'
       '[autoload]\nBus="*res://autoload/bus.gd"\n')
    _w(d, "scenes/main/main.tscn", '[gd_scene load_steps=3 format=3]\n'
       '[ext_resource type="Script" path="res://scenes/main/main.gd" id="1"]\n'
       '[ext_resource type="PackedScene" path="res://scenes/main/child.tscn" id="2"]\n[node name="M" type="Node"]\nscript = ExtResource("1")\n')
    _w(d, "scenes/main/child.tscn", '[gd_scene format=3]\n[ext_resource type="Script" path="res://scenes/main/child.gd" id="1"]\n'
       '[node name="C" type="Node"]\nscript = ExtResource("1")\n')
    _w(d, "scenes/main/child.gd", "extends Node\n")
    _w(d, "scenes/main/main.gd", 'extends Node\nconst Chain = preload("res://scenes/main/chain_a.gd")\n'
       'func _ready():\n\tvar h: Helper = Helper.new()\n')
    _w(d, "scenes/main/chain_a.gd", 'extends Node\nvar b = load("res://scenes/main/chain_b.gd")\n')
    _w(d, "scenes/main/chain_b.gd", 'extends "res://scenes/main/chain_c.gd"\n')
    _w(d, "scenes/main/chain_c.gd", "extends Node\n")
    _w(d, "scenes/main/helper.gd", "class_name Helper\nextends RefCounted\n")
    _w(d, "autoload/bus.gd", "extends Node\n")
    _w(d, "scripts/specfactory/gd_reach_stubs.txt", "# none\n")


def _repo(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    _git(d, "init", "-q", "-b", "main")
    _project(d)
    _git(d, "add", "-A")
    _git(d, "commit", "-qm", "base")
    return d, _git(d, "rev-parse", "HEAD")


def _commit(d, msg="c"):
    _git(d, "add", "-A")
    _git(d, "commit", "-qm", msg)


def _run(d, base, stubs=None):
    cmd = [sys.executable, str(LINT), "--ref", "HEAD", "--base-ref", base, "--project", str(d)]
    if stubs:
        cmd += ["--stubs", str(stubs)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def test_all_reached_is_ok(tmp_path):
    """HARNESS-gdreach: red because gd_reach_lint.py does not exist yet."""
    d, base = _repo(tmp_path)
    rc, out = _run(d, base)
    assert rc == 0, out
    assert "UNREACHABLE" not in out.replace("GD REACH LINT", "")


def test_new_orphan_rejects_naming_file(tmp_path):
    """HARNESS-gdreach: red because gd_reach_lint.py does not exist yet."""
    d, base = _repo(tmp_path)
    _w(d, "scenes/main/orphan.gd", "extends Node\n")
    _commit(d)
    rc, out = _run(d, base)
    assert rc != 0
    assert "NEW UNREACHABLE scenes/main/orphan.gd" in out


def test_orphan_in_stubs_file_only_warns(tmp_path):
    """HARNESS-gdreach: red because gd_reach_lint.py does not exist yet."""
    d, base = _repo(tmp_path)
    _w(d, "scenes/main/orphan.gd", "extends Node\n")
    stubs = d / "scripts/specfactory/gd_reach_stubs.txt"
    stubs.write_text("# declared stubs\nscenes/main/orphan.gd\n")
    _commit(d)
    rc, out = _run(d, base)
    assert rc == 0, out
    assert "NEW UNREACHABLE" not in out


def test_orphan_present_at_base_warns_not_rejects(tmp_path):
    """HARNESS-gdreach: red because gd_reach_lint.py does not exist yet."""
    d, base0 = _repo(tmp_path)
    _w(d, "scenes/main/old_orphan.gd", "extends Node\n")
    _commit(d, "orphan lands")
    base = _git(d, "rev-parse", "HEAD")
    _w(d, "scenes/main/child.gd", "extends Node\n# touched\n")
    _commit(d, "unrelated change")
    rc, out = _run(d, base)
    assert rc == 0, out
    assert "UNREACHABLE scenes/main/old_orphan.gd" in out
    assert "NEW UNREACHABLE" not in out


def test_class_name_type_annotation_counts_as_reached(tmp_path):
    """HARNESS-gdreach: red because gd_reach_lint.py does not exist yet. helper.gd is reached only via class_name Helper
    (a type annotation and .new() in main.gd), never by path."""
    d, base = _repo(tmp_path)
    _w(d, "scenes/main/main.gd", 'extends Node\nconst Chain = preload("res://scenes/main/chain_a.gd")\nfunc _ready():\n\tvar h: Helper = null\n')
    _commit(d)
    rc, out = _run(d, base)
    assert rc == 0, out
    assert "helper.gd" not in out
    # and dropping the only use makes it an orphan
    _w(d, "scenes/main/main.gd", "extends Node\n")
    _commit(d, "drop use")
    rc, out = _run(d, base)
    assert rc != 0 and "scenes/main/helper.gd" in out


def test_positive_control_planted_orphan_detected(tmp_path):
    """HARNESS-gdreach positive control: red because gd_reach_lint.py does not exist yet. A planted orphan under
    autoload/ in the base itself is listed (warn) -- the detector sees it."""
    d, base = _repo(tmp_path)
    _w(d, "autoload/planted.gd", "extends Node\n")
    _commit(d)
    base2 = _git(d, "rev-parse", "HEAD")
    rc, out = _run(d, base2)
    assert rc == 0 and "UNREACHABLE autoload/planted.gd" in out


def test_real_repo_lists_ground_units_and_slope_view():
    """HARNESS-gdreach: real-repo positive proof. At main 1398ba16 these two files were unreachable; VG-C-wire attaches
    them to Ground3D, so at HEAD they must NOT be in the lint's unreachable list. TD-HARNESS-gdreach-2."""
    p = subprocess.run([sys.executable, str(LINT), "--ref", "HEAD", "--base-ref", "HEAD", "--project", str(REPO)],
                       capture_output=True, text=True)
    out = p.stdout
    assert p.returncode == 0, out + p.stderr
    for f in ("scenes/ground3d/ground_units.gd", "scenes/ground3d/slope_view.gd"):
        assert f"UNREACHABLE {f}" not in out