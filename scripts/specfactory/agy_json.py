"""Shared parsing of an agy JSON envelope into the schema payload.

Under a JSON schema, agy returns the model's answer in the envelope's
"response" field. Gemini returns the bare JSON object; Claude models return
a short preamble line, then the object, sometimes with extra keys
(toolAction, toolSummary) the schema did not ask for. This extracts the
outermost object and keeps only the keys the caller expects.
"""
from __future__ import annotations

import json


def payload_from_envelope(stdout: str, required: tuple[str, ...]) -> dict | None:
    stdout = stdout.strip()
    if not stdout:
        return None
    try:
        env = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    resp = env.get("response", env)
    if isinstance(resp, dict):
        obj = resp
    else:
        text = str(resp or "")
        start = text.find("{")
        if start < 0:
            return None
        obj = None
        decoder = json.JSONDecoder()
        try:
            obj, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            end = text.rfind("}")
            while end > start and obj is None:
                try:
                    obj = json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    end = text.rfind("}", start, end)
        if not isinstance(obj, dict):
            return None
    if not all(k in obj for k in required):
        return None
    return {k: obj[k] for k in obj if k in required}
