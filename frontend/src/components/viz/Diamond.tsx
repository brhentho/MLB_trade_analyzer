import type { ReactNode } from "react";

/** Field coordinates in the SVG viewBox (x 0-100, y 0-90) for each lineup slot on a diamond viewed from behind home plate. */
export const DIAMOND_SLOTS: Record<string, { x: number; y: number }> = {
  C: { x: 50, y: 85 },
  "1B": { x: 71, y: 55 },
  "2B": { x: 61, y: 42 },
  SS: { x: 39, y: 42 },
  "3B": { x: 29, y: 55 },
  LF: { x: 17, y: 24 },
  CF: { x: 50, y: 11 },
  RF: { x: 83, y: 24 },
  DH: { x: 89, y: 82 },
};

interface Props {
  renderSlot: (slot: string) => ReactNode;
  ariaLabel?: string;
}

/**
 * Diamond depth chart. The field is drawn in SVG; each slot is an HTML overlay so it can hold
 * real interactive controls (buttons, drop targets) with proper focus behavior.
 */
export function Diamond({ renderSlot, ariaLabel = "Lineup by position" }: Props) {
  return (
    <div className="relative aspect-[10/9] w-full" role="group" aria-label={ariaLabel}>
      <svg viewBox="0 0 100 90" className="absolute inset-0 h-full w-full" aria-hidden preserveAspectRatio="none">
        <path d="M50 88 L2 40 Q50 -14 98 40 Z" fill="rgb(var(--field) / 0.55)" />
        <path d="M50 84 L72 62 L50 40 L28 62 Z" fill="rgb(var(--field))" stroke="rgb(var(--ink) / 0.25)" strokeWidth={0.4} />
        <circle cx={50} cy={62} r={2.2} fill="rgb(var(--ink) / 0.18)" />
        {[
          [72, 62],
          [50, 40],
          [28, 62],
        ].map(([bx, by]) => (
          <rect key={`${bx}-${by}`} x={bx! - 1.1} y={by! - 1.1} width={2.2} height={2.2} fill="rgb(var(--ink) / 0.7)" transform={`rotate(45 ${bx} ${by})`} />
        ))}
        <path d="M50 84 L2 36 M50 84 L98 36" stroke="rgb(var(--ink) / 0.2)" strokeWidth={0.3} />
      </svg>
      {Object.entries(DIAMOND_SLOTS).map(([slot, pos]) => (
        <div
          key={slot}
          className="absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${pos.x}%`, top: `${(pos.y / 90) * 100}%` }}
        >
          {renderSlot(slot)}
        </div>
      ))}
    </div>
  );
}
