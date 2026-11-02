"use client";

import { scaleLinear } from "d3-scale";
import { money } from "@/lib/format";
import type { Player } from "@/lib/types";

interface Props {
  players: Player[];
  planSeason: number;
  cbt: number;
  seasons?: number;
  /** Players named individually; the rest are grouped. */
  named?: number;
  highlightIds?: number[];
  onSelect?: (id: number) => void;
}

/**
 * Payroll ledger: one row per season, salary segments stacked left to right,
 * with the competitive balance tax line. Money coming off is visible as the bars shrink.
 */
export function PayrollLedger({ players, planSeason, cbt, seasons = 6, named = 8, highlightIds = [], onSelect }: Props) {
  const years = Array.from({ length: seasons }, (_, i) => planSeason + i);
  const biggest = [...players]
    .sort((a, b) => b.contract.salary_now - a.contract.salary_now)
    .slice(0, named)
    .map((p) => p.id);
  const totals = years.map((y) =>
    players.reduce((sum, p) => sum + (p.contract.years.find((c) => c.year === y)?.salary ?? 0), 0),
  );
  const maxTotal = Math.max(cbt * 1.08, ...totals);
  const x = scaleLinear().domain([0, maxTotal]).range([0, 100]);
  const highlight = new Set(highlightIds);

  return (
    <figure className="w-full">
      <div className="space-y-1.5" aria-hidden>
        {years.map((y, yi) => {
          let offset = 0;
          const segs = biggest
            .map((id) => {
              const p = players.find((pl) => pl.id === id)!;
              const sal = p.contract.years.find((c) => c.year === y)?.salary ?? 0;
              const seg = { p, sal, left: offset };
              offset += sal;
              return seg;
            })
            .filter((s) => s.sal > 0);
          const rest = (totals[yi] ?? 0) - offset;
          return (
            <div key={y} className="grid grid-cols-[3rem_1fr_4.5rem] items-center gap-2 text-xs">
              <span className="tabular text-ink-3">{y}</span>
              <div className="relative h-5 rounded-sm bg-surface-2">
                {segs.map(({ p, sal, left }) => (
                  <button
                    key={p.id}
                    type="button"
                    tabIndex={-1}
                    onClick={() => onSelect?.(p.id)}
                    title={`${p.name}: ${money(sal)} in ${y}${p.contract.verified ? "" : " (estimate)"}`}
                    className={`absolute inset-y-0 border-r border-bg transition-opacity duration-fast ease-out ${
                      highlight.size && !highlight.has(p.id) ? "opacity-40" : ""
                    } ${p.contract.verified ? "bg-accent" : "bg-accent/55"}`}
                    style={{ left: `${x(left)}%`, width: `${x(sal)}%` }}
                  >
                    {x(sal) > 9 && (
                      <span className="block truncate px-1 text-left text-[10px] font-semibold leading-5 text-accent-ink">
                        {p.name.split(" ").slice(-1)[0]}
                      </span>
                    )}
                  </button>
                ))}
                {rest > 0.01 && (
                  <span
                    className="absolute inset-y-0 bg-ink-3/40"
                    style={{ left: `${x(offset)}%`, width: `${x(rest)}%` }}
                    title={`Everyone else: ${money(rest)}`}
                  />
                )}
                <span className="absolute inset-y-[-3px] w-0.5 bg-bad" style={{ left: `${x(cbt)}%` }} />
              </div>
              <span className={`tabular text-right font-semibold ${(totals[yi] ?? 0) > cbt ? "text-bad" : ""}`}>
                {money(totals[yi] ?? 0, 0)}
              </span>
            </div>
          );
        })}
      </div>
      <figcaption className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-3">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-accent" /> Signed
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-accent/55" /> Estimated
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-3 w-0.5 bg-bad" /> Tax line {money(cbt, 0)}
        </span>
      </figcaption>
      <table className="sr-only">
        <caption>Committed payroll by season</caption>
        <thead>
          <tr>
            <th>Season</th>
            <th>Payroll</th>
          </tr>
        </thead>
        <tbody>
          {years.map((y, i) => (
            <tr key={y}>
              <td>{y}</td>
              <td>{money(totals[i] ?? 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
