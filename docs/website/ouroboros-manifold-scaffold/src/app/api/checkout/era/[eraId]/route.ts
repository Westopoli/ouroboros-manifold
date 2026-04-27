// =============================================================================
// POST /api/checkout/era/[eraId]
// Creates a Stripe Checkout session for one-time era pack purchase.
// =============================================================================

import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { stripe } from "@/lib/stripe";
import { prisma } from "@/lib/db";
import { checkRateLimit, getClientIp, RATE_LIMITS } from "@/lib/rate-limit";

// Era → Stripe Price ID mapping. In production, store in DB or config.
const ERA_PRICES: Record<string, string> = {
  // Populated from Stripe Dashboard price IDs
  // "settled-reach": "price_xxx",
  // "1980s": "price_yyy",
};

export async function POST(
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

  const priceId = ERA_PRICES[eraId];
  if (!priceId) {
    return NextResponse.json(
      { error: "Era not found or not available for purchase" },
      { status: 404 }
    );
  }

  try {
    const user = await prisma.user.findUnique({
      where: { id: session.user.id },
    });

    let stripeCustomerId = user?.stripeCustomerId;

    if (!stripeCustomerId) {
      const customer = await stripe.customers.create({
        email: user?.email || undefined,
        metadata: { user_id: session.user.id },
      });
      stripeCustomerId = customer.id;

      await prisma.user.update({
        where: { id: session.user.id },
        data: { stripeCustomerId: customer.id },
      });
    }

    // Check if user already owns this era
    const existingPurchase = await prisma.purchase.findFirst({
      where: { userId: session.user.id, eraId },
    });

    if (existingPurchase) {
      return NextResponse.json(
        { error: "You already own this era" },
        { status: 409 }
      );
    }

    const checkoutSession = await stripe.checkout.sessions.create({
      customer: stripeCustomerId,
      mode: "payment",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${process.env.NEXTAUTH_URL}/library?purchase=success&era=${eraId}`,
      cancel_url: `${process.env.NEXTAUTH_URL}/era-library?purchase=canceled`,
      metadata: {
        user_id: session.user.id,
        era_id: eraId,
      },
    });

    return NextResponse.json({ url: checkoutSession.url });
  } catch (error) {
    console.error("[CHECKOUT] Era purchase failed:", error);
    return NextResponse.json(
      { error: "Failed to create checkout session" },
      { status: 500 }
    );
  }
}
