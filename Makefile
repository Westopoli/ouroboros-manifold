# Makefile for the Ouroboros C sim core.
#
# Fenced (parent-owned): Agora writes csrc/*.c but does not edit this file or the
# header. Two shared libraries:
#   libouroboros.so      release build the fenced tests load
#   libouroboros_dbg.so  same sources + fault injection, for positive controls
#
# Determinism (docs/northstar/research/c_rewrite.md): identical flags on every
# platform, no fast-math, no FMA contraction, SSE math to kill x87 excess
# precision. The C trace must be byte-identical across Linux/Windows/macOS.

CC      ?= cc
SRC     := $(wildcard csrc/*.c)
HDR     := csrc/ouroboros_sim.h

CFLAGS_COMMON := -std=c11 -Wall -Wextra -Icsrc -fPIC
CFLAGS_DET    := -O2 -fno-fast-math -ffp-contract=off -fexcess-precision=standard \
                 -msse2 -mfpmath=sse -fno-math-errno
CFLAGS        := $(CFLAGS_COMMON) $(CFLAGS_DET)

.PHONY: all clean test
all: libouroboros.so libouroboros_dbg.so

libouroboros.so: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -shared -o $@ $(SRC)

libouroboros_dbg.so: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -DOM_DEBUG_INJECT -shared -o $@ $(SRC)

# Convenience: build then run the fenced C-sim test suite.
test: all
	python3 -m pytest tests/csim -p no:cacheprovider

clean:
	rm -f libouroboros.so libouroboros_dbg.so
