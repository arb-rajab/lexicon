"use client";

import { useState } from "react";

import * as api from "@/lib/api-client";
import { useIdentity } from "@/lib/identity";
import type { Document as LexiconDocument } from "@/lib/types";

import { ApiErrorMessage } from "./ApiErrorMessage";

export function DocumentList({
  corpusId,
  documents,
  onChanged,
}: {
  corpusId: string;
  documents: LexiconDocument[];
  onChanged: () => void;
}) {
  const { userId } = useIdentity();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  const handleDelete = async (documentId: string) => {
    setDeletingId(documentId);
    setError(null);
    try {
      await api.deleteDocument(userId, corpusId, documentId);
      onChanged();
    } catch (err) {
      setError(err);
    } finally {
      setDeletingId(null);
    }
  };

  if (documents.length === 0) {
    return <p className="muted">No documents uploaded yet.</p>;
  }

  return (
    <div>
      {error ? <ApiErrorMessage error={error} /> : null}
      <ul className="document-list">
        {documents.map((doc) => (
          <li key={doc.id} className="document-list__item">
            <span>{doc.source_filename}</span>
            <span className="muted">{doc.chunk_count} chunks</span>
            <button
              type="button"
              onClick={() => handleDelete(doc.id)}
              disabled={deletingId === doc.id}
            >
              {deletingId === doc.id ? "Removing…" : "Remove"}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
