import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it.each([
    ["pass", "positive"],
    ["success", "positive"],
    ["fail", "negative"],
    ["failure", "negative"],
    ["needs_review", "warning"],
    ["pending", "warning"],
    ["something_else", "neutral"],
  ])("renders %s with the %s tone", (value, tone) => {
    render(<StatusBadge value={value} />);

    const badge = screen.getByText(value.replace(/_/g, " "));
    expect(badge).toHaveClass(`badge--${tone}`);
  });

  it("renders an em dash placeholder for a null value", () => {
    render(<StatusBadge value={null} />);

    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
