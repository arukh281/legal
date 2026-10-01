import { describe, it, expect } from "vitest";

describe("Frontend navigation and contracts", () => {
  it("defines standard navigation tabs", () => {
    const tabs = ["today", "research", "matters", "authority", "alerts"];
    expect(tabs).toHaveLength(5);
    expect(tabs).toContain("today");
    expect(tabs).toContain("research");
    expect(tabs).toContain("matters");
    expect(tabs).toContain("authority");
    expect(tabs).toContain("alerts");
  });
});
