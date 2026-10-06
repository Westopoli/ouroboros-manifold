#!/usr/bin/env bash
# Fetch the pinned GodotSteam GDExtension into addons/godotsteam/ (not committed, see .gitignore).
# Usage: scripts/fetch_godotsteam.sh [local_zip]
set -euo pipefail

URL="https://codeberg.org/godotsteam/godotsteam/releases/download/v4.23-gde/godotsteam-4.23-gdextension-plugin-4.4.zip"
SHA256="c1728b4bf330da851a00eaf64dab2e99c506018b1d9f529511b25d7fe7649e97"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

if [ $# -ge 1 ]; then
    zip="$1"
else
    zip="$tmp/godotsteam.zip"
    curl -fsSL -o "$zip" "$URL"
fi

actual="$(sha256sum "$zip" | cut -d' ' -f1)"
if [ "$actual" != "$SHA256" ]; then
    echo "sha256 mismatch: expected $SHA256, got $actual" >&2
    exit 1
fi

unzip -q -o "$zip" 'addons/godotsteam/*' -d "$ROOT"
echo "godotsteam unpacked into $ROOT/addons/godotsteam"
