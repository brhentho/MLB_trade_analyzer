"use client";

import { scaleLinear } from "d3-scale";
import { useMemo, useRef, useState } from "react";
import type { Archetype, PlayerSummary } from "@/lib/types";
import { useWidth } from "@/lib/useWidth";

interface Props {
  players: PlayerSummary[];
  archetypes: Archetype[];
  width?: number;
  height?: number;
  selectedIds?: number[];
  focusId?: number | null;
  onBrush?: (ids: number[]) => void;
  onFocus?: (id: number) => void;
}

interface Box {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/**
 * Archetype constellation: every player placed by the shape of their ratings (2D projection).
 * Neighbors play alike. Drag to lasso a region; labels mark where archetypes cluster.
 */
export function Constellation({
  players,
  archetypes,
  width: fixedWidth,
  height: fixedHeight,
  selectedIds = [],
  focusId = null,
  onBrush,
  onFocus,
}: Props) {
  const [frame, measured] = useWidth<HTMLElement>(560);
  const width = fixedWidth ?? measured;
  const height = fixedHeight ?? Math.min(560, Math.round(width * 0.75));
  const svgRef = useRef<SVGSVGElement>(null);
  const [box, setBox] = useState<Box | null>(null);
  const [hover, setHover] = useState<PlayerSummary | null>(null);
  const pad = 18;
  const x = scaleLinear().domain([-1.05, 1.05]).range([pad, width - pad]);
  const y = scaleLinear().domain([-1.05, 1.05]).range([height - pad, pad]);
  const selected = useMemo(() => new Set(selectedIds), [selectedIds]);
  const mapped = players.filter((p) => p.map);

  const labels = useMemo(
    () =>
      archetypes
        .map((a) => {
          const members = mapped.filter((p) => p.archetypes.includes(a.id));
          if (members.length < 3) return null;
          const cx = members.reduce((s, p) => s + p.map!.x, 0) / members.length;
          const cy = members.reduce((s, p) => s + p.map!.y, 0) / members.length;
          return { id: a.id, label: a.label, cx, cy, n: members.length };
        })
        .filter((l): l is NonNullable<typeof l> => l !== null),
    [archetypes, mapped],
  );

  // Biggest clusters keep their label; any label whose box overlaps an earlier one is dropped.
  const visibleLabels = useMemo(() => {
    const kept: { box: [number, number, number, number]; l: (typeof labels)[number] }[] = [];
    for (const l of [...labels].sort((a, b) => b.n - a.n)) {
      const w = l.label.length * 6.4 + 8;
      const px = x(l.cx);
      const py = y(l.cy);
      const box: [number, number, number, number] = [px - w / 2, py - 10, px + w / 2, py + 4];
      if (kept.every(({ box: k }) => box[2] < k[0] || box[0] > k[2] || box[3] < k[1] || box[1] > k[3])) {
        kept.push({ box, l });
      }
    }
    return kept.map((k) => k.l);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labels, width, height]);

  const toLocal = (e: React.PointerEvent) => {
    const r = svgRef.current!.getBoundingClientRect();
    return { px: ((e.clientX - r.left) / r.width) * width, py: ((e.clientY - r.top) / r.height) * height };
  };

  const finish = (b: Box) => {
    const [xa, xb] = [Math.min(b.x0, b.x1), Math.max(b.x0, b.x1)];
    const [ya, yb] = [Math.min(b.y0, b.y1), Math.max(b.y0, b.y1)];
    if (xb - xa < 6 && yb - ya < 6) return;
    const ids = mapped
      .filter((p) => {
        const px = x(p.map!.x);
        const py = y(p.map!.y);
        return px >= xa && px <= xb && py >= ya && py <= yb;
      })
      .map((p) => p.id);
    onBrush?.(ids);
  };

  const focus = hover ?? mapped.find((p) => p.id === focusId) ?? null;

  return (
    <figure ref={frame} className="relative select-none">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="block max-w-full touch-none"
        role="img"
        aria-label={`Skill map of ${mapped.length} players. Drag to select a region.`}
        onPointerDown={(e) => {
          if (!onBrush) return;
          (e.target as Element).setPointerCapture?.(e.pointerId);
          const { px, py } = toLocal(e);
          setBox({ x0: px, y0: py, x1: px, y1: py });
        }}
        onPointerMove={(e) => {
          if (!box) return;
          const { px, py } = toLocal(e);
          setBox({ ...box, x1: px, y1: py });
        }}
        onPointerUp={() => {
          if (box) finish(box);
          setBox(null);
        }}
      >
        <rect x={0} y={0} width={width} height={height} fill="transparent" />
        <line x1={x(0)} x2={x(0)} y1={pad} y2={height - pad} stroke="rgb(var(--line))" strokeDasharray="2 4" />
        <line x1={pad} x2={width - pad} y1={y(0)} y2={y(0)} stroke="rgb(var(--line))" strokeDasharray="2 4" />
        {mapped.map((p) => {
          const on = selected.size === 0 || selected.has(p.id);
          const isFocus = p.id === focusId;
          return (
            <circle
              key={p.id}
              cx={x(p.map!.x)}
              cy={y(p.map!.y)}
              r={isFocus ? 6 : 2.5 + Math.max(0, p.ovr - 45) / 12}
              fill={on ? "rgb(var(--accent))" : "rgb(var(--ink-3) / 0.3)"}
              fillOpacity={on ? 0.75 : 1}
              stroke={isFocus ? "rgb(var(--ink))" : "none"}
              strokeWidth={1.5}
              onPointerEnter={() => setHover(p)}
              onPointerLeave={() => setHover(null)}
              onClick={(e) => {
                e.stopPropagation();
                onFocus?.(p.id);
              }}
            />
          );
        })}
        {visibleLabels.map((l) => (
          <text
            key={l.id}
            x={x(l.cx)}
            y={y(l.cy)}
            textAnchor="middle"
            className="pointer-events-none fill-ink"
            style={{ fontSize: 11, fontWeight: 600, paintOrder: "stroke", stroke: "rgb(var(--bg))", strokeWidth: 3 }}
          >
            {l.label}
          </text>
        ))}
        {box && (
          <rect
            x={Math.min(box.x0, box.x1)}
            y={Math.min(box.y0, box.y1)}
            width={Math.abs(box.x1 - box.x0)}
            height={Math.abs(box.y1 - box.y0)}
            fill="rgb(var(--accent) / 0.12)"
            stroke="rgb(var(--accent))"
            strokeDasharray="4 3"
          />
        )}
      </svg>
      {focus && (
        <figcaption className="pointer-events-none absolute left-2 top-2 rounded border border-line bg-surface px-2 py-1 text-xs">
          <span className="font-semibold">{focus.name}</span>{" "}
          <span className="text-ink-2">
            {focus.team} · {focus.group === "pitcher" ? focus.role : focus.position} · OVR {focus.ovr}
          </span>
        </figcaption>
      )}
    </figure>
  );
}
