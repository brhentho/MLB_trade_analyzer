"use client";

import type { Team } from "@/lib/types";

interface Props {
  teams: Team[];
  value: string;
  onChange: (abbrev: string) => void;
  label?: string;
  id?: string;
  className?: string;
}

export function TeamPicker({ teams, value, onChange, label = "Team", id = "team-picker", className = "" }: Props) {
  const byDivision = teams.reduce<Record<string, Team[]>>((acc, t) => {
    (acc[t.division || t.league] ??= []).push(t);
    return acc;
  }, {});
  return (
    <label htmlFor={id} className={`inline-flex items-center gap-2 text-sm ${className}`}>
      <span className="text-ink-2">{label}</span>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-10 rounded border border-line bg-surface px-2 font-semibold text-ink"
      >
        {Object.entries(byDivision)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([div, ts]) => (
            <optgroup key={div} label={div}>
              {ts.map((t) => (
                <option key={t.abbrev} value={t.abbrev}>
                  {t.name}
                </option>
              ))}
            </optgroup>
          ))}
      </select>
    </label>
  );
}
