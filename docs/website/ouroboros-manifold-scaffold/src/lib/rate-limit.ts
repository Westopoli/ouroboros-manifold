// =============================================================================
// Rate Limiter — Per-IP sliding window
// Implements: webapp_architecture_1_00.md § Middleware Stack
//
// In-memory store for development and low-traffic launch.
// Replace with Redis (Upstash) when scaling demands it.
//
// Security purpose: prevents brute-force attacks on magic link requests,
// key redemption, and API endpoints.
// =============================================================================

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

const store = new Map<string, RateLimitEntry>();

// Periodic cleanup to prevent memory leak from accumulated stale entries
const CLEANUP_INTERVAL = 60_000; // 1 minute
setInterval(() => {
  const now = Date.now();
  for (const [key, entry] of store) {
    if (now > entry.resetAt) {
      store.delete(key);
    }
  }
}, CLEANUP_INTERVAL);

export interface RateLimitConfig {
  /** Max requests allowed in the window */
  limit: number;
  /** Window duration in seconds */
  windowSeconds: number;
}

export const RATE_LIMITS = {
  /** Authenticated API routes */
  authenticated: { limit: 60, windowSeconds: 60 } as RateLimitConfig,
  /** Unauthenticated routes (sign-in, magic link) */
  unauthenticated: { limit: 10, windowSeconds: 60 } as RateLimitConfig,
  /** Key redemption — extra restrictive */
  keyRedeem: { limit: 5, windowSeconds: 60 } as RateLimitConfig,
  /** Magic link email send — per email address */
  magicLink: { limit: 3, windowSeconds: 600 } as RateLimitConfig,
} as const;

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: number;
}

/**
 * Check rate limit for a given identifier (IP, email, user ID).
 * Returns whether the request is allowed and how many requests remain.
 */
export function checkRateLimit(
  identifier: string,
  config: RateLimitConfig
): RateLimitResult {
  const now = Date.now();
  const windowMs = config.windowSeconds * 1000;
  const key = `${identifier}:${config.windowSeconds}`;

  const entry = store.get(key);

  // No existing entry or window expired — fresh window
  if (!entry || now > entry.resetAt) {
    const resetAt = now + windowMs;
    store.set(key, { count: 1, resetAt });
    return { allowed: true, remaining: config.limit - 1, resetAt };
  }

  // Within window — increment
  entry.count++;

  if (entry.count > config.limit) {
    return { allowed: false, remaining: 0, resetAt: entry.resetAt };
  }

  return {
    allowed: true,
    remaining: config.limit - entry.count,
    resetAt: entry.resetAt,
  };
}

/**
 * Extract client IP from request headers.
 * Handles Vercel/Cloudflare proxy headers.
 */
export function getClientIp(request: Request): string {
  // Vercel
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) {
    return forwarded.split(",")[0].trim();
  }

  // Cloudflare
  const cfIp = request.headers.get("cf-connecting-ip");
  if (cfIp) return cfIp;

  // Fallback
  return "unknown";
}
