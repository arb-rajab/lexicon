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

function authHeaders(userId: string): HeadersInit {
  return { "x-user-id": userId };
}

export async function listCorpora(userId: string): Promise<Corpus[]> {
  const res = await fetch("/api/corpora", { headers: authHeaders(userId) });
  return unwrap(res);
}

export async function createCorpus(userId: string, name: string): Promise<Corpus> {
  const res = await fetch("/api/corpora", {
    method: "POST",
    headers: { ...authHeaders(userId), "content-type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return unwrap(res);
}

export async function getCorpus(userId: string, corpusId: string): Promise<CorpusDetail> {
  const res = await fetch(`/api/corpora/${corpusId}`, { headers: authHeaders(userId) });
  return unwrap(res);
}

export async function listDocuments(userId: string, corpusId: string): Promise<LexiconDocument[]> {
  const res = await fetch(`/api/corpora/${corpusId}/documents`, { headers: authHeaders(userId) });
  return unwrap(res);
}

export async function uploadDocument(
  userId: string,
  corpusId: string,
  file: File,
): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`/api/corpora/${corpusId}/documents`, {
    method: "POST",
    headers: authHeaders(userId),
    body: formData,
  });
  return unwrap(res);
}

export async function deleteDocument(
  userId: string,
  corpusId: string,
  documentId: string,
): Promise<void> {
  const res = await fetch(`/api/corpora/${corpusId}/documents/${documentId}`, {
    method: "DELETE",
    headers: authHeaders(userId),
  });
  return unwrap(res);
}

export async function askQuestion(
  userId: string,
  corpusId: string,
  question: string,
): Promise<QueryResponse> {
  const res = await fetch(`/api/corpora/${corpusId}/query`, {
    method: "POST",
    headers: { ...authHeaders(userId), "content-type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return unwrap(res);
}
