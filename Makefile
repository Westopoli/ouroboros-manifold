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
#
# OPT (default -O2) and WERROR (default 0, add -Werror when 1) are the merge
# gate's knobs (`make OPT=-O2 WERROR=1`). The top-level libouroboros*.so
# targets always build at the repo root regardless of OPT -- conftest.py
# depends on that path. build/O0/ and build/O2/ are separate, always-O0 /
# always-O2 output dirs (checksum_trace.py compares one tree against the
# other in the same run, so their optimization level is not left to
# whatever OPT the caller happened to pass).

OPT     ?= -O2
WERROR  ?= 0

CC      ?= cc
SRC     := $(wildcard csrc/*.c)
HDR     := csrc/ouroboros_sim.h

CFLAGS_COMMON   := -std=c11 -Wall -Wextra -Icsrc -fPIC
CFLAGS_DET_BASE := -fno-fast-math -ffp-contract=off -fexcess-precision=standard \
                   -msse2 -mfpmath=sse -fno-math-errno
ifeq ($(WERROR),1)
CFLAGS_DET_BASE += -Werror
endif
CFLAGS_DET := $(OPT) $(CFLAGS_DET_BASE)
CFLAGS     := $(CFLAGS_COMMON) $(CFLAGS_DET)

.PHONY: all clean test
all: libouroboros.so libouroboros_dbg.so

libouroboros.so: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -shared -o $@ $(SRC)

libouroboros_dbg.so: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -DOM_DEBUG_INJECT -shared -o $@ $(SRC)

# Fixed-optimization output dirs for the O0-vs-O2 determinism gate
# (checksum_trace.py --lib build/O0/libouroboros.so ... equals the build/O2
# run). Always -O0 / always -O2 by name, independent of $(OPT).
build/O0/libouroboros.so: $(SRC) $(HDR)
	mkdir -p build/O0
	$(CC) $(CFLAGS_COMMON) -O0 $(CFLAGS_DET_BASE) -shared -o $@ $(SRC)

build/O0/libouroboros_dbg.so: $(SRC) $(HDR)
	mkdir -p build/O0
	$(CC) $(CFLAGS_COMMON) -O0 $(CFLAGS_DET_BASE) -DOM_DEBUG_INJECT -shared -o $@ $(SRC)

build/O2/libouroboros.so: $(SRC) $(HDR)
	mkdir -p build/O2
	$(CC) $(CFLAGS_COMMON) -O2 $(CFLAGS_DET_BASE) -shared -o $@ $(SRC)

build/O2/libouroboros_dbg.so: $(SRC) $(HDR)
	mkdir -p build/O2
	$(CC) $(CFLAGS_COMMON) -O2 $(CFLAGS_DET_BASE) -DOM_DEBUG_INJECT -shared -o $@ $(SRC)

# T1 placeholder pipe server (csrc/pipe/om_pipe.c); linked against the
# release library. -lm resolves libm symbols already present in
# libouroboros.so's object code (om_region_composite's round(), the region.c
# weak om_sin fallback's sin()) that ctypes.CDLL never had to resolve at
# link time. T1 replaces the source; this target's shape (name, library
# link) does not change.
pipe/ouroboros_pipe: csrc/pipe/om_pipe.c libouroboros.so
	mkdir -p pipe
	$(CC) $(CFLAGS) -o $@ csrc/pipe/om_pipe.c -L. -louroboros -lm -Wl,-rpath,'$$ORIGIN/..'

# Convenience: build then run the fenced C-sim test suite.
test: all
	python3 -m pytest tests/csim -p no:cacheprovider

clean:
	rm -f libouroboros.so libouroboros_dbg.so pipe/ouroboros_pipe
	rm -rf build
