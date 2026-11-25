"""Look cards: load and validate scripts/look/cards/<id>.toml (spec: docs/northstar/plans/cascades/look-judge-rig/spec.md). Fail closed."""
import tomllib

KINDS = ("state", "render", "look", "compare")


class CardError(Exception):
    pass


def load_card(path):
    try:
        with open(path, "rb") as f:
            c = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise CardError(f"{path}: {e}")
    for k in ("id", "words"):
        if not isinstance(c.get(k), str) or not c[k].strip():
            raise CardError(f"{path}: missing {k}")
    if not c.get("requirements") or not all(isinstance(r, str) for r in c["requirements"]):
        raise CardError(f"{path}: missing requirements")
    if not c.get("checks"):
        raise CardError(f"{path}: no checks")
    for ch in c["checks"]:
        if ch.get("kind") not in KINDS:
            raise CardError(f"{path}: check kind {ch.get('kind')!r}")
        for k in ("name", "success", "broken_twin"):
            if not isinstance(ch.get(k), str) or not ch[k].strip():
                raise CardError(f"{path}: check {ch.get('name')!r} missing {k}")
    return c
