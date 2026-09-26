"use client";

import { useCallback, useEffect, useState } from "react";

import * as api from "@/lib/api-client";
import { ApiError } from "@/lib/api-client";
import type { Corpus, CorpusDetail, Document as LexiconDocument } from "@/lib/types";

interface AsyncState<T> {
  data: T | null;
  error: ApiError | Error | null;
  loading: boolean;
}

/** List of the caller's own corpora, plus a way to add one locally after create. */
export function useCorpora() {
  const [state, setState] = useState<AsyncState<Corpus[]>>({
    data: null,
    error: null,
    loading: true,
  });

  const refetch = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    api
      .listCorpora()
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }));
  }, []);

  useEffect(refetch, [refetch]);

  const addCorpus = (corpus: Corpus) => {
    setState((s) => ({ ...s, data: s.data ? [corpus, ...s.data] : [corpus] }));
  };

  return { ...state, refetch, addCorpus };
}

export function useCorpus(corpusId: string) {
  const [state, setState] = useState<AsyncState<CorpusDetail>>({
    data: null,
    error: null,
    loading: true,
  });

  const refetch = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    api
      .getCorpus(corpusId)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }));
  }, [corpusId]);

  useEffect(refetch, [refetch]);

  return { ...state, refetch };
}

export function useDocuments(corpusId: string) {
  const [state, setState] = useState<AsyncState<LexiconDocument[]>>({
    data: null,
    error: null,
    loading: true,
  });

  const refetch = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    api
      .listDocuments(corpusId)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }));
  }, [corpusId]);

  useEffect(refetch, [refetch]);

  return { ...state, refetch };
}
