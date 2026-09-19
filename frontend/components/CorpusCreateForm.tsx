"use client";

import { useState } from "react";

import * as api from "@/lib/api-client";
import { useIdentity } from "@/lib/identity";
import type { Corpus } from "@/lib/types";

import { ApiErrorMessage } from "./ApiErrorMessage";

export function CorpusCreateForm({ onCreated }: { onCreated: (corpus: Corpus) => void }) {
  const { userId } = useIdentity();
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setSubmitting(true);
    setError(null);
    try {
      const corpus = await api.createCorpus(userId, trimmed);
      onCreated(corpus);
      setName("");
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="corpus-create-form">
      <label htmlFor="corpus-name">New corpus</label>
      <div className="corpus-create-form__row">
        <input
          id="corpus-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. product-docs"
          disabled={submitting}
        />
        <button type="submit" disabled={submitting || !name.trim()}>
          {submitting ? "Creating…" : "Create"}
        </button>
      </div>
      {error ? <ApiErrorMessage error={error} /> : null}
    </form>
  );
}
