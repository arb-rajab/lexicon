// Mirrors backend/src/lexicon/config.py's max_upload_size_bytes default
// (10 MiB, .env.example: MAX_UPLOAD_SIZE_BYTES=10485760). This is only used
// for immediate client-side feedback before a file is even sent — the
// backend's own bounded read (api/documents.py) is the real, authoritative
// enforcement and returns 413 regardless of what this constant says.
export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024;

// Mirrors backend/src/lexicon/config.py's max_question_length default
// (.env.example: MAX_QUESTION_LENGTH=1000). Same caveat as above: the
// backend's own check (api/query.py, 422 question_too_long) is authoritative.
export const MAX_QUESTION_LENGTH = 1000;
