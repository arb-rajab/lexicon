import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ corpusId: string }> },
) {
  const { corpusId } = await params;
  return proxyToBackend(request, `/api/v1/corpora/${corpusId}/documents`, { method: "GET" });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ corpusId: string }> },
) {
  const { corpusId } = await params;
  const contentType = request.headers.get("content-type") ?? "";
  const body = await request.arrayBuffer();
  return proxyToBackend(request, `/api/v1/corpora/${corpusId}/documents`, {
    method: "POST",
    headers: { "content-type": contentType },
    body,
  });
}
