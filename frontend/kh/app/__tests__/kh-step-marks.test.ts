// KH: the marks Kochheft puts into step texts (tap a time, amounts in brackets; D39, D42) survive Mealie's sanitizer,
// which drops every other class (v1.1, Mealie 3.31).
import { describe, expect, test } from "vitest";
import { renderMarkdown } from "~/lib/sanitize";

describe("step marks", () => {
  test("keep their class", () => {
    const html = renderMarkdown("Backen <span class=\"kh-time\">20 Min.</span> mit <span class=\"kh-amount\">(200 g)</span>");
    expect(html).toContain("<span class=\"kh-time\">20 Min.</span>");
    expect(html).toContain("<span class=\"kh-amount\">(200 g)</span>");
  });

  test("never carry another class along", () => {
    expect(renderMarkdown("<span class=\"position-fixed\">x</span>")).not.toContain("class");
    expect(renderMarkdown("<span class=\"kh-time position-fixed\">x</span>")).not.toContain("class");
  });
});
