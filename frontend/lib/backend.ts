import { NextRequest, NextResponse } from "next/server";

// Server-side only: the real lexicon backend, never exposed to the browser
// directly. Route handlers under app/api/** proxy to it so the browser only
// ever talks same-origin to this Next.js server — the backend has no CORS
// middleware (see backend/src/lexicon/main.py), so a direct browser->backend
// fetch across ports would be blocked anyway.
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

/**
 * Forwards a request to the backend, passing through the caller-supplied
 * X-User-Id header (the entire auth model — see backend/src/lexicon/api/auth.py)
 * and relaying the backend's status code, body and Retry-After header
 * unchanged so the browser sees the real contract.
 */
export async function proxyToBackend(
  request: NextRequest,
  path: string,
  init?: RequestInit,
): Promise<NextResponse> {
  const userId = request.headers.get("x-user-id");
  const headers = new Headers(init?.headers);
  if (userId) headers.set("x-user-id", userId);

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
