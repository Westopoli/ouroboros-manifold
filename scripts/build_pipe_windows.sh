#!/usr/bin/env bash
# Static Windows x86_64 pipe exe via mingw-w64, linked against ucrt: dist/windows/ouroboros_pipe.exe.
# GCC 13 has no -mcrtdll=ucrt, so a specs file swaps -lmsvcrt for -lucrt (W8a, Steam spec).
# Binary stdio: om_pipe.c has no _setmode yet (W8b), so a force-included constructor sets it.
set -euo pipefail
cd "$(dirname "$0")/.."
CC=${CC:-x86_64-w64-mingw32-gcc}
out=dist/windows; mkdir -p "$out"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
$CC -dumpspecs | sed 's/-lmsvcrt/-lucrt/g' > "$tmp/ucrt.specs"
cat > "$tmp/binstdio.h" <<'H'
#include <fcntl.h>
#include <io.h>
#include <stdio.h>
__attribute__((constructor)) static void om_binary_stdio(void) {
  _setmode(_fileno(stdin), _O_BINARY);
  _setmode(_fileno(stdout), _O_BINARY);
}
H
$CC -specs="$tmp/ucrt.specs" -std=gnu11 -Wall -Wextra -Icsrc -O2 \
  -fno-fast-math -ffp-contract=off -fno-math-errno -msse2 -mfpmath=sse -fexcess-precision=standard \
  -D__USE_MINGW_ANSI_STDIO=1 -static -include "$tmp/binstdio.h" \
  -o "$out/ouroboros_pipe.exe" csrc/*.c csrc/pipe/om_pipe.c csrc/pipe/pipe_*.c -lm
echo "$out/ouroboros_pipe.exe"
