"use client";

import { useState } from "react";

import * as api from "@/lib/api-client";
import { MAX_QUESTION_LENGTH } from "@/lib/constants";
import { useIdentity } from "@/lib/identity";
import type { QueryResponse } from "@/lib/types";

import { ApiErrorMessage } from "./ApiErrorMessage";

export function QueryPanel({ corpusId }: { corpusId: string }) {
  const { userId } = useIdentity();
  const [question, setQuestion] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);

  const overLimit = question.length > MAX_QUESTION_LENGTH;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || overLimit) return;

    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.askQuestion(userId, corpusId, trimmed);
      setResult(response);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="query-panel">
      <form onSubmit={handleSubmit}>
        <label htmlFor="question">Ask this corpus a question</label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
          disabled={submitting}
          placeholder="What does the deployment runbook say about rollback?"
        />
        <div className="query-panel__meta">
          <span className={overLimit ? "error-text" : "muted"}>
            {question.length} / {MAX_QUESTION_LENGTH}
          </span>
          <button type="submit" disabled={submitting || !question.trim() || overLimit}>
            {submitting ? "Asking…" : "Ask"}
          </button>
        </div>
      </form>

      {error ? <ApiErrorMessage error={error} /> : null}

      {result ? <QueryResult result={result} /> : null}
    </section>
  );
}

function QueryResult({ result }: { result: QueryResponse }) {
  if (!result.answered) {
    return (
      <div className="query-result query-result--refused">
        <p>
          <strong>Refused to answer.</strong> {result.refusal_reason}
        </p>
        <p className="muted">
          Retrieved {result.retrieved_chunk_count} chunk
          {result.retrieved_chunk_count === 1 ? "" : "s"}, none supported a grounded answer.
        </p>
      </div>
    );
  }

  return (
    <div className="query-result">
      <p className="query-result__answer">{result.answer}</p>
      {result.citations.length > 0 ? (
        <ul className="citation-list">
          {result.citations.map((c) => (
            <li key={c.chunk_id}>
              <span className="citation-list__source">
                {c.source_filename}
                {c.section_heading ? ` — ${c.section_heading}` : ""}
              </span>
              <span className="muted">{c.claim_text}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
