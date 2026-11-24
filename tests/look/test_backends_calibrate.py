"""look-judge-rig spec piece 2 (backends): calibrate.py over a control set.

Assumed control-set layout: <dir>/controls.json = [{"id","check","role":"break"|"clean",
"frame":"x.png","truth":{...},"label":"PASS"|"FAIL"}]; CLI `--controls DIR --backend NAME`;
JSON report on stdout: {"false_pass": {check: n}, "agreement": float 0..1, ...}; main(argv) -> exit code.
Fake server: image bytes containing b"BREAK" are answered "count: 2" (truth 0 -> FAIL), others "count: 0".
"""
import base64
import json

import pytest

from conftest import PNG_HEAD


def build_set(root, items):
    root.mkdir(exist_ok=True)
    rows = []
    for i, (chk, role, tag) in enumerate(items):
        f = "f%d.png" % i
        (root / f).write_bytes(PNG_HEAD + tag + b"%d" % i)
        rows.append({"id": "c%d" % i, "check": chk, "role": role, "frame": f,
                     "truth": {"count": 0}, "label": "FAIL" if role == "break" else "PASS"})
    (root / "controls.json").write_text(json.dumps(rows))
    return root


def run(root, capsys, backend="ollama"):
    from scripts.look import calibrate
    try:
        code = calibrate.main(["--controls", str(root), "--backend", backend])
    except SystemExit as e:
        code = e.code
    out = capsys.readouterr().out
    return (code or 0), json.loads(out)


@pytest.fixture
def judge_by_tag(ollama):
    def reply(req):
        img = base64.b64decode(req["images"][0])
        return "count: 2" if b"BREAK" in img else "count: 0"
    ollama.reply = reply
    return ollama


def test_all_breaks_fail_and_twins_pass_exits_0(judge_by_tag, tmp_path, capsys):
    """Piece 2: exit 0 when all planted breaks FAIL and clean twins PASS."""
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK"), ("overlap", "clean", b"CLEAN"),
                                        ("wall", "break", b"BREAK"), ("wall", "clean", b"CLEAN")])
    code, rep = run(root, capsys)
    assert code == 0
    assert sum(rep["false_pass"].values()) == 0
    assert rep["agreement"] == 1.0


def test_false_pass_on_planted_break_exits_1(ollama, tmp_path, capsys):
    """Piece 2 / DRAFT-look-false-pass-max = 0: any planted-break control that gets PASS exits 1."""
    ollama.reply = lambda r: "count: 0"  # blind judge passes everything
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK"), ("overlap", "clean", b"CLEAN"),
                                        ("wall", "break", b"BREAK")])
    code, rep = run(root, capsys)
    assert code == 1
    assert rep["false_pass"]["overlap"] == 1 and rep["false_pass"]["wall"] == 1


def test_false_pass_zero_when_every_break_fails(judge_by_tag, tmp_path, capsys):
    """Piece 2: per-check false-pass report lists zero for a check whose breaks all FAIL."""
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK"), ("overlap", "break", b"BREAK")])
    code, rep = run(root, capsys)
    assert code == 0 and rep["false_pass"].get("overlap", 0) == 0


def test_agreement_with_labelled_frames(ollama, tmp_path, capsys):
    """Piece 2: reports agreement with labelled frames; a wrong call on a clean twin lowers it without a false pass."""
    ollama.reply = lambda r: "count: 2"  # fails everything: no false pass, twins wrong
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK"), ("overlap", "clean", b"CLEAN")])
    code, rep = run(root, capsys)
    assert code == 0
    assert rep["agreement"] == 0.5
    assert sum(rep["false_pass"].values()) == 0


def test_unsure_on_break_is_not_a_false_pass(ollama, tmp_path, capsys):
    """Piece 2: UNSURE counts as FAIL; a break answered with a bare yes is not a false pass."""
    ollama.reply = lambda r: "yes"
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK")])
    code, rep = run(root, capsys)
    assert code == 0 and sum(rep["false_pass"].values()) == 0


def test_server_down_never_yields_false_pass(tmp_path, monkeypatch, capsys):
    """Piece 2: a dead back end gives no PASS, so calibration reports no false pass."""
    monkeypatch.setenv("OM_LOOK_OLLAMA_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("OM_LOOK_CACHE_DIR", str(tmp_path / "c"))
    root = build_set(tmp_path / "set", [("overlap", "break", b"BREAK")])
    code, rep = run(root, capsys)
    assert code == 0 and sum(rep["false_pass"].values()) == 0
