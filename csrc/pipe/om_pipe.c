/* csrc/pipe/om_pipe.c — T1 placeholder. Prints one hello JSON line naming
 * this build's ABI version, then exits; piece T1 replaces this with the real
 * stdio pipe server (docs/architecture.md, "C transport v1"). */
#include <stdio.h>

#include "ouroboros_sim.h"

int main(void) {
    printf("{\"type\":\"hello\",\"abi\":%u}\n", om_abi_version());
    return 0;
}
