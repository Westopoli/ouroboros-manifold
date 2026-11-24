"""Approved-scene ledger tool (story look-judge-rig, spec piece 4).

python3 -m scripts.look.ledger {validate|list|reopen|verify|replace} <ledger.toml> ...
"""
import hashlib
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REQUIRED = ["id", "requirements", "sha", "scene", "fight_or_layout", "seed",
            "reopen_command", "frames", "words", "date", "trace_hash", "source"]
ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return tomllib.loads(Path(path).read_text()).get("row", [])


def errors(rows):
    errs, ids = [], {r.get("id") for r in rows}
    for r in rows:
        rid = r.get("id", "?")
        for f in REQUIRED:
            if f not in r:
                errs.append(f"row {rid}: missing field {f}")
        if "sha" in r and subprocess.run(["git", "cat-file", "-e", str(r["sha"]) + "^{commit}"],
                                         cwd=ROOT, capture_output=True).returncode != 0:
            errs.append(f"row {rid}: sha {r['sha']} not found")
        if "words" in r and not str(r["words"]).strip():
            errs.append(f"row {rid}: words is empty")
        if "superseded_by" in r and r["superseded_by"] not in ids:
            errs.append(f"row {rid}: superseded_by {r['superseded_by']} names no row")
    return errs


def find(rows, rid):
    for r in rows:
        if r.get("id") == rid:
            return r
    sys.exit(f"no row {rid}")


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd, path, rest = argv[0], argv[1], argv[2:]
    rows = load(path)
    if cmd == "validate":
        errs = errors(rows)
        if errs:
            sys.exit("\n".join(errs))
    elif cmd == "list":
        for r in rows:
            print(r["id"])
    elif cmd == "reopen":
        print(find(rows, rest[0])["reopen_command"])
    elif cmd == "verify":
        try:
            p = subprocess.run(find(rows, rest[0])["reopen_command"], shell=True,
                               capture_output=True, timeout=3600)
            ok = p.returncode == 0 and hashlib.sha256(p.stdout).hexdigest() == find(rows, rest[0])["trace_hash"]
        except (OSError, subprocess.SubprocessError):
            ok = False
        print("PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    elif cmd == "replace":
        old, new_text = rest[0], Path(rest[1]).read_text()
        find(rows, old)
        text = Path(path).read_text()
        new_id = tomllib.loads(new_text)["row"][0]["id"]
        text, n = re.subn(rf'^(id = "{re.escape(old)}"\n)', rf'\1superseded_by = "{new_id}"\n',
                          text, count=1, flags=re.M)
        if n != 1:
            sys.exit(f"cannot place superseded_by on {old}")
        Path(path).write_text(text.rstrip("\n") + "\n\n" + new_text)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
