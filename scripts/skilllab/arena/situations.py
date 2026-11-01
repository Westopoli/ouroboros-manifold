"""H-040 part 5: the situations converter. Turns each `SIT-*.md` (written from situations/TEMPLATE.md) into a catalogue layout
`L-NNNN.toml` and `.json` in the H-025 schema, checked by the producer's own `check_layout`.

CLI: python3 -m scripts.skilllab.arena.situations --dir <situations dir> --out <catalogue dir> --next-id <L-NNNN>
Prints `CONVERTED <sit> <layout>` or `REJECT <sit> <rule or missing field>`; exits 2 on any REJECT. A situation whose stage is above the
current one is still converted. Units are placed in blocks at the producer's PITCH (DRAFT-block-pitch, 40 wu), through its `_block`.
Every number is an Architect draft dated 2026-10-31 that Westley rules."""
import argparse
import json
import math
import re
import sys
from pathlib import Path

from scripts.skilllab.catalogue.produce import PITCH, SITUATIONS, _block, _round_unit, check_layout, presets, rules, write_layout

COMPASS = {"east": 0.0, "south": math.pi / 2, "west": math.pi, "north": -math.pi / 2}  # atan2(dy, dx); y grows southward, as on screen
SIDE_COLUMNS = ("side", "role", "count", "anchor x", "anchor y", "facing", "range", "layer")
FEATURE_COLUMNS = ("kind", "x", "y", "size", "notes")


class Reject(Exception):
    """One reason the situation does not convert: a violated rule id or `missing <field>`."""


def _head(text, name):
    """The value of a `Name: value   (comment)` header line; the comment after two or more spaces is dropped. None when absent or empty."""
    m = re.search(r"^%s:[ \t]*(.*)$" % re.escape(name), text, re.M | re.I)
    value = re.split(r"\s{2,}", m.group(1).strip())[0] if m else ""
    return value or None


def _section(text, title):
    """The lines under the `## title` heading, up to the next heading."""
    m = re.search(r"^##[ \t]+%s[ \t]*$(.*?)(?=^##[ \t]|\Z)" % re.escape(title), text, re.M | re.I | re.S)
    return m.group(1).splitlines() if m else []


def _rows(lines, columns, field):
    """Data rows of the first table in `lines`, as dicts keyed by `columns` (matched by header name, order free)."""
    cells = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines if ln.strip().startswith("|")]
    if not cells:
        raise Reject("missing %s" % field)
    head = [c.lower() for c in cells[0]]
    for c in columns:
        if c not in head:
            raise Reject("missing %s column %s" % (field, c))
    return [dict(zip(head, row)) for row in cells[1:] if not all(re.fullmatch(r":?-*:?", c) for c in row)]


def _number(value, what, kind=float):
    try:
        return kind(value)
    except ValueError:
        raise Reject("bad %s %r" % (what, value))


def _facing(value):
    value = value.lower()
    if value in COMPASS:
        angle = COMPASS[value]
    else:
        angle = math.radians(_number(value, "facing"))
    return math.atan2(math.sin(angle), math.cos(angle))


def _block_units(row):
    """The units of one table row: a block centred on its anchor, rows running back from the front, at the producer's pitch."""
    n = _number(row["count"], "count", int)
    facing = _facing(row["facing"])
    cols = max(1, math.ceil(math.sqrt(n)))
    shift = (math.ceil(n / cols) - 1) / 2 * PITCH  # _block puts the front row on its centre; move it so the anchor is the block's centre
    cx = _number(row["anchor x"], "anchor x") + shift * math.cos(facing)
    cy = _number(row["anchor y"], "anchor y") + shift * math.sin(facing)
    if _number(row["range"], "range") != 0:
        raise Reject("range %s: only 0 (the role's own range) converts" % row["range"])
    return [_round_unit(x, y, f, lay, row["role"]) for x, y, f, lay in _block(n, cx, cy, facing, cols, _number(row["layer"], "layer", int))]


