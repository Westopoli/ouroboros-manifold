"""Look judge back ends (look-judge-rig piece 2). judge(crop_png, check) -> {"verdict", "answer", "raw"}.

Fails closed: any error, timeout or unparseable answer is UNSURE, never PASS. Only successful
back-end replies are cached (key: frame hash + prompt hash + back-end id), never failures.
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

FORMAT_HINT = ("\nAnswer with exactly one line: 'class: <name>', 'count: <integer>' "
               "or 'coordinates: (x,y) (x,y)'.")


def _timeout():
    try:
        return float(os.environ.get("OM_LOOK_TIMEOUT", "120"))
    except ValueError:
        return 120.0


def _ask_ollama(png, prompt, model):
    url = os.environ.get("OM_LOOK_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "images": [base64.b64encode(Path(png).read_bytes()).decode()]}).encode()
    req = urllib.request.Request(url + "/api/generate", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=_timeout()) as r:
        return json.loads(r.read())["response"]


def _ask_claude(png, prompt):
    r = subprocess.run(["claude", "-p", "--allowedTools", "Read", "%s\nImage file: %s" % (prompt, png)],
                       input="", capture_output=True, text=True, timeout=_timeout(), check=True)
    return r.stdout


def parse(text):
    """Return ("class", str) | ("count", int) | ("coordinates", [[x, y], ...]) | None."""
    t = text.strip()
    m = re.fullmatch(r"class:\s*(\S+)", t, re.I)
    if m:
        return "class", m.group(1).strip(".,").lower()
    m = re.fullmatch(r"count:\s*(-?\d+)", t, re.I)
    if m:
        return "count", int(m.group(1))
    m = re.fullmatch(r"coordinates:\s*((?:\(\s*-?\d+\s*,\s*-?\d+\s*\)[\s,]*)+)", t, re.I)
    if m:
        pts = re.findall(r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", m.group(1))
        return "coordinates", [[int(x), int(y)] for x, y in pts]
    return None


def _compare(parsed, truth):
    if parsed is None:
        return "UNSURE"
    kind, value = parsed
    if kind not in truth:
        return "FAIL"
    want = truth[kind]
    if kind == "class":
        want = str(want).lower()
    if kind == "coordinates":
        return "PASS" if sorted(value) == sorted(list(p) for p in want) else "FAIL"
    return "PASS" if value == want else "FAIL"


def judge(crop_png, check):
    png = Path(crop_png)
    backend = check.get("backend", "ollama")
    prompt = check["prompt"] + FORMAT_HINT
    model = os.environ.get("OM_LOOK_OLLAMA_MODEL", "qwen3-vl:8b")
    backend_id = "ollama:" + model if backend == "ollama" else backend
    try:
        key = hashlib.sha256(b"\0".join([hashlib.sha256(png.read_bytes()).digest(),
                                         hashlib.sha256(prompt.encode()).digest(),
                                         backend_id.encode()])).hexdigest()
    except OSError:
        return {"verdict": "UNSURE", "answer": "", "raw": "unreadable frame"}
    cache = Path(os.environ.get("OM_LOOK_CACHE_DIR", ".cache/look")) / (key + ".json")
    raw = None
    try:
        raw = json.loads(cache.read_text())["raw"]
    except (OSError, ValueError, KeyError):
        pass
    if raw is None:
        try:
            if backend == "ollama":
                raw = _ask_ollama(png, prompt, model)
            elif backend == "claude":
                raw = _ask_claude(png, prompt)
            else:
                raise ValueError("unknown back end %r" % backend)
            if not isinstance(raw, str):
                raise ValueError("non-text reply")
        except Exception as e:  # fail closed: any failure is UNSURE and is not cached
            return {"verdict": "UNSURE", "answer": "", "raw": "error: %s" % e}
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"raw": raw}))
    parsed = parse(raw)
    return {"verdict": _compare(parsed, check["truth"]),
            "answer": "" if parsed is None else json.dumps(parsed[1]), "raw": raw}
