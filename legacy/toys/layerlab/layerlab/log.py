"""Append-only experiment log (SPEC.md section 8, transfer classes in section 12)."""
from pathlib import Path

from .ffi import LAB

TRANSFER_CLASSES = ("T1", "T2", "T3")
DEFAULT_PATH = LAB / "results" / "log.md"


def check_class(transfer_class):
    if not isinstance(transfer_class, str) or transfer_class not in TRANSFER_CLASSES:
        raise ValueError("transfer_class must be one of %s, got %r" % (", ".join(TRANSFER_CLASSES), transfer_class))


def _fmt_diff(diff):
    if not diff:
        return "(none)"
    return "\n".join("%s: %r -> %r" % (p, a, b) for p, (a, b) in diff.items())


def append(entry, path=None):
    check_class(entry.get("transfer_class"))
    path = Path(path) if path is not None else DEFAULT_PATH
    lines = ["## %s: %s" % (entry["date"], entry.get("title") or "entry"), ""]
    lines.append("- Command: `%s`" % entry["command"])
    lines.append("- Transfer class: %s" % entry["transfer_class"])
    if entry.get("png"):
        lines.append("- PNG: %s" % entry["png"])
    if entry.get("note"):
        lines += ["", entry["note"]]
    lines += ["", "Scenario diff against base.toml:", "", "```", _fmt_diff(entry.get("diff")), "```", "",
              "```", entry["table"].rstrip("\n"), "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    lead = "\n" if path.exists() and path.stat().st_size else ""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(lead + "\n".join(lines))
