"use client";

import { scaleLinear } from "d3-scale";
import { useMemo, useState } from "react";
import { money, num } from "@/lib/format";
import type { AnyPlayer } from "@/lib/types";
import { useWidth } from "@/lib/useWidth";

interface Props {
  players: AnyPlayer[];
  dollarsPerWar: number;
  width?: number;
  height?: number;
  highlightIds?: number[];
  selectedId?: number | null;
  onSelect?: (id: number) => void;
}

const projected = (p: AnyPlayer) =>
  Array.isArray(p.proj_war) ? (p.proj_war[0] ?? p.war) : (p.proj_war ?? p.war);

/**
 * Bargain field: projected value (sWAR) against this season's salary. The diagonal is the
 * market rate ($/WAR); everything above it is surplus. Upper-left is where bargains live.
 */
export function BargainField({
  players,
  dollarsPerWar,
  width: fixedWidth,
  height = 320,
  highlightIds = [],
  selectedId = null,
  onSelect,
}: Props) {
  const [box, measured] = useWidth<HTMLElement>(520);
  const width = fixedWidth ?? measured;
  const [hover, setHover] = useState<AnyPlayer | null>(null);
  const m = { t: 12, r: 16, b: 34, l: 40 };
  const maxSal = Math.max(10, ...players.map((p) => p.contract.salary_now));
  const maxWar = Math.max(2, ...players.map(projected));
  const minWar = Math.min(-0.5, ...players.map(projected));
  const x = scaleLinear().domain([0, maxSal * 1.05]).range([m.l, width - m.r]);
  const y = scaleLinear().domain([minWar, maxWar * 1.08]).range([height - m.b, m.t]);
  const highlight = useMemo(() => new Set(highlightIds), [highlightIds]);
  const xTicks = x.ticks(5);
  const yTicks = y.ticks(5);
  const lineEnd = Math.min(maxSal * 1.05, (maxWar * 1.08 * dollarsPerWar));
  const focus = hover ?? players.find((p) => p.id === selectedId) ?? null;

  return (
    <figure ref={box} className="relative">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="block max-w-full"
        role="img"
        aria-label={`Projected sWAR versus ${players.length} salaries; diagonal marks ${money(dollarsPerWar)} per win`}
      >
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line x1={m.l} x2={width - m.r} y1={y(t)} y2={y(t)} stroke="rgb(var(--line))" strokeWidth={t === 0 ? 1 : 0.5} />
            <text x={m.l - 6} y={y(t)} textAnchor="end" dominantBaseline="middle" className="fill-ink-3 tabular" style={{ fontSize: 10 }}>
              {t}
            </text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={`x${t}`} x={x(t)} y={height - m.b + 14} textAnchor="middle" className="fill-ink-3 tabular" style={{ fontSize: 10 }}>
            ${t}M
          </text>
        ))}
        <text x={width - m.r} y={height - 4} textAnchor="end" className="fill-ink-3" style={{ fontSize: 10 }}>
          Salary next season
        </text>
        <text x={4} y={m.t} className="fill-ink-3" style={{ fontSize: 10 }}>
          sWAR
        </text>
        <line
          x1={x(0)}
          y1={y(0)}
          x2={x(lineEnd)}
          y2={y(lineEnd / dollarsPerWar)}
          stroke="rgb(var(--ink-3))"
          strokeDasharray="4 4"
        />
        <text x={x(lineEnd) - 4} y={y(lineEnd / dollarsPerWar) - 6} textAnchor="end" className="fill-ink-3" style={{ fontSize: 10 }}>
          Market rate
        </text>
        {players.map((p) => {
          const on = highlight.size === 0 || highlight.has(p.id);
          const sel = p.id === selectedId;
          return (
            <circle
              key={p.id}
              cx={x(p.contract.salary_now)}
              cy={y(projected(p))}
              r={sel ? 6 : on ? 4 : 2.5}
              fill={on ? "rgb(var(--accent))" : "rgb(var(--ink-3) / 0.35)"}
              fillOpacity={on ? 0.85 : 1}
              stroke={sel ? "rgb(var(--ink))" : "none"}
              strokeWidth={1.5}
              onMouseEnter={() => setHover(p)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onSelect?.(p.id)}
              style={{ cursor: onSelect ? "pointer" : undefined }}
            />
          );
        })}
      </svg>
      {focus && (
        <figcaption className="pointer-events-none absolute right-2 top-2 rounded border border-line bg-surface px-2 py-1 text-xs">
          <span className="font-semibold">{focus.name}</span>{" "}
          <span className="tabular text-ink-2">
            {num(projected(focus))} sWAR · {money(focus.contract.salary_now)}
          </span>
        </figcaption>
      )}
    </figure>
  );
}