def _layout(text):
    """The layout dict (no id yet) for one situation file; Reject on a missing field."""
    stage, kind, field, predict, why = (_head(text, k) for k in ("Stage", "Kind", "Field", "Predict", "Why"))
    for name, value in (("stage", stage), ("kind", kind), ("field", field), ("predict", predict), ("why", why)):
        if value is None:
            raise Reject("missing %s" % name)
    if kind not in SITUATIONS:
        raise Reject("kind %r is not a situation kind" % kind)
    if predict not in ("A", "B", "draw"):
        raise Reject("predict %r is not A, B or draw" % predict)
    sides = {"A": [], "B": []}
    for row in _rows(_section(text, "Sides"), SIDE_COLUMNS, "sides"):
        if row["side"] not in sides:
            raise Reject("side %r is not A or B" % row["side"])
        sides[row["side"]] += _block_units(row)
    for letter, units in sides.items():
        if not units:
            raise Reject("missing side %s" % letter)
    features = []
    for row in _rows(_section(text, "Features"), FEATURE_COLUMNS, "features"):
        if row["kind"]:
            features.append({"kind": row["kind"], "x": _number(row["x"], "feature x"), "y": _number(row["y"], "feature y"),
                             "size": row["size"], "notes": row["notes"]})
    defender = next((ln.split()[0] for ln in _section(text, "Defender") if ln.strip()), "none")  # an absent section is "none", as the template's
    if defender not in ("none", "A", "B"):
        raise Reject("defender %r is not none, A or B" % defender)
    return {"id": "", "situation": kind, "landscape": field, "seed": 0, "predict": predict, "predict_why": why, "verdict": "", "feedback": "",
            "defender": "" if defender == "none" else defender, "features": features,
            "side_a": {"headcount": len(sides["A"]), "units": sides["A"]}, "side_b": {"headcount": len(sides["B"]), "units": sides["B"]}}


def _write(layout, out):
    """write_layout (the producer's), then the keys its TOML writer does not carry: `defender` and `features`. The JSON already has them."""
    path = write_layout(layout, out)
    text = path.read_text()
    top = []
    if not re.search(r"^defender =", text, re.M):
        top.append("defender = %s" % json.dumps(layout["defender"]))
    if not layout["features"] and not re.search(r"^features\b", text, re.M):
        top.append("features = []")
    if top:
        text = text.replace("\n[side_a]", "\n" + "\n".join(top) + "\n\n[side_a]", 1)
    if layout["features"] and "[[features]]" not in text:
        for f in layout["features"]:
            text += "\n[[features]]\n" + "".join("%s = %s\n" % (k, json.dumps(v) if isinstance(v, str) else repr(v)) for k, v in f.items())
    path.write_text(text)


def convert(sit_dir, out, next_id):
    """Convert every SIT-*.md in file-name order; (lines printed, whether any was rejected). An id is used only by a converted file."""
    m = re.fullmatch(r"L-(\d{4})", next_id)
    if not m:
        raise SystemExit("--next-id %r is not L-NNNN" % next_id)
    number, lines, rejected = int(m.group(1)), [], False
    pre, rul = presets(), rules()
    Path(out).mkdir(parents=True, exist_ok=True)
    for path in sorted(Path(sit_dir).glob("SIT-*.md")):
        try:
            layout = _layout(path.read_text())
            layout["id"] = "L-%04d" % number
            if (Path(out) / (layout["id"] + ".toml")).exists():
                raise Reject("%s already exists in %s" % (layout["id"], out))
            bad = check_layout(layout, pre, rul)
            if bad:
                raise Reject(" ".join(bad))
        except Reject as why:
            lines.append("REJECT %s %s" % (path.stem, why))
            rejected = True
            continue
        _write(layout, out)
        lines.append("CONVERTED %s %s" % (path.stem, layout["id"]))
        number += 1
    return lines, rejected


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--next-id", required=True)
    args = ap.parse_args(argv)
    lines, rejected = convert(args.dir, args.out, args.next_id)
    print("\n".join(lines))
    return 2 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
