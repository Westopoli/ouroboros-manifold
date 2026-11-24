"""look-judge-rig spec piece 2 (backends): claude back end via a fake `claude` first on PATH."""
from conftest import check, make_png


def judge(*a, **k):
    from scripts.look.backends import judge as j
    return j(*a, **k)


def test_control_fake_claude_runs(claude):
    """Positive control (piece 2): the fake claude is found first on PATH and runs."""
    import shutil, subprocess
    assert shutil.which("claude") == str(claude.bin / "claude")
    claude.say("count: 0")
    r = subprocess.run(["claude", "-p"], input="", capture_output=True, text=True)
    assert r.stdout == "count: 0" and len(claude.calls()) == 1


def test_invokes_claude_headless_with_the_image(claude, tmp_path):
    """Piece 2: headless `claude -p`; the image reaches the process."""
    png = make_png(tmp_path / "crop.png")
    claude.say("count: 0")
    out = judge(png, check("claude"))
    calls = claude.calls()
    assert len(calls) == 1
    assert "-p" in calls[0]["argv"] or "--print" in calls[0]["argv"]
    assert str(png) in " ".join(calls[0]["argv"]) + calls[0]["stdin"]
    assert out["verdict"] == "PASS" and "count" in out["raw"]


def test_one_image_per_call_fresh_process_per_call(claude, tmp_path):
    """Piece 2: one image per call, fresh process per call (no session reuse)."""
    a, b = make_png(tmp_path / "a.png", b"A"), make_png(tmp_path / "b.png", b"B")
    claude.say("count: 0")
    judge(a, check("claude"))
    judge(b, check("claude"))
    calls = claude.calls()
    assert len(calls) == 2
    assert calls[0]["pid"] != calls[1]["pid"]
    for c, p in zip(calls, (a, b)):
        text = " ".join(c["argv"]) + c["stdin"]
        assert str(p) in text
        assert text.count(".png") == 1
        assert "--resume" not in c["argv"] and "--continue" not in c["argv"]


def test_nonzero_exit_is_not_pass(claude, tmp_path):
    """Piece 2: nonzero exit => UNSURE or FAIL, never PASS (stdout would have matched)."""
    claude.say("count: 0", mode="fail")
    assert judge(make_png(tmp_path / "a.png"), check("claude"))["verdict"] in ("UNSURE", "FAIL")


def test_timeout_is_not_pass(claude, tmp_path, monkeypatch):
    """Piece 2: timeout => UNSURE or FAIL, never PASS."""
    monkeypatch.setenv("OM_LOOK_TIMEOUT", "0.5")
    claude.say("count: 0", mode="sleep")
    assert judge(make_png(tmp_path / "a.png"), check("claude"))["verdict"] in ("UNSURE", "FAIL")


def test_missing_claude_binary_is_not_pass(tmp_path, monkeypatch):
    """Piece 2: no claude on PATH => UNSURE or FAIL, never PASS."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("OM_LOOK_CACHE_DIR", str(tmp_path / "c"))
    assert judge(make_png(tmp_path / "a.png"), check("claude"))["verdict"] in ("UNSURE", "FAIL")
