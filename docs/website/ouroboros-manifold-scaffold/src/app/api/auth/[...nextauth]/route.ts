// =============================================================================
// NextAuth Route Handler — catches all /api/auth/* routes
//
// Steam's OpenID 2.0 provider requires the incoming Request object to
// validate the OpenID assertion. We rebuild the handler per-request
// so Steam can inspect the callback parameters.
// =============================================================================

import { buildHandlers } from "@/lib/auth";

export async function GET(req: Request) {
  const { GET } = buildHandlers(req);
  return GET(req);
}

export async function POST(req: Request) {
  const { POST } = buildHandlers(req);
  return POST(req);
}
