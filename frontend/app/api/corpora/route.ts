import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function GET(request: NextRequest) {
  return proxyToBackend(request, "/api/v1/corpora", { method: "GET" });
}

export async function POST(request: NextRequest) {
  const body = await request.text();
  return proxyToBackend(request, "/api/v1/corpora", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
