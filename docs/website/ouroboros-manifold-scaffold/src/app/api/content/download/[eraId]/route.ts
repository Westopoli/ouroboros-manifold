// =============================================================================
// GET /api/content/download/[eraId]
// Implements: webapp_architecture_1_00.md § Content Delivery → Download Flow
//
// Validates entitlement, then generates a short-lived signed R2 URL.
// The server never proxies file bytes — the client downloads from R2 directly.
// =============================================================================

import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { resolveEntitlements } from "@/lib/entitlements";
import { checkRateLimit, getClientIp, RATE_LIMITS } from "@/lib/rate-limit";

// R2 signed URL generation
// Uses AWS S3-compatible presigning since R2 is S3-compatible
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
// Note: @aws-sdk/s3-request-presigner needs to be installed
// import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const SIGNED_URL_EXPIRY = 15 * 60; // 15 minutes

export async function GET(
  request: Request,
  { params }: { params: Promise<{ eraId: string }> }
) {
  const { eraId } = await params;

  const ip = getClientIp(request);
  const limit = checkRateLimit(ip, RATE_LIMITS.authenticated);
  if (!limit.allowed) {
    return NextResponse.json({ error: "Too many requests" }, { status: 429 });
  }

  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 }
    );
  }

  // Validate entitlement
  const entitlements = await resolveEntitlements(session.user.id);
  const hasAccess =
    entitlements.eras.includes("all") || entitlements.eras.includes(eraId);

  if (!hasAccess) {
    return NextResponse.json(
      { error: "You do not have access to this era" },
      { status: 403 }
    );
  }

  try {
    // TODO: Generate signed R2 URLs once R2 bucket is configured.
    // The implementation will use @aws-sdk/client-s3 and
    // @aws-sdk/s3-request-presigner with the R2 endpoint.
    //
    // const s3 = new S3Client({
    //   region: "auto",
    //   endpoint: process.env.R2_ENDPOINT!,
    //   credentials: {
    //     accessKeyId: process.env.R2_ACCESS_KEY_ID!,
    //     secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
    //   },
    // });
    //
    // const manifestUrl = await getSignedUrl(s3,
    //   new GetObjectCommand({
    //     Bucket: process.env.R2_BUCKET!,
    //     Key: `eras/${eraId}/latest/manifest.json`,
    //   }),
    //   { expiresIn: SIGNED_URL_EXPIRY }
    // );

    return NextResponse.json({
      message: "Content delivery not yet configured",
      eraId,
      // manifest_url: manifestUrl,
      // library_url: libraryUrl,
      // assets_url: assetsUrl,
    });
  } catch (error) {
    console.error("[CONTENT] Download URL generation failed:", error);
    return NextResponse.json(
      { error: "Failed to generate download URL" },
      { status: 500 }
    );
  }
}
