// =============================================================================
// Entitlement Resolution
// Implements: webapp_architecture_1_00.md § Entitlement Resolution
//
// Given a user ID, determines which eras they can access by combining:
// 1. Free tier (always includes "roman")
// 2. Active subscription (all eras)
// 3. One-time purchases (permanent per-era)
// 4. Access keys (type-dependent)
// 5. Steam DLC ownership
//
// The Godot client and account dashboard both consume this.
// =============================================================================

import { prisma } from "@/lib/db";

const FREE_TIER_ERAS = ["roman"] as const;

export interface EntitlementResult {
  /** All era IDs the user can currently access */
  eras: string[];
  /** Whether the user has an active subscription */
  subscriptionActive: boolean;
  /** Remaining trial missions per era (for mission_limited keys) */
  trialMissionsRemaining: Record<string, number>;
}

export async function resolveEntitlements(
  userId: string
): Promise<EntitlementResult> {
  const eras = new Set<string>(FREE_TIER_ERAS);
  const trialMissions: Record<string, number> = {};

  // Fetch all entitlement sources in parallel — single DB round trip
  const [subscription, purchases, keys, steamEntitlements] = await Promise.all([
    prisma.subscription.findUnique({ where: { userId } }),
    prisma.purchase.findMany({ where: { userId }, select: { eraId: true } }),
    prisma.accessKey.findMany({
      where: { redeemedBy: userId },
      select: {
        keyType: true,
        scope: true,
        durationDays: true,
        missionCount: true,
        redeemedAt: true,
      },
    }),
    prisma.steamEntitlement.findMany({
      where: { userId },
      select: { eraId: true },
    }),
  ]);

  // 2. Active subscription → all eras
  const subActive =
    subscription !== null &&
    ["active", "trialing", "past_due"].includes(subscription.status) &&
    new Date() < subscription.currentPeriodEnd;

  if (subActive) {
    // Subscription grants all available eras.
    // In production, this would query an era registry.
    // For now, return early — subscription trumps everything.
    return {
      eras: ["all"],
      subscriptionActive: true,
      trialMissionsRemaining: {},
    };
  }

  // 3. One-time purchases → permanent
  for (const purchase of purchases) {
    eras.add(purchase.eraId);
  }

  // 4. Access keys → type-dependent
  const now = new Date();
  for (const key of keys) {
    const scope = key.scope as { eras: string[] | "all" };
    const keyEras =
      scope.eras === "all" ? ["all"] : Array.isArray(scope.eras) ? scope.eras : [];

    switch (key.keyType) {
      case "permanent":
        keyEras.forEach((e) => eras.add(e));
        break;

      case "time_limited":
        if (
          key.redeemedAt &&
          key.durationDays &&
          now.getTime() <
            key.redeemedAt.getTime() + key.durationDays * 86_400_000
        ) {
          keyEras.forEach((e) => eras.add(e));
        }
        break;

      case "mission_limited":
        if (key.missionCount && key.missionCount > 0) {
          keyEras.forEach((e) => {
            eras.add(e);
            trialMissions[e] = (trialMissions[e] || 0) + key.missionCount!;
          });
        }
        break;
    }
  }

  // 5. Steam DLC ownership
  for (const ent of steamEntitlements) {
    eras.add(ent.eraId);
  }

  return {
    eras: Array.from(eras),
    subscriptionActive: false,
    trialMissionsRemaining: trialMissions,
  };
}
