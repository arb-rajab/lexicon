import { NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/session-cookie";

// ADR-0005 accepted trade-off: session tokens are not server-side
// revocable (no refresh-token/blocklist mechanism). "Logout" here means
// exactly what it can honestly mean given that — this browser stops
// sending the token — not that the token itself is invalidated early.
export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
