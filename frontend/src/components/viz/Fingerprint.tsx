import { RATING_LABELS, RATING_SHORT, ratingKeys } from "@/lib/format";
import type { Group, Ratings } from "@/lib/types";

interface Props {
  group: Group;
  ratings: Ratings;
  compare?: Ratings | null;
  size?: number;
  labels?: boolean;
  title?: string;
}

const MIN = 20;
const MAX = 80;

function points(keys: string[], ratings: Ratings, r: number, c: number): string {
  return keys
    .map((k, i) => {
      const v = (ratings as Record<string, number | null | undefined>)[k] ?? 35;
      const t = (Math.min(MAX, Math.max(MIN, v)) - MIN) / (MAX - MIN);
      const a = (Math.PI * 2 * i) / keys.length - Math.PI / 2;
      return `${(c + Math.cos(a) * r * t).toFixed(1)},${(c + Math.sin(a) * r * t).toFixed(1)}`;
    })
    .join(" ");
}

/**
 * Skill fingerprint: radial shape of a player's 20-80 ratings. The dashed ring is 50 (average).
 * Players with the same "shape" play the same way, regardless of overall level.
 */
export function Fingerprint({ group, ratings, compare, size = 64, labels = false, title }: Props) {
  const keys = ratingKeys(group);
  const pad = labels ? 22 : 2;
  const c = size / 2;
  const r = c - pad;
  const avgT = (50 - MIN) / (MAX - MIN);
  const summary = keys
    .map((k) => `${RATING_LABELS[k]} ${(ratings as Record<string, number | null>)[k] ?? "no data"}`)
    .join(", ");
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={title ?? summary}>
      <title>{title ?? summary}</title>
      <polygon
        points={keys
          .map((_, i) => {
            const a = (Math.PI * 2 * i) / keys.length - Math.PI / 2;
            return `${c + Math.cos(a) * r},${c + Math.sin(a) * r}`;
          })
          .join(" ")}
        fill="rgb(var(--surface-2))"
        stroke="rgb(var(--line))"
      />
      <circle cx={c} cy={c} r={r * avgT} fill="none" stroke="rgb(var(--ink-3))" strokeDasharray="2 3" strokeWidth={1} />
      {keys.map((_, i) => {
        const a = (Math.PI * 2 * i) / keys.length - Math.PI / 2;
        return (
          <line
            key={i}
            x1={c}
            y1={c}
            x2={c + Math.cos(a) * r}
            y2={c + Math.sin(a) * r}
            stroke="rgb(var(--line))"
            strokeWidth={0.75}
          />
        );
      })}
      {compare && (
        <polygon
          points={points(keys, compare, r, c)}
          fill="rgb(var(--ink-2) / 0.12)"
          stroke="rgb(var(--ink-2))"
          strokeWidth={1.25}
          strokeDasharray="3 2"
        />
      )}
      <polygon
        points={points(keys, ratings, r, c)}
        fill="rgb(var(--accent) / 0.35)"
        stroke="rgb(var(--accent))"
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      {labels &&
        keys.map((k, i) => {
          const a = (Math.PI * 2 * i) / keys.length - Math.PI / 2;
          return (
            <text
              key={k}
              x={c + Math.cos(a) * (r + 12)}
              y={c + Math.sin(a) * (r + 12)}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-ink-3"
              style={{ fontSize: 9, fontWeight: 600, letterSpacing: 0.4 }}
            >
              {RATING_SHORT[k]}
            </text>
          );
        })}
    </svg>
  );
}
