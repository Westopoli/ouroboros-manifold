# Layer lab build (SPEC.md section 9). Run from toys/layerlab/.
#   make                 build/O0, build/O2 and build/liblayerlab.so (copy of O2)
#   make WERROR=1        same, warnings are errors
#   make smoke           build and run the C smoke harness against the O2 library
#   make det             run it against O0 and O2; hashes must match; seed 0 twice in-process
# OPT (default -O2) is the optimisation level of the build/O2 directory; build/O0 is always -O0.
# WERROR (default 0) adds -Werror when 1.

OPT     ?= -O2
WERROR  ?= 0
CC      ?= cc

SRC := $(wildcard src/*.c)
HDR := $(wildcard include/*.h src/*.h)

UNAME_M := $(shell uname -m)
UNAME_S := $(shell uname -s)

CFLAGS_COMMON := -std=c11 -Wall -Wextra -Iinclude -fPIC
CFLAGS_DET    := -fno-fast-math -ffp-contract=off -fno-math-errno
ifeq ($(UNAME_M),x86_64)
CFLAGS_DET += -msse2 -mfpmath=sse -fexcess-precision=standard
endif
ifeq ($(WERROR),1)
CFLAGS_DET += -Werror
endif

# Position-independent lookup so the smoke binary finds the library next to itself.
ifeq ($(UNAME_S),Darwin)
SO_NAME := -Wl,-install_name,@rpath/liblayerlab.so
EXE_RPATH := -Wl,-rpath,@executable_path
else
SO_NAME :=
EXE_RPATH := -Wl,-rpath,'$$ORIGIN'
endif

.PHONY: all O0 O2 clean smoke det
all: O0 O2 build/liblayerlab.so
O0: build/O0/liblayerlab.so
O2: build/O2/liblayerlab.so

build/O0/liblayerlab.so: $(SRC) $(HDR)
	mkdir -p build/O0
	$(CC) $(CFLAGS_COMMON) -O0 $(CFLAGS_DET) -shared $(SO_NAME) -o $@ $(SRC) -lm

build/O2/liblayerlab.so: $(SRC) $(HDR)
	mkdir -p build/O2
	$(CC) $(CFLAGS_COMMON) $(OPT) $(CFLAGS_DET) -shared $(SO_NAME) -o $@ $(SRC) -lm

build/liblayerlab.so: build/O2/liblayerlab.so
	cp $< $@

build/O0/c_smoke: tests/c_smoke.c build/O0/liblayerlab.so
	$(CC) $(CFLAGS_COMMON) -O0 $(CFLAGS_DET) -o $@ tests/c_smoke.c build/O0/liblayerlab.so $(EXE_RPATH)

build/O2/c_smoke: tests/c_smoke.c build/O2/liblayerlab.so
	$(CC) $(CFLAGS_COMMON) $(OPT) $(CFLAGS_DET) -o $@ tests/c_smoke.c build/O2/liblayerlab.so $(EXE_RPATH)

smoke: build/O2/c_smoke
	build/O2/c_smoke

det: build/O0/c_smoke build/O2/c_smoke
	@build/O0/c_smoke > build/O0/smoke.out; s0=$$?; \
	 build/O2/c_smoke > build/O2/smoke.out; s2=$$?; \
	 if [ $$s0 -eq 1 ] || [ $$s2 -eq 1 ]; then echo "det: FAIL in-process or run error"; cat build/O0/smoke.out build/O2/smoke.out; exit 1; fi; \
	 h0=`grep '^HASH' build/O0/smoke.out`; h2=`grep '^HASH' build/O2/smoke.out`; \
	 echo "O0 $$h0"; echo "O2 $$h2"; \
	 if [ "$$h0" = "$$h2" ] && [ -n "$$h0" ]; then echo "det: PASS (O0 == O2, seed 0 repeats identical)"; \
	 else echo "det: FAIL (O0 and O2 hashes differ)"; exit 1; fi

clean:
	rm -rf build
