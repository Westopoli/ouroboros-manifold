"""How far a result transfers (definition unconfirmed, Architect to rule): a tunable number changed or not."""
RULE_GEOMETRY = "rule geometry: holds as is"
MAGNITUDES = "magnitudes: will retune"


def transfer_class(setup):
    """MAGNITUDES iff the setup overrides engine settings or unit stats, narrows the firing arc or sets a cone (decision 29 item 7);
    headcounts, layout, the point and the order style are geometry."""
    return MAGNITUDES if setup.settings or setup.unit_types or setup.firing_arc_deg < 360.0 or setup.cone else RULE_GEOMETRY


def row_labels(setup):
    return {"transfer": transfer_class(setup)}


def label_build(build):
    """Wrap a BuildFn so batches carry the 'transfer' label; the class does not depend on headcount."""
    def wrapped(enemy_heads, swap):
        return build(enemy_heads, swap)
    wrapped.labels = dict(getattr(build, "labels", {}), **row_labels(build(1, False)))
    return wrapped
