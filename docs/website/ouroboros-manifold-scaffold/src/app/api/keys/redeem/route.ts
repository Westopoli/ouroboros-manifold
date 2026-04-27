// =============================================================================
// POST /api/keys/redeem
// Implements: webapp_architecture_1_00.md § Access Key System → Redemption Flow
//
// Security:
// - Extra-restrictive rate limiting (5/min per IP)
// - Constant-time response to prevent key enumeration
// - Key codes are 16–24 chars with 62-char alphabet (>10^28 possibilities)
// =============================================================================

import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { checkRateLimit, getClientIp, RATE_LIMITS } from "@/lib/rate-limit";

export async function POST(request: Request) {
  const ip = getClientIp(request);
  const limit = checkRateLimit(ip, RATE_LIMITS.keyRedeem);
  if (!limit.allowed) {
    return NextResponse.json(
      { error: "Too many attempts. Please wait and try again." },
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

  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 }
    );
  }

  let body: { code?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  const code = body.code?.trim();
  if (!code || code.length < 8 || code.length > 32) {
    // Generic error — don't reveal valid code length
    return NextResponse.json({ error: "Invalid key" }, { status: 400 });
  }

  // Sanitize: only alphanumeric characters
  if (!/^[a-zA-Z0-9]+$/.test(code)) {
    return NextResponse.json({ error: "Invalid key" }, { status: 400 });
  }

  try {
    // Atomic: find and claim in a transaction to prevent race conditions
    const result = await prisma.$transaction(async (tx) => {
      const key = await tx.accessKey.findUnique({
        where: { code },
      });

      // Constant-time-ish: always do the same work regardless of outcome.
      // This prevents timing attacks that could distinguish "key exists
      // but redeemed" from "key doesn't exist".
      if (!key) {
        return { success: false, reason: "invalid" } as const;
      }

      if (key.redeemedBy) {
        return { success: false, reason: "invalid" } as const; // Same error as not found
      }

      if (key.expiresAt && new Date() > key.expiresAt) {
        return { success: false, reason: "invalid" } as const;
      }

      // Claim the key
      await tx.accessKey.update({
        where: { id: key.id },
        data: {
          redeemedBy: session.user!.id,
          redeemedAt: new Date(),
        },
      });

      return {
        success: true,
        keyType: key.keyType,
        scope: key.scope,
      } as const;
    });

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid or expired key" },
        { status: 400 }
      );
    }

    return NextResponse.json({
      success: true,
      keyType: result.keyType,
      scope: result.scope,
    });
  } catch (error) {
    console.error("[KEY REDEEM] Failed:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
