// Mirrors backend/src/lexicon/api/schemas.py — keep in sync with that file,
// not with any Next.js-side assumption about shape.

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    field: string | null;
  };
}

export interface Corpus {
  id: string;
  name: string;
  created_at: string;
}

export interface CorpusDetail extends Corpus {
  document_count: number;
}

export interface Document {
  id: string;
  source_filename: string;
  version: number;
  status: string;
  chunk_count: number;
}

export interface DocumentUploadResult {
  document_id: string;
  status: string;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  source_filename: string;
  section_heading: string;
  claim_text: string;
}

export interface QueryResponse {
  query_log_id: string;
  answered: boolean;
  answer: string | null;
  citations: Citation[];
  refusal_reason: string | null;
  retrieved_chunk_count: number;
}
