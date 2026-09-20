import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { QueryPanel } from "@/components/QueryPanel";
import { ApiError } from "@/lib/api-client";
import { IdentityProvider } from "@/lib/identity";

function renderPanel() {
  return render(
    <IdentityProvider>
      <QueryPanel corpusId="corpus-1" />
    </IdentityProvider>,
  );
}

async function waitForHydration() {
  // IdentityProvider renders null until its localStorage-read effect runs.
  await waitFor(() => expect(screen.getByLabelText(/ask this corpus/i)).toBeInTheDocument());
}

describe("QueryPanel", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submits a question and renders a grounded answer with citations", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          query_log_id: "log-1",
          answered: true,
          answer: "Rollback is triggered via the deploy CLI.",
          citations: [
            {
              chunk_id: "chunk-1",
              document_id: "doc-1",
              source_filename: "runbook.md",
              section_heading: "Rollback",
              claim_text: "Run `deploy rollback` to revert.",
            },
          ],
          refusal_reason: null,
          retrieved_chunk_count: 3,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    renderPanel();
    await waitForHydration();

    await user.type(screen.getByLabelText(/ask this corpus/i), "How do I roll back?");
    await user.click(screen.getByRole("button", { name: /ask/i }));

    expect(await screen.findByText(/rollback is triggered/i)).toBeInTheDocument();
    expect(screen.getByText(/runbook\.md/)).toBeInTheDocument();

    const [, init] = vi.mocked(fetch).mock.calls[0];
    expect(init?.headers).toMatchObject({ "x-user-id": "demo-user" });
  });

  it("renders a refusal when the pipeline can't ground an answer", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          query_log_id: "log-2",
          answered: false,
          answer: null,
          citations: [],
          refusal_reason: "No retrieved chunk supported a grounded claim.",
          retrieved_chunk_count: 2,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    renderPanel();
    await waitForHydration();

    await user.type(screen.getByLabelText(/ask this corpus/i), "What is the meaning of life?");
    await user.click(screen.getByRole("button", { name: /ask/i }));

    expect(await screen.findByText(/refused to answer/i)).toBeInTheDocument();
    expect(screen.getByText(/no retrieved chunk supported/i)).toBeInTheDocument();
  });

  it("surfaces a 429 rate-limit error with retry-after", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: { code: "rate_limited", message: "Query rate limit exceeded for this corpus", field: null },
        }),
        { status: 429, headers: { "content-type": "application/json", "retry-after": "42" } },
      ),
    );

    renderPanel();
    await waitForHydration();

    await user.type(screen.getByLabelText(/ask this corpus/i), "Another question");
    await user.click(screen.getByRole("button", { name: /ask/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/slow down/i);
    expect(alert).toHaveTextContent(/retry in 42s/i);
  });

  it("surfaces a 403 forbidden error distinctly from other failures", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: { code: "forbidden", message: "Not authorised for this corpus", field: null },
        }),
        { status: 403, headers: { "content-type": "application/json" } },
      ),
    );

    renderPanel();
    await waitForHydration();

    await user.type(screen.getByLabelText(/ask this corpus/i), "Another question");
    await user.click(screen.getByRole("button", { name: /ask/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/don't have access/i);
  });

  it("disables submit and shows an error count once the question is too long", async () => {
    const user = userEvent.setup();
    renderPanel();
    await waitForHydration();

    const textarea = screen.getByLabelText(/ask this corpus/i);
    await user.type(textarea, "a".repeat(1001));

    expect(screen.getByRole("button", { name: /ask/i })).toBeDisabled();
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("ApiError", () => {
  it("carries status, code and retryAfter", () => {
    const err = new ApiError(
      429,
      { error: { code: "rate_limited", message: "slow down", field: null } },
      10,
    );
    expect(err.status).toBe(429);
    expect(err.code).toBe("rate_limited");
    expect(err.retryAfter).toBe(10);
  });
});
