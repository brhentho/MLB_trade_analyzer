import { RATING_LABELS, money } from "@/lib/format";
import type { RatingKey, SearchFilters } from "@/lib/types";

const PCT_LABELS: Record<string, string> = {
  chase_percent: "Chase",
  whiff_percent: "Whiff",
  k_percent: "K",
  bb_percent: "BB",
  brl_percent: "Barrel",
  exit_velocity: "Exit velo",
  max_ev: "Max EV",
  hard_hit_percent: "Hard-hit",
  sprint_speed: "Sprint speed",
  bat_speed: "Bat speed",
  fb_velocity: "FB velo",
  fb_spin: "FB spin",
  oaa: "OAA",
  arm_strength: "Arm strength",
  xwoba: "xwOBA",
  xera: "xERA",
};

export interface Chip {
  /** Key used to remove this constraint from the filters. */
  id: string;
  label: string;
}

/** Turn filters into human-readable, individually removable chips. */
export function filtersToChips(f: SearchFilters, archetypeLabels: Record<string, string> = {}): Chip[] {
  const chips: Chip[] = [];
  if (f.group && !f.positions && !f.roles) chips.push({ id: "group", label: f.group === "hitter" ? "Hitters" : "Pitchers" });
  f.positions?.forEach((p) => chips.push({ id: `positions:${p}`, label: p }));
  f.roles?.forEach((r) => chips.push({ id: `roles:${r}`, label: r === "SP" ? "Starter" : "Reliever" }));
  f.throws?.forEach((t) => chips.push({ id: `throws:${t}`, label: `Throws ${t}` }));
  f.bats?.forEach((b) => chips.push({ id: `bats:${b}`, label: `Bats ${b}` }));
  f.teams?.forEach((t) => chips.push({ id: `teams:${t}`, label: t }));
  if (f.age_min !== undefined) chips.push({ id: "age_min", label: `Age ≥ ${f.age_min}` });
  if (f.age_max !== undefined) chips.push({ id: "age_max", label: `Age ≤ ${f.age_max}` });
  f.archetypes?.forEach((a) => chips.push({ id: `archetypes:${a}`, label: archetypeLabels[a] ?? a }));
  Object.entries(f.ratings_min ?? {}).forEach(([k, v]) =>
    chips.push({ id: `ratings_min:${k}`, label: `${RATING_LABELS[k as RatingKey] ?? k} ≥ ${v}` }),
  );
  Object.entries(f.ratings_max ?? {}).forEach(([k, v]) =>
    chips.push({ id: `ratings_max:${k}`, label: `${RATING_LABELS[k as RatingKey] ?? k} ≤ ${v}` }),
  );
  Object.entries(f.percentiles_min ?? {}).forEach(([k, v]) =>
    chips.push({ id: `percentiles_min:${k}`, label: `${PCT_LABELS[k] ?? k} ≥ ${v}th pct` }),
  );
  if (f.salary_max !== undefined) chips.push({ id: "salary_max", label: `Salary ≤ ${money(f.salary_max)}` });
  if (f.control_min_years !== undefined)
    chips.push({ id: "control_min_years", label: `${f.control_min_years}+ yrs control` });
  if (f.war_min !== undefined) chips.push({ id: "war_min", label: `sWAR ≥ ${f.war_min}` });
  return chips;
}

/** Remove the constraint behind a chip, returning new filters. */
export function removeChip(f: SearchFilters, chipId: string): SearchFilters {
  const next: SearchFilters = structuredClone(f);
  const [key, value] = chipId.split(":") as [keyof SearchFilters, string | undefined];
  if (value === undefined) {
    delete next[key];
    return next;
  }
  const field = next[key];
  if (Array.isArray(field)) {
    const filtered = (field as string[]).filter((v) => v !== value);
    if (filtered.length) (next as Record<string, unknown>)[key] = filtered;
    else delete next[key];
  } else if (field && typeof field === "object") {
    const obj = { ...(field as Record<string, number>) };
    delete obj[value];
    if (Object.keys(obj).length) (next as Record<string, unknown>)[key] = obj;
    else delete next[key];
  }
  return next;
}
