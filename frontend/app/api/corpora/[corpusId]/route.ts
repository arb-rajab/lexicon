import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ corpusId: string }> },
) {
  const { corpusId } = await params;
  return proxyToBackend(request, `/api/v1/corpora/${corpusId}`, { method: "GET" });
}
