# Rule pins: none (harness piece SHOWCASE-legacy-toys: no S- or R- id; spec docs/northstar/plans/showcase/README.md, paragraph "SHOWCASE-legacy-toys")
"""SHOWCASE-legacy-toys: toys/ moved to legacy/toys/ and its layerlab Makefile still builds the .so inside the folder.

UNSTATED INTERFACE CHOICES:
- "builds its .so" is read as plain `make` run with cwd = the layerlab folder producing build/liblayerlab.so (the
  Makefile's `all` target copy of O2). The build runs in a temp copy of the folder so the repo tree stays clean.
- The temp copy is placed at <tmp>/layerlab (the Makefile uses only relative paths, no parent-folder assumptions).
- "The old path is gone" is read as toys/layerlab not existing in the checked-out tree (toys/ itself is not asserted).
Positive control: the build helper is also run on a minimal one-file Makefile project, which must produce its target,
so a failing build of layerlab cannot come from a broken subprocess call."""
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
NEW = REPO / "legacy" / "toys" / "layerlab"
OLD = REPO / "toys" / "layerlab"


def _build(src: Path, tmp: Path, target: str) -> Path:
    dst = tmp / "layerlab"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("build"))
    run = subprocess.run(["make", "-j4"], cwd=dst, capture_output=True, text=True, timeout=110)
    assert run.returncode == 0, f"make in {src} failed: {run.stderr[-400:]}"
    return dst / target


def test_build_helper_positive_control(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "Makefile").write_text("all:\n\tmkdir -p build\n\ttouch build/out.so\n")
    assert _build(src, tmp_path / "w", "build/out.so").exists()


def test_layerlab_builds_its_so_from_the_new_folder(tmp_path):
    assert NEW.is_dir(), f"{NEW} does not exist (git mv toys legacy/toys not done)"
    so = _build(NEW, tmp_path, "build/liblayerlab.so")
    assert so.exists(), "make succeeded but build/liblayerlab.so is missing"


def test_old_toys_layerlab_path_is_gone():
    assert not OLD.exists(), f"{OLD} still exists"
