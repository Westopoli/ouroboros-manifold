// =============================================================================
// POST /api/webhooks/stripe
// Implements: webapp_architecture_1_00.md § Stripe Integration → Webhook Events
//
// Security:
// - Validates Stripe signature on every request (rejects spoofed payloads)
// - Idempotent — safe to receive the same event multiple times
// - No session/CSRF middleware (Stripe can't send cookies)
// - Rate limiting not applied (Stripe controls send rate)
// =============================================================================

import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { prisma } from "@/lib/db";
import type Stripe from "stripe";

export async function POST(request: Request) {
  const body = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    console.error("[STRIPE WEBHOOK] Missing stripe-signature header");
    return NextResponse.json(
      { error: "Missing signature" },
      { status: 400 }
    );
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error(`[STRIPE WEBHOOK] Signature verification failed: ${message}`);
    return NextResponse.json(
      { error: "Invalid signature" },
      { status: 400 }
    );
  }

  try {
    switch (event.type) {
      case "checkout.session.completed":
        await handleCheckoutCompleted(
          event.data.object as Stripe.Checkout.Session
        );
        break;

      case "customer.subscription.updated":
        await handleSubscriptionUpdated(
          event.data.object as Stripe.Subscription
        );
        break;

      case "customer.subscription.deleted":
        await handleSubscriptionDeleted(
          event.data.object as Stripe.Subscription
        );
        break;

      case "invoice.payment_failed":
        await handlePaymentFailed(event.data.object as Stripe.Invoice);
        break;

      case "invoice.paid":
        await handlePaymentSucceeded(event.data.object as Stripe.Invoice);
        break;

      default:
        console.log(`[STRIPE WEBHOOK] Unhandled event type: ${event.type}`);
    }
  } catch (error) {
    console.error(`[STRIPE WEBHOOK] Handler error for ${event.type}:`, error);
    // Return 500 so Stripe retries
    return NextResponse.json(
      { error: "Webhook handler failed" },
      { status: 500 }
    );
  }

  return NextResponse.json({ received: true });
}

// ---------------------------------------------------------------------------
// Event Handlers — all idempotent
// ---------------------------------------------------------------------------

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  const userId = session.metadata?.user_id;
  if (!userId) {
    console.error("[STRIPE WEBHOOK] checkout.session.completed missing user_id metadata");
    return;
  }

  if (session.mode === "subscription" && session.subscription) {
    const sub = await stripe.subscriptions.retrieve(
      session.subscription as string
    );

    // Upsert — idempotent if we receive this event twice
    await prisma.subscription.upsert({
      where: { userId },
      create: {
        userId,
        stripeSubscriptionId: sub.id,
        status: mapStripeStatus(sub.status),
        currentPeriodStart: new Date(sub.current_period_start * 1000),
        currentPeriodEnd: new Date(sub.current_period_end * 1000),
        cancelAtPeriodEnd: sub.cancel_at_period_end,
      },
      update: {
        stripeSubscriptionId: sub.id,
        status: mapStripeStatus(sub.status),
        currentPeriodStart: new Date(sub.current_period_start * 1000),
        currentPeriodEnd: new Date(sub.current_period_end * 1000),
        cancelAtPeriodEnd: sub.cancel_at_period_end,
      },
    });

    console.log(`[STRIPE WEBHOOK] Subscription created for user ${userId}`);
  }

  if (session.mode === "payment") {
    const eraId = session.metadata?.era_id;
    const paymentIntentId = session.payment_intent as string;

    if (!eraId || !paymentIntentId) {
      console.error("[STRIPE WEBHOOK] Era purchase missing metadata");
      return;
    }

    // Upsert on payment_intent — idempotent
    const existing = await prisma.purchase.findUnique({
      where: { stripePaymentIntentId: paymentIntentId },
    });

    if (!existing) {
      await prisma.purchase.create({
        data: {
          userId,
          eraId,
          stripePaymentIntentId: paymentIntentId,
          amountCents: session.amount_total || 0,
          currency: session.currency || "usd",
        },
      });
      console.log(`[STRIPE WEBHOOK] Era purchase recorded: user=${userId} era=${eraId}`);
    }
  }
}

async function handleSubscriptionUpdated(sub: Stripe.Subscription) {
  await prisma.subscription.updateMany({
    where: { stripeSubscriptionId: sub.id },
    data: {
      status: mapStripeStatus(sub.status),
      currentPeriodStart: new Date(sub.current_period_start * 1000),
      currentPeriodEnd: new Date(sub.current_period_end * 1000),
      cancelAtPeriodEnd: sub.cancel_at_period_end,
    },
  });
  console.log(`[STRIPE WEBHOOK] Subscription updated: ${sub.id} → ${sub.status}`);
}

async function handleSubscriptionDeleted(sub: Stripe.Subscription) {
  await prisma.subscription.updateMany({
    where: { stripeSubscriptionId: sub.id },
    data: { status: "canceled" },
  });
  console.log(`[STRIPE WEBHOOK] Subscription deleted: ${sub.id}`);
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  if (invoice.subscription) {
    await prisma.subscription.updateMany({
      where: { stripeSubscriptionId: invoice.subscription as string },
      data: { status: "past_due" },
    });
    console.log(`[STRIPE WEBHOOK] Payment failed for subscription: ${invoice.subscription}`);
  }
}

async function handlePaymentSucceeded(invoice: Stripe.Invoice) {
  if (invoice.subscription) {
    await prisma.subscription.updateMany({
      where: {
        stripeSubscriptionId: invoice.subscription as string,
        status: "past_due",
      },
      data: { status: "active" },
    });
    console.log(`[STRIPE WEBHOOK] Payment recovered for subscription: ${invoice.subscription}`);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mapStripeStatus(
  status: Stripe.Subscription.Status
): "active" | "past_due" | "canceled" | "trialing" | "paused" {
  switch (status) {
    case "active":
      return "active";
    case "past_due":
      return "past_due";
    case "canceled":
    case "unpaid":
    case "incomplete_expired":
      return "canceled";
    case "trialing":
      return "trialing";
    case "paused":
      return "paused";
    default:
      return "canceled";
  }
}
