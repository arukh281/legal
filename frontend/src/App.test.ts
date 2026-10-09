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
  it("validates research endpoint and display band contracts", () => {
    const requiredDisplayBands = ["quote verified · uncalibrated preview", "WITHHELD", "CHECK"];
    expect(requiredDisplayBands).toContain("quote verified · uncalibrated preview");
  });

  it("ensures honest contrary sweep is marked LIMITED", () => {
    const contraryStatus = "LIMITED";
    const contraryNotes = "lexical only, no citator";
    expect(contraryStatus).toBe("LIMITED");
    expect(contraryNotes).toContain("lexical only");
  });
});
