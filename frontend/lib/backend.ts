import { NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/session-cookie";

// Server-side only: the real lexicon backend, never exposed to the browser
// directly. Route handlers under app/api/** proxy to it so the browser only
// ever talks same-origin to this Next.js server — the backend has no CORS
// middleware (see backend/src/lexicon/main.py), so a direct browser->backend
// fetch across ports would be blocked anyway.
export const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

/**
 * Forwards a request to the backend, attaching the caller's session token
 * (ADR-0005) as `Authorization: Bearer <token>` — read from this app's own
 * httpOnly session cookie, never from anything the browser's JavaScript can
 * see or set directly. Before ADR-0005, this function forwarded a
 * caller-supplied `X-User-Id` header verbatim, which was the entire
 * client-side half of the impersonation vulnerability that ADR fixes: any
 * value a page's JavaScript (or a direct API call) put in that header was
 * trusted as-is. There is no equivalent client-controlled input here — the
 * cookie is `httpOnly` (set only by app/api/auth/*'s route handlers) and its
 * value is itself a signed token the backend independently verifies, so
 * forwarding it is not a repeat of the same trust mistake.
 *
 * Relays the backend's status code, body and Retry-After header unchanged
 * so the browser sees the real contract.
 */
export async function proxyToBackend(
  request: NextRequest,
  path: string,
  init?: RequestInit,
): Promise<NextResponse> {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  const headers = new Headers(init?.headers);
  if (token) headers.set("authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      ...init,
      headers,
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

  const body = await response.text();
  const responseHeaders = new Headers();
  const contentType = response.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);
  const retryAfter = response.headers.get("retry-after");
  if (retryAfter) responseHeaders.set("retry-after", retryAfter);

  return new NextResponse(body, {
    status: response.status,
    headers: responseHeaders,
  });
}
