import type {
  ApiErrorBody,
  Corpus,
  CorpusDetail,
  Document as LexiconDocument,
  DocumentUploadResult,
  QueryResponse,
} from "@/lib/types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly field: string | null;
  readonly retryAfter: number | null;

  constructor(status: number, body: ApiErrorBody, retryAfter: number | null) {
    super(body.error.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error.code;
    this.field = body.error.field;
    this.retryAfter = retryAfter;
  }
}

async function unwrap<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const retryAfterHeader = response.headers.get("retry-after");
    const retryAfter = retryAfterHeader ? Number.parseInt(retryAfterHeader, 10) : null;
    let body: ApiErrorBody;
    try {
      body = await response.json();
    } catch {
      body = { error: { code: "unknown_error", message: response.statusText, field: null } };
    }
    throw new ApiError(response.status, body, retryAfter);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

// No caller-identity header to attach here (ADR-0005): the browser sends
// this app's own httpOnly session cookie automatically on every same-origin
// request, and app/api/**'s route handlers (lib/backend.ts) turn it into
// the real `Authorization: Bearer <token>` the backend verifies.

export async function listCorpora(): Promise<Corpus[]> {
  const res = await fetch("/api/corpora");
  return unwrap(res);
}

export async function createCorpus(name: string): Promise<Corpus> {
  const res = await fetch("/api/corpora", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return unwrap(res);
}

export async function getCorpus(corpusId: string): Promise<CorpusDetail> {
  const res = await fetch(`/api/corpora/${corpusId}`);
  return unwrap(res);
}

export async function listDocuments(corpusId: string): Promise<LexiconDocument[]> {
  const res = await fetch(`/api/corpora/${corpusId}/documents`);
  return unwrap(res);
}

export async function uploadDocument(corpusId: string, file: File): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`/api/corpora/${corpusId}/documents`, {
    method: "POST",
    body: formData,
  });
  return unwrap(res);
}

export async function deleteDocument(corpusId: string, documentId: string): Promise<void> {
  const res = await fetch(`/api/corpora/${corpusId}/documents/${documentId}`, {
    method: "DELETE",
  });
  return unwrap(res);
}

export async function askQuestion(corpusId: string, question: string): Promise<QueryResponse> {
  const res = await fetch(`/api/corpora/${corpusId}/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return unwrap(res);
}
