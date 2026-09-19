import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { UploadForm } from "@/components/UploadForm";
import { IdentityProvider } from "@/lib/identity";

function renderForm(onUploaded = vi.fn()) {
  render(
    <IdentityProvider>
      <UploadForm corpusId="corpus-1" onUploaded={onUploaded} />
    </IdentityProvider>,
  );
  return onUploaded;
}

async function waitForHydration() {
  await waitFor(() => expect(screen.getByLabelText(/upload a document/i)).toBeInTheDocument());
}

describe("UploadForm", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("rejects an oversized file client-side without calling the backend", async () => {
    const user = userEvent.setup();
    const onUploaded = renderForm();
    await waitForHydration();

    const oversized = new File([new Uint8Array(11 * 1024 * 1024)], "huge.txt", {
      type: "text/plain",
    });

    await user.upload(screen.getByLabelText(/upload a document/i), oversized);

    expect(await screen.findByRole("alert")).toHaveTextContent(/over the 10\.0 MB upload limit/i);
    expect(fetch).not.toHaveBeenCalled();
    expect(onUploaded).not.toHaveBeenCalled();
  });

  it("uploads an in-bounds file and calls onUploaded", async () => {
    const user = userEvent.setup();
    const onUploaded = renderForm();
    await waitForHydration();

    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ document_id: "doc-1", status: "ready" }), {
        status: 201,
        headers: { "content-type": "application/json" },
      }),
    );

    const file = new File(["hello world"], "doc.txt", { type: "text/plain" });
    await user.upload(screen.getByLabelText(/upload a document/i), file);

    await waitFor(() => expect(onUploaded).toHaveBeenCalledTimes(1));
    expect(fetch).toHaveBeenCalledWith(
      "/api/corpora/corpus-1/documents",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("surfaces a 413 from the backend when the client-side check is bypassed", async () => {
    const user = userEvent.setup();
    renderForm();
    await waitForHydration();

    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "file_too_large",
            message: "Uploaded file exceeds the 10485760-byte limit",
            field: "file",
          },
        }),
        { status: 413, headers: { "content-type": "application/json" } },
      ),
    );

    const file = new File(["small but backend disagrees"], "doc.txt", { type: "text/plain" });
    await user.upload(screen.getByLabelText(/upload a document/i), file);

    expect(await screen.findByRole("alert")).toHaveTextContent(/larger than the upload limit/i);
  });
});
