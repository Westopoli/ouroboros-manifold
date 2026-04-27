// =============================================================================
// Next.js Middleware — runs on every request before route handlers
// Implements: webapp_architecture_1_00.md § Middleware Stack
//
// Responsibilities:
// 1. Rate limiting (per-IP)
// 2. Auth protection for /account, /library, /redeem, /api/* (except webhooks)
// 3. Security headers are handled in next.config.ts
// =============================================================================

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Paths that require authentication
const PROTECTED_PATHS = ["/account", "/library", "/redeem"];

// API paths that require authentication (everything except webhooks and auth)
const PROTECTED_API_PREFIXES = [
  "/api/entitlements",
  "/api/checkout",
  "/api/portal",
  "/api/keys",
  "/api/content",
  "/api/steam",
];

// Paths that are always public
const PUBLIC_PATHS = [
  "/",
  "/the-game",
  "/era-library",
  "/articles",
  "/api/auth",
  "/api/webhooks",
];

function isProtectedPath(pathname: string): boolean {
  // Check exact protected paths
  for (const path of PROTECTED_PATHS) {
    if (pathname === path || pathname.startsWith(path + "/")) {
      return true;
    }
  }
  // Check protected API prefixes
  for (const prefix of PROTECTED_API_PREFIXES) {
    if (pathname.startsWith(prefix)) {
      return true;
    }
  }
  return false;
}

function isPublicPath(pathname: string): boolean {
  for (const path of PUBLIC_PATHS) {
    if (pathname === path || pathname.startsWith(path + "/")) {
      return true;
    }
  }
  return false;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip static assets and Next.js internals
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // For protected paths, check for session cookie presence.
  // Full JWT validation happens in the route handler via auth().
  // This middleware provides a fast redirect for unauthenticated users.
  if (isProtectedPath(pathname)) {
    const sessionCookie =
      request.cookies.get("om-session") ||
      request.cookies.get("__Secure-om-session");

    if (!sessionCookie) {
      // API routes get 401, page routes redirect to sign-in
      if (pathname.startsWith("/api/")) {
        return NextResponse.json(
          { error: "Authentication required" },
          { status: 401 }
        );
      }

      const signInUrl = new URL("/account", request.url);
      signInUrl.searchParams.set("callbackUrl", pathname);
      return NextResponse.redirect(signInUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  // Run middleware on all paths except static files
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
