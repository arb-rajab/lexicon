import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ corpusId: string; documentId: string }> },
) {
  const { corpusId, documentId } = await params;
  return proxyToBackend(request, `/api/v1/corpora/${corpusId}/documents/${documentId}`, {
    method: "DELETE",
  });
}
