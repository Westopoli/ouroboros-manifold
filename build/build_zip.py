"""Stage 13 build pipeline.

One command: `python build/build_zip.py`. Runs PyInstaller on the sim, runs
Godot headless export of the Windows release preset, assembles the folder
structure documented in `docs/stage_specs/stage_13_spec.md`, and produces the
final ZIP.

This is a developer tool. Linear, no error recovery beyond printing what
failed and exiting non-zero. Iterate during Stage 13 Checkpoint E.

Prerequisites (manual, one-time):
- Godot 4.x export templates installed for Windows.
- A Godot export preset named `Windows Release` (or override via
  --godot-preset). The preset must include the custom feature tag
  `release_build` so `OS.has_feature("release_build")` flips
  `IS_RELEASE_BUILD` to true.
- PyInstaller installed in the Python environment running this script.

Outputs to build/_dist/ by default. Final ZIP at build/_dist/OuroborosManifold-vX.Y.Z.zip.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = BUILD_DIR / "_dist"
PYI_WORK = BUILD_DIR / "_pyi_work"
PYI_DIST = BUILD_DIR / "_pyi_dist"
SPEC_FILE = BUILD_DIR / "pyinstaller_spec.spec"

DEFAULT_VERSION = "0.13.0"
DEFAULT_GODOT_PRESET = "Windows Release"
DEFAULT_GAME_NAME = "OuroborosManifold"


def _step(msg: str) -> float:
    print(f"\n[build] {msg}")
    return time.perf_counter()


def _done(msg: str, t0: float) -> None:
    dt = time.perf_counter() - t0
    print(f"[build] {msg} ({dt:.1f}s)")


def _run(cmd: list[str], **kw) -> None:
    print(f"[build]   $ {' '.join(cmd)}")
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"[build] command failed (exit {r.returncode}): {' '.join(cmd)}")


def run_pyinstaller() -> Path:
    t0 = _step("PyInstaller — freezing the sim")
    PYI_WORK.mkdir(parents=True, exist_ok=True)
    PYI_DIST.mkdir(parents=True, exist_ok=True)
    _run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--workpath", str(PYI_WORK),
        "--distpath", str(PYI_DIST),
        str(SPEC_FILE),
    ])
    sim_dir = PYI_DIST / "ouroboros_sim"
    if not sim_dir.exists():
        sys.exit(f"[build] expected PyInstaller output at {sim_dir} — not found")
    _done("PyInstaller done", t0)
    return sim_dir


def run_godot_export(godot_bin: str, preset: str, out_dir: Path, game_name: str) -> tuple[Path, Path]:
    t0 = _step(f"Godot — exporting preset {preset!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_exe = out_dir / f"{game_name}.exe"
    _run([
        godot_bin,
        "--headless",
        "--path", str(PROJECT_ROOT),
        "--export-release", preset, str(out_exe),
    ])
    out_pck = out_dir / f"{game_name}.pck"
    if not out_exe.exists():
        sys.exit(f"[build] Godot did not produce {out_exe}")
    _done("Godot export done", t0)
    return out_exe, out_pck


def assemble_folder(sim_dir: Path, exe: Path, pck: Path, game_name: str) -> Path:
    t0 = _step("Assembling output folder")
    out = DIST_DIR / game_name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(sim_dir, out / "sim")
    shutil.copy2(exe, out / exe.name)
    if pck.exists():
        shutil.copy2(pck, out / pck.name)
    readme_src = BUILD_DIR / "README.txt"
    fb_src = BUILD_DIR / "feedback.txt"
    if readme_src.exists():
        shutil.copy2(readme_src, out / "README.txt")
    if fb_src.exists():
        shutil.copy2(fb_src, out / "feedback.txt")
    (out / "data").mkdir(exist_ok=True)
    _done(f"Assembled at {out}", t0)
    return out


def make_zip(folder: Path, version: str, game_name: str) -> Path:
    t0 = _step("Creating ZIP")
    zip_path = DIST_DIR / f"{game_name}-v{version}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, _dirs, files in os.walk(folder):
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(folder.parent)
                zf.write(full, rel)
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    _done(f"ZIP created: {zip_path} ({size_mb:.1f} MB)", t0)
    return zip_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Stage 13 friends-ZIP build pipeline")
    ap.add_argument("--version", default=DEFAULT_VERSION)
    ap.add_argument("--game-name", default=DEFAULT_GAME_NAME)
    ap.add_argument("--godot", default=os.environ.get("GODOT_BIN", "godot"))
    ap.add_argument("--godot-preset", default=DEFAULT_GODOT_PRESET)
    ap.add_argument("--skip-pyinstaller", action="store_true")
    ap.add_argument("--skip-godot", action="store_true")
    args = ap.parse_args()

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    if args.skip_pyinstaller:
        sim_dir = PYI_DIST / "ouroboros_sim"
        if not sim_dir.exists():
            sys.exit("[build] --skip-pyinstaller set but no prior PyInstaller output found")
    else:
        sim_dir = run_pyinstaller()

    godot_out = BUILD_DIR / "_godot_out"
    if args.skip_godot:
        exe = godot_out / f"{args.game_name}.exe"
        pck = godot_out / f"{args.game_name}.pck"
        if not exe.exists():
            sys.exit("[build] --skip-godot set but no prior Godot export found")
    else:
        exe, pck = run_godot_export(args.godot, args.godot_preset, godot_out, args.game_name)

    folder = assemble_folder(sim_dir, exe, pck, args.game_name)
    zip_path = make_zip(folder, args.version, args.game_name)
    print(f"\n[build] done: {zip_path}")


if __name__ == "__main__":
    main()
