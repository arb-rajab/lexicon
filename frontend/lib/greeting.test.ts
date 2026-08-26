import { describe, expect, it } from "vitest";

import { greet } from "./greeting";

describe("greet", () => {
  it("greets by name", () => {
    expect(greet("lexicon")).toBe("Hello, lexicon");
  });
});
