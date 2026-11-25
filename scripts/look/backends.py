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
    # The prompt precedes `--allowedTools`: that flag is variadic and swallows every token after it, so a trailing prompt made the real CLI exit 1.
    r = subprocess.run(["claude", "-p", "%s\nImage file: %s" % (prompt, png), "--allowedTools", "Read"],
                       input="", capture_output=True, text=True, timeout=_timeout(), check=True)
    return r.stdout


_FIELD = r"(?:class:\s*[^\s,]+|count:\s*-?\d+|coordinates:\s*(?:\(\s*-?\d+\s*,\s*-?\d+\s*\)[\s,]*)+)"
_FIELDS = re.compile(_FIELD + r"(?:[\s,;]+" + _FIELD + r")*[.\s]*", re.I)


def parse(text):
    """Return every field of a reply that is made only of fields: [("class", str) | ("count", int) | ("coordinates", [[x, y], ...])], in order; [] when it is anything else."""
    t = text.strip()
    if not _FIELDS.fullmatch(t):
        return []
    out = []
    for m in re.finditer(r"(class):\s*([^\s,]+)|(count):\s*(-?\d+)|(coordinates):\s*((?:\(\s*-?\d+\s*,\s*-?\d+\s*\)[\s,]*)+)", t, re.I):
        if m.group(1):
            out.append(("class", m.group(2).strip(".,;").lower()))
        elif m.group(3):
            out.append(("count", int(m.group(4))))
        else:
            pts = re.findall(r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", m.group(6))
            out.append(("coordinates", [[int(x), int(y)] for x, y in pts]))
    return out


def _compare(fields, truth):
    """(verdict, parsed field used). The field answering the check is the one whose key the truth asks for; two different values for it are UNSURE."""
    if not fields:
        return "UNSURE", None
    for kind in ("class", "count", "coordinates"):
        if kind not in truth:
            continue
        values = [v for k, v in fields if k == kind]
        if not values:
            continue
        if any(v != values[0] for v in values):
            return "UNSURE", None
        want = truth[kind]
        if kind == "class":
            want = str(want).lower()
        if kind == "coordinates":
            return ("PASS" if sorted(values[0]) == sorted(list(p) for p in want) else "FAIL"), (kind, values[0])
        return ("PASS" if values[0] == want else "FAIL"), (kind, values[0])
    return "FAIL", fields[0]


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
    if isinstance(raw, str) and not raw.strip():  # an empty reply cached by an earlier version is a miss
        raw = None
    if raw is None:
        try:
            if backend == "ollama":
                raw = _ask_ollama(png, prompt, model)
            elif backend == "claude":
                raw = _ask_claude(png, prompt)
            else:
                raise ValueError("unknown back end %r" % backend)
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError("empty or non-text reply")
        except Exception as e:  # fail closed: any failure is UNSURE and is not cached
            return {"verdict": "UNSURE", "answer": "", "raw": "error: %s" % e}
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"raw": raw}))
    verdict, used = _compare(parse(raw), check["truth"])
    return {"verdict": verdict, "answer": "" if used is None else json.dumps(used[1]), "raw": raw}
