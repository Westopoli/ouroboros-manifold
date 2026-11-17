/* csrc/notice_internal.h -- internal (not the contract header): the notice distance of E-11 R-087-04 (engine rule fixes, Round 5, G1).
 * A unit's notice distance to an enemy is its weapon's reach to that enemy (R-087-10) times 1 + OM_NOTICE_MARGIN; it acquires nothing beyond it
 * and its lock ends when the target leaves it (R-087-03). The leash (om_tac_leash in csrc/unit.c) is a different distance and is not this one. */
#ifndef OM_NOTICE_INTERNAL_H
#define OM_NOTICE_INTERNAL_H

/* DRAFT-notice-margin (R-087-04, Westley's number to change): one tenth of the reach; 30 wu on a range of 300. */
#define OM_NOTICE_MARGIN 0.1

#endif
