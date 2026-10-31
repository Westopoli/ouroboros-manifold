"""Validator for the nine-field lab trace row (H-024): (tick, unit, x, y, target, facing, alive, layer, unit_type)."""

NAMES = ("tick", "unit", "x", "y", "target", "facing", "alive", "layer", "unit_type")
INT_FIELDS = ("tick", "unit", "target", "layer", "unit_type")
NUM_FIELDS = ("x", "y", "facing")


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, float) or _is_int(v)


def validate_row(row):
    if len(row) != len(NAMES):
        raise ValueError("trace row needs 9 fields, got %d" % len(row))
    for name, value in zip(NAMES, row):
        if name in INT_FIELDS:
            ok = _is_int(value)
        elif name in NUM_FIELDS:
            ok = _is_num(value)
        else:
            ok = isinstance(value, bool) or (_is_int(value) and value in (0, 1))
        if not ok:
            raise ValueError("trace row field %s bad: %s" % (name, value))


def validate_trace(rows):
    for row in rows:
        validate_row(row)
    return len(rows)
