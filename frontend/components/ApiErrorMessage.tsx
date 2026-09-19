import { ApiError } from "@/lib/api-client";

const FRIENDLY_MESSAGE: Record<string, string> = {
  unauthenticated: "You need an identity set before doing that.",
  forbidden: "You don't have access to this corpus.",
  not_found: "That resource doesn't exist.",
  file_too_large: "That file is larger than the upload limit.",
  unsupported_document_type: "That file type isn't supported.",
  question_too_long: "Your question is too long.",
  rate_limited: "Too many queries too fast — slow down and try again.",
  spend_ceiling_exceeded: "This corpus has hit its daily query limit.",
  llm_provider_error: "The answer engine failed to respond. Try again shortly.",
  validation_error: "That request wasn't valid.",
};

export function describeApiError(error: unknown): string {
  if (error instanceof ApiError) {
    const friendly = FRIENDLY_MESSAGE[error.code];
    const suffix =
      error.retryAfter != null ? ` (retry in ${error.retryAfter}s)` : "";
    return `${friendly ?? error.message}${suffix}`;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

export function ApiErrorMessage({ error }: { error: unknown }) {
  return (
    <p role="alert" className="error-banner">
      {describeApiError(error)}
    </p>
  );
}
