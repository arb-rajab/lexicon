import { NextRequest, NextResponse } from "next/server";

import { BACKEND_URL } from "@/lib/backend";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/session-cookie";

// Mirrors the backend's default `jwt_access_token_expire_minutes`
// (config.py) — best-effort only, not authoritative: the backend
// independently verifies the token's own `exp` claim on every request
// regardless of how long this cookie sticks around, so a mismatch here is a
// stale-cookie UX question (a request goes out with an already-expired
// token, gets a 401, the client re-prompts for login), never a security
// question.
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24;

interface CredentialsTokenResponse {
  access_token: string;
  username: string;
}

/**
 * Shared by app/api/auth/register and /login: both proxy a username/
 * password to the backend, and on success set this app's own httpOnly
 * session cookie from the returned token — the token itself never reaches
 * the browser response body, so page JavaScript can never read it (ADR-0005:
 * this is what makes forwarding the cookie in lib/backend.ts safe, unlike
 * the old client-readable-X-User-Id-header model).
 */
export async function handleCredentialsAuth(
  request: NextRequest,
  backendPath: "/api/v1/auth/register" | "/api/v1/auth/login",
  successStatus: number,
): Promise<NextResponse> {
  const requestBody = await request.text();

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: requestBody,
    });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "backend_unreachable",
          message: "Could not reach the lexicon backend. Is it running?",
          field: null,
        },
      },
      { status: 502 },
    );
  }

  const responseBody = await response.text();
  if (!response.ok) {
    return new NextResponse(responseBody, {
      status: response.status,
      headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
    });
  }

  const { access_token: accessToken, username } = JSON.parse(responseBody) as CredentialsTokenResponse;

  const nextResponse = NextResponse.json({ username }, { status: successStatus });
  nextResponse.cookies.set(
    SESSION_COOKIE,
    accessToken,
    sessionCookieOptions(SESSION_MAX_AGE_SECONDS),
  );
  return nextResponse;
}
