"use client";

import { useState } from "react";
import { money, num, positionLabel, signedMoney } from "@/lib/format";
import type { AnyPlayer } from "@/lib/types";
import { Fingerprint } from "@/components/viz/Fingerprint";

export type SortKey = "war" | "salary" | "surplus";

const SORTS: { key: SortKey; label: string }[] = [
  { key: "war", label: "sWAR" },
  { key: "salary", label: "Salary" },
  { key: "surplus", label: "Surplus" },
];

const value = (p: AnyPlayer, k: SortKey) =>
  k === "war" ? p.war : k === "salary" ? p.contract.salary_now : p.surplus;

interface Props {
  players: AnyPlayer[];
  /** Extra column, e.g. shape match %. */
  extra?: (p: AnyPlayer) => string | null;
  onRoster: Set<number>;
  armedId: number | null;
  onPick: (p: AnyPlayer, el: HTMLElement) => void;
  sortable?: boolean;
  pageSize?: number;
}

/** Finder results. Picking a row selects the player for placement and opens their details. */
export function PlayerList({ players, extra, onRoster, armedId, onPick, sortable = true, pageSize = 40 }: Props) {
  const [sort, setSort] = useState<SortKey>("war");
  const [desc, setDesc] = useState(true);
  const [limit, setLimit] = useState(pageSize);
  const rows = sortable
    ? [...players].sort((a, b) => (desc ? value(b, sort) - value(a, sort) : value(a, sort) - value(b, sort)))
    : players;
  const shown = rows.slice(0, limit);

  return (
    <div>
      {sortable && (
        <div className="mb-1 flex items-center gap-1 text-xs" role="group" aria-label="Sort players">
          <span className="mr-1 text-ink-3">Sort by</span>
          {SORTS.map((s) => {
            const on = s.key === sort;
            return (
              <button
                key={s.key}
                type="button"
                aria-pressed={on}
                onClick={() => (on ? setDesc((d) => !d) : (setSort(s.key), setDesc(s.key !== "salary")))}
                className={`min-h-8 rounded-sm px-2 font-semibold ${on ? "bg-surface-2 text-ink" : "text-ink-2 hover:bg-surface-2"}`}
              >
                {s.label}
                {on && <span aria-hidden> {desc ? "↓" : "↑"}</span>}
                {on && <span className="sr-only">{desc ? ", highest first" : ", lowest first"}</span>}
              </button>
            );
          })}
        </div>
      )}
      <div aria-hidden className="tabular grid grid-cols-[minmax(0,1fr)_auto] gap-2 px-1 pb-1 text-[11px] text-ink-3">
        <span>{players.length} players</span>
        <span className="grid grid-cols-[2.5rem_3.75rem_4rem] gap-1 text-right">
          <span>sWAR</span>
          <span>Salary</span>
          <span>Surplus</span>
        </span>
      </div>
      <ul className="divide-y divide-line border-y border-line">
        {shown.map((p) => {
          const x = extra?.(p);
          const mine = onRoster.has(p.id);
          return (
            <li key={p.id}>
              <button
                type="button"
                onClick={(e) => onPick(p, e.currentTarget)}
                aria-pressed={armedId === p.id}
                className={`grid min-h-11 w-full grid-cols-[2rem_minmax(0,1fr)_auto] items-center gap-2 px-1 py-1 text-left text-sm hover:bg-surface-2 ${
                  armedId === p.id ? "bg-surface-2" : ""
                }`}
              >
                <Fingerprint group={p.group} ratings={p.ratings} size={30} title={`${p.name} rating shape`} />
                <span className="min-w-0">
                  <span className="block truncate font-semibold">{p.name}</span>
                  <span className="block truncate text-xs text-ink-2">
                    {p.team} · {positionLabel(p)} · Age {p.age}
                    {x ? ` · ${x}` : ""}
                    {mine ? " · On your roster" : ""}
                  </span>
                </span>
                <span className="tabular grid grid-cols-[2.5rem_3.75rem_4rem] gap-1 text-right text-xs">
                  <span title="sWAR">
                    <span className="sr-only">sWAR </span>
                    {num(p.war)}
                  </span>
                  <span className="text-ink-2" title="Salary">
                    {money(p.contract.salary_now)}
                  </span>
                  <span className={p.surplus >= 0 ? "text-good" : "text-bad"} title="Surplus value">
                    {signedMoney(p.surplus, 0)}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {rows.length > limit && (
        <button
          type="button"
          onClick={() => setLimit((l) => l + pageSize)}
          className="mt-1 min-h-10 px-1 text-xs font-semibold text-ink-2 hover:underline"
        >
          Show {Math.min(pageSize, rows.length - limit)} more of {rows.length - limit}
        </button>
      )}
    </div>
  );
}
