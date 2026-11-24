"""look-judge-rig spec piece 2 (backends): ollama back end against a local fake server."""
import base64

import pytest

from conftest import check, make_png


def judge(*a, **k):
    from scripts.look.backends import judge as j
    return j(*a, **k)


def test_control_fake_server_answers(ollama, tmp_path):
    """Positive control (piece 2): the fake server is reachable and records a POST."""
    import urllib.request
    req = urllib.request.Request(ollama.url + "/api/generate", data=b"{}", method="POST",
                                 headers={"Content-Length": "2"})
    assert urllib.request.urlopen(req).status == 200
    assert len(ollama.requests) == 1


def test_posts_base64_image_in_images_field(ollama, tmp_path):
    """Piece 2: ollama back end posts HTTP with the image base64 in `images`."""
    png = make_png(tmp_path / "a.png", b"XYZ")
    ollama.reply = lambda r: "count: 0"
    out = judge(png, check("ollama"))
    body = ollama.requests[0]["body"]
    assert body["images"] == [base64.b64encode(png.read_bytes()).decode()]
    assert "prompt" in body and body["prompt"]
    assert set(out) >= {"verdict", "answer", "raw"}


def test_model_from_env_default_qwen(ollama, tmp_path):
    """Piece 2: model name from OM_LOOK_OLLAMA_MODEL, default qwen3-vl:8b."""
    png = make_png(tmp_path / "a.png")
    judge(png, check("ollama"))
    assert ollama.requests[0]["body"]["model"] == "qwen3-vl:8b"


def test_model_from_env_override(ollama, tmp_path, monkeypatch):
    """Piece 2: model name from OM_LOOK_OLLAMA_MODEL."""
    monkeypatch.setenv("OM_LOOK_OLLAMA_MODEL", "tiny:1b")
    judge(make_png(tmp_path / "a.png"), check("ollama"))
    assert ollama.requests[0]["body"]["model"] == "tiny:1b"


def test_matching_count_passes_mismatch_fails(ollama, tmp_path):
    """Piece 2: the answer is compared with the truth passed in."""
    png = make_png(tmp_path / "a.png")
    ollama.reply = lambda r: "count: 0"
    assert judge(png, check("ollama", {"count": 0}))["verdict"] == "PASS"
    ollama.reply = lambda r: "count: 2"
    assert judge(png, check("ollama", {"count": 0}, prompt="p2"))["verdict"] == "FAIL"


def test_server_down_is_not_pass(tmp_path, monkeypatch):
    """Piece 2: server down => UNSURE or FAIL, never PASS."""
    monkeypatch.setenv("OM_LOOK_OLLAMA_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("OM_LOOK_CACHE_DIR", str(tmp_path / "c"))
    out = judge(make_png(tmp_path / "a.png"), check("ollama"))
    assert out["verdict"] in ("UNSURE", "FAIL")


def test_timeout_is_not_pass(ollama, tmp_path, monkeypatch):
    """Piece 2: timeout => UNSURE or FAIL, never PASS."""
    monkeypatch.setenv("OM_LOOK_TIMEOUT", "0.3")
    ollama.delay = 2.0
    out = judge(make_png(tmp_path / "a.png"), check("ollama"))
    assert out["verdict"] in ("UNSURE", "FAIL")


def test_http_error_is_not_pass(ollama, tmp_path):
    """Piece 2: a server error => UNSURE or FAIL, never PASS."""
    ollama.status = 500
    out = judge(make_png(tmp_path / "a.png"), check("ollama"))
    assert out["verdict"] in ("UNSURE", "FAIL")
