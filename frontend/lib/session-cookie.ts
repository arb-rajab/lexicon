// ADR-0005 — the session token (a backend-issued JWT) lives only in an
// httpOnly cookie this server sets and reads; page JavaScript never has
// access to it (no localStorage, no readable cookie), which is the actual
// reason forwarding it in lib/backend.ts isn't a repeat of the old
// client-controlled-X-User-Id-header trust mistake.
export const SESSION_COOKIE = "lexicon_session";

interface SessionCookieOptions {
  httpOnly: boolean;
  secure: boolean;
  sameSite: "lax";
  path: string;
  maxAge: number;
}

export function sessionCookieOptions(maxAgeSeconds: number): SessionCookieOptions {
  return {
    httpOnly: true,
    // NOT tied to NODE_ENV: `next start` (docker-compose.prod.yml's
    // production build) sets NODE_ENV=production regardless of whether TLS
    // terminates in front of it, and neither compose stack in this
    // repository ever does (ADR-0005's own accepted trade-off,
    // 08-deployment-and-operations.md's TLS descoping) — a `Secure` cookie
    // served over plain HTTP is silently dropped by the browser, which
    // would have broken login on the "production-shaped" stack specifically
    // while looking fine in dev. `COOKIE_SECURE=true` is the real signal to
    // flip this, set only once this app is actually served over HTTPS.
    secure: process.env.COOKIE_SECURE === "true",
    sameSite: "lax",
    path: "/",
    maxAge: maxAgeSeconds,
  };
}
