// =============================================================================
// Auth Configuration — NextAuth.js v5 (Auth.js)
// Implements: webapp_architecture_1_00.md § Authentication
//
// Security principles:
// - No passwords. All identity is delegated to trusted providers.
// - Auto-link only on verified email. Unverified providers require manual link.
// - Steam synthetic emails are NEVER used for auto-linking.
// - HttpOnly + Secure + SameSite=Lax cookies.
// - JWT strategy — no server-side session store.
// - CSRF protection built into NextAuth.
//
// Steam integration:
// Steam uses OpenID 2.0 (not OAuth2). The authjs-steam-provider package
// handles the assertion exchange and profile enrichment. Steam does NOT
// provide a real email — the provider generates a synthetic one
// (steamid@steamcommunity.com). We strip this in the signIn callback
// to prevent it from polluting the user record or triggering auto-link.
// =============================================================================

import NextAuth from "next-auth";
import { PrismaAdapter } from "@auth/prisma-adapter";
import Google from "next-auth/providers/google";
import Discord from "next-auth/providers/discord";
import Apple from "next-auth/providers/apple";
import Resend from "next-auth/providers/resend";
import SteamProvider from "authjs-steam-provider";
import type { NextAuthConfig } from "next-auth";
import { prisma } from "@/lib/db";

// Synthetic email domain used by the Steam provider — never trust for linking
const STEAM_SYNTHETIC_EMAIL_DOMAIN = "@steamcommunity.com";

/**
 * Build the auth config. The Steam provider requires the incoming Request
 * object to validate the OpenID assertion, so providers must be constructed
 * per-request in the route handler.
 */
function buildAuthConfig(req?: Request): NextAuthConfig {
  // Base providers that don't need the request
  const providers: NextAuthConfig["providers"] = [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code",
        },
      },
    }),

    Discord({
      clientId: process.env.DISCORD_CLIENT_ID!,
      clientSecret: process.env.DISCORD_CLIENT_SECRET!,
    }),

    Apple({
      clientId: process.env.APPLE_CLIENT_ID!,
      clientSecret: process.env.APPLE_CLIENT_SECRET!,
    }),

    // Magic link email — no passwords
    Resend({
      apiKey: process.env.RESEND_API_KEY!,
      from: process.env.EMAIL_FROM || "noreply@ouroborosmanifold.com",
    }),
  ];

  // Steam requires the Request for OpenID assertion validation.
  // Only add when we have a request (route handler context).
  if (req) {
    providers.push(
      SteamProvider(req, {
        clientSecret: process.env.STEAM_API_KEY!,
        callbackUrl: `${process.env.NEXTAUTH_URL}/api/auth/callback`,
      })
    );
  }

  return {
    adapter: PrismaAdapter(prisma),
    providers,

    session: {
      strategy: "jwt",
      maxAge: 30 * 24 * 60 * 60, // 30 days for web sessions
    },

    cookies: {
      sessionToken: {
        name: "om-session",
        options: {
          httpOnly: true,
          sameSite: "lax",
          path: "/",
          secure: process.env.NODE_ENV === "production",
        },
      },
    },

    pages: {
      signIn: "/account",
      error: "/account",
      verifyRequest: "/account/verify",
    },

    callbacks: {
      // -----------------------------------------------------------------
      // Account linking policy — security-critical
      //
      // Rules:
      // 1. Steam: NEVER auto-link. Steam provides no real email.
      //    The synthetic email is stripped to null so it can't match.
      // 2. Google/Apple: auto-link on verified email (provider-verified).
      // 3. Discord: auto-link only if Discord email is verified.
      // 4. Magic link: auto-link (the email itself IS the verification).
      // 5. Unverified email from any provider: block auto-link.
      // -----------------------------------------------------------------
      async signIn({ user, account, profile }) {
        if (!account) return true;

        // --- Steam: strip synthetic email ---
        // The Steam provider generates "steamid@steamcommunity.com" which
        // is not a real email. If we let it through, it could:
        // a) Pollute the user record with a fake email
        // b) Accidentally match if two Steam users have adjacent IDs
        //    (extremely unlikely but defense-in-depth)
        // We null it out so the user record has no email until they link
        // a real provider or add one manually.
        if (account.provider === "steam" && user.email?.endsWith(STEAM_SYNTHETIC_EMAIL_DOMAIN)) {
          user.email = null;
          return true; // Allow sign-in, but with no email for linking
        }

        // --- Other providers: check email verification ---
        const emailVerified =
          account.provider === "google"
            ? (profile as Record<string, unknown>)?.email_verified === true
            : account.provider === "discord"
              ? (profile as Record<string, unknown>)?.verified === true
              : account.provider === "apple"
                ? true // Apple always verifies
                : account.provider === "resend"
                  ? true // Magic link IS the verification
                  : false; // Unknown provider — don't trust

        // If email is not verified, block auto-link to existing accounts
        if (!emailVerified && user.email) {
          const existingUser = await prisma.user.findUnique({
            where: { email: user.email },
          });
          if (existingUser) {
            return false; // Must link manually from account settings
          }
        }

        return true;
      },

      // Include user ID and Steam ID in the JWT
      async jwt({ token, user, account, profile }) {
        if (user?.id) {
          token.userId = user.id;
        }
        // Persist Steam profile data in the token for the session
        if (account?.provider === "steam" && profile) {
          token.steamId = (profile as Record<string, unknown>).steamid;
          token.steamAvatar = (profile as Record<string, unknown>).avatarfull;
        }
        return token;
      },

      // Expose user ID (and Steam data if applicable) in the session
      async session({ session, token }) {
        if (token.userId && session.user) {
          session.user.id = token.userId as string;
        }
        return session;
      },
    },

    // Security events — log for monitoring
    events: {
      async signIn({ user, account }) {
        console.log(
          `[AUTH] Sign in: user=${user.id} provider=${account?.provider}`
        );
      },
      async signOut({ token }) {
        console.log(`[AUTH] Sign out: user=${token?.userId}`);
      },
      async linkAccount({ user, account }) {
        console.log(
          `[AUTH] Account linked: user=${user.id} provider=${account.provider}`
        );
      },
    },
  };
}

// ---------------------------------------------------------------------------
// Export the default config (without request — for middleware/server checks)
// and a request-aware version for the route handler.
// ---------------------------------------------------------------------------

// For middleware, server components, and non-route-handler contexts
const defaultConfig = buildAuthConfig();
export const { auth, signIn, signOut } = NextAuth(defaultConfig);

// For the route handler — must pass the request for Steam OpenID
export function buildHandlers(req: Request) {
  return NextAuth(buildAuthConfig(req)).handlers;
}
