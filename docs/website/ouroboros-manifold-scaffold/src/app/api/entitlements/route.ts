// =============================================================================
// GET /api/entitlements
// Implements: webapp_architecture_1_00.md § API Surface
//
// Returns the authenticated user's full entitlement set.
// Called by: Godot client on launch, account dashboard.
// =============================================================================

import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { resolveEntitlements } from "@/lib/entitlements";
import {
  checkRateLimit,
  getClientIp,
  RATE_LIMITS,
} from "@/lib/rate-limit";

export async function GET(request: Request) {
  // Rate limit
  const ip = getClientIp(request);
  const limit = checkRateLimit(ip, RATE_LIMITS.authenticated);
  if (!limit.allowed) {
    return NextResponse.json(
      { error: "Too many requests" },
      {
        status: 429,
        headers: {
          "Retry-After": String(
            Math.ceil((limit.resetAt - Date.now()) / 1000)
          ),
        },
      }
    );
  }

  // Auth check
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 }
    );
  }

  try {
    const entitlements = await resolveEntitlements(session.user.id);
    return NextResponse.json(entitlements);
  } catch (error) {
    console.error("[ENTITLEMENTS] Resolution failed:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
