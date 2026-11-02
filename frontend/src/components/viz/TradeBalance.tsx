import { money } from "@/lib/format";

interface Props {
  leftLabel: string;
  rightLabel: string;
  /** Surplus value received by each side, $M. */
  left: number;
  right: number;
}

/**
 * Trade balance beam: tilts toward the side receiving more surplus value.
 * Tilt is capped so a lopsided deal reads clearly without exaggeration.
 */
export function TradeBalance({ leftLabel, rightLabel, left, right }: Props) {
  const diff = left - right;
  const scale = Math.abs(left) + Math.abs(right) + 20;
  // The side receiving more value is heavier, so it sinks (negative angle lowers the left pan).
  const angle = -Math.max(-9, Math.min(9, (diff / scale) * 18));
  const short = (s: string) => (s.length > 18 ? `${s.slice(0, 17)}…` : s);
  const lean =
    Math.abs(diff) < 10 ? "Balanced" : `${diff > 0 ? leftLabel : rightLabel} gain ${money(Math.abs(diff))} more`;
  return (
    <figure className="w-full" aria-label={`Trade balance: ${lean}`}>
      <svg viewBox="0 0 320 120" className="w-full" aria-hidden>
        <polygon points="160,74 146,104 174,104" fill="rgb(var(--ink-3))" />
        <g
          style={{
            transform: `rotate(${angle}deg)`,
            transformOrigin: "160px 70px",
            transition: "transform var(--dur-slow) var(--ease-out)",
          }}
        >
          <rect x={30} y={67} width={260} height={6} rx={3} fill="rgb(var(--ink-2))" />
          <rect x={14} y={44} width={70} height={22} rx={4} fill={diff >= 0 ? "rgb(var(--accent))" : "rgb(var(--surface-2))"} />
          <rect x={236} y={44} width={70} height={22} rx={4} fill={diff < 0 ? "rgb(var(--accent))" : "rgb(var(--surface-2))"} />
          <text x={49} y={59} textAnchor="middle" className="tabular" style={{ fontSize: 11, fontWeight: 700 }}
            fill={diff >= 0 ? "rgb(var(--accent-ink))" : "rgb(var(--ink))"}>
            {money(left, 0)}
          </text>
          <text x={271} y={59} textAnchor="middle" className="tabular" style={{ fontSize: 11, fontWeight: 700 }}
            fill={diff < 0 ? "rgb(var(--accent-ink))" : "rgb(var(--ink))"}>
            {money(right, 0)}
          </text>
        </g>
        <text x={49} y={20} textAnchor="middle" className="fill-ink-2" style={{ fontSize: 11 }}>
          <title>{leftLabel}</title>
          {short(leftLabel)}
        </text>
        <text x={271} y={20} textAnchor="middle" className="fill-ink-2" style={{ fontSize: 11 }}>
          <title>{rightLabel}</title>
          {short(rightLabel)}
        </text>
      </svg>
      <figcaption className="text-center text-sm font-semibold">{lean}</figcaption>
    </figure>
  );
}
