import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backend";

// Reuses the generic proxy: with no session cookie set, proxyToBackend
// sends no Authorization header at all, and the backend correctly responds
// 401 unauthenticated — there is no separate "am I logged in" check to keep
// in sync with the backend's own verification.
export async function GET(request: NextRequest) {
  return proxyToBackend(request, "/api/v1/auth/me", { method: "GET" });
}
