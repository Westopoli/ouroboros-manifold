#!/usr/bin/env bash
# Tier 2 regression: scripts/integration_check.sh <name> [--only a,b] [--no-compare] [--declare file]
# See docs/northstar/regression.md. Logic lives in integration_check.py.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PY:-/home/westopoli/Projects/agora/.venv/bin/python}"
exec "$PY" "$HERE/integration_check.py" "$@"
