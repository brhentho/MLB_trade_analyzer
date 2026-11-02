import { describe, expect, it } from "vitest";
import { filtersToChips, removeChip } from "./chips";
import { controlYears, money, ratingT, scout5, signedMoney } from "./format";
import type { PlayerSummary } from "./types";

describe("format", () => {
  it("formats millions", () => {
    expect(money(0.78)).toBe("$780K");
    expect(money(17.45)).toBe("$17.4M");
    expect(money(-12)).toBe("−$12.0M");
    expect(money(1240)).toBe("$1.24B");
    expect(money(null)).toBe("—");
    expect(signedMoney(4)).toBe("+$4.0M");
  });

  it("rounds to the OOTP 5-step scale", () => {
    expect(scout5(67)).toBe("65");
    expect(scout5(68)).toBe("70");
    expect(scout5(null)).toBe("—");
  });

  it("clamps rating color position", () => {
    expect(ratingT(20)).toBe(0);
    expect(ratingT(80)).toBe(1);
    expect(ratingT(52.5)).toBeCloseTo(0.5);
  });

  it("counts seasons of control from the planning season", () => {
    const p = { contract: { control_through: 2029 } } as PlayerSummary;
    expect(controlYears(p, 2027)).toBe(3);
    expect(controlYears(p, 2030)).toBe(0);
  });
});

describe("chips", () => {
  const filters = {
    group: "pitcher" as const,
    roles: ["RP" as const],
    throws: ["L"],
    percentiles_min: { chase_percent: 90 },
    salary_max: 6,
    control_min_years: 2,
  };

  it("describes every constraint", () => {
    expect(filtersToChips(filters).map((c) => c.label)).toEqual([
      "Reliever",
      "Throws L",
      "Chase ≥ 90th pct",
      "Salary ≤ $6.0M",
      "2+ yrs control",
    ]);
  });

  it("removes a single constraint without mutating the original", () => {
    const next = removeChip(filters, "percentiles_min:chase_percent");
    expect(next.percentiles_min).toBeUndefined();
    expect(filters.percentiles_min).toEqual({ chase_percent: 90 });
    expect(removeChip(filters, "salary_max").salary_max).toBeUndefined();
    expect(removeChip(filters, "roles:RP").roles).toBeUndefined();
  });
});
