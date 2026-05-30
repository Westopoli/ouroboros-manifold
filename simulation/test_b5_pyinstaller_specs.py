"""B5-A acceptance: Windows PyInstaller spec parity with Mac spec + DebugOverlay autoload registered."""

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAC_SPEC = REPO_ROOT / "build" / "pyinstaller_spec.spec"
WIN_SPEC = REPO_ROOT / "build" / "pyinstaller_win.spec"
PROJECT_GODOT = REPO_ROOT / "project.godot"


def _parse_spec(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _extract_list_literal(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"binding {name} not found")


def _extract_collect_name(tree: ast.Module) -> str:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "COLLECT":
            for kw in node.keywords:
                if kw.arg == "name":
                    return ast.literal_eval(kw.value)
    raise AssertionError("COLLECT name not found")


def _hidden_imports(tree: ast.Module):
    return set(_extract_list_literal(tree, "hidden_imports"))


def _datas_dest_set(tree: ast.Module):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "datas":
                    assert isinstance(node.value, (ast.List, ast.Tuple))
                    dests = set()
                    for elt in node.value.elts:
                        assert isinstance(elt, ast.Tuple) and len(elt.elts) == 2
                        dest_node = elt.elts[1]
                        assert isinstance(dest_node, ast.Constant) and isinstance(dest_node.value, str)
                        dests.add(dest_node.value)
                    return dests
    raise AssertionError("datas binding not found")


def test_both_specs_parse():
    assert MAC_SPEC.exists(), f"missing Mac spec at {MAC_SPEC}"
    assert WIN_SPEC.exists(), f"missing Win spec at {WIN_SPEC}"
    _parse_spec(MAC_SPEC)
    _parse_spec(WIN_SPEC)


def test_hidden_imports_match():
    mac = _hidden_imports(_parse_spec(MAC_SPEC))
    win = _hidden_imports(_parse_spec(WIN_SPEC))
    assert mac == win, f"hidden_imports diverge: mac-only={mac - win} win-only={win - mac}"


def test_data_files_match():
    mac = _datas_dest_set(_parse_spec(MAC_SPEC))
    win = _datas_dest_set(_parse_spec(WIN_SPEC))
    assert mac == win, f"datas diverge: mac-only={mac - win} win-only={win - mac}"


def test_collect_name_ouroboros_sim():
    assert _extract_collect_name(_parse_spec(MAC_SPEC)) == "ouroboros_sim"
    assert _extract_collect_name(_parse_spec(WIN_SPEC)) == "ouroboros_sim"


def test_debug_overlay_autoload_registered():
    text = PROJECT_GODOT.read_text(encoding="utf-8")
    pattern = re.compile(r'^DebugOverlay\s*=\s*"\*res://autoload/debug_overlay\.gd"$', re.MULTILINE)
    assert pattern.search(text), "DebugOverlay autoload line missing from project.godot"
