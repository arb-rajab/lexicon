"use client";

import Link from "next/link";

import { useCorpora } from "@/lib/hooks";

import { ApiErrorMessage } from "./ApiErrorMessage";
import { CorpusCreateForm } from "./CorpusCreateForm";

export function CorpusList() {
  const { data, error, loading, addCorpus } = useCorpora();

  return (
    <section>
      <CorpusCreateForm onCreated={addCorpus} />

      {loading ? <p className="muted">Loading corpora…</p> : null}
      {error ? <ApiErrorMessage error={error} /> : null}

      {!loading && !error && data?.length === 0 ? (
        <p className="muted">No corpora yet — create one above to get started.</p>
      ) : null}

      {data && data.length > 0 ? (
        <ul className="corpus-list">
          {data.map((corpus) => (
            <li key={corpus.id}>
              <Link href={`/corpora/${corpus.id}`} className="corpus-list__item">
                <span className="corpus-list__name">{corpus.name}</span>
                <span className="muted">
                  {new Date(corpus.created_at).toLocaleDateString()}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
