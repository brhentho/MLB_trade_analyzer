"use client";

import { useMemo, useState } from "react";
import { ControlPips } from "@/components/viz/ControlPips";
import { RatingCell } from "@/components/viz/RatingBar";
import { RATING_LABELS, RATING_SHORT, money, num, positionLabel, ratingKeys, signedMoney } from "@/lib/format";
import type { AnyPlayer, Group, Reason } from "@/lib/types";

export type SortKey = "name" | "pos" | "age" | "ovr" | "pot" | "war" | "salary" | "control" | "surplus" | `r:${string}`;

interface Props {
  group: Group;
  players: AnyPlayer[];
  planSeason: number;
  caption: string;
  selectedId?: number | null;
  onSelect?: (id: number) => void;
  reasons?: Record<number, Reason[]>;
  /** Optional leading checkbox column (trade builder). */
  checked?: Set<number>;
  onToggle?: (id: number) => void;
  /** Hide rating columns for narrow side-by-side tables. */
  compact?: boolean;
  initialSort?: SortKey;
  showTeam?: boolean;
}

const ASCENDING_FIRST: SortKey[] = ["name", "pos", "age"];

const value = (p: AnyPlayer, key: SortKey, plan: number): number | string => {
  if (key.startsWith("r:")) return (p.ratings as Record<string, number | null>)[key.slice(2)] ?? -1;
  switch (key) {
    case "name":
      return p.name;
    case "pos":
      return positionLabel(p);
    case "age":
      return p.age;
    case "ovr":
      return p.ovr;
    case "pot":
      return p.pot;
    case "war":
      return p.war;
    case "salary":
      return p.contract.salary_now;
    case "control":
      return p.contract.control_through - plan;
    case "surplus":
      return p.surplus;
    default:
      return 0;
  }
};

/** Dense, sortable player grid in the Out of the Park tradition. */
export function PlayerTable({
  group,
  players,
  planSeason,
  caption,
  selectedId = null,
  onSelect,
  reasons,
  checked,
  onToggle,
  compact = false,
  initialSort = "war",
  showTeam = false,
}: Props) {
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({
    key: initialSort,
    desc: !ASCENDING_FIRST.includes(initialSort),
  });
  const keys = compact ? [] : ratingKeys(group);
  const rows = useMemo(() => {
    const out = [...players];
    out.sort((a, b) => {
      const va = value(a, sort.key, planSeason);
      const vb = value(b, sort.key, planSeason);
      const cmp = typeof va === "string" ? va.localeCompare(String(vb)) : va - (vb as number);
      return sort.desc ? -cmp : cmp;
    });
    return out;
  }, [players, sort, planSeason]);

  const header = (key: SortKey, label: string, title: string, align: "text-left" | "text-right" | "text-center") => {
    const active = sort.key === key;
    return (
      <th
        key={key}
        scope="col"
        aria-sort={active ? (sort.desc ? "descending" : "ascending") : "none"}
        className={`sticky top-0 z-10 bg-surface px-1 py-1 font-medium ${align}`}
      >
        <button
          type="button"
          title={title}
          onClick={() =>
            setSort((s) => ({ key, desc: s.key === key ? !s.desc : !ASCENDING_FIRST.includes(key) }))
          }
          className={`inline-flex min-h-7 items-center gap-0.5 rounded-sm px-1 text-xs ${
            active ? "text-accent-text" : "text-ink-3 hover:text-ink"
          }`}
        >
          {label}
          <span aria-hidden className="inline-block w-2">
            {active ? (sort.desc ? "↓" : "↑") : ""}
          </span>
        </button>
      </th>
    );
  };

  const cell = "px-1.5 py-1";

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="border-b border-line">
          <tr>
            {onToggle && (
              <th scope="col" className="sticky top-0 z-10 w-8 bg-surface">
                <span className="sr-only">Include</span>
              </th>
            )}
            {header("name", "Player", "Sort by name", "text-left")}
            {showTeam && (
              <th scope="col" className="sticky top-0 bg-surface px-1.5 text-left text-xs font-medium text-ink-3">
                Team
              </th>
            )}
            {header("pos", "Pos", "Position", "text-left")}
            {header("age", "Age", "Age", "text-right")}
            {header("ovr", "OVR", "Overall, 20–80", "text-right")}
            {!compact && header("pot", "POT", "Potential, 20–80", "text-right")}
            {keys.map((k) => header(`r:${k}`, RATING_SHORT[k], RATING_LABELS[k], "text-center"))}
            {header("war", "sWAR", "StatSlugger WAR estimate, stats season", "text-right")}
            {header("salary", `${planSeason}`, `Salary in ${planSeason}`, "text-right")}
            {!compact && header("control", "Control", "Seasons of control", "text-left")}
            {header("surplus", "Surplus", "Projected value minus salary over control", "text-right")}
            {reasons && (
              <th scope="col" className="sticky top-0 bg-surface px-1.5 text-left text-xs font-medium text-ink-3">
                Why it matched
              </th>
            )}
          </tr>
        </thead>
        <tbody className="tabular">
          {rows.map((p) => {
            const sel = p.id === selectedId;
            return (
              <tr
                key={p.id}
                className={`border-b border-line/60 transition-colors duration-fast ease-out ${
                  sel ? "bg-accent/15" : checked?.has(p.id) ? "bg-surface-2" : "hover:bg-surface-2"
                }`}
              >
                {onToggle && (
                  <td className={cell}>
                    <input
                      type="checkbox"
                      aria-label={`Include ${p.name}`}
                      checked={checked?.has(p.id) ?? false}
                      onChange={() => onToggle(p.id)}
                      className="h-4 w-4 accent-[rgb(var(--accent))]"
                    />
                  </td>
                )}
                <th scope="row" className={`${cell} max-w-[13rem] text-left font-normal`}>
                  <button
                    type="button"
                    onClick={() => onSelect?.(p.id)}
                    aria-pressed={sel}
                    title={p.name}
                    className="block min-h-7 w-full truncate rounded-sm text-left font-semibold text-ink hover:text-accent-text"
                  >
                    {p.name}
                  </button>
                </th>
                {showTeam && <td className={`${cell} text-ink-2`}>{p.team}</td>}
                <td className={`${cell} text-ink-2`}>{positionLabel(p)}</td>
                <td className={`${cell} text-right`}>{p.age}</td>
                <td className={`${cell} text-right font-semibold`}>{p.ovr}</td>
                {!compact && <td className={`${cell} text-right text-ink-2`}>{p.pot}</td>}
                {keys.map((k) => (
                  <td key={k} className={`${cell} text-center`}>
                    <RatingCell value={p.ratings[k]} />
                  </td>
                ))}
                <td className={`${cell} text-right font-semibold`}>{num(p.war)}</td>
                <td className={`${cell} whitespace-nowrap text-right`}>
                  {money(p.contract.salary_now)}
                  <span className="ml-0.5 inline-block w-1.5 text-ink-3" title={p.contract.verified ? undefined : "Estimated salary"}>
                    {p.contract.verified ? "" : "*"}
                  </span>
                </td>
                {!compact && (
                  <td className={cell}>
                    <ControlPips player={p} planSeason={planSeason} max={6} />
                  </td>
                )}
                <td className={`${cell} whitespace-nowrap text-right ${p.surplus >= 0 ? "text-good" : "text-bad"}`}>
                  {signedMoney(p.surplus, 0)}
                </td>
                {reasons && (
                  <td className={`${cell} min-w-[14rem] text-xs text-ink-2`}>
                    {(reasons[p.id] ?? []).map((r) => r.label).join(" · ")}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
