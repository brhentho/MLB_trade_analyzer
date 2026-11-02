import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { PlayerSummary } from "@/lib/types";
import { PlayerTable } from "./PlayerTable";

const make = (id: number, name: string, war: number, salary: number, verified = true): PlayerSummary => ({
  id,
  name,
  team: "SEA",
  team_id: 136,
  group: "hitter",
  position: "SS",
  role: "SS",
  bats: "R",
  throws: "R",
  age: 27,
  ratings: { contact: 55, power: 60, eye: 50, speed: 45, glove: null, arm: 50 },
  ovr: 55,
  pot: 58,
  war,
  proj_war: war,
  surplus: 10,
  archetypes: [],
  map: null,
  contract: { status: "guaranteed", salary_now: salary, aav: salary, control_through: 2029, verified },
});

const players = [make(1, "Alpha", 1.0, 20), make(2, "Bravo", 4.0, 1), make(3, "Charlie", 2.5, 8, false)];

const names = () =>
  within(screen.getAllByRole("rowgroup")[1]!)
    .getAllByRole("rowheader")
    .map((r) => r.textContent);

describe("PlayerTable", () => {
  it("sorts by sWAR descending by default and toggles direction", () => {
    render(<PlayerTable group="hitter" players={players} planSeason={2027} caption="Test" />);
    expect(names()).toEqual(["Bravo", "Charlie", "Alpha"]);
    fireEvent.click(screen.getByRole("button", { name: /sWAR/ }));
    expect(names()).toEqual(["Alpha", "Charlie", "Bravo"]);
  });

  it("sorts by salary and exposes aria-sort", () => {
    render(<PlayerTable group="hitter" players={players} planSeason={2027} caption="Test" />);
    const btn = screen.getByRole("button", { name: /^2027/ });
    fireEvent.click(btn);
    expect(names()).toEqual(["Alpha", "Charlie", "Bravo"]);
    expect(btn.closest("th")).toHaveAttribute("aria-sort", "descending");
  });

  it("marks estimated salaries and reports selection", () => {
    const onSelect = vi.fn();
    render(<PlayerTable group="hitter" players={players} planSeason={2027} caption="Test" onSelect={onSelect} />);
    expect(screen.getByTitle("Estimated salary")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Charlie" }));
    expect(onSelect).toHaveBeenCalledWith(3);
  });

  it("supports a checkbox column for trade building", () => {
    const onToggle = vi.fn();
    render(
      <PlayerTable group="hitter" players={players} planSeason={2027} caption="Test" checked={new Set([2])} onToggle={onToggle} compact />,
    );
    expect(screen.getByRole("checkbox", { name: "Include Bravo" })).toBeChecked();
    fireEvent.click(screen.getByRole("checkbox", { name: "Include Alpha" }));
    expect(onToggle).toHaveBeenCalledWith(1);
  });
});
