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
ARC_COLUMNS = ("shape", "centre_x", "centre_y", "radius", "start_deg", "end_deg")  # H-053, optional: a table without them is all blocks
ORDERS = ("both_same_point", "hold:A", "hold:B")
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


def _arc_units(row, index):
    """The units of one arc row (H-053 Interfaces 2): one ring, units at the chord PITCH from start_deg clockwise on screen, each facing the centre and
    tagged `arc` = the arc's index in the side's `arcs` list (R7 reads the tag). Returns (units, the arc record)."""
    cx, cy, radius, start, end = (_number(row.get(c, ""), c) for c in ARC_COLUMNS[1:])
    n, span = _number(row["count"], "count", int), end - start
    step = 2 * math.asin(PITCH / (2 * radius))
    if n > 1 and (n - 1) * step > math.radians(span) + 1e-9:
        need = math.ceil(PITCH / (2 * math.sin(math.radians(span) / (2 * (n - 1)))))
        raise Reject("arc too small: %d units at pitch %d on %d° need radius %d" % (n, PITCH, round(span), need))
    if _number(row["range"], "range") != 0:
        raise Reject("range %s: only 0 (the role's own range) converts" % row["range"])
    units = []
    for k in range(n):
        a = math.radians(start) + k * step
        x, y = cx + radius * math.cos(a), cy + radius * math.sin(a)
        units.append(dict(_round_unit(x, y, math.atan2(cy - y, cx - x), _number(row["layer"], "layer", int), row["role"]), arc=index))
    return units, {"centre": [cx, cy], "radius": radius, "start_deg": start, "end_deg": end, "count": n}


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
    keys = {}
    if _number(stage, "stage", int) >= 2:
        rate = _head(text, "Expected win rate")
        if rate is None:
            raise Reject("missing expected win rate")
        keys["predict_rate"] = _number(rate, "expected win rate")
        if not 0 <= keys["predict_rate"] <= 1:
            raise Reject("expected win rate %s is not between 0 and 1" % rate)
    orders = _head(text, "Orders")
    if orders is not None:
        if orders not in ORDERS:
            raise Reject("orders %r is not both_same_point, hold:A or hold:B" % orders)
        keys["orders"] = orders
    point = _head(text, "Orders point")
    if point is not None and point.lower() != "midpoint":
        xy = point.split()
        if len(xy) != 2:
            raise Reject("orders point %r is not midpoint or <x> <y>" % point)
        keys["orders_point"] = [_number(v, "orders point") for v in xy]
    for head, key in (("What to expect", "what_to_expect"), ("Approve means", "approve_means"), ("Deny means", "deny_means")):
        if _head(text, head) is not None:   # H-053 page text, optional
            keys[key] = _head(text, head)
    sides, arcs = {"A": [], "B": []}, {"A": [], "B": []}
    for row in _rows(_section(text, "Sides"), SIDE_COLUMNS, "sides"):
        if row["side"] not in sides:
            raise Reject("side %r is not A or B" % row["side"])
        shape = row.get("shape", "").lower() or "block"
        if shape not in ("block", "arc"):
            raise Reject("shape %r is not block or arc" % shape)
        if shape == "arc":   # each row is its own block or arc; a side may mix them
            units, record = _arc_units(row, len(arcs[row["side"]]))
            sides[row["side"]] += units
            arcs[row["side"]].append(record)
        else:
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
    layout = {"id": "", "situation": kind, "landscape": field, "seed": 0, "predict": predict, "predict_why": why, "verdict": "", "feedback": "",
            "defender": "" if defender == "none" else defender, "features": features,
            "side_a": {"headcount": len(sides["A"]), "units": sides["A"]}, "side_b": {"headcount": len(sides["B"]), "units": sides["B"]}}
    layout.update(keys)
    for letter, records in arcs.items():
        if records:
            layout["side_" + letter.lower()]["arcs"] = records
    return layout


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
