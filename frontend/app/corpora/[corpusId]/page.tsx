"use client";

import Link from "next/link";
import { use } from "react";

import { ApiErrorMessage } from "@/components/ApiErrorMessage";
import { DocumentList } from "@/components/DocumentList";
import { QueryPanel } from "@/components/QueryPanel";
import { UploadForm } from "@/components/UploadForm";
import { useCorpus, useDocuments } from "@/lib/hooks";

export default function CorpusPage({
  params,
}: {
  params: Promise<{ corpusId: string }>;
}) {
  const { corpusId } = use(params);
  const corpus = useCorpus(corpusId);
  const documents = useDocuments(corpusId);

  const refreshAll = () => {
    corpus.refetch();
    documents.refetch();
  };

  return (
    <main>
      <p>
        <Link href="/">&larr; All corpora</Link>
      </p>

      {corpus.loading ? <p className="muted">Loading corpus…</p> : null}
      {corpus.error ? <ApiErrorMessage error={corpus.error} /> : null}

      {corpus.data ? (
        <>
          <h1>{corpus.data.name}</h1>
          <p className="muted">{corpus.data.document_count} documents</p>

          <section>
            <h2>Documents</h2>
            <UploadForm corpusId={corpusId} onUploaded={refreshAll} />
            {documents.loading ? <p className="muted">Loading documents…</p> : null}
            {documents.error ? <ApiErrorMessage error={documents.error} /> : null}
            {documents.data ? (
              <DocumentList
                corpusId={corpusId}
                documents={documents.data}
                onChanged={refreshAll}
              />
            ) : null}
          </section>

          <section>
            <h2>Ask</h2>
            <QueryPanel corpusId={corpusId} />
          </section>
        </>
      ) : null}
    </main>
  );
}
