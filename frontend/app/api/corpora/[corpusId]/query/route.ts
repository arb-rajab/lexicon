import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ corpusId: string }> },
) {
  const { corpusId } = await params;
  const body = await request.text();
  return proxyToBackend(request, `/api/v1/corpora/${corpusId}/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
