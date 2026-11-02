import { RATING_LABELS, ratingColor, ratingT, ratingWord, scout5 } from "@/lib/format";
import type { RatingKey } from "@/lib/types";

interface Props {
  rating: RatingKey;
  value: number | null | undefined;
  /** Show the exact 20-80 value instead of OOTP-style nearest 5. */
  exact?: boolean;
  compact?: boolean;
}

/** 20-80 scouting bar with a tick at 50 (league average). */
export function RatingBar({ rating, value, exact = false, compact = false }: Props) {
  const label = RATING_LABELS[rating];
  const shown = exact ? (value ?? "—") : scout5(value);
  return (
    <div
      className={`grid items-center gap-2 ${compact ? "grid-cols-[5.5rem_1fr_2rem] text-xs" : "grid-cols-[6.5rem_1fr_2.25rem] text-sm"}`}
      title={value == null ? `${label}: no data` : `${label}: ${value} (${ratingWord(value)})`}
    >
      <span className="truncate text-ink-2">{label}</span>
      <span className="relative h-2 rounded-sm bg-surface-2" aria-hidden>
        <span
          className="absolute inset-y-0 left-0 rounded-sm"
          style={{ width: `${Math.max(4, ratingT(value) * 100)}%`, background: ratingColor(value) }}
        />
        <span className="absolute inset-y-[-2px] w-px bg-ink-3" style={{ left: `${ratingT(50) * 100}%` }} />
      </span>
      <span className="tabular text-right font-semibold" aria-label={`${label} ${value ?? "no data"}`}>
        {shown}
      </span>
    </div>
  );
}

/** Single heat-colored rating cell for dense grids. */
export function RatingCell({ value, exact = true }: { value: number | null | undefined; exact?: boolean }) {
  if (value == null) return <span className="text-ink-3">—</span>;
  const t = ratingT(value);
  return (
    <span
      className="tabular inline-flex min-w-[2.25rem] justify-center rounded-sm px-1 py-0.5 font-semibold"
      style={{
        background: ratingColor(value),
        color: t > 0.55 ? "rgb(var(--accent-ink))" : "rgb(var(--ink))",
      }}
      title={`${value} (${ratingWord(value)})`}
    >
      {exact ? value : scout5(value)}
    </span>
  );
}
