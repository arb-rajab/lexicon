"use client";

import { useRef, useState } from "react";

import * as api from "@/lib/api-client";
import { MAX_UPLOAD_SIZE_BYTES } from "@/lib/constants";

import { ApiErrorMessage } from "./ApiErrorMessage";

function formatBytes(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadForm({
  corpusId,
  onUploaded,
}: {
  corpusId: string;
  onUploaded: () => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [rejection, setRejection] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setRejection(null);

    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      setRejection(
        `"${file.name}" is ${formatBytes(file.size)}, which is over the ${formatBytes(MAX_UPLOAD_SIZE_BYTES)} upload limit.`,
      );
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setUploading(true);
    try {
      await api.uploadDocument(corpusId, file);
      onUploaded();
    } catch (err) {
      setError(err);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className="upload-form">
      <label htmlFor="document-upload">Upload a document</label>
      <input
        id="document-upload"
        ref={inputRef}
        type="file"
        onChange={handleChange}
        disabled={uploading}
      />
      {uploading ? <p className="muted">Uploading…</p> : null}
      {rejection ? (
        <p role="alert" className="error-banner">
          {rejection}
        </p>
      ) : null}
      {error ? <ApiErrorMessage error={error} /> : null}
    </div>
  );
}
